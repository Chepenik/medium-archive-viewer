'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import { ThemeToggle } from '../../components/ThemeToggle';

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

export default function ArticlePage() {
  const params = useParams();
  const id = params.id as string;
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        const response = await fetch(`/api/articles/${id}`);
        if (!response.ok) throw new Error('Failed to fetch article');
        const data = await response.json();
        setArticle(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (id) fetchArticle();
  }, [id]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-text-secondary">Loading article...</p>
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
        <p className="text-text-secondary mb-4">{error}</p>
        <Link href="/" className="text-accent hover:text-accent-hover transition-colors">
          Return to archive
        </Link>
      </div>
    </div>
  );

  if (!article) return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="text-center">
        <h2 className="font-heading text-xl mb-2">Article not found</h2>
        <Link href="/" className="text-accent hover:text-accent-hover transition-colors">
          Return to archive
        </Link>
      </div>
    </div>
  );

  const rawTime = article.readingTime || estimateReadingTime(article.content);
  const readingTime = Math.max(1, Math.round(rawTime));
  const wordCount = article.wordCount || article.content.trim().split(/\s+/).length;

  return (
    <div className="min-h-screen bg-bg">
      {/* Navigation */}
      <nav className="border-b border-border sticky top-0 bg-bg/95 backdrop-blur-sm z-10">
        <div className="max-w-3xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link
            href="/"
            className="group flex items-center gap-2 text-text-secondary hover:text-text transition-colors"
          >
            <svg
              className="w-5 h-5 transform group-hover:-translate-x-1 transition-transform"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back to archive</span>
          </Link>
          <ThemeToggle />
        </div>
      </nav>

      {/* Article Header */}
      <header className="max-w-3xl mx-auto px-6 pt-12 pb-8">
        <h1 className="font-heading text-3xl sm:text-4xl lg:text-5xl tracking-tight leading-tight mb-6">
          {article.title}
        </h1>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-text-secondary">
          <time dateTime={article.createdAt} className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {format(new Date(article.createdAt), 'MMMM d, yyyy')}
          </time>

          <span className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {readingTime} min read
          </span>

          <span className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {wordCount.toLocaleString()} words
          </span>
        </div>

        {article.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {article.tags.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1 text-sm bg-bg-secondary text-text-secondary rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </header>

      {/* Article Content */}
      <main className="max-w-3xl mx-auto px-6 pb-16">
        <article className="prose prose-lg prose-stone dark:prose-invert prose-archive max-w-none
                          prose-headings:font-heading prose-headings:tracking-tight
                          prose-p:leading-relaxed prose-p:text-text
                          prose-a:text-accent prose-a:no-underline hover:prose-a:underline
                          prose-blockquote:border-accent prose-blockquote:text-text-secondary
                          prose-strong:text-text prose-strong:font-semibold
                          prose-code:text-text prose-code:bg-bg-secondary prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
                          prose-pre:bg-bg-secondary prose-pre:text-text
                          prose-img:rounded-lg prose-img:shadow-md">
          <ReactMarkdown>{article.content}</ReactMarkdown>
        </article>
      </main>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="max-w-3xl mx-auto px-6 py-8">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <Link
              href="/"
              className="group flex items-center gap-2 text-text-secondary hover:text-text transition-colors"
            >
              <svg
                className="w-5 h-5 transform group-hover:-translate-x-1 transition-transform"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19l-7-7 7-7" />
              </svg>
              <span>Back to archive</span>
            </Link>

            <div className="flex items-center gap-4">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href);
                }}
                className="flex items-center gap-2 px-4 py-2 text-sm text-text-secondary hover:text-text
                         bg-bg-secondary hover:bg-border rounded-lg transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                </svg>
                Copy link
              </button>

              <a
                href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(article.title)}&url=${encodeURIComponent(typeof window !== 'undefined' ? window.location.href : '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 text-sm text-text-secondary hover:text-text
                         bg-bg-secondary hover:bg-border rounded-lg transition-colors"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
                Share
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
