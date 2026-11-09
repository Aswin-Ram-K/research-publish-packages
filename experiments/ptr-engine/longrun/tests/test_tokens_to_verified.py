"""Tests for experiments/ptr-engine/tools/tokens_to_verified.py (TVS, grade_v5 of record).

Six contracted cases: T6 cutoff, T12-in-48 cutoff, no pass, null completion_tokens,
fetch follow-up at the pass turn, and the red->green whole-run mutation. One extra
case pins the duplicate-record rule.
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TOOLS = os.path.join(ROOT, "experiments", "ptr-engine", "tools")
sys.path.insert(0, TOOLS)

import tokens_to_verified as ttv  # noqa: E402


def row(turn, prompt=100, completion=10, cached=40, kind="turn", ts=None, arm="pointer-stable",
        content="x", rep=1):
    return {
        "arm": arm, "rep": rep, "turn": turn, "kind": kind,
        "prompt_tokens": prompt, "completion_tokens": completion, "cached_tokens": cached,
        "ts": ts or "2026-10-26T13:00:%02d.000Z" % (turn % 60), "content_sha256": content,
    }


def grade_v5(pass_turns, all_turns=(12, 24, 46), arm="pointer-stable"):
    """pass_turns: iterable of turns graded pass; every other declared turn grades fail."""
    cells = []
    for t in all_turns:
        cells.append({
            "id": "cp.%d.t%02d" % (all_turns.index(t), t), "turn": t, "arm": arm,
            "verdict": "pass" if t in pass_turns else "fail",
            "reason": "num_equal" if t in pass_turns else "answer_not_contract",
        })
    return {"grader": "grade_v5", "arms": {arm: {"passed": len(list(pass_turns))}}, "cells": cells}


class TVSCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tvs-test-")

    def write(self, name, obj):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            if name.endswith(".jsonl"):
                for r in obj:
                    fh.write(json.dumps(r) + "\n")
            else:
                json.dump(obj, fh)
        return path

    def run_cell(self, rows, grade, arm="pointer-stable", **kw):
        return ttv.analyse(self.write("rows.jsonl", rows), self.write("grade.json", grade),
                           arm=arm, grid="rows-synthetic", **kw)

    # 1 -- pass at T6 covers turns 1-6 exactly; a row added after T6 does not change it
    def test_t6_covers_turns_1_to_6(self):
        rows = [row(t) for t in range(1, 21)]
        out = self.run_cell(rows, grade_v5({6}, all_turns=(6, 12, 24)))
        self.assertEqual(out["tvs"]["turn"], 6)
        self.assertEqual(out["tvs"]["tokens"], 6 * 110)
        rows.append(row(21, prompt=999, completion=99))
        later = self.run_cell(rows, grade_v5({6}, all_turns=(6, 12, 24)))
        self.assertEqual(later["tvs"]["tokens"], 6 * 110)

    # 2 -- a pass at T12 in a 48-turn run sums turns 1-12 only, not the whole run
    def test_t12_in_48_turn_run_is_not_whole_run(self):
        rows = [row(t) for t in range(1, 49)]
        out = self.run_cell(rows, grade_v5({12}))
        self.assertEqual(out["tvs"]["turn"], 12)
        self.assertEqual(out["tvs"]["tokens"], 12 * 110)
        self.assertEqual(out["whole_run_total"], 48 * 110)
        self.assertNotEqual(out["tvs"]["tokens"], out["whole_run_total"])

    # 3 -- no pass: key present, value null, reason no_verified_success
    def test_no_pass_is_null_not_zero(self):
        out = self.run_cell([row(t) for t in range(1, 49)], grade_v5(set()))
        self.assertIn("tvs", out)
        self.assertIsNone(out["tvs"])
        self.assertEqual(out["reason"], "no_verified_success")
        self.assertEqual(out["pass_turns"], [])

    # 4 -- a null completion_tokens row is excluded and counted, never treated as 0
    def test_null_completion_token_row_excluded_and_counted(self):
        rows = [row(t) for t in range(1, 7)]
        rows[2] = row(3, completion=None)
        out = self.run_cell(rows, grade_v5({6}, all_turns=(6, 12, 24)))
        self.assertEqual(out["tvs"]["tokens"], 5 * 110)
        self.assertEqual(out["tvs"]["excluded_null_token_rows"], 1)
        self.assertEqual(out["tvs"]["null_token_turns"], [3])

    # 5 -- a pass whose turn carries a fetch/tool follow-up bills BOTH requests
    def test_fetch_followup_at_pass_turn_is_included(self):
        rows = [row(t) for t in range(1, 12)]
        rows.append(row(12, prompt=100, completion=10, kind="turn",
                        ts="2026-10-26T13:12:01.000Z", content="main"))
        rows.append(row(12, prompt=200, completion=20, kind="tool-followup",
                        ts="2026-10-26T13:12:02.000Z", content="followup"))
        out = self.run_cell(rows, grade_v5({12}))
        self.assertEqual(out["tvs"]["tokens"], 11 * 110 + 110 + 220)
        self.assertEqual(out["tvs"]["requests_counted"], 13)

    # 6 -- red -> green: the whole-run window must fail the T12 assertion, then restore
    def test_red_green_whole_run_fails_t12_then_restores(self):
        rows = [row(t) for t in range(1, 49)]
        g = grade_v5({12})
        green = self.run_cell(rows, g)
        red = self.run_cell(rows, g, whole_run=True)
        self.assertEqual(green["tvs"]["tokens"], 12 * 110)     # green
        self.assertNotEqual(red["tvs"]["tokens"], 12 * 110)   # red: whole-run total
        self.assertEqual(red["tvs"]["tokens"], 48 * 110)
        self.assertEqual(self.run_cell(rows, g)["tvs"]["tokens"], 12 * 110)  # restored

    # 7 -- duplicate records of one billed request are counted once (the runner logs the
    #      last follow-up twice: kind="turn" and kind="tool-followup" at the same ts)
    def test_duplicate_record_of_one_request_counted_once(self):
        rows = [row(t) for t in range(1, 7)]
        rows.append(row(6, kind="tool-followup", ts=rows[5]["ts"], content="x"))
        out = self.run_cell(rows, grade_v5({6}, all_turns=(6, 12, 24)))
        self.assertEqual(out["duplicate_records_skipped"], 1)
        self.assertEqual(out["tvs"]["tokens"], 6 * 110)


if __name__ == "__main__":
    unittest.main(verbosity=2)
