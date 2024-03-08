sudo mv ~/server/apps/metube/data/* .
sudo ls -v | cat -n | while read n f; do sudo mv -n "$f" "$n.mp4"; done