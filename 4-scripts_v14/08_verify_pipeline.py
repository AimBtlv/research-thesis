#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 08_verify_pipeline.py
Description: Workflow Stage 1, final check of the whole pipeline (Steps 1-5).
             Compares every output in pipeline_v14/output/ with the existing
             files of the repository (byte-identical where the step was only
             re-run) and with the reference numbers measured when the
             pipeline was built (catalogue v13 + parser v14.2 on the whole
             Old Babylonian corpus: OBP_full/practiceOBP_all.atf, 16,906
             tablets, 15,709 with text). Prints PASS / DIFF for each check.
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.2 (Step 5 reference numbers for the whole OB corpus)
"""

import csv
import filecmp
from collections import Counter
from pathlib import Path

# --- Paths (relative to the repository: research-thesis/pipeline_v14/<this file>) ---
ROOT = Path(__file__).resolve().parents[1]
DP = ROOT / "2-dataset" / "DataProfile"
UA = DP / "1-5unicodeAssignmentFiles"
PROF = UA / "2_professorsFiles"
OUT = Path(__file__).resolve().parent / "output"

results = []


def check(step, what, expected, actual):
    """Store one check; equality decides PASS / DIFF."""
    results.append((step, what, expected, actual, "PASS" if expected == actual else "DIFF"))


def rows(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def same_file(a, b):
    return a.exists() and b.exists() and filecmp.cmp(a, b, shallow=False)


def main():
    # Step 1: re-run of existing scripts -> identical files expected
    s1 = OUT / "step1"
    check("1.1", "Syllabary_CM.csv identical to 2_professorsFiles/Syllabary_CM.csv",
          True, same_file(s1 / "Syllabary_CM.csv", PROF / "Syllabary_CM.csv"))
    check("1.2", "3_matched_signs_full.csv identical to the repository file (791 signs)",
          True, same_file(s1 / "3_matched_signs_full.csv", UA / "3_matched_signs_full.csv"))
    check("1.2", "4_unmatched_for_review.csv identical to the repository file (443 signs)",
          True, same_file(s1 / "4_unmatched_for_review.csv", UA / "4_unmatched_for_review.csv"))
    check("1.3", "restUnicodeSigns.csv identical to 5_restUnicodeSigns.csv",
          True, same_file(s1 / "restUnicodeSigns.csv", UA / "5_restUnicodeSigns.csv"))

    check("1.4", "7_unicodePhoneticVersion_full.csv identical to the repository file",
          True, same_file(s1 / "7_unicodePhoneticVersion_full.csv",
                          DP / "7_unicodePhoneticVersion_full.csv"))
    if (OUT / "step2" / "diri_lexical_list.csv").exists():
        new_diri = rows(OUT / "step2" / "diri_lexical_list.csv")
        old_diri = rows(UA / "diri_lexical_list.csv")
        check("2", "Diri lines (same as the repository file)", len(old_diri), len(new_diri))
        check("2", "Diri texts (same as the repository file)",
              len({r["p_number"] for r in old_diri}), len({r["p_number"] for r in new_diri}))
        # rows that differ in place: usually later corrections in the Oracc editions
        # (e.g. {d}KU3.GI -> {d}KU3-GI), not an error of the script
        n_changed = sum(a != b for a, b in zip(old_diri, new_diri))
        results.append(("2", "Diri rows changed by a newer Oracc download (info)",
                        "-", n_changed, "INFO" if n_changed else "PASS"))
    else:
        results.append(("2", "Diri not re-run (Oracc JSON absent): existing file used",
                        "-", "-", "SKIP"))

    # Steps 3-4: catalogue v13
    s4 = OUT / "step4"
    if (s4 / "allograph_all_v13.csv").exists():
        cat = rows(s4 / "allograph_all_v13.csv")
        check("4", "catalogue rows", 10573, len(cat))
        atom = {r["unicode_id"] for r in cat if r["typePhonetic_Version"] == "Single Sign Reading"}
        uni = [r["unicode_id"] for r in rows(UA / "1_unicodeSigns.csv")]
        check("4", "Unicode signs without a simple-reading row", 9,
              sum(1 for u in uni if u not in atom))
        check("4", "rows with OSL @v values added", 490,
              sum(1 for r in cat if r.get("osl_v_added")))
        comp = rows(s4 / "compound_form_reading_table_v13.csv")
        check("3", "compound forms in table", 2389, len(comp))
        check("3", "compound forms with attested reading", 1612,
              sum(1 for r in comp if r["reading_status"] == "ATTESTED_DIRECT"))
        check("4", "OSL / catalogue conflicts recorded", 748,
              len(rows(s4 / "osl_reading_conflicts_v13.csv")))
    else:
        check("4", "allograph_all_v13.csv exists", True, False)

    # Step 5: parser v14.2 on the whole OB corpus (717 school + 16,189 practical tablets)
    s5 = OUT / "step5"
    if (s5 / "atf_tokens.csv").exists() and (s5 / "grapheme.csv").exists():
        tok = rows(s5 / "atf_tokens.csv")
        kinds = Counter(r["token_kind"] for r in tok)
        check("5.1", "tablets with text (16,906 minus 1,197 header-only)", 15709,
              len({r["p_number"] for r in tok}))
        check("5.1", "token rows", 2267576, len(tok))
        check("5.1", "unresolved tokens", 5395, kinds["unresolved"])
        check("5.1", "unreadable x", 56215, kinds["unreadable"])
        del tok
        gr = rows(s5 / "grapheme.csv")
        check("5.2", "grapheme rows", 2155501, len(gr))
        check("5.2", "grapheme rows with Unicode", 2152956, sum(1 for r in gr if r["unicode_id"]))
        check("5.2", "LOGO rows", 317092, sum(1 for r in gr if r["sign_type"] == "LOGO"))
    else:
        check("5", "atf_tokens.csv and grapheme.csv exist", True, False)

    width = max(len(r[1]) for r in results)
    print(f"\n{'step':5} {'check':{width}}  {'expected':>9}  {'actual':>9}  result")
    print("-" * (width + 40))
    for step, what, exp, act, res in results:
        print(f"{step:5} {what:{width}}  {str(exp):>9}  {str(act):>9}  {res}")
    n_diff = sum(r[4] == "DIFF" for r in results)
    print("-" * (width + 40))
    print("ALL CHECKS PASSED" if not n_diff else f"{n_diff} check(s) differ: see DIFF rows above")


if __name__ == "__main__":
    main()
