#!/usr/bin/env python3
"""tranche_canary.py - the PRE-TRANCHE CANARY: spend a few turns, find a broken launch shape.

WHY THIS EXISTS (measured, 2026-10-26):
`TRANCH1-DRYRUN-2` passed 10/10 cells offline -- gates allowed, treatments fired by T48,
design_cap_tokens 10616, 0 spawns, 0 sockets -- and the live tranche then died: cell 1
reached T27 of 48, with T3 and T27 each consuming the full 4,096-token completion ceiling
(`length`, then `runaway_turn`, `truncated: true`), exit 6. 28 requests spent, 0 usable
cells. An offline rehearsal cannot see this class of failure: it is MODEL BEHAVIOUR on the
chosen prompts at the chosen channel, not a gate, a cap or a socket. The cheapest
instrument that sees it is a few real turns, and the recorded cell proves the signal is
available early: the FIRST cap-length completion is at T3.

WHAT IT DOES: given an arm's cell-1 launch command (live mode) or a rows file (replay
mode), classify the first N turn rows into exactly one of three verdicts:

    shape_ok          no turn hit the completion ceiling, no stop signal in
                      {runaway_turn, turn_wall_cap}, no tool-call storm, and the arm's own
                      answer contract fired in-window (which contract is consumed depends
                      on the row shape: see STOP-SIGNAL PRECEDENCE below).
    shape_degenerate  a cap-length completion appeared within N turns (the turn,
                      completion_tokens, max_tokens, wall_ms and stop signal are named),
                      because a 4,096-token completion on a question whose answers are a
                      few tokens is a CHANNEL/PROMPT MISMATCH, not a measurement; or a
                      tool-call storm appeared (STORM_MIN_CALLS requested calls in one
                      turn), which is the launch failing to fan-in, not measuring.
    shape_unknown     fewer than N turns recorded, a stop signal outside the closed
                      vocabulary (or missing), no traffic at all, or -- the quiet one --
                      the answer contract did not fire inside the window. Never rounded
                      up to ok.

STOP-SIGNAL PRECEDENCE (why era B rows are readable at all). A turn row can say why it
ended through four different fields, and the two writers do not agree on which one they
emit: the tools-off cells write the engine-derived `stop_reason`, while the tools-on
(run_longrun) rows carry only the wire `finish_reason`. The canary therefore resolves
the signal in this order, first present field wins, and records WHICH field it read in
`stop_signal_source`:

    1. `stop_reason`, when present and non-null -- the engine's own derivation, and the
       only field the tools-off control carries. Never overridden by a weaker signal.
    2. `finish_reason`, when present and non-null -- the protocol field the tools-on rows
       carry instead; `length` means the completion was cut by max_tokens.
    3. `truncated: true` -- an explicit boolean that the content was cut; read as
       `length` only when no reason field is present, because it does not say WHERE the
       cut came from.
    4. `completion_tokens == max_tokens` -- arithmetic last: it is corroboration, not a
       protocol statement, so it must never outrank a field that names the reason.
    5. otherwise `None` -> shape_unknown, as before.

ANSWER CONTRACT, PER SHAPE (not averaged). Two different contracts exist and the verdict
consumes exactly one of them, chosen by the shape of the rows:

    era A (rows carry `stop_reason`): consumes `parseable_answers` -- unchanged from
        CANARY-FALSE-POSITIVE, and deliberately NOT loosened.
    era B (rows carry `finish_reason` only): consumes `answer_verified` -- the checkpoint
        grader's verdict, computed by the harness. `parseable_answers` is structurally 0
        on this shape (those rows carry no `answer_turn`/`answer_value`), so requiring it
        would make shape_ok unreachable; `answer_verified` is the same contract stated by
        the harness that actually parsed the answer, and it is only non-null at checkpoint
        turns (T12/T24/T46 in the recorded runs). Both counts are reported so the reader
        can see the shape's own evidence rather than a number that cannot move.

TOOL-CALL STORM. `STORM_MIN_CALLS = 110` requested calls in one turn. Measured, not
chosen: the manifest cap is `tools.max_calls_per_turn = 2`, the two recorded storms fired
116 (v4 T45) and 130 (v5 T29) calls in one turn, and the largest fan-out on a turn the
engine contained (cap refusals, finish `stop`, no failed_turn) is 101 (v6 T26). 110 is
the midpoint of that observed gap: above every contained turn seen, below every storm
seen. The false negative it admits is stated rather than hidden: a genuine storm under
110 calls (v5 T36 fired 25 against the same cap) is not caught, and a genuinely thorough
turn above 110 calls is declared degenerate. The rule is a fan-out bound, not a proof of
intent, so it is reported as `tool_call_storm` with the turn and count named.

PRIORITY: a positive degeneration signal outranks a short window. A cap-length completion
inside the rows we DO have is evidence; a window that stopped short is only absence of
evidence. So `degenerate` is checked first, and everything else that is not `ok` is
`unknown`. Among the degeneration triggers the order is fixed -- completion ceiling, then
degenerate stop reason, then tool-call storm -- so a turn that both consumed the ceiling
and stormed is named by the ceiling (the era A control fires the ceiling at T3 and must
keep that name).

EXIT CODES (all four exist in longrun/exit_codes.EXIT_TABLE; the numbers are REUSED by the
canary's contract, which is why each one is imported rather than re-typed):
    0 ok | 1 degenerate | 2 unknown | 3 could-not-run (bad argv, refused launch)
Only the canary's verdict number is reused here: the table's `name`/`meaning` describe the
CONDUCTOR's use of the same number, and the canary prints its own verdict name next to it.

THIS TOOL REPORTS. IT CANNOT CHANGE THE SHAPE. It rewrites exactly one argv value -- the
`--turns` window -- and it refuses a launch whose `--reps` is above 1, because cell 1 is
rep 1. Whether a degenerate shape gets re-launched is a human-or-card decision.

USAGE
    # replay: classify rows already on disk. ZERO requests.
    python3 tools/tranche_canary.py --rows experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl --turns 5

    # live: run the first N turns of one arm's cell 1 (SPENDS REAL REQUESTS -- count it).
    python3 tools/tranche_canary.py --live --arm pointer-stable --turns 5 \\
        --launch "python3 experiments/ptr-engine/longrun/cell.py --arm pointer-stable \\
                  --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json \\
                  --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 \\
                  --runaway-turns 2 --budget 900 --hypothesis H2 --no-cell-handoff \\
                  --out-dir experiments/ptr-engine/measure" \\
        --rows experiments/ptr-engine/measure

Stdlib only. Reads rows; writes nothing unless --out is given.
"""

from __future__ import annotations

import argparse
import glob as globmod
import json
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ENGINE = HERE.parent.parent                      # experiments/ptr-engine
LONGRUN = ENGINE / "longrun"

# Codes come from the one table; never re-typed numbers.
sys.path.insert(0, str(LONGRUN))
from exit_codes import (  # noqa: E402
    EXIT_BUDGET,
    EXIT_INTERNAL,
    EXIT_OK,
    EXIT_PREFLIGHT,
)

EXIT_SHAPE_OK = EXIT_OK            # 0
EXIT_DEGENERATE = EXIT_INTERNAL    # 1 -- the launched shape is not a measurement
EXIT_UNKNOWN = EXIT_PREFLIGHT      # 2 -- cannot say; never rounded to ok
EXIT_CANNOT_RUN = EXIT_BUDGET      # 3 -- bad argv / refused launch


class CanaryParser(argparse.ArgumentParser):
    """Usage errors exit 3 (could-not-run), NOT argparse's default 2.

    2 is this tool's `shape_unknown` verdict, so an argv typo must not read as a shape
    verdict. This is the one place the canary departs from argparse's convention, and it
    departs towards the card's contract: bad argv is "could not run", never "unknown".
    """

    def error(self, message):
        self.print_usage(sys.stderr)
        print("3/canary could not run: %s" % message, file=sys.stderr)
        raise SystemExit(EXIT_CANNOT_RUN)


def cannot_run(message):
    """Exit 3 with a single message: the tool could not be asked the question at all."""
    print("3/canary could not run: %s" % message, file=sys.stderr)
    raise SystemExit(EXIT_CANNOT_RUN)

#: The row vocabulary is OWNED by longrun/client.py. Import it when the client module is
#: importable (it is stdlib + httpx, so normally it is); otherwise fall back to this
#: literal, which tests/test_tranche_canary.py pins against the owner when it can.
_FALLBACK_STOP_REASONS = (
    "stop", "length", "tool_calls", "content_filter", "turn_wall_cap",
    "runaway_turn", "http_error", "stream_error", "empty_response", "unknown",
)

#: Stop reasons shape_ok must never contain: the launch could not carry a measurement.
DEGENERATE_STOP_REASONS = frozenset({"runaway_turn", "turn_wall_cap"})

#: The WIRE stop vocabulary (the protocol's `finish_reason`). Used only to read the era B
#: rows, which carry no `stop_reason`; the engine's closed vocabulary above stays the
#: authority for era A rows.
PROTOCOL_FINISH_REASONS = frozenset({"stop", "length", "tool_calls", "content_filter"})

#: The stop-signal field precedence, in the order stop_signal() reads it. Exported so the
#: doc and the tests quote one list instead of three copies.
STOP_SIGNAL_PRECEDENCE = (
    "stop_reason",
    "finish_reason",
    "truncated",
    "completion_tokens==max_tokens",
)

#: Requested tool calls in ONE turn above which the turn is a storm rather than a
#: measurement. 110 is measured: storms fired 116 (v4 T45) and 130 (v5 T29) calls, the
#: largest fan-out on a contained turn is 101 (v6 T26), so 110 is the midpoint of the
#: observed gap. See the module docstring for the false negative this admits.
STORM_MIN_CALLS = 110

#: Which answer contract each row shape's verdict consumes. Never averaged across shapes.
ANSWER_CONTRACT_BY_ERA = {"A": "parseable_answers", "B": "answer_verified"}


def stop_reasons():
    """The closed stop-reason vocabulary, preferring its owner's definition."""
    try:
        if str(LONGRUN) not in sys.path:
            sys.path.insert(0, str(LONGRUN))
        import client  # type: ignore
        return tuple(client.STOP_REASONS)
    except Exception:
        return _FALLBACK_STOP_REASONS


def load_rows(path):
    """Read a JSONL rows file. Blank lines are skipped; only turn rows are returned later."""
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                cannot_run("%s:%d is not JSON (%s)" % (path, lineno, exc))
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _groups(rows):
    """Group turn rows by (arm, rep), preserving first-seen order."""
    groups = {}
    for row in rows:
        if row.get("kind") not in (None, "turn"):
            continue
        if not isinstance(row.get("turn"), int):
            continue
        key = (row.get("arm"), row.get("rep"))
        groups.setdefault(key, []).append(row)
    for key in groups:
        groups[key].sort(key=lambda r: r["turn"])
    return groups


def stop_signal(row):
    """Why did this turn end? Returns (reason, source) per STOP_SIGNAL_PRECEDENCE.

    Era A rows write the engine-derived `stop_reason`; era B (tools-on) rows carry only
    the wire `finish_reason`. Reading only `stop_reason` is what made 3 of 3 tools-on
    files shape_unknown at every N below 48: the field was present in the row, just not
    the one the reader looked at.
    """
    reason = row.get("stop_reason")
    if reason:
        return reason, "stop_reason"
    finish = row.get("finish_reason")
    if finish:
        return finish, "finish_reason"
    if row.get("truncated"):
        return "length", "truncated"
    ct, mt = row.get("completion_tokens"), row.get("max_tokens")
    if isinstance(ct, int) and isinstance(mt, int) and mt > 0 and ct >= mt:
        return "length", "completion_tokens==max_tokens"
    return None, None


def _cap_hit(row):
    """True when this turn consumed the completion ceiling."""
    if stop_signal(row)[0] == "length":
        return True
    ct, mt = row.get("completion_tokens"), row.get("max_tokens")
    return isinstance(ct, int) and isinstance(mt, int) and mt > 0 and ct >= mt


def tool_call_fanout(row):
    """How many tool calls this turn REQUESTED (executed or refused). 0 when tools are off."""
    calls = row.get("tool_calls")
    return len(calls) if isinstance(calls, list) else 0


def _storm(row):
    """True when one turn requested a tool-call storm (>= STORM_MIN_CALLS calls)."""
    return tool_call_fanout(row) >= STORM_MIN_CALLS


def _shape_era(window):
    """'A' when the rows carry the engine's stop_reason, 'B' when only the wire field."""
    if any(r.get("stop_reason") for r in window):
        return "A"
    if any(r.get("finish_reason") or r.get("answer_verified") is not None for r in window):
        return "B"
    return "A"


def _parseable_answer(row):
    """True when this turn produced an answer the arm's own contract could parse."""
    if not row.get("answer_turn"):
        return False
    if row.get("answer_parse_error"):
        return False
    value = row.get("answer_value")
    if value is None:
        raw = row.get("answer_raw")
        return bool(isinstance(raw, str) and raw.strip())
    return True


def _evidence(row, trigger):
    reason, source = stop_signal(row)
    return {
        "turn": row.get("turn"),
        "completion_tokens": row.get("completion_tokens"),
        "max_tokens": row.get("max_tokens"),
        "stop_reason": reason,
        "stop_signal_source": source,
        "wall_ms": row.get("wall_ms"),
        "truncated": row.get("truncated"),
        "tool_calls": tool_call_fanout(row),
        "trigger": trigger,
    }


def classify(rows, n=5, arm=None, rep=None):
    """Classify the first N turn rows. Pure function over rows; performs no I/O."""
    if n < 1:
        raise ValueError("n must be >= 1")

    groups = _groups(rows)
    if not groups:
        return {
            "verdict": "shape_unknown", "exit_code": EXIT_UNKNOWN,
            "arm": arm, "rep": rep, "n": n, "turns_observed": 0,
            "parseable_answers": 0, "triggers": [],
            "why": "no traffic at all: the rows hold no turn rows, so nothing was launched "
                   "or nothing was recorded",
        }

    if arm is not None:
        keys = [k for k in groups if k[0] == arm]
        if not keys:
            return {
                "verdict": "shape_unknown", "exit_code": EXIT_UNKNOWN,
                "arm": arm, "rep": rep, "n": n, "turns_observed": 0,
                "parseable_answers": 0, "triggers": [],
                "why": "no traffic for arm %r: the rows carry no turn rows for it" % (arm,),
            }
    else:
        keys = list(groups)
    if rep is not None:
        keys = [k for k in keys if k[1] == rep] or keys[:1]
    key = sorted(keys, key=lambda k: (str(k[0]), str(k[1])))[0]

    window = [r for r in groups[key] if r["turn"] <= n]
    vocab = stop_reasons()
    era = _shape_era(window)
    contract = ANSWER_CONTRACT_BY_ERA[era]
    out = {
        "arm": key[0], "rep": key[1], "n": n,
        "turns_observed": len(window),
        "parseable_answers": sum(1 for r in window if _parseable_answer(r)),
        "answer_verified": sum(1 for r in window if r.get("answer_verified") is True),
        "answer_verified_false": sum(1 for r in window if r.get("answer_verified") is False),
        "shape_era": era,
        "answer_contract": contract,
        "stop_signal_sources": sorted({(stop_signal(r)[1] or "none") for r in window}),
        "storm_min_calls": STORM_MIN_CALLS,
        "triggers": [],
    }

    # 1. A positive degeneration signal outranks a short window. Fixed trigger order:
    #    ceiling, then degenerate stop reason, then tool-call storm.
    for row in window:
        if _cap_hit(row):
            out.update(verdict="shape_degenerate", exit_code=EXIT_DEGENERATE,
                       trigger="completion_ceiling", evidence=_evidence(row, "completion_ceiling"),
                       triggers=["completion_ceiling"])
            out["why"] = (
                "turn %s consumed the completion ceiling: completion_tokens %s of "
                "max_tokens %s (stop signal %r read from %s, wall_ms %s). A full-ceiling "
                "completion on a question whose answers are a few tokens is a "
                "CHANNEL/PROMPT MISMATCH, not a measurement."
                % (row.get("turn"), row.get("completion_tokens"), row.get("max_tokens"),
                   stop_signal(row)[0], stop_signal(row)[1], row.get("wall_ms")))
            return out
        if stop_signal(row)[0] in DEGENERATE_STOP_REASONS:
            out.update(verdict="shape_degenerate", exit_code=EXIT_DEGENERATE,
                       trigger="degenerate_stop_reason",
                       evidence=_evidence(row, "degenerate_stop_reason"),
                       triggers=["degenerate_stop_reason"])
            out["why"] = (
                "turn %s stopped with %r, which is outside anything a cell can measure "
                "(wall_ms %s). The launch shape ends cells rather than measuring them."
                % (row.get("turn"), stop_signal(row)[0], row.get("wall_ms")))
            return out

    for row in window:
        if _storm(row):
            out.update(verdict="shape_degenerate", exit_code=EXIT_DEGENERATE,
                       trigger="tool_call_storm",
                       evidence=_evidence(row, "tool_call_storm"),
                       triggers=["tool_call_storm"])
            out["why"] = (
                "turn %s requested %d tool calls in one turn, at or above the storm "
                "threshold of %d: the launch is not fanning tool results back in, so the "
                "turn cannot measure. A genuinely thorough turn above %d calls is the "
                "false negative this rule admits."
                % (row.get("turn"), tool_call_fanout(row), STORM_MIN_CALLS, STORM_MIN_CALLS))
            return out

    # 2. Fewer turns than the window asked for: the window is incomplete.
    if len(window) < n:
        out.update(verdict="shape_unknown", exit_code=EXIT_UNKNOWN)
        out["why"] = (
            "only %d of the %d requested turns are recorded (last turn %s): the window is "
            "short, so nothing about the shape is established and it is NOT rounded to ok"
            % (len(window), n, window[-1]["turn"] if window else None))
        return out

    # 3. A stop signal outside the closed vocabulary (or missing) means the row cannot
    #    say why the turn ended; that is unknown, not ok.
    for row in window:
        reason, source = stop_signal(row)
        if reason not in vocab:
            out.update(verdict="shape_unknown", exit_code=EXIT_UNKNOWN,
                       trigger="stop_reason_outside_vocabulary",
                       evidence=_evidence(row, "stop_reason_outside_vocabulary"),
                       triggers=["stop_reason_outside_vocabulary"])
            out["why"] = (
                "turn %s carries stop signal %r (read from %r), which is not in the closed "
                "vocabulary %s" % (row.get("turn"), reason, source, list(vocab)))
            return out

    # 4. The ok case needs the arm's own answer contract to have fired in-window. WHICH
    #    field that is depends on the shape, and the two are never averaged: era A is
    #    held to parseable_answers (the old gate, not loosened), era B to answer_verified.
    needed = (out["parseable_answers"] if contract == "parseable_answers"
              else out["answer_verified"])
    if needed == 0:
        trigger = ("no_parseable_answer" if contract == "parseable_answers"
                   else "no_verified_answer")
        out.update(verdict="shape_unknown", exit_code=EXIT_UNKNOWN, trigger=trigger)
        out["triggers"] = [trigger]
        if contract == "parseable_answers":
            out["why"] = (
                "no completion ceiling was hit and every stop reason is in-vocabulary, but "
                "the arm's answer contract produced no parseable answer in the first %d "
                "turns (era %s), so 'ok' is not demonstrated -- this is unknown, not a "
                "pass" % (n, era))
        else:
            out["why"] = (
                "no completion ceiling was hit, no storm, and every finish_reason is "
                "in-vocabulary, but no checkpoint in the first %d turns has "
                "answer_verified true (era %s; %d checkpoint(s) failed verification, "
                "parseable_answers=%d is structurally 0 on this shape). The answer "
                "contract is unproven inside the window, so this is unknown, not a pass"
                % (n, era, out["answer_verified_false"], out["parseable_answers"]))
        return out

    out.update(verdict="shape_ok", exit_code=EXIT_SHAPE_OK)
    out["why"] = (
        "no completion ceiling and no tool-call storm in %d turns, every stop signal "
        "in-vocabulary (read from %s), and the era %s answer contract confirmed by %d "
        "%s" % (n, ",".join(out["stop_signal_sources"]) or "none", era, needed, contract))
    return out


def resolve_rows(spec, arm=None):
    """Resolve --rows: an existing file, a glob, or a directory holding cells' row files."""
    path = Path(spec)
    if path.is_dir():
        pattern = "rows-cell-*%s*.jsonl" % (("*%s*" % arm) if arm else "")
        hits = sorted(globmod.glob(str(path / pattern)), key=lambda p: Path(p).stat().st_mtime)
        if not hits:
            cannot_run("no rows file matching %s in %s" % (pattern, path))
        return hits[-1]
    if any(ch in spec for ch in "*?["):
        hits = sorted(globmod.glob(spec), key=lambda p: Path(p).stat().st_mtime)
        if not hits:
            cannot_run("--rows glob matched nothing: %s" % spec)
        return hits[-1]
    if not path.is_file():
        cannot_run("--rows is not a file: %s" % spec)
    return str(path)


def effective_argv(launch, n):
    """The launch argv with ONLY the --turns window set to n. Refuses a multi-rep launch.

    The canary bounds the window; it does not own the arm, fixture, channel or budget.
    """
    argv = shlex.split(launch)
    if not argv:
        cannot_run("--launch is empty")
    for i, token in enumerate(argv):
        if token == "--turns" and i + 1 < len(argv):
            argv[i + 1] = str(n)
            break
        if token.startswith("--turns="):
            argv[i] = "--turns=%d" % n
            break
    else:
        argv += ["--turns", str(n)]
    for i, token in enumerate(argv):
        reps = None
        if token == "--reps" and i + 1 < len(argv):
            reps = argv[i + 1]
        elif token.startswith("--reps="):
            reps = token.split("=", 1)[1]
        if reps is not None and reps != "1":
            cannot_run(
                "--reps %s in the launch command. The canary runs cell 1 only (rep 1); a "
                "multi-rep launch is the tranche's shape, not the canary's, and would "
                "multiply the requests it spends." % reps)
    return argv


def run_live(argv, timeout):
    """Run the launch command. Returns (returncode, stderr_tail)."""
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        cannot_run("launch executable not found: %s" % exc)
    except subprocess.TimeoutExpired:
        return None, "launch timed out after %ss" % timeout
    return proc.returncode, (proc.stderr or "").strip().splitlines()[-8:]


def render(verdict):
    """One human line for a verdict; the JSON twin carries the detail."""
    bits = ["%s exit=%d" % (verdict.get("verdict"), verdict.get("exit_code", -1)),
            "arm=%s rep=%s n=%s turns=%s" % (verdict.get("arm"), verdict.get("rep"),
                                             verdict.get("n"), verdict.get("turns_observed"))]
    ev = verdict.get("evidence")
    if ev:
        bits.append("turn %s completion_tokens=%s max_tokens=%s wall_ms=%s stop_reason=%s (%s)"
                    % (ev.get("turn"), ev.get("completion_tokens"), ev.get("max_tokens"),
                       ev.get("wall_ms"), ev.get("stop_reason"), ev.get("trigger")))
    bits.append(verdict.get("why", ""))
    return " ".join(b for b in bits if b)


def main(argv=None):
    parser = CanaryParser(
        description="Pre-tranche canary: classify the first N turns of one arm's cell 1.")
    parser.add_argument("--rows", required=True,
                        help="rows JSONL file, glob, or a directory of rows-cell-*.jsonl")
    parser.add_argument("--turns", type=int, default=5, help="window size N (default 5)")
    parser.add_argument("--arm", default=None, help="arm to classify (default: first group)")
    parser.add_argument("--rep", type=int, default=None, help="rep within the arm (default 1st)")
    parser.add_argument("--launch", default=None,
                        help="cell-1 launch command; requires --live; SPENDS REAL REQUESTS")
    parser.add_argument("--live", action="store_true",
                        help="actually run --launch (offline replay never passes this)")
    parser.add_argument("--timeout", type=float, default=1800.0,
                        help="live launch timeout in seconds (default 1800)")
    parser.add_argument("--out", default=None, help="write the verdict JSON to this path")
    parser.add_argument("--json", action="store_true", help="print only the verdict JSON")
    args = parser.parse_args(argv)  # usage errors exit 3, see CanaryParser

    if args.turns < 1:
        parser.error("--turns must be >= 1 (the window is at least one turn)")
    if args.launch and not args.live:
        parser.error("--launch requires --live: replaying rows is the only zero-request mode")
    if args.live and not args.launch:
        parser.error("--live requires --launch")

    rc = None
    stderr_tail = None
    launch_argv = None
    if args.live:
        launch_argv = effective_argv(args.launch, args.turns)
        rc, stderr_tail = run_live(launch_argv, args.timeout)

    rows_path = resolve_rows(args.rows, arm=args.arm)
    try:
        rows = load_rows(rows_path)
    except SystemExit:
        raise
    verdict = classify(rows, n=args.turns, arm=args.arm, rep=args.rep)
    verdict["rows"] = rows_path
    verdict["mode"] = "live" if args.live else "replay"
    verdict["requests_spent"] = (args.turns if args.live else 0)
    if launch_argv is not None:
        verdict["launch_argv"] = launch_argv
        verdict["launch_rc"] = rc
        if stderr_tail:
            verdict["launch_stderr_tail"] = stderr_tail

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(verdict, indent=1, sort_keys=True) + "\n",
                                  encoding="utf-8")

    if args.json:
        print(json.dumps(verdict, indent=1, sort_keys=True))
    else:
        print(render(verdict))
    return verdict["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
