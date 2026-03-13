import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeAPI, type KnowledgeFile } from '../api/client';
import { LoadingSpinner } from '../components/ui';
import { useIsDesktop } from '../hooks/useMediaQuery';
import MarkdownContent from '../components/MarkdownContent';

// ---------------------------------------------------------------------------
// File tree panel
// ---------------------------------------------------------------------------

function FileTree({
  files,
  selectedPath,
  onSelect,
}: {
  files: KnowledgeFile[];
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  const agentsMd = files.find((f) => f.kind === 'agents_md');
  const skills = files.filter((f) => f.kind === 'skill');

  const itemCls = (path: string) => {
    const active = selectedPath === path;
    return `w-full text-left pl-4 pr-3 py-1.5 text-xs transition-colors border-l-2 ${
      active
        ? 'bg-[var(--retro-bg-light)] text-[var(--retro-accent-cyan)] border-[var(--retro-accent-cyan)]'
        : 'text-[var(--retro-text-secondary)] hover:text-[var(--retro-text-primary)] hover:bg-[var(--retro-bg-light)] border-transparent'
    }`;
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="px-3 py-3 border-b border-[var(--retro-border)]">
        <h2 className="text-sm font-bold text-[var(--retro-text-primary)]">Knowledge Base</h2>
        <div className="text-[10px] text-[var(--retro-text-muted)] mt-1 font-mono">
          homelab/agent-memory
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* AGENTS.md pinned at top */}
        {agentsMd && (
          <div className="border-b border-[var(--retro-border)] pb-1 pt-2">
            <div className="px-3 pb-1">
              <span className="text-[0.6rem] font-semibold tracking-[0.12em] uppercase text-[var(--retro-text-muted)]">
                Core
              </span>
            </div>
            <button className={itemCls(agentsMd.path)} onClick={() => onSelect(agentsMd.path)}>
              <span className="flex items-center gap-2">
                <svg width="11" height="11" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M3 1h6.5L12 3.5V14H3V1z"/><path d="M9.5 1v3H12"/>
                </svg>
                AGENTS.md
              </span>
            </button>
          </div>
        )}

        {/* Skills */}
        {skills.length > 0 && (
          <div className="pt-2">
            <div className="px-3 pb-1">
              <span className="text-[0.6rem] font-semibold tracking-[0.12em] uppercase text-[var(--retro-text-muted)]">
                Skills ({skills.length})
              </span>
            </div>
            {skills.map((f) => (
              <button key={f.path} className={itemCls(f.path)} onClick={() => onSelect(f.path)}>
                <span className="flex items-center gap-2 truncate">
                  <svg width="11" height="11" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M7.5 1C5 1 3 3 3 5.5c0 1.5.5 2.5 1.5 3.5L3 14h9l-1.5-5c1-1 1.5-2 1.5-3.5C12 3 10 1 7.5 1z"/>
                  </svg>
                  <span className="truncate font-mono">{f.name}</span>
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
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
  const queryClient = useQueryClient();
  const [editMode, setEditMode] = useState(false);
  const [draftContent, setDraftContent] = useState('');
  const [commitMsg, setCommitMsg] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge-file', selectedPath],
    queryFn: () => knowledgeAPI.getFile(selectedPath!),
    enabled: !!selectedPath,
    staleTime: 60 * 1000,
  });

  const mutation = useMutation({
    mutationFn: ({ content, sha, message }: { content: string; sha: string; message: string }) =>
      knowledgeAPI.updateFile(selectedPath!, content, sha, message || undefined),
    onSuccess: (updated) => {
      queryClient.setQueryData(['knowledge-file', selectedPath], updated);
      setEditMode(false);
      setSaveError(null);
      setSavedAt(new Date().toLocaleTimeString());
    },
    onError: (err: Error) => {
      setSaveError(err.message);
    },
  });

  const handleEdit = useCallback(() => {
    if (data) {
      setDraftContent(data.content);
      setCommitMsg('');
      setSaveError(null);
      setEditMode(true);
    }
  }, [data]);

  const handleCancel = useCallback(() => {
    setEditMode(false);
    setSaveError(null);
  }, []);

  const handleSave = useCallback(() => {
    if (!data) return;
    mutation.mutate({
      content: draftContent,
      sha: data.sha,
      message: commitMsg,
    });
  }, [data, draftContent, commitMsg, mutation]);

  if (!selectedPath) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-3">
          <div className="text-3xl font-mono text-[var(--retro-text-muted)]">~/.innie</div>
          <p className="text-sm text-[var(--retro-text-muted)]">Select a file to view</p>
          <p className="text-xs text-[var(--retro-text-muted)] max-w-xs">
            Browse agent config and skills from the agent-memory repo.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) return <LoadingSpinner size="md" message="Loading file..." />;
  if (error) {
    return (
      <div className="p-6 text-sm text-[var(--retro-accent-red)]">
        Failed to load: {(error as Error).message}
      </div>
    );
  }
  if (!data) return null;

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
          <span className="text-xs font-mono text-[var(--retro-text-muted)] truncate">{selectedPath}</span>
          <span className="text-[10px] text-[var(--retro-text-muted)] font-mono flex-shrink-0">
            {(data.size / 1024).toFixed(1)}kb
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {savedAt && !editMode && (
            <span className="text-[10px] text-[var(--retro-accent-green)] font-mono">saved {savedAt}</span>
          )}
          {!editMode ? (
            <button
              onClick={handleEdit}
              className="px-2.5 py-1 text-xs border border-[var(--retro-border)] text-[var(--retro-text-secondary)] hover:border-[var(--retro-border-active)] hover:text-[var(--retro-text-primary)] transition-colors rounded-sm"
            >
              Edit
            </button>
          ) : (
            <>
              <button
                onClick={handleCancel}
                disabled={mutation.isPending}
                className="px-2.5 py-1 text-xs border border-[var(--retro-border)] text-[var(--retro-text-muted)] hover:text-[var(--retro-text-secondary)] transition-colors rounded-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={mutation.isPending}
                className="px-2.5 py-1 text-xs border border-[var(--retro-accent-cyan)]/60 text-[var(--retro-accent-cyan)] hover:bg-[var(--retro-accent-cyan)]/10 transition-colors rounded-sm disabled:opacity-50"
              >
                {mutation.isPending ? 'Saving...' : 'Commit'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Edit mode: commit message + textarea */}
      {editMode && (
        <div className="px-4 py-2 border-b border-[var(--retro-border)] flex-shrink-0 space-y-2">
          <input
            type="text"
            placeholder="Commit message (optional)"
            value={commitMsg}
            onChange={(e) => setCommitMsg(e.target.value)}
            className="w-full bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded-sm px-2.5 py-1 text-xs font-mono text-[var(--retro-text-primary)] placeholder-[var(--retro-text-muted)] focus:outline-none focus:border-[var(--retro-border-active)]"
          />
          {saveError && (
            <p className="text-xs text-[var(--retro-accent-red)]">{saveError}</p>
          )}
        </div>
      )}

      {/* Content area */}
      <div className="flex-1 overflow-y-auto">
        {editMode ? (
          <textarea
            value={draftContent}
            onChange={(e) => setDraftContent(e.target.value)}
            className="w-full h-full bg-[var(--retro-bg-dark)] text-[var(--retro-text-primary)] text-xs font-mono p-4 resize-none focus:outline-none border-none"
            spellCheck={false}
          />
        ) : (
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

export default function KnowledgePage() {
  const isDesktop = useIsDesktop();
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  const { data: files, isLoading, error } = useQuery({
    queryKey: ['knowledge-tree'],
    queryFn: knowledgeAPI.tree,
    staleTime: 5 * 60 * 1000,
  });

  const handleSelect = (path: string) => {
    setSelectedPath(path);
  };

  const handleBack = () => {
    setSelectedPath(null);
  };

  if (isLoading) return <LoadingSpinner size="md" message="Loading knowledge base..." />;
  if (error) {
    return (
      <div className="p-6 text-sm text-[var(--retro-accent-red)]">
        Failed to load knowledge base: {(error as Error).message}
      </div>
    );
  }

  const treePanel = (
    <div
      className={`${isDesktop ? 'w-64 flex-shrink-0 border-r border-[var(--retro-border)]' : 'w-full flex-1'} bg-[var(--retro-bg-medium)] flex flex-col overflow-hidden`}
    >
      <FileTree files={files ?? []} selectedPath={selectedPath} onSelect={handleSelect} />
    </div>
  );

  const contentPanel = (
    <div className="flex-1 overflow-hidden bg-[var(--retro-bg-dark)]">
      <ContentPanel selectedPath={selectedPath} onBack={handleBack} />
    </div>
  );

  if (isDesktop) {
    return (
      <div className="flex h-full">
        {treePanel}
        {contentPanel}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {selectedPath ? contentPanel : treePanel}
    </div>
  );
}
