# **P10. OSL And Catalogue Give A Reading To Different Signs (Конфликты чтений)**

*File: `P10_osl_reading_conflicts.csv`, 702 rows, check_id `P10-0001`–`P10-0702`. Built by `10_build_manual_check.py` from the outputs of 2026-11-14 (pipeline v14.4).*

## **Place In The Workflow (Место в workflow)**

Stage 1, Step 6.0 (manual check before the gold standard). Documented in `4.doc_sign_catalogue_v13.md` § 6 *Gap filling from OSL @v* (`osl_reading_conflicts_v13.csv`); `1.doc_unicode_assign_v3.md` (702 conflicts); script 06.

## **The Problem (Проблема)**

OSL gives the reading to one sign, the catalogue (syllabary) to another (mur₂: MURUB₄ vs NISAG). By the project rule the disagreement is recorded, not overwritten. The column `parser_resolves_to` shows which sign the parser actually uses. Some conflicts come from the normalisation ḫ → h of Step 5 (*hi*: OSL DIN, catalogue HI), not from the sign lists.

## **Automatic Fix (Автоматическое исправление)**

**No.** Choosing between sign lists is philology. ⚠️ The ḫ / h cases may need a change of the normalisation instead of a sign decision.

## **Size And Effect On The Corpus (Объём)**

702 conflicts; 42 readings occur in the corpus, 13,159 tokens.

## **Which Rows To Check (Scope)**

Rows in the corpus: **mandatory**, the 10 rows with ≥ 100 tokens first. The rest: optional.

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `osl_sign / catalogue_sign` | the two candidates |
| `parser_resolves_to` | sign used by the parser and how often |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Look the reading up in OSL and MZL.
2. If the conflict comes from h / ḫ (or ş / ṣ), write `NORMALISATION`.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `KEEP_CATALOGUE` | the catalogue sign is right | – |
| `USE_OSL` | the OSL sign is right | – |
| `NORMALISATION` | an artefact of the letter normalisation | explain |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| reading | osl_sign | catalogue_sign | parser_resolves_to | tokens_in_OB_corpus |
|---|---|---|---|---|
| hi | DIN | HI | HI 7911 | 7911 |
| maš | MAŠ@t | MAŠ | MAŠ 1189 | 1189 |
| lil₂ | E₂ | KID | KID 855 | 855 |
| uš₂ | TIL | UŠ₂ | UŠ₂ 608 | 608 |
| lamma | GURUŠ | KAL | KAL 342 | 342 |
| kar₂ | GAN₂ | GAN₂@t | GAN₂@t 313 | 313 |

*These are real rows of the file, not decisions.*
