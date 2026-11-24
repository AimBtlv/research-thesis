# Pipeline_v16: 
*Stage 1    
Steps 1–5 and Step 6.0. 
`research-thesis/` repository.    
`4-scripts_v16/`(next to `2-dataset/`)       
All paths are relative to the repository, every result is written to `4-scripts_v16/output/`          
Run: `python3 00_run_pipeline.py`      
Version Of 2026-11-22       
Python 3.9 or newer.*


## What Is In This Folder?

| No. | Script | Step | Output |
|---|---|---|---|
| 00 | `00_run_pipeline.py` runs 01–10 in order with one command| all | – |
| 01 | `01_build_syllabary_CM.py` | 1.1 | `output/step1/Syllabary_CM.csv` |
| 02 | `02_join_unicode_syllabary_CM.py`| 1.2 | `output/step1/3_matched_signs_full.csv` (779), `4_unmatched_for_review.csv` (455) |
| 03 | `03_build_rest_unicode_signs.py` | 1.3 | `output/step1/restUnicodeSigns.csv` |
| 04 | `04_join_matched_rest_signs.py`  | 1.4 | `output/step1/7_unicodePhoneticVersion_full.csv` |
| 05 | `05_build_diri_lexical_list.py` (optional: runs only if the Oracc DCCLT JSON is in `2-dataset/DataProfile/step2/dcclt/`) | 2 | `output/step2/diri_lexical_list.csv`, else the existing file is used; an incomplete download goes to `diri_lexical_list_PARTIAL.csv` and does not replace the full list |
| 06 | `06_build_sign_catalogue_v13.py` | 3–4 | `output/step4/sign_catalogue_v13.csv`, `compound_form_reading_table_v13.csv`, `osl_reading_conflicts_v13.csv` |
| 07 | `07_parse_atf_to_tokens_v14.py [atf_file_or_folder]` (default: the whole OB corpus `OBP_full/practiceOBP_all.atf`, 16,906 tablets) | 5.1 | `output/step5/atf_tokens.csv`, `warnings.csv`, `txt/` |
| 08 | `08_tokens_to_grapheme_v14.py [atf] [metadata]` (default metadata: `OBP_full/allOBP_metadata_16911.csv`) | 5.2 | `output/step5/grapheme.csv`, `warnings_grapheme.csv` |
| 08a | `08a_function_layer.py` (helper of 08, not run on its own: function of the sign by language and context) | 5.2 | – |
| 08b | `08b_goldlib.py` (helper of 08a, not run on its own: copy of `goldlib.py` of the gold package; only the `Name:` line differs) | 5.2 | – |
| 09 | `09_verify_pipeline.py` | ***| PASS / DIFF table |
| 10 | `10_build_manual_check.py` | 6.0 | `output/manual_check_v2/P01–P15_*.csv` |

*** PASS / DIFF check of every step against the reference numbers (table `REFERENCE` at the top of the script). The large files are read row by row, so the check takes a few seconds. 

`08a_function_layer.py`, `08b_goldlib.py`,`09_verify_pipeline.py`: Without these three files `00_run_pipeline.py` stops with a clear message.

Run order: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 (uses 08a, which uses 08b) → 09 → 10

**Git:** `output/` is not stored in Git (`.gitignore`): `grapheme.csv` (~410 MB) and `atf_tokens.csv` (~120 MB) are over the GitHub limit of 100 MB per file. Anyone can recreate them with `00_run_pipeline.py`.

## Oracc DCCLT Input

Unzip the Oracc JSON archives (https://oracc.museum.upenn.edu/json/) into `2-dataset/DataProfile/step2/dcclt/` (05 finds `catalogue.json` and every `corpusjson` folder there by itself):

| Oracc archive (as downloaded) | Put its content in |
|---|---|
| `dcclt-signlists` (`signlists/`) | `dcclt_full/dcclt/signlists/` (its `catalogue.json` is found there) |
| `dcclt` main project (`dcclt-5/corpusjson`, ~5,000 texts) | `dcclt2_full/dcclt-2/corpusjson/` |
| `dcclt-ebla` (`ebla/`) | `dcclt-ebla_full/dcclt-ebla/ebla/` |
| `dcclt-nineveh` (`nineveh/`) | `dcclt-niniveh_full/dcclt-niniveh/nineveh/` |

Expected: 233 Diri texts in the catalogue, 118 present, 115 with content, 4,084 lines. If fewer lines are found (for example 1,284 without the main `dcclt` project), the full list in `2-dataset/DataProfile/step2/` is kept and used, the lines found are written to `output/step2/diri_lexical_list_PARTIAL.csv`, and 09 shows DIFF for Step 2. 

##  Corpus

The whole Old Babylonian corpus is parsed: `2-dataset/InputData/1.downloadCorpusATF/OBP_full/practiceOBP_all.atf`      
16,906 tablets = 717 school + 16,189 practical.     
1,197 of them have only a header and no text lines, so 15,709 tablets give tokens.
School and comparison corpora are separated later by the metadata (`is_school_text`, `genres`)

Reference numbers (v16, run of 22 November 2026):     
2,267,828 tokens,     
3,465 unresolved,      
56,215 unreadable `x`,       
2,156,055 grapheme rows,     
2,153,364 with Unicode,  



## How To Install And Run 

1. Make a copy of your current `4-scripts_v16/` (for comparison).
2. Copy the 10 scripts of this folder into `research-thesis/4-scripts_v16/`, replacing the old ones. Keep `08a`, `08b`, `09`.
3. Run `python3 00_run_pipeline.py --list`: all 13 files must be found.
4. Run `python3 00_run_pipeline.py --from 06` (Steps 1–2 are unchanged; 06 → 07 → 08 → 09 → 10).
5. `09_verify_pipeline.py` must show **PASS** in every row. A **DIFF** means that a number changed: find its cause before the number is changed in `REFERENCE`. 
6. Script 10 rebuilds `output/manual_check_v2/P01–P15_*.csv`, the cases fixed by the code disappear from the lists.

