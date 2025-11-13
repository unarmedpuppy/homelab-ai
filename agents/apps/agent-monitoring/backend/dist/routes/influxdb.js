"use strict";
/**
 * InfluxDB export routes
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createInfluxDBRouter = createInfluxDBRouter;
const express_1 = require("express");
function createInfluxDBRouter(influxService) {
    const router = (0, express_1.Router)();
    // POST /api/influxdb/export - Export all metrics to InfluxDB
    router.post('/export', async (_req, res) => {
        if (!influxService) {
            res.status(503).json({
                status: 'error',
                message: 'InfluxDB not configured'
            });
            return;
        }
        try {
            const result = await influxService.exportAll();
            res.json({
                status: 'success',
                message: 'Metrics exported to InfluxDB',
                exported: result
            });
        }
        catch (error) {
            res.status(500).json({
                status: 'error',
                message: error.message
            });
        }
    });
    // POST /api/influxdb/export/actions - Export agent actions
    router.post('/export/actions', async (req, res) => {
        if (!influxService) {
            res.status(503).json({
                status: 'error',
                message: 'InfluxDB not configured'
            });
            return;
        }
        try {
            const hours = req.body.hours || 1;
            const count = await influxService.exportAgentActions(hours);
            res.json({
                status: 'success',
                message: `Exported ${count} actions to InfluxDB`,
                count
            });
        }
        catch (error) {
            res.status(500).json({
                status: 'error',
                message: error.message
            });
        }
    });
    // POST /api/influxdb/export/status - Export agent status
    router.post('/export/status', async (_req, res) => {
        if (!influxService) {
            res.status(503).json({
                status: 'error',
                message: 'InfluxDB not configured'
            });
            return;
        }
        try {
            const count = await influxService.exportAgentStatus();
            res.json({
                status: 'success',
                message: `Exported ${count} agent statuses to InfluxDB`,
                count
            });
        }
        catch (error) {
            res.status(500).json({
                status: 'error',
                message: error.message
            });
        }
    });
    return router;
}
//# sourceMappingURL=influxdb.js.map