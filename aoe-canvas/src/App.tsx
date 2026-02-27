import { useRef, useState, useEffect, useCallback } from 'react';
import { PhaserGame } from './game/PhaserGame';
import { HUD } from './ui/HUD';
import { BottomPanel } from './ui/BottomPanel';
import { PromptBar } from './ui/PromptBar';
import { BuildMenu } from './ui/BuildMenu';
import { AgePanel } from './ui/AgePanel';
import { useGameBridge } from './hooks/useGameBridge';
import { useAgentJobs } from './hooks/useAgentJobs';
import { useTasksByBuilding } from './hooks/useTasks';
import { createJob } from './api/agentHarness';
import { BuildingType, BuildingData, UnitProfile } from './types/game';
import type { MapScene } from './game/scenes/MapScene';

let buildingIdCounter = 100;

// Default tile positions for each building type on the map
const BUILDING_POSITIONS: Record<BuildingType, { col: number; row: number }> = {
  'town-center': { col: 16, row: 16 },
  'castle':      { col: 12, row: 16 },
  'barracks':    { col: 15, row: 19 },
  'market':      { col: 19, row: 17 },
  'university':  { col: 21, row: 15 },
};

// Which agent to route dispatch to based on building type
const BUILDING_AGENT: Record<BuildingType, UnitProfile> = {
  'town-center': 'avery',
  'castle':      'gilfoyle',
  'barracks':    'ralph',
  'market':      'ralph',
  'university':  'jobin',
};

const BUILDING_DISPLAY_NAMES: Record<BuildingType, string> = {
  'town-center': 'Town Center',
  'castle':      'Castle',
  'barracks':    'Barracks',
  'market':      'Market',
  'university':  'University',
};

export default function App() {
  const sceneRef = useRef<MapScene | null>(null);
  const [sceneReady, setSceneReady] = useState(false);
  const [agePanelVisible, setAgePanelVisible] = useState(false);
  const { data: jobs = [] } = useAgentJobs();
  const tasksByBuilding = useTasksByBuilding();
  const placedBuildings = useRef<Set<BuildingType>>(new Set());

  const {
    selectedUnit,
    selectedBuilding,
    rightClickTile,
    setRightClickTile,
    placeBuilding,
    syncJobs,
  } = useGameBridge();

  // Sync job state to game engine on every job update
  useEffect(() => {
    if (jobs.length > 0) {
      syncJobs(jobs.map(j => ({ id: j.id, status: j.status, agent: j.agent })));
    }
  }, [jobs, syncJobs]);

  const handleSceneReady = useCallback((scene: MapScene) => {
    sceneRef.current = scene;
    setSceneReady(true);
  }, []);

  // Auto-place buildings from Tasks API. Runs when tasks load or scene becomes ready.
  // One building per building_type — represents the department, not individual tasks.
  useEffect(() => {
    if (!sceneReady) return;

    const buildingTypes: BuildingType[] = ['castle', 'barracks', 'market', 'university'];
    for (const bType of buildingTypes) {
      if (placedBuildings.current.has(bType)) continue;

      const tasks = tasksByBuilding.get(bType) ?? [];
      if (tasks.length === 0) continue;

      const pos = BUILDING_POSITIONS[bType];
      const hasActive = tasks.some(t => t.status === 'IN_PROGRESS');

      placeBuilding({
        id: `building-${bType}-tasks`,
        type: bType,
        status: hasActive ? 'active' : 'idle',
        col: pos.col,
        row: pos.row,
        name: BUILDING_DISPLAY_NAMES[bType],
        projectId: tasks[0]?.id,
      });
      placedBuildings.current.add(bType);
    }
  }, [tasksByBuilding, placeBuilding, sceneReady]);

  const handlePromptSubmit = useCallback(async (prompt: string, villagerCount: number) => {
    if (!prompt.trim()) return;

    // Unit selected → dispatch directly to that agent
    if (selectedUnit) {
      try {
        await createJob({ prompt, agent: selectedUnit.profile });
      } catch (err) {
        console.error('Failed to dispatch job:', err);
      }
      return;
    }

    // Building selected → dispatch to the building's default agent
    if (selectedBuilding) {
      const agent = BUILDING_AGENT[selectedBuilding.buildingData.type] ?? 'ralph';
      try {
        await createJob({ prompt, agent });
      } catch (err) {
        console.error('Failed to dispatch job to building agent:', err);
      }
      return;
    }

    // Nothing selected → spawn villager(s)
    for (let i = 0; i < villagerCount; i++) {
      try {
        await createJob({ prompt, agent: 'villager' });
      } catch (err) {
        console.error('Failed to dispatch villager job:', err);
      }
    }
  }, [selectedUnit, selectedBuilding]);

  const handlePlaceBuilding = useCallback((type: BuildingType, name: string) => {
    if (!rightClickTile) return;
    const id = `building-${type}-${++buildingIdCounter}`;
    placeBuilding({
      id,
      type,
      status: 'idle',
      col: rightClickTile.col,
      row: rightClickTile.row,
      name,
    });
    setRightClickTile(null);
  }, [rightClickTile, placeBuilding, setRightClickTile]);

  const promptPlaceholder = selectedUnit
    ? `Dispatch to ${selectedUnit.profile}...`
    : selectedBuilding
      ? `Dispatch to ${BUILDING_AGENT[selectedBuilding.buildingData.type]} via ${BUILDING_DISPLAY_NAMES[selectedBuilding.buildingData.type]}...`
      : 'Type a goal and press Enter to dispatch...';

  return (
    <div className="relative w-full h-full overflow-hidden" style={{ background: '#1a1208' }}>
      {/* Phaser canvas layer */}
      <PhaserGame onReady={handleSceneReady} />

      {/* HUD overlay */}
      <HUD />

      {/* Age panel button */}
      <button
        onClick={() => setAgePanelVisible(v => !v)}
        className="absolute top-10 right-2 z-10 px-2 py-1"
        style={{
          background: 'rgba(26,18,8,0.9)',
          border: '1px solid #6b5320',
          color: '#c8a84b',
          fontSize: '10px',
          fontFamily: 'Courier New',
          cursor: 'pointer',
        }}
      >
        AGE &#9876;
      </button>

      <AgePanel visible={agePanelVisible} onClose={() => setAgePanelVisible(false)} />

      {/* Bottom selection panel */}
      <BottomPanel
        selectedUnit={selectedUnit}
        selectedBuilding={selectedBuilding}
        tasksByBuilding={tasksByBuilding}
        onDispatch={handlePromptSubmit}
      />

      {/* Prompt bar */}
      <PromptBar onSubmit={handlePromptSubmit} placeholder={promptPlaceholder} />

      {/* Build menu (appears on right-click empty tile) */}
      {rightClickTile && (
        <BuildMenu
          col={rightClickTile.col}
          row={rightClickTile.row}
          onPlace={handlePlaceBuilding}
          onClose={() => setRightClickTile(null)}
        />
      )}
    </div>
  );
}
