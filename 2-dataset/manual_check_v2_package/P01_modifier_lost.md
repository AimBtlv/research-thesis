# P01. Modifier Lost In A Name Split 

*File: `P01_modifier_lost.csv`.  
25 rows.   
Check_id `P01-0001`–`P01-0025`. 

## Place In The Workflow

Stage 1, Step 6.0 (manual check before the gold standard).     
Documented in `4.doc_sign_catalogue_v13.md`, Step 4.4 *Decomposing Compound Signs*.     
Script `06_build_sign_catalogue_v13.py`.

## The Problem
**1. What Is A Modifier?**     
A modifier is a mark in the name of a sign that stands for a
**changed form** of the sign: `@t` (tenû, slanted), `@g` (gunû, with extra
strokes), `@c` (curved).

**2.Explanation:**           
AŠ and AŠ@c are not the same. They are different graphic units,
and sign lists may give them different code points.

**3. What The Script Does With A Compound Sign?**      
Take |LAGAB×AŠ@c|: "the sign LAGAB with AŠ@c written inside it".      
If OSL gives no ready list of components (`@useq`), the script cuts the name at `×` itself:

    |LAGAB×AŠ@c|  →  LAGAB  +  AŠ@c

Then it looks for a **Unicode code point** for each piece.

**4. Where The Error Arises?**   

- `LAGAB` has a code point.
- `AŠ@c` has no code point of its own in the Unicode list. The old script then
  **drops the modifier** and takes the plain sign: `AŠ@c` → `AŠ`.

The glyph is wrong: the plain AŠ is stored instead of the curved AŠ@c. This is
what "modifier lost" means.

**5. What Was Tried?**

Before, the script looked for the piece only among the **main signs** of OSL
(the `@sign` entries).      
Now it also looks among the **forms** (the `@form` entries, i.e. variants listed inside another sign): perhaps a code point for `AŠ@c` is recorded there? And one is indeed found: OSL gives `AŠ@c` the code point **U+12550**, and
`DIŠ@c` **U+12559**.

**6. Why These Code Points Were Not Used? (U+12550, U+12559)**

*Definition:* a **ratified** (approved) code point is one that is already part of
the official Unicode standard. Our list of such code points is
`1_unicodeSigns.csv`, 1,234 signs (U+12000–U+12543).  U+12550 and U+12559 lie **outside** this list. They have only been *proposed* to Unicode (the proposal is submitted but not yet accepted). Using them is risky:

1. fonts usually do not contain these signs, so an empty box appears on screen.
2. the proposal may be changed or rejected, and the code point in the data would
   then be wrong.
3. the pipeline already marks such code points as `[unverified]`.

They were therefore **deliberately not used**.

**7. Result**    
The automatic fix changed nothing for these 25 cases. Whether the modifier
matters and how the components should be written will be decided by the
expert. Hence the last sentence of the paragraph: *All rows stay manual*.


25 forms; only 1 occurs in the OB corpus (1 token). The check matters for the catalogue, hardly for the thesis.

## **Which Rows To Check (Scope)**

Rows with `tokens_in_OB_corpus` > 0: **mandatory**. The rest: optional.

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `modifier_dropped` | the piece and what it became (`AMAR@t -> AMAR`) |
| `components_names / components_unicode / glyph` | what the pipeline stores now |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Look the compound up in OSL and, with `sign_lists`, in MZL.
2. Does the modifier matter for the identity of the sign (another sign, another reading)?
3. If yes, write the components *with* the modifier in `correct_components` (`AB₂ + AMAR@t`).

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `OK_WITHOUT_MODIFIER` | the plain sign is acceptable for counting | empty |
| `MODIFIER_LOST` | the modifier matters | required |
| `UNSURE` | cannot decide | reason in `comment` |

## **First Rows Of The File (Examples)**

| compound_form | modifier_dropped | components_names | tokens_in_OB_corpus |
|---|---|---|---|
| \|AB₂×AMAR@t\| | AMAR@t -> AMAR | AB₂ + AMAR | 1 |
| \|A×SUD@90\| | SUD@90 -> SUD | A + SUD | 0 |
| \|AŠ@z&AŠ@z&AŠ@z\| | AŠ@z -> AŠ; AŠ@z -> AŠ; AŠ@z -> AŠ | AŠ + AŠ + AŠ | 0 |
| \|LAGAB×AŠ@c\| | AŠ@c -> AŠ | LAGAB + AŠ | 0 |
| \|EZEN×U@c\| | U@c -> U | EZEN + U | 0 |
| \|GIŠ×EŠ₂@t\| | EŠ₂@t -> EŠ₂ | GIŠ + EŠ₂ | 0 |

*These are real rows of the file, not decisions.*
