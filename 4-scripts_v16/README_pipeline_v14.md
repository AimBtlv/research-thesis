# Pipeline_v16: 
*Stage 1.      
Steps 1–5 and Step 6.0.           
Run: `python3 00_run_pipeline.py`      
Version Of 2026-11-20       
Python 3.9 or newer.*

## What Is In This Folder

| No. | Script | Step | 
|---|---|---|
| 00 | `00_run_pipeline.py` | all | 
| 01 | `01_build_syllabary_CM.py` | 1.1 | 
| 02 | `02_join_unicode_syllabary_CM.py` | 1.2 | 
| 03 | `03_build_rest_unicode_signs.py` | 1.3 |
| 04 | `04_join_matched_rest_signs.py` | 1.4 | 
| 05 | `05_build_diri_lexical_list.py` | 2 |
| 06 | `06_build_sign_catalogue_v13.py` | 3–4 |
| 07 | `07_parse_atf_to_tokens_v14.py` | 5.1 |
| 08 | `08_tokens_to_grapheme_v14.py` | 5.2 | 
| 08a| `08a_function_layer.py` | * |
| 08b| `08b_goldlib.py` | ** |
| 09 | `09_verify_pipeline.py` | ***| 
| 10 | `10_build_manual_check.py` | 6.0 |

## Not In This Folder: Keep Your Own Copies 

These files were not part of the upload and were not changed. Keep them in `pipeline_v14/`:

| File | Why it is needed |
|---|---|
| `08a_function_layer.py` | helper of 08 (function of the sign by language and context) |
| `08b_goldlib.py` | helper of 08a (copy of `goldlib.py` of the gold package) |
| `09_verify_pipeline.py` | PASS / DIFF check.  Its reference numbers for Step 5 belong to v14.4 and must be updated after the first run of v14.5 (see below) |

Without these three files `00_run_pipeline.py` stops with a clear message.

## What Changed 

| Script | Fix | What it does | Effect |
|---|---|---|---|
| 06 v13.1 | P02 | a `@form` named like a `@sign` with its own code point takes that code point (\|HI×BAD\| = KAM) | 13 forms; catalogue only |
| 06 v13.1 | P01 / P13 | a piece of a name split is also looked up among `@form` entries with a ratified code point | 4 compounds newly split (\|LAK648×IM\| …) |
| 06 v13.1 | P03b | `@v` of all OSL entries with the same name are used | 4 compounds get a reading |
| 06 v13.1 | P04 | "nested in longer form" matched on whole components, not letters | 37 wrong matches removed |
| 07 v14.4 | P08a | a span of several readings is not merged into a compound with a placeholder | *ni-ir* = NI + IR (247 tokens) |
| 08 v14.5 | P15 | a registered name takes the code point of its own row | **74,102 tokens get the right glyph** (*da*, *ri*, *nam*, *u* …) |
| 08 v14.5 | P06 | components of a compound from one OSL entry only | 2,377 duplicated rows removed |
| 08 v14.5 | P07 | placeholders X / O / ? are not stored as code points | 1,399 tokens; "with Unicode" counts only real codes |
| 10 v1.1 | – | builds the manual-check files P01–P15 | `output/manual_check_v2/` |

Details: `WorkFlowDocumentations/` (sections *Changes v13.1* in `3.doc_…` and `4.doc_…`, *Changes v14.4 / v14.5* in `5.doc_…`) and `manual_check_v2/00_WORKFLOW.md`.

## **How To Install And Run (Установка и запуск)**

1. Make a copy of your current `pipeline_v14/` (for comparison).
2. Copy the 10 scripts of this folder into `research-thesis/pipeline_v14/`, replacing the old ones. Keep `08a`, `08b`, `09`.
3. Run `python3 00_run_pipeline.py --list`: all 13 files must be found.
4. Run `python3 00_run_pipeline.py --from 06` (Steps 1–2 are unchanged; 06 → 07 → 08 → 09 → 10).
5. ⚠️ `09_verify_pipeline.py` will show **DIFF** for Step 5. This is expected: the old numbers (2,157,404 grapheme rows, 2,154,861 with Unicode, 663,099 LOGO) belong to v14.4. Check the new numbers, then update them in 09.
6. Script 10 rebuilds `output/manual_check_v2/P01–P15_*.csv`; the cases fixed by the code disappear from the lists.

## **What Was Tested (Проверка)**

1. All scripts: syntax check; 01–05 are byte-identical to the uploaded versions.
2. 06 v13.1: run on `osl.asl` and `1_unicodeSigns.csv` of the project (without the real Diri / OGSL files); the OSL rows of the old catalogue were reproduced exactly before the change, and the differences after it are exactly the intended ones.
3. 07 v14.4: tokenizer tested on the real catalogue (*ni-ir* → NI + IR; *ku₃-babbar*, *zimbir*, *a-na* unchanged).
4. 08 v14.5: sign lookup tested on the real catalogue (DA → U+12055, RI → U+12291, \|AŠ.AŠ\| → 2 components, placeholders without code).
5. 10 v1.1: run on the outputs of 2026-11-14.

⚠️ **Not tested here:** a full run of 05–09 on the real corpus (the ATF files, the CDLI metadata, `diri_lexical_list.csv`, `ogsl_sign_readings.json`, `08a`, `08b` and `09` were not available). The first full run on your computer is the real test.
