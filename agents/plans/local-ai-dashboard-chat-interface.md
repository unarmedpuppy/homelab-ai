# Local AI Dashboard - Chat Interface Implementation Plan

## Overview

Add a ChatGPT-style chat interface to the Local AI Dashboard with sidebar navigation, conversation history, and model testing capabilities.

## Current Status

**✅ Completed:**
- Added chat completion types to `src/types/api.ts` (ChatMessage, ChatCompletionRequest, ChatCompletionResponse)

**🚧 In Progress:**
- Nothing currently

**📋 Remaining:**
- Everything else below

## Design Requirements

### Layout
- **Left Sidebar** (fixed width ~300px):
  - Top: Navigation menu (Chat, Stats Overview)
  - Middle: Search conversations input
  - Bottom: Chat history list (sorted by last updated)
  - "New Chat" button at top of chat history

- **Main Panel** (flex-grow):
  - Default view: Chat interface
  - Can switch to Stats Overview or other views via sidebar navigation

### Chat Interface Features

1. **Model Selection**
   - Dropdown with options: auto (default), small, fast, big, medium, 3090, gaming-pc, glm, claude
   - Positioned above chat input

2. **Message Display**
   - User messages: right-aligned or distinct styling
   - Assistant messages: left-aligned or distinct styling
   - Show metadata for each assistant message (model, backend, tokens)
   - Auto-scroll to bottom on new messages

3. **Input Area**
   - Text input for messages
   - Send button
   - Loading state while waiting for response (spinner or "typing..." indicator)

4. **Advanced Settings** (Collapsible)
   - Temperature (0-2, default 1)
   - Max Tokens (optional)
   - Top P (0-1, default 1)
   - Frequency Penalty (0-2, default 0)
   - Presence Penalty (0-2, default 0)

5. **Conversation Memory**
   - All chat messages include `X-Enable-Memory: true` header
   - Auto-generate conversation IDs for new chats
   - Include `X-Project: dashboard` header
   - Include `X-User-ID: dashboard-user` header

### Conversation History (Sidebar)

- Display list of conversations (most recent first)
- Show conversation ID (first ~20 chars) and timestamp
- Show message count
- Click to load conversation into chat view
- Highlight currently selected conversation
- Search/filter functionality integrated into sidebar

### Navigation

- Chat (default view)
- Stats Overview (current Dashboard component)
- Remove separate RAG Search tab (integrate into conversation search)

## Implementation Steps

### Step 1: Add Chat API to Client
**File:** `src/api/client.ts`

```typescript
// Chat API
export const chatAPI = {
  sendMessage: async (params: {
    model: string;
    messages: ChatMessage[];
    conversationId?: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  }) => {
    const { conversationId, messages, ...requestBody } = params;

    const headers: Record<string, string> = {
      'X-Enable-Memory': 'true',
      'X-Project': 'dashboard',
      'X-User-ID': 'dashboard-user',
    };

    if (conversationId) {
      headers['X-Conversation-ID'] = conversationId;
    }

    const response = await apiClient.post<ChatCompletionResponse>(
      '/v1/chat/completions',
      requestBody,
      { headers }
    );

    return response.data;
  },
};
```

### Step 2: Create ChatInterface Component
**File:** `src/components/ChatInterface.tsx`

**State:**
- `messages: ChatMessage[]` - Current conversation messages
- `input: string` - User input text
- `isLoading: boolean` - Waiting for response
- `selectedModel: string` - Current model (default: 'auto')
- `conversationId: string | null` - Current conversation ID
- `showAdvanced: boolean` - Show/hide advanced settings
- `temperature: number` - Default 1
- `maxTokens: number | undefined`
- `topP: number` - Default 1
- `frequencyPenalty: number` - Default 0
- `presencePenalty: number` - Default 0
- `messageMetadata: Map<number, usage>` - Store token usage per message

**Functions:**
- `handleSendMessage()` - Send message to API, update conversation
- `handleNewChat()` - Clear messages, reset conversation ID
- `loadConversation(id: string)` - Load existing conversation from API

**UI Structure:**
```
┌─────────────────────────────────────┐
│ Model Selector  [auto ▼] [⚙️]      │ <- Model dropdown + settings toggle
├─────────────────────────────────────┤
│                                     │
│ [User Message]                      │
│             [Assistant Response]    │
│ [User Message]                      │
│             [Assistant Response]    │ <- Message list (scrollable)
│   └─ model: gpt2 | tokens: 150     │    with metadata
│                                     │
│                ↓                    │
├─────────────────────────────────────┤
│ [___________________________] [▸]   │ <- Input + send button
└─────────────────────────────────────┘
```

**Advanced Settings Panel:**
```
┌─────────────────────────────────────┐
│ ⚙️ Advanced Settings                │
│                                     │
│ Temperature: [slider] 1.0           │
│ Max Tokens: [input]                 │
│ Top P: [slider] 1.0                 │
│ Frequency Penalty: [slider] 0.0     │
│ Presence Penalty: [slider] 0.0      │
└─────────────────────────────────────┘
```

### Step 3: Create ConversationSidebar Component
**File:** `src/components/ConversationSidebar.tsx`

**Props:**
- `selectedConversationId: string | null`
- `onSelectConversation: (id: string) => void`
- `onNewChat: () => void`

**State:**
- `searchQuery: string`
- `conversations: Conversation[]` - From memoryAPI.listConversations()

**UI Structure:**
```
┌──────────────────────┐
│ [🔍 Search...]       │ <- Search input
├──────────────────────┤
│ [+ New Chat]         │ <- New chat button
├──────────────────────┤
│ ▸ conv-abc-123       │
│   3 msgs · 2h ago    │ <- Conversation item
│                      │
│ ▸ conv-def-456       │    (scrollable list)
│   8 msgs · 5h ago    │
│                      │
│ ▸ conv-ghi-789       │
│   2 msgs · 1d ago    │
└──────────────────────┘
```

### Step 4: Update App.tsx Layout
**File:** `src/App.tsx`

**New Layout:**
```typescript
type ViewType = 'chat' | 'stats';

const [activeView, setActiveView] = useState<ViewType>('chat');
const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);

// Layout:
// ┌──────────┬────────────────────────┐
// │          │                        │
// │          │   Main Panel           │
// │ Sidebar  │   (Chat or Stats)      │
// │          │                        │
// │          │                        │
// └──────────┴────────────────────────┘
```

**Structure:**
```jsx
<div className="flex h-screen bg-black">
  {/* Sidebar */}
  <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col">
    {/* Header */}
    <div className="p-4 border-b border-gray-800">
      <h1>Local AI Dashboard</h1>
    </div>

    {/* Navigation */}
    <div className="p-4 border-b border-gray-800">
      <button onClick={() => setActiveView('chat')}>Chat</button>
      <button onClick={() => setActiveView('stats')}>Stats Overview</button>
    </div>

    {/* Conversation Sidebar (only show in chat view) */}
    {activeView === 'chat' && (
      <ConversationSidebar
        selectedConversationId={selectedConversationId}
        onSelectConversation={setSelectedConversationId}
        onNewChat={() => setSelectedConversationId(null)}
      />
    )}
  </div>

  {/* Main Panel */}
  <div className="flex-1 overflow-auto">
    {activeView === 'chat' && (
      <ChatInterface conversationId={selectedConversationId} />
    )}
    {activeView === 'stats' && <Dashboard />}
  </div>
</div>
```

### Step 5: Testing & Refinement

1. **Test new chat creation**
   - Create new chat
   - Send messages
   - Verify conversation appears in sidebar
   - Verify messages stored with memory headers

2. **Test loading existing conversations**
   - Click conversation in sidebar
   - Verify messages load correctly
   - Send new message in existing conversation
   - Verify conversation updates

3. **Test model selection**
   - Test different models (auto, small, big, glm, claude)
   - Verify correct model used in API calls
   - Verify model metadata shown in responses

4. **Test advanced settings**
   - Adjust temperature, max_tokens, etc.
   - Verify settings sent in API requests
   - Verify behavior changes

5. **Test UI/UX**
   - Auto-scroll works
   - Loading states clear
   - Error handling works
   - Responsive on different screen sizes

## File Checklist

- [x] `src/types/api.ts` - Add chat types
- [ ] `src/api/client.ts` - Add chatAPI
- [ ] `src/components/ChatInterface.tsx` - Create component
- [ ] `src/components/ConversationSidebar.tsx` - Create component
- [ ] `src/App.tsx` - Update layout to sidebar + main panel
- [ ] `src/components/ConversationExplorer.tsx` - Can delete (functionality in sidebar)
- [ ] `src/components/RAGPlayground.tsx` - Can delete (search integrated in sidebar)

## Design Decisions

### Streaming: Deferred
- Complexity: Moderate (SSE/ReadableStream handling)
- Decision: Skip for v1, focus on good loading feedback
- Future: Can add later if needed

### Conversation Continuation: Deferred
- Feature: Edit/continue old conversations from UI
- Decision: Load read-only for now
- Can assess complexity after basic chat works

### RAG Search Integration
- Remove as separate tab
- Integrate into conversation search in sidebar
- Users can search conversations directly from sidebar

## API Integration Details

### Headers for Memory Storage
```typescript
{
  'X-Enable-Memory': 'true',              // Enable memory storage
  'X-Conversation-ID': conversationId,    // Use/create conversation
  'X-Project': 'dashboard',               // Tag with project
  'X-User-ID': 'dashboard-user',          // Associate with user
}
```

### Request Format
```typescript
POST /v1/chat/completions
{
  "model": "auto",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "How are you?"}
  ],
  "temperature": 1.0,
  "max_tokens": 2000
}
```

### Response Format
```typescript
{
  "id": "chatcmpl-abc123",
  "model": "gpt2",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "I'm doing well, thank you!"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 8,
    "total_tokens": 28
  }
}
```

## Notes

- Keep terminal aesthetic (monospace fonts, dark theme, terminal-style UI)
- Use existing color scheme (gray backgrounds, blue/green accents)
- Match existing component styling from Dashboard and ConversationExplorer
- All conversations automatically tracked in memory system
- Conversation IDs auto-generated if not provided

## Future Enhancements (Not in Scope)

- Streaming responses
- Edit message and regenerate
- Copy messages to clipboard
- Export conversation
- Delete conversations
- Conversation folders/tags
- Multi-user support
- Custom system prompts
