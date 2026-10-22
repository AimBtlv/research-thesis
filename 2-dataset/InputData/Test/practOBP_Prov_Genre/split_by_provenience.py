#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: split_by_provenience.py
Description: Merge one or more CDLI ATF exports with their catalogue CSVs,
             remove duplicates, and split the corpus into a two-level folder
             tree: <provenience>/<genre>/. Every genre folder gets one .atf
             file per text and one combined corpus file; every provenience
             folder also keeps a combined file of all its texts.
             A top-level index CSV records the assignment, flags hints from
             the ATF (never used for sorting), and a validation report lists
             counts, duplicates and mismatches between ATF and CSV.
Author: Claude (for a Digital Humanities project)
Date: 2026-10-16
Version: 1.2
"""

import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# Folder names used when a catalogue cell is empty
EMPTY_PROVENIENCE = "_no_provenience_in_catalogue"
EMPTY_GENRE = "_no_genre_in_catalogue"
# Folder name for texts that are in the CSV but have no ATF block
NO_ATF_NOTE = "csv_only_no_transliteration"

csv.field_size_limit(10**9)  # some CDLI cells are very long


# ---------------------------------------------------------------- naming ---

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

    Multi-genre cells ('Lexical; Literary') become one combined folder
    'Lexical+Literary', so every text is stored exactly once.
    """
    if not label.strip():
        return EMPTY_GENRE
    parts = []
    for part in label.split(";"):
        s = re.sub(r"[^A-Za-z0-9\-]+", "_", to_ascii(part.strip()))
        parts.append(re.sub(r"_+", "_", s).strip("_"))
    return "+".join(p for p in parts if p)


# --------------------------------------------------------------- reading ---

def collect_files(inputs: list, suffix: str) -> list:
    """Expand files and folders into a sorted list, skipping macOS junk."""
    found = []
    for item in inputs:
        path = Path(item)
        candidates = path.rglob(f"*{suffix}") if path.is_dir() else [path]
        for f in candidates:
            # '__MACOSX' folders and '._name' files are Finder metadata
            if "__MACOSX" in f.parts or f.name.startswith("._"):
                continue
            if f.suffix.lower() == suffix:
                found.append(f)
    return sorted(set(found))


def read_atf(files: list, report: list) -> dict:
    """Read all ATF files into {artifact_id: block}, tracking duplicates."""
    blocks, duplicates, conflicts = {}, 0, []
    for f in files:
        # Normalise Windows line endings so blocks compare cleanly
        text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
        for block in re.split(r"^(?=&P\d+)", text, flags=re.M):
            match = re.match(r"&P(\d+)", block)
            if not match:
                continue
            pid, block = int(match.group(1)), block.rstrip() + "\n"
            if pid in blocks:
                duplicates += 1
                if blocks[pid] != block:
                    conflicts.append(pid)  # same P-number, different text
                continue
            blocks[pid] = block
    report.append(f"ATF files read: {len(files)}")
    report.append(f"ATF unique texts: {len(blocks)}")
    report.append(f"ATF duplicates skipped: {duplicates}")
    report.append(f"ATF duplicates with different text: {len(conflicts)} {conflicts[:20]}")
    return blocks


def read_csv(files: list, report: list) -> dict:
    """Read all catalogue CSVs into {artifact_id: row}, tracking duplicates."""
    rows, duplicates = {}, 0
    for f in files:
        with f.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                pid = int(row["artifact_id"])
                if pid in rows:
                    duplicates += 1
                    continue
                rows[pid] = row
    report.append(f"CSV files read: {len(files)}")
    report.append(f"CSV unique records: {len(rows)}")
    report.append(f"CSV duplicates skipped: {duplicates}")
    return rows


# ----------------------------------------------------------------- hints ---

def provenience_hint(block: str) -> str:
    """Provenance hint from ATF comments (for manual checking only)."""
    # Skip '#link:' lines: 'OB Nippur Lu' there names a composite text
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
    """Genre hint from the ATF or catalogue comments (checking only)."""
    if "#atf: use lexical" in block:
        return "Lexical? (#atf: use lexical)"
    if "#atf: use math" in block:
        return "Mathematical? (#atf: use math)"
    if re.search(r">>Q000(482|782|349|573|79\d|80\d|823)", block) or \
            "CDLI Literary" in meta.get("designation", ""):
        return "Literary? (linked to literary composite)"
    if "lentil" in (meta.get("genres_comment", "") + meta.get("artifact_comments", "")):
        return "School exercise? (lentil)"
    return ""


# ------------------------------------------------------------------ main ---

def write_corpus(folder: Path, name: str, pids: list, blocks: dict) -> None:
    """Write a combined corpus file with all texts of a folder."""
    combined = "\n".join(blocks[pid] for pid in pids)
    (folder / f"_ALL_{name}.atf").write_text(combined, encoding="utf-8")


def main(out_dir: str, inputs: list) -> None:
    out_path = Path(out_dir)
    report = []
    blocks = read_atf(collect_files(inputs, ".atf"), report)
    catalogue = read_csv(collect_files(inputs, ".csv"), report)

    csv_only = sorted(set(catalogue) - set(blocks))
    atf_only = sorted(set(blocks) - set(catalogue))
    report.append(f"In CSV but no ATF: {len(csv_only)} "
                  f"{['P%06d' % p for p in csv_only]}")
    report.append(f"In ATF but no CSV: {len(atf_only)} "
                  f"{['P%06d' % p for p in atf_only[:50]]}")
    periods = Counter(r.get("period", "") for r in catalogue.values())
    report.append(f"Periods in CSV: {dict(periods)}")

    # tree[provenience][genre] -> list of P-numbers (only texts with ATF)
    tree = defaultdict(lambda: defaultdict(list))
    index_rows = []
    for pid in sorted(set(blocks) | set(catalogue)):
        meta = catalogue.get(pid, {})
        prov = slug_provenience(meta.get("provenience", ""))
        genre = slug_genre(meta.get("genres", ""))
        has_atf = pid in blocks
        if has_atf:
            tree[prov][genre].append(pid)
        block = blocks.get(pid, "")
        index_rows.append({
            "p_number": f"P{pid:06d}",
            "designation": meta.get("designation", ""),
            "provenience_csv": meta.get("provenience", "") or "(empty)",
            "genres_csv": meta.get("genres", "") or "(empty)",
            "folder": f"{prov}/{genre}" if has_atf else NO_ATF_NOTE,
            "languages": meta.get("languages", ""),
            "artifact_type": meta.get("artifact_type", ""),
            "is_provenience_uncertain": meta.get("is_provenience_uncertain", ""),
            "genres_uncertain": meta.get("genres_uncertain", ""),
            "provenience_hint_atf": provenience_hint(block),
            "genre_hint_atf": genre_hint(block, meta) if not meta.get("genres") else "",
            "genres_comment": meta.get("genres_comment", "").strip(),
            "museum_no": meta.get("museum_no", ""),
            "collections": meta.get("collections", ""),
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

    # Full merged corpus in one file, handy for later NLP work
    write_corpus(out_path, "corpus_merged", sorted(blocks), blocks)

    # Top-level index (utf-8-sig so Excel opens diacritics correctly)
    with (out_path / "provenience_genre_index.csv").open(
            "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(index_rows[0]))
        writer.writeheader()
        writer.writerows(index_rows)

    # Summary table: provenience x genre counts
    with (out_path / "summary_counts.csv").open(
            "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["provenience_folder", "genre_folder", "texts"])
        for prov, genres in sorted(tree.items()):
            for genre, pids in sorted(genres.items()):
                writer.writerow([prov, genre, len(pids)])

    # Validation report
    written = sum(len(v) for g in tree.values() for v in g.values())
    report.append(f"Texts written to folders: {written}")
    report.append(f"Provenience folders: {len(tree)}")
    (out_path / "validation_report.txt").write_text("\n".join(report) + "\n",
                                                    encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Usage: python3 split_by_provenience.py OUTPUT_DIR "
                 "INPUT [INPUT ...]   (files or folders with .atf and .csv)")
    main(sys.argv[1], sys.argv[2:])
