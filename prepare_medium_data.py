import argparse, json, re, unicodedata, glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datasets import Dataset
from ftfy import fix_text
from tqdm import tqdm

# ---------- helpers ----------

def html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for br in soup.find_all(["br"]):
        br.replace_with("\n")
    text = soup.get_text("\n")
    return text

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = fix_text(s)
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    # Try normal JSON
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Try JSONL fallback
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [json.loads(x) for x in f if x.strip()]
            return {"_jsonl_list": lines}
        except Exception:
            return None

# ---------- core extraction for your schema ----------

def coerce_post_record(it: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize to:
      { title, subtitle, tags, date, body }
    Designed for your Medium JSON:
      - title: string
      - createdAt: string
      - tags: [string]
      - url: string (not used in training but handy metadata)
      - content: Markdown string (FULL BODY)
    Also supports a few other common shapes.
    """
    try:
        title = (
            it.get("title")
            or (it.get("content", {}) if isinstance(it.get("content"), dict) else None)
            or ""
        )

        # subtitle: not present in your sample, leave empty
        subtitle = it.get("subtitle", "")

        # tags
        raw_tags = it.get("tags", [])
        tags = []
        if isinstance(raw_tags, list):
            tags = [t["name"] if isinstance(t, dict) and "name" in t else str(t) for t in raw_tags]
        elif isinstance(raw_tags, str):
            tags = [raw_tags]

        # date
        date = it.get("createdAt") or it.get("publishedAt") or it.get("date") or ""

        # ----- BODY extraction -----
        body = ""

        # 1) Your schema: content is a big Markdown string
        if isinstance(it.get("content"), str):
            body = it["content"]

        # 2) If content has HTML (other exports)
        if not body and isinstance(it.get("content"), dict):
            html = it["content"].get("bodyHtml") or it["content"].get("subtitleHtml")
            if html:
                body = html_to_text(html)
            else:
                # Sometimes text key exists
                body = it["content"].get("text", "") or ""

        # 3) Fallbacks
        if not body:
            body = it.get("content_html", "")  # some exports use this
            if body:
                body = html_to_text(body)
        if not body:
            body = it.get("text", "") or it.get("markdown", "") or it.get("contentMarkdown", "")

        title = normalize_text(title)
        subtitle = normalize_text(subtitle)
        body = normalize_text(body)

        if not body or len(body) < 50:  # skip tiny/empty
            return None

        return {
            "title": title,
            "subtitle": subtitle,
            "tags": tags,
            "date": str(date),
            "body": body,
        }
    except Exception:
        return None

def extract_core_fields(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    # JSONL wrapper
    if "_jsonl_list" in obj and isinstance(obj["_jsonl_list"], list):
        for it in obj["_jsonl_list"]:
            p = coerce_post_record(it)
            if p: out.append(p)
        return out

    # If it's a list of posts
    if isinstance(obj, list):
        for it in obj:
            p = coerce_post_record(it)
            if p: out.append(p)
        return out

    # Known collection keys
    for key in ["posts", "items", "articles", "stories", "data"]:
        if key in obj and isinstance(obj[key], list):
            for it in obj[key]:
                p = coerce_post_record(it)
                if p: out.append(p)
            if out:
                return out

    # Single post object
    p = coerce_post_record(obj)
    if p:
        out.append(p)

    return out

def chunk_text(text: str, max_chars: int = 1600, overlap: int = 200) -> List[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
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
    if overlap > 0 and len(chunks) > 1:
        with_ov = []
        for i, ch in enumerate(chunks):
            if i == 0:
                with_ov.append(ch)
            else:
                prev_tail = chunks[i-1][-overlap:]
                with_ov.append((prev_tail + "\n" + ch).strip())
        chunks = with_ov
    return chunks

def build_examples(records, style_hint, max_chars, overlap):
    ex = []
    for r in records:
        title, subtitle, tags, date, body = r["title"], r["subtitle"], r["tags"], r["date"], r["body"]
        meta_line = " | ".join(filter(None, [
            f"Title: {title}" if title else "",
            f"Subtitle: {subtitle}" if subtitle else "",
            f"Tags: {', '.join(tags)}" if tags else "",
            f"Date: {date}" if date else "",
        ])).strip()

        instruction = "Write in my voice and structure, matching tone, rhythm, and formatting."
        if title:
            inp = f"{style_hint}\n\nTarget title: {title}\n{('Details: ' + subtitle) if subtitle else ''}\n{('Meta: ' + meta_line) if meta_line else ''}\n"
        else:
            inp = f"{style_hint}\n\nMeta: {meta_line}\n"

        chunks = chunk_text(body, max_chars=max_chars, overlap=overlap)
        if len(chunks) == 1:
            ex.append({"instruction": instruction, "input": inp.strip(), "output": chunks[0].strip()})
        else:
            for i, ch in enumerate(chunks, 1):
                ex.append({"instruction": instruction, "input": (inp + f"\nChunk {i}/{len(chunks)}").strip(), "output": ch.strip()})
    return ex

def main():
    ap = argparse.ArgumentParser(description="Prepare Medium JSON archive for local SFT (Conor schema).")
    ap.add_argument("--in_dir", required=True, help="Folder containing Medium JSON files (recursively).")
    ap.add_argument("--out_dir", default="my_medium_dataset", help="Output folder for save_to_disk.")
    ap.add_argument("--preview_jsonl", default="medium_preview.jsonl", help="Write a preview JSONL.")
    ap.add_argument("--max_chars", type=int, default=1600)
    ap.add_argument("--overlap", type=int, default=200)
    ap.add_argument("--style_hint", default="You are Conor Chepenik. Use your authentic Medium style: concise, clear, no em dashes, Bitcoin-forward when relevant, headings where useful, and avoid fluff.")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    if not in_dir.exists():
        raise SystemExit(f"Input folder not found: {in_dir}")

    json_files = [Path(p) for p in glob.glob(str(in_dir / "**" / "*.json"), recursive=True)]
    if not json_files:
        raise SystemExit(f"No .json files found under {in_dir}")

    all_records = []
    for jf in tqdm(json_files, desc="Reading JSON"):
        obj = load_json(jf)
        if not obj:
            continue
        posts = extract_core_fields(obj)
        all_records.extend(posts)

    # de-dupe by (title, date, first 80 chars)
    seen, deduped = set(), []
    for r in all_records:
        sig = (r.get("title","").lower(), r.get("date",""), (r.get("body","")[:80]).lower())
        if sig not in seen:
            seen.add(sig)
            deduped.append(r)

    examples = build_examples(deduped, args.style_hint, args.max_chars, args.overlap)
    if not examples:
        raise SystemExit("No examples produced. Likely a schema mismatch—ping me and we’ll adapt in 1 min.")

    with open(args.preview_jsonl, "w", encoding="utf-8") as f:
        for ex in examples[:20000]:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    ds = Dataset.from_list(examples)
    ds.save_to_disk(args.out_dir)
    print(f"✅ Dataset saved to '{args.out_dir}' with {len(ds)} examples.")
    print(f"👀 Preview written to '{args.preview_jsonl}'.")

if __name__ == "__main__":
    main()
