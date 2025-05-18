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

  const filteredArticles = articles.filter(article => {
    const matchesSearch = article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         article.content.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTag = !selectedTag || article.tags.includes(selectedTag);
    return matchesSearch && matchesTag;
  });

  const allTags = Array.from(new Set(articles.flatMap(article => article.tags)));

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>
  );
  
  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="p-8 text-center text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg">
        <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        Error: {error}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen transition-colors duration-200">
      <header className="border-b border-gray-200 dark:border-gray-800 transition-colors duration-200 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 dark:from-blue-500/10 dark:to-purple-500/10"></div>
        <div className="container mx-auto px-4 py-6 relative">
          <div className="flex justify-between items-center">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-3xl font-bold transition-colors duration-200 bg-gradient-to-r from-gray-900 to-gray-700 dark:from-gray-100 dark:to-gray-300 bg-clip-text text-transparent">
                  Conor Chepenik&apos;s Medium Archive
                </h1>
                <span className="px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">
                  Latest Posts
                </span>
              </div>
              <p className="mt-2 text-gray-600 dark:text-gray-400 transition-colors duration-200">
                Personal archive of the Binmucker who writes on Medium every day because writing is good for the soul!! 
                <br />
                <span className="inline-flex items-center gap-1">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
                  </svg>
                  Everything divided by 21 million.
                </span>
              </p>
            </div>
            <ThemeToggle />
          </div>

          <div className="mt-6 flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Search articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 pl-10 rounded-lg border border-gray-200 dark:border-gray-700 
                         bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         transition-all duration-200"
              />
              <svg className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" 
                   fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setSelectedTag(selectedTag === tag ? null : tag)}
                  className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap
                            transition-all duration-200 ${
                              selectedTag === tag
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                            }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid gap-6 grid-cols-1 sm:grid-cols-3 xl:grid-cols-5">
          {filteredArticles.map((article) => (
            <article
              key={article.id}
              className="group border border-gray-200 dark:border-gray-800 rounded-lg p-6 
                         hover:shadow-lg transition-all duration-300 
                         bg-white dark:bg-gray-800
                         hover:scale-[1.02] hover:-translate-y-1
                         relative overflow-hidden cursor-pointer"
              onClick={(e) => {
                // Don't navigate if clicking on social buttons
                if (!(e.target as HTMLElement).closest('.social-button')) {
                  window.location.href = `/article/${article.id}`;
                }
              }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 to-blue-500/0 
                            group-hover:from-blue-500/5 group-hover:to-purple-500/5 
                            transition-all duration-300" />
              
              <h2 className="text-xl font-semibold mb-2 
                           group-hover:text-blue-600 dark:group-hover:text-blue-400 
                           transition-colors duration-200
                           bg-gradient-to-r from-gray-900 to-gray-700 
                           dark:from-gray-100 dark:to-gray-300 
                           bg-clip-text text-transparent">
                {article.title}
              </h2>
              
              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 
                            transition-colors duration-200 mb-4">
                <time dateTime={article.createdAt} className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {format(new Date(article.createdAt), 'MMMM d, yyyy')}
                </time>
                
                {article.tags.length > 0 && (
                  <div className="flex gap-2 flex-wrap">
                    {article.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 bg-gray-100 dark:bg-gray-700 
                                 text-gray-700 dark:text-gray-300 rounded-full text-xs
                                 transition-colors duration-200
                                 hover:bg-blue-100 dark:hover:bg-blue-900
                                 hover:text-blue-700 dark:hover:text-blue-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              
              <p className="text-gray-700 dark:text-gray-300 line-clamp-3 
                          transition-colors duration-200">
                {article.content.substring(0, 200)}...
              </p>
              
              <div className="mt-4 flex items-center justify-between">
                <span className="text-blue-600 dark:text-blue-400 
                              transition-colors duration-200
                              flex items-center gap-1 group">
                  Read more 
                  <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" 
                       fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M9 5l7 7-7 7" />
                  </svg>
                </span>
                
                <div className="flex items-center gap-4">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigator.clipboard.writeText(window.location.origin + `/article/${article.id}`);
                    }}
                    className="social-button text-gray-500 hover:text-blue-500 transition-colors duration-200"
                    title="Copy link"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                            d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                    </svg>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(article.title)}&url=${encodeURIComponent(window.location.origin + `/article/${article.id}`)}`, '_blank');
                    }}
                    className="social-button text-gray-500 hover:text-blue-500 transition-colors duration-200"
                    title="Share on Twitter"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                    </svg>
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </main>
    </div>
  );
}
