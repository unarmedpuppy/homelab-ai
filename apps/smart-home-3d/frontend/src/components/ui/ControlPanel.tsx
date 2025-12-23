import { useState } from 'react';
import type { Device } from '../../types';

interface ControlPanelProps {
  device: Device;
}

export function ControlPanel({ device }: ControlPanelProps) {
  const [isUpdating, setIsUpdating] = useState(false);

  const handleToggle = async () => {
    setIsUpdating(true);
    try {
      await fetch(`/api/devices/${device.id}/toggle`, { method: 'POST' });
    } catch (error) {
      console.error('Failed to toggle device:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleBrightnessChange = async (value: number) => {
    try {
      await fetch(`/api/devices/${device.id}/state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ property: 'brightness', value }),
      });
    } catch (error) {
      console.error('Failed to update brightness:', error);
    }
  };

  const canToggle = device.capabilities.some((c) => c.type === 'toggle');
  const canBrightness = device.capabilities.some((c) => c.type === 'brightness');
  const canColor = device.capabilities.some((c) => c.type === 'color');

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-white">{device.name}</h3>
        <span className="text-xs text-gray-400">{device.type}</span>
      </div>

      {/* Toggle */}
      {canToggle && (
        <div className="flex items-center justify-between">
          <span className="text-gray-300">Power</span>
          <button
            onClick={handleToggle}
            disabled={isUpdating}
            className={`relative w-14 h-7 rounded-full transition-colors ${
              device.state.on ? 'bg-primary-600' : 'bg-gray-600'
            } ${isUpdating ? 'opacity-50' : ''}`}
          >
            <span
              className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-transform ${
                device.state.on ? 'left-8' : 'left-1'
              }`}
            />
          </button>
        </div>
      )}

      {/* Brightness */}
      {canBrightness && device.state.on && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-300">Brightness</span>
            <span className="text-gray-400">{device.state.brightness || 0}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={device.state.brightness || 0}
            onChange={(e) => handleBrightnessChange(Number(e.target.value))}
            className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      )}

      {/* Color */}
      {canColor && device.state.on && (
        <div className="flex items-center justify-between">
          <span className="text-gray-300">Color</span>
          <input
            type="color"
            value={device.state.color || '#ffffff'}
            onChange={(e) => {
              fetch(`/api/devices/${device.id}/state`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ property: 'color', value: e.target.value }),
              });
            }}
            className="w-10 h-10 rounded cursor-pointer"
          />
        </div>
      )}

      {/* State info */}
      <div className="pt-4 border-t border-gray-700 text-sm text-gray-400">
        <p>Entity: {device.entityId}</p>
        <p>
          Last updated:{' '}
          {new Date(device.lastUpdated).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
