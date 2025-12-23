# Smart Home 3D

Interactive 3D visualization of your smart home with real-time device monitoring and control.

## Access

- **URL**: https://home3d.server.unarmedpuppy.com
- **Port**: 3100 (direct access)
- **Status**: 🚧 IN DEVELOPMENT

## Features

- **3D Visualization**: Interactive Three.js scene of your home
- **Real-time Updates**: Live device state changes via WebSocket
- **Home Assistant Integration**: Connect to existing HA deployment
- **Device Control**: Toggle lights, adjust brightness, control thermostats
- **History Tracking**: Persist and visualize device state changes
- **Floor Plan Editor**: Define rooms and place devices in 3D space

## Quick Start

### Development

```bash
# Install dependencies
cd frontend && npm install
cd ../backend && npm install

# Start database
docker compose up -d smart-home-3d-db smart-home-3d-redis

# Run database migrations
cd backend && npx prisma db push

# Start development servers
cd frontend && npm run dev  # Port 5173
cd backend && npm run dev   # Port 3001
```

### Production

```bash
# Create .env from template
cp env.template .env
# Edit .env with your Home Assistant token

# Start all services
docker compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_PASSWORD` | Database password | Yes |
| `HOME_ASSISTANT_URL` | HA WebSocket URL | No |
| `HOME_ASSISTANT_TOKEN` | HA Long-lived access token | No |

### Getting Home Assistant Token

1. Go to Home Assistant → Profile
2. Scroll to "Long-Lived Access Tokens"
3. Create a new token
4. Copy to `HOME_ASSISTANT_TOKEN` in `.env`

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                           │
│  React + Three.js + TailwindCSS                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ 3D Scene │  │Dashboard │  │ Control Panel        │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────┴────────────────────────────────┐
│                      Backend                            │
│  Express + Socket.IO + Prisma                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │REST API  │  │WebSocket │  │Home Assistant Client │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                    Data Layer                           │
│  PostgreSQL (history) + Redis (cache)                  │
└─────────────────────────────────────────────────────────┘
```

## API Endpoints

### Devices

- `GET /api/devices` - List all devices
- `GET /api/devices/:id` - Get device by ID
- `POST /api/devices/:id/toggle` - Toggle device
- `PUT /api/devices/:id/state` - Set device state
- `POST /api/devices/sync` - Sync from Home Assistant

### Floor Plan

- `GET /api/floor-plan` - Get current floor plan
- `POST /api/floor-plan` - Save floor plan
- `PUT /api/floor-plan/rooms/:roomId/devices` - Add device to room

### History

- `GET /api/history/device/:deviceId` - Get device history
- `GET /api/history/device/:deviceId/aggregate` - Get aggregated history
- `GET /api/history/device/:deviceId/export` - Export as CSV

## WebSocket Events

### Client → Server

- `devices:subscribe` - Subscribe to device updates
- `device:toggle` - Toggle device
- `device:setState` - Set device state

### Server → Client

- `devices:initial` - Initial device list
- `device:stateChanged` - Device state changed
- `device:updated` - Device updated

## Development Tasks

See `agents/plans/smart-home-3d-visualization.md` for the full implementation plan.

Tracked in Beads:
- Epic: `home-server-623` - Smart Home 3D Visualization
- Phase 1: `home-server-cbz` - Foundation & Setup
- Phase 2: `home-server-1fs` - Floor Plan Processing
- Phase 3: `home-server-2lj` - 3D Scene Construction
- Phase 4: `home-server-6hr` - Smart Home Integration
- Phase 5: `home-server-wc4` - History & Persistence
- Phase 6: `home-server-s4k` - UI & Interaction
- Phase 7: `home-server-5cw` - Docker Deployment
- Phase 8: `home-server-341` - Testing & Optimization

## References

- [React Three Fiber](https://docs.pmnd.rs/react-three-fiber)
- [Three.js](https://threejs.org/)
- [Home Assistant WebSocket API](https://developers.home-assistant.io/docs/api/websocket/)
- [Prisma](https://www.prisma.io/docs)
