#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: select_sample.py
Description: Workflow Stage 1, Step 6.4. Stratified, reproducible selection of ~50 Old Babylonian tablets
             (20 school + 30 practical) for the sign-level gold standard.
             Strata = corpus_group (proposed genre -> corpus mapping);
             within a stratum tablets are chosen to maximise provenience
             diversity among "annotatable" tablets (enough readable text).
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.1
"""

import csv
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from goldlib import split_atf_tablets, iter_text_lines, tokenize_line  # noqa

DS = Path(sys.argv[1] if len(sys.argv) > 1 else
          "/home/claude/ds/2-dataset/InputData/1.downloadCorpusATF")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "/home/claude/out")
SEED = 20261109

# --- proposed mapping CDLI genre -> thesis corpus (first listed genre wins)
GENRE_GROUP = [
    (r"^lexical|^thematic word list", "LEXICAL"),
    (r"^administrative|^account|^receipt", "ADMINISTRATIVE"),
    (r"^legal|contracts|^inheritance|^judicial|^marriage|^dowries|^adoption",
     "LEGAL"),
    (r"^letter$|^letter;", "LETTER"),
    (r"^literary|^wisdom|^prayer|^incantation|^ritual", "LITERARY"),
    (r"^mathematical|^scholarly|^divination|^medical", "SCHOLARLY"),
    (r"^official|^royal|^votive|^seals", "OTHER"),
]


def corpus_group(genres: str, is_school: str) -> str:
    if is_school == "1":
        return "SCHOOL"
    g = (genres or "").strip().lower()
    if not g:
        return "NO_GENRE"
    for pat, grp in GENRE_GROUP:
        if re.search(pat, g):
            return grp
    return "OTHER"


def load_meta():
    meta = {}
    for path in [DS / "OBP.csv",
                 DS / "OBP_full" / "practiceOBP_metadata_practical_16194.csv"]:
        with open(path, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                p = "P" + r["artifact_id"].zfill(6)
                r["p_number"] = p
                r["corpus_group"] = corpus_group(r.get("genres", ""),
                                                 r.get("is_school_text", "0"))
                meta[p] = r
    return meta


def load_atf():
    texts = {}
    for p, b in split_atf_tablets((DS / "OBP.atf").read_text(encoding="utf-8")):
        texts[p] = b
    for f in (DS / "practOBP_Prov_Genre").rglob("P*.atf"):
        for p, b in split_atf_tablets(f.read_text(encoding="utf-8",
                                                  errors="replace")):
            texts.setdefault(p, b)
    return texts


def tablet_stats(block: str):
    n_words = n_signs = n_readable = 0
    langs = Counter()
    has_lem = "#lem:" in block
    for ln in iter_text_lines(block):
        for w in tokenize_line(ln["content"]):
            n_words += 1
            for pc in w["pieces"]:
                n_signs += 1
                t = pc["text"].replace("#", "").replace("?", "")
                if t.lower() != "x" and not pc["broken"]:
                    n_readable += 1
        langs[ln["base_lang"]] += 1
    return {"n_words": n_words, "n_signs": n_signs, "n_readable": n_readable,
            "readable_share": round(n_readable / n_signs, 3) if n_signs else 0,
            "atf_lang": langs.most_common(1)[0][0] if langs else "",
            "has_lem": int(has_lem)}


QUOTA = {  # school 20 + practical 30
    "SCHOOL": 20, "ADMINISTRATIVE": 6, "LEGAL": 6, "LETTER": 6,
    "LITERARY": 4, "LEXICAL": 4, "SCHOLARLY": 4}
SCHOOL_SUBQUOTA = {"Lexical": 8, "Wisdom or proverb": 5,
                   "Business / Contracts": 3, "Literary": 3, "*": 1}


def pick_diverse(cands, k, rng):
    """Greedy: shuffle, then prefer unseen proveniences and alternate
    languages, so the stratum covers as many sites as possible."""
    rng.shuffle(cands)
    chosen, seen_prov, seen_lang = [], Counter(), Counter()
    pool = list(cands)
    while pool and len(chosen) < k:
        pool.sort(key=lambda c: (seen_prov[c["provenience"]],
                                 seen_lang[c["atf_lang"]]))
        c = pool.pop(0)
        chosen.append(c)
        seen_prov[c["provenience"]] += 1
        seen_lang[c["atf_lang"]] += 1
    return chosen


def main():
    rng = random.Random(SEED)
    meta, texts = load_meta(), load_atf()
    rows = []
    for p, m in meta.items():
        if p not in texts:
            continue
        st = tablet_stats(texts[p])
        st["lang_source"] = "atf_header"
        if st["atf_lang"] not in ("sux", "akk") and \
                "#atf: use lexical" in texts[p]:
            # OB lexical lists are Sumerian; Akkadian columns are marked %a
            st["atf_lang"], st["lang_source"] = "sux", "assumed_lexical"
        if st["atf_lang"] not in ("sux", "akk"):
            L = (m.get("languages") or "").lower()
            if L.startswith("sumerian"):
                st["atf_lang"], st["lang_source"] = "sux", "cdli_metadata"
            elif L.startswith("akkadian"):
                st["atf_lang"], st["lang_source"] = "akk", "cdli_metadata"
            elif "lexical" in (m.get("genres") or "").lower() or \
                    "#atf: use lexical" in texts[p]:
                st["atf_lang"], st["lang_source"] = "sux", "assumed_lexical"
        rows.append({**{k: m.get(k, "") for k in
                        ("p_number", "designation", "provenience", "genres",
                         "languages", "is_school_text", "corpus_group",
                         "genres_uncertain", "is_provenience_uncertain")}, **st})
    OUT.mkdir(parents=True, exist_ok=True)
    print("tablets with ATF + metadata:", len(rows))
    print(Counter(r["corpus_group"] for r in rows))

    # annotatable = enough text, mostly readable
    ok = [r for r in rows if (25 if r["corpus_group"] == "SCHOOL" else 30) <= r["n_signs"] <= 260
          and r["readable_share"] >= 0.75 and r["atf_lang"] in ("sux", "akk")]
    print("annotatable:", len(ok), Counter(r["corpus_group"] for r in ok))

    selected = []
    for grp, k in QUOTA.items():
        cands = [r for r in ok if r["corpus_group"] == grp]
        if grp == "SCHOOL":
            used = set()
            for g, kk in SCHOOL_SUBQUOTA.items():
                sub = [c for c in cands if c["p_number"] not in used and
                       (c["genres"] == g if g != "*" else
                        c["genres"] not in SCHOOL_SUBQUOTA)]
                got = pick_diverse(sub, kk, rng)
                used |= {c["p_number"] for c in got}
                selected += got
        else:
            selected += pick_diverse(cands, k, rng)

    fields = list(selected[0].keys())
    with open(OUT / "gold_sample_tablets.csv", "w", encoding="utf-8",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(selected)
    # write the ATF of the selected tablets (= the gold corpus)
    corp = OUT / "gold_corpus_atf"
    corp.mkdir(exist_ok=True)
    for r in selected:
        (corp / f"{r['p_number']}.atf").write_text(texts[r["p_number"]],
                                                    encoding="utf-8")
    # full stats table for the unprocessed corpus as well
    with open(OUT / "corpus_tablet_stats.csv", "w", encoding="utf-8",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("selected:", len(selected))
    print(Counter(r["corpus_group"] for r in selected))
    print(Counter(r["atf_lang"] for r in selected))
    print("proveniences:", len({r["provenience"] for r in selected}))
    print("signs total:", sum(r["n_signs"] for r in selected))


if __name__ == "__main__":
    main()
