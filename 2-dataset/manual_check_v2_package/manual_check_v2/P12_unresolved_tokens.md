# **P12. Unresolved Tokens (Нераспознанные токены)**

*File: `P12_unresolved_tokens.csv`, 1265 rows, check_id `P12-0001`–`P12-1265`. Built by `10_build_manual_check.py` from the outputs of 2026-11-14 (pipeline v14.4).*

## **Place In The Workflow (Место в workflow)**

Stage 1, Step 6.0 (manual check before the gold standard). Documented in `5.doc_parsing_layer_v14.md` § 16 *Warnings File* (`warnings.csv`); script 07.

## **The Problem (Проблема)**

Readings that match nothing in any dictionary. Some are new readings (*tur₃*, *ginₓ*), some editorial markup that slipped through (`(…)`, `{{%a`), some sign-list numbers (*rec169*).

## **Automatic Fix (Автоматическое исправление)**

**No**, but every answer can become a rule of 07 (new reading → catalogue; markup → skipped).

## **Size And Effect On The Corpus (Объём)**

1265 token types, 3,495 tokens (0.15 % of all tokens; 135 in school texts).

## **Which Rows To Check (Scope)**

Rows with ≥ 10 tokens (41 rows, 1,559 tokens): **mandatory**. The rest: optional.

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `normalized_token` | the token after the normalisation of Step 5.1 |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Open `corpus_example`.
2. Decide what the token is.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `NEW_READING` | a reading of a known sign | `sign_or_reading` required |
| `EDITORIAL_MARKUP` | ATF markup, not a sign | – |
| `BROKEN` | damaged text | – |
| `KEEP_UNRESOLVED` | cannot be resolved | – |

## **First Rows Of The File (Examples)**

| normalized_token | tokens_in_OB_corpus | tokens_school | top_sites |
|---|---|---|---|
| tur3 | 357 | 4 | (empty) 146, Nippur 92, Ur 44, uncertain 39 |
| (…) | 125 | 0 | (empty) 47, Nippur 31, Sippar-Yahrurum 25, Dilbat 4 |
| ginx | 109 | 0 | Nippur 75, uncertain 34 |
| gilgames2 | 94 | 0 | (empty) 83, Nippur 5, Ur 5, uncertain 1 |
| iti6 | 59 | 1 | (empty) 35, Nippur 13, Ur 9, uncertain 1 |
| rec169 | 55 | 0 | (empty) 35, Nippur 19, Ur 1 |

*These are real rows of the file, not decisions.*
