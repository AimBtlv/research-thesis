# P15. Registered Name Took The Code Of Another Sign 

*File: `P15_wrong_code_of_registered_name.csv`.   
30 rows.   
Check_id `P15-0001`–`P15-0030`.   
The outputs of 2026-11-22*.   

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard).    
Documented in `5.doc_parsing_layer_v14.md` § 10 *Sign Identity Of Variants* (v13).   
Script `08_tokens_to_grapheme_v14.py`.    
 
## The Problem

**The largest error found.** For 30 frequent signs the parser stored the
**glyph of another sign** in `grapheme.csv`: *da* got 𒀉 (A₂) instead of
𒁕 (DA), *ri* got 𒄷 (HU) instead of 𒊑.

*Registered sign.* In this pipeline a sign is **registered** if it has its own
`@sign` entry in OSL (a catalogue row without `osl_form`). A sign can also
stand in OSL as a **variant** (`@form`) inside another sign:

| Where in OSL | What it is | Code point |
|---|---|---|
| `@sign DA` | its own entry | **U+12055** 𒁕 |
| `@form DA` inside A₂ | a variant of A₂ | none of its own |

*Inherited code point.*    
A form without a code point receives the code point of
its parent (`structural_hint = inherited_from_parent`): the form DA inside A₂
got U+12009 𒀉 (A₂).

*The change of v13.*      
A variant that is a registered sign of its own is resolved
under its own name (MAŠ₂, not its parent KUN). This rule is right.

*Where the error arose?*      
Step 5.2 (script 08) then took the code point of the **first** catalogue row with this name. 
The entry A₂ comes before the entry DA in OSL, so the first row was the form DA **with the inherited code of A₂**:

    code for DA?
      1st row named DA: @form DA inside A₂ → U+12009 𒀉 (A₂)   ← taken
      2nd row:          @sign DA          → U+12055 𒁕 (DA)   ← right

The same happened to 30 names:    
RI (23,554 tokens, code of HU)     
DA (21,194,A₂)     
NAM (11,448, BURU₅)   
DUN₃@g (4,926)     
KAL (2,571, GURUŠ)    
PAP (1,790, DIŠ)    
U (1,398, DIŠ) ....

*Why it was not seen?*     
The reading (*da*) and the sign name (DA) were right.    
Only the glyph and the code point were wrong.     
The gold check of v14.4 compared the **function** and the name of the sign, not the glyphs. The gold standard must therefore compare **glyph sequences**.

## Automatic Fix 

**Yes**: A registered name now takes the code point of **its own** row: *da* → DA → U+12055 𒁕.

## Size And Effect On The Corpus 

30 names
**74,102** tokens  of the rows of `grapheme.csv`.   
**1,428** in school texts.   
72,674 in practical texts. 
Every count by glyph (inventories, Jaccard index, frequencies) was affected: the data contained signs (A₂, HU, BURU₅) that are not in these words, and the real DA, RI, NAM
were undercounted by thousands. 
The expert compares `old_glyph` and `new_glyph` and writes `CONFIRM`.

## **Which Rows To Check (Scope)**

All rows: a quick **confirmation** (compare `old_glyph` and `new_glyph`).

## **Columns**

| Column | Meaning |
|---|---|
| `old_unicode_id / old_glyph / old_taken_from` | the wrong code and the row it came from |
| `new_unicode_id / new_glyph` | the code of the sign's own row |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Check that `new_glyph` is the sign of the reading (da = 𒁕).
2. Write `CONFIRM`.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `CONFIRM` | the fix is right | – |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| sign_name | old_glyph | old_taken_from | new_glyph | tokens_in_OB_corpus | tokens_school |
|---|---|---|---|---|---|
| RI | 𒄷 | HU / @form RI | 𒊑 | 23554 | 421 |
| DA | 𒀉 | A₂ / @form DA | 𒁕 | 21194 | 407 |
| NAM | 𒉅 | BURU₅ / @form NAM | 𒉆 | 11448 | 212 |
| DUN₃@g | 𒂅 | DUN₃ / @form DUN₃@g | 𒂆 | 4926 | 54 |
| KAL | 𒄨 | GURUŠ / @form KAL | 𒆗 | 2571 | 80 |
| PAP | 𒁹 | DIŠ / @form PAP | 𒉽 | 1790 | 46 |

*These are real rows of the file, not decisions.*
