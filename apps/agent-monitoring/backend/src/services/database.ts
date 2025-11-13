/**
 * Database service for SQLite operations
 */

import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';
import { Agent, Action, ToolUsage, SessionStats, QueryOptions } from '../types';

export class DatabaseService {
  private db: Database.Database;

  constructor(dbPath: string) {
    // Ensure directory exists
    const dbDir = path.dirname(dbPath);
    if (!fs.existsSync(dbDir)) {
      fs.mkdirSync(dbDir, { recursive: true });
    }

    this.db = new Database(dbPath);
    this.db.pragma('journal_mode = WAL'); // Enable WAL mode for better concurrency
  }

  // Agent Status Operations

  getAllAgents(): Agent[] {
    const stmt = this.db.prepare(`
      SELECT * FROM agent_status
      ORDER BY last_updated DESC
    `);
    return stmt.all() as Agent[];
  }

  getAgentById(agentId: string): Agent | null {
    const stmt = this.db.prepare(`
      SELECT * FROM agent_status
      WHERE agent_id = ?
    `);
    const result = stmt.get(agentId) as Agent | undefined;
    return result || null;
  }

  getAgentsByStatus(status: string): Agent[] {
    const stmt = this.db.prepare(`
      SELECT * FROM agent_status
      WHERE status = ?
      ORDER BY last_updated DESC
    `);
    return stmt.all(status) as Agent[];
  }

  updateAgentStatus(
    agentId: string,
    status: string,
    currentTaskId?: string,
    progress?: string,
    blockers?: string
  ): number {
    // Check if status exists
    const checkStmt = this.db.prepare('SELECT id FROM agent_status WHERE agent_id = ?');
    const existing = checkStmt.get(agentId) as { id: number } | undefined;

    if (existing) {
      // Update existing
      const updateStmt = this.db.prepare(`
        UPDATE agent_status
        SET status = ?, current_task_id = ?, progress = ?, blockers = ?,
            last_updated = CURRENT_TIMESTAMP
        WHERE agent_id = ?
      `);
      updateStmt.run(status, currentTaskId || null, progress || null, blockers || null, agentId);
      return existing.id;
    } else {
      // Insert new
      const insertStmt = this.db.prepare(`
        INSERT INTO agent_status (agent_id, status, current_task_id, progress, blockers)
        VALUES (?, ?, ?, ?, ?)
      `);
      const result = insertStmt.run(agentId, status, currentTaskId || null, progress || null, blockers || null);
      return result.lastInsertRowid as number;
    }
  }

  // Action Operations

  getActions(options: QueryOptions = {}): Action[] {
    const {
      limit = 100,
      offset = 0,
      agentId,
      actionType,
      toolName,
      startTime,
      endTime
    } = options;

    // Validate limit and offset
    const validLimit = Math.min(Math.max(1, limit), 1000); // Max 1000, min 1
    const validOffset = Math.max(0, offset);

    let query = 'SELECT * FROM agent_actions WHERE 1=1';
    const params: any[] = [];

    if (agentId) {
      query += ' AND agent_id = ?';
      params.push(agentId);
    }

    if (actionType) {
      query += ' AND action_type = ?';
      params.push(actionType);
    }

    if (toolName) {
      query += ' AND tool_name = ?';
      params.push(toolName);
    }

    if (startTime) {
      query += ' AND timestamp >= ?';
      params.push(startTime);
    }

    if (endTime) {
      query += ' AND timestamp <= ?';
      params.push(endTime);
    }

    query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?';
    params.push(validLimit, validOffset);

    const stmt = this.db.prepare(query);
    const results = stmt.all(...params) as Action[];

    // Parse JSON parameters safely
    return results.map(action => {
      try {
        return {
          ...action,
          parameters: action.parameters ? JSON.parse(action.parameters as any) : null
        };
      } catch (e) {
        // If JSON parsing fails, return null for parameters
        return {
          ...action,
          parameters: null
        };
      }
    });
  }

  getActionsLast24h(): Action[] {
    const stmt = this.db.prepare(`
      SELECT * FROM agent_actions
      WHERE timestamp >= datetime('now', '-24 hours')
      ORDER BY timestamp DESC
    `);
    const results = stmt.all() as Action[];

    return results.map(action => ({
      ...action,
      parameters: action.parameters ? JSON.parse(action.parameters as any) : null
    }));
  }

  getActionsByAgent(agentId: string, limit: number = 50): Action[] {
    const stmt = this.db.prepare(`
      SELECT * FROM agent_actions
      WHERE agent_id = ?
      ORDER BY timestamp DESC
      LIMIT ?
    `);
    const results = stmt.all(agentId, limit) as Action[];

    return results.map(action => ({
      ...action,
      parameters: action.parameters ? JSON.parse(action.parameters as any) : null
    }));
  }

  addAction(
    agentId: string,
    actionType: string,
    toolName?: string,
    parameters?: any,
    resultStatus: string = 'success',
    durationMs?: number,
    error?: string
  ): number {
    const stmt = this.db.prepare(`
      INSERT INTO agent_actions 
      (agent_id, action_type, tool_name, parameters, result_status, duration_ms, error)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    const paramsJson = parameters ? JSON.stringify(parameters) : null;
    const result = stmt.run(
      agentId,
      actionType,
      toolName || null,
      paramsJson,
      resultStatus,
      durationMs || null,
      error || null
    );
    return result.lastInsertRowid as number;
  }

  // Tool Usage Statistics

  getToolUsage(agentId?: string, limit: number = 20): ToolUsage[] {
    let query = `
      SELECT 
        tool_name,
        COUNT(*) as count,
        SUM(CASE WHEN result_status = 'success' THEN 1 ELSE 0 END) as success_count,
        SUM(CASE WHEN result_status = 'error' THEN 1 ELSE 0 END) as error_count,
        AVG(duration_ms) as avg_duration_ms
      FROM agent_actions
      WHERE tool_name IS NOT NULL
    `;

    const params: any[] = [];

    if (agentId) {
      query += ' AND agent_id = ?';
      params.push(agentId);
    }

    query += `
      GROUP BY tool_name
      ORDER BY count DESC
      LIMIT ?
    `;
    params.push(limit);

    const stmt = this.db.prepare(query);
    return stmt.all(...params) as ToolUsage[];
  }

  // Session Statistics

  getSessionStats(agentId: string): SessionStats {
    const stmt = this.db.prepare(`
      SELECT 
        COUNT(*) as total_sessions,
        SUM(tasks_completed) as total_tasks_completed,
        SUM(tools_called) as total_tools_called,
        AVG(
          CASE 
            WHEN session_end IS NOT NULL 
            THEN (julianday(session_end) - julianday(session_start)) * 24 * 60
            ELSE NULL
          END
        ) as avg_session_duration_minutes
      FROM agent_sessions
      WHERE agent_id = ?
    `);

    const result = stmt.get(agentId) as any;

    return {
      total_sessions: result?.total_sessions || 0,
      total_tasks_completed: result?.total_tasks_completed || 0,
      total_tools_called: result?.total_tools_called || 0,
      avg_session_duration_minutes: result?.avg_session_duration_minutes || 0
    };
  }

  startSession(agentId: string): number {
    const stmt = this.db.prepare(`
      INSERT INTO agent_sessions (agent_id, session_start)
      VALUES (?, CURRENT_TIMESTAMP)
    `);
    const result = stmt.run(agentId);
    return result.lastInsertRowid as number;
  }

  endSession(agentId: string, tasksCompleted: number = 0, toolsCalled: number = 0): void {
    // Find the most recent active session first
    const findStmt = this.db.prepare(`
      SELECT id FROM agent_sessions 
      WHERE agent_id = ? AND session_end IS NULL
      ORDER BY session_start DESC
      LIMIT 1
    `);
    const session = findStmt.get(agentId) as { id: number } | undefined;
    
    if (session) {
      // Update the found session
      const updateStmt = this.db.prepare(`
        UPDATE agent_sessions
        SET session_end = CURRENT_TIMESTAMP,
            tasks_completed = ?,
            tools_called = ?
        WHERE id = ?
      `);
      updateStmt.run(tasksCompleted, toolsCalled, session.id);
    }
  }

  // System Statistics

  getSystemStats(): any {
    // Total agents
    const totalAgentsStmt = this.db.prepare('SELECT COUNT(*) as count FROM agent_status');
    const totalAgents = (totalAgentsStmt.get() as any).count;

    // Agents by status
    const statusStmt = this.db.prepare(`
      SELECT status, COUNT(*) as count
      FROM agent_status
      GROUP BY status
    `);
    const statusCounts = statusStmt.all() as Array<{ status: string; count: number }>;

    const statusMap: Record<string, number> = {};
    statusCounts.forEach(item => {
      statusMap[item.status] = item.count;
    });

    // Total actions
    const totalActionsStmt = this.db.prepare('SELECT COUNT(*) as count FROM agent_actions');
    const totalActions = (totalActionsStmt.get() as any).count;

    // Actions last 24h
    const actions24hStmt = this.db.prepare(`
      SELECT COUNT(*) as count
      FROM agent_actions
      WHERE timestamp >= datetime('now', '-24 hours')
    `);
    const actionsLast24h = (actions24hStmt.get() as any).count;

    // Tool usage (top 10)
    const toolUsageStmt = this.db.prepare(`
      SELECT tool_name, COUNT(*) as count
      FROM agent_actions
      WHERE tool_name IS NOT NULL
      GROUP BY tool_name
      ORDER BY count DESC
      LIMIT 10
    `);
    const toolUsageResults = toolUsageStmt.all() as Array<{ tool_name: string; count: number }>;
    const toolUsage: Record<string, number> = {};
    toolUsageResults.forEach(item => {
      toolUsage[item.tool_name] = item.count;
    });

    // Task stats (would need to integrate with task coordination system)
    // For now, return placeholder
    const taskStats = {
      pending: 0,
      in_progress: 0,
      completed: 0
    };

    return {
      totalAgents,
      activeAgents: statusMap['active'] || 0,
      idleAgents: statusMap['idle'] || 0,
      blockedAgents: statusMap['blocked'] || 0,
      totalActions,
      actionsLast24h,
      toolUsage,
      taskStats
    };
  }

  close(): void {
    this.db.close();
  }
}

