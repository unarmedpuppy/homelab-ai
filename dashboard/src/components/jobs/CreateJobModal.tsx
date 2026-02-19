import { useState } from 'react';
import type { Agent } from '../../types/agents';
import type { JobCreateRequest } from '../../types/jobs';
import { jobsAPI } from '../../api/client';
import { RetroModal, RetroButton, RetroInput, RetroSelect } from '../ui';

interface CreateJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  agents: Agent[];
  preselectedAgentId?: string;
  onJobCreated?: () => void;
}

const MODEL_OPTIONS = [
  { value: 'sonnet', label: 'Claude Sonnet (Default)' },
  { value: 'haiku', label: 'Claude Haiku (Fast)' },
  { value: 'opus', label: 'Claude Opus (Best)' },
];

export function CreateJobModal({
  isOpen,
  onClose,
  agents,
  preselectedAgentId,
  onJobCreated,
}: CreateJobModalProps) {
  const [agentId, setAgentId] = useState(preselectedAgentId || '');
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('sonnet');
  const [workingDirectory, setWorkingDirectory] = useState('');
  const [maxTurns, setMaxTurns] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onlineAgents = agents.filter(a => a.health.status === 'online');
  const selectedAgent = agents.find(a => a.id === agentId);
  const canSubmit = agentId && prompt.trim() && selectedAgent?.health.status === 'online';

  const agentOptions = agents.map(agent => ({
    value: agent.id,
    label: `${agent.name} (${agent.health.status})`,
    disabled: agent.health.status !== 'online',
  }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setError(null);

    try {
      const request: JobCreateRequest = {
        agent_id: agentId,
        prompt: prompt.trim(),
        model,
      };

      if (workingDirectory.trim()) {
        request.working_directory = workingDirectory.trim();
      }

      if (maxTurns) {
        const turns = parseInt(maxTurns, 10);
        if (!isNaN(turns) && turns > 0) {
          request.max_turns = turns;
        }
      }

      await jobsAPI.create(request);
      onJobCreated?.();
      handleClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create job');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setPrompt('');
    setModel('sonnet');
    setWorkingDirectory('');
    setMaxTurns('');
    setError(null);
    if (!preselectedAgentId) {
      setAgentId('');
    }
    onClose();
  };

  return (
    <RetroModal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create Job"
      size="lg"
      footer={
        <div className="flex justify-end gap-2">
          <RetroButton variant="ghost" onClick={handleClose}>
            Cancel
          </RetroButton>
          <RetroButton
            variant="primary"
            onClick={handleSubmit}
            disabled={!canSubmit || submitting}
          >
            {submitting ? 'Creating...' : 'Create Job'}
          </RetroButton>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Agent Selection */}
        {!preselectedAgentId && (
          <RetroSelect
            label="Agent"
            options={agentOptions}
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            placeholder="Select an agent..."
            error={agentId && selectedAgent?.health.status !== 'online' ? 'Agent is offline' : undefined}
          />
        )}

        {preselectedAgentId && selectedAgent && (
          <div className="text-sm">
            <span className="text-[var(--retro-text-muted)]">Agent: </span>
            <span className="text-[var(--retro-text-primary)] font-bold">{selectedAgent.name}</span>
          </div>
        )}

        {onlineAgents.length === 0 && (
          <div className="p-3 bg-[rgba(255,200,100,0.1)] border border-[var(--retro-accent-yellow)] rounded text-sm text-[var(--retro-accent-yellow)]">
            No agents are currently online. Jobs can only be submitted to online agents.
          </div>
        )}

        {/* Prompt */}
        <div className="space-y-1">
          <label
            htmlFor="prompt"
            className="block text-xs font-semibold text-[var(--retro-text-secondary)]"
          >
            Prompt
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt for the agent..."
            rows={4}
            className="retro-input w-full resize-none font-mono text-sm"
          />
        </div>

        {/* Model Selection */}
        <RetroSelect
          label="Model"
          options={MODEL_OPTIONS}
          value={model}
          onChange={(e) => setModel(e.target.value)}
        />

        {/* Advanced Options */}
        <details className="group">
          <summary className="cursor-pointer text-xs font-semibold text-[var(--retro-text-muted)] hover:text-[var(--retro-text-secondary)]">
            Advanced Options
          </summary>
          <div className="mt-3 space-y-3 pl-2 border-l-2 border-[var(--retro-border)]">
            <RetroInput
              label="Working Directory"
              value={workingDirectory}
              onChange={(e) => setWorkingDirectory(e.target.value)}
              placeholder="/workspace/project"
            />
            <RetroInput
              label="Max Turns"
              type="number"
              value={maxTurns}
              onChange={(e) => setMaxTurns(e.target.value)}
              placeholder="Leave empty for default"
              min={1}
              max={100}
            />
          </div>
        </details>

        {/* Error message */}
        {error && (
          <div className="p-3 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm text-[var(--retro-accent-red)]">
            {error}
          </div>
        )}
      </form>
    </RetroModal>
  );
}

export default CreateJobModal;
