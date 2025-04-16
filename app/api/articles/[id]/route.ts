import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const filePath = path.join(process.cwd(), 'medium_archive', `${params.id}.json`);
    
    if (!fs.existsSync(filePath)) {
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