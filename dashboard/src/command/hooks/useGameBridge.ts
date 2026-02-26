import { useEffect, useState, useCallback } from 'react';
import { EventBus } from '../game/EventBus';
import type { UnitProfile, UnitStatus, BuildingData } from '../types/game';

export interface SelectedUnit {
  unitId: string;
  profile: UnitProfile;
  status: UnitStatus;
}

export interface SelectedBuilding {
  buildingId: string;
  buildingData: BuildingData;
}

export function useGameBridge() {
  const [selectedUnit, setSelectedUnit] = useState<SelectedUnit | null>(null);
  const [selectedBuilding, setSelectedBuilding] = useState<SelectedBuilding | null>(null);
  const [rightClickTile, setRightClickTile] = useState<{ col: number; row: number } | null>(null);

  useEffect(() => {
    const onUnitSelected = (data: SelectedUnit) => {
      setSelectedUnit(data);
      setSelectedBuilding(null);
    };
    const onBuildingSelected = (data: SelectedBuilding) => {
      setSelectedBuilding(data);
      setSelectedUnit(null);
    };
    const onCleared = () => {
      setSelectedUnit(null);
      setSelectedBuilding(null);
    };
    const onRightClick = (data: { col: number; row: number }) => {
      setRightClickTile(data);
    };

    EventBus.on('unit-selected', onUnitSelected);
    EventBus.on('building-selected', onBuildingSelected);
    EventBus.on('selection-cleared', onCleared);
    EventBus.on('right-click-empty', onRightClick);

    return () => {
      EventBus.off('unit-selected', onUnitSelected);
      EventBus.off('building-selected', onBuildingSelected);
      EventBus.off('selection-cleared', onCleared);
      EventBus.off('right-click-empty', onRightClick);
    };
  }, []);

  const dispatchJob = useCallback((payload: {
    unitId?: string;
    buildingId?: string;
    prompt: string;
  }) => {
    EventBus.emit('dispatch-job-to-building', payload);
  }, []);

  const placeBuilding = useCallback((data: BuildingData) => {
    EventBus.emit('place-building', data);
  }, []);

  const syncJobs = useCallback((jobs: Array<{ id: string; status: string; agent?: string }>) => {
    EventBus.emit('sync-jobs', jobs);
  }, []);

  return {
    selectedUnit,
    selectedBuilding,
    rightClickTile,
    setRightClickTile,
    dispatchJob,
    placeBuilding,
    syncJobs,
  };
}
