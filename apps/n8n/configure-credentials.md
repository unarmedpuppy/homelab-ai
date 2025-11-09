# Configure n8n Credentials for AI Agent Workflows

## Webhook Service Status

✅ **AI Agent Webhook Service is running**
- URL: `http://192.168.86.47:8100` or `http://ai-agent-webhook:8100` (from Docker network)
- Health endpoint: `http://localhost:8100/health`
- Webhook endpoint: `http://ai-agent-webhook:8100/webhook/ai-agent` (from n8n container)
- Webhook Secret: `0e4c4ef968594f3bd1d77740646f88493efb015b21f9d74eb31e0308fd0b6d10`

## Required Credentials

### 1. Execute Command Nodes - No Credential Needed!

**Important**: The Execute Command nodes in these workflows don't actually need credentials!

Since the Docker socket is already mounted in the n8n container (`/var/run/docker.sock:/var/run/docker.sock:ro`), the Execute Command nodes can run Docker commands directly without any credentials.

**What to do**:
1. Open each workflow in n8n
2. For each **Execute Command** node, you may see a credential warning
3. **Simply ignore it or leave it unconfigured** - the Docker commands will work because the socket is mounted
4. If n8n requires a credential field, you can:
   - Leave it empty/unselected
   - Or the workflow might work without assigning anything

**Note**: If you see errors about missing credentials, the workflows might need to be updated to remove the credential references. The Docker commands should work directly since the socket is accessible.

### 2. AI Agent Webhook Auth Credential

**For**: HTTP Request nodes (calling the webhook service)

1. Go to **Credentials** → **New**
2. Select **HTTP Header Auth** type
3. Name: `AI Agent Webhook Auth`
4. Configuration:
   - **Header Name**: `Authorization`
   - **Header Value**: `Bearer 0e4c4ef968594f3bd1d77740646f88493efb015b21f9d74eb31e0308fd0b6d10`
   - Save the credential

## Update Workflows

### Update Webhook URLs

For each imported workflow, update the "Call AI Agent Webhook" node:

1. **Docker Container Failure Monitor**
2. **Docker Build Failure Monitor**  
3. **Service Health Monitor**

For each workflow:
1. Open the workflow in n8n
2. Find the **"Call AI Agent Webhook"** node
3. Update the URL to: `http://ai-agent-webhook:8100/webhook/ai-agent`
4. Select the **"AI Agent Webhook Auth"** credential you just created
5. Save the workflow

### Configure Execute Command Nodes

For each workflow with Execute Command nodes:
1. Open the workflow
2. Find each **Execute Command** node (Check All Containers, Get Container Logs, etc.)
3. **No credential needed** - Docker socket is already mounted in the container
4. If you see credential warnings, you can ignore them or leave the credential field empty
5. Test the nodes by executing the workflow manually to verify Docker commands work
6. Save the workflow

## Activate Workflows

After configuring credentials and updating URLs:
1. Open each workflow
2. Toggle the **Active** switch (top right) to enable
3. Verify workflows appear in the **Executions** tab

## Test

1. **Test webhook service**:
   ```bash
   curl http://localhost:8100/health
   ```

2. **Test workflow**:
   - Manually trigger a workflow execution
   - Check the execution logs
   - Verify webhook receives the event:
     ```bash
     curl http://localhost:8100/events?limit=5
     ```

## Troubleshooting

- **Webhook not receiving events**: Check webhook URL is correct and service is running
- **Docker commands failing**: Verify Docker socket credential is assigned
- **Authentication errors**: Check webhook secret matches in credential

