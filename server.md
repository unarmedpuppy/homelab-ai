# Linux Server

- [Debian 12](https://www.debian.org/download) (Installed using [Etcher](https://etcher.balena.io/) to turn a USB drive into a bootable device)
- local ip: `192.168.86.47` (`hostname -I`)
- Power mode: Performance
- Power Saving Options: Screen blank: Never, Auto Suspend: Off
- Power Button Behavior: Nothing

`ssh unarmedpuppy@192.168.86.47 -p 4242`

# user list

`root` (root)

`unarmedpuppy` (added to sudoers file)

docker group id: 994 (`stat -c '%g' /var/run/docker.sock`)

# External Storage

- PLEX 2TB (media contenxt)
- server-storage 2TB (misc)
- server-backup 2TB (backup target)
- TBD Raid 5 array

# Command Logs

### get local IP

`Hostname I`

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

### Daily Backups

- Install [rsnapshot](https://github.com/rsnapshot/rsnapshot)

    `sudo apt-get install rsnapshot`

- Configure rsnapshot

    `sudo nano /etc/rsnapshot.conf`

    Backing up to external drive, /mnt/server-backup 

- Testing rsnapshot

    `sudo rsnapshot configtest`

- Running rsnapshot

    `sudo rsnapshot alpha`

- Automate rsnapshot Backups

    `sudo crontab -e`

    ```
    0 */4 * * *     /usr/local/bin/rsnapshot alpha
    00 00 * * *     /usr/local/bin/rsnapshot beta
    00 23 * * 6     /usr/local/bin/rsnapshot gamma
    00 22 1 * *     /usr/local/bin/rsnapshot delta
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

    `sudo mkdir /mnt/plex`
    `sudo mkdir /mnt/server-backup`
    `sudo mkdir /mnt/server-storage`

- Edit /etc/fstab

    `sudo nano /etc/fstab`

- Add the Mount Entry

    `UUID=264A52274A51F3D1  /mnt/plex  ntfs  defaults  0  2`
    `UUID=CC6AD5676AD54EB8  /mnt/server-backup  ntfs  defaults  0  2`
    `UUID=0812C2CF12C2C0C4  /mnt/server-storage  ntfs  defaults  0  2`

- Test the Mount

    `sudo mount -a`

### Home Assistant

- `docker-compose.yml`


### Pi Hole

- `docker-compose.yml`

### Plex

- [Get claim code](https://www.plex.tv/claim/)

- `docker-compose.yml`

### Grafana
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
Spawning up this docker stack will provide you
with:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
- A containerized Grafana web instance runnning on the default port TCP/3000                                                                                                                                                                                                        
- A containerized Telegraf instance that fetches data points from your docker host server                                                                                                                                                                                             
- A containerized InfluxDB instance for storing Telegraf data, which can be defined in Grafana as datasource (just specify `http://influxdb:8086`). Default database is `telegraf`. Default username is `telegrafuser`. Default password is `MyStrongTelegrafPassword`. Defaults can >
- A containerized Promtail instance that can fetch various log files (bind mounted into the promtail container from your docker host server) and send them into the Loki container (e.g. /var/log/auth.log or your Traefik reverse proxy logs)                                        
- A containerized Loki instance for storing Promtail log data, which can be defined in Grafana as datasource (just specify `http://loki:3100`). No authentication enabled per default.                                                                                                                                                                                                                                                                                                                                                                                      
Finally, after configuring InfluxDB and Loki as datasources on Grafana, you can just import the provided `Grafana_Dashboard_Template.json` dashboard template YAML file in Grafana by browsing http://127.0.0.1:3000/dashboard/import. Your dashboard will look like the following:                                                                                                                                                                                                                                                                                         
<img src="https://blog.lrvt.de/content/images/2022/11/image-4-1.png">                                                                                                                                                                                                                                                                                            





