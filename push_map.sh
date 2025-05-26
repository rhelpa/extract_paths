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
echo "→ Preparing catalog at: $CAT_ROOT/"
mkdir -p "$CAT_ROOT"

# Preload existing subdirectories under this station (for reuse)
mapfile -t EXISTING < <(
  find "$CAT_ROOT" -mindepth 1 -maxdepth 1 -type d -printf '%f\n'
)

# Clear out any previous contents for a fresh run
echo "🧹  Clearing existing contents in $CAT_ROOT ..."
rm -rf "$CAT_ROOT"/*

declare -A SHOW_TARGETS   # cache of user choices for each TV show

# Loop over map file
while IFS='|' read -r src_rel tgt_sub; do
  [[ -z "$src_rel" || "$src_rel" =~ ^# ]] && continue

  # Special case: if this is the root of Bumps or Commercials, drill into each subdirectory
  if [[ "$src_rel" == "Bumps" || "$src_rel" == "Commercials" ]]; then
    echo
    echo "📂 Expanding category: $src_rel/"
    for d in "$SHARE/$src_rel"/*/; do
      [[ -d "$d" ]] || continue
      subpath="${src_rel}/$(basename "$d")"
      default="${tgt_sub}"

      # ask where to link this bump/commercial
      echo
      echo "🎬 Item: $subpath"
      echo "Default target subdir: $default"
      options=( "$default" "${EXISTING[@]}" "CUSTOM" )
      PS3="Choose target for \"$subpath\" (1-${#options[@]}): "
      select opt in "${options[@]}"; do
        if [[ -n "$opt" ]]; then
          if [[ "$opt" == "CUSTOM" ]]; then
            read -rp "Enter custom subdir name: " opt < /dev/tty
          fi
          tgt_choice="$opt"
          break
        else
          echo "⚠️  Invalid choice." >&2
        fi
      done < /dev/tty

      # add to EXISTING if new
      if ! printf '%s\n' "${EXISTING[@]}" | grep -Fxq "$tgt_choice"; then
        EXISTING+=("$tgt_choice")
      fi

      # link it
      dst_dir="$CAT_ROOT/$tgt_choice"
      mkdir -p "$dst_dir"
      ln -sfn "$d" "$dst_dir/$(basename "$d")"
      echo "📁 Linked $(basename "$d") → $station/$tgt_choice/"
    done

    # skip the normal single-link path for this entry
    continue
  fi

  # detect TV show grouping
  show=""
  if [[ "$src_rel" =~ ^TV\ Shows/([^/]+)/ ]]; then
    show="${BASH_REMATCH[1]}"
  fi

  if [[ -n "$show" ]]; then
    if [[ -n "${SHOW_TARGETS[$show]:-}" ]]; then
      tgt_sub="${SHOW_TARGETS[$show]}"
      echo
      echo "📺 $show → using cached target: $tgt_sub"
    else
      echo
      echo "📺 Show: $show"
      echo "Default target subdir: $tgt_sub"
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

      SHOW_TARGETS[$show]="$tgt_sub"
      if ! printf '%s\n' "${EXISTING[@]}" | grep -Fxq "$tgt_sub"; then
        EXISTING+=("$tgt_sub")
      fi
    fi
  else
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

    if ! printf '%s\n' "${EXISTING[@]}" | grep -Fxq "$tgt_sub"; then
      EXISTING+=("$tgt_sub")
    fi
  fi

  # perform symlink for single file or directory
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
