import { NextResponse } from 'next/server';
import { NextRequest } from 'next/server';
import fs from 'fs';
import path from 'path';

// Cache for article metadata (excludes content for performance)
let cachedArticles: any[] | null = null;
let cacheTimestamp: number = 0;
const CACHE_TTL = 60 * 1000; // 1 minute cache

// Find all medium_archive_* folders
function getArchiveFolders(): string[] {
  const cwd = process.cwd();
  const entries = fs.readdirSync(cwd);
  return entries
    .filter(entry => entry.startsWith('medium_archive_'))
    .map(entry => path.join(cwd, entry))
    .filter(folderPath => fs.statSync(folderPath).isDirectory());
}

// Load all articles (with caching)
function loadArticles(): any[] {
  const now = Date.now();

  if (cachedArticles && (now - cacheTimestamp) < CACHE_TTL) {
    return cachedArticles;
  }

  const archiveFolders = getArchiveFolders();
  const articles: any[] = [];

  for (const dataDir of archiveFolders) {
    const files = fs.readdirSync(dataDir);
    for (const file of files) {
      if (file.endsWith('.json')) {
        try {
          const content = fs.readFileSync(path.join(dataDir, file), 'utf-8');
          const article = JSON.parse(content);
          // Exclude content field for list view (saves bandwidth)
          const { content: _, ...articleMeta } = article;
          articles.push(articleMeta);
        } catch (e) {
          console.error(`Error reading ${file}:`, e);
        }
      }
    }
  }

  // Sort by date (newest first)
  articles.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

  cachedArticles = articles;
  cacheTimestamp = now;

  return articles;
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '20', 10);
    const offset = parseInt(searchParams.get('offset') || '0', 10);

    const allArticles = loadArticles();

    if (allArticles.length === 0) {
      return NextResponse.json({
        articles: [],
        total: 0,
        hasMore: false
      });
    }

    // Apply pagination
    const paginatedArticles = allArticles.slice(offset, offset + limit);
    const hasMore = offset + limit < allArticles.length;

    return NextResponse.json({
      articles: paginatedArticles,
      total: allArticles.length,
      hasMore,
    });
  } catch (error) {
    console.error('Error reading articles:', error);
    return NextResponse.json(
      { error: 'Failed to read articles' },
      { status: 500 }
    );
  }
}
