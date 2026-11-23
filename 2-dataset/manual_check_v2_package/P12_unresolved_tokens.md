# P12. Unresolved Tokens 
*File: `P12_unresolved_tokens.csv`.   
1263 rows.    
Check_id `P12-0001`–`P12-1263`.    
The outputs of 2026-11-22*

## Place In The Workflow

Stage 1, Step 6.0 (manual check before the gold standard).     
Documented in `5.doc_parsing_layer_v14.md` § 16 *Warnings File* (`warnings.csv`).     
Script: `07_parse_atf_to_tokens_v14.py`

## The Problem

*How a token becomes "unresolved"?*       
For every ATF reading, script 07 tries in turn the dictionary of simple signs, the dictionary of compounds, a sign name in brackets, and so on. If nothing fits, the token gets
`token_kind = unresolved` and goes to `warnings.csv`. It has no sign and no
glyph and does not enter `grapheme.csv`.

*Five kinds.* 
The column `kind_guess` gives a rough first sorting by the form of the token (not a decision):

| kind_guess | What it is | Example | Types / tokens |
|---|---|---|---|
| READING | reading missing from the catalogue | *tur₃* (357), *gilgameš₂* (94) | 406 / 1,175 |
| MARKUP or broken bracket | ATF markup, or a bracket cut apart by a space | `(…)`, `{{%a`, `min(gu` + `za)` | 368 / 1,158 |
| QUALIFIER reading(SIGN) | a qualified reading whose sign name the parser could not read | *geštuₓ(\|giš+tug₂\|)*, *sukuₓ(sukud)* | 374 / 673 |
| x-INDEX or SIGN NAME | a reading with the index ₓ, or a sign name | *ginₓ* (109), \|KA×X\| (46) | 112 / 392 |
| SIGN-LIST NUMBER | a sign-list number instead of a reading | *rec169* (55) | 3 / 67 |

*Why these are different tasks?*      
A missing reading needs philology (which sign is *tur₃*?)     
Markup is usually a tokenizing problem: ATF `min(gu za)` has a space inside the brackets, and the parser, which splits at spaces, gets the pieces `min(gu` and `za)`    
A qualifier with a lower-case sign name (*sukud*) or with `+` inside is also a rule for the parser.     
*rec169* can be linked to an OSL sign through `@list REC169`.

## Automatic Fix 

**No**
But almost every answer becomes a rule that resolves all tokens of a
type at once: `NEW_READING` adds the reading to the catalogue (source
`PROFESSOR`), `PARSER_RULE` teaches 07 to read a pattern, `EDITORIAL_MARKUP`
makes 07 skip it.

## Size And Effect On The Corpus

1,263 token types.    
**3,465** tokens ( **135** in school texts).    
The 40 rows with ≥ 10 tokens (1,530 tokens, almost half) are mandatory.     
For the thesis this answers the open question whether different shares of unresolved tokens distort the comparison: the share is small, but higher in lexical texts.     

## **Which Rows To Check (Scope)**

Rows with ≥ 10 tokens (40 rows, 1,530 tokens): **mandatory**. The rest: optional.

## Columns 

| Column | Meaning |
|---|---|
| `normalized_token` | the token after the normalisation of Step 5.1 (subscripts as digits) |
| `kind_guess` | rough sorting: READING / MARKUP or broken bracket / QUALIFIER reading(SIGN) / x-INDEX or SIGN NAME / SIGN-LIST NUMBER |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Open `corpus_example` on CDLI and look at the line.
2. Decide what the token is, for a reading give the sign.

## Decision Values

| Value | Meaning | Other columns |
|---|---|---|
| `NEW_READING` | a reading of a known sign | `sign_or_reading` required |
| `PARSER_RULE` | markup or a qualifier the parser should read (describe the pattern) | `comment` required |
| `EDITORIAL_MARKUP` | ATF markup, simply skip | – |
| `BROKEN` | damaged text | – |
| `KEEP_UNRESOLVED` | cannot be resolved | – |

## **First Rows Of The File (Examples)**

| normalized_token | kind_guess | tokens_in_OB_corpus | tokens_school | top_sites |
|---|---|---|---|---|
| tur3 | READING | 357 | 4 | (empty) 146, Nippur 92, Ur 44, uncertain 39 |
| (…) | MARKUP or broken bracket | 125 | 0 | (empty) 47, Nippur 31, Sippar-Yahrurum 25, Dilbat 4 |
| ginx | x-INDEX or SIGN NAME | 109 | 0 | Nippur 75, uncertain 34 |
| gilgames2 | READING | 94 | 0 | (empty) 83, Nippur 5, Ur 5, uncertain 1 |
| iti6 | READING | 59 | 1 | (empty) 35, Nippur 13, Ur 9, uncertain 1 |
| rec169 | SIGN-LIST NUMBER | 55 | 0 | (empty) 35, Nippur 19, Ur 1 |

*These are real rows of the file, not decisions.*
