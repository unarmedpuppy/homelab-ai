# Local AI Dashboard - Model Warmup Status Indication

## Overview

Add real-time status indication when models are loading/warming up, especially when switching models or after inactivity. This provides better UX during the wait time for cold model starts.

## Problem Statement

**Current Behavior:**
- User sends message → UI shows "typing..." → eventual response
- No indication during model warmup (can be 10-30 seconds on cold start)
- User doesn't know if request is stuck or model is loading
- Especially problematic when switching models or first interaction after idle time

**Desired Behavior:**
- User sends message → immediate feedback with specific status
- Show "Warming up model..." when model is loading
- Show "Generating response..." when inference starts
- Clear progress indication throughout the entire flow

## Technical Approach

We'll use **Server-Sent Events (SSE) streaming** for real-time status updates. This aligns with OpenAI's streaming API pattern and provides accurate, real-time feedback.

### Why SSE Streaming?

1. **Real-time updates** - No polling delay, instant status changes
2. **OpenAI compatible** - Standard streaming pattern for chat completions
3. **Detailed progress** - Can emit multiple status updates during processing
4. **Efficient** - Single connection, no repeated HTTP requests
5. **Browser native** - Built-in EventSource API support

### Architecture

```
Frontend (React)
    ↓ POST with stream=true
Backend Router (Local AI Router)
    ↓ SSE stream
Frontend receives events:
    - {"status": "routing", "message": "Selecting backend..."}
    - {"status": "loading", "message": "Warming up model on 3090..."}
    - {"status": "generating", "message": "Generating response..."}
    - {"status": "done", "content": "...", "model": "..."}
```

## Implementation Plan

### Backend (Local AI Router)

#### 1. Add Streaming Support to Chat Completions Endpoint

**File:** `apps/local-ai-router/router.py` (or main router file)

**Add streaming parameter:**
```python
@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    stream: bool = False,  # NEW PARAMETER
    ...
):
    if stream:
        return StreamingResponse(
            stream_chat_completion(request, ...),
            media_type="text/event-stream"
        )
    else:
        # Existing non-streaming implementation
        ...
```

#### 2. Implement Stream Generator Function

**New function:**
```python
async def stream_chat_completion(
    request: ChatCompletionRequest,
    backend: str,
    ...
) -> AsyncGenerator[str, None]:
    """
    Generator that yields SSE-formatted status updates and response.

    Yields events:
    - data: {"status": "routing", "message": "..."}
    - data: {"status": "loading", "message": "..."}
    - data: {"status": "generating", "message": "..."}
    - data: {"status": "done", "content": "...", ...}
    - data: [DONE]
    """

    # Emit routing status
    yield format_sse_event({
        "status": "routing",
        "message": f"Routing to {backend}...",
        "timestamp": time.time()
    })

    # Select backend
    backend_url = get_backend_url(backend)

    # Emit loading status (model warmup)
    yield format_sse_event({
        "status": "loading",
        "message": f"Warming up model on {backend}...",
        "backend": backend,
        "timestamp": time.time()
    })

    # Make request to backend (with streaming if supported)
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{backend_url}/v1/chat/completions",
            json=request.dict(),
            timeout=300.0
        ) as response:
            # Emit generating status
            yield format_sse_event({
                "status": "generating",
                "message": "Generating response...",
                "timestamp": time.time()
            })

            # Stream response chunks
            content = ""
            async for chunk in response.aiter_text():
                content += chunk

            # Emit completion
            yield format_sse_event({
                "status": "done",
                "content": content,
                "model": response.headers.get("X-Model-Used"),
                "backend": backend,
                "timestamp": time.time()
            })

    # Emit termination signal
    yield "data: [DONE]\n\n"

def format_sse_event(data: dict) -> str:
    """Format data as SSE event."""
    return f"data: {json.dumps(data)}\n\n"
```

#### 3. Add Status Tracking in Backend Wrappers

**Files:** Backend integration code (3070, 3090, etc.)

**Track model loading state:**
```python
class BackendManager:
    def __init__(self):
        self.model_states = {}  # Track which models are loaded

    async def is_model_loaded(self, backend: str, model: str) -> bool:
        """Check if model is already loaded (warm)."""
        return self.model_states.get(f"{backend}:{model}") == "loaded"

    async def estimate_warmup_time(self, backend: str, model: str) -> int:
        """Estimate warmup time in seconds."""
        if await self.is_model_loaded(backend, model):
            return 0

        # Estimate based on model size (can refine with metrics)
        model_sizes = {
            "small": 5,   # 5 seconds
            "medium": 15, # 15 seconds
            "big": 30,    # 30 seconds
        }
        return model_sizes.get(model, 10)
```

#### 4. Update Response Schema

**Pydantic models:**
```python
class StreamEvent(BaseModel):
    status: Literal["routing", "loading", "generating", "done"]
    message: Optional[str] = None
    content: Optional[str] = None
    model: Optional[str] = None
    backend: Optional[str] = None
    timestamp: float
    estimated_time: Optional[int] = None  # seconds
```

### Frontend (Dashboard)

#### 1. Update API Client to Support Streaming

**File:** `apps/local-ai-dashboard/src/api/client.ts`

**Add streaming method:**
```typescript
export const chatAPI = {
  // ... existing sendMessage method ...

  /**
   * Send message with streaming for real-time status updates
   */
  sendMessageStream: async function* (params: {
    model: string;
    messages: ChatMessage[];
    conversationId?: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  }): AsyncGenerator<StreamEvent, void, unknown> {
    const { conversationId, messages, model, ...options } = params;

    const headers: Record<string, string> = {
      'X-Enable-Memory': 'true',
      'X-Project': 'dashboard',
      'X-User-ID': 'dashboard-user',
    };

    if (conversationId) {
      headers['X-Conversation-ID'] = conversationId;
    }

    const requestBody = {
      model,
      messages,
      stream: true, // Enable streaming
      ...options,
    };

    const response = await fetch(`${API_BASE_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;

          try {
            const event = JSON.parse(data) as StreamEvent;
            yield event;
          } catch (e) {
            console.error('Failed to parse SSE event:', data);
          }
        }
      }
    }
  },
};

interface StreamEvent {
  status: 'routing' | 'loading' | 'generating' | 'done';
  message?: string;
  content?: string;
  model?: string;
  backend?: string;
  timestamp: number;
  estimated_time?: number;
}
```

#### 2. Update ChatInterface Component

**File:** `apps/local-ai-dashboard/src/components/ChatInterface.tsx`

**Add streaming state and handling:**
```typescript
export default function ChatInterface({ conversationId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<MessageWithMetadata[]>([]);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState('auto');

  // NEW: Streaming status state
  const [streamStatus, setStreamStatus] = useState<{
    active: boolean;
    status: string;
    message: string;
    estimatedTime?: number;
  } | null>(null);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();

    // Add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');

    try {
      // Use streaming API
      const stream = chatAPI.sendMessageStream({
        model: selectedModel,
        messages: [
          ...messages.map(m => ({ role: m.role, content: m.content })),
          { role: 'user', content: userMessage },
        ],
        conversationId: conversationId || undefined,
        temperature,
        max_tokens: maxTokens,
        top_p: topP,
        frequency_penalty: frequencyPenalty,
        presence_penalty: presencePenalty,
      });

      // Process stream events
      for await (const event of stream) {
        if (event.status === 'done') {
          // Add assistant response
          setMessages(prev => [
            ...prev,
            {
              role: 'assistant',
              content: event.content!,
              model: event.model,
              backend: event.backend,
            },
          ]);
          setStreamStatus(null);
        } else {
          // Update status
          setStreamStatus({
            active: true,
            status: event.status,
            message: event.message || '',
            estimatedTime: event.estimated_time,
          });
        }
      }
    } catch (error) {
      console.error('Chat stream error:', error);
      // Remove failed message
      setMessages(prev => prev.slice(0, -1));
      setStreamStatus(null);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-black">
      {/* ... existing header ... */}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message, idx) => (
          // ... existing message rendering ...
        ))}

        {/* NEW: Streaming status indicator */}
        {streamStatus && (
          <div className="flex items-start gap-3">
            <div className="text-xs font-mono uppercase text-green-400">
              ◂ ASSISTANT
            </div>
            <div className="flex-1">
              <div className="bg-gray-900 border border-green-900/30 rounded p-4">
                {/* Status message */}
                <div className="flex items-center gap-3 text-sm text-gray-300">
                  {/* Animated spinner */}
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-600 border-t-green-400" />

                  <div>
                    {/* Status text */}
                    <div className="font-medium">
                      {streamStatus.status === 'routing' && 'Selecting backend...'}
                      {streamStatus.status === 'loading' && 'Warming up model...'}
                      {streamStatus.status === 'generating' && 'Generating response...'}
                    </div>

                    {/* Additional details */}
                    {streamStatus.message && (
                      <div className="text-xs text-gray-500 mt-1">
                        {streamStatus.message}
                      </div>
                    )}

                    {/* Estimated time */}
                    {streamStatus.estimatedTime && streamStatus.estimatedTime > 0 && (
                      <div className="text-xs text-gray-600 mt-1">
                        Estimated wait: ~{streamStatus.estimatedTime}s
                      </div>
                    )}
                  </div>
                </div>

                {/* Progress bar (optional) */}
                {streamStatus.estimatedTime && (
                  <div className="mt-3 w-full bg-gray-800 rounded-full h-1">
                    <div
                      className="bg-green-500 h-1 rounded-full transition-all duration-1000 ease-linear"
                      style={{ width: '100%' }}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ... existing input area ... */}
    </div>
  );
}
```

#### 3. Add Status Message Component (Optional)

**New file:** `apps/local-ai-dashboard/src/components/StreamStatus.tsx`

**Reusable status indicator:**
```typescript
interface StreamStatusProps {
  status: 'routing' | 'loading' | 'generating';
  message?: string;
  estimatedTime?: number;
}

export function StreamStatus({ status, message, estimatedTime }: StreamStatusProps) {
  const statusConfig = {
    routing: {
      label: 'Selecting backend...',
      icon: '🔄',
      color: 'blue',
    },
    loading: {
      label: 'Warming up model...',
      icon: '🔥',
      color: 'orange',
    },
    generating: {
      label: 'Generating response...',
      icon: '✨',
      color: 'green',
    },
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-3 text-sm text-gray-300">
      {/* Animated spinner */}
      <div className={`animate-spin rounded-full h-4 w-4 border-2 border-gray-600 border-t-${config.color}-400`} />

      <div>
        <div className="font-medium">
          {config.icon} {config.label}
        </div>

        {message && (
          <div className="text-xs text-gray-500 mt-1">
            {message}
          </div>
        )}

        {estimatedTime && estimatedTime > 0 && (
          <div className="text-xs text-gray-600 mt-1">
            Estimated wait: ~{estimatedTime}s
          </div>
        )}
      </div>
    </div>
  );
}
```

## Testing Plan

### Backend Testing

1. **SSE Stream Format**
   ```bash
   # Test streaming endpoint
   curl -X POST http://localhost:8012/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "auto",
       "messages": [{"role": "user", "content": "Hello"}],
       "stream": true
     }' \
     --no-buffer

   # Should see:
   # data: {"status": "routing", "message": "..."}
   # data: {"status": "loading", "message": "..."}
   # data: {"status": "generating", "message": "..."}
   # data: {"status": "done", "content": "..."}
   # data: [DONE]
   ```

2. **Model State Tracking**
   - Send request to cold model → should show "loading" status
   - Send another request to same model immediately → should skip "loading" or show shorter time
   - Switch models → should show "loading" for new model

3. **Error Handling**
   - Backend down → should emit error status event
   - Timeout → should emit timeout status event
   - Invalid request → should return error immediately

### Frontend Testing

1. **UI Status Display**
   - Send message → see "Selecting backend..." status
   - Wait → see "Warming up model..." status
   - Wait → see "Generating response..." status
   - Complete → status disappears, response appears

2. **Model Switching**
   - Send message with model A → see fast response (warm)
   - Switch to model B → send message → see "Warming up..." (cold)
   - Switch back to model A → see fast response (warm)

3. **Edge Cases**
   - Cancel request mid-stream → status should clear
   - Network error → should show error and remove user message
   - Multiple rapid messages → should queue properly

## Design Decisions

### Streaming vs Polling

**Chose Streaming (SSE):**
- ✅ Real-time updates with no delay
- ✅ Single connection, efficient
- ✅ Standard OpenAI pattern
- ✅ Browser native support
- ❌ Slightly more complex implementation

**Rejected Polling:**
- ❌ Delay between status updates
- ❌ Multiple HTTP requests
- ❌ More server load
- ✅ Simpler implementation

### Status Granularity

**Chose 4 states:**
1. `routing` - Selecting backend (quick, <1s)
2. `loading` - Loading model into memory (10-30s on cold start)
3. `generating` - Running inference (varies by response length)
4. `done` - Complete

**Why not more states?**
- Too many states clutters UI
- These 4 cover the key phases users care about
- Can add more detail in `message` field

### Estimated Time Display

**Show estimated time for `loading` status only:**
- Warmup time is predictable based on model size
- Generation time varies too much to estimate accurately
- Show "~30s" range rather than countdown timer (less pressure)

### Backwards Compatibility

**Support both streaming and non-streaming:**
- `stream=false` (default) → existing behavior
- `stream=true` → new SSE behavior
- Frontend can use streaming for dashboard, clients can use non-streaming

## File Checklist

### Backend
- [ ] `apps/local-ai-router/router.py` - Add streaming parameter and StreamingResponse
- [ ] `apps/local-ai-router/stream.py` - New file: SSE stream generator functions
- [ ] `apps/local-ai-router/backends.py` - Add model state tracking
- [ ] `apps/local-ai-router/models.py` - Add StreamEvent Pydantic model

### Frontend
- [ ] `src/api/client.ts` - Add `sendMessageStream` method
- [ ] `src/types/api.ts` - Add `StreamEvent` interface
- [ ] `src/components/ChatInterface.tsx` - Add streaming state and status display
- [ ] `src/components/StreamStatus.tsx` - New file: Reusable status component

## Future Enhancements (Not in Scope)

- **Progress bar** - Show actual progress during generation (requires token-level streaming)
- **Model preloading** - Preload commonly used models to reduce warmup
- **Warmup caching** - Cache model state for faster subsequent loads
- **Detailed metrics** - Show token/s generation speed
- **Cancel button** - Allow canceling in-progress requests
- **Queue position** - Show position in queue if backend is busy
- **Historical warmup times** - Learn actual warmup times from metrics

## Success Criteria

- ✅ Users see immediate status feedback when sending messages
- ✅ "Warming up model..." shown during cold starts
- ✅ Status updates smoothly transition through phases
- ✅ Estimated time shown for model loading phase
- ✅ No breaking changes to existing non-streaming API
- ✅ Works across all model backends (3070, 3090, etc.)
- ✅ Error states handled gracefully

## Implementation Order

1. **Backend streaming infrastructure** (router.py, stream.py)
2. **Backend model state tracking** (backends.py)
3. **Frontend API client streaming** (client.ts)
4. **Frontend UI status display** (ChatInterface.tsx)
5. **Testing and refinement**
6. **Optional: Extract StreamStatus component**

## Dependencies

- **Requires:** FastAPI StreamingResponse (already available)
- **Requires:** httpx AsyncClient for streaming (likely already in use)
- **Requires:** Fetch API in browser (native)
- **Blocks:** None - can be implemented independently

## Estimated Complexity

- **Backend:** Medium (streaming implementation, state tracking)
- **Frontend:** Medium (async generator handling, UI state management)
- **Overall:** Medium complexity feature
- **Risk:** Low - backwards compatible, gradual rollout possible
