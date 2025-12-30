# External Vertical GPU Mount Plan

**Status**: ✅ Complete
**Created**: 2025-12-20
**Last Updated**: 2025-12-30
**Completed**: 2025-12-30
**Epic**: `home-server-n6y` (Hardware Upgrade Plan)
**Related**: `home-server-bme` (Two-GPU Local AI Architecture)

## Related Beads

| Bead ID | Task | Status |
|---------|------|--------|
| `home-server-n6y` | Epic: Hardware Upgrade Plan | Open |
| `home-server-ngo` | Purchase 1U full-depth vented shelf | ✅ Complete (StarTech CABSHELF116V) |
| `home-server-k33` | Install RTX 3070 in external vertical rack mount | ✅ Complete (2025-12-30) |
| `home-server-6yo` | Install NVIDIA drivers + CUDA on Debian | ✅ Complete (2025-12-30) |

## Overview

Mount an RTX 3070 externally in a vertical orientation on top of the existing 3U rack-mounted home server, using a PCIe riser, while preserving full server serviceability.

### Goals
- Full server serviceability (server must slide out normally)
- Correct airflow (GPU fans facing outward)
- Mechanical safety (no GPU weight on riser)
- Expandability (future GPUs / reconfiguration)

## Server & Rack Context

### Server
| Attribute | Value |
|-----------|-------|
| Chassis | Sliger CX3701 |
| Height | 3U |
| Depth | ~15" |
| Motherboard | B550I AORUS Pro AX (Mini-ITX, PCIe 4.0 x16) |
| PSU | Corsair SF750 (SFX) |
| Airflow | Right → Left internally |

### Rack
| Attribute | Value |
|-----------|-------|
| Type | 12U wall-mounted |
| Height | ~3 ft above ground |
| U12 | UPS |
| U10-U11 | 2U utility shelf |
| U9 | PDU |
| U4-U6 | Server (3U) |
| Airflow | Intake below server, exhaust above (U3) |

## Critical Design Decision

**DO NOT attach GPU mount to the server chassis.**

Reason:
- Server must remain removable for maintenance
- Any rigid attachment would require full GPU disassembly to service server
- Drilling chassis = permanent, brittle, inferior solution

### Correct Architecture

```
Rack (fixed)
  ↓
1U Shelf (fixed infrastructure layer)
  ↓
External GPU mount (fixed)
  ↓
Server (removable compute unit)
```

The shelf mechanically decouples GPU from server.

## Physical Architecture

### GPU Orientation
- **Vertical**
- Fans facing left / outward (toward open room air)
- PCIe fingers facing down
- Power connectors facing up/right

### Mechanical Stack (Top → Bottom)

```
GPU
↓
NZXT Vertical GPU Bracket (acts as "case wall")
↓
Two steel L-brackets (vertical spine)
↓
1U full-depth vented rack shelf
↓
Server chassis (not mechanically attached)
```

- GPU weight path goes downward into shelf, not into riser or motherboard
- Shelf sits on rack rails, not on server
- Server can slide out once riser + power are disconnected

## Parts List

### Ordered (Dec 20, 2025)

| Item | Price | Status |
|------|-------|--------|
| 4× Black Heavy Duty Steel Adjustable Slotted L Brackets | $39.50 | Arriving overnight |
| BNUOK 280 PCS M5 Screws Assortment Kit | (incl.) | Arriving overnight |
| NZXT Vertical GPU Mounting Kit (AB-RH175-B1) | $53.93 | Arriving Monday |
| YEZriler 8-Pin PCIe Cable (25-inch/63cm) | $108.65 | Arriving overnight |
| GLOTRENDS 400mm PCIe 4.0 X16 Riser Cable | (incl.) | Arriving overnight |

**Total Ordered**: ~$202

### Purchased (Dec 2025)

| Item | Price | Status | Notes |
|------|-------|--------|-------|
| StarTech.com 1U Server Rack Shelf (CABSHELF116V) | $49.99 | ✅ Purchased | 16" deep, vented, 44lb capacity, includes M6 mounting hardware |
| RTX 3070 GPU | (owned) | ✅ Owned | Already have |

### Shelf Specifications
- **Model**: StarTech.com CABSHELF116V
- **Height**: 1U
- **Depth**: 16" (40.6 cm)
- **Width**: 17.4" (standard 19" rack width)
- **Material**: SPCC commercial cold-rolled steel
- **Weight Capacity**: 44 lbs (20 kg)
- **Mounting**: Front-mount cantilever (includes 4× M6 cage nuts, 4× M6 screws)
- **Vented**: Yes (improves airflow)
- **Amazon Link**: https://www.amazon.com/dp/B071YP4JL5

**Why This Shelf**:
- 16" depth provides ample clearance for GPU + L-brackets + NZXT mount
- Vented design improves airflow around GPU
- Heavy-duty steel construction (44lb capacity exceeds GPU weight)
- Includes mounting hardware (M6 cage nuts and screws)
- Well-reviewed and proven design

## Fastener Specifications

L-bracket slots are 6.3mm → **M5 hardware is correct**

### NZXT Bracket → L-Brackets
- M5 × 16mm bolts
- Flat washer (both sides)
- Nylock nut

### L-Brackets → Shelf
- M5 × 20mm bolts
- Flat washer
- Nylock nut

Washers eliminate play from slot clearance.

## PCIe Riser Routing

- From motherboard PCIe slot
- Gentle vertical exit (no sharp bends)
- Down rear corner
- Up into GPU mount
- Supported every ~8-10 cm with cable anchors

**Chosen**: GLOTRENDS 400mm PCIe 4.0 x16 riser

## Cooling Strategy

- GPU draws ambient room air
- Exhaust blows away from rack
- Likely sufficient without extra fans

**Optional Enhancement**:
- 1-2 × 120mm PWM fans mounted near GPU
- Powered from motherboard header or SATA PWM hub

## Assembly Steps

1. Install 1U full-depth shelf in rack above server (U3)
2. Bolt two slotted L-brackets vertically to shelf
3. Bolt NZXT vertical GPU bracket to L-brackets (horizontal bolts)
4. Install GPU into NZXT bracket
5. Route PCIe riser with gentle curves
6. Connect GPU power from PSU (8-pin PCIe cable)
7. Optional: add stabilizer strap to rack frame (not server)
8. Test thermals + PCIe link speed

## Verification Checklist

- [x] GPU seated correctly in NZXT bracket
- [x] All M5 bolts torqued with washers
- [x] PCIe riser has no sharp bends
- [x] PCIe link speed verified (Gen4 x16)
- [x] GPU temps under load acceptable
- [x] Server can slide out with GPU disconnected
- [x] No interference with rack airflow
- [x] NVIDIA driver installed (535.247.01)
- [x] CUDA 12.2 available
- [x] Docker GPU support working (nvidia-container-toolkit)

## Rejected Options (Do Not Revisit)

- ❌ Drilling server chassis
- ❌ Mounting GPU directly to server
- ❌ Mining-style USB risers
- ❌ PCIe 3.0 risers
- ❌ Long (>40 cm) risers without support
- ❌ Hanging GPU weight from riser
- ❌ Rack-rail cantilevered GPU mounts

## Future Expansion

This shelf architecture allows:
- GPU swap (3070 → 3090)
- Additional shelves for more GPUs
- No changes to server chassis

PSU sizing (SF750) already supports 3090 + system load.

## Completion Summary (2025-12-30)

**What was done**:
1. Installed StarTech.com 1U vented shelf (CABSHELF116V) in rack above server at U3
2. Mounted steel L-brackets vertically to shelf
3. Attached NZXT vertical GPU bracket to L-brackets
4. Installed RTX 3070 into NZXT bracket (vertical orientation, fans facing outward)
5. Routed GLOTRENDS 400mm PCIe 4.0 x16 riser from motherboard to GPU
6. Connected 8-pin PCIe power from PSU (YEZriler 25-inch/63cm cable)
7. Installed NVIDIA driver 535.247.01 on Debian
8. Installed nvidia-container-toolkit for Docker GPU support
9. Verified GPU operation with `nvidia-smi` and Docker test container

**Previous GPU removed**:
- GT 1030 was removed from the system (no longer needed with RTX 3070)

**Final Configuration**:
```
U3: 1U Shelf with RTX 3070 in vertical mount
U4-U6: Server (3U Sliger CX3701)
PCIe: 4.0 x16 riser connecting motherboard to external GPU
Driver: NVIDIA 535.247.01
CUDA: 12.2
```

## Integration with Two-GPU Architecture

This hardware installation is a prerequisite for the Two-GPU Local AI Architecture (`home-server-bme`):

1. **Physical Install** (this plan) → RTX 3070 mounted in rack
2. **Software Setup** (`home-server-6yo`) → NVIDIA drivers + CUDA on Debian
3. **Router Service** (`home-server-jz4`) → Intelligent routing between 3070 and 3090

## References

- [local-ai-two-gpu-architecture.md](local-ai-two-gpu-architecture.md) - Software architecture plan
- [network-upgrade-unifi.md](network-upgrade-unifi.md) - Network infrastructure plan
- [infrastructure-agent.md](../personas/infrastructure-agent.md) - Infrastructure documentation
