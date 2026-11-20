# P06. Duplicated Components

*File: `P06_duplicated_components.csv`.   
40 rows    
Check_id `P06-0001`–`P06-0040`   
The outputs of 2026-11-14 (pipeline v14.4)*   

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard).     
Documented in `5.doc_parsing_layer_v14.md` § 13 *Compound Expansion*.     
Script `08_tokens_to_grapheme_v14.py`

## The Problem

How a compound enters *grapheme.csv?*      
A compound sign is written to `grapheme.csv` as **one row per component**.      
ATF *didli* (the sign |AŠ.AŠ|,
"several, individual") = AŠ + AŠ, so one token gives **2 rows** (AŠ 𒀸, AŠ 𒀸).

One form, several entries in OSL. OSL lists |AŠ.AŠ| **twice**:

| Where in OSL | What it is |
|---|---|
| `@sign AŠ.AŠ` | the sign's own entry |
| `@form AŠ.AŠ` inside AN.AŠ.AN | a variant of another sign |

Both describe **the same sign** with the same components AŠ + AŠ, so the
catalogue has two groups of rows with `compound_form = |AŠ.AŠ|`.

*Where the error arose?*     
Step 5.2 (script 08) built the list of components by collecting **all** catalogue rows with this compound name. It did not notice that they came from **two different entries** and added them up:

    entry 1: AŠ + AŠ
    entry 2: AŠ + AŠ
    result:  AŠ + AŠ + AŠ + AŠ   ← 4 components instead of 2

Every *didli* in the corpus gave **4 rows**.
|ŠE.NAGA|  gave **6** rows instead of 2. Each extra row counts as an extra sign, so the frequency of AŠ was inflated, most of all where *didli* is frequent (mainly practical texts, Sippar).

## Automatic Fix

**Yes,** The script now takes the components **only from the first entry** of a compound and skips the others:

    |AŠ.AŠ|  →  AŠ + AŠ   (2 rows per token)

**Nothing is lost.**     
The column `same_components_in_all_entries` shows whether all entries give the same components. It is `yes` in **all 40** rows, so taking the first entry is safe.

## Size And Effect On The Corpus

**40** compounds are listed several times in OSL.    
**18** occur in the corpus, with **935** tokens (41 in school texts).     
About **2,377 superfluous rows** disappear from `grapheme.csv`.      
The most frequent: |AŠ.AŠ| (283, *didli*), |ŠE.NAGA| (215), |ZI&ZI.LAGAB| (134), |ANŠE.ARAD| (69).     
The expert only confirms (`CONFIRM`).    

## Size And Effect On The Corpus

40 forms.   
18 in the corpus    
935 tokens.    
About 2,377 superfluous rows disappear from `grapheme.csv`.

## Which Rows To Check (Scope)

All rows with tokens: a quick **confirmation**.

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `entries` | the OSL entries that list the form (sign / form) |
| `components_before / components_after` | rows per token before and after the fix |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## How To Check One Row (Procedure)

1. Check one or two rows in OSL.
2. Write `CONFIRM`.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `CONFIRM` | the fix is right | – |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| compound_form | entries | components_before | components_after | tokens_in_OB_corpus |
|---|---|---|---|---|
| \|AŠ.AŠ\| | \|AN.AŠ.AN\| / \|AŠ.AŠ\|; \|AŠ.AŠ\| / (sign) | 4 | 2 | 283 |
| \|ŠE.NAGA\| | \|AN.ŠE.NAGA\| / \|ŠE.NAGA\|; NAGA / \|ŠE.NAGA\|; \|ŠE.NAGA\| / (sign) | 6 | 2 | 215 |
| \|ZI&ZI.LAGAB\| | \|ZI&ZI.EŠ₂\| / \|ZI&ZI.LAGAB\|; \|ZI&ZI.LAGAB\| / (sign) | 4 | 2 | 134 |
| \|ANŠE.ARAD\| | \|ANŠE.ARAD\| / (sign); \|GIR₃.ARAD\| / \|ANŠE.ARAD\| | 4 | 2 | 69 |
| \|ZI&ZI\| | \|ZI&ZI.A\| / \|ZI&ZI\|; \|ZI&ZI.LAGAB\| / \|ZI&ZI\| | 4 | 2 | 43 |
| \|ZI&ZI.EŠ₂\| | \|A.ZI&ZI\| / \|ZI&ZI.EŠ₂\|; \|ZI&ZI.EŠ₂\| / (sign) | 4 | 2 | 34 |

*These are real rows of the file, not decisions.*
