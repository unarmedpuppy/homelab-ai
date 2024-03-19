#!/bin/bash
~/repos/home-server/scripts/git-sync.sh
ssh unarmedpuppy@172.16.30.45 -p 4242 "~/server/scripts/git-sync.sh"

