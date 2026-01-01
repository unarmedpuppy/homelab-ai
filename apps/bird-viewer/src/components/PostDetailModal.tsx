import { useQuery } from '@tanstack/react-query';
import { postsAPI } from '../api/client';
import type { Post } from '../types/api';

interface PostDetailModalProps {
  postId: string;
  onClose: () => void;
}

export function PostDetailModal({ postId, onClose }: PostDetailModalProps) {
  const { data: post, isLoading, error } = useQuery({
    queryKey: ['post', postId],
    queryFn: () => postsAPI.get(postId),
  });

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
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

  // Close on escape key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  // Close on backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
          <h2 className="text-lg font-semibold">Post Detail</h2>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading && (
            <div className="flex items-center justify-center h-32">
              <div className="text-zinc-400">Loading...</div>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
              <p className="text-red-400">Error loading post: {(error as Error).message}</p>
            </div>
          )}

          {post && <PostContent post={post} formatDate={formatDate} parseMediaUrls={parseMediaUrls} />}
        </div>

        {/* Footer */}
        {post?.url && (
          <div className="px-6 py-4 border-t border-zinc-800 bg-zinc-900/50">
            <a
              href={post.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
              View on X
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

function PostContent({
  post,
  formatDate,
  parseMediaUrls,
}: {
  post: Post;
  formatDate: (dateStr: string | null) => string | null;
  parseMediaUrls: (mediaStr: string | null) => string[];
}) {
  const mediaUrls = parseMediaUrls(post.media_urls);

  return (
    <div className="space-y-6">
      {/* Author */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center text-xl font-bold">
          {post.author_display_name?.[0] || post.author_username?.[0] || '?'}
        </div>
        <div>
          <div className="font-semibold">{post.author_display_name || 'Unknown'}</div>
          {post.author_username && (
            <a
              href={`https://x.com/${post.author_username}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-zinc-500 hover:text-blue-400 text-sm"
            >
              @{post.author_username}
            </a>
          )}
        </div>
      </div>

      {/* Content */}
      {post.content && (
        <div className="text-zinc-200 text-lg leading-relaxed whitespace-pre-wrap break-words">
          {post.content}
        </div>
      )}

      {/* Media */}
      {mediaUrls.length > 0 && (
        <div className="space-y-3">
          <div className="text-sm text-zinc-400 font-medium">Media ({mediaUrls.length})</div>
          <div className={`grid gap-2 ${mediaUrls.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
            {mediaUrls.map((url, index) => (
              <a
                key={index}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-lg overflow-hidden bg-zinc-800 hover:opacity-90 transition-opacity"
              >
                <img
                  src={url}
                  alt={`Media ${index + 1}`}
                  className="w-full h-auto max-h-64 object-cover"
                  loading="lazy"
                />
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="pt-4 border-t border-zinc-800 space-y-2 text-sm">
        {post.tweet_created_at && (
          <div className="flex items-center gap-2 text-zinc-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>Posted: {formatDate(post.tweet_created_at)}</span>
          </div>
        )}
        <div className="flex items-center gap-2 text-zinc-400">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          <span>Fetched: {formatDate(post.fetched_at)}</span>
        </div>
        <div className="flex items-center gap-2 text-zinc-400">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
          </svg>
          <span>Tweet ID: {post.tweet_id}</span>
        </div>
      </div>
    </div>
  );
}
