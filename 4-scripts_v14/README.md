# pipeline_v14: Stage 1 From Step 1 To Step 5

 `research-thesis/` repository.    
`4-scripts_v14/`(next to `2-dataset/`)       
All paths are relative to the repository, every result is written to `4-scripts_v14/output/`.     
The original files are never overwritten.      
Python 3.9 or newer.

| Order | Script | Step | Output |
|---|---|---|---|
| 1 | `01_build_syllabary_CM.py` | 1.1 | `output/step1/Syllabary_CM.csv` |
| 1b | `01b_join_unicode_syllabary_CM.py` (restored from the March 2026 chat version of the empty `2_scriptJoinUnicode_SyllabaryCM.py`; byte-identical output) | 1.2 | `output/step1/3_matched_signs_full.csv` (791), `4_unmatched_for_review.csv` (443) |
| 2 | `03_build_rest_unicode_signs.py` | 1.3 | `output/step1/restUnicodeSigns.csv` |
| 3 | `04_join_matched_rest_signs.py` (reconstruction of the empty `4_scriptJoinMatched_RestSigns.py`, byte-identical output) | 1.4 | `output/step1/7_unicodePhoneticVersion_full.csv` |
| 4 | `02_build_diri_lexical_list.py` (optional: runs only if the Oracc DCCLT JSON is in `2-dataset/DataProfile/oracc_dcclt/`) | 2 | `output/step2/diri_lexical_list.csv`, else the existing file is used |
| 5 | `05_build_sign_catalogue_v13.py` | 3–4 | `output/step4/allograph_all_v13.csv`, `compound_form_reading_table_v13.csv`, `osl_reading_conflicts_v13.csv` |
| 6 | `06_parse_atf_to_tokens_v14.py [atf_file_or_folder]` (default: the whole OB corpus `OBP_full/practiceOBP_all.atf`, 16,906 tablets) | 5.1 | `output/step5/atf_tokens.csv`, `warnings.csv`, `txt/` |
| 7 | `07_tokens_to_grapheme_v14.py [atf] [metadata]` (default metadata: `OBP_full/allOBP_metadata_16911.csv`) | 5.2 | `output/step5/grapheme.csv`, `warnings_grapheme.csv` |
| 8 | `08_verify_pipeline.py` | check | PASS / DIFF table |

In VS Code: *Terminal → Run Task… → RUN ALL · Steps 1 -> 5 + check*.

## Step 2: Oracc DCCLT Input

Unzip the Oracc JSON archives (https://oracc.museum.upenn.edu/json/) into `2-dataset/DataProfile/oracc_dcclt/`:

| Oracc archive (as downloaded) | Put its content in |
|---|---|
| `dcclt-signlists` (`signlists/`) | `dcclt_full/dcclt/signlists/` and copy its `catalogue.json` to `oracc_dcclt/catalogue.json` |
| `dcclt` main project (`dcclt-5/corpusjson`, ~5,000 texts) | `dcclt2_full/dcclt-2/corpusjson/` |
| `dcclt-ebla` (`ebla/`) | `dcclt-ebla_full/dcclt-ebla/ebla/` |
| `dcclt-nineveh` (`nineveh/`) | `dcclt-niniveh_full/dcclt-niniveh/nineveh/` |

Expected: 233 Diri texts in the catalogue, 118 present, 115 with content, 4,084 lines. With the October 2026 download, 3 rows differ from the September file because Oracc changed the editions (`{d}KU₃.GI` -> `{d}KU₃-GI`, `{d}KU₃.SUD` -> `{d}KU₃-SUD`, `(<(A.X)>)` -> `<(A-X)>`); the check reports them as INFO.

## Step 5: Corpus     

The whole Old Babylonian corpus is parsed:     
`2-dataset/InputData/1.downloadCorpusATF/OBP_full/practiceOBP_all.atf`      
16,906 tablets (717 school + 16,189 practical)     
1,197 of them have only a header and no text lines, so 15,709 tablets give tokens.    
School and comparison corpora are separated later by the metadata (`is_school_text`, `genres`), never by file name:
`practiceOBP_all.atf` also contains the 717 school tablets of `OBP.atf`.


Reference numbers (v14.2):    
2,267,576 tokens.     
56,215 unreadable `x`.     
2,155,501 grapheme rows    
2,152,956 with Unicode.    
317,092 LOGO.
