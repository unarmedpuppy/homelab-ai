# LLM PC Hardware Specifications

**⚠️ Important**: This is a **separate computer** from the home server. This PC is dedicated to running local AI/LLM models and is connected to the home server network.

## Overview

This PC hosts the local AI inference services that are accessed via the `local-ai-app` proxy service running on the home server. The models run in Docker containers on this Windows machine and are accessed remotely.

**Connection Details**:
- **IP Address**: `192.168.86.100` (configured in `apps/local-ai-app/docker-compose.yml`)
- **Manager Port**: `8000`
- **Operating System**: Windows
- **Purpose**: Local LLM inference (Llama 3.1 8B, Qwen 2.5 14B AWQ, DeepSeek Coder, Qwen Image Edit)

## Chassis

- **Model**: LIAN LI PC-O11 Dynamic White
- **Type**: ATX Mid Tower Gaming Computer Case
- **Features**: Tempered Glass on Front and Left Sides
- **Form Factor**: SECC ATX Mid Tower

## Motherboard

- **Model**: ASUS Prime X570-Pro
- **Socket**: AMD AM4 (Ryzen 3 compatible)
- **Form Factor**: ATX
- **Features**:
  - PCIe Gen4 support
  - Dual M.2 slots
  - HDMI output
  - SATA 6Gb/s
  - USB 3.2 Gen 2

## CPU

*To be documented* - Please add CPU model, cores, threads, and specifications when available.

## RAM

- **Total Capacity**: 32GB
- **Configuration**: 2 kits of 16GB (2 x 8GB modules each)
- **Model**: CORSAIR Vengeance RGB Pro
- **Type**: DDR4
- **Speed**: 3200 MHz (PC4 25600)
- **Part Number**: CMW16GX4M2C3200C16W
- **Configuration**: 4 x 8GB modules (32GB total)
- **Pin Count**: 288-pin

## Storage

- **Primary SSD**: SAMSUNG 970 EVO PLUS
- **Capacity**: 1TB
- **Form Factor**: M.2 2280
- **Interface**: PCIe Gen 3.0 x4, NVMe 1.3
- **Technology**: V-NAND 3-bit MLC
- **Model Number**: MZ-V7S1T0B/AM

## Graphics Card

- **Model**: NVIDIA GeForce RTX 3090
- **Edition**: Founders Edition
- **VRAM**: 24GB GDDR6X
- **Purpose**: GPU acceleration for LLM inference

## Power Supply

- **Model**: CORSAIR TX-M Series TX750M
- **Wattage**: 750W
- **Efficiency**: 80 PLUS Gold Certified
- **Form Factor**: ATX12V v2.4 / EPS 2.92
- **Modularity**: Semi-Modular
- **PFC**: Active PFC
- **Part Number**: CP-9020131-NA

## Network Configuration

The PC is connected to the local network and accessible from the home server:

```yaml
# From apps/local-ai-app/docker-compose.yml
environment:
  - WINDOWS_AI_HOST=192.168.86.100
  - WINDOWS_AI_PORT=8000
```

**Firewall Configuration**:
- Port 8000 must be open for inbound connections from the home server IP (`192.168.86.47`)
- Windows Firewall rule: "LLM Manager 8000"

## Software Stack

### Operating System
- **OS**: Windows
- **Docker**: Docker Desktop with GPU support enabled

### Services Running
- **LLM Manager Service**: Port 8000
- **Model Containers**: Various (Llama 3.1 8B, Qwen 2.5 14B AWQ, DeepSeek Coder, Qwen Image Edit)
- **Auto-loading/Unloading**: Models start on-demand and stop after idle timeout (10 minutes)

### Setup Location
- **Repository Path**: `local-ai/` directory in home-server repository
- **Setup Script**: `local-ai/setup.sh`

## Performance Notes

- **GPU**: RTX 3090 provides 24GB VRAM for large model inference
- **RAM**: 32GB system RAM supports model loading and system operations
- **Storage**: NVMe SSD provides fast model loading times

## Maintenance

### Checking System Information

**Windows System Info**:
```powershell
# System information
systeminfo

# GPU information
nvidia-smi

# Memory information
Get-CimInstance Win32_PhysicalMemory | Format-Table
```

**Docker Container Status**:
```bash
# From the local-ai directory
docker ps
docker logs <container-name>
```

### Monitoring

- Monitor GPU usage: `nvidia-smi`
- Monitor Docker containers: `docker stats`
- Check manager service: `http://192.168.86.100:8000/health`

## Related Documentation

- **Local AI App**: `apps/local-ai-app/README.md` - Proxy service documentation
- **Setup Instructions**: `local-ai/setup.sh` - Initial setup script
- **Home Server Hardware**: `apps/wiki/wiki-pages/hardware-specifications.md` - Home server specs

## Notes

- This PC is physically separate from the home server
- Models are loaded on-demand to conserve GPU memory
- The RTX 3090's 24GB VRAM allows for running larger models
- All model inference happens on this PC; the home server only acts as a proxy

---

**Last Updated**: [Date to be added]  
**Status**: Active - Running local AI inference services
