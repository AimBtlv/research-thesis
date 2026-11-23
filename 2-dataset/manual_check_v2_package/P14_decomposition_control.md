# P14. Control Sample Of The Decompositions

*File: `P14_decomposition_control.csv`     
72 rows     
Check_id `P14-0001`–`P14-0072`     
The outputs of 2026-11-22 (pipeline v14.5)*

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard).      
Documented in `4.doc_sign_catalogue_v13.md` § 4; `5.doc_parsing_layer_v14.md` § 13     
Scripts: `06_build_sign_catalogue_v13.py`,`08_tokens_to_grapheme_v14.py`

## The Problem 

This file is not a problem but a **control sample**: it checks whether the
components of compound signs are recorded correctly. In `grapheme.csv` a
compound is written as one row per component (|EN.ZU| → EN 𒂗 + ZU 𒍪).    
The components come from one of two places:

| Source | Decided by | Example |
|---|---|---|
| OSL `@useq` | the editors of OSL: code points given directly | \|EN.ZU\|: `@useq x12097.x1236A` |
| name split | our script: cuts the name at × / & | \|KA×ŠU\| → KA + ŠU |

P01, P06, P07 and P13 found specific errors. To judge whether the **rest** is
right, a sample is checked instead of all 2,380 compounds.

*Part B: all name splits in the corpus* (42 rows, 390 tokens).    
The script is trusted less than OSL, so every case is checked.     
Forms that are registered signs of their own (P02: |HI×BAD| = KAM, |KA×ŠU|, |ZI&ZI| …) are simple signs and are not split, so they are not in this part.

*Part C: a sample of OSL.*       
The corpus has **480** compounds with `@useq`, **79,850** tokens.    
The **30** most frequent (part C) cover **76.6 %** of these tokens: |EN.ZU| (*suen*, 13,295), |KU₃.UD| (*kubabbar*, 5,868), |A.AN| (5,643), |EN.KID| (*enlil*, 4,447), |AMAR.UD| (*marduk*, 3,552) …

If part C contains no error, `@useq` is accepted as reliable for the other 450
compounds.      
This is an assumption, not a proof: a rare compound can still be
wrong, but rare compounds hardly affect the counts, and the visible errors
(placeholders, duplicates) are already in P06 and P07.

## Automatic Fix 

**No**: this file is the check of the automatic decompositions. Rows with
placeholders (P07) are not repeated here.

## Size And Effect On The Corpus 

72 rows (B: 42; C: 30), 61,591 tokens (904 in school
texts). All rows are mandatory: they are the sample.

## Which Rows To Check (Scope)

All rows: **mandatory** (sample).

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `part` | B = name split in the corpus, C = @useq sample |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Compare `components_names` with OSL / MZL.
2. Same signs and order → OK.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `OK` | the split is right | – |
| `WRONG_COMPONENT` | a component is another sign | `correct_components` |
| `WRONG_ORDER` | wrong order | `correct_components` |
| `MODIFIER_LOST` | a modifier matters | `correct_components` |
| `SIMPLE_SIGN` | should not be split | name / code |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| compound_form | part | components_names | glyph | tokens_in_OB_corpus |
|---|---|---|---|---|
| \|EN.ZU\| | C (@useq sample) | EN + ZU | 𒂗𒍪 | 13295 |
| \|KU₃.UD\| | C (@useq sample) | KU₃ + UD | 𒆬𒌓 | 5868 |
| \|A.AN\| | C (@useq sample) | A + AN | 𒀀𒀭 | 5643 |
| \|EN.KID\| | C (@useq sample) | EN + KID | 𒂗𒆤 | 4447 |
| \|AMAR.UD\| | C (@useq sample) | AMAR + UD | 𒀫𒌓 | 3552 |
| \|AN.NA\| | C (@useq sample) | AN + NA | 𒀭𒈾 | 3331 |

*These are real rows of the file, not decisions.*
