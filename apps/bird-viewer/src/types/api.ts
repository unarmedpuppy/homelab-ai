export interface Run {
  id: string;
  timestamp: string;
  source: string;
  status: string;
  post_count: number;
  error_message: string | null;
  created_at: string;
}

export interface RunListResponse {
  runs: Run[];
  total: number;
}

export interface Post {
  id: string;
  run_id: string | null;
  tweet_id: string;
  author_username: string | null;
  author_display_name: string | null;
  content: string | null;
  url: string | null;
  media_urls: string | null;
  tweet_created_at: string | null;
  fetched_at: string;
}

export interface PostListResponse {
  posts: Post[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Stats {
  total_posts: number;
  total_runs: number;
  latest_run: Run | null;
  posts_by_source: Record<string, number>;
}
