"""test_request_ledger_sound.py -- the published spend may not be quietly de-duplicated.

LEDGER-CONSERVATIVE (2026-10-26). `V-DUPLICATE-RULE` graded `overall: fail`: the duplicate
rule's tuple cannot decide request identity, because `content_sha256` is
sha256(assistant `content`) -- a RESPONSE hash (`run_longrun.py:1555`; 869/869 rows that
carry it satisfy `content_sha256 == sha256(content)`). Two different requests that returned
the same text collapse into one row, so subtracting the excess UNDERSTATES spend. The
previous publication (1,071 requests / 3,249 remaining) was therefore withdrawn and the raw
figure republished (1,101 / 3,219).

These tests are the guard that keeps the flip from happening silently:

  A. `requests` is the RAW count, and `remaining` is the raw remainder.
  B. the de-duplicated figure is still published -- under `diagnostic`, `deducted: false`,
     with its reason -- so the reversal is auditable rather than concealed.
  C. `requests == requests_raw` unless a deduction is authorised, and authorising one takes
     BOTH a `deduction_rule_sound` flag AND evidence naming a request-identity hash. A flag
     on its own raises: no one may flip the number by editing a boolean.
  D. the published artefact on disk says exactly what this pass claims.

Offline: no network, no inference, no live request. Reads row files and the report only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)
TOOL = os.path.join(ENGINE, "tools", "request_ledger.py")
MEASURE = os.path.join(ENGINE, "measure")
ARTEFACT = os.path.join(MEASURE, "REQUEST-LEDGER.json")

ENGINE_TOOLS = os.path.join(ENGINE, "tools")
if ENGINE_TOOLS not in sys.path:
    sys.path.insert(0, ENGINE_TOOLS)

import request_ledger  # noqa: E402


def modern(kind: str, n: int, content: str, prompt: int = 100, completion: int = 10) -> dict:
    """A counted row on the decidable schema: millisecond ts + content_sha256."""
    return {
        "kind": kind,
        "ts": "2026-10-26T10:00:%02d.%03dZ" % (n % 60, n),
        "content_sha256": content,
        "content": content,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
    }


def three_groups() -> list[dict]:
    """8 counted rows, 3 duplicate groups of 2 (raw 8, de-duplicated 5)."""
    rows: list[dict] = []
    for n in (1, 2, 3):
        content = "answer-%d" % n
        rows.append(modern("turn", n, content, prompt=100 + n, completion=10))
        rows.append(modern("tool-followup", n, content, prompt=100 + n, completion=10))
    rows.append(modern("turn", 4, "answer-4", prompt=200, completion=11))
    rows.append(modern("turn", 5, "answer-5", prompt=201, completion=12))
    return rows


def write_rows(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def real_row_paths() -> list[str]:
    return sorted(
        p for p in (os.path.join(MEASURE, f) for f in os.listdir(MEASURE))
        if os.path.basename(p).startswith("rows-") and p.endswith(".jsonl")
    )


class FixtureCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="ledger-sound-")
        self.path = os.path.join(self.tmp, "rows-fixture.jsonl")

    def report(self, cap: int = 4320, would_spend: int = 0, **kwargs):
        return request_ledger.build_report([self.path], cap, 0, would_spend, **kwargs)


class TestPublishedIsRaw(FixtureCase):
    def test_1_headline_is_raw_and_dedup_is_diagnostic(self) -> None:
        """A: requests == requests_raw; the de-duplicated figure is NOT the headline."""
        write_rows(self.path, three_groups())
        report = self.report()

        self.assertEqual(report["requests_raw"], 8, "every counted row is a request")
        self.assertEqual(report["requests_deduplicated"], 5, "the rule still runs and reports")
        self.assertEqual(report["requests"], 8, "headline is the RAW figure, not the deduction")
        self.assertEqual(report["duplicate_excess"], 3)
        self.assertEqual(report["remaining"], 4320 - 8, "remaining is the raw remainder")
        self.assertEqual(report["remaining_deduplicated"], 4320 - 5, "published, not deducted")
        self.assertFalse(report["deduction_rule_sound"], "no rule is sound today")
        self.assertFalse(report["deduction"]["applied"], "nothing was deducted")
        self.assertEqual(report["deduction"]["deducted_requests"], 0)
        self.assertEqual(report["deduction"]["candidate_excess"], 3, "the candidate stays visible")

    def test_2_diagnostic_keeps_the_withdrawn_figure(self) -> None:
        """B: reversal, not deletion -- 1,071 sits in the artefact with its reason."""
        write_rows(self.path, three_groups())
        report = self.report()

        diag = report["diagnostic"]
        self.assertFalse(diag["deducted"], "the diagnostic figure is explicitly not deducted")
        self.assertEqual(diag["requests_deduplicated"], 5)
        self.assertEqual(diag["duplicate_excess"], 3)
        self.assertEqual(diag["per_file_excess"], {"rows-fixture.jsonl": 3})
        self.assertEqual(len(diag["rows"]), 3, "each excess row is named, not just counted")
        for row in diag["rows"]:
            self.assertIs(row["deducted"], False)
            self.assertEqual(row["reason"], request_ledger.DEDUCTION_REASON)
            self.assertIn("duplicate_of_line", row, "a reader can find the row it mirrors")
        self.assertIn("content_sha256 hashes assistant content", diag["reason"])
        self.assertIn("V-DUPLICATE-RULE", diag["reason"])

    def test_3_no_rectangles_for_a_legacy_file(self) -> None:
        """An undecidable schema still subtracts nothing and does not claim to."""
        rows = [{"kind": "turn", "ts_utc": "2026-10-26T10:00:00Z",
                 "prompt_tokens": 10, "completion_tokens": 2} for _ in range(3)]
        write_rows(self.path, rows)
        report = self.report()
        self.assertEqual(report["requests"], 3)
        self.assertEqual(report["requests_deduplicated"], 3)
        self.assertEqual(report["duplicate_excess"], 0)
        self.assertEqual(report["diagnostic"]["rows"], [])


class TestDeductionNeedsEvidence(FixtureCase):
    def test_4_flag_alone_raises(self) -> None:
        """C (red): flipping the flag without an evidence path FAILS, it does not deduct."""
        write_rows(self.path, three_groups())
        with self.assertRaises(ValueError) as caught:
            self.report(deduction_rule_sound=True)
        self.assertIn("sound_rule_evidence", str(caught.exception))

    def test_5_flag_with_evidence_missing_the_hash_raises(self) -> None:
        """C (red): a dict that does not name a request-identity hash is not evidence."""
        write_rows(self.path, three_groups())
        for bogus in ({}, {"note": "we think it is fine"}, {"request_identity_hash": "   "}):
            with self.assertRaises(ValueError, msg="accepted bogus evidence: %r" % (bogus,)):
                self.report(deduction_rule_sound=True, sound_rule_evidence=bogus)

    def test_6_flag_with_a_real_hash_deducts(self) -> None:
        """C (green): a sound rule WITH evidence is the only path to the smaller number."""
        write_rows(self.path, three_groups())
        report = self.report(
            deduction_rule_sound=True,
            sound_rule_evidence={"request_identity_hash": "sha256(canonical request bytes)"},
        )
        self.assertTrue(report["deduction"]["applied"])
        self.assertTrue(report["deduction_rule_sound"])
        self.assertEqual(report["requests"], 5, "with a sound rule the deduction is published")
        self.assertEqual(report["requests_raw"], 8, "the raw count is never lost")
        self.assertEqual(report["deduction"]["deducted_requests"], 3)
        self.assertEqual(report["diagnostic"]["per_file_deducted"],
                         {"rows-fixture.jsonl": 3}, "the sound rule deducts the whole excess")
        for row in report["diagnostic"]["rows"]:
            self.assertIs(row["deducted"], True)

    def test_7_module_default_is_unsound(self) -> None:
        """The flag ships OFF, and the default path refuses to deduct."""
        self.assertIs(request_ledger.DEDUCTION_RULE_SOUND, False)
        permitted, reason = request_ledger.deduction_permitted()
        self.assertFalse(permitted)
        self.assertEqual(reason, request_ledger.DEDUCTION_REASON)

    def test_8_no_cli_switch_can_flip_the_flag(self) -> None:
        """A flip must be a code change with evidence, not a flag on the command line."""
        proc = subprocess.run(
            [sys.executable, TOOL, "--help"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for forbidden in ("deduction-rule-sound", "deduction_rule_sound", "sound-rule-evidence"):
            self.assertNotIn(forbidden, proc.stdout,
                             "a CLI switch would make the flip silent")


class TestRedGreenMutation(FixtureCase):
    def test_9_flipping_the_module_constant_makes_the_guard_fire(self) -> None:
        """Red -> green on the guard itself.

        Green today: the default path publishes the raw count. Red: set the module constant
        (the natural "just flip it" edit) and the same call RAISES instead of quietly
        deducting, because the evidence path is still absent.
        """
        write_rows(self.path, three_groups())

        green = self.report()
        self.assertEqual(green["requests"], green["requests_raw"],
                         "GUARD GREEN: requests == requests_raw with no sound rule")

        original = request_ledger.DEDUCTION_RULE_SOUND
        request_ledger.DEDUCTION_RULE_SOUND = True
        try:
            with self.assertRaises(ValueError):
                self.report()
        finally:
            request_ledger.DEDUCTION_RULE_SOUND = original

        after = self.report()
        self.assertEqual(after["requests"], after["requests_raw"],
                         "restoring the flag restores the raw headline")


class TestPublishedArtefact(unittest.TestCase):
    def test_10_artefact_publishes_raw_1101_and_keeps_1071(self) -> None:
        """D: the report of record says 1,176 / 3,144 and keeps 1,146 as diagnostic."""
        # +27: the report of record was rebuilt by LEDGER-REBUILD-27 after the cell that stopped
        # rows-cell-pointer-stable-20261026T182535Z.jsonl (27 rows written before exit 6, sha256
        # 46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1) landed on disk.
        # Every figure below moved by that one cell: 1,101 -> 1,128 spent, 3,219 -> 3,192
        # remaining, 1,071 -> 1,098 de-duplicated (still diagnostic, still never deducted).
        # +48 (LEDGER-AFTER-CANARY): four live cells of 12 rows each landed after that snapshot --
        # the three LIVE-CANARY-4ARM-3 arms plus one live pointer-stable cell written 2m58s after
        # the canary recorded its spend (manifest longrun-2026-10-26T204258Z-pointer-stable-r1).
        # 1,128 -> 1,176 spent, 3,192 -> 3,144 remaining, 1,098 -> 1,146 de-duplicated (still
        # diagnostic, still never deducted: none of the 48 rows is a duplicate pairing).
        # The name still says 1101/1071 because docs/FETCH-BUDGET-48.md cites this test by name.
        with open(ARTEFACT, "r", encoding="utf-8") as handle:
            doc = json.load(handle)

        self.assertEqual(doc["requests"], 1176, "published spend is the RAW count")
        self.assertEqual(doc["requests_raw"], 1176)
        self.assertEqual(doc["remaining"], 3144)
        self.assertEqual(doc["remaining_deduplicated"], 3174, "the withdrawn figure is still here")
        self.assertEqual(doc["requests_deduplicated"], 1146)
        self.assertEqual(doc["duplicate_excess"], 30)
        self.assertEqual(doc["budget"]["spent"], 1176, "the gate's input is the conservative one")
        self.assertEqual(doc["budget"]["projected"], 1176)
        self.assertFalse(doc["deduction"]["applied"])
        self.assertEqual(doc["deduction"]["deducted_requests"], 0)

        diag = doc["diagnostic"]
        self.assertFalse(diag["deducted"])
        # 1,098 -> 1,146: same +48, still a diagnostic that is never deducted.
        self.assertEqual(diag["requests_deduplicated"], 1146)
        self.assertEqual(diag["per_file_excess"], {
            "rows-longrun-v6-tools.jsonl": 11,
            "rows-longrun-v4-tools-2026-10-26.jsonl": 17,
            "rows-longrun-v5-tools.jsonl": 2,
        })
        self.assertEqual(len(diag["rows"]), 30)
        self.assertTrue(all(row["deducted"] is False for row in diag["rows"]))
        self.assertEqual({row["reason"] for row in diag["rows"]}, {request_ledger.DEDUCTION_REASON})
        self.assertEqual(sorted(os.path.basename(r["file"]) for r in diag["rows"]).count(
            "rows-longrun-v6-tools.jsonl"), 11)

    def test_11_artefact_matches_a_fresh_scan(self) -> None:
        """The artefact is not a hand-written number: a fresh scan reproduces it."""
        paths = real_row_paths()
        self.assertTrue(paths, "the corpus must exist for this guard to mean anything")
        fresh = request_ledger.build_report(paths, 4320, 0, 0)
        with open(ARTEFACT, "r", encoding="utf-8") as handle:
            doc = json.load(handle)

        for key in ("requests", "requests_raw", "requests_deduplicated", "duplicate_excess",
                    "remaining", "remaining_deduplicated"):
            self.assertEqual(doc[key], fresh[key], "artefact drifted from the rows: %s" % key)
        self.assertEqual(doc["requests"], doc["requests_raw"],
                         "the published figure is the raw one on the live corpus too")

    def test_12_rows_files_still_drive_the_count(self) -> None:
        """The reversal did not touch a measurement: the rule still reports its 30 groups."""
        with open(ARTEFACT, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        statuses = {f["file"]: f["rule_status"] for f in doc["per_file"]}
        # 12 -> 16 (+27 cell, then the four 12-row cells of LEDGER-AFTER-CANARY): each new file
        # carries content_sha256 + millisecond ts, so it is decidable; the excess arithmetic below
        # is unchanged because none of them holds a duplicate pair.
        self.assertEqual(sum(1 for s in statuses.values() if s == "decided"), 16)
        self.assertEqual(sum(1 for s in statuses.values() if s == "not_applicable"), 3)
        self.assertEqual(
            sum(f["duplicate_excess"] for f in doc["per_file"]), 30,
            "the rule's own arithmetic is unchanged; only its authority to subtract was revoked",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
