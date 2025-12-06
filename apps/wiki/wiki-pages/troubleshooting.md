# Troubleshooting

### Common Issues

1. **Services not accessible**: Check Traefik labels and network configuration
2. **Port conflicts**: Use `netstat -tulpn | grep <port>` to check port usage
3. **File permissions**: Ensure directories are owned by `1000:1000` (PUID/PGID)
4. **Docker network issues**: Verify `my-network` exists and services are connected
5. **ZFS mount issues**: Run `sudo zfs load-key -a && sudo zfs mount -a`

### Log Locations

- **System logs**: `journalctl`
- **Traefik logs**: `~/server/apps/traefik/logs/`
- **Docker logs**: `docker logs <container_name>`

---

**Last Updated**: See git history for latest changes
**Server**: 192.168.86.47 (unarmedpuppy@home-server)