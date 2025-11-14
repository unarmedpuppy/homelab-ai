"use strict";
/**
 * Agent routes
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createAgentsRouter = createAgentsRouter;
const express_1 = require("express");
const cache_1 = require("../utils/cache");
function createAgentsRouter(dbService) {
    const router = (0, express_1.Router)();
    // GET /api/agents - List all agents (cached for 3 seconds)
    router.get('/', (req, res) => {
        try {
            const status = req.query.status;
            const cacheKey = status ? `agents_${status}` : 'agents_all';
            const cached = cache_1.cache.get(cacheKey);
            if (cached) {
                return res.json({
                    status: 'success',
                    count: cached.length,
                    agents: cached,
                    cached: true
                });
            }
            let agents;
            if (status) {
                agents = dbService.getAgentsByStatus(status);
            }
            else {
                agents = dbService.getAllAgents();
            }
            cache_1.cache.set(cacheKey, agents, 3000); // Cache for 3 seconds
            return res.json({
                status: 'success',
                count: agents.length,
                agents
            });
        }
        catch (error) {
            return res.status(500).json({
                status: 'error',
                message: error.message
            });
        }
    });
    // POST /api/agents/status - Update agent status
    router.post('/status', (req, res) => {
        try {
            const { agent_id, status, current_task_id, progress, blockers } = req.body;
            // Validate required fields
            if (!agent_id || !status) {
                res.status(400).json({
                    status: 'error',
                    message: 'agent_id and status are required'
                });
                return;
            }
            const statusId = dbService.updateAgentStatus(agent_id, status, current_task_id, progress, blockers);
            res.json({
                status: 'success',
                status_id: statusId,
                message: 'Agent status updated successfully'
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