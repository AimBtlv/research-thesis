# P05. Guessed Readings Used By The Parser 

*File: `P05_inferred_matches.csv`      
26 rows      
Check_id `P05-0001`–`P05-0026`      
The outputs of 2026-11-22*     

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard).     
Documented in:     
`3.doc_compound_phonetic_table_v13.md` § 5 and     
`5.doc_parsing_layer_v14.md` § 7.     
Scripts:     
`06_build_sign_catalogue_v13.py`     
`07_parse_atf_to_tokens_v14.py`

## The Problem
`component_reading_inferred` is a column in which the program
builds a "reading" of a compound itself: it takes the **first** reading of every
component and joins them with a hyphen.     
Example: |EN.ZU| = EN + ZU, the first reading of EN is *adₓ(en)*, of ZU *ka₁₄*, giving *adx(en)-ka14*. The real reading is *suen* (the Moon god).

*Why the guesses cannot be trusted.* Compound signs exist precisely because
their reading **cannot be derived** from the parts. Of 1,528 comparable cases,
the guess equals an attested reading only **twice**. The column is therefore
not data, only orientation.

*New finding: the parser uses the guesses.* Script 07 reads a word in two
passes:
1. the first pass looks for **attested** readings of compounds (OSL, Diri,
   OGSL, syllabary);
2. the second pass compares what is left with the **guesses**
   (`inferred_compound_dict`).

So ATF *ra-ra* (two readings) matches the guess *ra-ra* of |RA.RA|, and the
parser stores **one compound** |RA.RA| with `confidence = inferred`. This file
lists exactly these matches.

## Automatic Fix 

**No Automatic Fix.** *ra-ra*, *bu-bu*, *du₆-du₆* can be understood in two ways:

| Option | Meaning | Example |
|---|---|---|
| two separate signs | ordinary repetition (reduplication) | *ra* + *ra* |
| one compound sign | the scribe wrote a special two-part sign | \|RA.RA\| |

This is a decision about the **reading**, not something the program can decide.
Note that the editor wrote *bu-bu* with a hyphen, i.e. as **two signs**; merging
it into |BU&BU| (`&` = ligature, two signs fused into one) may contradict the
edition itself.

*What changes and what does not.* In all 26 cases the **glyphs are the same**
either way: |RA.RA| is stored as RA + RA, the same glyphs 𒊏𒊏 as two separate
*ra*. Sign and glyph counts do not change; the number of **reading units**
does (one compound or two simple signs, and whether |RA.RA| appears as a type
of its own).

## **Size And Effect On The Corpus (Объём)**

26 token types, **606** tokens, only **7** in school texts. The most frequent:
*ra-ra* → |RA.RA| (186), *bu-bu* → |BU&BU| (126), *du₆-du₆* →
|LAGAR@g&LAGAR@g| (54), *gab₂-bu* → |KAB.BU| (44). All rows are mandatory.

In addition, one decision about the whole column `component_reading_inferred`
(remove it, replace it by sign names such as *EN-ZU*, use another reading, or
keep it). This decides whether the second pass of the parser stays active.





## **Size And Effect On The Corpus (Объём)**

26 token types, 606 tokens (7 in school texts).

## **Which Rows To Check (Scope)**

All rows (**mandatory**, short). In addition one decision about the whole column `component_reading_inferred` (options A–D of the earlier file 5: remove, sign names, basic reading, keep).

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `raw_atf_token / resolved_compound` | the ATF span and the compound the guess gave |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Read the span in its context (`corpus_example`).
2. One word written with a compound sign, or a sequence of separate signs (reduplication, syllables)?

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `COMPOUND_OK` | the merge is right | – |
| `SEPARATE_SIGNS` | the readings are separate signs: stop the merge | – |
| `OTHER` | another compound or reading | `correct_reading_or_signs` |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| raw_atf_token | resolved_compound | components_names | tokens_in_OB_corpus | tokens_school |
|---|---|---|---|---|
| ra-ra | \|RA.RA\| | RA + RA | 186 | 5 |
| bu-bu | \|BU&BU\| | BU + BU | 126 | 0 |
| du6-du6 | \|LAGAR@g&LAGAR@g\| | LAGAR@g + LAGAR@g | 54 | 0 |
| gab2-bu | \|KAB.BU\| | KAB + BU | 44 | 0 |
| du12-du12 | \|TUK.TUK\| | TUK + TUK | 32 | 0 |
| ar3-ar3 | \|HI×AŠ₂.HI×AŠ₂\| | \|HI×AŠ₂\| + \|HI×AŠ₂\| | 31 | 0 |

*These are real rows of the file, not decisions.*
