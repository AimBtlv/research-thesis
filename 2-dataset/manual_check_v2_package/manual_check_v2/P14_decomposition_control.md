# **P14. Control Sample Of The Decompositions (Контрольная выборка разложений)**

*File: `P14_decomposition_control.csv`, 78 rows, check_id `P14-0001`–`P14-0078`. Built by `10_build_manual_check.py` from the outputs of 2026-11-14 (pipeline v14.4).*

## **Place In The Workflow (Место в workflow)**

Stage 1, Step 6.0 (manual check before the gold standard). Documented in `4.doc_sign_catalogue_v13.md` § 4; `5.doc_parsing_layer_v14.md` § 13; scripts 06, 08.

## **The Problem (Проблема)**

The components of most compounds come from OSL `@useq` (expert decision); the others from a name split by the script. Part B lists all name splits that occur in the corpus; part C the 30 most frequent `@useq` compounds as a sample. If C finds no error, `@useq` is treated as reliable.

## **Automatic Fix (Автоматическое исправление)**

**No** (this is the control itself). Rows with placeholders (P07) are not repeated here.

## **Size And Effect On The Corpus (Объём)**

78 rows (B: 48, C: 30), 72,849 tokens.

## **Which Rows To Check (Scope)**

All rows: **mandatory** (sample).

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `part` | B = name split in the corpus, C = @useq sample |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Compare `components_names` with OSL / MZL.
2. Same signs and order → OK.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `OK` | the split is right | – |
| `WRONG_COMPONENT` | a component is another sign | `correct_components` |
| `WRONG_ORDER` | wrong order | `correct_components` |
| `MODIFIER_LOST` | a modifier matters | `correct_components` |
| `SIMPLE_SIGN` | should not be split | name / code |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| compound_form | part | components_names | glyph | tokens_in_OB_corpus |
|---|---|---|---|---|
| \|EN.ZU\| | C (@useq sample) | EN + ZU | 𒂗𒍪 | 13295 |
| \|HI×BAD\| | B (name split, in corpus) | HI + BAD | 𒄮 | 11512 |
| \|KU₃.UD\| | C (@useq sample) | KU₃ + UD | 𒆬𒌓 | 5868 |
| \|A.AN\| | C (@useq sample) | A + AN | 𒀀𒀭 | 5643 |
| \|EN.KID\| | C (@useq sample) | EN + KID | 𒂗𒆤 | 4447 |
| \|AMAR.UD\| | C (@useq sample) | AMAR + UD | 𒀫𒌓 | 3552 |

*These are real rows of the file, not decisions.*
