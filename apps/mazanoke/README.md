# Mazanoke

A self-hosted local image optimizer that runs in your browser. Works offline, keeps your images private, and processes everything on-device.

## Description

Mazanoke is a simple, privacy-focused image optimizer that runs entirely in your browser. It never uploads your images to a server - all processing happens locally on your device. Perfect for optimizing images before uploading to your server or sharing with others.

## Features

- 🖼️ **Optimize Images in Your Browser**
  - Adjust image quality
  - Set target file size
  - Set max width/height
  - Paste images from clipboard
  - Convert between formats: JPG, PNG, WebP, ICO
  - Convert from: HEIC, AVIF, TIFF, GIF, SVG

- 🔒 **Privacy-Focused**
  - Works offline
  - On-device image processing
  - Removes EXIF data (location, date, etc.)
  - No tracking
  - Installable web app (PWA)

## Access

- **Local**: `http://192.168.86.47:8102`
- **HTTPS**: `https://mazanoke.server.unarmedpuppy.com`

## Setup

1. Start the service:
   ```bash
   docker compose up -d
   ```

2. Access at `http://192.168.86.47:8102` or via Traefik at `https://mazanoke.server.unarmedpuppy.com`

## Usage

1. Open the web interface
2. Drag and drop images or paste from clipboard
3. Adjust quality, size, or dimensions
4. Choose output format
5. Download optimized images

## Notes

- All processing happens in your browser - no server-side processing
- Works completely offline once loaded
- Can be installed as a Progressive Web App (PWA)
- Perfect for optimizing images before uploading to Immich, Plex, or other services

## References

- [GitHub Repository](https://github.com/civilblur/mazanoke)
- [Live Demo](https://mazanoke.com)

