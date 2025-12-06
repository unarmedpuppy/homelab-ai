# Security Configuration

### System Security

#### Malware Check (Lynis)
```bash
sudo apt install lynis
sudo lynis audit system
```

#### System Logging

**View Logs**:
```bash
journalctl
```

**Limit Journal Size**:
```bash
sudo journalctl --vacuum-size=100M
```

---