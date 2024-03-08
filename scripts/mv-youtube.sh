sudo mv ~/server/apps/metube/data/* .
ls -v | cat -n | while read n f; do mv -n "$f" "$n.ext"; done