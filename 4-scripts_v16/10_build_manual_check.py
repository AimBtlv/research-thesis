#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 10_build_manual_check.py
Description: Workflow Stage 1, Step 6.0 (manual check of the catalogue and of
             the parser, before the gold standard). Builds one CSV file per
             problem (P01-P14) for the manual check by the supervisor, from
             the outputs of Steps 1-5 and osl.asl:
               P01 modifier lost in a name split          (manual)
               P02 name = compound and simple sign        (auto-fixed, confirm)
               P03 compound without an attested reading   (manual)
               P04 compound nested in a longer form       (manual)
               P05 guessed readings (inferred)            (one decision)
               P06 duplicated components                  (auto-fixed, confirm)
               P07 placeholder components X / O / ?       (manual)
               P08 span of readings merged into a compound
                   whose glyphs differ from the separate readings (manual)
               P09 syllabary name without Unicode used in the corpus (manual)
               P10 OSL / catalogue reading conflicts      (manual)
               P11 syllabary / OSL sign disagreements     (manual)
               P12 unresolved tokens                      (manual)
               P13 compounds the script could not split   (optional)
               P14 control sample of the decompositions   (sample)
               P15 registered name with the code of another sign
                   (da -> A₂, ri, nam, u)                  (auto-fixed, confirm)
             Every row has corpus counts split into school / practical
             tablets and the main sites, because the thesis compares school
             and practical writing by place (Old Babylonian period only).
             The empty columns at the right end (decision ...) are filled in
             by hand. Output: output/manual_check_v2/P01_...csv ... P14_...csv
             and summary.json. Run AFTER 00_run_pipeline.py.
Author: Aima, prepared with Claude
Date: 2026-11-18
Version: 1.1 (2026-11-20: P09 OSL suggestions also by reading; P10 column
         relation: a @form of the same sign or really different signs; P12
         column kind_guess)
"""

import csv
import importlib.util
import json
import re
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
DP = ROOT / "2-dataset" / "DataProfile"
OUT = HERE / "output"
CAT = OUT / "step4" / "sign_catalogue_v13.csv"
CTAB = OUT / "step4" / "compound_form_reading_table_v13.csv"
CONFL = OUT / "step4" / "osl_reading_conflicts_v13.csv"
DISAG = OUT / "step1" / "step1_syllabary_osl_disagreements.csv"
SYLL = OUT / "step1" / "Syllabary_CM.csv"
TOKENS = OUT / "step5" / "atf_tokens.csv"
GRAPH = OUT / "step5" / "grapheme.csv"
WARN = OUT / "step5" / "warnings.csv"
OSL = DP / "step1" / "6_osl.asl"
UNICODE = DP / "step1" / "1_unicodeSigns.csv"
DEST = OUT / "manual_check_v2"

MAIN_SITES = ("Nippur", "Ur", "Shaduppum", "Sippar-Yahrurum", "Mari", "Larsa")
CODE_RE = re.compile(r"^U\+[0-9A-F]{4,6}( \[unverified\])?$")
SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


# ---------------------------------------------------------------- helpers
def load_module(name, file_name, stub_function_layer=False):
    """Load a pipeline script whose name starts with a digit."""
    if stub_function_layer and "function_layer" not in sys.modules:
        # 08 imports 08a at module level; the function layer is not needed here
        sys.modules["function_layer"] = types.ModuleType("function_layer")
    spec = importlib.util.spec_from_file_location(name, HERE / file_name)
    mod = importlib.util.module_from_spec(spec)
    if stub_function_layer:
        real = mod.__dict__
        src = (HERE / file_name).read_text(encoding="utf-8")
        src = src.replace('fl = _load_helper("function_layer", "08a_function_layer.py")',
                          'fl = None')
        exec(compile(src, str(HERE / file_name), "exec"), real)
        return mod
    spec.loader.exec_module(mod)
    return mod


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows, fields, prefix):
    DEST.mkdir(parents=True, exist_ok=True)
    for k, r in enumerate(rows, 1):
        r["check_id"] = f"{prefix}-{k:04d}"
    with open(DEST / name, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["check_id"] + fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"  {name}: {len(rows)} rows")
    return len(rows)


def is_code(v):
    return bool(CODE_RE.match(v.strip()))


def clean_lists(s):
    return "; ".join(re.sub(r"\s*\[.*?\]", "", x).strip() for x in s.split(";") if x.strip())


# ------------------------------------------------------------ corpus data
def tablet_meta():
    """artifact_id -> (is_school_text, provenance) from grapheme.csv."""
    meta = {}
    with open(GRAPH, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["artifact_id"] not in meta:
                meta[r["artifact_id"]] = (r["is_school_text"], r["provenance"] or "(empty)")
    return meta


class Stats:
    """Corpus counts of one key: total, school, practical, sites, example."""
    __slots__ = ("n", "school", "pract", "sites", "example")

    def __init__(self):
        self.n = self.school = self.pract = 0
        self.sites = Counter()
        self.example = ""

    def add(self, p, line, meta):
        self.n += 1
        school, site = meta.get(p, ("", "(empty)"))
        if school == "1":
            self.school += 1
        else:
            self.pract += 1
        self.sites[site] += 1
        if not self.example:
            self.example = f"{p} {line}".strip()

    def cols(self):
        top = ", ".join(f"{s} {c}" for s, c in self.sites.most_common(4))
        return {"tokens_in_OB_corpus": self.n, "tokens_school": self.school,
                "tokens_practical": self.pract, "top_sites": top,
                "corpus_example": self.example}


EMPTY = Stats()


def token_stats(meta):
    """One pass over atf_tokens.csv."""
    by_name = defaultdict(Stats)          # resolved_name -> stats
    spans = defaultdict(Stats)            # (raw, compound) for multi-reading spans
    inferred = defaultdict(Stats)         # (raw, compound) for inferred matches
    unresolved = defaultdict(Stats)       # normalised raw token
    reading = defaultdict(Stats)          # normalised raw reading (atomic) -> stats
    reading_sign = defaultdict(Counter)   # normalised reading -> resolved names
    with open(TOKENS, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            p, line, kind = r["p_number"], r["line_num"], r["token_kind"]
            raw, res = r["raw_atf_token"], r["resolved_name"]
            if kind in ("atomic", "compound"):
                by_name[res].add(p, line, meta)
                key = raw.translate(SUB).lower()
                reading[key].add(p, line, meta)
                reading_sign[key][res] += 1
            if kind == "compound" and re.search(r"[-.]", raw):
                spans[(raw, res)].add(p, line, meta)
            if r["confidence"] == "inferred":
                inferred[(raw, res)].add(p, line, meta)
            if kind == "unresolved":
                unresolved[raw.translate(SUB).lower()].add(p, line, meta)
    return by_name, spans, inferred, unresolved, reading, reading_sign


# ------------------------------------------------------------------ main
def main():
    for p in (CAT, CTAB, TOKENS, GRAPH, OSL, UNICODE, SYLL):
        if not p.exists():
            sys.exit(f"[ERROR] missing input: {p}\n        run 00_run_pipeline.py first")

    m06 = load_module("p06", "06_build_sign_catalogue_v13.py")
    m07 = load_module("p07", "07_parse_atf_to_tokens_v14.py")
    m08 = load_module("p08", "08_tokens_to_grapheme_v14.py", stub_function_layer=True)

    print("[1] osl.asl, catalogue, compound table")
    unicode_ref = m06.load_unicode_reference(UNICODE)
    _, entity_v = m06.parse_osl(OSL, unicode_ref)        # fills FORM_INDEX, ALL_V_VALUES
    cat = read_csv(CAT)
    ctab = read_csv(CTAB)
    uid_name = {}
    for r in cat:
        if r["typePhonetic_Version"] == "Single Sign Reading" and r["unicode_id"]:
            uid_name.setdefault(r["unicode_id"].replace(" [unverified]", ""),
                                r.get("osl_form") or r["sign_name"])

    # compound entities of the catalogue: (sign_name, osl_form, compound_form) -> rows
    entities = defaultdict(list)
    for r in cat:
        if r["sign_structure"] == "compound" and r["compound_form"]:
            entities[(r["sign_name"], r["osl_form"], r["compound_form"])].append(r)
    first = {}
    for key in entities:
        first.setdefault(key[2], key)

    def comp_cols(rows):
        rows = sorted(rows, key=lambda r: int(r["component_position"] or 0))
        uids = [r["unicode_id"] for r in rows]
        return {"components_names": " + ".join(uid_name.get(u.replace(" [unverified]", ""), "?")
                                               for u in uids),
                "components_unicode": "; ".join(uids),
                "glyph": rows[0]["compound_grapheme"] if rows else "",
                "sign_lists": clean_lists(rows[0]["signList_analogue"]) if rows else ""}

    def method(cf):
        return "@useq" if entity_v.get(cf, {}).get("useq") else "name split (× / &)"

    def parent(key):
        return key[0] if key[1] else ""

    print("[2] corpus counts (atf_tokens.csv, grapheme.csv)")
    meta = tablet_meta()
    by_name, spans, inferred, unresolved, reading, reading_sign = token_stats(meta)
    summary = {}

    # P01 modifier lost ------------------------------------------------
    rows = []
    for key, crow in entities.items():
        cf = key[2]
        if key != first[cf] or method(cf) != "name split (× / &)":
            continue
        inner = cf.strip("|")
        op = "×" if "×" in inner else "&"
        dropped = []
        stored = comp_cols(crow)["components_names"].split(" + ")
        for part in inner.split(op):
            if "@" not in part or part in stored:
                continue
            if not (m06.lookup_component_uid(part, entity_v) in unicode_ref
                    or m06.lookup_component_uid(part, m06.FORM_INDEX)):
                dropped.append(f"{part} -> {re.sub(r'@[a-zA-Z0-9]+$', '', part)}")
        if dropped:
            rows.append({"compound_form": cf, "parent_sign": parent(key),
                         "modifier_dropped": "; ".join(dropped), **comp_cols(crow),
                         **by_name.get(cf, EMPTY).cols()})
    rows.sort(key=lambda r: -r["tokens_in_OB_corpus"])
    summary["P01"] = write_csv("P01_modifier_lost.csv", rows,
        ["compound_form", "parent_sign", "modifier_dropped", "components_names",
         "components_unicode", "glyph", "sign_lists", "tokens_in_OB_corpus", "tokens_school",
         "tokens_practical", "top_sites", "corpus_example",
         "decision", "correct_components", "comment"], "P01")

    # P02 name = compound and simple sign (auto-fixed in 06 v13.1) -------
    rows = []
    for r in cat:
        if r["structural_hint"] == "uid_via_same_name_sign":
            rows.append({"osl_form": r["osl_form"], "parent_sign": r["sign_name"],
                         "status": "auto-fixed (06 v13.1)", "new_unicode_id": r["unicode_id"],
                         "new_glyph": r["sign_grapheme"],
                         **by_name.get(r["osl_form"], EMPTY).cols()})
    if not rows:   # catalogue built by 06 v13: list the cases the fix will change
        registered = {r["sign_name"]: r["unicode_id"] for r in cat
                      if r["sign_source"] == "OSL" and not r["osl_form"] and r["unicode_id"]
                      and r["sign_structure"] in ("atomic", "atomic_with_decompositions")}
        for key, crow in entities.items():
            cf = key[2]
            if key[1] == cf and key[0] != cf and cf in registered:
                rows.append({"osl_form": cf, "parent_sign": key[0],
                             "status": "to be fixed by 06 v13.1",
                             "old_components": comp_cols(crow)["components_names"],
                             "new_unicode_id": registered[cf],
                             **by_name.get(cf, EMPTY).cols()})
    summary["P02"] = write_csv("P02_name_compound_and_simple.csv", rows,
        ["osl_form", "parent_sign", "status", "old_components", "new_unicode_id", "new_glyph",
         "tokens_in_OB_corpus", "tokens_school", "tokens_practical", "top_sites",
         "corpus_example", "decision", "comment"], "P02")
    p02_forms = {r["osl_form"] for r in rows}

    # P03 / P04 readings of compounds (nested check on whole components) --
    syll_names = sorted({r["sign_name"] for r in read_csv(SYLL)})
    p03, p04 = [], []
    for r in ctab:
        cf = r["compound_form"]
        if cf in p02_forms or r["reading_status"] == "ATTESTED_DIRECT":
            continue
        hidden_v = m06.ALL_V_VALUES.get(cf, []) if not entity_v.get(cf, {}).get("v_values") else []
        key = first.get(cf)
        base = {"compound_form": cf, "operator_in_name": operator(cf),
                **(comp_cols(entities[key]) if key else {}),
                "component_reading_inferred": r["component_reading_inferred"],
                **by_name.get(cf, EMPTY).cols()}
        if hidden_v:
            base["auto_fix"] = "06 v13.1: @v of another entry of the same name: " + " | ".join(hidden_v)
        nested = [n for n in syll_names if m06.is_nested_in(cf, n)][:5]
        if nested and not hidden_v:
            base["nested_in_forms"] = "; ".join(nested)
            p04.append(base)
        else:
            if r["reading_status"] == "NESTED_IN_LONGER_FORM" and not hidden_v:
                base["auto_fix"] = ("06 v13.1: old 'nested' match was accidental ("
                                    + r["nested_in_forms"][:80] + ")")
            p03.append(base)
    for lst in (p03, p04):
        lst.sort(key=lambda r: (-r["tokens_in_OB_corpus"], r["compound_form"]))
    common = ["compound_form", "operator_in_name", "components_names", "components_unicode",
              "glyph", "component_reading_inferred", "tokens_in_OB_corpus", "tokens_school",
              "tokens_practical", "top_sites", "corpus_example", "sign_lists", "auto_fix"]
    summary["P03"] = write_csv("P03_no_attested_reading.csv", p03,
        common + ["decision", "reading_by_professor", "source", "comment"], "P03")
    summary["P04"] = write_csv("P04_nested_in_longer_form.csv", p04,
        common[:1] + ["nested_in_forms"] + common[1:] +
        ["decision", "reading_by_professor", "source", "comment"], "P04")

    # P05 guessed readings: matches the parser actually made with them ----
    rows = []
    for (raw, cf), st in inferred.items():
        rows.append({"raw_atf_token": raw, "resolved_compound": cf,
                     **(comp_cols(entities[first[cf]]) if cf in first else {}), **st.cols()})
    rows.sort(key=lambda r: -r["tokens_in_OB_corpus"])
    summary["P05"] = write_csv("P05_inferred_matches.csv", rows,
        ["raw_atf_token", "resolved_compound", "components_names", "glyph",
         "tokens_in_OB_corpus", "tokens_school", "tokens_practical", "top_sites",
         "corpus_example", "decision", "correct_reading_or_signs", "comment"], "P05")

    # P06 duplicated components (auto-fixed in 08 v14.5) -----------------
    per_form = defaultdict(list)
    for key in entities:
        per_form[key[2]].append(key)
    rows = []
    for cf, keys in per_form.items():
        if len(keys) < 2:
            continue
        n_first = len(entities[keys[0]])
        n_all = sum(len(entities[k]) for k in keys)
        uid_sets = {tuple(r["unicode_id"] for r in sorted(entities[k],
                    key=lambda r: int(r["component_position"] or 0))) for k in keys}
        rows.append({"compound_form": cf, "entries_in_osl": len(keys),
                     "entries": "; ".join(f"{k[0]} / {k[1] or '(sign)'}" for k in keys),
                     "components_before": n_all, "components_after": n_first,
                     "extra_rows_per_token_before": n_all - n_first,
                     "same_components_in_all_entries": "yes" if len(uid_sets) == 1 else "NO",
                     "status": "auto-fixed (08 v14.5)",
                     **comp_cols(entities[keys[0]]), **by_name.get(cf, EMPTY).cols()})
    rows.sort(key=lambda r: -r["tokens_in_OB_corpus"])
    summary["P06"] = write_csv("P06_duplicated_components.csv", rows,
        ["compound_form", "entries_in_osl", "entries", "components_names", "glyph",
         "components_before", "components_after", "extra_rows_per_token_before",
         "same_components_in_all_entries", "status",
         "tokens_in_OB_corpus", "tokens_school", "tokens_practical", "top_sites",
         "corpus_example", "decision", "comment"], "P06")

    # P07 placeholder components -----------------------------------------
    rows = []
    for cf, key in first.items():
        uids = [r["unicode_id"] for r in entities[key]]
        if all(is_code(u) for u in uids):
            continue
        st = by_name.get(cf, EMPTY)
        multi = any(re.search(r"[-.]", raw) for (raw, c) in spans if c == cf)
        rows.append({"compound_form": cf, "parent_sign": parent(key), "method": method(cf),
                     **comp_cols(entities[key]),
                     "osl_v": " | ".join(entity_v.get(cf, {}).get("v_values", [])),
                     "auto_fix": ("07 v14.4: spans of several readings split into simple signs; "
                                  if multi else "") + "08 v14.5: placeholder stored without code",
                     **st.cols()})
    rows.sort(key=lambda r: -r["tokens_in_OB_corpus"])
    summary["P07"] = write_csv("P07_placeholder_components.csv", rows,
        ["compound_form", "parent_sign", "method", "components_names", "components_unicode",
         "glyph", "osl_v", "auto_fix", "tokens_in_OB_corpus", "tokens_school",
         "tokens_practical", "top_sites", "corpus_example", "sign_lists",
         "decision", "correct_components", "comment"], "P07")
    placeholder = {r["compound_form"] for r in rows}

    # P08 span merged, glyphs differ from the separate readings ----------
    simple = m07.load_simple_dict(CAT)
    att, inf, src = m07.load_compound_dicts(CTAB)
    m07.NAME_INDEX.update(m07.build_name_index(CAT))
    atomic_lookup, comp_lookup = m08.load_sign_lookup(CAT)
    rows = []
    for (raw, cf), st in spans.items():
        if cf in placeholder:
            continue
        pieces = [x for x in re.split(r"[-.]", raw) if x]
        sep_names, sep_uids = [], []
        for x in pieces:
            name, kind, _ = m07.resolve_single_piece(x, simple, {}, {})
            sep_names.append(name if kind == "atomic" else f"{x}?")
            sep_uids.append(atomic_lookup.get(name, {}).get("unicode_id", "") if kind == "atomic" else "")
        comp_uids = [u for _, u, _ in comp_lookup.get(cf, [])]
        if sep_uids == comp_uids or "" in sep_uids:
            continue
        rows.append({"raw_atf_token": raw, "resolved_compound": cf,
                     "compound_unicode": "; ".join(comp_uids),
                     "compound_glyph": "".join(g for _, _, g in comp_lookup.get(cf, [])),
                     "separate_signs": " + ".join(sep_names),
                     "separate_unicode": "; ".join(sep_uids),
                     "separate_glyph": "".join(atomic_lookup.get(n, {}).get("sign_grapheme", "")
                                               for n in sep_names),
                     "reading_source": src.get(cf, ""), **st.cols()})
    rows.sort(key=lambda r: -r["tokens_in_OB_corpus"])
    summary["P08"] = write_csv("P08_span_glyphs_differ.csv", rows,
        ["raw_atf_token", "resolved_compound", "compound_unicode", "compound_glyph",
         "separate_signs", "separate_unicode", "separate_glyph", "reading_source",
         "tokens_in_OB_corpus", "tokens_school", "tokens_practical", "top_sites",
         "corpus_example", "decision", "comment"], "P08")

    # P09 syllabary-only names without Unicode used in the corpus --------
    # value -> OSL entries, read line by line from osl.asl, so that a @v that
    # stands after a @form line is also found (sipa of |PA.LU|)
    value_owner = defaultdict(set)
    current = None
    with open(OSL, encoding="utf-8") as fh:
        for line in fh:
            mm = re.match(r"^@(sign|form)([+-]?)[ \t]+(\S+)", line)
            if mm:
                current = None if mm.group(2) == "-" else mm.group(3)
                continue
            if line.startswith("@end sign"):
                current = None
                continue
            mm = re.match(r"^@v[ \t]+(\S+)\s*$", line)
            if mm and current and not mm.group(1).startswith("%"):
                value_owner[mm.group(1).rstrip("?").translate(SUB).lower()].add(current)
    norm_osl = {m06.normalize_name(n).upper(): n for n in entity_v}
    no_code = {}
    for r in cat:
        if r["typePhonetic_Version"] == "Single Sign Reading" and not r["unicode_id"]:
            no_code.setdefault(r["sign_name"], r)
    rows = []
    for name, r in no_code.items():
        st = by_name.get(name)
        if not st or not st.n:
            continue
        sugg = []
        if name.translate(SUB).upper() in norm_osl:
            sugg.append(f"same name in OSL: {norm_osl[name.translate(SUB).upper()]}")
        readings_used = Counter()
        for key, c in reading_sign.items():
            if name in c:
                readings_used[key] += c[name]
        # OSL entries that have the NAME or one of the READINGS as a value
        own = set(value_owner.get(name.translate(SUB).lower(), set()))
        for key in readings_used:
            own |= value_owner.get(key, set())
        if own:
            sugg.append("OSL value of: " + "; ".join(sorted(own)[:4]))
        rows.append({"sign_name": name, "sign_source": r["sign_source"],
                     "readings_in_corpus": ", ".join(f"{k} {v}" for k, v in readings_used.most_common(4)),
                     "osl_suggestion": " / ".join(sugg), **st.cols()})
    rows.sort(key=lambda r: -r["tokens_in_OB_corpus"])
    summary["P09"] = write_csv("P09_syllabary_name_without_unicode.csv", rows,
        ["sign_name", "sign_source", "readings_in_corpus", "osl_suggestion",
         "tokens_in_OB_corpus", "tokens_school", "tokens_practical", "top_sites",
         "corpus_example", "decision", "osl_sign", "comment"], "P09")

    # P10 OSL / catalogue reading conflicts ------------------------------
    # relation of the two signs in osl.asl: is the OSL sign only a @form
    # (variant) of the catalogue sign, or are they really different signs?
    form_parent = defaultdict(set)
    current = None
    with open(OSL, encoding="utf-8") as fh:
        for line in fh:
            mm = re.match(r"^@(sign|form)([+-]?)[ \t]+(\S+)", line)
            if not mm:
                continue
            if mm.group(1) == "sign":
                current = None if mm.group(2) == "-" else mm.group(3)
            elif current and mm.group(2) != "-":
                form_parent[mm.group(3)].add(current)

    def relation(osl_sign, cat_sign):
        if cat_sign in form_parent.get(osl_sign, set()):
            return "OSL sign is a @form of the catalogue sign"
        if osl_sign in form_parent.get(cat_sign, set()):
            return "catalogue sign is a @form of the OSL sign"
        if form_parent.get(osl_sign, set()) & form_parent.get(cat_sign, set()):
            return "both are @forms of one sign"
        return "different signs"

    rows = []
    if CONFL.exists():
        for r in read_csv(CONFL):
            key = r["reading"].translate(SUB).lower()
            st = reading.get(key, EMPTY)
            used = reading_sign.get(key, Counter())
            rows.append({**r, "relation": relation(r["osl_sign"], r["catalogue_sign"]),
                         "osl_sign_is_form_of": "; ".join(sorted(form_parent.get(r["osl_sign"], set()))),
                         "parser_resolves_to": ", ".join(f"{n} {c}" for n, c in used.most_common(3)),
                         **st.cols()})
    # real conflicts (different signs) first, then by frequency
    rows.sort(key=lambda r: (r["relation"] != "different signs", -r["tokens_in_OB_corpus"], r["reading"]))
    summary["P10"] = write_csv("P10_osl_reading_conflicts.csv", rows,
        ["reading", "osl_sign", "catalogue_sign", "relation", "osl_sign_is_form_of",
         "parser_resolves_to", "tokens_in_OB_corpus",
         "tokens_school", "tokens_practical", "top_sites", "corpus_example",
         "decision", "comment"], "P10")

    # P11 syllabary / OSL disagreements of Step 1.2 ----------------------
    rows = []
    if DISAG.exists():
        for r in read_csv(DISAG):
            st = Stats()
            for nm in r["osl_sign"].split(" / "):
                s2 = by_name.get(nm.strip())
                if s2:
                    st.n += s2.n; st.school += s2.school; st.pract += s2.pract
                    st.sites.update(s2.sites); st.example = st.example or s2.example
            rows.append({**r, "step1_decision": r.pop("decision"), **st.cols()})
    summary["P11"] = write_csv("P11_syllabary_osl_disagreements.csv", rows,
        ["unicode_id", "sign_grapheme", "unicodeTrLit", "syllabary_sign", "osl_sign",
         "step1_decision", "tokens_in_OB_corpus", "tokens_school", "tokens_practical",
         "top_sites", "corpus_example", "decision", "comment"], "P11")

    # P12 unresolved tokens ----------------------------------------------
    def kind_guess(t):
        """Rough first sorting for the expert (not a decision)."""
        if re.fullmatch(r"[^()]+\((?:[^()]+)\)", t):
            return "QUALIFIER reading(SIGN)"
        if re.search(r"[{}()<>\[\]…%]", t) or t in ("|", "x|", "|x"):
            return "MARKUP or broken bracket"
        if re.match(r"^(rec|lak|zatu|bau|elles|abzl|mzl|kwu)\d", t):
            return "SIGN-LIST NUMBER"
        if re.search(r"[a-zšŋ]x(\(|$)", t) or "|" in t:
            return "x-INDEX or SIGN NAME"
        return "READING"

    rows = [{"normalized_token": k, "kind_guess": kind_guess(k), **st.cols()}
            for k, st in unresolved.items()]
    rows.sort(key=lambda r: -r["tokens_in_OB_corpus"])
    summary["P12"] = write_csv("P12_unresolved_tokens.csv", rows,
        ["normalized_token", "kind_guess", "tokens_in_OB_corpus", "tokens_school", "tokens_practical",
         "top_sites", "corpus_example", "decision", "sign_or_reading", "comment"], "P12")

    # P13 compounds the script could not split ---------------------------
    rows, seen = [], set()
    for r in cat:
        nm = r["osl_form"] or r["sign_name"]
        if r["sign_source"] != "OSL" or r["sign_structure"] != "not_identified" or nm in seen:
            continue
        if not re.search(r"[×&]", nm):
            continue
        seen.add(nm)
        reason = ("nested parentheses (compound inside compound)" if "(" in nm
                  else "component not found as @sign / @form")
        rows.append({"entity": nm, "parent_sign": r["sign_name"] if r["osl_form"] else "",
                     "hint_in_catalogue": r["structural_hint"], "reason": reason,
                     "sign_lists": clean_lists(r["signList_analogue"]),
                     **by_name.get(nm, EMPTY).cols()})
    rows.sort(key=lambda r: (-r["tokens_in_OB_corpus"], r["entity"]))
    summary["P13"] = write_csv("P13_compound_unresolved.csv", rows,
        ["entity", "parent_sign", "hint_in_catalogue", "reason", "sign_lists",
         "tokens_in_OB_corpus", "decision", "correct_components", "comment"], "P13")

    # P14 control sample of the decompositions ---------------------------
    rows = []
    useq_n = 0
    for cf, key in sorted(first.items(), key=lambda kv: -by_name.get(kv[0], EMPTY).n):
        st = by_name.get(cf, EMPTY)
        if not st.n or cf in placeholder:
            continue
        m = method(cf)
        if m == "@useq":
            if useq_n >= 30:
                continue
            useq_n += 1
            part = "C (@useq sample)"
        else:
            part = "B (name split, in corpus)"
        rows.append({"compound_form": cf, "part": part, "method": m, "parent_sign": parent(key),
                     **comp_cols(entities[key]), **st.cols()})
    summary["P14"] = write_csv("P14_decomposition_control.csv", rows,
        ["compound_form", "part", "method", "parent_sign", "components_names",
         "components_unicode", "glyph", "sign_lists", "tokens_in_OB_corpus", "tokens_school",
         "tokens_practical", "top_sites", "corpus_example",
         "decision", "correct_components", "comment"], "P14")

    # P15 registered name took the code of a @form row of another sign ---
    registered = {r["sign_name"] for r in cat if not r.get("osl_form")}
    old_first, own = {}, {}
    for r in cat:
        if r["typePhonetic_Version"] != "Single Sign Reading":
            continue
        f = r.get("osl_form", "")
        name = f if f and f in registered else r["sign_name"]
        old_first.setdefault(name, r)
        if not f:
            own.setdefault(r["sign_name"], r)
    rows = []
    for name, r_old in old_first.items():
        r_own = own.get(name)
        if not r_own or not r_own["unicode_id"] or r_old["unicode_id"] == r_own["unicode_id"]:
            continue
        rows.append({"sign_name": name, "old_unicode_id": r_old["unicode_id"],
                     "old_glyph": r_old["sign_grapheme"],
                     "old_taken_from": f"{r_old['sign_name']} / @form {r_old['osl_form']}",
                     "new_unicode_id": r_own["unicode_id"], "new_glyph": r_own["sign_grapheme"],
                     "status": "auto-fixed (08 v14.5)", **by_name.get(name, EMPTY).cols()})
    rows.sort(key=lambda r: -r["tokens_in_OB_corpus"])
    summary["P15"] = write_csv("P15_wrong_code_of_registered_name.csv", rows,
        ["sign_name", "old_unicode_id", "old_glyph", "old_taken_from", "new_unicode_id",
         "new_glyph", "status", "tokens_in_OB_corpus", "tokens_school", "tokens_practical",
         "top_sites", "corpus_example", "decision", "comment"], "P15")

    with open(DEST / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(f"[3] done -> {DEST}")


def operator(cf):
    inner = cf.strip("|")
    ops = {o for o in ".×&+" if o in inner}
    if not ops:
        return "other"
    if len(ops) > 1:
        return "mixed"
    return ops.pop()


if __name__ == "__main__":
    main()
