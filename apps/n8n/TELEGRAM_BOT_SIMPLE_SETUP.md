# Simple Telegram Bot Setup (Without OpenAI)

I've created a minimal version of the Telegram bot that works without the OpenAI node (which was causing the error). You can add OpenAI later once the basic workflow is working.

## What's Included

The minimal workflow:
- ✅ Receives Telegram messages
- ✅ Checks authorization
- ✅ Executes a simple command (`docker ps`)
- ✅ Sends results back to Telegram

## Next Steps: Add OpenAI

Once you can open the workflow successfully:

1. **Open the workflow** in n8n
2. **Add an OpenAI node** between "Check Authorization" and "Execute Command"
3. **Configure the OpenAI node**:
   - Resource: `Chat`
   - Operation: `Create Message`
   - Model: `gpt-4` or `gpt-3.5-turbo`
   - Add system message
   - Add user message: `={{ $json['message'] }}`
4. **Add a Code node** to parse OpenAI response and extract commands
5. **Update Execute Command** to use the parsed command

## Or Use HTTP Request for OpenAI

If the OpenAI node still causes issues, use an HTTP Request node instead:

1. **Add HTTP Request node**
2. **Configure**:
   - Method: `POST`
   - URL: `https://api.openai.com/v1/chat/completions`
   - Authentication: Header Auth
   - Header Name: `Authorization`
   - Header Value: `Bearer YOUR_OPENAI_API_KEY`
   - Body Content Type: `JSON`
   - Body:
     ```json
     {
       "model": "gpt-4",
       "messages": [
         {
           "role": "system",
           "content": "You are a helpful system administrator assistant..."
         },
         {
           "role": "user",
           "content": "={{ $json['message'] }}"
         }
       ],
       "temperature": 0.3,
       "max_tokens": 500
     }
     ```

This approach is more reliable and doesn't have the parameter structure issues.

