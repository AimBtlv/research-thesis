## 2. How Was diri_lexical_list.csv Built?

**Digitised Extract of the Ancient Diri Lexical Series (Diri = watru)**
This step extracts authentic, tablet-attested readings of sign compounds from the primary source(The ancient Sumerian lexical series Diri (ORACC/DCCLT))
The goal is to enrich the table of Compounds (in Step3). It is a direct quote from the ancient textbook. And have third reading priority in this work after @v (reading version of sign ) in osl.asl. The pipeline must be able to answer two questions reliably: 
- How Sumerian students read a specific sign combination, according to the very text used to teach them?     

**The second stage of the pipeline is to extract Diri = watru (MSL 15), ORACC/DCCLT**.   
**Note**: What "Diri" Actually Means?    
A **diri compound** is one whose reading is genuinely **unpredictable** from its components.   
 `osl.asl`'s `.` notation does not distinguish the two, both are recorded identically. 
 **Note** **qcat (Q-catalogue)** is not a text corpus, but a service consolidated catalog of ORACC, which tracks all composite texts (those marked with a Q-number, that is, "consolidated" versions reconstructed by scientists, collected from several duplicate tablets) across the entire consortium at once, and for each such composite lists from which physical tablets (P-numbers) it was compiled.

## Data Sources
**ORACC / DCCLT**  Digital Corpus of Cuneiform Lexical Texts. Publishes JSON editions of lexical texts. https://oracc.museum.upenn.edu/json/

| Source | Description |
|---|---|
| **catalogue.json** | The DCCLT/signlists project catalogue. A Diri text is identified by **two independent tags**: `subgenre` (used for individual tablet exemplars i.e. `"OB Nippur Diri"`) and `series` (used for composite/score editions i.e `Q000146`, `series = "Diri"`). |
| **qcat.zip** | Global ORACC catalogue of composite texts(Q-number texts). No new texts resulted, but confirmed completeness of the exemplar-level search. |
| **Five combined archives** | `dcclt.zip`, `dcclt-signlists.zip`, `dcclt-ebla.zip`, `dcclt-niniveh.zip`.  `dcclt-jena.zip`. This is a project within the ORACC consortium, which is specifically engaged in the digitization of lexical/educational cuneiform texts (lists of signs, syllabaries, word lists what Sumerian scribes studied) |



## Pipeline Overview

| Stage | Task | Output |
|---|---|---|
| **Stage 1** | Filter `catalogue.json` for `subgenre` containing "Diri" **or** `series == "Diri"` | Catalogued Diri texts 
| **Stage 2** | Cross-reference all five archives against this list | Texts physically located |
| **Stage 3** | Route each text by ID prefix: `P*`, `Q*` (composite parser) | - |
| **Stage 4** | Classify each lemma by language and form shape, discard broken/ellipsis placeholders (`[...]`, `x`) |lines extracted |

**Output: `diri_lexical_list.csv`**, 4,084 rows.

## Output Description

●	**`p_number`** — the CDLI/ORACC identifier of the source tablet. 
●	**`designation`** — standard publication citation. How the tablet is cited in scientific literature?  
●	**`period`** - the tablet's dated period (Old Babylonian, Middle Babylonian, Middle Assyrian, Neo-Assyrian, Neo-Babylonian).
● **`provenience`** — findspot, where recorded. 
●	**`subgenre`** — the specific Diri recension this tablet belongs to.
●	**`line_label`** — tablet line reference, for citing back to source. (i.e r i' 4')   
●	**`sumerian_reading`** — attested Sumerian pronunciation.    
●	**`sign_sequence`** — the compound sign sequence 
●	**`akkadian_gloss`** — accompanying Akkadian translation/equivalent, where preserved.    

## Summary

|  | Count  |
|---|---|
|Diri texts catalogued  | 233 | 
| **Lines extracted** | **4,084** |

