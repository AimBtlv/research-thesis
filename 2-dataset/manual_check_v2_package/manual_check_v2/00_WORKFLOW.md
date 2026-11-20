# **Manual Check v2: Workflow (Ручная проверка v2: порядок работы)**

*Prepared 2026-11-18. Stage 1, Step 6.0. 

## **Why This Check (Why)**

The thesis compares how signs were written in **school** texts and in **practical** texts (letters, contracts, administrative and literary texts), and at which **sites**. For this, a Python pipeline turns every reading of the CDLI transliterations (ATF) into a cuneiform sign and its Unicode glyph: *da* → DA 𒁕, *suen* → \|EN.ZU\| 𒂗𒍪.

Most of these decisions come from sign lists (OSL, the syllabary of M. Maiocchi, Diri). Some cannot be made by a program: the sources are silent, they disagree, or the right answer depends on philological judgement. This package collects exactly these cases, one problem per file, so that they can be decided by an expert.

1. **Errors of the code.** They are fixed automatically.
2. **Questions the sources do not answer** (a missing reading, a placeholder sign, two sign lists that disagree). Code cannot decide them (table B).

## Place In The Workflow

```
Step 1–4  catalogue (01–06)      
Step 5    parsing (07, 08)   
Step 6.1    manual check of catalogue (expert answers), re-run 06–08
Step 6.2    gold standard (tokens)  
Step 7    rules / AI on the corpus
```
Each step is described in `WorkFlowDocumentations/` (`1.doc_…` to `5.doc_…`). The MD file of every problem names the document and section it belongs to.
Documentation of the steps: 
`1.doc_unicode_assign_v3.md` (Step 1),
`3.doc_compound_phonetic_table_v13.md` (Step 3), 
`4.doc_sign_catalogue_v13.md` (Step 4), 
`5.doc_parsing_layer_v14.md` (Step 5).     
[text](../../manual_check_v2_package_v2/manual_check_v2/00_WORKFLOW.md)
Each P-file names the section it belongs to.

| Term | Meaning |
|---|---|
| *simple sign* | one sign with one glyph: DA 𒁕 |
| *compound sign* | a sign made of several signs, written as one unit: \|EN.ZU\| = EN + ZU, read *suen* |
| *component* | one of the signs a compound is made of |
| *modifier* | a mark that changes a sign: `@t` (tenû), `@g` (gunû), `@c` |
| *@useq* | the list of components that OSL gives for a compound |
| *placeholder* | `X`, `O` or `?` where OSL gives no sign for a component |
| *token* | one occurrence of a reading in a tablet |
| *span* | several readings joined by hyphens: *ku₃-babbar* |

| File | Question | Rows | To check | Tokens in the corpus (school) |
|---|---|---|---|---|
| **P01** | modifier lost in a name split | 24 | 1 in corpus | 1 (1) |
 **P02** | Is each of these forms the same sign as the simple sign of the same name? (\|HI×BAD\| = KAM) | 16 |
 | **P03** | No source gives a reading of this compound. Is a reading known? | 722 | 41 in the corpus | 133 (5) |
 | **P04** | A compound appears only inside a longer form. Is it a word of its own? | 53 | 3 in the corpus | 5 (3) |
 | **P05** | Two readings were joined into a compound on a guess. Is it one compound? (*ra-ra*) | 26 | all | 606 (7) |
 | **P06** | Does each of these compounds have the right number of components? (\|AŠ.AŠ\| = 2, not 4) | 40 |
 | **P07** | OSL writes a component as `X` / `O`. Which sign is it? (*zimbir*) | 140 | 7 in the corpus | 1,399 (10) |
 | **P08** | Two readings were joined into one compound sign, which gives other glyphs. Compound or separate signs? (*eš₁₈-dar*, *um-me-da*) | 9 | all | 1,195 (41) |
 | **P09** | A name from the syllabary has no Unicode sign. Which OSL sign is it? (SIPA, KA.AN.RA) | 31 | all | 2,543 (50) |
 | **P10** | OSL and the catalogue give the same reading to different signs. Which is right? (*hi*, *maš*, *lil₂*) | 702 | 42 in the corpus | 13,159 (375) |
 | **P11** | The syllabary and OSL name different signs for the same Unicode character. Which is right? | 18 | all | 21,670 (366) |
 | **P12** | The parser did not recognise this reading. What is it? (*tur₃*, *ginₓ*) | 1,265 | 41 (≥ 10 tokens) | 3,495 (135) |
| **P13** | The program could not split this compound into components. What are they? | 182 | optional | 2 (0) |
| **P14** | Control sample: are the components of these compounds right? | 78 | all | 72,849 (1,021) |
| **P15** | Is the new glyph of these signs right? (e.g. *da* = 𒁕, not 𒀉) | 30 |

## **How To Read One Row (Example)**

From `P15_wrong_code_of_registered_name.csv`:

| check_id | sign_name | old_glyph | new_glyph | tokens_in_OB_corpus | tokens_school | decision | comment |
|---|---|---|---|---|---|---|---|
| P15-0002 | DA | 𒀉 | 𒁕 | 21,194 | 407 | *CONFIRM* | |

1. The left columns are **computed** and must not be changed.
2. The corpus columns are the same in every file: `tokens_in_OB_corpus` (how often), `tokens_school` / `tokens_practical` (in which texts), `top_sites` (where), `corpus_example` (a tablet and line to open on CDLI).
3. The **empty columns at the right end** are filled in: `decision` always, other columns only if the MD file asks for them.



## Common Rules

1. `decision` takes one value from the list in the MD file of that problem. Anything else goes into `comment`.
2. Order of sources: OSL → Borger MZL → Labat, for readings also Proto-Ea, Ea, Diri. If sign lists disagree, both go into `comment`.
3. If unsure: `UNSURE` with a short reason.
4. When writing about a row, quote its `check_id` (P08-0003).

## What Happens With The Answers

The filled files are read back by a script (`11_apply_manual_check.py`, to be written after the check). New readings and components enter the catalogue with the source `PROFESSOR`, kept apart from OSL and the syllabary. Decisions about joining or separating readings become rules of the parser. Every change can be traced back to its `check_id`. The pipeline is then run again, and the gold standard (Step 6) checks whole tablets in context.

## What This Check Cannot See 

The package checks **types**: catalogue entries and kinds of tokens. Whether *one* reading in *one* line of *one* tablet was turned into the right glyphs depends on its context. That is checked by the gold standard, which compares the glyphs of whole tablets.

## For The Pipeline (Technical Note)

The CSV files are built by `10_build_manual_check.py` from the pipeline outputs of 2026-11-14. After a new run (`python3 00_run_pipeline.py --from 06`), script 10 rebuilds them; corrected cases then disappear from the lists. What was corrected in the code and why is documented in `3.doc_…`, `4.doc_…` and `5.doc_…`, sections *Changes v13.1* and *Changes v14.4 / v14.5*.
