#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: split_by_provenience.py
Description: Split a CDLI ATF corpus into a two-level folder tree:
             <provenience>/<genre>/, using the 'provenience' and 'genres'
             columns of the matching CDLI catalogue CSV.
             Every genre folder gets one .atf file per text and one combined
             corpus file. Every provenience folder also keeps a combined file
             of all its texts. A top-level index CSV records the assignment
             and flags hints from the ATF itself (never used for sorting).
Author: Claude (for a Digital Humanities project)
Date: 2026-10-16
Version: 1.1
"""

import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

# Folder names used when a catalogue cell is empty
EMPTY_PROVENIENCE = "_no_provenience_in_catalogue"
EMPTY_GENRE = "_no_genre_in_catalogue"


def to_ascii(label: str) -> str:
    """Strip diacritics so folder names work on Windows, macOS and Linux."""
    return unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()


def slug_provenience(label: str) -> str:
    """'Nippur (mod. Nuffar)' -> 'Nippur__mod_Nuffar'."""
    if not label.strip():
        return EMPTY_PROVENIENCE
    s = to_ascii(label).replace("(mod.", "_mod").replace(")", "")
    s = re.sub(r"[^A-Za-z0-9\-_]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_").replace("_mod_", "__mod_")


def slug_genre(label: str) -> str:
    """'Business / Contracts' -> 'Business_Contracts'.

    Multi-genre cells such as 'Lexical; Literary' become one combined folder
    'Lexical+Literary', so every text is stored exactly once.
    """
    if not label.strip():
        return EMPTY_GENRE
    parts = []
    for part in label.split(";"):
        s = re.sub(r"[^A-Za-z0-9\-]+", "_", to_ascii(part.strip()))
        parts.append(re.sub(r"_+", "_", s).strip("_"))
    return "+".join(p for p in parts if p)


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


def provenience_hint(block: str) -> str:
    """Return a provenance hint from ATF comments (for manual checking only)."""
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


def genre_hint(block: str, meta: dict) -> str:
    """Return a genre hint from the ATF or catalogue comments (checking only)."""
    if "#atf: use lexical" in block:
        return "Lexical? (#atf: use lexical)"
    if re.search(r">>Q000(482|782|349|573)", block) or \
            "CDLI Literary" in meta.get("designation", ""):
        return "Literary? (linked to literary composite)"
    if "lentil" in (meta.get("genres_comment", "") + meta.get("artifact_comments", "")):
        return "School exercise? (lentil)"
    return ""


def write_corpus(folder: Path, name: str, pids: list, blocks: dict) -> None:
    """Write a combined corpus file with all texts of a folder."""
    combined = "\n".join(blocks[pid] for pid in pids)
    (folder / f"_ALL_{name}.atf").write_text(combined, encoding="utf-8")


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

    # tree[provenience][genre] -> list of P-numbers
    tree = defaultdict(lambda: defaultdict(list))
    index_rows = []
    for pid in sorted(blocks):
        meta = catalogue.get(pid, {})
        prov = slug_provenience(meta.get("provenience", ""))
        genre = slug_genre(meta.get("genres", ""))
        tree[prov][genre].append(pid)
        index_rows.append({
            "p_number": f"P{pid:06d}",
            "designation": meta.get("designation", ""),
            "provenience_csv": meta.get("provenience", "") or "(empty)",
            "genres_csv": meta.get("genres", "") or "(empty)",
            "folder": f"{prov}/{genre}",
            "is_provenience_uncertain": meta.get("is_provenience_uncertain", ""),
            "genres_uncertain": meta.get("genres_uncertain", ""),
            "provenience_hint_atf": provenience_hint(blocks[pid]),
            "genre_hint_atf": genre_hint(blocks[pid], meta)
            if not meta.get("genres") else "",
            "genres_comment": meta.get("genres_comment", "").strip(),
            "museum_no": meta.get("museum_no", ""),
        })

    # Write files: <provenience>/<genre>/P*.atf + combined corpora
    for prov, genres in tree.items():
        prov_dir = out_path / prov
        all_pids = []
        for genre, pids in genres.items():
            genre_dir = prov_dir / genre
            genre_dir.mkdir(parents=True, exist_ok=True)
            for pid in pids:
                (genre_dir / f"P{pid:06d}.atf").write_text(blocks[pid],
                                                          encoding="utf-8")
            write_corpus(genre_dir, genre, pids, blocks)
            all_pids.extend(pids)
        write_corpus(prov_dir, prov, sorted(all_pids), blocks)

    # Top-level index (utf-8-sig so Excel opens diacritics correctly)
    with (out_path / "provenience_genre_index.csv").open(
            "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(index_rows[0]))
        writer.writeheader()
        writer.writerows(index_rows)

    # Console report: provenience, then genres inside it
    total = 0
    for prov, genres in sorted(tree.items(), key=lambda kv: -sum(map(len, kv[1].values()))):
        n = sum(len(v) for v in genres.values())
        total += n
        print(f"{n:4d}  {prov}")
        for genre, pids in sorted(genres.items(), key=lambda kv: -len(kv[1])):
            print(f"      {len(pids):4d}  {genre}")
    print(f"Texts written: {total}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python3 split_by_provenience.py OBP.atf OBP.csv OUTPUT_DIR")
    main(*sys.argv[1:])
