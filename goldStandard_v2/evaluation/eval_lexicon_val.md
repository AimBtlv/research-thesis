# Evaluation Report (Validation Split)

*Gold rows:* 498  *Predicted rows:* 498  *Aligned:* 498  *Missing in prediction:* 0  *Extra in prediction:* 0

*Token alignment (coverage):* 1.000


## Overall

*Rows:* 498

| Metric | Value |
|---|---|
| Sign name accuracy | 1.000 |
| Unicode accuracy | 1.000 |
| Function accuracy (5 classes) | 0.972 |
| Function macro-F1 | 0.987 |
| Function Cohen's kappa | 0.955 |
| LOGO/SYLL accuracy (gold LOGO or SYLL) | 0.967 |
| include_in_analysis agreement | 1.000 |

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| LOGO | 0.952 | 0.987 | 0.969 | 223 |
| SYLL | 0.985 | 0.946 | 0.965 | 205 |
| DET | 1.000 | 1.000 | 1.000 | 23 |
| NUM | 1.000 | 1.000 | 1.000 | 15 |
| UNCLEAR | 1.000 | 1.000 | 1.000 | 32 |

*Confusion matrix (rows = gold, columns = prediction):*

| gold \ pred | LOGO | SYLL | DET | NUM | UNCLEAR |
|---|---|---|---|---|---|
| LOGO | 220 | 3 | 0 | 0 | 0 |
| SYLL | 11 | 194 | 0 | 0 | 0 |
| DET | 0 | 0 | 23 | 0 | 0 |
| NUM | 0 | 0 | 0 | 15 | 0 |
| UNCLEAR | 0 | 0 | 0 | 0 | 32 |

## By corpus: LETTER

*Rows:* 80

| Metric | Value |
|---|---|
| Sign name accuracy | 1.000 |
| Unicode accuracy | 1.000 |
| Function accuracy (5 classes) | 1.000 |
| Function macro-F1 | 1.000 |
| Function Cohen's kappa | 1.000 |
| LOGO/SYLL accuracy (gold LOGO or SYLL) | 1.000 |
| include_in_analysis agreement | 1.000 |

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| LOGO | 1.000 | 1.000 | 1.000 | 36 |
| SYLL | 1.000 | 1.000 | 1.000 | 38 |
| DET | 1.000 | 1.000 | 1.000 | 5 |
| NUM | 1.000 | 1.000 | 1.000 | 1 |

*Confusion matrix (rows = gold, columns = prediction):*

| gold \ pred | LOGO | SYLL | DET | NUM | UNCLEAR |
|---|---|---|---|---|---|
| LOGO | 36 | 0 | 0 | 0 | 0 |
| SYLL | 0 | 38 | 0 | 0 | 0 |
| DET | 0 | 0 | 5 | 0 | 0 |
| NUM | 0 | 0 | 0 | 1 | 0 |
| UNCLEAR | 0 | 0 | 0 | 0 | 0 |

## By corpus: LEXICAL

*Rows:* 58

| Metric | Value |
|---|---|
| Sign name accuracy | 1.000 |
| Unicode accuracy | 1.000 |
| Function accuracy (5 classes) | 0.983 |
| Function macro-F1 | 0.988 |
| Function Cohen's kappa | 0.973 |
| LOGO/SYLL accuracy (gold LOGO or SYLL) | 0.978 |
| include_in_analysis agreement | 1.000 |

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| LOGO | 1.000 | 0.964 | 0.982 | 28 |
| SYLL | 0.944 | 1.000 | 0.971 | 17 |
| DET | 1.000 | 1.000 | 1.000 | 2 |
| NUM | 1.000 | 1.000 | 1.000 | 11 |

*Confusion matrix (rows = gold, columns = prediction):*

| gold \ pred | LOGO | SYLL | DET | NUM | UNCLEAR |
|---|---|---|---|---|---|
| LOGO | 27 | 1 | 0 | 0 | 0 |
| SYLL | 0 | 17 | 0 | 0 | 0 |
| DET | 0 | 0 | 2 | 0 | 0 |
| NUM | 0 | 0 | 0 | 11 | 0 |
| UNCLEAR | 0 | 0 | 0 | 0 | 0 |

## By corpus: LITERARY

*Rows:* 255

| Metric | Value |
|---|---|
| Sign name accuracy | 1.000 |
| Unicode accuracy | 1.000 |
| Function accuracy (5 classes) | 0.953 |
| Function macro-F1 | 0.971 |
| Function Cohen's kappa | 0.917 |
| LOGO/SYLL accuracy (gold LOGO or SYLL) | 0.947 |
| include_in_analysis agreement | 1.000 |

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| LOGO | 0.928 | 0.993 | 0.959 | 142 |
| SYLL | 0.987 | 0.871 | 0.925 | 85 |
| DET | 1.000 | 1.000 | 1.000 | 13 |
| UNCLEAR | 1.000 | 1.000 | 1.000 | 15 |

*Confusion matrix (rows = gold, columns = prediction):*

| gold \ pred | LOGO | SYLL | DET | NUM | UNCLEAR |
|---|---|---|---|---|---|
| LOGO | 141 | 1 | 0 | 0 | 0 |
| SYLL | 11 | 74 | 0 | 0 | 0 |
| DET | 0 | 0 | 13 | 0 | 0 |
| NUM | 0 | 0 | 0 | 0 | 0 |
| UNCLEAR | 0 | 0 | 0 | 0 | 15 |

## By corpus: SCHOOL

*Rows:* 105

| Metric | Value |
|---|---|
| Sign name accuracy | 1.000 |
| Unicode accuracy | 1.000 |
| Function accuracy (5 classes) | 0.990 |
| Function macro-F1 | 0.992 |
| Function Cohen's kappa | 0.983 |
| LOGO/SYLL accuracy (gold LOGO or SYLL) | 0.988 |
| include_in_analysis agreement | 1.000 |

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| LOGO | 1.000 | 0.941 | 0.970 | 17 |
| SYLL | 0.985 | 1.000 | 0.992 | 65 |
| DET | 1.000 | 1.000 | 1.000 | 3 |
| NUM | 1.000 | 1.000 | 1.000 | 3 |
| UNCLEAR | 1.000 | 1.000 | 1.000 | 17 |

*Confusion matrix (rows = gold, columns = prediction):*

| gold \ pred | LOGO | SYLL | DET | NUM | UNCLEAR |
|---|---|---|---|---|---|
| LOGO | 16 | 1 | 0 | 0 | 0 |
| SYLL | 0 | 65 | 0 | 0 | 0 |
| DET | 0 | 0 | 3 | 0 | 0 |
| NUM | 0 | 0 | 0 | 3 | 0 |
| UNCLEAR | 0 | 0 | 0 | 0 | 17 |

## By language: akk

*Rows:* 137

| Metric | Value |
|---|---|
| Sign name accuracy | 1.000 |
| Unicode accuracy | 1.000 |
| Function accuracy (5 classes) | 0.985 |
| Function macro-F1 | 0.991 |
| Function Cohen's kappa | 0.978 |
| LOGO/SYLL accuracy (gold LOGO or SYLL) | 0.980 |
| include_in_analysis agreement | 1.000 |

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| LOGO | 1.000 | 0.939 | 0.969 | 33 |
| SYLL | 0.971 | 1.000 | 0.986 | 68 |
| DET | 1.000 | 1.000 | 1.000 | 5 |
| NUM | 1.000 | 1.000 | 1.000 | 14 |
| UNCLEAR | 1.000 | 1.000 | 1.000 | 17 |

*Confusion matrix (rows = gold, columns = prediction):*

| gold \ pred | LOGO | SYLL | DET | NUM | UNCLEAR |
|---|---|---|---|---|---|
| LOGO | 31 | 2 | 0 | 0 | 0 |
| SYLL | 0 | 68 | 0 | 0 | 0 |
| DET | 0 | 0 | 5 | 0 | 0 |
| NUM | 0 | 0 | 0 | 14 | 0 |
| UNCLEAR | 0 | 0 | 0 | 0 | 17 |

## By language: sux

*Rows:* 361

| Metric | Value |
|---|---|
| Sign name accuracy | 1.000 |
| Unicode accuracy | 1.000 |
| Function accuracy (5 classes) | 0.967 |
| Function macro-F1 | 0.985 |
| Function Cohen's kappa | 0.942 |
| LOGO/SYLL accuracy (gold LOGO or SYLL) | 0.963 |
| include_in_analysis agreement | 1.000 |

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| LOGO | 0.945 | 0.995 | 0.969 | 190 |
| SYLL | 0.992 | 0.920 | 0.955 | 137 |
| DET | 1.000 | 1.000 | 1.000 | 18 |
| NUM | 1.000 | 1.000 | 1.000 | 1 |
| UNCLEAR | 1.000 | 1.000 | 1.000 | 15 |

*Confusion matrix (rows = gold, columns = prediction):*

| gold \ pred | LOGO | SYLL | DET | NUM | UNCLEAR |
|---|---|---|---|---|---|
| LOGO | 189 | 1 | 0 | 0 | 0 |
| SYLL | 11 | 126 | 0 | 0 | 0 |
| DET | 0 | 0 | 18 | 0 | 0 |
| NUM | 0 | 0 | 0 | 1 | 0 |
| UNCLEAR | 0 | 0 | 0 | 0 | 15 |

## Errors (Function or Sign) For Qualitative Review

| Tablet | Line | Word | Sign | Gold | Pred | Type |
|---|---|---|---|---|---|---|
| P251826 | obv::7 | `adab{ki}` | adab | LOGO | SYLL | function |
| P478899 | sur::3 | `sze-er-zi3` | še | SYLL | LOGO | function |
| P478899 | sur::3 | `sze-er-zi3` | er | SYLL | LOGO | function |
| P478899 | sur::4 | `sze-er-zi3` | še | SYLL | LOGO | function |
| P478899 | sur::4 | `sze-er-zi3` | er | SYLL | LOGO | function |
| P478899 | sur::20 | `nu-kusz2-u3-de3` | u₃ | SYLL | LOGO | function |
| P478899 | sur::28 | `im-me` | im | SYLL | LOGO | function |
| P478899 | sur::29 | `im-me` | im | SYLL | LOGO | function |
| P478899 | sur::30 | `e-ne` | e | SYLL | LOGO | function |
| P478899 | sur::30 | `mu-un-da-e` | mu | SYLL | LOGO | function |
| P478899 | sur::30 | `mu-un-da-e` | un | SYLL | LOGO | function |
| P478899 | sur::30 | `mu-un-da-e` | e | LOGO | SYLL | function |
| P478899 | sur::31 | `mu-da-ab-kusz2-u3` | u₃ | SYLL | LOGO | function |
| P423699 | obv::4 | `sin-isz-me-an-ni` | sin | LOGO | SYLL | function |
