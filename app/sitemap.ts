import { MetadataRoute } from 'next';
import { promises as fs } from 'fs';
import path from 'path';

async function getArticleIds(): Promise<string[]> {
  const articleIds: string[] = [];
  const baseDir = process.cwd();

  // Read from all medium_archive_* directories
  const entries = await fs.readdir(baseDir, { withFileTypes: true });
  const archiveDirs = entries
    .filter(entry => entry.isDirectory() && entry.name.startsWith('medium_archive_'))
    .map(entry => entry.name);

  for (const dir of archiveDirs) {
    const dirPath = path.join(baseDir, dir);
    const files = await fs.readdir(dirPath);
    const jsonFiles = files.filter(f => f.endsWith('.json'));

    for (const file of jsonFiles) {
      const id = file.replace('.json', '');
      articleIds.push(id);
    }
  }

  return articleIds;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://chepsblog.com';

  // Get all article IDs
  const articleIds = await getArticleIds();

  // Generate article URLs
  const articleUrls = articleIds.map((id) => ({
    url: `${baseUrl}/article/${id}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.7,
  }));

  return [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    ...articleUrls,
  ];
}
