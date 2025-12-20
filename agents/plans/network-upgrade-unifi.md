# Network Upgrade Plan: Google Wifi → UniFi (Rack-Mount)

**Status**: Planned
**Created**: 2025-12-20
**Related Beads**: `home-server-n6y` (epic), `home-server-r7e` (purchase), `home-server-c9m` (setup), `home-server-c0y` (docs)

## Overview

Replace Google Home / Nest Wifi mesh system with UniFi rack-mount infrastructure for full network control.

### Priorities
- Full network control (VLANs, firewall, QoS, visibility)
- Rack-mount form factor (strong preference)
- Comparable or better simplicity than Google Wifi after setup
- Wired backhaul (no wireless mesh)

### Why Replace Google Wifi
- Isolates devices when internet is down (prevents local network access)
- No VLAN support
- Limited firewall/QoS control
- Minimal debugging/telemetry
- Cloud-dependent behavior

## Environment

| Metric | Value |
|--------|-------|
| House size | ~2,513 sq ft total |
| Main floor | ~1,386 sq ft |
| Basement | ~1,127 sq ft |
| Layout | Long, rectangular footprint |
| Rack location | Basement / utility room |
| Ethernet | Available or can be run |

### Floor Characteristics
- **Main Floor**: Open living/kitchen area
- **Basement**: Recreation room, office, bedrooms (finished)

## Hardware Decision

### Core Principle
```
UDM-SE (rack) ≈ Dream Router 7 (brains)
U7 Pro APs ≈ Dream Router 7 (Wi-Fi)
```

No rack-mount UniFi device exists with integrated Wi-Fi 7. External APs are mandatory.

### Final Hardware Selection

#### Gateway / Controller
**Ubiquiti UniFi Dream Machine Special Edition (UDM-SE)**
- Rack-mount (1U)
- Integrated PoE switch (powers APs directly)
- UniFi OS + Network Controller
- Sufficient throughput for home + homelab
- Avoids need for PoE injectors or extra switches

#### Wireless Access Points
**2 × Ubiquiti UniFi U7 Pro Access Points**
- Wi-Fi 7
- Wired backhaul (critical)
- Ceiling-mounted
- PoE powered from UDM-SE

### Purchase Details
**Micro Center Bundle**: UDM-SE + 2× U7 Pro APs

| Item | Approximate Price |
|------|-------------------|
| UDM-SE | ~$499 |
| U7 Pro AP (×2) | ~$189 each |
| **Total** | **~$877** |

### Rejected Alternatives
- **Dream Router 7**: Form factor rejection (non-rack)
- **UDM Pro Max**: Unnecessary performance tier for home use
- **U6+ / U6 Pro**: Wi-Fi 6, superseded by U7 Pro
- **ASUS RT-AX86U Pro + RT-AX58U**: Consumer-grade, less control

## Access Point Placement

### AP Count Rationale
- **Exactly 2 APs**
- 1 is insufficient (basement signal attenuation through floor)
- 3+ is unnecessary overkill for this footprint

### Placement Strategy

| Location | Position | Coverage Area |
|----------|----------|---------------|
| Main Floor | Ceiling-mounted near center of Living Room / Kitchen boundary | Living, dining, kitchen, primary bedroom, secondary bedroom |
| Basement | Ceiling-mounted in Recreation Room | Office, bedrooms, common areas |

**Note**: Vertical alignment between floors is acceptable.

## Comparison: Google Wifi vs UniFi

| Dimension | Google Wifi | UniFi Setup |
|-----------|-------------|-------------|
| Backhaul | Wireless mesh | Wired |
| Latency | Variable | Deterministic |
| Control | Minimal | Full (VLANs, firewall, QoS) |
| IoT isolation | Weak | Proper VLAN/SSID |
| Debugging | Nearly none | Full telemetry |
| Expandability | Limited | Modular |
| Local operation | Degrades without internet | Fully functional |
| Aesthetics | Visible pucks | Invisible ceiling APs + rack |

**Key insight**: Google Wifi hides problems. UniFi exposes them.

## Implementation Phases

### Phase 1: Purchase
- [ ] Purchase UDM-SE + U7 Pro bundle from Micro Center
- Related bead: `home-server-r7e`

### Phase 2: Physical Installation
- [ ] Rack-mount UDM-SE in basement
- [ ] Run ethernet cables to AP locations (if not already present)
- [ ] Ceiling-mount U7 Pro AP on main floor
- [ ] Ceiling-mount U7 Pro AP in basement recreation room
- [ ] Connect APs to UDM-SE PoE ports

### Phase 3: Initial Configuration
- [ ] Connect UDM-SE to modem
- [ ] Initial setup via UniFi mobile app or web UI
- [ ] Configure primary WiFi network (same SSID/password as Google Wifi for seamless transition)
- [ ] Adopt both U7 Pro APs in UniFi controller
- Related bead: `home-server-c9m`

### Phase 4: DNS Integration
- [ ] Configure DHCP to advertise AdGuard Home DNS (192.168.86.47)
- [ ] Verify all clients receive correct DNS via DHCP
- [ ] Disable any UDM built-in DNS features that conflict

### Phase 5: Optional VLAN Setup
- [ ] Create IoT VLAN (isolated from main network)
- [ ] Create Guest VLAN (internet only, no local access)
- [ ] Configure firewall rules between VLANs
- [ ] Create corresponding SSIDs for each VLAN

### Phase 6: Verification
- [ ] Verify coverage on both floors
- [ ] Test local network access with WAN disconnected
- [ ] Verify AdGuard DNS blocking works
- [ ] Test inter-device communication
- [ ] Verify server accessibility from all locations

### Phase 7: Documentation
- [ ] Update network topology diagrams
- [ ] Document new IP scheme if changed
- [ ] Update infrastructure-agent.md with new network details
- [ ] Add UniFi management URLs to documentation
- Related bead: `home-server-c0y`

## Network Configuration Details

### Current Network (Google Wifi)
- Server IP: `192.168.86.47` (static)
- Router Gateway: `192.168.86.1`
- Docker Network: `my-network`
- SSH Port: `4242`

### Planned Configuration (UniFi)
- Maintain `192.168.86.0/24` subnet if possible (minimizes changes)
- Or transition to `192.168.1.0/24` (UniFi default)
- Server gets static IP reservation
- AdGuard Home remains DNS server

### VLAN Design (Optional)

| VLAN ID | Name | Purpose | SSID |
|---------|------|---------|------|
| 1 | Default | Main network, trusted devices | HomeNetwork |
| 10 | IoT | Smart home devices, isolated | HomeNetwork-IoT |
| 20 | Guest | Visitors, internet only | HomeNetwork-Guest |
| 30 | Server | Server infrastructure | (wired only) |

## Rollback Plan

If issues arise during migration:
1. Keep Google Wifi hardware available for 30 days
2. Can revert by reconnecting Google Wifi to modem
3. Devices will auto-reconnect if SSID/password unchanged

## Future Expansion Options

- Additional U7 Pro APs for coverage extension
- UniFi Protect cameras (uses same controller)
- Additional PoE switches for more wired devices
- UniFi doorbell/access control

## References

- [UniFi Store - UDM-SE](https://store.ui.com/us/en/products/udm-se)
- [UniFi Store - U7 Pro](https://store.ui.com/us/en/products/u7-pro)
- [infrastructure-agent.md](../personas/infrastructure-agent.md) - Network infrastructure reference
- [GOOGLE_HOME_DNS_SETUP.md](../reference/setup/GOOGLE_HOME_DNS_SETUP.md) - Current DNS setup (will be superseded)
