import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { postsAPI } from '../api/client';
import { PostDetailModal } from './PostDetailModal';

export function PostList() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [selectedPostId, setSelectedPostId] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['posts', page, search],
    queryFn: () => postsAPI.list({ page, page_size: 20, search: search || undefined }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString();
  };

  const parseMediaUrls = (mediaStr: string | null): string[] => {
    if (!mediaStr) return [];
    try {
      return JSON.parse(mediaStr);
    } catch {
      return [];
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-zinc-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <p className="text-red-400">Error loading posts: {(error as Error).message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Posts</h2>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search content..."
            className="bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-zinc-500"
          />
          <button
            type="submit"
            className="bg-zinc-800 hover:bg-zinc-700 px-4 py-2 rounded-lg text-sm"
          >
            Search
          </button>
        </form>
      </div>

      <div className="text-sm text-zinc-400">
        Showing {data?.posts.length ?? 0} of {data?.total ?? 0} posts
      </div>

      <div className="space-y-4">
        {data?.posts.map((post) => (
          <div
            key={post.id}
            className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 cursor-pointer hover:border-zinc-700 hover:bg-zinc-900/80 transition-colors"
            onClick={() => setSelectedPostId(post.id)}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  {post.author_display_name && (
                    <span className="font-semibold">{post.author_display_name}</span>
                  )}
                  {post.author_username && (
                    <span className="text-zinc-500">@{post.author_username}</span>
                  )}
                </div>
                <p className="text-zinc-300 whitespace-pre-wrap break-words line-clamp-4">
                  {post.content}
                </p>
                {parseMediaUrls(post.media_urls).length > 0 && (
                  <div className="mt-2 text-xs text-zinc-500">
                    {parseMediaUrls(post.media_urls).length} media attachment(s)
                  </div>
                )}
              </div>
              {post.url && (
                <a
                  href={post.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 text-sm shrink-0"
                  onClick={(e) => e.stopPropagation()}
                >
                  View
                </a>
              )}
            </div>
            <div className="mt-3 pt-3 border-t border-zinc-800 flex items-center gap-4 text-xs text-zinc-500">
              {post.tweet_created_at && (
                <span>Posted: {formatDate(post.tweet_created_at)}</span>
              )}
              <span>Fetched: {formatDate(post.fetched_at)}</span>
            </div>
          </div>
        ))}
      </div>

      {selectedPostId && (
        <PostDetailModal
          postId={selectedPostId}
          onClose={() => setSelectedPostId(null)}
        />
      )}

      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-2 rounded-lg text-sm"
          >
            Previous
          </button>
          <span className="text-zinc-400 px-4">
            Page {page} of {data.pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
            disabled={page === data.pages}
            className="bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-2 rounded-lg text-sm"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
