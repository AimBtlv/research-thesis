#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: join_allograph_trlit.py
Description: LEFT JOIN allograph_all.csv + 6_unicodeTrLit_Grph_Phon.csv
             on unicode_id → allograph_enriched.csv

             Join logic:
               - Base (left):  allograph_all.csv       (2535 rows, all preserved)
               - Enrichment:   6_unicodeTrLit_Grph_Phon.csv (724 rows)
               - Key:          unicode_id
               - Type:         LEFT JOIN
                               matched rows  → unicodeTrLit, syllabarySign,
                                               PhoneticsVersion filled
                               unmatched rows → those 3 fields = '' (NULL)

             Why LEFT JOIN:
               allograph_all is the primary dataset — every allograph record
               must be preserved, including Type_3 inherited UIDs and Type_2
               component rows that may not exist in the Unicode standard table.
               NULL in TrLit fields = informative: allograph without verified
               phonetics in the Unicode standard.

             Column order (as specified):
               unicode_id, allograph_ucun, component_position,
               allograph_sign, allograph_form, allograph_type,
               compound_form, allographCompound_cun, allographCompound_useq,
               unicodeTrLit, syllabarySign, PhoneticsVersion,
               signList_analogue

             Pipeline position:
               STEP 1 → extract_allograph_all_v4.py   → allograph_all.csv
               STEP 2 → extract_allographByType.py     → allographType_1/2/3.csv
               STEP 3 → THIS FILE                      → allograph_enriched.csv
               STEP 4 → transferTrLit_Sign.py          reads enriched CSV
                                                        as extended syllabary

Author: Digital Humanities Pipeline
Date: 2026-04-24
Version: 1.0
"""

import csv
import os

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
INPUT_LEFT  = os.path.join(ROOT_DIR, "2.allograph_all_v5.csv")
INPUT_RIGHT = os.path.join(ROOT_DIR, "6.unicodeTrLit_Grph_Phon.csv")
OUTPUT_CSV  = os.path.join(ROOT_DIR, "allograph_enriched.csv")

# Column order as specified
FIELDNAMES = [
    "unicode_id",             # join key — U+xxxx or compound sequence
    "allograph_ucun",         # cuneiform glyph of this row
    "component_position",     # Type_2 only: position within compound (1,2,3…)
    "allograph_sign",         # root @sign scientific name
    "allograph_form",         # @form value from osl.asl
    "allograph_type",         # Type_1 | Type_2 | Type_3
    "graphic_variant_id",     # graphical variant label (e.g. DIS_v1 / compound)
    "compound_form",          # Type_2 only: full compound @form name
    "allographCompound_cun",  # Type_2 only: full compound glyph
    "allographCompound_useq", # Type_2 only: full U+ sequence
    # ── from 6_unicodeTrLit_Grph_Phon.csv (NULL if no match) ────────────────
    "unicodeTrLit",           # Unicode transliteration label (e.g. 'a', 'a × bad')
    "syllabarySign",          # scientific sign name from Unicode standard (e.g. A, A×BAD)
    "PhoneticsVersion",       # pipe-separated list of all phonetic readings
    # ── back to allograph_all ────────────────────────────────────────────────
    "signList_analogue",      # analogue paper catalogue refs (annotated)
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def load_trlit_lookup(filepath: str) -> dict:
    """
    Load 6_unicodeTrLit_Grph_Phon.csv into a lookup dict:
      { unicode_id -> {unicodeTrLit, syllabarySign, PhoneticsVersion} }

    unicode_id is unique in this file (verified: 0 duplicates),
    so a plain dict is safe.
    """
    lookup = {}
    with open(filepath, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            uid = row["unicode_id"].strip()
            if uid:
                lookup[uid] = {
                    "unicodeTrLit":    row.get("unicodeTrLit", "").strip(),
                    "syllabarySign":   row.get("syllabarySign", "").strip(),
                    "PhoneticsVersion": row.get("PhoneticsVersion", "").strip(),
                }
    return lookup


def load_allograph(filepath: str) -> list:
    """Load allograph_all.csv and return list of row dicts."""
    with open(filepath, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Load both files ───────────────────────────────────────────────────────
    print(f"[INFO] Loading base (left):  {INPUT_LEFT}")
    allograph_rows = load_allograph(INPUT_LEFT)
    print(f"[INFO] Rows in allograph_all: {len(allograph_rows)}")

    print(f"[INFO] Loading enrichment:   {INPUT_RIGHT}")
    trlit_lookup = load_trlit_lookup(INPUT_RIGHT)
    print(f"[INFO] Rows in TrLit lookup: {len(trlit_lookup)}")

    # ── LEFT JOIN ─────────────────────────────────────────────────────────────
    # For each allograph row, look up unicode_id in trlit_lookup.
    # If found  → attach unicodeTrLit, syllabarySign, PhoneticsVersion.
    # If not found → those three fields are empty string (NULL equivalent).

    matched   = 0
    unmatched = 0
    result_rows = []

    for row in allograph_rows:
        uid = row.get("unicode_id", "").strip()

        # Look up in TrLit
        trlit_data = trlit_lookup.get(uid)

        if trlit_data:
            matched += 1
        else:
            unmatched += 1
            # Empty placeholders — NULL equivalent in CSV
            trlit_data = {
                "unicodeTrLit":    "",
                "syllabarySign":   "",
                "PhoneticsVersion": "",
            }

        # Merge into output row in specified column order
        out_row = {
            "unicode_id":             uid,
            "allograph_ucun":         row.get("allograph_ucun", ""),
            "component_position":     row.get("component_position", ""),
            "allograph_sign":         row.get("allograph_sign", ""),
            "allograph_form":         row.get("allograph_form", ""),
            "allograph_type":         row.get("allograph_type", ""),
            "compound_form":          row.get("compound_form", ""),
            "allographCompound_cun":  row.get("allographCompound_cun", ""),
            "allographCompound_useq": row.get("allographCompound_useq", ""),
            "unicodeTrLit":           trlit_data["unicodeTrLit"],
            "syllabarySign":          trlit_data["syllabarySign"],
            "PhoneticsVersion":       trlit_data["PhoneticsVersion"],
            "signList_analogue":      row.get("signList_analogue", ""),
        }
        result_rows.append(out_row)

    # ── Stats ─────────────────────────────────────────────────────────────────
    print(f"\n[JOIN] LEFT JOIN results:")
    print(f"  matched   (TrLit data added)  : {matched}")
    print(f"  unmatched (TrLit fields = '')  : {unmatched}")
    print(f"  total rows                     : {len(result_rows)}")

    # Breakdown by allograph type
    type_stats = {}
    for row in result_rows:
        t   = row["allograph_type"]
        has = bool(row["syllabarySign"])
        key = (t, has)
        type_stats[key] = type_stats.get(key, 0) + 1

    print()
    print("  Breakdown by type:")
    print(f"  {'type':<10} {'with TrLit':>12} {'without TrLit':>14}")
    print(f"  {'-'*38}")
    for t in ["Type_1", "Type_2", "Type_3"]:
        with_    = type_stats.get((t, True),  0)
        without_ = type_stats.get((t, False), 0)
        print(f"  {t:<10} {with_:>12} {without_:>14}")

    # ── Write output ──────────────────────────────────────────────────────────
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result_rows)

    print(f"\n[OK] {len(result_rows)} rows → {OUTPUT_CSV}")
    print("[DONE]")


if __name__ == "__main__":
    main()
