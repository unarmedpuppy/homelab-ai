"use strict";
/**
 * Statistics routes
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createStatsRouter = createStatsRouter;
const express_1 = require("express");
const cache_1 = require("../utils/cache");
function createStatsRouter(dbService) {
    const router = (0, express_1.Router)();
    // GET /api/stats - Get system statistics (cached for 5 seconds)
    router.get('/', (_req, res) => {
        try {
            const cached = cache_1.cache.get('system_stats');
            if (cached) {
                return res.json({
                    status: 'success',
                    stats: cached,
                    cached: true
                });
            }
            const stats = dbService.getSystemStats();
            cache_1.cache.set('system_stats', stats, 5000); // Cache for 5 seconds
            return res.json({
                status: 'success',
                stats
            });
        }
        catch (error) {
            return res.status(500).json({
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