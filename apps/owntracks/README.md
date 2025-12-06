# OwnTracks

Location tracking and recording service with MQTT broker.

## Setup

### 1. Generate MQTT Password

Generate a password hash for the MQTT broker:

```bash
docker run --rm -it eclipse-mosquitto mosquitto_passwd -c -b /tmp/passwd owntracks YOUR_PASSWORD
docker run --rm -it eclipse-mosquitto cat /tmp/passwd
```

Copy the output and create `data/mosquitto/config/passwd` with that content.

Alternatively, create the file manually:
```bash
cd apps/owntracks
docker run --rm -it -v $(pwd)/data/mosquitto/config:/mosquitto/config eclipse-mosquitto mosquitto_passwd -c /mosquitto/config/passwd owntracks
# Enter password when prompted
```

### 2. Set Environment Variable

Create a `.env` file or set the `OTR_PASS` environment variable to match the MQTT password:

```bash
echo "OTR_PASS=your_password_here" > .env
```

### 3. Start Services

```bash
docker compose up -d
```

## Access

- **Web UI**: https://owntracks.server.unarmedpuppy.com
  - Local network: No authentication required
  - External: Basic auth required (unarmedpuppy / password)

## MQTT Configuration

The MQTT broker is available at:
- **Host**: `mosquitto` (internal) or `192.168.86.47` (external)
- **Port**: `1883` (MQTT) or `8883` (MQTT over TLS)
- **Username**: `owntracks`
- **Password**: Set in `OTR_PASS` environment variable

## Client Configuration

**Important**: MQTT traffic (port 1883/8883) does NOT go through Traefik, so basic auth does not apply. The mobile app connects directly to the MQTT broker.

Configure OwnTracks mobile apps to connect to:
- **Host**: `owntracks.server.unarmedpuppy.com` (if DNS resolves locally via AdGuard) or `192.168.86.47` (direct IP)
- **Port**: `1883` (MQTT) or `8883` (MQTT over TLS)
- **Username**: `owntracks`
- **Password**: Same as `OTR_PASS` (default: `owntracks123`)

### Connection Methods

1. **Local Network (Recommended)**: Use `192.168.86.47:1883` - fastest and most reliable
2. **Via DNS**: Use `owntracks.server.unarmedpuppy.com:1883` - requires AdGuard DNS rewrite to work locally
3. **External**: Use your public IP `76.156.139.101:1883` - requires port forwarding on your router

## Verifying It's Working

### 1. Check Web Interface
Visit `https://owntracks.server.unarmedpuppy.com/` - you should see the OwnTracks Recorder web interface.

### 2. Check MQTT Connection
```bash
# On the server, check if OwnTracks recorder is connected
docker logs owntracks | grep -i "connected\|subscribing"

# Check mosquitto for client connections
docker logs owntracks-mosquitto | grep -i "client connected"
```

### 3. Test MQTT Connection Manually
```bash
# Subscribe to see location updates
docker exec owntracks-mosquitto mosquitto_sub -h localhost -p 1883 -u owntracks -P owntracks123 -t "owntracks/#" -v

# Publish a test message (from another terminal)
docker exec owntracks-mosquitto mosquitto_pub -h localhost -p 1883 -u owntracks -P owntracks123 -t "owntracks/test" -m "hello"
```

### 4. Check Mobile App Connection
- Open the OwnTracks mobile app
- Configure connection settings (see Client Configuration above)
- Send a test location update
- Check the web interface at `https://owntracks.server.unarmedpuppy.com/` - you should see your device appear
- Check mosquitto logs: `docker logs owntracks-mosquitto | tail -20` - you should see connection messages

## Volumes

- `./data/store` - Location data storage
- `./data/config` - OwnTracks Recorder configuration
- `./data/mosquitto/config` - Mosquitto configuration
- `./data/mosquitto/data` - Mosquitto data
- `./data/mosquitto/log` - Mosquitto logs

## Documentation

- [OwnTracks Booklet](https://owntracks.org/booklet/)
- [OwnTracks Recorder GitHub](https://github.com/owntracks/recorder)

