#!/usr/bin/env python3
"""
Prepare Medium JSON archive for local fine-tuning with originality scoring.

=============================================================================
WHAT DOES THIS SCRIPT DO?
=============================================================================
This script converts your Medium articles into training data for AI fine-tuning.
Think of it like creating a "curriculum" to teach an AI your writing style.

THE PROCESS:
1. READ: Load all your articles from the JSON files
2. CLEAN: Normalize text, remove HTML, fix encoding issues
3. SCORE: Analyze each article for "originality" (how much it reflects YOUR voice)
4. FORMAT: Convert articles into instruction/response pairs the AI can learn from
5. SPLIT: Divide into training (90%) and validation (10%) sets
6. SAVE: Output files ready for MLX fine-tuning

WHY ORIGINALITY SCORING?
Not all articles are equally valuable for teaching your voice:
- An article that's mostly quotes from others doesn't teach YOUR style
- An article with lots of "I think" and personal stories is more valuable
- We give higher "training weight" to more original content

WHAT IS FINE-TUNING?
Pre-trained AI models (like GPT) know how to write, but not in YOUR voice.
Fine-tuning teaches a model YOUR specific writing patterns:
- Your vocabulary and phrases
- Your typical article structure
- Your opinions and perspectives
- Your tone (casual, formal, humorous, etc.)

=============================================================================

Usage:
    python prepare_medium_data.py --in_dir medium_archive_1 --out_dir my_medium_dataset
    python prepare_medium_data.py --all  # Process all medium_archive_* folders
"""
import argparse
import json
import re
import unicodedata
import glob
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from bs4 import BeautifulSoup  # HTML parsing library
from datasets import Dataset   # HuggingFace datasets library
from ftfy import fix_text      # Fixes text encoding issues
from tqdm import tqdm          # Progress bar library

import rag_config as cfg


# =============================================================================
# ORIGINALITY SCORING
# =============================================================================
#
# This section contains the logic for determining how "original" an article is.
# The idea: content that's uniquely YOURS should have higher training weight.
#
# We analyze several signals:
# - Quote density: More quotes = less original (you're citing others)
# - Link density: More links = less original (you're referencing others)
# - First-person pronouns: More "I/my/me" = more personal voice
# - External entities: More mentions of companies/people = less original
# - Narrative structure: Personal stories > listicles
# =============================================================================

# First-person pronouns that indicate personal voice
# When you use these words, you're expressing YOUR thoughts
FIRST_PERSON = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves"}

# Patterns that match external entities (people, companies, etc.)
# When you mention these a lot, you're talking about OTHERS, not your own ideas
ENTITY_PATTERNS = [
    r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # Named persons (e.g., "John Smith")
    r"\b(?:Google|Apple|Microsoft|Amazon|Facebook|Meta|Twitter|Tesla|OpenAI)\b",  # Big tech
    r"\b(?:Bitcoin|Ethereum|Solana)\b",  # Crypto (these are topics, but tracked)
]

# Patterns that identify quoted text (someone else's words)
QUOTE_PATTERNS = [
    r'"[^"]{20,}"',              # Regular quotes with 20+ characters
    r'\u201c[^\u201d]{20,}\u201d',  # "Smart quotes" (curly quotes)
    r'^\s*>\s*.+',               # Markdown blockquotes (> like this)
]

# Pattern to find URLs and markdown links
URL_PATTERN = r'https?://[^\s\)>\]]+|(?<!\[)\[.+?\]\(.+?\)'

# Patterns that indicate listicle-style content (less personal/narrative)
LISTICLE_PATTERNS = [
    r'^\s*\d+\.\s+',           # Numbered lists: "1. First item"
    r'^\s*[-*]\s+',            # Bullet points: "- Item" or "* Item"
    r'\b(?:top|best)\s+\d+\b', # "Top 10", "Best 5" style headlines
]


def compute_originality_score(text: str) -> Tuple[float, Dict[str, float]]:
    """
    Compute an originality score (0.0-1.0) for an article.

    HOW IT WORKS:
    We analyze the text for various signals and combine them into a score.
    Higher score = more original content = higher training weight.

    COMPONENTS:
    1. Quote score: 1.0 if no quotes, 0.0 if heavily quoted
    2. Link score: 1.0 if few links, 0.0 if link-heavy
    3. First-person score: 1.0 if lots of "I/my/me", 0.0 if none
    4. Entity score: 1.0 if focused on your ideas, 0.0 if mostly about others
    5. Narrative score: 1.0 for personal stories, 0.0 for pure listicles

    Returns:
        Tuple of (overall_score, breakdown_dict)
    """
    # Handle edge cases
    if not text or len(text) < 100:
        return 0.5, {}  # Default middle score for very short content

    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)  # Extract all words
    word_count = len(words) if words else 1     # Avoid division by zero

    # =========================================================================
    # COMPONENT 1: Quote Density (fewer quotes = more original)
    # =========================================================================
    # Find all quoted passages and calculate what percentage of the article
    # they represent. High quote density = low originality score.
    quote_matches = []
    for pattern in QUOTE_PATTERNS:
        quote_matches.extend(re.findall(pattern, text, re.MULTILINE))
    quote_chars = sum(len(q) for q in quote_matches)
    quote_density = min(quote_chars / len(text), 1.0)
    quote_score = 1.0 - quote_density  # Invert: low density = high score

    # =========================================================================
    # COMPONENT 2: Link Density (fewer links = more original)
    # =========================================================================
    # Count external links. Many links suggest the article is referencing
    # or summarizing other sources rather than presenting original thoughts.
    links = re.findall(URL_PATTERN, text)
    link_density = min(len(links) / (word_count / 100), 1.0)  # links per 100 words
    link_score = 1.0 - min(link_density / 3, 1.0)  # 3+ links per 100 words = 0

    # =========================================================================
    # COMPONENT 3: First-Person Ratio (more personal pronouns = more original)
    # =========================================================================
    # When you use "I", "my", "me", you're expressing YOUR perspective.
    # This is a strong signal of original, personal content.
    first_person_count = sum(1 for w in words if w in FIRST_PERSON)
    first_person_ratio = first_person_count / word_count
    # Normalize: 2%+ first-person usage = maximum score
    first_person_score = min(first_person_ratio / 0.02, 1.0)

    # =========================================================================
    # COMPONENT 4: External Entity Ratio (fewer mentions = more original)
    # =========================================================================
    # If you're constantly mentioning other people/companies, you might be
    # summarizing news or discussing others' work rather than your own ideas.
    entity_matches = []
    for pattern in ENTITY_PATTERNS:
        entity_matches.extend(re.findall(pattern, text))
    # Filter out first-person matches that might accidentally match patterns
    entities = [e for e in entity_matches if e.lower() not in FIRST_PERSON]
    entity_density = len(entities) / (word_count / 100)
    entity_score = 1.0 - min(entity_density / 5, 1.0)  # 5+ entities per 100 words = 0

    # =========================================================================
    # COMPONENT 5: Narrative Score (stories vs listicles)
    # =========================================================================
    # Personal essays and stories are more valuable for learning voice than
    # listicles like "Top 10 Ways to..." which are more formulaic.
    listicle_matches = []
    for pattern in LISTICLE_PATTERNS:
        listicle_matches.extend(re.findall(pattern, text, re.MULTILINE | re.IGNORECASE))
    listicle_density = len(listicle_matches) / (word_count / 100)
    narrative_score = 1.0 - min(listicle_density / 10, 1.0)  # 10+ list items = 0

    # =========================================================================
    # COMBINE COMPONENTS INTO OVERALL SCORE
    # =========================================================================
    # Each component has a weight defined in rag_config.py
    # The weights determine how much each signal matters
    weights = cfg.ORIGINALITY_WEIGHTS
    overall_score = (
        weights["quote_density"] * quote_score +
        weights["link_density"] * link_score +
        weights["first_person_ratio"] * first_person_score +
        weights["entity_ratio"] * entity_score +
        weights["narrative_score"] * narrative_score
    )

    # Return both the overall score and the breakdown for debugging
    components = {
        "quote_score": round(quote_score, 3),
        "link_score": round(link_score, 3),
        "first_person_score": round(first_person_score, 3),
        "entity_score": round(entity_score, 3),
        "narrative_score": round(narrative_score, 3),
    }

    return round(overall_score, 3), components


def compute_originality_weight(originality_score: float, alpha: float = cfg.ORIGINALITY_ALPHA) -> float:
    """
    Convert originality score to training weight.

    WHY QUADRATIC SCALING?
    We use score^2 to amplify the difference between high and low originality.
    An article with 0.8 originality gets much more weight than one with 0.4.

    The alpha multiplier (default 2.7) controls how aggressive this weighting is.
    Higher alpha = more emphasis on original content.

    EXAMPLE:
    - Score 0.9 → Weight = 2.7 * 0.81 = 2.19 (high weight)
    - Score 0.5 → Weight = 2.7 * 0.25 = 0.68 (low weight)
    """
    return alpha * (originality_score ** 2)


# =============================================================================
# TEXT PROCESSING - Clean up messy article text
# =============================================================================

def html_to_text(html: str) -> str:
    """
    Convert HTML to plain text.

    Some articles are stored with HTML formatting (<p>, <br>, etc.)
    We strip the HTML tags but preserve the text content.
    """
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    # Replace <br> tags with newlines
    for br in soup.find_all(["br"]):
        br.replace_with("\n")
    text = soup.get_text("\n")
    return text


def normalize_text(s: str) -> str:
    """
    Clean and normalize text.

    This fixes common text issues:
    - Broken Unicode characters (fix_text from ftfy)
    - Multiple spaces collapsed to single space
    - Multiple newlines collapsed to double newline
    - Leading/trailing whitespace removed
    """
    if not s:
        return ""
    s = fix_text(s)                          # Fix encoding issues
    s = unicodedata.normalize("NFKC", s)     # Normalize Unicode
    s = re.sub(r"[ \t]+", " ", s)            # Multiple spaces → single space
    s = re.sub(r"\n{3,}", "\n\n", s)         # 3+ newlines → 2 newlines
    return s.strip()


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file, handling both regular JSON and JSONL (line-delimited JSON).

    Some exports use one JSON object per file, others use one JSON object per line.
    This function handles both formats.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Try JSONL format (one JSON object per line)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [json.loads(x) for x in f if x.strip()]
            return {"_jsonl_list": lines}
        except Exception:
            return None


# =============================================================================
# ARTICLE EXTRACTION - Pull structured data from JSON
# =============================================================================

def coerce_post_record(it: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize an article record to a standard format.

    Different export formats have different field names. This function
    handles the variations and produces a consistent output format.

    The output includes originality scoring for training weighting.
    """
    try:
        # Extract basic fields (handling different naming conventions)
        title = it.get("title", "")
        subtitle = it.get("subtitle", "")
        raw_tags = it.get("tags", [])

        # Normalize tags (could be strings, dicts, or a single string)
        tags = []
        if isinstance(raw_tags, list):
            tags = [t["name"] if isinstance(t, dict) and "name" in t else str(t) for t in raw_tags]
        elif isinstance(raw_tags, str):
            tags = [raw_tags]

        # Try different date field names
        date = it.get("createdAt") or it.get("publishedAt") or it.get("date") or ""

        # Extract body content (trying various field names and formats)
        body = ""
        if isinstance(it.get("content"), str):
            body = it["content"]
        elif isinstance(it.get("content"), dict):
            html = it["content"].get("bodyHtml") or it["content"].get("subtitleHtml")
            if html:
                body = html_to_text(html)
            else:
                body = it["content"].get("text", "") or ""

        # More fallback options for body content
        if not body:
            body = it.get("content_html", "")
            if body:
                body = html_to_text(body)
        if not body:
            body = it.get("text", "") or it.get("markdown", "") or it.get("contentMarkdown", "")

        # Clean up all text fields
        title = normalize_text(title)
        subtitle = normalize_text(subtitle)
        body = normalize_text(body)

        # Skip articles that are too short (probably not useful for training)
        if not body or len(body) < 50:
            return None

        # =====================================================================
        # COMPUTE ORIGINALITY SCORE
        # =====================================================================
        # This is where we analyze how "original" this article is
        # and assign it a training weight
        originality_score, originality_components = compute_originality_score(body)
        originality_weight = compute_originality_weight(originality_score)

        return {
            "id": it.get("id", ""),
            "title": title,
            "subtitle": subtitle,
            "tags": tags,
            "date": str(date),
            "body": body,
            "url": it.get("url", ""),
            "word_count": it.get("wordCount", len(body.split())),
            "originality_score": originality_score,
            "originality_weight": round(originality_weight, 3),
            "originality_components": originality_components,
        }
    except Exception:
        return None


def extract_core_fields(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract articles from various JSON structures.

    Different export formats nest articles in different ways:
    - Top-level list
    - Under "posts", "items", "articles", "stories", or "data" keys
    - Single article object

    This function handles all these cases.
    """
    out = []

    # Handle JSONL format (list of objects)
    if "_jsonl_list" in obj and isinstance(obj["_jsonl_list"], list):
        for it in obj["_jsonl_list"]:
            p = coerce_post_record(it)
            if p:
                out.append(p)
        return out

    # Handle direct list of articles
    if isinstance(obj, list):
        for it in obj:
            p = coerce_post_record(it)
            if p:
                out.append(p)
        return out

    # Handle nested structures (articles under a key)
    for key in ["posts", "items", "articles", "stories", "data"]:
        if key in obj and isinstance(obj[key], list):
            for it in obj[key]:
                p = coerce_post_record(it)
                if p:
                    out.append(p)
            if out:
                return out

    # Try treating the whole object as a single article
    p = coerce_post_record(obj)
    if p:
        out.append(p)

    return out


# =============================================================================
# INSTRUCTION TEMPLATES - How we format training examples
# =============================================================================
#
# Fine-tuning works by showing the model examples of:
#   INPUT: "Write an article about Bitcoin"
#   OUTPUT: "[Your actual article about Bitcoin]"
#
# By seeing many of these pairs, the model learns your writing style.
# We use varied instruction templates to help the model generalize.
# =============================================================================

INSTRUCTION_TEMPLATES = [
    "Write an article in my voice about: {title}",
    "Create a Medium post titled: {title}",
    "Write in my authentic style on the topic: {title}",
    "Compose an article matching my tone: {title}",
    "Draft a piece for my Medium blog: {title}",
]

# For articles that get split into chunks, we use continuation prompts
CONTINUATION_TEMPLATES = [
    "Continue this article:\n\n{context}",
    "Write the next section of:\n\n{context}",
    "Complete this piece:\n\n{context}",
]


def chunk_text(text: str, max_chars: int = 1600, overlap: int = 200) -> List[str]:
    """
    Split long text into smaller chunks.

    WHY CHUNK?
    AI models have limited context windows. Very long articles might exceed
    what the model can process at once. We split them into chunks that the
    model can learn from individually.

    OVERLAP ensures context continuity between chunks.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text]  # Short enough, no chunking needed

    # Split on paragraph boundaries to keep related sentences together
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, cur = [], ""

    for p in paras:
        if not cur:
            cur = p
        elif len(cur) + 2 + len(p) <= max_chars:
            cur = cur + "\n\n" + p
        else:
            chunks.append(cur)
            cur = p

    if cur:
        chunks.append(cur)

    # Add overlap between chunks for context continuity
    if overlap > 0 and len(chunks) > 1:
        with_ov = []
        for i, ch in enumerate(chunks):
            if i == 0:
                with_ov.append(ch)
            else:
                prev_tail = chunks[i - 1][-overlap:]  # Last N chars of previous chunk
                with_ov.append((prev_tail + "\n" + ch).strip())
        chunks = with_ov

    return chunks


def build_examples(records: List[Dict], style_hint: str, max_chars: int, overlap: int) -> List[Dict]:
    """
    Build training examples from article records.

    WHAT IS A TRAINING EXAMPLE?
    It's an instruction/input/output triple that teaches the model:
    - "Here's what someone asked for" (instruction)
    - "Here's extra context" (input)
    - "Here's what you should produce" (output = your actual article)

    The model learns to produce outputs like yours when given similar inputs.
    """
    examples = []

    for r in records:
        title = r["title"]
        subtitle = r["subtitle"]
        tags = r["tags"]
        date = r["date"]
        body = r["body"]
        originality_weight = r["originality_weight"]

        # Build metadata line (helps model understand context)
        meta_parts = []
        if tags:
            meta_parts.append(f"Tags: {', '.join(tags)}")
        if date:
            meta_parts.append(f"Date: {date}")
        meta_line = " | ".join(meta_parts)

        # Randomly select an instruction template for variety
        template = random.choice(INSTRUCTION_TEMPLATES)
        instruction = template.format(title=title)

        # Build the input context (style hint + metadata)
        input_parts = [style_hint]
        if subtitle:
            input_parts.append(f"Subtitle: {subtitle}")
        if meta_line:
            input_parts.append(meta_line)
        input_text = "\n\n".join(input_parts)

        # Split article into chunks if needed
        chunks = chunk_text(body, max_chars=max_chars, overlap=overlap)

        if len(chunks) == 1:
            # Simple case: entire article fits in one example
            examples.append({
                "instruction": instruction,
                "input": input_text,
                "output": chunks[0],
                "originality_weight": originality_weight,
                "article_id": r.get("id", ""),
            })
        else:
            # Multi-part article: first chunk gets title instruction
            examples.append({
                "instruction": instruction,
                "input": input_text + f"\n\n(Part 1/{len(chunks)})",
                "output": chunks[0],
                "originality_weight": originality_weight,
                "article_id": r.get("id", ""),
            })

            # Subsequent chunks use continuation prompts
            for i, chunk in enumerate(chunks[1:], 2):
                cont_template = random.choice(CONTINUATION_TEMPLATES)
                prev_excerpt = chunks[i - 2][-300:]  # Context from previous chunk
                examples.append({
                    "instruction": cont_template.format(context=prev_excerpt),
                    "input": f"(Part {i}/{len(chunks)})",
                    "output": chunk,
                    "originality_weight": originality_weight,
                    "article_id": r.get("id", ""),
                })

    return examples


def format_for_mlx(example: Dict) -> Dict:
    """
    Format example for MLX-LM training.

    MLX-LM (the training framework) expects a specific format:
    {"text": "[full conversation]", "weight": [training weight]}

    We use Phi-3's chat format:
    <|user|>
    [instruction + input]<|end|>
    <|assistant|>
    [output]<|end|>

    This teaches the model to respond to user messages in your style.
    """
    instruction = example["instruction"]
    input_text = example["input"]
    output = example["output"]

    # Combine instruction and input for the user message
    if input_text:
        user_content = f"{instruction}\n\n{input_text}"
    else:
        user_content = instruction

    # Format as Phi-3 conversation (the model we're fine-tuning)
    text = f"<|user|>\n{user_content}<|end|>\n<|assistant|>\n{output}<|end|>"

    return {
        "text": text,
        "weight": example.get("originality_weight", 1.0),
    }


# =============================================================================
# MAIN SCRIPT
# =============================================================================

def main():
    # Set up command-line arguments
    ap = argparse.ArgumentParser(description="Prepare Medium archive for fine-tuning with originality scoring.")
    ap.add_argument("--in_dir", help="Folder containing Medium JSON files (recursively).")
    ap.add_argument("--all", action="store_true", help="Process all medium_archive_* folders.")
    ap.add_argument("--out_dir", default="my_medium_dataset", help="Output folder for datasets.")
    ap.add_argument("--preview_jsonl", default="medium_preview.jsonl", help="Write a preview JSONL.")
    ap.add_argument("--max_chars", type=int, default=1600)
    ap.add_argument("--overlap", type=int, default=200)
    ap.add_argument("--train_split", type=float, default=0.9, help="Train/validation split ratio.")
    ap.add_argument("--style_hint", default=cfg.STYLE_HINT)
    ap.add_argument("--show_originality", action="store_true", help="Show top/bottom originality articles.")
    args = ap.parse_args()

    # =========================================================================
    # DETERMINE INPUT DIRECTORIES
    # =========================================================================
    if args.all:
        in_dirs = list(cfg.ARCHIVE_DIRS)
    elif args.in_dir:
        in_dirs = [Path(args.in_dir)]
    else:
        in_dirs = list(cfg.ARCHIVE_DIRS)  # Default to all

    if not in_dirs:
        raise SystemExit("No input directories found. Use --in_dir or --all.")

    # =========================================================================
    # COLLECT ALL JSON FILES
    # =========================================================================
    json_files = []
    for in_dir in in_dirs:
        if not in_dir.exists():
            print(f"Warning: {in_dir} does not exist")
            continue
        json_files.extend([Path(p) for p in glob.glob(str(in_dir / "**" / "*.json"), recursive=True)])

    if not json_files:
        raise SystemExit("No .json files found")

    print(f"Found {len(json_files)} JSON files across {len(in_dirs)} directories")

    # =========================================================================
    # LOAD ALL ARTICLES
    # =========================================================================
    all_records = []
    for jf in tqdm(json_files, desc="Reading JSON"):
        obj = load_json(jf)
        if not obj:
            continue
        posts = extract_core_fields(obj)
        all_records.extend(posts)

    # =========================================================================
    # DE-DUPLICATE ARTICLES
    # =========================================================================
    # Same article might exist in multiple exports
    seen, deduped = set(), []
    for r in all_records:
        # Create a signature from title, date, and first 80 chars of body
        sig = (r.get("title", "").lower(), r.get("date", ""), (r.get("body", "")[:80]).lower())
        if sig not in seen:
            seen.add(sig)
            deduped.append(r)

    print(f"Loaded {len(deduped)} unique articles")

    # =========================================================================
    # SHOW ORIGINALITY ANALYSIS
    # =========================================================================
    # This helps you understand which articles will get the most training weight
    if args.show_originality or True:  # Always show
        sorted_by_orig = sorted(deduped, key=lambda x: x["originality_score"], reverse=True)

        print("\n" + "=" * 60)
        print("TOP 10 MOST ORIGINAL ARTICLES (highest training weight)")
        print("=" * 60)
        for r in sorted_by_orig[:10]:
            print(f"  [{r['originality_score']:.2f}] {r['title'][:60]}")

        print("\n" + "=" * 60)
        print("TOP 10 LEAST ORIGINAL ARTICLES (lowest training weight)")
        print("=" * 60)
        for r in sorted_by_orig[-10:]:
            print(f"  [{r['originality_score']:.2f}] {r['title'][:60]}")

        # Show distribution statistics
        scores = [r["originality_score"] for r in deduped]
        avg_score = sum(scores) / len(scores)
        print(f"\nOriginality Distribution:")
        print(f"  Average: {avg_score:.3f}")
        print(f"  Min: {min(scores):.3f}, Max: {max(scores):.3f}")

    # =========================================================================
    # BUILD TRAINING EXAMPLES
    # =========================================================================
    examples = build_examples(deduped, args.style_hint, args.max_chars, args.overlap)

    if not examples:
        raise SystemExit("No examples produced. Check the article format.")

    print(f"\nGenerated {len(examples)} training examples")

    # =========================================================================
    # SPLIT INTO TRAIN/VALIDATION
    # =========================================================================
    # Validation set is used to check if the model is overfitting
    # (memorizing training data rather than learning patterns)
    random.shuffle(examples)
    split_idx = int(len(examples) * args.train_split)
    train_examples = examples[:split_idx]
    valid_examples = examples[split_idx:]

    print(f"Train: {len(train_examples)}, Validation: {len(valid_examples)}")

    # =========================================================================
    # SAVE OUTPUT FILES
    # =========================================================================
    out_dir = Path(args.out_dir)
    out_dir.mkdir(exist_ok=True)

    # Write MLX-LM format (train.jsonl, valid.jsonl)
    # This is what the fine-tuning script reads
    train_path = out_dir / "train.jsonl"
    valid_path = out_dir / "valid.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for ex in train_examples:
            mlx_ex = format_for_mlx(ex)
            f.write(json.dumps(mlx_ex, ensure_ascii=False) + "\n")

    with open(valid_path, "w", encoding="utf-8") as f:
        for ex in valid_examples:
            mlx_ex = format_for_mlx(ex)
            f.write(json.dumps(mlx_ex, ensure_ascii=False) + "\n")

    print(f"MLX format: {train_path}, {valid_path}")

    # Write preview file (first 100 examples in original format for inspection)
    with open(args.preview_jsonl, "w", encoding="utf-8") as f:
        for ex in examples[:100]:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    # Save HuggingFace Dataset format (alternative format)
    ds = Dataset.from_list(examples)
    ds.save_to_disk(out_dir / "hf_dataset")
    print(f"HuggingFace format: {out_dir / 'hf_dataset'}")

    # Save originality weights for reference
    weights_path = out_dir / "originality_weights.json"
    weights_data = {
        ex["article_id"]: ex["originality_weight"]
        for ex in examples
        if ex.get("article_id")
    }
    with open(weights_path, "w", encoding="utf-8") as f:
        json.dump(weights_data, f, indent=2)
    print(f"Weights: {weights_path}")

    print(f"\nDataset ready for training!")


if __name__ == "__main__":
    main()
