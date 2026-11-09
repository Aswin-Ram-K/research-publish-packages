#!/usr/bin/env python3
"""Red->green tests for the DUPLICATE RULE in experiments/ptr-engine/tools/request_ledger.py.

Offline. Zero inference requests. No network. No git. Fixtures are built in a tmp dir; the
real row corpus is only ever READ.

Cases, per the REQUEST-LEDGER-2 unit contract:
  (1) a synthetic file with 3 duplicate groups of 2 -> duplicate_excess == 3,
      requests_deduplicated == rows - 3, rule_status == "decided"
  (2) a LEGACY-SCHEMA file whose rows collide on ts_utc but differ in latency_s -> NOT
      deduped, rule_status == "not_applicable" (the schema cannot decide, so no rule is
      applied and the collisions are reported, not subtracted)
  (3) --would-spend just inside / just outside the cap -> exit 0 / 4, and the exit-4
      arithmetic uses the RAW figure and says the de-duplicated one is NOT deducted
      (LEDGER-CONSERVATIVE reversal, 2026-10-26: the rule is unsound as a request-identity
      test, so its excess may not be spent against)
  (4) an unreadable row file -> exit 5 and nothing counted (no report written)
  (5) red->green: the dedupe CALL is load-bearing -- a mutant copy with the call disabled
      yields the raw count, so case (1) fails against it. The mutant is built in tmp;
      the real tool is untouched.
  (6) the real corpus: raw 1101 -> deduplicated 1071, excess 30, 3 files not_applicable,
      and every row file byte-identical before/after.

Run:
  python3 -m unittest discover -s experiments/ptr-engine/tests -p 'test_request_ledger_dedup.py' -v
Override the implementation under test:
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
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TOOL = os.environ.get(
    "REQUEST_LEDGER_TOOL",
    os.path.join(REPO, "experiments", "ptr-engine", "tools", "request_ledger.py"),
)
MEASURE = os.path.join(REPO, "experiments", "ptr-engine", "measure")


def write_rows(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def modern(kind: str, n: int, content: str, prompt: int = 100, completion: int = 10) -> dict:
    """A row from the decidable schema: content_sha256 + millisecond ts."""
    return {
        "kind": kind,
        "arm": "fixture",
        "task_id": "T-1",
        "rep": 1,
        "turn": n,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "content": content,
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "ts": f"2026-10-26T12:00:{n:02d}.529Z",
        "ttft_s": 0.19,
        "latency_s": 8.05,
    }


def legacy(n: int, *, latency_s: float) -> dict:
    """A row from the legacy schema: second-resolution ts_utc, no content_sha256."""
    return {
        "unit": "C0-BASELINE",
        "ts_utc": "2026-10-26T05:45:33Z",
        "arm": "C0",
        "turn": n,
        "rep": 1,
        "prompt_tokens": 1874,
        "completion_tokens": 300,
        "latency_s": latency_s,
    }


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_tool(*args: str, tool: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, tool or TOOL, *args],
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

    def report(self, *args: str, tool: str | None = None) -> dict:
        out = os.path.join(self.tmp, "report.json")
        proc = run_tool("--glob", self.pattern(), "--write", out, *args, tool=tool)
        self.assertIn(proc.returncode, (0, 4), proc.stderr)
        with open(out, "r", encoding="utf-8") as handle:
            return json.load(handle)


class TestDuplicateRule(FixtureCase):
    def three_groups(self) -> list[dict]:
        """3 duplicate groups of 2 (a turn/follow-up mirror per group), plus 2 singletons."""
        rows = []
        for n in (1, 2, 3):
            content = f"answer-{n}"
            # Identical tuple: same ts, same content, same token counts -> one request, two rows.
            rows.append(modern("turn", n, content, prompt=100 + n, completion=10))
            rows.append(modern("tool-followup", n, content, prompt=100 + n, completion=10))
        rows.append(modern("turn", 4, "answer-4", prompt=200, completion=11))
        rows.append(modern("turn", 5, "answer-5", prompt=201, completion=12))
        return rows

    def test_1_three_duplicate_groups_excess_three(self) -> None:
        """(1) 3 groups of 2 -> excess 3, dedup == rows - 3."""
        write_rows(os.path.join(self.tmp, "rows-one.jsonl"), self.three_groups())
        report = self.report()

        entry = report["per_file"][0]
        self.assertEqual(entry["rows"], 8, "8 rows were read")
        self.assertEqual(entry["requests"], 8, "raw count keeps every row")
        self.assertEqual(entry["duplicate_groups"], 3, "3 duplicate groups")
        self.assertEqual(entry["duplicate_excess"], 3, "one excess row per group")
        self.assertEqual(entry["requests_deduplicated"], 8 - 3, "dedup == rows - 3")
        self.assertEqual(entry["rule_status"], "decided", "the schema can decide the rule")

        self.assertEqual(report["requests_raw"], 8)
        self.assertEqual(report["requests_deduplicated"], 5)
        self.assertEqual(report["requests"], 8, "headline is the RAW figure (reversal 2026-10-26)")
        self.assertEqual(report["diagnostic"]["requests_deduplicated"], 5,
                         "the de-duplicated figure is kept as a diagnostic, not deducted")
        self.assertFalse(report["diagnostic"]["deducted"])
        self.assertEqual(report["duplicate_excess"], 3)
        self.assertEqual(report["files_deduped"], 1)
        self.assertEqual(report["files_not_applicable"], 0)
        self.assertIn("content_sha256", report["dedup_rule"])
        self.assertIn("first occurrence kept", report["dedup_rule"])

    def test_2_legacy_schema_is_not_applicable_and_not_deduped(self) -> None:
        """(2) rows collide on ts_utc but differ in latency_s -> not deduped, not_applicable."""
        rows = [
            legacy(1, latency_s=2.5),
            legacy(1, latency_s=9.5),      # same ts_utc + tokens, DIFFERENT request
            legacy(2, latency_s=3.0),
            legacy(2, latency_s=3.0),      # even identical here: still undecidable
        ]
        write_rows(os.path.join(self.tmp, "rows-legacy.jsonl"), rows)
        report = self.report()

        entry = report["per_file"][0]
        self.assertEqual(entry["rule_status"], "not_applicable")
        self.assertIn("no content_sha256", entry["rule_reason"])
        self.assertEqual(entry["duplicate_excess"], 0, "an undecidable schema subtracts nothing")
        self.assertEqual(entry["requests_deduplicated"], entry["requests"], "nothing deduped")
        self.assertEqual(report["requests_raw"], 4)
        self.assertEqual(report["requests_deduplicated"], 4, "legacy file must NOT be deduped")
        self.assertEqual(report["files_not_applicable"], 1)
        self.assertEqual(report["files_deduped"], 0)

        # The collisions are reported, not silently dropped: visibility without subtraction.
        # All four rows collide on the tuple here (second-resolution ts_utc + same token
        # counts), even though rep/turn/latency_s differ -- which is precisely why the rule
        # must not be applied: 3 "duplicates" it would merge are 3 distinct requests.
        collisions = entry["collisions_not_applied"]
        self.assertIsNotNone(collisions, "the would-be merges on an undecidable schema are reported")
        self.assertEqual(collisions["excess"], 3)
        self.assertIn("distinct requests", collisions["note"])

    def test_2b_mixed_directory_counts_both_rule_statuses(self) -> None:
        """A decided file and a legacy file in one corpus: the rule applies per file."""
        write_rows(os.path.join(self.tmp, "rows-a.jsonl"), self.three_groups())
        write_rows(os.path.join(self.tmp, "rows-b.jsonl"), [legacy(1, latency_s=2.5), legacy(1, latency_s=9.5)])
        report = self.report()
        statuses = {f["file"]: f["rule_status"] for f in report["per_file"]}
        self.assertEqual(statuses, {"rows-a.jsonl": "decided", "rows-b.jsonl": "not_applicable"})
        self.assertEqual(report["requests_raw"], 10)
        self.assertEqual(report["requests_deduplicated"], 7)
        self.assertEqual((report["files_deduped"], report["files_not_applicable"]), (1, 1))


class TestCapGateUsesRaw(FixtureCase):
    """The gate's `spent` is the RAW count (LEDGER-CONSERVATIVE reversal, 2026-10-26).

    These cases used to assert `spent` was the de-duplicated 5. That publication was
    withdrawn -- the tuple cannot decide request identity, so a deduction understates spend
    -- and the gate now takes the conservative figure. The rule itself still runs: the
    de-duplicated number is asserted here as a diagnostic, never as the input.
    """

    def test_3_would_spend_boundary_exits_zero_then_four(self) -> None:
        """(3) spent(raw)=8; cap 10 -> +2 fits (0), +3 does not (4), arithmetic printed."""
        write_rows(os.path.join(self.tmp, "rows-cap.jsonl"), TestDuplicateRule.three_groups(self))
        # raw 8, dedup 5 (diagnostic). cap 10: 8+2 == 10 -> within; 8+3 == 11 -> over.
        inside = run_tool("--glob", self.pattern(), "--cap", "10", "--would-spend", "2")
        self.assertEqual(inside.returncode, 0, inside.stderr)
        self.assertIn("within budget: 10 <= 10", inside.stdout)
        self.assertIn("NOT deducted", inside.stdout)
        self.assertIn("de-duplicated diagnostic 5", inside.stdout)

        outside = run_tool("--glob", self.pattern(), "--cap", "10", "--would-spend", "3")
        self.assertEqual(outside.returncode, 4, f"expected over-budget; got {outside.returncode}")
        message = outside.stderr
        for label, value in (
            ("spent", "8"),          # the RAW spend, not the de-duplicated 5
            ("would_spend", "3"),
            ("cap", "10"),
            ("reserve", "0"),
            ("headroom", "10"),
        ):
            self.assertIn(f"{label}={value}", message, f"{label} missing from: {message}")
        self.assertIn("OVER BUDGET", message)
        self.assertIn("spent is the RAW count", message, "the message must say which figure it used")
        self.assertIn("NOT deducted", message, "the withdrawn figure must be named as withheld")
        self.assertIn("5", message, "the de-duplicated diagnostic figure is still printed")

    def test_3b_reserve_boundary_uses_raw(self) -> None:
        write_rows(os.path.join(self.tmp, "rows-cap2.jsonl"), TestDuplicateRule.three_groups(self))
        # raw 8, headroom 20-4 = 16 -> +8 fits, +9 does not.
        self.assertEqual(
            run_tool("--glob", self.pattern(), "--cap", "20", "--reserve", "4", "--would-spend", "8").returncode,
            0,
        )
        over = run_tool("--glob", self.pattern(), "--cap", "20", "--reserve", "4", "--would-spend", "9")
        self.assertEqual(over.returncode, 4, over.stderr)
        self.assertIn("headroom=16", over.stderr)


class TestUnreadableRows(FixtureCase):
    def test_4_unreadable_row_file_exits_five_and_counts_nothing(self) -> None:
        """(4) a truncated row -> exit 5, no report written (nothing counted)."""
        path = os.path.join(self.tmp, "rows-bad.jsonl")
        write_rows(path, [modern("turn", 1, "a"), modern("turn", 2, "b")])
        with open(path, "a", encoding="utf-8") as handle:
            handle.write('{"kind": "turn", "ts": "2026-10-26T12:00:01.000Z"')  # truncated

        out = os.path.join(self.tmp, "report-bad.json")
        proc = run_tool("--glob", self.pattern(), "--write", out)
        self.assertEqual(proc.returncode, 5, f"expected 5; stderr={proc.stderr}")
        self.assertIn("unparseable", proc.stderr)
        self.assertIn("nothing counted", proc.stderr)
        self.assertFalse(os.path.exists(out), "no partial report when counting fails")


class TestRedGreen(FixtureCase):
    def test_5_disabling_the_dedupe_call_makes_case_1_fail(self) -> None:
        """(5) the dedupe call is load-bearing: mutate it off and the dedup count regresses."""
        with open(TOOL, "r", encoding="utf-8") as handle:
            source = handle.read()
        needle = "    dedupe_applied = True\n"
        self.assertIn(needle, source, "the dedupe call must be a single identifiable line")
        mutant = os.path.join(self.tmp, "mutant_ledger.py")
        with open(mutant, "w", encoding="utf-8") as handle:
            handle.write(source.replace(needle, "    dedupe_applied = False\n"))

        write_rows(os.path.join(self.tmp, "rows-one.jsonl"), TestDuplicateRule.three_groups(self))

        green = self.report()
        self.assertEqual(green["requests_deduplicated"], 5, "the real tool applies the rule")

        red = self.report(tool=mutant)
        self.assertEqual(red["requests_deduplicated"], 8, "with the call disabled the dedupe is gone")
        self.assertNotEqual(
            red["requests_deduplicated"],
            green["requests_deduplicated"],
            "case (1)'s assertion 5 == rows - 3 must fail on the mutant",
        )


class TestRealCorpus(unittest.TestCase):
    def test_6_real_corpus_raw_1101_deduplicated_1071(self) -> None:
        paths = sorted(
            p for p in (os.path.join(MEASURE, f) for f in os.listdir(MEASURE))
            if os.path.basename(p).startswith("rows-") and p.endswith(".jsonl")
        )
        before = {os.path.basename(p): sha256_file(p) for p in paths}

        out = os.path.join(tempfile.mkdtemp(), "real.json")
        proc = run_tool("--write", out, "--cap", "4320")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(out, "r", encoding="utf-8") as handle:
            report = json.load(handle)

        print(
            f"\n[real corpus] raw={report['requests_raw']} deduplicated={report['requests_deduplicated']} "
            f"excess={report['duplicate_excess']} remaining_raw={report['remaining_raw']} "
            f"remaining={report['remaining']} decided={report['files_deduped']} "
            f"na={report['files_not_applicable']}"
        )
        # +48 (unit LEDGER-AFTER-CANARY): four live cells appended 12 rows each after the
        # 2026-10-26T18:56:31Z snapshot -- the three canary arms LIVE-CANARY-4ARM-3 ran
        # (rows-cell-pointer-stable-20261026T202040Z, rows-cell-transcript-grow-20261026T202444Z,
        # rows-cell-transcript-compact-20261026T203733Z) plus one live pointer-stable cell written
        # 2m58s AFTER that canary recorded its own spend
        # (rows-cell-pointer-stable-20261026T204258Z, manifest longrun-...-204258Z-pointer-stable-r1).
        # So 1128 -> 1176 requests_raw, 3192 -> 3144 remaining, 1098 -> 1146
        # requests_deduplicated (none of the 48 rows holds a duplicate, so duplicate_excess stays
        # 30), and decidable files 12 -> 16. The earlier +27 note (LEDGER-REBUILD-27) is preserved
        # in history; the test name still says 1101/1071 because docs/FETCH-BUDGET-48.md cites it.
        self.assertEqual(report["requests_raw"], 1176)
        self.assertEqual(report["requests_deduplicated"], 1146)
        self.assertEqual(report["requests"], 1176, "published spend is the RAW count")
        self.assertEqual(report["duplicate_excess"], 30)
        self.assertEqual(report["remaining_raw"], 3144)
        self.assertEqual(report["remaining"], 3144, "remaining is the raw remainder")
        self.assertEqual(report["remaining_deduplicated"], 3174, "withdrawn figure stays visible")
        self.assertEqual(report["files_deduped"], 16)
        self.assertEqual(report["files_not_applicable"], 3)
        self.assertEqual(report["budget"]["spent"], 1176, "the gate's operand is the raw count")
        self.assertEqual(report["budget"]["spent_raw"], 1176)
        self.assertEqual(report["budget"]["spent_deduplicated"], 1146,
                         "diagnostic only: never the gate's operand")

        na = sorted(f["file"] for f in report["per_file"] if f["rule_status"] == "not_applicable")
        self.assertEqual(
            na,
            ["rows-baseline-2026-10-26.jsonl", "rows-equalinfo-2026-10-26.jsonl", "rows-live-2026-10-26.jsonl"],
        )
        for name in na:
            entry = next(f for f in report["per_file"] if f["file"] == name)
            self.assertIn("no content_sha256", entry["rule_reason"])

        # Every marker reconned in the report; the three the rule named are dead code.
        recon = {m["marker"]: m for m in report["marker_reconciliation"]}
        self.assertEqual(
            set(recon),
            {"billed", "followup_suppressed", "served_from",
             "billed_round", "fetch_followup", "prompt_served"},
        )
        for dead in ("billed", "followup_suppressed", "served_from"):
            self.assertEqual(recon[dead]["corpus_occurrences"], 0, dead)
            self.assertFalse(recon[dead]["can_change_count"], f"{dead} cannot change the count")
        self.assertEqual(recon["billed_round"]["corpus_values"], {"true": 20, "false": 4})
        self.assertEqual(recon["fetch_followup"]["corpus_values"], {"true": 68})
        self.assertFalse(recon["fetch_followup"]["can_change_count"])
        self.assertFalse(recon["billed_round"]["can_change_count"])
        self.assertFalse(recon["prompt_served"]["can_change_count"])

        after = {os.path.basename(p): sha256_file(p) for p in paths}
        self.assertEqual(before, after, "the ledger MUST NOT modify a row file")


if __name__ == "__main__":
    unittest.main(verbosity=2)
