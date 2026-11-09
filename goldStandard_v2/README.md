# Gold Standard Package v2 (Stage 1, Steps 6 And 7)

*Deliverable for the supervisor meeting:* (1) the gold standard, (2) the corpus it is based on, (3) the directions for the AI that annotates the unprocessed corpus, (4) the 90 % / 10 % split.

*Place in the thesis workflow.* Stage 1 gets two new steps after Step 5 (parsing v12):
- **Step 6. Gold standard and parser validation** (sub-steps 6.1–6.8): 50 stratified tablets, 5,372 sign rows, split by tablet into 45 train / 5 validation tablets.
- **Step 7. AI-assisted annotation of the whole corpus** (sub-steps 7.1–7.5): rule draft → LLM correction with train examples → evaluation on the validation split → full run → `grapheme.csv` v2 for Stage 2.

Full description: `ANNOTATION_GUIDELINES_v2.md` (English) and `ANNOTATION_GUIDELINES_v2_ru.md` (Russian).

## Contents

| Folder / file | Step | What it is |
|---|---|---|
| `ANNOTATION_GUIDELINES_v2.md`, `ANNOTATION_GUIDELINES_v2_ru.md` | 6–7 | workflow, rules, columns, data problems, open decisions |
| `scripts/goldlib.py`, `scripts/stage_c_tools.py` | 6.3 | OSL index, C-ATF normalisation, tokenizer, sign resolution |
| `scripts/select_sample.py` | 6.4 | stratified sample |
| `scripts/build_gold.py`, `scripts/word_overrides.csv`, `scripts/dump_words.py` | 6.5–6.6 | automatic annotation, 103 manual word decisions, review helper |
| `scripts/finalize_gold.py` | 6.7 | split 90 / 10, exports, statistics |
| `data/gold_signs.csv` | 6 | gold standard, 5,372 sign rows, 50 tablets (column `split`) |
| `data/gold_train.csv`, `data/gold_val.csv` | 6.7 | 45 tablets / 4,835 rows; 5 tablets / 537 rows |
| `data/gold_signs.conllu` | 6.7 | same data, CoNLL-U-style (one sentence = one ATF line) |
| `data/gold_sample_tablets.csv`, `data/corpus_tablet_stats.csv`, `data/gold_stats.json` | 6.4, 6.7 | sample, sampling frame of 16,906 tablets, counts |
| `corpus/gold_corpus_atf/` | 6.4 | ATF of the 50 tablets (the corpus of the gold standard) |
| `scripts/annotate_corpus.py` | 7.1 | rule draft for any set of tablets |
| `ai/ai_system_prompt.md`, `ai/run_llm_annotation.py`, `ai/example_prompt_P209784.txt` | 7.2 | LLM instructions, runner, sample prompt |
| `scripts/apply_lexicon.py` | 7.2b | option without AI: train word-type lexicon (added to the package outside the original session; checked) |
| `scripts/evaluate.py` | 7.3 | evaluation against the validation split |
| `scripts/corpus_quality.py` | 7.5 | quality report per corpus (unresolved, flagged, LOGO : SYLL) |
| `evaluation/` | 7.3 | rule baseline and lexicon reports on the validation split |

## Commands (Python 3.13, Linux)

`pandas` is needed only for `dump_words.py`; Step 7.2 needs `pip install anthropic` and `ANTHROPIC_API_KEY`.

1. *Rebuild Step 6:* `python3 scripts/build_gold.py osl.asl out/` (with `out/gold_sample_tablets.csv` and `out/gold_corpus_atf/`), then `python3 scripts/finalize_gold.py out/`.
2. *Step 7.1:* `ONLY_SPLIT=val python3 scripts/annotate_corpus.py osl.asl data/gold_sample_tablets.csv corpus/gold_corpus_atf val_rules.csv`.
3. *Step 7.2:* `python3 ai/run_llm_annotation.py val_rules.csv data/gold_train.csv val_llm.csv --model claude-sonnet-5-5` (first with `--dry-run`). *Option 7.2b:* `python3 scripts/apply_lexicon.py data/gold_train.csv val_rules.csv val_lex.csv`.
4. *Step 7.3:* `python3 scripts/evaluate.py data/gold_val.csv val_llm.csv report.md`.
5. *Step 7.4:* `python3 scripts/annotate_corpus.py osl.asl data/corpus_tablet_stats.csv <2-dataset/InputData/1.downloadCorpusATF> full_rules.csv` (about 1.5 min, 2,493,716 rows, about 600 MB). LLM on the whole corpus: about 16,300 requests; pilot first with `--limit 50`.
6. *Step 7.5:* `python3 scripts/corpus_quality.py full_rules.csv quality.md`.
7. *Step 6.8, option B:* human corrections in `<dir>/corrections.csv`, then `python3 scripts/build_gold.py osl.asl <dir> <dir>/corrections.csv` and `python3 scripts/finalize_gold.py <dir>`.

## Baseline (Step 7.3, Rules Only, Validation Split)

| Metric | Value |
|---|---|
| Evaluated units (readings; compounds counted once) | 498 |
| Function accuracy (5 classes) | 0.972 |
| Function macro-F1 | 0.987 |
| Cohen's κ (function) | 0.955 |
| LOGO / SYLL accuracy | 0.967 |
| Rules + train lexicon (7.2b) | 0.972 (covers 37.3 % of words, changes none) |
| Sign name accuracy | 1.000 (*not informative yet: gold sign names come from the same OSL lookup*) |

## Important Limitation

The labels come from rules and from a type-by-type review by Claude. They become a **gold** standard only after Step 6.8: manual verification by a person (`human_verified` column).
