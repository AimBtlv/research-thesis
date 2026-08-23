## 2. How was Created allograph_all_v8?

This step takes the Unicode + Phonetic Version catalogue produced in Step 1 (`unicodePhoneticVersion_full.csv`, 1,235 signs) and combines it with the full structural content of the ORACC Sign List (`osl.asl`) to build a single table that answers, for every attested cuneiform sign, three questions:    
**1. what Unicode identity does it carry?**   
**2. what is it built from, if it is a compound?**    
**3. what phonetic readings does it share with its component or parent signs**? 

Signs in `osl.asl` are not a flat list, they are catalogued either    
- as an independent `@sign` (a scientific/basic name) or 
- as a `@form` nested inside a `@sign` (an attested alternate catalogue name for the same underlying sign, such as an archaic Deimel number (LAK240)). 
- Some signs are atomic, some are explicitly built from other signs (`@useq`,compound signs connected with (.))
- some are written as a visual combination of other signs without any formal decomposition on record(compound signs conected by (x)(&)) and 
- some are documented only by name, with no Unicode identity at all.    
The purpose of this step is to resolve each of these situations consistently, so that a researcher can query the table by Unicode ID, by sign name, or by component, and always get a structurally correct answer, rather than treating undocumented and compound signs as if they were equivalent, or discarding signs that the underlying source records only partially.

## Data Sources

| Source | Description |
|---|---|
| **ORACC Sign List** `osl.asl` | Machine-readable ORACC Sign List. Encodes sign names (`@sign`), alternate catalogue names (`@form`), Unicode IDs (`@list U+...`), compound decompositions (`@useq`), glyphs (`@ucun`), and cross-references to historical paper catalogues (`@list <catalogue-code>`). |
| **Unicode Cuneiform Reference** `1_unicodeSigns.csv` | Canonical list of 1,235 ratified Unicode Cuneiform code points, produced independently of `osl.asl`. Used to verify that a code claimed in `osl.asl` is actually a published Unicode code point. |
| **Unicode + Phonetic Catalogue** `unicodePhoneticVersion_full.csv` (Step 1 output) | 1,235-entry table of `unicode_id → unicodeTrLit / syllabarySign / PhoneticsVersion`. Used as the lookup table joined into every row of this dataset. |
| **compound_form_reading_table.csv** | Per-compound reading status (`ATTESTED_DIRECT` / `NESTED_IN_LONGER_FORM` / `NO_ATTESTED_READING`) built in the step 2. |
| **Syllabary_CM.csv** | Merged historical syllabary (CM + URUK2 + ADDITIONAL, 4,196 distinct sign names), used both for compound readings and for signs missing from `osl.asl` entirely. |

## Pipeline Overview

The pipeline was built in three stage over the full sign list:

| Stage | Task | Output |
|---|---|---|
| **Stage 1** | Parse every `@sign` and `@form` entity, classify each into `sign_type` and `sign_structure`, decompose compounds into components | 7,238 rows (one per component position) covering all 3,249 signs |
| **Stage 2** | Assign `graphic_variant_id` to every row, numbering each sign's distinct documented @forms(catalogue variant) in the order they appear in `osl.asl` | same rows, `graphic_variant_id` populated |
| **Stage 3** | Join `unicodeTrLit`, `syllabary_sign`, `phonetic_version` from the Step 1 catalogue, matched by `unicode_id` | same rows, phonetic fields populated where a match exists |

**Output: `allograph_all_v8.csv`**, 7,238 rows, 3,249 unique signs (100% coverage).

## Step-by-Step Description

### 1. Parsing At Full Sign Coverage

The parser walks every `@sign` block in `osl.asl`.     
If the block contains one or more `@form` sub-block, each form is processed as its own entity, with the parent `@sign` header kept only as a fallback.     
If the block contains no `@form` at all (headless*), the header itself is processed as the sign's sole documented entity. 

**Note:**.  
***Headless**  meaning the sign has no attested alternate catalogue name (terminology of this project)
### 2. Subdividing Signs Into Three Types (`sign_type`)
We have divided all signs into 3 type groups:

| Value | Condition | 
|---|---|
| `Type_1` | Entity has its own unicode (`@list U+...`) | 
| `Type_2` | Entity has `@useq` or  `×`/`&`(each sign component has its own unicode) .The sequence of the whole sign components have no unicode of its own. | 
| `Type_3` | Neither own code nor complex decomposition (GA₂×(A.EN)) |

**Type_1** unites characters that have received their own, indivisible status in the Unicode standard. From a historical writing perspective, these are characters that the modern coding system recognizes as basic units of the cuneiform repertoire, that is, graphemes that cannot (or should not) be decomposed into simpler components for digital representation. Formally, a character receives an atomic code when it is perceived as an independent written unit, regardless of whether it is a simple form (like A) or a historically complex character (compound signs).   

**Type_2** describes signs that lack their own atomic identity, but are represented as a combination of already encoded signs. This reflect mechanisms of cuneiform development: the ability of scribes to create new graphemes by combining (juxtaposition with ×), ligature (&), or sequential writing (.) of existing signs. These signs "read" through its components, not as an independent unit. Type_2 captures precisely  compositional nature of writing, because it was built from other units.

**Type_3** is a residual category, representing characters that do not fall into either the first or second group. This category encompasses diverse phenomena, all united by the absence of formal digital status.
- graphic variants of existing characters (positional, modifications of the same basic character like A@g, A@t)
- characters known exclusively from historical paper catalogs (Daimmel, Messerschmidt, and other pre-modern systems) for which digital encoding has not yet been performed (like  LAK240, BAU067)
- characters whose composite nature is already evident from their script, but whose decomposition is not documented in the source.

This classification is purely structural (it does not interpret meaning)

### 3. Categorizing Signs Into Single and Compound (`sign_structure`)

`sign_type` alone is not sufficient to describe a sign's actual composition, because there are obsticles where:
1. Most Type_3 signs are not compounds at all, they are glyph-variant markers (`A@g`, `A@t`) or names known only from historical paper catalogues (`LAK240`, `BAU067`), with no compositional structure whatsoever.
2. Compound signs carry **both** their own Unicode code **and** a documented `@useq`: they became common enough to receive a dedicated atomic code, while their compositional origin remains separately recorded ( `|DUB.TI|`)

**Resolution 1:** 
**`sign_structure`Column**      
Add column  which helps to highlight the unresolved features (for further manual parsing) with following values:

| Value | Condition | 
|---|---|
| `atomic` | Own code, no `@useq` (or a code inherited from the parent sign) |
| `atomic_with_decompositions` | Own code **and** documented `@useq` |
| `compound` | No own code, but a component decomposition exists(explicit `@useq`, or algorithmically resolved from a `×`/`&`)|
| `not_identified` | No own code, no resolvable decomposition |


**Resolution 2:** 
**`structural_hint` Column**           
Add column which helps to highlight the unresolved features (for further manual parsing) with following cotegorizations:
| Value | Meaning | 
|---|---|
| *(empty)* | No special condition | 
| `inherited_from_parent` | Row has no code of its own; `unicode_id` was inherited from the parent `@sign`'s own code (classic case: an archaic catalogue form such as `LAK797` inheriting the code of its modern equivalent sign `A`). Kept out of `not_identified` deliberately, since the row *does* carry a usable Unicode value, just not one declared at its own level. | 
| `compound_unresolved` | Name contains `×` or `&` (structurally a compound) but decomposition could not be resolved automatically either because of nested parentheses (e.g. `\|GA₂×(A.EN)\|`) or because a named component could not be found in the sign index. `sign_structure` is `not_identified` for these rows, but the hint preserves the fact that a compound is suspected, for possible manual review. | 


### 4. Decomposing Compound Signs Into Components

For signs classified as `compound`, the component sequence is obtained in one of two ways. 
1. Where `osl.asl` records an explicit `@useq`, the sequence is read directly(splited by (.))
2. Where no `@useq` is present but the sign's name contains `×` (juxtaposition) or `&` (ligature), an automatic decomposition routine splits the name at the operator and attempts to resolve each resulting component against the full index of all 3,249 signs. 

**Note** names with nested parentheses ( `|GA₂×(A.EN)|`) were left for the `compound_unresolved` flag described above rather than guessed at.

Every compound entity is then exploded into one row per component, and four columns together reveal its full composition:    
●	**`component_position` column** numeric position of component in compound sign ( within the sequence left to right).   
●	**`compound_form`** the name of the compound as a whole, identical across all of its component rows.   
●	**`compound_grapheme`**  the full glyph sequence of the compound (not the single-component glyph).   
●	**`compound_unicode`** the semicolon-separated list of all component codes, in sequence order.   

Each row's own `unicode_id` and `sign_grapheme` (columns 1 and 2) describe that one component specifically, while `compound_form` / `compound_grapheme` / `compound_unicode` describe the compound as a whole, so a single compound sign is fully readable both at the component level and as an aggregate from the same set of rows.

### 5. Assigning `graphic_variant_id`

Each sign's distinct documented @forms(catalogue variant or glyph version) are numbered `{PREFIX}_v1`, `_v2`, in the order they are **documented in `osl.asl`**. All component rows belonging to one compound form share the same id, since they represent one physical attestation, not separate variants. This id is a structural label.

### 6. Assigning Phonetic Version, Transliteration, And Syllabary Sign

Every row's `unicode_id` is looked up against the Step 1 catalogue (`unicodePhoneticVersion_full.csv`), and three fields are copied in where a match is found:

●	**`unicodeTrLit`**  the transliteration derived from the sign's Unicode character name.    
●	**`syllabary_sign`** the scientific sign name as used in academic citation.    
●	**`phonetic_version`** the full pipe-separated list of attested phonetic readings.       
Because this join uses the same `unicode_id` key that Step 1 built, every sign's phonetic profile is inherited automatically, no separate phonetic lookup was re-implemented for this stage.     

**Note**  `X` rows carry the undeciphered-sign placeholder 



### 7. Role Of The Other Historical Catalogues (`signList_analogue`)

Beyond Unicode, `osl.asl` cross-references each sign against up to fifteen other historical sign-list systems (`LAK`, `MZL`, `RSP`, `ABZL`, `ELLES`, `KWU`, `BAU`, `ASY`, `GCSL`, `PTACE`, `HZL`, `SYA`, `ZATU`, `REC`, and others). These are not Unicode codes, they are references to paper catalogues compiled at different points in the history, each associated with a particular period and scholarly tradition ( `LAK` for the Uruk archaic corpus, `ABZL` for Old Babylonian school texts, `MZL` for standard Babylonian). `signList_analogue` collects every such reference attached to a sign, annotated with its approximate period and region, into one semicolon-separated field. Its role in this dataset is traceability: it lets a sign found in this table be cross-checked against the specific secondary-literature catalogue a philologist would recognize, and it gives an approximate chronological/regional anchor for a sign even before any corpus text has been joined.

**Note:***      
**"headless"** meaning all of the sign's information sits in the @sign header, with nothing catalogued as an alternate name.   
**"X"** as a component value is a placeholder for an undeciphered sign. Rows in this dataset contain X in unicode_id or compound_unicode. These rows should be excluded from any Unicode-keyed join.       
**"The [unverified]"** suffix on a unicode_id marks a code that osl.asl records but that is not present in the canonical 1_unicodeSigns.csv reference. Inspection of the @uage field for these entries shows they are not un-sourced errors: they carry values such as ACN or a Unicode Technical Committee document number (e.g. L2/24-270), indicating the code has been formally proposed to the Unicode Consortium but not yet ratified in a published version.     
**"not_identified"**(in sign_structure column) have no usable unicode_id.** Are structurally suspected compounds that could not be automatically decomposed (structural_hint = compound_unresolved)

## Output Description

**`allograph_all_v6.csv`**  7,238 rows, 3,249 unique signs(The whole corpus of OSL.asl).

| # | Column | Type | Definition | Source field in `osl.asl` |Notes |
|---|---|---|---|--|---
| 1 | `unicode_id` | string | The Unicode code point (`U+XXXXX`),   | `@list U+...` (own), or the corresponding token of `@useq` |one unicode - one sign |
| 2 | `sign_grapheme` | string (glyph) | Glyph of sign | `@ucun` | Glypg of Unicode sign|
| 3 |`sign_source`| string | `"OSL"`, or the syllabary origin (`"Uruk2"` / `"Syllabary_CM"` / `"Additional Sources"`)| - |-|
| 4 | `sign_structure` | categorical | Sign Categorization into single(atomic) or compound |Derived | The whole description in "Sign Structure Description"|
| 5 | `structural_hint` | categorical | Secondary flag qualifying `sign_structure`. | Derived |The whole description in "Sign Structure Description"|
| 6 | `component_position` | integer  | Position of Compound Sign Component from left to right. | derived from `@useq`, or from name-pattern decomposition |Empty for non-compound rows.|
| 7 | `sign_name` | string | The sign's primary/scientific name. | `@sign` |-|
| 8 | `allograph_form` | string | The specific `@form` name (an attested alternate catalogue name for the same sign), if one exists. | `@form` |Empty for headless* signs.|
| 9 | `graphic_variant_id` | string | The number of all attested alternative catalogue name of the same sign(@form)    | derived |All component rows of one compound form share the same id.More description below|
| 10 | `sign_type` | categorical | Categorization of all signs into three basic type  | derived |`Type_1` (own `@list U+`), `Type_2` (`@useq` present, no own code), `Type_3` (neither).|
| 11 | `compound_form` | string | The full name of the compound form itself | `@form` or `@sign` name |Identical across all its component rows.|
| 12 | `compound_grapheme` | string (glyph) | The full glyph sequence of the compound as a whole. | `@ucun` of the compound entity |Not the single-component glyph in column 2|
| 13 | `compound_unicode` | string | Semicolon-separated list of the component Unicode codes making up the compound. | `@useq` | In sequence order|
| 14 | `unicodeTrLit` | string | Scientific transliteration value associated with this row's `unicode_id`. | joined from `6_unicodeTrLit_Grph_Phon.csv` |-|
| 15 | `syllabary_sign` | string | Standard syllabary label for the sign. | joined from `6_unicodeTrLit_Grph_Phon.csv` |-|
| 16 | `typePhonetic_Version` | string | - | - |see Step 6 above|
| 17 | `phonetic_version` | string |  All attested phonetic reading versions for single and compound signs. | - |Pipe-separated list|
| 18 | `signList_analogue` | string |Cross-references to other historical sign catalogues (LAK, MZL, RSP, ABZL, etc.). | `@list` (all non-Unicode entries) | Semicolon-separated list, each annotated with approximate period and region|

