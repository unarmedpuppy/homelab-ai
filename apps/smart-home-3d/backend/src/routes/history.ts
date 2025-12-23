import { Router, Request, Response } from 'express';
import type { HistoryService } from '../services/historyService.js';

export function createHistoryRoutes(historyService: HistoryService) {
  const router = Router();

  // Get device history
  router.get('/device/:deviceId', async (req: Request, res: Response) => {
    const { deviceId } = req.params;
    const { start, end, limit } = req.query;

    const startDate = start ? new Date(start as string) : undefined;
    const endDate = end ? new Date(end as string) : undefined;
    const limitNum = limit ? parseInt(limit as string, 10) : 1000;

    const history = await historyService.getDeviceHistory(
      deviceId,
      startDate,
      endDate,
      limitNum
    );

    res.json(history);
  });

  // Get aggregated history for charts
  router.get('/device/:deviceId/aggregate', async (req: Request, res: Response) => {
    const { deviceId } = req.params;
    const { property, interval, start, end } = req.query;

    if (!property || !interval || !start || !end) {
      return res.status(400).json({
        error: 'Missing required parameters: property, interval, start, end',
      });
    }

    const validIntervals = ['hour', 'day', 'week', 'month'];
    if (!validIntervals.includes(interval as string)) {
      return res.status(400).json({
        error: `Invalid interval. Must be one of: ${validIntervals.join(', ')}`,
      });
    }

    const data = await historyService.getAggregatedHistory(
      deviceId,
      property as string,
      interval as 'hour' | 'day' | 'week' | 'month',
      new Date(start as string),
      new Date(end as string)
    );

    res.json(data);
  });

  // Export history as CSV
  router.get('/device/:deviceId/export', async (req: Request, res: Response) => {
    const { deviceId } = req.params;
    const { start, end } = req.query;

    if (!start || !end) {
      return res.status(400).json({
        error: 'Missing required parameters: start, end',
      });
    }

    const csv = await historyService.exportHistory(
      deviceId,
      new Date(start as string),
      new Date(end as string)
    );

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename="${deviceId}_history.csv"`
    );
    res.send(csv);
  });

  // Trigger history cleanup
  router.post('/cleanup', async (req: Request, res: Response) => {
    const { retentionDays } = req.body;
    const deleted = await historyService.cleanupOldHistory(retentionDays || 90);
    res.json({ deleted });
  });

  return router;
}
