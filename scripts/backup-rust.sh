#!/bin/bash
dest_dir="backup-$(date +%Y%m%d)"
mkdir -p "$dest_dir"
cp -pf $(find ~/server/apps/rust/data/rust/server/unarmedpuppy -type f -name '*player*') "$dest_dir"