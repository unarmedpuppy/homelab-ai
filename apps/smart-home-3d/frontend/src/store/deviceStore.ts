import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type { Device, DeviceState } from '../types';

interface DeviceStore {
  devices: Map<string, Device>;
  selectedDeviceId: string | null;
  isInitialized: boolean;

  // Actions
  setDevices: (devices: Device[]) => void;
  updateDevice: (deviceId: string, state: Partial<DeviceState>) => void;
  selectDevice: (deviceId: string | null) => void;
  getDevice: (deviceId: string) => Device | undefined;
  getDevicesByRoom: (roomId: string) => Device[];
  initialize: () => void;
}

export const useDeviceStore = create<DeviceStore>()(
  subscribeWithSelector((set, get) => ({
    devices: new Map(),
    selectedDeviceId: null,
    isInitialized: false,

    setDevices: (devices: Device[]) => {
      const map = new Map(devices.map((d) => [d.id, d]));
      set({ devices: map, isInitialized: true });
    },

    updateDevice: (deviceId: string, stateUpdate: Partial<DeviceState>) => {
      set((state) => {
        const device = state.devices.get(deviceId);
        if (!device) return state;

        const updatedDevice: Device = {
          ...device,
          state: { ...device.state, ...stateUpdate },
          lastUpdated: new Date(),
        };

        const newDevices = new Map(state.devices);
        newDevices.set(deviceId, updatedDevice);

        return { devices: newDevices };
      });
    },

    selectDevice: (deviceId: string | null) => {
      set({ selectedDeviceId: deviceId });
    },

    getDevice: (deviceId: string) => {
      return get().devices.get(deviceId);
    },

    getDevicesByRoom: (roomId: string) => {
      return Array.from(get().devices.values()).filter(
        (device) => device.roomId === roomId
      );
    },

    initialize: () => {
      set({ isInitialized: true });
    },
  }))
);
