# P10. OSL And Catalogue Give A Reading To Different Signs 

*File: `P10_osl_reading_conflicts.csv`   
702 rows     
Check_id `P10-0001`–`P10-0702`      
The outputs of 2026-11-14*

## Place In The Workflow

Stage 1, Step 6.0 (manual check before the gold standard). 
Documented in `4.doc_sign_catalogue_v13.md` § 6 *Gap filling from OSL @v* (`osl_reading_conflicts_v13.csv`).    
`1.doc_unicode_assign_v3.md` (702 conflicts).    
Script: `06_build_sign_catalogue_v13.py`

## The Problem 

*Where the conflicts come from?*      
Readings of simple signs come mostly from the syllabary, OSL `@v` values only **fill gaps** (Step 4, Stage 5). Before adding an OSL reading, `script 06` checks whether another sign of the catalogue already has it. If so, nothing is changed and the case is written to
`osl_reading_conflicts_v13.csv` (702 rows).     

Example: *murub₄* ("middle") is a value of MURUB₄ in OSL, of NISAG in the catalogue. The column `parser_resolves_to` shows the sign the parser actually uses (NISAG, 79 times).

*Most conflicts are not real.* OSL sometimes lists a reading **both under a sign
and under one of its `@form` variants**:

    @sign HI        @v hi     ← the main sign
      @form DIN     @v hi     ← a variant inside the sign HI

The script saw *hi* at HI in the catalogue and at DIN in OSL and recorded a
conflict, but DIN is a variant of HI itself: one sign, nothing to change.

The new column `relation` tells the cases apart:

| `relation` | Meaning | Conflicts | Tokens |
|---|---|---|---|
| `different signs` | really different signs | 400 | 979 |
| OSL sign is a @form of the catalogue sign | variant (*hi*, *maš*, *lil₂*) | 263 | 12,111 |
| catalogue sign is a @form of the OSL sign | the reverse | 38 | 69 |
| both are @forms of one sign | | 1 | 0 |


*Real conflicts in the corpus (15 signs)*:    
 *uš₂* (OSL TIL, catalogue UŠ₂, 608),       
 *murub₄* (MURUB₄ / NISAG, 79),     
 *samag* (DUB / UM, 78, **all in school texts**),     
 *di₂* and *ti₂* (TI₂ / HI, 70 and 19, the same problem as *ti₂* in Step 1.2,
see P11).

## Automatic Fix

**No.**     
Choosing between sign lists is philology. Script 10 only adds the
column `relation` and sorts the file.

## Size And Effect On The Corpus

702 conflicts     
42 readings occur in the corpus.     
13,159 tokens. 
Real conflicts between different signs: 400, of them **15** in the corpus with **979** tokens (92 in school texts).     
The 15 real conflicts are mandatory.    
Variant cases need only a quick look (usually `SAME_SIGN`).

## **Which Rows To Check (Scope)**

Rows in the corpus: **mandatory**, the 10 rows with ≥ 100 tokens first. The rest: optional.

## Columns 

| Column | Meaning |
|---|---|
| `osl_sign / catalogue_sign` | the two candidates |
| `parser_resolves_to` | sign used by the parser and how often |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Look the reading up in OSL and MZL.
2. If the conflict comes from h / ḫ (or ş / ṣ), write `NORMALISATION`.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `KEEP_CATALOGUE` | the catalogue sign is right | – |
| `USE_OSL` | the OSL sign is right | – |
| `NORMALISATION` | an artefact of the letter normalisation | explain |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| reading | osl_sign | catalogue_sign | parser_resolves_to | tokens_in_OB_corpus |
|---|---|---|---|---|
| hi | DIN | HI | HI 7911 | 7911 |
| maš | MAŠ@t | MAŠ | MAŠ 1189 | 1189 |
| lil₂ | E₂ | KID | KID 855 | 855 |
| uš₂ | TIL | UŠ₂ | UŠ₂ 608 | 608 |
| lamma | GURUŠ | KAL | KAL 342 | 342 |
| kar₂ | GAN₂ | GAN₂@t | GAN₂@t 313 | 313 |

*These are real rows of the file, not decisions.*
