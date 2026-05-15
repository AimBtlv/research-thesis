#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: extract_allographType_3.py
Description: Extract Type_3 allographs from allograph_all.csv and produce
             allographType_3.csv.

             Type_3 definition:
               Text-name-only allograph. No Unicode code point, no glyph,
               no @useq sequence. Only the form name from an analogue paper
               character list (e.g. LAK797, BU, |IGI.A|).
               Source in osl.asl: @form name only, no @list U+, no @useq.

             unicode_id and allograph_ucun:
               Since Type_3 has no own Unicode, both fields are INHERITED
               from the root @sign (the parent sign block in osl.asl).
               Rationale: the allograph differs only graphically — it is
               a variant form of the same sign, which does have a Unicode.
               60 cases exist where the root @sign itself has no Unicode
               (e.g. compound signs like |A.HA.TAR.DU|) — these rows
               will have empty unicode_id and allograph_ucun.

             Output columns (allographType_3.csv):
               1. unicode_id        — inherited from root @sign (U+xxxx)
               2. allograph_sign    — root @sign (scientific name)
               3. allograph_form    — @form value (analogue name, e.g. LAK797)
               4. allograph_ucun    — inherited from root @sign @ucun glyph
               5. signList_analogue — analogue paper catalogue refs (annotated)

             Pipeline position:
               STEP 1 → extract_allograph_all_v4.py  produces allograph_all.csv
               STEP 2a→ extract_allographType_1.py   produces allographType_1.csv
               STEP 2b→ extract_allographType_2.py   produces allographType_2.csv
               STEP 2c→ THIS FILE                    produces allographType_3.csv

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
OUTPUT_CSV = os.path.join(ROOT_DIR, "allographType_3.csv")

# Column order as defined in csvColumns_v2.docx
FIELDNAMES = [
    "unicode_id",        # inherited from root @sign (empty if root has no Unicode)
    "allograph_sign",    # root @sign scientific name
    "allograph_form",    # @form value — analogue name (e.g. LAK797, BU, |IGI.A|)
    "allograph_ucun",    # inherited from root @sign @ucun glyph
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

    # ── Filter Type_3 ─────────────────────────────────────────────────────────
    type3_rows = [r for r in all_rows if r["allograph_type"] == "Type_3"]
    print(f"[INFO] Type_3 rows selected: {len(type3_rows)}")

    # Stats: how many have inherited unicode vs empty
    with_uid    = sum(1 for r in type3_rows if r["unicode_id"])
    without_uid = len(type3_rows) - with_uid
    print(f"[INFO]   with inherited unicode_id : {with_uid}")
    print(f"[INFO]   without unicode_id (root @sign has none): {without_uid}")

    # ── Write output CSV ──────────────────────────────────────────────────────
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(type3_rows)

    print(f"[OK]  {len(type3_rows)} rows → {OUTPUT_CSV}")
    print("[DONE]")


if __name__ == "__main__":
    main()
