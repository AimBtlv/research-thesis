# **P09. Syllabary Name Without Unicode In The Corpus (Имя силлабария без кода)**

*File: `P09_syllabary_name_without_unicode.csv`, 31 rows, check_id `P09-0001`–`P09-0031`. Built by `10_build_manual_check.py` from the outputs of 2026-11-14 (pipeline v14.4).*

## **Place In The Workflow (Место в workflow)**

Stage 1, Step 6.0 (manual check before the gold standard). Documented in `4.doc_sign_catalogue_v13.md` § 7 *Extending The Dataset* (Stage 6–7); `5.doc_parsing_layer_v14.md` ⚠️ note on 2,545 rows; script 06.

## **The Problem (Проблема)**

Some readings resolve to a name that comes only from the historical syllabaries and is written like a compound (SIPA, KA.AN.RA = Babylon, AŠ2.A.AN = udru, IDIGNA). The parser treats it as one simple sign **without a code point**, so these tokens have no glyph in `grapheme.csv`.

## **Automatic Fix (Автоматическое исправление)**

**No.** The link to an OSL compound (sipa = \|PA.LU\|, babila₂ = \|KA₂.AN.RA\| …) is a philological decision; `osl_suggestion` shows candidates where OSL has the same name or the same value.

## **Size And Effect On The Corpus (Объём)**

31 names, 2,543 tokens (50 in school texts).

## **Which Rows To Check (Scope)**

All rows: **mandatory**.

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `readings_in_corpus` | the ATF readings that lead to this name |
| `osl_suggestion` | OSL entries with the same name or value |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Look the reading up in OSL / ePSD2.
2. Write the OSL sign (usually a compound) in `osl_sign`.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `LINK_TO_OSL` | the name is this OSL sign | `osl_sign` required |
| `KEEP_AS_NAME` | no OSL sign; keep without code | – |
| `NOT_A_SIGN` | an editorial artefact | – |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| sign_name | readings_in_corpus | osl_suggestion | tokens_in_OB_corpus | tokens_school |
|---|---|---|---|---|
| SIPA | sipa 1005, rex(sipa) 1 | OSL value of: \|PA.LU\| | 1006 | 32 |
| KA.AN.RA | babila2 537 | OSL value of: \|KA₂.AN.RA\| | 537 | 0 |
| AŠ2.A.AN | udru 425, imgaga 3 | OSL value of: \|ZIZ₂.A.AN\| | 428 | 1 |
| IDIGNA | idigna 205 | same name in OSL: IDIGNA / OSL value of: \|GU₂.GAR₃\|; \|TUM×PAP\| | 205 | 1 |
| GIŠ.TUG2.PI.ŠIR.SILA3 | gizzal 71 | OSL value of: \|GIŠ.TUG₂.PI.NU₁₁@90.SILA₃\| | 71 | 1 |
| KA.AN | babila 54, mitumx(\|ka+an\|) 1 | OSL value of: \|KA₂.AN\| | 55 | 4 |

*These are real rows of the file, not decisions.*
