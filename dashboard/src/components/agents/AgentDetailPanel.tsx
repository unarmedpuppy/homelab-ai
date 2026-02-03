import { useState } from 'react';
import type { Agent } from '../../types/agents';
import { RetroButton } from '../ui';
import { AgentContextViewer } from './AgentContextViewer';
import { AgentSessionHistory } from './AgentSessionHistory';
import { QuickInteract } from '../jobs';

type TabId = 'context' | 'sessions' | 'interact';

interface Tab {
  id: TabId;
  label: string;
  disabled?: boolean;
}

interface AgentDetailPanelProps {
  agent: Agent;
  onClose: () => void;
}

export function AgentDetailPanel({ agent, onClose }: AgentDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>('context');
  const isOnline = agent.health.status === 'online';

  const tabs: Tab[] = [
    { id: 'context', label: 'Context' },
    { id: 'sessions', label: 'Sessions' },
    { id: 'interact', label: 'Interact', disabled: !isOnline },
  ];

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-dark)]">
      {/* Header */}
      <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <RetroButton variant="ghost" size="sm" onClick={onClose}>
              ← Back
            </RetroButton>
            <div>
              <h2 className="text-lg font-bold text-[var(--retro-text-primary)]">
                {agent.name}
              </h2>
              <p className="text-xs text-[var(--retro-text-muted)]">
                {agent.description}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{
                backgroundColor: isOnline
                  ? 'var(--retro-accent-green)'
                  : 'var(--retro-text-muted)',
                boxShadow: isOnline ? '0 0 8px var(--retro-accent-green)' : 'none',
              }}
            />
            <span
              className={`text-xs uppercase font-bold ${
                isOnline ? 'text-[var(--retro-accent-green)]' : 'text-[var(--retro-text-muted)]'
              }`}
            >
              {agent.health.status}
            </span>
          </div>
        </div>

        {/* Offline Banner */}
        {!isOnline && (
          <div className="mb-3 p-2 bg-[rgba(255,200,100,0.1)] border border-[var(--retro-accent-yellow)] rounded text-xs text-[var(--retro-accent-yellow)]">
            Agent is offline. Some features are disabled.
            {agent.health.error && (
              <span className="block mt-1 text-[var(--retro-text-muted)] font-mono">
                {agent.health.error}
              </span>
            )}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-1 border-b border-[var(--retro-border)]">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveTab(tab.id)}
              disabled={tab.disabled}
              className={`
                px-4 py-2 text-sm font-bold uppercase tracking-wider
                border-b-2 transition-colors
                ${tab.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                ${
                  activeTab === tab.id
                    ? 'text-[var(--retro-accent-cyan)] border-[var(--retro-accent-cyan)]'
                    : 'text-[var(--retro-text-muted)] border-transparent hover:text-[var(--retro-text-primary)]'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'context' && (
          <AgentContextViewer agent={agent} />
        )}
        {activeTab === 'sessions' && (
          <AgentSessionHistory agent={agent} />
        )}
        {activeTab === 'interact' && (
          <QuickInteract agent={agent} />
        )}
      </div>
    </div>
  );
}

export default AgentDetailPanel;
