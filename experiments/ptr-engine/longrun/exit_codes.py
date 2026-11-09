#!/usr/bin/env python3
"""exit_codes.py - THE exit-code table for the cell conductor. One copy, no prose twin.

WHY THIS FILE EXISTS (unit EXIT-CODE-TABLE, measured): before it, the conductor's codes
lived in three places that could disagree -- a prose table in `cell.py`'s docstring, a
hard-coded dict of runner codes in `cell.py`, and the bare integers at each `Abort(...)`
raise site. They did disagree. A source scan found 11 codes reachable, a prose table of
11 entries with one (`7`, record) that NOTHING raised, and code `1` reachable only as an
uncaught traceback that no table entry described. A reader could not tell `1` (crash)
from a generic crash, and the record stage -- the step this project has already lost
evidence at -- could not have produced its own declared code.

    python3 exit_codes.py            # print the table a reader sees

CONTRACT (tests/test_exit_codes.py enforces it):
  * every key of EXIT_TABLE is raised by some site in cell.py, directly or by documented
    propagation (`RUNNER_CODES`), OR is declared in `EXTERNAL_CODES` and raised by the
    named tool outside the conductor (13, tree-moved, is `tools/tree_freeze.py`);
  * every integer handed to `Abort(...)`, `_enforce(..., code)`, `sys.exit(...)`,
    `raise SystemExit(...)` or returned from `main()` appears in EXIT_TABLE;
  * neither direction may drift, because the test fails on extra AND on missing codes.

Stdlib only. Imported by cell.py; imports nothing from it.
"""

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_PREFLIGHT = 2
EXIT_BUDGET = 3
EXIT_LEDGER_CAP = 4
EXIT_RUNNER_CRASH = 5
EXIT_RUNAWAY = 6
EXIT_UNWRITABLE = 7
EXIT_PROJECTION = 8
EXIT_INCONSISTENT = 9
EXIT_GRADE = 10
EXIT_ANALYSE = 11
EXIT_PREREG = 12
EXIT_TREE_MOVED = 13
# CAPGATE-CELL-LABEL: the runner's cap-gate refusal, at CELL level. 14, not 9:
# 9 is the cell's grader/analyser inconsistency and must stay single-meaning.
EXIT_CAPGATE_UNRECORDED = 14

# Runner codes cell.py propagates UNMODIFIED (never collapsed into one number). These are
# raise sites too: `stage_run` turns the runner's rc into `Abort(rc, ...)`. Any other rc is
# a crash (5). Kept here so the scan test can see the propagation as declared, not hidden
# inside a dict literal.
RUNNER_CODES = frozenset({2, 3, 4, 5, 6, 7})

# Codes run_longrun.py can terminate with that the conductor does NOT propagate verbatim,
# and why. They live here, in the one table module, so the remap is declared where the scan
# test can see it instead of hiding inside `rc if rc in RUNNER_CODES else 5`.
# Runner codes the conductor does NOT propagate verbatim but DOES hand a distinct
# cell code. Declared here for the same reason as the crash map below: the mapping
# is a claim about cell.py, and a claim that lives only inside an `elif` cannot be
# scanned. `EXIT_CAPGATE_UNRECORDED` is the CAPGATE-CELL-LABEL fix for a reported
# defect: a runaway/refused run was reported to the caller as "unmapped runner
# failure" (exit 5, runner-crash), which sends a reader looking for a crash when
# the cap gate had in fact refused because spend was unrecorded.
RUNNER_MAPPED_TO_CELL = {
    9: EXIT_CAPGATE_UNRECORDED,
}

RUNNER_MAPPED_TO_CRASH = {
    1: "a bare `raise SystemExit(str)` (RESUME REFUSED, run_longrun.py:1600) or an "
       "uncaught traceback: the runner failed, it did not refuse, so the cell reports 5 "
       "(runner-crash) and the runner's stderr in the record says why",
    9: "run_longrun.py's EXIT_CAP_DIVERGENCE -- the run's request count and its rows "
       "disagree. It must NOT be propagated as 9: 9 is the CELL's "
       "grader/analyser-inconsistency code, owned by DECIDABILITY-SEAM, and a caller "
       "reading 9 must not have to guess which refusal it is. WHERE IT GOES NOW: the "
       "cell reports RUNNER_MAPPED_TO_CELL[9] = 14 (capgate-unrecorded), and its message "
       "quotes the runner's own delta/headroom line. The traversal is unchanged and "
       "deliberate: the runner still exits 9 (its own numbering, not renumbered); only "
       "the CALLER-side code became the cap gate's own, so a reader is no longer sent to "
       "look for a crash. Until CAPGATE-CELL-LABEL this mapping said 'the cell's 5 is "
       "honest' -- the handoff V-CAPGATE-REFUSE measured that 5 reads as a crash.",
}

# Codes this table declares that NO cell.py stage raises, because they are not conductor
# codes at all: they belong to a tool that judges a TREE rather than a run. Declared here
# so the number cannot be re-typed elsewhere and so the scan test can excuse them for one
# stated reason instead of silently: `{code: module that raises it}`.
#
# 13 is the one that matters: "the tree moved under the audit" is NOT "the work failed",
# and a code shared with a failure would let a concurrent card's edit be reported as the
# claimant's verdict (measured: V-GATE-OPERAND's pin stopped naming cell.py at all, and
# SEAM-TEST-RED settled FAIL exit-1 on another card's in-flight red).
EXTERNAL_CODES = {
    EXIT_TREE_MOVED: "experiments/ptr-engine/tools/tree_freeze.py",
}

# The single source of truth. `meaning` is the one-line text a printout shows; `condition`

# says when it fires; `raise_site` names the code path that raises it (stable function
# names, plus the `Abort(...)` call); `action` is what the reader should do next -- a code
# without an action is a number, not a diagnosis.
EXIT_TABLE = {
    EXIT_OK: {
        "name": "ok",
        "meaning": "cell completed; gate verdicts and the record were written",
        "condition": "every stage returned, or --dry-run/--offline finished",
        "raise_site": "cell.py: main() `return 0` (both the dry-run branch and the end)",
        "action": "read the cell record in --out-dir; nothing to repair",
    },
    EXIT_INTERNAL: {
        "name": "internal-error",
        "meaning": "an exception the conductor did not classify escaped a stage; the "
                   "full traceback was printed and the run was identified",
        "condition": "any non-Abort exception in main() (bug, unreadable JSON after a "
                     "successful parse, a missing dependency at an unexpected point)",
        "raise_site": "cell.py: main() `except Exception` -> `return 1`",
        "action": "read the traceback on stderr: this is a HARNESS defect, not a "
                  "measurement. Do not re-run the cell hoping for a different result; "
                  "file the traceback against the stage named in the last stage line",
    },
    EXIT_PREFLIGHT: {
        "name": "preflight",
        "meaning": "the cell cannot be graded at all: fixture, harness freeze, or an "
                   "unreadable gate artefact",
        "condition": "fixture does not parse / no checkpoints / truth not derivable / "
                     "answer contract absent / harness digest mismatch or missing file / "
                     "gate artefact unreadable. ALSO argparse usage errors, which exit 2 "
                     "by argparse's own convention. NOT a G3 prereg refusal, which has "
                     "its own code 12",
        "raise_site": "cell.py: preflight(), stage_harness(), eval_gate_ledger() and the "
                      "gate-artefact loader -> `Abort(2, ...)`",
        "action": "fix the artefact or the flag named in the message; no request was "
                  "sent, so nothing was measured and nothing needs re-measuring",
    },
    EXIT_BUDGET: {
        "name": "budget",
        "meaning": "the runner's own --dry-run, plus 10% headroom, exceeds --budget",
        "condition": "required_with_headroom > args.budget, or the dry-run produced no "
                     "would_send_total",
        "raise_site": "cell.py: stage_budget() -> `Abort(3, \"3/7 budget\", ...)`",
        "action": "raise --budget, or lower --turns/--reps/--arm; do not edit the runner",
    },
    EXIT_LEDGER_CAP: {
        "name": "ledger-cap",
        "meaning": "the project ledger's cap gate (G1) refused the send; also the "
                   "runner's propagation of the ledger's own cap refusal",
        "condition": "spent + would_spend + reserve > cap, or the ledger's counter could "
                     "not read its row files (an uncountable budget must refuse)",
        "raise_site": "cell.py: _enforce(eval_gate_ledger(...), ..., 4) and stage_run() "
                      "propagating the runner's rc=4",
        "action": "extend or repair the ledger artefact named in the message; a refusal "
                  "here is the budget being honest, not a failure of the cell",
    },
    EXIT_RUNNER_CRASH: {
        "name": "runner-crash",
        "meaning": "run_longrun.py exited in a way that is not one of its own guard "
                   "refusals (or an unmapped runner code)",
        "condition": "runner rc not in {2,3,4,6,7} -- including rc=1, a runner-side "
                     "traceback or a bare `raise SystemExit(str)`",
        "raise_site": "cell.py: stage_run() -> `Abort(code, \"4/7 run\", ...)` with "
                      "code=5 for an unmapped rc",
        "action": "read the runner's stderr in the cell record; rows written before the "
                  "crash are kept at the rows path named in the message",
    },
    EXIT_RUNAWAY: {
        "name": "runaway",
        "meaning": "one or more runaway turns ended the cell",
        "condition": "the runner's --runaway-turns guard fired, or the live turn-wall cap "
                     "ended the cell",
        "raise_site": "cell.py: stage_run() propagating the runner's rc=6",
        "action": "inspect the rows up to the last turn; a runaway is a client/harness "
                  "problem, so fix it before spending another request",
    },
    EXIT_UNWRITABLE: {
        "name": "unwritable",
        "meaning": "an artefact the cell is REQUIRED to write could not be written -- "
                   "the runner's row file, or stage 7's cell JSON/markdown",
        "condition": "the runner returned 7 (it could not write its rows), or stage 7 hit "
                     "an OSError creating --out-dir or writing cell-<arm>-<stamp>.json/.md",
        "raise_site": "cell.py: stage_run() propagating the runner's rc=7, and "
                      "stage_record() -> `Abort(7, \"7/7 record\", ...)` (also main()'s "
                      "final record write)",
        "action": "fix the path, permissions or free space named in the message and "
                  "re-run. The measurement may exist but its evidence is NOT on disk: "
                  "an unwritten record is the failure this project has already paid for",
    },
    EXIT_PROJECTION: {
        "name": "projection",
        "meaning": "the projected wall clock (G2) exceeds --max-wall",
        "condition": "projected_requests x projected turn wall > --max-wall",
        "raise_site": "cell.py: _enforce(eval_gate_projection(...), ..., 8)",
        "action": "raise --max-wall, or recalibrate --projected-from / PROJECTION.json "
                  "with measured rows; never shrink the projection to fit",
    },
    EXIT_INCONSISTENT: {
        "name": "inconsistent",
        "meaning": "the grader and the analyser disagree about whether anything was "
                   "decided at all",
        "condition": "(grader decidable > 0) != (analyser graded_n > 0), and "
                     "--allow-inconsistent was not passed",
        "raise_site": "cell.py: stage_consistency() -> `Abort(9, \"7 consistency\", ...)`",
        "action": "find out why the two populations differ before believing either "
                  "number; --allow-inconsistent records the override, it does not "
                  "resolve the contradiction",
    },
    EXIT_GRADE: {
        "name": "grade",
        "meaning": "grade_v5.py itself refused (it exited non-zero)",
        "condition": "the grader's process exit != 0, e.g. fixture_truth_mismatch",
        "raise_site": "cell.py: stage_grade() -> `Abort(10, \"5/7 grade\", ...)`",
        "action": "re-run grade_v5.py on the same rows and fixture: the cell does not "
                  "need re-running, the grading does",
    },
    EXIT_ANALYSE: {
        "name": "analyse",
        "meaning": "analyze_stats.py itself refused (it exited non-zero)",
        "condition": "the analyser's process exit != 0, e.g. a document that is not a "
                     "grade_v5 document",
        "raise_site": "cell.py: stage_analyse() -> `Abort(11, \"6/7 analyse\", ...)`",
        "action": "re-run analyze_stats.py on the same rows and grade document; the "
                  "grade document stands, so no request is needed",
    },
    EXIT_PREREG: {
        "name": "prereg",
        "meaning": "G3 refused: the cell's own n cannot support the hypothesis it would "
                   "claim -- or it declared none at all",
        "condition": "no --hypothesis (silence), --hypothesis none, an unknown hypothesis, "
                     "H1 with n < 60, or H3 with a fixture carrying < 8 checkpoints",
        "raise_site": "cell.py: _enforce(eval_gate_prereg(...), \"3c/7 G3 prereg gate\", 12)",
        "action": "name the claim with --hypothesis, or raise --turns/--reps until n "
                  "meets PARM-1's minimum; never lower the minimum to fit the cell",
    },
    EXIT_CAPGATE_UNRECORDED: {
        "name": "capgate-unrecorded",
        "meaning": "the cap gate refused because requests reached the wire whose rows "
                   "were not written, so the ledger understates the spend; also a "
                   "reconcile-time divergence in either direction",
        "condition": "the runner's exit reconciliation finds delta < 0 (rows gained < "
                     "requests used) or delta > 0 (a row no request bought), or it cannot "
                     "record the final counts in its manifest. Reached by ABORTED runs "
                     "too: the runaway exits reconcile before returning",
        "raise_site": "cell.py: stage_run() -> `Abort(exit_codes.EXIT_CAPGATE_UNRECORDED, "
                      "\"4/7 run\", ...)` via RUNNER_MAPPED_TO_CELL[9]",
        "action": "read the quoted CAP GATE UNRECORDED line (delta, used_in_run, "
                  "rows_gained, headroom_before/after). Do NOT re-run before reconciling: "
                  "the ledger would grant headroom that does not exist. Find the row "
                  "writer that lost the request's row, or the row nothing paid for",
    },
    EXIT_TREE_MOVED: {
        "name": "tree-moved",
        "meaning": "the bytes an audit froze are no longer the bytes on disk: the tree "
                   "moved while the check ran, so the result names a file that has changed",
        "condition": "tools/tree_freeze.py verify() re-hashes a freeze and at least one "
                     "recorded file is `moved` (different sha256) or `deleted`. NOT a "
                     "command failure: this code says the tree moved, and a result judged "
                     "against it is UNSTAMPED, not FAIL",
        "raise_site": "tools/tree_freeze.py: verify() returns "
                      "`EXIT_TREE_MOVED` (the process exits with it) -- declared external "
                      "in EXTERNAL_CODES; cell.py never raises it",
        "action": "re-run the audit against the SETTLED tree, or re-freeze and re-run "
                  "whatever the moved file belongs to. Do not re-interpret the old result "
                  "and do not report the movement as the claimant's failure",
    },
}

# Derived views -- never a second copy.
EXIT_CODES = {code: spec["meaning"] for code, spec in EXIT_TABLE.items()}
EXIT_NAMES = {code: spec["name"] for code, spec in EXIT_TABLE.items()}


def describe(code):
    """One-line meaning for a code, or a loud fallback for an undeclared one."""
    spec = EXIT_TABLE.get(code)
    return spec["meaning"] if spec else "UNDECLARED exit code %r" % (code,)


def name_of(code):
    spec = EXIT_TABLE.get(code)
    return spec["name"] if spec else "undeclared"


def action_for(code):
    spec = EXIT_TABLE.get(code)
    return spec["action"] if spec else (
        "this code is not in exit_codes.EXIT_TABLE: the conductor and its table have "
        "drifted -- fix the raise site or declare the code, do not document around it")


def render_table(with_action=False):
    """The rendered table. cell.py appends this to its own __doc__; docs duplicate it."""
    out = ["FINAL EXIT-CODE TABLE (rendered from exit_codes.EXIT_TABLE -- the only copy):",
           ""]
    for code in sorted(EXIT_TABLE):
        spec = EXIT_TABLE[code]
        out.append("    %-2d %-14s %s" % (code, spec["name"], spec["meaning"]))
        if with_action:
            out.append("       next: %s" % spec["action"])
    return "\n".join(out)


if __name__ == "__main__":
    print(render_table(with_action=True))
