#!/usr/bin/env python3
"""test_capgate_label.py - a cap-gate refusal NAMES ITSELF through cell.py, and an
aborted (runaway) run reconciles before it leaves.

The defect this covers was measured by V-CAPGATE-REFUSE:
  (a) the runner's cap-gate refusal (`run_longrun.py` exit 9, "CAP GATE UNRECORDED") was
      remapped by `cell.py` to exit 5 and labelled "unmapped runner failure" -- a reader
      was sent to look for a crash that did not happen;
  (b) the four runaway returns in `run_cell` exited 6 without ever calling `_gate_finish`,
      so a runaway run's unrecorded remainder was never reconciled.

Cases:
  (a) runner 9 -> the cell's 14 (`capgate-unrecorded`), message names the cap gate and
      QUOTES the runner's delta/headroom -- exercised through `stage_run` end to end
      against a fake runner process (no endpoint, no socket, no request);
  (b) a delta < 0 at the end of an aborted run still refuses (exit 9 out of `_abort_stop`,
      not 6), and a clean delta returns the abort's own code;
  (c) the honest branches are unchanged: delta == 0 -> 0, delta > 0 -> 9 at the runner,
      pre-send refusal -> 4;
  (d) exit table / scan / docs agree, including the new code;
  (e) an induced refusal spawns NO runner (`runner_launch == 0` through `spawn_record`),
      while the same counter reports 1 for a real launch -- so the zero is measured, not
      assumed.

Offline: no request, no network, no git. Red->green per test is stated in its docstring.
"""
import importlib.util
import io
import os
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
sys.path.insert(0, LONGRUN)

import cell            # noqa: E402
import exit_codes      # noqa: E402
import run_longrun as R  # noqa: E402
import spawn_record    # noqa: E402

REPO = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
DOCS_EXIT_CODES = os.path.join(REPO, "docs", "EXIT-CODES.md")

# The runner's own words, verbatim as `_gate_finish` prints them. The delta and the
# headroom are the evidence a caller acts on, so they must survive the remap.
REFUSAL = (
    "cap-gate: allocation=4 cap=100 reserve=0 spent_at_start=96 used_in_run=3 "
    "spent_after=97 delta=-2\n"
    "CAP GATE UNRECORDED (delta=-2) — refusing, exit 9: 2 request(s) reached the wire but "
    "their rows were not written before the run stopped (used_in_run=3 rows_gained=1 "
    "headroom_before=4 headroom_after=6 rows=/tmp/rows.jsonl); rows were not persisted, "
    "so the ledger cannot be trusted for the next check — it would grant 2 request(s) "
    "beyond the true headroom.\n"
)


def fake_runner(tmpdir, rc, stderr_text=REFUSAL):
    """A stand-in for run_longrun.py: writes the given stderr, exits with `rc`.

    It ignores its argv on purpose: the cell's argv contract is not what this unit is
    testing, and a fake that parsed it would silently accept a broken argv.
    """
    path = os.path.join(tmpdir, "fake-runner-%d.py" % rc)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write("#!/usr/bin/env python3\n"
                 "import sys\n"
                 "sys.stderr.write(%r)\n"
                 "sys.exit(%d)\n" % (stderr_text, rc))
    return path


def stage_args(fixture):
    return types.SimpleNamespace(arm="pointer-stable", fixture=fixture, reps=1,
                                 turn_wall_cap=60.0, runaway_turns=2, endpoint=None,
                                 turns=0, thinking="off", hypothesis="none",
                                 temperature=0.0, budget_cap=12094,
                                 tools=None, fetch_policy=None)


class StubGate:
    """The smallest object `_gate_finish` needs: its own reconcile answer + counters."""

    def __init__(self, delta, used_in_run=3, spent_at_start=96, spent_after=97):
        self.delta = delta
        self.allocation = 4
        self.cap = 100
        self.reserve = 0
        self.spent_at_start = spent_at_start
        self.used_in_run = used_in_run
        self._spent_after = spent_after

    def reconcile(self):
        return {"delta": self.delta, "spent_at_start": self.spent_at_start,
                "spent_after": self._spent_after}

    def manifest_block(self, reconciled=None):
        return {"allocation": self.allocation, "reconciled": reconciled}


def run_with_stderr(fn, *args, **kwargs):
    """-> (result, stderr_text) -- the runner's refusal must be READABLE, not inferred."""
    buf = io.StringIO()
    with redirect_stderr(buf):
        result = fn(*args, **kwargs)
    return result, buf.getvalue()


class CellLabellingTests(unittest.TestCase):
    def test_a_runner_9_reaches_the_caller_as_the_capgate_code(self):
        """(a) RED: revert `_RUNNER_MAPPED_TO_CELL.get(rc, ...)` to the old
        `rc if rc in _RUNNER_CODES else EXIT_RUNNER_CRASH` -> the Abort code is 5 and the
        message says "unmapped runner failure". GREEN: code 14, the gate's own name and
        the runner's delta quoted. Run end to end through stage_run + a fake runner."""
        self.assertEqual(exit_codes.EXIT_CAPGATE_UNRECORDED, 14)
        self.assertEqual(cell._runner_exit_code(9), exit_codes.EXIT_CAPGATE_UNRECORDED)
        # the runner's own codes are untouched by the remap
        for rc in (2, 3, 4, 5, 6, 7):
            self.assertEqual(cell._runner_exit_code(rc), rc)
        self.assertEqual(cell._runner_exit_code(42), exit_codes.EXIT_RUNNER_CRASH)

        with tempfile.TemporaryDirectory(prefix="capgate-label-") as tmp:
            runner = fake_runner(tmp, 9)
            rows = os.path.join(tmp, "rows.jsonl")
            saved = (cell.RUNNER, cell.SPAWNS, cell.thinking_for_runner,
                     cell._resolved_claim)
            cell.RUNNER = runner
            cell.SPAWNS = spawn_record.SpawnRecord()
            cell.thinking_for_runner = lambda a: "off"
            # claim resolution is a different card's contract; this test pins the refusal
            cell._resolved_claim = lambda a: RuntimeError("claim not under test")
            try:
                with self.assertRaises(cell.Abort) as ctx:
                    cell.stage_run(stage_args(os.path.join(tmp, "absent.json")), rows)
                spawned = cell.SPAWNS.as_dict()["runner_launch"]
            finally:
                (cell.RUNNER, cell.SPAWNS, cell.thinking_for_runner,
                 cell._resolved_claim) = saved

        exc = ctx.exception
        self.assertEqual(exc.code, exit_codes.EXIT_CAPGATE_UNRECORDED,
                         "a cap-gate refusal must not reach the caller as %r" % (exc.code,))
        self.assertEqual(exc.stage, "4/7 run")
        self.assertIn("cap gate refused: unrecorded spend", exc.message)
        self.assertIn("delta=-2", exc.message,
                      "the delta the runner measured must be quoted: %s" % exc.message)
        self.assertIn("headroom_before=4", exc.message)
        self.assertIn("headroom_after=6", exc.message)
        self.assertNotIn("unmapped runner failure", exc.message,
                         "the old label sends a reader looking for a crash")
        self.assertIn(exit_codes.name_of(exc.code), "capgate-unrecorded")
        self.assertEqual(spawned, 1, "the launch must still be recorded exactly once")

    def test_b_an_aborted_run_still_reconciles_before_it_leaves(self):
        """(b) RED: mutate `_abort_stop` to `return rc` (no reconcile on abort) in a /tmp
        copy -> a delta < 0 aborted run returns 6 and nothing is refused. GREEN: 9."""
        rows = "/tmp/capgate-label-rows.jsonl"
        code, err = run_with_stderr(R._abort_stop, 6, StubGate(-2), None, None, rows)
        self.assertEqual(code, R.EXIT_CAP_DIVERGENCE,
                         "an aborted run whose spend is unrecorded must refuse, not exit 6")
        self.assertIn("CAP GATE UNRECORDED (delta=-2)", err)
        # a clean abort keeps the abort's own code
        clean, _ = run_with_stderr(R._abort_stop, 6, StubGate(0), None, None, rows)
        self.assertEqual(clean, 6)
        # ... and a positive divergence outranks the abort too
        positive, err_p = run_with_stderr(R._abort_stop, 6, StubGate(+1), None, None, rows)
        self.assertEqual(positive, R.EXIT_CAP_DIVERGENCE)
        self.assertIn("CAP GATE RECONCILE DIVERGENCE", err_p)

        # RED, runnable: the same gate through a conductor that forgot the reconcile.
        with tempfile.TemporaryDirectory(prefix="capgate-abort-red-") as tmp:
            src = io.open(os.path.join(LONGRUN, "run_longrun.py"), encoding="utf-8").read()
            mutant = src.replace("    return rc if cap_rc == 0 else cap_rc",
                                 "    return rc  # MUTANT: abort skips the reconcile")
            self.assertNotEqual(mutant, src, "the red mutation no longer applies")
            path = os.path.join(tmp, "run_longrun_mutant.py")
            with io.open(path, "w", encoding="utf-8") as fh:
                fh.write(mutant)
            spec = importlib.util.spec_from_file_location("run_longrun_mutant", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            red, red_err = run_with_stderr(mod._abort_stop, 6, StubGate(-2), None, None,
                                           rows)
            red_positive, _ = run_with_stderr(mod._abort_stop, 6, StubGate(+1), None,
                                              None, rows)
        self.assertEqual(red, 6, "RED: without the reconcile the unrecorded run exits 6")
        self.assertIn("CAP GATE UNRECORDED", red_err,
                      "RED: the refusal IS computed and printed -- and then thrown away, "
                      "which is exactly how the unrecorded spend disappeared on an abort")
        self.assertEqual(red_positive, 6, "RED: even a positive divergence is swallowed")

    def test_c_the_honest_branches_are_unchanged(self):
        """(c) delta == 0 -> 0; delta > 0 -> 9 at the runner; pre-send -> 4. If any of
        these moved, a fix for a label would have changed the brake."""
        rows = "/tmp/capgate-label-honest.jsonl"
        zero, err0 = run_with_stderr(R._gate_finish, StubGate(0), None, None, rows)
        self.assertEqual(zero[1], 0)
        self.assertIn("cap-gate: reconciled", err0)
        positive, err_p = run_with_stderr(R._gate_finish, StubGate(+1), None, None, rows)
        self.assertEqual(positive[1], R.EXIT_CAP_DIVERGENCE)
        self.assertIn("CAP GATE RECONCILE DIVERGENCE", err_p)
        negative, err_n = run_with_stderr(R._gate_finish, StubGate(-3), None, None, rows)
        self.assertEqual(negative[1], R.EXIT_CAP_DIVERGENCE)
        self.assertIn("delta=-3", err_n)
        refused, _ = run_with_stderr(R._cap_stop, R.CapRefusal("CAP REFUSED at T5"),
                                     StubGate(0), None, None, rows)
        self.assertEqual(refused, 4, "a pre-send refusal is exit 4 and stays exit 4")
        # 4 and 9 and 6 are all still distinct cell codes; 14 did not absorb any of them
        for rc in (4, 6):
            self.assertEqual(cell._runner_exit_code(rc), rc)
        # 9 is the ONE remap: it is the cap gate's now, never the grader/analyser's
        self.assertEqual(cell._runner_exit_code(9), exit_codes.EXIT_CAPGATE_UNRECORDED)

    def test_e_the_refusal_itself_spawns_nothing(self):
        """(e) Producing the refusal must not launch a runner: no retry, no probe. The
        counter is proven live in the same test (a real launch reports 1), so the zero is
        a measurement rather than an untouched default."""
        saved = (cell.SPAWNS, cell.RUNNER, cell.thinking_for_runner, cell._resolved_claim)
        cell.SPAWNS = spawn_record.SpawnRecord()
        try:
            abort = cell._capgate_abort(9, [REFUSAL], "/tmp/rows.jsonl")
            cell._runner_exit_code(9)
            self.assertEqual(cell.SPAWNS.as_dict()["runner_launch"], 0,
                             "reporting a cap-gate refusal launched a runner")
            self.assertEqual(abort.code, exit_codes.EXIT_CAPGATE_UNRECORDED)
            with tempfile.TemporaryDirectory(prefix="capgate-e-") as tmp:
                cell.RUNNER = fake_runner(tmp, 9)
                cell.thinking_for_runner = lambda a: "off"
                cell._resolved_claim = lambda a: RuntimeError("claim not under test")
                with self.assertRaises(cell.Abort):
                    cell.stage_run(stage_args(os.path.join(tmp, "absent.json")),
                                   os.path.join(tmp, "rows.jsonl"))
            self.assertEqual(cell.SPAWNS.as_dict()["runner_launch"], 1,
                             "the spawn counter is not live: the zero above proves nothing")
        finally:
            (cell.SPAWNS, cell.RUNNER, cell.thinking_for_runner,
             cell._resolved_claim) = saved


class TableAgreementTests(unittest.TestCase):
    def test_d_the_new_code_agrees_across_table_cell_docs_and_runner_map(self):
        """(d) The code exists once, is raised by a named cell site, is mapped from the
        runner's 9, and is named in docs/EXIT-CODES.md and docs/GATE-CHAIN.md.
        RED: drop the EXIT_TABLE entry (or the docs row) -> the scan test in
        test_exit_codes.py and the doc-table test both fail naming it."""
        self.assertEqual(exit_codes.EXIT_CAPGATE_UNRECORDED, 14)
        spec = exit_codes.EXIT_TABLE[14]
        self.assertEqual(spec["name"], "capgate-unrecorded")
        self.assertEqual(exit_codes.RUNNER_MAPPED_TO_CELL[9], 14)
        self.assertIn("14", exit_codes.RUNNER_MAPPED_TO_CRASH[9],
                      "the old 9 entry must say where 9 now goes")
        self.assertIn("capgate", exit_codes.RUNNER_MAPPED_TO_CRASH[9])
        self.assertNotIn(14, exit_codes.RUNNER_CODES)
        self.assertNotIn(14, exit_codes.EXTERNAL_CODES)

        cell_src = io.open(os.path.join(LONGRUN, "cell.py"), encoding="utf-8").read()
        self.assertIn("_RUNNER_MAPPED_TO_CELL = exit_codes.RUNNER_MAPPED_TO_CELL",
                      cell_src, "cell.py keeps a second copy of the remap")
        self.assertIn("raise _capgate_abort(rc, err_lines, rows_path, detail)", cell_src,
                      "stage_run() no longer routes the refusal through the declared "
                      "cap-gate abort")
        self.assertIn("Abort(exit_codes.EXIT_CAPGATE_UNRECORDED", cell_src,
                      "the cap-gate Abort must name the declared constant, not a literal")

        doc = io.open(DOCS_EXIT_CODES, encoding="utf-8").read()
        self.assertIn("| 14 | `capgate-unrecorded` |", doc,
                      "docs/EXIT-CODES.md does not name the new code in its table")
        gate_chain = io.open(os.path.join(REPO, "docs", "GATE-CHAIN.md"),
                             encoding="utf-8").read()
        self.assertIn("14", gate_chain,
                      "docs/GATE-CHAIN.md does not name the new cap-gate cell code")
        self.assertIn("capgate-unrecorded", gate_chain)


if __name__ == "__main__":
    unittest.main(verbosity=2)
