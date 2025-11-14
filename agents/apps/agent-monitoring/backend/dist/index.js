"use strict";
/**
 * Agent Monitoring Backend API
 * Node.js + Express + TypeScript
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const dotenv_1 = __importDefault(require("dotenv"));
const path_1 = __importDefault(require("path"));
const database_1 = require("./services/database");
const influxdb_1 = require("./services/influxdb");
const metricExporter_1 = require("./services/metricExporter");
const initDatabase_1 = require("./services/initDatabase");
const routes_1 = require("./routes");
// Load environment variables
dotenv_1.default.config();
const app = (0, express_1.default)();
const PORT = process.env.PORT || 3001;
// Middleware
app.use((0, cors_1.default)());
app.use(express_1.default.json());
// Request logging middleware (development)
if (process.env.NODE_ENV !== 'production') {
    app.use((req, _res, next) => {
        console.log(`${req.method} ${req.path}`);
        next();
    });
}
// Database service
// Default path: agents/apps/agent-monitoring/data/agent_activity.db
// When running from dist/, __dirname is dist/, so we go up to backend, then to agent-monitoring
let defaultDbPath = process.env.DATABASE_PATH;
if (!defaultDbPath) {
    // Resolve relative to project root for consistency
    // From dist/ -> backend/ -> agent-monitoring/ -> data/
    defaultDbPath = path_1.default.join(__dirname, '../../data/agent_activity.db');
    // Resolve to absolute path
    defaultDbPath = path_1.default.resolve(defaultDbPath);
}
// Initialize database schema if needed
(0, initDatabase_1.initializeDatabase)(defaultDbPath);
const dbService = new database_1.DatabaseService(defaultDbPath);
console.log(`📊 Database path: ${defaultDbPath}`);
// InfluxDB service (optional)
let influxService = null;
let metricExporter = null;
if (process.env.INFLUXDB_URL && process.env.INFLUXDB_TOKEN) {
    try {
        influxService = new influxdb_1.InfluxDBService(process.env.INFLUXDB_URL, process.env.INFLUXDB_TOKEN, process.env.INFLUXDB_ORG || 'home-server', process.env.INFLUXDB_DATABASE || 'agent_metrics', dbService);
        console.log('✅ InfluxDB service initialized');
        // Start automatic metric export
        metricExporter = new metricExporter_1.MetricExporter(influxService, dbService);
        const exportInterval = parseInt(process.env.METRIC_EXPORT_INTERVAL || '30000', 10);
        metricExporter.start(exportInterval);
    }
    catch (error) {
        console.warn('⚠️  InfluxDB not configured:', error);
    }
}
else {
    console.log('ℹ️  InfluxDB not configured (optional)');
}
// Routes
app.use('/api/agents', (0, routes_1.createAgentsRouter)(dbService));
app.use('/api/actions', (0, routes_1.createActionsRouter)(dbService));
app.use('/api/stats', (0, routes_1.createStatsRouter)(dbService));
app.use('/api/tasks', (0, routes_1.createTasksRouter)());
app.use('/api/influxdb', (0, routes_1.createInfluxDBRouter)(influxService));
app.use('/api/sessions', (0, routes_1.createSessionsRouter)(dbService));
app.use('/a2a', (0, routes_1.createA2ARouter)(dbService));
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
            a2a: '/a2a',
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
    if (metricExporter) {
        metricExporter.stop();
    }
    dbService.close();
    if (influxService) {
        influxService.close();
    }
    process.exit(0);
});
process.on('SIGINT', () => {
    console.log('SIGINT received, closing connections...');
    if (metricExporter) {
        metricExporter.stop();
    }
    dbService.close();
    if (influxService) {
        influxService.close();
    }
    process.exit(0);
});
//# sourceMappingURL=index.js.map