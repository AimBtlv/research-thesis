#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: build_gold.py
Description: Workflow Stage 1, Steps 6.5-6.6. Builds the sign-level pre-annotation (silver -> gold candidate)
             for the selected tablets. One row = one sign occurrence (one
             row per component for '.'-compounds, as in grapheme.csv).
             Readings are resolved against osl.asl directly (not against
             allograph_all_v11.csv, which lacks 226 simple signs).
             Function (LOGO/SYLL/DET/NUM/UNCLEAR) is assigned by language
             and context, never by letter case alone.
             Usage: python3 build_gold.py <osl.asl> <out_dir> [corrections.csv]
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.1
"""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from goldlib import (OSLIndex, iter_text_lines, tokenize_line,  # noqa
                     resolve_piece, label_function, looks_syllabic_akkadian)


# Sumerian divine names written logographically WITHOUT underscores in
# Akkadian ATF (CDLI convention). Multi-sign names listed as tuples.
DN_LOGO = [("nin", "šubur"), ("en", "lil₂"), ("en", "ki"), ("amar", "utu"),
           ("nin", "urta"), ("nin", "gal"), ("nin", "girsu"), ("nin", "isin₂", "na"),
           ("nin", "mar", "ki"), ("nin", "sun₂"), ("nin", "hur", "saŋ"),
           ("nin", "šubur"), ("dumu", "zi"), ("nin", "kar", "ra", "ak"),
           ("utu",), ("suen",), ("en", "zu"), ("iškur",), ("nanna",),
           ("inanna",), ("marduk",), ("nergal",), ("nisaba",), ("gibil₆",),
           ("iš₈", "tar₂"), ("ašnan",), ("ningal",), ("lamma",), ("nanše",),
           ("ezinu₂",), ("nuska",), ("ha", "ia₃"), ("i₇",), ("lugal",),
           ("nin", "a", "zu"), ("nin", "tu"), ("aš", "ŋi₇"), ("ŋeš", "bil₃", "ga", "mes"),
           ("uraš",), ("nusku",), ("mar", "tu"), ("nin", "lil₂"), 
           ("imin", "bi"), ("nin", "ka₅"), ("dumu", "zi", "da"),
           ("gibil",), ("nin", "mug"), ("lugal", "marad", "da"), ("nin", "si₄", "an", "na")]
# logographic first elements of Akkadian personal names written without _ _
AKK_PN_LOGO = {"dumu", "lu₂", "dingir", "ARAD", "ARAD₂", "puzur₄", "geme₂",
               "nur₂"}
# Akkadian plural markers (written with the logogram)
PLURAL_MARKERS = {"meš", "hi", "a", "didli"}
# Classifier words written as separate words at the head of lexical entries
LEX_CLASSIFIER = {"ŋeš", "giš", "geš", "na₄", "kuš", "tug₂", "urudu",
                  "uruda", "dug", "u₂", "zabar", "ku₆", "mušen"}

FIELDS = [
    "gold_row_id", "artifact_id", "corpus_group", "genre_cdli", "provenience",
    "is_school_text", "atf_lang", "surface", "column", "line_num", "line_ref",
    "word_id", "word_index", "raw_word", "sign_index", "reading_unit_id",
    "raw_sign", "reading", "sign_name", "is_compound", "component_position",
    "component_name", "unicode_id", "sign_grapheme", "sign_function",
    "include_in_analysis", "word_lang", "damage_state", "corrected",
    "resolution", "n_candidates", "alt_candidates", "function_rule",
    "needs_check", "check_reason", "annotation_status", "annotator_note",
    "human_verified", "human_correction_note",
]


CODE = {"L": "LOGO", "S": "SYLL", "D": "DET", "N": "NUM", "?": "UNCLEAR"}
OVERRIDES, USED = {}, set()


def load_overrides(path):
    if path and path.exists():
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                OVERRIDES[(r["artifact_id"], r["raw_word"])] = (
                    r["pattern"], r["still_check"] == "1", r["note"])


def damage_state(pc, flags):
    st = []
    if pc["broken"]:
        st.append("restored")      # [ ] restored by editor
    if pc["supplied"]:
        st.append("supplied")      # < > omitted by scribe, supplied
    if pc["erased"]:
        st.append("superfluous")   # << >> scribal superfluous/erased
    st += flags                    # damaged / uncertain / collated
    return ",".join(st) or "intact"


def split_components(sign_name, osl):
    """'|KA₂.GAL|' -> [('KA₂', codes, ucun), ('GAL', ...)]; only '.'
    sequences are split (×, &, % ligatures stay one grapheme)."""
    inner = sign_name.strip("|")
    if not sign_name.startswith("|") or "." not in inner or \
            re.search(r"[×&%@()]", inner.replace("@g", "").replace("@t", "")):
        return None
    comps = []
    for c in inner.split("."):
        name = osl.lookup_name(c) or c
        code, ucun = osl.unicode_of(name)
        comps.append((name, code, ucun))
    return comps


def mark_dn(word_rows, akk=True):
    """Sumerian DN after {d} -> LOGO (Akkadian and Sumerian texts); in
    Akkadian texts unlisted DNs -> SYLL, PN logograms, plural markers."""
    for k, r in enumerate(word_rows):
        if r["det"] and r["reading"] in ("d", "dingir") and \
                k + 1 < len(word_rows):
            rest = [x["reading"] for x in word_rows[k + 1:]]
            best = None
            for dn in sorted(DN_LOGO, key=len, reverse=True):
                if tuple(rest[:len(dn)]) == dn:
                    best = dn
                    break
            if best:
                for j in range(len(best)):
                    word_rows[k + 1 + j]["_force"] = ("LOGO",
                                                      "akk:divine_name_logogram",
                                                      False)
            elif rest and not word_rows[k + 1]["logo"] and akk:
                # unlisted DN outside _ _ : usually spelled syllabically
                word_rows[k + 1]["_force"] = ("SYLL",
                                              "akk:divine_name_unlisted_syllabic",
                                              True)
    # PN logographic elements and plural markers
    for k, r in enumerate(word_rows if akk else []):
        if not r["logo"] and not r["det"] and r["reading"] in AKK_PN_LOGO and \
                len(word_rows) > 1 and "_force" not in r and \
                (k == 0 or word_rows[k - 1]["det"]):
            r["_force"] = ("LOGO", "akk:pn_logographic_element", True)
        if r["logo"] and r["reading"] == "meš" and k > 0:
            r["_force"] = ("DET", "akk:plural_marker_meš", True)


def process_tablet(p, block, meta, osl, row_counter):
    rows = []
    word_index = 0
    atf_lang = meta["atf_lang"]
    is_lex = meta["corpus_group"] == "LEXICAL" or "#atf: use lexical" in block
    for ln in iter_text_lines(block):
        words = tokenize_line(ln["content"])
        line_ref = f"{ln['surface'][:3]}:{ln['column']}:{ln['line_num']}"
        for wi_line, w in enumerate(words):
            if not w["pieces"]:
                continue
            word_index += 1
            word_id = f"{p}_w{word_index}"
            wrows = []
            for si, pc in enumerate(w["pieces"]):
                res = resolve_piece(pc["text"], osl)
                if res["kind"] == "gap":
                    continue
                r = {**res, "det": pc["det"], "phon_compl": pc["phon_compl"],
                     "logo": pc["logo"], "broken": pc["broken"],
                     "supplied": pc["supplied"], "erased": pc["erased"],
                     "gloss": pc.get("gloss", False),
                     "lang": pc["lang"] or atf_lang, "raw_sign": pc["text"],
                     "_pc": pc}
                wrows.append(r)
            if not wrows:
                continue
            word_lang = wrows[0]["lang"] or atf_lang or "sux"
            wrows[-1]["_trunc"] = bool(re.search(r"(\.\.\.|…|x)\]?#?\??$",
                                                 w["raw"]))
            mark_dn(wrows, akk=word_lang.startswith("akk"))
            label_function(wrows, word_lang)
            for r in wrows:
                if "_force" in r and r["sign_function"] in ("LOGO", "SYLL", "UNCLEAR"):
                    r["sign_function"], r["function_rule"], r["needs_check"] = \
                        r["_force"]
                if r["gloss"] and r["sign_function"] in ("LOGO", "SYLL"):
                    r["sign_function"], r["function_rule"] = "SYLL", "gloss"
            # lexical classifier word at the head of an entry
            if is_lex and wi_line == 0 and len(words) > 1 and \
                    len(wrows) == 1 and wrows[0]["reading"] in LEX_CLASSIFIER \
                    and not word_lang.startswith("akk"):
                wrows[0]["sign_function"] = "DET"
                wrows[0]["function_rule"] = "lex:classifier_word_entry_head"
                wrows[0]["needs_check"] = True
            # manual word-level decisions (reviewed by Claude, to be verified)
            ov = OVERRIDES.get((p, w["raw"])) or OVERRIDES.get(("*", w["raw"]))
            if ov:
                pat, chk, note = ov
                if len(pat) != len(wrows):
                    print(f"[WARN] override length mismatch {p} {w['raw']}: "
                          f"{pat} vs {len(wrows)} signs")
                else:
                    for r, c in zip(wrows, pat):
                        r["sign_function"] = CODE[c]
                        r["function_rule"] = "manual_word_override"
                        r["needs_check"] = chk
                        r["_note"] = note
                        r["_reviewed"] = True
                    USED.add((p, w["raw"]))
            for si, r in enumerate(wrows, 1):
                ru_id = f"{word_id}_s{si}"
                fn = r["sign_function"]
                dmg = damage_state(r["_pc"], r["flags"])
                present = not (r["broken"] or r["supplied"] or r["erased"])
                include = int(fn in ("LOGO", "SYLL") and present)
                reasons = []
                if r["needs_check"]:
                    reasons.append("function:" + r["function_rule"])
                if r["resolution"] in ("unresolved", "sign_name_not_in_osl",
                                       "qualifier_not_in_osl"):
                    reasons.append("sign:" + r["resolution"])
                if r["n_candidates"] > 1:
                    reasons.append("sign:ambiguous_reading")
                if r["corrected"]:
                    reasons.append("sign:editor_correction")
                alts = ""
                if r["n_candidates"] > 1:
                    alts = "; ".join(c[0] for c in osl.lookup_value(r["reading"])[1:4])
                base = {
                    "artifact_id": p, "corpus_group": meta["corpus_group"],
                    "genre_cdli": meta["genres"], "provenience": meta["provenience"],
                    "is_school_text": meta["is_school_text"], "atf_lang": atf_lang,
                    "surface": ln["surface"], "column": ln["column"],
                    "line_num": ln["line_num"], "line_ref": line_ref,
                    "word_id": word_id, "word_index": word_index,
                    "raw_word": w["raw"], "sign_index": si,
                    "reading_unit_id": ru_id, "raw_sign": r["raw_sign"],
                    "reading": r["reading"], "sign_name": r["sign_name"],
                    "sign_function": fn, "include_in_analysis": include,
                    "word_lang": r["lang"] or word_lang, "damage_state": dmg,
                    "corrected": int(r["corrected"]),
                    "resolution": r["resolution"],
                    "n_candidates": r["n_candidates"], "alt_candidates": alts,
                    "function_rule": r["function_rule"],
                    "needs_check": int(bool(reasons)),
                    "check_reason": " | ".join(reasons),
                    "annotation_status": ("claude_word_override" if r.get("_reviewed")
                                          else "claude_type_review"),
                    "human_verified": "", "human_correction_note": "",
                    "annotator_note": r.get("_note", ""),
                }
                comps = split_components(r["sign_name"], osl) \
                    if r["sign_name"] else None
                if comps:
                    for cp, (cname, code, ucun) in enumerate(comps, 1):
                        row_counter[0] += 1
                        rows.append({**base, "gold_row_id": row_counter[0],
                                     "is_compound": "COMPOUND",
                                     "component_position": cp,
                                     "component_name": cname,
                                     "unicode_id": code, "sign_grapheme": ucun})
                else:
                    row_counter[0] += 1
                    rows.append({**base, "gold_row_id": row_counter[0],
                                 "is_compound": "COMPOUND"
                                 if r["sign_name"].startswith("|") else "SIMPLE",
                                 "component_position": "",
                                 "component_name": "",
                                 "unicode_id": r["unicode_id"],
                                 "sign_grapheme": r["ucun"]})
    return rows


def apply_corrections(rows, path):
    """corrections.csv (Step 6.8, human decisions that survive a rebuild):
    columns scope (type|token), key, field, value, note, still_check.
    type-scope key = '<word_lang>|<raw_word>|<sign_index>' or
                     '<word_lang>|*|<reading>' ; token-scope key = reading_unit_id."""
    if not path or not path.exists():
        return rows
    with open(path, encoding="utf-8") as f:
        corr = list(csv.DictReader(f))
    for c in corr:
        for r in rows:
            if c["scope"] == "token":
                hit = r["reading_unit_id"] == c["key"]
            else:
                lang, rw, x = c["key"].split("|")
                if rw == "*":
                    hit = r["word_lang"].startswith(lang) and r["reading"] == x
                else:
                    hit = (r["word_lang"].startswith(lang) and
                           r["raw_word"] == rw and str(r["sign_index"]) == x)
                if c.get("only_function") and r["sign_function"] != c["only_function"]:
                    hit = False
            if hit:
                r[c["field"]] = c["value"]
                if c["field"] == "sign_function":
                    present = r["damage_state"].split(",")[0] not in \
                        ("restored", "supplied", "superfluous")
                    r["include_in_analysis"] = int(
                        c["value"] in ("LOGO", "SYLL") and present)
                # corrections.csv holds the HUMAN decisions of Step 6.8
                r["annotation_status"] = "human_correction"
                r["human_verified"] = "1"
                r["needs_check"] = int(c.get("still_check", "0") == "1")
                r["human_correction_note"] = (r.get("human_correction_note", "") +
                                              " " + c["note"]).strip()
    return rows


def main():
    OSL_PATH = sys.argv[1]
    OUT = Path(sys.argv[2])
    CORR = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    osl = OSLIndex(OSL_PATH)
    import os
    if not os.environ.get("NO_OVERRIDES"):
        load_overrides(Path(__file__).parent / "word_overrides.csv")
    with open(OUT / "gold_sample_tablets.csv", encoding="utf-8") as f:
        sample = list(csv.DictReader(f))
    rows, counter = [], [0]
    for m in sample:
        block = (OUT / "gold_corpus_atf" / f"{m['p_number']}.atf").read_text(
            encoding="utf-8")
        rows += process_tablet(m["p_number"], block, m, osl, counter)
    rows = apply_corrections(rows, CORR)
    unused = set(OVERRIDES) - USED
    if unused:
        print("[WARN] unused overrides:", sorted(unused))
    with open(OUT / "gold_signs.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("rows:", len(rows))


if __name__ == "__main__":
    main()
