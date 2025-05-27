#!/usr/bin/env python3
import csv
import os
import argparse

# Place into FieldStation42/scripts
# Setup CSV with appropriate headers & filename (playlist-<station_name>.csv)

def parse_args():
    p = argparse.ArgumentParser(
        description="Generate media_map-<csv_name>.txt from playlist CSV grouped by tv_show/movie"
    )
    p.add_argument("csv", help="input playlist CSV")
    p.add_argument("--prefix",
                   default="/volume1/PLEX_MEDIA",
                   help="strip this off each CSV path")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    csv_path = args.csv
    csv_base = os.path.splitext(os.path.basename(csv_path))[0]
    out_filename = f"media-map-{csv_base}.txt"
    out_path = os.path.join(os.path.dirname(csv_path), out_filename)

    total = 0
    with open(csv_path, newline="", encoding="utf-8") as f, \
         open(out_path, "w", encoding="utf-8") as out:
        # default entries
        out.write("/Bumps|bump\n")
        out.write("/Commercials|commercial\n")
        # process CSV rows
        reader = csv.DictReader(f)
        for row in reader:
            full = row.get("items.locations", "").strip()
            if not full:
                continue
            kind = row.get("items.type", "").strip().lower()
            category = "tv_show" if kind == "episode" else "movie"
            # strip prefix
            rel = full[len(args.prefix):] if full.startswith(args.prefix) else full
            rel = rel.lstrip("/")
            out.write(f"{rel}|{category}\n")
            total += 1

    print(f"→ Wrote {total + 2} lines to '{out_path}'")
