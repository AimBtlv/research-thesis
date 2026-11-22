#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 05_build_diri_lexical_list.py (= 1_build_diri_lexical_list.py)
Description: Workflow Stage 1, Step 2. Extracts the lexical series Diri
             (sign sequence + ancient reading) from the Oracc DCCLT JSON
             (catalogue.json + corpusjson folders) into diri_lexical_list.csv.
             Only the paths are changed: the Oracc downloads are expected in
             2-dataset/DataProfile/oracc_dcclt/. If they are absent the step
             is skipped and the existing diri_lexical_list.csv is used.
Author: Aima, paths prepared with Claude
Date: 2026-11-09
Version: 1.3 (2026-11-22: Oracc JSON in 2-dataset/DataProfile/step2/dcclt/,
         found automatically; the corpusjson folders found are listed; a run
         with fewer lines than the reference file in DataProfile/ is written to
         diri_lexical_list_PARTIAL.csv and does not replace the full list)
"""

import json
import csv
from pathlib import Path

# --- Paths (relative to the repository: research-thesis/<scripts folder>/<this file>) ---
ROOT = Path(__file__).resolve().parents[1]                 # research-thesis/
DP = ROOT / "2-dataset" / "DataProfile"
# Oracc DCCLT JSON: 2-dataset/DataProfile/step2/dcclt/ (old place: oracc_dcclt/)
ORACC = next((d for d in (DP / "step2" / "dcclt", DP / "oracc_dcclt") if d.exists()),
             DP / "step2" / "dcclt")
OUT = Path(__file__).resolve().parent / "output"
OUTPUT_DIR = OUT / "step2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def find_catalogue(root: Path) -> Path:
    """catalogue.json of the DCCLT/signlists project: directly in the Oracc
    folder, else the first one found below it (signlists first)."""
    if (root / "catalogue.json").exists():
        return root / "catalogue.json"
    found = sorted(root.rglob("catalogue.json"), key=lambda p: ("signlists" not in str(p), str(p)))
    return found[0] if found else root / "catalogue.json"


def find_corpus_dirs(root: Path) -> list:
    """Every 'corpusjson' folder below the Oracc folder, in the order
    signlists, dcclt main project, ebla, nineveh (the first copy of a text wins)."""
    def rank(p):
        s = str(p).lower()
        for k, word in enumerate(("signlists", "dcclt-2", "ebla", "niniveh", "nineveh")):
            if word in s:
                return (k, s)
        return (9, s)
    return sorted((p for p in root.rglob("corpusjson") if p.is_dir()), key=rank)


CATALOGUE_PATH = find_catalogue(ORACC) if ORACC.exists() else ORACC / "catalogue.json"
CORPUS_DIRS = find_corpus_dirs(ORACC) if ORACC.exists() else []
OUTPUT_CSV = OUTPUT_DIR / "diri_lexical_list.csv"
# v1.3: a re-run that finds fewer lines than the reference file is written
# here instead, so that an incomplete set of archives never replaces the list
PARTIAL_CSV = OUTPUT_DIR / "diri_lexical_list_PARTIAL.csv"


def reference_file():
    """The Diri list kept in 2-dataset/ (input of Steps 3-4 when Step 2 is
    not re-run): DataProfile/step2/ first, then DataProfile/step1/."""
    for p in (DP / "step2" / "diri_lexical_list.csv", DP / "step1" / "diri_lexical_list.csv"):
        if p.exists():
            return p
    return None


def count_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


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

    # v1.3: show which archives were found, so that a missing one is visible
    print(f"[INFO] corpusjson folders found under {ORACC}: {len(CORPUS_DIRS)}")
    for d in CORPUS_DIRS:
        print(f"       {d.relative_to(ORACC)}  ({len(list(d.glob('P*.json')))} P-texts)")
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

    # v1.3: never replace the full list by a smaller one (archives missing)
    ref = reference_file()
    target = OUTPUT_CSV
    if ref is not None and len(all_rows) < count_rows(ref):
        target = PARTIAL_CSV
        if OUTPUT_CSV.exists():
            OUTPUT_CSV.unlink()      # Steps 3-4 then read the reference file
        print(f"\n[WARN] only {len(all_rows)} lines; the reference file has {count_rows(ref)}:")
        print(f"       {ref}")
        print(f"       An Oracc archive is probably missing (see the folders above; the main")
        print(f"       DCCLT project with ~5,000 texts holds most Old Babylonian Diri tablets).")
        print(f"       The reference file stays the input of Steps 3-4; this run -> {target.name}")
    with open(target, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["p_number", "designation", "period", "provenience", "subgenre",
                     "line_label", "sumerian_reading", "sign_sequence", "akkadian_gloss"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)

    print(f"\n[RESULT] {len(all_rows)} lines written -> {target}")
    print(f"[COVERAGE] {len(to_process)} / {len(diri_catalogue)} Diri texts processed "
          f"({100*len(to_process)/len(diri_catalogue):.1f}%)")


if __name__ == "__main__":
    import sys
    if not CATALOGUE_PATH.exists():
        print(f"[SKIP] Step 2 (Diri) not re-run: {CATALOGUE_PATH} not found.\n"
              f"       The existing 2-dataset/DataProfile/step2/"
              f"diri_lexical_list.csv will be used by Steps 3-4.\n"
              f"       To re-run: unzip the Oracc DCCLT JSON into {ORACC}")
        sys.exit(0)
    main()
