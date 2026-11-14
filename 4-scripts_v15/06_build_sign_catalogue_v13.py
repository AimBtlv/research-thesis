#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 06_build_sign_catalogue_v13.py (formerly 2_build_allograph_pipeline_v13.py)
Description: Workflow Stage 1, Step 4. Builds the full sign catalogue
             (sign_catalogue_v13.csv, formerly allograph_all_v11/v12.csv:
             the old name had nothing to do with allographs; since
             2026-11-12 also the columns allograph_form -> osl_form and
             graphic_variant_id -> osl_form_id) and compound_form_reading_table
             from osl.asl, the Unicode list, the phonetic reference, Diri,
             OGSL and Syllabary_CM.
             v12 FIX: a @sign that has @form variants now gets a row of its
             own (its own Unicode code point and readings) BEFORE the rows of
             its variants. In v11 only the variants were written, so 217
             Unicode signs (KA, SUM, TE, GAN, GUL, IL2, U ...) had no
             "Single Sign Reading" row and their readings (ka, du11, inim,
             šum2 ...) could not be resolved by the parser of Step 5.
             v13 (on top of v12):
             1. OSL @v values fill GAPS in the readings of simple signs: a
                value of a sign (or form) in osl.asl is added to that row
                only if no simple-sign row of the catalogue has this reading
                yet (e.g. ṣi, ṣa, ṭu₃ were missing). Existing readings are
                never moved. Added values are listed in the new column
                'osl_v_added'. Cases where OSL gives a reading to another
                sign than the catalogue are written to
                osl_reading_conflicts_v13.csv instead of being changed.
             2. Names that come only from the historical syllabaries (Uruk2,
                Syllabary_CM, additional sources) get the Unicode code point
                of an OSL sign when the link is unambiguous: the name is an
                OSL sign name (structural_hint unicode_via_osl_name) or an
                OSL value of exactly one simple sign (unicode_via_osl_value).
                A name that is the OSL value of exactly one COMPOUND sign
                (PA3 = pa₃ of |IGI.RU|) becomes a reference to that compound
                ('Syllabary Name Of OSL Compound'), so that it no longer hides
                the compound reading from the parser.
             Everything else is unchanged.
Author: Aima, fixes prepared with Claude
Date: 2026-11-09
Version: 13
"""

import csv
import json
import re
from collections import defaultdict, Counter

# CONFIGURATION
# --- Paths (relative to the repository: research-thesis/pipeline_v14/<this file>) ---
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parents[1]                 # research-thesis/
DP = ROOT / "2-dataset" / "DataProfile"
UA = DP / "1-5unicodeAssignmentFiles"
PROF = UA / "2_professorsFiles"
INPUTDATA = ROOT / "2-dataset" / "InputData"
OUT = _P(__file__).resolve().parent / "output"
OUTPUT_DIR = OUT / "step4"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_ASL = DP / "6_osl.asl"
INPUT_UNICODE = UA / "1_unicodeSigns.csv"
# Step 1.4 output of this pipeline (fixed 2026-11-14: before, the repository
# copy was always read, so changes of Step 1 never reached the catalogue)
INPUT_PHONETIC = (OUT / "step1" / "7_unicodePhoneticVersion_full.csv"
                  if (OUT / "step1" / "7_unicodePhoneticVersion_full.csv").exists()
                  else DP / "7_unicodePhoneticVersion_full.csv")
INPUT_SYLLABARY = OUT / "step1" / "Syllabary_CM.csv"      # from Step 1.1
INPUT_DIRI = (OUT / "step2" / "diri_lexical_list.csv"      # Step 2 re-run, if done
              if (OUT / "step2" / "diri_lexical_list.csv").exists()
              else UA / "diri_lexical_list.csv")
INPUT_OGSL = DP / "ogsl_sign_readings.json"



def check_inputs():
    """Stop with a clear message if an input file is missing, and show
    where a file with the same name exists elsewhere in 2-dataset/."""
    missing = [p for p in (INPUT_ASL, INPUT_UNICODE, INPUT_PHONETIC, INPUT_SYLLABARY,
                           INPUT_DIRI, INPUT_OGSL) if not p.exists()]
    if not missing:
        return
    import sys
    print("\n[ERROR] missing input file(s):")
    for p in missing:
        print(f"  - {p}")
        found = sorted(ROOT.joinpath("2-dataset").rglob(p.name))
        for f in found[:5]:
            print(f"      found elsewhere: {f}")
        if not found:
            print("      not found anywhere in 2-dataset/: restore it from git "
                  f"(git checkout -- \"{p.relative_to(ROOT)}\")")
    print("Move or copy the file to the expected place and run this step again.")
    sys.exit(1)


OUTPUT_COMPOUND_TABLE = OUTPUT_DIR / "compound_form_reading_table_v13.csv"
OUTPUT_CONFLICTS = OUTPUT_DIR / "osl_reading_conflicts_v13.csv"
OUTPUT_V8 = OUTPUT_DIR / "sign_catalogue_v13.csv"

SUBSCRIPT_TO_ASCII = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
V_PAT = re.compile(r'^@v\s+(.*)')

SIGN_LIST_META = {
    "LAK":   ("Uruk IV–III (~3400–3000 BCE)",    "Archaic / Uruk"),
    "REC":   ("Uruk IV–III (~3400–3000 BCE)",    "Archaic / Uruk"),
    "ZATU":  ("Uruk IV–III (~3400–3000 BCE)",    "Archaic / Uruk"),
    "BAU":   ("Early Dynastic (~2900–2340 BCE)", "Lagash"),
    "ELLES": ("Early Dynastic (~2900–2340 BCE)", "Ebla"),
    "RSP":   ("Early Dynastic (~2900–2340 BCE)", "Presargonic Lagash"),
    "GCSL":  ("Gudea period (~2100 BCE)",         "Lagash / Girsu"),
    "KWU":   ("Ur III (~2112–2004 BCE)",          "Administrative"),
    "ABZL":  ("Old Babylonian (~2000–1600 BCE)", "School texts"),
    "MZL":   ("Standard Babylonian (any period)","Akkado-Babylonian"),
    "ABZ":   ("Standard Babylonian (any period)","Akkado-Babylonian"),
    "SLLHA": ("Standard Babylonian (any period)","Akkado-Babylonian"),
    "ASY":   ("Standard Babylonian (any period)","Akkadian syllabary"),
    "SYA":   ("Standard Babylonian (any period)","Akkadian syllabary"),
    "HZL":   ("Hittite period (~1650–1180 BCE)", "Hittite"),
    "PTACE": ("Early Dynastic (~2900–2340 BCE)", "Ebla"),
}

SOURCE_LABELS = {"URUK2": "Uruk2", "CM": "Syllabary_CM", "ADDITIONAL": "Additional Sources"}
TYPE_PHONETIC_LABELS = {
    "ATTESTED_DIRECT": "Attested Compound Reading",
    "NESTED_IN_LONGER_FORM": "Compound Nested in Longer Form",
    "NO_ATTESTED_READING": "No Attested Compound Reading",
}

V8_FIELDNAMES = [
    "unicode_id", "sign_grapheme", "sign_source", "sign_structure", "structural_hint",
    "component_position", "sign_name", "osl_form", "osl_form_id",
    "sign_type", "compound_form", "compound_grapheme", "compound_unicode",
    "unicodeTrLit", "syllabary_sign", "typePhonetic_Version", "phonetic_version",
    "signList_analogue", "osl_v_added",
]

# SHARED HELPERS

def normalize_name(name: str) -> str:
    return name.strip('|').translate(SUBSCRIPT_TO_ASCII)


def make_variant_prefix(sign: str) -> str:
    s = sign
    for src, tgt in [('Š','S'),('š','s'),('Ž','Z'),('ž','z'),('Ĝ','G'),('ĝ','g'),
                      ('Ŋ','NG'),('ŋ','ng'),('Ḫ','H'),('ḫ','h')]:
        s = s.replace(src, tgt)
    clean = re.sub(r'[^A-Za-z0-9]', '', s)
    return clean[:8].upper() if clean else 'X'


def get_field(lines, tag):
    pat = re.compile(rf'^@{re.escape(tag)}\s+(.*)', re.IGNORECASE)
    for line in lines:
        m = pat.match(line.strip())
        if m:
            return m.group(1).strip()
    return ""


def get_v_values(lines):
    out = []
    for line in lines:
        m = V_PAT.match(line.strip())
        if m and m.group(1).strip():
            out.append(m.group(1).strip())
    return out


def xhex_to_uplus(token):
    token = token.strip()
    return "U+" + token[1:].upper() if re.match(r'^x[0-9A-Fa-f]+$', token) else token


def useq_to_uplus_list(useq_val):
    return [xhex_to_uplus(p.strip()) for p in useq_val.split(".") if p.strip()]


def collect_analogue_lists(lines):
    return [m.group(1).strip() for line in lines
            if (m := re.match(r'^@list\s+(\S+)', line.strip())) and not m.group(1).startswith("U+")]


def annotate_list_ref(ref):
    m = re.match(r'^([A-Za-z]+)', ref)
    if m and m.group(1).upper() in SIGN_LIST_META:
        period, region = SIGN_LIST_META[m.group(1).upper()]
        return f"{ref} [{period} | {region}]"
    return ref


def build_signlist_analogue(own_lists, parent_lists):
    seen, result = set(), []
    for ref in own_lists + parent_lists:
        if ref not in seen:
            seen.add(ref); result.append(annotate_list_ref(ref))
    return "; ".join(result)


def split_entity_lines(block_lines):
    name = block_lines[0].strip()
    header_lines = []
    for line in block_lines[1:]:
        if re.match(r'^@form[ \t]', line):
            break
        header_lines.append(line)
    return name, header_lines


def parse_entity_header(lines):
    own_uid = ""
    for line in lines:
        m = re.match(r'^@list\s+(U\+\S+)', line.strip())
        if m:
            own_uid = m.group(1).strip(); break
    is_fake = any(re.match(r'^@fake\s+1', line.strip()) for line in lines)
    return {"own_uid": own_uid, "useq": get_field(lines, "useq"),
            "ucun": get_field(lines, "ucun"), "catalog_refs": collect_analogue_lists(lines),
            "v_values": get_v_values(lines), "is_fake": is_fake}


def split_form_blocks(block):
    """Splits a @sign block's raw text into (form_text, is_deprecated) pairs
    for both '@form' (valid) and '@form-' (marked spurious/deprecated/
    superseded by osl.asl's own editors must be excluded, not silently
    merged into whichever form precedes it). form_text keeps the same shape
    the rest of the code expects: first line is the form's own name."""
    parts = re.split(r'(^@form-?[ \t])', block, flags=re.MULTILINE)
    # parts alternates: [pre-text, marker1, form1_text, marker2, form2_text, ...]
    result = []
    for i in range(1, len(parts), 2):
        marker = parts[i]
        text = parts[i+1] if i+1 < len(parts) else ""
        result.append((text, marker.startswith('@form-')))
    return result


def classify_no_unicode_reason(name):
    inner = name.strip('|')
    if '×' in inner: return 'COMPOUND_TIMES'
    if '&' in inner: return 'COMPOUND_LIGATURE'
    if '+' in inner: return 'COMPOUND_PLUS'
    if re.search(r'@[a-zA-Z0-9]+$', inner) or re.search(r'~[a-zA-Z0-9]+$', inner): return 'MODIFIER_VARIANT'
    if re.match(r"^[A-Z]+\d+[a-zA-Z\^']*$", inner): return 'CATALOG_ONLY'
    return 'PLAIN_OR_OTHER'


def lookup_component_uid(candidate, sign_index):
    cand = candidate.strip()
    if cand in sign_index and sign_index[cand]["own_uid"]:
        return sign_index[cand]["own_uid"]
    wrapped = f"|{cand}|"
    if wrapped in sign_index and sign_index[wrapped]["own_uid"]:
        return sign_index[wrapped]["own_uid"]
    return ""


def try_decompose_juxtaposition(name, operator, sign_index):
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


def classify_entity(name, header, sign_index, unicode_ref):
    own_uid_raw, useq_val = header["own_uid"], header["useq"]
    own_uid = ""
    if own_uid_raw:
        own_uid = own_uid_raw if own_uid_raw in unicode_ref else own_uid_raw + " [unverified]"

    if own_uid:
        if useq_val:
            return {"sign_type": "Type_1", "sign_structure": "atomic_with_decompositions",
                    "structural_hint": "", "own_uid": own_uid, "component_uids": useq_to_uplus_list(useq_val)}
        return {"sign_type": "Type_1", "sign_structure": "atomic",
                "structural_hint": "", "own_uid": own_uid, "component_uids": []}

    if useq_val:
        return {"sign_type": "Type_2", "sign_structure": "compound",
                "structural_hint": "", "own_uid": "", "component_uids": useq_to_uplus_list(useq_val)}

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


def load_unicode_reference(path):
    ref = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uid = row.get("unicode_id", "").strip()
            if uid:
                ref[uid] = row.get("sign_grapheme", "").strip()
    print(f"[INFO] Loaded {len(ref)} entries from unicode reference")
    return ref


def load_phonetic_reference(path):
    ref = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            uid = row.get("unicode_id", "").strip()
            if uid:
                ref[uid] = {"unicodeTrLit": row.get("unicodeTrLit", "").strip(),
                            "syllabarySign": row.get("syllabarySign", "").strip(),
                            "PhoneticsVersion": row.get("PhoneticsVersion", "").strip()}
    print(f"[INFO] Loaded {len(ref)} entries from phonetic reference")
    return ref



# STAGE 1 PARSE osl.asl ONCE: classify every sign, decompose compounds, and collect @v readings, all from a single pass over the file


def parse_osl(path, unicode_ref):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    sign_index = {}
    entity_v_index = {}
    sign_blocks_raw = re.split(r'^@sign-?[ \t]', content, flags=re.MULTILINE)
   
    deprecated_starts = set(m.start() for m in re.finditer(r'^@sign-[ \t]', content, flags=re.MULTILINE))
    all_starts = [m.start() for m in re.finditer(r'^@sign-?[ \t]', content, flags=re.MULTILINE)]

    sign_blocks = []
    for idx, block in enumerate(sign_blocks_raw[1:]):
        is_deprecated = all_starts[idx] in deprecated_starts
        sign_blocks.append((block, is_deprecated))

    for block, is_deprecated in sign_blocks:
        if not block.strip() or block.strip().startswith('@'):
            continue
        if is_deprecated:
            continue 
        lines = block.strip().split('\n')
        name, header_lines = split_entity_lines(lines)
        header = parse_entity_header(header_lines)
        sign_index[name] = header
        entity_v_index[name] = header
        form_parts = split_form_blocks(block)
        for form_section, form_is_dep in form_parts:
            if form_is_dep:
                continue  
            form_lines = form_section.strip().split('\n')
            entity_v_index[form_lines[0].strip()] = parse_entity_header(form_lines[1:])
    entity_index = sign_index  

    sign_rows = []
    for block, is_deprecated in sign_blocks:
        if not block.strip() or block.strip().startswith('@'):
            continue
        if is_deprecated:
            continue  
        block_lines = block.strip().split('\n')
        sign_name, sign_header_lines = split_entity_lines(block_lines)
        sign_header = parse_entity_header(sign_header_lines)
        sign_parent_lists = sign_header["catalog_refs"]

        form_parts_raw = split_form_blocks(block)
        form_sections = [seg for seg, is_dep in form_parts_raw if not is_dep]

        if not form_sections:
            if sign_header["is_fake"]:
                continue  
            cls = classify_entity(sign_name, sign_header, entity_index, unicode_ref)
            sign_rows.extend(build_rows_for_entity(
                sign_name, "", cls, sign_header["ucun"], unicode_ref,
                build_signlist_analogue([], sign_parent_lists)))
        else:
            # v12 FIX: write the sign itself first (its own code point and
            # readings), then its variants. v11 skipped the sign here.
            if not sign_header["is_fake"]:
                cls_parent = classify_entity(sign_name, sign_header, entity_index, unicode_ref)
                sign_rows.extend(build_rows_for_entity(
                    sign_name, "", cls_parent, sign_header["ucun"], unicode_ref,
                    build_signlist_analogue([], sign_parent_lists)))
            for form_section in form_sections:
                form_lines = form_section.strip().split('\n')
                form_name = form_lines[0].strip()
                form_header = parse_entity_header(form_lines[1:])
                if form_header["is_fake"]:
                    continue 
                cls = classify_entity(form_name, form_header, entity_index, unicode_ref)

                if (cls["sign_type"] == "Type_3" and not cls["component_uids"]
                        and not cls["own_uid"] and cls["structural_hint"] != "compound_unresolved"):
                    parent_uid = sign_header["own_uid"]
                    if parent_uid:
                        inherited = parent_uid if parent_uid in unicode_ref else parent_uid + " [unverified]"
                        cls = dict(cls)
                        cls["own_uid"] = inherited
                        cls["sign_structure"] = "atomic"
                        cls["structural_hint"] = "inherited_from_parent"

                sign_list_str = build_signlist_analogue(form_header["catalog_refs"], sign_parent_lists)
                own_ucun = form_header["ucun"] or sign_header["ucun"]
                sign_rows.extend(build_rows_for_entity(
                    sign_name, form_name, cls, own_ucun, unicode_ref, sign_list_str))

    return sign_rows, entity_v_index


def build_rows_for_entity(sign_name, osl_form, cls, own_ucun, unicode_ref, sign_list_str):
    rows = []
    entity_label = osl_form if osl_form else sign_name

    if cls["sign_structure"] in ("atomic", "not_identified"):
        rows.append({"unicode_id": cls["own_uid"],
                     "sign_grapheme": own_ucun or unicode_ref.get(cls["own_uid"], ""),
                     "sign_structure": cls["sign_structure"], "structural_hint": cls["structural_hint"],
                     "component_position": "", "sign_name": sign_name, "osl_form": osl_form,
                     "osl_form_id": "", "sign_type": cls["sign_type"],
                     "compound_form": "", "compound_grapheme": "", "compound_unicode": "",
                     "signList_analogue": sign_list_str})

    elif cls["sign_structure"] == "atomic_with_decompositions":
        comp_glyphs = [unicode_ref.get(u.replace(" [unverified]", ""), "") for u in cls["component_uids"]]
        rows.append({"unicode_id": cls["own_uid"],
                     "sign_grapheme": own_ucun or unicode_ref.get(cls["own_uid"].replace(" [unverified]", ""), ""),
                     "sign_structure": cls["sign_structure"], "structural_hint": "",
                     "component_position": "", "sign_name": sign_name, "osl_form": osl_form,
                     "osl_form_id": "", "sign_type": cls["sign_type"],
                     "compound_form": entity_label, "compound_grapheme": "".join(comp_glyphs) or own_ucun,
                     "compound_unicode": "; ".join(cls["component_uids"]), "signList_analogue": sign_list_str})

    elif cls["sign_structure"] == "compound":
        comp_uids = cls["component_uids"]
        comp_glyphs = [unicode_ref.get(u.replace(" [unverified]", ""), "") for u in comp_uids]
        full_cun = own_ucun or "".join(comp_glyphs)
        uid_seq = "; ".join(comp_uids)
        for pos, uid in enumerate(comp_uids, start=1):
            rows.append({"unicode_id": uid, "sign_grapheme": unicode_ref.get(uid.replace(" [unverified]", ""), ""),
                         "sign_structure": "compound", "structural_hint": "", "component_position": str(pos),
                         "sign_name": sign_name, "osl_form": osl_form, "osl_form_id": "",
                         "sign_type": cls["sign_type"], "compound_form": entity_label,
                         "compound_grapheme": full_cun, "compound_unicode": uid_seq,
                         "signList_analogue": sign_list_str})
    return rows


def assign_variant_ids(rows):
    form_order = defaultdict(dict)
    for row in rows:
        sign, form = row["sign_name"], row["osl_form"]
        if form not in form_order[sign]:
            form_order[sign][form] = len(form_order[sign]) + 1
    for row in rows:
        sign, form = row["sign_name"], row["osl_form"]
        row["osl_form_id"] = f"{make_variant_prefix(sign)}_v{form_order[sign][form]}"
    return rows


def join_phonetics(rows, phon_ref):
    for row in rows:
        uid = row["unicode_id"].replace(" [unverified]", "")
        p = phon_ref.get(uid)
        row["unicodeTrLit"] = p["unicodeTrLit"] if p else ""
        row["syllabary_sign"] = p["syllabarySign"] if p else ""
        row["phonetic_version"] = p["PhoneticsVersion"] if p else ""
    return rows



# STAGE 2 compound_form_reading_table: for every compound sign identified in Stage 1, resolve its whole-word reading from @v tags, or the merged historical syllabary as fallback


def load_syllabary(path):
    name_to_readings = defaultdict(list)
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name, reading = row["sign_name"].strip(), row["phonetic_reading"].strip()
            if name and reading:
                name_to_readings[name].append(reading)
    return name_to_readings


def load_diri_lexical(path):
    """Returns {normalized_sign_sequence: [reading, reading, ...]}, aggregating
    every attested reading across all surviving Diri tablet lines that share
    that exact sign sequence """
    seq_to_readings = defaultdict(list)
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            seq = row["sign_sequence"].strip()
            reading = row["sumerian_reading"].strip()
            if not seq or not reading:
                continue  # line too broken to use — need both fields together
            norm = normalize_name(seq)
            if reading not in seq_to_readings[norm]:
                seq_to_readings[norm].append(reading)
    return seq_to_readings


def load_ogsl(path):
    """Returns {normalized_sign_name: [reading, ...]}, from the OGSL
    (Oracc Global Sign List) portal export a cross-project consolidation
    of sign values drawn from ABZL, BAU, HZL, KWU, LAK, MZL, RSP, SLLHA,
    and other historical sign lists, one 'Values:' entry per sign."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {normalize_name(name): readings for name, readings in raw.items()}


def build_compound_table(sign_rows, entity_index, name_to_readings, diri_readings, ogsl_readings):
    compound_forms = set()
    compound_components = defaultdict(list)
    for row in sign_rows:
        if row["sign_structure"] == "compound":
            cf = row["compound_form"]
            compound_forms.add(cf)
            pos = int(row["component_position"]) if row["component_position"] else 0
            phon = row["phonetic_version"].strip()
            compound_components[cf].append((pos, phon.split("|")[0].strip() if phon else None))

    syll_names = list(name_to_readings.keys())
    table_rows, status_by_form, reading_by_form = [], {}, {}

    for cf in sorted(compound_forms):
        norm = normalize_name(cf)
        v_reading = entity_index.get(cf, {}).get("v_values", [])
        diri_reading = diri_readings.get(norm)
        ogsl_reading = ogsl_readings.get(norm)
        syll_reading = name_to_readings.get(norm)

        nested_in = []
        if not v_reading and not diri_reading and not ogsl_reading and not syll_reading:
            nested_in = [n for n in syll_names if norm in n and n != norm][:5]

        comps = sorted(compound_components.get(cf, []))
        inferred = "-".join(c[1].lower() for c in comps) if comps and all(c[1] for c in comps) else ""

       
        if v_reading:
            status, source, reading = "ATTESTED_DIRECT", "OSL", v_reading
        elif diri_reading:
            status, source, reading = "ATTESTED_DIRECT", "DIRI", diri_reading
        elif ogsl_reading:
            status, source, reading = "ATTESTED_DIRECT", "OGSL", ogsl_reading
        elif syll_reading:
            status, source, reading = "ATTESTED_DIRECT", "SYLLABARY_CM", syll_reading
        elif nested_in:
            status, source, reading = "NESTED_IN_LONGER_FORM", "", []
        else:
            status, source, reading = "NO_ATTESTED_READING", "", []

        status_by_form[cf] = status
        reading_by_form[cf] = "|".join(reading)
        table_rows.append({"compound_form": cf, "compound_form_normalized": norm,
                           "PhoneticVersion_Compound": "|".join(reading), "reading_status": status,
                           "reading_source": source, "nested_in_forms": "; ".join(nested_in),
                           "component_reading_inferred": inferred})

    return table_rows, status_by_form, reading_by_form

# STAGE 3 sign catalogue: attach phonetic typing to every sign (using Stage 2's compound readings) and extend coverage with sign names attested only in the historical syllabary


def clean_osl_value(v):
    """v13: usable @v value: no language-tagged lemmas (%akk ...), no
    multi-word values, trailing '?' removed."""
    v = v.strip()
    if not v or v.startswith("%") or " " in v:
        return ""
    return v.rstrip("?")


def reading_key(v):
    return v.strip().translate(SUBSCRIPT_TO_ASCII).lower()


def add_osl_values(v8_rows, entity_v_index):
    """v13: fill gaps in the readings of simple-sign rows with OSL @v values.
    Returns the list of conflicts (OSL value already given to another sign)."""
    simple = [r for r in v8_rows if r["typePhonetic_Version"] == "Single Sign Reading"]
    owner = {}
    for r in simple:
        for v in r["phonetic_version"].split("|"):
            if v.strip():
                owner.setdefault(reading_key(v), r.get("osl_form") or r["sign_name"])
    conflicts, seen_conf = [], set()
    for r in v8_rows:
        r.setdefault("osl_v_added", "")
    for r in simple:
        if r["sign_source"] != "OSL":
            continue
        entity = r.get("osl_form") or r["sign_name"]
        values = [clean_osl_value(v) for v in entity_v_index.get(entity, {}).get("v_values", [])]
        added = []
        for v in values:
            if not v:
                continue
            k = reading_key(v)
            if k not in owner:
                owner[k] = entity
                added.append(v)
            elif owner[k] != entity and (k, entity) not in seen_conf:
                seen_conf.add((k, entity))
                conflicts.append({"reading": v, "osl_sign": entity,
                                  "catalogue_sign": owner[k]})
        if added:
            existing = [v.strip() for v in r["phonetic_version"].split("|") if v.strip()]
            r["phonetic_version"] = " | ".join(existing + added)
            r["osl_v_added"] = " | ".join(added)
    return conflicts


def link_syllabary_rows(v8_rows, entity_v_index, reading_by_form, unicode_ref):
    """v13: link names that come only from the historical syllabaries to OSL
    when the link is unambiguous:
      - the name is an OSL sign/form name with its own code point
        -> unicode_id filled (structural_hint unicode_via_osl_name);
      - the name is an OSL value of exactly one simple sign
        -> unicode_id filled (unicode_via_osl_value);
      - the name is an OSL value of exactly one COMPOUND sign (PA3 = pa₃ of
        |IGI.RU|) -> the row becomes a reference to that compound
        (typePhonetic_Version 'Syllabary Name Of OSL Compound',
        compound_form = |IGI.RU|), so that it no longer hides the compound
        reading from the parser.
    Ambiguous names are only marked (osl_value_ambiguous)."""
    name_uid = {}
    value_owner = defaultdict(set)      # reading -> {("atomic", uid, ucun) | ("compound", form)}
    for name, header in entity_v_index.items():
        uid = header.get("own_uid", "")
        if uid:
            name_uid.setdefault(reading_key(normalize_name(name)), (uid, header.get("ucun", "")))
            for v in header.get("v_values", []):
                v = clean_osl_value(v)
                if v:
                    value_owner[reading_key(v)].add(("atomic", uid, header.get("ucun", "")))
    for form, readings in reading_by_form.items():
        for v in readings.split("|"):
            v = clean_osl_value(v)
            if v:
                value_owner[reading_key(v)].add(("compound", form, ""))
    linked = Counter()
    for r in v8_rows:
        if r["sign_source"] == "OSL" or r["unicode_id"]:
            continue
        key = reading_key(normalize_name(r["sign_name"]))
        owners = value_owner.get(key, set())
        if key in name_uid:
            uid, ucun = name_uid[key]
            r["unicode_id"], r["sign_grapheme"] = uid, ucun or unicode_ref.get(uid, "")
            r["structural_hint"] = "unicode_via_osl_name"
            linked["unicode_via_osl_name"] += 1
        elif len(owners) == 1:
            kind, target, ucun = next(iter(owners))
            if kind == "atomic":
                r["unicode_id"], r["sign_grapheme"] = target, ucun or unicode_ref.get(target, "")
                r["structural_hint"] = "unicode_via_osl_value"
                linked["unicode_via_osl_value"] += 1
            else:
                r["typePhonetic_Version"] = "Syllabary Name Of OSL Compound"
                r["compound_form"] = target
                r["structural_hint"] = "osl_value_of_compound"
                linked["osl_value_of_compound"] += 1
        elif len(owners) > 1:
            r["structural_hint"] = "osl_value_ambiguous"
            linked["osl_value_ambiguous"] += 1
        else:
            linked["no_osl_match"] += 1
    return linked


def build_v8_rows(sign_rows, status_by_form, reading_by_form, diri_readings, ogsl_readings):
    v8_rows = []
    covered_names = set()
    for raw in sign_rows:
        row = dict(raw)
        row["sign_source"] = "OSL"
        ss = row["sign_structure"]
        norm = normalize_name(row["sign_name"])

        if ss in ("atomic", "atomic_with_decompositions"):
            row["typePhonetic_Version"] = "Single Sign Reading"
           
            if not row["phonetic_version"].strip():
                if norm in diri_readings:
                    row["phonetic_version"] = "|".join(diri_readings[norm])
                    row["structural_hint"] = "phonetic_via_diri"
                elif norm in ogsl_readings:
                    row["phonetic_version"] = "|".join(ogsl_readings[norm])
                    row["structural_hint"] = "phonetic_via_ogsl"
        elif ss == "compound":
            status = status_by_form.get(row["compound_form"], "NO_ATTESTED_READING")
            row["typePhonetic_Version"] = TYPE_PHONETIC_LABELS[status]
            row["phonetic_version"] = reading_by_form.get(row["compound_form"], "") if status == "ATTESTED_DIRECT" else ""
        else:
            row["typePhonetic_Version"] = "No Sign Identity"
            row["phonetic_version"] = ""
         
            if norm in diri_readings:
                row["phonetic_version"] = "|".join(diri_readings[norm])
                row["structural_hint"] = "phonetic_via_diri"
            elif norm in ogsl_readings:
                row["phonetic_version"] = "|".join(ogsl_readings[norm])
                row["structural_hint"] = "phonetic_via_ogsl"

        v8_rows.append(row)
        covered_names.add(norm)
        if row["compound_form"]:
            covered_names.add(normalize_name(row["compound_form"]))
    return v8_rows, covered_names


def build_syllabary_only_rows(path, covered_names):
    name_to_readings = defaultdict(list)
    name_to_source = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name, reading = row["sign_name"].strip(), row["phonetic_reading"].strip()
            if not name or not reading:
                continue
            name_to_readings[name].append(reading)
            name_to_source[name] = row["source"].strip()

    rows = []
    for name, readings in sorted(name_to_readings.items()):
        if normalize_name(name) in covered_names:
            continue
        prefix = make_variant_prefix(name)
        rows.append({"unicode_id": "", "sign_grapheme": "",
                     "sign_source": SOURCE_LABELS.get(name_to_source.get(name, ""), name_to_source.get(name, "")),
                     "sign_structure": "not_identified", "structural_hint": "", "component_position": "",
                     "sign_name": name, "osl_form": "", "osl_form_id": f"{prefix}_v1",
                     "sign_type": "Type_3", "compound_form": "", "compound_grapheme": "", "compound_unicode": "",
                     "typePhonetic_Version": "Single Sign Reading", "phonetic_version": "|".join(readings),
                     "unicodeTrLit": "", "syllabary_sign": name, "signList_analogue": ""})
    return rows


def write_csv(rows, path, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


# ENTRY POINT

def main():
    check_inputs()
    unicode_ref = load_unicode_reference(INPUT_UNICODE)
    phon_ref = load_phonetic_reference(INPUT_PHONETIC)

    print(f"\n[Parsing] {INPUT_ASL}: classifying every sign, decomposing compounds")
    sign_rows, entity_v_index = parse_osl(INPUT_ASL, unicode_ref)
    sign_rows = assign_variant_ids(sign_rows)
    sign_rows = join_phonetics(sign_rows, phon_ref)
    print(f"  {len(sign_rows)} rows classified")

    print(f"\n[Step 3] Building compound_form_reading_table.csv")
    name_to_readings = load_syllabary(INPUT_SYLLABARY)
    diri_readings = load_diri_lexical(INPUT_DIRI)
    ogsl_readings = load_ogsl(INPUT_OGSL)
    print(f"  {len(diri_readings)} distinct sign sequences with attested Diri readings")
    print(f"  {len(ogsl_readings)} distinct sign sequences with attested OGSL readings")
    table_rows, status_by_form, reading_by_form = build_compound_table(
        sign_rows, entity_v_index, name_to_readings, diri_readings, ogsl_readings)
    write_csv(table_rows, OUTPUT_COMPOUND_TABLE, list(table_rows[0].keys()))
    stats = Counter(r["reading_status"] for r in table_rows)
    src_stats = Counter(r["reading_source"] for r in table_rows if r["reading_source"])
    print(f"  {len(table_rows)} rows -> {OUTPUT_COMPOUND_TABLE}")
    print(f"  ATTESTED_DIRECT {stats['ATTESTED_DIRECT']}, NESTED {stats['NESTED_IN_LONGER_FORM']}, "
          f"NONE {stats['NO_ATTESTED_READING']}")
    print(f"    via OSL: {src_stats['OSL']}, via DIRI: {src_stats['DIRI']}, "
          f"via OGSL: {src_stats['OGSL']}, via SYLLABARY_CM: {src_stats['SYLLABARY_CM']}")

    print(f"\n[Step 4] Building {OUTPUT_V8}")
    v8_rows, covered_names = build_v8_rows(sign_rows, status_by_form, reading_by_form, diri_readings, ogsl_readings)
    v8_rows += build_syllabary_only_rows(INPUT_SYLLABARY, covered_names)
    # v13: OSL @v values fill gaps; syllabary names linked to OSL signs
    conflicts = add_osl_values(v8_rows, entity_v_index)
    linked = link_syllabary_rows(v8_rows, entity_v_index, reading_by_form, unicode_ref)
    write_csv(conflicts, OUTPUT_CONFLICTS, ["reading", "osl_sign", "catalogue_sign"])
    n_added = sum(1 for r in v8_rows if r.get("osl_v_added"))
    n_values = sum(len(r["osl_v_added"].split("|")) for r in v8_rows if r.get("osl_v_added"))
    print(f"  OSL @v values added: {n_values} values in {n_added} rows; "
          f"conflicts recorded: {len(conflicts)} -> {OUTPUT_CONFLICTS}")
    print(f"  syllabary names linked to OSL: {dict(linked)}")
    write_csv(v8_rows, OUTPUT_V8, V8_FIELDNAMES)
    print(f"  {len(v8_rows)} rows, {len({r['sign_name'] for r in v8_rows})} unique sign_name -> {OUTPUT_V8}")


if __name__ == "__main__":
    main()
