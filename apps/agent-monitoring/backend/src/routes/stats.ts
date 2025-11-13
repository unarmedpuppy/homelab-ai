/**
 * Statistics routes
 */

import { Router, Request, Response } from 'express';
import { DatabaseService } from '../services/database';
import { cache } from '../utils/cache';

export function createStatsRouter(dbService: DatabaseService): Router {
  const router = Router();

  // GET /api/stats - Get system statistics (cached for 5 seconds)
  router.get('/', (_req: Request, res: Response) => {
    try {
      const cached = cache.get('system_stats');
      if (cached) {
        return res.json({
          status: 'success',
          stats: cached,
          cached: true
        });
      }

      const stats = dbService.getSystemStats();
      cache.set('system_stats', stats, 5000); // Cache for 5 seconds

      res.json({
        status: 'success',
        stats
      });
    } catch (error: any) {
      res.status(500).json({
        status: 'error',
        message: error.message
      });
    }
  });

  // GET /api/stats/tool-usage - Get tool usage statistics
  router.get('/tool-usage', (req: Request, res: Response) => {
    try {
      const agentId = req.query.agentId as string | undefined;
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 20;

      const toolUsage = dbService.getToolUsage(agentId, limit);

      res.json({
        status: 'success',
        count: toolUsage.length,
        toolUsage
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

