import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { appsAPI, docsAPI, type GiteaRepo } from '../api/client';
import { LoadingSpinner } from '../components/ui';
import MarkdownContent from '../components/MarkdownContent';
import { useIsDesktop } from '../hooks/useMediaQuery';

const GITEA_ORG = 'homelab';

function formatUpdated(dateStr: string | null): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'today';
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 30) return `${diffDays}d ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
  return `${Math.floor(diffDays / 365)}y ago`;
}

// ---------------------------------------------------------------------------
// Repo list panel
// ---------------------------------------------------------------------------

function RepoList({
  repos,
  selected,
  onSelect,
}: {
  repos: GiteaRepo[];
  selected: string | null;
  onSelect: (name: string) => void;
}) {
  const [search, setSearch] = useState('');

  const filtered = repos.filter((r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      r.name.toLowerCase().includes(q) ||
      r.description.toLowerCase().includes(q) ||
      r.language.toLowerCase().includes(q)
    );
  });

  const itemCls = (name: string) => {
    const active = selected === name;
    return `w-full text-left px-3 py-2.5 border-l-2 transition-colors ${
      active
        ? 'bg-[var(--retro-bg-light)] border-[var(--retro-border-active)] text-[var(--retro-text-primary)]'
        : 'border-transparent text-[var(--retro-text-secondary)] hover:bg-[var(--retro-bg-light)] hover:text-[var(--retro-text-primary)]'
    }`;
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="px-3 py-3 border-b border-[var(--retro-border)] flex-shrink-0">
        <h2 className="text-sm font-bold text-[var(--retro-text-primary)]">Repos</h2>
        <div className="text-[10px] text-[var(--retro-text-muted)] mt-0.5 font-mono">
          {GITEA_ORG} · {repos.length} total
        </div>
        <input
          type="text"
          placeholder="Filter..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mt-2 w-full bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded-sm px-2.5 py-1 text-xs font-mono text-[var(--retro-text-primary)] placeholder-[var(--retro-text-muted)] focus:outline-none focus:border-[var(--retro-border-active)]"
        />
      </div>
      <div className="flex-1 overflow-y-auto">
        {filtered.map((repo) => (
          <button key={repo.name} className={itemCls(repo.name)} onClick={() => onSelect(repo.name)}>
            <div className="flex items-center justify-between gap-2 min-w-0">
              <span className="text-xs font-mono truncate">{repo.name}</span>
              {repo.private && (
                <span className="text-[9px] text-[var(--retro-text-muted)] flex-shrink-0">private</span>
              )}
            </div>
            {repo.description && (
              <p className="text-[10px] text-[var(--retro-text-muted)] mt-0.5 truncate leading-snug">
                {repo.description}
              </p>
            )}
            <div className="flex items-center gap-2 mt-1 text-[9px] text-[var(--retro-text-muted)] font-mono">
              {repo.language && <span>{repo.language}</span>}
              {repo.updated_at && <span className="ml-auto">{formatUpdated(repo.updated_at)}</span>}
            </div>
          </button>
        ))}
        {filtered.length === 0 && (
          <div className="px-3 py-6 text-xs text-[var(--retro-text-muted)] text-center">No repos match</div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// README panel
// ---------------------------------------------------------------------------

function ReadmePanel({ repo, onBack }: { repo: GiteaRepo | null; onBack?: () => void }) {
  const isDesktop = useIsDesktop();

  const { data, isLoading, error } = useQuery({
    queryKey: ['repo-readme', repo?.name],
    queryFn: () => docsAPI.getContent(repo!.name, 'README.md'),
    enabled: !!repo,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  if (!repo) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-2">
          <div className="text-2xl font-mono text-[var(--retro-text-muted)]">homelab</div>
          <p className="text-sm text-[var(--retro-text-muted)]">Select a repo</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--retro-border)] flex-shrink-0 gap-3">
        <div className="flex items-center gap-2 min-w-0">
          {!isDesktop && onBack && (
            <button
              onClick={onBack}
              className="text-[var(--retro-accent-cyan)] text-xs hover:text-[var(--retro-text-primary)] transition-colors mr-1 flex-shrink-0"
            >
              ←
            </button>
          )}
          <span className="text-sm font-bold font-mono text-[var(--retro-text-primary)] truncate">{repo.name}</span>
          {repo.language && (
            <span className="text-[10px] text-[var(--retro-text-muted)] font-mono flex-shrink-0">{repo.language}</span>
          )}
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          {repo.updated_at && (
            <span className="text-[10px] text-[var(--retro-text-muted)] font-mono">{formatUpdated(repo.updated_at)}</span>
          )}
          <a
            href={repo.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-[var(--retro-text-muted)] hover:text-[var(--retro-text-secondary)] transition-colors font-mono"
          >
            open ↗
          </a>
        </div>
      </div>

      {/* Description */}
      {repo.description && (
        <div className="px-4 sm:px-6 pt-3 pb-1 flex-shrink-0">
          <p className="text-sm text-[var(--retro-text-secondary)]">{repo.description}</p>
        </div>
      )}

      {/* README content */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && <LoadingSpinner size="sm" message="Loading README..." />}

        {error && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-3 p-6">
              <p className="text-sm text-[var(--retro-text-muted)]">No README found</p>
              <a
                href={repo.html_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-[var(--retro-accent-cyan)] hover:underline"
              >
                View on Gitea ↗
              </a>
            </div>
          </div>
        )}

        {data && (
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6">
            <MarkdownContent content={data.content} />
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export default function AppsPage() {
  const isDesktop = useIsDesktop();
  const [selected, setSelected] = useState<string | null>(null);

  const { data: repos, isLoading, error } = useQuery({
    queryKey: ['apps-repos'],
    queryFn: appsAPI.listRepos,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) return <LoadingSpinner size="md" message="Loading repos..." />;
  if (error) {
    return (
      <div className="p-6 text-sm text-[var(--retro-accent-red)]">
        Failed to load repos: {(error as Error).message}
      </div>
    );
  }

  const selectedRepo = (repos ?? []).find((r) => r.name === selected) ?? null;

  const listPanel = (
    <div className={`${isDesktop ? 'w-64 flex-shrink-0 border-r border-[var(--retro-border)]' : 'w-full flex-1'} bg-[var(--retro-bg-medium)] flex flex-col overflow-hidden`}>
      <RepoList repos={repos ?? []} selected={selected} onSelect={setSelected} />
    </div>
  );

  const readmePanel = (
    <div className="flex-1 overflow-hidden bg-[var(--retro-bg-dark)]">
      <ReadmePanel repo={selectedRepo} onBack={() => setSelected(null)} />
    </div>
  );

  if (isDesktop) {
    return (
      <div className="flex h-full">
        {listPanel}
        {readmePanel}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {selected ? readmePanel : listPanel}
    </div>
  );
}
