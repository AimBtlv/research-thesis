## 2. How Created allograph_all_v6?

This step takes the Unicode + Phonetic Version catalogue produced in Step 1 (`unicodePhoneticVersion_full.csv`, 1,235 signs) and combines it with the full structural content of the ORACC Sign List (`osl.asl`) to build a single table that answers, for every attested cuneiform sign, three questions:    
**1. what Unicode identity does it carry?**   
**2. what is it built from, if it is a compound?**    
**3. what phonetic readings does it share with its component or parent signs**? 

Signs in `osl.asl` are not a flat list, they are catalogued either as an independent `@sign` (a scientific/basic name) or as a `@form` nested inside a `@sign` (an attested alternate catalogue name for the same underlying sign, such as an archaic Deimel number (LAK240)). Some signs are atomic, some are explicitly built from other signs (`@useq`), some are written as a visual combination of other signs without any formal decomposition on record, and some are documented only by name, with no Unicode identity at all. The purpose of this step is to resolve each of these situations consistently, so that a downstream researcher can query the table by Unicode ID, by sign name, or by component, and always get a structurally correct answer, rather than treating undocumented and compound signs as if they were equivalent, or discarding signs that the underlying source records only partially.

## Data Sources

| Source | Description |
|---|---|
| **ORACC Sign List** `osl.asl` | Machine-readable ORACC Sign List. Encodes sign names (`@sign`), alternate catalogue names (`@form`), Unicode IDs (`@list U+...`), compound decompositions (`@useq`), glyphs (`@ucun`), and cross-references to historical paper catalogues (`@list <catalogue-code>`). |
| **Unicode Cuneiform Reference** `1_unicodeSigns.csv` | Canonical list of 1,234 ratified Unicode Cuneiform code points, produced independently of `osl.asl`. Used to verify that a code claimed in `osl.asl` is actually a published Unicode code point. |
| **Unicode + Phonetic Catalogue** `unicodePhoneticVersion_full.csv` (Step 1 output) | 1,235-entry table of `unicode_id → unicodeTrLit / syllabarySign / PhoneticsVersion`. Used as the lookup table joined into every row of this dataset. |

## Pipeline Overview

The pipeline was built in two iterations. The first iteration parsed only the `@form` sub-entries of each `@sign` block, which covered 604 of the 3,249 signs in the file (18.6%): the remaining 2,645 signs record all of their information directly in the `@sign` header, with no nested `@form`, and were entirely absent from the first iteration's output. The second, final iteration parses every `@sign` header as a first-class entity in its own right, whether or not it has nested forms, achieving complete coverage.

The final pipeline runs in three passes over the full sign list:

| Pass | Task | Output |
|---|---|---|
| **Pass 1** | Parse every `@sign` and `@form` entity; classify each into `sign_type` and `sign_structure`; decompose compounds into components | 7,238 rows (one per component position) covering all 3,249 signs |
| **Pass 2** | Assign `graphic_variant_id` to every row, numbering each sign's distinct documented forms in the order they appear in `osl.asl` | same rows, `graphic_variant_id` populated |
| **Pass 3** | Join `unicodeTrLit`, `syllabary_sign`, `phonetic_version` from the Step 1 catalogue, matched by `unicode_id` | same rows, phonetic fields populated where a match exists |

**Output: `allograph_all_v6.csv`**, 7,238 rows, 3,249 unique signs (100% coverage).

## Step-by-Step Description

### 1. Parsing At Full Sign Coverage

The parser walks every `@sign` block in `osl.asl`. If the block contains one or more `@form` sub-entries, each form is processed as its own entity, with the parent `@sign` header kept only as a fallback. If the block contains no `@form` at all ("headless" in the working terminology of this project, meaning the sign has no attested alternate catalogue name), the header itself is processed as the sign's sole documented entity. This single design choice is what raises coverage from 604 to all 3,249 signs.

### 2. Subdividing Signs Into Three Types (`sign_type`)

Every parsed entity is classified mechanically, based only on which fields are present:

●	**Type_1** — the entity carries its own `@list U+...` code.
●	**Type_2** — the entity carries an explicit `@useq` (documented component sequence), with no code of its own.
●	**Type_3** — neither is present.

This classification is purely structural (it does not interpret meaning), and it is the same rule applied uniformly whether the entity is a `@sign` header or a `@form`.

### 3. Categorizing Signs Into Single vs. Compound (`sign_structure`)

`sign_type` alone is not sufficient to describe a sign's actual composition, because two situations cut across it. First, eleven signs (e.g. `|DUB.TI|`, `GI`) carry **both** their own Unicode code **and** a documented `@useq`: they became common enough to receive a dedicated atomic code, while their compositional origin remains separately recorded. Second, most Type_3 signs are not compounds at all, they are glyph-variant markers (`A@g`, `A@t`) or names known only from historical paper catalogues (`LAK240`, `BAU067`), with no compositional structure whatsoever; treating them the same as genuine unresolved compounds would misrepresent them in any later network analysis.

`sign_structure` resolves this with four values:

| Value | Condition | 
|---|---|
| `atomic` | Own code, no `@useq` (or a code inherited from the parent sign, see below) |
| `atomic_with_decompositions` | Own code **and** documented `@useq` |
| `compound` | No own code, but a component decomposition exists |
| `not_identified` | No own code, no resolvable decomposition |

A secondary field, `structural_hint`, records two situations that would otherwise be lost inside these four values: `inherited_from_parent` marks a row whose `unicode_id` was not declared at its own level but successfully inherited from its parent `@sign` (the classic case: the archaic catalogue form `LAK797` inheriting the code of its modern equivalent sign `A`), and `compound_unresolved` marks a name that structurally contains `×` or `&` (implying a compound) but whose components could not be automatically resolved (see Step 4), so it is kept honestly as `not_identified` rather than silently forced into `compound` with missing data.

### 4. Decomposing Compound Signs Into Components

For signs classified as `compound`, the component sequence is obtained in one of two ways. Where `osl.asl` records an explicit `@useq`, the sequence is read directly. Where no `@useq` is present but the sign's name contains `×` (juxtaposition) or `&` (ligature), an automatic decomposition routine splits the name at the operator and attempts to resolve each resulting component against the full index of all 3,249 signs. This recovered 307 of 348 (88%) tested juxtaposition compounds and 22 of 23 (96%) tested ligature compounds where the name contained no nested parentheses; names with nested parentheses (e.g. `|GA₂×(A.EN)|`) were left for the `compound_unresolved` flag described above rather than guessed at.

Every compound entity is then exploded into one row per component, and four columns together reveal its full composition:

●	**`component_position`** — the 1-based position of this specific component within the sequence (left to right).
●	**`compound_form`** — the name of the compound as a whole, identical across all of its component rows.
●	**`compound_grapheme`** — the full glyph sequence of the compound (not the single-component glyph).
●	**`compound_unicode`** — the semicolon-separated list of all component codes, in sequence order.

Each row's own `unicode_id` and `sign_grapheme` (columns 1 and 2) describe that one component specifically, while `compound_form` / `compound_grapheme` / `compound_unicode` describe the compound as a whole, so a single compound sign is fully readable both at the component level and as an aggregate from the same set of rows.

### 5. Assigning `graphic_variant_id`

Each sign's distinct documented forms are numbered `{PREFIX}_v1`, `_v2`, ... in the order they are **documented in `osl.asl`**. All component rows belonging to one compound form share the same id, since they represent one physical attestation, not separate variants. This id is a structural/documentation-order label; it does not claim which variant was more common in real texts, that question is reserved for a later stage once this table is joined against attested corpus texts.

### 6. Assigning Phonetic Version, Transliteration, And Syllabary Sign

Every row's `unicode_id` is looked up against the Step 1 catalogue (`unicodePhoneticVersion_full.csv`), and three fields are copied in where a match is found:

●	**`unicodeTrLit`** — the transliteration derived from the sign's Unicode character name.
●	**`syllabary_sign`** — the scientific sign name as used in Assyriological citation.
●	**`phonetic_version`** — the full pipe-separated list of attested phonetic readings.

Because this join uses the same `unicode_id` key that Step 1 built, every sign's phonetic profile is inherited automatically, no separate phonetic lookup was re-implemented for this stage. The join matched 5,663 of 7,238 rows (78.2%); the unmatched remainder is fully accounted for by rows with no usable `unicode_id`: 136 rows carry the undeciphered-sign placeholder `X`, and 462 rows are `not_identified` and have no `unicode_id` to look up in the first place.

### 7. Role Of The Other Historical Catalogues (`signList_analogue`)

Beyond Unicode, `osl.asl` cross-references each sign against up to fifteen other historical sign-list systems (`LAK`, `MZL`, `RSP`, `ABZL`, `ELLES`, `KWU`, `BAU`, `ASY`, `GCSL`, `PTACE`, `HZL`, `SYA`, `ZATU`, `REC`, and others). These are not Unicode codes, they are references to paper catalogues compiled at different points in the history of Assyriology, each associated with a particular period and scholarly tradition (e.g. `LAK` for the Uruk archaic corpus, `ABZL` for Old Babylonian school texts, `MZL` for standard Babylonian). `signList_analogue` collects every such reference attached to a sign, annotated with its approximate period and region, into one semicolon-separated field. Its role in this dataset is traceability: it lets a sign found in this table be cross-checked against the specific secondary-literature catalogue a philologist would recognize, and it gives an approximate chronological/regional anchor for a sign even before any corpus text has been joined.

## Output Description

**`allograph_all_v6.csv`** — 7,238 rows, 3,249 unique signs (100% of `osl.asl`).

●	**`unicode_id`** — Unicode code point for this specific row (own, inherited, or a compound component). Empty where none could be resolved. Source: `osl.asl` (`@list U+`, `@useq`), verified against `1_unicodeSigns.csv`.
●	**`sign_grapheme`** — Glyph for this row (component-level for compound rows). Source: `@ucun`.
●	**`sign_structure`** / **`structural_hint`** — Semantic classification (`atomic` / `atomic_with_decompositions` / `compound` / `not_identified`) and its qualifying flag. Derived.
●	**`component_position`** / **`compound_form`** / **`compound_grapheme`** / **`compound_unicode`** — Full decomposition of compound signs, explicit or algorithmically inferred. Derived from `@useq` or name-pattern decomposition.
●	**`sign_name`** / **`allograph_form`** — The sign's primary name and its specific attested alternate catalogue name, where one exists. Source: `@sign`, `@form`.
●	**`graphic_variant_id`** — Documentation-order label distinguishing a sign's differently-documented forms. Derived.
●	**`sign_type`** — Mechanical `Type_1` / `Type_2` / `Type_3` classification. Derived.
●	**`unicodeTrLit`** / **`syllabary_sign`** / **`phonetic_version`** — Phonetic and syllabic reading data, inherited from the Step 1 catalogue by `unicode_id` join. Source: `unicodePhoneticVersion_full.csv`.
●	**`signList_analogue`** — Cross-references to other historical sign catalogues, annotated with period and region. Source: `osl.asl` (`@list`, non-Unicode entries).
