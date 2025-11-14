/**
 * Database service for SQLite operations
 */
import { Agent, Action, ToolUsage, SessionStats, QueryOptions } from '../types';
export declare class DatabaseService {
    private db;
    constructor(dbPath: string);
    getAllAgents(): Agent[];
    getAgentById(agentId: string): Agent | null;
    getAgentsByStatus(status: string): Agent[];
    updateAgentStatus(agentId: string, status: string, currentTaskId?: string, progress?: string, blockers?: string): number;
    getActions(options?: QueryOptions): Action[];
    getActionsLast24h(): Action[];
    getActionsByAgent(agentId: string, limit?: number): Action[];
    addAction(agentId: string, actionType: string, toolName?: string, parameters?: any, resultStatus?: string, durationMs?: number, error?: string): number;
    getToolUsage(agentId?: string, limit?: number): ToolUsage[];
    getSessionStats(agentId: string): SessionStats;
    startSession(agentId: string): number;
    endSession(agentId: string, tasksCompleted?: number, toolsCalled?: number): void;
    getSystemStats(): any;
    close(): void;
}
//# sourceMappingURL=database.d.ts.map