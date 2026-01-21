#!/usr/bin/env python3
"""
Embed Medium articles into ChromaDB for RAG (Retrieval Augmented Generation).

=============================================================================
WHAT DOES THIS SCRIPT DO?
=============================================================================
This script reads all your Medium articles and converts them into a searchable
database. Here's the process:

1. LOAD ARTICLES: Read all JSON files from your medium_archive_* folders
2. CHUNK: Split each article into smaller pieces (about 200 words each)
3. EMBED: Convert each chunk into a list of numbers (a "vector embedding")
4. STORE: Save everything in ChromaDB, a vector database

WHY DO WE NEED EMBEDDINGS?
Traditional search looks for exact word matches. But what if you search for
"cryptocurrency" and your article says "Bitcoin"? Exact search would miss it.

Embeddings solve this by converting text to numbers that capture MEANING.
Similar concepts have similar numbers, so "cryptocurrency" and "Bitcoin"
would be close together in the embedding space.

WHEN TO RUN THIS:
- First time setup: Run once to build the initial database
- After adding new articles: Run again (it only processes new content)
- If you want to start fresh: Run with --reset flag

=============================================================================

Usage:
    python embed_articles.py [--backend ollama|lmstudio|sentence-transformers]

Prerequisites:
    - pip install chromadb requests
    - For ollama: brew install ollama && ollama pull nomic-embed-text
    - For sentence-transformers: pip install sentence-transformers
"""
import argparse
import json
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm  # Progress bar library

import chromadb
from chromadb.config import Settings

import rag_config as cfg


# =============================================================================
# STEP 1: LOAD ARTICLES FROM DISK
# =============================================================================

def load_articles() -> List[Dict[str, Any]]:
    """
    Load all articles from archive directories.

    This function:
    1. Finds all folders named "medium_archive_*"
    2. Opens every .json file in those folders
    3. Returns a list of article dictionaries

    Each article has fields like: id, title, content, tags, createdAt, url
    """
    articles = []

    # Loop through each archive folder (medium_archive_1, medium_archive_2, etc.)
    for archive_dir in cfg.ARCHIVE_DIRS:
        if not archive_dir.exists():
            continue

        # Find all JSON files in this folder
        for json_file in archive_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    article = json.load(f)
                    # Remember which file this came from (for debugging)
                    article["_source_file"] = str(json_file)
                    articles.append(article)
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")

    return articles


# =============================================================================
# STEP 2: CHUNK TEXT INTO SMALLER PIECES
# =============================================================================

def chunk_text(text: str, chunk_size: int = cfg.CHUNK_SIZE,
               overlap: int = cfg.CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks.

    WHY CHUNK?
    - AI models have limited "context windows" (how much they can read at once)
    - Smaller chunks are more precise for search
    - Overlap ensures we don't lose context at boundaries

    EXAMPLE:
    If chunk_size=100 and overlap=20, a 200-character text might become:
    - Chunk 1: characters 0-100
    - Chunk 2: characters 80-180 (20 chars overlap with chunk 1)
    - Chunk 3: characters 160-200 (20 chars overlap with chunk 2)

    The overlap means if an important sentence spans two chunks,
    it will still be fully contained in at least one of them.
    """
    # Skip empty or very short texts
    if not text or len(text) < cfg.MIN_CHUNK_SIZE:
        return []

    # First, try to split on paragraph boundaries (double newlines)
    # This keeps related sentences together
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if not current_chunk:
            # Starting a new chunk
            current_chunk = para
        elif len(current_chunk) + len(para) + 2 <= chunk_size:
            # Paragraph fits in current chunk, add it
            current_chunk = current_chunk + "\n\n" + para
        else:
            # Paragraph doesn't fit, save current chunk and start new one
            if len(current_chunk) >= cfg.MIN_CHUNK_SIZE:
                chunks.append(current_chunk)

            # Start new chunk with some overlap from the previous chunk
            # This ensures continuity of context
            overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
            current_chunk = (overlap_text + "\n\n" + para).strip()

    # Don't forget the last chunk!
    if current_chunk and len(current_chunk) >= cfg.MIN_CHUNK_SIZE:
        chunks.append(current_chunk)

    # Handle case where text doesn't have paragraph breaks
    # (Fall back to simple character-based chunking)
    if not chunks and len(text) >= cfg.MIN_CHUNK_SIZE:
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if len(chunk) >= cfg.MIN_CHUNK_SIZE:
                chunks.append(chunk)

    return chunks


# =============================================================================
# STEP 3: GENERATE EMBEDDINGS (Convert text to numbers)
# =============================================================================
#
# These functions call different services to convert text into "embeddings"
# (lists of ~768 numbers that represent the meaning of the text).
#
# The magic: texts with similar meanings have similar number patterns.
# =============================================================================

def get_embedding_ollama(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings from Ollama (local AI service).

    Ollama is a free, local AI runner. We use its 'nomic-embed-text' model
    which is specifically designed for creating text embeddings.

    Install: brew install ollama && ollama pull nomic-embed-text
    Run: ollama serve (in a terminal)
    """
    embeddings = []
    for text in texts:
        # Call Ollama's API endpoint
        response = requests.post(
            f"{cfg.OLLAMA_BASE_URL}/api/embeddings",
            json={"model": cfg.OLLAMA_MODEL, "prompt": text}
        )
        response.raise_for_status()  # Raise error if request failed
        embeddings.append(response.json()["embedding"])
    return embeddings


def get_embedding_lmstudio(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings from LM Studio (alternative local AI).

    LM Studio is a desktop app for running AI models locally.
    It provides an OpenAI-compatible API on port 1234.
    """
    response = requests.post(
        cfg.LMSTUDIO_EMBED_URL,
        json={"model": cfg.LMSTUDIO_EMBED_MODEL, "input": texts},
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    data = response.json()
    return [item["embedding"] for item in data["data"]]


def get_embedding_st(texts: List[str], model=None) -> List[List[float]]:
    """
    Get embeddings from sentence-transformers (pure Python, no server).

    This is the fallback option that doesn't require any external service.
    It's slower but works anywhere Python runs.
    """
    from sentence_transformers import SentenceTransformer
    if model is None:
        model = SentenceTransformer(cfg.ST_MODEL, trust_remote_code=True)
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def get_embeddings(texts: List[str], backend: str, model=None) -> List[List[float]]:
    """
    Get embeddings using the specified backend.

    This is a "router" function that calls the appropriate embedding service
    based on which backend you've configured.
    """
    if backend == "ollama":
        return get_embedding_ollama(texts)
    elif backend == "lmstudio":
        return get_embedding_lmstudio(texts)
    elif backend == "sentence-transformers":
        return get_embedding_st(texts, model)
    else:
        raise ValueError(f"Unknown backend: {backend}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_chunk_id(article_id: str, chunk_idx: int) -> str:
    """
    Create a unique ID for each chunk.

    Example: "abc123_chunk_0", "abc123_chunk_1", etc.
    This helps us track which chunks belong to which article.
    """
    return f"{article_id}_chunk_{chunk_idx}"


# =============================================================================
# MAIN SCRIPT
# =============================================================================

def main():
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description="Embed Medium articles into ChromaDB")
    parser.add_argument(
        "--backend",
        choices=["ollama", "lmstudio", "sentence-transformers"],
        default=cfg.EMBEDDING_BACKEND,
        help="Embedding backend to use (default: ollama)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Number of chunks to embed at once (default: 32)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing database and start fresh"
    )
    args = parser.parse_args()

    print(f"Using embedding backend: {args.backend}")

    # If using sentence-transformers, load the model once upfront
    # (Loading is slow, so we reuse the same model for all embeddings)
    st_model = None
    if args.backend == "sentence-transformers":
        from sentence_transformers import SentenceTransformer
        print(f"Loading model: {cfg.ST_MODEL}")
        st_model = SentenceTransformer(cfg.ST_MODEL, trust_remote_code=True)

    # ==========================================================================
    # INITIALIZE CHROMADB (Vector Database)
    # ==========================================================================
    # ChromaDB is a database specifically designed for storing embeddings.
    # It lets us quickly find which chunks are most similar to a search query.

    cfg.CHROMA_DB_PATH.mkdir(exist_ok=True)  # Create folder if it doesn't exist

    client = chromadb.PersistentClient(
        path=str(cfg.CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False)  # Don't send usage data
    )

    # Handle --reset flag (delete and recreate the collection)
    if args.reset:
        try:
            client.delete_collection(cfg.COLLECTION_NAME)
            print("Deleted existing collection")
        except Exception:
            pass  # Collection didn't exist, that's fine

    # Get or create the collection (like a "table" in a regular database)
    # "cosine" distance means we measure similarity by the angle between vectors
    collection = client.get_or_create_collection(
        name=cfg.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # Check what's already in the database (so we don't duplicate work)
    existing_ids = set(collection.get()["ids"])
    print(f"Collection has {len(existing_ids)} existing chunks")

    # ==========================================================================
    # LOAD AND PROCESS ARTICLES
    # ==========================================================================

    articles = load_articles()
    print(f"Found {len(articles)} articles across {len(cfg.ARCHIVE_DIRS)} archive folders")

    # Prepare batches of chunks to embed
    all_chunks = []      # The actual text content
    all_ids = []         # Unique IDs for each chunk
    all_metadatas = []   # Extra info (title, tags, date, etc.)

    # Process each article
    for article in tqdm(articles, desc="Chunking articles"):
        article_id = article.get("id", "")
        title = article.get("title", "")
        content = article.get("content", "")
        tags = article.get("tags", [])
        created_at = article.get("createdAt", "")
        url = article.get("url", "")

        if not content:
            continue

        # Prepend the title to the content for better context
        # This way, searches for the title will also find relevant chunks
        full_text = f"# {title}\n\n{content}" if title else content
        chunks = chunk_text(full_text)

        for idx, chunk in enumerate(chunks):
            chunk_id = create_chunk_id(article_id, idx)

            # Skip if we've already embedded this chunk
            if chunk_id in existing_ids:
                continue

            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadatas.append({
                "article_id": article_id,
                "title": title,
                "tags": ", ".join(tags) if tags else "",
                "created_at": created_at,
                "url": url,
                "chunk_index": idx,
                "total_chunks": len(chunks)
            })

    # If nothing new to embed, we're done!
    if not all_chunks:
        print("No new chunks to embed")
        return

    print(f"Embedding {len(all_chunks)} new chunks...")

    # ==========================================================================
    # EMBED AND STORE IN BATCHES
    # ==========================================================================
    # We process chunks in batches to:
    # 1. Show progress (tqdm progress bar)
    # 2. Handle errors gracefully (one bad batch doesn't kill everything)
    # 3. Avoid overwhelming the embedding service with too many requests

    for i in tqdm(range(0, len(all_chunks), args.batch_size), desc="Embedding"):
        batch_chunks = all_chunks[i:i + args.batch_size]
        batch_ids = all_ids[i:i + args.batch_size]
        batch_metadatas = all_metadatas[i:i + args.batch_size]

        try:
            # Convert text chunks to embeddings (lists of numbers)
            embeddings = get_embeddings(batch_chunks, args.backend, st_model)

            # Store in ChromaDB
            # - ids: Unique identifier for each chunk
            # - embeddings: The vector representation (for searching)
            # - documents: The original text (returned in search results)
            # - metadatas: Extra info like title, date, URL
            collection.add(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_chunks,
                metadatas=batch_metadatas
            )
        except Exception as e:
            print(f"Error embedding batch {i}: {e}")
            continue

    # ==========================================================================
    # DONE!
    # ==========================================================================

    final_count = collection.count()
    print(f"\nEmbedding complete!")
    print(f"Total chunks in database: {final_count}")
    print(f"Database location: {cfg.CHROMA_DB_PATH}")


if __name__ == "__main__":
    main()
