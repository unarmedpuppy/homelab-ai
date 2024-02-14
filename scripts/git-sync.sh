#!/bin/bash
cd ~/server
git add --all
git commit -m "syncing..."
git pull
git push origin main
