import { Router, Request, Response } from 'express';
import type { DeviceManager } from '../services/deviceManager.js';

export function createDeviceRoutes(deviceManager: DeviceManager) {
  const router = Router();

  // Get all devices
  router.get('/', (_req: Request, res: Response) => {
    const devices = deviceManager.getAllDevices();
    res.json(devices);
  });

  // Get device by ID
  router.get('/:id', (req: Request, res: Response) => {
    const device = deviceManager.getDevice(req.params.id);
    if (!device) {
      return res.status(404).json({ error: 'Device not found' });
    }
    res.json(device);
  });

  // Get devices by room
  router.get('/room/:roomId', (req: Request, res: Response) => {
    const devices = deviceManager.getDevicesByRoom(req.params.roomId);
    res.json(devices);
  });

  // Toggle device
  router.post('/:id/toggle', async (req: Request, res: Response) => {
    try {
      await deviceManager.toggleDevice(req.params.id);
      const device = deviceManager.getDevice(req.params.id);
      res.json(device);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      res.status(400).json({ error: message });
    }
  });

  // Set device state
  router.put('/:id/state', async (req: Request, res: Response) => {
    try {
      const { property, value } = req.body;

      if (!property) {
        return res.status(400).json({ error: 'Property is required' });
      }

      await deviceManager.setDeviceState(req.params.id, property, value);
      const device = deviceManager.getDevice(req.params.id);
      res.json(device);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      res.status(400).json({ error: message });
    }
  });

  // Update device position (for floor plan mapping)
  router.put('/:id/position', (req: Request, res: Response) => {
    try {
      const { roomId, position } = req.body;

      if (!roomId || !position) {
        return res.status(400).json({ error: 'roomId and position are required' });
      }

      deviceManager.updateDevicePosition(req.params.id, roomId, position);
      const device = deviceManager.getDevice(req.params.id);
      res.json(device);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      res.status(400).json({ error: message });
    }
  });

  // Sync devices from Home Assistant
  router.post('/sync', async (_req: Request, res: Response) => {
    try {
      await deviceManager.syncDevices();
      const devices = deviceManager.getAllDevices();
      res.json({ synced: devices.length, devices });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      res.status(500).json({ error: message });
    }
  });

  return router;
}
