## 3. How Was compound_form_reading_table.csv Built?

This step, for each compound sign from osl.as, searches for its reading (complete, attested) across four leyers of sources
-  @v in osl.asl itself
- The Diri Table
- OGSL
- The modern syllabary
Instead of relying on the readings of its individual constituent signs.

The goal is to provide to the final dataset (Step 4) the compound as a whole word, rather than a random choose o single component sign. (Which often doesn't correspond at all to how the word was actually pronounced.)
The pipeline try to answer the questions:
- When this sequence of signs was read as a single word, what kind of word it was? 
- How do we know this?(from which source, with what degree of confidence).


## Data Sources

| Source | Description |
|---|---|
| **osl.asl** | Every compound sign, its components, and its own reading form `@v` field. |
| **diri_lexical_list.csv** *(Step 2)* | Digitised extract of the ancient Diri = watru series, 4,084 lines |
| **ogsl_sign_readings.json** | OGSL (Oracc Global Sign List), a cross-project consolidation of sign values drawn from ABZL, BAU, HZL, KWU, LAK, MZL, RSP, SLLHA and other historical catalogues. Parsed from `ogsl.zip`'s portal export: sign detail pages carry a `Values:` field, extracted as `{sign_name: [readings]}`, 2,170 signs. |
| **Syllabary_CM.csv** | Merged historical syllabary (CM + URUK2 + ADDITIONAL), 4,196 distinct names.(in Step 1) |

## Pipeline Overview

| Stage | Task | Output |
|---|---|---|
| **Stage 1** | Parse `osl.asl`, identify every compound, its components, and any `@v` readings |  distinct compounds |
| **Stage 2** | Normalise every compound's name (strip `\|...\|` pipes, fold Unicode subscripts to ASCII) | comparable key for the three name-matched sources |
| **Stage 3** | Resolve in priority order: `@v` → Diri → OGSL → Syllabary_CM | `ATTESTED_DIRECT`, tagged with which source supplied it |
| **Stage 4** | For compounds matched by none of the four, search for the name as a sub-sequence inside a longer, independently attested name | `NESTED_IN_LONGER_FORM` |
| **Stage 5** | Synthesise a fallback reading by concatenating each component's own individual reading | `component_reading_inferred` — a guess, never a fact |

**Output: `compound_form_reading_table.csv`**, 2,178 rows.

**Note:**     
**ATTESTED_DIRECT** a status indicating that the compound has a real, fully attested reading found in at least one of four sources (OSL/DIRI/OGSL/SYLLABARY_CM).

**NESTED_IN_LONGER_FORM**  a status for a compound that has no reading of its own, but is documented only as part of a longer, separately attested sequence—that is, it has never been read as an independent word.

**component_reading_inferred** a compund's guess, not a fact: a reading obtained by simply hyphenating the readings of each component of the compound separately, this is filled in regardless of the status above and should never be considered a real attested reading.

## Step-by-Step Description

### 1.Pass Through Four Dataset

1. **`@v` in `osl.asl`**  tied directly to the entity, no name-matching risk. **1,275 compounds**.
2. **Diri** the ancient primary source itself. Checked before any modern compilation. **42 compounds**.
3. **OGSL**  project which consolidate historical paper sign lists. **18 compounds**.
4. **Syllabary_CM** — broadest modern compilation. **69 compounds**.

Combined: **1,404 of 2,178 compounds** have an attested whole-word reading.

### 2. Difference of `.` in Diri and `.` osl.asl  

The dot `.` in osl.asl means only one thing: "this sign is composed of several other signs." This is a structural fact about the writing form.    
"Diri" in a strictly scientific sense is a different, linguistic statement: the reading of such a sign cannot be guessed simply by knowing the readings of its component parts.
The dot says nothing about whether the reading can be guessed or not.    

**Can we verify this?** Only for compounds that are confirmed specifically through the Diri table (diri_lexical_list.csv). The rest are confirmed via @v within osl.asl (most likely, the editors of osl.asl also took these readings from Diri or similar lists, but osl.asl itself does not say where exactly, we have reading but dont know the sources)

### 3. Compound Categorization

Each compound is classified into exactly one of six mutually exclusive categories by the operator in the name (`.`, `×`,`&`, `+`,`mixed (. + ×/&)`,`other`), after which the share of ATTESTED_DIRECT and the breakdown by source (OSL/DIRI/OGSL/SYLLABARY_CM) are calculated within each category.

`.` sequences are attested far more often than `×`/`&` compounds.    
 `×`/`&` compounds are more often a documented **graphic** form  than an independently attested **spoken** word.
`×`has almost no overlap with DIRI
`.` not equal DIRI: the presence of a dot only means "a documented sequence of characters" and does not guarantee that the reading is unpredictable from the parts

### 4. The "Other" Category, Fully Identified
- `3/4(GUR)`?
- `O`?
- `OO`?


**Note:**    
`|A.AB.BA|` (`NO_ATTESTED_READING`) in `osl.asl`have  `@inote` "writing for Tiʾamat in Tiʾamat-bašti".     
`@compoundonly` There is no @sign block of its own in `osl.asl` 


### 5. Not attested reading (Guessed Compounds ,`component_reading_inferred`)

Each compound's components read individually (their own first-listed reading) and hyphen-joined. Explicitly a guess, not an attested fact, diri-writing exists precisely because a compound's real reading is not guaranteed to equal its components' concatenation.

## Output Description
**`compound_form_reading_table.csv`** — 2,176 rows

●	**`compound_form`** the compound's name, exactly as documented in `osl.asl`. 
●   **`compound_form_normalized`** without pipes (|...|)
●	**`PhoneticVersion_Compound`** attested whole-word reading(s), pipe-separated `ATTESTED_DIRECT` unless Empty.   
●	**`reading_status`** `ATTESTED_DIRECT` / `NESTED_IN_LONGER_FORM` / `NO_ATTESTED_READING`.
●	**`reading_source`** `OSL` / `DIRI` / `OGSL` / `SYLLABARY_CM`, in priority order; empty otherwise.
●	**`nested_in_forms`** for `NESTED_IN_LONGER_FORM` rows, the longer attested name this compound is documented as part of. Semicolon-separated. 
●	**`component_reading_inferred`** hyphen-joined concatenation of each component's own reading. 



