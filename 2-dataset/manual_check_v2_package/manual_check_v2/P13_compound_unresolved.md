# P13. Compounds The Script Could Not Split 

*File: `P13_compound_unresolved.csv`   
182 rows    
Check_id `P13-0001`–`P13-0182`     
The outputs of 2026-11-14 (pipeline v14.4)*

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard). 
Documented in `4.doc_sign_catalogue_v13.md` § 4, `structural_hint = compound_unresolved`.    
Script: `06_build_sign_catalogue_v13.py`

## The Problem 

*How the script splits a compound?*      
When OSL gives no list of components (`@useq`), `script 06` cuts the name at the operator and looks up every piece in OSL (as in P01): |AB×A| → AB + A. If one piece is not found, the script **does not guess**: the sign stays unsplit (`sign_structure = not_identified`,
`compound_unresolved`).     
A wrong split would be worse than none.

*Why a piece is not found?*       
By the form of the name:

| Group | Example | Rows | Reason |
|---|---|---|---|
| nested brackets | \|GA₂×(HAL.A)\|, \|(BU%BU)×AB\| | 126 | a compound inside a compound; the script cuts only one level |
| X in the name | \|AB×X\|, \|EN×X\| | 24 | X = unknown sign, nothing to look up |
| sign-list number | \|AB×LAK178\|, \|LAK648×IM\| | 9 | LAK178 is a number of the LAK list, not an OSL sign name |
| numeral prefix | 2(\|GEŠU@c×KASKAL\|) | 8 | "two signs …", a count, not a component |
| repetition number | \|3×LU₂\|, \|4×GABA\| | 4 | "three LU₂": the script does not read 3× as a repetition |
| other | \|ASAL₂×A\|, \|ŠIM×X₁\| | 11 | the piece is not found under this name |

(The grouping is by the form of the name, the column `reason` of the CSV has
only two values: nested brackets / component not found.)

## Automatic Fix 

**Partly.**      
A piece is now also looked up among the `@form` entries with a ratified code point.     
This works for LAK648, which OSL lists as a `@form` with a code: |LAK648×IM|, |LAK648×IGI|, |LAK648×LU₃| and |LAK648×DIŠ@c| are now split (the last one with the modifier dropped, DIŠ@c → DIŠ, see P01).
The file was built from the outputs before the re-run, after the re-run these 4 rows leave it (178 remain).

For the other groups an expert decides how to split a nested sign (and whether
it should be split at all: some are one graphic unit), which OSL sign a LAK
number stands for, and whether a sign with X can be split.

76 of the rows already have a reading found by the sign name (69 via OGSL,
7 via Diri, column `hint_in_catalogue`): the reading is known, the components
are not.

## Size And Effect On The Corpus

182 entries (178 after the re-run) 
Only **1** occurs in the Old Babylonian corpus: |DAG.KISIM₅×LU| (a form of |DAG.KISIM₅×(LU.MAŠ₂)|), **2** tokens. This is a question of catalogue quality, not of the thesis: the file is optional.

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
