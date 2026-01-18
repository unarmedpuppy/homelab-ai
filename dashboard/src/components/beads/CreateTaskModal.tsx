import { useState } from 'react';
import {
  RetroModal,
  RetroButton,
  RetroInput,
  RetroSelect,
} from '../ui';
import { beadsAPI } from '../../api/client';
import { REPO_LABELS, TASK_TYPES, PRIORITIES } from '../../types/beads';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function CreateTaskModal({
  isOpen,
  onClose,
  onCreated,
}: CreateTaskModalProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState(2);
  const [taskType, setTaskType] = useState('task');
  const [repoLabel, setRepoLabel] = useState('');
  const [additionalLabels, setAdditionalLabels] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    if (!repoLabel) {
      setError('Repository label is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Build labels array
      const labels = [repoLabel];
      if (additionalLabels.trim()) {
        const extra = additionalLabels.split(',').map(l => l.trim()).filter(Boolean);
        labels.push(...extra);
      }

      await beadsAPI.createTask({
        title: title.trim(),
        priority,
        type: taskType,
        labels,
        description: description.trim() || undefined,
      });

      // Reset form
      setTitle('');
      setDescription('');
      setPriority(2);
      setTaskType('task');
      setRepoLabel('');
      setAdditionalLabels('');

      onCreated();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create task');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <RetroModal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create New Task"
      size="lg"
      footer={
        <>
          <RetroButton variant="ghost" onClick={handleClose} disabled={loading}>
            CANCEL
          </RetroButton>
          <RetroButton
            variant="primary"
            onClick={handleSubmit}
            disabled={loading || !title.trim() || !repoLabel}
            loading={loading}
          >
            CREATE TASK
          </RetroButton>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title */}
        <RetroInput
          label="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Task title..."
          required
        />

        {/* Type & Priority */}
        <div className="grid grid-cols-2 gap-4">
          <RetroSelect
            label="Type"
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
            options={TASK_TYPES.map(t => ({ value: t.value, label: t.label }))}
          />
          <RetroSelect
            label="Priority"
            value={priority.toString()}
            onChange={(e) => setPriority(parseInt(e.target.value))}
            options={PRIORITIES.map(p => ({ value: p.value.toString(), label: p.label }))}
          />
        </div>

        {/* Repository Label */}
        <RetroSelect
          label="Repository (required)"
          value={repoLabel}
          onChange={(e) => setRepoLabel(e.target.value)}
          placeholder="Select repository..."
          options={REPO_LABELS.map(r => ({
            value: r.value,
            label: `${r.label} - ${r.description}`,
          }))}
          error={!repoLabel && error?.includes('Repository') ? error : undefined}
        />

        {/* Additional Labels */}
        <RetroInput
          label="Additional Labels (comma-separated)"
          value={additionalLabels}
          onChange={(e) => setAdditionalLabels(e.target.value)}
          placeholder="e.g., urgent, api, frontend"
        />

        {/* Description */}
        <div className="space-y-1">
          <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--retro-text-secondary)]">
            Description (optional)
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Markdown description..."
            rows={4}
            className="retro-input resize-none"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="p-3 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm text-[var(--retro-accent-red)]">
            {error}
          </div>
        )}
      </form>
    </RetroModal>
  );
}

export default CreateTaskModal;
