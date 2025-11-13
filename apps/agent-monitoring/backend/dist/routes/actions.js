"use strict";
/**
 * Action routes
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createActionsRouter = createActionsRouter;
const express_1 = require("express");
function createActionsRouter(dbService) {
    const router = (0, express_1.Router)();
    // GET /api/actions - Get actions with filters
    router.get('/', (req, res) => {
        try {
            const options = {
                limit: req.query.limit ? parseInt(req.query.limit) : 100,
                offset: req.query.offset ? parseInt(req.query.offset) : 0,
                agentId: req.query.agentId,
                actionType: req.query.actionType,
                toolName: req.query.toolName,
                startTime: req.query.startTime,
                endTime: req.query.endTime
            };
            // Validate numeric inputs
            if (isNaN(options.limit) || options.limit < 1) {
                res.status(400).json({
                    status: 'error',
                    message: 'Invalid limit parameter (must be >= 1)'
                });
                return;
            }
            if (isNaN(options.offset) || options.offset < 0) {
                res.status(400).json({
                    status: 'error',
                    message: 'Invalid offset parameter (must be >= 0)'
                });
                return;
            }
            const actions = dbService.getActions(options);
            res.json({
                status: 'success',
                count: actions.length,
                actions
            });
        }
        catch (error) {
            res.status(500).json({
                status: 'error',
                message: error.message
            });
        }
    });
    // GET /api/actions/recent - Get recent actions (last 24h)
    router.get('/recent', (_req, res) => {
        try {
            const actions = dbService.getActionsLast24h();
            res.json({
                status: 'success',
                count: actions.length,
                actions
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
//# sourceMappingURL=actions.js.map