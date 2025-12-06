# System Overview

### Operating System

- **OS**: Debian 12 (Bookworm)
- **Installation Method**: Created bootable USB using [Etcher](https://etcher.balena.io/)

### Power Management

- **Power Mode**: Performance
- **Screen Blank**: Never
- **Auto Suspend**: Off
- **Power Button Behavior**: Nothing (disabled)

### Users

- **root** - Root user
- **unarmedpuppy** - Primary user (added to sudoers file)
- **Docker Group ID**: 994 (`stat -c '%g' /var/run/docker.sock`)

### Prevent System Suspend

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

---