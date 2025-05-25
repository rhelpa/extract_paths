#!/usr/bin/env bash
set -euo pipefail

# Configuration: adjust if needed
SHARE="${HOME}/helpa_media_share"
CATALOG="${HOME}/FieldStation42/catalog"

# Pick map-file from arg or first media-map-*.txt
MAPFILE="${1:-}"
if [[ -z "$MAPFILE" ]]; then
  shopt -s nullglob
  files=( media-map-*.txt )
  (( ${#files[@]} )) || { echo "❌  No media-map-*.txt here." >&2; exit 1; }
  MAPFILE="${files[0]}"
fi

[[ -r "$MAPFILE" ]] || { echo "❌  Cannot read $MAPFILE" >&2; exit 1; }
echo "Using map file: $MAPFILE"

# Derive station name
base="$(basename "$MAPFILE" .txt)"
playlist_raw="${base#media-map-}"
station="${playlist_raw#playlist-}"

# Root for this station
CAT_ROOT="$CATALOG/$station"
echo "→ Linking into: $CAT_ROOT/"
mkdir -p "$CAT_ROOT"

# Preload existing subdirectories under this station
mapfile -t EXISTING < <(
  find "$CAT_ROOT" -mindepth 1 -maxdepth 1 -type d -printf '%f\n'
)

declare -A SHOW_TARGETS   # cache of user choices for each TV show

# Loop over map file
while IFS='|' read -r src_rel tgt_sub; do
  [[ -z "$src_rel" || "$src_rel" =~ ^# ]] && continue

  # detect TV show grouping
  show=""
  if [[ "$src_rel" =~ ^TV\ Shows/([^/]+)/ ]]; then
    show="${BASH_REMATCH[1]}"
  fi

  if [[ -n "$show" ]]; then
    # if we've already asked for this show, reuse the answer
    if [[ -n "${SHOW_TARGETS[$show]:-}" ]]; then
      tgt_sub="${SHOW_TARGETS[$show]}"
      echo
      echo "📺 $show → using cached target: $tgt_sub"
    else
      # first episode of this show: prompt once
      echo
      echo "📺 Show: $show"
      echo "Default target subdir: $tgt_sub"
      # build menu
      options=( "$tgt_sub" "${EXISTING[@]}" "CUSTOM" )
      PS3="Choose target for \"$show\" (1-${#options[@]}): "
      select opt in "${options[@]}"; do
        if [[ -n "$opt" ]]; then
          if [[ "$opt" == "CUSTOM" ]]; then
            read -rp "Enter custom subdir name for \"$show\": " opt < /dev/tty
          fi
          tgt_sub="$opt"
          break
        else
          echo "⚠️  Invalid choice." >&2
        fi
      done < /dev/tty

      # cache this choice
      SHOW_TARGETS[$show]="$tgt_sub"
      # add to EXISTING if new
      if ! printf '%s\n' "${EXISTING[@]}" | grep -Fxq "$tgt_sub"; then
        EXISTING+=("$tgt_sub")
      fi
    fi
  else
    # non-TV (e.g. movies) — prompt per-file as before
    echo
    echo "🎬 File: $src_rel"
    echo "Default target subdir: $tgt_sub"
    options=( "$tgt_sub" "${EXISTING[@]}" "CUSTOM" )
    PS3="Choose target for this file (1-${#options[@]}): "
    select opt in "${options[@]}"; do
      if [[ -n "$opt" ]]; then
        if [[ "$opt" == "CUSTOM" ]]; then
          read -rp "Enter custom subdir name: " opt < /dev/tty
        fi
        tgt_sub="$opt"
        break
      else
        echo "⚠️  Invalid choice." >&2
      fi
    done < /dev/tty

    # add new to cache
    if ! printf '%s\n' "${EXISTING[@]}" | grep -Fxq "$tgt_sub"; then
      EXISTING+=("$tgt_sub")
    fi
  fi

  # perform symlink
  src="$SHARE/$src_rel"
  dst_dir="$CAT_ROOT/$tgt_sub"
  dst="$dst_dir/$(basename "$src_rel")"

  if [[ ! -e "$src" ]]; then
    echo "⚠️  Source missing: $src" >&2
    continue
  fi

  mkdir -p "$dst_dir"
  ln -sfn "$src" "$dst"
  echo "📁  Linked $(basename "$src_rel") → $station/$tgt_sub/"

done < "$MAPFILE"
