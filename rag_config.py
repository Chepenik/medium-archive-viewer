"""
RAG Configuration for Medium Article Archive

=============================================================================
WHAT IS THIS FILE?
=============================================================================
This is the central configuration file for the AI/ML system. Think of it as
the "settings panel" where you control how all the AI components behave.

WHAT IS RAG?
RAG stands for "Retrieval Augmented Generation". It's a technique where:
1. You ask a question
2. The system searches your articles to find relevant passages
3. Those passages are sent to an AI along with your question
4. The AI answers based on YOUR actual writing (not just its general knowledge)

This prevents the AI from "hallucinating" (making stuff up) because it can
only reference content that actually exists in your articles.
=============================================================================
"""
from pathlib import Path

# =============================================================================
# PATHS - Where things are stored on your computer
# =============================================================================

# The folder where this file lives (automatically detected)
PROJECT_ROOT = Path(__file__).parent

# Finds all folders named "medium_archive_*" (where your articles are stored)
# Each folder contains JSON files, one per article
ARCHIVE_DIRS = sorted(PROJECT_ROOT.glob("medium_archive_*"))

# Where the vector database is stored (created by embed_articles.py)
# This is like a "searchable index" of all your articles
CHROMA_DB_PATH = PROJECT_ROOT / "chroma_db"

# Where training data is saved (created by prepare_medium_data.py)
DATASET_OUTPUT_DIR = PROJECT_ROOT / "my_medium_dataset"


# =============================================================================
# EMBEDDING SETTINGS - How we convert text into searchable numbers
# =============================================================================
#
# "Embeddings" are a way to convert text into a list of numbers (a "vector").
# Similar texts have similar numbers, which lets us search by meaning, not
# just exact word matches. For example:
#   - "Bitcoin is great" and "BTC is awesome" would have similar embeddings
#   - Even though they share no words, the AI understands they mean similar things
#
# We support three "backends" (services that create embeddings):
#   - "ollama": Free, runs locally, recommended for Mac
#   - "lmstudio": Also free and local, if you already have it running
#   - "sentence-transformers": Pure Python, no server needed, but slower
# =============================================================================

# Which embedding service to use (change this to switch backends)
EMBEDDING_BACKEND = "ollama"

# Ollama settings (recommended - install via `brew install ollama`)
# nomic-embed-text is a small, fast, high-quality embedding model
OLLAMA_MODEL = "nomic-embed-text"
OLLAMA_BASE_URL = "http://localhost:11434"

# LM Studio settings (alternative if you prefer LM Studio)
LMSTUDIO_EMBED_URL = "http://localhost:1234/v1/embeddings"
LMSTUDIO_EMBED_MODEL = "nomic-ai/nomic-embed-text-v1.5-GGUF"

# Sentence Transformers (fallback - pure Python, no server needed)
ST_MODEL = "nomic-ai/nomic-embed-text-v1.5"


# =============================================================================
# CHUNKING SETTINGS - How articles are split into searchable pieces
# =============================================================================
#
# AI models have limited "context windows" (how much text they can process).
# We can't send entire articles to the embedding model, so we split them
# into smaller "chunks". When you search, we find the most relevant chunks.
#
# Overlap ensures we don't cut off important context at chunk boundaries.
# Think of it like reading a book with your thumb covering the last few
# lines of the previous page - the overlap is that repeated section.
# =============================================================================

CHUNK_SIZE = 1000       # Characters per chunk (roughly 150-200 words)
CHUNK_OVERLAP = 200     # Characters to repeat between chunks (for context)
MIN_CHUNK_SIZE = 100    # Skip chunks smaller than this (probably not useful)


# =============================================================================
# RETRIEVAL SETTINGS - How many results to return when searching
# =============================================================================
#
# When you ask a question, we search for relevant chunks and return the top
# matches. More results = more context for the AI, but also more noise.
# The similarity threshold filters out low-quality matches.
# =============================================================================

TOP_K_RESULTS = 5           # Number of chunks to retrieve per query
SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score (0-1, higher = stricter)


# =============================================================================
# LLM SETTINGS - The AI that generates responses
# =============================================================================
#
# LLM = "Large Language Model" (like ChatGPT, but running locally)
# We use LM Studio which provides an OpenAI-compatible API, meaning any
# model you load in LM Studio can be used here automatically.
#
# Temperature controls "creativity":
#   - 0.0 = Very deterministic, same question gets same answer
#   - 1.0 = Very creative/random, answers vary wildly
#   - 0.7 = Good balance for conversational AI
# =============================================================================

LLM_BASE_URL = "http://localhost:1234/v1"  # LM Studio's API endpoint
LLM_MODEL = "local-model"   # LM Studio uses this generic name for whatever's loaded
LLM_TEMPERATURE = 0.7       # Creativity level (0.0 = robotic, 1.0 = chaotic)
LLM_MAX_TOKENS = 2048       # Maximum length of AI response


# =============================================================================
# CHROMADB COLLECTION - The "table name" for our vector database
# =============================================================================

COLLECTION_NAME = "medium_articles"


# =============================================================================
# FINE-TUNING SETTINGS - Training the AI on your writing style
# =============================================================================
#
# "Fine-tuning" takes a pre-trained AI model and teaches it YOUR specific
# writing style by training it on your articles. This is like hiring a
# ghostwriter and having them read everything you've ever written.
#
# We use "LoRA" (Low-Rank Adaptation) which is a memory-efficient technique
# that only trains a small portion of the model. This makes it possible to
# fine-tune on a laptop instead of needing expensive cloud GPUs.
#
# Key concepts:
#   - BASE_MODEL: The starting AI model (Phi-3.5-mini is 3.8 billion parameters)
#   - LORA_RANK: How much the model can learn (higher = more capacity, more memory)
#   - LEARNING_RATE: How fast the model learns (too high = unstable, too low = slow)
#   - BATCH_SIZE: How many examples to process at once (limited by RAM)
#   - MAX_STEPS: Total training iterations (more = better, but diminishing returns)
# =============================================================================

BASE_MODEL = "microsoft/Phi-3.5-mini-instruct"  # Starting model from Microsoft
LORA_RANK = 16              # LoRA adapter size (16 is good for personal use)
LORA_ALPHA = 32             # LoRA scaling factor (usually 2x the rank)
LEARNING_RATE = 1e-4        # How fast the model learns (0.0001)
BATCH_SIZE = 1              # Examples per training step (keep at 1 for 24GB RAM)
GRADIENT_ACCUMULATION = 4   # Simulates larger batches by accumulating gradients
MAX_STEPS = 1000            # Total training steps
WARMUP_STEPS = 50           # Gradual learning rate increase at start
EVAL_STEPS = 100            # How often to check model quality
SAVE_STEPS = 200            # How often to save checkpoints


# =============================================================================
# ORIGINALITY SCORING - Weighting training data by how "original" it is
# =============================================================================
#
# Not all articles are equally valuable for teaching your voice. An article
# that's just quotes from other people doesn't capture YOUR thinking.
#
# This scoring system identifies your most original content:
#   - quote_density: Articles with fewer quotes are more original
#   - link_density: Articles with fewer external links are more original
#   - first_person_ratio: Articles with more "I/my/me" show your personal voice
#   - entity_ratio: Articles mentioning fewer external people/companies
#   - narrative_score: Personal stories vs listicles/news summaries
#
# High-originality articles get higher training weights, meaning the AI
# pays more attention to them when learning your style.
# =============================================================================

ORIGINALITY_WEIGHTS = {
    "quote_density": 0.30,      # 30% weight - fewer quotes = more original
    "link_density": 0.20,       # 20% weight - fewer external links = more original
    "first_person_ratio": 0.20, # 20% weight - more "I/my/me" = more personal voice
    "entity_ratio": 0.15,       # 15% weight - fewer mentions of others = more original
    "narrative_score": 0.15,    # 15% weight - personal stories vs listicles
}
ORIGINALITY_ALPHA = 2.7  # Exponent that amplifies the effect of originality scores


# =============================================================================
# AUTHOR INFO - Your identity for the AI
# =============================================================================

AUTHOR_NAME = "Conor Chepenik"
STYLE_HINT = (
    f"You are {AUTHOR_NAME}. Use your authentic Medium style: "
    "concise, clear, no em dashes, Bitcoin-forward when relevant, "
    "headings where useful, and avoid fluff."
)
