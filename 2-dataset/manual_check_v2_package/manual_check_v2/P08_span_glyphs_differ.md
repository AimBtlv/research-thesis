# P08. Span Merged Into A Compound With Other Glyphs 

*File: `P08_span_glyphs_differ.csv`  
9 rows     
check_id `P08-0001`–`P08-0009`     
The outputs of 2026-11-14*

## Place In The Workflow 

Stage 1, Step 6.0 (manual check before the gold standard).     
Documented in `5.doc_parsing_layer_v14.md` § 7 *Tokenisation* (pass 1, attested compounds).   
Script:  `07_parse_atf_to_tokens_v14.py`

## The Problem

*What a merge is?*      
The parser sometimes stores *several* ATF readings as **one** compound sign.     
Example without a problem: ATF *ku₃-babbar* ("silver"). The compound |KU₃.UD| has the reading *ku₃-babbar*, so the parser merges. |KU₃.UD| = KU₃ + UD, exactly the signs that *ku₃* and *babbar* give one by one: the **glyphs are the same**, and sign counts do not change.

*How the bad cases were found.* For every merge the program compared:

    A (merged):        compound → its components → glyphs
    B (one by one):    each reading separately → its sign → glyphs

If the glyphs of A and B **differ**, the row is in this file.

*Three kinds of difference.* A quick test: how many readings stand in ATF and
how many glyphs result (an editor usually writes one reading per sign).

| Kind | Example | ATF | Merged (A) | One by one (B) |
|---|---|---|---|---|
| another sign | *eš₁₈-dar* | 2 readings | AŠ@t + DAR 𒀹𒁯 | AŠ + DAR 𒀸𒁯 |
| a sign lost | *um-me-da* | 3 readings | UM + ME 𒌝𒈨 | UM + ME + DA 𒌝𒈨𒁕 |
| extra signs | *an-zib₂* | 2 readings | AN + GU₂×NUN + PA + EL | AN + ZIG |

*The error can be on either side.*       
The file shows a **difference**, not who is right. In OSL, *eš₁₈* belongs to AŠ@t and |AŠ@t.DAR| has the value *eš₁₈-dar*, so here the merged compound (A) is probably right and the separate lookup is wrong. For *um-me-da*, OSL does give |UM.ME| the value *um-me-da*, but ATF has three readings and the sign DA is probably on the tablet: the merge loses it,
so B is probably right.

## Automatic Fix 

**No.**      
Neither "always merge" nor "never merge" works: for *eš₁₈-dar* the
merge seems to correct an error of the catalogue, for *um-me-da* it creates
one. OSL, MZL and the photo of the tablet (`corpus_example`) decide. Rows
already fixed by other changes are not listed: *ni-ir* (placeholder, P07),
*u-gun₃* and *šu-u* (wrong code of *u*, P15).

## Size And Effect On The Corpus (Объём)

9 token types      
**1,195** tokens (41 in school texts). 
Almost all of them are *eš₁₈-dar* (Ištar, 755, mostly Sippar) and *aga-us₂* ("soldier", 415). All 9 rows are mandatory.

## **Which Rows To Check (Scope)**

All rows: **mandatory** (short).

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `compound_unicode / compound_glyph` | glyphs of the merged compound |
| `separate_signs / separate_unicode / separate_glyph` | glyphs the readings give one by one |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Look the compound up in OSL (`@useq`) and MZL.
2. Open `corpus_example`: what does the tablet show?

## Decision Values

| Value | Meaning | Other columns |
|---|---|---|
| `COMPOUND_OK` | the compound glyphs are right | – |
| `SEPARATE_SIGNS` | the separate readings are right: stop the merge | – |
| `OTHER_SIGN` | neither is right | explain in `comment` |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| raw_atf_token | resolved_compound | compound_glyph | separate_signs | separate_glyph | tokens_in_OB_corpus |
|---|---|---|---|---|---|
| eš18-dar | \|AŠ@t.DAR\| | 𒀹𒁯 | AŠ + DAR | 𒀸𒁯 | 755 |
| aga-us2 | \|DUN₃@g.UŠ\| | 𒂆𒍑 | DUN₃@g@g + UŠ | 𒂇𒍑 | 415 |
| nam-ri | \|MUŠ₃.ZA\| | 𒈹𒍝 | NAM + RI | 𒉆𒊑 | 10 |
| gum2-gum2-šu2 | \|LUM&LUM.ŠU₂\| | 𒈞𒋙 | LUM + LUM + ŠU₂ | 𒈝𒈝𒋙 | 5 |
| um-me-da | \|UM.ME\| | 𒌝𒈨 | UM + ME + DA | 𒌝𒈨𒁕 | 3 |
| an-zib2 | \|AN.GU₂×NUN.PA.EL\| | 𒀭𒄛𒉺𒂖 | AN + ZIG | 𒀭𒍨 | 3 |

*These are real rows of the file, not decisions.*
