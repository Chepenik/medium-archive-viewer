#!/usr/bin/env python3
"""
Conor AI - Unified CLI for Medium Article AI System

=============================================================================
WHAT IS THIS?
=============================================================================
This is the "command center" for your personal AI writing assistant.
Instead of remembering multiple scripts, you can do everything through
this single interface.

WHAT CAN IT DO?
1. CHAT: Have a conversation grounded in your 1,400+ articles (RAG)
2. SEARCH: Find relevant articles by topic
3. GENERATE: Create new content in your writing style
4. TRAIN: Fine-tune an AI model on your writing

HOW IT WORKS:
This script is basically a "traffic controller" that calls the other
scripts in the right way. It's much easier than remembering all the
individual commands.

=============================================================================

Commands:
    python conor_ai.py chat              # RAG-enhanced conversation with your articles
    python conor_ai.py generate "topic"  # Generate new content in your style
    python conor_ai.py search "query"    # Search articles directly
    python conor_ai.py train             # Run fine-tuning
    python conor_ai.py embed             # Build/update embeddings
    python conor_ai.py prepare           # Prepare training data
    python conor_ai.py status            # Show system status

Examples:
    python conor_ai.py chat
    python conor_ai.py search "Bitcoin mining"
    python conor_ai.py generate "Why I'm optimistic about 2025"
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import rag_config as cfg


# =============================================================================
# STATUS CHECK
# =============================================================================
# This shows you what's set up and what's missing

def get_status() -> dict:
    """
    Get system status information.

    Checks:
    - How many article folders exist
    - How many articles are in the archive
    - Whether embeddings have been built (for search/chat)
    - Whether training data has been prepared
    - Whether a fine-tuned model exists
    """
    status = {
        "archive_folders": len(list(cfg.ARCHIVE_DIRS)),
        "total_articles": 0,
        "embeddings_ready": cfg.CHROMA_DB_PATH.exists(),
        "embeddings_count": 0,
        "training_data_ready": (cfg.DATASET_OUTPUT_DIR / "train.jsonl").exists(),
        "training_examples": 0,
        "fine_tuned_model": (cfg.PROJECT_ROOT / "fine_tuned_model" / "adapters").exists(),
    }

    # Count total articles across all archive folders
    for archive_dir in cfg.ARCHIVE_DIRS:
        if archive_dir.exists():
            status["total_articles"] += len(list(archive_dir.glob("*.json")))

    # Count embeddings (if database exists)
    if status["embeddings_ready"]:
        try:
            import chromadb
            from chromadb.config import Settings
            client = chromadb.PersistentClient(
                path=str(cfg.CHROMA_DB_PATH),
                settings=Settings(anonymized_telemetry=False)
            )
            collection = client.get_collection(cfg.COLLECTION_NAME)
            status["embeddings_count"] = collection.count()
        except Exception:
            pass

    # Count training examples (if data exists)
    if status["training_data_ready"]:
        train_file = cfg.DATASET_OUTPUT_DIR / "train.jsonl"
        with open(train_file) as f:
            status["training_examples"] = sum(1 for _ in f)

    return status


def print_status():
    """
    Print formatted status.

    This gives you a quick overview of what's ready and what
    steps you need to take next.
    """
    status = get_status()

    print("\n" + "=" * 60)
    print(f"  CONOR AI - System Status")
    print("=" * 60)

    # Archive status
    print(f"\n  Archive:")
    print(f"    Folders: {status['archive_folders']}")
    print(f"    Articles: {status['total_articles']}")

    # RAG system status (for search and chat)
    print(f"\n  RAG System:")
    ready = "Ready" if status["embeddings_ready"] else "Not built"
    print(f"    Embeddings: {ready}")
    if status["embeddings_count"]:
        print(f"    Chunks: {status['embeddings_count']}")

    # Training system status
    print(f"\n  Training:")
    ready = "Ready" if status["training_data_ready"] else "Not prepared"
    print(f"    Data: {ready}")
    if status["training_examples"]:
        print(f"    Examples: {status['training_examples']}")

    model = "Available" if status["fine_tuned_model"] else "Not trained"
    print(f"    Fine-tuned model: {model}")

    print("\n" + "=" * 60)

    # Helpful suggestions based on current state
    print("\n  Next steps:")
    if not status["embeddings_ready"]:
        print("    1. Build embeddings: python conor_ai.py embed")
    elif not status["training_data_ready"]:
        print("    1. Prepare data: python conor_ai.py prepare")
    elif not status["fine_tuned_model"]:
        print("    1. Fine-tune model: python conor_ai.py train")
    else:
        print("    System ready! Try: python conor_ai.py chat")

    print()


# =============================================================================
# COMMAND HANDLERS
# =============================================================================
# Each function below handles one of the CLI commands by calling the
# appropriate underlying script.

def run_embed(args):
    """
    Build article embeddings.

    This converts all your articles into searchable vectors.
    Required before using chat or search.

    Calls: embed_articles.py
    """
    cmd = [sys.executable, "embed_articles.py"]

    # Pass through backend option if specified
    if hasattr(args, "backend") and args.backend:
        cmd.extend(["--backend", args.backend])

    # Pass through reset flag if specified
    if hasattr(args, "reset") and args.reset:
        cmd.append("--reset")

    subprocess.run(cmd, cwd=str(cfg.PROJECT_ROOT))


def run_prepare(args):
    """
    Prepare training data.

    This processes your articles and creates the training files
    that the fine-tuning script needs.

    Calls: prepare_medium_data.py --all
    """
    cmd = [sys.executable, "prepare_medium_data.py", "--all"]
    subprocess.run(cmd, cwd=str(cfg.PROJECT_ROOT))


def run_train(args):
    """
    Run fine-tuning.

    This trains an AI model on your writing style.
    Requires: training data (run 'prepare' first)
    Takes: 30-60 minutes on Apple Silicon

    Calls: finetune_mlx.py
    """
    cmd = [sys.executable, "finetune_mlx.py"]

    # Pass through options if specified
    if hasattr(args, "steps") and args.steps:
        cmd.extend(["--steps", str(args.steps)])
    if hasattr(args, "resume") and args.resume:
        cmd.append("--resume")

    subprocess.run(cmd, cwd=str(cfg.PROJECT_ROOT))


def run_search(query: str, top_k: int = 5):
    """
    Search articles.

    Finds articles relevant to your query using semantic search.
    (Not just keyword matching - it understands meaning!)

    Calls: query_articles.py --search
    """
    cmd = [sys.executable, "query_articles.py", "--search", query, "--top-k", str(top_k)]
    subprocess.run(cmd, cwd=str(cfg.PROJECT_ROOT))


def run_chat():
    """
    Start interactive chat.

    This is the main feature - have a conversation where the AI
    answers based on YOUR articles. Great for:
    - "What have I written about Bitcoin?"
    - "What's my opinion on remote work?"
    - "Find my article about that startup I worked at"

    Calls: query_articles.py
    """
    cmd = [sys.executable, "query_articles.py"]
    subprocess.run(cmd, cwd=str(cfg.PROJECT_ROOT))


def run_generate(topic: str):
    """
    Generate content using fine-tuned model or RAG.

    Creates new content in your writing style on a given topic.

    If you have a fine-tuned model: Uses MLX to generate directly
    If not: Uses LM Studio with RAG context for style guidance
    """
    import requests

    # Check if we have a fine-tuned model
    fine_tuned_path = cfg.PROJECT_ROOT / "fine_tuned_model" / "adapters"

    if fine_tuned_path.exists():
        # =======================================================================
        # OPTION 1: Use the fine-tuned model (best quality)
        # =======================================================================
        # If you've trained a model, it knows your style directly
        try:
            from mlx_lm import load, generate

            print("Loading fine-tuned model...")
            model, tokenizer = load(
                cfg.BASE_MODEL,
                adapter_path=str(fine_tuned_path),
            )

            # Format prompt for Phi-3
            prompt = f"<|user|>\n{cfg.STYLE_HINT}\n\nWrite an article about: {topic}<|end|>\n<|assistant|>\n"

            print(f"\nGenerating article about: {topic}\n")
            print("-" * 60)

            response = generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=1500,
                temp=0.7,
            )

            print(response)
            print("-" * 60)
            return

        except ImportError:
            print("MLX not available, falling back to LM Studio...")

    # =======================================================================
    # OPTION 2: Use LM Studio with RAG (fallback)
    # =======================================================================
    # If no fine-tuned model, we use RAG to provide style context
    print(f"Generating article about: {topic}")
    print("(Using LM Studio with RAG context)\n")

    # Get relevant context from your articles
    import chromadb
    from chromadb.config import Settings

    if not cfg.CHROMA_DB_PATH.exists():
        print("No embeddings found. Run: python conor_ai.py embed")
        return

    client = chromadb.PersistentClient(
        path=str(cfg.CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )

    try:
        collection = client.get_collection(cfg.COLLECTION_NAME)
    except Exception:
        print("Collection not found. Run: python conor_ai.py embed")
        return

    # Search for relevant context
    from query_articles import get_query_embedding, format_context

    query_embedding = get_query_embedding(topic, cfg.EMBEDDING_BACKEND)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        include=["documents", "metadatas"]
    )

    # Build context from search results
    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i]
        })

    context = format_context(chunks) if chunks else ""

    # Create prompt with your style guidelines and example content
    system_prompt = f"""You are {cfg.AUTHOR_NAME}. Write a Medium article in your authentic voice.

Your style characteristics:
- Concise and clear
- No em dashes
- Bitcoin-forward when relevant
- Use headings where useful
- Avoid fluff
- Personal anecdotes welcome

Here are excerpts from your previous articles for reference:
{context}

Now write a NEW article about the requested topic. Don't just summarize the excerpts - use them as style reference only."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Write an article about: {topic}"}
    ]

    # Send to LM Studio
    try:
        response = requests.post(
            f"{cfg.LLM_BASE_URL}/chat/completions",
            json={
                "model": cfg.LLM_MODEL,
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 2000,
            },
            timeout=120
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        print("-" * 60)
        print(content)
        print("-" * 60)

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to LM Studio.")
        print("Make sure LM Studio is running on port 1234.")
    except Exception as e:
        print(f"Error: {e}")


# =============================================================================
# MAIN CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Conor AI - Chat with your Medium articles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__  # Use the docstring at the top as help text
    )

    # Create subcommands (chat, search, generate, etc.)
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # STATUS command - show system status
    status_parser = subparsers.add_parser("status", help="Show system status")

    # CHAT command - interactive RAG chat
    chat_parser = subparsers.add_parser("chat", help="Interactive RAG chat")

    # SEARCH command - search articles
    search_parser = subparsers.add_parser("search", help="Search articles")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results")

    # GENERATE command - create new content
    gen_parser = subparsers.add_parser("generate", help="Generate content in your style")
    gen_parser.add_argument("topic", help="Topic to write about")

    # EMBED command - build embeddings
    embed_parser = subparsers.add_parser("embed", help="Build article embeddings")
    embed_parser.add_argument("--backend", choices=["ollama", "lmstudio", "sentence-transformers"],
                              default=cfg.EMBEDDING_BACKEND)
    embed_parser.add_argument("--reset", action="store_true", help="Rebuild from scratch")

    # PREPARE command - prepare training data
    prep_parser = subparsers.add_parser("prepare", help="Prepare training data")

    # TRAIN command - fine-tune model
    train_parser = subparsers.add_parser("train", help="Fine-tune model")
    train_parser.add_argument("--steps", type=int, help="Training steps")
    train_parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")

    args = parser.parse_args()

    # If no command specified, show help and status
    if args.command is None:
        parser.print_help()
        print("\n" + "=" * 60)
        print_status()
        return

    # Route to the appropriate handler
    if args.command == "status":
        print_status()
    elif args.command == "chat":
        run_chat()
    elif args.command == "search":
        run_search(args.query, args.top_k)
    elif args.command == "generate":
        run_generate(args.topic)
    elif args.command == "embed":
        run_embed(args)
    elif args.command == "prepare":
        run_prepare(args)
    elif args.command == "train":
        run_train(args)


if __name__ == "__main__":
    main()
