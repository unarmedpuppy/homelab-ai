"use strict";
/**
 * Automatic metric exporter to InfluxDB
 * Runs on a schedule to export metrics
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.MetricExporter = void 0;
class MetricExporter {
    influxService;
    exportInterval = null;
    isRunning = false;
    constructor(influxService, _dbService // Kept for future use
    ) {
        this.influxService = influxService;
    }
    /**
     * Start automatic metric export
     * @param intervalMs - Export interval in milliseconds (default: 30 seconds)
     */
    start(intervalMs = 30000) {
        if (this.isRunning) {
            console.warn('Metric exporter is already running');
            return;
        }
        if (!this.influxService) {
            console.warn('InfluxDB service not configured, metric export disabled');
            return;
        }
        this.isRunning = true;
        console.log(`📊 Starting metric exporter (interval: ${intervalMs}ms)`);
        // Export immediately
        this.export().catch(err => {
            console.error('Initial metric export failed:', err);
        });
        // Then export on schedule
        this.exportInterval = setInterval(() => {
            this.export().catch(err => {
                console.error('Scheduled metric export failed:', err);
            });
        }, intervalMs);
    }
    /**
     * Stop automatic metric export
     */
    stop() {
        if (this.exportInterval) {
            clearInterval(this.exportInterval);
            this.exportInterval = null;
        }
        this.isRunning = false;
        console.log('📊 Metric exporter stopped');
    }
    /**
     * Export all metrics to InfluxDB
     */
    async export() {
        if (!this.influxService) {
            return;
        }
        try {
            const result = await this.influxService.exportAll();
            console.log(`📊 Metrics exported: ${JSON.stringify(result)}`);
        }
        catch (error) {
            console.error('Failed to export metrics:', error);
        }
    }
}
exports.MetricExporter = MetricExporter;
//# sourceMappingURL=metricExporter.js.map