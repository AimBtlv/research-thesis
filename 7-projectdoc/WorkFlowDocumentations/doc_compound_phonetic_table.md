## 2. How Was compound_form_reading_table.csv Built?

For every compound sign documented in `osl.asl` (a sign written as a sequence, ligature, or fusion of other signs) and other catalogue  this table answers one question:  A compound sign's *components*  have their own individual reading or  compound *as a whole*?


## Data Sources

| Source | Description |
|---|---|
| **osl.asl** | Every compound sign, its components, and (where present) the `@v` field listing its directly attested readings, read under the compound's own `@sign` header or `@form` block. |
| **Syllabary_CM.csv** | Merged historical syllabary: CM (19,274 readings, Prof. M.Maiocchi) + URUK2 (2,122, archaic Uruk period) + ADDITIONAL (64, supplementary/rare forms). 4,196 distinct sign names, 21,460 total attested readings. Used only where `osl.asl` itself has no `@v` for a compound. |

## Pipeline Overview

| Stage | Task | Output |
|---|---|---|
| **Stage 1** | Parse `osl.asl`, identify every compound sign, its components, and any `@v` readings attested directly under it |  distinct compounds,  entities with at least one attested reading |
| **Stage 2** | Normalise every compound's name (strip ORACC `\|...\|` pipes, fold Unicode subscript digits to ASCII) | comparable name for the syllabary fallback |
| **Stage 3** | For compounds with no `@v`, look up the normalised name in the merged syllabary *Syllabary_CM.csv**  | secondary `ATTESTED_DIRECT` source |
| **Stage 4** | For compounds with neither, search for the name as a sub-sequence inside a longer, independently attested name | `NESTED_IN_LONGER_FORM` where found |
| **Stage 5** | For every compound, attempt a synthesised reading by concatenating each component's own individual reading | `component_reading_inferred`, populated only when *all* components have one |

**Output: `compound_form_reading_table.csv`**, 2,176 rows, one per distinct compound sign.

## Step-by-Step Description

### 1. `@v`: The Primary Source

In `osl.asl` `@v` is the Variant of Phonetic Version of the Sign.  For a compound such as `|A.A|`, these `@v` lines are the compound's own attested readings, not a component's. This is checked **before** any external source
### 2. Name Normalisation (For The Syllabary Fallback)

Where `osl.asl` has no `@v` for a compound, the fallback(alternative) is the historical syllabary, which uses a different naming convention. Before lookup, the compound's name is normalised: pipes stripped, subscript digits folded to ASCII.

### 3. Syllabary Fallback (`SYLLABARY_CM`)

The normalised name is looked up against the merged syllabary(**Syllabary_CM.csv** ). This recovers  compound, mostly diri-writings (`.`joined sequences) whose reading tradition was documented by Prof. Maiocchi's syllabary but not carried into `osl.asl`'s own `@v` field.

Combined, `@v` and the syllabary together give  compounds  an attested whole-word reading.Coverage remains strongly uneven by compound type: `.` ("diri" sequence read as one word) is more higher  , when  `×` (juxtaposition/fusion), `&` (ligature)  much lower.

### 4. Nested-Form Fallback (`NESTED_IN_LONGER_FORM`)

For a name with neither an `@v` nor a syllabary match  **Syllabary_CM.csv** , the table checks whether it occurs as a documented sub-sequence inside a longer, independently attested compound name.

```
|A.BU| no reading of its own, but occurs inside  SI.A.BUR2
```

### 5. ?Synthesised Component Reading (`component_reading_inferred`) 

As a separate, lower-confidence fallback, each compound's components are read individually (their own first attested reading) and joined with hyphens, e.g. `|A.AB.BA|` to `u4-ab-ba`. 

## Output Description

**`compound_form_reading_table.csv`** — 2,176 rows, one per distinct compound sign.

●	**`compound_form`**  the compound's name, exactly as documented in `osl.asl`.    
●	**`compound_form_normalized`** pipes stripped, subscript digits folded to ASCII, the syllabary lookup key.     
●	**`PhoneticVersion_Compound`** —the compound's attested whole-word reading, pipe-separated, populated only for `ATTESTED_DIRECT` rows. Empty otherwise.     
●	**`reading_status`**  `ATTESTED_DIRECT` / `NESTED_IN_LONGER_FORM` / `NO_ATTESTED_READING`.     
●	**`reading_source`**  `OSL` or `SYLLABARY_CM` for `ATTESTED_DIRECT` rows, empty otherwise. Records which source actually supplied the reading.     
●	**`nested_in_forms`**  for `NESTED_IN_LONGER_FORM` rows, the longer attested name this compound is documented as part of. Semicolon-separated.    
●	**`component_reading_inferred`**   hyphen-joined concatenation of each component's own reading. 

