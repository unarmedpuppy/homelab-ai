import { EventEmitter } from 'events';
import type { HomeAssistantService } from './homeAssistant.js';
import type { HistoryService } from './historyService.js';

interface DeviceState {
  on: boolean;
  brightness?: number;
  color?: string;
  temperature?: number;
  humidity?: number;
  motion?: boolean;
}

interface Device {
  id: string;
  entityId: string;
  name: string;
  type: string;
  roomId: string;
  position: { x: number; y: number; z: number };
  rotation: number;
  state: DeviceState;
  capabilities: { type: string; min?: number; max?: number }[];
  lastUpdated: Date;
  integration: string;
}

export class DeviceManager extends EventEmitter {
  private devices = new Map<string, Device>();

  constructor(
    private haService: HomeAssistantService,
    private historyService: HistoryService
  ) {
    super();
    this.setupListeners();
  }

  private setupListeners(): void {
    this.haService.on('state_changed', (event: { entityId: string; newState: any; oldState: any }) => {
      this.handleStateChange(event);
    });
  }

  private handleStateChange(event: { entityId: string; newState: any; oldState: any }): void {
    const device = this.getDeviceByEntityId(event.entityId);
    if (!device) return;

    const oldDeviceState = { ...device.state };
    const newDeviceState = this.parseHAState(event.newState);

    device.state = newDeviceState;
    device.lastUpdated = new Date();

    // Record history
    this.historyService.recordEvent({
      deviceId: device.id,
      timestamp: new Date(),
      property: 'state',
      oldValue: oldDeviceState,
      newValue: newDeviceState,
    });

    this.emit('deviceStateChanged', device);
  }

  private parseHAState(haState: any): DeviceState {
    const state: DeviceState = {
      on: haState.state === 'on',
    };

    const attrs = haState.attributes || {};

    if (attrs.brightness !== undefined) {
      state.brightness = Math.round((attrs.brightness / 255) * 100);
    }

    if (attrs.rgb_color) {
      const [r, g, b] = attrs.rgb_color;
      state.color = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }

    if (attrs.current_temperature !== undefined) {
      state.temperature = attrs.current_temperature;
    } else if (!isNaN(parseFloat(haState.state))) {
      state.temperature = parseFloat(haState.state);
    }

    if (attrs.humidity !== undefined) {
      state.humidity = attrs.humidity;
    }

    return state;
  }

  async syncDevices(): Promise<void> {
    try {
      const states = await this.haService.getStates();

      for (const state of states) {
        const device = this.createDeviceFromHA(state);
        if (device) {
          this.devices.set(device.id, device);
        }
      }

      console.log(`Synced ${this.devices.size} devices from Home Assistant`);
    } catch (error) {
      console.error('Failed to sync devices:', error);
    }
  }

  private createDeviceFromHA(haState: any): Device | null {
    const entityId = haState.entity_id;
    const [domain] = entityId.split('.');

    // Only handle supported domains
    const supportedDomains = ['light', 'switch', 'sensor', 'climate', 'binary_sensor', 'lock', 'cover'];
    if (!supportedDomains.includes(domain)) return null;

    const typeMap: Record<string, string> = {
      light: 'light',
      switch: 'switch',
      sensor: 'sensor',
      climate: 'thermostat',
      binary_sensor: 'sensor',
      lock: 'lock',
      cover: 'blind',
    };

    const capabilities = this.getCapabilities(domain, haState.attributes);

    return {
      id: entityId.replace('.', '-'),
      entityId,
      name: haState.attributes?.friendly_name || entityId,
      type: typeMap[domain] || 'other',
      roomId: 'unknown', // Would need floor plan mapping
      position: { x: 0, y: 0, z: 1 },
      rotation: 0,
      state: this.parseHAState(haState),
      capabilities,
      lastUpdated: new Date(haState.last_updated),
      integration: 'home-assistant',
    };
  }

  private getCapabilities(domain: string, attrs: any): { type: string; min?: number; max?: number }[] {
    const capabilities: { type: string; min?: number; max?: number }[] = [];

    if (['light', 'switch'].includes(domain)) {
      capabilities.push({ type: 'toggle' });
    }

    if (domain === 'light' && attrs?.supported_color_modes?.includes('brightness')) {
      capabilities.push({ type: 'brightness', min: 0, max: 100 });
    }

    if (domain === 'light' && attrs?.supported_color_modes?.some((m: string) => ['rgb', 'hs', 'xy'].includes(m))) {
      capabilities.push({ type: 'color' });
    }

    if (domain === 'climate') {
      capabilities.push({ type: 'temperature', min: 15, max: 30 });
    }

    if (domain === 'cover') {
      capabilities.push({ type: 'position', min: 0, max: 100 });
    }

    return capabilities;
  }

  getDeviceByEntityId(entityId: string): Device | undefined {
    return Array.from(this.devices.values()).find((d) => d.entityId === entityId);
  }

  getDevice(deviceId: string): Device | undefined {
    return this.devices.get(deviceId);
  }

  getAllDevices(): Device[] {
    return Array.from(this.devices.values());
  }

  getDevicesByRoom(roomId: string): Device[] {
    return this.getAllDevices().filter((d) => d.roomId === roomId);
  }

  async toggleDevice(deviceId: string): Promise<void> {
    const device = this.devices.get(deviceId);
    if (!device) throw new Error(`Device not found: ${deviceId}`);

    await this.haService.toggle(device.entityId);
  }

  async setDeviceState(deviceId: string, property: string, value: unknown): Promise<void> {
    const device = this.devices.get(deviceId);
    if (!device) throw new Error(`Device not found: ${deviceId}`);

    const [domain] = device.entityId.split('.');

    switch (property) {
      case 'on':
        if (value) {
          await this.haService.turnOn(device.entityId);
        } else {
          await this.haService.turnOff(device.entityId);
        }
        break;

      case 'brightness':
        await this.haService.turnOn(device.entityId, {
          brightness: Math.round(((value as number) / 100) * 255),
        });
        break;

      case 'color':
        const hex = (value as string).replace('#', '');
        const rgb = [
          parseInt(hex.substring(0, 2), 16),
          parseInt(hex.substring(2, 4), 16),
          parseInt(hex.substring(4, 6), 16),
        ];
        await this.haService.turnOn(device.entityId, { rgb_color: rgb });
        break;

      case 'temperature':
        await this.haService.callService(domain, 'set_temperature', device.entityId, {
          temperature: value,
        });
        break;

      case 'position':
        await this.haService.callService(domain, 'set_cover_position', device.entityId, {
          position: value,
        });
        break;
    }
  }

  registerDevice(device: Device): void {
    this.devices.set(device.id, device);
    this.emit('deviceRegistered', device);
  }

  updateDevicePosition(
    deviceId: string,
    roomId: string,
    position: { x: number; y: number; z: number }
  ): void {
    const device = this.devices.get(deviceId);
    if (device) {
      device.roomId = roomId;
      device.position = position;
      this.emit('devicePositionUpdated', device);
    }
  }
}
