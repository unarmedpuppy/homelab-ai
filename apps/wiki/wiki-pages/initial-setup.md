# Initial Setup

### User Management

#### Add User to Sudoers

```bash
# Switch to root
su -

# Install sudo (if not installed)
apt-get install sudo

# Add user to sudo group
adduser unarmedpuppy sudo

# Verify
getent group sudo

# Switch back to user
su - unarmedpuppy

# Test sudo access
sudo whoami
```

### SSH Configuration

#### Enable and Configure SSH

```bash
# Update packages
sudo apt-get update

# Install SSH server
sudo apt-get install openssh-server

# Check status
sudo systemctl status ssh

# Enable SSH on boot
sudo systemctl enable ssh
```

#### Secure SSH Configuration

Edit `/etc/ssh/sshd_config`:

```bash
sudo nano /etc/ssh/sshd_config
```

**Settings**:
- `PermitRootLogin no` - Disable root login
- `Port 4242` - Change from default port 22

```bash
# Restart SSH service
sudo systemctl restart ssh
```

#### Lock Down SSH to Key-Only Access

**1. Create SSH Key Pair (Server)**:
```bash
ssh-keygen -t rsa -b 4096
# Passphrase: same as unarmedpuppy password
# (Note: not actually used yet)
```

**2. Create SSH Key Pair (Client)**:
```bash
ssh-keygen -t rsa -b 4096
# Location: /c/Users/micro/.ssh/id_rsa (Windows example)
```

**3. Copy Public Key to Server**:
```bash
ssh-copy-id -i /c/Users/micro/.ssh/id_rsa.pub -o 'Port=4242' unarmedpuppy@192.168.86.47
```

**4. Test Key-Based Login**:
```bash
ssh -o 'Port=4242' 'unarmedpuppy@192.168.86.47'
```

**5. Disable Password Authentication**:

Edit `/etc/ssh/sshd_config`:
```
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM no
```

**6. Reload SSH Service**:
```bash
sudo systemctl reload sshd
```

**Additional Security**:
- [Securing SSH with FIDO2](https://developers.yubico.com/SSH/Securing_SSH_with_FIDO2.html) - YubiKey authentication

---