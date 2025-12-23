import { create } from 'zustand';
import type { FloorPlan, FloorLevel } from '../types';

type ViewMode = '3d' | 'top-down' | 'first-person';

interface SceneStore {
  floorPlan: FloorPlan | null;
  activeLevel: FloorLevel | null;
  viewMode: ViewMode;
  cameraPosition: [number, number, number];
  isLoading: boolean;
  error: string | null;

  // Actions
  setFloorPlan: (floorPlan: FloorPlan) => void;
  setActiveLevel: (levelId: string) => void;
  setViewMode: (mode: ViewMode) => void;
  setCameraPosition: (position: [number, number, number]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialCameraPosition: [number, number, number] = [10, 15, 10];

export const useSceneStore = create<SceneStore>((set, get) => ({
  floorPlan: null,
  activeLevel: null,
  viewMode: '3d',
  cameraPosition: initialCameraPosition,
  isLoading: false,
  error: null,

  setFloorPlan: (floorPlan: FloorPlan) => {
    const activeLevel = floorPlan.levels[0] || null;
    set({ floorPlan, activeLevel, error: null });
  },

  setActiveLevel: (levelId: string) => {
    const { floorPlan } = get();
    if (!floorPlan) return;

    const level = floorPlan.levels.find((l) => l.id === levelId);
    if (level) {
      set({ activeLevel: level });
    }
  },

  setViewMode: (viewMode: ViewMode) => {
    let cameraPosition = get().cameraPosition;

    // Adjust camera based on view mode
    switch (viewMode) {
      case 'top-down':
        cameraPosition = [0, 20, 0];
        break;
      case 'first-person':
        cameraPosition = [0, 1.7, 0]; // Eye level
        break;
      case '3d':
      default:
        cameraPosition = initialCameraPosition;
    }

    set({ viewMode, cameraPosition });
  },

  setCameraPosition: (cameraPosition: [number, number, number]) => {
    set({ cameraPosition });
  },

  setLoading: (isLoading: boolean) => {
    set({ isLoading });
  },

  setError: (error: string | null) => {
    set({ error, isLoading: false });
  },

  reset: () => {
    set({
      floorPlan: null,
      activeLevel: null,
      viewMode: '3d',
      cameraPosition: initialCameraPosition,
      isLoading: false,
      error: null,
    });
  },
}));
