#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 08a_function_layer.py
Description: Workflow Stage 1, Step 5.2 (helper of 08_tokens_to_grapheme_v14.py).
             Gives every token of atf_tokens.csv the function of its sign
             (LOGO / SYLL / DET / NUM / UNCLEAR) BY LANGUAGE AND CONTEXT,
             with exactly the rules of the gold standard:
               - each tablet is labelled with the gold code itself
                 (08b_goldlib.py = goldlib.py of the gold package, copied unchanged:
                 tokenize_line -> resolve_piece -> mark_dn -> label_function,
                 plus the lexical-classifier and gloss rules of build_gold.py;
                 the manual word overrides of the gold are NOT used);
               - the gold signs and the pipeline tokens of the same tablet
                 are aligned by their readings (difflib), so every token
                 gets the function of the sign(s) it covers.
             The language of a tablet is decided as in the gold
             (select_sample.py): the '#atf: lang' line; else Sumerian for
             '#atf: use lexical'; else the CDLI 'languages' field. If it is
             still unknown, or a token cannot be aligned, the old letter-case
             rule is used as a fallback (function_rule 'fallback:letter_case').
Author: Aima, prepared with Claude
Date: 2026-11-11
Version: 1.0
"""

import re
from collections import Counter
from difflib import SequenceMatcher

import importlib.util
import sys
from pathlib import Path


def _load_goldlib():
    """08b_goldlib.py starts with a digit, so it is loaded by its path."""
    if "goldlib" in sys.modules:
        return sys.modules["goldlib"]
    path = Path(__file__).resolve().parent / "08b_goldlib.py"
    spec = importlib.util.spec_from_file_location("goldlib", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["goldlib"] = module
    spec.loader.exec_module(module)
    return module


_gl = _load_goldlib()
OSLIndex, iter_text_lines, tokenize_line = _gl.OSLIndex, _gl.iter_text_lines, _gl.tokenize_line
resolve_piece, label_function = _gl.resolve_piece, _gl.label_function
to_unicode_reading, to_ascii_key = _gl.to_unicode_reading, _gl.to_ascii_key
split_atf_tablets = _gl.split_atf_tablets

# --- constants copied unchanged from build_gold.py (gold package v2_1) ---
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
AKK_PN_LOGO = {"dumu", "lu₂", "dingir", "ARAD", "ARAD₂", "puzur₄", "geme₂",
               "nur₂"}
LEX_CLASSIFIER = {"ŋeš", "giš", "geš", "na₄", "kuš", "tug₂", "urudu",
                  "uruda", "dug", "u₂", "zabar", "ku₆", "mušen"}


def mark_dn(word_rows, akk=True):
    """Copied unchanged from build_gold.py: Sumerian DN after {d} -> LOGO;
    in Akkadian texts unlisted DNs -> SYLL, PN logograms, plural markers."""
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
                word_rows[k + 1]["_force"] = ("SYLL",
                                              "akk:divine_name_unlisted_syllabic",
                                              True)
    for k, r in enumerate(word_rows if akk else []):
        if not r["logo"] and not r["det"] and r["reading"] in AKK_PN_LOGO and \
                len(word_rows) > 1 and "_force" not in r and \
                (k == 0 or word_rows[k - 1]["det"]):
            r["_force"] = ("LOGO", "akk:pn_logographic_element", True)
        if r["logo"] and r["reading"] == "meš" and k > 0:
            r["_force"] = ("DET", "akk:plural_marker_meš", True)


def tablet_language(block: str, cdli_languages: str) -> str:
    """Base language of a tablet, decided as in select_sample.py."""
    langs = Counter(ln["base_lang"] for ln in iter_text_lines(block))
    lang = langs.most_common(1)[0][0] if langs else ""
    if lang not in ("sux", "akk") and "#atf: use lexical" in block:
        return "sux"
    if lang not in ("sux", "akk"):
        cdli = (cdli_languages or "").lower()
        if cdli.startswith("sumerian"):
            return "sux"
        if cdli.startswith("akkadian"):
            return "akk"
    return lang if lang in ("sux", "akk") else ""


def label_tablet(block: str, atf_lang: str, is_lexical: bool, osl: OSLIndex) -> list:
    """Gold labelling of one tablet (build_gold.process_tablet without the
    manual word overrides). Returns the list of non-determinative signs in
    text order: dicts with key, function, rule, needs_check, line_ref."""
    out = []
    for ln in iter_text_lines(block):
        words = tokenize_line(ln["content"])
        line_ref = f"{ln['surface'][:3]}:{ln['column']}:{ln['line_num']}"
        for wi_line, w in enumerate(words):
            if not w["pieces"]:
                continue
            wrows = []
            for pc in w["pieces"]:
                res = resolve_piece(pc["text"], osl)
                if res["kind"] == "gap":
                    continue
                wrows.append({**res, "det": pc["det"], "phon_compl": pc["phon_compl"],
                              "logo": pc["logo"], "broken": pc["broken"],
                              "gloss": pc.get("gloss", False),
                              "lang": pc["lang"] or atf_lang, "raw_sign": pc["text"]})
            if not wrows:
                continue
            word_lang = wrows[0]["lang"] or atf_lang or "sux"
            wrows[-1]["_trunc"] = bool(re.search(r"(\.\.\.|…|x)\]?#?\??$", w["raw"]))
            mark_dn(wrows, akk=word_lang.startswith("akk"))
            label_function(wrows, word_lang)
            for r in wrows:
                if "_force" in r and r["sign_function"] in ("LOGO", "SYLL", "UNCLEAR"):
                    r["sign_function"], r["function_rule"], r["needs_check"] = r["_force"]
                if r["gloss"] and r["sign_function"] in ("LOGO", "SYLL"):
                    r["sign_function"], r["function_rule"] = "SYLL", "gloss"
            if is_lexical and wi_line == 0 and len(words) > 1 and len(wrows) == 1 \
                    and wrows[0]["reading"] in LEX_CLASSIFIER \
                    and not word_lang.startswith("akk"):
                wrows[0]["sign_function"] = "DET"
                wrows[0]["function_rule"] = "lex:classifier_word_entry_head"
                wrows[0]["needs_check"] = True
            for r in wrows:
                if r["det"] or r["phon_compl"]:
                    continue          # the pipeline keeps braces out of its tokens
                out.append({"key": reading_key(r.get("reading") or r.get("reading_atf", "")),
                            "function": r["sign_function"],
                            "rule": r["function_rule"],
                            "needs_check": int(bool(r["needs_check"])),
                            "line_ref": line_ref})
    return out


def reading_key(text: str) -> str:
    """Comparable key for a reading on both sides (gold piece / pipeline piece)."""
    t = re.sub(r"[\[\]<>#?!*⌈⌉⸢⸣]", "", text or "")
    t = re.sub(r"\(.*\)$", "", t) if not re.match(r"^[\dn]", t) else t   # reading(SIGN) -> reading
    return to_ascii_key(to_unicode_reading(t)).replace("ʾ", "")


def token_pieces(raw: str) -> list:
    """Pieces of one pipeline token (a compound span 'ku3-babbar' has two)."""
    if re.match(r"^[\dn][\d/+]*\(", raw):           # numeral 1(diš), n+1(aš)
        return [raw]
    parts = [p for p in re.split(r"[-.]", raw) if p]
    return parts or [raw]


def align_functions(tokens: list, gold_signs: list) -> list:
    """tokens: list of (raw_atf_token, token_kind) of one tablet, in order.
    Returns, per token, (function, rule, needs_check, line_ref) or None."""
    pipe_keys, owner = [], []
    for t_index, (raw, kind) in enumerate(tokens):
        if kind == "broken":
            continue
        for piece in token_pieces(raw):
            pipe_keys.append(reading_key(piece))
            owner.append(t_index)
    gold_keys = [g["key"] for g in gold_signs]
    matched = {}
    sm = SequenceMatcher(None, pipe_keys, gold_keys, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for d in range(i2 - i1):
                matched.setdefault(owner[i1 + d], []).append(gold_signs[j1 + d])
    result = []
    for t_index in range(len(tokens)):
        g = matched.get(t_index)
        if not g:
            result.append(None)
            continue
        fns = [x["function"] for x in g]
        rule = g[0]["rule"] if len(set(fns)) == 1 else "compound_span:first_sign|" + g[0]["rule"]
        result.append((fns[0], rule, int(any(x["needs_check"] for x in g) or len(set(fns)) > 1),
                       g[0]["line_ref"]))
    return result


def load_atf_blocks(atf_source) -> dict:
    """p_number -> ATF block, from one file or a folder of .atf files."""
    src = Path(atf_source)
    files = [src] if src.is_file() else sorted(src.glob("**/*.atf"))
    blocks = {}
    for f in files:
        for p, b in split_atf_tablets(f.read_text(encoding="utf-8", errors="replace")):
            blocks.setdefault(p, b)
    return blocks
