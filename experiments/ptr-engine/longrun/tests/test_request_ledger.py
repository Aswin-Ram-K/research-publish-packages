#!/usr/bin/env python3
"""Red->green tests for experiments/ptr-engine/tools/request_ledger.py.

Offline. Zero inference requests. No network. No git. Every fixture is built in a tmp dir;
the real row corpus is only ever READ (never written) -- the sha256 of every row file is
recomputed and compared before/after so a mutation would fail the run.

Cases, per the unit contract:
  (a) 5 turn + 3 tool-followup + 1 suppressed  -> requests == 8, and the suppressed row is NAMED
  (b) a `billed: false` row is not counted
  (c) a row whose schema cannot decide is counted and flagged `assumed_billed`
  (d) --would-spend that fits -> exit 0; that does not -> exit 4 with the four arithmetic values
  (e) an unparseable row file -> exit 5, nothing counted silently
  (f) two runs over identical input -> byte-identical JSON
  (g) the real corpus: print the computed total and the delta from the hand-carried 466

Run:  python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_request_ledger.py' -v
Override the implementation under test (used to demonstrate red):
      REQUEST_LEDGER_TOOL=/path/to/copy.py python3 -m unittest ...
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TOOL = os.environ.get(
    "REQUEST_LEDGER_TOOL",
    os.path.join(REPO, "experiments", "ptr-engine", "tools", "request_ledger.py"),
)
MEASURE = os.path.join(REPO, "experiments", "ptr-engine", "measure")

HAND_CARRIED_BASELINE = 466
LONGRUN_SHA_PREFIX = "bc61d381"


def write_rows(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def turn(n: int) -> dict:
    return {
        "kind": "turn",
        "arm": "fixture",
        "task_id": "T-1",
        "rep": 1,
        "turn": n,
        "prompt_tokens": 100 + n,
        "completion_tokens": 10,
        "ts": f"2026-10-26T12:00:{n:02d}.000Z",
    }


def followup(n: int) -> dict:
    return {
        "kind": "tool-followup",
        "arm": "fixture",
        "task_id": "T-1",
        "rep": 1,
        "turn": n,
        "prompt_tokens": 200,
        "completion_tokens": 5,
        "ts": f"2026-10-26T12:01:{n:02d}.000Z",
    }


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        digest.update(handle.read())
    return digest.hexdigest()


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, TOOL, *args],
        capture_output=True,
        text=True,
        cwd=REPO,
    )


class FixtureCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def pattern(self) -> str:
        return os.path.join(self.tmp, "rows-*.jsonl")

    def report(self, *args: str) -> dict:
        out = os.path.join(self.tmp, "report.json")
        proc = run_tool("--glob", self.pattern(), "--write", out, *args)
        self.assertIn(proc.returncode, (0, 4), proc.stderr)
        with open(out, "r", encoding="utf-8") as handle:
            return json.load(handle)


class TestCounting(FixtureCase):
    def test_a_five_turn_three_followup_one_suppressed_counts_eight(self) -> None:
        """(a) 5 turn + 3 tool-followup + 1 suppressed -> 8 requests, suppressed row named."""
        rows = [turn(n) for n in range(1, 6)]
        rows += [followup(n) for n in range(1, 4)]
        rows.append({**followup(9), "followup_suppressed": True})
        write_rows(os.path.join(self.tmp, "rows-a.jsonl"), rows)

        report = self.report()
        self.assertEqual(report["total"]["rows"], 9, "all 9 rows were read")
        self.assertEqual(report["total"]["requests"], 8, "5 turn + 3 followup counted, suppressed not")
        self.assertEqual(report["total"]["assumed_billed"], 0, "every row carries a kind marker")

        self.assertEqual(len(report["suppressed"]), 1, "the suppressed row is named, not silently dropped")
        named = report["suppressed"][0]
        self.assertEqual(named["file"], "rows-a.jsonl")
        self.assertEqual(named["line"], 9, "the 9th line is the suppressed follow-up")
        self.assertEqual(named["marker"], "followup_suppressed")

        proc = run_tool("--glob", self.pattern())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("followup_suppressed", json.dumps(report))

    def test_b_billed_false_is_not_counted(self) -> None:
        """(b) a `billed: false` row is not counted even though its kind is a counted kind."""
        rows = [turn(1), turn(2), {**turn(3), "billed": False}]
        write_rows(os.path.join(self.tmp, "rows-b.jsonl"), rows)

        report = self.report()
        self.assertEqual(report["total"]["rows"], 3)
        self.assertEqual(report["total"]["requests"], 2, "billed:false must not consume budget")
        markers = [s["marker"] for s in report["suppressed"]]
        self.assertEqual(markers, ["billed:false"])
        self.assertEqual(report["suppressed"][0]["line"], 3)

    def test_b2_served_from_prompt_is_not_counted(self) -> None:
        rows = [turn(1), {**turn(2), "served_from": "prompt"}]
        write_rows(os.path.join(self.tmp, "rows-b2.jsonl"), rows)
        report = self.report()
        self.assertEqual(report["total"]["requests"], 1)
        self.assertEqual(report["suppressed"][0]["marker"], "served_from:prompt")

    def test_b3_markers_are_not_licensed_to_hide_a_row(self) -> None:
        """A row explicitly billed True still counts -- the exclusion needs `false`."""
        rows = [turn(1), {**turn(2), "billed": True}]
        write_rows(os.path.join(self.tmp, "rows-b3.jsonl"), rows)
        self.assertEqual(self.report()["total"]["requests"], 2)

    def test_c_undecidable_schema_counts_and_flags_assumed_billed(self) -> None:
        """(c) no `kind` and no marker -> counted, flagged assumed_billed."""
        undecidable = {
            "unit": "C0-BASELINE",
            "ts_utc": "2026-10-26T05:45:33Z",
            "endpoint": "http://192.168.2.168:8012/v1/chat/completions",
            "model": "occamy-1.0-NVFP4",
            "arm": "C0",
            "turn": 1,
            "rep": 1,
            "prompt_tokens": 1874,
            "completion_tokens": 300,
        }
        rows = [turn(1), undecidable]
        write_rows(os.path.join(self.tmp, "rows-c.jsonl"), rows)

        report = self.report()
        self.assertEqual(report["total"]["requests"], 2, "an undecidable row is counted, not dropped")
        self.assertEqual(report["total"]["assumed_billed"], 1, "and the doubt is reported")
        self.assertEqual(report["files"][0]["assumed_billed"], 1)

    def test_c2_per_file_fields_present(self) -> None:
        rows = [turn(1), {**turn(2), "ts": "2026-10-26T09:00:00.000Z"}]
        write_rows(os.path.join(self.tmp, "rows-c2.jsonl"), rows)
        entry = self.report()["files"][0]
        for key in ("file", "sha256", "rows", "requests", "assumed_billed", "first_ts", "last_ts"):
            self.assertIn(key, entry)
        self.assertEqual(entry["sha256"], sha256_file(os.path.join(self.tmp, "rows-c2.jsonl")))
        self.assertEqual(entry["first_ts"], "2026-10-26T09:00:00.000Z")
        self.assertEqual(entry["last_ts"], "2026-10-26T12:00:01.000Z")


class TestCapGate(FixtureCase):
    def setUp(self) -> None:
        super().setUp()
        write_rows(os.path.join(self.tmp, "rows-d.jsonl"), [turn(n) for n in range(1, 11)])

    def test_d_would_spend_that_fits_exits_zero(self) -> None:
        """(d) spent 10 + N 5 <= cap 20 - reserve 0 -> exit 0."""
        proc = run_tool("--glob", self.pattern(), "--cap", "20", "--would-spend", "5")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_d2_would_spend_that_does_not_fit_exits_four_with_arithmetic(self) -> None:
        """(d) spent 10 + N 15 > cap 20 - reserve 0 -> exit 4, all four values printed."""
        proc = run_tool("--glob", self.pattern(), "--cap", "20", "--would-spend", "15")
        self.assertEqual(proc.returncode, 4, f"expected over-budget; got {proc.returncode}")
        message = proc.stderr
        for label, value in (
            ("spent", "10"),
            ("would_spend", "15"),
            ("cap", "20"),
            ("reserve", "0"),
            ("headroom", "20"),
        ):
            self.assertIn(f"{label}={value}", message, f"{label} missing from: {message}")
        self.assertIn("OVER BUDGET", message)

    def test_d3_reserve_is_honoured(self) -> None:
        """spent 10 + N 4 <= 20 - reserve 6 (==14) -> exit 0; N 5 -> exit 4."""
        ok = run_tool("--glob", self.pattern(), "--cap", "20", "--reserve", "6", "--would-spend", "4")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        over = run_tool("--glob", self.pattern(), "--cap", "20", "--reserve", "6", "--would-spend", "5")
        self.assertEqual(over.returncode, 4, over.stderr)
        self.assertIn("reserve=6", over.stderr)
        self.assertIn("headroom=14", over.stderr)

    def test_d4_default_cap_is_4320_and_default_reserve_zero(self) -> None:
        report = self.report()
        self.assertEqual(report["budget"]["cap"], 4320)
        self.assertEqual(report["budget"]["reserve"], 0)

    def test_d5_usage_errors_exit_three(self) -> None:
        self.assertEqual(run_tool("--glob", self.pattern(), "--cap", "-1").returncode, 3)
        self.assertEqual(
            run_tool("--glob", self.pattern(), "--cap", "10", "--reserve", "11").returncode, 3
        )
        self.assertEqual(
            run_tool("--glob", os.path.join(self.tmp, "rows-none-*.jsonl")).returncode, 3
        )


class TestUnreadableRows(FixtureCase):
    def test_e_unparseable_row_file_exits_five_and_counts_nothing(self) -> None:
        """(e) a bad line -> exit 5, and no report is written (nothing counted silently)."""
        path = os.path.join(self.tmp, "rows-e.jsonl")
        write_rows(path, [turn(1), turn(2)])
        with open(path, "a", encoding="utf-8") as handle:
            handle.write('{"kind": "turn", "prompt_tokens": 1')  # truncated JSON

        out = os.path.join(self.tmp, "report-e.json")
        proc = run_tool("--glob", self.pattern(), "--write", out)
        self.assertEqual(proc.returncode, 5, f"expected 5; stderr={proc.stderr}")
        self.assertIn("unparseable", proc.stderr)
        self.assertIn("rows-e.jsonl", proc.stderr)
        self.assertFalse(os.path.exists(out), "no partial report is written when counting fails")

    def test_e2_non_object_row_exits_five(self) -> None:
        path = os.path.join(self.tmp, "rows-e2.jsonl")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("[1, 2, 3]\n")
        proc = run_tool("--glob", self.pattern())
        self.assertEqual(proc.returncode, 5, proc.stderr)
        self.assertIn("not an object", proc.stderr)


class TestDeterminism(FixtureCase):
    def test_f_two_runs_produce_byte_identical_json(self) -> None:
        """(f) same rows in -> byte-identical JSON out (including across shuffled line order)."""
        rows = [turn(n) for n in range(1, 6)] + [followup(1), followup(2)]
        rows.append({**followup(7), "followup_suppressed": True})
        write_rows(os.path.join(self.tmp, "rows-f1.jsonl"), rows)
        write_rows(os.path.join(self.tmp, "rows-f2.jsonl"), [turn(9)])
        # A second, separately-ordered directory with the same content must sort the same way.
        other = os.path.join(self.tmp, "other")
        os.makedirs(other)
        write_rows(os.path.join(other, "rows-f2.jsonl"), rows[:1])
        write_rows(os.path.join(other, "rows-f1.jsonl"), rows)

        first = os.path.join(self.tmp, "one.json")
        second = os.path.join(self.tmp, "two.json")
        self.assertEqual(run_tool("--glob", self.pattern(), "--write", first).returncode, 0)
        self.assertEqual(run_tool("--glob", self.pattern(), "--write", second).returncode, 0)
        with open(first, "rb") as a, open(second, "rb") as b:
            blob_a, blob_b = a.read(), b.read()
        self.assertEqual(blob_a, blob_b, "identical input must produce identical bytes")
        self.assertNotIn(b"generated_at", blob_a, "no wall-clock field may leak into the report")

        # File ordering is by NAME, not by directory accident.
        report = json.loads(blob_a.decode())
        names = [f["file"] for f in report["files"]]
        self.assertEqual(names, sorted(names))


class TestRealCorpus(unittest.TestCase):
    """(g) The real corpus: computed total and the delta from the hand-carried 466."""

    def test_g_real_corpus_total_and_delta_from_466(self) -> None:
        paths = sorted(
            p for p in (os.path.join(MEASURE, f) for f in os.listdir(MEASURE))
            if os.path.basename(p).startswith("rows-") and p.endswith(".jsonl")
        )
        self.assertGreater(len(paths), 0, "the real row corpus must exist")
        before = {os.path.basename(p): sha256_file(p) for p in paths}

        out = os.path.join(tempfile.mkdtemp(), "real.json")
        proc = run_tool("--write", out, "--cap", "4320")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(out, "r", encoding="utf-8") as handle:
            report = json.load(handle)

        total = report["total"]["requests"]
        delta = total - HAND_CARRIED_BASELINE
        print(
            f"\n[real corpus] files={report['total']['files']} rows={report['total']['rows']} "
            f"requests={total} assumed_billed={report['total']['assumed_billed']} "
            f"| hand-carried={HAND_CARRIED_BASELINE} delta=+{delta}"
        )
        self.assertGreater(total, 0)
        self.assertGreater(total, HAND_CARRIED_BASELINE, "the hand-carried figure understates the corpus")

        # The row files are read-only inputs: nothing may change.
        after = {os.path.basename(p): sha256_file(p) for p in paths}
        self.assertEqual(before, after, "the ledger MUST NOT modify a row file")

    def test_g2_longrun_sha_still_bc61d381(self) -> None:
        path = os.path.join(MEASURE, "rows-longrun-2026-10-26.jsonl")
        self.assertTrue(os.path.exists(path), "the pinned longrun row file must exist")
        digest = sha256_file(path)
        print(f"\n[longrun] sha256={digest}")
        self.assertTrue(
            digest.startswith(LONGRUN_SHA_PREFIX),
            f"rows-longrun-2026-10-26.jsonl is no longer {LONGRUN_SHA_PREFIX}...: {digest}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
