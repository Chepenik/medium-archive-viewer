'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import { ThemeToggle } from './components/ThemeToggle';

interface Article {
  id: string;
  title: string;
  createdAt: string;
  tags: string[];
  url: string;
  wordCount?: number;
  readingTime?: number;
}

interface ApiResponse {
  articles: Article[];
  total: number;
  hasMore: boolean;
}

const ARTICLES_PER_PAGE = 20;

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const fetchArticles = async (offset: number = 0, append: boolean = false) => {
    try {
      if (append) setLoadingMore(true);

      const response = await fetch(`/api/articles?limit=${ARTICLES_PER_PAGE}&offset=${offset}`);
      if (!response.ok) throw new Error('Failed to fetch articles');
      const data: ApiResponse = await response.json();

      if (append) {
        setArticles(prev => [...prev, ...data.articles]);
      } else {
        setArticles(data.articles);
      }
      setTotal(data.total);
      setHasMore(data.hasMore);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    fetchArticles(0, false);
  }, []);

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      fetchArticles(articles.length, true);
    }
  };

  const filteredArticles = useMemo(() => {
    return articles.filter(article => {
      const matchesSearch = searchQuery === '' ||
        article.title.toLowerCase().includes(searchQuery.toLowerCase());
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
          <div className="flex justify-between items-start gap-6">
            <div className="min-w-0 flex-1 pr-4">
              <h1 className="font-heading text-4xl sm:text-5xl tracking-tight mb-3 bg-gradient-to-r from-orange-500 to-amber-500 dark:from-orange-400 dark:to-amber-400 bg-clip-text text-transparent inline-block">
                Chep's Blog
              </h1>
              <p className="text-text-secondary text-lg italic">
                "It is the mark of an educated mind to be able to entertain a thought without accepting it." — Aristotle
              </p>
            </div>
            <div className="shrink-0 pt-1">
              <ThemeToggle />
            </div>
          </div>

          {/* Mission Statement */}
          <div className="mt-8 p-6 bg-bg-secondary rounded-lg border-l-4 border-accent">
            <p className="text-text leading-relaxed">
              I made a commitment to write every day for the rest of my life, or until Medium goes out of business. After years of keeping that promise, I built this archive as a backup and a <span className="text-accent font-medium">digital legacy</span>. As AI continues to evolve, I hope my children and their children will be able to have conversations with their ancestors through these words.
            </p>
            <div className="mt-4 pt-4 border-t border-border">
              <span className="font-heading text-2xl text-accent">{total.toLocaleString()}</span>
              <span className="text-text-secondary ml-2">articles archived and counting</span>
            </div>
          </div>

          {/* Search */}
          <div className="mt-8">
            <div className="relative">
              <input
                type="text"
                placeholder="Search loaded articles..."
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
              Showing {articles.length} of {total.toLocaleString()} articles
              {searchQuery && ` (${filteredArticles.length} match "${searchQuery}")`}
            </div>

            <div className="space-y-1">
              {filteredArticles.map((article) => (
                <ArticleRow key={article.id} article={article} />
              ))}
            </div>

            {/* Load More Button */}
            {hasMore && !searchQuery && !selectedTag && (
              <div className="mt-8 text-center">
                <button
                  onClick={loadMore}
                  disabled={loadingMore}
                  className="px-6 py-3 bg-accent text-white rounded-lg font-medium
                           hover:bg-accent-hover transition-colors duration-200
                           disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingMore ? (
                    <span className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Loading...
                    </span>
                  ) : (
                    `Load More Articles`
                  )}
                </button>
                <p className="text-text-muted text-sm mt-2">
                  {total - articles.length} more articles available
                </p>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="flex flex-col items-center gap-6">
            {/* Social Links */}
            <div className="flex items-center gap-6">
              <a
                href="https://github.com/Chepenik/medium-archive-viewer"
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-muted hover:text-text transition-colors"
                aria-label="GitHub"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
              </a>
              <a
                href="https://x.com/ConorChepenik"
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-muted hover:text-text transition-colors"
                aria-label="X (Twitter)"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
              <a
                href="https://www.linkedin.com/in/conorchepenik/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-muted hover:text-text transition-colors"
                aria-label="LinkedIn"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              </a>
              <a
                href="https://medium.com/@chepenikconor"
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-muted hover:text-text transition-colors"
                aria-label="Medium"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M13.54 12a6.8 6.8 0 01-6.77 6.82A6.8 6.8 0 010 12a6.8 6.8 0 016.77-6.82A6.8 6.8 0 0113.54 12zM20.96 12c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z" />
                </svg>
              </a>
            </div>

            {/* Tagline */}
            <div className="text-center text-text-muted text-sm">
              <p className="mb-1">Writing is good for the soul.</p>
              <p className="text-xs opacity-75">Everything divided by 21 million.</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function ArticleRow({ article }: { article: Article }) {
  const readingTime = article.readingTime ? Math.max(1, Math.round(article.readingTime)) : 1;

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
