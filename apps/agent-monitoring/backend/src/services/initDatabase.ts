/**
 * Database initialization script
 * Creates the required tables if they don't exist
 */

import Database from 'better-sqlite3';
import path from 'path';

export function initializeDatabase(dbPath: string): void {
  const db = new Database(dbPath);
  
  // Enable WAL mode for better concurrency
  db.pragma('journal_mode = WAL');
  
  // Agent Status table
  db.exec(`
    CREATE TABLE IF NOT EXISTS agent_status (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      agent_id TEXT NOT NULL UNIQUE,
      status TEXT NOT NULL,
      current_task_id TEXT,
      progress TEXT,
      blockers TEXT,
      last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);
  
  // Create indexes for agent_status
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_agent_status_agent_id 
    ON agent_status(agent_id)
  `);
  
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_agent_status_status 
    ON agent_status(status)
  `);
  
  // Agent Actions table
  db.exec(`
    CREATE TABLE IF NOT EXISTS agent_actions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      agent_id TEXT NOT NULL,
      action_type TEXT NOT NULL,
      tool_name TEXT,
      parameters TEXT,
      result_status TEXT NOT NULL,
      duration_ms INTEGER,
      error TEXT,
      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);
  
  // Create indexes for agent_actions
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_agent_actions_agent_id 
    ON agent_actions(agent_id)
  `);
  
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_agent_actions_timestamp 
    ON agent_actions(timestamp)
  `);
  
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_agent_actions_action_type 
    ON agent_actions(action_type)
  `);
  
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_agent_actions_tool_name 
    ON agent_actions(tool_name)
  `);
  
  // Agent Sessions table
  db.exec(`
    CREATE TABLE IF NOT EXISTS agent_sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      agent_id TEXT NOT NULL,
      session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      session_end TIMESTAMP,
      tasks_completed INTEGER DEFAULT 0,
      tools_called INTEGER DEFAULT 0
    )
  `);
  
  // Create index for agent_sessions
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_id 
    ON agent_sessions(agent_id)
  `);
  
  db.close();
  console.log('✅ Database schema initialized');
}

