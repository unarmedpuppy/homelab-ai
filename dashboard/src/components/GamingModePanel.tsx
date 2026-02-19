import { useEffect, useState, useCallback } from 'react';
import { gamingModeAPI } from '../api/client';
import { RetroCard, RetroBadge, RetroButton } from './ui';

interface GamingPCStatus {
  gaming_mode: boolean;
  safe_to_game: boolean;
  running_models: string[];
  stopped_models: string[];
}

export default function GamingModePanel() {
  const [status, setStatus] = useState<GamingPCStatus | null>(null);
  const [offline, setOffline] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await gamingModeAPI.getStatus();
      setStatus(data);
      setOffline(false);
      setError(null);
    } catch {
      setOffline(true);
      setStatus(null);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleToggle = async () => {
    if (!status) return;
    setToggling(true);
    setError(null);
    try {
      await gamingModeAPI.toggle(!status.gaming_mode);
      // Re-fetch after a brief delay to let the gaming PC settle
      setTimeout(fetchStatus, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle gaming mode');
    } finally {
      setToggling(false);
    }
  };

  return (
    <RetroCard variant={offline ? 'warning' : 'default'} size="responsive">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-base sm:text-lg font-semibold text-[var(--retro-text-primary)] uppercase tracking-wider">
            Gaming PC
          </h3>
          {offline ? (
            <RetroBadge variant="status-blocked" size="sm">Offline</RetroBadge>
          ) : status?.gaming_mode ? (
            <RetroBadge variant="status-progress" size="sm">Gaming Mode</RetroBadge>
          ) : (
            <RetroBadge variant="status-done" size="sm">Serving Models</RetroBadge>
          )}
        </div>
        {!offline && status && (
          <RetroButton
            variant={status.gaming_mode ? 'success' : 'warning'}
            size="sm"
            onClick={handleToggle}
            loading={toggling}
            disabled={toggling}
          >
            {status.gaming_mode ? 'Disable Gaming Mode' : 'Enable Gaming Mode'}
          </RetroButton>
        )}
      </div>

      {offline ? (
        <p className="text-xs sm:text-sm text-[var(--retro-text-muted)]">
          Gaming PC is unreachable. It may be powered off or disconnected.
        </p>
      ) : status && (
        <div className="space-y-2">
          <div className="flex items-center gap-4 text-xs sm:text-sm">
            <span className="text-[var(--retro-text-muted)]">
              Safe to game:{' '}
              <span className={status.safe_to_game ? 'text-[var(--retro-accent-green)]' : 'text-[var(--retro-accent-red)]'}>
                {status.safe_to_game ? 'Yes' : 'No'}
              </span>
            </span>
            <span className="text-[var(--retro-text-muted)]">
              Running: <span className="text-[var(--retro-text-primary)]">{status.running_models.length}</span>
            </span>
            <span className="text-[var(--retro-text-muted)]">
              Stopped: <span className="text-[var(--retro-text-primary)]">{status.stopped_models.length}</span>
            </span>
          </div>

          {status.running_models.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {status.running_models.map((model) => (
                <RetroBadge key={model} variant="label" size="sm">
                  {model}
                </RetroBadge>
              ))}
            </div>
          )}
        </div>
      )}

      {error && (
        <p className="text-xs text-[var(--retro-accent-red)] mt-2">{error}</p>
      )}
    </RetroCard>
  );
}
