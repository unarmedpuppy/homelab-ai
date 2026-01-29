const http = require('http');
const { URL, URLSearchParams } = require('url');

const PORT = 8080;
const BASE_URL = 'https://averys-mac-mini.tail86b033.ts.net';

// Escape XML special characters
function escapeXml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

// Parse POST body
function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        resolve(new URLSearchParams(body));
      } catch (e) {
        resolve(new URLSearchParams());
      }
    });
    req.on('error', reject);
  });
}

// Generate TwiML response
function twiml(content) {
  return `<?xml version="1.0" encoding="UTF-8"?><Response>${content}</Response>`;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const params = await parseBody(req);
  
  // Health check
  if (url.pathname === '/health') {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ status: 'ok', time: new Date().toISOString() }));
    return;
  }
  
  // Reject non-voice endpoints
  if (!url.pathname.startsWith('/voice')) {
    res.statusCode = 404;
    res.end('Not Found');
    return;
  }
  
  console.log(`[${new Date().toISOString()}] ${req.method} ${url.pathname}`);
  
  res.setHeader('Content-Type', 'text/xml');
  
  // Initial call handler
  if (url.pathname === '/voice' || url.pathname === '/voice/') {
    const xml = twiml(`<Say voice="Polly.Joanna">Hello, this is Avery. How can I help?</Say><Gather input="speech" action="${BASE_URL}/voice/respond" speechTimeout="auto" speechModel="phone_call"></Gather><Say voice="Polly.Joanna">Goodbye.</Say>`);
    console.log('Sent greeting');
    res.end(xml);
    return;
  }
  
  // Handle speech response
  if (url.pathname === '/voice/respond') {
    const speechResult = params.get('SpeechResult') || '';
    const safeSpeech = escapeXml(speechResult);
    console.log('Heard:', speechResult);
    
    const lowerSpeech = speechResult.toLowerCase();
    
    if (lowerSpeech.includes('goodbye') || lowerSpeech.includes('bye')) {
      res.end(twiml('<Say voice="Polly.Joanna">Goodbye!</Say><Hangup/>'));
      console.log('Sent goodbye');
      return;
    }
    
    const reply = `I heard: ${safeSpeech}. What else?`;
    res.end(twiml(`<Say voice="Polly.Joanna">${reply}</Say><Gather input="speech" action="${BASE_URL}/voice/respond" speechTimeout="auto" speechModel="phone_call"></Gather><Say voice="Polly.Joanna">Goodbye.</Say>`));
    console.log('Sent reply');
    return;
  }
  
  res.statusCode = 404;
  res.end('Not Found');
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`Twilio webhook on http://127.0.0.1:${PORT}`);
  console.log(`Using absolute URLs: ${BASE_URL}`);
});
