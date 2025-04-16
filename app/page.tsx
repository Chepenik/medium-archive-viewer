'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import { ThemeToggle } from './components/ThemeToggle';

interface Article {
  id: string;
  title: string;
  createdAt: string;
  tags: string[];
  url: string;
  content: string;
}

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const response = await fetch('/api/articles');
        if (!response.ok) throw new Error('Failed to fetch articles');
        const data = await response.json();
        setArticles(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, []);

  if (loading) return <div className="p-8 text-center">Loading...</div>;
  if (error) return <div className="p-8 text-center text-red-500">Error: {error}</div>;

  return (
    <div className="min-h-screen transition-colors duration-200">
      <header className="border-b border-gray-200 dark:border-gray-800 transition-colors duration-200">
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold transition-colors duration-200">Conor Chepenik&apos;s Medium Archive</h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400 transition-colors duration-200">
                Personal archive of the Binmucker who writes on Medium every day because writing is good for the soul!! 
                <br />
                Everything divided by 21 million.
              </p>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid gap-6">
          {articles.map((article) => (
            <article
              key={article.id}
              className="border border-gray-200 dark:border-gray-800 rounded-lg p-6 
                         hover:shadow-lg transition-all duration-200 
                         bg-white dark:bg-gray-800"
            >
              <Link href={`/article/${article.id}`}>
                <h2 className="text-xl font-semibold mb-2 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-200">
                  {article.title}
                </h2>
              </Link>
              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 transition-colors duration-200 mb-4">
                <time dateTime={article.createdAt}>
                  {format(new Date(article.createdAt), 'MMMM d, yyyy')}
                </time>
                {article.tags.length > 0 && (
                  <div className="flex gap-2 flex-wrap">
                    {article.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 bg-gray-100 dark:bg-gray-700 
                                 text-gray-700 dark:text-gray-300 rounded-full text-xs
                                 transition-colors duration-200"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <p className="text-gray-700 dark:text-gray-300 line-clamp-3 transition-colors duration-200">
                {article.content.substring(0, 200)}...
              </p>
              <div className="mt-4">
                <Link
                  href={`/article/${article.id}`}
                  className="text-blue-600 dark:text-blue-400 hover:underline transition-colors duration-200"
                >
                  Read more →
                </Link>
              </div>
            </article>
          ))}
        </div>
      </main>
    </div>
  );
}
