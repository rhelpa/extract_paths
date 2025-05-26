#!/usr/bin/env python3
import csv
import re
from pathlib import Path

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
INPUT_CSV = "all-playlists.csv"   # adjust if needed
TYPE_COL   = "type"               # column marking playlist boundaries
TITLE_COL  = "title"              # column holding the playlist title

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def sanitize_filename(name: str) -> str:
    """
    Replace any character that's not a letter, digit, dot, underscore, or hyphen
    with an underscore, then strip leading/trailing whitespace.
    """
    safe = re.sub(r'[^\w\-. ]', '_', name)
    return safe.strip()

# ─── MAIN LOGIC ────────────────────────────────────────────────────────────────
def split_playlists(input_path: Path):
    playlists = {}   # title -> list of rows
    current_title = None
    current_rows  = []

    # Open source CSV
    with input_path.open(newline='', encoding='utf-8') as src:
        reader = csv.DictReader(src)
        headers = reader.fieldnames

        if headers is None or TYPE_COL not in headers:
            raise ValueError(f"CSV must have a '{TYPE_COL}' column")

        for row in reader:
            if row.get(TYPE_COL) == "playlist":
                # Flush previous playlist
                if current_title:
                    playlists[current_title] = current_rows

                # Start new playlist
                title = row.get(TITLE_COL, "").strip()
                if not title:
                    # fallback in case TITLE_COL is empty
                    title = f"untitled_{len(playlists)+1}"
                current_title = title
                current_rows  = [row]
            else:
                # Continue accumulating under the current playlist
                if current_title:
                    current_rows.append(row)
                # else: ignore any rows before the first 'playlist' marker

        # Flush the last
        if current_title:
            playlists[current_title] = current_rows

    # Write out each playlist file
    for title, rows in playlists.items():
        safe_title = sanitize_filename(title)
        out_path   = Path(f"playlist-{safe_title}.csv")
        with out_path.open('w', newline='', encoding='utf-8') as dst:
            writer = csv.DictWriter(dst, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} rows to {out_path}")

if __name__ == "__main__":
    split_playlists(Path(INPUT_CSV))
