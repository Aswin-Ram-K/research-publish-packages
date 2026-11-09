"""Tests for experiments/ptr-engine/tools/stop_reason_audit.py (unit STOP-REASON-AUDIT).

Every test is offline: the only input is rows already on disk or rows this test
writes into a temporary directory.  No endpoint is called and no cell is re-run.

The contract under test, from docs/STOP-REASON.md:

(a) a reasoning-only row (length cap, empty content, reasoning produced) is
    classified `reasoning_only` and is NEVER counted as a wrong answer;
(b) a truncated row (length cap, partial content) is classified
    `truncated_answer` and stays a gradable answer, not `missing_answer_empty`;
(c) a normal answered row is graded normally;
(d) a genuine wrong answer (content present, wrong value) is still `fail` and is
    NOT swept into `missing_answer_empty`.

Red→green: (a)-(d) fail on the pre-fix scanner (which had no cause vocabulary and
therefore reported an empty row and a wrong answer through the same "fail" door);
they pass once `classify_row`/`row_state`/`verdict` separate emptiness from
wrongness.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
MEASURE = os.path.abspath(os.path.join(HERE, "..", "..", "measure"))
sys.path.insert(0, TOOLS)

import stop_reason_audit as sra  # noqa: E402

STAGE1 = os.path.join(MEASURE, "rows-longrun-2026-10-26.jsonl")


def crafted_rows():
    """The three crafted rows the contract names, plus the wrong-answer control."""
    return [
        # (a) reasoning-only: the cap stopped the stream, the budget went to thinking.
        {
            "arm": "probe", "turn": 1, "rep": 1,
            "completion_tokens": 400, "max_tokens": 400,
            "finish_reason": "length", "truncated": True,
            "content": "",
            "reasoning_content": "Let me look at resolve.py ... the default is 64, so ",
            "reasoning_tokens": 400,
        },
        # (b) truncated answer: partial content, cap stopped it, still an answer.
        {
            "arm": "probe", "turn": 2, "rep": 1,
            "completion_tokens": 128, "max_tokens": 128,
            "finish_reason": "length", "truncated": True,
            "content": "The default is 64, and the budget is overri",
        },
        # (c) normal answered row.
        {
            "arm": "probe", "turn": 3, "rep": 1,
            "completion_tokens": 12, "max_tokens": 16384,
            "finish_reason": "stop", "truncated": False,
            "content": "64",
        },
        # (d) control: a real answer to a real question, and it is wrong.
        {
            "arm": "probe", "turn": 4, "rep": 1,
            "completion_tokens": 9, "max_tokens": 16384,
            "finish_reason": "stop", "truncated": False,
            "content": "128",
        },
    ]


class CraftedRows(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="stop-reason-")
        self.path = os.path.join(self.tmp, "rows-crafted.jsonl")
        with open(self.path, "w", encoding="utf-8") as handle:
            for row in crafted_rows():
                handle.write(json.dumps(row) + "\n")
        self.rows = crafted_rows()

    def tearDown(self):
        for name in os.listdir(self.tmp):
            os.unlink(os.path.join(self.tmp, name))
        os.rmdir(self.tmp)

    # (a) ------------------------------------------------------------------
    def test_reasoning_only_row_is_classified_and_never_fail(self):
        row = self.rows[0]
        info = sra.classify_row(row)
        self.assertTrue(info["empty"], "the reasoning-only row carries no answer text")
        self.assertEqual(info["cause"], "reasoning_only")
        self.assertEqual(info["label"], "empty_content: reasoning_only")
        self.assertEqual(info["reasoning"], "text")
        self.assertTrue(info["truncated"])
        self.assertEqual(sra.row_state(row)["state"], "missing_answer_empty")
        self.assertEqual(sra.verdict(row, expected="64"), "missing_answer_empty")
        self.assertNotEqual(sra.verdict(row, expected="64"), "fail")

    def test_reasoning_only_detected_from_tokens_without_text(self):
        row = dict(self.rows[0])
        row.pop("reasoning_content")
        info = sra.classify_row(row)
        self.assertEqual(info["reasoning"], "tokens")
        self.assertEqual(info["cause"], "reasoning_only")

    # (b) ------------------------------------------------------------------
    def test_truncated_row_is_an_answer_not_an_empty_row(self):
        row = self.rows[1]
        info = sra.classify_row(row)
        self.assertFalse(info["empty"], "a truncated row HAS partial content")
        self.assertTrue(info["truncated_answer"])
        self.assertIsNone(info["cause"], "a truncated answer is not an empty-content cause")
        self.assertEqual(sra.row_state(row)["state"], "gradable")
        self.assertNotEqual(sra.verdict(row), "missing_answer_empty")

    def test_capped_empty_row_without_reasoning_is_cap_exhausted(self):
        row = dict(self.rows[0])
        row.pop("reasoning_content")
        row.pop("reasoning_tokens")
        row["completion_tokens"] = 128
        row["max_tokens"] = 128
        self.assertEqual(sra.classify_row(row)["cause"], "cap_exhausted_no_content")

    # (c) ------------------------------------------------------------------
    def test_normal_row_is_graded_normally(self):
        row = self.rows[2]
        info = sra.classify_row(row)
        self.assertFalse(info["empty"])
        self.assertIsNone(info["cause"])
        self.assertFalse(info["truncated_answer"])
        self.assertEqual(sra.row_state(row)["state"], "gradable")
        self.assertEqual(sra.verdict(row, expected="64"), "pass")
        self.assertEqual(sra.verdict(row, expected="128"), "fail")

    # (d) ------------------------------------------------------------------
    def test_genuine_wrong_answer_stays_fail_and_is_not_swept_into_missing(self):
        row = self.rows[3]
        state = sra.row_state(row)
        self.assertEqual(state["state"], "gradable")
        self.assertIsNone(state["cause"])
        self.assertNotEqual(state["cause"], "unrecorded_empty_content")
        self.assertEqual(sra.verdict(row, expected="64"), "fail")
        self.assertNotEqual(sra.verdict(row, expected="64"), "missing_answer_empty")

    # scanner counts -------------------------------------------------------
    def test_scan_file_counts_empty_and_wrong_answer_separately(self):
        report = sra.scan_file(self.path)
        self.assertEqual(report["rows"], 4)
        self.assertEqual(report["answered_rows"], 3)          # (b) truncated, (c) normal, (d) wrong
        self.assertEqual(report["empty_content_rows"], 1)     # only (a) carries no text
        self.assertEqual(report["empty_content_with_completion_tokens"], 1)
        self.assertEqual(report["reasoning_with_empty_content"], 1)
        self.assertEqual(report["truncated_answer_rows"], 1)
        self.assertEqual(report["causes"], {"reasoning_only": 1})
        # The wrong answer is in the answered population and in NO empty-content bucket.
        hit_turns = [hit["turn"] for hit in report["hits"]]
        self.assertEqual(hit_turns, [1])
        self.assertNotIn(4, hit_turns, "a wrong answer must never be counted as empty content")

    def test_empty_content_row_never_reaches_fail_through_the_scanner(self):
        report = sra.scan_file(self.path)
        for hit in report["hits"]:
            self.assertTrue(hit["label"].startswith("empty_content: "))
            self.assertNotEqual(hit["cause"], None)

    # answer-field resolution ---------------------------------------------
    def test_old_schema_answer_text_is_an_answer_not_an_empty_row(self):
        # rows-baseline / rows-equalinfo write `answer_text` and have no `content`
        # key at all.  Reading only `content` would call every one of them empty.
        row = {"arm": "probe", "turn": 5, "rep": 1, "completion_tokens": 7,
               "answer_text": "64", "answer_correct": True}
        info = sra.classify_row(row)
        self.assertFalse(info["empty"], "the answer lives in answer_text, not content")
        self.assertEqual(info["answer_field"], "answer_text")
        self.assertIsNone(info["cause"])
        self.assertEqual(sra.verdict(row, expected="64"), "pass")

    def test_row_with_no_answer_field_is_not_a_model_failure_signal(self):
        row = {"turn": 1, "role": "probe", "completion_tokens": 1}
        info = sra.classify_row(row)
        self.assertTrue(info["empty"])
        self.assertEqual(info["cause"], "no_answer_text_field")
        self.assertEqual(sra.row_state(row)["state"], "missing_answer_empty")
        self.assertNotEqual(sra.verdict(row, expected="64"), "fail")


class StageOneCorpus(unittest.TestCase):
    """The measured corpus this unit was opened for — read-only, no re-run."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(STAGE1):
            raise unittest.SkipTest("rows-longrun-2026-10-26.jsonl not present")
        cls.report = sra.scan_file(STAGE1)

    def test_stage1_empty_rows_spend_exactly_the_cap(self):
        self.assertGreater(self.report["empty_content_with_completion_tokens"], 0)
        tokens = {hit["completion_tokens"]
                  for hit in self.report["hits"]}
        self.assertEqual(tokens, {128}, "every empty row in Stage 1 bills exactly the 128-token cap")

    def test_stage1_rows_record_nothing_about_the_stop(self):
        # TASK 5: the schema carried no finish_reason, so the cause is unrecorded.
        self.assertEqual(self.report["rows_with_finish_reason_field"], 0)
        self.assertEqual(self.report["rows_with_reasoning_field"], 0)
        for hit in self.report["hits"]:
            self.assertIsNone(hit["finish_reason"])
            self.assertFalse(hit["has_finish_field"])
            self.assertIsNone(hit["http_status"])
            self.assertIsNone(hit["error"])
            self.assertEqual(hit["cause"], "unrecorded_empty_content")

    def test_every_stage1_empty_row_is_missing_answer_empty_never_fail(self):
        for hit in self.report["hits"]:
            self.assertEqual(hit["label"], "empty_content: unrecorded_empty_content")


class OnDiskArtefact(unittest.TestCase):
    def test_stop_reason_json_matches_a_fresh_scan(self):
        path = os.path.join(MEASURE, "STOP-REASON.json")
        if not os.path.exists(path):
            raise unittest.SkipTest("STOP-REASON.json not written yet")
        result = subprocess.run(
            [sys.executable, os.path.join(TOOLS, "stop_reason_audit.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cap_128_is_recorded_as_a_harness_cap(self):
        path = os.path.join(MEASURE, "STOP-REASON.json")
        if not os.path.exists(path):
            raise unittest.SkipTest("STOP-REASON.json not written yet")
        with open(path, encoding="utf-8") as handle:
            report = json.load(handle)
        self.assertTrue(report["cap_128"]["is_harness_cap"])
        self.assertEqual(report["cap_128"]["cap_value"], 128)
        self.assertEqual(
            report["cap_128"]["frozen_in_manifest"]["path"],
            "experiments/ptr-engine/longrun/manifests/stage1-lr01-lease-reopen-r1.json",
        )
        self.assertEqual(report["cap_128"]["frozen_in_manifest"]["line"], 36)


if __name__ == "__main__":
    unittest.main()
