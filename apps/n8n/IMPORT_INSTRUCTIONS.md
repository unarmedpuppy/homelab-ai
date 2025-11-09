# Quick Import Instructions

The workflows have been added to your server. To import them into n8n:

## Option 1: Manual Import (Easiest)

1. **Open n8n**: Navigate to `https://n8n.server.unarmedpuppy.com`
2. **Login** with your credentials
3. **Import each workflow**:
   - Click the **three-dot menu** (⋮) in the upper-right corner
   - Select **"Import from File"**
   - Navigate to: `~/server/apps/n8n/workflows/`
   - Import each file:
     - `docker-container-failure-monitor.json`
     - `docker-build-failure-monitor.json`
     - `service-health-monitor.json`

## Option 2: Set Up API Key First (For Automated Import)

If you want to use the import script:

1. **Generate API Key in n8n**:
   - Go to `https://n8n.server.unarmedpuppy.com`
   - Click your profile → **Settings** → **API**
   - Click **Create API Key**
   - Copy the key

2. **Add to .env file**:
   ```bash
   cd ~/server/apps/n8n
   echo "N8N_API_KEY=your-api-key-here" >> .env
   ```

3. **Run import script**:
   ```bash
   cd ~/server/apps/n8n
   export N8N_API_KEY=$(grep N8N_API_KEY .env | cut -d'=' -f2)
   bash import-workflows.sh
   ```

## After Import

1. **Configure Credentials** (required for workflows to work):
   - **Docker Socket**: Create credential for Execute Command nodes
   - **AI Agent Webhook Auth**: Create HTTP Header Auth credential (if webhook service is set up)

2. **Update Webhook URLs**: 
   - Open each workflow
   - Update the "Call AI Agent Webhook" node with the correct webhook URL
   - Currently set to: `https://n8n.server.unarmedpuppy.com/webhook/ai-agent`
   - Change to: `http://ai-agent-webhook:8080/webhook/ai-agent` (if using Docker) or `http://192.168.86.47:8080/webhook/ai-agent` (if standalone)

3. **Activate Workflows**: Toggle the **Active** switch on each workflow

## Current Status

✅ Workflow files are on the server at: `~/server/apps/n8n/workflows/`
⏳ Waiting for manual import or API key setup

