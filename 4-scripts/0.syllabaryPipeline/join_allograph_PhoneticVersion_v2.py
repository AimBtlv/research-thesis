#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: join_allograph_omograph.py
Description: LEFT JOIN allograph_all.csv + 6_unicodeTrLit_Grph_Phon.csv
             on unicode_id → 3_joinAllograph_Omograph.csv

             Adapted from extract_allograph_all_v5.py:
               - Column order follows v5 canonical structure
               - graphic_variant_id column included (position 6)
               - Three TrLit enrichment columns inserted at positions 11–13
                 (before signList_analogue)

             Join logic:
               Base (left)  : allograph_all.csv         — 2535 rows, all preserved
               Enrichment   : 6_unicodeTrLit_Grph_Phon.csv — 724 rows
               Key          : unicode_id
               Type         : LEFT JOIN
                 matched rows   → unicodeTrLit, syllabarySign, PhoneticsVersion filled
                 unmatched rows → those 3 fields = '' (NULL)

             Why LEFT JOIN:
               allograph_all is the primary dataset — every allograph record
               must be preserved, including Type_3 inherited UIDs and Type_2
               component rows not present in the Unicode standard table.
               NULL in TrLit fields = informative: allograph without verified
               phonetics in the Unicode standard.

             Column order (14 columns — v5 base + 3 TrLit):
               1.  unicode_id
               2.  allograph_sign
               3.  allograph_form
               4.  allograph_ucun
               5.  allograph_type
               6.  graphic_variant_id        ← from v5
               7.  compound_form
               8.  component_position
               9.  allographCompound_cun
               10. allographCompound_useq
               11. unicodeTrLit              ← from 6_unicodeTrLit_Grph_Phon.csv
               12. syllabarySign             ← from 6_unicodeTrLit_Grph_Phon.csv
               13. PhoneticsVersion          ← from 6_unicodeTrLit_Grph_Phon.csv
               14. signList_analogue

             Pipeline position:
               STEP 1 → extract_allograph_all_v5.py  → allograph_all.csv
               STEP 2 → extract_allographByType.py    → allographType_1/2/3.csv
               STEP 3 → THIS FILE                     → 3_joinAllograph_Omograph.csv
               STEP 4 → transferTrLit_Sign.py          reads join file as syllabary
               STEP 5 → txt_to_grapheme.py             → grapheme.csv

Author: Digital Humanities Pipeline
Date: 2026-04-24
Version: 2.0
"""

import csv
import os

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
INPUT_LEFT  = os.path.join(ROOT_DIR, "2.allograph_all_v5.csv")          # from v5
INPUT_RIGHT = os.path.join(ROOT_DIR, "6.unicodeTrLit_Grph_Phon.csv")
OUTPUT_CSV  = os.path.join(ROOT_DIR, "3_joinAllograph_Omograph.csv")

# Column order: v5 canonical structure + 3 TrLit fields before signList_analogue
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
# LOADERS
# ─────────────────────────────────────────────────────────────────────────────

def load_allograph(filepath: str) -> list:
    """
    Load allograph_all.csv (output of extract_allograph_all_v5.py).
    Returns list of row dicts — all 2535 rows preserved.
    Expected columns include graphic_variant_id from v5.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"[ERROR] allograph_all.csv not found: {filepath}\n"
                                f"        Run extract_allograph_all_v5.py first.")
    with open(filepath, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # Verify graphic_variant_id is present (v5 output check)
    if rows and "graphic_variant_id" not in rows[0]:
        raise ValueError("[ERROR] graphic_variant_id column missing.\n"
                         "        Input must be from extract_allograph_all_v5.py, not v4.")
    return rows


def load_trlit_lookup(filepath: str) -> dict:
    """
    Load 6_unicodeTrLit_Grph_Phon.csv into a lookup dict:
      { unicode_id → {unicodeTrLit, syllabarySign, PhoneticsVersion} }

    unicode_id is unique in this file (0 duplicates verified),
    so a plain dict is safe — no collision handling needed.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"[ERROR] TrLit file not found: {filepath}")
    lookup = {}
    with open(filepath, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            uid = row.get("unicode_id", "").strip()
            if uid:
                lookup[uid] = {
                    "unicodeTrLit":     row.get("unicodeTrLit",     "").strip(),
                    "syllabarySign":    row.get("syllabarySign",    "").strip(),
                    "PhoneticsVersion": row.get("PhoneticsVersion", "").strip(),
                }
    return lookup


# ─────────────────────────────────────────────────────────────────────────────
# JOIN
# ─────────────────────────────────────────────────────────────────────────────

def left_join(allograph_rows: list, trlit_lookup: dict) -> list:
    """
    LEFT JOIN allograph_all rows with TrLit lookup on unicode_id.

    For each allograph row:
      - uid found in trlit_lookup  → attach unicodeTrLit, syllabarySign,
                                     PhoneticsVersion
      - uid not found              → those 3 fields = '' (NULL equivalent)

    graphic_variant_id is passed through unchanged from allograph_all (v5).
    Column order follows FIELDNAMES — v5 structure with TrLit columns at 11–13.
    """
    result_rows = []
    matched = unmatched = 0

    for row in allograph_rows:
        uid = row.get("unicode_id", "").strip()

        trlit = trlit_lookup.get(uid)
        if trlit:
            matched += 1
        else:
            unmatched += 1
            trlit = {"unicodeTrLit": "", "syllabarySign": "", "PhoneticsVersion": ""}

        result_rows.append({
            # ── from allograph_all (v5 column order) ──────────────────────────
            "unicode_id":             uid,
            "allograph_sign":         row.get("allograph_sign",         ""),
            "allograph_form":         row.get("allograph_form",         ""),
            "allograph_ucun":         row.get("allograph_ucun",         ""),
            "allograph_type":         row.get("allograph_type",         ""),
            "graphic_variant_id":     row.get("graphic_variant_id",     ""),  # v5
            "compound_form":          row.get("compound_form",          ""),
            "component_position":     row.get("component_position",     ""),
            "allographCompound_cun":  row.get("allographCompound_cun",  ""),
            "allographCompound_useq": row.get("allographCompound_useq", ""),
            # ── from 6_unicodeTrLit_Grph_Phon.csv (NULL if no match) ─────────
            "unicodeTrLit":           trlit["unicodeTrLit"],
            "syllabarySign":          trlit["syllabarySign"],
            "PhoneticsVersion":       trlit["PhoneticsVersion"],
            # ── back to allograph_all ─────────────────────────────────────────
            "signList_analogue":      row.get("signList_analogue",      ""),
        })

    return result_rows, matched, unmatched


# ─────────────────────────────────────────────────────────────────────────────
# STATS REPORT
# ─────────────────────────────────────────────────────────────────────────────

def print_stats(result_rows: list, matched: int, unmatched: int):
    """Print join statistics broken down by allograph type."""
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
    print(f"  {'type':<10} {'with TrLit':>12} {'without TrLit':>14}")
    print(f"  {'-'*40}")
    for t in ["Type_1", "Type_2", "Type_3"]:
        with_    = type_stats.get((t, True),  0)
        without_ = type_stats.get((t, False), 0)
        print(f"  {t:<10} {with_:>12} {without_:>14}")

    # Breakdown by graphic_variant_id pattern
    print()
    compound_rows = sum(1 for r in result_rows if r["graphic_variant_id"] == "compound")
    v1_rows       = sum(1 for r in result_rows if r["graphic_variant_id"].endswith("_v1"))
    v2plus_rows   = sum(1 for r in result_rows
                        if "_v" in r["graphic_variant_id"]
                        and not r["graphic_variant_id"].endswith("_v1"))
    print(f"  graphic_variant_id summary:")
    print(f"    _v1 (canonical variant)  : {v1_rows}")
    print(f"    _v2+ (additional variants): {v2plus_rows}")
    print(f"    compound                  : {compound_rows}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Load ─────────────────────────────────────────────────────────────────
    print(f"[INFO] Loading base (left)  : {INPUT_LEFT}")
    allograph_rows = load_allograph(INPUT_LEFT)
    print(f"[INFO] Rows in allograph_all: {len(allograph_rows)}")

    print(f"[INFO] Loading enrichment   : {INPUT_RIGHT}")
    trlit_lookup = load_trlit_lookup(INPUT_RIGHT)
    print(f"[INFO] Rows in TrLit lookup : {len(trlit_lookup)}")

    # ── Join ─────────────────────────────────────────────────────────────────
    result_rows, matched, unmatched = left_join(allograph_rows, trlit_lookup)

    # ── Stats ─────────────────────────────────────────────────────────────────
    print_stats(result_rows, matched, unmatched)

    # ── Write ─────────────────────────────────────────────────────────────────
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result_rows)

    print(f"\n[OK] {len(result_rows)} rows → {OUTPUT_CSV}")
    print("[DONE]")


if __name__ == "__main__":
    main()
