# **P11. Syllabary And OSL Name Different Signs (Расхождения силлабария и OSL)**

*File: `P11_syllabary_osl_disagreements.csv`, 18 rows, check_id `P11-0001`–`P11-0018`. Built by `10_build_manual_check.py` from the outputs of 2026-11-14 (pipeline v14.4).*

## **Place In The Workflow (Место в workflow)**

Stage 1, Step 6.0 (manual check before the gold standard). Documented in `1.doc_unicode_assign_v3.md`, Step 1.2, *Correction: OSL decides which sign it is*; script 02.

## **The Problem (Проблема)**

For 18 Unicode signs the syllabary and OSL name different signs (duh → GABA, ti₂ → HI …). Version 1.2 lets OSL decide. The decision should be checked against MZL, because it moves thousands of tokens (gaba → GABA 2,504).

## **Automatic Fix (Автоматическое исправление)**

**Already decided automatically (02 v1.2): OSL wins.** The check confirms or rejects this rule sign by sign.

## **Size And Effect On The Corpus (Объём)**

18 signs; 9 in the corpus, 21,670 tokens.

## **Which Rows To Check (Scope)**

All rows: **mandatory**.

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `syllabary_sign / osl_sign / step1_decision` | the two names and what Step 1.2 did |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Compare with MZL (and Labat if needed).
2. Write the decision.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `CONFIRM_OSL` | OSL is right | – |
| `USE_SYLLABARY` | the syllabary is right | reason |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| syllabary_sign | osl_sign | step1_decision | tokens_in_OB_corpus |
|---|---|---|---|
| GAR.IB | ARKAB₂ | syllabary sign ARKAB2 (= OSL name) used | 1 |
| GABA | DUH | not matched: described from OSL in Step 1.3 | 2504 |
| HI×U | \|ŠAR₂×U\| | not matched: described from OSL in Step 1.3 | 0 |
| LAGAB×GUD+GUD | \|LAGAB×(GUD&GUD)\| | not matched: described from OSL in Step 1.3 | 906 |
| MA×TAK4 | \|MA@g×TAK₄\| | not matched: described from OSL in Step 1.3 | 0 |
| ŠIR@t | NU₁₁@t | syllabary sign NU11@t (= OSL name) used | 0 |

*These are real rows of the file, not decisions.*
