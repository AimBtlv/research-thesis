"""
build_restUnicodeSigns.py
─────────────────────────────────────────────────────────────────────────────
Task:
  Find all Unicode cuneiform signs that are present in 1_unicodeSigns.csv
  but MISSING from 4_matched_signs_full.csv, then enrich them with phonetic
  values from the OSL sign-list (osl.asl) and save as restUnicodeSigns.csv.

Input files:
  1_unicodeSigns.csv        — full Unicode sign inventory  (unicode_id, sign_grapheme, transliteration)
  4_matched_signs_full.csv  — already matched signs        (unicode_id, sign_grapheme, unicodeTrLit, syllabarySign, PhoneticsVersion)
  osl.asl                   — ORACC Sign List (ASL format) — authoritative phonetic values

Output:
  restUnicodeSigns.csv      — same schema as 4_matched_signs_full.csv,
                              containing only the 443 previously-missing signs

Schema of output:
  unicode_id       — e.g. U+12000
  sign_grapheme    — cuneiform character(s)
  unicodeTrLit     — transliteration from 1_unicodeSigns.csv
  syllabarySign    — scientific sign name from OSL (@sign line)
  PhoneticsVersion — pipe-separated phonetic values from OSL (@v lines)
─────────────────────────────────────────────────────────────────────────────
"""

import csv
import re
from pathlib import Path

# ── 0. Paths ──────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent          # directory of this script
INPUT_DIR  = Path("/mnt/project")           # read-only project files
OUTPUT_DIR = Path("/mnt/user-data/outputs") # output directory

UNICODE_CSV  = INPUT_DIR  / "1_unicodeSigns.csv"
MATCHED_CSV  = INPUT_DIR  / "4_matched_signs_full.csv"
OSL_FILE     = INPUT_DIR  / "osl.asl"
OUTPUT_CSV   = OUTPUT_DIR / "restUnicodeSigns.csv"

OUTPUT_FIELDNAMES = [
    "unicode_id",
    "sign_grapheme",
    "unicodeTrLit",
    "syllabarySign",
    "PhoneticsVersion",
]


# ── 1. Load 1_unicodeSigns.csv ────────────────────────────────────────────────

def load_unicode_signs(path: Path) -> dict[str, dict]:
    """
    Returns {unicode_id: {unicode_id, sign_grapheme, transliteration}}
    """
    signs = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            signs[row["unicode_id"]] = row
    print(f"[1] Loaded {len(signs):,} signs from {path.name}")
    return signs


# ── 2. Load 4_matched_signs_full.csv — collect already-matched IDs ────────────

def load_matched_ids(path: Path) -> set[str]:
    """
    Returns the set of unicode_id values already present in the matched file.
    """
    ids = set()
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ids.add(row["unicode_id"])
    print(f"[2] Loaded {len(ids):,} already-matched IDs from {path.name}")
    return ids


# ── 3. Parse osl.asl ──────────────────────────────────────────────────────────

def parse_osl(path: Path) -> dict[str, dict]:
    """
    Parse an ORACC Sign List (.asl) file and return a dict keyed by unicode_id.

    For every @sign block the parser collects:
      sign_name  — the token on the @sign line (e.g. "A", "|AN.KI|")
      uname      — the Unicode character name from @uname
      ucun       — the cuneiform glyph(s) from @ucun
      values     — list of phonetic readings from @v lines
                   (lines with @v- "deprecated" and %lang-qualified are skipped)

    Only blocks that carry a @list U+xxxx entry are included; the *first*
    such U+ code in each block is used as the key.
    """
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()

    # Split on the start of every @sign block
    blocks = re.split(r"\n(?=@sign\b)", raw)

    osl: dict[str, dict] = {}
    total_blocks = 0

    for block in blocks:
        lines = block.strip().splitlines()
        if not lines or not lines[0].startswith("@sign"):
            continue
        total_blocks += 1

        # --- sign name ---
        m = re.match(r"@sign\s+(.+)", lines[0])
        if not m:
            continue
        sign_name = m.group(1).strip()

        unicode_id  = None
        uname       = None
        ucun        = None
        values: list[str] = []

        for line in lines[1:]:
            line = line.strip()

            if line.startswith("@uname"):
                uname = re.sub(r"^@uname\s+", "", line).strip()

            elif re.match(r"@list\s+U\+", line):
                m2 = re.match(r"@list\s+(U\+[0-9A-Fa-f]+)", line)
                if m2 and unicode_id is None:          # keep the first U+ code
                    unicode_id = m2.group(1).upper()

            elif line.startswith("@ucun") and ucun is None:
                m3 = re.match(r"@ucun\s+(.+)", line)
                if m3:
                    ucun = m3.group(1).strip()

            elif re.match(r"@v\s+", line) and not line.startswith("@v-"):
                # Skip language-qualified values like "@v  %akk dannu"
                m4 = re.match(r"@v\s+(.+)", line)
                if m4:
                    v = m4.group(1).strip()
                    if not v.startswith("%"):
                        values.append(v)

            elif line.startswith("@end sign"):
                break

            # Nested @form blocks also contain @v lines; the current simple
            # loop collects them all — this is intentional so we capture
            # every attested reading for polyphony analysis.

        if unicode_id:
            osl[unicode_id] = {
                "sign_name": sign_name,
                "uname":     uname,
                "ucun":      ucun,
                "values":    values,
            }

    print(
        f"[3] Parsed {total_blocks:,} @sign blocks from {path.name}; "
        f"{len(osl):,} have a Unicode ID"
    )
    return osl


# ── 4. Build the output rows ───────────────────────────────────────────────────

def build_missing_rows(
    unicode_signs: dict[str, dict],
    matched_ids:   set[str],
    osl:           dict[str, dict],
) -> tuple[list[dict], list[str]]:
    """
    For each unicode_id that is absent from matched_ids:
      • look it up in osl to get syllabarySign + PhoneticsVersion
      • fall back to empty strings when no OSL entry exists

    Returns (rows, not_in_osl_ids).
    """
    missing_ids = sorted(set(unicode_signs.keys()) - matched_ids)
    print(f"[4] Missing IDs to process: {len(missing_ids):,}")

    rows: list[dict]   = []
    not_in_osl: list[str] = []

    for uid in missing_ids:
        u = unicode_signs[uid]

        if uid in osl:
            o = osl[uid]
            syllabary  = o["sign_name"]
            phonetics  = " | ".join(o["values"]) if o["values"] else ""
        else:
            syllabary  = ""
            phonetics  = ""
            not_in_osl.append(uid)

        rows.append({
            "unicode_id":      uid,
            "sign_grapheme":   u["sign_grapheme"],
            "unicodeTrLit":    u["transliteration"],
            "syllabarySign":   syllabary,
            "PhoneticsVersion": phonetics,
        })

    return rows, not_in_osl


# ── 5. Write output CSV ────────────────────────────────────────────────────────

def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[5] Written {len(rows):,} rows → {path}")


# ── 6. Summary report ─────────────────────────────────────────────────────────

def print_summary(rows: list[dict], not_in_osl: list[str]) -> None:
    with_phonetics = sum(1 for r in rows if r["PhoneticsVersion"])
    with_syllabary = sum(1 for r in rows if r["syllabarySign"])

    print("\n── Summary ──────────────────────────────────────────────────")
    print(f"  Total rows written  : {len(rows):>6,}")
    print(f"  With syllabarySign  : {with_syllabary:>6,}  ({with_syllabary/len(rows)*100:.1f} %)")
    print(f"  With PhoneticsVersion:{with_phonetics:>5,}  ({with_phonetics/len(rows)*100:.1f} %)")
    print(f"  Not found in OSL    : {len(not_in_osl):>6,}")
    if not_in_osl:
        print("  → These are compound / archaic variant signs whose Unicode")
        print("    code-point appears under an @form sub-entry in OSL,")
        print("    not as a top-level @sign block.")
        for uid in not_in_osl:
            print(f"      {uid}")
    print("─────────────────────────────────────────────────────────────\n")

    print("Sample output rows:")
    for r in rows[:5]:
        phon_preview = r["PhoneticsVersion"][:60] + ("…" if len(r["PhoneticsVersion"]) > 60 else "")
        print(
            f"  {r['unicode_id']}  {r['sign_grapheme']}  "
            f"{r['unicodeTrLit']!r:30s}  "
            f"{r['syllabarySign']!r:25s}  {phon_preview}"
        )


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 65)
    print("  build_restUnicodeSigns.py")
    print("=" * 65)

    unicode_signs = load_unicode_signs(UNICODE_CSV)
    matched_ids   = load_matched_ids(MATCHED_CSV)
    osl           = parse_osl(OSL_FILE)

    rows, not_in_osl = build_missing_rows(unicode_signs, matched_ids, osl)

    write_csv(OUTPUT_CSV, rows, OUTPUT_FIELDNAMES)
    print_summary(rows, not_in_osl)


if __name__ == "__main__":
    main()
