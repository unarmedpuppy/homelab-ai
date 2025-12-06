# Hardware Specifications

### BIOS

- **Version**: MC123IOE.100
- **ME FW Version**: 12/0.41.1435

### CHASSIS

- Sliger CX3701 | 3U 15" Deep Chassis | 10 X tray-less 3.5 HDD hot-swap/direct-wired SATA connectors | SFX PSU | Mini ITX Motherboard

### MOTHERBOARD

- B550I AORUS Pro AX AMD AM4 Mini-ITX Motherboard

### POWER SUPPLY

- Corsair SF750 (2018) 750 W 80+ Platinum Certified Fully Modular SFX Power Supply

### CPU

**Original**:
- Model: Intel(R) Celeron(R) G4900T CPU @ 2.90GHz
- Cores: 2
- Memory: 64008 MB

**Upgraded**:
- Model: Intel Core i7-6700K
- Cores: 4 (8 threads with hyperthreading)
- Clock Speed: 4.0 GHz (base)
- Socket: LGA 1151
- TDP: 91W
- Integrated Graphics: Intel HD Graphics 530

### RAM

- **Capacity**: 32GB
- **Type**: DDR4
- **Manufacturer**: Kingston
- **Part Number**: CBD26D4S9S8ME-8

To inspect detailed RAM information:
```bash
sudo dmidecode --type memory
```

### Storage

- **Internal SSD**: 1TB
- **server-storage**: 4TB (used for syncing media & photo content to/from Seafile - intended to be ephemeral)
- **server-cloud**: 8TB (Seafile sync server, server backups - intended to be a backup of Jenquist cloud & serve as a syncing source for other devices, including server-storage)
- **Jenquist Cloud**: ZFS RAID (raidz1) - primary archive storage

### Current File System Layout

```
/boot/efi
/dev/sda2      fuseblk      1.9T  1.8T   54G  98% /mnt/plex
/dev/sdb1      fuseblk      1.8T  120G  1.7T   7% /mnt/server-storage
/dev/sdb2      fuseblk      2.0T   39G  1.9T   2% /mnt/server-backup
```

---