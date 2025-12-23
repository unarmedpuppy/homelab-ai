import { useDeviceStore } from '../../store';
import type { Device, DeviceType } from '../../types';

const deviceIcons: Record<DeviceType, string> = {
  light: '💡',
  switch: '🔘',
  sensor: '📡',
  thermostat: '🌡️',
  camera: '📹',
  lock: '🔐',
  blind: '🪟',
  speaker: '🔊',
  tv: '📺',
  other: '📱',
};

interface DeviceItemProps {
  device: Device;
  isSelected: boolean;
  onClick: () => void;
}

function DeviceItem({ device, isSelected, onClick }: DeviceItemProps) {
  const isOn = device.state.on;

  return (
    <button
      onClick={onClick}
      className={`w-full p-3 rounded-lg text-left transition-colors ${
        isSelected
          ? 'bg-primary-600 text-white'
          : 'bg-dark-100 text-gray-300 hover:bg-dark-100/80'
      }`}
    >
      <div className="flex items-center gap-3">
        <span className="text-xl">{deviceIcons[device.type]}</span>
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{device.name}</p>
          <p className="text-xs opacity-75">{device.type}</p>
        </div>
        <div
          className={`w-2 h-2 rounded-full ${
            isOn ? 'bg-green-400' : 'bg-gray-500'
          }`}
        />
      </div>
    </button>
  );
}

export function DeviceList() {
  const { devices, selectedDeviceId, selectDevice } = useDeviceStore();
  const deviceArray = Array.from(devices.values());

  // Group by room
  const devicesByRoom = deviceArray.reduce(
    (acc, device) => {
      const roomId = device.roomId || 'unknown';
      if (!acc[roomId]) acc[roomId] = [];
      acc[roomId].push(device);
      return acc;
    },
    {} as Record<string, Device[]>
  );

  if (deviceArray.length === 0) {
    return (
      <div className="text-center text-gray-400 py-8">
        <p>No devices found</p>
        <p className="text-sm mt-2">Connect to Home Assistant to see devices</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {Object.entries(devicesByRoom).map(([roomId, roomDevices]) => (
        <div key={roomId}>
          <h3 className="text-sm font-medium text-gray-400 mb-2 uppercase tracking-wide">
            {roomId}
          </h3>
          <div className="space-y-2">
            {roomDevices.map((device) => (
              <DeviceItem
                key={device.id}
                device={device}
                isSelected={selectedDeviceId === device.id}
                onClick={() =>
                  selectDevice(selectedDeviceId === device.id ? null : device.id)
                }
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
