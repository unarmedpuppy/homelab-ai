
# Seafile
 installed seafile cli

 mkdir ~/seafile-client

 seaf-cli init -d ~/seafile-client

 seaf-cli start

 seaf-cli download -l "6e64c8a4-dac9-40a2-bf17-730b740d902b" -s  "http://192.168.86.47:7780/" -d "/mnt/server-storage/entertainment-sync" -u "seafile@jenquist.com" -p "MySecureLoginPassword"
 seaf-cli download -l "c8a506c3-ee92-4301-8dbc-ac3336dea4ec" -s  "http://192.168.86.47:7780/" -d "/mnt/server-storage/family-media-sync" -u "seafile@jenquist.com" -p "MySecureLoginPassword"

 check library integrity:

 `docker exec -it <container-name> /bin/bash`

`cd seafile-server-latest`

 `./seaf-fsck.sh`

run as non-root:

 sudo groupadd --gid 8000 seafile
sudo useradd --home-dir /home/seafile --create-home --uid 8000 --gid 8000 --shell /bin/sh --skel /dev/null seafile


