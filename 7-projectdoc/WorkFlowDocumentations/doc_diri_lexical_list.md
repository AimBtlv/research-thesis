# Data Dictionary: diri_lexical_list.csv

**Digitised Extract of the Ancient Diri Lexical Series (Diri = watru)**

---

## Research Question / Purpose

Every other phonetic source used so far in this project (`osl.asl`'s `@v` tags, the merged historical syllabary) is a *modern scholarly compilation*, assembled by researchers cross-referencing many original tablets. This dataset is different in kind: it is a direct digitised transcription of the **ancient teaching texts themselves**, the actual lexical lists that Mesopotamian scribal students copied and memorised to learn compound sign readings.

The series is called **Diri**, named after its first, most famous entry: the sign sequence `SI.A`, conventionally read *diri* ("exceeding, surplus"). In its standard modern edition it comprises seven tablets and roughly 2,100 entries (Civil et al., *Materials for the Sumerian Lexicon* vol. 15, 1969, hereafter MSL 15). A Diri entry is a documented case where a sequence of signs was read as a single word whose pronunciation is not predictable from the signs' individual values, exactly the phenomenon this project's `compound_form_reading_table.csv` was built to capture, but sourced here directly from a named, citable ancient text rather than inferred from cross-referenced modern catalogues.

## Data Sources

| Source | Description |
|---|---|
| **ORACC / DCCLT** | Digital Corpus of Cuneiform Lexical Texts, part of the Open Richly Annotated Cuneiform Corpus consortium. Publishes machine-readable (JSON) editions of lexical texts, including Diri exemplars from multiple sites and periods. Released under Creative Commons Attribution Share-Alike 3.0. |
| **catalogue.json** | The DCCLT/signlists project catalogue (2,444 entries), used to identify which specific tablets belong to the Diri series via the `subgenre` field (`Diri`, `OB Nippur Diri`, `Diri Boghazkoy`, `OB Sippar Diri`, `OB Diri varia`, `OB Diri Oxford`). |
| **Five ORACC project archives** | `dcclt.zip`, a second general `dcclt` export, `dcclt-signlists.zip`, `dcclt-ebla.zip`, and `dcclt-niniveh.zip`, downloaded from `oracc.museum.upenn.edu/json/` and cross-combined, since no single archive contained the full set of catalogued Diri texts. |

## Pipeline Overview

| Stage | Task | Output |
|---|---|---|
| **Stage 1** | Filter `catalogue.json` for every text whose `subgenre` field names a Diri sub-series | 223 catalogued Diri texts identified |
| **Stage 2** | Cross-reference all five archives' `corpusjson/` folders against this list | 119 of the 223 texts physically located (five have an empty edition shell, no transliterated content yet) |
| **Stage 3** | Parse each text's ORACC CDL (Cuneiform Discourse Language) JSON tree; group lemmas by tablet line (`sentence` node) | one group of 2–3 fields per surviving tablet line |
| **Stage 4** | Classify each lemma by language and form shape, and assign it to the correct column | 3,452 lines extracted |

**Output: `diri_lexical_list.csv`**, 3,452 rows, drawn from 114 tablets with recoverable content.

## Step-by-Step Description

### 1. Identifying The Diri Texts

`catalogue.json` records, for every text in the DCCLT/signlists project, a `subgenre` field naming its specific place within the sign-list tradition (`Diri`, `Aa`, `Ea`, `Syllabary A`, `Idu`, and others catalogued alongside it in the same school curriculum). Filtering for any value containing "Diri" isolates the 223 texts that belong to this series specifically, spanning several named regional and chronological recensions (general `Diri`: 151; `OB Nippur Diri`: 44; `Diri Boghazkoy`, the Hittite-period recension: 16; `OB Sippar Diri`: 6; smaller Old Babylonian groupings: 6).

### 2. Locating Available Editions Across Multiple Archives

No single ORACC archive contained the full set. Five were downloaded and combined:

| Archive | Diri texts found |
|---|---|
| `dcclt.zip` (first download) | 24 |
| `dcclt.zip` (second, larger download, ~4,980 files) | 60 |
| `dcclt-niniveh.zip` | 35 |
| `dcclt-ebla.zip` | 0 |
| `dcclt-jena.zip` | 0 (catalogue/index files only, no text editions) |
| **Combined, de-duplicated** | **119** |

Of these 119, five (`P437086`, `P437078`, `X110011`, `X003860`, `X110013`) have a published file but an empty content tree, catalogued but not yet transliterated, leaving **114 texts with usable content**.

### 3. Parsing The ORACC Text Structure

Each ORACC JSON edition encodes a tablet as a nested tree (`cdl`, Cuneiform Discourse Language). Every physical tablet line is grouped under a `sentence` node. Within a Diri tablet's line, this typically contains two or three parallel entries:

●	a **Sumerian reading** (lowercase, e.g. `nindaba`) — how the sign sequence was pronounced.
●	a **sign sequence** (uppercase, pipe-bracketed, e.g. `|PAD.AN.MUŠ₃|`) — the compound sign itself.
●	an **Akkadian gloss** (lowercase, syllabically spelled, e.g. `ni-in-da-bu-u₂`) — the Akkadian translation or phonetic equivalent given alongside it in the bilingual tradition.

Each lemma is classified by its ORACC-recorded language code (`sux` for Sumerian, `akk-x-*` for the various Akkadian dialects) and by whether its form is pipe-bracketed/uppercase (sign sequence) or plain lowercase (reading). Broken or ellipsis placeholders (`[...]`, `x`) are discarded rather than recorded as empty facts.

### 4. What This Text Directly Confirms About Diri

A concrete example survives intact in the data: the sign sequence `|EN.ME.GI|` is read `engiz` in two consecutive lines of the same tablet (`P227753`, lines r i' 13 and r i' 14), each paired with a *different* Akkadian gloss (`nuḫattimmu` and `sirašû`). This is a directly attested instance of the polyphony this project investigates, recorded in the primary teaching text itself, not inferred from a modern cross-reference.

## Output Description

**`diri_lexical_list.csv`** — 3,452 rows.

●	**`p_number`** — the CDLI/ORACC identifier of the source tablet.
●	**`designation`** — its standard publication citation (e.g. `PBS 05, 131`, `MSL 15, 009 S`).
●	**`period`** — the tablet's dated period (Old Babylonian, Middle Babylonian, Middle Assyrian, Neo-Assyrian, Neo-Babylonian).
●	**`provenience`** — findspot, where recorded.
●	**`subgenre`** — the specific Diri recension this tablet belongs to.
●	**`line_label`** — the tablet line reference (e.g. `r i' 4'`), for citing back to the original.
●	**`sumerian_reading`** — the attested Sumerian pronunciation, where preserved.
●	**`sign_sequence`** — the compound sign sequence, where preserved.
●	**`akkadian_gloss`** — the accompanying Akkadian translation/equivalent, where preserved.

## Summary

| | Count | Share |
|---|---|---|
| Diri texts catalogued | 223 | 100% |
| Located across five archives | 119 | 53.4% |
| With recoverable content | 114 | 51.1% |
| **Lines extracted** | **3,452** | — |
| Lines with both `sumerian_reading` and `sign_sequence` | 2,200 | 63.7% of extracted lines |

By period:

| Period | Lines |
|---|---|
| Old Babylonian | 1,443 |
| Neo-Assyrian | 1,230 |
| Middle Babylonian | 400 |
| Middle Assyrian | 312 |
| Neo-Babylonian | 67 |

## Data Integrity Note

Coverage is 53.4% of the catalogued Diri corpus, not 100%, and this reflects the current state of ORACC's ongoing digitisation work rather than a gap in this project's methodology. `catalogue.json` records every tablet identified by past scholarship as belonging to the Diri series (some identified decades ago), but full line-by-line transliteration into a machine-readable ORACC edition is a separate, ongoing task, and not every catalogued tablet has one yet. Five of the 119 located files are themselves proof of this: they exist as registered editions with no transliterated content at all. The remaining 104 texts are catalogued but currently have no digital edition, in any of the five archives checked. This dataset therefore represents the full extent of what is presently publishable from primary sources, not an artificially incomplete sample.

This dataset stands independently of `compound_form_reading_table.csv` (Step 2) at this stage: it has not yet been cross-joined against it. A natural next step, not carried out here, would be to add a third `reading_source` tier (`ANCIENT_DIRI_SERIES`) alongside the existing `OSL_V_TAG` and `SYLLABARY_CM`, for any compound whose reading can be independently confirmed against this primary-source extract.
