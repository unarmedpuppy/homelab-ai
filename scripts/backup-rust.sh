#!/bin/bash
dest_dir="/home/unarmedpuppy/server/apps/rust/data/backups/backup-$(date +%Y%m%d)"
mkdir -p "$dest_dir"
cp -pf $(find ~/server/apps/rust/data/rust/server/unarmedpuppy -type f -name '*player*') "$dest_dir"