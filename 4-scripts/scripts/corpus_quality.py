#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: corpus_quality.py
Description: Workflow Stage 1, Step 7.5. Quality report of an annotated
             corpus (output of annotate_corpus.py, run_llm_annotation.py or
             apply_lexicon.py), per corpus_group: tablets, sign rows, share
             of rows in the analysis, share of unresolved / unclear signs,
             share of flagged rows, LOGO : SYLL ratio. Answers the Open
             Question whether corpora differ in unrecognised tokens before
             they are compared in Stage 2. Reads the CSV as a stream, so it
             also works on the 600 MB full-corpus file.
             Usage: python3 corpus_quality.py <annotated.csv> <report.md>
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.0
"""

import csv
import sys
from collections import defaultdict

UNRESOLVED = {"unresolved", "qualifier_not_in_osl", "sign_name_not_in_osl"}


def main():
    src, report = sys.argv[1], sys.argv[2]
    stats = defaultdict(lambda: defaultdict(int))
    tablets = defaultdict(set)
    with open(src, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            # count reading units once (first component of a compound)
            if r["component_position"] not in ("", "1"):
                continue
            g = r["corpus_group"] or "NO_GROUP"
            for key in (g, "ALL"):
                s = stats[key]
                tablets[key].add(r["artifact_id"])
                s["units"] += 1
                s["include"] += r["include_in_analysis"] == "1"
                s["unresolved"] += r["resolution"] in UNRESOLVED
                s["unclear"] += r["sign_function"] == "UNCLEAR"
                s["flagged"] += r["needs_check"] == "1"
                s["logo"] += (r["sign_function"] == "LOGO" and
                              r["include_in_analysis"] == "1")
                s["syll"] += (r["sign_function"] == "SYLL" and
                              r["include_in_analysis"] == "1")

    def pct(a, b):
        return f"{100 * a / b:.2f} %" if b else "-"

    lines = ["# Corpus Quality Report (Step 7.5)\n",
             f"*Source:* `{src}`; reading units (compounds counted once).\n",
             "| Corpus | Tablets | Units | In analysis | Unresolved (not in OSL) "
             "| UNCLEAR (x) | Flagged | LOGO : SYLL |",
             "|---|---|---|---|---|---|---|---|"]
    order = sorted(k for k in stats if k != "ALL") + ["ALL"]
    for k in order:
        s = stats[k]
        ratio = f"{s['logo'] / s['syll']:.2f}" if s["syll"] else "-"
        lines.append(f"| {k} | {len(tablets[k])} | {s['units']} | "
                     f"{pct(s['include'], s['units'])} | "
                     f"{pct(s['unresolved'], s['units'])} | "
                     f"{pct(s['unclear'], s['units'])} | "
                     f"{pct(s['flagged'], s['units'])} | {ratio} |")
    lines.append("\n*Reading the table:* if one corpus has a clearly higher "
                 "share of unresolved or flagged signs, its inventory is less "
                 "complete; compare corpora on normalised measures, or check "
                 "the flagged rows of that corpus first.")
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
