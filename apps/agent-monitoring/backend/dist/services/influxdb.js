"use strict";
/**
 * InfluxDB export service for Grafana integration
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.InfluxDBService = void 0;
const influxdb_client_1 = require("@influxdata/influxdb-client");
class InfluxDBService {
    client = null;
    writeApi = null;
    dbService;
    constructor(url, token, org, bucket, dbService) {
        this.dbService = dbService;
        if (url && token) {
            this.client = new influxdb_client_1.InfluxDB({ url, token });
            this.writeApi = this.client.getWriteApi(org, bucket, 'ms');
        }
    }
    /**
     * Export agent actions to InfluxDB
     */
    async exportAgentActions(hours = 1) {
        if (!this.writeApi) {
            throw new Error('InfluxDB not configured');
        }
        const startTime = new Date();
        startTime.setHours(startTime.getHours() - hours);
        const actions = this.dbService.getActions({
            startTime: startTime.toISOString()
        });
        let exported = 0;
        for (const action of actions) {
            const point = new influxdb_client_1.Point('agent_actions')
                .tag('agent_id', action.agent_id)
                .tag('action_type', action.action_type)
                .tag('result_status', action.result_status)
                .intField('count', 1);
            if (action.tool_name) {
                point.tag('tool_name', action.tool_name);
            }
            if (action.duration_ms !== null && action.duration_ms !== undefined) {
                point.intField('duration_ms', action.duration_ms);
            }
            point.timestamp(new Date(action.timestamp));
            this.writeApi.writePoint(point);
            exported++;
        }
        await this.writeApi.flush();
        return exported;
    }
    /**
     * Export agent status to InfluxDB
     */
    async exportAgentStatus() {
        if (!this.writeApi) {
            throw new Error('InfluxDB not configured');
        }
        const agents = this.dbService.getAllAgents();
        let exported = 0;
        for (const agent of agents) {
            const point = new influxdb_client_1.Point('agent_status')
                .tag('agent_id', agent.agent_id)
                .tag('status', agent.status)
                .intField('status_count', 1);
            if (agent.current_task_id) {
                point.tag('task_id', agent.current_task_id);
            }
            point.timestamp(new Date(agent.last_updated));
            this.writeApi.writePoint(point);
            exported++;
        }
        await this.writeApi.flush();
        return exported;
    }
    /**
     * Export tool usage statistics to InfluxDB
     */
    async exportToolUsage() {
        if (!this.writeApi) {
            throw new Error('InfluxDB not configured');
        }
        const toolUsage = this.dbService.getToolUsage();
        let exported = 0;
        for (const tool of toolUsage) {
            const point = new influxdb_client_1.Point('tool_usage')
                .tag('tool_name', tool.tool_name)
                .intField('count', tool.count)
                .intField('success_count', tool.success_count)
                .intField('error_count', tool.error_count)
                .floatField('avg_duration_ms', tool.avg_duration_ms || 0)
                .timestamp(new Date());
            this.writeApi.writePoint(point);
            exported++;
        }
        await this.writeApi.flush();
        return exported;
    }
    /**
     * Export system statistics to InfluxDB
     */
    async exportSystemStats() {
        if (!this.writeApi) {
            throw new Error('InfluxDB not configured');
        }
        const stats = this.dbService.getSystemStats();
        const point = new influxdb_client_1.Point('system_stats')
            .intField('total_agents', stats.totalAgents)
            .intField('active_agents', stats.activeAgents)
            .intField('idle_agents', stats.idleAgents)
            .intField('blocked_agents', stats.blockedAgents)
            .intField('total_actions', stats.totalActions)
            .intField('actions_last_24h', stats.actionsLast24h)
            .timestamp(new Date());
        this.writeApi.writePoint(point);
        await this.writeApi.flush();
        return 1;
    }
    /**
     * Export all metrics to InfluxDB
     */
    async exportAll() {
        const actions = await this.exportAgentActions(24);
        const status = await this.exportAgentStatus();
        const tools = await this.exportToolUsage();
        const stats = await this.exportSystemStats();
        return { actions, status, tools, stats };
    }
    /**
     * Close InfluxDB connection
     */
    close() {
        if (this.writeApi) {
            this.writeApi.close();
        }
    }
}
exports.InfluxDBService = InfluxDBService;
//# sourceMappingURL=influxdb.js.map