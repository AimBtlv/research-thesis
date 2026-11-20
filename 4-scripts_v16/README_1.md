# pipeline_v14: Stage 1 From Step 1 To Step 5

`research-thesis/` repository.    
`4-scripts_v14/`(next to `2-dataset/`)       
All paths are relative to the repository, every result is written to `4-scripts_v14/output/`.     
The original files are never overwritten.      
Python 3.9 or newer.

| No. | Script | Step | Output |
|---|---|---|---|
| 00 | `00_run_pipeline.py` runs 01–09 in order with one command| all | – |
| 01 | `01_build_syllabary_CM.py` | 1.1 | `output/step1/Syllabary_CM.csv` |
| 02 | `02_join_unicode_syllabary_CM.py`| 1.2 | `output/step1/3_matched_signs_full.csv` (791), `4_unmatched_for_review.csv` (443) |
| 03 | `03_build_rest_unicode_signs.py` | 1.3 | `output/step1/restUnicodeSigns.csv` |
| 04 | `04_join_matched_rest_signs.py`  | 1.4 | `output/step1/7_unicodePhoneticVersion_full.csv` |
| 05 | `05_build_diri_lexical_list.py` (optional: runs only if the Oracc DCCLT JSON is in `2-dataset/DataProfile/oracc_dcclt/`) | 2 | `output/step2/diri_lexical_list.csv`, else the existing file is used |
| 06 | `06_build_sign_catalogue_v13.py` | 3–4 | `output/step4/sign_catalogue_v13.csv`, `compound_form_reading_table_v13.csv`, `osl_reading_conflicts_v13.csv` |
| 07 | `07_parse_atf_to_tokens_v14.py [atf_file_or_folder]` (default: the whole OB corpus `OBP_full/practiceOBP_all.atf`, 16,906 tablets) | 5.1 | `output/step5/atf_tokens.csv`, `warnings.csv`, `txt/` |
| 08 | `08_tokens_to_grapheme_v14.py [atf] [metadata]` (default metadata: `OBP_full/allOBP_metadata_16911.csv`) | 5.2 | `output/step5/grapheme.csv`, `warnings_grapheme.csv` |
| 08a | `08a_function_layer.py` (helper of 08, not run on its own: function of the sign by language and context) | 5.2 | – |
| 08b | `08b_goldlib.py` (helper of 08a, not run on its own: copy of `goldlib.py` of the gold package; only the `Name:` line differs) | 5.2 | – |
| 09 | `09_verify_pipeline.py` | check | PASS / DIFF table |

Run order: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 (uses 08a, which uses 08b) → 09.



**Git:** `output/` is not stored in Git (`.gitignore`): `grapheme.csv` (~410 MB) and `atf_tokens.csv` (~120 MB) are over the GitHub limit of 100 MB per file. Anyone can recreate them with `00_run_pipeline.py`.

## Step 2: Oracc DCCLT Input

Unzip the Oracc JSON archives (https://oracc.museum.upenn.edu/json/) into `2-dataset/DataProfile/oracc_dcclt/`:

| Oracc archive (as downloaded) | Put its content in |
|---|---|
| `dcclt-signlists` (`signlists/`) | `dcclt_full/dcclt/signlists/` and copy its `catalogue.json` to `oracc_dcclt/catalogue.json` |
| `dcclt` main project (`dcclt-5/corpusjson`, ~5,000 texts) | `dcclt2_full/dcclt-2/corpusjson/` |
| `dcclt-ebla` (`ebla/`) | `dcclt-ebla_full/dcclt-ebla/ebla/` |
| `dcclt-nineveh` (`nineveh/`) | `dcclt-niniveh_full/dcclt-niniveh/nineveh/` |

Expected: 233 Diri texts in the catalogue, 118 present, 115 with content, 4,084 lines. 

## Step 5: Corpus

The whole Old Babylonian corpus is parsed: `2-dataset/InputData/1.downloadCorpusATF/OBP_full/practiceOBP_all.atf`      
16,906 tablets = 717 school + 16,189 practical.     
1,197 of them have only a header and no text lines, so 15,709 tablets give tokens.
School and comparison corpora are separated later by the metadata (`is_school_text`, `genres`)

Reference numbers (v14):     
2,267,576 tokens,     
3,495 unresolved,      
56,215 unreadable `x`,       
2,157,401 grapheme rows,     
2,154,856 with Unicode,     
663,102 LOGO (v14)

## Step 5.2: Function Of The Sign (v14)

`sign_type` (simple signs) and `sign_function` (all rows) are decided **by language and context**,
with exactly the rules of the gold standard: `08a_function_layer.py` uses `08b_goldlib.py` (copied unchanged from the gold package)
and the word-level steps of `build_gold.py` (without the manual word overrides). The letter-case rule is only a fallback
(176 tablets with unknown language; tokens that cannot be aligned): `function_rule = fallback:letter_case`, 26,529 rows.

Check on the 50 gold tablets, sign by sign: Akkadian 98.6 %, Sumerian 94.6 % agreement with the gold standard
(LOGO share: Akkadian 19.9 % vs 20.5 % in the gold; Sumerian 61.0 % vs 56.4 %). 115 of the 118 Sumerian differences are
the manual word overrides of the gold. Before v14.4 the letter-case rule gave 7.0 % LOGO in Sumerian texts.
