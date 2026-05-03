import { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { knowledgeAPI } from '../api/client';
import { LoadingSpinner } from '../components/ui';
import { useIsDesktop } from '../hooks/useMediaQuery';
import MarkdownContent from '../components/MarkdownContent';

// ---------------------------------------------------------------------------
// Search panel
// ---------------------------------------------------------------------------

function SearchPanel({ onSearch }: { onSearch: (query: string) => void }) {
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const handleSearch = useCallback(() => {
    onSearch(query);
  }, [query, onSearch]);

  return (
    <div className="p-3 border-b border-[var(--retro-border)]">
      <div className="space-y-2">
        <input
          type="text"
          placeholder="Search knowledge base..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="w-full bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded-sm px-3 py-2 text-sm text-[var(--retro-text-primary)] placeholder-[var(--retro-text-muted)] focus:outline-none focus:border-[var(--retro-border-active)]"
        />
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="w-full bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded-sm px-3 py-2 text-sm text-[var(--retro-text-primary)] focus:outline-none focus:border-[var(--retro-border-active)]"
        >
          <option value="all">All Categories</option>
          <option value="AI">AI</option>
          <option value="Finance">Finance</option>
          <option value="Other">Other</option>
          <option value="Unsorted">Unsorted</option>
        </select>
        <button
          onClick={handleSearch}
          className="w-full bg-[var(--retro-accent-cyan)]/20 border border-[var(--retro-accent-cyan)] text-[var(--retro-accent-cyan)] hover:bg-[var(--retro-accent-cyan)]/30 transition-colors rounded-sm px-3 py-2 text-sm font-medium"
        >
          Search
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Results list
// ---------------------------------------------------------------------------

function ResultsList({
  results,
  onSelect,
}: {
  results: Array<{
    path: string;
    filename: string;
    category: string;
    title: string;
    content_snippet: string;
    tags: string[];
    categories: string[];
    score: number;
    created_at?: string;
    author?: string;
  }>;
  onSelect: (path: string) => void;
}) {
  if (results.length === 0) {
    return (
      <div className="p-6 text-center">
        <div className="text-2xl font-mono text-[var(--retro-text-muted)] mb-2">No Results</div>
        <p className="text-sm text-[var(--retro-text-muted)]">Try a different search term</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-[var(--retro-border)]">
      {results.map((result) => (
        <button
          key={result.path}
          onClick={() => onSelect(result.path)}
          className="w-full text-left p-3 hover:bg-[var(--retro-bg-light)] transition-colors"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-[var(--retro-accent-cyan)]">
                  {result.category}
                </span>
                {result.tags.length > 0 && (
                  <span className="text-xs text-[var(--retro-text-muted)]">
                    #{result.tags.slice(0, 3).join(',')}
                    {result.tags.length > 3 && '...'}
                  </span>
                )}
              </div>
              <div className="font-medium text-[var(--retro-text-primary)] truncate">
                {result.title || result.filename}
              </div>
              <div className="text-xs text-[var(--retro-text-secondary)] mt-1 line-clamp-2">
                {result.content_snippet}
              </div>
            </div>
            {result.score > 0 && (
              <div className="text-xs font-mono text-[var(--retro-accent-green)]">
                {result.score.toFixed(1)}
              </div>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Content panel
// ---------------------------------------------------------------------------

function ContentPanel({
  selectedPath,
  onBack,
}: {
  selectedPath: string | null;
  onBack?: () => void;
}) {
  const isDesktop = useIsDesktop();

  const { data, isLoading, error } = useQuery({
    queryKey: ['kb-file', selectedPath],
    queryFn: () => knowledgeAPI.getFile(selectedPath!),
    enabled: !!selectedPath,
    staleTime: 60 * 1000,
  });

  if (!selectedPath) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-3">
          <div className="text-3xl font-mono text-[var(--retro-text-muted)]">~/.kb</div>
          <p className="text-sm text-[var(--retro-text-muted)]">Select a file to view</p>
          <p className="text-xs text-[var(--retro-text-muted)] max-w-xs">
            Browse your personal knowledge base. Search for topics, categories, or tags.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) return <LoadingSpinner size="md" message="Loading content..." />;
  if (error) {
    return (
      <div className="p-6 text-sm text-[var(--retro-accent-red)]">
        Failed to load: {(error as Error).message}
      </div>
    );
  }
  if (!data) return null;

  const frontmatter = data.frontmatter || {};

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--retro-border)] flex-shrink-0 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {!isDesktop && onBack && (
            <button
              onClick={onBack}
              className="text-[var(--retro-accent-cyan)] text-xs hover:text-[var(--retro-text-primary)] transition-colors mr-1"
            >
              ←
            </button>
          )}
          <span className="text-xs font-mono text-[var(--retro-text-muted)] truncate">
            {data.path}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {frontmatter.created_at && (
            <span className="text-[10px] text-[var(--retro-text-muted)] font-mono">
              {new Date(frontmatter.created_at).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6">
          <MarkdownContent content={data.content} />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export default function KnowledgeBasePage() {
  const isDesktop = useIsDesktop();
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<
    Array<{
      path: string;
      filename: string;
      category: string;
      title: string;
      content_snippet: string;
      tags: string[];
      categories: string[];
      score: number;
    }>
  >([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    try {
      const results = await knowledgeAPI.search(query, selectedCategory !== 'all' ? selectedCategory : undefined);
      setSearchResults(results.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    }
  }, [selectedCategory]);

  const handleSelect = (path: string) => {
    setSelectedPath(path);
    setSearchResults([]);
    setSearchQuery('');
  };

  const handleBack = () => {
    setSelectedPath(null);
  };

  const { data: files, isLoading: loadingFiles } = useQuery({
    queryKey: ['kb-files'],
    queryFn: knowledgeAPI.listFiles,
    staleTime: 5 * 60 * 1000,
  });

  // Show search results when querying, otherwise show file list
  const showResults = searchResults.length > 0;

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left panel: Search or results */}
      <div
        className={`${
          isDesktop ? 'w-96 flex-shrink-0 border-r border-[var(--retro-border)]' : 'w-full flex-1'
        } bg-[var(--retro-bg-medium)] flex flex-col overflow-hidden`}
      >
        <div className="px-3 py-3 border-b border-[var(--retro-border)]">
          <h2 className="text-sm font-bold text-[var(--retro-text-primary)]">Knowledge Base</h2>
          <div className="text-[10px] text-[var(--retro-text-muted)] mt-1 font-mono">
            personal-knowledge-base
          </div>
        </div>

        {showResults ? (
          <>
            <SearchPanel
              onSearch={(q) => {
                setSearchQuery(q);
                handleSearch(q);
              }}
            />
            <div className="flex-1 overflow-y-auto">
              <ResultsList results={searchResults} onSelect={handleSelect} />
            </div>
          </>
        ) : (
          <>
            <SearchPanel onSearch={handleSearch} />
            <div className="flex-1 overflow-y-auto">
              {loadingFiles ? (
                <div className="p-4 text-center text-sm text-[var(--retro-text-muted)]">
                  Loading files...
                </div>
              ) : (
                <>
                  {/* Categories */}
                  {files?.map((file) => (
                    <div key={file.path} className="border-b border-[var(--retro-border)]">
                      <div className="px-3 py-2">
                        <span className="text-[0.6rem] font-semibold tracking-[0.12em] uppercase text-[var(--retro-text-muted)]">
                          {file.category}
                        </span>
                      </div>
                      {file.files.slice(0, 5).map((f) => (
                        <button
                          key={f.path}
                          onClick={() => handleSelect(f.path)}
                          className="w-full text-left pl-4 pr-3 py-1.5 text-xs transition-colors border-l-2 hover:bg-[var(--retro-bg-light)] border-transparent text-[var(--retro-text-secondary)] hover:text-[var(--retro-text-primary)]"
                        >
                          <span className="flex items-center gap-2 truncate">
                            <svg
                              width="11"
                              height="11"
                              viewBox="0 0 15 15"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.4"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              aria-hidden="true"
                            >
                              <path d="M3 1h6.5L12 3.5V14H3V1z" />
                              <path d="M9.5 1v3H12" />
                            </svg>
                            <span className="truncate font-mono">{f.name}</span>
                          </span>
                        </button>
                      ))}
                      {file.files.length > 5 && (
                        <div className="px-4 py-1 text-[10px] text-[var(--retro-text-muted)]">
                          +{file.files.length - 5} more
                        </div>
                      )}
                    </div>
                  ))}
                </>
              )}
            </div>
          </>
        )}
      </div>

      {/* Right panel: Content */}
      <div className="flex-1 overflow-hidden bg-[var(--retro-bg-dark)]">
        <ContentPanel selectedPath={selectedPath} onBack={handleBack} />
      </div>
    </div>
  );
}
