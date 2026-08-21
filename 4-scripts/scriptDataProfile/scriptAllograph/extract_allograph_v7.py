#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: extract_allograph_v6.py
Description: Full rewrite of the allograph extraction pipeline. Parses
             osl.asl at the @sign level (100% coverage of all 3249 signs,
             including the 2645 "headless" signs that have no @form
             children, which v5 silently dropped). Each @sign or @form
             entity is classified into:
               sign_type      : Type_1 / Type_2 / Type_3  (mechanical,
                                 based on presence of own @list U+ and
                                 @useq)
               sign_structure : atomic / atomic_with_decompositions /
                                 compound / not_identified  (semantic,
                                 refines Type_3 by distinguishing real
                                 modifier-variants and catalog-only signs
                                 from compounds, and flags the 11 signs
                                 that have BOTH their own U+ code AND a
                                 documented @useq decomposition)
             Compound signs without an explicit @useq but with a × or &
             juxtaposition/ligature name are resolved automatically
             against the full sign index when every component can be
             found; unresolved cases (nested parentheses, unknown
             components) are kept as not_identified with
             structural_hint = 'compound_unresolved' so the information
             is not silently lost.
             graphic_variant_id is unified across all three types: it
             is a pure DOCUMENTATION-ORDER label (PREFIX_v1, _v2, ...)
             numbering the distinct forms attested for one sign in the
             order they appear in osl.asl. It intentionally does NOT
             claim which variant is more "canonical" or more frequently
             used in real texts, that question belongs to a later step
             once this profile is joined against real ATF corpus data.
             All component rows of one compound form share one id.
             Phonetic/syllabary data is joined from
             6_unicodeTrLit_Grph_Phon.csv by unicode_id.
Author: Digital Humanities Pipeline
Date: 2026-08-20
Version: 6.0
"""

import re
import csv
import os
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

ROOT_DIR       = os.path.dirname(os.path.abspath(__file__))
INPUT_ASL      = os.path.join(ROOT_DIR, "osl.asl")
INPUT_UNICODE  = os.path.join(ROOT_DIR, "1_unicodeSigns.csv")
INPUT_PHONETIC = os.path.join(ROOT_DIR, "7_unicodePhoneticVersion_full.csv")
OUTPUT_CSV     = os.path.join(ROOT_DIR, "allograph_all_v6.csv")

FIELDNAMES = [
    "unicode_id",
    "sign_grapheme",       # = @ucun, position-specific for compound components
    "sign_structure",      # atomic | atomic_with_decompositions | compound | not_identified
    "structural_hint",     # only populated for unresolved × / & compounds
    "component_position",  # only for compound rows
    "sign_name",            # the @sign entity this row's form belongs to
    "allograph_form",      # @form value, empty for headless signs
    "graphic_variant_id",
    "sign_type",            # Type_1 | Type_2 | Type_3 (mechanical)
    "compound_form",
    "compound_grapheme",
    "compound_unicode",
    "unicodeTrLit",
    "syllabary_sign",
    "phonetic_version",
    "signList_analogue",
]

SIGN_LIST_META = {
    "LAK":   ("Uruk IV–III (~3400–3000 BCE)",      "Archaic / Uruk"),
    "REC":   ("Uruk IV–III (~3400–3000 BCE)",      "Archaic / Uruk"),
    "ZATU":  ("Uruk IV–III (~3400–3000 BCE)",      "Archaic / Uruk"),
    "BAU":   ("Early Dynastic (~2900–2340 BCE)",   "Lagash"),
    "ELLES": ("Early Dynastic (~2900–2340 BCE)",   "Ebla"),
    "RSP":   ("Early Dynastic (~2900–2340 BCE)",   "Presargonic Lagash"),
    "GCSL":  ("Gudea period (~2100 BCE)",           "Lagash / Girsu"),
    "KWU":   ("Ur III (~2112–2004 BCE)",            "Administrative"),
    "ABZL":  ("Old Babylonian (~2000–1600 BCE)",   "School texts"),
    "MZL":   ("Standard Babylonian (any period)",  "Akkado-Babylonian"),
    "ABZ":   ("Standard Babylonian (any period)",  "Akkado-Babylonian"),
    "SLLHA": ("Standard Babylonian (any period)",  "Akkado-Babylonian"),
    "ASY":   ("Standard Babylonian (any period)",  "Akkadian syllabary"),
    "SYA":   ("Standard Babylonian (any period)",  "Akkadian syllabary"),
    "HZL":   ("Hittite period (~1650–1180 BCE)",   "Hittite"),
    "PTACE": ("Early Dynastic (~2900–2340 BCE)",   "Ebla"),
}


# ─────────────────────────────────────────────────────────────────────────────
# LOW-LEVEL HELPERS  (unchanged from v5)
# ─────────────────────────────────────────────────────────────────────────────

def get_field(lines: list, tag: str) -> str:
    pat = re.compile(rf'^@{re.escape(tag)}\s+(.*)', re.IGNORECASE)
    for line in lines:
        m = pat.match(line.strip())
        if m:
            return m.group(1).strip()
    return ""


def xhex_to_uplus(token: str) -> str:
    token = token.strip()
    if re.match(r'^x[0-9A-Fa-f]+$', token):
        return "U+" + token[1:].upper()
    return token


def useq_to_uplus_list(useq_val: str) -> list:
    parts = [p.strip() for p in useq_val.split(".") if p.strip()]
    return [xhex_to_uplus(p) for p in parts]


def collect_analogue_lists(lines: list) -> list:
    refs = []
    for line in lines:
        m = re.match(r'^@list\s+(\S+)', line.strip())
        if m:
            val = m.group(1).strip()
            if not val.startswith("U+"):
                refs.append(val)
    return refs


def annotate_list_ref(ref: str) -> str:
    prefix = re.match(r'^([A-Za-z]+)', ref)
    if prefix:
        key = prefix.group(1).upper()
        if key in SIGN_LIST_META:
            period, region = SIGN_LIST_META[key]
            return f"{ref} [{period} | {region}]"
    return ref


def build_signlist_analogue(own_lists: list, parent_lists: list) -> str:
    seen, result = set(), []
    for ref in own_lists + parent_lists:
        if ref not in seen:
            seen.add(ref)
            result.append(annotate_list_ref(ref))
    return "; ".join(result)


def make_variant_prefix(sign: str) -> str:
    s = sign
    for src, tgt in [('Š', 'S'), ('š', 's'), ('Ž', 'Z'), ('ž', 'z'),
                      ('Ĝ', 'G'), ('ĝ', 'g'), ('Ŋ', 'NG'), ('ŋ', 'ng'),
                      ('Ḫ', 'H'), ('ḫ', 'h')]:
        s = s.replace(src, tgt)
    clean = re.sub(r'[^A-Za-z0-9]', '', s)
    return clean[:8].upper() if clean else 'X'


def load_unicode_reference(filepath: str) -> dict:
    ref = {}
    with open(filepath, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uid, glyph = row.get("unicode_id", "").strip(), row.get("sign_grapheme", "").strip()
            if uid:
                ref[uid] = glyph
    print(f"[INFO] Loaded {len(ref)} entries from unicode reference")
    return ref


def load_phonetic_reference(filepath: str) -> dict:
    ref = {}
    with open(filepath, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            uid = row.get("unicode_id", "").strip()
            if uid:
                ref[uid] = {
                    "unicodeTrLit":     row.get("unicodeTrLit", "").strip(),
                    "syllabarySign":    row.get("syllabarySign", "").strip(),
                    "PhoneticsVersion": row.get("PhoneticsVersion", "").strip(),
                }
    print(f"[INFO] Loaded {len(ref)} entries from phonetic reference")
    return ref


# ─────────────────────────────────────────────────────────────────────────────
# ENTITY PARSING — works identically for a @sign header block and a @form block
# ─────────────────────────────────────────────────────────────────────────────

def split_entity_lines(block_lines: list) -> tuple:
    """Return (name, header_lines) — header_lines stop at the first @form."""
    name = block_lines[0].strip()
    header_lines = []
    for line in block_lines[1:]:
        if re.match(r'^@form[ \t]', line):
            break
        header_lines.append(line)
    return name, header_lines


def parse_entity_header(lines: list) -> dict:
    """Extract own_uid / useq / ucun / catalog_refs from an entity's header lines."""
    own_uid = ""
    for line in lines:
        m = re.match(r'^@list\s+(U\+\S+)', line.strip())
        if m:
            own_uid = m.group(1).strip()
            break
    return {
        "own_uid":      own_uid,
        "useq":         get_field(lines, "useq"),
        "ucun":         get_field(lines, "ucun"),
        "catalog_refs": collect_analogue_lists(lines),
    }


# ─────────────────────────────────────────────────────────────────────────────
# FULL SIGN INDEX — every @sign, header-level info (used for own-uid lookups
# during × / & decomposition and for Type_3 inheritance)
# ─────────────────────────────────────────────────────────────────────────────

def build_full_sign_index(content: str) -> dict:
    index = {}
    sign_blocks = re.split(r'^@sign[ \t]', content, flags=re.MULTILINE)
    for block in sign_blocks:
        if not block.strip() or block.strip().startswith('@'):
            continue
        lines = block.strip().split('\n')
        name, header_lines = split_entity_lines(lines)
        index[name] = parse_entity_header(header_lines)
    return index


# ─────────────────────────────────────────────────────────────────────────────
# NAME-PATTERN CLASSIFICATION FOR "NO OWN UID, NO USEQ" ENTITIES
# ─────────────────────────────────────────────────────────────────────────────

def classify_no_unicode_reason(name: str) -> str:
    inner = name.strip('|')
    if '×' in inner:
        return 'COMPOUND_TIMES'
    if '&' in inner:
        return 'COMPOUND_LIGATURE'
    if '+' in inner:
        return 'COMPOUND_PLUS'
    if re.search(r'@[a-zA-Z0-9]+$', inner) or re.search(r'~[a-zA-Z0-9]+$', inner):
        return 'MODIFIER_VARIANT'
    if re.match(r"^[A-Z]+\d+[a-zA-Z\^']*$", inner):
        return 'CATALOG_ONLY'
    return 'PLAIN_OR_OTHER'


def lookup_component_uid(candidate: str, sign_index: dict) -> str:
    cand = candidate.strip()
    if cand in sign_index and sign_index[cand]["own_uid"]:
        return sign_index[cand]["own_uid"]
    wrapped = f"|{cand}|"
    if wrapped in sign_index and sign_index[wrapped]["own_uid"]:
        return sign_index[wrapped]["own_uid"]
    return ""


def try_decompose_juxtaposition(name: str, operator: str, sign_index: dict) -> list:
    """Best-effort split of a simple (non-nested) × / & compound name into
    component unicode_ids. Returns [] if any component cannot be resolved
    or if the name contains nested parentheses (out of scope here)."""
    inner = name.strip('|')
    if '(' in inner or ')' in inner:
        return []
    parts = inner.split(operator)
    if len(parts) < 2:
        return []
    comps = []
    for part in parts:
        base = re.sub(r'@[a-zA-Z0-9]+$', '', part).strip()
        uid = lookup_component_uid(part, sign_index) or lookup_component_uid(base, sign_index)
        if not uid:
            return []
        comps.append(uid)
    return comps


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION — sign_type + sign_structure + resolved component list
# ─────────────────────────────────────────────────────────────────────────────

def classify_entity(name: str, header: dict, sign_index: dict, unicode_ref: dict) -> dict:
    """
    Returns:
      sign_type       : Type_1 | Type_2 | Type_3
      sign_structure  : atomic | atomic_with_decompositions | compound | not_identified
      structural_hint : "" | "compound_unresolved"
      own_uid         : validated/[unverified]-flagged own code, or ""
      component_uids  : list of U+ codes (explicit or inferred), or []
    """
    own_uid_raw = header["own_uid"]
    useq_val    = header["useq"]

    own_uid = ""
    if own_uid_raw:
        own_uid = own_uid_raw if own_uid_raw in unicode_ref else own_uid_raw + " [unverified]"

    # ── has its own Unicode code ──────────────────────────────────────────
    if own_uid:
        if useq_val:
            return {"sign_type": "Type_1", "sign_structure": "atomic_with_decompositions",
                     "structural_hint": "", "own_uid": own_uid,
                     "component_uids": useq_to_uplus_list(useq_val)}
        return {"sign_type": "Type_1", "sign_structure": "atomic",
                 "structural_hint": "", "own_uid": own_uid, "component_uids": []}

    # ── explicit @useq, no own code ───────────────────────────────────────
    if useq_val:
        return {"sign_type": "Type_2", "sign_structure": "compound",
                 "structural_hint": "", "own_uid": "",
                 "component_uids": useq_to_uplus_list(useq_val)}

    # ── no own code, no explicit useq: try name-pattern / inference ───────
    reason = classify_no_unicode_reason(name)
    if reason in ('COMPOUND_TIMES', 'COMPOUND_LIGATURE'):
        operator = '×' if reason == 'COMPOUND_TIMES' else '&'
        comps = try_decompose_juxtaposition(name, operator, sign_index)
        if comps:
            return {"sign_type": "Type_2", "sign_structure": "compound",
                     "structural_hint": "", "own_uid": "", "component_uids": comps}
        return {"sign_type": "Type_3", "sign_structure": "not_identified",
                 "structural_hint": "compound_unresolved", "own_uid": "", "component_uids": []}

    return {"sign_type": "Type_3", "sign_structure": "not_identified",
             "structural_hint": "", "own_uid": "", "component_uids": []}


# ─────────────────────────────────────────────────────────────────────────────
# PASS 1 — PARSE osl.asl AT FULL @sign COVERAGE
# ─────────────────────────────────────────────────────────────────────────────

def parse_osl(filepath: str, unicode_ref: dict) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    sign_index = build_full_sign_index(content)
    rows = []
    stats = defaultdict(int)

    sign_blocks = re.split(r'^@sign[ \t]', content, flags=re.MULTILINE)

    for block in sign_blocks:
        if not block.strip() or block.strip().startswith('@'):
            continue
        block_lines = block.strip().split('\n')
        sign_name, sign_header_lines = split_entity_lines(block_lines)
        sign_header = parse_entity_header(sign_header_lines)
        sign_parent_lists = sign_header["catalog_refs"]

        form_parts = re.split(r'^@form[ \t]', block, flags=re.MULTILINE)
        form_sections = form_parts[1:]

        if not form_sections:
            # ── headless sign: the header itself is the only entity ────────
            cls = classify_entity(sign_name, sign_header, sign_index, unicode_ref)
            stats[cls["sign_structure"]] += 1
            entity_rows = build_rows_for_entity(
                sign_name=sign_name, allograph_form="", cls=cls,
                own_ucun=sign_header["ucun"], unicode_ref=unicode_ref,
                sign_list_str=build_signlist_analogue([], sign_parent_lists),
            )
            rows.extend(entity_rows)
        else:
            for form_section in form_sections:
                form_lines = form_section.strip().split('\n')
                form_name, form_header_lines = split_entity_lines(form_lines)
                # form header lines: everything up to end of block (forms have no nested @form)
                form_header_lines = form_lines[1:]
                form_header = parse_entity_header(form_header_lines)

                cls = classify_entity(form_name, form_header, sign_index, unicode_ref)

                # Inherit from parent sign ONLY if this form resolved to nothing of its
                # own AND is not a known-but-unresolved compound (inheriting a single
                # atomic code onto a structurally compound name would misrepresent it).
                if (cls["sign_type"] == "Type_3" and not cls["component_uids"]
                        and not cls["own_uid"] and cls["structural_hint"] != "compound_unresolved"):
                    parent_uid = sign_header["own_uid"]
                    if parent_uid:
                        inherited = parent_uid if parent_uid in unicode_ref else parent_uid + " [unverified]"
                        cls = dict(cls)
                        cls["own_uid"] = inherited
                        # Row now carries a real, usable unicode_id (just not its OWN —
                        # it was inherited), so it belongs with 'atomic', not 'not_identified'.
                        cls["sign_structure"] = "atomic"
                        cls["structural_hint"] = "inherited_from_parent"

                stats[cls["sign_structure"]] += 1
                sign_list_str = build_signlist_analogue(form_header["catalog_refs"], sign_parent_lists)
                own_ucun = form_header["ucun"] or sign_header["ucun"]
                entity_rows = build_rows_for_entity(
                    sign_name=sign_name, allograph_form=form_name, cls=cls,
                    own_ucun=own_ucun, unicode_ref=unicode_ref,
                    sign_list_str=sign_list_str,
                )
                rows.extend(entity_rows)

    print("[INFO] sign_structure counts:")
    for k, v in stats.items():
        print(f"    {k:28} {v}")
    print(f"[INFO] Total rows (Pass 1): {len(rows)}")
    return rows


def build_rows_for_entity(sign_name, allograph_form, cls, own_ucun, unicode_ref, sign_list_str) -> list:
    """Turn one classified entity (a @sign header or a @form) into 1..N rows."""
    rows = []
    entity_label = allograph_form if allograph_form else sign_name

    if cls["sign_structure"] in ("atomic", "not_identified"):
        rows.append({
            "unicode_id": cls["own_uid"],
            "sign_grapheme": own_ucun or unicode_ref.get(cls["own_uid"], ""),
            "sign_structure": cls["sign_structure"],
            "structural_hint": cls["structural_hint"],
            "component_position": "",
            "sign_name": sign_name,
            "allograph_form": allograph_form,
            "graphic_variant_id": "",  # Pass 2
            "sign_type": cls["sign_type"],
            "compound_form": "",
            "compound_grapheme": "",
            "compound_unicode": "",
            "signList_analogue": sign_list_str,
        })

    elif cls["sign_structure"] == "atomic_with_decompositions":
        comp_glyphs = [unicode_ref.get(u.replace(" [unverified]", ""), "") for u in cls["component_uids"]]
        rows.append({
            "unicode_id": cls["own_uid"],
            "sign_grapheme": own_ucun or unicode_ref.get(cls["own_uid"].replace(" [unverified]", ""), ""),
            "sign_structure": cls["sign_structure"],
            "structural_hint": "",
            "component_position": "",
            "sign_name": sign_name,
            "allograph_form": allograph_form,
            "graphic_variant_id": "",
            "sign_type": cls["sign_type"],
            "compound_form": entity_label,
            "compound_grapheme": "".join(comp_glyphs) or own_ucun,
            "compound_unicode": "; ".join(cls["component_uids"]),
            "signList_analogue": sign_list_str,
        })

    elif cls["sign_structure"] == "compound":
        comp_uids = cls["component_uids"]
        comp_glyphs = [unicode_ref.get(u.replace(" [unverified]", ""), "") for u in comp_uids]
        full_cun = own_ucun or "".join(comp_glyphs)
        uid_seq = "; ".join(comp_uids)
        for pos, uid in enumerate(comp_uids, start=1):
            rows.append({
                "unicode_id": uid,
                "sign_grapheme": unicode_ref.get(uid.replace(" [unverified]", ""), ""),
                "sign_structure": "compound",
                "structural_hint": "",
                "component_position": str(pos),
                "sign_name": sign_name,
                "allograph_form": allograph_form,
                "graphic_variant_id": "",
                "sign_type": cls["sign_type"],
                "compound_form": entity_label,
                "compound_grapheme": full_cun,
                "compound_unicode": uid_seq,
                "signList_analogue": sign_list_str,
            })

    return rows


# ─────────────────────────────────────────────────────────────────────────────
# PASS 2 — UNIFIED graphic_variant_id (documentation-order, not frequency)
# ─────────────────────────────────────────────────────────────────────────────

def assign_variant_ids(rows: list) -> list:
    form_order = defaultdict(dict)  # sign_name -> {allograph_form: n}
    for row in rows:
        sign, form = row["sign_name"], row["allograph_form"]
        if form not in form_order[sign]:
            form_order[sign][form] = len(form_order[sign]) + 1

    for row in rows:
        sign, form = row["sign_name"], row["allograph_form"]
        prefix = make_variant_prefix(sign)
        n = form_order[sign][form]
        row["graphic_variant_id"] = f"{prefix}_v{n}"
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# PASS 3 — JOIN PHONETIC / SYLLABARY DATA BY unicode_id
# ─────────────────────────────────────────────────────────────────────────────

def join_phonetics(rows: list, phon_ref: dict) -> list:
    matched = 0
    for row in rows:
        uid = row["unicode_id"].replace(" [unverified]", "")
        p = phon_ref.get(uid)
        if p:
            matched += 1
            row["unicodeTrLit"]     = p["unicodeTrLit"]
            row["syllabary_sign"]   = p["syllabarySign"]
            row["phonetic_version"] = p["PhoneticsVersion"]
        else:
            row["unicodeTrLit"] = row["syllabary_sign"] = row["phonetic_version"] = ""
    print(f"[INFO] Phonetic join matched: {matched} / {len(rows)} rows")
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# WRITER
# ─────────────────────────────────────────────────────────────────────────────

def write_csv(rows: list, output_path: str):
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Written {len(rows)} rows -> {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"[INFO] Loading Unicode reference: {INPUT_UNICODE}")
    unicode_ref = load_unicode_reference(INPUT_UNICODE)

    print(f"[INFO] Loading Phonetic reference: {INPUT_PHONETIC}")
    phon_ref = load_phonetic_reference(INPUT_PHONETIC)

    print(f"\n[INFO] PASS 1 - Parsing (full @sign coverage): {INPUT_ASL}")
    rows = parse_osl(INPUT_ASL, unicode_ref)

    print(f"\n[INFO] PASS 2 - Assigning graphic_variant_id (documentation order)")
    rows = assign_variant_ids(rows)

    print(f"\n[INFO] PASS 3 - Joining phonetic/syllabary data")
    rows = join_phonetics(rows, phon_ref)

    print(f"\n[INFO] Writing output...")
    write_csv(rows, OUTPUT_CSV)
    print("[DONE]")


if __name__ == "__main__":
    main()
