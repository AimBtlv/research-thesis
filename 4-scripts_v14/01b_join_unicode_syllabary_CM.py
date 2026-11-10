#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 01b_join_unicode_syllabary_CM.py
Description: Workflow Stage 1, Step 1.2. Restoration of the empty script
             2_scriptJoinUnicode_SyllabaryCM.py from its last working version
             (chat "Производитель языка Perl", March 2026).
             Joins the 1,234 Unicode cuneiform signs (1_unicodeSigns.csv)
             with the professor's syllabaries (syllabary_CM.txt,
             additional_signs.txt, syllabary_uruk2.txt):
               - the Unicode name of every sign is normalised
                 (subscripts -> digits, x -> X, GUNU -> @G, TENU -> @T,
                 SH -> Š, THREE -> X3, DAG KISIM5 -> DAG.KISIM5, ...);
               - the same normalisation is applied to every sign name and
                 every reading of the syllabaries;
               - a sign is matched first by sign name, then by reading;
               - all readings of the matched sign go to PhoneticsVersion.
             Outputs: 3_matched_signs_full.csv (791 signs) and
             4_unmatched_for_review.csv (443 signs, input of Step 1.3).

"""

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

# --- Paths (relative to the repository: research-thesis/pipeline_v14/<this file>) ---
ROOT = Path(__file__).resolve().parents[1]
UA = ROOT / "2-dataset" / "DataProfile" / "1-5unicodeAssignmentFiles"
PROF = UA / "2_professorsFiles"
OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "step1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

UNICODE_CSV = UA / "1_unicodeSigns.csv"
# (file, uruk_preprocessing) in the original reading order: order matters,
# because the first sign name / reading found wins in the indexes
SYLLABARIES = [
    (PROF / "syllabary_CM.txt", False),
    (PROF / "additional_signs.txt", False),
    (PROF / "syllabary_uruk2.txt", True),
]
MATCHED_CSV = OUTPUT_DIR / "3_matched_signs_full.csv"
UNMATCHED_CSV = OUTPUT_DIR / "4_unmatched_for_review.csv"


def deep_normalize(s):
    """Normalise a Unicode-derived sign name (or a syllabary entry)
    to one comparable form. The order of the rules matters."""
    s = s.upper()
    # 1. subscripts first, before any letter substitution
    s = s.translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
    # 2. multiplication sign
    s = s.replace("×", "X")
    # 3. modifier words of the Unicode names
    s = re.sub(r"\s*GUNU3?", "@G", s)
    s = re.sub(r"\s*TENU", "@T", s)
    # 4. English SH spelling of the Unicode names -> Š (as in the syllabary)
    s = re.sub(r"SHESH", "ŠEŠ", s)
    s = re.sub(r"SHITA", "ŠITA", s)
    s = re.sub(r"SHA", "ŠA", s)
    s = re.sub(r"SHE", "ŠE", s)
    s = re.sub(r"SHI", "ŠI", s)
    s = re.sub(r"SHU", "ŠU", s)
    s = re.sub(r"MUSH", "MUŠ", s)
    s = re.sub(r"GISH", "GIŠ", s)
    s = re.sub(r"ASH", "AŠ", s)       # no word boundary: also ASH2, ASHGAB
    s = re.sub(r"USH", "UŠ", s)
    s = re.sub(r"ESH", "EŠ", s)
    s = re.sub(r"ANSHE", "ANŠE", s)
    # 5. THREE patterns, before spaces are removed
    s = re.sub(r"(\w+)\s*THREE\s*X?", r"\1X3", s)
    s = re.sub(r"^THREE\s*(\w+)", r"3X\1", s)
    # 6. purely descriptive parts of the Unicode names
    s = re.sub(r"(\w+)/(\w+)", r"\1/\2", s)   # stacked signs kept as they are
    s = re.sub(r"OPPOSING.*", "", s)
    s = re.sub(r"SQUARED", "", s)
    # 7. dots the syllabary writes inside compound names
    s = re.sub(r"DAG\s*KISIM5", "DAG.KISIM5", s)
    s = re.sub(r"NUNUZ\s*([A-ZŠĜŢṬṢ])", r"NUNUZ.\1", s)
    # 8. spaces around operators, then all remaining spaces
    s = re.sub(r"\s*X\s*", "X", s)
    s = re.sub(r"\s*\+\s*", "+", s)
    s = re.sub(r"\s+", "", s)
    return s


def normalize_uruk_line(line):
    """Preprocessing of syllabary_uruk2.txt (ported from the Perl script)."""
    line = re.sub(r"\?", "", line)
    line = re.sub(r"\|", "", line)
    line = line.replace(".", "+")
    line = re.sub(r"[()]", "", line)
    return line


def load_syllabaries():
    """sign name -> list of all its readings, in file order."""
    sign_to_keys = defaultdict(list)
    for path, preproc in SYLLABARIES:
        if not path.exists():
            sys.exit(f"[ERROR] missing syllabary: {path}")
        with open(path, encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                if preproc:
                    line = normalize_uruk_line(line)
                line = re.sub(r"\?", "", line)
                parts = re.split(r"\s+", line)
                if not parts[0]:
                    continue
                key = parts[0]
                name = parts[1] if len(parts) >= 2 else parts[0]
                if key not in sign_to_keys[name]:
                    sign_to_keys[name].append(key)

    # add x / + variants of compound readings (Perl step).
    # Note: the second pattern replaces x with x, so it adds nothing;
    # it is kept to reproduce the original behaviour exactly.
    for name, keys in list(sign_to_keys.items()):
        extras = []
        for k in keys:
            if re.search(r"(\w)\+(\w)", k):
                nk = re.sub(r"(\w)\+(\w)", r"\1x\2", k)
                if nk not in sign_to_keys[name] and nk not in extras:
                    extras.append(nk)
            if re.search(r"(\w)x(\w)", k):
                nk = re.sub(r"(\w)x(\w)", r"\1x\2", k)
                if nk not in sign_to_keys[name] and nk not in extras:
                    extras.append(nk)
        sign_to_keys[name].extend(extras)
    return sign_to_keys


def main():
    sign_to_keys = load_syllabaries()

    # indexes: normalised sign NAME -> name; normalised READING -> name
    # (the first entry found wins)
    by_name, by_key = {}, {}
    for name, keys in sign_to_keys.items():
        by_name.setdefault(deep_normalize(name), name)
        for k in keys:
            by_key.setdefault(deep_normalize(k), name)

    matched, unmatched = [], []
    with open(UNICODE_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            td = deep_normalize(row["transliteration"])
            name = by_name.get(td) or by_key.get(td)
            if name:
                matched.append({
                    "unicode_id": row["unicode_id"],
                    "sign_grapheme": row["sign_grapheme"],
                    "unicodeTrLit": row["transliteration"],
                    "syllabarySign": name,
                    "PhoneticsVersion": " | ".join(sign_to_keys.get(name, [])),
                })
            else:
                unmatched.append({
                    "unicode_id": row["unicode_id"],
                    "sign_grapheme": row["sign_grapheme"],
                    "transliteration": row["transliteration"],
                    "translit_normalized": td,
                })

    # csv default line terminator (CRLF), as in the original files
    with open(MATCHED_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["unicode_id", "sign_grapheme", "unicodeTrLit",
                                           "syllabarySign", "PhoneticsVersion"])
        w.writeheader()
        w.writerows(matched)
    with open(UNMATCHED_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["unicode_id", "sign_grapheme", "transliteration",
                                           "translit_normalized"])
        w.writeheader()
        w.writerows(unmatched)

    print(f"[1] matched:   {len(matched)} -> {MATCHED_CSV}")
    print(f"[2] unmatched: {len(unmatched)} -> {UNMATCHED_CSV}")


if __name__ == "__main__":
    main()
