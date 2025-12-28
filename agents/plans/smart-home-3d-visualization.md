# Smart Home 3D Visualization System - Implementation Plan

**Status**: In Progress
**Beads Epic**: `home-server-623`

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [Phase 1: Foundation & Setup](#phase-1-foundation--setup)
5. [Phase 2: Floor Plan Processing](#phase-2-floor-plan-processing)
6. [Phase 3: 3D Scene Construction](#phase-3-3d-scene-construction)
7. [Phase 4: Smart Home Integration](#phase-4-smart-home-integration)
8. [Phase 5: History & Persistence](#phase-5-history--persistence)
9. [Phase 6: User Interface & Interaction](#phase-6-user-interface--interaction)
10. [Phase 7: Docker Deployment](#phase-7-docker-deployment)
11. [Phase 8: Testing & Optimization](#phase-8-testing--optimization)

---

## Project Overview

### Objectives
- Create an interactive 3D web representation of your house using Three.js
- Integrate smart home peripherals for real-time monitoring and control
- Provide a live view dashboard showing current states
- Persist historical data for analysis and review
- Deploy via Docker for easy setup and maintenance

### Key Features
- **3D Visualization**: Interactive walkthrough of your home
- **Real-time Integration**: Live updates from smart devices
- **Photo Mapping**: Texture surfaces with actual room photos
- **Historical Tracking**: Save and visualize device state changes over time
- **Control Interface**: Toggle and adjust smart devices from the 3D view
- **Multi-user Support**: Access from any device in the home

---

## Technology Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18+** | UI framework |
| **Three.js / React Three Fiber** | 3D rendering |
| **@react-three/drei** | Helper utilities for R3F |
| **TailwindCSS** | Styling |
| **Zustand** | State management |
| **React Query** | Server state & caching |

### Backend
| Technology | Purpose |
|------------|---------|
| **Node.js 20 LTS** | Runtime |
| **Express.js** | API server |
| **Socket.IO** | Real-time communication |
| **MQTT.js** | Smart home communication |
| **PostgreSQL** | Data persistence |

### DevOps & Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker & Docker Compose** | Containerization |
| **Nginx** | Reverse proxy & static files |
| **Redis** | Caching & pub/sub |
| **Traefik** | SSL & routing (existing) |

### Smart Home Protocols
- **MQTT** (via Home Assistant, Zigbee2MQTT, etc.)
- **REST APIs** (for devices that support it)
- **WebSockets** (for real-time updates)
- **Home Assistant API** (existing deployment)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Browser                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  React UI    │  │  Three.js    │  │  Control Panel       │  │
│  │  (Dashboard) │  │  (3D View)   │  │  (Device Controls)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                     │                │
│         └─────────────────┴─────────────────────┘                │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │ HTTP/WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Container                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Traefik (Existing)                     │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                       │
│  ┌───────────────────────┴───────────────────────────────────┐  │
│  │                      Backend API                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐    │  │
│  │  │ Express  │  │Socket.IO │  │  Home Assistant      │    │  │
│  │  │   API    │  │ Server   │  │  Integration         │    │  │
│  │  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘    │  │
│  └───────┼─────────────┼───────────────────┼───────────────┘  │
│          │             │                   │                   │
│  ┌───────┴─────┐ ┌─────┴─────┐     ┌───────┴─────────┐        │
│  │  PostgreSQL │ │   Redis   │     │  Home Assistant │        │
│  │  (History)  │ │  (Cache)  │     │  (Existing)     │        │
│  └─────────────┘ └───────────┘     └─────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation & Setup

### 1.1 Project Structure

```
apps/smart-home-3d/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── 3d/
│   │   │   │   ├── Scene.tsx
│   │   │   │   ├── Room.tsx
│   │   │   │   ├── DeviceMarker.tsx
│   │   │   │   ├── FloorPlanEditor.tsx
│   │   │   │   └── CameraControls.tsx
│   │   │   ├── ui/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── DeviceList.tsx
│   │   │   │   ├── HistoryChart.tsx
│   │   │   │   └── ControlPanel.tsx
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       └── Sidebar.tsx
│   │   ├── hooks/
│   │   │   ├── useThreeScene.ts
│   │   │   ├── useDeviceStates.ts
│   │   │   └── useHistoryData.ts
│   │   ├── store/
│   │   │   ├── deviceStore.ts
│   │   │   └── sceneStore.ts
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── socket.ts
│   │   │   └── homeAssistant.ts
│   │   ├── types/
│   │   │   ├── device.ts
│   │   │   ├── floorPlan.ts
│   │   │   └── history.ts
│   │   ├── utils/
│   │   │   ├── floorPlanParser.ts
│   │   │   ├── textureMapper.ts
│   │   │   └── geometryHelpers.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   │   ├── floor-plans/
│   │   ├── textures/
│   │   └── models/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── backend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── devices.ts
│   │   │   ├── floorPlan.ts
│   │   │   └── history.ts
│   │   ├── services/
│   │   │   ├── homeAssistant.ts
│   │   │   ├── deviceManager.ts
│   │   │   └── historyService.ts
│   │   ├── models/
│   │   │   ├── Device.ts
│   │   │   ├── Room.ts
│   │   │   └── HistoryRecord.ts
│   │   ├── socket/
│   │   │   └── deviceSocket.ts
│   │   └── server.ts
│   ├── prisma/
│   │   └── schema.prisma
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

### 1.2 Docker Setup

**docker-compose.yml:**

```yaml
version: "3.8"

x-enabled: true

services:
  smart-home-3d:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: smart-home-3d
    restart: unless-stopped
    environment:
      - TZ=America/Chicago
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@smart-home-3d-db:5432/smarthome3d
      - REDIS_URL=redis://smart-home-3d-redis:6379
      - HOME_ASSISTANT_URL=http://homeassistant:8123
      - HOME_ASSISTANT_TOKEN=${HOME_ASSISTANT_TOKEN}
    ports:
      - "3100:3000"
    depends_on:
      - smart-home-3d-db
      - smart-home-3d-redis
    networks:
      - my-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.smarthome3d.rule=Host(`home3d.server.unarmedpuppy.com`)"
      - "traefik.http.routers.smarthome3d.entrypoints=websecure"
      - "traefik.http.routers.smarthome3d.tls.certresolver=myresolver"
      - "traefik.http.services.smarthome3d.loadbalancer.server.port=3000"
      # Homepage labels
      - "homepage.group=Infrastructure"
      - "homepage.name=Home 3D"
      - "homepage.icon=si-threedotjs"
      - "homepage.href=https://home3d.server.unarmedpuppy.com"
      - "homepage.description=3D smart home visualization"

  smart-home-3d-db:
    image: postgres:16-alpine
    container_name: smart-home-3d-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=smarthome3d
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    networks:
      - my-network

  smart-home-3d-redis:
    image: redis:alpine
    container_name: smart-home-3d-redis
    restart: unless-stopped
    volumes:
      - ./data/redis:/data
    networks:
      - my-network

networks:
  my-network:
    external: true
```

### 1.3 Initial Dependencies

**Frontend:**
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install three @react-three/fiber @react-three/drei
npm install zustand @tanstack/react-query socket.io-client
npm install tailwindcss postcss autoprefixer
npm install -D @types/three
```

**Backend:**
```bash
npm init -y
npm install express socket.io cors dotenv
npm install pg prisma @prisma/client ioredis
npm install -D typescript @types/node @types/express tsx
```

---

## Phase 2: Floor Plan Processing

### 2.1 Floor Plan Data Model

```typescript
export interface FloorPlan {
  id: string;
  name: string;
  scale: number; // pixels per meter
  levels: FloorLevel[];
}

export interface FloorLevel {
  id: string;
  name: string;
  elevation: number;
  rooms: Room[];
}

export interface Room {
  id: string;
  name: string;
  outline: Point[]; // polygon points
  area: number;
  ceilingHeight: number;
  walls: Wall[];
  doors: Door[];
  windows: Window[];
  devices: DeviceLocation[];
  textures: RoomTextures;
}

export interface Point {
  x: number;
  y: number;
}

export interface Wall {
  id: string;
  start: Point;
  end: Point;
  height: number;
  thickness: number;
  type: 'interior' | 'exterior' | 'load-bearing';
}
```

### 2.2 Floor Plan Editor

A 2D canvas editor to trace over floor plan images:
- Draw walls, rooms, and place device markers
- Export as JSON for 3D generation
- Support importing existing CAD/DXF files

### 2.3 Photo-to-Texture Pipeline

Process room photos into Three.js textures:
- Perspective correction
- Seamless tile pattern creation
- Automatic room surface mapping

---

## Phase 3: 3D Scene Construction

### 3.1 Scene Setup with React Three Fiber

- PerspectiveCamera with OrbitControls
- Ambient and directional lighting with shadows
- Environment preset for realistic lighting
- Grid helper for orientation

### 3.2 Room Component

- Generate geometry from room outline polygons
- Apply textures to floor, walls, ceiling
- Render doors and windows as openings
- Place device markers in 3D space

### 3.3 Device Marker Component

- Visual indicators for device types (lights, sensors, etc.)
- Animation for active states
- Hover/click interactions
- Real-time state updates

---

## Phase 4: Smart Home Integration

### 4.1 Home Assistant Integration

Connect to existing Home Assistant deployment:
- REST API for device discovery and control
- WebSocket for real-time state updates
- Entity mapping to 3D positions

### 4.2 Device Manager

- Register devices from Home Assistant
- Track device states in real-time
- Control devices from 3D interface
- Handle connection failures gracefully

### 4.3 WebSocket Integration

- Socket.IO for frontend-backend communication
- Broadcast device state changes to all clients
- Handle reconnection automatically

---

## Phase 5: History & Persistence

### 5.1 Database Schema (Prisma)

- Device table with positions and capabilities
- DeviceState table for historical records
- FloorPlan/Room tables for 3D configuration
- Efficient time-series queries with indexes

### 5.2 History Service

- Record all device state changes
- Aggregate data for charts (hourly, daily, weekly)
- Export to CSV for analysis
- Automatic cleanup of old data

---

## Phase 6: User Interface & Interaction

### 6.1 State Management (Zustand)

- Device store for real-time states
- Scene store for camera and selection
- Socket integration for updates

### 6.2 Dashboard Components

- Device list with status indicators
- History charts with Chart.js
- Control panel for device adjustment
- Room-based filtering

### 6.3 3D Interactions

- Click devices to select and control
- Hover for device info tooltips
- Camera presets for room views
- First-person walkthrough mode

---

## Phase 7: Docker Deployment

### 7.1 Multi-stage Dockerfile

- Build frontend with Vite
- Build backend with TypeScript
- Production image with Nginx + Node

### 7.2 Traefik Integration

- HTTPS with Let's Encrypt
- Subdomain: home3d.server.unarmedpuppy.com
- Add to Cloudflare DDNS

### 7.3 Homepage Dashboard

- Add to Infrastructure group
- Use Three.js icon

---

## Phase 8: Testing & Optimization

### 8.1 Performance Optimization

- Geometry instancing for repeated elements
- Texture compression and LOD
- Lazy loading for large scenes
- WebSocket message batching

### 8.2 Testing

- Unit tests for core logic
- Integration tests for API
- E2E tests for critical flows

---

## Quick Start Commands

```bash
# Development
cd apps/smart-home-3d
docker compose up -d smart-home-3d-db smart-home-3d-redis
cd frontend && npm run dev
cd backend && npm run dev

# Production
docker compose up -d

# Deploy
bash scripts/deploy-to-server.sh "Add smart-home-3d" --app smart-home-3d
```

---

## Related Resources

- [React Three Fiber Docs](https://docs.pmnd.rs/react-three-fiber)
- [Three.js Examples](https://threejs.org/examples/)
- [Home Assistant REST API](https://developers.home-assistant.io/docs/api/rest/)
- Existing: `apps/homeassistant/docker-compose.yml`
