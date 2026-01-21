# Chep's Blog - Medium Archive

A personal archive of 1,400+ articles from my [Medium](https://medium.com/@chepenikconor) writing journey.

**Live site:** [chepsblog.com](https://chepsblog.com)

## Why This Exists

I made a commitment to write every day for the rest of my life, or until Medium goes out of business. After years of keeping that promise, I built this archive as a backup and a digital legacy.

Platforms come and go. Servers crash. Policies change. This archive ensures my thoughts live on in a format I control.

## About the Live Site

Due to the large number of articles (1,400+), the live site loads **20 articles at a time** for performance. Click "Load More" to see additional articles.

**Want to browse all articles?** Clone this repo and run it locally:

```bash
git clone https://github.com/Chepenik/medium-archive-viewer.git
cd medium-archive-viewer
npm install
npm run dev
```

Then visit `http://localhost:3000`

---

## AI-Powered Writing Assistant

This repo also includes a complete AI system for:
1. **Chatting with your articles** (RAG - Retrieval Augmented Generation)
2. **Fine-tuning a model on your writing style** (MLX on Apple Silicon)
3. **Generating new content in your voice**

### Quick Start (AI Features)

```bash
# Install Python dependencies
pip install -r requirements-ml.txt

# Install Ollama for embeddings (Mac)
brew install ollama
ollama pull nomic-embed-text

# Build the searchable database (one-time)
python3 conor_ai.py embed

# Start chatting with your articles!
python3 conor_ai.py chat
```

### How It Works

**RAG (Retrieval Augmented Generation):**
1. Your articles are converted to "embeddings" (numerical representations)
2. When you ask a question, we find the most relevant article passages
3. Those passages are sent to an LLM along with your question
4. The LLM answers based on YOUR actual writing, not hallucinated content

**Fine-Tuning (Optional):**
1. Prepare training data: `python3 conor_ai.py prepare`
2. Train on Apple Silicon: `python3 conor_ai.py train`
3. The model learns YOUR vocabulary, opinions, and writing patterns

### AI Commands

| Command | Description |
|---------|-------------|
| `python3 conor_ai.py status` | Show system status |
| `python3 conor_ai.py chat` | Interactive chat with your articles |
| `python3 conor_ai.py search "query"` | Search articles semantically |
| `python3 conor_ai.py generate "topic"` | Generate content in your style |
| `python3 conor_ai.py embed` | Build/update article embeddings |
| `python3 conor_ai.py prepare` | Prepare fine-tuning data |
| `python3 conor_ai.py train` | Fine-tune model on your writing |

### AI System Files

| File | Purpose |
|------|---------|
| `conor_ai.py` | Unified CLI (start here) |
| `rag_config.py` | All configuration settings |
| `embed_articles.py` | Convert articles to searchable vectors |
| `query_articles.py` | Search + chat interface |
| `prepare_medium_data.py` | Prepare training data with originality scoring |
| `finetune_mlx.py` | Apple Silicon fine-tuning with LoRA |
| `requirements-ml.txt` | Python dependencies for AI features |

### Originality Scoring

Not all articles are equal for training. The system scores each article by:
- **Quote density** - Fewer quotes = more original
- **Link density** - Fewer external links = more original
- **First-person ratio** - More "I/my/me" = more personal voice
- **Entity mentions** - Fewer mentions of others = more original
- **Narrative structure** - Personal stories > listicles

High-originality articles get more weight during training, helping the AI focus on content that truly represents YOUR voice.

### Requirements for AI Features

- **Python 3.11+**
- **Mac with Apple Silicon** (for fine-tuning) or any Mac/Linux (for RAG only)
- **16GB+ RAM recommended** (24GB ideal for fine-tuning)
- **LM Studio** (optional, for local LLM inference)
- **Ollama** (recommended for embeddings)

---

## What's Included

- Full archive of 1,400+ Medium articles
- Search functionality to find specific posts
- Metadata: publish date, reading time, tags
- Raw content stored in JSON format
- AI-powered chat and search
- Fine-tuning pipeline for personalized AI

## Tech Stack

**Web Viewer:**
- **Next.js 16** - React framework
- **Tailwind CSS** - Styling
- **Node.js sync script** - Pulls articles via [Unofficial Medium API](https://mediumapi.com)

**AI System:**
- **MLX** - Apple Silicon ML framework
- **ChromaDB** - Vector database for RAG
- **Ollama** - Local embedding service
- **LM Studio** - Local LLM inference
- **Phi-3.5-mini** - Base model for fine-tuning

## Keeping It Updated

The sync script fetches new articles I publish:

```bash
node syncMediumArchive.js
```

After syncing, rebuild embeddings:

```bash
python3 conor_ai.py embed
```

## Folder Structure

```
medium-archive-viewer/
├── app/                      # Next.js app (web viewer)
├── medium_archive_1/         # Articles (JSON files)
├── medium_archive_2/         # More articles
├── conor_ai.py              # AI CLI (start here)
├── rag_config.py            # AI configuration
├── embed_articles.py        # Embedding script
├── query_articles.py        # RAG query interface
├── prepare_medium_data.py   # Training data prep
├── finetune_mlx.py          # MLX fine-tuning
├── syncMediumArchive.js     # Medium API sync
└── requirements-ml.txt      # Python dependencies
```

Articles are organized in `medium_archive_*/` folders (max 900 files per folder for GitHub compatibility).

## Contact

- X/Twitter: [@ConorChepenik](https://x.com/ConorChepenik)
- LinkedIn: [conorchepenik](https://www.linkedin.com/in/conorchepenik/)

---

> You don't need permission to own your words.
