#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
from pathlib import Path
from collections import defaultdict


# CONFIGURATION


INPUT_ALLOGRAPH = "/Users/aima/Desktop/Practice/GitHub/research-thesis/4-scripts/scriptDataParsing/8_allograph_all_v11.csv"
INPUT_TOKENS = "/Users/aima/Desktop/Practice/GitHub/research-thesis/2-dataset/InputData/2.parsingFromAtf_Txt/atf_tokens.csv"
OUTPUT_GRAPHEME = "/Users/aima/Desktop/Practice/GitHub/research-thesis/2-dataset/InputData/3.parsingFromTxt_Csv/grapheme.csv"
OUTPUT_WARNINGS = "/Users/aima/Desktop/Practice/GitHub/research-thesis/2-dataset/InputData/3.parsingFromTxt_Csv/warnings_grapheme.csv"

GRAPHEME_FIELDS = [
    "unicode_id", "sign_grapheme", "sign_trlitScien", "sign_phonetic",
    "sign_translation", "sign_type", "is_compound", "component_position",
    "word_id", "confidence", "source",
    "artifact_id", "corpus_id", "genre_name", "provenance", "modern",
    "archaeological_context", "period_index", "period_dates", "languages",
    "is_school_text", "genre_uncertain", "period_uncertain", "provenience_uncertain",
]

# STAGE 1  LOAD allograph_all_v11.csv


def load_sign_lookup(path: str) -> tuple:
    """
    Returns (atomic_lookup, compound_components).
    atomic_lookup:       {sign_name: {unicode_id, sign_grapheme, unicodeTrLit}}
                          only rows with sign_structure in ('atomic',
                          'atomic_with_decompositions') or syllabary-only
                          simple signs  one canonical row per name.
    compound_components: {compound_form: [(position, unicode_id, sign_grapheme), ...]}
                          sorted by component_position.
    """
    atomic_lookup = {}
    compound_raw = defaultdict(list)

    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["sign_structure"] == "compound":
                pos = int(row["component_position"]) if row["component_position"] else 0
                compound_raw[row["compound_form"]].append(
                    (pos, row["unicode_id"], row["sign_grapheme"]))
            elif row["typePhonetic_Version"] == "Single Sign Reading":
                name = row["sign_name"]
                if name not in atomic_lookup:
                    atomic_lookup[name] = {
                        "unicode_id": row["unicode_id"],
                        "sign_grapheme": row["sign_grapheme"],
                        "unicodeTrLit": row["unicodeTrLit"],
                    }

    compound_components = {
        cf: sorted(comps, key=lambda c: c[0]) for cf, comps in compound_raw.items()
    }
    return atomic_lookup, compound_components



# STAGE 2 sign_type FROM raw_atf_token 


def determine_sign_type(raw_atf_token: str, token_kind: str) -> str:
    """LOGO/SYLL is a property of a single atomic token's actual case in
    the source text. Compounds are their own category, not assigned a
    LOGO/SYLL value at all (see module docstring, point 4)."""
    if token_kind == "compound":
        return "COMPOUND"
    if token_kind == "numeral":
        return "NUMERAL"
    if token_kind == "unresolved":
        return "UNKNOWN"
    first_alpha = next((c for c in raw_atf_token if c.isalpha()), None)
    if first_alpha is None:
        return "UNKNOWN"
    return "LOGO" if first_alpha.isupper() else "SYLL"


# STAGE 3 — ATF METADATA (&, #, @ header lines)  unchanged in logic


PERIOD_TABLE = [
    ("uruk", "Uruk", 3400), ("jemdet nasr", "Jemdet Nasr", 3000),
    ("early dynastic i", "Early Dynastic I", 2900),
    ("early dynastic ii", "Early Dynastic II", 2750),
    ("early dynastic iii", "Early Dynastic IIIa", 2600),
    ("early dynastic", "Early Dynastic", 2700),
    ("old akkadian", "Old Akkadian", 2340), ("lagash ii", "Lagash II", 2150),
    ("ur iii", "Ur III", 2100), ("old babylonian", "Old Babylonian", 1900),
    ("old assyrian", "Old Assyrian", 1900),
    ("middle babylonian", "Middle Babylonian", 1400),
    ("middle assyrian", "Middle Assyrian", 1300),
    ("neo-assyrian", "Neo-Assyrian", 700), ("neo-babylonian", "Neo-Babylonian", 600),
    ("late babylonian", "Late Babylonian", 400), ("achaemenid", "Achaemenid", 500),
    ("hellenistic", "Hellenistic", 300),
]

CORPUS_TABLE = [
    ("lexical", "SCHOOL", "Lexical / school corpus"),
    ("school", "SCHOOL", "Lexical / school corpus"),
    ("eduba", "SCHOOL", "Lexical / school corpus"),
    ("administrative", "ADMIN", "Administrative corpus"),
    ("admin", "ADMIN", "Administrative corpus"),
    ("legal", "LEGAL", "Legal corpus"), ("literary", "LIT", "Literary corpus"),
    ("hymn", "LIT", "Literary corpus"), ("myth", "LIT", "Literary corpus"),
    ("ritual", "LIT", "Literary corpus"), ("letter", "LETTER", "Letters"),
    ("trade", "TRADE", "Trade / commercial corpus"),
    ("royal", "ROYAL", "Royal inscriptions"),
    ("mathematical", "MATH", "Mathematical corpus"),
    ("astronomical", "ASTRO", "Astronomical corpus"),
]

PROVENANCE_CONTEXT = {
    "nippur": "Nippur", "ur": "Ur", "uruk": "Uruk", "lagash": "Lagash",
    "girsu": "Lagash", "umma": "Umma", "eridu": "Eridu", "sippar": "Sippar",
    "babylon": "Babylon", "assur": "Assur", "nineveh": "Nineveh",
    "larsa": "Larsa", "isin": "Isin", "eshnunna": "Eshnunna", "adab": "Adab",
    "kish": "Kish", "shuruppak": "Shuruppak", "drehem": "Ur",
    "garšana": "Garšana", "ebla": "Ebla", "mari": "Mari",
}


GENRE_TO_CORPUS = [
    ("lexical", "SCHOOL"), ("school", "SCHOOL"), ("administrative", "ADMIN"),
    ("legal", "LEGAL"), ("literary", "LIT"), ("letter", "LETTER"),
    ("royal", "ROYAL"), ("mathematical", "MATH"), ("astronomical", "ASTRO"),
    ("omen", "OMEN"), ("ritual", "LIT"), ("lexical", "SCHOOL"),
]


PERIOD_SPLIT_RE = re.compile(r'^(.*?)\s*\(([^()]*)\)\s*$')
PROVENANCE_MODERN_RE = re.compile(r'^(.*?)\s*\(mod\.\s*([^()]*)\)\s*$', re.IGNORECASE)


def split_period(period_str: str) -> tuple:
    """'ED IIIa (ca. 2600-2500 BC)' to ('ED IIIa', 'ca. 2600-2500 BC').
    Returns (period_index, period_dates), if there is no parenthetical
    part at all, period_dates is left empty rather than guessed."""
    m = PERIOD_SPLIT_RE.match(period_str)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return period_str.strip(), ""


def split_provenance(provenance_str: str) -> tuple:
    """'Shuruppak (mod. Fara)' - ('Shuruppak', 'Fara'). Only the specific
    'mod. X' convention is split off; a parenthetical that isn't a modern-
    name gloss (i.e. an uncertainty marker) is left attached to
    provenance untouched, rather than guessed apart."""
    m = PROVENANCE_MODERN_RE.match(provenance_str)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return provenance_str.strip(), ""


def load_artifact_metadata_csv(path) -> dict:
    """Reads one CDLI artifacts_{artifact_id}.csv export directly  the
    authoritative source when available, in preference to guessing period/
    genre/provenance by keyword-matching noisy ATF body text. Preserves
    CDLI's own uncertainty flags rather than discarding them: a genre or
    period marked uncertain in the source should stay visibly uncertain
    here, not be presented with the same confidence as a certain one."""
    with open(path, encoding="utf-8-sig") as f:
        row = next(csv.DictReader(f))

    p_number = f"P{int(row['artifact_id']):06d}"
    genres = row.get("genres", "").strip()
    corpus_id = ""
    for kw, cid in GENRE_TO_CORPUS:
        if kw in genres.lower():
            corpus_id = cid
            break

    provenience_raw = row.get("provenience", "").strip()
    provenience, modern = split_provenance(provenience_raw)
    arch_context = ""
    for city, context in PROVENANCE_CONTEXT.items():
        if city in provenience.lower():
            arch_context = context
            break

    period_index, period_dates = split_period(row.get("period", "").strip())

    return {
        "artifact_id": p_number,
        "corpus_id": corpus_id,
        "genre_name": genres,
        "provenance": provenience,
        "modern": modern,
        "archaeological_context": arch_context,
        "period_index": period_index,
        "period_dates": period_dates,
        "languages": row.get("languages", "").strip(),
        "is_school_text": row.get("is_school_text", "0").strip(),
        "genre_uncertain": row.get("genres_uncertain", "0").strip(),
        "period_uncertain": row.get("is_period_uncertain", "0").strip(),
        "provenience_uncertain": row.get("is_provenience_uncertain", "0").strip(),
    }


def load_all_artifact_metadata(metadata_folder: str) -> dict:
    """Returns {p_number: metadata_dict}, one entry per artifacts_*.csv
    file found. This is the primary metadata source, load_all_atf_metadata
    (keyword-matching against ATF header text) is used only as a fallback
    for any P-number with no matching artifacts_*.csv."""
    index = {}
    
    for path in Path(metadata_folder).glob("**/artifacts_*.csv"):
        try:
            meta = load_artifact_metadata_csv(path)
            index[meta["artifact_id"]] = meta
        except (StopIteration, KeyError, ValueError):
            continue  # malformed or empty metadata file — fall back per-tablet
    return index


def parse_atf_metadata(header_text: str, p_number: str) -> dict:
    meta = {"artifact_id": p_number, "corpus_id": "", "genre_name": "",
            "provenance": "", "modern": "", "archaeological_context": "",
            "period_index": "", "period_dates": "", "languages": "",
            "is_school_text": "", "genre_uncertain": "",
            "period_uncertain": "", "provenience_uncertain": ""}
    full_text = header_text.lower()

    lang_m = re.search(r'#atf:\s*lang\s+(\S+)', header_text)
    if lang_m:
        lang_map = {"sux": "Sumerian", "akk": "Akkadian", "qpn": "Proper nouns",
                    "sux-x-emesal": "Emesal", "ebl": "Eblaite", "hit": "Hittite",
                    "elx": "Elamite"}
        meta["languages"] = lang_map.get(lang_m.group(1).lower(), lang_m.group(1).upper())

    for kw, label, date in PERIOD_TABLE:
        if kw in full_text:
            meta["period_index"], meta["period_dates"] = label, str(date)
            break
    for kw, cid, gname in CORPUS_TABLE:
        if kw in full_text:
            meta["corpus_id"], meta["genre_name"] = cid, gname
            break
    for city, context in PROVENANCE_CONTEXT.items():
        if city in full_text:
            meta["provenance"], meta["archaeological_context"] = city.capitalize(), context
            break
    return meta


def load_all_atf_metadata(atf_folder: str) -> dict:
    """Returns {p_number: metadata_dict}."""
    index = {}
    for atf_path in Path(atf_folder).glob("**/*.atf"):
        text = atf_path.read_text(encoding="utf-8", errors="replace")
        pm = re.search(r'&\s*(P\d+)', text)
        p_number = pm.group(1) if pm else atf_path.stem
        header_lines = [l for l in text.splitlines() if re.match(r'^[&#@$]', l.strip())]
        index[p_number] = parse_atf_metadata("\n".join(header_lines), p_number)
    return index

# STAGE 4 EXPAND TOKENS INTO grapheme.csv ROWS


def process_tokens(tokens_path: str, atomic_lookup: dict, compound_components: dict,
                    artifact_meta_index: dict, atf_meta_index: dict) -> tuple:
    records = []
    missing = {}

    with open(tokens_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            meta = artifact_meta_index.get(row["p_number"])
            if meta is None:
                meta = atf_meta_index.get(row["p_number"], {
                    "artifact_id": row["p_number"], "corpus_id": "", "genre_name": "",
                    "provenance": "", "modern": "", "archaeological_context": "",
                    "period_index": "", "period_dates": "", "languages": "",
                    "is_school_text": "", "genre_uncertain": "",
                    "period_uncertain": "", "provenience_uncertain": "",
                })
            sign_type = determine_sign_type(row["raw_atf_token"], row["token_kind"])
            base = {
                "sign_translation": "",
                "sign_type": sign_type,
                "word_id": row["word_id"],
                "confidence": row["confidence"],
                "source": row["source"],
                **{k: meta.get(k, "") for k in
                   ("artifact_id", "corpus_id", "genre_name", "provenance", "modern",
                    "archaeological_context", "period_index", "period_dates", "languages",
                    "is_school_text", "genre_uncertain", "period_uncertain", "provenience_uncertain")},
            }

            if row["token_kind"] == "compound":
                components = compound_components.get(row["resolved_name"], [])
                if not components:
                    missing.setdefault(row["resolved_name"], []).append(
                        (row["word_id"], meta.get("provenance",""), meta.get("period_index","")))
                    records.append({**base, "unicode_id": "", "sign_grapheme": "",
                                    "sign_trlitScien": row["resolved_name"],
                                    "sign_phonetic": row["raw_atf_token"],
                                    "is_compound": "COMPOUND", "component_position": ""})
                    continue
                for position, unicode_id, sign_grapheme in components:
                    records.append({**base, "unicode_id": unicode_id,
                                    "sign_grapheme": sign_grapheme,
                                    "sign_trlitScien": row["resolved_name"],
                                    "sign_phonetic": row["raw_atf_token"],
                                    "is_compound": "COMPOUND",
                                    "component_position": position})

            elif row["token_kind"] == "atomic":
                info = atomic_lookup.get(row["resolved_name"])
                if info is None:
                    missing.setdefault(row["resolved_name"], []).append(
                        (row["word_id"], meta.get("provenance",""), meta.get("period_index","")))
                    info = {"unicode_id": "", "sign_grapheme": "", "unicodeTrLit": ""}
                records.append({**base, "unicode_id": info["unicode_id"],
                                "sign_grapheme": info["sign_grapheme"],
                                "sign_trlitScien": row["resolved_name"],
                                "sign_phonetic": row["raw_atf_token"],
                                "is_compound": "SIMPLE", "component_position": ""})

            elif row["token_kind"] == "broken":
                continue 
            elif row["token_kind"] == "numeral":
                continue 

            else:  # unresolved
                missing.setdefault(row["raw_atf_token"], []).append(
                    (row["word_id"], meta.get("provenance",""), meta.get("period_index","")))
                continue 

    return records, missing


# MAIN


def main(atf_folder: str = "/Users/aima/Desktop/Practice/GitHub/research-thesis/2-dataset/InputData/1.downloadCorpusATF/EDIII-OBP_School/atf",
         metadata_folder: str = "/Users/aima/Desktop/Practice/GitHub/research-thesis/2-dataset/InputData/1.downloadCorpusATF/EDIII-OBP_School/metadata"):
    print(f"[INFO] Loading {INPUT_ALLOGRAPH}")
    atomic_lookup, compound_components = load_sign_lookup(INPUT_ALLOGRAPH)
    print(f"  atomic signs indexed: {len(atomic_lookup)}")
    print(f"  compound forms indexed: {len(compound_components)}")

    print(f"[INFO] Loading artifact metadata from {metadata_folder}")
    artifact_meta_index = load_all_artifact_metadata(metadata_folder)
    print(f"  {len(artifact_meta_index)} tablets with CDLI artifact metadata")

    print(f"[INFO] Loading ATF header metadata from {atf_folder} (fallback only)")
    atf_meta_index = load_all_atf_metadata(atf_folder)
    fallback_used = set(atf_meta_index) - set(artifact_meta_index)
    print(f"  {len(fallback_used)} tablet(s) will use ATF-header fallback: {sorted(fallback_used) or 'none'}")

    print(f"[INFO] Processing {INPUT_TOKENS}")
    records, missing = process_tokens(INPUT_TOKENS, atomic_lookup, compound_components,
                                       artifact_meta_index, atf_meta_index)

    with open(OUTPUT_GRAPHEME, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=GRAPHEME_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)
    print(f"\n[RESULT] {len(records)} sign-occurrence rows -> {OUTPUT_GRAPHEME}")

    n_uid = sum(1 for r in records if r["unicode_id"])
    print(f"  Unicode resolved: {n_uid} / {len(records)} ({100*n_uid/len(records):.1f}%)")

    type_c = defaultdict(int)
    for r in records:
        type_c[r["sign_type"]] += 1
    print(f"\n  sign_type distribution:")
    for t, c in sorted(type_c.items(), key=lambda x: -x[1]):
        print(f"    {t:10} {c:6}  ({100*c/len(records):.1f}%)")

    if missing:
        with open(OUTPUT_WARNINGS, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["word_id", "unresolved_name", "sign_type", "provenance", "period_index", "count"])
           
            grouped = defaultdict(list)
            for name, occurrences in missing.items():
                for word_id, provenance, period_index in occurrences:
                    grouped[(name, provenance, period_index)].append(word_id)
            rows = sorted(grouped.items(), key=lambda kv: -len(kv[1]))
            for (name, provenance, period_index), word_ids in rows:
                w.writerow([word_ids[0], name, "UNKNOWN", provenance, period_index, len(word_ids)])
        print(f"\n[WARNINGS] {len(missing)} unique unresolved names, "
              f"{sum(len(v) for v in missing.values())} total occurrences -> {OUTPUT_WARNINGS}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        main()