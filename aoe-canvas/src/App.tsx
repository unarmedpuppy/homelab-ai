import { useRef, useState, useEffect, useCallback } from 'react';
import { PhaserGame } from './game/PhaserGame';
import { HUD } from './ui/HUD';
import { BottomPanel } from './ui/BottomPanel';
import { PromptBar } from './ui/PromptBar';
import { BuildMenu } from './ui/BuildMenu';
import { AgePanel } from './ui/AgePanel';
import { useGameBridge } from './hooks/useGameBridge';
import { useAgentJobs } from './hooks/useAgentJobs';
import { createJob } from './api/agentHarness';
import { BuildingType } from './types/game';
import type { MapScene } from './game/scenes/MapScene';

let buildingIdCounter = 100;

export default function App() {
  const sceneRef = useRef<MapScene | null>(null);
  const [agePanelVisible, setAgePanelVisible] = useState(false);
  const { data: jobs = [] } = useAgentJobs();

  const {
    selectedUnit,
    selectedBuilding,
    rightClickTile,
    setRightClickTile,
    dispatchJob,
    placeBuilding,
    syncJobs,
  } = useGameBridge();

  // Sync job state to game engine periodically
  useEffect(() => {
    if (jobs.length > 0) {
      syncJobs(jobs.map(j => ({ id: j.id, status: j.status, agent: j.agent })));
    }
  }, [jobs, syncJobs]);

  const handleSceneReady = useCallback((scene: MapScene) => {
    sceneRef.current = scene;
  }, []);

  const handlePromptSubmit = useCallback(async (prompt: string, villagerCount: number) => {
    // If a unit is selected, dispatch to that agent
    if (selectedUnit) {
      try {
        await createJob({
          prompt,
          agent: selectedUnit.profile,
        });
      } catch (err) {
        console.error('Failed to dispatch job:', err);
      }
      return;
    }

    // Otherwise spawn villager(s)
    for (let i = 0; i < villagerCount; i++) {
      try {
        await createJob({
          prompt,
          agent: 'villager',
        });
      } catch (err) {
        console.error('Failed to dispatch villager job:', err);
      }
    }
  }, [selectedUnit]);

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

  // Suppress unused warning for dispatchJob — available for imperative use
  void dispatchJob;

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
        onDispatch={handlePromptSubmit}
      />

      {/* Prompt bar */}
      <PromptBar onSubmit={handlePromptSubmit} />

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
