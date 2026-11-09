#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: apply_lexicon.py
Description: Non-AI alternative to step 2. Learns a word-type lexicon from
             the TRAIN split of the gold standard (word written as a sequence
             of readings + language -> function pattern, majority vote) and
             applies it to a rule-based draft. Words not in the lexicon keep
             the rule labels. Memory-based tagging: no LLM, fully transparent.
             Usage: python3 apply_lexicon.py <gold_train.csv> <draft.csv> <out.csv>
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.0
"""

import csv
import re
import sys
from collections import Counter, OrderedDict, defaultdict


def units(rows):
    """word_id -> list of first-component rows (one per reading unit)."""
    w = OrderedDict()
    for r in rows:
        if r["component_position"] in ("", "1"):
            w.setdefault(r["word_id"], []).append(r)
    return w


def key(sigs):
    """Word type = language + ATF word without damage/editorial marks.
    Underscores and braces are KEPT: _u4_-mi-im (logogram) and u4-mi-im
    (syllabic) are different types."""
    raw = re.sub(r"[#?!*\[\]<>⸢⸣]", "", sigs[0]["raw_word"])
    return (sigs[0]["word_lang"][:3], raw)


def main():
    train_p, draft_p, out_p = sys.argv[1:4]
    with open(train_p, encoding="utf-8") as f:
        train = list(csv.DictReader(f))
    with open(draft_p, encoding="utf-8") as f:
        draft = list(csv.DictReader(f))

    # 1. learn: word type -> most frequent gold function pattern
    votes = defaultdict(Counter)
    for sigs in units(train).values():
        votes[key(sigs)][tuple(s["sign_function"] for s in sigs)] += 1
    lexicon = {k: c.most_common(1)[0][0] for k, c in votes.items()}

    # 2. apply to draft (all component rows of a unit get the same label)
    by_unit = defaultdict(list)
    for r in draft:
        by_unit[r["reading_unit_id"]].append(r)
    hit = changed = 0
    for wid, sigs in units(draft).items():
        pat = lexicon.get(key(sigs))
        if not pat:
            continue
        hit += 1
        for s, fn in zip(sigs, pat):
            for r in by_unit[s["reading_unit_id"]]:
                if r["sign_function"] != fn:
                    changed += 1
                    r["sign_function"] = fn
                    r["function_rule"] = "train_lexicon"
                present = r["damage_state"].split(",")[0] not in (
                    "restored", "supplied", "superfluous")
                r["include_in_analysis"] = str(int(fn in ("LOGO", "SYLL") and present))
    with open(out_p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(draft[0].keys()))
        w.writeheader()
        w.writerows(draft)
    n = len(units(draft))
    print(f"lexicon types: {len(lexicon)}  words in draft: {n}  "
          f"found in lexicon: {hit} ({100 * hit / n:.1f} %)  rows changed: {changed}")


if __name__ == "__main__":
    main()
