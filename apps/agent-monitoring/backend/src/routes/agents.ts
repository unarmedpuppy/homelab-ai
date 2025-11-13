/**
 * Agent routes
 */

import { Router, Request, Response } from 'express';
import { DatabaseService } from '../services/database';
import { AgentDetails } from '../types';
import { cache } from '../utils/cache';

export function createAgentsRouter(dbService: DatabaseService): Router {
  const router = Router();

  // GET /api/agents - List all agents (cached for 3 seconds)
  router.get('/', (req: Request, res: Response) => {
    try {
      const status = req.query.status as string | undefined;
      const cacheKey = status ? `agents_${status}` : 'agents_all';
      
      const cached = cache.get(cacheKey);
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
      } else {
        agents = dbService.getAllAgents();
      }

      cache.set(cacheKey, agents, 3000); // Cache for 3 seconds

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

