# Phase 5 Manual Testing Guide

**Date**: 2025-12-29
**Dashboard URL**: https://local-ai-dashboard.server.unarmedpuppy.com/
**Tester**: Josh

---

## Pre-Testing Checklist

- [ ] Dashboard is accessible at https://local-ai-dashboard.server.unarmedpuppy.com/
- [ ] Browser console is open (F12 → Console tab) to check for errors
- [ ] Network tab is open (F12 → Network tab) to monitor API calls

---

## Phase 5.1: Dynamic Model/Provider Selection

### Test 1: Model Dropdown Loads Dynamically
**Expected**: Model dropdown populates from `/admin/providers` API

1. Navigate to https://local-ai-dashboard.server.unarmedpuppy.com/
2. Observe the "Model:" dropdown in the header
3. **Check Network tab**: Look for `GET /admin/providers` request
4. **Expected**: Request returns 200 OK with provider/model data

**Result**: [ ] PASS / [ ] FAIL
**Notes**:

---

### Test 2: Model Display Format
**Expected**: Models show provider names in friendly format

1. Click the "Model:" dropdown
2. **Expected options**:
   - "Auto (Intelligent Routing)" (first option)
   - "Qwen 2.5 14B Instruct AWQ (Gaming PC (RTX 3090))"
   - "Qwen Image Edit 2509 (Gaming PC (RTX 3090))"
   - "Llama 3.1 8B Instruct (Server (RTX 3070))"
   - "DeepSeek Coder V2 Lite (Server (RTX 3070))"
   - "GLM-4 Flash (Z.ai)"
   - "GLM-4 Plus (Z.ai)"
   - "Claude 3.5 Sonnet (Anthropic (Claude))"
   - "Claude 3.5 Haiku (Anthropic (Claude))"

**Result**: [ ] PASS / [ ] FAIL
**Notes**:

---

### Test 3: Offline Provider Indication
**Expected**: Offline providers show "(offline)" and are disabled

1. Check provider status at https://local-ai-dashboard.server.unarmedpuppy.com/providers
2. Note which providers are offline
3. Go back to chat, open model dropdown
4. **Expected**: Offline provider models show "(offline)" label and are grayed out/disabled

**Offline Providers**:
- [ ] Server (RTX 3070) - Expected offline (no vLLM running)
- [ ] Z.ai - Expected offline (no API key)
- [ ] Anthropic - Expected offline (no API key)

**Result**: [ ] PASS / [ ] FAIL
**Notes**:

---

### Test 4: Auto-Refresh (30 seconds)
**Expected**: Model dropdown refreshes every 30 seconds

1. Open chat page
2. Open Network tab, filter to `/admin/providers`
3. Wait 30 seconds
4. **Expected**: New `GET /admin/providers` request appears every 30 seconds

**Result**: [ ] PASS / [ ] FAIL
**Notes**:

---

### Test 5: Loading State
**Expected**: Shows "Loading models..." while fetching

1. Hard refresh page (Ctrl+Shift+R or Cmd+Shift+R)
2. Immediately check model dropdown
3. **Expected**: Shows "Loading models..." option while data is fetching

**Result**: [ ] PASS / [ ] FAIL
**Notes**:

---

### Test 6: Send Message with Specific Model
**Expected**: Can select and send message with specific model

**Prerequisites**: Gaming PC vLLM must be running

1. Select "Qwen 2.5 14B Instruct AWQ (Gaming PC (RTX 3090))" from dropdown
2. Type message: "Say hello in exactly 5 words."
3. Click Send
4. **Expected**: Message sends successfully, response received

**Result**: [ ] PASS / [ ] FAIL / [ ] SKIP (vLLM not running)
**Notes**:

---

### Test 7: Message Metadata Display
**Expected**: Assistant response shows provider, model, backend, tokens

**Prerequisites**: Test 6 completed successfully

1. After receiving assistant response, scroll down to see metadata section
2. **Expected metadata** (below message content):
   - `provider: gaming-pc-3090` (appears first)
   - `model: qwen2.5-14b-awq` (or similar)
   - `backend: <backend-info>` (if available)
   - `tokens: X,XXX` (formatted with commas)

**Result**: [ ] PASS / [ ] FAIL / [ ] SKIP
**Notes**:

---

## Phase 5.2: Conversation Browsing & Search

### Test 8: Conversation Sidebar Display
**Expected**: Sidebar shows recent conversations

1. Look at left sidebar
2. **Expected**:
   - "New Chat" button at top
   - List of recent conversations below
   - Each conversation shows: ID, message count, relative time

**Result**: [ ] PASS / [ ] FAIL
**Notes**:

---

### Test 9: Search Conversations
**Expected**: Search filters conversation list

1. If search field exists, type a keyword from a previous conversation
2. **Expected**: Conversation list filters to matching conversations

**Result**: [ ] PASS / [ ] FAIL / [ ] N/A (no search field)
**Notes**:

---

### Test 10: Click Conversation to Load
**Expected**: Clicking conversation loads its messages

1. Click on a conversation in the sidebar
2. **Expected**:
   - URL changes to `/chat/:conversationId`
   - Messages from that conversation load in main panel
   - Conversation history displays correctly

**Result**: [ ] PASS / [ ] FAIL
**Notes**:

---

### Test 11: New Chat Button
**Expected**: "New Chat" clears current conversation

1. Click "New Chat" button in sidebar
2. **Expected**:
   - URL changes to `/`
   - Chat panel clears
   - Shows "Start a new conversation" placeholder

**Result**: [ ] PASS / [ ] FAIL
**Notes**:

---

## Phase 5.3: Enhanced Message Metadata

### Test 12: Provider Field Appears First
**Expected**: Provider ID is first in metadata section

1. Send a test message (if vLLM running)
2. Check assistant response metadata
3. **Expected**: Provider appears before model/backend/tokens

**Result**: [ ] PASS / [ ] FAIL / [ ] SKIP
**Notes**:

---

### Test 13: Token Count Formatting
**Expected**: Token count shows with comma separators

1. Send a longer message to generate more tokens
2. Check token count in metadata
3. **Expected**: Format like "1,234" not "1234" for numbers ≥1,000

**Result**: [ ] PASS / [ ] FAIL / [ ] SKIP
**Notes**:

---

### Test 14: All Metadata Fields Visible
**Expected**: All available metadata displays correctly

1. Send test message
2. Check all metadata fields are visible and readable
3. **Expected fields** (if available):
   - provider
   - model
   - backend
   - tokens

**Result**: [ ] PASS / [ ] FAIL / [ ] SKIP
**Notes**:

---

## Cross-Feature Integration Tests

### Test 15: Navigation Between Views
**Expected**: Can navigate between Chat/Providers/Stats

1. Click "🔌 Providers" in sidebar
2. Verify provider monitoring page loads
3. Click "💬 Chat" in sidebar
4. Verify chat page loads
5. Click "📊 Stats Overview" in sidebar
6. Verify stats page loads

**Result**: [ ] PASS / [ ] FAIL
**Notes**:

---

### Test 16: Browser Console Errors
**Expected**: No JavaScript errors in console

1. Open browser console (F12 → Console)
2. Navigate through all pages (Chat, Providers, Stats)
3. Send a test message (if vLLM running)
4. **Expected**: No red error messages in console

**Result**: [ ] PASS / [ ] FAIL
**Notes (if errors found)**:

---

## Known Limitations

The following tests require live vLLM backend and cannot be completed if Gaming PC vLLM is not running:

- [ ] Test 6: Send Message with Specific Model
- [ ] Test 7: Message Metadata Display
- [ ] Test 12: Provider Field Appears First
- [ ] Test 13: Token Count Formatting
- [ ] Test 14: All Metadata Fields Visible

**vLLM Status**: [ ] Running / [ ] Not Running

---

## Summary

**Total Tests**: 16
**Tests Passed**: _____
**Tests Failed**: _____
**Tests Skipped**: _____

**Overall Status**: [ ] PASS / [ ] FAIL / [ ] PARTIAL

**Critical Issues Found**:
1.
2.
3.

**Minor Issues Found**:
1.
2.
3.

**Additional Notes**:


---

**Testing Completed**: ___________
**Tester Signature**: Josh
