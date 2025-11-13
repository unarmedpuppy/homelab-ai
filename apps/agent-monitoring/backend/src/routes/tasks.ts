/**
 * Task routes (integration with task coordination system)
 */

import { Router, Request, Response } from 'express';
import { readFileSync } from 'fs';
import { join } from 'path';

export function createTasksRouter(): Router {
  const router = Router();

  // GET /api/tasks - Get task overview from task coordination system
  router.get('/', (_req: Request, res: Response) => {
    try {
      // Read from task coordination registry
      const projectRoot = join(__dirname, '../../../../..');
      const registryPath = join(projectRoot, 'agents', 'tasks', 'registry.md');

      let tasks: any[] = [];
      let taskStats = {
        pending: 0,
        in_progress: 0,
        completed: 0,
        blocked: 0,
        claimed: 0
      };

      try {
        const registryContent = readFileSync(registryPath, 'utf-8');
        const lines = registryContent.split('\n');

        // Parse markdown table
        let inTable = false;
        for (const line of lines) {
          if (line.includes('| Task ID')) {
            inTable = true;
            continue;
          }
          if (inTable && line.startsWith('|') && !line.includes('---')) {
            const parts = line.split('|').map(p => p.trim()).filter(p => p);
            if (parts.length >= 4) {
              const task = {
                task_id: parts[0],
                title: parts[1],
                description: parts[2] || '',
                status: parts[3],
                assignee: parts[4] || '-',
                priority: parts[5] || 'medium',
                dependencies: parts[6] || '-',
                project: parts[7] || '',
                created: parts[8] || '',
                updated: parts[9] || ''
              };
              tasks.push(task);

              // Count by status
              const status = task.status.toLowerCase();
              if (status === 'pending') taskStats.pending++;
              else if (status === 'in_progress') taskStats.in_progress++;
              else if (status === 'completed') taskStats.completed++;
              else if (status === 'blocked') taskStats.blocked++;
              else if (status === 'claimed') taskStats.claimed++;
            }
          }
        }
      } catch (error) {
        // Registry file might not exist yet
        console.warn('Could not read task registry:', error);
      }

      res.json({
        status: 'success',
        count: tasks.length,
        tasks,
        stats: taskStats
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

