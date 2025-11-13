/**
 * Action routes
 */

import { Router, Request, Response } from 'express';
import { DatabaseService } from '../services/database';
import { QueryOptions } from '../types';

export function createActionsRouter(dbService: DatabaseService): Router {
  const router = Router();

  // GET /api/actions - Get actions with filters
  router.get('/', (req: Request, res: Response) => {
    try {
      const options: QueryOptions = {
        limit: req.query.limit ? parseInt(req.query.limit as string) : 100,
        offset: req.query.offset ? parseInt(req.query.offset as string) : 0,
        agentId: req.query.agentId as string | undefined,
        actionType: req.query.actionType as string | undefined,
        toolName: req.query.toolName as string | undefined,
        startTime: req.query.startTime as string | undefined,
        endTime: req.query.endTime as string | undefined
      };

      const actions = dbService.getActions(options);

      res.json({
        status: 'success',
        count: actions.length,
        actions
      });
    } catch (error: any) {
      res.status(500).json({
        status: 'error',
        message: error.message
      });
    }
  });

  // GET /api/actions/recent - Get recent actions (last 24h)
  router.get('/recent', (_req: Request, res: Response) => {
    try {
      const actions = dbService.getActionsLast24h();

      res.json({
        status: 'success',
        count: actions.length,
        actions
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

