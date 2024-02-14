#!/bin/bash
~/repos/home-server/scripts/git-sync.sh
~/repos/home-server/scripts/connect-server.sh "shopt -s expand_aliases; source ~/.bashrc; eval sync"
exit
