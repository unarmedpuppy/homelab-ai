import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { docsAPI } from '../api/client';
import { LoadingSpinner } from '../components/ui';
import MarkdownContent from '../components/MarkdownContent';

type RepoADRs = Awaited<ReturnType<typeof docsAPI.getRepos>>[number];

function slugFromPath(path: string): string {
  const name = path.split('/').pop() || '';
  return name.replace(/\.md$/, '');
}

function StatusChip({ status }: { status: string }) {
  if (!status) return null;
  const lower = status.toLowerCase();
  const colors =
    lower === 'accepted'
      ? 'bg-[var(--retro-accent-green)]/20 text-[var(--retro-accent-green)] border-[var(--retro-accent-green)]/40'
      : lower === 'proposed'
        ? 'bg-[var(--retro-accent-cyan)]/20 text-[var(--retro-accent-cyan)] border-[var(--retro-accent-cyan)]/40'
        : lower === 'deprecated' || lower === 'superseded'
          ? 'bg-[var(--retro-accent-red)]/20 text-[var(--retro-accent-red)] border-[var(--retro-accent-red)]/40'
          : 'bg-[var(--retro-bg-light)] text-[var(--retro-text-muted)] border-[var(--retro-border)]';

  return (
    <span className={`inline-block px-1.5 py-0.5 text-[10px] border rounded ${colors}`}>
      {status}
    </span>
  );
}

function RepoSection({
  repo,
  selectedSlug,
  selectedRepo,
  onSelect,
}: {
  repo: RepoADRs;
  selectedSlug?: string;
  selectedRepo?: string;
  onSelect: (repo: string, slug: string, path: string) => void;
}) {
  const [expanded, setExpanded] = useState(
    selectedRepo === repo.repo || false
  );

  return (
    <div className="border-b border-[var(--retro-border)]">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-[var(--retro-bg-light)] transition-colors text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[var(--retro-text-muted)] text-xs">{expanded ? '▾' : '▸'}</span>
          <span className="text-sm font-medium text-[var(--retro-text-primary)] truncate">
            {repo.repo}
          </span>
        </div>
        <span className="text-xs text-[var(--retro-text-muted)] font-mono ml-2 flex-shrink-0">
          {repo.adrs.length}
        </span>
      </button>

      {expanded && (
        <div className="pb-1">
          {repo.adrs.map((adr) => {
            const slug = slugFromPath(adr.path);
            const isActive = selectedRepo === repo.repo && selectedSlug === slug;
            return (
              <button
                key={adr.path}
                onClick={() => onSelect(repo.repo, slug, adr.path)}
                className={`
                  w-full text-left pl-7 pr-3 py-1.5 text-xs transition-colors
                  ${isActive
                    ? 'bg-[var(--retro-bg-light)] text-[var(--retro-accent-cyan)] border-l-2 border-[var(--retro-accent-cyan)]'
                    : 'text-[var(--retro-text-secondary)] hover:text-[var(--retro-text-primary)] hover:bg-[var(--retro-bg-light)] border-l-2 border-transparent'
                  }
                `}
              >
                <div className="flex items-center gap-2">
                  <span className="truncate flex-1">{adr.title}</span>
                  <StatusChip status={adr.status} />
                </div>
                {adr.date && (
                  <div className="text-[10px] text-[var(--retro-text-muted)] mt-0.5 font-mono">
                    {adr.date}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function DocsPage() {
  const { repo: urlRepo, slug: urlSlug } = useParams<{ repo?: string; slug?: string }>();
  const navigate = useNavigate();

  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const activeRepo = urlRepo;
  const activeSlug = urlSlug;

  const {
    data: repos,
    isLoading: reposLoading,
    error: reposError,
  } = useQuery({
    queryKey: ['docs-repos'],
    queryFn: docsAPI.getRepos,
    staleTime: 5 * 60 * 1000,
  });

  // Resolve the path for fetching content
  const contentPath = selectedPath || (repos && urlRepo && urlSlug
    ? repos
        .find((r) => r.repo === urlRepo)
        ?.adrs.find((a) => slugFromPath(a.path) === urlSlug)?.path
    : null);

  const {
    data: contentData,
    isLoading: contentLoading,
    error: contentError,
  } = useQuery({
    queryKey: ['docs-content', activeRepo, contentPath],
    queryFn: () => docsAPI.getContent(activeRepo!, contentPath!),
    enabled: !!activeRepo && !!contentPath,
    staleTime: 60 * 1000,
  });

  const handleSelect = (repo: string, slug: string, path: string) => {
    setSelectedPath(path);
    navigate(`/docs/${repo}/${slug}`);
  };

  const totalADRs = repos?.reduce((sum, r) => sum + r.adrs.length, 0) ?? 0;

  return (
    <div className="flex h-full">
      {/* Left panel - repo/ADR list */}
      <div className="w-72 flex-shrink-0 border-r border-[var(--retro-border)] bg-[var(--retro-bg-medium)] flex flex-col overflow-hidden">
        <div className="px-3 py-3 border-b border-[var(--retro-border)]">
          <h2 className="text-sm font-bold text-[var(--retro-text-primary)]">
            Architecture Decision Records
          </h2>
          <div className="text-[10px] text-[var(--retro-text-muted)] mt-1 font-mono">
            {reposLoading ? '...' : `${repos?.length ?? 0} repos / ${totalADRs} ADRs`}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {reposLoading && <LoadingSpinner size="sm" message="Loading repos..." />}
          {reposError && (
            <div className="p-3 text-xs text-[var(--retro-accent-red)]">
              Failed to load repos: {(reposError as Error).message}
            </div>
          )}
          {repos?.map((repo) => (
            <RepoSection
              key={repo.repo}
              repo={repo}
              selectedRepo={activeRepo}
              selectedSlug={activeSlug}
              onSelect={handleSelect}
            />
          ))}
        </div>
      </div>

      {/* Right panel - ADR content */}
      <div className="flex-1 overflow-y-auto bg-[var(--retro-bg-dark)]">
        {!activeRepo || !activeSlug ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-3">
              <div className="text-4xl">{"</>"}</div>
              <p className="text-sm text-[var(--retro-text-muted)]">
                Select an ADR to view
              </p>
              <p className="text-xs text-[var(--retro-text-muted)] max-w-xs">
                Browse architecture decision records across all homelab repos.
              </p>
            </div>
          </div>
        ) : contentLoading ? (
          <LoadingSpinner size="md" message="Loading document..." />
        ) : contentError ? (
          <div className="p-6 text-sm text-[var(--retro-accent-red)]">
            Failed to load: {(contentError as Error).message}
          </div>
        ) : contentData ? (
          <div className="max-w-3xl mx-auto px-6 py-8">
            <div className="flex items-center gap-2 mb-4 text-xs text-[var(--retro-text-muted)] font-mono">
              <span>{contentData.repo}</span>
              <span>/</span>
              <span>{contentData.path}</span>
            </div>
            <MarkdownContent content={contentData.content} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
