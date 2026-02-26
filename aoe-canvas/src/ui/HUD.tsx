import { useHarnessHealth, useRouterMetrics } from '../hooks/useMetrics';
import { useActiveJobs } from '../hooks/useAgentJobs';

export function HUD() {
  const { data: harnessHealth } = useHarnessHealth();
  const { data: metrics } = useRouterMetrics();
  const activeJobs = useActiveJobs();

  const totalTokens = (metrics as { total_tokens?: number } | null)?.total_tokens ?? 0;
  const totalCost = (metrics as { total_cost_usd?: number } | null)?.total_cost_usd ?? 0;

  return (
    <div
      className="absolute top-0 left-0 right-0 z-10 flex items-center gap-4 px-3 py-1.5"
      style={{
        background: 'linear-gradient(to bottom, rgba(26,18,8,0.95), rgba(26,18,8,0.85))',
        borderBottom: '2px solid #6b5320',
        fontFamily: 'Courier New, monospace',
      }}
    >
      {/* Agent harness status */}
      <div className="flex items-center gap-2">
        <div
          className="w-2 h-2 rounded-full"
          style={{ background: (harnessHealth as { status?: string } | null)?.status === 'healthy' ? '#00cc44' : '#cc4400' }}
        />
        <span style={{ color: '#d4c06a', fontSize: '11px' }}>
          {(harnessHealth as { profile?: { display_name?: string } } | null)?.profile?.display_name ?? 'Harness'}
        </span>
      </div>

      <div style={{ color: '#6b5320' }}>|</div>

      {/* Active jobs */}
      <div className="flex items-center gap-1.5">
        <span style={{ color: '#c8a84b', fontSize: '11px' }}>JOBS:</span>
        <span style={{
          color: activeJobs.length > 0 ? '#ffcc44' : '#888',
          fontSize: '11px',
          fontWeight: 'bold',
        }}>
          {activeJobs.length} active
        </span>
      </div>

      <div style={{ color: '#6b5320' }}>|</div>

      {/* Tokens */}
      <div className="flex items-center gap-1.5">
        <span style={{ color: '#c8a84b', fontSize: '11px' }}>TOKENS:</span>
        <span style={{ color: '#d4c06a', fontSize: '11px' }}>
          {totalTokens > 0 ? `${(totalTokens / 1000).toFixed(1)}k` : '\u2014'}
        </span>
      </div>

      <div style={{ color: '#6b5320' }}>|</div>

      {/* Cost */}
      <div className="flex items-center gap-1.5">
        <span style={{ color: '#c8a84b', fontSize: '11px' }}>COST:</span>
        <span style={{ color: '#d4c06a', fontSize: '11px' }}>
          {totalCost > 0 ? `$${totalCost.toFixed(3)}` : '\u2014'}
        </span>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Age label */}
      <div
        className="px-2 py-0.5"
        style={{
          background: 'rgba(200,168,75,0.15)',
          border: '1px solid #6b5320',
          color: '#c8a84b',
          fontSize: '11px',
          letterSpacing: '1px',
        }}
      >
        IMPERIAL AGE
      </div>
    </div>
  );
}
