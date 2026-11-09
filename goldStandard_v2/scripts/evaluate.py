#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: evaluate.py
Description: Workflow Stage 1, Step 7.3 (and parser validation in
             Step 6). Compares a machine annotation (rules baseline or LLM output)
             with the gold validation split, sign by sign. Reports accuracy
             of sign identification (sign_name, unicode_id), of function
             (LOGO/SYLL/DET/NUM/UNCLEAR: per-class precision/recall/F1,
             Cohen's kappa, confusion matrix) and of include_in_analysis,
             overall and by corpus and language. Writes a Markdown report.
             Usage: python3 evaluate.py <gold_val.csv> <pred.csv> <report.md>
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.1
"""

import csv
import sys
from collections import Counter, defaultdict

KEY = ("reading_unit_id", "component_position")
CLASSES = ["LOGO", "SYLL", "DET", "NUM", "UNCLEAR"]


def load(path):
    """One entry per reading unit (first component of a compound only), so
    that a compound sign is not counted twice."""
    with open(path, encoding="utf-8") as f:
        return {tuple(r[k] for k in KEY): r for r in csv.DictReader(f)
                if r["component_position"] in ("", "1")}


def prf(pairs):
    """pairs: list of (gold, pred). Per-class P/R/F1 + macro-F1."""
    out = {}
    for c in CLASSES:
        tp = sum(g == c and p == c for g, p in pairs)
        fp = sum(g != c and p == c for g, p in pairs)
        fn = sum(g == c and p != c for g, p in pairs)
        P = tp / (tp + fp) if tp + fp else 0.0
        R = tp / (tp + fn) if tp + fn else 0.0
        F = 2 * P * R / (P + R) if P + R else 0.0
        out[c] = (P, R, F, tp + fn)
    present = [c for c in CLASSES if out[c][3] > 0]
    out["macro_F1"] = sum(out[c][2] for c in present) / max(len(present), 1)
    return out


def kappa(pairs):
    n = len(pairs)
    if not n:
        return 0.0
    po = sum(g == p for g, p in pairs) / n
    gc, pc = Counter(g for g, _ in pairs), Counter(p for _, p in pairs)
    pe = sum(gc[c] * pc[c] for c in set(gc) | set(pc)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def acc(pairs):
    return sum(g == p for g, p in pairs) / len(pairs) if pairs else 0.0


def main():
    gold, pred = load(sys.argv[1]), load(sys.argv[2])
    report = sys.argv[3]
    common = [k for k in gold if k in pred]
    missing = [k for k in gold if k not in pred]
    extra = [k for k in pred if k not in gold]
    L = []
    L.append("# Evaluation Report (Validation Split)\n")
    L.append(f"*Gold rows:* {len(gold)}  *Predicted rows:* {len(pred)}  "
             f"*Aligned:* {len(common)}  *Missing in prediction:* {len(missing)}  "
             f"*Extra in prediction:* {len(extra)}\n")
    L.append(f"*Token alignment (coverage):* {len(common) / len(gold):.3f}\n")

    def block(title, keys):
        f_pairs = [(gold[k]["sign_function"], pred[k]["sign_function"]) for k in keys]
        s_pairs = [(gold[k]["sign_name"], pred[k]["sign_name"]) for k in keys]
        u_pairs = [(gold[k]["unicode_id"], pred[k]["unicode_id"]) for k in keys]
        i_pairs = [(gold[k]["include_in_analysis"], pred[k]["include_in_analysis"])
                   for k in keys]
        ls = [(g, p) for g, p in f_pairs if g in ("LOGO", "SYLL")]
        m = prf(f_pairs)
        L.append(f"\n## {title}\n")
        L.append(f"*Rows:* {len(keys)}\n")
        L.append("| Metric | Value |\n|---|---|")
        L.append(f"| Sign name accuracy | {acc(s_pairs):.3f} |")
        L.append(f"| Unicode accuracy | {acc(u_pairs):.3f} |")
        L.append(f"| Function accuracy (5 classes) | {acc(f_pairs):.3f} |")
        L.append(f"| Function macro-F1 | {m['macro_F1']:.3f} |")
        L.append(f"| Function Cohen's kappa | {kappa(f_pairs):.3f} |")
        L.append(f"| LOGO/SYLL accuracy (gold LOGO or SYLL) | {acc(ls):.3f} |")
        L.append(f"| include_in_analysis agreement | {acc(i_pairs):.3f} |\n")
        L.append("| Class | Precision | Recall | F1 | Support |\n|---|---|---|---|---|")
        for c in CLASSES:
            P, R, F, n = m[c]
            if n:
                L.append(f"| {c} | {P:.3f} | {R:.3f} | {F:.3f} | {n} |")
        cm = Counter(f_pairs)
        L.append("\n*Confusion matrix (rows = gold, columns = prediction):*\n")
        L.append("| gold \\ pred | " + " | ".join(CLASSES) + " |")
        L.append("|---|" + "---|" * len(CLASSES))
        for g in CLASSES:
            L.append(f"| {g} | " + " | ".join(str(cm[(g, p)]) for p in CLASSES) + " |")
        return f_pairs

    block("Overall", common)
    by = defaultdict(list)
    for k in common:
        by[("corpus", gold[k]["corpus_group"])].append(k)
        by[("language", gold[k]["atf_lang"])].append(k)
    for (kind, name), keys in sorted(by.items()):
        block(f"By {kind}: {name}", keys)
    # error list for qualitative review (preference 16: check metrics
    # against philological observation)
    L.append("\n## Errors (Function or Sign) For Qualitative Review\n")
    L.append("| Tablet | Line | Word | Sign | Gold | Pred | Type |\n|---|---|---|---|---|---|---|")
    for k in common:
        g, p = gold[k], pred[k]
        if g["sign_function"] != p["sign_function"]:
            L.append(f"| {g['artifact_id']} | {g['line_ref']} | `{g['raw_word']}` | "
                     f"{g['reading']} | {g['sign_function']} | {p['sign_function']} | function |")
        if g["sign_name"] != p["sign_name"]:
            L.append(f"| {g['artifact_id']} | {g['line_ref']} | `{g['raw_word']}` | "
                     f"{g['reading']} | {g['sign_name']} | {p['sign_name']} | sign |")
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
