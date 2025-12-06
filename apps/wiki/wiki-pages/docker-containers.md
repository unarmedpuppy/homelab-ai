# Docker & Containers

### Docker Installation

**1. Install Required Packages**:
```bash
sudo apt-get install apt-transport-https ca-certificates curl gnupg2 software-properties-common
```

**2. Add Docker's Official GPG Key**:
```bash
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
```

**Modern method (recommended)**:
```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo tee /etc/apt/keyrings/docker.gpg > /dev/null
```

**3. Set Up Docker Repository**:
```bash
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
```

Modern method:
```bash
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

**4. Install Docker CE**:
```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

**5. Verify Installation**:
```bash
sudo systemctl status docker
sudo docker run hello-world
```

**6. Add User to Docker Group**:
```bash
sudo usermod -aG docker unarmedpuppy
```
Log out and log back in for group membership to take effect.

**7. Enable Docker on Boot**:
```bash
sudo systemctl enable docker
```

**8. Install Docker Compose**:
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.4/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

**9. Enable Docker TCP** (optional):
See: [Docker TCP Configuration Guide](https://gist.github.com/styblope/dc55e0ad2a9848f2cc3307d4819d819f)

### Docker Networks

**Create Networks**:
```bash
docker network create my-network          # General use
docker network create monitoring_default  # Grafana services
```

**Network Configuration Example**:
```yaml
networks:
  - my-network

networks:
  my-network:
    driver: bridge
    external: true
```

**Inspect Network**:
```bash
docker network inspect my-network
```

Expected subnet: `192.168.160.0/20`, Gateway: `192.168.160.1`

### Docker Maintenance

**Prune Old Images**:
```bash
docker rmi $(docker images -a -q)
docker system prune -a -f
```

**View Reclaimable Space**:
```bash
docker system df
```

**Prune Unused Volumes**:
```bash
docker volume prune
```

**Cron Job for Weekly Pruning**:
```
0 5 * * 1 docker system prune -a -f
```

### NVIDIA GPU Support (Optional)

**1. Add NVIDIA Container Toolkit Repository**:
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null
```

**2. Install NVIDIA Container Toolkit**:
```bash
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

**3. Install NVIDIA Drivers**:
```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository contrib
sudo add-apt-repository non-free
sudo add-apt-repository non-free-firmware
sudo apt update
sudo apt install -y nvidia-driver nvidia-smi firmware-misc-nonfree
```

**4. Test GPU Access**:
```bash
docker run --rm --gpus all nvidia/cuda:12.2.0-runtime-ubuntu22.04 nvidia-smi
```

---