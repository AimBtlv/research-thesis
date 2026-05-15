#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: extract_allographType_1.py
Description: Extract Type_1 allographs from allograph_all.csv and produce
             allographType_1.csv.

             Type_1 definition:
               Allograph has its own Unicode code point.
               Source in osl.asl: @form -> @list U+xxxx

             Output columns (allographType_1.csv):
               1. unicode_id        — @form -> @list U+ (own Unicode code point)
               2. allograph_sign    — root @sign (scientific name)
               3. allograph_form    — @form transliteration value
               4. allograph_ucun    — @form -> @ucun glyph
               5. signList_analogue — analogue paper catalogue refs (annotated)

             Pipeline position:
               STEP 1 → extract_allograph_all_v4.py  produces allograph_all.csv
               STEP 2a→ THIS FILE                    produces allographType_1.csv
               STEP 2b→ extract_allographType_2.py   produces allographType_2.csv
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
OUTPUT_CSV = os.path.join(ROOT_DIR, "allographType_1.csv")

# Column order as defined in csvColumns_v2.docx
FIELDNAMES = [
    "unicode_id",        # @form -> @list U+xxxx (own Unicode code point)
    "allograph_sign",    # root @sign scientific name
    "allograph_form",    # @form transliteration
    "allograph_ucun",    # @form -> @ucun glyph
    "signList_analogue", # analogue paper catalogue refs (annotated with period/region)
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

    # ── Filter Type_1 ─────────────────────────────────────────────────────────
    type1_rows = [r for r in all_rows if r["allograph_type"] == "Type_1"]
    print(f"[INFO] Type_1 rows selected: {len(type1_rows)}")

    # ── Write output CSV ──────────────────────────────────────────────────────
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(type1_rows)

    print(f"[OK]  {len(type1_rows)} rows → {OUTPUT_CSV}")
    print("[DONE]")


if __name__ == "__main__":
    main()
