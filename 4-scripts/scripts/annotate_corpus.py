#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: annotate_corpus.py
Description: Workflow Stage 1, Step 7.1 (rule draft). Applies the same rule-based
             annotation that produced the gold draft (OSL lookup + function
             rules, WITHOUT the manual word overrides) to any set of
             tablets: the validation split (to measure the baseline) or the
             unprocessed corpus. Output has the gold_signs.csv schema;
             rows with needs_check=1 are the ones the LLM (Step 7.2) reviews.
             Usage:
               python3 annotate_corpus.py <osl.asl> <tablets.csv> <atf_dir_or_file> <out.csv>
             tablets.csv needs columns p_number, corpus_group, genres,
             provenience, is_school_text, atf_lang (as gold_sample_tablets.csv
             or corpus_tablet_stats.csv).
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.1
"""

import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_gold  # noqa: E402
from goldlib import OSLIndex, split_atf_tablets  # noqa: E402


def load_atf(src: Path) -> dict:
    """Accepts a folder of per-tablet .atf files (searched recursively) or
    one multi-tablet .atf file. Returns {P-number: ATF block}."""
    files = [src] if src.is_file() else sorted(src.rglob("*.atf"))
    texts = {}
    for f in files:
        for p, b in split_atf_tablets(f.read_text(encoding="utf-8",
                                                  errors="replace")):
            texts.setdefault(p, b)
    return texts


def main():
    osl_path, tab_csv, atf_src, out_csv = sys.argv[1:5]
    osl = OSLIndex(osl_path)
    # NO manual overrides here: this is what the machine does on new data
    if os.environ.get("USE_OVERRIDES"):
        build_gold.load_overrides(Path(__file__).parent / "word_overrides.csv")
    with open(tab_csv, encoding="utf-8") as f:
        tabs = list(csv.DictReader(f))
    if os.environ.get("ONLY_SPLIT"):
        tabs = [t for t in tabs if t.get("split") == os.environ["ONLY_SPLIT"]]
    texts = load_atf(Path(atf_src))
    rows, counter, missing = [], [0], 0
    for t in tabs:
        block = texts.get(t["p_number"])
        if block is None:
            missing += 1
            continue
        t.setdefault("atf_lang", "sux")
        rows += build_gold.process_tablet(t["p_number"], block, t, osl, counter)
    for r in rows:
        r["annotation_status"] = "rules_auto"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=build_gold.FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    n_chk = sum(int(r["needs_check"]) for r in rows)
    print(f"tablets: {len(tabs) - missing} (missing ATF: {missing})  rows: {len(rows)}"
          f"  needs_check: {n_chk} ({100 * n_chk / max(len(rows), 1):.1f} %)")


if __name__ == "__main__":
    main()
