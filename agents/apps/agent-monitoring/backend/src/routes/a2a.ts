/**
 * A2A (Agent-to-Agent) Protocol Routes
 * 
 * Implements JSON-RPC 2.0 over HTTP for A2A protocol compliance.
 */

import { Router, Request, Response } from 'express';
import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync } from 'fs';
import { join } from 'path';
import { DatabaseService } from '../services/database';

// Paths for A2A communication
const COMMUNICATION_DIR = join(__dirname, '../../../../communication');
const MESSAGES_DIR = join(COMMUNICATION_DIR, 'messages');
const AGENTCARDS_DIR = join(COMMUNICATION_DIR, 'agentcards');

// Ensure directories exist
function ensureDirs() {
  [MESSAGES_DIR, AGENTCARDS_DIR].forEach(dir => {
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  });
}

// JSON-RPC 2.0 error codes
const JSON_RPC_ERRORS = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
};

// Helper to create JSON-RPC 2.0 response
function createResponse(id: string, result?: any, error?: any) {
  const response: any = {
    jsonrpc: '2.0',
    id,
  };
  if (error) {
    response.error = error;
  } else {
    response.result = result;
  }
  return response;
}

// Helper to create error response
function createErrorResponse(id: string, code: number, message: string, data?: any) {
  return createResponse(id, undefined, {
    code,
    message,
    data,
  });
}

// Load message index
function loadIndex(): any {
  const indexPath = join(MESSAGES_DIR, 'index.json');
  if (!existsSync(indexPath)) {
    return { messages: [] };
  }
  try {
    return JSON.parse(readFileSync(indexPath, 'utf-8'));
  } catch {
    return { messages: [] };
  }
}

// Save message index
function saveIndex(index: any) {
  const indexPath = join(MESSAGES_DIR, 'index.json');
  writeFileSync(indexPath, JSON.stringify(index, null, 2));
}

// Generate message ID
function generateMessageId(): string {
  const date = new Date().toISOString().split('T')[0];
  const index = loadIndex();
  const todayMessages = index.messages.filter((m: any) =>
    m.message_id?.startsWith(`MSG-${date}`)
  );
  const nextNum = todayMessages.length + 1;
  return `MSG-${date}-${nextNum.toString().padStart(3, '0')}`;
}

export function createA2ARouter(_dbService: DatabaseService): Router {
  const router = Router();
  ensureDirs();

  // POST /a2a - A2A JSON-RPC 2.0 endpoint
  router.post('/', (req: Request, res: Response) => {
    try {
      const body = req.body;

      // Validate JSON-RPC 2.0 structure
      if (body.jsonrpc !== '2.0') {
        return res.status(400).json(
          createErrorResponse(
            body.id || 'unknown',
            JSON_RPC_ERRORS.INVALID_REQUEST,
            "Invalid jsonrpc version (must be '2.0')"
          )
        );
      }

      if (!body.method) {
        return res.status(400).json(
          createErrorResponse(
            body.id || 'unknown',
            JSON_RPC_ERRORS.INVALID_REQUEST,
            "Missing 'method' field"
          )
        );
      }

      if (!body.id) {
        return res.status(400).json(
          createErrorResponse(
            'unknown',
            JSON_RPC_ERRORS.INVALID_REQUEST,
            "Missing 'id' field"
          )
        );
      }

      // Route to appropriate method handler
      const method = body.method;
      const params = body.params || {};
      const requestId = body.id;

      switch (method) {
        case 'a2a.sendMessage':
          return handleSendMessage(req, res, requestId, params);
        case 'a2a.getMessages':
          return handleGetMessages(req, res, requestId, params);
        case 'a2a.acknowledgeMessage':
          return handleAcknowledgeMessage(req, res, requestId, params);
        case 'a2a.resolveMessage':
          return handleResolveMessage(req, res, requestId, params);
        case 'a2a.getAgentCard':
          return handleGetAgentCard(req, res, requestId, params);
        case 'a2a.listAgentCards':
          return handleListAgentCards(req, res, requestId, params);
        default:
          return res.status(400).json(
            createErrorResponse(
              requestId,
              JSON_RPC_ERRORS.METHOD_NOT_FOUND,
              `Method not found: ${method}`
            )
          );
      }
      } catch (error: any) {
        return res.status(500).json(
          createErrorResponse(
            req.body?.id || 'unknown',
            JSON_RPC_ERRORS.INTERNAL_ERROR,
            'Internal server error',
            error.message
          )
        );
      }
  });

  // GET /a2a/agentcard/:agentId - Get AgentCard
  router.get('/agentcard/:agentId', (req: Request, res: Response) => {
    try {
      const agentId = req.params.agentId;
      const cardPath = join(AGENTCARDS_DIR, `${agentId}.json`);

      if (!existsSync(cardPath)) {
        return res.status(404).json({
          status: 'error',
          message: `AgentCard not found for agent: ${agentId}`,
        });
      }

      const card = JSON.parse(readFileSync(cardPath, 'utf-8'));
      return res.json({
        status: 'success',
        agentcard: card,
      });
    } catch (error: any) {
      return res.status(500).json({
        status: 'error',
        message: error.message,
      });
    }
  });

  // GET /a2a/agentcards - List all AgentCards
  router.get('/agentcards', (_req: Request, res: Response) => {
    try {
      if (!existsSync(AGENTCARDS_DIR)) {
        return res.json({
          status: 'success',
          count: 0,
          agentcards: [],
        });
      }

      const files = readdirSync(AGENTCARDS_DIR).filter(f => f.endsWith('.json'));
      const agentcards = files.map(file => {
        const cardPath = join(AGENTCARDS_DIR, file);
        return JSON.parse(readFileSync(cardPath, 'utf-8'));
      });

      return res.json({
        status: 'success',
        count: agentcards.length,
        agentcards,
      });
    } catch (error: any) {
      return res.status(500).json({
        status: 'error',
        message: error.message,
      });
    }
  });

  return router;
}

// Handler: a2a.sendMessage
function handleSendMessage(_req: Request, res: Response, requestId: string, params: any) {
  try {
    // Validate params
    const required = ['from', 'to', 'type', 'priority', 'subject', 'content'];
    for (const field of required) {
      if (!(field in params)) {
        return res.status(400).json(
          createErrorResponse(
            requestId,
            JSON_RPC_ERRORS.INVALID_PARAMS,
            `Missing required parameter: ${field}`
          )
        );
      }
    }

    // Generate message ID
    const messageId = generateMessageId();

    // Create message file
    const messageFile = join(MESSAGES_DIR, `${messageId}.md`);
    const frontmatter = {
      message_id: messageId,
      from_agent: params.from,
      to_agent: params.to,
      type: params.type,
      priority: params.priority,
      status: 'pending',
      subject: params.subject,
      created_at: new Date().toISOString(),
      acknowledged_at: null,
      resolved_at: null,
      ...(params.metadata?.related_task_id && { related_task_id: params.metadata.related_task_id }),
      ...(params.metadata?.related_message_id && { related_message_id: params.metadata.related_message_id }),
    };

    const messageContent = `---\n${JSON.stringify(frontmatter, null, 2)}\n---\n\n# ${params.subject}\n\n${params.content}\n`;
    writeFileSync(messageFile, messageContent);

    // Update index
    const index = loadIndex();
    index.messages.push({
      message_id: messageId,
      from_agent: params.from,
      to_agent: params.to,
      type: params.type,
      priority: params.priority,
      status: 'pending',
      created_at: frontmatter.created_at,
      file: `messages/${messageId}.md`,
    });
    saveIndex(index);

    return res.json(
      createResponse(requestId, {
        message_id: messageId,
        status: 'success',
        message: `Message sent successfully to ${params.to}`,
      })
    );
  } catch (error: any) {
    return res.status(500).json(
      createErrorResponse(
        requestId,
        JSON_RPC_ERRORS.INTERNAL_ERROR,
        'Failed to send message',
        error.message
      )
    );
  }
}

// Handler: a2a.getMessages
function handleGetMessages(_req: Request, res: Response, requestId: string, params: any) {
  try {
    const index = loadIndex();
    let messages = index.messages || [];

    // Filter by agent_id
    if (params.agent_id && params.agent_id !== 'all') {
      messages = messages.filter(
        (m: any) => m.to_agent === params.agent_id || m.from_agent === params.agent_id
      );
    }

    // Apply filters
    if (params.status) messages = messages.filter((m: any) => m.status === params.status);
    if (params.type) messages = messages.filter((m: any) => m.type === params.type);
    if (params.priority) messages = messages.filter((m: any) => m.priority === params.priority);

    // Load full messages
    const fullMessages = messages.slice(0, params.limit || 20).map((msg: any) => {
      const msgPath = join(COMMUNICATION_DIR, msg.file);
      if (existsSync(msgPath)) {
        try {
          const content = readFileSync(msgPath, 'utf-8');
          const parts = content.split('---');
          if (parts.length >= 3) {
            const metadata = JSON.parse(parts[1]);
            const body = parts[2].trim();
            return {
              ...metadata,
              content: body,
            };
          }
        } catch {
          // Skip invalid messages
        }
      }
      return msg;
    });

    return res.json(
      createResponse(requestId, {
        count: fullMessages.length,
        messages: fullMessages,
      })
    );
  } catch (error: any) {
    return res.status(500).json(
      createErrorResponse(
        requestId,
        JSON_RPC_ERRORS.INTERNAL_ERROR,
        'Failed to get messages',
        error.message
      )
    );
  }
}

// Handler: a2a.acknowledgeMessage
function handleAcknowledgeMessage(_req: Request, res: Response, requestId: string, params: any) {
  try {
    if (!params.message_id || !params.agent_id) {
      return res.status(400).json(
        createErrorResponse(
          requestId,
          JSON_RPC_ERRORS.INVALID_PARAMS,
          'Missing required parameters: message_id, agent_id'
        )
      );
    }

    const messageFile = join(MESSAGES_DIR, `${params.message_id}.md`);
    if (!existsSync(messageFile)) {
      return res.status(404).json(
        createErrorResponse(
          requestId,
          JSON_RPC_ERRORS.INVALID_PARAMS,
          `Message not found: ${params.message_id}`
        )
      );
    }

    // Update message status
    const content = readFileSync(messageFile, 'utf-8');
    const parts = content.split('---');
    if (parts.length >= 3) {
      const metadata = JSON.parse(parts[1]);
      metadata.status = 'acknowledged';
      metadata.acknowledged_at = new Date().toISOString();

      const newContent = `---\n${JSON.stringify(metadata, null, 2)}\n---\n${parts[2]}`;
      writeFileSync(messageFile, newContent);

      // Update index
      const index = loadIndex();
      const msgIndex = index.messages.findIndex((m: any) => m.message_id === params.message_id);
      if (msgIndex >= 0) {
        index.messages[msgIndex].status = 'acknowledged';
        index.messages[msgIndex].acknowledged_at = metadata.acknowledged_at;
        saveIndex(index);
      }
      
      return res.json(
        createResponse(requestId, {
          status: 'success',
          message: `Message ${params.message_id} acknowledged`,
        })
      );
    }
    
    return res.json(
      createResponse(requestId, {
        status: 'error',
        message: 'Invalid message format',
      })
    );
  } catch (error: any) {
    return res.status(500).json(
      createErrorResponse(
        requestId,
        JSON_RPC_ERRORS.INTERNAL_ERROR,
        'Failed to acknowledge message',
        error.message
      )
    );
  }
}

// Handler: a2a.resolveMessage
function handleResolveMessage(_req: Request, res: Response, requestId: string, params: any) {
  try {
    if (!params.message_id || !params.agent_id) {
      return res.status(400).json(
        createErrorResponse(
          requestId,
          JSON_RPC_ERRORS.INVALID_PARAMS,
          'Missing required parameters: message_id, agent_id'
        )
      );
    }

    const messageFile = join(MESSAGES_DIR, `${params.message_id}.md`);
    if (!existsSync(messageFile)) {
      return res.status(404).json(
        createErrorResponse(
          requestId,
          JSON_RPC_ERRORS.INVALID_PARAMS,
          `Message not found: ${params.message_id}`
        )
      );
    }

    // Update message status
    const content = readFileSync(messageFile, 'utf-8');
    const parts = content.split('---');
    if (parts.length >= 3) {
      const metadata = JSON.parse(parts[1]);
      metadata.status = 'resolved';
      metadata.resolved_at = new Date().toISOString();

      let body = parts[2];
      if (params.resolution_note) {
        body += `\n\n## Resolution\n\n${params.resolution_note}\n`;
      }

      const newContent = `---\n${JSON.stringify(metadata, null, 2)}\n---\n${body}`;
      writeFileSync(messageFile, newContent);

      // Update index
      const index = loadIndex();
      const msgIndex = index.messages.findIndex((m: any) => m.message_id === params.message_id);
      if (msgIndex >= 0) {
        index.messages[msgIndex].status = 'resolved';
        index.messages[msgIndex].resolved_at = metadata.resolved_at;
        saveIndex(index);
      }
      
      return res.json(
        createResponse(requestId, {
          status: 'success',
          message: `Message ${params.message_id} resolved`,
        })
      );
    }
    
    return res.json(
      createResponse(requestId, {
        status: 'error',
        message: 'Invalid message format',
      })
    );
  } catch (error: any) {
    return res.status(500).json(
      createErrorResponse(
        requestId,
        JSON_RPC_ERRORS.INTERNAL_ERROR,
        'Failed to resolve message',
        error.message
      )
    );
  }
}

// Handler: a2a.getAgentCard
function handleGetAgentCard(_req: Request, res: Response, requestId: string, params: any) {
  try {
    if (!params.agent_id) {
      return res.status(400).json(
        createErrorResponse(
          requestId,
          JSON_RPC_ERRORS.INVALID_PARAMS,
          'Missing required parameter: agent_id'
        )
      );
    }

    const cardPath = join(AGENTCARDS_DIR, `${params.agent_id}.json`);
    if (!existsSync(cardPath)) {
      return res.status(404).json(
        createErrorResponse(
          requestId,
          JSON_RPC_ERRORS.INVALID_PARAMS,
          `AgentCard not found for agent: ${params.agent_id}`
        )
      );
    }

    const card = JSON.parse(readFileSync(cardPath, 'utf-8'));
    return res.json(createResponse(requestId, { agentcard: card }));
  } catch (error: any) {
    return res.status(500).json(
      createErrorResponse(
        requestId,
        JSON_RPC_ERRORS.INTERNAL_ERROR,
        'Failed to get AgentCard',
        error.message
      )
    );
  }
}

// Handler: a2a.listAgentCards
function handleListAgentCards(_req: Request, res: Response, requestId: string, _params: any) {
  try {
    if (!existsSync(AGENTCARDS_DIR)) {
      return res.json(
        createResponse(requestId, {
          count: 0,
          agentcards: [],
        })
      );
    }

    const files = readdirSync(AGENTCARDS_DIR).filter(f => f.endsWith('.json'));
    const agentcards = files.map(file => {
      const cardPath = join(AGENTCARDS_DIR, file);
      return JSON.parse(readFileSync(cardPath, 'utf-8'));
    });

    return res.json(
      createResponse(requestId, {
        count: agentcards.length,
        agentcards,
      })
    );
  } catch (error: any) {
    return res.status(500).json(
      createErrorResponse(
        requestId,
        JSON_RPC_ERRORS.INTERNAL_ERROR,
        'Failed to list AgentCards',
        error.message
      )
    );
  }
}

