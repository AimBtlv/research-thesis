#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: split_by_provenience.py
Description: Split a CDLI ATF corpus into folders by provenience, using the
             'provenience' column of the matching CDLI catalogue CSV.
             For every site folder the script writes one .atf file per text
             and one combined corpus file. A top-level index CSV records the
             assignment and flags extra hints found in ATF comments.
Author: Claude (for a Digital Humanities project)
Date: 2026-10-16
Version: 1.0
"""

import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

# Folder name used for texts whose 'provenience' cell in the CSV is empty
EMPTY_LABEL = "_no_provenience_in_catalogue"


def slugify(label: str) -> str:
    """Turn a CDLI provenience label into a safe ASCII folder name.

    Example: 'Nippur (mod. Nuffar)' -> 'Nippur__mod_Nuffar'
    """
    if not label.strip():
        return EMPTY_LABEL
    # Strip diacritics (Dūr-Abī-ēšuḫ -> Dur-Abi-esuh) so folders work on any OS
    ascii_label = (
        unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
    )
    ascii_label = ascii_label.replace("(mod.", "_mod").replace(")", "")
    ascii_label = re.sub(r"[^A-Za-z0-9\-_]+", "_", ascii_label)
    return re.sub(r"_+", "_", ascii_label).strip("_").replace("_mod_", "__mod_")


def read_atf_blocks(atf_path: Path) -> dict:
    """Split the ATF file into blocks keyed by numeric artifact id (P-number)."""
    text = atf_path.read_text(encoding="utf-8")
    blocks = {}
    # Each text starts with a line like '&P117397 = MVN 13, 624'
    for block in re.split(r"^(?=&P\d+)", text, flags=re.M):
        match = re.match(r"&P(\d+)", block)
        if match:
            blocks[int(match.group(1))] = block.rstrip() + "\n"
    return blocks


def atf_hint(block: str) -> str:
    """Return a provenance hint found inside ATF comments, if any.

    This is NOT used for assignment; it only helps manual checking.
    """
    # Skip '#link:' lines: 'OB Nippur Lu' there names a composite text,
    # not the findspot of this tablet (false positive otherwise)
    comments = " ".join(
        line for line in block.splitlines()
        if line.startswith("#") and not line.startswith("#link")
    )
    if "Shaduppum" in comments:
        return "Shaduppum (ATF comment)"
    if re.search(r"Nippur|\b[23]N-T", comments):
        return "Nippur (ATF comment)"
    if "Susa" in comments:
        return "Susa (ATF comment)"
    return ""


def main(atf_file: str, csv_file: str, out_dir: str) -> None:
    atf_path, csv_path, out_path = Path(atf_file), Path(csv_file), Path(out_dir)
    blocks = read_atf_blocks(atf_path)

    with csv_path.open(encoding="utf-8", newline="") as fh:
        catalogue = {int(r["artifact_id"]): r for r in csv.DictReader(fh)}

    # Sanity check: both files must describe the same set of texts
    missing_in_csv = sorted(set(blocks) - set(catalogue))
    missing_in_atf = sorted(set(catalogue) - set(blocks))
    if missing_in_csv or missing_in_atf:
        print("WARNING: id mismatch",
              "ATF-only:", missing_in_csv, "CSV-only:", missing_in_atf)

    groups = defaultdict(list)
    index_rows = []
    for pid in sorted(blocks):
        meta = catalogue.get(pid, {})
        label = meta.get("provenience", "")
        folder = slugify(label)
        groups[folder].append(pid)
        index_rows.append({
            "p_number": f"P{pid:06d}",
            "designation": meta.get("designation", ""),
            "provenience_csv": label or "(empty)",
            "folder": folder,
            "is_provenience_uncertain": meta.get("is_provenience_uncertain", ""),
            "atf_comment_hint": atf_hint(blocks[pid]),
            "genres": meta.get("genres", ""),
            "museum_no": meta.get("museum_no", ""),
        })

    # Write one file per text plus one combined corpus file per site
    for folder, pids in groups.items():
        site_dir = out_path / folder
        site_dir.mkdir(parents=True, exist_ok=True)
        for pid in pids:
            (site_dir / f"P{pid:06d}.atf").write_text(blocks[pid], encoding="utf-8")
        combined = "\n".join(blocks[pid] for pid in pids)
        (site_dir / f"_ALL_{folder}.atf").write_text(combined, encoding="utf-8")

    # Top-level index for checking and later filtering in pandas/Excel
    with (out_path / "provenience_index.csv").open("w", encoding="utf-8-sig",
                                                  newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(index_rows[0]))
        writer.writeheader()
        writer.writerows(index_rows)

    # Short console report
    print(f"Texts written: {sum(len(v) for v in groups.values())}")
    for folder, pids in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"{len(pids):4d}  {folder}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python3 split_by_provenience.py OBP.atf OBP.csv OUTPUT_DIR")
    main(*sys.argv[1:])
