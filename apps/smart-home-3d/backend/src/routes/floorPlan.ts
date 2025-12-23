import { Router, Request, Response } from 'express';

// In-memory storage for now - will be replaced with Prisma
let floorPlan: any = null;

export function createFloorPlanRoutes() {
  const router = Router();

  // Get current floor plan
  router.get('/', (_req: Request, res: Response) => {
    if (!floorPlan) {
      return res.status(404).json({ error: 'No floor plan configured' });
    }
    res.json(floorPlan);
  });

  // Save floor plan
  router.post('/', (req: Request, res: Response) => {
    floorPlan = {
      ...req.body,
      id: req.body.id || crypto.randomUUID(),
      updatedAt: new Date(),
    };
    res.json(floorPlan);
  });

  // Update floor plan
  router.put('/:id', (req: Request, res: Response) => {
    if (!floorPlan || floorPlan.id !== req.params.id) {
      return res.status(404).json({ error: 'Floor plan not found' });
    }

    floorPlan = {
      ...floorPlan,
      ...req.body,
      id: req.params.id,
      updatedAt: new Date(),
    };
    res.json(floorPlan);
  });

  // Get specific room
  router.get('/rooms/:roomId', (req: Request, res: Response) => {
    if (!floorPlan) {
      return res.status(404).json({ error: 'No floor plan configured' });
    }

    for (const level of floorPlan.levels) {
      const room = level.rooms.find((r: any) => r.id === req.params.roomId);
      if (room) {
        return res.json(room);
      }
    }

    res.status(404).json({ error: 'Room not found' });
  });

  // Update room
  router.put('/rooms/:roomId', (req: Request, res: Response) => {
    if (!floorPlan) {
      return res.status(404).json({ error: 'No floor plan configured' });
    }

    for (const level of floorPlan.levels) {
      const roomIndex = level.rooms.findIndex((r: any) => r.id === req.params.roomId);
      if (roomIndex >= 0) {
        level.rooms[roomIndex] = {
          ...level.rooms[roomIndex],
          ...req.body,
          id: req.params.roomId,
        };
        floorPlan.updatedAt = new Date();
        return res.json(level.rooms[roomIndex]);
      }
    }

    res.status(404).json({ error: 'Room not found' });
  });

  // Add device location to room
  router.post('/rooms/:roomId/devices', (req: Request, res: Response) => {
    if (!floorPlan) {
      return res.status(404).json({ error: 'No floor plan configured' });
    }

    for (const level of floorPlan.levels) {
      const room = level.rooms.find((r: any) => r.id === req.params.roomId);
      if (room) {
        const { deviceId, position, rotation = 0 } = req.body;

        if (!deviceId || !position) {
          return res.status(400).json({ error: 'deviceId and position are required' });
        }

        // Remove existing device location if present
        room.devices = room.devices.filter((d: any) => d.deviceId !== deviceId);

        // Add new location
        room.devices.push({ deviceId, position, rotation });
        floorPlan.updatedAt = new Date();

        return res.json(room);
      }
    }

    res.status(404).json({ error: 'Room not found' });
  });

  // Remove device from room
  router.delete('/rooms/:roomId/devices/:deviceId', (req: Request, res: Response) => {
    if (!floorPlan) {
      return res.status(404).json({ error: 'No floor plan configured' });
    }

    for (const level of floorPlan.levels) {
      const room = level.rooms.find((r: any) => r.id === req.params.roomId);
      if (room) {
        room.devices = room.devices.filter((d: any) => d.deviceId !== req.params.deviceId);
        floorPlan.updatedAt = new Date();
        return res.json(room);
      }
    }

    res.status(404).json({ error: 'Room not found' });
  });

  return router;
}
