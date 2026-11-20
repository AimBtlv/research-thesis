# Manual Check v2: How To Work With This Package 
*Prepared 2026-11-18.   
Stage 1, Step 6.0.    
Period: Old Babylonian only.*   

## What This Package Is?

The thesis compares how signs were written in **school** texts and in **practical** texts (letters, contracts, administrative and literary texts), and at which **sites**.     
For this, a Python pipeline turns every reading of the CDLI transliterations (ATF) into a cuneiform sign and its Unicode glyph: *da* → DA 𒁕, *suen* → \|EN.ZU\| 𒂗𒍪.

Most of these decisions come from sign lists (OSL, the syllabary of M. Maiocchi, Diri).      
Some cannot be made by a program: the sources are silent, they disagree, or the right answer depends on philological judgement. This package collects exactly these cases, one problem per file, so that they can be decided by an expert.

## Place In The Workflow 

```
Step 1–4  sign catalogue (scripts 01–06)
Step 5    parsing of the corpus: ATF → atf_tokens.csv → grapheme.csv (07, 08)
Step 6.0  THIS PACKAGE: manual check of the catalogue and of the parser (10)
Step 6    gold standard: manual check of whole tablets
Step 7    annotation of the rest of the corpus
```

Each step is described in `WorkFlowDocumentations/` (`1.doc_…` to `5.doc_…`).    
The MD file of every problem names the document and section it belongs to.

## **Words Used In The Files (Glossary)**

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

## The Files 

Every problem has **two files with the same number**: a CSV with the cases and an MD that explains the problem, the columns, how to check one row and which answers are possible.

The files fall into three kinds of task.

**1. Confirm (short).** The pipeline has already been corrected, please check that the correction is right.
| File | Question | Rows |
|----|---|----|
| **P01** | A modifier was lost when the name was split (\|AB₂×AMAR@t\| → AB₂ + AMAR). Does it matter? | 24 |
| **P02** | Is each of these forms the same sign as the simple sign of the same name? (\|HI×BAD\| = KAM) | 16 |
| **P03** | No source gives a reading of this compound. Is a reading known? | 722 |
| **P04** | A compound appears only inside a longer form. Is it a word of its own? | 53 |
| **P05** | Two readings were joined into a compound on a guess. Is it one compound? (*ra-ra*) | 26 |
| **P06** | Does each of these compounds have the right number of components? (\|AŠ.AŠ\| = 2, not 4) | 40 |
| **P07** | OSL writes a component as `X` / `O`. Which sign is it? (*zimbir*) | 140 | 7 in the corpus | 1,399 (10) |
| **P08** | Two readings were joined into one compound sign, which gives other glyphs. Compound or separate signs? (*eš₁₈-dar*, *um-me-da*) | 9 |
| **P09** | A name from the syllabary has no Unicode sign. Which OSL sign is it? (SIPA, KA.AN.RA) | 31 |
| **P10** | OSL and the catalogue give the same reading to different signs. Which is right? (*uš₂*, *murub₄*, *samag*) | 702 | 
| **P11** | The syllabary and OSL name different signs for the same Unicode character. Which is right? | 18 |
| **P12** | The parser did not recognise this reading. What is it? (*tur₃*, *ginₓ*) | 1,265 |
| **P13** | The program could not split this compound into components. What are they? | 182 |
| **P14** | Control sample: are the components of these compounds right? | 78 |
| **P15** | Is the new glyph of these signs right? (e.g. *da* = 𒁕, not 𒀉) | 30 |


## **How To Read One Row (Example)**

From `P15_wrong_code_of_registered_name.csv`:

| check_id | sign_name | old_glyph | new_glyph | tokens_in_OB_corpus | tokens_school | decision | comment |
|---|---|---|---|---|---|---|---|
| P15-0002 | DA | 𒀉 | 𒁕 | 21,194 | 407 | *CONFIRM* | |

1. The left columns are **computed** and must not be changed.
2. The corpus columns are the same in every file: `tokens_in_OB_corpus` (how often), `tokens_school` / `tokens_practical` (in which texts), `top_sites` (where), `corpus_example` (a tablet and line to open on CDLI).
3. The **empty columns at the right end** are filled in: `decision` always, other columns only if the MD file asks for them.

## Recommended Order

1. **P15, P06, P02**: confirmation, about an hour.
2. **P08, P09, P11**: few rows that affect many tokens.
3. **P10** (the 15 real conflicts at the top), **P05**, **P07** (rows in the corpus).
4. **P14**: if its 30 `@useq` rows contain no error, OSL decompositions are treated as reliable.
5. **P12** (≥ 10 tokens), **P03**, **P04**, **P01** (rows in the corpus).
6. P13 and the optional rows, if there is time.

## Common Rules

1. `decision` takes one value from the list in the MD file of that problem. Anything else goes into `comment`.
2. Order of sources: OSL → Borger MZL → Labat; for readings also Proto-Ea, Ea, Diri. If sign lists disagree, both go into `comment`.
3. If unsure: `UNSURE` with a short reason. An honest "unsure" is better than a guess, because the answers become data of the thesis.
4. When writing about a row, quote its `check_id` (P08-0003).

## What Happens With The Answers 

The filled files are read back by a script (`11_apply_manual_check.py`, to be written after the check). New readings and components enter the catalogue with the source `PROFESSOR`, kept apart from OSL and the syllabary. Decisions about joining or separating readings become rules of the parser. Every change can be traced back to its `check_id`. The pipeline is then run again, and the gold standard (Step 6) checks whole tablets in context.

## What This Check Cannot See

The package checks **types**: catalogue entries and kinds of tokens. Whether *one* reading in *one* line of *one* tablet was turned into the right glyphs depends on its context. That is checked by the gold standard, which compares the glyphs of whole tablets.

## **For The Pipeline (Technical Note)**
