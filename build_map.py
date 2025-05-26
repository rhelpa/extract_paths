#!/usr/bin/env python3
import csv
import os
import sys
import argparse


# Place into FieldStation42/scripts
# Setup CSV with appropriate headers & filename (playlist-<station_name>.csv)




def parse_args():
    p = argparse.ArgumentParser(
        description="Generate media_map-<csv_name>.txt from playlist CSV and optionally create symlinks grouped by tv_show/movie"
    )
    p.add_argument("csv", help="input playlist CSV")
    p.add_argument("--share",
                   default=os.path.expanduser("~/helpa_media_share"),
                   help="root of your mounted share")
    p.add_argument("--catalog",
                   default=os.path.expanduser("~/FieldStation42/catalog"),
                   help="root where to link into (tv_show/movie folders created here)")
    p.add_argument("--prefix",
                   default="/volume1/PLEX_MEDIA",
                   help="strip this off each CSV path")
    p.add_argument("--link", action="store_true",
                   help="also perform the ln -sfn operations")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    mapping = {}  # src_rel -> category ('tv_show' or 'movie')

    # 1) pull paths & determine category
    with open(args.csv, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            full = row.get("items.locations", "").strip()
            if not full:
                continue

            kind = row.get("items.type", "").strip().lower()
            if kind == "episode":
                category = "tv_show"
            else:
                # missing or movie
                category = "movie"

            # strip mount prefix
            rel = full[len(args.prefix):] if full.startswith(args.prefix) else full
            if rel.startswith("/"):
                rel = rel[1:]

            mapping[rel] = category

    # 2) write media-map-<csv_name>.txt
    csv_base = os.path.splitext(os.path.basename(args.csv))[0]
    out_filename = f"media-map-{csv_base}.txt"
    map_file = os.path.join(os.path.dirname(args.csv), out_filename)
    with open(map_file, "w", encoding="utf-8") as out:
        out.write("/Bumps|bump\n")
        out.write("/Commercials|commercial\n")
        for src_rel, category in sorted(mapping.items()):
            out.write(f"{src_rel}|{category}\n")
    print(f"→ Wrote {len(mapping) + 2} lines to {map_file!r}")

    # 3) optionally perform symlinking
    if args.link:
        for src_rel, category in mapping.items():
            src = os.path.join(args.share, src_rel)
            dst_dir = os.path.join(args.catalog, category)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, os.path.basename(src_rel))

            if os.path.lexists(dst):
                os.remove(dst)
            try:
                os.symlink(src, dst)
                print(f"Linked {os.path.basename(src_rel)} → {category}/")
            except OSError as e:
                print(f"⚠️  Failed to link {src}: {e}", file=sys.stderr)