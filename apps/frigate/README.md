# Frigate NVR

AI-powered NVR (Network Video Recorder) with real-time object detection.

## Access

- **URL**: https://frigate.server.unarmedpuppy.com
- **Ports**:
  - `8971` - Web UI (authenticated)
  - `8554` - RTSP restreaming
  - `8555` - WebRTC (TCP/UDP)
- **Status**: Configured (awaiting cameras)

## Configuration

### Adding Cameras

Edit `config/config.yml` and add camera configurations:

```yaml
cameras:
  front_door:
    ffmpeg:
      inputs:
        - path: rtsp://user:password@camera-ip:554/stream
          roles:
            - detect
            - record
    detect:
      width: 1280
      height: 720
      fps: 5
```

### Hardware Acceleration

For Intel GPUs (QSV), add to docker-compose.yml:
```yaml
devices:
  - /dev/dri/renderD128:/dev/dri/renderD128
```

For Coral TPU accelerators:
```yaml
devices:
  - /dev/bus/usb:/dev/bus/usb
```

And update `config/config.yml`:
```yaml
detectors:
  coral:
    type: edgetpu
    device: usb
```

### Shared Memory

Default `shm_size: 512mb` supports ~4 cameras at 720p. Increase if needed:
- 2 cameras @ 720p: 128mb
- 4 cameras @ 1080p: 256mb
- 8+ cameras: 512mb+

## Storage

Recordings and snapshots are stored in `./storage/`. Consider mounting a dedicated drive for larger deployments.

## References

- [Official Documentation](https://docs.frigate.video/)
- [GitHub Repository](https://github.com/blakeblackshear/frigate)
- [Camera Setup Guide](https://docs.frigate.video/configuration/cameras)
- [Hardware Acceleration](https://docs.frigate.video/configuration/hardware_acceleration)
