# Data Dictionary: sign_all_v6.csv


## Basic Description

This dataset is a structured, machine-readable Cuneiform Sign List (`osl.asl`), built to support quantitative analysis of **sign allography and polyphony** 

The dataset provides, for every documented sign in the reference list:

- its Unicode identity (own code, or the codes of the components it is built from),
- its structural status (simple sign, compound, or undocumented),
- its attested alternate catalogue names (allographs),
- compound sign decomposition
- and its phonetic / syllabic reading data

**Coverage.** The dataset covers **3,249 `@sign` entries** in the source file (`osl.asl) and 7,238 rows after compound signs are exploded into one row per component. 

## Unit Description
**One row = one component position of one documented graphic form.**

- For a **simple** sign (atomic, no decomposition), the form corresponds to exactly one row.
- For a **compound** sign, the form is exploded into *N* rows, one per component, in left-to-right sequence order.

## Sign Type Description
We have divided all signs into 3 type groups:

| Value | Condition | 
|---|---|
| `Type_1` | Entity has its own `@list U+...` | 
| `Type_2` | Entity has `@useq` (explicit or resolved from `×`/`&`), no own code | 
| `Type_3` | Neither own code nor resolvable decomposition |

**Type_1** unites characters that have received their own, indivisible status in the Unicode standard. From a historical writing perspective, these are characters that the modern coding system recognizes as basic units of the cuneiform repertoire, that is, graphemes that cannot (or should not) be decomposed into simpler components for digital representation. Formally, a character receives an atomic code when it is perceived as an independent written unit, regardless of whether it is a simple form (like A) or a historically complex character (compound signs).   

**Type_2** describes signs that lack their own atomic identity, but are represented as a combination of already encoded signs. This reflect mechanisms of cuneiform development: the ability of scribes to create new graphemes by combining (juxtaposition with ×), ligature (&), or sequential writing (.) of existing signs. These signs "read" through its components, not as an independent unit. Type_2 captures precisely  compositional nature of writing, because it was built from other units.

**Type_3** is a residual category, representing characters that do not fall into either the first or second group. This category encompasses diverse phenomena, all united by the absence of formal digital status.
- graphic variants of existing characters (positional, modifications of the same basic character like A@g, A@t)
- characters known exclusively from historical paper catalogs (Daimmel, Messerschmidt, and other pre-modern systems) for which digital encoding has not yet been performed (like  LAK240, BAU067)
- characters whose composite nature is already evident from their script, but whose decomposition is not documented in the source.

##  Column Reference


| # | Column | Type | Definition | Source field in `osl.asl` |Notes |
|---|---|---|---|---|---|
| 1 | `unicode_id` | string | The Unicode code point (`U+XXXXX`),   | `@list U+...` (own), or the corresponding token of `@useq` |one unicode - one sign |
| 2 | `sign_grapheme` | string (glyph) | Glyph of sign | `@ucun` | Glypg of Unicode sign|
| 3 | `sign_structure` | categorical | Sign Categorization into single(atomic) or compound |Derived | The whole description in "Sign Structure Description"|
| 4 | `structural_hint` | categorical | Secondary flag qualifying `sign_structure`. | Derived |The whole description in "Sign Structure Description"|
| 5 | `component_position` | integer  | Position of Compound Sign Component from left to right. | derived from `@useq`, or from name-pattern decomposition |Empty for non-compound rows.|
| 6 | `sign_name` | string | The sign's primary/scientific name. | `@sign` |-|
| 7 | `allograph_form` | string | The specific `@form` name (an attested alternate catalogue name for the same sign), if one exists. | `@form` |Empty for headless* signs.|
| 8 | `graphic_variant_id` | string | The number of all attested alternative catalogue name of the same sign(@form)    | derived |All component rows of one compound form share the same id.More description below|
| 9 | `sign_type` | categorical | Categorization of all signs into three basic type  | derived |`Type_1` (own `@list U+`), `Type_2` (`@useq` present, no own code), `Type_3` (neither).|
| 10 | `compound_form` | string | The full name of the compound form itself | `@form` or `@sign` name |Identical across all its component rows.|
| 11 | `compound_grapheme` | string (glyph) | The full glyph sequence of the compound as a whole. | `@ucun` of the compound entity |Not the single-component glyph in column 2|
| 12 | `compound_unicode` | string | Semicolon-separated list of the component Unicode codes making up the compound. | `@useq` | In sequence order|
| 13 | `unicodeTrLit` | string | Scientific transliteration value associated with this row's `unicode_id`. | joined from `6_unicodeTrLit_Grph_Phon.csv` |-|
| 14 | `syllabary_sign` | string | Standard syllabary label for the sign. | joined from `6_unicodeTrLit_Grph_Phon.csv` |-|
| 15 | `phonetic_version` | string |  All attested phonetic reading versions for this sign. | joined from `6_unicodeTrLit_Grph_Phon.csv` |Pipe-separated list|
| 16 | `signList_analogue` | string |Cross-references to other historical sign catalogues (LAK, MZL, RSP, ABZL, etc.). | `@list` (all non-Unicode entries) | Semicolon-separated list, each annotated with approximate period and region|


##  `sign_structure` column

| Value | Condition |
|---|---|
| `atomic` | Own Unicode code, no `@useq` **or** code successfully inherited from the parent `@sign` (see `structural_hint`) | 
| `atomic_with_decompositions` | Own Unicode code **and** a documented `@useq` — the sign received its own atomic code but its historical composition is also recorded | 
| `compound` | No own code, but a component decomposition exists (explicit `@useq`, or successfully inferred from a `×`/`&` name) | 
| `not_identified` | No own code, no resolvable decomposition | 

## `structural_hint` column

| Value | Meaning | 
|---|---|
| *(empty)* | No special condition | 
| `inherited_from_parent` | Row has no code of its own; `unicode_id` was inherited from the parent `@sign`'s own code (classic case: an archaic catalogue form such as `LAK797` inheriting the code of its modern equivalent sign `A`). Kept out of `not_identified` deliberately, since the row *does* carry a usable Unicode value, just not one declared at its own level. | 
| `compound_unresolved` | Name contains `×` or `&` (structurally a compound) but decomposition could not be resolved automatically either because of nested parentheses (e.g. `\|GA₂×(A.EN)\|`) or because a named component could not be found in the sign index. `sign_structure` is `not_identified` for these rows, but the hint preserves the fact that a compound is suspected, for possible manual review. | 

## `graphic_variant_id` column
- Reflects catalogue documentation order.
- `{PREFIX}_v{N}`, where N numbers the distinct @forms of `sign_name` in the order they are documented in `osl.asl`.


## Notes * 
- **"headless"**  meaning all of the sign's information sits in the `@sign` header, with nothing catalogued as an alternate name.
- **`X` as a component value is a placeholder for an undeciphered sign**. Rows in this dataset contain `X` in `unicode_id` or `compound_unicode`. These rows should be excluded from any Unicode-keyed join.
- **The `[unverified]` suffix on a `unicode_id`** marks a code that `osl.asl` records but that is not present in the canonical `1_unicodeSigns.csv` reference. Inspection of the `@uage` field for these entries shows they are not un-sourced errors: they carry values such as `ACN` or a Unicode Technical Committee document number (e.g. `L2/24-270`), indicating the code has been formally proposed to the Unicode Consortium but not yet ratified in a published version.
- `not_identified`(in  `sign_structure` column) have no usable `unicode_id`.** Are structurally suspected compounds that could not be automatically decomposed (`structural_hint = compound_unresolved`)




## Source Files

| File | Role | 
|---|---|
| `osl.asl` | Primary source (Oracc Cuneiform Sign List, ASL format) |
| `1_unicodeSigns.csv` | Canonical Unicode Cuneiform reference (used to validate own-codes and resolve component glyphs) |
| `6_unicodeTrLit_Grph_Phon.csv` | Phonetic / syllabary reference, joined by `unicode_id` | 













