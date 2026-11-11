#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 08b_goldlib.py
Description: Workflow Stage 1, Step 6.3 + 6.5. Core library for building the sign-level gold standard of the
             Old Babylonian CDLI corpus: OSL sign-list index, ATF tokenizer
             (line -> word -> sign), sign resolution (reading -> OSL sign ->
             Unicode) and rule-based function labelling (LOGO / SYLL / DET /
             NUM / UNCLEAR) by language and context.
Author: Aima (thesis "Signs and Their Readings in School and Other Texts of
        the Old Babylonian Period"), prepared with Claude
Date: 2026-11-09
Version: 1.2
"""

import re
import unicodedata
from collections import defaultdict

# ---------------------------------------------------------------------------
# 1. NORMALISATION
# ---------------------------------------------------------------------------

SUB_DIGITS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
PLAIN_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉ₓ", "0123456789x")

# C-ATF ASCII conventions -> Unicode (order matters: digraphs first)
ASCII_MAP = [("sz", "š"), ("SZ", "Š"), ("s,", "ṣ"), ("S,", "Ṣ"),
             ("t,", "ṭ"), ("T,", "Ṭ"), ("j", "ŋ"), ("J", "Ŋ"),
             ("ĝ", "ŋ"), ("Ĝ", "Ŋ"), ("g̃", "ŋ"), ("G̃", "Ŋ"),
             ("ḫ", "h"), ("Ḫ", "H"), ("'", "ʾ")]


def to_unicode_reading(s: str) -> str:
    """ASCII C-ATF reading ('du11', 'sza3', 'kux') -> OSL-style reading
    ('du₁₁', 'ša₃', 'kuₓ'). OSL writes ḫ as plain h and ĝ as ŋ."""
    for a, b in ASCII_MAP:
        s = s.replace(a, b)
    # trailing index digits -> subscript; 'x' index -> ₓ
    m = re.match(r"^(.*?[^\d])(\d+|x)$", s)
    if m and not re.fullmatch(r"\d+", s):
        base, idx = m.groups()
        idx = "ₓ" if idx == "x" else idx.translate(SUB_DIGITS)
        s = base + idx
    # digits inside sign names like 'LU2@s' / 'KA2.GAL'
    s = re.sub(r"(?<=[A-Za-zŠšŊŋṢṣṬṭ])(\d+)",
               lambda mm: mm.group(1).translate(SUB_DIGITS), s)
    return unicodedata.normalize("NFC", s)


def to_ascii_key(s: str) -> str:
    """Lookup key: lower case, plain digits (used for case-insensitive
    matching between ATF and OSL)."""
    return unicodedata.normalize("NFC", s).translate(PLAIN_DIGITS).lower()


# ---------------------------------------------------------------------------
# 2. OSL INDEX
# ---------------------------------------------------------------------------

class OSLIndex:
    """Parses osl.asl into:
       values[key]  -> list of (sign_name, is_form_value, deprecated)
       signs[name]  -> {'ucun':..., 'codes':[...], 'kind':'sign'|'form',
                        'parent':...}
    key = to_ascii_key(reading), e.g. 'du11'."""

    def __init__(self, path: str):
        self.values = defaultdict(list)
        self.signs = {}
        self.name_key = {}  # ascii key of sign name -> canonical name
        self._parse(path)

    def _parse(self, path):
        cur_sign, cur_form = None, None
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if re.match(r"@sign[+-]?\s", line):  # tab or space separator
                    name = line.split(None, 1)[1].strip()
                    cur_sign, cur_form = name, None
                    self.signs.setdefault(name, {"ucun": "", "codes": [],
                                                 "kind": "sign", "parent": None})
                    self.name_key.setdefault(to_ascii_key(name.strip("|")), name)
                elif re.match(r"@form[+-]?\s", line):
                    # '@form+ AŠ@c' marks a form too (fixed in v1.2)
                    name = line.split(None, 1)[1].strip()
                    cur_form = name
                    self.signs.setdefault(name, {"ucun": "", "codes": [],
                                                 "kind": "form", "parent": cur_sign})
                    self.name_key.setdefault(to_ascii_key(name.strip("|")), name)
                elif line.strip() == "@@":
                    cur_form = None
                elif line.startswith("@end sign"):
                    cur_sign, cur_form = None, None
                elif cur_sign is None:
                    continue
                elif line.startswith("@ucun"):
                    tgt = cur_form or cur_sign
                    # separator may be a tab or a space ('@ucun 𒕐')
                    self.signs[tgt]["ucun"] = line.split(None, 1)[-1].strip()
                elif re.match(r"@list\s+U\+", line):
                    tgt = cur_form or cur_sign
                    self.signs[tgt]["codes"].append(line.split(None, 1)[1].strip())
                elif line.startswith("@useq"):
                    tgt = cur_form or cur_sign
                    seq = line.split("\t", 1)[-1].strip()
                    if not self.signs[tgt]["codes"]:
                        self.signs[tgt]["codes"] = [
                            "U+" + p[1:].upper() for p in seq.split(".")
                            if p.startswith("x")]
                elif line.startswith("@v"):
                    deprecated = line.startswith("@v-")
                    val = line.split("\t", 1)[-1].strip()
                    if val.startswith("%") or " " in val:
                        continue  # language-tagged lemma values (%akk ...)
                    val = val.rstrip("?")
                    owner = cur_form or cur_sign
                    self.values[to_ascii_key(val)].append(
                        (owner, cur_form is not None, deprecated))

    def lookup_value(self, reading: str):
        """Return list of candidate sign names for a reading, best first:
        non-deprecated sign values > form values > deprecated."""
        cands = self.values.get(to_ascii_key(to_unicode_reading(reading)), [])
        ranked = sorted(cands, key=lambda c: (c[2], c[1]))
        seen, out = set(), []
        for name, is_form, dep in ranked:
            if name not in seen:
                seen.add(name)
                out.append((name, is_form, dep))
        return out

    def lookup_name(self, name: str):
        """Sign name as written in ATF ('KA', '|KA2.GAL|', 'LU2@s')."""
        key = to_ascii_key(to_unicode_reading(name.strip("|")).replace("x", "×")
                           if "|" in name else to_unicode_reading(name.strip("|")))
        if key in self.name_key:
            return self.name_key[key]
        key2 = to_ascii_key(to_unicode_reading(name.strip("|")))
        return self.name_key.get(key2)

    def unicode_of(self, name: str):
        info = self.signs.get(name)
        if not info:
            return "", ""
        codes = list(dict.fromkeys(info["codes"]))
        ucun = info["ucun"]
        if not codes and info["kind"] == "form" and info["parent"]:
            p = self.signs.get(info["parent"], {})
            return "; ".join(p.get("codes", [])), p.get("ucun", "")
        return "; ".join(codes), ucun


# ---------------------------------------------------------------------------
# 3. ATF READING: tablets, lines, words, signs
# ---------------------------------------------------------------------------

def split_atf_tablets(text: str):
    """Yield (p_number, block_text) for every &P... block in an ATF file."""
    blocks = re.split(r"(?m)^(?=&P\d+)", text)
    for b in blocks:
        m = re.match(r"&(P\d+)", b)
        if m:
            yield m.group(1), b


LINE_RE = re.compile(r"^(\d+[a-z]?'*(?:-\d+'*)?)\.\s+(.*)$")


def iter_text_lines(block: str):
    """Yield dicts for every transliteration line of one tablet with its
    structural position (surface, column) and base language."""
    surface, column = "", ""
    lang = ""
    m = re.search(r"#atf:\s*lang\s+(\S+)", block)
    if m:
        lang = m.group(1).strip()
    for raw in block.splitlines():
        s = raw.rstrip()
        if not s:
            continue
        if s.startswith("@"):
            tag = s[1:].split()[0] if len(s) > 1 else ""
            if tag in ("obverse", "reverse", "left", "right", "top", "bottom",
                       "edge", "seal", "envelope", "tablet", "case", "surface",
                       "fragment", "object", "prism", "face", "docket"):
                if tag in ("tablet", "envelope", "case", "object"):
                    surface = tag if tag not in ("tablet", "object") else surface
                else:
                    surface = s[1:].strip()
                column = ""
            elif tag == "column":
                column = s.split(None, 1)[1].strip() if " " in s else ""
            continue
        m = LINE_RE.match(s)
        if m:
            yield {"line_num": m.group(1), "content": m.group(2).strip(),
                   "surface": surface or "obverse", "column": column,
                   "base_lang": lang}


# Damage / editorial flags on a single sign
def parse_flags(sign: str):
    flags = []
    if "#" in sign:
        flags.append("damaged")
    if "?" in sign:
        flags.append("uncertain")
    if "*" in sign:
        flags.append("collated")
    clean = sign.replace("#", "").replace("?", "").replace("*", "")
    return clean, flags


NUMERAL_RE = re.compile(r"^(n|\d+(?:/\d+)?)\(([^()]+)\)$")
QUAL_RE = re.compile(r"^(.+?)(!?)\((.+)\)$")   # reading(SIGN) or reading!(SIGN)


def tokenize_line(content: str):
    """Split one ATF line into words, keeping editorial state across words:
    _..._ (logogram region in Akkadian), [...] (broken), <...> (omitted by
    scribe, supplied by editor), <<...>> (erased / superfluous),
    %a / %s language switches, '=' column separator in lexical lists.
    Returns list of word dicts with raw text and per-character state."""
    words = []
    # remove inline ($ ... $) comments
    content = re.sub(r"\(\$.*?\$\)", " ", content)
    content = content.replace("⸢", "").replace("⸣", "")
    state = {"logo": False, "broken": False, "supplied": False,
             "erased": False, "lang": None, "gloss": False}
    for raw in content.split():
        if raw in ("=", ":", "/", "|"):
            state["gloss"] = False
            continue
        if raw.startswith(",!"):
            # pronunciation gloss marker (e.g. ',!pr' in Susa lexical texts)
            state["gloss"] = True
            continue
        if re.fullmatch(r"%[a-z0-9-]+", raw):
            state["lang"] = {"%a": "akk", "%s": "sux", "%sux": "sux",
                             "%akk": "akk", "%e": "sux-x-emesal"}.get(raw, raw[1:])
            continue
        words.append(_parse_word(raw, state))
    return words


def _parse_word(raw: str, state: dict):
    """Walk one raw ATF word character by character. Produces a list of
    'pieces' (sign strings) each with its own editorial state, separators
    and determinative status."""
    pieces = []
    buf, buf_state = "", None
    det_depth = 0
    det_is_phon = False
    i = 0
    start_state = dict(state)

    def flush():
        nonlocal buf, buf_state
        if buf.strip():
            pieces.append({"text": buf, **(buf_state or dict(state)),
                           "det": det_depth > 0, "phon_compl": det_is_phon})
        buf, buf_state = "", None

    in_pipe = False
    paren = 0
    while i < len(raw):
        c = raw[i]
        two = raw[i:i + 2]
        if c == "|":
            in_pipe = not in_pipe
            buf += c
            i += 1
            continue
        if in_pipe or paren:
            if c == "(":
                paren += 1
            elif c == ")":
                paren -= 1
            buf += c
            i += 1
            continue
        if two == "{{":
            flush(); state["gloss"] = True; i += 2; continue
        if two == "}}":
            flush(); state["gloss"] = False; i += 2; continue
        if two == "<<":
            flush(); state["erased"] = True; i += 2; continue
        if two == ">>":
            flush(); state["erased"] = False; i += 2; continue
        if c == "<":
            flush(); state["supplied"] = True; i += 1; continue
        if c == ">":
            flush(); state["supplied"] = False; i += 1; continue
        if c == "[":
            flush(); state["broken"] = True; i += 1; continue
        if c == "]":
            flush(); state["broken"] = False; i += 1; continue
        if c == "_":
            flush(); state["logo"] = not state["logo"]; i += 1; continue
        if c == "{":
            flush(); det_depth += 1
            det_is_phon = raw[i + 1:i + 2] == "+"
            i += 2 if det_is_phon else 1
            continue
        if c == "}":
            flush(); det_depth -= 1; det_is_phon = False; i += 1; continue
        if c in "-.+" and not paren:
            # '+' inside readings only occurs in compounds (handled in pipes)
            flush(); i += 1; continue
        if c == "(":
            paren += 1
        if buf == "":
            buf_state = dict(state)
        buf += c
        i += 1
    flush()
    return {"raw": raw, "pieces": pieces, "start_state": start_state}


# ---------------------------------------------------------------------------
# 4. SIGN RESOLUTION
# ---------------------------------------------------------------------------

# Philological preferences where OSL lists several signs for one value
PREFERRED_SIGN = {"babila₂": "|KA₂.AN.RA|"}


def resolve_piece(text: str, osl: OSLIndex):
    """Resolve one sign piece. Returns dict with reading, sign_name,
    codes, ucun, resolution, n_candidates, flags, kind."""
    clean, flags = parse_flags(text)
    out = {"reading_atf": clean, "flags": flags, "kind": "sign",
           "reading": "", "sign_name": "", "unicode_id": "", "ucun": "",
           "resolution": "", "n_candidates": 0, "corrected": False,
           "qualifier": ""}
    if clean in ("...", "…", "&", "~", "$") or re.fullmatch(r"\.+", clean):
        out["kind"] = "gap"   # break, column marker or sign-list placeholder
        return out
    if re.fullmatch(r"\d+", clean) or clean == "n":
        # bare digits = modern (sexagesimal) number notation of the editor,
        # 'n' = indeterminate number
        out.update(kind="numeral", reading=clean, sign_name="NUMBER",
                   resolution="numeral_modern_notation" if clean != "n"
                   else "numeral_indeterminate")
        return out
    if clean.lower() == "x":
        out.update(kind="unreadable", sign_name="X", resolution="unreadable")
        return out
    # numerals: 2(asz), 1/2(disz), n(gesz2)
    nm = NUMERAL_RE.match(clean)
    if nm and re.fullmatch(r"[a-zšŋA-ZŠ0-9@~]+", to_unicode_reading(nm.group(2))
                           .translate(PLAIN_DIGITS)):
        vc = osl.lookup_value(clean)
        name = vc[0][0] if vc else None
        out.update(kind="numeral", reading=to_unicode_reading(clean),
                   sign_name=name or to_unicode_reading(clean).upper(),
                   resolution="numeral")
        if name:
            out["unicode_id"], out["ucun"] = osl.unicode_of(name)
        return out
    # reading(SIGN) / reading!(SIGN)
    qm = QUAL_RE.match(clean)
    if qm and (qm.group(3)[:1].isupper() or qm.group(3).startswith("|")):
        rd, bang, sname = qm.groups()
        # qualifier may carry its own damage marks / brackets / 2nd qualifier
        sname = re.sub(r"\)\(.*$", "", sname)
        sname = re.sub(r"[\[\]#?*]", "", sname)
        out["corrected"] = bool(bang)
        out["qualifier"] = sname
        name = osl.lookup_name(sname)
        out.update(reading=to_unicode_reading(rd.replace("!", "")),
                   sign_name=name or to_unicode_reading(sname),
                   resolution="qualifier" + ("_corrected" if bang else ""),
                   n_candidates=1 if name else 0)
        if name:
            out["unicode_id"], out["ucun"] = osl.unicode_of(name)
        else:
            out["resolution"] = "qualifier_not_in_osl"
        return out
    if "!" in clean:
        out["corrected"] = True
        clean = clean.replace("!", "")
    # explicit sign name / compound written in capitals or pipes
    is_name = clean.startswith("|") or (clean[:1].isupper() and clean.upper() == clean)
    if is_name:
        name = osl.lookup_name(clean)
        if not name and not clean.startswith("|"):
            vc = osl.lookup_value(clean.lower())
            name = vc[0][0] if vc else None
        out.update(reading=to_unicode_reading(clean), sign_name=name or
                   to_unicode_reading(clean), resolution="sign_name" if name
                   else "sign_name_not_in_osl", n_candidates=1 if name else 0)
        out["kind"] = "compound" if clean.startswith("|") else "sign"
        if name:
            out["unicode_id"], out["ucun"] = osl.unicode_of(name)
        out["reading_is_name"] = True
        return out
    rd = to_unicode_reading(clean)
    cands = osl.lookup_value(rd)
    out["reading"] = rd
    out["n_candidates"] = len(cands)
    if not cands:
        out["resolution"] = "unresolved"
        return out
    name = cands[0][0]
    pref = PREFERRED_SIGN.get(rd)
    if pref and any(c[0] == pref for c in cands):
        name = pref
        out["resolution_note"] = "preferred_over_osl_first_candidate"
    out["sign_name"] = name
    out["resolution"] = "osl_value" if not cands[0][1] else "osl_form_value"
    if cands[0][2]:
        out["resolution"] = "osl_deprecated_value"
    if name.startswith("|"):
        out["kind"] = "compound"
    out["unicode_id"], out["ucun"] = osl.unicode_of(name)
    return out


# ---------------------------------------------------------------------------
# 5. FUNCTION LABELLING (LOGO / SYLL / DET / NUM / UNCLEAR)
# ---------------------------------------------------------------------------

# Sumerian grammatical morphemes that are normally written phonetically.
SUX_VERBAL_PREFIX = {
    "mu", "ma", "ba", "bi₂", "bi", "i₃", "i", "im", "in", "an", "ab", "al",
    "am₃", "nu", "la", "li", "ga", "ha", "he₂", "hu", "na", "nam", "ša",
    "u₃", "e", "ni", "ne", "ri", "ra", "ta", "da", "ši", "me", "mi", "en",
    "un", "ib₂", "ab₂", "a", "im", "bara₂", "nan", "ga₂",
    "ši₃", "re", "ra₂"}
SUX_STRONG_PREFIX = {"mu", "ma", "ba", "bi₂", "i₃", "im", "in", "al", "nu", "ga",
                     "he₂", "ha", "u₃", "ab", "an", "am₃", "na", "ša", "ib₂",
                     "bara₂", "nam", "i", "im"}
SUX_SUFFIX = {
    "ha", "a", "ab", "ak", "am", "am₃", "an", "ar", "aš", "ba", "bi", "bi₂", "bu", "da", "dam", "de₃", "e", "en", "ene", "eš", "eše₂", "eš₂", "ga", "ga₂", "ge", "ge₄", "gin₇", "gu₁₀", "im", "ir", "ka", "kam", "ke", "ke₄", "la", "lu", "ma", "me", "men", "mi", "mu", "na", "ne", "ne₂", "ne₃", "ni", "nu", "ra", "ra₂", "re", "ri", "ru", "sa", "ta", "um", "ur", "uš", "ze", "zu", "ŋa₂", "ŋu₁₀", "ša", "še", "še₃", "šè"}
# Readings used ONLY grammatically (cannot be lexical roots in practice)
SUX_PURE_GRAMMAR = {"še₃", "ke₄", "ŋu₁₀", "gu₁₀", "am₃", "i₃", "bi₂",
                    "he₂", "u₃", "ib₂", "de₃", "gin₇", "eš", "eš₂", "men",
                    "ne", "ra", "ta", "da", "ka", "ga", "ge", "re", "ri",
                    "bi", "ni", "na", "ma", "la", "ab", "an", "in", "im",
                    "nu", "mu", "ba", "e", "a", "ke", "ge₄", "dam", "en",
                    "um", "am", "ŋa₂", "kam", "zu", "me", "ša", "ra₂"}
# Readings that are frequent Sumerian lexemes even though homographic with
# a morpheme. At word start without verbal context they stay LOGO.
SUX_LEXICAL_HOMOGRAPHS = {"a", "e₂", "mu", "ka", "an", "ki", "ŋa₂", "da",
                          "ta", "me", "zu", "ga", "ra", "na", "ni", "ab",
                          "du", "di", "e₃", "ša", "nu", "la", "ma", "en",
                          "ba", "bi", "u₃", "ti", "zi", "si", "sa", "ŋa",
                          "ne", "ri", "ku", "li", "lu", "ki"}

# frequent Akkadian personal-name elements written syllabically
AKK_NAME_ELEMENTS = {"i-din", "e-ri", "ri-ba", "ma-gir", "iš-me", "ib-ni",
                     "li-pi₂", "pi₂-it", "i-qi₂", "i₃-li₂", "li₂-šu",
                     "ap-hu", "na-ṣi", "e-tel", "ba-ni", "ha-zi", "zi-ir",
                     "mu-ša", "ša-lim", "re-me", "me-ni", "su-i", "i-lu",
                     "mu-ra", "ra-pi₂", "e-šu", "šu-uh", "da-gan", "ma-bu",
                     "ip-te", "ip-ti", "na-na", "a-hu", "qar-ra", "ta-a",
                     "a-ar", "pu-um", "nu-ur₂", "an-nu", "um-pi₄",
                     "pi₄-ša", "mi-iq", "ku-du", "du-ur"}
# Logographic signs that never start a syllabic Akkadian spelling
SUX_LOGO_ANCHORS = {"lugal", "dingir", "inim", "dumu", "lu₂", "e₂", "ur",
                    "ARAD₂", "ARAD", "nin", "en", "ama", "puzur₄", "ku₃",
                    "me", "nam", "nig₂", "šeš", "geme₂"}

AKK_LIKE = re.compile(r"(q|ṣ|ṭ|w|ʾ|ia|ii|iu|ie)")


def looks_syllabic_akkadian(readings):
    """Heuristic for Akkadian words (names, loanwords) inside Sumerian text:
    contains Akkadian-only phonemes, or ends in mimation -um/-im/-am, and
    has >= 2 signs."""
    if len(readings) < 2 or readings[0] in SUX_LOGO_ANCHORS:
        return False
    joined = "-".join(readings)
    if AKK_LIKE.search(joined):
        return True
    if readings[-1] in ("um", "im", "am", "tum", "tim", "tam", "rum", "lum",
                        "nam", "šu", "ša") and len(readings) >= 3:
        return True
    if any(r in AKK_NAME_ELEMENTS for r in ("-".join(readings[i:i + 2])
                                            for i in range(len(readings)))):
        return True
    return False


def label_word_sumerian(sign_rows):
    """Assign LOGO/SYLL to the non-DET, non-NUM, readable signs of one
    Sumerian word. Returns list of (function, rule, needs_check)."""
    idx = [k for k, r in enumerate(sign_rows)
           if r["_fn_base"] is None]
    res = {}
    rds = [sign_rows[k]["reading"] for k in idx]
    if not idx:
        return res
    # explicit sign names (capitals) in Sumerian: logographic use assumed
    if looks_syllabic_akkadian(rds):
        for k in idx:
            res[k] = ("SYLL", "sux:akkadian_word_syllabic", True)
        return res
    n = len(idx)
    if n == 1:
        k = idx[0]
        r = rds[0]
        if r in SUX_PURE_GRAMMAR and r not in SUX_LEXICAL_HOMOGRAPHS:
            res[k] = ("SYLL", "sux:isolated_grammatical", True)
        else:
            res[k] = ("LOGO", "sux:single_sign_word", False)
        return res
    # find prefix chain at start
    pos = 0
    first = rds[0]
    has_lexical_later = any(r not in SUX_SUFFIX and r not in SUX_VERBAL_PREFIX
                            for r in rds[1:])
    truncated = sign_rows[idx[-1]].get("_trunc", False)
    nam_is_abstract = first == "nam" and (n < 2 or rds[1] not in SUX_VERBAL_PREFIX)
    if truncated and first in SUX_STRONG_PREFIX and not nam_is_abstract and \
            all(r in SUX_VERBAL_PREFIX for r in rds):
        for k in idx:
            res[k] = ("SYLL", "sux:verbal_prefix_chain_truncated", False)
        return res
    if first in SUX_STRONG_PREFIX and has_lexical_later and not nam_is_abstract:
        while pos < n - 1 and rds[pos] in SUX_VERBAL_PREFIX and \
                any(r not in SUX_SUFFIX and r not in SUX_VERBAL_PREFIX
                    for r in rds[pos + 1:]):
            res[idx[pos]] = ("SYLL", "sux:verbal_prefix", False)
            pos += 1
    # root = first sign after prefixes; further non-grammatical signs = LOGO
    root_done = False
    for j in range(pos, n):
        k, r = idx[j], rds[j]
        if not root_done:
            amb = (r in SUX_PURE_GRAMMAR and j > 0)
            res[k] = ("LOGO", "sux:root" if not amb else "sux:root_homograph",
                      amb)
            root_done = True
            continue
        prev = rds[j - 1]
        if r == "la₂" and prev == "lil₂":
            res[k] = ("SYLL", "sux:genitive_after_enlil", False)
        elif r == prev and res.get(idx[j - 1], ("",))[0] == "LOGO":
            res[k] = ("LOGO", "sux:reduplicated_root", False)
        elif r in SUX_SUFFIX:
            res[k] = ("SYLL", "sux:suffix_or_phon_complement", False)
        else:
            res[k] = ("LOGO", "sux:compound_noun_element", False)
    return res


def label_function(sign_rows, word_lang: str):
    """Fill 'sign_function', 'function_rule', 'needs_check' for all sign
    rows belonging to one word (in place)."""
    for r in sign_rows:
        r["_fn_base"] = None
        if r["kind"] == "numeral":
            r["_fn_base"] = ("NUM", "numeral_notation", False)
        elif r["det"] and not r["phon_compl"]:
            r["_fn_base"] = ("DET", "braces_determinative", False)
        elif r["phon_compl"]:
            r["_fn_base"] = ("SYLL", "phonetic_complement_{+}", False)
        elif r["kind"] in ("unreadable",):
            r["_fn_base"] = ("UNCLEAR", "x_unreadable", False)
        elif r["resolution"] == "unresolved":
            r["_fn_base"] = ("UNCLEAR", "reading_not_in_osl", True)
    res = {}
    lang = word_lang
    if lang.startswith("akk"):
        # inside _..._ = Sumerian (logograms / Sumerian phrases)
        logo_k = [k for k, r in enumerate(sign_rows)
                  if r["logo"] and r["_fn_base"] is None]
        if logo_k:
            sub = [sign_rows[k] for k in logo_k]
            sres = label_word_sumerian(sub)
            for j, k in enumerate(logo_k):
                f, rule, chk = sres.get(j, ("LOGO", "x", True))
                res[k] = (f, "akk:inside_underscore|" + rule, chk)
        out_k = [k for k, r in enumerate(sign_rows)
                 if not r["logo"] and r["_fn_base"] is None]
        lower = [k for k in out_k if not sign_rows[k].get("reading_is_name")]
        for k in out_k:
            r = sign_rows[k]
            if r.get("reading_is_name"):
                if lower:
                    res[k] = ("SYLL", "akk:sign_name_in_syllabic_word", True)
                else:
                    res[k] = ("LOGO", "akk:sign_name_outside_underscore", True)
            else:
                res[k] = ("SYLL", "akk:outside_underscore", False)
    else:
        # in a Sumerian text _..._ switches to Akkadian (syllabic)
        for k, r in enumerate(sign_rows):
            if r["logo"] and r["_fn_base"] is None:
                r["_fn_base"] = ("SYLL", "sux:akkadian_in_underscore", False)
                r["lang"] = "akk"
        res = label_word_sumerian(sign_rows)
        for k, r in enumerate(sign_rows):
            if k in res and r.get("reading_is_name"):
                f, rule, _ = res[k]
                res[k] = (f, rule + "+sign_name_reading_unknown", True)
    for k, r in enumerate(sign_rows):
        f = r["_fn_base"] or res.get(k) or ("UNCLEAR", "no_rule", True)
        r["sign_function"], r["function_rule"], r["needs_check"] = f
        del r["_fn_base"]
    return sign_rows
