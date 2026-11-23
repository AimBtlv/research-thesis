# P07. Placeholder Components X / O / ? 

*File: `P07_placeholder_components.csv`     
140 rows, check_id `P07-0001`–`P07-0140`     
The outputs of 2026-11-22*

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard).         
Documented in `4.doc_sign_catalogue_v13.md` § Note on 'X' `5.doc_parsing_layer_v14.md` § 7, § 13.    
Scripts: `07_parse_atf_to_tokens_v14.py`,`08_tokens_to_grapheme_v14.py`

## The Problem 
*How OSL records components?*       
`@useq` is the line of OSL that lists the components of a compound as **Unicode code points**, separated by dots. The pipeline takes the codes for `grapheme.csv` from it.

*What a placeholder is?*      
A placeholder is `X` or `O` in `@useq` **instead of a code point**. OSL uses it for a component that has **no code point in Unicode**. Example, *zimbir* (the city of Sippar):

    @form |UD.(GIŠ%GIŠ)@g.AN|
    @useq  x12313 . X . x1202D
           UD       ?    AN

The middle component (GIŠ%GIŠ)@g has no code point of its own.

*Error 1: the placeholder was counted as a code.*      
Script 08 copied `X` into the column `unicode_id` of `grapheme.csv`. The count of "rows with Unicode" took `X` for a code point, and a count of signs would have shown a "sign X" that does not exist.     
Almost all cases come from practical texts (*zimbir*: Sippar, 887 of
1,145), so the error created a false difference between school and practice.

*Error 2: ni-ir was merged into a compound.* OSL has

    @sign |NA₂.X|
    @useq  x1223F . O
    @v     ni-ir

The parser looks for attested readings of compounds in ATF words. In Akkadian
texts it found *ni-ir* (ordinary syllables *ni* + *ir*), matched it with the
value of |NA₂.X| and merged the two readings into **one compound**. Instead of
NI 𒉌 and IR 𒅕 the data received NA₂ and the placeholder `O`.

## Automatic Fix 

**Partly.**

1. **07 v14.4 (fix P08a):** a reading made of **several syllables joined by
   hyphens** is no longer merged into a compound with a placeholder:
   *ni-ir* = NI + IR.
2. **08 v14.5 (fix P07):** a placeholder is no longer stored as a code point.
   The row of the component stays (there is a sign on the tablet), but its
   `unicode_id` is empty:

       before: zimbir → U+12313 | X       | U+1202D
       after:  zimbir → U+12313 | (empty) | U+1202D

*Why only "partly".* The code now says honestly *"there is a sign here, but no
code point for it"*. *Which* sign it is cannot be decided by the program: e.g.
can the middle component of *zimbir* (usually written UD.KIB.NUN) be written
with existing code points? That is for the expert.

## Size And Effect On The Corpus 

140 forms
6 occur in the corpus 
1,152 tokens (3 in school texts), almost all practical texts. *ni-ir* (|NA₂.X|, 247 tokens) is no longer among them, because it is now read NI + IR (fix 1). 

## **Which Rows To Check (Scope)
Rows in the corpus: **mandatory**. The rest: optional.

## Columns 

| Column | Meaning |
|---|---|
| `osl_v` | the `@v` value(s) of the compound in OSL |
| `auto_fix` | what 07 / 08 now do |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Look the compound up in OSL / MZL: which sign is the placeholder?
2. For *zimbir*: compare with the usual writing UD.KIB.NUN.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `SIGN_KNOWN` | the placeholder is a known sign | `correct_components` required |
| `SEPARATE_SIGNS` | the span is a sequence of signs (ni-ir) | – |
| `NOT_IDENTIFIED` | the sign is really unidentified | – |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| compound_form | components_names | osl_v | tokens_in_OB_corpus | top_sites |
|---|---|---|---|---|
| \|UD.(GIŠ%GIŠ)@g.AN\| | UD + ? + AN | zimbir | 1145 | Sippar-Yahrurum 887, Sippar-Amnanum 111, (empty) 108, uncertain 11 |
| \|NUNUZ.AB₂×TAB\| | NUNUZ + ? | lahtanₓ | 3 | Nippur 3 |
| \|EN.DAG.NUN.X\| | EN + DAG + NUN + ? | enkumₓ | 1 | Isin 1 |
| \|LAGAR@g&LAGAR@g.LAGAR@g&LAGAR@g.LAGAR@g&LAGAR@g\| | ? + ? + ? |  | 1 | Nippur 1 |
| \|NUNUZ.AB₂×NI\| | NUNUZ + ? |  | 1 | Nippur 1 |
| \|NUNUZ.AB₂×X\| | NUNUZ + ? | huburₓ \| mudₓ \| xdiₓ \| xgidaₓ | 1 | Nippur 1 |

*These are real rows of the file, not decisions.*
