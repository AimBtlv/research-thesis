# P03. Compound Without An Attested Reading 

*File: `P03_no_attested_reading.csv`   
723 rows    
Check_id `P03-0001`–`P03-0723`.     
The outputs of 2026-11-22*

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard).     
Documented in `3.doc_compound_phonetic_table_v13.md`     
Step 3 (`NO_ATTESTED_READING`)      
Script `06_build_sign_catalogue_v13.py`

## The Problem 
The reading of a compound sign is how the **whole combination** was pronounced as one word, not each sign separately. |EN.ZU| consists of EN and ZU, but it is read *suen* (the Moon god), not *en-zu*. Such a reading cannot be guessed from the parts, it must come from a source.
*Where the pipeline looks.*     
Script 06 checks the sources in a fixed order and takes the **first** reading it finds:

    1. OSL @v  →  2. Diri  →  3. OGSL  →  4. Syllabary_CM

A compound with a reading in at least one of them gets the status `ATTESTED_DIRECT`.   
The compounds of this file have a reading in **none** of the four
sources (`NO_ATTESTED_READING`). Example: |DUR₂&DUR₂| ("two DUR₂ joined into
one sign"). OSL knows the sign and its components, but not how it was read.

This is **not an error of the code**: the program worked correctly, the sources
are simply silent. An expert view is needed who knows the wider literature (MZL, Labat,
Proto-Ea, Ea, ePSD2). The answers will enter the data as a **new, fifth source** `PROFESSOR`, kept apart from the others.    
*Note:* The column `component_reading_inferred` (*dur2-dur2*, *amar-amar*) is a
**guess** of the program that joins the first reading of every component. It is
for orientation only, not a fact.

## Automatic Fix 

**Partly (06 v13.1).**

*Fix 1: "hidden" OSL readings.* Sometimes OSL has **two entries with the same
name**. The old script kept only the last one and lost the `@v` of the first.
It now collects the readings of all entries of that name, e.g. |HI×MAŠ| gets
*surₓ | šurₓ*. Such compounds (|HI×MAŠ|, |LAGAB×AŠ@c|) now have a reading and
are no longer in this file.

*Fix 2: false "nesting".* A compound without a reading used to be tested for
being part of a longer name (`NESTED_IN_LONGER_FORM`, see P04). The test
compared **letters**, so |A.BU| was "found" inside SI.A.BUR₂, although BU and
BUR₂ are **different signs**, and |AMAR&AMAR| was "found" inside **itself**.
The test now compares whole components. 37 compounds (36 accidental matches +
|AMAR&AMAR|) lost the wrong status and are in this file.

## Size And Effect On The Corpus 

723 compounds (the catalogue is deliberately broader than the corpus and covers
all periods). Only **41** occur in the Old Babylonian corpus, with **133**
tokens (5 in school texts). 

## **Which Rows To Check (Scope)**
Rows in the corpus (the first rows of the file): **mandatory**. The rest: optional.

## Columns

| Column | Meaning |
|---|---|
| `component_reading_inferred` | guess only, for orientation (see P05) |
| `auto_fix` | what script 06 changed for this row; empty when the catalogue already contains the fix, as in this run |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**
1. Look the compound up in MZL / Labat, for Sumerian words also Proto-Ea, Ea, Diri and ePSD2.
2. Open `corpus_example`: is the compound read as one word or sign by sign?
3. Write the reading in ATF notation with subscript index (several: ` | `) and the reference in `source` (`MZL 892`).

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `READING` | a reading is known | `reading_by_professor` + `source` |
| `READ_BY_COMPONENTS` | read as separate signs | – |
| `GRAPHIC_ONLY` | a graphic form without its own reading | – |
| `NO_READING_KNOWN` | no reading known | – |
| `NAME_ERROR` | the name is wrong | explain in `comment` |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| compound_form | components_names | tokens_in_OB_corpus | tokens_school | auto_fix |
|---|---|---|---|---|
| \|DUR₂&DUR₂\| | DUR₂ + DUR₂ | 29 | 0 |  |
| \|AMAR&AMAR\| | AMAR + AMAR | 15 | 0 |  |
| \|GU&GU\| | GU + GU | 15 | 0 |  |
| \|AB₂×MU\| | AB₂ + MU | 12 | 0 |  |
| \|NE.NE\| | NE + NE | 11 | 0 |  |
| \|U.GA₂\| | U + GA₂ | 4 | 0 |  |

*These are real rows of the file, not decisions.*
