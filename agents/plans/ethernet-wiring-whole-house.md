# Home Ethernet Wiring Plan

**Status**: Planned
**Created**: 2025-12-20
**Epic**: `home-server-w8p` (Whole-house Ethernet wiring)
**Parent Epic**: `home-server-n6y` (Hardware Upgrade Plan)
**Related**: `agents/plans/network-upgrade-unifi.md` (UniFi network upgrade)

## Related Beads

| Bead ID | Task | Status |
|---------|------|--------|
| `home-server-w8p` | Epic: Whole-house Ethernet wiring | Open |
| `home-server-3zc` | Purchase Ethernet wiring materials | Ready |
| `home-server-fig` | Plan and mark Ethernet drop locations | Ready |
| `home-server-jan` | Drill penetrations and install pull strings | Blocked by `3zc`, `fig` |
| `home-server-o7e` | Pull all Ethernet cables | Blocked by `jan` |
| `home-server-7vs` | Terminate all Ethernet runs | Blocked by `o7e` |
| `home-server-0lu` | Test and document all Ethernet runs | Blocked by `7vs` |

## Overview

Hard-wired Ethernet throughout the house with PoE support for cameras and Wi-Fi access points. DIY installation with professional-grade topology.

### Goals
- Ethernet termination in every bedroom
- PoE security cameras (interior + exterior)
- Ceiling-mounted PoE Wi-Fi access points
- Centralized, professional-grade star topology
- Least destructive, clean, future-proof install

## House Context

| Attribute | Value |
|-----------|-------|
| Total Size | ~2,500 sq ft |
| Floors | Basement + Main Floor + Attic access |
| MDF Location | Basement office (server rack corner) |
| Installer | DIY (technically competent) |

## Core Architectural Decisions

### Network Topology
- **Star topology** - all runs home-run to single patch panel
- No daisy-chaining
- No mid-point terminations

### Main Distribution Frame (MDF)
- **Location**: Basement office (server corner)
- **Contains**:
  - Patch panel
  - PoE switch
  - Router/firewall (UDM-SE)
- No termination in attic
- No termination in utility room

### Vertical Cable Spine
- Single vertical drop from attic → basement
- **Wall**: Shared wall between utility room and office (office side)
- **Rationale**:
  - Interior wall
  - Continuous attic-to-basement path
  - Adjacent to server room

## Physical Routing Strategy

### Movement Rules
| Direction | Method |
|-----------|--------|
| Vertical | Inside stud bays only |
| Horizontal | Attic or basement ceiling joists only |

**Critical**: No horizontal fishing inside finished walls

### Attic
- Used only as distribution pass-through
- Cables laid across joists (not stapled tight)
- Drops down interior walls to rooms and devices

### Basement
- Cables exit vertical spine high on office wall
- Routed horizontally along ceiling joists
- Single vertical drop into rack location

## Wall & Ceiling Penetrations

### Vertical Spine
- One 1.5–2" drilled path through:
  - Attic top plate
  - Subfloor
  - Basement top/bottom plates
- Fire-blocked after cable pulls

### Office Wall Exit
- One 2–3" opening high on wall
- Brush plate or grommet installed
- Allows bundle to turn from vertical → horizontal

## Future-Proofing

- Install one empty 2" conduit (ENT or EMT)
- **Path**: Office ceiling → utility room ceiling
- **Purpose**: Allows future rack relocation without re-fishing
- Pull string installed, ends capped and labeled

## Cable Specification

| Attribute | Value |
|-----------|-------|
| Type | Cat6, solid copper |
| Rating | CMR (riser-rated) |
| Total Runs | ~28 |
| Avg Length | 60–90 ft |
| Total Cable | ~3,000 ft |

### Do NOT Use
- ❌ CCA (copper-clad aluminum)
- ❌ Cat5e
- ❌ Cat6A (unnecessary stiffness)

## Drop Count

| Category | Runs |
|----------|------|
| Bedrooms (5 × 2 drops) | 10 |
| Office wall drops | 4 |
| Wi-Fi APs (ceiling) | 2 |
| Cameras (PoE) | 8 |
| Spare / future | 4 |
| **Total** | **28** |

## Room-by-Room Plan

### Bedrooms
- 2 Cat6 drops per bedroom
- Interior walls only
- Standard outlet height wall plates

### Office
- 4 wall drops (desk, printer, test gear)
- Separate from rack feeds

### Wi-Fi Access Points
- 1 ceiling AP on main floor (central living area)
- 1 ceiling AP in basement recreation room
- PoE, Cat6 home-run each
- **Note**: These feed the UniFi U7 Pro APs from network upgrade plan

### Cameras
- **Interior**: ceiling or high-corner mounts (3 minimum)
- **Exterior**: soffit-mounted preferred (5 minimum)
- Cable exits attic directly into soffit
- Drip loops + silicone sealing
- Avoid exterior wall fishing when possible

## Termination Strategy

### Rack Side (MDF)
- 24- or 48-port Cat6 patch panel
- Vertical cable manager
- 3–6 ft service loops

### Room Side
- Keystone Cat6 jacks
- Low-voltage old-work brackets
- No electrical boxes

## Labeling Scheme

**Format**: `[TYPE]-[FLOOR]-[ROOM]-[POSITION]`

### Examples
| Label | Description |
|-------|-------------|
| `BR-UP-BED2-NORTH-1` | Bedroom 2, upstairs, north wall, port 1 |
| `CAM-EXT-GARAGE-E` | Exterior camera, garage, east side |
| `AP-MAIN-CENTER` | Access point, main floor, center |
| `OFF-BSMT-DESK-2` | Office, basement, desk area, port 2 |

**Critical**: Label both ends immediately after pull, before termination.

## Implementation Order

### Phase 1: Preparation
1. [ ] Plan exact drop locations per room
2. [ ] Purchase materials (cable, patch panel, jacks, tools)
3. [ ] Mark all penetration points

### Phase 2: Infrastructure
4. [ ] Drill all penetrations (spine + room drops)
5. [ ] Install pull strings in all paths
6. [ ] Install future-proofing conduit (office → utility)

### Phase 3: Cable Pulls
7. [ ] Pull attic → basement spine bundle
8. [ ] Pull upstairs room drops
9. [ ] Pull basement room drops
10. [ ] Pull AP ceiling runs
11. [ ] Pull camera runs (interior then exterior)

### Phase 4: Termination
12. [ ] Label all cable ends
13. [ ] Terminate patch panel (rack side)
14. [ ] Terminate wall jacks (room side)
15. [ ] Install wall plates and brush plates

### Phase 5: Verification
16. [ ] Test all runs with cable tester
17. [ ] Document final run map
18. [ ] Fire-block all penetrations

## Materials List

### Cable & Termination
| Item | Quantity | Notes |
|------|----------|-------|
| Cat6 CMR cable (1000 ft box) | 3 | Solid copper, riser-rated |
| 48-port Cat6 patch panel | 1 | Rack-mount |
| Cat6 keystone jacks | 30+ | RJ45 |
| Low-voltage old-work brackets | 15+ | For wall plates |
| 2-port wall plates | 10+ | For bedrooms |
| 1-port wall plates | 8+ | For APs, cameras |
| Brush plates | 2 | Cable exits |

### Tools & Accessories
| Item | Notes |
|------|-------|
| Cable tester | Verify all runs |
| Punch-down tool | 110-style for keystone |
| Fish tape / rods | For wall pulls |
| Drill bits (1.5", 2", 3") | For penetrations |
| Cable labels | Both ends of every run |
| Velcro cable ties | Cable management |
| Fire-stop caulk | Seal penetrations |

## Explicit "Do NOT" List

- ❌ Do NOT terminate in attic
- ❌ Do NOT create a utility-room patch point
- ❌ Do NOT extend Ethernet via patch cords between rooms
- ❌ Do NOT fish horizontally inside finished walls
- ❌ Do NOT use CCA cable
- ❌ Do NOT terminate before all pulls are complete

## Integration with Other Plans

### UniFi Network Upgrade
- Ethernet runs for ceiling APs feed the UniFi U7 Pro access points
- UDM-SE PoE switch powers APs directly
- See `agents/plans/network-upgrade-unifi.md`

### Future Security Cameras
- Camera runs designed for UniFi Protect compatibility
- PoE powered from UDM-SE or additional PoE switch
- 8 total camera drops (3 interior, 5 exterior)

## References

- [network-upgrade-unifi.md](network-upgrade-unifi.md) - UniFi network plan
- [infrastructure-agent.md](../personas/infrastructure-agent.md) - Network infrastructure docs
