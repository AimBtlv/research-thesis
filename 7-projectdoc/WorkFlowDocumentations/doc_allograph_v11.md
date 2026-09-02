## 4. How Was allograph_all_v11.csv Built?

This step produces the complete sign dataset for sign documented in the available sources
- Its Unicode identity 
- Its structural composition (simple sign or compound, and if compound, exactly which components it decomposes into)
- Its phonetic reading, drawing on Step 3's compound reading table wherever a sign is a compound.
This step takes the Unicode + Phonetic Version catalogue produced in Step 1 and the compound reading table produced in Step 3 and combines it with the ORACC Sign List (osl.asl) and Merged historical syllabary (CM + URUK2 + ADDITIONAL) to build a single table that answers, for every attested cuneiform sign, three questions: 
1. what Unicode identity does it carry? 
2. what is it built from, if it is a compound? 
3. what phonetic readings does it share with its component or parent signs?

osl.asl alone does not cover every sign a real text might contain, so a second goal of this step is to clearify which signs carry full Unicode-level verification and which do not.


## Data Sources

| Source | Description |
|---|---|
| **osl.asl** | ORACC Cuneiform Sign List |
| **7_unicodePhoneticVersion_full.csv** *(Step 1)* | Dataset for each unicode cuneiform character + Its Phonetic Version: `unicode_id / unicodeTrLit / syllabarySign / PhoneticsVersion`. |
| **compound_form_reading_table.csv** *(Step 3)* | Attested Compound reading as a whole word. |
| **diri_lexical_list.csv** / **ogsl_sign_readings.json** |  DIRI list/ OGSL (Oracc Global Sign List), a cross-project consolidation of sign values drawn from ABZL, BAU, HZL, KWU, LAK, MZL, RSP, SLLHA and other historical catalogues |
| **Syllabary_CM.csv** | Merged historical syllabary (CM + URUK2 + ADDITIONAL)signs not attested in `osl.asl` |

## Pipeline Overview

The pipeline was built in five stages over the full sign list:

| Stage | Task | Note |
|---|---|---|
| **Stage 1** | Parse every `@sign` and `@form` in `osl.asl`, skipping any block flagged `@sign-`/`@form-`/`@fake`. Classify each into `sign_type` and `sign_structure`. Decompose compounds into ordered components | One raw per component position covering all signs in `osl.asl` |
| **Stage 2** | Assign `graphic_variant_id` to every row, numbering each sign's distinct documented @forms (catalogue variant) in the order they appear in `osl.asl` | `graphic_variant_id` the number of all attested alternative catalogue name of the same sign(@form)|
| **Stage 3** | Join phonetic data: atomic signs from the Step 1 catalogue by `unicode_id`. Compounds from Step 3's reading table by `compound_form` | New columns `typePhonetic_Version` and `phonetic_version` filled on every row |
| **Stage 4** | Where an atomic sign's `phonetic_version` is still empty, or a sign has no Unicode identity at all, check the sign's own name against `diri_lexical_list.csv` and `ogsl_sign_readings.json` |  `No Sign Identity` rows given a real reading despite having no Unicode code |
| **Stage 5** | Find every sign name in the merged syllabary **Syllabary_CM.csv** with no counterpart in Stage 1's output, and append it | Additional rows without unicode|

**Output: `allograph_all_v11.csv`**, 9,603 rows

## Step-by-Step Description
The table constructed in a way that each line describes a single character if it's a simple character, it occupies one entire line, if it's a compound character, it's split into several consecutive lines, one line for each character that makes it up.   

However, all of these lines share the fields that describe the compound as a whole (its full name, its full glyph, its reading), and differ only in the fields that pertain specifically to the current component (its own Unicode code, its own glyph, its position within the sequence).     
This means that the same table can be read simultaneously at the level of both a single character and the compound as a whole, without duplicating the structure.

### 1. Parsing Full Coverage At The Sign Level
- The parser walks every `@sign` block in `osl.asl`.
- If the block contains one or more `@form` sub-block, each form is processed as its own entity, with the parent `@sign` header kept only as a fallback, meaning the parent's Unicode code is not lost when a form is processed separately: if the form has no code of its own, it receives the parent's code, and this is recorded  as `structural_hint = inherited_from_parent`.
- If a sign has no `@form` sub-blocks at all (here call this "headless"), the `@sign` header's own data becomes the sign's entire row in the dataset on its own.
This gives complete coverage of `osl.asl`: all 3,249 signs.
- A systematic audit of every `@`-tag in the file, found two further markers that  affect this pars:

| Marker | Meaning |
|---|---|
| `@sign-` (hyphen, no space) | Entry explicitly flagged spurious/deprecated/"do not use" by `osl.asl`'s own editors | 
| `@form-` | Same convention, at the form level |
| `@fake 1` | This entry is physically present in the list for technical reasons, but its status as a real, independent cuneiform sign is not recognized. | 

**Note:**
***Headless** meaning the sign has no attested alternate catalogue name (terminology of this project)


### 2. Subdividing Signs Into Three Types (`sign_type`)
We have divided all signs into 3 type groups:

| Value | Condition |
|---|---|
| `Type_1` | Entity has its own unicode (`@list U+...`) |
| `Type_2` | Entity has `@useq`s(equence of several Unicode characters for displaying or encoding a specific cuneiform sign (ligature, compound sign, or complex glyph)). or `×`/`&` (each sign component has its own unicode). The sequence of the whole sign components have no unicode of its own. |
| `Type_3` | Neither own code nor complex decomposition (GA₂×(A.EN)) |

**Type_1** unites characters that have received their own, indivisible status in the Unicode standard. From a historical writing perspective, these are characters that the modern coding system recognizes as basic units of the cuneiform repertoire, that is, graphemes that cannot (or should not) be decomposed into simpler components for digital representation. Formally, a character receives an atomic code when it is perceived as an independent written unit, regardless of whether it is a simple form (like A) or a historically complex character (compound signs).

**Type_2** describes signs that lack their own atomic identity, but are represented as a combination of already encoded signs. This reflects mechanisms of cuneiform development: the ability of scribes to create new graphemes by combining (juxtaposition with ×), ligature (&), or sequential writing (.) of existing signs. These signs "read" through its components, not as an independent unit. Type_2 captures precisely the compositional nature of writing, because it was built from other units.

**Type_3** is a residual category, representing characters that do not fall into either the first or second group. This category encompasses diverse phenomena, all united by the absence of formal digital status.
- graphic variants of existing characters (positional, modifications of the same basic character like A@g, A@t)
- characters known exclusively from historical paper catalogs (Deimel, Messerschmidt, and other pre-modern systems) for which digital encoding has not yet been performed (like LAK240, BAU067)
- characters whose composite nature is already evident from their script, but whose decomposition is not documented in the source
- synthetic placeholder entities marked `@fake 1` in `osl.asl` itself (not real signs at all — excluded from the dataset entirely, not merely classified as Type_3; see Step 1 above)

This classification is purely structural (it does not interpret meaning).


### 3. Categorizing Signs Into Single And Compound (`sign_structure`)

`sign_type` alone is not sufficient to describe a sign's actual composition, because there are obstacles where:
1. Most Type_3 signs are not compounds at all, they are glyph-variant markers (`A@g`, `A@t`) or names known only from historical paper catalogues (`LAK240`, `BAU067`), with no compositional structure whatsoever.
2. Compound signs carry **both** their own Unicode code **and** a documented `@useq`: they became common enough to receive a dedicated atomic code, while their compositional origin remains separately recorded (`|DUB.TI|`)

**Resolution 1:**
**`sign_structure` Column**
Added column which helps to highlight the unresolved features (for further manual parsing) with following values:

| Value | Condition |
|---|---|
| `atomic` | Own code, no `@useq` (or a code inherited from the parent sign) |
| `atomic_with_decompositions` | Own code **and** documented `@useq` |
| `compound` | No own code, but a component decomposition exists (explicit `@useq`, or algorithmically resolved from a `×`/`&`) |
| `not_identified` | No own code, no resolvable decomposition |

**Resolution 2:**
**`structural_hint` Column**
Add column which helps to highlight the unresolved features (for further manual parsing) with following categorizations:

| Value | Meaning |
|---|---|
| *(empty)* | No special condition |
| `inherited_from_parent` | Row has no code of its own; `unicode_id` was inherited from the parent `@sign`'s own code (classic case: an archaic catalogue form such as `LAK797` inheriting the code of its modern equivalent sign `A`). Kept out of `not_identified` deliberately, since the row *does* carry a usable Unicode value, just not one declared at its own level. |
| `compound_unresolved` | Name contains `×` or `&` (structurally a compound) but decomposition could not be resolved automatically either because of nested parentheses (e.g. `\|GA₂×(A.EN)\|`) or because a named component could not be found in the sign index. `sign_structure` is `not_identified` for these rows, but the hint preserves the fact that a compound is suspected, for possible manual review. |
| `phonetic_via_diri` | Reading for this row was found in `diri_lexical_list.csv` by sign name, after the Step 1/Step 3 catalogue-based join left `phonetic_version` empty. See Step 6. |
| `phonetic_via_ogsl` | Same as above, but the reading came from `ogsl_sign_readings.json`. Checked only when Diri had no reading either. See Step 6. |

**Note:**     
**`@useq`** Sequence of several Unicode characters (code points) for displaying or encoding a specific cuneiform sign (ligature, compound sign, or complex glyph).

### 4. Decomposing Compound Signs Into Components

For signs classified as `compound`, the component sequence is obtained in one of two ways.
1. Where `osl.asl` records an explicit `@useq`, the sequence is read directly (split by (.))
2. Where no `@useq` is present but the sign's name contains `×` (juxtaposition) or `&` (ligature), the parser tries to split the name into pieces and find each piece as its own sign, for example splitting `AB×A` into `AB` and `A`.

To look up each piece, the parser checks only the list of `@sign` headers, never the `@form` names.

**Note:**    
- **Nested parentheses.** A name like `|GA₂×(A.EN)|` has a compound inside another compound (the `(A.EN)` part is itself two signs, and it sits inside a larger ×-combination). The automatic splitting routine does not try to guess how to break this apart(a wrong guess here would be worse than leaving it unresolved). These are left flagged as `compound_unresolved` instead.    
- **`@compoundonly` shapes.** Sometimes one piece of a compound's name does not exist as its own sign at all in `osl.asl`.There is no `@sign` entry for it anywhere. Instead, `osl.asl` mentions that shape in a separate,  each name simply marked `@compoundonly`. This shape has been seen, but only as part of some other compound it has never been treated as a sign on its own.

Every compound entity is then exploded into one row per component, and four columns together reveal its full composition:   
●	**`component_position` column** numeric position of component in compound sign (within the sequence left to right).   
●	**`compound_form`column** the name of the compound as a whole, identical across all of its component rows.   
●	**`compound_grapheme`column** the full glyph sequence of the compound (not the single-component glyph).   
●	**`compound_unicode`column** the semicolon-separated list of all component codes, in sequence order.   

Each row's own `unicode_id` and `sign_grapheme` (columns 1 and 2) describe that one component specifically, while `compound_form` / `compound_grapheme` / `compound_unicode` describe the compound as a whole, so a single compound sign is fully readable both at the component level and as an aggregate from the same set of rows.

### 5. Assigning `graphic_variant_id`

Each sign's distinct documented @forms (catalogue variant or glyph version) are numbered `{PREFIX}_v1`, `_v2`, in the order they are **documented in `osl.asl`**. All component rows belonging to one compound form share the same id, since they represent one physical attestation, not separate variants. 

### 6. Assigning Phonetic Version, Transliteration, And Syllabary Sign

●	**`unicodeTrLit`** the transliteration derived from the sign's Unicode character name.   
●	**`syllabary_sign`** the scientific sign name as used in academic citation.   
●	**`phonetic_version`** the full pipe-separated list of attested phonetic readings.  
●   Every row is classified into exactly one of five **`typePhonetic_Version`** values    filled accordingly:

| `typePhonetic_Version` | Condition |
|---|---|
| `Single Sign Reading` | atomic sign, joined by its own `unicode_id` against the Step 1 catalogue | 
| `Attested Compound Reading` | compound, whole-word reading found via Step 3's table | 
| `No Attested Compound Reading` | compound, no reading found anywhere |
| `Compound Nested in Longer Form` | compound documented only inside a longer attested form |
| `No Sign Identity` | no Unicode code, no decomposition |

●  and **`phonetic_version`** Variant of sign reading. 

For compound rows, every component row of the same compound carries the **same** `phonetic_version`, the compound's own whole-word reading, following the same convention already used by `compound_form` / `compound_grapheme` / `compound_unicode`.     
The compound's reading describes the word as a whole, not any single component. Where no compound-level reading is attested, the field is left empty.      
`Compound Nested in Longer Form` rows are, by design, always empty in `phonetic_version`: that status specifically means no reading of the short form's own exists (explained in  `nested_in_forms` in `compound_form_reading_table.csv` for that context).

For atomic rows, an empty `phonetic_version` happens for one of two reasons: either the Unicode code `osl.asl` claims for the sign is not one of the 1,234 officially ratified codes, or the code is fully legitimate but no reading for it was ever recorded in the Step 1 (7_unicodePhoneticVersion_full.csv) phonetic catalogue in the first place.

The Step 1(7_unicodePhoneticVersion_full.csv) catalogue can only help where it has something to join — it is looked up strictly by `unicode_id`, so a row with no working code, or a row whose code has no entry there, gets nothing from it at all. For these rows, a second check is made by the sign's own **name** instead of its code: `diri_lexical_list.csv` and `ogsl_sign_readings.json` are both keyed by name, so they can still find a reading even where the Unicode-based join found nothing. This is applied in two places:

●	**`Single Sign Reading` rows with an empty `phonetic_version`** (294 originally): the sign's own name is checked against Diri, then OGSL. **67 closed** (`structural_hint` set to `phonetic_via_diri` or `phonetic_via_ogsl` accordingly).
●	**`No Sign Identity` rows** (no Unicode code at all, 462 originally): the same by-name check. **116–118 given a real, attested reading** despite having no Unicode identity — direct evidence that "not encoded in Unicode" and "not linguistically attested" are two different facts about a sign.

Step 1's catalogue (`7_unicodePhoneticVersion_full.csv`) is searched by `unicode_id` only. This means it can only help a row that already has a working Unicode code listed in that catalogue. If a row has no code, or a code the catalogue never recorded a reading for, this search finds nothing, regardless of anything else about the sign.

For exactly these rows, a second search is done, this time by the sign's own **name**, not its code. `diri_lexical_list.csv` and `ogsl_sign_readings.json` are both organised by sign name, so they can still return a reading in cases where the Unicode-based search could not.
This name-based search is applied in two places:

●	The sign's name is checked against Diri first, then against OGSL if Diri has nothing. 
●	**Signs with no Unicode code at all**: the same name-based search. Signs have a real, attested reading anyway showing that having no Unicode code and having no known reading are two separate facts about a sign, not the same thing.
Diri is always checked first, OGSL only as a fallback where Diri has nothing. The same priority order established for compound readings in Step 3.

### 7. Extending Dataset With Signs Outside osl.asl

Every one of the 4,196 distinct sign names in the merged syllabary (**Syllabary_CM.csv**) is checked against every sign already classified in Stage 1 (normalised: pipes stripped, Unicode subscript digits folded to ASCII). And there are signs which have no counterpart anywhere.**
The overwhelming majority come from the archaic proto-cuneiform Uruk period (3400–3000 BCE).

**Classification Of **Syllabary_CM.csv** Additional Signs** Due to lack of information source:
- `unicode_id` the absence is specifically of a Unicode identity
- No `sign_type`/`sign_structure` distinction for these Additional Signs
- `sign_type = "Type_3"`
- `sign_structure = "not_identified"`, identical to any other sign without a Unicode identity.
- `sign_source`: `"Uruk2"` / `"Syllabary_CM"` / `"Additional Sources"` for these rows. Every field that cannot apply to them (`unicode_id`, `sign_grapheme`, `compound_form`, `compound_grapheme`, `compound_unicode`, `unicodeTrLit`, `signList_analogue`) is left empty
- `typePhonetic_Version`  since they do carry a real, attested reading, that is the entire reason they are included

### 8. Role Of The Other Historical Catalogues (`signList_analogue`)

Beyond Unicode, `osl.asl` cross-references each sign against up to fifteen other historical sign-list systems (`LAK`, `MZL`, `RSP`, `ABZL`, `ELLES`, `KWU`, `BAU`, `ASY`, `GCSL`, `PTACE`, `HZL`, `SYA`, `ZATU`, `REC`, and others). These are not Unicode codes, they are references to paper catalogues compiled at different points in the history, each associated with a particular period and scholarly tradition (`LAK` for the Uruk archaic corpus, `ABZL` for Old Babylonian school texts, `MZL` for standard Babylonian). `signList_analogue` collects every such reference attached to a sign, annotated with its approximate period and region, into one semicolon-separated field. Its role in this dataset is traceability: it lets a sign found in this table be cross-checked against the specific secondary-literature catalogue a philologist would recognize, and it gives an approximate chronological/regional anchor for a sign even before any corpus text has been joined.

### 9. `@compoundonly` Investigated, No Fix Required

`osl.asl` separately declares  sign names via a standalone `@compoundonly` directive, outside any `@sign` block, acknowledging that a given shape exists only as part of another, already-documented compound. None have their own `@sign` entry at all. See Step 4 above for its one confirmed, narrow effect on `compound_unresolved` decomposition.

**Note:***
**"headless"** meaning all of the sign's information sits in the @sign header, with nothing catalogued as an alternate name.
**"X"** as a component value is a placeholder for an undeciphered sign. Rows in this dataset contain X in unicode_id or compound_unicode. These rows should be excluded from any Unicode-keyed join.
**"[unverified]"** suffix on a unicode_id marks a code that osl.asl records but that is not present in the canonical 1_unicodeSigns.csv reference. Inspection of the @uage field for these entries shows they are not un-sourced errors: they carry values such as ACN or a Unicode Technical Committee document number (e.g. L2/24-270), indicating the code has been formally proposed to the Unicode Consortium but not yet ratified in a published version.
**"not_identified"** (in sign_structure column) have no usable unicode_id. Are structurally suspected compounds that could not be automatically decomposed (structural_hint = compound_unresolved).

## Output Description

**`allograph_all_v11.csv`** 9,603 rows

| # | Column | Type | Definition | Source field in `osl.asl` | Notes |
|---|---|---|---|--|---|
| 1 | `unicode_id` | string | The Unicode code point (`U+XXXXX`) | `@list U+...` (own), or the corresponding token of `@useq` | one unicode - one sign |
| 2 | `sign_grapheme` | string (glyph) | Glyph of sign | `@ucun` | Glyph of Unicode sign |
| 3 | `sign_source` | string | `"OSL"`, or the syllabary origin (`"Uruk2"` / `"Syllabary_CM"` / `"Additional Sources"`) | - | - |
| 4 | `sign_structure` | categorical | Sign Categorization into single(atomic) or compound | Derived | See Step 3 |
| 5 | `structural_hint` | categorical | Secondary flag qualifying `sign_structure`, including the two Diri/OGSL fallback values | Derived | See Steps 3 and 6 |
| 6 | `component_position` | integer | Position of Compound Sign Component from left to right | derived from `@useq`, or from name-pattern decomposition | Empty for non-compound rows |
| 7 | `sign_name` | string | The sign's primary/scientific name | `@sign` | - |
| 8 | `allograph_form` | string | The specific `@form` name (an attested alternate catalogue name for the same sign), if one exists | `@form` | Empty for headless* signs |
| 9 | `graphic_variant_id` | string | The number of all attested alternative catalogue names of the same sign (@form) | derived | All component rows of one compound form share the same id |
| 10 | `sign_type` | categorical | Categorization of all signs into three basic types | derived | `Type_1` (own `@list U+`), `Type_2` (`@useq` present, no own code), `Type_3` (neither) |
| 11 | `compound_form` | string | The full name of the compound form itself | `@form` or `@sign` name | Identical across all its component rows |
| 12 | `compound_grapheme` | string (glyph) | The full glyph sequence of the compound as a whole | `@ucun` of the compound entity | Not the single-component glyph in column 2 |
| 13 | `compound_unicode` | string | Semicolon-separated list of the component Unicode codes making up the compound | `@useq` | In sequence order |
| 14 | `unicodeTrLit` | string | Scientific transliteration value associated with this row's `unicode_id` | joined from Step 1's `unicodePhoneticVersion_full.csv` | - |
| 15 | `syllabary_sign` | string | Standard syllabary label for the sign | joined from Step 1's `unicodePhoneticVersion_full.csv` | - |
| 16 | `typePhonetic_Version` | string | - | - | see Step 6 above |
| 17 | `phonetic_version` | string | All attested phonetic reading versions for single and compound signs | - | Pipe-separated list, may be filled via Step 3's table or, failing that, via Diri/OGSL by name (Step 6) |
| 18 | `signList_analogue` | string | Cross-references to other historical sign catalogues (LAK, MZL, RSP, ABZL, etc.) | `@list` (all non-Unicode entries) | Semicolon-separated list, each annotated with approximate period and region |
















