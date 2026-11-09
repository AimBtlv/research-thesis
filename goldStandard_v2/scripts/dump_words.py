#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: dump_words.py
Description: Workflow Stage 1, Step 6.6. Review helper - prints each unique word type with its sign-level
             function labels (L/S/D/N/?) for a given language and corpus file.
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.1
"""
import sys
import pandas as pd
g = pd.read_csv(sys.argv[1], dtype=str, keep_default_na=False)
lang = sys.argv[2]
g = g[g.component_position.isin(['', '1'])]
g = g[g.atf_lang.str.startswith(lang)]
ab = {'LOGO': 'L', 'SYLL': 'S', 'DET': 'D', 'NUM': 'N', 'UNCLEAR': '?'}
seen = {}
for wid, grp in g.groupby('word_id', sort=False):
    key = ' '.join(f"{r.reading or r.raw_sign}/{ab[r.sign_function]}" for r in grp.itertuples())
    rw = grp.iloc[0].raw_word
    if (rw, key) not in seen:
        seen[(rw, key)] = grp.iloc[0].artifact_id
for (rw, key), a in seen.items():
    if len(key.split()) > 1:
        print(a, '|', rw, '|', key)
