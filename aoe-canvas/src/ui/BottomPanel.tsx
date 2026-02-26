import { SelectedUnit, SelectedBuilding } from '../hooks/useGameBridge';
import { useAgentJobs } from '../hooks/useAgentJobs';
import { cancelJob } from '../api/agentHarness';
import { UNIT_COLORS, UNIT_LABELS } from '../types/game';

const PROFILE_NAMES: Record<string, string> = {
  avery: 'Avery',
  gilfoyle: 'Gilfoyle',
  ralph: 'Ralph',
  jobin: 'Jobin',
  villager: 'Villager',
};

const STATUS_COLORS: Record<string, string> = {
  idle: '#00cc44',
  moving: '#ffaa00',
  working: '#ffff00',
  done: '#00ff88',
  error: '#ff3333',
};

interface BottomPanelProps {
  selectedUnit: SelectedUnit | null;
  selectedBuilding: SelectedBuilding | null;
  onDispatch: (prompt: string, count: number) => void;
}

export function BottomPanel({ selectedUnit, selectedBuilding }: BottomPanelProps) {
  const { data: jobs = [] } = useAgentJobs();

  if (!selectedUnit && !selectedBuilding) {
    return (
      <div
        className="absolute bottom-10 left-0 right-0 h-24 flex items-center justify-center"
        style={{
          background: 'linear-gradient(to top, rgba(26,18,8,0.9), transparent)',
          pointerEvents: 'none',
        }}
      >
        <span style={{ color: '#6b5320', fontSize: '11px', fontFamily: 'Courier New' }}>
          Click a unit or building to inspect
        </span>
      </div>
    );
  }

  if (selectedUnit) {
    const { unitId: _unitId, profile, status } = selectedUnit;
    const unitJobs = jobs.filter(j => j.agent === profile && (j.status === 'running' || j.status === 'pending'));
    const activeJob = unitJobs[0];
    const colorHex = '#' + UNIT_COLORS[profile].toString(16).padStart(6, '0');

    return (
      <div
        className="absolute bottom-10 left-0 right-0 px-3 py-2 flex gap-4"
        style={{
          background: 'linear-gradient(to top, rgba(26,18,8,0.97), rgba(26,18,8,0.85))',
          borderTop: '2px solid #6b5320',
          fontFamily: 'Courier New',
        }}
      >
        {/* Portrait */}
        <div
          className="flex-none w-14 h-14 flex items-center justify-center rounded"
          style={{ background: colorHex + '33', border: `2px solid ${colorHex}` }}
        >
          <span style={{ fontSize: '24px', color: colorHex, fontWeight: 'bold' }}>
            {UNIT_LABELS[profile]}
          </span>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span style={{ color: '#c8a84b', fontSize: '13px', fontWeight: 'bold' }}>
              {PROFILE_NAMES[profile] ?? profile}
            </span>
            <span style={{ color: STATUS_COLORS[status] ?? '#888', fontSize: '10px' }}>
              {'\u25cf'} {status.toUpperCase()}
            </span>
          </div>

          {activeJob ? (
            <div>
              <div style={{ color: '#888', fontSize: '10px', marginBottom: '2px' }}>
                {activeJob.id} | {activeJob.model}
              </div>
              <div
                style={{
                  color: '#d4c06a',
                  fontSize: '10px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '400px',
                }}
              >
                {activeJob.prompt}
              </div>
              {activeJob.cost_usd != null && (
                <div style={{ color: '#888', fontSize: '10px', marginTop: '2px' }}>
                  ${activeJob.cost_usd.toFixed(4)} | {activeJob.input_tokens ?? 0} in / {activeJob.output_tokens ?? 0} out
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: '#666', fontSize: '10px' }}>No active job</div>
          )}
        </div>

        {/* Actions */}
        {activeJob && (
          <div className="flex-none flex flex-col gap-1 justify-center">
            <button
              onClick={() => cancelJob(activeJob.id)}
              style={{
                background: 'rgba(200,50,50,0.3)',
                border: '1px solid #cc3333',
                color: '#ff8888',
                fontSize: '10px',
                padding: '2px 8px',
                cursor: 'pointer',
                fontFamily: 'Courier New',
              }}
            >
              STOP
            </button>
          </div>
        )}
      </div>
    );
  }

  if (selectedBuilding) {
    const { buildingData } = selectedBuilding;
    const buildingJobs = jobs.filter(j =>
      (j.status === 'running' || j.status === 'pending') &&
      (j.working_directory?.includes(buildingData.name) ?? false)
    );

    return (
      <div
        className="absolute bottom-10 left-0 right-0 px-3 py-2"
        style={{
          background: 'linear-gradient(to top, rgba(26,18,8,0.97), rgba(26,18,8,0.85))',
          borderTop: '2px solid #6b5320',
          fontFamily: 'Courier New',
        }}
      >
        <div className="flex items-center gap-3 mb-1">
          <span style={{ color: '#c8a84b', fontSize: '13px', fontWeight: 'bold' }}>
            {buildingData.name}
          </span>
          <span style={{ color: '#888', fontSize: '10px' }}>
            {buildingData.type} | [{buildingData.col}, {buildingData.row}]
          </span>
          <span style={{
            color: buildingData.status === 'active' ? '#ffff44' : '#888',
            fontSize: '10px',
          }}>
            {'\u25cf'} {buildingData.status.toUpperCase()}
          </span>
        </div>
        {buildingData.projectId && (
          <div style={{ color: '#d4c06a', fontSize: '10px' }}>
            Project: {buildingData.projectId}
          </div>
        )}
        {buildingJobs.length > 0 && (
          <div style={{ color: '#888', fontSize: '10px' }}>
            {buildingJobs.length} active job(s)
          </div>
        )}
      </div>
    );
  }

  return null;
}
