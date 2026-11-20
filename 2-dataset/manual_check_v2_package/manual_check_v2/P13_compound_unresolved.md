# **P13. Compounds The Script Could Not Split (Неразрешённые составные)**

*File: `P13_compound_unresolved.csv`, 182 rows, check_id `P13-0001`–`P13-0182`. Built by `10_build_manual_check.py` from the outputs of 2026-11-14 (pipeline v14.4).*

## **Place In The Workflow (Место в workflow)**

Stage 1, Step 6.0 (manual check before the gold standard). Documented in `4.doc_sign_catalogue_v13.md` § 4, `structural_hint = compound_unresolved`; script 06.

## **The Problem (Проблема)**

A name with `×` or `&` that the script could not split: nested brackets (\|GA₂×(HAL.A)\|) or a piece that is not a sign (LAK178, X).

## **Automatic Fix (Автоматическое исправление)**

**Partly (06 v13.1, fix P01).** Pieces are now also looked up among the `@form` entries with a ratified code: \|LAK648×IM\|, \|LAK648×IGI\|, \|LAK648×LU₃\|, \|LAK648×DIŠ@c\| are now split (the last one with the modifier dropped: DIŠ@c → DIŠ, see P01).

## **Size And Effect On The Corpus (Объём)**

182 entries; 1 in the corpus (2 tokens). For the catalogue, not for the thesis.

## **Which Rows To Check (Scope)**

**Optional.**

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `reason` | nested brackets or component not found |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. As in the earlier file 2 of the package.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `SPLIT` | components given | required |
| `KEEP_UNSPLIT` | one graphic unit | – |
| `COMPONENT_ALIAS` | missing piece has another OSL name | `old = new` |
| `NOT_IDENTIFIED` | contains X | – |
| `NOT_A_SIGN` | not a real sign | – |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| entity | reason | tokens_in_OB_corpus |
|---|---|---|
| \|DAG.KISIM₅×LU\| | component not found as @sign / @form | 2 |
| 2(\|GEŠU@c×KASKAL\|) | nested parentheses (compound inside compound) | 0 |
| 3(\|GEŠU@c×KASKAL\|) | nested parentheses (compound inside compound) | 0 |
| 4(\|GEŠU@c×KASKAL\|) | nested parentheses (compound inside compound) | 0 |
| 5(\|GEŠU@c×KASKAL\|) | nested parentheses (compound inside compound) | 0 |
| 6(\|BAD×DIŠ@t\|) | nested parentheses (compound inside compound) | 0 |

*These are real rows of the file, not decisions.*
