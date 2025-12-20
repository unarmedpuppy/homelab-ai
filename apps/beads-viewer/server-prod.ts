import express from 'express';
import { createServer } from 'http';
import { WebSocketServer } from 'ws';
import { spawn } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync, readFileSync, watch } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 3001;

const app = express();
app.use(express.json());

// Serve static files from dist
app.use(express.static(join(__dirname, 'dist')));

// Beads data path - looks for .beads in current working directory
const beadsPath = join(process.cwd(), '.beads', 'issues.jsonl');

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', beadsPath, exists: existsSync(beadsPath) });
});

// Execute bd commands
app.post('/api/bd', async (req, res) => {
  const { args } = req.body;
  try {
    const bd = spawn('bd', args, {
      cwd: process.cwd(),
      env: { ...process.env, BEADS_JSON: '1' }
    });

    let stdout = '';
    let stderr = '';

    bd.stdout.on('data', (data) => { stdout += data; });
    bd.stderr.on('data', (data) => { stderr += data; });

    bd.on('close', (code) => {
      if (code === 0) {
        try {
          res.json(JSON.parse(stdout));
        } catch {
          res.json({ output: stdout });
        }
      } else {
        res.status(500).json({ error: stderr || stdout });
      }
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get issues
app.get('/api/issues', (req, res) => {
  if (!existsSync(beadsPath)) {
    return res.json({ issues: [], error: 'No .beads/issues.jsonl found' });
  }
  try {
    const content = readFileSync(beadsPath, 'utf-8');
    const issues = content.trim().split('\n').filter(Boolean).map(line => JSON.parse(line));
    res.json({ issues });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// SPA fallback - Express 5 requires named parameter for catch-all
app.get('/{*splat}', (req, res) => {
  res.sendFile(join(__dirname, 'dist', 'index.html'));
});

const server = createServer(app);

// WebSocket for live updates
const wss = new WebSocketServer({ server, path: '/ws' });

wss.on('connection', (ws) => {
  console.log('WebSocket client connected');
  ws.on('close', () => console.log('WebSocket client disconnected'));
});

// Watch for file changes
if (existsSync(beadsPath)) {
  watch(beadsPath, () => {
    console.log('Issues file changed, notifying clients');
    wss.clients.forEach(client => {
      if (client.readyState === 1) {
        client.send(JSON.stringify({ type: 'refresh' }));
      }
    });
  });
}

server.listen(PORT, () => {
  console.log(`Beads Viewer running at http://localhost:${PORT}`);
  console.log(`Looking for beads at: ${beadsPath}`);
});
