# Linux Server

- Debian 12
- local ip: `192.168.86.47`
- Power mode: Performance
- Power Saving Options: Screen blank: Never, Auto Suspend: Off
- Power Button Behavior: Nothing

`ssh unarmedpuppy@192.168.86.47 -p 4242`

# user list

`root` (root)

`unarmedpuppy` (added to sudoers file)

# External Storage

- PLEX 2TB (media contenxt)
- server-storage 2TB (misc)
- server-backup 2TB (backup target)


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

- Install rsnapshot

    `sudo apt-get install rsnapshot`

- Configure rsnapshot

    `sudo nano /etc/rsnapshot.conf`

    Backing up to external drive, /media/unarmedpuppy/server-backup 

- Testing rsnapshot

    `sudo rsnapshot configtest`

- Running rsnapshot

    `sudo rsnapshot daily`

### Home Assistant

### Pi Hole

### Plex






