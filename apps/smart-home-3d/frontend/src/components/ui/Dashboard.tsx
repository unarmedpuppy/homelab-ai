import { useDeviceStore, useSceneStore } from '../../store';
import { DeviceList } from './DeviceList';
import { ControlPanel } from './ControlPanel';

export function Dashboard() {
  const { selectedDeviceId, devices } = useDeviceStore();
  const { activeLevel, floorPlan, viewMode, setViewMode } = useSceneStore();

  const selectedDevice = selectedDeviceId ? devices.get(selectedDeviceId) : null;

  return (
    <div className="fixed top-0 right-0 h-full w-80 bg-dark-200/95 backdrop-blur-sm border-l border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-xl font-bold text-white">Smart Home 3D</h1>
        {floorPlan && (
          <p className="text-sm text-gray-400 mt-1">
            {activeLevel?.name || 'Select a level'}
          </p>
        )}
      </div>

      {/* View Mode Toggle */}
      <div className="p-4 border-b border-gray-700">
        <label className="text-sm text-gray-400 block mb-2">View Mode</label>
        <div className="flex gap-2">
          {(['3d', 'top-down', 'first-person'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === mode
                  ? 'bg-primary-600 text-white'
                  : 'bg-dark-100 text-gray-300 hover:bg-dark-100/80'
              }`}
            >
              {mode === '3d' ? '3D' : mode === 'top-down' ? 'Top' : 'FPS'}
            </button>
          ))}
        </div>
      </div>

      {/* Device List */}
      <div className="flex-1 overflow-y-auto p-4">
        <DeviceList />
      </div>

      {/* Control Panel (when device selected) */}
      {selectedDevice && (
        <div className="border-t border-gray-700">
          <ControlPanel device={selectedDevice} />
        </div>
      )}
    </div>
  );
}
