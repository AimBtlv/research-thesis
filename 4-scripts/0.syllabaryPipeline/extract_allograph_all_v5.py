#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: extract_allograph_all_v5.py
Description: Extract allograph data from osl.asl → allograph_all.csv
             Integrates graphic_variant_id assignment from add_graphic_variant_id.py

             v5 changes vs v4:
               - graphic_variant_id column added (position 6, after allograph_type)
                 Format: PREFIX_vN  (e.g. DIS_v1, DIS_v2, ANSE_v2)
                         PREFIX_compound  → simplified to "compound" for Type_2
               - variant_group_size removed (per specification)
               - Two-pass architecture:
                   PASS 1 — parse_osl()        → raw rows (no variant ids yet)
                   PASS 2 — assign_variants()  → adds graphic_variant_id to each row
                 Two passes are necessary because variant numbering requires
                 knowing ALL rows for a sign before assigning v1/v2/v3 labels.

             Column order (allograph_all.csv):
               1.  unicode_id
               2.  allograph_sign
               3.  allograph_form
               4.  allograph_ucun
               5.  allograph_type
               6.  graphic_variant_id   ← NEW
               7.  compound_form
               8.  component_position
               9.  allographCompound_cun
               10. allographCompound_useq
               11. signList_analogue

             Variant numbering rules:
               v1  = uid most frequently attested across rows for this sign
                     (canonical / standard form)
               v2+ = remaining uids ordered:
                       Type_1 verified (no [unverified]) first
                       Type_1 unverified next
                       Type_3 (inherited uid) last
               Type_2 rows → graphic_variant_id = "compound"
               Type_3 rows with no uid → graphic_variant_id = "PREFIX_v1"

Author: Digital Humanities Pipeline
Date: 2026-04-24
Version: 5.0
"""

import re
import csv
import os
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

ROOT_DIR      = os.path.dirname(os.path.abspath(__file__))
INPUT_ASL     = os.path.join(ROOT_DIR, "osl.asl")
INPUT_UNICODE = os.path.join(ROOT_DIR, "1_unicodeSigns.csv")
OUTPUT_CSV    = os.path.join(ROOT_DIR, "allograph_all.csv")

FIELDNAMES = [
    "unicode_id",             # Type_1: U+12037 | Type_2: component U+ | Type_3: root @sign U+
    "allograph_sign",         # Root @sign scientific name
    "allograph_form",         # @form value from osl.asl — always populated
    "allograph_ucun",         # Cuneiform glyph
    "allograph_type",         # Type_1 | Type_2 | Type_3
    "graphic_variant_id",     # Graphical variant label: PREFIX_vN or "compound"
    "compound_form",          # Type_2 only: original @form name of the compound
    "component_position",     # Type_2 only: 1-based position in compound
    "allographCompound_cun",  # Type_2 only: full compound glyph
    "allographCompound_useq", # Type_2 only: full U+ sequence
    "signList_analogue",      # Analogue catalogue refs (annotated with period/region)
]

# ─────────────────────────────────────────────────────────────────────────────
# SIGN LIST METADATA
# ─────────────────────────────────────────────────────────────────────────────

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


def annotate_list_ref(ref: str) -> str:
    """Append [period | region] metadata to a catalogue reference."""
    prefix = re.match(r'^([A-Za-z]+)', ref)
    if prefix:
        key = prefix.group(1).upper()
        if key in SIGN_LIST_META:
            period, region = SIGN_LIST_META[key]
            return f"{ref} [{period} | {region}]"
    return ref


# ─────────────────────────────────────────────────────────────────────────────
# UNICODE REFERENCE  (1_unicodeSigns.csv — authoritative standard)
# ─────────────────────────────────────────────────────────────────────────────

def load_unicode_reference(filepath: str) -> dict:
    """
    Load 1_unicodeSigns.csv → {unicode_id: sign_grapheme}.
    Used to:
      - Validate Type_1 codes against Unicode standard
      - Look up individual component glyphs for Type_2 (exploded rows)
      - Assign inherited unicode_id + glyph to Type_3
    """
    ref = {}
    if not os.path.exists(filepath):
        print(f"[WARN] Unicode reference not found: {filepath}")
        return ref
    with open(filepath, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uid   = row.get("unicode_id", "").strip()
            glyph = row.get("sign_grapheme", "").strip()
            if uid:
                ref[uid] = glyph
    print(f"[INFO] Loaded {len(ref)} entries from unicode reference")
    return ref


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_field(lines: list, tag: str) -> str:
    """Return first value of @<tag> in lines, or ''."""
    pat = re.compile(rf'^@{re.escape(tag)}\s+(.*)', re.IGNORECASE)
    for line in lines:
        m = pat.match(line.strip())
        if m:
            return m.group(1).strip()
    return ""


def xhex_to_uplus(token: str) -> str:
    """'x12000' → 'U+12000'. Leaves unknown tokens unchanged."""
    token = token.strip()
    if re.match(r'^x[0-9A-Fa-f]+$', token):
        return "U+" + token[1:].upper()
    return token


def useq_to_uplus_list(useq_val: str) -> list:
    """'x12000.x12094.x1223E' → ['U+12000', 'U+12094', 'U+1223E']"""
    parts = [p.strip() for p in useq_val.split(".") if p.strip()]
    return [xhex_to_uplus(p) for p in parts]


def collect_analogue_lists(lines: list) -> list:
    """Extract all @list entries that are NOT 'U+...' from text lines."""
    refs = []
    for line in lines:
        m = re.match(r'^@list\s+(\S+)', line.strip())
        if m:
            val = m.group(1).strip()
            if not val.startswith("U+"):
                refs.append(val)
    return refs


def build_signlist_analogue(form_lists: list, sign_lists: list) -> str:
    """
    Merge @form and parent @sign analogue lists, deduplicate, annotate.
    @form entries first (more specific), then @sign entries.
    """
    seen   = set()
    result = []
    for ref in form_lists + sign_lists:
        if ref not in seen:
            seen.add(ref)
            result.append(annotate_list_ref(ref))
    return "; ".join(result)


def make_variant_prefix(sign: str) -> str:
    """
    Create a clean alphabetic prefix from a sign name for graphic_variant_id.
    Removes special characters, transliterates common diacritics,
    keeps letters + digits, truncates to 8 chars, uppercases.

    Examples:
      'DIŠ'               → 'DIS'
      'ANŠE'              → 'ANSE'
      'BAHAR₂'            → 'BAHAR2'
      '|A.TU.GABA.LIŠ|'  → 'ATUGABALI'
    """
    s = sign
    # Transliterate common cuneiform diacritics
    for src, tgt in [('Š','S'),('š','s'),('Ž','Z'),('ž','z'),
                     ('Ĝ','G'),('ĝ','g'),('Ŋ','NG'),('ŋ','ng'),
                     ('Ḫ','H'),('ḫ','h')]:
        s = s.replace(src, tgt)
    # Remove non-alphanumeric characters
    clean = re.sub(r'[^A-Za-z0-9]', '', s)
    return clean[:8].upper() if clean else 'X'


# ─────────────────────────────────────────────────────────────────────────────
# ROOT SIGN INDEX — built once before processing @form blocks
# ─────────────────────────────────────────────────────────────────────────────

def build_sign_index(content: str, unicode_ref: dict) -> dict:
    """
    Pre-build index of root @sign data:
      sign_name → {
          'unicode_id': str  (validated against 1_unicodeSigns.csv),
          'ucun':       str  (from @ucun in sign header),
          'ana_lists':  list (analogue @list entries from sign header)
      }
    Used to inherit unicode_id + ucun for Type_3 allographs and to
    contribute parent analogue lists to signList_analogue.
    """
    index = {}
    sign_blocks = re.split(r'^@sign[ \t]', content, flags=re.MULTILINE)

    for block in sign_blocks:
        lines = block.strip().split('\n')
        if not lines:
            continue
        sign_name = lines[0].strip()

        # Parse header only (lines before first @form)
        header_lines = []
        for line in lines[1:]:
            if re.match(r'^@form[ \t]', line):
                break
            header_lines.append(line)

        root_uid = root_ucun = ""
        for line in header_lines:
            m = re.match(r'^@list\s+(U\+\S+)', line.strip())
            if m:
                raw = m.group(1).strip()
                root_uid  = raw if raw in unicode_ref else raw + " [unverified]"
                root_ucun = unicode_ref.get(raw, "")
                break

        # Prefer explicit @ucun from osl.asl over unicode_ref lookup
        ucun_asl = get_field(header_lines, "ucun")
        if ucun_asl:
            root_ucun = ucun_asl

        index[sign_name] = {
            "unicode_id": root_uid,
            "ucun":       root_ucun,
            "ana_lists":  collect_analogue_lists(header_lines),
        }
    return index


# ─────────────────────────────────────────────────────────────────────────────
# PASS 2 — ASSIGN GRAPHIC VARIANT IDs
# ─────────────────────────────────────────────────────────────────────────────

def assign_variants(rows: list) -> list:
    """
    PASS 2: iterate over all rows produced by parse_osl() and assign
    graphic_variant_id to each row.

    Algorithm:
      Step A — Count uid frequency per sign (Type_1 + Type_3 only,
                excluding Type_2 compound components)
      Step B — For each sign: most frequent uid = v1 (canonical)
                Remaining uids sorted:
                  (0) Type_1 verified   (no [unverified])
                  (1) Type_1 unverified
                  (2) Type_3 inherited
      Step C — Assign PREFIX_vN to each row based on its (sign, uid) pair
               Type_2 rows → "compound"
               Type_3 rows with empty uid → PREFIX_v1

    Returns the same list with 'graphic_variant_id' filled in each row dict.
    """

    # ── Step A: count uid frequency per sign (exclude Type_2) ────────────────
    sign_uid_freq = defaultdict(lambda: defaultdict(int))  # sign → {uid → count}
    sign_uid_type = defaultdict(dict)                       # sign → {uid → allograph_type}

    for row in rows:
        if row["allograph_type"] == "Type_2":
            continue
        sign = row["allograph_sign"]
        uid  = row["unicode_id"]
        sign_uid_freq[sign][uid] += 1
        if uid not in sign_uid_type[sign]:
            sign_uid_type[sign][uid] = row["allograph_type"]

    # ── Step B: build {sign → {uid → variant_number}} ────────────────────────
    sign_uid_varnum = {}

    for sign, uid_freq in sign_uid_freq.items():
        # v1 = most frequent uid
        sorted_by_freq = sorted(uid_freq.items(), key=lambda x: -x[1])
        v1_uid = sorted_by_freq[0][0]

        # Sort the rest by type reliability
        rest = sorted_by_freq[1:]

        def sort_key(uid_cnt):
            uid = uid_cnt[0]
            typ = sign_uid_type[sign].get(uid, "Type_3")
            unverified = "[unverified]" in uid
            if   typ == "Type_1" and not unverified: return (0, uid)
            elif typ == "Type_1" and unverified:     return (1, uid)
            else:                                    return (2, uid)

        rest_sorted = sorted(rest, key=sort_key)

        uid_to_varnum = {v1_uid: 1}
        for i, (uid, _) in enumerate(rest_sorted, start=2):
            uid_to_varnum[uid] = i

        sign_uid_varnum[sign] = uid_to_varnum

    # ── Step C: assign graphic_variant_id to every row ───────────────────────
    for row in rows:
        sign   = row["allograph_sign"]
        uid    = row["unicode_id"]
        typ    = row["allograph_type"]
        prefix = make_variant_prefix(sign)

        if typ == "Type_2":
            # Compound component — simplified label as specified
            row["graphic_variant_id"] = "compound"

        elif not uid:
            # Type_3 with no inherited uid (compound root sign, no Unicode exists)
            row["graphic_variant_id"] = f"{prefix}_v1"

        else:
            vnum = sign_uid_varnum.get(sign, {}).get(uid, 1)
            row["graphic_variant_id"] = f"{prefix}_v{vnum}"

    # Stats
    multi = sum(1 for s, m in sign_uid_varnum.items() if len(m) > 1)
    extra = sum(len(m) - 1 for m in sign_uid_varnum.values() if len(m) > 1)
    print(f"[INFO] Signs with multiple graphic variants: {multi}")
    print(f"[INFO] Additional variant rows (v2+): {extra}")

    return rows


# ─────────────────────────────────────────────────────────────────────────────
# PASS 1 — PARSE osl.asl
# ─────────────────────────────────────────────────────────────────────────────

def parse_osl(filepath: str, unicode_ref: dict) -> list:
    """
    PASS 1: Parse osl.asl and extract all @form (allograph) records.
    graphic_variant_id is left empty here — filled in Pass 2.

    Row structure per allograph type:
    ─────────────────────────────────────────────────────────────────────────
    Type_1 (own Unicode):       one row per @form
    Type_2 (compound, @useq):   EXPLODED — one row per component U+
    Type_3 (text name only):    one row per @form, inherits root @sign uid
    ─────────────────────────────────────────────────────────────────────────
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    sign_index = build_sign_index(content, unicode_ref)
    rows  = []
    stats = {"Type_1": 0, "Type_1_unverified": 0,
             "Type_2": 0, "Type_2_rows": 0,
             "Type_3": 0, "Type_3_no_root_uid": 0}

    sign_blocks = re.split(r'^@sign[ \t]', content, flags=re.MULTILINE)

    for sign_block in sign_blocks:
        if not sign_block.strip():
            continue

        sign_name        = sign_block.strip().split('\n')[0].strip()
        root_info        = sign_index.get(sign_name,
                               {"unicode_id": "", "ucun": "", "ana_lists": []})
        parent_ana_lists = root_info["ana_lists"]

        form_parts = re.split(r'^@form[ \t]', sign_block, flags=re.MULTILINE)

        for form_section in form_parts[1:]:
            form_lines     = form_section.strip().split('\n')
            allograph_form = form_lines[0].strip()
            form_own_lists = collect_analogue_lists(form_lines)
            sign_list_str  = build_signlist_analogue(form_own_lists, parent_ana_lists)

            # ── Type_1: has @list U+ inside @form block ──────────────────────
            form_uid = ""
            for line in form_lines:
                m = re.match(r'^@list\s+(U\+\S+)', line.strip())
                if m:
                    form_uid = m.group(1).strip()
                    break

            if form_uid:
                stats["Type_1"] += 1
                if form_uid not in unicode_ref:
                    form_uid += " [unverified]"
                    stats["Type_1_unverified"] += 1

                rows.append({
                    "unicode_id":             form_uid,
                    "allograph_sign":         sign_name,
                    "allograph_form":         allograph_form,
                    "allograph_ucun":         get_field(form_lines, "ucun"),
                    "allograph_type":         "Type_1",
                    "graphic_variant_id":     "",          # filled in Pass 2
                    "compound_form":          "",
                    "component_position":     "",
                    "allographCompound_cun":  "",
                    "allographCompound_useq": "",
                    "signList_analogue":      sign_list_str,
                })
                continue

            # ── Type_2: has @useq inside @form block ─────────────────────────
            useq_val = get_field(form_lines, "useq")
            if useq_val:
                stats["Type_2"] += 1
                uid_list = useq_to_uplus_list(useq_val)
                uid_seq  = "; ".join(uid_list)
                full_cun = get_field(form_lines, "ucun")

                for pos, uid in enumerate(uid_list, start=1):
                    stats["Type_2_rows"] += 1
                    rows.append({
                        "unicode_id":             uid,
                        "allograph_sign":         sign_name,
                        "allograph_form":         allograph_form,
                        "allograph_ucun":         unicode_ref.get(uid, ""),
                        "allograph_type":         "Type_2",
                        "graphic_variant_id":     "",      # filled in Pass 2
                        "compound_form":          allograph_form,
                        "component_position":     str(pos),
                        "allographCompound_cun":  full_cun,
                        "allographCompound_useq": uid_seq,
                        "signList_analogue":      sign_list_str,
                    })
                continue

            # ── Type_3: text name only ────────────────────────────────────────
            stats["Type_3"] += 1
            inherited_uid  = root_info["unicode_id"]
            inherited_ucun = root_info["ucun"]
            if not inherited_uid:
                stats["Type_3_no_root_uid"] += 1

            rows.append({
                "unicode_id":             inherited_uid,
                "allograph_sign":         sign_name,
                "allograph_form":         allograph_form,
                "allograph_ucun":         inherited_ucun,
                "allograph_type":         "Type_3",
                "graphic_variant_id":     "",              # filled in Pass 2
                "compound_form":          "",
                "component_position":     "",
                "allographCompound_cun":  "",
                "allographCompound_useq": "",
                "signList_analogue":      sign_list_str,
            })

    print(f"[INFO] Type_1: {stats['Type_1']} "
          f"(unverified: {stats['Type_1_unverified']})")
    print(f"[INFO] Type_2: {stats['Type_2']} compounds → "
          f"{stats['Type_2_rows']} exploded rows")
    print(f"[INFO] Type_3: {stats['Type_3']} "
          f"(no root unicode: {stats['Type_3_no_root_uid']})")
    print(f"[INFO] Total rows (Pass 1): {len(rows)}")
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# WRITER
# ─────────────────────────────────────────────────────────────────────────────

def write_csv(rows: list, output_path: str):
    """Write to UTF-8 CSV with BOM (Excel/LibreOffice compatible)."""
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Written {len(rows)} rows → {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"[INFO] Loading Unicode reference: {INPUT_UNICODE}")
    unicode_ref = load_unicode_reference(INPUT_UNICODE)

    print(f"\n[INFO] PASS 1 — Parsing: {INPUT_ASL}")
    rows = parse_osl(INPUT_ASL, unicode_ref)

    print(f"\n[INFO] PASS 2 — Assigning graphic_variant_id")
    rows = assign_variants(rows)

    print(f"\n[INFO] Writing output...")
    write_csv(rows, OUTPUT_CSV)
    print("[DONE]")


if __name__ == "__main__":
    main()
