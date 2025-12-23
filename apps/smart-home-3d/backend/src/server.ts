import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import { config } from 'dotenv';
import { createDeviceRoutes } from './routes/devices.js';
import { createFloorPlanRoutes } from './routes/floorPlan.js';
import { createHistoryRoutes } from './routes/history.js';
import { DeviceManager } from './services/deviceManager.js';
import { HomeAssistantService } from './services/homeAssistant.js';
import { HistoryService } from './services/historyService.js';
import { setupDeviceSocket } from './socket/deviceSocket.js';

config();

const PORT = process.env.PORT || 3001;
const HA_URL = process.env.HOME_ASSISTANT_URL || 'http://homeassistant:8123';
const HA_TOKEN = process.env.HOME_ASSISTANT_TOKEN || '';

async function main() {
  const app = express();
  const httpServer = createServer(app);

  // Socket.IO setup
  const io = new SocketIOServer(httpServer, {
    cors: {
      origin: process.env.CORS_ORIGIN || '*',
      methods: ['GET', 'POST'],
    },
  });

  // Middleware
  app.use(cors());
  app.use(express.json());

  // Health check
  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  // Initialize services
  const haService = new HomeAssistantService(HA_URL, HA_TOKEN);
  const historyService = new HistoryService();
  const deviceManager = new DeviceManager(haService, historyService);

  // Setup routes
  app.use('/api/devices', createDeviceRoutes(deviceManager));
  app.use('/api/floor-plan', createFloorPlanRoutes());
  app.use('/api/history', createHistoryRoutes(historyService));

  // Setup WebSocket
  setupDeviceSocket(io, deviceManager);

  // Start server
  httpServer.listen(PORT, () => {
    console.log(`Smart Home 3D server running on port ${PORT}`);
    console.log(`Home Assistant: ${HA_URL}`);
  });

  // Connect to Home Assistant
  if (HA_TOKEN) {
    try {
      await haService.connect();
      console.log('Connected to Home Assistant');

      // Load devices from Home Assistant
      await deviceManager.syncDevices();
    } catch (error) {
      console.error('Failed to connect to Home Assistant:', error);
    }
  } else {
    console.warn('No Home Assistant token provided - running in demo mode');
  }
}

main().catch(console.error);
