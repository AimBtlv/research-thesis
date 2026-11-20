# **P15. Registered Name Took The Code Of Another Sign (Чужой код у знака)**

*File: `P15_wrong_code_of_registered_name.csv`, 30 rows, check_id `P15-0001`–`P15-0030`. Built by `10_build_manual_check.py` from the outputs of 2026-11-14 (pipeline v14.4).*

## **Place In The Workflow (Место в workflow)**

Stage 1, Step 6.0 (manual check before the gold standard). Documented in `5.doc_parsing_layer_v14.md` § 10 *Sign Identity Of Variants* (v13); script `08_tokens_to_grapheme_v14.py`.

## **The Problem (Проблема)**

**The largest error found.** Since v13 a variant that is a registered sign of its own is resolved under its own name (MAŠ₂, not KUN). Step 5.2 then took the code point of the *first* catalogue row with this name. For 30 names that first row was a `@form` row of *another* sign with an inherited code point: *da* got U+12009 (A₂, 𒀉) instead of U+12055 (DA, 𒁕), *ri* got 𒄷 (HU) instead of 𒊑, *nam* BURU₅ instead of NAM, *u* DIŠ instead of U. The reading and the sign name were right; only the glyph was wrong, so the check by function (gold, v14.4) could not see it.

## **Automatic Fix (Автоматическое исправление)**

**Yes (08 v14.5, fix P15).** A registered name takes the code point of its own row.

## **Size And Effect On The Corpus (Объём)**

30 names, 74,102 tokens ≈ 74,100 rows of `grapheme.csv` (3.4 %), 1,428 of them in school texts. Every count by glyph (Jaccard, inventories) was affected.

## **Which Rows To Check (Scope)**

All rows: a quick **confirmation** (compare `old_glyph` and `new_glyph`).

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `old_unicode_id / old_glyph / old_taken_from` | the wrong code and the row it came from |
| `new_unicode_id / new_glyph` | the code of the sign's own row |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Check that `new_glyph` is the sign of the reading (da = 𒁕).
2. Write `CONFIRM`.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `CONFIRM` | the fix is right | – |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| sign_name | old_glyph | old_taken_from | new_glyph | tokens_in_OB_corpus | tokens_school |
|---|---|---|---|---|---|
| RI | 𒄷 | HU / @form RI | 𒊑 | 23554 | 421 |
| DA | 𒀉 | A₂ / @form DA | 𒁕 | 21194 | 407 |
| NAM | 𒉅 | BURU₅ / @form NAM | 𒉆 | 11448 | 212 |
| DUN₃@g | 𒂅 | DUN₃ / @form DUN₃@g | 𒂆 | 4926 | 54 |
| KAL | 𒄨 | GURUŠ / @form KAL | 𒆗 | 2571 | 80 |
| PAP | 𒁹 | DIŠ / @form PAP | 𒉽 | 1790 | 46 |

*These are real rows of the file, not decisions.*
