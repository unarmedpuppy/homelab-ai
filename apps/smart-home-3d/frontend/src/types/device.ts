export type DeviceType =
  | 'light'
  | 'switch'
  | 'sensor'
  | 'thermostat'
  | 'camera'
  | 'lock'
  | 'blind'
  | 'speaker'
  | 'tv'
  | 'other';

export type IntegrationType =
  | 'home-assistant'
  | 'hue'
  | 'zigbee2mqtt'
  | 'mqtt'
  | 'rest';

export interface DeviceState {
  on: boolean;
  brightness?: number; // 0-100
  color?: string; // hex
  temperature?: number; // Celsius
  humidity?: number; // percentage
  motion?: boolean;
  door?: 'open' | 'closed' | 'locked' | 'unlocked';
  position?: number; // percentage for blinds
  volume?: number; // 0-100
}

export interface DeviceCapability {
  type: 'toggle' | 'brightness' | 'color' | 'temperature' | 'position' | 'volume';
  min?: number;
  max?: number;
  step?: number;
}

export interface Device {
  id: string;
  entityId: string; // Home Assistant entity ID
  name: string;
  type: DeviceType;
  roomId: string;
  position: { x: number; y: number; z: number };
  rotation: number;
  state: DeviceState;
  capabilities: DeviceCapability[];
  lastUpdated: Date;
  integration: IntegrationType;
}

export interface DeviceEvent {
  deviceId: string;
  timestamp: Date;
  property: keyof DeviceState;
  oldValue: unknown;
  newValue: unknown;
}
