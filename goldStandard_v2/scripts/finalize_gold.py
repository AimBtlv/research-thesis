#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: finalize_gold.py
Description: Workflow Stage 1, Step 6.7. Tablet-level stratified 90/10 split of the gold standard
             (45 train / 5 validation tablets, ~10 % of signs in validation),
             exports CSV + CoNLL-U-style files and summary statistics.
             Usage: python3 finalize_gold.py <out_dir>
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.1
"""

import csv
import itertools
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(sys.argv[1])
SEED = 20261109
N_VAL = 5


def choose_validation(tabs, sign_counts):
    """Pick N_VAL tablets: 2 SCHOOL + 3 practical from 3 different corpus
    groups, >=1 Akkadian and >=1 Sumerian, sign share closest to 10 %."""
    total = sum(sign_counts.values())
    school = [t for t in tabs if t["corpus_group"] == "SCHOOL"]
    pract = [t for t in tabs if t["corpus_group"] != "SCHOOL"]
    rng = random.Random(SEED)
    best, best_d = None, 1e9
    for _ in range(20000):
        cand = rng.sample(school, 2) + rng.sample(pract, 3)
        groups = {t["corpus_group"] for t in cand[2:]}
        langs = {t["atf_lang"] for t in cand}
        if len(groups) < 3 or langs != {"sux", "akk"}:
            continue
        share = sum(sign_counts[t["p_number"]] for t in cand) / total
        d = abs(share - 0.10)
        if d < best_d:
            best, best_d = cand, d
    return {t["p_number"] for t in best}


def to_conllu(rows, path):
    """CoNLL-U-like export: one 'sentence' per ATF line, one token per sign
    row. Columns: ID FORM READING SIGN UNICODE FUNCTION INCLUDE WORD DAMAGE
    LANG MISC  (text itself is never changed, labels are added)."""
    by_line = defaultdict(list)
    order = []
    for r in rows:
        key = (r["artifact_id"], r["line_ref"])
        if key not in by_line:
            order.append(key)
        by_line[key].append(r)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# columns = ID FORM READING SIGN_NAME UNICODE FUNCTION "
                "INCLUDE WORD_ID DAMAGE WORD_LANG MISC\n")
        for key in order:
            lr = by_line[key]
            words = []
            for r in lr:
                if not words or words[-1][0] != r["word_id"]:
                    words.append((r["word_id"], r["raw_word"]))
            f.write(f"# sent_id = {key[0]}:{key[1]}\n")
            f.write(f"# corpus = {lr[0]['corpus_group']}  split = {lr[0]['split']}\n")
            f.write("# text = " + " ".join(w[1] for w in words) + "\n")
            for i, r in enumerate(lr, 1):
                misc = []
                if r["component_position"]:
                    misc.append(f"Comp={r['component_position']}:{r['component_name']}")
                if r["needs_check"] == "1":
                    misc.append("NeedsCheck=" + r["check_reason"].replace(" ", ""))
                f.write("\t".join([
                    str(i), r["raw_sign"], r["reading"] or "_",
                    r["sign_name"] or "_", r["unicode_id"] or "_",
                    r["sign_function"], r["include_in_analysis"], r["word_id"],
                    r["damage_state"], r["word_lang"],
                    "|".join(misc) or "_"]) + "\n")
            f.write("\n")


def main():
    with open(OUT / "gold_signs.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(OUT / "gold_sample_tablets.csv", encoding="utf-8") as f:
        tabs = list(csv.DictReader(f))
    counts = Counter(r["artifact_id"] for r in rows)
    val = choose_validation(tabs, counts)
    for t in tabs:
        t["split"] = "val" if t["p_number"] in val else "train"
        t["n_gold_rows"] = counts[t["p_number"]]
    for r in rows:
        r["split"] = "val" if r["artifact_id"] in val else "train"
    fields = list(rows[0].keys())
    fields = ["split"] + [c for c in fields if c != "split"]
    for name, sub in [("gold_signs.csv", rows),
                      ("gold_train.csv", [r for r in rows if r["split"] == "train"]),
                      ("gold_val.csv", [r for r in rows if r["split"] == "val"])]:
        with open(OUT / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(sub)
    with open(OUT / "gold_sample_tablets.csv", "w", encoding="utf-8",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(tabs[0].keys()))
        w.writeheader()
        w.writerows(tabs)
    to_conllu(rows, OUT / "gold_signs.conllu")

    # summary statistics
    def summ(sub):
        return {
            "tablets": len({r["artifact_id"] for r in sub}),
            "rows": len(sub),
            "function": dict(Counter(r["sign_function"] for r in sub)),
            "include_in_analysis": sum(r["include_in_analysis"] == "1" for r in sub),
            "needs_check": sum(r["needs_check"] == "1" for r in sub),
            "word_overrides": sum(r["annotation_status"] == "claude_word_override"
                                  for r in sub),
            "unresolved_sign": sum(r["resolution"] in (
                "unresolved", "qualifier_not_in_osl", "sign_name_not_in_osl")
                for r in sub),
        }
    stats = {"all": summ(rows),
             "train": summ([r for r in rows if r["split"] == "train"]),
             "val": summ([r for r in rows if r["split"] == "val"]),
             "by_corpus": {g: summ([r for r in rows if r["corpus_group"] == g])
                           for g in sorted({r["corpus_group"] for r in rows})},
             "val_tablets": sorted(val)}
    (OUT / "gold_stats.json").write_text(json.dumps(stats, indent=2,
                                                    ensure_ascii=False))
    print(json.dumps({k: stats[k] for k in ("all", "train", "val",
                                            "val_tablets")}, indent=1,
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
