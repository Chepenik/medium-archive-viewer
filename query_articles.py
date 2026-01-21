#!/usr/bin/env python3
"""
RAG Query Interface for Medium Articles.

=============================================================================
WHAT DOES THIS SCRIPT DO?
=============================================================================
This is the "chat" interface for your article archive. When you ask a question,
it follows this process:

1. SEARCH: Convert your question to an embedding and find similar chunks
2. CONTEXT: Gather the most relevant article excerpts
3. PROMPT: Send the context + your question to an LLM
4. ANSWER: The LLM generates a response grounded in YOUR writing

This is called RAG (Retrieval Augmented Generation) because we "retrieve"
relevant content first, then "augment" the AI's knowledge with it.

WHY IS THIS USEFUL?
- Regular ChatGPT doesn't know about your articles
- With RAG, the AI can answer questions about things you've written
- The answers are grounded in YOUR actual words, not hallucinated

PREREQUISITES:
- Run embed_articles.py first to build the vector database
- Have LM Studio running with a model loaded (or configure another LLM)

=============================================================================

Usage:
    python query_articles.py                    # Interactive chat mode
    python query_articles.py "your question"   # Single query
    python query_articles.py --search "topic"  # Search only (no LLM)
"""
import argparse
import json
import requests
from typing import List, Dict, Tuple, Optional

import chromadb
from chromadb.config import Settings

import rag_config as cfg


# =============================================================================
# STEP 1: CONVERT QUERY TO EMBEDDING
# =============================================================================
#
# When you search, we need to convert your question into the same format as
# the stored article chunks (a vector/embedding). This lets us compare them.
# =============================================================================

def get_query_embedding(query: str, backend: str = cfg.EMBEDDING_BACKEND) -> List[float]:
    """
    Get embedding for a query string.

    This converts your question into a list of numbers (same format as the
    article chunks). The embedding service must match what was used to
    embed the articles, or similarity comparisons won't work correctly.
    """
    if backend == "ollama":
        # Ollama: Local AI service (recommended for Mac)
        response = requests.post(
            f"{cfg.OLLAMA_BASE_URL}/api/embeddings",
            json={"model": cfg.OLLAMA_MODEL, "prompt": query}
        )
        response.raise_for_status()
        return response.json()["embedding"]

    elif backend == "lmstudio":
        # LM Studio: Alternative local AI service
        response = requests.post(
            cfg.LMSTUDIO_EMBED_URL,
            json={"model": cfg.LMSTUDIO_EMBED_MODEL, "input": [query]},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

    elif backend == "sentence-transformers":
        # Sentence Transformers: Pure Python, no server needed
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(cfg.ST_MODEL, trust_remote_code=True)
        embedding = model.encode([query])[0]
        return embedding.tolist()

    else:
        raise ValueError(f"Unknown backend: {backend}")


# =============================================================================
# STEP 2: SEARCH FOR RELEVANT ARTICLE CHUNKS
# =============================================================================

def search_articles(
    query: str,
    collection,
    top_k: int = cfg.TOP_K_RESULTS,
    backend: str = cfg.EMBEDDING_BACKEND
) -> List[Dict]:
    """
    Search for relevant article chunks.

    HOW IT WORKS:
    1. Convert query to embedding (list of numbers)
    2. Compare to all stored chunk embeddings
    3. Return the top_k most similar chunks

    The similarity is measured by "cosine distance" - basically how close
    the angle is between two vectors. Smaller distance = more similar.
    """
    # Convert query text to embedding
    query_embedding = get_query_embedding(query, backend)

    # Search ChromaDB for similar chunks
    # n_results: how many to return
    # include: what data to return (text, metadata, distances)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # Process results into a cleaner format
    chunks = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]

        # ChromaDB returns "distance" (lower = more similar)
        # We convert to "similarity" (higher = more similar) for clarity
        similarity = 1 - distance

        # Filter out low-quality matches
        if similarity < cfg.SIMILARITY_THRESHOLD:
            continue

        chunks.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "similarity": similarity
        })

    return chunks


# =============================================================================
# STEP 3: FORMAT CONTEXT FOR THE LLM
# =============================================================================

def format_context(chunks: List[Dict]) -> str:
    """
    Format retrieved chunks as context for the LLM.

    This takes the raw chunk data and formats it nicely so the LLM can
    understand where each piece of information came from.

    Example output:
    ---
    From: "Why Bitcoin Matters" (2024-01-15)
    Bitcoin is revolutionary because...

    ---
    From: "The Future of Money" (2024-02-20)
    When I first discovered...
    """
    if not chunks:
        return "No relevant articles found."

    context_parts = []
    seen_articles = set()

    for chunk in chunks:
        meta = chunk["metadata"]
        article_id = meta.get("article_id", "")
        title = meta.get("title", "Untitled")

        # Add article header only once per article
        # (Multiple chunks might come from the same article)
        if article_id not in seen_articles:
            seen_articles.add(article_id)
            header = f"\n---\nFrom: \"{title}\""
            if meta.get("created_at"):
                header += f" ({meta['created_at'][:10]})"  # Just the date part
            context_parts.append(header)

        context_parts.append(chunk["text"])

    return "\n".join(context_parts)


# =============================================================================
# STEP 4: QUERY THE LLM
# =============================================================================

def query_llm(
    question: str,
    context: str,
    system_prompt: Optional[str] = None
) -> str:
    """
    Send query to LM Studio (OpenAI-compatible API).

    This sends the context (article excerpts) plus your question to the LLM,
    which generates a response based on that context.

    LM Studio provides an API that works just like OpenAI's ChatGPT API,
    but runs locally on your computer.
    """
    # Default system prompt tells the AI how to behave
    if system_prompt is None:
        system_prompt = f"""You are {cfg.AUTHOR_NAME}'s AI assistant, helping to answer questions about their Medium articles.

IMPORTANT RULES:
1. Base your answers ONLY on the provided article excerpts
2. If the articles don't contain relevant information, say so
3. Quote specific passages when helpful
4. Maintain {cfg.AUTHOR_NAME}'s voice and perspective
5. Be concise but thorough"""

    # Format the messages for the chat API
    # "system": Instructions for the AI
    # "user": The actual question with context
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""Here are relevant excerpts from my Medium articles:

{context}

---

Question: {question}

Answer based on the article excerpts above:"""}
    ]

    try:
        # Call the LM Studio API (same format as OpenAI)
        response = requests.post(
            f"{cfg.LLM_BASE_URL}/chat/completions",
            json={
                "model": cfg.LLM_MODEL,
                "messages": messages,
                "temperature": cfg.LLM_TEMPERATURE,  # Controls creativity
                "max_tokens": cfg.LLM_MAX_TOKENS,    # Max response length
                "stream": False                       # Get complete response at once
            },
            headers={"Content-Type": "application/json"},
            timeout=120  # Wait up to 2 minutes for response
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to LM Studio. Make sure it's running on port 1234."
    except Exception as e:
        return f"Error querying LLM: {e}"


# =============================================================================
# INTERACTIVE CHAT MODE
# =============================================================================

def interactive_mode(collection, backend: str):
    """
    Run interactive chat mode.

    This is the main interface where you can have a conversation with your
    articles. Type questions and get answers grounded in your writing.
    """
    print("\n" + "=" * 60)
    print(f"RAG Chat with {cfg.AUTHOR_NAME}'s Medium Articles")
    print("=" * 60)
    print("Commands:")
    print("  /search <query>  - Search only, no LLM response")
    print("  /sources         - Show sources from last query")
    print("  /quit or /exit   - Exit")
    print("=" * 60 + "\n")

    last_chunks = []  # Remember last search results for /sources command

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Handle Ctrl+C or Ctrl+D gracefully
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Handle exit commands
        if user_input.lower() in ["/quit", "/exit", "quit", "exit"]:
            print("Goodbye!")
            break

        # Handle /search command (search without LLM response)
        if user_input.startswith("/search "):
            query = user_input[8:].strip()
            chunks = search_articles(query, collection, backend=backend)
            last_chunks = chunks

            if not chunks:
                print("No relevant articles found.")
            else:
                print(f"\nFound {len(chunks)} relevant chunks:\n")
                for i, chunk in enumerate(chunks, 1):
                    meta = chunk["metadata"]
                    print(f"{i}. [{chunk['similarity']:.2f}] {meta.get('title', 'Untitled')}")
                    print(f"   {chunk['text'][:200]}...")  # Preview first 200 chars
                    print()
            continue

        # Handle /sources command (show sources from last query)
        if user_input == "/sources":
            if not last_chunks:
                print("No previous search results.")
            else:
                print("\nSources from last query:")
                seen = set()
                for chunk in last_chunks:
                    meta = chunk["metadata"]
                    url = meta.get("url", "")
                    if url and url not in seen:
                        seen.add(url)
                        print(f"  - {meta.get('title', 'Untitled')}")
                        print(f"    {url}")
            continue

        # =======================================================================
        # REGULAR QUERY WITH RAG
        # =======================================================================
        # This is the main flow:
        # 1. Search for relevant chunks
        # 2. Format them as context
        # 3. Send to LLM for a response

        print("\nSearching articles...")
        chunks = search_articles(user_input, collection, backend=backend)
        last_chunks = chunks

        if not chunks:
            print("No relevant articles found for this query.")
            continue

        print(f"Found {len(chunks)} relevant chunks. Generating response...\n")

        # Build context from the retrieved chunks
        context = format_context(chunks)

        # Get LLM response
        response = query_llm(user_input, context)

        print(f"Assistant: {response}")

        # Show sources (article titles)
        print("\n[Sources]")
        seen = set()
        for chunk in chunks[:3]:  # Show top 3 sources
            meta = chunk["metadata"]
            title = meta.get("title", "Untitled")
            if title not in seen:
                seen.add(title)
                print(f"  - {title}")


# =============================================================================
# SINGLE QUERY MODE
# =============================================================================

def single_query(
    question: str,
    collection,
    backend: str,
    search_only: bool = False
) -> str:
    """
    Execute a single query and return the result.

    This is for non-interactive use (e.g., from command line or scripts).
    """
    chunks = search_articles(question, collection, backend=backend)

    if search_only:
        # Just return search results, no LLM response
        if not chunks:
            return "No relevant articles found."

        output = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk["metadata"]
            output.append(f"\n{i}. [{chunk['similarity']:.2f}] {meta.get('title', 'Untitled')}")
            output.append(f"   Date: {meta.get('created_at', 'Unknown')[:10]}")
            output.append(f"   {chunk['text'][:300]}...")
        return "\n".join(output)

    # Full RAG response
    if not chunks:
        return "No relevant articles found for this query."

    context = format_context(chunks)
    response = query_llm(question, context)
    return response


# =============================================================================
# MAIN SCRIPT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Query Medium articles with RAG")
    parser.add_argument(
        "query",
        nargs="?",
        help="Question to ask (omit for interactive mode)"
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="Search only, don't query LLM"
    )
    parser.add_argument(
        "--backend",
        choices=["ollama", "lmstudio", "sentence-transformers"],
        default=cfg.EMBEDDING_BACKEND,
        help="Embedding backend to use"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=cfg.TOP_K_RESULTS,
        help="Number of chunks to retrieve"
    )
    args = parser.parse_args()

    # ==========================================================================
    # LOAD THE VECTOR DATABASE
    # ==========================================================================

    # Check that the database exists
    if not cfg.CHROMA_DB_PATH.exists():
        print("Error: Vector database not found.")
        print("Run 'python embed_articles.py' first to build the database.")
        return

    # Connect to ChromaDB
    client = chromadb.PersistentClient(
        path=str(cfg.CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )

    # Get the collection (where our article chunks are stored)
    try:
        collection = client.get_collection(cfg.COLLECTION_NAME)
    except Exception:
        print("Error: Collection not found.")
        print("Run 'python embed_articles.py' first to build the database.")
        return

    count = collection.count()
    print(f"Loaded database with {count} chunks")

    # ==========================================================================
    # RUN QUERY
    # ==========================================================================

    if args.query:
        # Single query mode: just answer the question and exit
        result = single_query(
            args.query,
            collection,
            args.backend,
            search_only=args.search
        )
        print(result)
    else:
        # Interactive mode: continuous chat
        interactive_mode(collection, args.backend)


if __name__ == "__main__":
    main()
