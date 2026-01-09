# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A personal Medium article archive with two main components:
1. **Next.js Web Viewer** - Displays archived Medium articles with search and dark mode
2. **Archive Sync Script** - Fetches articles from Medium via the Unofficial Medium API (RapidAPI)

## Common Commands

```bash
# Development
npm run dev          # Start Next.js dev server (http://localhost:3000)
npm run build        # Build for production
npm run lint         # Run ESLint

# Sync articles from Medium
node syncMediumArchive.js   # Requires .env with MEDIUM_API_KEY and MEDIUM_USERNAME

# Prepare data for ML fine-tuning (requires Python venv)
python prepare_medium_data.py --in_dir medium_archive --out_dir my_medium_dataset
```

## Architecture

### Data Flow
- `syncMediumArchive.js` fetches articles from Medium API → saves JSON files to `medium_archive_*/` folders
- Next.js API routes read from all `medium_archive_*/` folders → serve to frontend
- Articles stored as individual JSON files distributed across folders (max 900 per folder for GitHub performance)
- When syncing, new articles auto-save to the first folder with room, or create a new folder

### Key Files
- `app/page.tsx` - Home page with article grid, search, and tag filtering
- `app/article/[id]/page.tsx` - Individual article view with markdown rendering
- `app/api/articles/route.ts` - Lists all articles (reads from filesystem)
- `app/api/articles/[id]/route.ts` - Fetches single article by ID
- `syncMediumArchive.js` - Medium API sync script (Node.js, uses axios)
- `prepare_medium_data.py` - Converts archive to HuggingFace Dataset for fine-tuning

### Article JSON Schema
```json
{
  "id": "string",
  "title": "string",
  "createdAt": "ISO date",
  "tags": ["string"],
  "url": "Medium URL",
  "content": "Markdown string",
  "wordCount": "number",
  "readingTime": "number",
  "claps": "number",
  "voters": "number"
}
```

## Environment Variables

Copy `.env.example` to `.env` and set:
- `MEDIUM_API_KEY` - RapidAPI key for medium2.p.rapidapi.com
- `MEDIUM_USERNAME` - Medium username to archive

## Tech Stack
- Next.js 14 (App Router)
- React 18, TypeScript
- Tailwind CSS, next-themes (dark mode)
- react-markdown for article rendering
- date-fns for date formatting
