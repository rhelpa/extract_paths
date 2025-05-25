#!/usr/bin/env python3
import csv
import os
import sys
import argparse

def parse_args():
    p = argparse.ArgumentParser(
        description="Generate media_map.txt from playlist CSV and optionally create symlinks grouped by genre-show_type tags"
    )
    p.add_argument("csv", help="input playlist CSV")
    p.add_argument("--share",
                   default=os.path.expanduser("~/helpa_media_share"),
                   help="root of your mounted share")
    p.add_argument("--catalog",
                   default=os.path.expanduser("~/FieldStation42/catalog/cosmic22"),
                   help="root where to link into (tag folders created here)")
    p.add_argument("--prefix",
                   default="/volume1/PLEX_MEDIA",
                   help="strip this off each CSV path")
    p.add_argument("--link", action="store_true",
                   help="also perform the ln -sfn operations")
    # fields in CSV for tag construction
    p.add_argument("--genre-field",
                   default="items.genre",
                   help="CSV column name to use for genre")
    p.add_argument("--type-field",
                   default="items.show_type",
                   help="CSV column name to use for show type (e.g. half_hour, hour_long, movie)")
    return p.parse_args()

def sanitize(value: str) -> str:
    """Lowercase, strip spaces, and replace internal spaces with underscores"""
    return value.strip().lower().replace(' ', '_') if value else 'unknown'

if __name__ == "__main__":
    args = parse_args()
    mapping = {}  # src_rel -> tag

    # 1) pull paths & build tag mapping
    with open(args.csv, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            full = row.get("items.locations", row.get("location", "")).strip()
            if not full:
                continue

            # derive CSV-based tag
            genre_raw = row.get(args.genre_field, "")
            type_raw = row.get(args.type_field, row.get("items.type", ""))
            genre = sanitize(genre_raw)
            show_type = sanitize(type_raw)
            tag = f"{genre}-{show_type}"  # e.g. scifi-hour_long

            # strip mount prefix
            rel = full[len(args.prefix):] if full.startswith(args.prefix) else full
            if rel.startswith("/"):
                rel = rel[1:]

            mapping[rel] = tag

    # 2) write media_map.txt
    map_file = os.path.join(os.path.dirname(args.csv), "media_map.txt")
    with open(map_file, "w", encoding="utf-8") as out:
        # defaults
        out.write("/Bumps|bump\n")
        out.write("/Commercials|commercial\n")
        for src_rel, tag in sorted(mapping.items()):
            out.write(f"{src_rel}|{tag}\n")
    print(f"→ Wrote {len(mapping) + 2} lines to {map_file!r}")

    # 3) optionally perform symlinking
    if args.link:
        for src_rel, tag in mapping.items():
            src = os.path.join(args.share, src_rel)
            dst_dir = os.path.join(args.catalog, tag)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, os.path.basename(src_rel))

            if os.path.lexists(dst):
                os.remove(dst)
            try:
                os.symlink(src, dst)
                print(f"Linked {os.path.basename(src_rel)} → {tag}/")
            except OSError as e:
                print(f"⚠️  Failed to link {src}: {e}", file=sys.stderr)
