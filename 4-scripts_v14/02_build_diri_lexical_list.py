#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 02_build_diri_lexical_list.py (= 1_build_diri_lexical_list.py)
Description: Workflow Stage 1, Step 2. Extracts the lexical series Diri
             (sign sequence + ancient reading) from the Oracc DCCLT JSON
             (catalogue.json + corpusjson folders) into diri_lexical_list.csv.
             Only the paths are changed: the Oracc downloads are expected in
             2-dataset/DataProfile/oracc_dcclt/. If they are absent the step
             is skipped and the existing diri_lexical_list.csv is used.
Author: Aima, paths prepared with Claude
Date: 2026-11-09
Version: 1.1
"""

import json
import csv
from pathlib import Path

# --- Paths (relative to the repository: research-thesis/pipeline_v14/<this file>) ---
ROOT = Path(__file__).resolve().parents[1]                 # research-thesis/
DP = ROOT / "2-dataset" / "DataProfile"
ORACC = DP / "oracc_dcclt"        # put the unzipped Oracc DCCLT JSON here
OUT = Path(__file__).resolve().parent / "output"
OUTPUT_DIR = OUT / "step2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CATALOGUE_PATH = ORACC / "catalogue.json"
CORPUS_DIRS = [
    ORACC / "dcclt_full/dcclt/signlists/corpusjson",
    ORACC / "dcclt2_full/dcclt-2/corpusjson",
    ORACC / "dcclt-ebla_full/dcclt-ebla/ebla/corpusjson",
    ORACC / "dcclt-niniveh_full/dcclt-niniveh/nineveh/corpusjson",
]
OUTPUT_CSV = OUTPUT_DIR / "diri_lexical_list.csv"


def load_diri_catalogue(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        cat = json.load(f)
    members = cat["members"]

    return {pid: rec for pid, rec in members.items()
            if "diri" in rec.get("subgenre", "").lower()
            or rec.get("series", "").strip().lower() == "diri"}


def process_composite_text(json_path: Path, meta: dict) -> list:
    """Composite/score editions (Q-number ids) encode the sign identity
    differently from individual tablet exemplars: not as a sibling lemma,
    but as the gdl_sign attribute inside the reading lemma's own gdl
    breakdown. This function is used for any text whose id starts with 'Q'."""
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)

    sentences = []
    find_sentences(d.get("cdl", []), sentences)

    rows = []
    for s in sentences:
        lemmas = []
        find_lemmas(s.get("cdl", []), lemmas)
        reading = sign_seq = akkadian = ""
        for l in lemmas:
            f = l.get("f", {})
            lang, form = f.get("lang", ""), f.get("form", "")
            gdl = f.get("gdl", [])
            if lang.startswith("sux") and form and form != "x":
                reading = form
                signs = [g.get("gdl_sign", "") for g in gdl if isinstance(g, dict) and g.get("gdl_sign")]
                if signs:
                    sign_seq = ".".join(signs) if len(signs) > 1 else signs[0]
            elif lang.startswith("akk") and form and form not in ("x", "x-x"):
                akkadian = form
        if not (reading or sign_seq):
            continue
        rows.append({
            "p_number": meta["id_composite"],
            "designation": meta.get("designation", ""),
            "period": meta.get("period", ""),
            "provenience": meta.get("place", meta.get("provenience", "")),
            "subgenre": f"{meta.get('series','')} (composite score)",
            "line_label": s.get("label", ""),
            "sumerian_reading": reading,
            "sign_sequence": sign_seq,
            "akkadian_gloss": akkadian,
        })
    return rows


def find_sentences(node, results):
    if isinstance(node, dict):
        if node.get("type") == "sentence":
            results.append(node)
        for v in node.values():
            find_sentences(v, results)
    elif isinstance(node, list):
        for item in node:
            find_sentences(item, results)


def find_lemmas(node, results):
    if isinstance(node, dict):
        if node.get("node") == "l":
            results.append(node)
        for v in node.values():
            find_lemmas(v, results)
    elif isinstance(node, list):
        for item in node:
            find_lemmas(item, results)


def classify_lemma(lemma: dict) -> str:
    f = lemma.get("f", {})
    lang = f.get("lang", "")
    form = f.get("form", "")
    if lang.startswith("akk"):
        return "akkadian_gloss"
    if lang.startswith("sux"):
        if "|" in form or (form.isupper() and form not in ("X", "")):
            return "sign_sequence"
        return "sumerian_reading"
    return "other"


def process_text(json_path: Path, meta: dict) -> list:
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)

    sentences = []
    find_sentences(d.get("cdl", []), sentences)

    rows = []
    for s in sentences:
        lemmas = []
        find_lemmas(s.get("cdl", []), lemmas)
        if not lemmas:
            continue

        reading = sign_sequence = akkadian = ""
        for l in lemmas:
            kind = classify_lemma(l)
            frag = l.get("frag", "").strip()
            if not frag or frag in ("[...]", "x", "..."):
                continue
            if kind == "sumerian_reading" and not reading:
                reading = frag
            elif kind == "sign_sequence" and not sign_sequence:
                sign_sequence = frag
            elif kind == "akkadian_gloss" and not akkadian:
                akkadian = frag

        if not (reading or sign_sequence):
            continue 

        rows.append({
            "p_number": meta["id_text"],
            "designation": meta.get("designation", ""),
            "period": meta.get("period", ""),
            "provenience": meta.get("provenience", ""),
            "subgenre": meta.get("subgenre", ""),
            "line_label": s.get("label", ""),
            "sumerian_reading": reading,
            "sign_sequence": sign_sequence,
            "akkadian_gloss": akkadian,
        })
    return rows


def main():
    diri_catalogue = load_diri_catalogue(CATALOGUE_PATH)
    print(f"[INFO] {len(diri_catalogue)} Diri texts identified in catalogue "
          f"(individual exemplars + composite score editions)")

    available = {}
    for corpus_dir in CORPUS_DIRS:
        for p in list(corpus_dir.glob("P*.json")) + list(corpus_dir.glob("Q*.json")):
            available.setdefault(p.stem, p) 
    to_process = {pid: meta for pid, meta in diri_catalogue.items() if pid in available}
    print(f"[INFO] {len(to_process)} of those texts are present in the corpus archives")

    all_rows = []
    for pid, meta in sorted(to_process.items()):
        if pid.startswith("Q"):
            rows = process_composite_text(available[pid], meta)
        else:
            rows = process_text(available[pid], meta)
        all_rows.extend(rows)
        tag = "composite" if pid.startswith("Q") else "exemplar"
        print(f"  [OK] {pid} ({tag}, {meta.get('designation','')}): {len(rows)} lines")

    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["p_number", "designation", "period", "provenience", "subgenre",
                     "line_label", "sumerian_reading", "sign_sequence", "akkadian_gloss"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)

    print(f"\n[RESULT] {len(all_rows)} lines written -> {OUTPUT_CSV}")
    print(f"[COVERAGE] {len(to_process)} / {len(diri_catalogue)} Diri texts processed "
          f"({100*len(to_process)/len(diri_catalogue):.1f}%)")


if __name__ == "__main__":
    import sys
    if not CATALOGUE_PATH.exists():
        print(f"[SKIP] Step 2 (Diri) not re-run: {CATALOGUE_PATH} not found.\n"
              f"       The existing 2-dataset/DataProfile/1-5unicodeAssignmentFiles/"
              f"diri_lexical_list.csv will be used by Steps 3-4.\n"
              f"       To re-run: unzip the Oracc DCCLT JSON into {ORACC}")
        sys.exit(0)
    main()
