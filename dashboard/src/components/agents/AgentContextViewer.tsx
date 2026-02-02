import { useState, useEffect, useCallback } from 'react';
import type { Agent } from '../../types/agents';
import { agentsAPI } from '../../api/client';
import { RetroButton } from '../ui';

interface AgentContextViewerProps {
  agent: Agent;
}

interface ContextData {
  content: string;
  last_modified: string | null;
  size_bytes: number;
}

export function AgentContextViewer({ agent }: AgentContextViewerProps) {
  const [context, setContext] = useState<ContextData | null>(null);
  const [editedContent, setEditedContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const isOnline = agent.health.status === 'online';

  const fetchContext = useCallback(async () => {
    if (!isOnline) {
      setLoading(false);
      setError('Agent is offline - cannot fetch context');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await agentsAPI.getContext(agent.id);
      setContext(data);
      setEditedContent(data.content);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch context');
      console.error('Failed to fetch context:', e);
    } finally {
      setLoading(false);
    }
  }, [agent.id, isOnline]);

  useEffect(() => {
    fetchContext();
  }, [fetchContext]);

  useEffect(() => {
    setHasChanges(context?.content !== editedContent);
  }, [context?.content, editedContent]);

  const handleSave = async () => {
    if (!hasChanges) return;

    try {
      setSaving(true);
      setError(null);
      const updated = await agentsAPI.updateContext(agent.id, editedContent);
      setContext(updated);
      setIsEditing(false);
      setHasChanges(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save context');
      console.error('Failed to save context:', e);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (context) {
      setEditedContent(context.content);
    }
    setIsEditing(false);
    setHasChanges(false);
  };

  const formatLastModified = (timestamp: string | null) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleString();
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} bytes`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-[var(--retro-text-muted)] retro-animate-pulse uppercase tracking-wider text-sm">
          Loading context...
        </div>
      </div>
    );
  }

  if (!isOnline) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="text-[var(--retro-text-muted)] uppercase tracking-wider mb-2">
          Agent Offline
        </div>
        <p className="text-sm text-[var(--retro-text-muted)] text-center max-w-md">
          CONTEXT.md cannot be viewed or edited while the agent is offline.
          The agent must be running to access its context file.
        </p>
      </div>
    );
  }

  if (error && !context) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="text-[var(--retro-accent-red)] uppercase tracking-wider mb-2">
          Error Loading Context
        </div>
        <p className="text-sm text-[var(--retro-text-muted)] text-center max-w-md mb-4">
          {error}
        </p>
        <RetroButton variant="ghost" size="sm" onClick={fetchContext}>
          Retry
        </RetroButton>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Context Header */}
      <div className="p-3 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)] flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <span className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wider">
              CONTEXT.md
            </span>
            {context && (
              <div className="text-xs text-[var(--retro-text-muted)] mt-0.5">
                {formatSize(context.size_bytes)} • Modified: {formatLastModified(context.last_modified)}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isEditing ? (
            <>
              <RetroButton
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                disabled={saving}
              >
                Cancel
              </RetroButton>
              <RetroButton
                variant="success"
                size="sm"
                onClick={handleSave}
                disabled={!hasChanges || saving}
                loading={saving}
              >
                Save
              </RetroButton>
            </>
          ) : (
            <RetroButton
              variant="primary"
              size="sm"
              onClick={() => setIsEditing(true)}
              disabled={!isOnline}
            >
              Edit
            </RetroButton>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="p-2 bg-[rgba(255,68,68,0.1)] border-b border-[var(--retro-accent-red)] text-xs text-[var(--retro-accent-red)]">
          {error}
        </div>
      )}

      {/* Unsaved changes warning */}
      {hasChanges && (
        <div className="p-2 bg-[rgba(255,200,100,0.1)] border-b border-[var(--retro-accent-yellow)] text-xs text-[var(--retro-accent-yellow)]">
          You have unsaved changes
        </div>
      )}

      {/* Content area */}
      <div className="flex-1 overflow-auto p-4">
        {isEditing ? (
          <textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            className="
              w-full h-full min-h-[400px]
              bg-[var(--retro-bg-dark)]
              border border-[var(--retro-border)]
              rounded p-3
              text-[var(--retro-text-primary)]
              font-mono text-sm
              resize-none
              focus:outline-none focus:border-[var(--retro-accent-cyan)]
            "
            spellCheck={false}
          />
        ) : (
          <pre className="
            whitespace-pre-wrap
            text-sm font-mono
            text-[var(--retro-text-primary)]
            bg-[var(--retro-bg-light)]
            border border-[var(--retro-border)]
            rounded p-4
            overflow-auto
          ">
            {context?.content || 'No content'}
          </pre>
        )}
      </div>
    </div>
  );
}

export default AgentContextViewer;
