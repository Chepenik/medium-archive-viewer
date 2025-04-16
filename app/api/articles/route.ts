import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const dataDir = path.join(process.cwd(), 'medium_archive');
    if (!fs.existsSync(dataDir)) {
      return NextResponse.json({ error: 'No articles found' }, { status: 404 });
    }

    const files = fs.readdirSync(dataDir);
    const articles = files
      .filter(file => file.endsWith('.json'))
      .map(file => {
        const content = fs.readFileSync(path.join(dataDir, file), 'utf-8');
        return JSON.parse(content);
      })
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    return NextResponse.json(articles);
  } catch (error) {
    console.error('Error reading articles:', error);
    return NextResponse.json(
      { error: 'Failed to read articles' },
      { status: 500 }
    );
  }
} 