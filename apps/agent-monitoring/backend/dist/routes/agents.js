"use strict";
/**
 * Agent routes
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createAgentsRouter = createAgentsRouter;
const express_1 = require("express");
function createAgentsRouter(dbService) {
    const router = (0, express_1.Router)();
    // GET /api/agents - List all agents
    router.get('/', (req, res) => {
        try {
            const status = req.query.status;
            let agents;
            if (status) {
                agents = dbService.getAgentsByStatus(status);
            }
            else {
                agents = dbService.getAllAgents();
            }
            res.json({
                status: 'success',
                count: agents.length,
                agents
            });
        }
        catch (error) {
            res.status(500).json({
                status: 'error',
                message: error.message
            });
        }
    });
    // GET /api/agents/:id - Get agent details
    router.get('/:id', (req, res) => {
        try {
            const agentId = req.params.id;
            const agent = dbService.getAgentById(agentId);
            if (!agent) {
                res.status(404).json({
                    status: 'not_found',
                    message: `Agent ${agentId} not found`
                });
                return;
            }
            // Get additional details
            const recentActions = dbService.getActionsByAgent(agentId, 20);
            const toolUsage = dbService.getToolUsage(agentId, 10);
            const sessionStats = dbService.getSessionStats(agentId);
            // Task history would come from task coordination system
            // For now, return empty array
            const taskHistory = [];
            const agentDetails = {
                ...agent,
                recentActions,
                toolUsage,
                taskHistory,
                sessionStats
            };
            res.json({
                status: 'success',
                agent: agentDetails
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
//# sourceMappingURL=agents.js.map