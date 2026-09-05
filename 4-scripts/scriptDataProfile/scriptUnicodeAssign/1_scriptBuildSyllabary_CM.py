#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
from pathlib import Path

# 0. Paths


INPUT_DIR  = Path("/mnt/project")           
OUTPUT_DIR = Path("/mnt/user-data/outputs") 

CM_FILE         = INPUT_DIR / "2_syllabary_CM.csv"
URUK2_FILE      = INPUT_DIR / "syllabary_uruk2.txt"
ADDITIONAL_FILE = INPUT_DIR / "additional_signs.txt"
OUTPUT_CSV      = OUTPUT_DIR / "Syllabary_CM.csv"

FIELDNAMES = ["phonetic_reading", "sign_name", "source"]


#1. Parse syllabary_CM.txt
def parse_cm(path: Path) -> list[dict]:
    """
    Parse the main CM syllabary.

    Format per line:  phonetic_reading<TAB>SIGN_NAME
    - Lines without a tab separator are skipped with a warning.
    - Leading/trailing whitespace is stripped from both fields.
    - Empty lines are skipped silently.

    Returns a list of dicts with keys: phonetic_reading, sign_name, source.
    """
    rows = []
    skipped = 0

    with open(path, encoding="utf-8", newline="") as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue                          

            parts = line.split("\t")
            if len(parts) < 2:
                skipped += 1                       
                continue

            phonetic  = parts[0].strip()
            sign_name = parts[1].strip()

            if not phonetic or not sign_name:
                skipped += 1
                continue

            rows.append({
                "phonetic_reading": phonetic,
                "sign_name":        sign_name,
                "source":           "CM",
            })

    print(f"  [CM]         {len(rows):>6,} entries  ← {path.name}"
          + (f"  ({skipped} lines skipped)" if skipped else ""))
    return rows


#  2. Parse syllabary_uruk2.txt 

def parse_uruk2(path: Path) -> list[dict]:
    """
    Parse the Uruk archaic sign list.

    Format per line:  SIGN_NAME   (one sign name per line, no phonetic value)
    - Lines starting with # are comments  skip.
    - Empty lines are skipped silently.

    Because Uruk-period writing was purely logographic (no phonetic component),
    these entries have no ATF reading. The sign name itself is stored in BOTH
    fields: phonetic_reading = sign_name.  This makes them findable by name
    in Stage A lookups while making their logographic nature explicit.

    Returns a list of dicts with keys: phonetic_reading, sign_name, source.
    """
    rows = []

    with open(path, encoding="utf-8", newline="") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            rows.append({
                "phonetic_reading": line,  
                "sign_name":        line,   
                "source":           "URUK2",
            })

    print(f"  [URUK2]      {len(rows):>6,} entries  ← {path.name}")
    return rows


#  3. Parse additional_signs.txt

def parse_additional(path: Path) -> list[dict]:
    """
    Parse the supplementary signs file.

    Format per line:  phonetic_reading<TAB>SIGN_NAME
    Identical format to syllabary_CM.txt.
    Lines without a tab separator are skipped with a warning.

    Returns a list of dicts with keys: phonetic_reading, sign_name, source.
    """
    rows = []
    skipped = 0

    with open(path, encoding="utf-8", newline="") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 2:
                skipped += 1
                continue

            phonetic  = parts[0].strip()
            sign_name = parts[1].strip()

            if not phonetic or not sign_name:
                skipped += 1
                continue

            rows.append({
                "phonetic_reading": phonetic,
                "sign_name":        sign_name,
                "source":           "ADDITIONAL",
            })

    print(f"  [ADDITIONAL] {len(rows):>6,} entries  ← {path.name}"
          + (f"  ({skipped} lines skipped)" if skipped else ""))
    return rows


#  4. Merge and deduplicate 
def merge(cm: list[dict], uruk2: list[dict], additional: list[dict]) -> list[dict]:
    """
    Merge all three sources.

    Priority order (earlier source wins on duplicate phonetic_reading):
        1. CM          — most authoritative for standard periods
        2. ADDITIONAL  — extends CM with rare/compound forms
        3. URUK2       — archaic logographic signs (lowest priority)

    Deduplication is on the composite key (phonetic_reading, sign_name).
    The same reading can legitimately map to multiple sign names (homophony),
    so only exact (phonetic_reading, sign_name) pairs are deduplicated.
    """
    seen = set()
    merged = []

    for row in cm + additional + uruk2:
        key = (row["phonetic_reading"], row["sign_name"])
        if key not in seen:
            seen.add(key)
            merged.append(row)

    return merged


# 5. Write output 

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  [saved] {path}")


#  6. Summary

def print_summary(cm, uruk2, additional, merged) -> None:
    from collections import Counter
    by_source = Counter(r["source"] for r in merged)
    duplicates = (len(cm) + len(uruk2) + len(additional)) - len(merged)

    print("\n── Merge summary ─────────────────────────────────────────────")
    print(f"  CM entries             : {len(cm):>6,}")
    print(f"  URUK2 entries          : {len(uruk2):>6,}")
    print(f"  ADDITIONAL entries     : {len(additional):>6,}")
    print(f"  ─────────────────────────────────────────────────────────")
    print(f"  Raw total              : {len(cm)+len(uruk2)+len(additional):>6,}")
    print(f"  Duplicates removed     : {duplicates:>6,}")
    print(f"  Final unified entries  : {len(merged):>6,}")
    print()
    print(f"  By source in output:")
    print(f"    CM         : {by_source['CM']:>6,}")
    print(f"    ADDITIONAL : {by_source['ADDITIONAL']:>6,}")
    print(f"    URUK2      : {by_source['URUK2']:>6,}")
    print()
    print(f"  Sample rows:")
    for r in merged[:4]:
        print(f"    {r['phonetic_reading']:20s} → {r['sign_name']:25s} [{r['source']}]")
    print("──────────────────────────────────────────────────────────────\n")


# main

def main() -> None:
    print("=" * 65)
    print("  build_syllabary_CM.py  —  Stage A / Step 1")
    print("  Building master Syllabary_CM.csv from three source files")
    print("=" * 65 + "\n")

    for f in [CM_FILE, URUK2_FILE, ADDITIONAL_FILE]:
        if not f.exists():
            sys.exit(f"[ERROR] File not found: {f}")

    cm         = parse_cm(CM_FILE)
    uruk2      = parse_uruk2(URUK2_FILE)
    additional = parse_additional(ADDITIONAL_FILE)

    merged = merge(cm, uruk2, additional)

    write_csv(OUTPUT_CSV, merged)
    print_summary(cm, uruk2, additional, merged)


if __name__ == "__main__":
    main()
