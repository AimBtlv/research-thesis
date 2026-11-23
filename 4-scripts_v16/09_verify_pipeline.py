#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 09_verify_pipeline.py
Description: Workflow Stage 1, final check of the whole pipeline (Steps 1-5).
             Compares every output in <scripts folder>/output/ with the files
             of the repository (byte-identical where a step only re-runs an
             existing script) and with the reference numbers of the last
             checked run (catalogue v13.2 + parser v14.4 + grapheme v14.5 on
             the whole Old Babylonian corpus: OBP_full/practiceOBP_all.atf,
             16,906 tablets, 15,709 with text). Prints PASS / DIFF / INFO /
             SKIP for each check.
             The big files (atf_tokens.csv, grapheme.csv) are read row by row
             and counted on the fly, they are never loaded into memory as a
             whole: this keeps the check fast and light.
             The Diri check knows two special cases: the reference list is
             looked for in DataProfile/step2 first and then in DataProfile/
             step1, and a run of Step 05 that stopped with an incomplete
             Oracc download (diri_lexical_list_PARTIAL.csv) is reported as
             DIFF with an explanation.
Author: Aima, prepared with Claude
Date: 2026-11-22
Version: 2.0
"""

import csv
import filecmp
from collections import Counter
from pathlib import Path

# CONFIGURATION
# --- Paths (relative to the repository: research-thesis/<scripts folder>/<this file>) ---
ROOT = Path(__file__).resolve().parents[1]
DP = ROOT / "2-dataset" / "DataProfile"
UA = DP / "step1"                       # inputs of Steps 1-4
STEP2_IN = DP / "step2"                 # inputs of Step 2 (Diri, OGSL)
PROF = UA / "2_professorsFiles"
OUT = Path(__file__).resolve().parent / "output"

# --- Reference numbers of the last checked run ---
# Change them ONLY after a run whose differences were checked and explained
# (see the WorkFlowDocumentations). Steps 1-3 and 5: run of 22.11.2026.
# Step 4: catalogue 06 v13.2 (the forms |ZI&ZI| and |GU₂×IGI@g| keep their
# own readings: 2 more rows with OSL @v, 4 conflicts fewer). Values marked
# "to confirm" may move slightly with 06 v13.2 (numun₂, gug₄, šub₅ are again
# compounds: about 160 tokens).
REFERENCE = {
    # Step 1
    "matched_syllabary": 779,
    "left_for_osl": 455,
    "syllabary_osl_disagree": 18,
    "described_from_osl": 455,
    "osl_without_name": 19,
    "unicode_full": 1234,
    "unicode_with_reading": 1035,
    # Steps 3-4
    "catalogue_rows": 10563,
    "unicode_without_simple_row": 9,
    "rows_osl_v_added": 479,
    "compound_forms": 2380,
    "compound_attested": 1604,
    "osl_conflicts": 701,
    "same_name_form_rows": 16,          # P02: forms that take the code of a same-name @sign
    # Step 5.1
    "tablets_with_text": 15709,
    "token_rows": 2267828,
    "tokens_compound": 81150,           # to confirm
    "tokens_atomic": 1985845,           # to confirm
    "tokens_unresolved": 3465,          # to confirm (ginₓ may now be read as DUN₃)
    "tokens_unreadable": 56215,
    # Step 5.2
    "grapheme_rows": 2156055,           # to confirm
    "grapheme_with_unicode": 2153364,   # to confirm
    "grapheme_logo": 662336,            # to confirm
    "grapheme_no_function": 1853,
    "grapheme_fallback": 26474,
}

# readings that belong to the compounds |ZI&ZI.LAGAB| / |ZI&ZI.EŠ₂| and must
# never appear on a simple-sign row of the form |ZI&ZI| (regression of v13.1)
ZI_GUARD = {"numun₂", "gug₄", "šub₅"}

results = []


def check(step, what, expected, actual):
    """Store one check; equality decides PASS / DIFF."""
    results.append((step, what, expected, actual, "PASS" if expected == actual else "DIFF"))


def info(step, what, actual, status="INFO"):
    """Store a line that is reported but not compared."""
    results.append((step, what, "-", actual, status))


def iter_rows(path):
    """Yield the rows of a CSV one by one (no full load into memory)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


def count_rows(path):
    return sum(1 for _ in iter_rows(path))


def same_file(a, b):
    return a.exists() and b.exists() and filecmp.cmp(a, b, shallow=False)


def first_existing(*paths):
    for p in paths:
        if p.exists():
            return p
    return None


def check_step1():
    s1 = OUT / "step1"
    check("1.1", "Syllabary_CM.csv identical to 2_professorsFiles/Syllabary_CM.csv",
          True, same_file(s1 / "Syllabary_CM.csv", PROF / "Syllabary_CM.csv"))
    check("1.2", "signs matched to the syllabary",
          REFERENCE["matched_syllabary"], count_rows(s1 / "3_matched_signs_full.csv"))
    check("1.2", "signs left for OSL (Step 1.3)",
          REFERENCE["left_for_osl"], count_rows(s1 / "4_unmatched_for_review.csv"))
    check("1.2", "signs where syllabary and OSL disagree (review file)",
          REFERENCE["syllabary_osl_disagree"],
          count_rows(s1 / "step1_syllabary_osl_disagreements.csv"))
    n_rest = n_rest_noname = 0
    for r in iter_rows(s1 / "restUnicodeSigns.csv"):
        n_rest += 1
        n_rest_noname += not r["syllabarySign"]
    check("1.3", "signs described from OSL", REFERENCE["described_from_osl"], n_rest)
    check("1.3", "of them without a sign name in OSL", REFERENCE["osl_without_name"], n_rest_noname)
    n_full = n_read = 0
    for r in iter_rows(s1 / "7_unicodePhoneticVersion_full.csv"):
        n_full += 1
        n_read += bool(r["PhoneticsVersion"])
    check("1.4", "Unicode signs in the full list", REFERENCE["unicode_full"], n_full)
    check("1.4", "signs with at least one reading", REFERENCE["unicode_with_reading"], n_read)


def check_step2():
    new_path = OUT / "step2" / "diri_lexical_list.csv"
    partial = OUT / "step2" / "diri_lexical_list_PARTIAL.csv"
    ref_path = first_existing(STEP2_IN / "diri_lexical_list.csv", UA / "diri_lexical_list.csv")

    if partial.exists() and not new_path.exists():
        # Step 05 found fewer lines than the reference and refused to overwrite it
        results.append(("2", "Diri re-run INCOMPLETE (Oracc download partial): "
                             "see output/step2/diri_lexical_list_PARTIAL.csv",
                        count_rows(ref_path) if ref_path else "-",
                        count_rows(partial), "DIFF"))
        return
    if not new_path.exists():
        info("2", "Diri not re-run (Oracc JSON absent): existing file used", "-", "SKIP")
        return
    if ref_path is None:
        info("2", "Diri reference file not found in DataProfile/step2 or step1", "-", "SKIP")
        return

    new_diri = list(iter_rows(new_path))      # small file (about 4,000 rows)
    old_diri = list(iter_rows(ref_path))
    where = ref_path.parent.name
    check("2", f"Diri lines (same as {where}/diri_lexical_list.csv)", len(old_diri), len(new_diri))
    check("2", f"Diri texts (same as {where}/diri_lexical_list.csv)",
          len({r["p_number"] for r in old_diri}), len({r["p_number"] for r in new_diri}))
    # rows that differ in place: usually later corrections in the Oracc editions
    # (e.g. {d}KU3.GI -> {d}KU3-GI), not an error of the script
    n_changed = sum(a != b for a, b in zip(old_diri, new_diri))
    info("2", "Diri rows changed by a newer Oracc download (info)", n_changed,
         "INFO" if n_changed else "PASS")


def check_steps3_4():
    s4 = OUT / "step4"
    cat_path = s4 / "sign_catalogue_v13.csv"
    if not cat_path.exists():
        check("4", "sign_catalogue_v13.csv exists", True, False)
        return

    n_cat = n_added = n_same_name = 0
    atom = set()
    zi_leak = 0
    for r in iter_rows(cat_path):
        n_cat += 1
        n_added += bool(r.get("osl_v_added"))
        n_same_name += r.get("structural_hint") == "uid_via_same_name_sign"
        if r["typePhonetic_Version"] == "Single Sign Reading":
            atom.add(r["unicode_id"])
            if r.get("osl_form") == "|ZI&ZI|":
                values = {v.strip() for v in r["phonetic_version"].split("|")}
                zi_leak += bool(values & ZI_GUARD)
    uni = [r["unicode_id"] for r in iter_rows(UA / "1_unicodeSigns.csv")]

    check("4", "catalogue rows", REFERENCE["catalogue_rows"], n_cat)
    check("4", "Unicode signs without a simple-reading row",
          REFERENCE["unicode_without_simple_row"], sum(1 for u in uni if u not in atom))
    check("4", "rows with OSL @v values added", REFERENCE["rows_osl_v_added"], n_added)
    check("4", "forms with the code of a same-name @sign (P02)",
          REFERENCE["same_name_form_rows"], n_same_name)
    check("4", "|ZI&ZI| rows with readings of the parent compound (must be 0)", 0, zi_leak)

    n_comp = n_att = 0
    for r in iter_rows(s4 / "compound_form_reading_table_v13.csv"):
        n_comp += 1
        n_att += r["reading_status"] == "ATTESTED_DIRECT"
    check("3", "compound forms in table", REFERENCE["compound_forms"], n_comp)
    check("3", "compound forms with attested reading", REFERENCE["compound_attested"], n_att)
    check("4", "OSL / catalogue conflicts recorded", REFERENCE["osl_conflicts"],
          count_rows(s4 / "osl_reading_conflicts_v13.csv"))


def check_step5():
    s5 = OUT / "step5"
    tok_path, gr_path = s5 / "atf_tokens.csv", s5 / "grapheme.csv"
    if not (tok_path.exists() and gr_path.exists()):
        check("5", "atf_tokens.csv and grapheme.csv exist", True, False)
        return

    # Step 5.1: one pass over atf_tokens.csv
    n_tok, kinds, tablets = 0, Counter(), set()
    for r in iter_rows(tok_path):
        n_tok += 1
        kinds[r["token_kind"]] += 1
        tablets.add(r["p_number"])
    check("5.1", "tablets with text (16,906 minus 1,197 header-only)",
          REFERENCE["tablets_with_text"], len(tablets))
    check("5.1", "token rows", REFERENCE["token_rows"], n_tok)
    check("5.1", "compound tokens", REFERENCE["tokens_compound"], kinds["compound"])
    check("5.1", "atomic tokens", REFERENCE["tokens_atomic"], kinds["atomic"])
    check("5.1", "unresolved tokens", REFERENCE["tokens_unresolved"], kinds["unresolved"])
    check("5.1", "unreadable x", REFERENCE["tokens_unreadable"], kinds["unreadable"])

    # Step 5.2: one pass over grapheme.csv
    n_gr = n_uid = n_logo = n_nofunc = n_fallback = 0
    for r in iter_rows(gr_path):
        n_gr += 1
        n_uid += bool(r["unicode_id"])
        n_logo += r["sign_type"] == "LOGO"
        n_nofunc += not r["sign_function"]
        n_fallback += r["function_rule"] == "fallback:letter_case"
    check("5.2", "grapheme rows", REFERENCE["grapheme_rows"], n_gr)
    check("5.2", "grapheme rows with Unicode", REFERENCE["grapheme_with_unicode"], n_uid)
    check("5.2", "LOGO rows (sign_type, by language and context)", REFERENCE["grapheme_logo"], n_logo)
    check("5.2", "rows without sign_function (no rule and no letter)",
          REFERENCE["grapheme_no_function"], n_nofunc)
    check("5.2", "rows labelled by the letter-case fallback", REFERENCE["grapheme_fallback"], n_fallback)


def report():
    width = max(len(r[1]) for r in results)
    print(f"\n{'step':5} {'check':{width}}  {'expected':>9}  {'actual':>9}  result")
    print("-" * (width + 40))
    for step, what, exp, act, res in results:
        print(f"{step:5} {what:{width}}  {str(exp):>9}  {str(act):>9}  {res}")
    n_diff = sum(r[4] == "DIFF" for r in results)
    print("-" * (width + 40))
    print("ALL CHECKS PASSED" if not n_diff else f"{n_diff} check(s) differ: see DIFF rows above")


def main():
    check_step1()
    check_step2()
    check_steps3_4()
    check_step5()
    report()


if __name__ == "__main__":
    main()
