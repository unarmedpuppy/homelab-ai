# Linux Home Server

- [Debian 12](https://www.debian.org/download) (Installed using [Etcher](https://etcher.balena.io/) to turn a USB drive into a bootable device)
- local ip: `192.168.86.47` (`hostname -I`)
- MAC address: 
- Power mode: Performance
- Power Saving Options: Screen blank: Never, Auto Suspend: Off
- Power Button Behavior: Nothing

`ssh unarmedpuppy@192.168.86.47 -p 4242`

- Prevent suspend

`sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target`

- size of directory

`du -sh server/apps/bedrock-viz/`

- Backup disk image

`sudo dd if=/dev/sda of=/mnt/server-storage/test-bk.img status=progress`

- disk usage visualization

`sudo apt install ncdu`

`sudo ncdu /`

`sudo du -sh * | sort -hr | head -n10`

# user list

`root` (root)

`unarmedpuppy` (added to sudoers file)

docker group id: 994 (`stat -c '%g' /var/run/docker.sock`)

# CPU

CPU Model: Intel(R) Celeron(R) G4900T CPU @ 2.90GHz Cores: 2 Memory: 64008 MB

upgrade: Intel Xeon E-2288G

# Motherboard

Base Board Information
        Manufacturer: Elo Touch Solutions
        Product Name: Coffeelake
        Version: EloPOS Pack
        Serial Number: To be filled by O.E.M.
        Asset Tag: Default string
        Features:
                Board is a hosting board
                Board is replaceable
        Location In Chassis: Default string
        Chassis Handle: 0x0003
        Type: Motherboard
        Contained Object Handles: 0

# RAM

# External Storage

- Internal SSD 1TB
- server-storage 4TB (used for syncing media & photo content to/from Seafile - inteneded to be ephemeral)
- server-cloud 8TB (Seafile sync server, server backups - intended to be a backup of Jenquist cloud & serve as a syncing source for other devices, including server-storage)

- Jenquist Archive (8TB Raid 1 - remote/not mounted to system) Source of truth for all files synced to this server


# Router configuration (Google Home)


# Docker

[Enable TCP](https://gist.github.com/styblope/dc55e0ad2a9848f2cc3307d4819d819f)

# Aliases

`cycle`

- Runs `~/server/docker-restart.sh`

- Which runs `~/server/docker-stop.sh` & `~/server/docker-start.sh`

`server`

- Runs `connect-server.sh`

`sync`

- Git pull, add, commit & push

# Workspace Automations

[Run on Save](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave) enabled in this repo. The settings are found in `.vscode/settings.json`. Everytime a file is saved in this workspace, the bash script `scripts/git-server-sync.sh` will execute. This will pull & add all changed files to a new commit and push to the remore, then ssh into the home server run the same git operations. This effectively syncs any changes done in this repo locally to the server automatically. (lol [git history](https://github.com/unarmedpuppy/home-server/commit/518a12e52a8be8a583721c27bf34d4b4331af8f0))


# Command Logs
<details>
<summary>Get System Info</summary>

### get local IP

`Hostname I`

### get MAC address

`sudo apt-get install net-tools`

`/sbin/ifconfig`

### Inspect Memory details

- Detailed information about your system's hardware, including RAM. To use it for RAM details
    
    `sudo dmidecode --type memory`

output: 
```
Type: DDR4
Manufacturer: Kingston
Serial Number: C182B4DC
Part Number: CBD26D4S9S8ME-8
```

</details>


<details>
<summary>Manage users & permissions</summary>

### Add primary user to sudoer file

- Switch to the Root User

    `su -`

- Install sudo (if it's not already installed)

    `apt-get install sudo`

- Add User to the sudo Group

    `adduser unarmedpuppy sudo`

- Verify the Addition

    `getent group sudo`

- Restart the Session

    `su - unarmedpuppy`

- Testing sudo Access

    `sudo whoami`
76.156.139.101/24

</details>

<details>
<summary>Configure SSH</summary>

### Enable & configure SSH

- Update System Packages

    `sudo apt-get update`

- Install SSH Server

    `sudo apt-get install openssh-server`

- Check SSH Service Status

    `sudo systemctl status ssh`

- Enable SSH on Boot

    `sudo systemctl enable ssh`

- Disable root login

    `sudo nano /etc/ssh/sshd_config`

    Disabled root login by finding the line `#PermitRootLogin prohibit-password` and changed it to `PermitRootLogin no`.
    Changde the port by finding the line `#Port 22` and changed it to `4242`

- Restart SSH Service

    `sudo systemctl restart ssh`

### Lock down access to SSH key only

- Create SSH Key Pair (server)

    `ssh-keygen -t rsa -b 4096` (passphrase same as unarmedpuppy pass)
    - (not actually used yet)

- Crease SSH key pair (client)

    `ssh-keygen -t rsa -b 4096`
    -(/c/Users/micro/.ssh/id_rsa)

- Copy the Public Key to the Server

    `ssh-copy-id -i /c/Users/micro/.ssh/id_rsa.pub -o 'Port=4242' unarmedpuppy@192.168.86.47`

- Now able to login with key

    `ssh -o 'Port=4242' 'unarmedpuppy@192.168.86.47'`

- Disable Password Authentication on the Server

    `sudo nano /etc/ssh/sshd_config`

    ```
    PasswordAuthentication no
    ChallengeResponseAuthentication no
    UsePAM no
    ```

- Reload SSH Service

    `sudo systemctl reload sshd`


</details>

<details>

`sudo apt install parted`

<summary>Configure Docker</summary>

### Install Docker & Docker-compose

- Install Required Packages
    
    `sudo apt-get install apt-transport-https ca-certificates curl gnupg2 software-properties-common`

- Add Docker’s Official GPG Key

    `curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -`

- Set Up the Docker Repository

    `sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"`

- Update the apt Package Index

    `sudo apt-get update`

- Install Docker CE (Community Edition)

    `sudo apt-get install docker-ce docker-ce-cli containerd.io`

- Verify that Docker is Installed Successfully

    `sudo systemctl status docker`
    `sudo docker run hello-world`

- Add Your User to the Docker Group

    `sudo usermod -aG docker unarmedpuppy`

    (Log out and log back in so that your group membership is re-evaluated.)

- Configure Docker to Start on Boot

    `sudo systemctl enable docker`

- Download the [Current Stable Release](https://github.com/docker/compose/tags) of Docker Compose

    `sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.4/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose`

- Apply Executable Permissions to the Binary

    `sudo chmod +x /usr/local/bin/docker-compose`

- Verify Installation

    `docker-compose --version`

- Create Docker Network

    `docker network create my-network`  - general use
    `docker network create monitoring_default` - grafana services

    ```
        networks:
      - my-network

networks:
  my-network:
    driver: bridge
    external: true
    ```

- inspect network

  `docker network inspect my-network`
```
"IPAM": {
            "Driver": "default",
            "Options": {},
            "Config": [
                {
                    "Subnet": "192.168.160.0/20",
                    "Gateway": "192.168.160.1"
                }
            ]
        },
```

</details>

<details>
<summary>Configure Backups & Storage</summary>

### Daily Backups

- Install [rsnapshot](https://github.com/rsnapshot/rsnapshot)

    `sudo apt-get install rsnapshot`

- Configure rsnapshot

    `sudo nano /etc/rsnapshot.conf`

    Backing up to external drive, /mnt/archive

- Testing rsnapshot

    `sudo rsnapshot configtest`

- Running rsnapshot

    `sudo rsnapshot alpha`

- Automate rsnapshot Backups

    `sudo crontab -e`

    ```
    0 */4 * * *     /usr/bin/rsnapshot alpha
    00 00 * * *     /usr/bin/rsnapshot beta
    00 23 * * 6     /usr/bin/rsnapshot gamma
    00 22 1 * *     /usr/bin/rsnapshot delta
    ```

     There will be six `alpha` snapshots taken each day, a `beta` rsnapshot at midnight, a `gamma` snapshot on Saturdays at 11:00pm and a `delta` rsnapshot at 10pm on the first day of each month.

### Persist mounted external hard drives

- Identify the Drive

    `sudo blkid`
    
    ```
    /dev/sdb2: LABEL="PLEX" BLOCK_SIZE="512" UUID="264A52274A51F3D1" TYPE="ntfs" PARTLABEL="Basic data partition" PARTUUID="52305598-83f9-4b21-9ef2-caed906b4391"                          
    
    /dev/sdc2: LABEL="server-backup" BLOCK_SIZE="512" UUID="CC6AD5676AD54EB8" TYPE="ntfs" PARTLABEL="Basic data partition" PARTUUID="1d989182-929a-4703-a291-75d18fecc25d"                               
    
    /dev/sdc1: LABEL="server-storage" BLOCK_SIZE="512" UUID="0812C2CF12C2C0C4" TYPE="ntfs" PARTLABEL="Basic data partition" PARTUUID="80f6f63e-d935-4851-9549-59a101365094"
    ```

- Create a Mount Point

    `sudo mkdir /mnt/server-storage`
    `sudo mkdir /mnt/server-cloud`

- Edit /etc/fstab

    `sudo nano /etc/fstab`

- Add the Mount Entry

    `UUID=0812C2CF12C2C0C4  /mnt/server-storage  ntfs  defaults,nofail  0  0`
    `UUID=BA30D6F430D6B69B  /mnt/server-cloud  ntfs  defaults,nofail  0  0`


- Test the Mount

    `sudo mount -a`

</details>

<details>
<summary>Configure Home Assistant</summary>

### Home Assistant

- `docker-compose.yml`

</details>

<details>
<summary>Configure Plex</summary>

### Plex

- [Get claim code](https://www.plex.tv/claim/)

- `docker-compose.yml`


 back up fo docker file that worked with traefik, but not in app
```
version: '3.3'

services:
    pms-docker:
        image: plexinc/pms-docker
        container_name: plex
        #network_mode: host
        environment:
            - TZ=America/Chicago
            - PLEX_CLAIM=claim-A7EhBpo7PRhsx7sDKMYh
        volumes:
            - ./config:/config
            - ./transcode:/transcode
            - /mnt/plex:/data
        restart: unless-stopped
        ports:
            - '32400:32400'
        networks:
            - my-network
        labels:
            - "traefik.enable=true"
            - "traefik.http.routers.plex.rule=Host(`plex.server.unarmedpuppy.com`)"
            - "traefik.http.routers.plex.entrypoints=websecure"
            - "traefik.http.routers.plex.tls.certresolver=myresolver"
            - "traefik.http.routers.plex.service=plex"
            - "traefik.http.services.plex.loadbalancer.server.port=32400"
            - "traefik.http.middlewares.plex-https-redirect.redirectscheme.scheme=https"
            - "traefik.http.routers.plex.middlewares=plex-https-redirect"

networks:
  my-network:
    external: true
    driver: bridge
```

</details>

<details>
<summary>Configure Pihole</summary>

### Pihole

- `docker-compose.yml`

</details>


<details>
<summary>Configure Nextcloud</summary>

### Nextcloud

- `docker-compose.yml`

- reverse proxy (not currently working)
https://github.com/nextcloud/all-in-one/blob/main/reverse-proxy.md

</details>

<details>
<summary>Configure Cloudflare DDNS</summary>

### Cloudflare DDNS

- `docker-compose.yml`

</details>

<details>
<summary>Configure Grafana</summary>

### Grafana

- `docker-compose.yml`

                                                                                                    
Spawning up this docker stack will provide you
with:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
- A containerized Grafana web instance runnning on the default port TCP/3000                                                                                                                                                                                                        
- A containerized Telegraf instance that fetches data points from your docker host server                                                                                                                                                                                             
- A containerized InfluxDB instance for storing Telegraf data, which can be defined in Grafana as datasource (just specify `http://influxdb:8086`). Default database is `telegraf`. Default username is `telegrafuser`. Default password is `MyStrongTelegrafPassword`. Defaults can >
- A containerized Promtail instance that can fetch various log files (bind mounted into the promtail container from your docker host server) and send them into the Loki container (e.g. /var/log/auth.log or your Traefik reverse proxy logs)                                        
- A containerized Loki instance for storing Promtail log data, which can be defined in Grafana as datasource (just specify `http://loki:3100`). No authentication enabled per default.                                                                                                                                                                                                                                                                                                                                                                                      
Finally, after configuring InfluxDB and Loki as datasources on Grafana, you can just import the provided `Grafana_Dashboard_Template.json` dashboard template YAML file in Grafana by browsing http://127.0.0.1:3000/dashboard/import. Your dashboard will look like the following:                                                                                                                                                                                                                                                                                         
<img src="https://blog.lrvt.de/content/images/2022/11/image-4-1.png">                       

</details>

<details>
<summary>Configure UFW</summary>

### UFW

- install UFW

    `sudo apt install ufw`

- allow SSH

    `sudo ufw allow 4242/tcp`

- enable ufw

    `sudo ufw enable`

- Set Default Policies

    `sudo ufw default deny incoming`
    `sudo ufw default allow outgoing`

- Allow specifc services

    ~`sudo ufw allow 8123/tcp` (homeassistant)~ `sudo ufw delete allow 8123/tcp`
    `sudo ufw allow 32400/tcp` (plex)
    `sudo ufw allow 19132/udp` (minecraft)
    `sudo ufw allow 28015/udp` (rust)
    `sudo ufw allow 28015` (rust)
    `sudo ufw allow 28016` (rust)
    `sudo ufw allow 8080` (rust)
    `sudo ufw allow 53/tcp` (adguard)
    `sudo ufw allow 53/udp` (adguard)
    ~`sudo ufw allow from 172.17.0.0/16 to any port 2375 proto tcp` (docker subnet connect to docker socket over tcp)~


    `sudo ufw default deny incoming`
    `sudo ufw default allow outgoing`

    **IMPORTANT: for external traffic (game servers) dont forget to setup the port mapping in google router**

- Check Status and Rules

    `sudo ufw status verbose`

</details>



<details>
<summary>Configure Reverse Proxy</summary>

### Caddy

- *DEPRECATED (uninstalled/down)*

- Update Caddy file to match cloudflare DDNS

- Update Port Forwarding on google home router
Forward TCP port 80 (HTTP) and 443 (HTTPS) to the internal IP address of the server running Caddy. This ensures that Caddy can handle incoming requests and manage SSL certificates through Let's Encrypt.


### Traefik

- Utilizing docker network prviously set up & running named `my-network`

- Create a Traefik Configuration Directory

    `mkdir -p ~/server/apps/traefik/{config,logs}`

- Create the Traefik Configuration File (traefik.yml):

    `touch ~/server/apps/traefik/config/traefik.yml`

    ```
    api:
      dashboard: true
      entryPoints:
        web:
          address: ":80"
        websecure:
          address: ":443"

      providers:
        docker:
          endpoint: "unix:///var/run/docker.sock"
          exposedByDefault: false
          network: my-network

    certificatesResolvers:
      myresolver:
        acme:
          email: traefik@jenquist.com
          storage: acme.json
          httpChallenge:
            # Using httpChallenge means we're going to solve a challenge using port 80
            entryPoint: web
          # dnsChallenge:
            # provider: cloudflare
            # Delay before checking DNS propagation
            # delayBeforeCheck: 0
    
    accessLog:
      filePath: "~/server/apps/traefik/logs/access.log"
      format: json

    metrics:
      prometheus: {}

    tracing:
      jaeger:
        samplingType: const
        samplingParam: 1.0
    ```

- Create an Empty acme.json File for Storing Certificates

    `touch ~/server/apps/traefik/config/acme.json && chmod 600 ~/server/apps/traefik/config/acme.json`

-  Docker Compose File for Traefik

    ```
version: '3.7'

services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    restart: unless-stopped
    environment:
      - TZ=America/Chicago
      - CF_DNS_API_TOKEN=redacted
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./config/traefik.yml:/traefik.yml:ro"
      - "./config/acme.json:/acme.json"
      - "./logs:/var/log/traefik"
    networks:
      - my-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`traefik.server.unarmedpuppy.com`)"
      - "traefik.http.routers.api.service=api@internal"
      - "traefik.http.routers.api.middlewares=auth"
      - "traefik.http.middlewares.auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=myresolver"

networks:
  my-network:
    external: true
    ```

- generate new credentials using the `htpasswd` tool (part of the Apache HTTP Server package)

  `sudo apt-get install apache2-utils`

- generate user + password

  `htpasswd -nb admin example`

- example enable traefik on container

```
labels:
      - "traefik.enable=true"
      - "traefik.http.routers.libreddit.rule=Host(`libreddit.server.unarmedpuppy.com`)"
      - "traefik.http.routers.libreddit.entrypoints=web"
      #- traefik.http.routers.libreddit.middlewares=local-ipwhitelist@file,basic-auth@file      
    networks:
      - my-network

networks:
  my-network:
    external: true


    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.homeassistant.rule=Host(`homeassistant.server.unarmedpuppy.com`)"
      - "traefik.http.routers.homeassistant.entrypoints=websecure"
      - "traefik.http.routers.homeassistant.tls.certresolver=myresolver"
    networks:
      - my-network

networks:
  my-network:
    external: true
```

### Bypass basic auth for LAN

```
    labels:
      - "traefik.http.routers.whoami2.rule=Host(`server.unarmedpuppy.com`) && !ClientIP(`192.168.1.1/254`)"
      - "traefik.http.routers.whoami2.priority=99"
      - "traefik.http.routers.whoami2.middlewares=secured2"
      - "traefik.http.routers.whoami.rule=Host(`whoami.localhost`)"
      - "traefik.http.routers.whoami.priority=100"
      - "traefik.http.routers.whoami.middlewares=secured"
      - "traefik.http.middlewares.secured.chain.middlewares=auth"
      - "traefik.http.middlewares.secured2.chain.middlewares="
      - "traefik.http.middlewares.auth.basicauth.users=test1:$$apr1$$H6uskkkW$$IgXLP6ewTrSuBkTrqE8wj/"
      #- "traefik.http.middlewares.known-ips.ipwhitelist.sourceRange=192.168.1.7,127.0.0.1/32"
```

```
---
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  namespace: example-namespace
  name: example-ingressroute
  labels:
    app: example
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`example.com`)
      kind: Rule
      priority: 99
      services:
        - name: example-service
          port: 3000
    - match: Host(`server.unarmedpuppy.com`) && ! ClientIP(`192.168.1.1/254`)
      kind: Rule
      priority: 100
      services:
        - name: example-service
          port: 3000
      middlewares:
        - name: basicauth-middleware
          namespace: example-namespace
  tls:
    secretName: example-cert

```

      - "traefik.http.routers.whoami2.rule=Host(`server.unarmedpuppy.com`) && !ClientIP(`192.168.1.1/254`)"
      - "traefik.http.routers.whoami2.priority=99"
      - "traefik.http.routers.whoami2.middlewares=secured2"

      - "traefik.http.routers.whoami.rule=Host(`whoami.localhost`)"
      - "traefik.http.routers.whoami.priority=100"
      - "traefik.http.routers.whoami.middlewares=secured"

      - "traefik.http.middlewares.secured.chain.middlewares=auth"
      - "traefik.http.middlewares.secured2.chain.middlewares="

      - "traefik.http.middlewares.auth.basicauth.users=test1:$$apr1$$H6uskkkW$$IgXLP6ewTrSuBkTrqE8wj/"
```
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.homepage.rule=Host(`server.unarmedpuppy.com`) && ClientIP(`192.168.1.0/24`, `76.156.139.101/24`)"
      - "traefik.http.routers.homepage.priority=99"
      - "traefik.http.routers.homepage.entrypoints=websecure"
      - "traefik.http.routers.homepage.middlewares=bypass"
      - "traefik.http.routers.homepage.tls.certresolver=myresolver"
      - "traefik.http.routers.homepage2.rule=Host(`server.unarmedpuppy.com`)"
      - "traefik.http.routers.homepage2.priority=100"
      - "traefik.http.routers.homepage2.entrypoints=websecure"
      - "traefik.http.routers.homepage2.middlewares=do-auth"
      - "traefik.http.routers.homepage2.tls.certresolver=myresolver"
      - "traefik.http.middlewares.do-auth.chain.middlewares=homepage-auth"
      - "traefik.http.middlewares.bypass.chain.middlewares="
      - "traefik.http.middlewares.homepage-auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
      - "traefik.http.middlewares.homepage-auth.basicauth.realm=homepage"
```

</details>

<details>
<summary>Configure Reverse Proxy</summary>
### Libreddit

JS snippet to snag all subs

```
var items = ''
document.querySelectorAll('[role="menuitem"]').forEach(function (el){
items = items + el.ariaLabel + "+"
});
```
</details>


<details>
<summary>Game Servers</summary>

### Rust

[server banner (1024 x 512) ](https://i.imgur.com/FIXxuRI.jpg)

[rcon](http://192.168.86.47:8080/#/192.168.86.47:28016/playerlist)



TODO:

local DNS (pihole - do this at night)

### Minecraft

- Copy world from PC to server

  `scp -P  4242 -r ~/Desktop/server/minecraft/gumberlund unarmedpuppy@192.168.86.47:~/server/apps/minecraft/gumberlund`


scp -P  4242 -r ./static unarmedpuppy@192.168.86.47:~/server/apps/bedrock-viz/repo/build/static-upload

- Server commands

  `docker exec minecraft-bedrock-1 send-command op unarmedpupy`

  unarmedpupy, xuid: 2535454866260420

### Bedrock-viz 

https://github.com/bedrock-viz/bedrock-viz?tab=readme-ov-file

- Generate static files on PC

  `bedrock-viz.exe --db C:\Users\micro\Desktop\server\minecraft\gumberlund --out ./map --html-most` (not working for my map)


- Copy generated map from PC to server

  `scp -P  4242 -r ~/Desktop/server/minecraft/map unarmedpuppy@192.168.86.47:~/server/apps/bedrock-viz/map`

```
version: '3'

services:
  bedrock-viz-http:
    image: nginx
    container_name: bedrock-viz-http
    volumes:
      - /map:/usr/share/nginx/html:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.bedrock-viz-http.rule=Host(`minecraft.server.unarmedpuppy.com`)"
      - "traefik.http.routers.bedrock-viz-http.entrypoints=web"
      - "traefik.http.services.bedrock-viz-http.loadbalancer.server.port=80"
    networks:
      - my-network

networks:
  my-network:
    external: true
```

- [Try building from source](https://github.com/bedrock-viz/bedrock-viz/blob/master/docs/BUILD.md#ubuntu-tested--supported-on-ubuntu-2004-2104)

```

cmake: sudo apt install cmake

libpng and zlib: sudo apt install libpng++-dev zlib1g-dev

boost sudo apt install libboost-program-options-dev

sudo apt install -y build-essential


```

`~/server/apps/bedrock-viz/repo/build$ ./bedrock-viz --db ~/server/apps/minecraft/backup-gumberlund --cfg ~/server/apps/bedrock-viz/repo/data/bedrock_viz.cfg --xml ~/server/apps/bedrock-viz/repo/data/bedrock_viz.xml --html-all`

</details>

<details>
<summary>Home Page</summary>

- [Docs](https://github.com/gethomepage/homepage?ref=noted.lol)

```
version: "3.3"
services:
  homepage:
    image: ghcr.io/gethomepage/homepage:latest
    container_name: homepage
    ports:
      - 3000:3000
    volumes:
      - ~/server/apps/homepage/config:/app/config # Make sure your local config directory exists
      - /var/run/docker.sock:/var/run/docker.sock:ro # optional, for docker integrations
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.homepage.rule=Host(`server.unarmedpuppy.com`)"
      - "traefik.http.routers.homepage.entrypoints=websecure"
      - "traefik.http.routers.homepage.tls.certresolver=myresolver"
      - "traefik.http.routers.homepage.middlewares=homepage-auth"
      - "traefik.http.middlewares.homepage-auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
      - "traefik.http.middlewares.homepage-auth.basicauth.realm=homepage"
    restart: unless-stopped
    networks:
      - my-network

networks:
  my-network:
    external: true
```

- add labels to all containers:

```
      - "homepage.group=Game Servers"
      - "homepage.name=Bedrock Viz"
      #- homepage.icon=emby.png
      - "homepage.href=http://minecraft.server.unarmedpuppy.com"
      - "homepage.description=Minecraft server map"
```
</details>


labels:
      - "homepage.group=Game Servers"
      - "homepage.name=Rust Server"
      #- homepage.icon=emby.png
      - "homepage.href=http://rust.server.unarmedpuppy.com"
      - "homepage.description=Rust server, UDP traffic on port 28015"
    networks:
      - my-network

networks:
  my-network:
    external: true



/boot/efi
/dev/sda2      fuseblk      1.9T  1.8T   54G  98% /mnt/plex
/dev/sdb1      fuseblk      1.8T  120G  1.7T   7% /mnt/server-storage
/dev/sdb2      fuseblk      2.0T   39G  1.9T   2% /mnt/server-backup


### Adguard

```
Admin Web Interface
Listen interface
All interfaces
Port
80
Your AdGuard Home admin web interface will be available on the following addresses:
http://127.0.0.1
http://192.168.160.9
DNS server
Listen interface
All interfaces
Port
53
You will need to configure your devices or router to use the DNS server on the following addresses:
127.0.0.1
192.168.160.9
Static IP Address
AdGuard Home is a server so it needs a static IP address to function properly. Otherwise, at some point, your router may assign a different IP address to this device.

Configure your devices
To start using AdGuard Home, you need to configure your devices to use it.
AdGuard Home DNS server is listening on the following addresses:
127.0.0.1
192.168.160.9
Router
Windows
macOS
Android
iOS
DNS Privacy
Router
This setup automatically covers all devices connected to your home router, no need to configure each of them manually.

Open the preferences for your router. Usually, you can access it from your browser via a URL, such as http://192.168.0.1/ or http://192.168.1.1/. You may be prompted to enter a password. If you don't remember it, you can often reset the password by pressing a button on the router itself, but be aware that if this procedure is chosen, you will probably lose the entire router configuration. If your router requires an app to set it up, please install the app on your phone or PC and use it to access the router’s settings.
Find the DHCP/DNS settings. Look for the DNS letters next to a field which allows two or three sets of numbers, each broken into four groups of one to three digits.
Enter your AdGuard Home server addresses there.
On some router types, a custom DNS server cannot be set up. In that case, setting up AdGuard Home as a DHCP server may help. Otherwise, you should check the router manual on how to customize DNS servers on your specific router model.
```


# Seafile
 installed seafile cli

 mkdir ~/seafile-client

 seaf-cli init -d ~/seafile-client

 seaf-cli start