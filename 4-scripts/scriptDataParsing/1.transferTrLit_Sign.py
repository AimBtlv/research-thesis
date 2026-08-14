#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transferTrLit_Sign.py  (v1.0)
================================================================================
CODE №1  —  ANNOTATION LAYER  /  LEMMATIZATION
================================================================================

PURPOSE
-------
Converts CDLI ATF transliteration files:
    phonetic reading  →  scientific sign name

Following the logic of sign_name.py (Perl original 14 OCT 2014).

INPUT
-----
  - One or more ATF files (*.atf)  OR  a folder containing ATF files
  - Syllabaries (must be in same folder as this script OR set SYLLABARY_DIR):
      syllabary_CM.txt
      syllabary_uruk2.txt
      additional_signs.txt

OUTPUT
------
  Folder:  output_sign_names/
  For each input ATF file  →  one TXT file with scientific sign names,
  preserving ATF structure (header lines unchanged, transliteration replaced).

  Also writes:
      output_sign_names/warnings_missing.csv   — tokens not found in syllabary
      output_sign_names/DUMP_syllabary.csv     — full syllabary dump (debug)

USAGE
-----
  python transferTrLit_Sign.py                    # prompts for input
  python transferTrLit_Sign.py corpus.atf         # single file
  python transferTrLit_Sign.py ./atf_folder/      # whole folder

================================================================================
"""

import sys
import os
import re
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — SYLLABARY LOADING
# Three files: syllabary_CM.txt | syllabary_uruk2.txt | additional_signs.txt
# Replicates sign_name.py steps 1–4 exactly.
# ══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent

def _find_file(name: str) -> Path:
    """Look for a syllabary file next to this script."""
    p = SCRIPT_DIR / name
    if p.exists():
        return p
    # Also check uploads dir (for claude.ai context)
    up = Path("/mnt/user-data/uploads") / name
    if up.exists():
        return up
    return p  # will fail gracefully below


def load_syllabary() -> dict[str, str]:
    """
    Load all three syllabary files into one dict {reading: scientific_name}.
    Priority: CM > additional_signs > uruk2  (first-write wins).
    """
    syllabary: dict[str, str] = {}

    # ── 1a. syllabary_CM.txt  (tab-separated: reading \\t scientific_name) ──
    cm_path = _find_file("syllabary_CM.txt")
    if not cm_path.exists():
        print(f"[WARN] syllabary_CM.txt not found at {cm_path}")
    else:
        with open(cm_path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\r\n").replace("?", "")
                parts = line.split("\t")
                if len(parts) >= 2:
                    r, n = parts[0].strip(), parts[1].strip()
                    if r and r not in syllabary:
                        syllabary[r] = n
        print(f"[syllabary] CM loaded      : {len(syllabary):6d} entries")

    prev = len(syllabary)

    # ── 1b. additional_signs.txt  (tab-separated, same format) ──────────────
    as_path = _find_file("additional_signs.txt")
    if not as_path.exists():
        print(f"[WARN] additional_signs.txt not found at {as_path}")
    else:
        with open(as_path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\r\n").replace("?", "")
                parts = line.split("\t")
                if len(parts) >= 2:
                    r, n = parts[0].strip(), parts[1].strip()
                    if r and r not in syllabary:
                        syllabary[r] = n
        print(f"[syllabary] additional     : +{len(syllabary)-prev:5d} entries")

    prev = len(syllabary)

    # ── 1c. syllabary_uruk2.txt  (one sign per line, no tab) ────────────────
    #    sign_name.py normalisation:
    #      remove |  →  remove .  replace with +
    #      remove ( )
    uruk_path = _find_file("syllabary_uruk2.txt")
    if not uruk_path.exists():
        print(f"[WARN] syllabary_uruk2.txt not found at {uruk_path}")
    else:
        with open(uruk_path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\r\n").replace("?", "")
                line = line.replace("|", "")
                line = line.replace(".", "+")
                line = line.replace("(", "").replace(")", "")
                parts = line.split()
                if not parts or parts[0].startswith("#"):
                    continue
                reading = parts[0]
                if reading in syllabary:
                    continue
                if len(parts) >= 2:
                    syllabary[reading] = parts[1]
                else:
                    syllabary[reading] = reading   # self-referential
        print(f"[syllabary] uruk2          : +{len(syllabary)-prev:5d} entries")

    # ── 1d. Expand x / × / + variants (sign_name.py step 4) ─────────────────
    #    GI+GI  ↔  GIxGI  ↔  GI×GI
    prev = len(syllabary)
    extra: dict[str, str] = {}
    for reading, name in list(syllabary.items()):
        if not reading:
            continue
        if re.search(r'(\w)\+(\w)', reading):
            xr = re.sub(r'(\w)\+(\w)', r'\1x\2', reading)
            if xr not in syllabary:
                extra[xr] = name
        if re.search(r'(\w)x(\w)', reading):
            xr = re.sub(r'(\w)x(\w)', r'\1×\2', reading)
            if xr not in syllabary:
                extra[xr] = name
    syllabary.update(extra)
    # Remove empty keys
    syllabary = {k: v for k, v in syllabary.items() if k}

    print(f"[syllabary] x/× expansion  : +{len(syllabary)-prev:5d} entries")
    print(f"[syllabary] TOTAL          : {len(syllabary):6d} entries\n")
    return syllabary


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — DUMP SYLLABARY  (debug / transparency)
# ══════════════════════════════════════════════════════════════════════════════

def dump_syllabary(syllabary: dict[str, str], out_dir: Path) -> None:
    dump_path = out_dir / "DUMP_syllabary.csv"
    with open(dump_path, "w", encoding="utf-8") as f:
        f.write("phonetic_reading\tscientific_name\n")
        for k in sorted(syllabary.keys()):
            f.write(f"{k}\t{syllabary[k]}\n")
    print(f"[dump] Syllabary written → {dump_path}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — TOKEN NORMALISATION
# Mirrors sign_name.py steps 9–19 (the per-token cleanup loop).
# ══════════════════════════════════════════════════════════════════════════════

# ASCII diacritics → Unicode  (sign_name.py step 9б)
ASCII_DIA = [
    ("s'", "ṣ"), ("s,", "ṣ"), ("S'", "Ṣ"), ("S,", "Ṣ"),
    ('s"', "š"), ("sz", "š"), ('S"', "Š"), ("SZ", "Š"),
    ("t'", "ṭ"), ("t,", "ṭ"), ("T'", "Ṭ"), ("T,", "Ṭ"),
]

# Regex used to strip structural ATF punctuation from inside a token
_STRIP_RE = re.compile(
    r'(\s+|\-\=|\=\-|\-\:|\:\-|=\+|\+=|\w\??\_|\-|\:|\{|\})'
)


def _apply_diacritics(text: str) -> str:
    for asc, uni in ASCII_DIA:
        text = text.replace(asc, uni)
    return text


def normalise_token(tok: str) -> str:
    """
    Apply all sign_name.py normalisation steps to a single token string.
    Returns the canonical lookup key for the syllabary.
    """
    if not tok:
        return ""

    # step 11 — @-modifier substitutions
    tok = (tok.replace("@x",  "×")
              .replace("@+",  "+")
              .replace("@^",  "")
              .replace("@'",  "")
              .replace("@.",  "")
              .replace("@>",  "")
              .replace("@:",  "")
              .replace("@<",  "")
              .replace("@\\", "@t")
              .replace("@;",  "@g")
              .replace("@/",  "@g")
              .replace("@|",  "&")
              .replace("@#",  "@"))
    tok = tok.replace("g̃", "g").replace("ḫ", "h")

    # step 12 — Uruk numerals: 1(N34) → N34
    tok = re.sub(r'\d+\((N\d+.+?)\)', r'\1', tok)
    tok = re.sub(r'\d+\((N\d+)\)',    r'\1', tok)

    # step 13 — strip noise characters
    tok = re.sub(r'[\"*?!\[\]<>⌜⌝#]', '', tok)
    tok = re.sub(_STRIP_RE, '', tok)

    # step 14 — KAxA → KA×A
    tok = re.sub(
        r'([a-zA-ZĝĜţŢṭṬṣṢšŠ?!0-9|~()+@]+)x'
        r'([a-zA-ZĝĜţŢṭṬṣṢšŠ?!0-9|~()+@]+)',
        r'\1×\2', tok
    )

    # step 17 — sign(content) → content
    m = re.match(r'.+?\((.+?)\)$', tok)
    if m:
        tok = m.group(1)

    # step 18 — LU0 → LUx
    tok = re.sub(r'([a-zA-ZĝĜţŢšŠṭṬṣṢ&.@×?!]+)(0)$', r'\1x', tok)

    # step 19 — clean residual brackets / pipes
    tok = re.sub(r'\)~?[a-z][0-9]?',    '',    tok)
    tok = re.sub(r'\|~?[a-z][0-9]?',    '',    tok)
    tok = re.sub(r'^\((.+[^\)])$',       r'\1', tok)
    tok = re.sub(r'^([^(]+)\)~?[a-z]$', r'\1', tok)
    tok = re.sub(r'^([^(]+)\)$',         r'\1', tok)
    tok = re.sub(r'^\|(.+[^|])$',        r'\1', tok)
    tok = re.sub(r'^([^|]+)\|~?[a-z]$', r'\1', tok)
    tok = re.sub(r'^([^|]+)\|$',         r'\1', tok)

    return tok.strip()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — LINE PREPROCESSOR
# Mirrors sign_name.py steps 9а–9з (line-level cleanup before splitting).
# ══════════════════════════════════════════════════════════════════════════════

def preprocess_line(line: str) -> str:
    """Apply line-level ATF cleanup before tokenisation."""
    line = line.replace(",", "").replace(";", "")
    line = re.sub(r'(\w)x(\w)', r'\1×\2', line)

    # step 9б — diacritics
    line = _apply_diacritics(line)

    # step 9в — special markup
    line = (line.replace("[^", "⌐")
                .replace("]^", "¬")
                .replace("-/", "-")
                .replace("/-", "-"))

    # step 9г — ellipsis
    line = line.replace("...", "…").replace("..", "…")

    # step 9д — numeric artefacts
    line = line.replace("-:", "-").replace(":-", "-")

    # step 9е — x(A.B) → x(A+B)
    line = re.sub(
        r'x\((.+?)\.(.+?)\)',
        lambda mo: 'x' + mo.group(1) + '+' + mo.group(2),
        line
    )

    # step 9з — ligature normalisation inside |…|
    line = re.sub(r'\|(.+?)\+(.+?)\|', r'|\1x\2|', line)

    return line


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — SPLIT LINE INTO SIGN TOKENS
# ATF morpheme separator = hyphen.  Word separator = space.
# Dot inside a word = two consecutive sign names (E2.DU → [E2, DU]).
# ══════════════════════════════════════════════════════════════════════════════

def split_into_tokens(transliteration: str) -> list[str]:
    """
    Split one ATF transliteration string (without line number) into
    a flat list of individual sign tokens.
    """
    tokens: list[str] = []
    # split on spaces first
    for word in transliteration.split():
        # step 9ж — hyphen inside bracketed region → dot
        if re.search(r'\w\(.+\)', word) and '~' not in word \
                and not re.search(r'\(N\d', word):
            parts_w = re.split(r'(\(.+?\))', word)
            word = "".join(
                p.replace("-", ".") if p.startswith("(") else p
                for p in parts_w
            )
        # expand dot-joined (E2.DU → [E2, DU]) — but not decimal dots
        if re.search(r'\.\D', word) and not re.match(r'^[lrvs]e?\??\.',word):
            tokens.extend(word.split("."))
        else:
            # split on hyphens (morpheme boundary = sign boundary)
            for part in word.split("-"):
                if part:
                    tokens.append(part)
    return tokens


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — SIGN NAME RESOLVER
# Looks up normalised token in syllabary and applies back-normalisation
# (Unicode → ASCII) to the output, matching sign_name.py steps 20–22.
# ══════════════════════════════════════════════════════════════════════════════

# Back-normalisation (step 21): Unicode diacritics → ASCII in output names
BACK_NORM = [
    ("ṣ", "s,"), ("Ṣ", "S,"),
    ("š", "sz"), ("Š", "SZ"),
    ("ṭ", "t,"), ("Ṭ", "T,"),
]


def _back_normalise(name: str) -> str:
    for uni, asc in BACK_NORM:
        name = name.replace(uni, asc)
    name = name.replace("xx", "[...]").replace("×", "x")
    return name


def resolve_token(token: str, syllabary: dict[str, str]) -> tuple[str, bool]:
    """
    Returns (scientific_name, found).
    scientific_name is back-normalised to ASCII for output consistency.
    """
    norm = normalise_token(token)
    if not norm:
        return ("", False)

    name = syllabary.get(norm, "")
    if name:
        return (_back_normalise(name), True)

    # Fallback: try UPPERCASE of the normalised token
    name = syllabary.get(norm.upper(), "")
    if name:
        return (_back_normalise(name), True)

    # Not found — return the original token as-is (passthrough)
    return (_back_normalise(norm), False)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — PROCESS ONE ATF FILE  →  one TXT output file
# Mirrors sign_name.py step 9 main loop.
# ══════════════════════════════════════════════════════════════════════════════

def process_atf_file(
    atf_path: Path,
    out_dir: Path,
    syllabary: dict[str, str],
    global_missing: dict[str, int],
) -> None:
    """
    Read one ATF file, convert phonetic transliteration to scientific names,
    write result to out_dir / <stem>_sign_names.txt
    """
    with open(atf_path, encoding="utf-8") as f:
        lines = f.readlines()

    out_lines: list[str] = []

    for raw in lines:
        line = raw.rstrip("\n")
        original = line   # kept for warning context

        # ── Header / structural lines: pass through unchanged ────────────────
        if re.match(r'^.?[&@$#>]', line) or not line.strip():
            out_lines.append(line)
            continue

        # ── Transliteration line ─────────────────────────────────────────────
        # Extract line number (first token before first space)
        m = re.match(r'^(\S+)\s+(.*)', line)
        if not m:
            out_lines.append(line)   # blank or unparseable
            continue

        line_num = m.group(1)
        transliteration = m.group(2)

        # Preprocess the transliteration body
        transliteration = preprocess_line(transliteration)

        # Split into individual sign tokens
        raw_tokens = split_into_tokens(transliteration)

        # ── Diri expansion (step 16): if the resolved name is A.B.C, expand ─
        resolved_names: list[str] = []
        for tok in raw_tokens:
            sci_name, found = resolve_token(tok, syllabary)
            if not found:
                # record as missing
                norm = normalise_token(tok)
                if norm:
                    global_missing[norm] = global_missing.get(norm, 0) + 1

            # If scientific name contains '.' it is a diri compound: expand
            if sci_name and re.search(r'\.\D', sci_name):
                resolved_names.extend(sci_name.split("."))
            elif sci_name:
                resolved_names.append(sci_name)

        out_lines.append(f"{line_num} " + " ".join(resolved_names))

    # ── Write output TXT ─────────────────────────────────────────────────────
    out_name = atf_path.stem + "_sign_names.txt"
    out_path = out_dir / out_name
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")

    print(f"  [OK] {atf_path.name:40} → {out_name}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — WARNINGS FILE
# ══════════════════════════════════════════════════════════════════════════════

def write_warnings(missing: dict[str, int], out_dir: Path) -> None:
    warn_path = out_dir / "warnings_missing.csv"
    with open(warn_path, "w", encoding="utf-8") as f:
        f.write("token\tcount\n")
        for tok, cnt in sorted(missing.items(), key=lambda x: -x[1]):
            f.write(f"{tok}\t{cnt}\n")
    total = sum(missing.values())
    print(f"\n[warnings] {len(missing)} unique unresolved tokens "
          f"({total} total occurrences) → {warn_path}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 9 — MAIN / CLI
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 60)
    print("  transferTrLit_Sign.py  v1.0")
    print("  Phonetic ATF  →  Scientific Sign Names")
    print("=" * 60 + "\n")

    # ── Load syllabaries ─────────────────────────────────────────────────────
    syllabary = load_syllabary()

    # ── Dump for debugging ───────────────────────────────────────────────────
    out_dir = Path("output_sign_names")
    out_dir.mkdir(exist_ok=True)
    dump_syllabary(syllabary, out_dir)

    # ── Collect ATF files ────────────────────────────────────────────────────
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        print("Input: path to ATF file or folder containing ATF files.")
        raw = input(">>> ").strip()
        target = Path(raw)

    if not target.exists():
        sys.exit(f"[ERROR] Not found: {target}")

    if target.is_dir():
        atf_files = sorted(target.glob("*.atf"))
        if not atf_files:
            # Try .txt as well (some CDLI exports use .txt)
            atf_files = sorted(target.glob("*.txt"))
    else:
        atf_files = [target]

    if not atf_files:
        sys.exit(f"[ERROR] No ATF files found in {target}")

    print(f"\n[files] Processing {len(atf_files)} file(s) → {out_dir}/\n")

    # ── Process each file ────────────────────────────────────────────────────
    global_missing: dict[str, int] = {}

    for atf_path in atf_files:
        process_atf_file(atf_path, out_dir, syllabary, global_missing)

    # ── Write warnings ───────────────────────────────────────────────────────
    if global_missing:
        write_warnings(global_missing, out_dir)
    else:
        print("\n[warnings] No unresolved tokens.")

    print(f"\n[done] Output folder: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
