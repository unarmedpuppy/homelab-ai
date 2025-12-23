import type { Server as SocketIOServer, Socket } from 'socket.io';
import type { DeviceManager } from '../services/deviceManager.js';

export function setupDeviceSocket(
  io: SocketIOServer,
  deviceManager: DeviceManager
): void {
  io.on('connection', (socket: Socket) => {
    console.log('Client connected:', socket.id);

    // Send initial device states
    const devices = deviceManager.getAllDevices();
    socket.emit('devices:initial', devices);

    // Subscribe to specific devices
    socket.on('devices:subscribe', (deviceIds: string[]) => {
      deviceIds.forEach((id) => {
        socket.join(`device:${id}`);
      });
      console.log(`Client ${socket.id} subscribed to devices:`, deviceIds);
    });

    // Unsubscribe from devices
    socket.on('devices:unsubscribe', (deviceIds: string[]) => {
      deviceIds.forEach((id) => {
        socket.leave(`device:${id}`);
      });
    });

    // Handle device toggle
    socket.on(
      'device:toggle',
      async (deviceId: string, callback: (result: { success: boolean; device?: unknown; error?: string }) => void) => {
        try {
          await deviceManager.toggleDevice(deviceId);
          const device = deviceManager.getDevice(deviceId);
          callback({ success: true, device });
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          callback({ success: false, error: message });
        }
      }
    );

    // Handle device state change
    socket.on(
      'device:setState',
      async (
        data: { deviceId: string; property: string; value: unknown },
        callback: (result: { success: boolean; device?: unknown; error?: string }) => void
      ) => {
        try {
          await deviceManager.setDeviceState(
            data.deviceId,
            data.property,
            data.value
          );
          const device = deviceManager.getDevice(data.deviceId);
          callback({ success: true, device });
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          callback({ success: false, error: message });
        }
      }
    );

    // Handle disconnect
    socket.on('disconnect', () => {
      console.log('Client disconnected:', socket.id);
    });
  });

  // Broadcast device state changes from Home Assistant
  deviceManager.on('deviceStateChanged', (device: unknown) => {
    const d = device as { id: string };
    io.to(`device:${d.id}`).emit('device:stateChanged', device);
    io.emit('device:updated', device);
  });

  deviceManager.on('deviceRegistered', (device: unknown) => {
    io.emit('device:registered', device);
  });

  deviceManager.on('devicePositionUpdated', (device: unknown) => {
    io.emit('device:positionUpdated', device);
  });
}
