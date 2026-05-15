#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: extract_allographType_2.py
Description: Extract Type_2 allographs from allograph_all.csv and produce
             allographType_2.csv.

             Type_2 definition:
               Compound allograph — rendered via @useq (sequence of Unicode
               characters) and @ucun (visual glyph), but has NO single own
               Unicode code point (@form does NOT have @list U+).
               Source in osl.asl: @form -> @useq + @ucun

             Row structure (exploded):
               Each compound @form is split into one row per component U+.
               All rows of the same compound share the same compound_form,
               allographCompound_cun, and allographCompound_useq values.
               component_position tracks the order within the compound.

             Output columns (allographType_2.csv):
               1. unicode_id             — component U+ (one row per component)
               2. allograph_sign         — root @sign (scientific name)
               3. compound_form          — original @form name of the compound
               4. component_position     — 1-based position within compound
               5. allograph_ucun         — glyph of THIS component only
               6. allographCompound_cun  — full compound glyph (@ucun of @form)
               7. allographCompound_useq — full U+ sequence of compound
               8. signList_analogue      — analogue paper catalogue refs (annotated)

             Pipeline position:
               STEP 1 → extract_allograph_all_v4.py  produces allograph_all.csv
               STEP 2a→ extract_allographType_1.py   produces allographType_1.csv
               STEP 2b→ THIS FILE                    produces allographType_2.csv
               STEP 2c→ extract_allographType_3.py   produces allographType_3.csv

Author: Digital Humanities Pipeline
Date: 2026-04-24
Version: 1.0
"""

import csv
import os

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

ROOT_DIR   = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV  = os.path.join(ROOT_DIR, "allograph_all.csv")   # master file (from Step 1)
OUTPUT_CSV = os.path.join(ROOT_DIR, "allographType_2.csv")

# Column order as defined in csvColumns_v2.docx
FIELDNAMES = [
    "unicode_id",             # component U+ (one per row, exploded from @useq)
    "allograph_sign",         # root @sign scientific name
    "compound_form",          # original @form name of the compound (e.g. |A.EDIN|)
    "component_position",     # 1-based position of this component within the compound
    "allograph_ucun",         # glyph of THIS component (looked up from unicode_ref)
    "allographCompound_cun",  # full compound glyph (from @ucun of @form block)
    "allographCompound_useq", # full U+ sequence (all components, semicolon-separated)
    "signList_analogue",      # analogue paper catalogue refs (annotated with period/region)
]

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Read master CSV ───────────────────────────────────────────────────────
    print(f"[INFO] Reading master: {INPUT_CSV}")
    with open(INPUT_CSV, encoding="utf-8-sig") as f:
        all_rows = list(csv.DictReader(f))
    print(f"[INFO] Total rows in master: {len(all_rows)}")

    # ── Filter Type_2 ─────────────────────────────────────────────────────────
    type2_rows = [r for r in all_rows if r["allograph_type"] == "Type_2"]
    print(f"[INFO] Type_2 rows selected: {len(type2_rows)} "
          f"(exploded — one row per component U+)")

    # Count unique compounds for reference
    unique_compounds = len({r["compound_form"] for r in type2_rows})
    print(f"[INFO] Unique compound @forms: {unique_compounds}")

    # ── Write output CSV ──────────────────────────────────────────────────────
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(type2_rows)

    print(f"[OK]  {len(type2_rows)} rows → {OUTPUT_CSV}")
    print("[DONE]")


if __name__ == "__main__":
    main()
