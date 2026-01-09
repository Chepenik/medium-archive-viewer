import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Find all medium_archive_* folders
function getArchiveFolders(): string[] {
  const cwd = process.cwd();
  const entries = fs.readdirSync(cwd);
  return entries
    .filter(entry => entry.startsWith('medium_archive_'))
    .map(entry => path.join(cwd, entry))
    .filter(folderPath => fs.statSync(folderPath).isDirectory());
}

export async function GET() {
  try {
    const archiveFolders = getArchiveFolders();

    if (archiveFolders.length === 0) {
      return NextResponse.json({ error: 'No articles found' }, { status: 404 });
    }

    const articles: any[] = [];

    for (const dataDir of archiveFolders) {
      const files = fs.readdirSync(dataDir);
      for (const file of files) {
        if (file.endsWith('.json')) {
          try {
            const content = fs.readFileSync(path.join(dataDir, file), 'utf-8');
            articles.push(JSON.parse(content));
          } catch (e) {
            console.error(`Error reading ${file}:`, e);
          }
        }
      }
    }

    articles.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    return NextResponse.json(articles);
  } catch (error) {
    console.error('Error reading articles:', error);
    return NextResponse.json(
      { error: 'Failed to read articles' },
      { status: 500 }
    );
  }
} 