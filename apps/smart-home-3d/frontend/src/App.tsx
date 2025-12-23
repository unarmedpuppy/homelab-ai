import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Scene } from './components/3d';
import { Dashboard } from './components/ui';
import { useSceneStore, useDeviceStore } from './store';
import type { FloorPlan } from './types';

const queryClient = new QueryClient();

// Demo floor plan for testing
const demoFloorPlan: FloorPlan = {
  id: 'demo-1',
  name: 'Demo Home',
  scale: 50,
  levels: [
    {
      id: 'ground',
      name: 'Ground Floor',
      elevation: 0,
      rooms: [
        {
          id: 'living-room',
          name: 'Living Room',
          outline: [
            { x: 0, y: 0 },
            { x: 6, y: 0 },
            { x: 6, y: 5 },
            { x: 0, y: 5 },
          ],
          area: 30,
          ceilingHeight: 2.7,
          floorThickness: 0.2,
          walls: [
            { id: 'w1', start: { x: 0, y: 0 }, end: { x: 6, y: 0 }, height: 2.7, thickness: 0.15, type: 'exterior' },
            { id: 'w2', start: { x: 6, y: 0 }, end: { x: 6, y: 5 }, height: 2.7, thickness: 0.15, type: 'exterior' },
            { id: 'w3', start: { x: 6, y: 5 }, end: { x: 0, y: 5 }, height: 2.7, thickness: 0.15, type: 'interior' },
            { id: 'w4', start: { x: 0, y: 5 }, end: { x: 0, y: 0 }, height: 2.7, thickness: 0.15, type: 'exterior' },
          ],
          doors: [
            { id: 'd1', position: { x: 3, y: 5 }, width: 0.9, height: 2.1, rotation: 0, type: 'standard' },
          ],
          windows: [
            { id: 'win1', position: { x: 0, y: 2.5 }, width: 1.5, height: 1.2, elevation: 1.0 },
            { id: 'win2', position: { x: 6, y: 2.5 }, width: 1.5, height: 1.2, elevation: 1.0 },
          ],
          devices: [
            { deviceId: 'light-1', position: { x: 3, y: 2.5, z: 2.5 }, rotation: 0 },
            { deviceId: 'sensor-1', position: { x: 5.5, y: 0.5, z: 1.5 }, rotation: 0 },
          ],
          textures: {},
        },
        {
          id: 'kitchen',
          name: 'Kitchen',
          outline: [
            { x: 0, y: 5 },
            { x: 4, y: 5 },
            { x: 4, y: 9 },
            { x: 0, y: 9 },
          ],
          area: 16,
          ceilingHeight: 2.7,
          floorThickness: 0.2,
          walls: [
            { id: 'kw1', start: { x: 0, y: 5 }, end: { x: 4, y: 5 }, height: 2.7, thickness: 0.15, type: 'interior' },
            { id: 'kw2', start: { x: 4, y: 5 }, end: { x: 4, y: 9 }, height: 2.7, thickness: 0.15, type: 'interior' },
            { id: 'kw3', start: { x: 4, y: 9 }, end: { x: 0, y: 9 }, height: 2.7, thickness: 0.15, type: 'exterior' },
            { id: 'kw4', start: { x: 0, y: 9 }, end: { x: 0, y: 5 }, height: 2.7, thickness: 0.15, type: 'exterior' },
          ],
          doors: [],
          windows: [
            { id: 'kwin1', position: { x: 0, y: 7 }, width: 1.2, height: 1.0, elevation: 1.2 },
          ],
          devices: [
            { deviceId: 'light-2', position: { x: 2, y: 7, z: 2.5 }, rotation: 0 },
            { deviceId: 'thermostat-1', position: { x: 3.5, y: 5.5, z: 1.5 }, rotation: 0 },
          ],
          textures: {},
        },
      ],
    },
  ],
  createdAt: new Date(),
  updatedAt: new Date(),
};

// Demo devices for testing
const demoDevices = [
  {
    id: 'light-1',
    entityId: 'light.living_room',
    name: 'Living Room Light',
    type: 'light' as const,
    roomId: 'living-room',
    position: { x: 3, y: 2.5, z: 2.5 },
    rotation: 0,
    state: { on: true, brightness: 80 },
    capabilities: [{ type: 'toggle' as const }, { type: 'brightness' as const, min: 0, max: 100 }],
    lastUpdated: new Date(),
    integration: 'home-assistant' as const,
  },
  {
    id: 'light-2',
    entityId: 'light.kitchen',
    name: 'Kitchen Light',
    type: 'light' as const,
    roomId: 'kitchen',
    position: { x: 2, y: 7, z: 2.5 },
    rotation: 0,
    state: { on: false, brightness: 0 },
    capabilities: [{ type: 'toggle' as const }, { type: 'brightness' as const, min: 0, max: 100 }],
    lastUpdated: new Date(),
    integration: 'home-assistant' as const,
  },
  {
    id: 'sensor-1',
    entityId: 'sensor.living_room_temp',
    name: 'Living Room Sensor',
    type: 'sensor' as const,
    roomId: 'living-room',
    position: { x: 5.5, y: 0.5, z: 1.5 },
    rotation: 0,
    state: { on: true, temperature: 22.5, humidity: 45 },
    capabilities: [],
    lastUpdated: new Date(),
    integration: 'home-assistant' as const,
  },
  {
    id: 'thermostat-1',
    entityId: 'climate.kitchen',
    name: 'Kitchen Thermostat',
    type: 'thermostat' as const,
    roomId: 'kitchen',
    position: { x: 3.5, y: 5.5, z: 1.5 },
    rotation: 0,
    state: { on: true, temperature: 21 },
    capabilities: [{ type: 'temperature' as const, min: 15, max: 30 }],
    lastUpdated: new Date(),
    integration: 'home-assistant' as const,
  },
];

function AppContent() {
  const { setFloorPlan, isLoading, error } = useSceneStore();
  const { setDevices } = useDeviceStore();

  useEffect(() => {
    // Load demo data for now
    // In production, this would fetch from the API
    setFloorPlan(demoFloorPlan);
    setDevices(demoDevices);
  }, [setFloorPlan, setDevices]);

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-dark-300 text-white">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Error Loading Scene</h1>
          <p className="text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-dark-300 flex">
      {/* 3D Scene */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-dark-300/80 z-10">
            <div className="text-white">Loading...</div>
          </div>
        )}
        <Scene />
      </div>

      {/* Dashboard Sidebar */}
      <Dashboard />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
