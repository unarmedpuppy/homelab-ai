/**
 * Agent routes
 */

import { Router, Request, Response } from 'express';
import { DatabaseService } from '../services/database';
import { AgentDetails } from '../types';

export function createAgentsRouter(dbService: DatabaseService): Router {
  const router = Router();

  // GET /api/agents - List all agents
  router.get('/', (req: Request, res: Response) => {
    try {
      const status = req.query.status as string | undefined;
      
      let agents;
      if (status) {
        agents = dbService.getAgentsByStatus(status);
      } else {
        agents = dbService.getAllAgents();
      }

      res.json({
        status: 'success',
        count: agents.length,
        agents
      });
    } catch (error: any) {
      res.status(500).json({
        status: 'error',
        message: error.message
      });
    }
  });

  // GET /api/agents/:id - Get agent details
  router.get('/:id', (req: Request, res: Response) => {
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
      const taskHistory: any[] = [];

      const agentDetails: AgentDetails = {
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
    } catch (error: any) {
      res.status(500).json({
        status: 'error',
        message: error.message
      });
    }
  });

  return router;
}

