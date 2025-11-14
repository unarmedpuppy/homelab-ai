"use strict";
/**
 * Session routes
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createSessionsRouter = createSessionsRouter;
const express_1 = require("express");
function createSessionsRouter(dbService) {
    const router = (0, express_1.Router)();
    // POST /api/sessions - Start a new session
    router.post('/', (req, res) => {
        try {
            const { agent_id } = req.body;
            // Validate required fields
            if (!agent_id) {
                res.status(400).json({
                    status: 'error',
                    message: 'agent_id is required'
                });
                return;
            }
            const sessionId = dbService.startSession(agent_id);
            res.status(201).json({
                status: 'success',
                session_id: sessionId,
                message: 'Session started successfully'
            });
        }
        catch (error) {
            res.status(500).json({
                status: 'error',
                message: error.message
            });
        }
    });
    // POST /api/sessions/end - End a session
    router.post('/end', (req, res) => {
        try {
            const { agent_id, tasks_completed = 0, tools_called = 0 } = req.body;
            // Validate required fields
            if (!agent_id) {
                res.status(400).json({
                    status: 'error',
                    message: 'agent_id is required'
                });
                return;
            }
            dbService.endSession(agent_id, tasks_completed, tools_called);
            res.json({
                status: 'success',
                message: 'Session ended successfully'
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
//# sourceMappingURL=sessions.js.map