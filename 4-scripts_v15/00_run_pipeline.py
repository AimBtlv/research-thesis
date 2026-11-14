#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: 00_run_pipeline.py
Description: Workflow Stage 1, Steps 1-5 + check. Runs the whole pipeline
             with one command, without VS Code:
                 python3 00_run_pipeline.py
             The scripts 01-09 are run one after another, in order. The run
             stops at the first script that fails and prints its name.
             The helper modules 08a_function_layer.py and 08b_goldlib.py are
             not run here: script 08 loads them itself.
             Options:
                 --from 07   start at script 07 (Steps 1-4 already done)
                 --list      only print the scripts and their steps
Author: Aima, prepared with Claude
Date: 2026-11-12
Version: 1.0
"""

import subprocess
import sys
import time
from pathlib import Path

# --- The scripts, in run order: (file, step of the workflow, what it does) ---
SCRIPTS = [
    ("01_build_syllabary_CM.py",        "1.1",  "merged syllabary Syllabary_CM.csv"),
    ("02_join_unicode_syllabary_CM.py", "1.2",  "Unicode signs x syllabary (779 + 455), OSL decides the sign"),
    ("03_build_rest_unicode_signs.py",  "1.3",  "the other 455 signs from OSL"),
    ("04_join_matched_rest_signs.py",   "1.4",  "full list of 1,234 Unicode signs"),
    ("05_build_diri_lexical_list.py",   "2",    "Diri list (skipped without the Oracc JSON)"),
    ("06_build_sign_catalogue_v13.py",  "3-4",  "compound readings + sign catalogue"),
    ("07_parse_atf_to_tokens_v14.py",   "5.1",  "ATF -> atf_tokens.csv (whole OB corpus)"),
    ("08_tokens_to_grapheme_v14.py",    "5.2",  "atf_tokens.csv -> grapheme.csv"),
    ("09_verify_pipeline.py",           "check", "PASS / DIFF for every step"),
]

HERE = Path(__file__).resolve().parent      # the scripts always run from their own folder


def parse_args(argv):
    """Very small argument parser: --from NN and --list."""
    start, only_list = "01", False
    if "--list" in argv:
        only_list = True
    if "--from" in argv:
        i = argv.index("--from")
        if i + 1 >= len(argv):
            sys.exit("[ERROR] --from needs a number, e.g. --from 07")
        start = argv[i + 1].zfill(2)
    return start, only_list


def main():
    if sys.version_info < (3, 9):
        sys.exit(f"[ERROR] Python 3.9 or newer is needed (this is {sys.version.split()[0]})")

    start, only_list = parse_args(sys.argv[1:])
    todo = [s for s in SCRIPTS if s[0][:2] >= start]
    if not todo:
        sys.exit(f"[ERROR] no script with a number >= {start}")

    missing = [name for name, _, _ in todo if not (HERE / name).exists()]
    for helper in ("08a_function_layer.py", "08b_goldlib.py"):
        if any(n.startswith("08_") for n, _, _ in todo) and not (HERE / helper).exists():
            missing.append(helper)
    if missing:
        sys.exit("[ERROR] missing in " + str(HERE) + ":\n  " + "\n  ".join(missing))

    print(f"Python {sys.version.split()[0]} | folder {HERE}")
    for name, step, what in todo:
        print(f"  {name:34} step {step:5} {what}")
    if only_list:
        return

    total_start = time.time()
    for k, (name, step, what) in enumerate(todo, 1):
        print(f"\n=== [{k}/{len(todo)}] {name} (step {step}) ===", flush=True)
        t0 = time.time()
        result = subprocess.run([sys.executable, name], cwd=HERE)
        took = time.time() - t0
        if result.returncode != 0:
            print(f"\n[STOP] {name} failed (exit code {result.returncode}) after {took:.0f} s.")
            print("       Fix the error shown above, then continue with:")
            print(f"       python3 {Path(__file__).name} --from {name[:2]}")
            sys.exit(result.returncode)
        print(f"--- {name}: done in {took:.0f} s")

    print(f"\nThe whole pipeline finished in {(time.time() - total_start) / 60:.1f} min.")
    print("See the PASS / DIFF table of 09_verify_pipeline.py above.")


if __name__ == "__main__":
    main()
