# Jellyfin with ZFS Encryption

This setup provides on-demand access to an encrypted ZFS dataset for Jellyfin, ensuring your data remains encrypted and mounted only when needed.

## Architecture

The solution consists of two components:
1. **Jellyfin Container**: Modified to only start when ZFS is already mounted
2. **Unlock Service**: A password-protected web UI that handles ZFS unlocking and Jellyfin lifecycle management

## Setup

### 1. Set up environment variables

**Option A: Use the setup script (requires Docker):**
```bash
cd apps/jellyfin
./setup-docker.sh
```

**Option B: Create a `.env` file manually in the `apps/jellyfin` directory:**

If creating manually, copy `env.template` to `.env` and edit:

```bash
cp env.template .env
# Edit .env with your values
```

For `UNLOCK_PASSWORD_HASH`, you can:
- Leave it empty to use the default password "changeme" (not recommended for production)
- Generate it with Docker: `docker run --rm -i python:3.11-slim sh -c "pip install --quiet werkzeug && python -c \"from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))\""`

### 3. Start the unlock service

The unlock service runs continuously and provides a web interface:

```bash
cd apps/jellyfin
docker-compose -f docker-compose-unlock.yml up -d
```

### 4. Access the UI

Open your browser and navigate to: `http://YOUR_SERVER_IP:8889`

You should see the unlock interface, which will also appear in your Homepage under the Services group as "ZFS Authenticator".

## Usage

### Unlocking and Starting Jellyfin

1. Open the unlock service UI
2. In the UI, you'll see three input fields:
   - **Username** & **Unlock Service Password**: The credentials you set during setup (these protect access to the unlock interface)
   - **ZFS Encryption Password**: Your existing ZFS dataset encryption key password (the password you use with `zfs load-key`)
3. Enter all three credentials and click "Unlock & Mount" to decrypt and mount the ZFS dataset
4. Click "Start Jellyfin" to start the Jellyfin container
5. Access Jellyfin at `http://YOUR_SERVER_IP:8096`

### Stopping and Locking

1. Click "Stop Jellyfin" to stop the container
2. Click "Unmount & Lock" to unmount and encrypt the ZFS dataset again
3. The data is now locked and inaccessible

### Homepage Integration

The unlock service automatically appears in your Homepage as "ZFS Authenticator" in the Services group. Click it to access the unlock interface.

## Security Features

- **No key storage**: The ZFS encryption password is never stored anywhere
- **Password-protected service**: The unlock service requires authentication
- **On-demand mounting**: ZFS dataset is only mounted when explicitly requested
- **Jellyfin won't start without mount**: The Jellyfin container will exit if ZFS is not mounted

## Troubleshooting

### Jellyfin won't start

- Check if ZFS is mounted: Look at the status indicators in the unlock UI
- Ensure the ZFS dataset path in `.env` is correct
- Check Jellyfin logs: `docker logs jellyfin`

### Can't unmount ZFS

- Make sure Jellyfin is stopped first
- Check if any processes are using the mounted dataset: `lsof ${ZFS_PATH}`

### Permission issues

- Ensure the unlock service has proper permissions to access the Docker socket
- Check that the ZFS dataset mount point path is correct
- Verify the user running the containers has ZFS permissions

## Manual operations

If needed, you can manually control ZFS:

```bash
# Unlock and mount
zfs load-key -a  # Will prompt for password
zfs mount -a

# Unmount
zfs unmount ${ZFS_PATH}

# Start/stop Jellyfin
docker-compose -f docker-compose.yml up -d jellyfin
docker-compose -f docker-compose.yml stop jellyfin
```

## Configuration

### Changing the unlock service port

Edit `docker-compose-unlock.yml` and change the port mapping:
```yaml
ports:
  - "8889:8888"  # Change the first number to your desired host port
```

### Updating the unlock service

```bash
cd apps/jellyfin
docker-compose -f docker-compose-unlock.yml down
docker-compose -f docker-compose-unlock.yml build
docker-compose -f docker-compose-unlock.yml up -d
```

