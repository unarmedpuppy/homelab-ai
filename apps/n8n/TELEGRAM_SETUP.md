# Telegram Integration Setup Guide

This guide shows you how to set up Telegram notifications and a Telegram bot that can communicate with an AI agent to execute server commands.

## Overview

### 1. Telegram Notifications
- Get notified on Telegram when server events occur
- Receive alerts for container failures, service issues, etc.

### 2. Telegram Bot with AI Agent
- Chat with a Telegram bot
- Bot uses OpenAI to understand your commands
- Bot can execute commands on your server (with safety checks)

## Prerequisites

1. **Telegram Bot Token**
   - Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
   - Get your bot token
   - Get your chat ID (for notifications)

2. **OpenAI API Key** (for AI agent bot)
   - Get API key from [OpenAI](https://platform.openai.com/api-keys)

3. **n8n Credentials**
   - Telegram credentials (bot token)
   - OpenAI credentials (API key)

## Step 1: Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Save the **bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Send `/mybots` → Select your bot → API Token to see it again

## Step 2: Get Your Chat ID

1. Search for `@userinfobot` on Telegram
2. Start a conversation - it will show your chat ID
3. Save your chat ID (a number like `123456789`)

## Step 3: Configure n8n Credentials

### A. Telegram Credential

1. Open n8n: `https://n8n.server.unarmedpuppy.com`
2. Go to **Credentials** → **New**
3. Search for **"Telegram"**
4. Select **Telegram** credential type
5. Name: `Telegram Bot`
6. **Access Token**: Paste your bot token from BotFather
7. Save

### B. OpenAI Credential

1. Go to **Credentials** → **New**
2. Search for **"OpenAI"**
3. Select **OpenAI** credential type
4. Name: `OpenAI API`
5. **API Key**: Paste your OpenAI API key
6. Save

## Step 4: Import Workflows

Import the following workflows:
- `workflows/telegram-notifications.json` - Adds Telegram notifications to existing workflows
- `workflows/telegram-ai-bot.json` - Telegram bot with OpenAI integration

## Step 5: Configure Workflows

### Telegram Notifications Workflow

1. Open the workflow
2. Update **"Send Telegram Message"** nodes:
   - Select **"Telegram Bot"** credential
   - Set **Chat ID** to your chat ID
3. Save

### Telegram AI Bot Workflow

1. Open the workflow
2. Configure **"Telegram Trigger"** node:
   - Select **"Telegram Bot"** credential
3. Configure **"OpenAI"** node:
   - Select **"OpenAI API"** credential
   - Set model (e.g., `gpt-4` or `gpt-3.5-turbo`)
4. Configure **"Execute Command"** nodes:
   - These will execute commands on your server
   - Review safety settings (see Security section)
5. Save and activate

## Security Considerations

### Command Execution Safety

The Telegram AI bot can execute commands on your server. Safety measures:

1. **Command Whitelist**: Only allow specific safe commands
2. **User Authorization**: Only allow commands from authorized Telegram users
3. **Command Validation**: Check commands before execution
4. **Logging**: Log all executed commands

### Recommended Restrictions

- Only allow read-only commands by default
- Require explicit permission for destructive commands
- Whitelist specific commands (docker ps, docker logs, etc.)
- Block dangerous commands (rm -rf, format, etc.)

## Usage

### Receiving Notifications

When server events occur, you'll receive Telegram messages like:
```
🚨 Server Alert: Docker Container Failure

Container: trading-bot
Status: died
Exit Code: 1
Severity: high

Logs: Out of memory error...
```

### Using the AI Bot

1. Start a chat with your Telegram bot
2. Send commands like:
   - "Check docker containers"
   - "Show logs for trading-bot"
   - "What's the server status?"
   - "Restart homepage container"
3. Bot uses OpenAI to understand your request
4. Bot executes appropriate commands and responds

## Example Commands

**Safe Commands (Read-only):**
- "List all containers"
- "Show logs for [service]"
- "Check disk usage"
- "What's the server status?"

**Action Commands (Require confirmation):**
- "Restart [container]"
- "Stop [container]"
- "Update [service]"

## Troubleshooting

### Bot Not Responding
- Check bot token is correct
- Verify bot is activated in n8n
- Check n8n execution logs

### Not Receiving Notifications
- Verify chat ID is correct
- Check Telegram credential is assigned
- Review workflow execution logs

### Commands Not Executing
- Check OpenAI API key is valid
- Verify Execute Command nodes have Docker socket access
- Review command whitelist settings

## Next Steps

- [ ] Set up command whitelist
- [ ] Configure user authorization
- [ ] Add command logging
- [ ] Set up command confirmation for destructive actions

