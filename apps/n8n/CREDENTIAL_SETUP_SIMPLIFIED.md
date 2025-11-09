# Simplified Credential Setup for n8n Workflows

## Quick Answer

**You only need to create ONE credential** - the HTTP Header Auth for the webhook.

The Execute Command nodes **don't need credentials** because the Docker socket is already mounted in the n8n container.

## Step-by-Step

### 1. Create HTTP Header Auth Credential (Required)

1. Open n8n: `https://n8n.server.unarmedpuppy.com`
2. Go to **Credentials** → **New**
3. Select **HTTP Header Auth** (or search for "Header Auth")
4. Name it: `AI Agent Webhook Auth`
5. Fill in:
   - **Header Name**: `Authorization`
   - **Header Value**: `Bearer 0e4c4ef968594f3bd1d77740646f88493efb015b21f9d74eb31e0308fd0b6d10`
6. Click **Save**

### 2. Update Workflows

For each of the 3 workflows:

1. **Open the workflow** in n8n
2. **Find the "Call AI Agent Webhook" node**
3. **Update the URL** to: `http://ai-agent-webhook:8100/webhook/ai-agent`
4. **Select the credential**: Choose "AI Agent Webhook Auth" from the credential dropdown
5. **For Execute Command nodes**: 
   - You might see a warning about missing credentials
   - **Ignore it** - Docker commands work because the socket is mounted
   - Leave the credential field empty/unselected
6. **Save the workflow**

### 3. Test Execute Command Nodes

To verify Docker commands work:

1. Open "Docker Container Failure Monitor" workflow
2. Click **"Execute Workflow"** button (top right)
3. Check the execution - the "Check All Containers" node should run successfully
4. If it works, you're good! If it fails, check the error message

### 4. Activate Workflows

1. Toggle the **Active** switch on each workflow
2. Done!

## Why No Credential for Docker?

The n8n container has the Docker socket mounted:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

This means Docker commands run directly from inside the n8n container, so no SSH or remote credentials are needed. The Execute Command node just runs `docker ps`, `docker logs`, etc. locally.

## Troubleshooting

**If Execute Command nodes fail:**
- Check that Docker socket is mounted: `docker inspect n8n | grep docker.sock`
- Verify the command syntax is correct
- Check execution logs in n8n for specific error messages

**If webhook calls fail:**
- Verify the credential is assigned to the HTTP Request node
- Check the webhook URL is correct: `http://ai-agent-webhook:8100/webhook/ai-agent`
- Test webhook service: `curl http://localhost:8100/health`

