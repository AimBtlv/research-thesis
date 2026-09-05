#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import re
import unicodedata
from pathlib import Path
from collections import defaultdict

# CONFIGURATION


INPUT_ALLOGRAPH = "/Users/aima/Desktop/Practice/GitHub/research-thesis/4-scripts/scriptDataParsing/8_allograph_all_v11.csv"
INPUT_COMPOUND_TABLE = "/Users/aima/Desktop/Practice/GitHub/research-thesis/4-scripts/scriptDataParsing/compound_form_reading_table.csv"

OUTPUT_TOKENS_CSV = "/Users/aima/Desktop/Practice/GitHub/research-thesis/2-dataset/InputData/2.parsingFromAtf_Txt/atf_tokens.csv"
OUTPUT_WARNINGS_CSV = "/Users/aima/Desktop/Practice/GitHub/research-thesis/2-dataset/InputData/2.parsingFromAtf_Txt/warnings.csv"
OUTPUT_TXT_DIR = "/Users/aima/Desktop/Practice/GitHub/research-thesis/2-dataset/InputData/2.parsingFromAtf_Txt"

SUB_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

TOKENS_FIELDNAMES = [
    "p_number", "line_num", "word_id", "raw_atf_token",
    "resolved_name", "token_kind", "confidence", "source", "determinative",
]

# NORMALISATION


def normalize_name(s: str) -> str:
    return s.strip('|').translate(SUB_MAP).lower()


def x_operator_variants(name: str) -> set:
    """For the narrow, confirmed case where a compound's own attested
    reading IS its own structural name (no deeper phonetic value  see
    project notes), the sign-name operator × may appear in the source ATF
    text as Unicode × or ASCII x. Returns the set of equivalent forms.
    Deliberately NOT applied to ordinary phonetic readings, which never
    contain a structural operator character."""
    variants = {name}
    if '×' in name:
        variants.add(name.replace('×', 'x'))
    if 'x' in name:
        variants.add(name.replace('x', '×'))
    return variants


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — LOAD THE THREE DICTIONARIES
# ─────────────────────────────────────────────────────────────────────────────

def load_simple_dict(path: str) -> dict:
    """{normalized_reading: sign_name}, atomic signs only (typePhonetic_Version
    == 'Single Sign Reading'). This already includes the Diri/OGSL fallback
    readings baked into allograph_all_v11.csv —no separate lookup needed."""
    d = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["typePhonetic_Version"] != "Single Sign Reading":
                continue
            if not row["phonetic_version"].strip():
                continue
            for reading in row["phonetic_version"].split("|"):
                reading = reading.strip()
                if reading:
                    d.setdefault(normalize_name(reading), row["sign_name"])
    return d


def load_compound_dicts(path: str) -> tuple:
    """Returns (attested_dict, inferred_dict, source_by_form).
    attested_dict:  {normalized_reading: compound_form}
    inferred_dict:  {normalized_reading: compound_form}  (guesses only)
    source_by_form: {compound_form: reading_source}
    Also expands the narrow self-citing-name subset with × / x variants."""
    attested, inferred, source_by_form = {}, {}, {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cf = row["compound_form"]
            cf_norm = normalize_name(cf)

            if row["reading_status"] == "ATTESTED_DIRECT" and row["PhoneticVersion_Compound"]:
                source_by_form[cf] = row["reading_source"]
                for reading in row["PhoneticVersion_Compound"].split("|"):
                    reading = reading.strip()
                    if not reading:
                        continue
                    r_norm = normalize_name(reading)
                    attested.setdefault(r_norm, cf)
                    # narrow self-citing case: reading IS the compound's own name
                    if r_norm == cf_norm:
                        for variant in x_operator_variants(r_norm):
                            attested.setdefault(variant, cf)

            if row["component_reading_inferred"]:
                r_norm = normalize_name(row["component_reading_inferred"])
                inferred.setdefault(r_norm, cf)

    return attested, inferred, source_by_form



# STAGE 2 LINE PREPROCESSING 




ASCII_DIACRITIC_TABLE = [
    # order impotant: longer/quote-marked forms before the bare digraph
    (r"s'", "ṣ"), (r"S'", "Ṣ"), (r's,', "ṣ"), (r'S,', "Ṣ"),
    (r's"', "š"), (r'S"', "Š"),
    (r"t'", "ṭ"), (r"T'", "Ṭ"), (r't,', "ṭ"), (r'T,', "Ṭ"),
    (r"sz", "š"), (r"SZ", "Š"),
]

AT_MODIFIER_TABLE = [
    ("@x", "×"), ("@+", "+"), ("@\\", "@t"), ("@;", "@g"), ("@/", "@g"),
    ("@|", "&"), ("@#", "@"),
    ("@^", ""), ("@'", ""), ("@.", ""), ("@>", ""), ("@:", ""), ("@<", ""),
]

INLINE_DOLLAR_COMMENT_RE = re.compile(r'\(\$.*?\$\)')
UNWANTED_GLYPHS_RE = re.compile(r'["*?!\[\]]|<<|>>|<|>|⌜|⌝|#')


def preprocess_line(raw: str) -> str:
    """line cleanup only.
    Order important: ASCII diacritics, @-modifiers,the general unwanted-glyph strip,"""
    line = raw

    # inline ($ ... $) structural comments: remove
    line = INLINE_DOLLAR_COMMENT_RE.sub('', line)

    for old, new in ASCII_DIACRITIC_TABLE:
        line = line.replace(old, new)
    for old, new in AT_MODIFIER_TABLE:
        line = line.replace(old, new)

    # combining-diacritic folding
    line = line.replace('g̃', 'g').replace('ḫ', 'h')

    line = re.sub(r'\.\.\.+', '…', line)          # ellipsis
    line = UNWANTED_GLYPHS_RE.sub('', line)       # damage,collation,editorial flags
    line = re.sub(r'⸢|⸣', '', line)
    line = re.sub(r'\s+', ' ', line).strip()

    # x(A.B) -> x(A+B) : disambiguation-parenthesis dot -> plus, so the
    # tokenizer's dot-splitting doesn't misread the qualifier itself
    def _fix_paren(m):
        return m.group(0).replace('.', '+')
    line = re.sub(r'\([^()]*\.[^()]*\)', _fix_paren, line)

    return line


DETERMINATIVE_RE = re.compile(r'\{[^{}]*\}')


def strip_determinatives(word: str) -> tuple:
    """Determinatives ({d}, {ki}, {giš}...) are grammatical classifiers,
    not signs to be phonetically resolved themselves. Returns
    (word_without_determinatives, list_of_determinatives_found).

    A determinative sitting strictly between two other signs with no
    existing hyphen/dot on either side (e.g. 'gal{d}la') is replaced with
    a hyphen, not deleted outright deleting it would silently fuse the
    surrounding signs into a phantom sequence that never existed in the
    source ('gal' + 'la' to 'galla'). Where a separator already exists
    immediately adjacent, no extra hyphen is inserted."""
    found = DETERMINATIVE_RE.findall(word)

    def _replace(m):
        start, end = m.span()
        before_ok = start == 0 or word[start - 1] in "-. "
        after_ok = end == len(word) or word[end] in "-. "
        return "" if (before_ok or after_ok) else "-"

    cleaned = DETERMINATIVE_RE.sub(_replace, word)
    return cleaned, found

# STAGE 3 — TOKENIZATION

_LRVS_EXCEPTION = re.compile(r'^[lrvs]e?\??\.')


def split_word_into_parts(word: str) -> tuple:
    """Splits one space-delimited word on both '-' and '.' together,
    preserving the original separators so a matched span can be
    reconstructed byte-for-byte from the source text."""
    pieces = re.split(r'([-.])', word)
    parts = pieces[0::2]
    seps = pieces[1::2]
    return parts, seps


def join_span(parts: list, seps: list, i: int, j: int) -> str:
    """Reconstructs the original substring covering parts[i:j], including
    its original separators, exactly as it appeared in the source word."""
    out = []
    for k in range(i, j):
        out.append(parts[k])
        if k < j - 1:
            out.append(seps[k])
    return "".join(out)


def tokenize_word(word: str, attested_dict: dict, inferred_dict: dict) -> list:
    """Returns a list of dicts: {text, resolved, kind, confidence, source}.
    'kind' is 'compound' or 'atomic_candidate' (single-sign resolution
    happens later, in resolve_atomic). Two full passes over the whole word:
    pass 1 (attested) must exhaust every position before pass 2 (inferred)
    is tried anywhere, so a synthesised guess can never pre-empt a real
    attested match starting a little further along the same word."""
    lrvs_prefix = ""
    m = _LRVS_EXCEPTION.match(word)
    if m:
        lrvs_prefix = m.group(0)
        word = word[len(lrvs_prefix):]
        if not word:
            return [{"text": lrvs_prefix, "kind": "atomic_candidate"}]

    parts, seps = split_word_into_parts(word)
    n = len(parts)
    # state: None = unresolved, else the finished token dict
    slots = [None] * n
    i = 0
    while i < n:
        if slots[i] is not None:
            i += 1
            continue
        matched = False
        for j in range(n, i, -1):
            if j - i < 2:
                continue
            span_text = join_span(parts, seps, i, j)
            norm = normalize_name(span_text)
            if norm in attested_dict:
                cf = attested_dict[norm]
                slots[i] = {"text": span_text, "resolved": cf, "kind": "compound",
                            "confidence": "attested", "span": (i, j)}
                for k in range(i + 1, j):
                    slots[k] = "consumed"
                i = j
                matched = True
                break
        if not matched:
            i += 1

    # PASS 2 
    i = 0
    while i < n:
        if slots[i] is not None:
            i += 1
            continue
        matched = False
        for j in range(n, i, -1):
            if j - i < 2:
                continue
            if any(slots[k] is not None for k in range(i, j)):
                continue  # would overlap an attested match — never allowed
            span_text = join_span(parts, seps, i, j)
            norm = normalize_name(span_text)
            if norm in inferred_dict:
                cf = inferred_dict[norm]
                slots[i] = {"text": span_text, "resolved": cf, "kind": "compound",
                            "confidence": "inferred", "span": (i, j)}
                for k in range(i + 1, j):
                    slots[k] = "consumed"
                i = j
                matched = True
                break
        if not matched:
            i += 1

    # remaining unresolved single positions -> atomic candidates
    tokens = []
    i = 0
    while i < n:
        if slots[i] is None:
            tokens.append({"text": parts[i], "kind": "atomic_candidate"})
            i += 1
        elif slots[i] == "consumed":
            i += 1  # already emitted as part of a compound span
        else:
            tokens.append(slots[i])
            i += 1
    if lrvs_prefix:
        tokens.insert(0, {"text": lrvs_prefix, "kind": "atomic_candidate"})
    return tokens


def resolve_single_piece(text: str, simple_dict: dict, attested_dict: dict,
                          source_by_form: dict) -> tuple:
    """Returns (resolved_name, token_kind, source). Priority is simple_dict
    FIRST, attested_dict only as a fallback  confirmed necessary on real
    data: 'u3' has both an ordinary atomic reading (|IGI.DIB|) and an
    unrelated attested DIRI compound reading (|IGI.LU|) for the exact same
    string, and the common syllable use must win by default, not the rare
    compound one. This applies to every single, un-hyphenated piece,
    whether it is a whole bare word (n==1) or a leftover piece inside a
    longer hyphenated word that PASS 1/2 left untouched.

    The broken-text marker '…' is checked FIRST, before either
    dictionary, and short-circuits straight to token_kind='broken'. This
    matters specifically for a piece like the '…' in '…-ka-du' (from ATF
    '[...]-ka-du'): the whole-word check in process_atf_text only ever
    sees a lone bare '…', never one embedded inside a longer hyphenated
    word, so without this second check here too, that piece would reach
    simple_dict and hit the same coincidental 'xxx' collision.

    'source' is always one of OSL/DIRI/OGSL/SYLLABARY_CM (looked up the
    same way as any other compound match) or empty  never a separate,
    made-up label for this fallback path."""
    if is_broken_marker(text):
        return text, "broken", ""
    norm = normalize_name(text)
    if norm in simple_dict:
        return simple_dict[norm], "atomic", ""
    if norm in attested_dict:
        cf = attested_dict[norm]
        return cf, "compound", source_by_form.get(cf, "")
    return text, "unresolved", ""


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — PROCESS ONE ATF FILE
# ─────────────────────────────────────────────────────────────────────────────

NUMERAL_RE = re.compile(r"^n?\d*(/\d+)?\([\w@'~]+\)$", re.UNICODE)


def is_broken_marker(word: str) -> bool:
    """The collapsed ellipsis '…' marks text broken/missing on the tablet
    (from ATF '[...]'), not an unidentified sign. It must never reach the
    dictionaries at all: allograph_all_v11.csv happens to contain a real,
    unrelated catalogue entry (sign name 'xxx', a placeholder for an
    undeciphered sign) whose own attested reading is literally the string
    '…', a coincidental character collision confirmed on real data. Without
    this check, every broken-text marker silently resolved to that
    placeholder sign instead of being recognised as broken text."""
    return word == "…"


def is_numeral(word: str) -> bool:
    """ATF numerals ('1(disz)', '1/2(disz)', 'n(iku)', '5(gesz2@c)') are a
    counting-system notation, not phonetic sign content, and are never
    looked up in the sign dictionaries. 'n' alone is the ORACC convention
    for an indeterminate/illegible quantity."""
    return word == "n" or bool(NUMERAL_RE.match(word))


# ─────────────────────────────────────────────────────────────────────────────

def find_p_number(text: str) -> str:
    m = re.search(r'&\s*(P\d+)', text)
    return m.group(1) if m else "UNKNOWN"


def process_atf_text(text: str, simple_dict: dict, attested_dict: dict,
                      inferred_dict: dict, source_by_form: dict,
                      token_rows: list, txt_lines: list, missing: dict) -> None:
    p_number = find_p_number(text)
    word_counter = 0

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        if not line.strip() or re.match(r'^[&#@$>]', line.strip()):
            continue
        m = re.match(r'^(\S+)\s+(.*)', line)
        if not m:
            continue
        line_num, content = m.group(1), m.group(2).strip()
        if not content:
            continue

        cleaned = preprocess_line(content)
        txt_lines.append(f"{line_num}\t{cleaned}")

        for word in cleaned.split(" "):
            if not word:
                continue
            word, dets = strip_determinatives(word)
            if not word:
                continue  # a bare determinative with nothing else - nothing to tokenize
            word_counter += 1
            word_id = f"{p_number}_{word_counter}"
            det_str = ";".join(d.strip("{}") for d in dets)

            if is_broken_marker(word):
                token_rows.append({
                    "p_number": p_number, "line_num": line_num, "word_id": word_id,
                    "raw_atf_token": word, "resolved_name": word,
                    "token_kind": "broken", "confidence": "", "source": "",
                    "determinative": det_str,
                })
                continue

            if is_numeral(word):
                token_rows.append({
                    "p_number": p_number, "line_num": line_num, "word_id": word_id,
                    "raw_atf_token": word, "resolved_name": word,
                    "token_kind": "numeral", "confidence": "", "source": "",
                    "determinative": det_str,
                })
                continue

            for tok in tokenize_word(word, attested_dict, inferred_dict):
                if tok["kind"] == "compound":
                    token_rows.append({
                        "p_number": p_number, "line_num": line_num, "word_id": word_id,
                        "raw_atf_token": tok["text"], "resolved_name": tok["resolved"],
                        "token_kind": "compound", "confidence": tok["confidence"],
                        "source": source_by_form.get(tok["resolved"], "") if tok["confidence"] == "attested" else "",
                        "determinative": det_str,
                    })
                else:
                    resolved, kind, source = resolve_single_piece(tok["text"], simple_dict, attested_dict, source_by_form)
                    if kind == "unresolved":
                        missing[normalize_name(tok["text"])] = missing.get(normalize_name(tok["text"]), 0) + 1
                    token_rows.append({
                        "p_number": p_number, "line_num": line_num, "word_id": word_id,
                        "raw_atf_token": tok["text"], "resolved_name": resolved,
                        "token_kind": kind,
                        "confidence": "attested" if kind in ("atomic", "compound") else "",
                        "source": source,
                        "determinative": det_str,
                    })


# MAIN


def main(atf_folder: str):
    print(f"[INFO] Loading dictionaries")
    simple_dict = load_simple_dict(INPUT_ALLOGRAPH)
    attested_dict, inferred_dict, source_by_form = load_compound_dicts(INPUT_COMPOUND_TABLE)
    print(f"  simple_dict: {len(simple_dict)} readings")
    print(f"  attested_compound_dict: {len(attested_dict)} readings")
    print(f"  inferred_compound_dict: {len(inferred_dict)} readings")

    Path(OUTPUT_TXT_DIR).mkdir(exist_ok=True)
    
    atf_files = sorted(Path(atf_folder).glob("**/*.atf"))
    print(f"[INFO] {len(atf_files)} ATF file(s) found in {atf_folder}")

    all_token_rows = []
    missing = {}

    for atf_path in atf_files:
        text = atf_path.read_text(encoding="utf-8")
        p_number = find_p_number(text)
        txt_lines = []
        process_atf_text(text, simple_dict, attested_dict, inferred_dict,
                          source_by_form, all_token_rows, txt_lines, missing)
        txt_path = Path(OUTPUT_TXT_DIR) / f"{p_number}.txt"
        txt_path.write_text("\n".join(txt_lines) + "\n", encoding="utf-8")
        print(f"  [OK] {atf_path.name} -> {p_number}.txt")

    with open(OUTPUT_TOKENS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TOKENS_FIELDNAMES)
        w.writeheader()
        w.writerows(all_token_rows)
    print(f"\n[RESULT] {len(all_token_rows)} token rows -> {OUTPUT_TOKENS_CSV}")

    if missing:
        with open(OUTPUT_WARNINGS_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["normalized_token", "count"])
            for tok, cnt in sorted(missing.items(), key=lambda x: -x[1]):
                w.writerow([tok, cnt])
        print(f"[WARNINGS] {len(missing)} unique unresolved tokens -> {OUTPUT_WARNINGS_CSV}")

    n_compound = sum(1 for r in all_token_rows if r["token_kind"] == "compound")
    n_atomic = sum(1 for r in all_token_rows if r["token_kind"] == "atomic")
    n_unresolved = sum(1 for r in all_token_rows if r["token_kind"] == "unresolved")
    print(f"\n  compound: {n_compound}, atomic: {n_atomic}, unresolved: {n_unresolved}")


if __name__ == "__main__":
    import sys
    default_atf = "/Users/aima/Desktop/Practice/GitHub/research-thesis/2-dataset/InputData/1.downloadCorpusATF/EDIII-OBP_School/atf"
    main(sys.argv[1] if len(sys.argv) > 1 else default_atf)
