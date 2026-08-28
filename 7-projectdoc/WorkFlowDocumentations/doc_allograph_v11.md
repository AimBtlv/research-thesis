## 4. How Was allograph_all_v11.csv Built?

This step produces the complete sign-level dataset: for every sign documented anywhere in the available sources, its Unicode identity, its structural composition (simple sign or compound, and if compound, exactly which components it decomposes into), and its phonetic reading, drawing on Step 3's compound reading table wherever a sign is a compound.

## Data Sources

| Source | Description |
|---|---|
| **osl.asl** | ORACC Cuneiform Sign List — the structural backbone. |
| **Unicode + Phonetic Catalogue** *(Step 1)* | `unicode_id → unicodeTrLit / syllabarySign / PhoneticsVersion`. |
| **compound_form_reading_table.csv** *(Step 3)* | Per-compound reading, resolved through four tiers. |
| **diri_lexical_list.csv** / **ogsl_sign_readings.json** | Used a second time here, directly, as a name-keyed fallback for signs the unicode-keyed Step 1 catalogue cannot help — see §4 below. |
| **Syllabary_CM.csv** | For sign names attested nowhere in `osl.asl` at all. |

## Editorial Markers In osl.asl That Change How It Must Be Parsed

A systematic audit of every `@`-tag in the file (not only the ones already known to be needed) found three markers that materially affect correctness, beyond the ordinary `@sign` / `@form` / `@useq` / `@v` structure already documented:

●	**`@sign-` (60 occurrences) and `@form-` (31 occurrences)** — hyphen immediately after the tag name, no space. This is not a typo: it is `osl.asl`'s own editorial convention for marking an entry explicitly **spurious, deprecated, or "do not use"** (`@note "spurious, too"`, `@inote "Do not use: this is ANŠE.ARAD with ARAD written UŠ"`, `@note "which is deprecated"`). A parser that only recognises `@sign ` / `@form ` (with a space) does not see these as block boundaries at all — their content silently merges into whichever valid entry precedes them, corrupting it with a stray, explicitly-rejected entity's data. This was discovered by tracing a specific anomaly: `|KA@KA|`, a name with no data of its own beyond an object ID, was found carrying components, glyphs, and a reading (`babila`) that in fact belonged to the *following* block, `|KA.AN|` — merged in only because the block between them, `@sign- |KA.AN|`... no — the entry itself, marked with the hyphen convention, was never recognised as starting a new block. The same mechanism explained an older, previously unresolved anomaly: `|A×BAD|` had been carrying Unicode code `U+12003`, which in fact belongs to a *different*, explicitly spurious entry (`@sign- |A×GAN₂@t|`, `@note "LAK800 is |A×GAN₂@g|, which is spurious, too"`) that had merged into it under the old parsing. Both are now resolved: `|KA@KA|` correctly has no data, and `|A×BAD|` correctly resolves to `|A.BAD|`, reading *agam*.
●	**`@fake 1`** (40 occurrences) — an explicit flag for synthetic placeholder entities that are not real signs (e.g. a "temporary sign" created as an ATF-processor workaround, or technical notation markers). Only 2 of the 40 had been noticed before this audit, by accident, via an unrelated "what does the leftover 'other' category contain" check. All 40 are now excluded from the inventory.
●	**`@compoundonly`** (142 occurrences) — a standalone directive (not nested in any `@sign` block) acknowledging that a given shape exists only as part of another, already-documented compound. Investigated and found to require **no fix**: since these names never have their own `@sign` entry, they were never at risk of appearing as phantom rows. See the Step 3 documentation for the related, and separate, causal check on `compound_unresolved` signs.
●	**`@v-`** (168 occurrences) — the same hyphen convention applied to individual readings within an otherwise-valid sign (marking one specific proposed reading as rejected, e.g. `@inote "collate this--does it really exist?"`). Checked directly: the existing `@v` parsing regex requires whitespace immediately after `@v`, which `@v-` does not have, so these were already correctly excluded without any code change needed.

## Extending Coverage With Diri/OGSL By Name, Not Just By Unicode

Two categories of row cannot be enriched by the unicode-keyed Step 1 catalogue, because the Step 1 catalogue is joined by `unicode_id` and these rows either lack a working code or a documented reading for the code they have. Diri and OGSL, being keyed by **sign name** rather than Unicode identity, can still help:

●	**`Single Sign Reading` rows with an empty `phonetic_version`** (294 originally): checked whether the sign's own name resolves in Diri or OGSL. **67 closed** (18 via Diri, 165 via OGSL — the discrepancy in reporting order reflects Diri being checked first per row; totals are counted per-row not per-unique-name). 226 remain genuinely unattested even by these sources.
●	**`No Sign Identity` rows** (signs with no Unicode code at all, 462 originally): the same by-name lookup. **116–118 given a real, attested reading despite having no Unicode identity** — direct evidence that "not encoded in Unicode" and "not linguistically attested" are two different, independent facts about a sign.

Both fallback cases are flagged in `structural_hint` (`phonetic_via_diri` / `phonetic_via_ogsl`) rather than merged silently into the Step 1-sourced readings, so provenance remains visible per row.

## Sign Classification (Unchanged In Method, Now On Corrected Input)

Every entity is still classified as `atomic` (own Unicode code, no `@useq`), `atomic_with_decompositions` (own code *and* documented `@useq`), `compound` (no own code, but a decomposition exists — explicit or algorithmically resolved from `×`/`&`), or `not_identified` (neither). `structural_hint = inherited_from_parent` marks a code inherited from a parent entity (e.g. an archaic catalogue form inheriting its modern equivalent's code); `structural_hint = compound_unresolved` marks a `×`/`&` name whose components could not be automatically resolved (103 cases; 2 of these specifically because a component is an `@compoundonly` shape with no independent Unicode lookup entry — see Step 3 §6).

## Output Description

Column set unchanged from the established schema: `unicode_id, sign_grapheme, sign_source, sign_structure, structural_hint, component_position, sign_name, allograph_form, graphic_variant_id, sign_type, compound_form, compound_grapheme, compound_unicode, unicodeTrLit, syllabary_sign, typePhonetic_Version, phonetic_version, signList_analogue`. `structural_hint` now additionally carries the two fallback-provenance values described above, alongside its two pre-existing values.

## Summary

| | Count |
|---|---|
| Total rows | 9,603 |
| Unique `sign_name` | 5,610 |
| `sign_source = OSL` | 7,202 |
| `sign_source` = syllabary-only (Uruk2 / Syllabary_CM / Additional Sources) | 2,401 |

| `typePhonetic_Version` | Rows |
|---|---|
| `Attested Compound Reading` | 3,659 |
| `Single Sign Reading` | 3,580 |
| `No Attested Compound Reading` | 1,739 |
| `No Sign Identity` | 426 |
| `Compound Nested in Longer Form` | 199 |

| `structural_hint` | Rows |
|---|---|
| `inherited_from_parent` | 199 |
| `phonetic_via_ogsl` | 165 |
| `compound_unresolved` | 103 |
| `phonetic_via_diri` | 17 |
