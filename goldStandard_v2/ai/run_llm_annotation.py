#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: run_llm_annotation.py
Description: Workflow Stage 1, Step 7.2 (LLM correction). Takes the rule-based draft
             (annotate_corpus.py output, Step 7.1), shows each tablet to Claude together
             with the gold guidelines (ai_system_prompt.md) and few-shot
             examples drawn ONLY from the TRAIN split of the gold standard,
             and merges Claude's corrections back into the sign rows.
             The validation split is never used as an example.
             Usage:
               python3 run_llm_annotation.py <draft.csv> <gold_train.csv> <out.csv>
                   [--model claude-sonnet-5-5] [--dry-run] [--limit N]
                   [--max-words 300] [--only-flagged]
             --dry-run writes the prompts to <out>.prompts/ without calling
             the API (to inspect them). Needs ANTHROPIC_API_KEY otherwise.
Author: Aima, prepared with Claude
Date: 2026-11-09
Version: 1.2
"""

import argparse
import csv
import json
import os
import random
from collections import OrderedDict, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
CODE = {"LOGO": "L", "SYLL": "S", "DET": "D", "NUM": "N", "UNCLEAR": "?"}
DECODE = {v: k for k, v in CODE.items()}

TOOL = {
    "name": "submit_annotation",
    "description": "Return corrected function labels for the words of one tablet.",
    "input_schema": {
        "type": "object",
        "properties": {
            "words": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "word_id": {"type": "string"},
                        "labels": {"type": "string",
                                   "description": "one of L/S/D/N/? per sign, in order"},
                        "sign_fixes": {
                            "type": "array",
                            "items": {"type": "object",
                                      "properties": {
                                          "sign_index": {"type": "integer"},
                                          "sign_name": {"type": "string"}},
                                      "required": ["sign_index", "sign_name"]}},
                        "check": {"type": "boolean"},
                        "note": {"type": "string"}},
                    "required": ["word_id", "labels", "check"]}}},
        "required": ["words"]},
}


def words_of(rows):
    """Group sign rows (first component only) into words, keep order."""
    w = OrderedDict()
    for r in rows:
        if r["component_position"] not in ("", "1"):
            continue
        w.setdefault(r["word_id"], []).append(r)
    return w


def word_line(wid, sigs, labels=None):
    lab = labels or [CODE[s["sign_function"]] for s in sigs]
    toks = " ".join(f"{s['reading'] or s['raw_sign']}:{l}" for s, l in zip(sigs, lab))
    flags = ";".join(sorted({s["check_reason"] for s in sigs if s["check_reason"]}))
    return f"{wid} | {sigs[0]['raw_word']} | {sigs[0]['word_lang']} | {toks} | {flags or '-'}"


def build_fewshot(train_rows, n_plain=60, seed=20261109):
    """Few-shot block: every manually decided word of the train split (the
    hard cases) + a random sample of ordinary words per language."""
    rng = random.Random(seed)
    w = words_of(train_rows)
    hard = [k for k, s in w.items() if any(x["annotation_status"] ==
                                           "claude_word_override" for x in s)]
    plain = [k for k, s in w.items() if k not in hard and len(s) > 1]
    rng.shuffle(plain)
    by_lang = defaultdict(list)
    for k in plain:
        by_lang[w[k][0]["word_lang"][:3]].append(k)
    chosen = hard + by_lang["sux"][:n_plain // 2] + by_lang["akk"][:n_plain // 2]
    lines = ["# Gold Examples (train split; labels are correct)\n",
             "word_id | raw ATF word | language | reading:GOLD_label ... | -"]
    for k in chosen:
        note = next((x["annotator_note"] for x in w[k] if x["annotator_note"]), "")
        lines.append(word_line(k, w[k]).rsplit("|", 1)[0] + f"| {note or '-'}")
    return "\n".join(lines)


def chunks_of(rows, max_words):
    """Large tablets (up to ~18,000 signs) do not fit into one request:
    split the tablet into consecutive parts of at most max_words words."""
    order = list(words_of(rows).keys())
    for i in range(0, len(order), max_words):
        ids = set(order[i:i + max_words])
        yield i // max_words + 1, [r for r in rows if r["word_id"] in ids]


def tablet_prompt(pid, rows, meta_line, part=1, n_parts=1):
    w = words_of(rows)
    title = f"# Tablet {pid}" + (f" (part {part} of {n_parts})" if n_parts > 1 else "")
    lines = [title, meta_line, "",
             "word_id | raw ATF word | language | reading:draft_label ... | draft flags"]
    cur_line = None
    for k, s in w.items():
        if s[0]["line_ref"] != cur_line:
            cur_line = s[0]["line_ref"]
            lines.append(f"## line {cur_line}")
        lines.append(word_line(k, s))
    return "\n".join(lines)


def merge(rows, answer):
    """Apply Claude's word-level answer to all sign rows of the tablet."""
    by_word = defaultdict(list)
    for r in rows:
        by_word[r["word_id"]].append(r)
    for item in answer.get("words", []):
        sigs = by_word.get(item["word_id"])
        if not sigs:
            continue
        units = OrderedDict()
        for r in sigs:
            units.setdefault(r["reading_unit_id"], []).append(r)
        labs = item["labels"]
        if len(labs) != len(units):
            for r in sigs:
                r["needs_check"] = "1"
                r["check_reason"] += " | llm:label_length_mismatch"
            continue
        fixes = {f["sign_index"]: f["sign_name"] for f in item.get("sign_fixes", [])}
        for i, (ru, comp_rows) in enumerate(units.items(), 1):
            for r in comp_rows:
                new = DECODE.get(labs[i - 1], r["sign_function"])
                if new != r["sign_function"]:
                    r["sign_function"] = new
                    r["function_rule"] = "llm_correction"
                present = r["damage_state"].split(",")[0] not in (
                    "restored", "supplied", "superfluous")
                r["include_in_analysis"] = str(int(new in ("LOGO", "SYLL") and present))
                if i in fixes:
                    r["sign_name"] = fixes[i]
                    r["unicode_id"] = ""   # re-resolve against OSL afterwards
                    r["check_reason"] += " | llm:sign_changed"
                    r["needs_check"] = "1"
                if item.get("check"):
                    r["needs_check"] = "1"
                    r["check_reason"] += " | llm:check"
                r["annotation_status"] = "llm"
                if item.get("note"):
                    r["annotator_note"] = item["note"]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("gold_train")
    ap.add_argument("out")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-words", type=int, default=300,
                    help="words per request; larger tablets are split")
    ap.add_argument("--only-flagged", action="store_true",
                    help="send only tablets (parts) with needs_check rows")
    a = ap.parse_args()

    with open(a.draft, encoding="utf-8") as f:
        draft = list(csv.DictReader(f))
    with open(a.gold_train, encoding="utf-8") as f:
        train = list(csv.DictReader(f))
    system = (HERE / "ai_system_prompt.md").read_text(encoding="utf-8")
    fewshot = build_fewshot(train)
    by_tab = OrderedDict()
    for r in draft:
        by_tab.setdefault(r["artifact_id"], []).append(r)
    tabs = list(by_tab.items())[: a.limit or None]

    client = None
    if not a.dry_run:
        import anthropic  # pip install anthropic
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    pdir = Path(a.out + ".prompts")
    pdir.mkdir(exist_ok=True)
    log = []
    for pid, rows in tabs:
        meta = (f"corpus={rows[0]['corpus_group']} genre={rows[0]['genre_cdli']} "
                f"language={rows[0]['atf_lang']} provenience={rows[0]['provenience']}")
        parts = list(chunks_of(rows, a.max_words))
        for part, sub in parts:
            if a.only_flagged and not any(r["needs_check"] == "1" for r in sub):
                continue
            user = fewshot + "\n\n" + tablet_prompt(pid, sub, meta, part, len(parts))
            name = pid if len(parts) == 1 else f"{pid}_part{part}"
            (pdir / f"{name}.txt").write_text(system + "\n\n=====\n\n" + user,
                                             encoding="utf-8")
            if a.dry_run:
                continue
            msg = client.messages.create(
                model=a.model, max_tokens=8000, system=system,
                tools=[TOOL], tool_choice={"type": "tool", "name": TOOL["name"]},
                messages=[{"role": "user", "content": user}])
            answer = next((b.input for b in msg.content if b.type == "tool_use"), {})
            merge(sub, answer)
            log.append({"tablet": name, "changed_words": len(answer.get("words", [])),
                        "input_tokens": msg.usage.input_tokens,
                        "output_tokens": msg.usage.output_tokens})
            print(log[-1])
    out_rows = [r for _, rows in tabs for r in rows]
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(draft[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    Path(a.out + ".log.json").write_text(json.dumps(log, indent=1))
    print(f"done: {len(tabs)} tablets -> {a.out}  (prompts in {pdir})")


if __name__ == "__main__":
    main()
