"use strict";
/**
 * Database service for SQLite operations
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.DatabaseService = void 0;
const better_sqlite3_1 = __importDefault(require("better-sqlite3"));
const path_1 = __importDefault(require("path"));
const fs_1 = __importDefault(require("fs"));
class DatabaseService {
    db;
    constructor(dbPath) {
        // Ensure directory exists
        const dbDir = path_1.default.dirname(dbPath);
        if (!fs_1.default.existsSync(dbDir)) {
            fs_1.default.mkdirSync(dbDir, { recursive: true });
        }
        this.db = new better_sqlite3_1.default(dbPath);
        this.db.pragma('journal_mode = WAL'); // Enable WAL mode for better concurrency
    }
    // Agent Status Operations
    getAllAgents() {
        const stmt = this.db.prepare(`
      SELECT * FROM agent_status
      ORDER BY last_updated DESC
    `);
        return stmt.all();
    }
    getAgentById(agentId) {
        const stmt = this.db.prepare(`
      SELECT * FROM agent_status
      WHERE agent_id = ?
    `);
        const result = stmt.get(agentId);
        return result || null;
    }
    getAgentsByStatus(status) {
        const stmt = this.db.prepare(`
      SELECT * FROM agent_status
      WHERE status = ?
      ORDER BY last_updated DESC
    `);
        return stmt.all(status);
    }
    // Action Operations
    getActions(options = {}) {
        const { limit = 100, offset = 0, agentId, actionType, toolName, startTime, endTime } = options;
        // Validate limit and offset
        const validLimit = Math.min(Math.max(1, limit), 1000); // Max 1000, min 1
        const validOffset = Math.max(0, offset);
        let query = 'SELECT * FROM agent_actions WHERE 1=1';
        const params = [];
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
        const results = stmt.all(...params);
        // Parse JSON parameters safely
        return results.map(action => {
            try {
                return {
                    ...action,
                    parameters: action.parameters ? JSON.parse(action.parameters) : null
                };
            }
            catch (e) {
                // If JSON parsing fails, return null for parameters
                return {
                    ...action,
                    parameters: null
                };
            }
        });
    }
    getActionsLast24h() {
        const stmt = this.db.prepare(`
      SELECT * FROM agent_actions
      WHERE timestamp >= datetime('now', '-24 hours')
      ORDER BY timestamp DESC
    `);
        const results = stmt.all();
        return results.map(action => ({
            ...action,
            parameters: action.parameters ? JSON.parse(action.parameters) : null
        }));
    }
    getActionsByAgent(agentId, limit = 50) {
        const stmt = this.db.prepare(`
      SELECT * FROM agent_actions
      WHERE agent_id = ?
      ORDER BY timestamp DESC
      LIMIT ?
    `);
        const results = stmt.all(agentId, limit);
        return results.map(action => ({
            ...action,
            parameters: action.parameters ? JSON.parse(action.parameters) : null
        }));
    }
    // Tool Usage Statistics
    getToolUsage(agentId, limit = 20) {
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
        const params = [];
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
        return stmt.all(...params);
    }
    // Session Statistics
    getSessionStats(agentId) {
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
        const result = stmt.get(agentId);
        return {
            total_sessions: result?.total_sessions || 0,
            total_tasks_completed: result?.total_tasks_completed || 0,
            total_tools_called: result?.total_tools_called || 0,
            avg_session_duration_minutes: result?.avg_session_duration_minutes || 0
        };
    }
    // System Statistics
    getSystemStats() {
        // Total agents
        const totalAgentsStmt = this.db.prepare('SELECT COUNT(*) as count FROM agent_status');
        const totalAgents = totalAgentsStmt.get().count;
        // Agents by status
        const statusStmt = this.db.prepare(`
      SELECT status, COUNT(*) as count
      FROM agent_status
      GROUP BY status
    `);
        const statusCounts = statusStmt.all();
        const statusMap = {};
        statusCounts.forEach(item => {
            statusMap[item.status] = item.count;
        });
        // Total actions
        const totalActionsStmt = this.db.prepare('SELECT COUNT(*) as count FROM agent_actions');
        const totalActions = totalActionsStmt.get().count;
        // Actions last 24h
        const actions24hStmt = this.db.prepare(`
      SELECT COUNT(*) as count
      FROM agent_actions
      WHERE timestamp >= datetime('now', '-24 hours')
    `);
        const actionsLast24h = actions24hStmt.get().count;
        // Tool usage (top 10)
        const toolUsageStmt = this.db.prepare(`
      SELECT tool_name, COUNT(*) as count
      FROM agent_actions
      WHERE tool_name IS NOT NULL
      GROUP BY tool_name
      ORDER BY count DESC
      LIMIT 10
    `);
        const toolUsageResults = toolUsageStmt.all();
        const toolUsage = {};
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
    close() {
        this.db.close();
    }
}
exports.DatabaseService = DatabaseService;
//# sourceMappingURL=database.js.map