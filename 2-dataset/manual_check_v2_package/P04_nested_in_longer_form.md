# P04. Compound Nested In A Longer Form 

*File: `P04_nested_in_longer_form.csv`    
53 rows     
Check_id `P04-0001`–`P04-0053`     
The outputs of 2026-11-22*

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard)     
Documented in `3.doc_compound_phonetic_table_v13.md`    
Step 3 (`NESTED_IN_LONGER_FORM`)     
Script `06_build_sign_catalogue_v13.py`

## The Problem
A compound is **nested** if it occurs, sign by sign, inside the
name of a longer compound. |DUG.SILA₃.BUR| (DUG + SILA₃ + BUR) occurs inside
DUG.SILA₃.BUR.NA. The long name has a reading in the syllabary, the short one
has none of its own (status `NESTED_IN_LONGER_FORM`).

*Why it matters.* There are two possibilities:
1. the short compound is a **word of its own** whose reading is simply not
   recorded.    
2. it is **only a part** of the longer word (e.g. the longer word is broken or
   abbreviated on the tablet).

For counting signs these are different: in the first case it is a unit of its
own, in the second it is not.

*Where the error was.* The old script compared names **as strings of letters**:
"do the letters A.BU occur inside another name?". This gave false matches:

| Short compound | "Found" inside | Why this is wrong |
|---|---|---|
| \|A.BU\| | SI.A.BUR₂ | the letters are there, but the sign is BUR₂, not BU |
| \|GU&GU\| | a name with GU.GU | `&` (joined signs) and `.` (signs side by side) are different |
| \|AMAR&AMAR\| | \|AMAR&AMAR\| | the compound was "found" inside **itself** |

## Automatic Fix **

**Partly** A name is now first split into **signs and operators** (`.`, `×`, `&`, `+`), and whole signs are compared:

    A.BU       →  A . BU
    SI.A.BUR₂  →  SI . A . BUR₂     →  BU ≠ BUR₂: not nested

A compound can no longer be nested in itself.

*Result:* of 90 rows, 37 left this file (36 accidental matches and
\|AMAR&AMAR\|) they are now in P03 (compounds without a reading). **53** rows
remain where the match is real, e.g. \|GI&GI\| inside \|GI&GI&GI\| and
\|HI.SUHUR\| inside \|GA₂~a×(HI.SUHUR)\|.

*Why only "partly".* The program now answers correctly *whether* the short
compound is part of the longer one. *Whether it is a word of its own* is a
philological question: dictionaries (MZL, Labat, lexical lists) and the context
on the tablet decide.

## Size And Effect On The Corpus 

53 compounds
Only **3** occur in the Old Babylonian corpus with **5** tokens.    
3 in school texts: \|DUG.SILA₃.BUR\| (3, Nippur), \|AB₂×GUD\| (1) and
\|GA₂×DIM\| (1).      
The effect on the thesis is minimal, only these 3 rows are mandatory.

## Columns (Columns)
| Column | Meaning |
|---|---|
| `nested_in_forms` | up to five longer syllabary names that contain the compound as whole components |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Compare the compound with each name in `nested_in_forms`.
2. Look it up in MZL / Labat / lexical lists.
3. Open `corpus_example`: a word of its own, or a broken / abbreviated longer form?

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `INDEPENDENT` | independent word | reading + source if known |
| `PART_OF_LONGER` | only a part of the longer form | – |
| `ACCIDENTAL_MATCH` | the match is still accidental | – |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| compound_form | nested_in_forms | tokens_in_OB_corpus |
|---|---|---|
| \|DUG.SILA₃.BUR\| | DUG.SILA3.BUR.NA | 3 |
| \|AB₂×GUD\| | NUNUZ.AB2×GUD | 1 |
| \|GA₂×DIM\| | GA2×DIM×ŠE | 1 |
| \|(ŠE.NUN&NUN)&(ŠE.NUN&NUN).GAD&GAD\| | (ŠE.NUN&NUN)&(ŠE.NUN&NUN).GAD&GAD.GAR&GAR | 0 |
| \|A.PA.GISAL\| | A.PA.GISAL.PAD.SI.A | 0 |
| \|A.SI\| | LAK589.A.SI | 0 |

*These are real rows of the file, not decisions.*
