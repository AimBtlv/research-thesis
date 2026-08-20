# Data Dictionary: allograph_all_v6.csv

**Cuneiform Sign Allograph and Compound-Decomposition Dataset**

---

## 1. Purpose And Scope

This dataset is a structured, machine-readable transformation of the Oracc Cuneiform Sign List (`osl.asl`), built to support quantitative analysis of **sign allography and polyphony** (Research Question 1: whether the graphic and phonetic variation documented for cuneiform signs shows regular patterns across provenance and period, and whether school-context sign usage correlates with usage in administrative, literary, or commercial corpora).

The dataset provides, for every documented sign in the reference list:

- its Unicode identity (own code, or the codes of the components it is built from),
- its structural status (simple sign, compound, or undocumented),
- its attested alternate catalogue names (allographs),
- and its phonetic / syllabic reading data, joined from a secondary reference.

**Coverage.** The dataset covers **100% of the 3,249 `@sign` entries** in the source file (7,238 rows after compound signs are exploded into one row per component). This is a deliberate improvement over an earlier extraction pass, which parsed only `@form` sub-entries and consequently covered only 604 signs (18.6%) — the remaining 2,645 signs record all of their information directly in the `@sign` header, with no nested `@form` block, and were previously omitted entirely.

**What this dataset is NOT.** This is a profile of the *reference sign list*, not of an attested text corpus. Any counts derivable from this table (e.g. how many named forms share a Unicode code) reflect how the cataloguing tradition documented a sign, not how frequently that sign was actually written by scribes. Corpus-level frequency requires a separate join against ATF-transliterated texts (e.g. from CDLI), which is a planned downstream step and is out of scope for this file.

---

## 2. Source Files

| File | Role | Size |
|---|---|---|
| `osl.asl` | Primary source (Oracc Cuneiform Sign List, ASL format) | 3,249 `@sign` entries |
| `1_unicodeSigns.csv` | Canonical Unicode Cuneiform reference (used to validate own-codes and resolve component glyphs) | 1,234 entries |
| `6_unicodeTrLit_Grph_Phon.csv` | Phonetic / syllabary reference, joined by `unicode_id` | 724 entries |
| `extract_allograph_v6.py` | Generation script (version 6.0) | — |

---

## 3. Unit Of Observation

**One row = one component position of one documented graphic form.**

- For a **simple** sign (atomic, no decomposition), the form corresponds to exactly one row.
- For a **compound** sign, the form is exploded into *N* rows, one per component, in left-to-right sequence order. All *N* rows share the same `graphic_variant_id` and `compound_form`, but each carries its own `unicode_id` and `component_position`.
- For a sign with **no nested `@form`** ("headless" in the working terminology of this project — meaning all of the sign's information sits in the `@sign` header, with nothing catalogued as an alternate name), the header itself is treated as the sign's only documented form, and `allograph_form` is left empty. 4,599 of the 7,238 rows (63.5%) fall into this category.

---

## 4. Column Reference

| # | Column | Type | Definition | Source field(s) in `osl.asl` |
|---|---|---|---|---|
| 1 | `unicode_id` | string | The Unicode code point (`U+XXXXX`) that applies to *this row*. For an atomic sign, its own code. For a compound row, the code of *that specific component*. Empty when no code exists or could be resolved. | `@list U+...` (own), or the corresponding token of `@useq` |
| 2 | `sign_grapheme` | string (glyph) | The actual cuneiform character for this row. For compound rows, this is the component's own glyph, not the full compound glyph (see `compound_grapheme` for that). | `@ucun` |
| 3 | `sign_structure` | categorical | Semantic classification of the row's structural status. See §5. | derived (see §5) |
| 4 | `structural_hint` | categorical | Secondary flag qualifying `sign_structure`. See §5. | derived |
| 5 | `component_position` | integer (1-based) | Position of this component within its compound form. Empty for non-compound rows. Populated both for explicit `@useq` decompositions and for `×` / `&` compounds resolved algorithmically against the full sign index. | derived from `@useq`, or from name-pattern decomposition |
| 6 | `sign_name` | string | The `@sign` entry this row belongs to (the sign's primary/scientific name). | `@sign` |
| 7 | `allograph_form` | string | The specific `@form` name (an attested alternate catalogue name for the same sign), if one exists. Empty for headless signs. | `@form` |
| 8 | `graphic_variant_id` | string | `{PREFIX}_v{N}`, where N numbers the distinct forms of `sign_name` **in the order they are documented in `osl.asl`**. All component rows of one compound form share the same id. **This is a documentation-order label, not a frequency or canonicality ranking** — see §6. | derived |
| 9 | `sign_type` | categorical | Mechanical classification based purely on presence of fields: `Type_1` (own `@list U+`), `Type_2` (`@useq` present, no own code), `Type_3` (neither). | derived |
| 10 | `compound_form` | string | For compound / atomic_with_decompositions rows, the name of the compound form itself (identical across all its component rows). | `@form` or `@sign` name |
| 11 | `compound_grapheme` | string (glyph) | The full glyph sequence of the compound as a whole (not the single-component glyph in column 2). | `@ucun` of the compound entity |
| 12 | `compound_unicode` | string | Semicolon-separated list of the component Unicode codes making up the compound, in sequence order. | `@useq` |
| 13 | `unicodeTrLit` | string | Scientific transliteration value associated with this row's `unicode_id`. | joined from `6_unicodeTrLit_Grph_Phon.csv` |
| 14 | `syllabary_sign` | string | Standard syllabary label for the sign. | joined from `6_unicodeTrLit_Grph_Phon.csv` |
| 15 | `phonetic_version` | string | Pipe-separated list of all attested phonetic reading versions for this sign. | joined from `6_unicodeTrLit_Grph_Phon.csv` |
| 16 | `signList_analogue` | string | Semicolon-separated list of cross-references to other historical sign catalogues (LAK, MZL, RSP, ABZL, etc.), each annotated with approximate period and region. | `@list` (all non-Unicode entries) |

---

## 5. Controlled Vocabularies

### 5.1 `sign_type` (mechanical, 3 values)

| Value | Condition | Row count |
|---|---|---|
| `Type_1` | Entity has its own `@list U+...` | 986 |
| `Type_2` | Entity has `@useq` (explicit or resolved from `×`/`&`), no own code | 5,591 |
| `Type_3` | Neither own code nor resolvable decomposition | 661 |

### 5.2 `sign_structure` (semantic, 4 values)

| Value | Condition | Row count |
|---|---|---|
| `atomic` | Own Unicode code, no `@useq` **or** code successfully inherited from the parent `@sign` (see `structural_hint`) | 1,173 |
| `atomic_with_decompositions` | Own Unicode code **and** a documented `@useq` — the sign received its own atomic code but its historical composition is also recorded | 12 |
| `compound` | No own code, but a component decomposition exists (explicit `@useq`, or successfully inferred from a `×`/`&` name) | 5,591 |
| `not_identified` | No own code, no resolvable decomposition | 462 |

### 5.3 `structural_hint`

| Value | Meaning | Row count |
|---|---|---|
| *(empty)* | No special condition | 6,861 |
| `inherited_from_parent` | Row has no code of its own; `unicode_id` was inherited from the parent `@sign`'s own code (classic case: an archaic catalogue form such as `LAK797` inheriting the code of its modern equivalent sign `A`). Kept out of `not_identified` deliberately, since the row *does* carry a usable Unicode value, just not one declared at its own level. | 199 |
| `compound_unresolved` | Name contains `×` or `&` (structurally a compound) but decomposition could not be resolved automatically — either because of nested parentheses (e.g. `\|GA₂×(A.EN)\|`) or because a named component could not be found in the sign index. `sign_structure` is `not_identified` for these rows, but the hint preserves the fact that a compound is suspected, for possible manual review. | 178 |

---

## 6. Known Methodological Limitations

These are documented explicitly so they can be cited or paraphrased directly in the methodology section of the thesis.

1. **`graphic_variant_id` reflects catalogue documentation order, not corpus frequency.** An earlier version of the pipeline ranked variants by how often a code was cross-referenced within the reference list itself, which risked being misread as "the standard/canonical form." The current version numbers variants purely by the order in which they are documented in `osl.asl`. Neither scheme reflects how often a variant was actually used by scribes; that requires a future join against attested ATF texts.

2. **`X` as a component value is a placeholder for an undeciphered sign**, following ATF convention, not a Unicode code point. 136 rows in this dataset contain `X` in `unicode_id` or `compound_unicode`. These rows should be excluded from any Unicode-keyed join.

3. **The `[unverified]` suffix on a `unicode_id`** (98 rows) marks a code that `osl.asl` records but that is not present in the canonical `1_unicodeSigns.csv` reference. Inspection of the `@uage` field for these entries shows they are not un-sourced errors: they carry values such as `ACN` or a Unicode Technical Committee document number (e.g. `L2/24-270`), indicating the code has been formally proposed to the Unicode Consortium but not yet ratified in a published version.

4. **462 rows (`not_identified`) have no usable `unicode_id`.** Of these, 178 are structurally suspected compounds that could not be automatically decomposed (`structural_hint = compound_unresolved`); the remainder are signs documented only by a modifier suffix (`@x`/`~x`) or by a historical catalogue number, with no Unicode assignment at all.

5. **Coverage is complete at the reference-list level (3,249 / 3,249 signs), not at the corpus level.** Absence of a sign from an actual text corpus, or its frequency within one, cannot be inferred from this file alone.

---

## 7. Example Rows

| sign_structure | sign_name | allograph_form | unicode_id | component_position | Note |
|---|---|---|---|---|---|
| atomic | `A` | `LAK797` | U+12000 | | `structural_hint = inherited_from_parent` |
| atomic_with_decompositions | `\|DUB.TI\|` | | U+1207F | | own code + documented `@useq` (DUB+TI) |
| compound | `\|A.A\|` | | U+12000 | 1 | headless sign, first of 2 components |
| compound | `\|A.A\|` | | U+12000 | 2 | second component, same `graphic_variant_id` |
| compound | `\|A.DU&A.DU\|` | | X | 2 | undeciphered component, per ATF convention |
| not_identified | `A@g` | | *(empty)* | | pure modifier variant, no code at any level |

---

*Generated from `extract_allograph_v6.py` (v6.0), verified against a live run on the project's `osl.asl`, `1_unicodeSigns.csv`, and `6_unicodeTrLit_Grph_Phon.csv`.*
