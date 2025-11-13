/**
 * Agent Monitoring Backend API
 * Node.js + Express + TypeScript
 */

import express, { Express } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { DatabaseService } from './services/database';
import { InfluxDBService } from './services/influxdb';
import {
  createAgentsRouter,
  createActionsRouter,
  createStatsRouter,
  createTasksRouter,
  createInfluxDBRouter
} from './routes';

// Load environment variables
dotenv.config();

const app: Express = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Database service
// Default path: apps/agent-monitoring/data/agent_activity.db
// When running from dist/, __dirname is dist/, so we go up to backend, then to agent-monitoring
let defaultDbPath = process.env.DATABASE_PATH;
if (!defaultDbPath) {
  // Resolve relative to project root for consistency
  // From dist/ -> backend/ -> agent-monitoring/ -> data/
  defaultDbPath = path.join(__dirname, '../../data/agent_activity.db');
  // Resolve to absolute path
  defaultDbPath = path.resolve(defaultDbPath);
}
const dbService = new DatabaseService(defaultDbPath);
console.log(`📊 Database path: ${defaultDbPath}`);

// InfluxDB service (optional)
let influxService: InfluxDBService | null = null;
if (process.env.INFLUXDB_URL && process.env.INFLUXDB_TOKEN) {
  try {
    influxService = new InfluxDBService(
      process.env.INFLUXDB_URL,
      process.env.INFLUXDB_TOKEN,
      process.env.INFLUXDB_ORG || 'home-server',
      process.env.INFLUXDB_DATABASE || 'agent_metrics',
      dbService
    );
    console.log('✅ InfluxDB service initialized');
  } catch (error) {
    console.warn('⚠️  InfluxDB not configured:', error);
  }
} else {
  console.log('ℹ️  InfluxDB not configured (optional)');
}

// Routes
app.use('/api/agents', createAgentsRouter(dbService));
app.use('/api/actions', createActionsRouter(dbService));
app.use('/api/stats', createStatsRouter(dbService));
app.use('/api/tasks', createTasksRouter());
app.use('/api/influxdb', createInfluxDBRouter(influxService));

// Health check
app.get('/health', (_req, res) => {
  res.json({
    status: 'ok',
    service: 'agent-monitoring-backend',
    timestamp: new Date().toISOString()
  });
});

// Root endpoint
app.get('/', (_req, res) => {
  res.json({
    service: 'agent-monitoring-backend',
    version: '0.1.0',
    endpoints: {
      agents: '/api/agents',
      actions: '/api/actions',
      stats: '/api/stats',
      tasks: '/api/tasks',
      influxdb: '/api/influxdb',
      health: '/health'
    }
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Agent Monitoring Backend running on port ${PORT}`);
  console.log(`📊 Database: ${defaultDbPath}`);
  console.log(`🔗 API: http://localhost:${PORT}/api`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, closing connections...');
  dbService.close();
  if (influxService) {
    influxService.close();
  }
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received, closing connections...');
  dbService.close();
  if (influxService) {
    influxService.close();
  }
  process.exit(0);
});

