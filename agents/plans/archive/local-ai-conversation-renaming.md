# Local AI Dashboard - Conversation Renaming Feature

## Overview

Add the ability to rename conversations in the Local AI Dashboard for better organization and identification.

## Current State

- Conversations are identified only by their auto-generated IDs (e.g., `chatcmpl-abc-123`)
- No way to add custom names or descriptions
- Makes it hard to find specific conversations in the history

## Desired State

- Users can set custom names for conversations (e.g., "Planning new features", "Debug session")
- Names display in the conversation sidebar
- Fallback to showing conversation ID if no name is set
- Names are searchable

## Implementation Plan

### Backend (Local AI Router)

**File:** `apps/local-ai-router/memory.py` (or wherever memory system is implemented)

#### 1. Database Schema Update

Add `name` column to conversations table:

```sql
ALTER TABLE conversations ADD COLUMN name TEXT;
```

Or in the SQLAlchemy/model definition:
```python
class Conversation(Base):
    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    project = Column(String, nullable=True)
    name = Column(String, nullable=True)  # NEW FIELD
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

#### 2. New API Endpoint

Add `PATCH /memory/conversations/{id}` endpoint:

```python
@router.patch("/memory/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    update: ConversationUpdate,  # Pydantic model
    db: Session = Depends(get_db)
):
    """Update conversation metadata (e.g., name)"""
    conversation = db.query(Conversation).filter_by(id=conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if update.name is not None:
        conversation.name = update.name

    conversation.updated_at = datetime.utcnow()
    db.commit()

    return conversation
```

**Pydantic Model:**
```python
class ConversationUpdate(BaseModel):
    name: Optional[str] = None
```

#### 3. Update Existing Endpoints

Ensure `name` field is included in responses:
- `GET /memory/conversations` - List conversations with names
- `GET /memory/conversations/{id}` - Get single conversation with name
- `POST /memory/search` - Include names in search results

### Frontend (Dashboard)

**Files:** `apps/local-ai-dashboard/src/`

#### 1. Update Types

**File:** `src/types/api.ts`

```typescript
export interface Conversation {
  id: string;
  session_id?: string;
  user_id?: string;
  project?: string;
  name?: string;  // NEW FIELD
  created_at: string;
  updated_at: string;
  message_count?: number;
  messages?: Message[];
}
```

#### 2. Add API Client Method

**File:** `src/api/client.ts`

```typescript
export const memoryAPI = {
  // ... existing methods

  updateConversation: async (id: string, data: { name?: string }) => {
    const response = await apiClient.patch<Conversation>(
      `/memory/conversations/${id}`,
      data
    );
    return response.data;
  },
};
```

#### 3. Update ConversationSidebar UI

**File:** `src/components/ConversationSidebar.tsx`

Add rename functionality:
- Show custom name if set, otherwise show ID
- Add edit icon button next to each conversation
- Inline editing or modal for renaming
- Optimistic UI update

**UI Flow:**
1. User clicks edit icon (✏️) next to conversation name
2. Input field appears (or modal opens)
3. User types new name and presses Enter (or clicks Save)
4. API call to update name
5. UI updates immediately (optimistic update)
6. If API call fails, revert to previous name

**Example Implementation:**

```tsx
const [editingId, setEditingId] = useState<string | null>(null);
const [editName, setEditName] = useState('');

const updateNameMutation = useMutation({
  mutationFn: (params: { id: string; name: string }) =>
    memoryAPI.updateConversation(params.id, { name: params.name }),
  onSuccess: () => {
    // Refetch conversations to get updated data
    queryClient.invalidateQueries(['conversations']);
    setEditingId(null);
  },
});

const handleStartEdit = (conv: Conversation) => {
  setEditingId(conv.id);
  setEditName(conv.name || '');
};

const handleSaveEdit = (id: string) => {
  updateNameMutation.mutate({ id, name: editName });
};
```

**UI Elements:**

```tsx
{sortedConversations.map((conv) => (
  <div key={conv.id} className="...">
    {editingId === conv.id ? (
      // Edit mode
      <input
        value={editName}
        onChange={(e) => setEditName(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSaveEdit(conv.id)}
        onBlur={() => handleSaveEdit(conv.id)}
        autoFocus
      />
    ) : (
      // Display mode
      <div className="flex items-center justify-between">
        <div className="truncate">
          {conv.name || conv.id}
        </div>
        <button onClick={() => handleStartEdit(conv)}>
          ✏️
        </button>
      </div>
    )}
  </div>
))}
```

#### 4. Update ChatInterface (Optional)

**File:** `src/components/ChatInterface.tsx`

Add ability to name conversation from chat view:
- Show current conversation name at top
- Click to edit
- Auto-generate name from first user message (optional)

## Testing Plan

### Backend Testing

1. **Database Migration**
   - Verify `name` column added successfully
   - Existing conversations have NULL name (graceful handling)

2. **API Endpoint Testing**
   ```bash
   # Update conversation name
   curl -X PATCH http://localhost:8012/memory/conversations/conv-123 \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Conversation"}'

   # Verify name in list
   curl http://localhost:8012/memory/conversations?limit=10

   # Verify name in get single
   curl http://localhost:8012/memory/conversations/conv-123
   ```

3. **Edge Cases**
   - Empty name (should allow clearing)
   - Very long name (should truncate or reject)
   - Special characters in name
   - Non-existent conversation ID (404)

### Frontend Testing

1. **UI Testing**
   - Click edit icon → input field appears
   - Type name and press Enter → name updates
   - Click away without saving → reverts to original
   - Empty name → clears name, shows ID
   - Very long name → truncates with ellipsis

2. **API Integration**
   - Successful update → name persists after refresh
   - Failed update → shows error message
   - Optimistic update → UI updates immediately
   - Error handling → reverts on failure

3. **Search Integration**
   - Search by custom name finds conversation
   - Search by ID still works
   - Search matches partial names

## File Checklist

### Backend
- [ ] `apps/local-ai-router/memory.py` - Add database schema
- [ ] `apps/local-ai-router/memory.py` - Add PATCH endpoint
- [ ] `apps/local-ai-router/memory.py` - Update existing endpoints to return name
- [ ] Database migration script (if needed)

### Frontend
- [ ] `src/types/api.ts` - Add `name?` to Conversation interface
- [ ] `src/api/client.ts` - Add `updateConversation` method
- [ ] `src/components/ConversationSidebar.tsx` - Add rename UI
- [ ] `src/components/ChatInterface.tsx` - (Optional) Show/edit name in chat header

## Design Decisions

### Where to Store Names
- **Database table:** `conversations.name` column
- **Type:** `TEXT` (allows any length, frontend can truncate)
- **Nullable:** Yes (existing conversations won't have names)

### Name Display Priority
1. If `name` is set and non-empty → Show custom name
2. Otherwise → Show conversation ID
3. Always show ID somewhere (tooltip, metadata) for reference

### Rename UX
- **Inline editing** - Click icon, input appears in place
- **Enter to save** - Quick and efficient
- **Click away or Escape to cancel**
- **Optimistic updates** - Immediate feedback
- **Auto-focus** - Start typing immediately

### Search Behavior
- Search queries match against both `name` and `id`
- Custom names take priority in results
- Partial matching supported

## Future Enhancements (Not in Scope)

- Auto-generate names from first message
- Conversation tags/categories
- Bulk rename
- Name templates
- Conversation folders
- Color coding
- Pin important conversations
- Archive old conversations

## Success Criteria

- ✅ Users can set custom names for conversations
- ✅ Names persist across sessions
- ✅ Names display in conversation sidebar
- ✅ Search works with custom names
- ✅ UI is intuitive and responsive
- ✅ No breaking changes to existing functionality
- ✅ Graceful handling of conversations without names
