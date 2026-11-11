#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 04_join_matched_rest_signs.py
Description: Workflow Stage 1, Step 1.4. Reconstruction of the empty script
             4_scriptJoinMatched_RestSigns.py. Joins the 791 Unicode signs
             matched to Syllabary_CM (Step 1.2, 3_matched_signs_full.csv) and
             the 443 remaining signs described from OSL (Step 1.3,
             restUnicodeSigns.csv) into one table with all 1,234 Unicode
             signs, in the order of 1_unicodeSigns.csv:
             7_unicodePhoneticVersion_full.csv.
             The reconstruction was checked against the existing file
             (byte-identical output).
Author: Aima, reconstruction prepared with Claude
Date: 2026-11-09
Version: 1.0
"""

import csv
import sys

# --- Paths (relative to the repository: research-thesis/pipeline_v14/<this file>) ---
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parents[1]                 # research-thesis/
DP = ROOT / "2-dataset" / "DataProfile"
UA = DP / "1-5unicodeAssignmentFiles"
OUT = _P(__file__).resolve().parent / "output"
OUTPUT_DIR = OUT / "step1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

UNICODE_CSV = UA / "1_unicodeSigns.csv"
# Step 1.2 output: taken from this pipeline if present, else from the repository
MATCHED_CSV = (OUTPUT_DIR / "3_matched_signs_full.csv"
               if (OUTPUT_DIR / "3_matched_signs_full.csv").exists()
               else UA / "3_matched_signs_full.csv")
REST_CSV = OUTPUT_DIR / "restUnicodeSigns.csv"          # Step 1.3 output
OUTPUT_CSV = OUTPUT_DIR / "7_unicodePhoneticVersion_full.csv"

FIELDNAMES = ["unicode_id", "sign_grapheme", "unicodeTrLit", "syllabarySign",
              "PhoneticsVersion"]


def read_rows(path):
    """Rows of a CSV file keyed by unicode_id."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {row["unicode_id"]: row for row in csv.DictReader(fh)}


def main():
    for path in (UNICODE_CSV, MATCHED_CSV, REST_CSV):
        if not path.exists():
            sys.exit(f"[ERROR] missing input: {path}\n"
                     f"        run Step 1.2 and Step 1.3 first")
    matched, rest = read_rows(MATCHED_CSV), read_rows(REST_CSV)
    overlap = set(matched) & set(rest)
    if overlap:
        print(f"[WARN] {len(overlap)} signs in both inputs; matched version kept")

    # order of the full Unicode list (1_unicodeSigns.csv)
    with open(UNICODE_CSV, encoding="utf-8-sig", newline="") as fh:
        order = [row["unicode_id"] for row in csv.DictReader(fh)]

    out, missing = [], []
    for uid in order:
        row = matched.get(uid) or rest.get(uid)
        if row is None:
            missing.append(uid)
            continue
        out.append({k: row.get(k, "") for k in FIELDNAMES})

    # csv default line terminator is CRLF, as in the original file
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(out)

    print(f"[1] matched (Step 1.2): {len(matched)}   rest (Step 1.3): {len(rest)}")
    print(f"[2] written {len(out)} rows -> {OUTPUT_CSV}")
    if missing:
        print(f"[WARN] {len(missing)} Unicode signs in neither input: {missing[:10]}")


if __name__ == "__main__":
    main()
