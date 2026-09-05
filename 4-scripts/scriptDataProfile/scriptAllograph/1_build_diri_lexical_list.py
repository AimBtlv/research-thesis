#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import csv
from pathlib import Path

CATALOGUE_PATH = "catalogue.json"
CORPUS_DIRS = [
    Path("dcclt_full/dcclt/signlists/corpusjson"),
    Path("dcclt2_full/dcclt-2/corpusjson"),
    Path("dcclt-ebla_full/dcclt-ebla/ebla/corpusjson"),
    Path("dcclt-niniveh_full/dcclt-niniveh/nineveh/corpusjson"),
]
OUTPUT_CSV = "diri_lexical_list.csv"


def load_diri_catalogue(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        cat = json.load(f)
    members = cat["members"]
    # Two independent tags mark a Diri text in this catalogue: 'subgenre'
    # (used for individual tablet exemplars, e.g. 'OB Nippur Diri') and
    # 'series' (used for composite/score editions, e.g. Q000146 'Diri 01').
    # Missing the second missed the actual MSL 15 = watru master edition
    # entirely in the first pass.
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
            continue  # fully broken line, nothing usable

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
            available.setdefault(p.stem, p)  # first archive found wins
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
    main()
