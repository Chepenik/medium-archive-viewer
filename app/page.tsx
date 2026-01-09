'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { format, differenceInDays, parseISO } from 'date-fns';
import { ThemeToggle } from './components/ThemeToggle';

interface Article {
  id: string;
  title: string;
  createdAt: string;
  tags: string[];
  url: string;
  content: string;
  wordCount?: number;
  readingTime?: number;
}

function estimateReadingTime(content: string): number {
  const wordsPerMinute = 200;
  const words = content.trim().split(/\s+/).length;
  const minutes = Math.round(words / wordsPerMinute);
  return minutes < 1 ? 1 : minutes;
}

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

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

  const filteredArticles = useMemo(() => {
    return articles.filter(article => {
      const matchesSearch = searchQuery === '' ||
        article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        article.content.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesTag = !selectedTag || article.tags.includes(selectedTag);
      return matchesSearch && matchesTag;
    });
  }, [articles, searchQuery, selectedTag]);

  const allTags = useMemo(() => {
    const tagCounts = new Map<string, number>();
    articles.forEach(article => {
      article.tags.forEach(tag => {
        tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
      });
    });
    return Array.from(tagCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 12);
  }, [articles]);

  // Calculate the writing streak
  const stats = useMemo(() => {
    if (articles.length === 0) return null;

    const sortedDates = articles
      .map(a => parseISO(a.createdAt))
      .sort((a, b) => a.getTime() - b.getTime());

    const firstDate = sortedDates[0];
    const lastDate = sortedDates[sortedDates.length - 1];
    const totalDays = differenceInDays(lastDate, firstDate) + 1;

    const totalWords = articles.reduce((sum, a) => {
      return sum + (a.wordCount || a.content.trim().split(/\s+/).length);
    }, 0);

    return {
      totalArticles: articles.length,
      totalDays,
      firstDate,
      lastDate,
      totalWords,
    };
  }, [articles]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-text-secondary font-body">Loading the archive...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="text-center max-w-md px-6">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="font-heading text-xl mb-2">Something went wrong</h2>
        <p className="text-text-secondary">{error}</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="flex justify-between items-start gap-4">
            <div className="min-w-0 flex-1">
              <h1 className="font-heading text-4xl sm:text-5xl tracking-tight mb-3 bg-gradient-to-r from-orange-500 to-amber-500 dark:from-orange-400 dark:to-amber-400 bg-clip-text text-transparent">
                Chep's Blog
              </h1>
              <p className="text-text-secondary text-lg italic">
                "I've decided to write everyday for the rest of my life or until Medium goes out of business."
              </p>
            </div>
            <div className="shrink-0">
              <ThemeToggle />
            </div>
          </div>

          {/* Mission Statement */}
          <div className="mt-8 p-6 bg-bg-secondary rounded-lg border-l-4 border-accent">
            <p className="text-text leading-relaxed">
              After years of daily writing on Medium, I figured it was time to back up this archive in case they ever go out of business.
              More than a backup, I hope this serves as a <span className="text-accent font-medium">digital legacy</span>.
              As AI and LLMs continue to evolve, perhaps my children and their children will be able to have conversations with their ancestors through these words.
            </p>
            {stats && (
              <div className="mt-4 pt-4 border-t border-border">
                <span className="font-heading text-2xl text-accent">{stats.totalArticles.toLocaleString()}</span>
                <span className="text-text-secondary ml-2">articles archived and counting</span>
              </div>
            )}
          </div>

          {/* Search */}
          <div className="mt-8">
            <div className="relative">
              <input
                type="text"
                placeholder="Search the archive..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-3 pl-12 bg-bg-secondary border border-border rounded-lg
                         text-text placeholder:text-text-muted
                         focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent
                         transition-colors duration-200"
              />
              <svg
                className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-text-muted"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            {/* Tags */}
            {allTags.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedTag(null)}
                  className={`px-3 py-1.5 text-sm rounded-full transition-colors duration-200
                    ${!selectedTag
                      ? 'bg-accent text-white'
                      : 'bg-bg-secondary text-text-secondary hover:text-text hover:bg-border'
                    }`}
                >
                  All
                </button>
                {allTags.map(([tag, count]) => (
                  <button
                    key={tag}
                    onClick={() => setSelectedTag(selectedTag === tag ? null : tag)}
                    className={`px-3 py-1.5 text-sm rounded-full transition-colors duration-200
                      ${selectedTag === tag
                        ? 'bg-accent text-white'
                        : 'bg-bg-secondary text-text-secondary hover:text-text hover:bg-border'
                      }`}
                  >
                    {tag}
                    <span className="ml-1.5 opacity-60">{count}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Article List */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        {filteredArticles.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-text-secondary">No articles found matching your search.</p>
          </div>
        ) : (
          <>
            <div className="text-text-secondary text-sm mb-6">
              {filteredArticles.length === articles.length
                ? `${articles.length} articles in the archive`
                : `${filteredArticles.length} of ${articles.length} articles`
              }
            </div>

            <div className="space-y-1 stagger-children">
              {filteredArticles.map((article) => (
                <ArticleRow key={article.id} article={article} />
              ))}
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16">
        <div className="max-w-4xl mx-auto px-6 py-8 text-center text-text-muted text-sm">
          <p className="mb-2">
            Writing is good for the soul.
          </p>
          <p className="text-xs opacity-75">
            Everything divided by 21 million.
          </p>
        </div>
      </footer>
    </div>
  );
}

function ArticleRow({ article }: { article: Article }) {
  const rawTime = article.readingTime || estimateReadingTime(article.content);
  const readingTime = Math.max(1, Math.round(rawTime));

  return (
    <Link
      href={`/article/${article.id}`}
      className="group block py-5 border-b border-border/50 hover:border-border transition-colors duration-200"
    >
      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2">
        <h2 className="font-heading text-xl group-hover:text-accent transition-colors duration-200">
          {article.title}
        </h2>
        <div className="flex items-center gap-4 text-sm text-text-muted shrink-0">
          <time dateTime={article.createdAt}>
            {format(new Date(article.createdAt), 'MMM d, yyyy')}
          </time>
          <span>{readingTime} min read</span>
        </div>
      </div>

      {article.tags.length > 0 && (
        <div className="flex gap-2 mt-2">
          {article.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="text-xs text-text-muted"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
