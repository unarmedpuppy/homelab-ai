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

Configure OwnTracks mobile apps to connect to:
- **Host**: `owntracks.server.unarmedpuppy.com` (if using TLS) or `192.168.86.47` (local)
- **Port**: `1883` (MQTT) or `8883` (MQTT over TLS)
- **Username**: `owntracks`
- **Password**: Same as `OTR_PASS`

## Volumes

- `./data/store` - Location data storage
- `./data/config` - OwnTracks Recorder configuration
- `./data/mosquitto/config` - Mosquitto configuration
- `./data/mosquitto/data` - Mosquitto data
- `./data/mosquitto/log` - Mosquitto logs

## Documentation

- [OwnTracks Booklet](https://owntracks.org/booklet/)
- [OwnTracks Recorder GitHub](https://github.com/owntracks/recorder)

