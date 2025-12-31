#!/usr/bin/env bash

ROOT="${1:-.}"

season=1

find "$ROOT" -type d | sort | while read -r dir; do
  files=()
  while IFS= read -r -d '' f; do
    files+=("$f")
  done < <(find "$dir" -maxdepth 1 -type f -print0 | sort -z)

  [ ${#files[@]} -eq 0 ] && continue

  printf "Processing season %02d: %s\n" "$season" "$dir"

  episode=1
  for file in "${files[@]}"; do
    base="$(basename "$file")"
    ext="${base##*.}"
    name="${base%.*}"

    # Skip already-numbered files
    if [[ "$name" =~ ^S[0-9]{2}E[0-9]{2} ]]; then
      ((episode++))
      continue
    fi

    new="S$(printf "%02d" "$season")E$(printf "%02d" "$episode") - $base"
    mv -n "$file" "$dir/$new"
    ((episode++))
  done

  ((season++))
done