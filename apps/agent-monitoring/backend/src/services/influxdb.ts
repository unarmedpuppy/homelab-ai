/**
 * InfluxDB export service for Grafana integration
 */

import { InfluxDB, Point, WriteApi } from '@influxdata/influxdb-client';
import { DatabaseService } from './database';

export class InfluxDBService {
  private client: InfluxDB | null = null;
  private writeApi: WriteApi | null = null;
  private dbService: DatabaseService;

  constructor(
    url: string,
    token: string,
    org: string,
    bucket: string,
    dbService: DatabaseService
  ) {
    this.dbService = dbService;

    if (url && token) {
      this.client = new InfluxDB({ url, token });
      this.writeApi = this.client.getWriteApi(org, bucket, 'ms');
      console.log(`📊 InfluxDB WriteApi initialized: org=${org}, bucket=${bucket}`);
    }
  }

  /**
   * Export agent actions to InfluxDB
   */
  async exportAgentActions(hours: number = 1): Promise<number> {
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
      const point = new Point('agent_actions')
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
  async exportAgentStatus(): Promise<number> {
    if (!this.writeApi) {
      throw new Error('InfluxDB not configured');
    }

    const agents = this.dbService.getAllAgents();
    let exported = 0;

    for (const agent of agents) {
      const point = new Point('agent_status')
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
  async exportToolUsage(): Promise<number> {
    if (!this.writeApi) {
      throw new Error('InfluxDB not configured');
    }

    const toolUsage = this.dbService.getToolUsage();
    let exported = 0;

    for (const tool of toolUsage) {
      const point = new Point('tool_usage')
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
  async exportSystemStats(): Promise<number> {
    if (!this.writeApi) {
      throw new Error('InfluxDB not configured');
    }

    const stats = this.dbService.getSystemStats();

    const point = new Point('system_stats')
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
  async exportAll(): Promise<{ actions: number; status: number; tools: number; stats: number }> {
    const actions = await this.exportAgentActions(24);
    const status = await this.exportAgentStatus();
    const tools = await this.exportToolUsage();
    const stats = await this.exportSystemStats();

    return { actions, status, tools, stats };
  }

  /**
   * Close InfluxDB connection
   */
  close(): void {
    if (this.writeApi) {
      this.writeApi.close();
    }
  }
}

