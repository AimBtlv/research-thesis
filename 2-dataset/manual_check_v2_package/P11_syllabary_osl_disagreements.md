# P11. Syllabary And OSL Name Different Signs 

*File: `P11_syllabary_osl_disagreements.csv`     
18 rows      
Check_id `P11-0001`–`P11-0018`          
The outputs of 2026-11-22*

## **Place In The Workflow 
Stage 1, Step 6.0 (manual check before the gold standard).
Documented in `1.doc_unicode_assign_v3.md`, Step 1.2, *Correction: OSL decides which sign it is*
Script:`02_join_unicode_syllabary_CM.py`

## The Problem

*What Step 1.2 does?*      
For each of the 1,234 Unicode characters it finds **which sign** it is and which readings it has. Every character has a code point, a glyph and an English Unicode name:

    U+12083   𒂃   "CUNEIFORM SIGN DUH"



*The rule of version 1.2: OSL decides*      
OSL records the code point of every sign **directly** (`@list U+12083` in `@sign DUH`). Since v1.2:
1. **which sign** it is, is decided by OSL through the code point
2. the syllabary gives the **readings** only if it names the **same** sign
3. otherwise the sign is described from OSL (Step 1.3).
>[Note] Before version 1.2 the script looked for the sign in the syllabary **by this
English name** or, failing that, **by a reading**. So the character "duh" went
to the sign GABA, because GABA has the reading *duh* in the syllabary. *Why this is dangerous?* A character assigned to the wrong sign receives the
**readings of another sign**: *gaba* got the glyph 𒂃 (DUH) instead of its own.
About 2,480 words of the corpus had a wrong sign (*gaba* → DUH, *kalam* →
KALAM@g, *na₄* → DAG₃).
This file lists all 18 disagreements: in 3 cases the syllabary sign with the
OSL name was used (NIN → |SAL.TUG₂|, ARKAB₂, NU₁₁@t), in 15 the sign was
described from OSL (𒂃: GABA → DUH).

## Automatic Fix 

**Already decided automatically.** 
The rule is convenient, but OSL can also be wrong or use another notation, so the check confirms or rejects it sign by sign against MZL.     
Two pairs need special care:
- **𒌦 (Unicode "UN") and 𒌧 ("UN gunû")**: in our OSL 𒌦 = KALAM@g and
  𒌧 = KALAM. The syllabary calls them UN and UN@g. 9,993 tokens depend on this
  pair (*un*, *uĝ₃*, *kalam*).
- **𒎏 NIN = |SAL.TUG₂|**: the same sign under two names, almost certainly
  safe, but 7,200 tokens.

## Size And Effect On The Corpus 

18 signs     
9 occur in the corpus.     
**21,670** tokens (366 in school texts).        
The most frequent:    
𒌦 UN / KALAM@g (8,896),    
𒎏 NIN / |SAL.TUG₂| (7,200),    
𒂃 GABA / DUH (2,504),    
𒌧 UN@g / KALAM (1,097),    
𒌤 UMUM×KASKAL / DE₂ (1,044),     
𒇇 LAGAB×GUD+GUD / |LAGAB×(GUD&GUD)| (906).    
All 18 rows are mandatory.     
## **Which Rows To Check (Scope)**   

All rows: **mandatory**.

## **Columns (Columns)**

| Column | Meaning |
|---|---|
| `syllabary_sign / osl_sign / step1_decision` | the two names and what Step 1.2 did |
| `check_id` | row id (P01-0001 …); quote it in e-mails |
| `tokens_in_OB_corpus` | how often the parser used this case in the OB corpus (atf_tokens.csv) |
| `tokens_school / tokens_practical` | the same, split by the CDLI flag `is_school_text` |
| `top_sites` | the four most frequent proveniences of these tokens |
| `corpus_example` | first tablet (P-number) and line, to open the photo / hand copy on CDLI |

Only the empty columns at the right end (`decision`, …, `comment`) are filled in.

## **How To Check One Row (Procedure)**

1. Compare with MZL (and Labat if needed).
2. Write the decision.

## **Decision Values (decision)**

| Value | Meaning | Other columns |
|---|---|---|
| `CONFIRM_OSL` | OSL is right | – |
| `USE_SYLLABARY` | the syllabary is right | reason |
| `UNSURE` | cannot decide | reason |

## **First Rows Of The File (Examples)**

| syllabary_sign | osl_sign | step1_decision | tokens_in_OB_corpus |
|---|---|---|---|
| GAR.IB | ARKAB₂ | syllabary sign ARKAB2 (= OSL name) used | 1 |
| GABA | DUH | not matched: described from OSL in Step 1.3 | 2504 |
| HI×U | \|ŠAR₂×U\| | not matched: described from OSL in Step 1.3 | 0 |
| LAGAB×GUD+GUD | \|LAGAB×(GUD&GUD)\| | not matched: described from OSL in Step 1.3 | 906 |
| MA×TAK4 | \|MA@g×TAK₄\| | not matched: described from OSL in Step 1.3 | 0 |
| ŠIR@t | NU₁₁@t | syllabary sign NU11@t (= OSL name) used | 0 |

*These are real rows of the file, not decisions.*
