import { useState, useEffect, useCallback } from 'react';
import type { Agent, AgentSkill } from '../../types/agents';
import { agentsAPI } from '../../api/client';
import { RetroButton } from '../ui';

interface AgentSkillsTabProps {
  agent: Agent;
}

export function AgentSkillsTab({ agent }: AgentSkillsTabProps) {
  const [skills, setSkills] = useState<AgentSkill[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');

  const isOnline = agent.health.status === 'online';

  const fetchSkills = useCallback(async () => {
    if (!isOnline) {
      setLoading(false);
      setError('Agent is offline — cannot fetch skills');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await agentsAPI.getSkills(agent.id);
      setSkills(data.skills);
      setCount(data.count);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch skills');
    } finally {
      setLoading(false);
    }
  }, [agent.id, isOnline]);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const filtered = filter
    ? skills.filter(
        (s) =>
          s.name.toLowerCase().includes(filter.toLowerCase()) ||
          s.description.toLowerCase().includes(filter.toLowerCase())
      )
    : skills;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32 text-[var(--retro-text-muted)] text-sm">
        Loading skills...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="p-3 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-xs text-[var(--retro-accent-red)]">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="p-3 border-b border-[var(--retro-border)] flex items-center gap-3">
        <span className="text-xs text-[var(--retro-text-muted)]">{count} skills</span>
        <input
          type="text"
          placeholder="Filter skills..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="flex-1 text-xs bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded px-2 py-1 text-[var(--retro-text-primary)] placeholder-[var(--retro-text-muted)] focus:outline-none focus:border-[var(--retro-accent-cyan)]"
        />
        <RetroButton variant="ghost" size="sm" onClick={fetchSkills}>
          Refresh
        </RetroButton>
      </div>

      {/* Skills list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filtered.length === 0 ? (
          <div className="text-center py-8 text-[var(--retro-text-muted)] text-sm">
            {filter ? 'No skills match filter' : 'No skills found'}
          </div>
        ) : (
          filtered.map((skill) => (
            <div
              key={skill.name}
              className="p-3 bg-[var(--retro-bg-medium)] border border-[var(--retro-border)] rounded"
            >
              <div className="font-mono text-xs font-bold text-[var(--retro-accent-cyan)] mb-1">
                {skill.name}
              </div>
              <div className="text-xs text-[var(--retro-text-muted)] leading-relaxed line-clamp-2">
                {skill.description}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default AgentSkillsTab;
