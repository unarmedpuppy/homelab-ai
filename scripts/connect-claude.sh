#!/bin/bash
# Connect to claude-harness container via SSH
# Usage:
#   ./connect-claude.sh          # SSH into container
#   ./connect-claude.sh claude   # Run claude directly
#   ./connect-claude.sh bash     # Run bash shell

if [ -z "$1" ]; then
    ssh appuser@192.168.86.47 -p 2222
else
    ssh appuser@192.168.86.47 -p 2222 -t "$@"
fi
