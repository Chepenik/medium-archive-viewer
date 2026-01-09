import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Find article in any medium_archive_* folder
function findArticle(articleId: string): string | null {
  const cwd = process.cwd();
  const entries = fs.readdirSync(cwd);
  const archiveFolders = entries.filter(entry => entry.startsWith('medium_archive_'));

  for (const folder of archiveFolders) {
    const filePath = path.join(cwd, folder, `${articleId}.json`);
    if (fs.existsSync(filePath)) {
      return filePath;
    }
  }

  return null;
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const filePath = findArticle(id);

    if (!filePath) {
      return NextResponse.json({ error: 'Article not found' }, { status: 404 });
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const article = JSON.parse(content);

    return NextResponse.json(article);
  } catch (error) {
    console.error('Error reading article:', error);
    return NextResponse.json(
      { error: 'Failed to read article' },
      { status: 500 }
    );
  }
}
