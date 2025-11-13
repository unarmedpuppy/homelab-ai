/**
 * Automatic metric exporter to InfluxDB
 * Runs on a schedule to export metrics
 */
import { InfluxDBService } from './influxdb';
import { DatabaseService } from './database';
export declare class MetricExporter {
    private influxService;
    private exportInterval;
    private isRunning;
    constructor(influxService: InfluxDBService | null, _dbService: DatabaseService);
    /**
     * Start automatic metric export
     * @param intervalMs - Export interval in milliseconds (default: 30 seconds)
     */
    start(intervalMs?: number): void;
    /**
     * Stop automatic metric export
     */
    stop(): void;
    /**
     * Export all metrics to InfluxDB
     */
    private export;
}
//# sourceMappingURL=metricExporter.d.ts.map