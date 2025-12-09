# SSH Setup for n8n Auto-Restart Workflow

## Overview

The Docker Container Auto-Restart workflow uses SSH to execute commands directly on the server. This is much simpler and more reliable than trying to use Docker API calls from within the n8n container.

## Why SSH?

- ✅ Server has all tools (docker, docker-compose, etc.)
- ✅ Simpler commands (no complex curl/python parsing)
- ✅ Can use docker-compose directly (handles dependencies)
- ✅ More reliable and maintainable

## Setup Steps

### 1. Create SSH User (Optional - can use existing user)

If you want to create a dedicated user for n8n:

```bash
# On the server
sudo adduser n8n-automation
sudo usermod -aG docker n8n-automation
sudo mkdir -p /home/n8n-automation/.ssh
sudo chmod 700 /home/n8n-automation/.ssh
```

### 2. Generate SSH Key Pair

**Option A: Generate on your local machine**

```bash
# Generate key pair
ssh-keygen -t ed25519 -f ~/.ssh/n8n_server_key -N ""

# Copy public key to server
ssh-copy-id -i ~/.ssh/n8n_server_key.pub unarmedpuppy@192.168.86.47 -p 4242

# Or manually:
cat ~/.ssh/n8n_server_key.pub | ssh unarmedpuppy@192.168.86.47 -p 4242 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

**Option B: Generate on server and download private key**

```bash
# On server
ssh-keygen -t ed25519 -f ~/.ssh/n8n_key -N ""
cat ~/.ssh/n8n_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Download private key to your local machine
scp -P 4242 unarmedpuppy@192.168.86.47:~/.ssh/n8n_key ~/.ssh/n8n_server_key
```

### 3. Configure SSH Credential in n8n

1. **Open n8n**: `https://n8n.server.unarmedpuppy.com`
2. **Go to Credentials** → **New**
3. **Select "SSH"** credential type
4. **Fill in**:
   - **Name**: `Server SSH`
   - **Host**: `192.168.86.47`
   - **Port**: `4242`
   - **Username**: `unarmedpuppy` (or the user you created)
   - **Authentication Method**: `Private Key`
   - **Private Key**: Paste the contents of `~/.ssh/n8n_server_key` (the private key)
   - **Passphrase**: (leave empty if key has no passphrase)
5. **Test Connection**: Click "Test" to verify it works
6. **Save**

### 4. Update Workflow

The workflow is already configured to use the SSH credential named "Server SSH". After creating the credential:

1. **Open the workflow** in n8n
2. **Check each SSH node**:
   - "Check Gluetun Health"
   - "Check Dependent Containers"
   - "Restart Container"
   - "Verify Restart"
3. **Select "Server SSH"** from the credential dropdown for each node
4. **Save the workflow**

### 5. Test the Workflow

1. **Manually execute** the workflow in n8n
2. **Check execution logs** to verify:
   - SSH connection works
   - Commands execute successfully
   - Container restart works

## SSH Key Format

The private key should be in OpenSSH format. If you have a different format, convert it:

```bash
# Convert to OpenSSH format
ssh-keygen -p -m PEM -f ~/.ssh/n8n_server_key
```

## Security Considerations

1. **Use a dedicated user** with limited permissions (if possible)
2. **Restrict SSH access** to specific IPs (if n8n is on a fixed IP)
3. **Use key-based auth only** (disable password auth)
4. **Rotate keys periodically**
5. **Monitor SSH access logs**

## Troubleshooting

### SSH Connection Fails

1. **Test SSH manually**:
   ```bash
   ssh -i ~/.ssh/n8n_server_key unarmedpuppy@192.168.86.47 -p 4242 "echo 'test'"
   ```

2. **Check SSH server config**:
   ```bash
   # On server
   sudo nano /etc/ssh/sshd_config
   # Ensure: PubkeyAuthentication yes
   # Restart: sudo systemctl restart sshd
   ```

3. **Check permissions**:
   ```bash
   # On server
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   ```

### Commands Fail

1. **Test command manually**:
   ```bash
   ssh -i ~/.ssh/n8n_server_key unarmedpuppy@192.168.86.47 -p 4242 "docker ps"
   ```

2. **Check user has Docker access**:
   ```bash
   # On server
   sudo usermod -aG docker unarmedpuppy
   # User needs to log out and back in for group to take effect
   ```

3. **Check docker-compose path**:
   ```bash
   ssh -i ~/.ssh/n8n_server_key unarmedpuppy@192.168.86.47 -p 4242 "cd ~/server/apps/media-download && docker-compose ps"
   ```

## Alternative: Use Existing User

If you want to use the existing `unarmedpuppy` user:

1. **Generate SSH key** (as above)
2. **Add public key** to `~/.ssh/authorized_keys` on server
3. **Use same credentials** in n8n (just point to existing user)

## Quick Reference

- **Server IP**: `192.168.86.47`
- **SSH Port**: `4242`
- **Default User**: `unarmedpuppy`
- **Server Path**: `~/server`
- **Docker Compose Path**: `~/server/apps/media-download`

