/**
 * InfluxDB export service for Grafana integration
 */
import { DatabaseService } from './database';
export declare class InfluxDBService {
    private client;
    private writeApi;
    private dbService;
    constructor(url: string, token: string, org: string, bucket: string, dbService: DatabaseService);
    /**
     * Export agent actions to InfluxDB
     */
    exportAgentActions(hours?: number): Promise<number>;
    /**
     * Export agent status to InfluxDB
     */
    exportAgentStatus(): Promise<number>;
    /**
     * Export tool usage statistics to InfluxDB
     */
    exportToolUsage(): Promise<number>;
    /**
     * Export system statistics to InfluxDB
     */
    exportSystemStats(): Promise<number>;
    /**
     * Export all metrics to InfluxDB
     */
    exportAll(): Promise<{
        actions: number;
        status: number;
        tools: number;
        stats: number;
    }>;
    /**
     * Close InfluxDB connection
     */
    close(): void;
}
//# sourceMappingURL=influxdb.d.ts.map