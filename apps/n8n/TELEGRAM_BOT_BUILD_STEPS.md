# Building Telegram Bot Workflow - Step by Step

Since the simple test workflow works, I'm building the full Telegram bot workflow incrementally.

## Step 1: ✅ Test Workflow (Working)
- ID: `2q6BTAk3l9ZARpvf`
- Just receives message and replies
- **Status**: Opens successfully ✅

## Step 2: Basic Bot (Current)
- Receives message
- Parses message
- Checks authorization
- Executes command (currently just echoes the message)
- Sends result back

## Next Steps: Add OpenAI

Once Step 2 opens successfully, you can manually add OpenAI:

1. **Open the workflow** in n8n
2. **Add OpenAI node** between "Check Authorization" and "Execute Command"
3. **Configure OpenAI**:
   - Resource: `Chat`
   - Operation: `Create Message`
   - Model: `gpt-4`
   - System message: (your prompt)
   - User message: `={{ $json['message'] }}`
4. **Add Code node** to parse OpenAI response
5. **Update Execute Command** to use parsed command

## Or Use HTTP Request for OpenAI

If OpenAI node causes issues, use HTTP Request:

1. **Add HTTP Request node**
2. **Method**: `POST`
3. **URL**: `https://api.openai.com/v1/chat/completions`
4. **Authentication**: Header Auth
5. **Header**: `Authorization: Bearer YOUR_API_KEY`
6. **Body**: JSON with messages array

This approach is more reliable.

