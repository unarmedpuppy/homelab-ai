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
    getActions(options?: QueryOptions): Action[];
    getActionsLast24h(): Action[];
    getActionsByAgent(agentId: string, limit?: number): Action[];
    getToolUsage(agentId?: string, limit?: number): ToolUsage[];
    getSessionStats(agentId: string): SessionStats;
    getSystemStats(): any;
    close(): void;
}
//# sourceMappingURL=database.d.ts.map