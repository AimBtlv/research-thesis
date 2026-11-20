# P09. Syllabary Name Without Unicode In The Corpus

*File: `P09_syllabary_name_without_unicode.csv`    
31 rows      
Check_id `P09-0001`–`P09-0031`    
The outputs of 2026-11-14*    

## Place In The Workflow

Stage 1, Step 6.0 (manual check before the gold standard).         
Documented in `4.doc_sign_catalogue_v13.md` § 7 *Extending The Dataset* (Stage 6–7)`5.doc_parsing_layer_v14.md`      
Note on 2,545 rows      
Script: `06_build_sign_catalogue_v13.py`

## The Problem
*Where such names come from?* 
The sign catalogue is built from two kinds of sources: **OSL** (a modern sign list, its signs have Unicode code points) and the **historical syllabaries** (Syllabary_CM of M. Maiocchi, Uruk2), which name signs in their own way. A syllabary name that does not exist in OSL is still added to the catalogue, so that its reading is not lost, but it has **no
Unicode code point**, because only OSL gives code points.

*Where the problem arises?*      
Example: the reading *sipa* ("shepherd").

| Step | What happens |
|---|---|
| ATF | *sipa* |
| catalogue | *sipa* → name **SIPA** (from Uruk2) |
| OSL | no sign named SIPA |
| grapheme.csv | sign SIPA, `unicode_id` **empty**, no glyph |

In OSL, *sipa* is a value of the compound **\|PA.LU\|** = PA + LU (𒉺𒇻): two
glyphs should be stored.

| Syllabary name | Reading | OSL candidate | Tokens |
|---|---|---|---|
| SIPA | *sipa* | \|PA.LU\| | 1,006 |
| KA.AN.RA | *babila₂* (Babylon) | \|KA₂.AN.RA\| | 537 |
| AŠ2.A.AN | *udru* (camel) | \|ZIZ₂.A.AN\| | 428 |
| IDIGNA | *idigna* (Tigris) | \|GU₂.GAR₃\| or \|TUM×PAP\| | 205 |

*Why it matters?*     
A token without a glyph **drops out** of every count by sign
(inventories, Jaccard index). These are frequent words, and they drop out
unevenly: mostly in practical texts (Sippar, Mari, Larsa), only 50 of 2,543 in
school texts.

## Automatic Fix 

**No.**     
The OSL candidate (`osl_suggestion`) is only a **suggestion**:
1. syllabary and OSL spell names differently (KA.AN.RA vs \|KA₂.AN.RA\|; KA and
   KA₂ are different signs; AŠ2.A.AN vs \|ZIZ₂.A.AN\|).  
2. there can be several candidates (*idigna*: two OSL signs)
3. sometimes it is not a sign at all (`X`, 46 tokens, comes from ATF markup)
4. OSL marks \|KA.AN.RA\| as deprecated (`@sign-`), the valid entry is
   \|KA₂.AN.RA\|.

The script 10(`10_build_manual_check.py`)  looks for OSL entries that have the syllabary name **or one of the readings** that lead to it in the corpus as a value, reading `osl.asl` line by line  
22 of 31 rows now have a suggestion.

## Size And Effect On The Corpus

31 names         
**2,543** tokens without a glyph (**50** in school texts).     
The five most frequent give 2,247 tokens.     
All rows are mandatory.


## **Which Rows To Check (Scope)**

All rows: **mandatory**.

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `readings_in_corpus` | the ATF readings that lead to this name |
| `osl_suggestion` | OSL entries with the same name or value |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Look the reading up in OSL / ePSD2.
2. Write the OSL sign (usually a compound) in `osl_sign`.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `LINK_TO_OSL` | the name is this OSL sign | `osl_sign` required |
| `KEEP_AS_NAME` | no OSL sign; keep without code | – |
| `NOT_A_SIGN` | an editorial artefact | – |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| sign_name | readings_in_corpus | osl_suggestion | tokens_in_OB_corpus | tokens_school |
|---|---|---|---|---|
| SIPA | sipa 1005, rex(sipa) 1 | OSL value of: \|PA.LU\| | 1006 | 32 |
| KA.AN.RA | babila2 537 | OSL value of: \|KA₂.AN.RA\| | 537 | 0 |
| AŠ2.A.AN | udru 425, imgaga 3 | OSL value of: \|ZIZ₂.A.AN\| | 428 | 1 |
| IDIGNA | idigna 205 | same name in OSL: IDIGNA / OSL value of: \|GU₂.GAR₃\|; \|TUM×PAP\| | 205 | 1 |
| GIŠ.TUG2.PI.ŠIR.SILA3 | gizzal 71 | OSL value of: \|GIŠ.TUG₂.PI.NU₁₁@90.SILA₃\| | 71 | 1 |
| KA.AN | babila 54, mitumx(\|ka+an\|) 1 | OSL value of: \|KA₂.AN\| | 55 | 4 |

*These are real rows of the file, not decisions.*
