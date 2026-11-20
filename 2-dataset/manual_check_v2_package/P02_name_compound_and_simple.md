# P02. Name Is Both A Compound And A Simple Sign 

*File: `P02_name_compound_and_simple.csv`,    
16 rows    
Check_id `P02-0001`–`P02-0016`     
The outputs of 2026-11-14.*

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard).     
Documented in `4.doc_sign_catalogue_v13.md`.      
Step 4/2–4    
Script `06_build_sign_catalogue_v13.py`.

## The Problem 
In OSL every sign has a main entry `@sign`. Inside it there can be
`@form` entries: **variants** of this sign (other shapes or other names of the
same graphic unit). The main sign usually has its own Unicode code point, a form
often has none.

*What is special here.*
Take |HI×BAD|: "the sign HI with BAD written inside it".
OSL lists it **twice**:

| Where in OSL | What it is | Code point |
|---|---|---|
| `@sign HI×BAD` (its own entry) | the simple sign KAM | **U+12130**  |
| `@form HI×BAD` inside HI×AŠ | a variant of HI×AŠ | none |

*Where the error arose.*     
While reading the entry |HI×AŠ|, the old script reached
the form |HI×BAD|. The form has no code point, so the script cut its name at `×`
as if it were a compound: |HI×BAD| → HI + BAD.     
The catalogue then held **the same sign twice**: once as the simple sign KAM (U+12130), once as the compound HI + BAD with two glyphs.

## Automatic Fix

Before cutting a form into pieces, the script now checks whether OSL has a main sign with **exactly the same name and its own code point**. If so, the form takes that code point and is treated as a simple sign:

    @form |HI×BAD|  →  KAM, U+12130   (instead of HI + BAD)

Such rows are marked `structural_hint = uid_via_same_name_sign` ("code point
taken from the sign of the same name"). The 13 forms are no longer compounds and
leave the compound reading table.

## Size And Effect On The Corpus

16 rows for 13 forms: some forms stand inside **two** entries (|HI×AŠ| and
|HI×DIŠ| under |HI×BAD| and under TE; |ZI&ZI| under |ZI&ZI.A| and
|ZI&ZI.LAGAB|).

For the corpus **nothing changes**: the parser already used the simple sign
(all 11,512 tokens of |HI×BAD| in the Old Babylonian texts were KAM, U+12130).
The fix **cleans the catalogue**, which no longer describes one sign in two
contradictory ways. The expert only confirms that each form and the main sign
are really the same sign (`CONFIRM` or `REJECT`).

## Which Rows To Check (Scope)

All rows: a quick **confirmation**.

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `old_components` | how the form was split before |
| `new_unicode_id` | the code point it takes now |
| `check_id` | row id (P01-0001 …), quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## How To Check One Row (Procedure)

1. Check in OSL that the form is the same sign as the `@sign` of the same name.
2. Write `CONFIRM` or `REJECT`.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `CONFIRM` | same sign, the fix is right | – |
| `REJECT` | a different sign: undo the fix for this form | reason in `comment` |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| osl_form | parent_sign | old_components | new_unicode_id | tokens_in_OB_corpus |
|---|---|---|---|---|
| \|AB×NUN@t\| | \|AB×AŠ₂\| | AB + NUN@t | U+12480 | 0 |
| \|AB₂×TAK₄\| | \|AB₂×GAN₂@t\| | AB₂ + TAK₄ | U+1201B | 0 |
| \|LAGAB×HA\| | \|GA₂×(A.DA.HA)\| | LAGAB + HA | U+121C8 | 0 |
| \|GA₂×IGI@g\| | \|GA₂×(IGI@g.ME)\| | GA₂ + IGI@g | U+120D6 | 0 |
| \|HI×BAD\| | \|HI×AŠ\| | HI + BAD | U+12130 | 11512 |
| \|HI×AŠ\| | \|HI×BAD\| | HI + AŠ | U+1212E | 18 |

*These are real rows of the file*
