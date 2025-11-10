# Telegram Integration - Quick Start Guide

## What You're Getting

1. **Telegram Notifications** - Get alerts on Telegram when server issues occur
2. **Telegram AI Bot** - Chat with a bot that can execute commands on your server using OpenAI

## Step 1: Create Telegram Bot (2 minutes)

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Follow instructions to name your bot
4. **Save the bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Send `/mybots` → Select your bot → API Token to see it again

## Step 2: Get Your Chat ID (1 minute)

1. Search for `@userinfobot` on Telegram
2. Start a conversation - it shows your chat ID (a number like `123456789`)
3. **Save your chat ID**

## Step 3: Configure n8n Credentials (3 minutes)

### A. Telegram Credential

1. Open n8n: `https://n8n.server.unarmedpuppy.com`
2. Go to **Credentials** → **New**
3. Search for **"Telegram"**
4. Name: `Telegram Bot`
5. **Access Token**: Paste your bot token from Step 1
6. Save

### B. OpenAI Credential (for AI bot)

1. Go to **Credentials** → **New**
2. Search for **"OpenAI"**
3. Name: `OpenAI API`
4. **API Key**: Paste your OpenAI API key
5. Save

## Step 4: Configure Workflows

### A. Telegram AI Bot Workflow

1. Open workflow: `https://n8n.server.unarmedpuppy.com/workflow/F1g7iulbXHm0qnBm`
2. **Telegram Trigger** node:
   - Select **"Telegram Bot"** credential
3. **Parse Message** node:
   - Edit the code, add your Telegram user ID to `authorizedUsers` array:
     ```javascript
     const authorizedUsers = [
       123456789  // Replace with your actual Telegram user ID
     ];
     ```
4. **OpenAI Chat** node:
   - Select **"OpenAI API"** credential
   - Model: `gpt-4` or `gpt-3.5-turbo` (your choice)
5. **Execute Command** node:
   - No credential needed (Docker socket is mounted)
6. Save and **Activate** the workflow

### B. Add Telegram to Existing Workflows

The Docker Container Failure Monitor workflow has been updated to include Telegram notifications. To configure:

1. Open the workflow
2. Find **"Format Telegram Message"** node
3. Update the code to set your chat ID:
   ```javascript
   chatId: '123456789'  // Replace with your Telegram chat ID
   ```
   Or add to n8n environment variables: `TELEGRAM_CHAT_ID=123456789`
4. **"Send Telegram Notification"** node:
   - Select **"Telegram Bot"** credential
5. Save

## Step 5: Test It!

### Test Notifications

1. Manually trigger a workflow that sends notifications
2. Check Telegram - you should receive a message

### Test AI Bot

1. Find your bot on Telegram (search for the name you gave it)
2. Send: `"List all docker containers"`
3. Bot should respond and execute `docker ps`
4. Try: `"Show logs for homepage"`
5. Bot should show container logs

## How It Works

### Notifications Flow
```
Server Event → n8n Workflow → Format Message → Send to Telegram → You get notified
```

### AI Bot Flow
```
You send message → Telegram → n8n → OpenAI (understands) → Execute Command → Send result back
```

## Example Commands for AI Bot

**Safe Commands:**
- "List all containers"
- "Show logs for trading-bot"
- "Check disk usage"
- "What containers are running?"
- "Show me the server status"

**Action Commands:**
- "Restart homepage container"
- "Stop trading-bot"
- "Check if grafana is running"

**Dangerous commands are blocked:**
- `rm -rf` - Blocked
- `format` - Blocked
- `dd if=` - Blocked

## Security Notes

1. **Authorization**: Only authorized Telegram users can use the bot (set in Parse Message node)
2. **Command Filtering**: Dangerous commands are automatically blocked
3. **Logging**: All commands are logged in n8n executions

## Troubleshooting

### Bot Not Responding
- Check bot token is correct
- Verify workflow is **Active**
- Check n8n execution logs

### Not Receiving Notifications
- Verify chat ID is correct
- Check Telegram credential is assigned
- Review workflow execution

### Commands Not Executing
- Check OpenAI API key is valid
- Verify Execute Command node works (Docker socket mounted)
- Review command in execution logs

## Next Steps

- [ ] Add your Telegram user ID to authorized users
- [ ] Test the bot with simple commands
- [ ] Add Telegram notifications to other workflows
- [ ] Customize the OpenAI system prompt for your needs

