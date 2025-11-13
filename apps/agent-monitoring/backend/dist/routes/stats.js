"use strict";
/**
 * Statistics routes
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createStatsRouter = createStatsRouter;
const express_1 = require("express");
function createStatsRouter(dbService) {
    const router = (0, express_1.Router)();
    // GET /api/stats - Get system statistics
    router.get('/', (_req, res) => {
        try {
            const stats = dbService.getSystemStats();
            res.json({
                status: 'success',
                stats
            });
        }
        catch (error) {
            res.status(500).json({
                status: 'error',
                message: error.message
            });
        }
    });
    // GET /api/stats/tool-usage - Get tool usage statistics
    router.get('/tool-usage', (req, res) => {
        try {
            const agentId = req.query.agentId;
            const limit = req.query.limit ? parseInt(req.query.limit) : 20;
            const toolUsage = dbService.getToolUsage(agentId, limit);
            res.json({
                status: 'success',
                count: toolUsage.length,
                toolUsage
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
//# sourceMappingURL=stats.js.map