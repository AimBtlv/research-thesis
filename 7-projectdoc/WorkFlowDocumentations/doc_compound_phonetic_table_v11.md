## 3. How Was compound_form_reading_table.csv Built?

For every compound sign documented in `osl.asl` (a sign written as a sequence, ligature, or fusion of other signs), this table answers one question: when this sequence is read as a single word, what was it actually called? Four sources are checked, in order of authority: `osl.asl`'s own `@v` field, the digitised ancient Diri lexical series (Step 2), OGSL (a cross-project consolidation of historical sign lists), and the merged historical syllabary as a last resort.

## Data Sources

| Source | Description |
|---|---|
| **osl.asl** | Every compound sign, its components, and (where present) its own `@v` field. |
| **diri_lexical_list.csv** *(Step 2)* | Digitised extract of the ancient Diri = watru series, 4,084 lines, 115 texts. |
| **ogsl_sign_readings.json** | OGSL (Oracc Global Sign List), a cross-project consolidation of sign values drawn from ABZL, BAU, HZL, KWU, LAK, MZL, RSP, SLLHA and other historical catalogues. Parsed from `ogsl.zip`'s portal export: sign detail pages carry a `Values:` field, extracted as `{sign_name: [readings]}`, 2,170 signs. |
| **Syllabary_CM.csv** | Merged historical syllabary (CM + URUK2 + ADDITIONAL), 4,196 distinct names, 21,460 readings. Lowest priority: the most general secondary compilation. |

## Pipeline Overview

| Stage | Task | Output |
|---|---|---|
| **Stage 1** | Parse `osl.asl`; identify every compound, its components, and any `@v` readings | 2,178 distinct compounds |
| **Stage 2** | Normalise every compound's name (strip `\|...\|` pipes, fold Unicode subscripts to ASCII) | comparable key for the three name-matched sources |
| **Stage 3** | Resolve in priority order: `@v` → Diri → OGSL → Syllabary_CM | `ATTESTED_DIRECT`, tagged with which source supplied it |
| **Stage 4** | For compounds matched by none of the four, search for the name as a sub-sequence inside a longer, independently attested name | `NESTED_IN_LONGER_FORM` |
| **Stage 5** | Synthesise a fallback reading by concatenating each component's own individual reading | `component_reading_inferred` — a guess, never a fact |

**Output: `compound_form_reading_table.csv`**, 2,178 rows.

## Step-by-Step Description

### 1. Four-Tier Resolution, In Order Of Authority

1. **`@v` in `osl.asl`** — tied directly to the entity, no name-matching risk. **1,275 compounds (58.5%)**.
2. **Diri** — the ancient primary source itself. Checked before any modern compilation. **42 compounds (1.9%)**.
3. **OGSL** — cross-project consolidation of historical paper sign lists. **18 compounds (0.8%)**.
4. **Syllabary_CM** — broadest modern compilation, used only as the final fallback. **69 compounds (3.2%)**.

Combined: **1,404 of 2,178 compounds (64.5%)** have an attested whole-word reading.

### 2. "`.` = diri" Is A Common But Imprecise Shorthand — Corrected Here

An important terminological correction made during this project: `.` in `osl.asl`'s naming convention marks a documented **sequence** of signs, structurally. It does **not** by itself mean the reading is *unpredictable* from its parts (true diri, in the strict philological sense — see Step 2). Testing this directly is possible for the 32 compounds whose reading is confirmed specifically via the Diri source (as opposed to the 998 confirmed only via `osl.asl`'s own `@v`, which likely also draws on Diri and other lists during its own compilation, but cannot be independently cited back to a specific tablet the way this project's own Diri extract can).

An attempt to test this more broadly — comparing each compound's real attested reading against a naive concatenation of its components' own readings — was tried and found **unreliable**: the phonetic catalogue lists each sign's readings alphabetically, not by frequency, so a "first listed reading" comparison is contaminated by picking an atypical value (e.g. sign `A`'s alphabetically-first reading is the rare `'U4`, not the common `a`). This was identified, tested, and explicitly retracted as a method during the project rather than presented as a finding.

### 3. Coverage By Operator Type — A Real Structural Pattern

Categories are mutually exclusive (a compound with both `.` and `×` is counted once, as `mixed`, not double-counted under `.`):

| Category | Total | ATTESTED | NESTED | NONE | % attested |
|---|---|---|---|---|---|
| `.` | 1,450 | 1,092–1,093 | 47 | 310–311 | ~75.3% |
| `mixed (. + ×/&)` | ~300 | ~190 | ~5 | ~105 | ~63% |
| `&` | 34 | 11 | 8 | 15 | 32.4% |
| `+` | 8 | 3 | 0 | 5 | 37.5% |
| `×` | ~380 | ~105 | 29 | ~248 | ~27% |
| other | 3 | 3 | 0 | 0 | 100% |

`.`-sequences are attested far more often than `×`/`&` compounds. This is a real linguistic pattern: `×`/`&` compounds are far more often a documented **graphic** form (a fused sign shape recorded in a palaeographic catalogue) than an independently attested **spoken** word.

**Among unattested compounds specifically**, the majority (411 of 685, ~60%) are still `.`-type, not `×`/`&` — despite `.` having the higher attestation *rate* overall, it is also by far the largest pool, so it still contributes the largest *absolute* count of gaps. For `×`/`&` compounds, an unattested status is most likely permanent (graphic-only forms rarely gain a reading). For `.` compounds, it is more likely a **coverage gap**: the Diri series is only ~50% digitised (Step 2), so a real ancient reading plausibly exists on a tablet not yet found.

### 4. The "Other" Category, Fully Identified

Only 3 entries after excluding `+` into its own category and fixing the parsing issues below:

●	`3/4(GUR)` — a metrological fraction notation (dry-capacity measure), not a sign compound in the usual sense.
●	`O`, `OO` — investigated individually. `O` carries `@fake 1` in `osl.asl` (an explicit synthetic-placeholder flag) and is now excluded from the inventory entirely (see Step 4). `OO` is *not* fake — it is a genuinely documented ATF convention ("the notation oo... is used to transliterate space left to indicate zero") and is correctly retained.

### 5. One Divine-Name Case, Investigated In Full

`|A.AB.BA|` (`NO_ATTESTED_READING`) was checked directly against its `osl.asl` entry: `@inote "writing for Tiʾamat in Tiʾamat-bašti"`. This is a one-off logographic spelling of the divine name Tiʾamat in a specific royal inscription, not general vocabulary — the kind of entry lexical lists like Diri were never compiled to catalogue. Checking systematically found this explains only 6 of 685 unattested compounds; it is a real but minor category, not the dominant explanation (see §3 above for the dominant one).

### 6. `@compoundonly` — Investigated, No Fix Required

`osl.asl` separately declares 142 sign names via a standalone `@compoundonly` directive, outside any `@sign` block, meaning these shapes are acknowledged to exist only as parts of other, already-documented compounds. None have their own `@sign` entry at all, so they never appear as phantom rows in this pipeline. A causal check — do any of the 100 `compound_unresolved` signs fail their `×`/`&` decomposition specifically because a component is one of these `@compoundonly` names, absent from the lookup index? — found exactly **2** confirmed cases (`|MUD₃@g×GU|`, `|AB×LAK178|`). Left unfixed given the small scale; documented here as a known, quantified limitation.

### 7. Synthesised Component Reading (`component_reading_inferred`)

Each compound's components read individually (their own first-listed reading) and hyphen-joined. **2,018 of 2,178 (92.6%)**. ⚠️ Explicitly a guess, not an attested fact — diri-writing exists precisely because a compound's real reading is not guaranteed to equal its components' concatenation. This field must never be confused with `nested_in_forms`: 599 of the 685 `NO_ATTESTED_READING` compounds have a populated `component_reading_inferred`, but **zero** of them have anything in `nested_in_forms` — the two fields answer unrelated questions ("what might this read, guessed from its own parts" vs. "is this compound documented only as part of a longer one").

## Output Description

●	**`compound_form`** / **`compound_form_normalized`** — name as documented, and its lookup key.
●	**`PhoneticVersion_Compound`** — attested whole-word reading(s), pipe-separated. Empty unless `ATTESTED_DIRECT`.
●	**`reading_status`** — `ATTESTED_DIRECT` / `NESTED_IN_LONGER_FORM` / `NO_ATTESTED_READING`.
●	**`reading_source`** — `OSL` / `DIRI` / `OGSL` / `SYLLABARY_CM`, in priority order; empty otherwise.
●	**`nested_in_forms`** — longer attested name(s) this compound is documented as part of, semicolon-separated.
●	**`component_reading_inferred`** — synthesised guess. Never an attested value.

## Summary

| `reading_status` | Count | Share |
|---|---|---|
| `ATTESTED_DIRECT` | 1,404 | 64.5% |
| — via `OSL` | 1,275 | 58.5% |
| — via `DIRI` | 42 | 1.9% |
| — via `OGSL` | 18 | 0.8% |
| — via `SYLLABARY_CM` | 69 | 3.2% |
| `NESTED_IN_LONGER_FORM` | 89 | 4.1% |
| `NO_ATTESTED_READING` | 685 | 31.5% |
| **Total** | **2,178** | **100%** |
