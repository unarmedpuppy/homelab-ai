import { useState } from 'react';
import type { SelectedUnit, SelectedBuilding } from '../hooks/useGameBridge';
import { useAgentJobs } from '../hooks/useAgentJobs';
import { cancelJob } from '../api/agentHarness';
import { UNIT_COLORS, UNIT_LABELS, BUILDING_COLORS, BUILDING_LABELS } from '../types/game';
import type { BuildingType, Task } from '../types/game';

const PROFILE_NAMES: Record<string, string> = {
  avery: 'Avery',
  gilfoyle: 'Gilfoyle',
  ralph: 'Ralph',
  jobin: 'Jobin',
  colin: 'Colin',
  villager: 'Villager',
};

const BUILDING_NAMES: Record<BuildingType, string> = {
  'town-center': 'Town Center',
  'barracks': 'Barracks',
  'market': 'Market',
  'university': 'University',
  'castle': 'Castle',
};

const BUILDING_DESC: Record<BuildingType, string> = {
  'town-center': 'Command hub — dispatch named agents and coordinate operations',
  'barracks': 'Engineering — code tasks, Claude Code, agent work',
  'market': 'Data exchange — trading, analytics, data pipelines',
  'university': 'Research — AI experiments, model evaluations, knowledge work',
  'castle': 'Infrastructure — systems operations, server management',
};

const BUILDING_AGENT: Record<BuildingType, string> = {
  'town-center': 'avery',
  'castle': 'gilfoyle',
  'barracks': 'ralph',
  'market': 'ralph',
  'university': 'jobin',
};

const PRIORITY_COLOR: Record<string, string> = {
  P0: '#ff3333',
  P1: '#ff8844',
  P2: '#c8a84b',
  P3: '#888888',
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
  tasksByBuilding: Map<BuildingType, Task[]>;
  onDispatch: (prompt: string, count: number) => void;
}

export function BottomPanel({ selectedUnit, selectedBuilding, tasksByBuilding, onDispatch }: BottomPanelProps) {
  const { data: jobs = [] } = useAgentJobs();
  const [dispatchPrompt, setDispatchPrompt] = useState('');

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
    const { profile, status } = selectedUnit;
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
        <div
          className="flex-none w-14 h-14 flex items-center justify-center rounded"
          style={{ background: colorHex + '33', border: `2px solid ${colorHex}` }}
        >
          <span style={{ fontSize: '24px', color: colorHex, fontWeight: 'bold' }}>
            {UNIT_LABELS[profile]}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span style={{ color: '#c8a84b', fontSize: '13px', fontWeight: 'bold' }}>
              {PROFILE_NAMES[profile] ?? profile}
            </span>
            <span style={{ color: STATUS_COLORS[status] ?? '#888', fontSize: '10px' }}>
              &#x25cf; {status.toUpperCase()}
            </span>
          </div>

          {activeJob ? (
            <div>
              <div style={{ color: '#888', fontSize: '10px', marginBottom: '2px' }}>
                {activeJob.id} | {activeJob.model}
              </div>
              <div style={{
                color: '#d4c06a', fontSize: '10px',
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '400px',
              }}>
                {activeJob.prompt}
              </div>
              {activeJob.cost_usd != null && (
                <div style={{ color: '#888', fontSize: '10px', marginTop: '2px' }}>
                  ${activeJob.cost_usd.toFixed(4)} | {activeJob.input_tokens ?? 0}in / {activeJob.output_tokens ?? 0}out
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: '#666', fontSize: '10px' }}>No active job — select and type a prompt to dispatch</div>
          )}
        </div>

        {activeJob && (
          <div className="flex-none flex flex-col gap-1 justify-center">
            <button
              onClick={() => cancelJob(activeJob.id)}
              style={{
                background: 'rgba(200,50,50,0.3)', border: '1px solid #cc3333',
                color: '#ff8888', fontSize: '10px', padding: '2px 8px',
                cursor: 'pointer', fontFamily: 'Courier New',
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
    const tasks = tasksByBuilding.get(buildingData.type) ?? [];
    const runningJobs = jobs.filter(j =>
      j.agent === BUILDING_AGENT[buildingData.type] &&
      (j.status === 'running' || j.status === 'pending')
    );
    const colorHex = '#' + BUILDING_COLORS[buildingData.type].toString(16).padStart(6, '0');

    const handleBuildingDispatch = (e: React.FormEvent) => {
      e.preventDefault();
      if (!dispatchPrompt.trim()) return;
      onDispatch(dispatchPrompt.trim(), 1);
      setDispatchPrompt('');
    };

    return (
      <div
        className="absolute bottom-10 left-0 right-0 px-3 py-2 flex gap-4"
        style={{
          background: 'linear-gradient(to top, rgba(26,18,8,0.97), rgba(26,18,8,0.85))',
          borderTop: '2px solid #6b5320',
          fontFamily: 'Courier New',
        }}
      >
        <div
          className="flex-none w-14 h-14 flex items-center justify-center rounded"
          style={{ background: colorHex + '22', border: `2px solid ${colorHex}` }}
        >
          <span style={{ fontSize: '18px', color: colorHex, fontWeight: 'bold' }}>
            {BUILDING_LABELS[buildingData.type]}
          </span>
        </div>

        <div className="flex-1 min-w-0 flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span style={{ color: '#c8a84b', fontSize: '13px', fontWeight: 'bold' }}>
              {BUILDING_NAMES[buildingData.type]}
            </span>
            <span style={{ color: '#666', fontSize: '10px' }}>
              agent: {BUILDING_AGENT[buildingData.type]}
            </span>
            {runningJobs.length > 0 && (
              <span style={{ color: '#ffaa00', fontSize: '10px' }}>
                &#x25cf; {runningJobs.length} running
              </span>
            )}
          </div>
          <div style={{ color: '#665a30', fontSize: '10px' }}>
            {BUILDING_DESC[buildingData.type]}
          </div>

          {/* Task queue */}
          {tasks.length > 0 ? (
            <div className="flex gap-2 overflow-x-auto" style={{ marginTop: '2px' }}>
              {tasks.slice(0, 4).map(task => (
                <div
                  key={task.id}
                  onClick={() => setDispatchPrompt(`Work on: ${task.title}`)}
                  style={{
                    background: 'rgba(200,168,75,0.08)',
                    border: `1px solid ${PRIORITY_COLOR[task.priority] ?? '#444'}44`,
                    padding: '2px 6px',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                  title={task.description ?? task.title}
                >
                  <span style={{ color: PRIORITY_COLOR[task.priority] ?? '#888', fontSize: '9px' }}>
                    {task.priority}
                  </span>
                  {' '}
                  <span style={{ color: '#d4c06a', fontSize: '9px' }}>
                    {task.title.length > 30 ? task.title.slice(0, 30) + '…' : task.title}
                  </span>
                </div>
              ))}
              {tasks.length > 4 && (
                <span style={{ color: '#666', fontSize: '9px', alignSelf: 'center' }}>
                  +{tasks.length - 4} more
                </span>
              )}
            </div>
          ) : (
            <div style={{ color: '#444', fontSize: '10px' }}>No open tasks</div>
          )}

          {/* Inline dispatch */}
          <form onSubmit={handleBuildingDispatch} className="flex gap-1 mt-1">
            <input
              type="text"
              value={dispatchPrompt}
              onChange={(e) => setDispatchPrompt(e.target.value)}
              placeholder={`Dispatch to ${BUILDING_AGENT[buildingData.type]}...`}
              style={{
                flex: 1, background: 'rgba(42,31,10,0.8)',
                border: '1px solid #6b5320', color: '#d4c06a',
                fontSize: '10px', padding: '2px 6px', fontFamily: 'Courier New',
                outline: 'none',
              }}
            />
            <button
              type="submit"
              disabled={!dispatchPrompt.trim()}
              style={{
                background: dispatchPrompt.trim() ? 'rgba(200,168,75,0.2)' : 'transparent',
                border: '1px solid #6b5320',
                color: dispatchPrompt.trim() ? '#c8a84b' : '#444',
                fontSize: '10px', padding: '2px 8px',
                cursor: dispatchPrompt.trim() ? 'pointer' : 'default',
                fontFamily: 'Courier New',
              }}
            >
              GO
            </button>
          </form>
        </div>
      </div>
    );
  }

  return null;
}
