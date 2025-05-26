#!/usr/bin/env python3
import csv, os, sys, shutil, argparse
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(
        description="Generate media-map-<csv>.txt and (optionally) sync a FieldStation42 catalog"
    )
    p.add_argument("csv", help="input playlist CSV")
    p.add_argument("--share", default=Path.home()/"helpa_media_share",
                   help="root of your mounted share")
    p.add_argument("--catalog", default=Path.home()/"FieldStation42"/"catalog",
                   help="root where to link into")
    p.add_argument("--prefix", default="/volume1/PLEX_MEDIA",
                   help="strip this off each CSV path")
    p.add_argument("--link", action="store_true",
                   help="also clear & populate the catalog")
    return p.parse_args()

def build_mapping(csv_path, prefix):
    mapping = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            full = row.get("items.locations","").strip()
            if not full: continue
            kind = row.get("items.type","").lower().strip()
            category = "tv_show" if kind=="episode" else "movie"
            rel = full[len(prefix):] if full.startswith(prefix) else full
            mapping[rel.lstrip("/")] = category
    return mapping

def write_map_file(csv_path, mapping):
    base = Path(csv_path).stem
    out = Path(csv_path).with_name(f"media-map-{base}.txt")
    with open(out,"w",encoding="utf-8") as o:
        o.write("/Bumps|bump\n")
        o.write("/Commercials|commercial\n")
        for rel,cat in sorted(mapping.items()):
            o.write(f"{rel}|{cat}\n")
    print(f"→ Wrote {len(mapping)+2} lines to {out}")
    return out

def sync_catalog(map_file, share_root, catalog_root):
    # derive station name
    raw = map_file.stem.removeprefix("media-map-")
    station = raw.removeprefix("playlist-")
    cat_root = catalog_root/station

    # clear & recreate
    if cat_root.exists():
        shutil.rmtree(cat_root)
    cat_root.mkdir(parents=True)

    # preload existing subdirs
    existing = [d.name for d in cat_root.iterdir() if d.is_dir()]

    show_targets = {}

    # read map and symlink
    with open(map_file, encoding="utf-8") as f:
        for line in f:
            src_rel, tgt = line.strip().split("|",1)
            if not src_rel or src_rel.startswith("#"): continue

            # group episodes by show
            show = None
            if src_rel.startswith("TV Shows/"):
                show = Path(src_rel).parts[2]  # "TV Shows / ShowName / ..."

            # pick target dir
            if show:
                if show in show_targets:
                    tgt_sub = show_targets[show]
                else:
                    tgt_sub = prompt_choice(show, tgt, existing)
                    show_targets[show] = tgt_sub
            else:
                tgt_sub = prompt_choice(src_rel, tgt, existing)

            if tgt_sub not in existing:
                existing.append(tgt_sub)
