## 2. How Was diri_lexical_list.csv Built?

**Digitised Extract of the Ancient Diri Lexical Series (Diri = watru)**

## Research Question / Purpose

Every other phonetic source in this pipeline is a *modern scholarly compilation*, assembled by researchers cross-referencing many original tablets. This dataset is different in kind: it is a direct digitised transcription of the **ancient teaching texts themselves**, the school lists Mesopotamian scribal students actually copied and memorised to learn compound sign readings. The series is called **Diri**, named after its own first entry: the sign sequence `SI.A`, conventionally read *diri* ("exceeding, surplus"). Its standard modern edition (MSL 15, Civil et al. 1969) comprises seven tablets and roughly 2,100 entries.

## What "Diri" Actually Means — A Necessary Clarification

`.` in `osl.asl`'s naming convention marks any documented **sequence** of signs, structurally. This is not the same claim as "diri" in the strict philological sense: a **true diri compound** is one whose reading is genuinely *unpredictable* from its components (`SI.A` → *dirig*, not "si-a"), which is exactly why such sequences needed a dedicated memorisation list. An **ordinary compositional sequence**, by contrast, could in principle be read by simply concatenating each component's own value. `osl.asl`'s `.` notation does not distinguish the two — both are recorded identically. This dataset is one of the few sources that can, in principle, confirm a reading is *specifically* attested in the Diri tradition rather than merely documented as a sequence elsewhere; see the Step 3 documentation for how this distinction is used, and its limits.

## Data Sources

| Source | Description |
|---|---|
| **ORACC / DCCLT** | Digital Corpus of Cuneiform Lexical Texts. Publishes machine-readable JSON editions of lexical texts. CC BY-SA 3.0. |
| **catalogue.json** | The DCCLT/signlists project catalogue. A Diri text is identified by **two independent, non-overlapping tags**: `subgenre` (used for individual tablet exemplars, e.g. `"OB Nippur Diri"`) and `series` (used for composite/score editions, e.g. `Q000146`, `series = "Diri"`). Filtering on `subgenre` alone misses every composite edition entirely — this was discovered only after an initial pass returned suspiciously few results. |
| **qcat.zip** | Global ORACC catalogue of composite (Q-number) texts. Used to confirm which individual tablet exemplars (P-numbers) each composite score was built from; cross-checked against exemplars already found independently by `subgenre` (no new texts resulted, but confirmed completeness of the exemplar-level search). |
| **Five combined archives** | `dcclt.zip` ×2 downloads, `dcclt-signlists.zip`, `dcclt-ebla.zip`, `dcclt-niniveh.zip`. No single archive contained every catalogued Diri text; `dcclt-jena.zip` was also checked and contained catalogue/index files only, no text editions. |

## Two Structurally Different Text Types

ORACC encodes two distinct kinds of Diri text, and they must be **parsed differently**:

●	**Individual tablet exemplars** (`P`-number IDs) — a physical tablet's own transliteration. Sign identity is recorded as a **separate sibling lemma** alongside the reading: one lemma with `lang=sux`, lowercase form (the reading), and another with `lang=sux`, pipe-bracketed/uppercase form (the sign sequence).
●	**Composite/score editions** (`Q`-number IDs) — the modern reconstructed "master" text, combining evidence from every known exemplar to fill gaps. Sign identity here is instead embedded **inside the reading lemma's own `gdl` breakdown**, as the `gdl_sign` attribute of each syllable (e.g. reading `dirig` carries `gdl_sign: "|SI.A|"` directly on itself, no separate sibling lemma exists).

A single composite text can be dramatically richer than any individual exemplar: `Q000057` ("OB Nippur Diri") alone contributed 632 lines, more than all 114 individual exemplars combined contributed on their own before it was added. Its very first line is the entry that gives the whole series its citation name: `|SI.A|` → *dirig*, Akkadian gloss *watrum*.

## Pipeline Overview

| Stage | Task | Output |
|---|---|---|
| **Stage 1** | Filter `catalogue.json` for `subgenre` containing "Diri" **or** `series == "Diri"` | 233 catalogued Diri texts (223 exemplars + 10 composites) |
| **Stage 2** | Cross-reference all five archives against this list | 121 texts physically located |
| **Stage 3** | Route each text by ID prefix: `P*` → exemplar parser, `Q*` → composite parser | correct field extraction for either structure |
| **Stage 4** | Classify each lemma by language and form shape; discard broken/ellipsis placeholders (`[...]`, `x`) | 4,084 lines extracted |

**Output: `diri_lexical_list.csv`**, 4,084 rows, from 115 texts with recoverable content.

## Output Description

●	**`p_number`** — CDLI/ORACC identifier (P-number for an exemplar, Q-number for a composite).
●	**`designation`** — standard publication citation.
●	**`period`** / **`provenience`** — where known.
●	**`subgenre`** — the specific Diri recension, or `"{series} (composite score)"` for Q-texts.
●	**`line_label`** — tablet line reference, for citing back to source.
●	**`sumerian_reading`** — attested Sumerian pronunciation.
●	**`sign_sequence`** — the compound sign sequence (extracted differently per text type, see above).
●	**`akkadian_gloss`** — accompanying Akkadian translation/equivalent, where preserved.

## Summary

| | Count | Share |
|---|---|---|
| Diri texts catalogued (exemplars + composites) | 233 | 100% |
| Located across five archives | 121 | 51.9% |
| With recoverable content | 115 | 49.4% |
| **Lines extracted** | **4,084** | — |
| Lines with both `sumerian_reading` and `sign_sequence` | 2,829 | 69.3% |
| Distinct sign sequences represented | 1,218 | — |

## Data Integrity Note

Coverage is roughly half of the catalogued corpus, and this reflects the current state of ORACC's ongoing digitisation rather than a methodological gap: `catalogue.json` records tablets identified by scholarship over decades, while full machine-readable transliteration is separate, ongoing work. The seven tablets of the main MSL 15 composite edition (`Q000146`–`Q000152`, "Diri 01"–"Diri 07") were specifically searched for and **not found** in any of the five archives tried, despite `qcat.zip` confirming their existence and citing exact MSL 15 page ranges; their individual source exemplars, however, were independently found and are included. This dataset represents the full extent of what is presently extractable from open digital sources, not an artificially incomplete sample.
