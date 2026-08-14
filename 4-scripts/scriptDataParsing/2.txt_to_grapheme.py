#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
atf_to_grapheme.py  (v1.0)
================================================================================
CODE №2  —  ANNOTATION LAYER  /  TOKENISATION + PoS-TAGGING + METADATA
================================================================================

PURPOSE
-------
Takes the TXT files produced by transferTrLit_Sign.py (scientific sign names)
and the original ATF files, then:

  Layer 1  Tokenisation    — splits each TXT line into individual sign tokens
  Layer 2  Unicode lookup  — assigns unicode_id + cuneiform grapheme to each
                             token via loop over 6_unicodeTrLit_Grph_Phon.csv
  Layer 3  PoS-tagging     — LOGO | SYLL | NUMERAL | COMPOUND | SIMPLE | UNKNOWN
  Layer 4  Metadata        — provenance, period, corpus from ATF &-/#-lines

OUTPUT  (two CSV files, one per run)
------
  A.  unicode.csv    — sign reference table (one row per unique sign)
        unicode_id | sign_grapheme | unicodeTrLit | scientific_name

  B.  grapheme.csv   — attestation table (ONE ROW = ONE TOKEN OCCURRENCE)
        unicode_id | sign_cuneiform | sign_trlitScien | sign_trlitPhonet |
        sign_translation | artifact_id | corpus_id | genre_name |
        provenance | archaeological_context | period_index | period_dates |
        languages | sign_type | is_compound

  One row = one fact of transliteration in one artifact.
  The same unicode_id will repeat many times → enables frequency analysis,
  logographic vs syllabographic use, cross-corpus comparison.

USAGE
-----
  python atf_to_grapheme.py

  The script will prompt for:
    1. Path to the folder produced by transferTrLit_Sign.py
       (containing *_sign_names.txt files)
    2. Path to the original ATF folder/file
       (for metadata extraction from &-lines)
    3. Path to 6_unicodeTrLit_Grph_Phon.csv

================================================================================
"""

import sys
import os
import re
import csv
from pathlib import Path
from collections import defaultdict


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD UNICODE SIGN TABLE
# Source: 6_unicodeTrLit_Grph_Phon.csv
# Builds two indexes:
#   sci_to_row   {scientific_name → row}   (primary lookup)
#   phon_to_row  {phonetic_reading → row}  (secondary / fallback)
# ══════════════════════════════════════════════════════════════════════════════

def load_unicode_table(csv_path: str) -> tuple[dict, dict]:
    """
    Returns (sci_to_row, phon_to_row).
    Each value is a dict with keys:
        unicode_id | sign_grapheme | unicodeTrLit | syllabarySign
        + derived: all_phonetic (list), all_logographic (list),
                   polyphony_count, sign_type, is_compound
    """
    sci_to_row:  dict[str, dict] = {}
    phon_to_row: dict[str, dict] = {}

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sci    = row["syllabarySign"].strip()
            phon   = row["unicodeTrLit"].strip()
            uid    = row["unicode_id"].strip()
            glyph  = row["sign_grapheme"].strip()
            allvar = row["PhoneticsVersion"].strip()

            # Split all variants, classify by case
            variants  = [v.strip() for v in allvar.split("|") if v.strip()]
            logos     = [v for v in variants if v and v[0].isupper()
                         and not re.match(r'^N\d', v)]
            sylls     = [v for v in variants if v and v[0].islower()]
            nums      = [v for v in variants if re.match(r'^N\d', v)]

            # sign_type: based on what readings exist
            if nums:
                stype = "NUMERAL"
            elif logos and sylls:
                # Both exist — will be disambiguated per token at PoS step
                stype = "BIVALENT"
            elif logos:
                stype = "LOGO"
            elif sylls:
                stype = "SYLL"
            else:
                stype = "UNKNOWN"

            # is_compound: scientific name contains ×, +, or .
            is_comp = "COMPOUND" if re.search(r'[×x+.]', sci) else "SIMPLE"

            enriched = {
                "unicode_id":      uid,
                "sign_grapheme":   glyph,
                "unicodeTrLit":    phon,
                "scientific_name": sci,
                "all_phonetic":    sylls,
                "all_logographic": logos,
                "all_numeral":     nums,
                "polyphony_count": len(variants),
                "default_stype":   stype,
                "is_compound":     is_comp,
            }

            # Index by scientific name (primary)
            if sci and sci not in sci_to_row:
                sci_to_row[sci] = enriched

            # Index by primary phonetic reading
            if phon and phon not in phon_to_row:
                phon_to_row[phon] = enriched

            # Index ALL variant readings as secondary phonetic keys
            for v in variants:
                if v and v not in phon_to_row:
                    phon_to_row[v] = enriched

    print(f"[unicode table] {len(sci_to_row)} scientific names indexed")
    print(f"[unicode table] {len(phon_to_row)} phonetic variants indexed\n")
    return sci_to_row, phon_to_row


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — WRITE unicode.csv  (reference table, one row per unique sign)
# ══════════════════════════════════════════════════════════════════════════════

UNICODE_FIELDS = [
    "unicode_id",
    "sign_grapheme",
    "unicodeTrLit",
    "scientific_name",
]


def write_unicode_csv(sci_to_row: dict, out_path: str) -> None:
    seen: set[str] = set()
    rows: list[dict] = []
    for sci, row in sorted(sci_to_row.items()):
        uid = row["unicode_id"]
        if uid in seen:
            continue
        seen.add(uid)
        rows.append({
            "unicode_id":      uid,
            "sign_grapheme":   row["sign_grapheme"],
            "unicodeTrLit":    row["unicodeTrLit"],
            "scientific_name": row["scientific_name"],
        })

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=UNICODE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[unicode.csv] {len(rows)} unique signs written → {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — ATF METADATA PARSER
# Extracts tablet-level metadata from ATF header lines (&, #, @).
# ══════════════════════════════════════════════════════════════════════════════

# Period string → (period_index label, period_dates as BC midpoint integer)
PERIOD_TABLE: list[tuple[str, str, int]] = [
    # keyword_in_lower         period_index                period_dates (BCE)
    ("uruk",                   "Uruk",                      3400),
    ("jemdet nasr",            "Jemdet Nasr",               3000),
    ("early dynastic i",       "Early Dynastic I",          2900),
    ("early dynastic ii",      "Early Dynastic II",         2750),
    ("early dynastic iii",     "Early Dynastic IIIa",       2600),
    ("early dynastic",         "Early Dynastic",            2700),
    ("old akkadian",           "Old Akkadian",              2340),
    ("lagash ii",              "Lagash II",                 2150),
    ("ur iii",                 "Ur III",                    2100),
    ("old babylonian",         "Old Babylonian",            1900),
    ("old assyrian",           "Old Assyrian",              1900),
    ("middle babylonian",      "Middle Babylonian",         1400),
    ("middle assyrian",        "Middle Assyrian",           1300),
    ("neo-assyrian",           "Neo-Assyrian",               700),
    ("neo-babylonian",         "Neo-Babylonian",             600),
    ("late babylonian",        "Late Babylonian",            400),
    ("achaemenid",             "Achaemenid",                 500),
    ("hellenistic",            "Hellenistic",                300),
]

# Corpus type keywords → (corpus_id, genre_name)
CORPUS_TABLE: list[tuple[str, str, str]] = [
    ("lexical",          "SCHOOL",   "Lexical / school corpus"),
    ("school",           "SCHOOL",   "Lexical / school corpus"),
    ("eduba",            "SCHOOL",   "Lexical / school corpus"),
    ("administrative",   "ADMIN",    "Administrative corpus"),
    ("admin",            "ADMIN",    "Administrative corpus"),
    ("legal",            "LEGAL",    "Legal corpus"),
    ("literary",         "LIT",      "Literary corpus"),
    ("hymn",             "LIT",      "Literary corpus"),
    ("myth",             "LIT",      "Literary corpus"),
    ("ritual",           "LIT",      "Literary corpus"),
    ("letter",           "LETTER",   "Letters"),
    ("trade",            "TRADE",    "Trade / commercial corpus"),
    ("royal",            "ROYAL",    "Royal inscriptions"),
    ("mathematical",     "MATH",     "Mathematical corpus"),
    ("astronomical",     "ASTRO",    "Astronomical corpus"),
]

# Provenance city → archaeological_context (main administrative city)
PROVENANCE_CONTEXT: dict[str, str] = {
    "nippur":    "Nippur",
    "ur":        "Ur",
    "uruk":      "Uruk",
    "lagash":    "Lagash",
    "girsu":     "Lagash",       # Girsu is part of the Lagash city-state
    "umma":      "Umma",
    "eridu":     "Eridu",
    "sippar":    "Sippar",
    "babylon":   "Babylon",
    "assur":     "Assur",
    "nineveh":   "Nineveh",
    "larsa":     "Larsa",
    "isin":      "Isin",
    "eshnunna":  "Eshnunna",
    "adab":      "Adab",
    "kish":      "Kish",
    "shuruppak": "Shuruppak",
    "drehem":    "Ur",           # Drehem (Puzrish-Dagan) = administrative centre of Ur III Ur
    "garšana":   "Garšana",
    "ebla":      "Ebla",
    "mari":      "Mari",
}


def parse_atf_metadata(header_lines: list[str]) -> dict:
    """
    Parse ATF &-line and #-comment lines to extract tablet metadata.
    Returns a dict with all grapheme.csv metadata fields.
    """
    meta = {
        "artifact_id":            "",
        "corpus_id":              "",
        "genre_name":             "",
        "provenance":             "",
        "archaeological_context": "",
        "period_index":           "",
        "period_dates":           "",
        "languages":              "",
    }

    full_text = " ".join(header_lines).lower()

    # artifact_id — P-number from &-line
    for line in header_lines:
        m = re.match(r'&\s*(P\d+)', line.strip())
        if m:
            meta["artifact_id"] = m.group(1)
            break

    # language
    lang_m = re.search(r'#atf:\s*lang\s+(\w+)', " ".join(header_lines))
    if lang_m:
        lang_code = lang_m.group(1).lower()
        lang_map = {
            "sux": "Sumerian", "akk": "Akkadian", "qpn": "Proper nouns",
            "sux-x-emesal": "Emesal", "ebl": "Eblaite", "hit": "Hittite",
            "elx": "Elamite",
        }
        meta["languages"] = lang_map.get(lang_code, lang_code.upper())

    # period
    for kw, label, date in PERIOD_TABLE:
        if kw in full_text:
            meta["period_index"] = label
            meta["period_dates"] = str(date)
            break

    # corpus
    for kw, cid, gname in CORPUS_TABLE:
        if kw in full_text:
            meta["corpus_id"]  = cid
            meta["genre_name"] = gname
            break

    # provenance
    for city, context in PROVENANCE_CONTEXT.items():
        if city in full_text:
            meta["provenance"]             = city.capitalize()
            meta["archaeological_context"] = context
            break

    return meta


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — PoS TAGGER
# Input: scientific name (UPPERCASE) or phonetic reading (lowercase)
# Rules:
#   scientific name ALL-CAPS (no lowercase letters) → LOGO
#   primary phonetic (all lowercase) → SYLL
#   starts with N + digits → NUMERAL
#   contains ×, +, .      → COMPOUND (overrides LOGO/SYLL)
#   determinative {…}     → DET (determinative, a type of LOGO)
#   unknown                → UNKNOWN
# Note: POLY is NOT a PoS tag here. Per the workflow, each row = one token =
# one specific use, so we tag the actual use (LOGO or SYLL), not the sign's
# potential.
# ══════════════════════════════════════════════════════════════════════════════

def pos_tag(sci_name: str, phonetic_token: str) -> tuple[str, str]:
    """
    Returns (sign_type, is_compound).

    sign_type choices:
        LOGO      — used as logogram (sign name written in caps in original ATF,
                    or resolved to a caps-only scientific name)
        SYLL      — used as syllabogram (lowercase in original ATF)
        NUMERAL   — numeric sign (N01, 1(diš), etc.)
        COMPOUND  — compound sign (contains × + .)
        SIMPLE    — simple sign (neither of the above categories)
        UNKNOWN   — could not be determined
    """
    if not sci_name:
        return ("UNKNOWN", "SIMPLE")

    # NUMERAL
    if re.match(r'^N\d', sci_name) or re.match(r'^\d', phonetic_token):
        return ("NUMERAL", "SIMPLE")

    # COMPOUND check (applies to both LOGO and SYLL)
    is_comp = "COMPOUND" if re.search(r'[×x+.]', sci_name) else "SIMPLE"

    # Determine LOGO vs SYLL from the original phonetic token case
    if phonetic_token and phonetic_token[0].isupper():
        stype = "LOGO"
    elif phonetic_token and phonetic_token[0].islower():
        stype = "SYLL"
    else:
        # Fallback: if sci_name is all-caps (no lowercase letters) → LOGO
        letters = re.sub(r'[^a-zA-Z]', '', sci_name)
        stype = "LOGO" if letters == letters.upper() else "SYLL"

    # If compound → return COMPOUND (subsumes LOGO/SYLL structural info)
    if is_comp == "COMPOUND":
        return ("COMPOUND", "COMPOUND")

    return (stype, "SIMPLE")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — PROCESS ONE TXT FILE + MATCHING ATF METADATA
# ══════════════════════════════════════════════════════════════════════════════

GRAPHEME_FIELDS = [
    "unicode_id",
    "sign_grapheme",
    "sign_trlitScien",
    "sign_phonetic",
    "sign_translation",
    "artifact_id",
    "corpus_id",
    "genre_name",
    "provenance",
    "archaeological_context",
    "period_index",
    "period_dates",
    "languages",
    "sign_type",
    "is_compound",
]


def process_txt_file(
    txt_path: Path,
    atf_meta: dict,
    sci_to_row: dict,
    phon_to_row: dict,
    records: list[dict],
    missing: dict[str, int],
) -> None:
    """
    Read one *_sign_names.txt file, loop over sign tokens,
    look up each in unicode table, append rows to `records`.
    """
    with open(txt_path, encoding="utf-8") as f:
        lines = f.readlines()

    for raw in lines:
        line = raw.rstrip("\n")

        # Skip header/structural lines
        if re.match(r'^.?[&@$#>]', line) or not line.strip():
            continue

        # Extract line number + content
        m = re.match(r'^(\S+)\s+(.*)', line)
        if not m:
            continue

        line_num = m.group(1)
        content  = m.group(2).strip()

        # Each space-separated token is one scientific sign name
        # (diri compounds were already expanded to individual components
        #  by transferTrLit_Sign.py)
        sign_tokens = content.split()

        for pos, sci_tok in enumerate(sign_tokens, start=1):
            sci_tok = sci_tok.strip()
            if not sci_tok:
                continue

            # ── Unicode lookup ────────────────────────────────────────────
            row = sci_to_row.get(sci_tok)

            # Fallback: look up via phonetic index (handles lowercase tokens
            # that transferTrLit_Sign left unresolved)
            if row is None:
                row = phon_to_row.get(sci_tok)

            if row is None:
                missing[sci_tok] = missing.get(sci_tok, 0) + 1
                uid      = ""
                glyph    = ""
                sci_name = sci_tok
                phon     = ""
            else:
                uid      = row["unicode_id"]
                glyph    = row["sign_grapheme"]
                sci_name = row["scientific_name"]
                phon     = row["unicodeTrLit"]    # primary phonetic reading

            # ── PoS tagging ───────────────────────────────────────────────
            sign_type, is_compound = pos_tag(sci_name, sci_tok)

            # ── Build record ──────────────────────────────────────────────
            record = {
                "unicode_id":             uid,
                "sign_grapheme":         glyph,
                "sign_trlitScien":        sci_name,
                "sign_phonetic":       phon,
                "sign_translation":       "",      # to be filled manually / from dict
                "artifact_id":            atf_meta.get("artifact_id", ""),
                "corpus_id":              atf_meta.get("corpus_id",   ""),
                "genre_name":             atf_meta.get("genre_name",  ""),
                "provenance":             atf_meta.get("provenance",  ""),
                "archaeological_context": atf_meta.get("archaeological_context", ""),
                "period_index":           atf_meta.get("period_index", ""),
                "period_dates":           atf_meta.get("period_dates", ""),
                "languages":              atf_meta.get("languages",   ""),
                "sign_type":              sign_type,
                "is_compound":            is_compound,
            }
            records.append(record)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — LOAD ATF METADATA FOR ALL TABLETS
# Reads all ATF files and indexes them by P-number.
# ══════════════════════════════════════════════════════════════════════════════

def load_all_atf_metadata(atf_source: Path) -> dict[str, dict]:
    """
    Returns {artifact_id (P-number): metadata_dict}.
    Also returns a dict keyed by filename stem for files without P-numbers.
    """
    if atf_source.is_dir():
        atf_files = list(atf_source.glob("*.atf")) + list(atf_source.glob("*.txt"))
    else:
        atf_files = [atf_source]

    index: dict[str, dict] = {}   # by P-number
    by_stem: dict[str, dict] = {}  # by filename stem

    for atf_path in atf_files:
        with open(atf_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Collect header lines until first transliteration line
        header_buf: list[str] = []
        current_pid = ""

        for raw in lines:
            s = raw.rstrip("\n")
            if re.match(r'^&', s):
                # Save previous tablet if any
                if header_buf and current_pid:
                    meta = parse_atf_metadata(header_buf)
                    index[current_pid] = meta
                # Start new tablet
                header_buf = [s]
                pm = re.match(r'&\s*(P\d+)', s)
                current_pid = pm.group(1) if pm else ""
            elif re.match(r'^[#@$>]', s):
                header_buf.append(s)
            # First non-header line: stop collecting for this tablet
            # (header might be followed by more tablets in same file)

        if header_buf and current_pid:
            meta = parse_atf_metadata(header_buf)
            index[current_pid] = meta
            by_stem[atf_path.stem] = meta

    print(f"[ATF metadata] {len(index)} tablets indexed by P-number")
    return index, by_stem


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — MATCH TXT FILES TO ATF METADATA
# The TXT filename stem is  <original_stem>_sign_names
# The original stem may contain the P-number or the tablet name.
# ══════════════════════════════════════════════════════════════════════════════

def get_meta_for_txt(txt_path: Path,
                     atf_index: dict[str, dict],
                     by_stem: dict[str, dict]) -> dict:
    """
    Try to find ATF metadata for a TXT file by:
      1. Extracting P-number from filename
      2. Matching original stem (without _sign_names suffix)
    """
    stem = txt_path.stem  # e.g. "P123456_sign_names"

    # Try P-number
    pm = re.search(r'(P\d{6})', stem)
    if pm and pm.group(1) in atf_index:
        return atf_index[pm.group(1)]

    # Try stem without _sign_names
    orig_stem = re.sub(r'_sign_names$', '', stem)
    if orig_stem in by_stem:
        return by_stem[orig_stem]

    # Return empty metadata
    return {
        "artifact_id": pm.group(1) if pm else "",
        "corpus_id": "", "genre_name": "",
        "provenance": "", "archaeological_context": "",
        "period_index": "", "period_dates": "", "languages": "",
    }


# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — MAIN
# ══════════════════════════════════════════════════════════════════════════════

def _prompt(msg: str, default: str = "") -> str:
    val = input(f"{msg} [{default}]: ").strip()
    return val if val else default


def main() -> None:
    print("=" * 64)
    print("  atf_to_grapheme.py  v1.0")
    print("  TXT (sign names) + ATF  →  unicode.csv + grapheme.csv")
    print("=" * 64 + "\n")

    # ── Paths ─────────────────────────────────────────────────────────────────
    if len(sys.argv) == 4:
        txt_folder  = Path(sys.argv[1])
        atf_source  = Path(sys.argv[2])
        unicode_csv = sys.argv[3]
    else:
        txt_folder  = Path(_prompt(
            "Folder with *_sign_names.txt files (output of transferTrLit_Sign.py)",
            "output_sign_names"))
        atf_source  = Path(_prompt(
            "Original ATF file or folder (for metadata)",
            "."))
        unicode_csv = _prompt(
            "Path to 6_unicodeTrLit_Grph_Phon.csv",
            "6_unicodeTrLit_Grph_Phon.csv")

    # Validate
    if not txt_folder.exists():
        sys.exit(f"[ERROR] TXT folder not found: {txt_folder}")
    if not atf_source.exists():
        sys.exit(f"[ERROR] ATF source not found: {atf_source}")
    if not Path(unicode_csv).exists():
        sys.exit(f"[ERROR] Unicode CSV not found: {unicode_csv}")

    # ── Load sign table ───────────────────────────────────────────────────────
    sci_to_row, phon_to_row = load_unicode_table(unicode_csv)

    # ── Write unicode.csv ─────────────────────────────────────────────────────
    out_unicode = txt_folder / "unicode.csv"
    write_unicode_csv(sci_to_row, str(out_unicode))

    # ── Load ATF metadata ─────────────────────────────────────────────────────
    atf_index, by_stem = load_all_atf_metadata(atf_source)

    # ── Process TXT files ─────────────────────────────────────────────────────
    txt_files = sorted(txt_folder.glob("*_sign_names.txt"))
    if not txt_files:
        sys.exit(f"[ERROR] No *_sign_names.txt files found in {txt_folder}")

    print(f"\n[files] Processing {len(txt_files)} file(s)...\n")

    all_records: list[dict] = []
    missing:     dict[str, int] = {}

    for txt_path in txt_files:
        meta = get_meta_for_txt(txt_path, atf_index, by_stem)
        pid  = meta.get("artifact_id", txt_path.stem)
        process_txt_file(txt_path, meta, sci_to_row, phon_to_row,
                         all_records, missing)
        print(f"  [OK] {txt_path.name:50} artifact={pid}")

    # ── Write grapheme.csv ────────────────────────────────────────────────────
    out_grapheme = txt_folder / "grapheme2.csv"
    with open(out_grapheme, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=GRAPHEME_FIELDS,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_records)

    # ── Statistics ────────────────────────────────────────────────────────────
    total     = len(all_records)
    n_uid     = sum(1 for r in all_records if r["unicode_id"])
    n_miss    = sum(missing.values())
    type_cnt: dict[str, int] = defaultdict(int)
    for r in all_records:
        type_cnt[r["sign_type"]] += 1

    print(f"\n{'─'*50}")
    print(f"[grapheme2.csv] {total} token records  →  {out_grapheme}")
    print(f"  Unicode resolved : {n_uid} / {total} "
          f"({n_uid/total*100:.1f}%)")
    print(f"  Unresolved       : {n_miss} tokens "
          f"({len(missing)} unique)")
    print(f"\n  sign_type distribution:")
    for t, c in sorted(type_cnt.items(), key=lambda x: -x[1]):
        print(f"    {t:12} {c:6}  ({c/total*100:.1f}%)")

    # ── Write warnings ────────────────────────────────────────────────────────
    if missing:
        warn_path = txt_folder / "warnings_grapheme.csv"
        with open(warn_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["sign_name", "count"])
            for tok, cnt in sorted(missing.items(), key=lambda x: -x[1]):
                writer.writerow([tok, cnt])
        print(f"\n[warnings] {warn_path}")

    print(f"\n[done]")
    print(f"  unicode.csv   →  {out_unicode}")
    print(f"  grapheme2.csv  →  {out_grapheme}")


if __name__ == "__main__":
    main()
