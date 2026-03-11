import { useState } from 'react';
import { RetroButton, RetroInput, RetroSelect, RetroModal } from '../ui';
import type { CustomModelCreate, ModelType } from '../../types/models';

interface RegisterModelModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (model: CustomModelCreate) => Promise<void>;
}

const EMPTY_FORM: CustomModelCreate = {
  id: '',
  name: '',
  type: 'text',
  description: '',
  quantization: '',
  vram_gb: undefined,
  context_window: undefined,
  max_tokens: undefined,
  architecture: '',
  license: '',
  harbor_ref: '',
  hf_model: '',
  tags: [],
};

export function RegisterModelModal({ isOpen, onClose, onSubmit }: RegisterModelModalProps) {
  const [form, setForm] = useState<CustomModelCreate>({ ...EMPTY_FORM });
  const [tagsInput, setTagsInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    setForm({ ...EMPTY_FORM });
    setTagsInput('');
    setError(null);
    onClose();
  };

  const handleSubmit = async () => {
    if (!form.id.trim() || !form.name.trim()) {
      setError('ID and Name are required');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const tags = tagsInput
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
      await onSubmit({ ...form, tags });
      handleClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to register model');
    } finally {
      setSubmitting(false);
    }
  };

  const updateField = <K extends keyof CustomModelCreate>(key: K, value: CustomModelCreate[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <RetroModal
      isOpen={isOpen}
      onClose={handleClose}
      title="Register Custom Model"
      size="lg"
      footer={
        <div className="flex gap-2 justify-end">
          <RetroButton variant="secondary" onClick={handleClose}>
            Cancel
          </RetroButton>
          <RetroButton variant="primary" onClick={handleSubmit} disabled={submitting}>
            {submitting ? 'Registering...' : 'Register'}
          </RetroButton>
        </div>
      }
    >
      <div className="space-y-4">
        {error && (
          <div className="p-3 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm text-[var(--retro-accent-red)]">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Model ID *</label>
            <RetroInput
              placeholder="my-custom-model"
              value={form.id}
              onChange={(e) => updateField('id', e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Name *</label>
            <RetroInput
              placeholder="My Custom Model"
              value={form.name}
              onChange={(e) => updateField('name', e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Description</label>
          <RetroInput
            placeholder="Brief description of the model"
            value={form.description || ''}
            onChange={(e) => updateField('description', e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Type</label>
            <RetroSelect
              value={form.type}
              onChange={(e) => updateField('type', e.target.value as ModelType)}
              options={[
                { value: 'text', label: 'Text' },
                { value: 'image', label: 'Image' },
                { value: 'tts', label: 'TTS' },
                { value: 'embedding', label: 'Embedding' },
              ]}
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Quantization</label>
            <RetroInput
              placeholder="awq, gptq, bnb-4bit..."
              value={form.quantization || ''}
              onChange={(e) => updateField('quantization', e.target.value || undefined)}
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">VRAM (GB)</label>
            <RetroInput
              type="number"
              placeholder="24"
              value={form.vram_gb ?? ''}
              onChange={(e) => updateField('vram_gb', e.target.value ? Number(e.target.value) : undefined)}
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Context Window</label>
            <RetroInput
              type="number"
              placeholder="32768"
              value={form.context_window ?? ''}
              onChange={(e) => updateField('context_window', e.target.value ? Number(e.target.value) : undefined)}
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Max Tokens</label>
            <RetroInput
              type="number"
              placeholder="8192"
              value={form.max_tokens ?? ''}
              onChange={(e) => updateField('max_tokens', e.target.value ? Number(e.target.value) : undefined)}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Architecture</label>
            <RetroInput
              placeholder="Qwen3.5, Llama3..."
              value={form.architecture || ''}
              onChange={(e) => updateField('architecture', e.target.value || undefined)}
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">License</label>
            <RetroInput
              placeholder="Apache-2.0, MIT..."
              value={form.license || ''}
              onChange={(e) => updateField('license', e.target.value || undefined)}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Harbor Reference</label>
            <RetroInput
              placeholder="harbor.server.unarmedpuppy.com/models/..."
              value={form.harbor_ref || ''}
              onChange={(e) => updateField('harbor_ref', e.target.value || undefined)}
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--retro-text-muted)] mb-1">HuggingFace Model</label>
            <RetroInput
              placeholder="org/model-name"
              value={form.hf_model || ''}
              onChange={(e) => updateField('hf_model', e.target.value || undefined)}
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-[var(--retro-text-muted)] mb-1">Tags (comma-separated)</label>
          <RetroInput
            placeholder="reasoning, coding, distilled..."
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
          />
        </div>
      </div>
    </RetroModal>
  );
}
