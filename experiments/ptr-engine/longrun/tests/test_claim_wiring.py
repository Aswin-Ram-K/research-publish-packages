#!/usr/bin/env python3
"""test_claim_wiring.py - WIRE-CLAIM-MODE: the claim decision has ONE author.

The module decision lives in `claim_mode.py` (HYPOTHESIS-SMOKE-MODE, settled). This
file tests only the WIRING: that `cell.py` asks the module (once) instead of parsing
the flag itself, that its decision reaches the run stage, and that the analyser
REFUSES a `claim="none"` cell by name instead of filtering it out of a group-by-arm.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
for path in (LONGRUN, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

import cell          # noqa: E402
import claim_mode    # noqa: E402
import analyze_stats  # noqa: E402


def _args(**kw):
    base = dict(fixture=os.path.join(LONGRUN, "fixtures", "LR-01.json"),
                arm="baseline", reps=1, turns=3, hypothesis=None,
                turn_wall_cap=180.0, runaway_turns=2, thinking="off",
                endpoint=None, out_dir=tempfile.mkdtemp(prefix="claimwire-"),
                temperature=0.0, budget_cap=12094, tools=None, fetch_policy=None)
    base.update(kw)
    return SimpleNamespace(**base)


def _fixture():
    return cell._load_fixture(os.path.join(LONGRUN, "fixtures", "LR-01.json"))


# --- (a) a DECLARED smoke reaches the run stage and stamps claim="none" ------------
def test_smoke_reaches_runner_path_and_stamps_claim_none():
    """--hypothesis smoke: allowed by G3, and the RUN STAGE carries claim="none"."""
    args = _args(hypothesis="smoke")
    cell._CLAIM_CACHE.clear()
    verdict = cell.eval_gate_prereg(args, _fixture())
    assert verdict["ok"] is True, verdict
    assert verdict["claim"] == "none", verdict
    assert verdict["comparison_eligible"] is False, verdict
    assert verdict["mode"] == "smoke", verdict
    # the operand validation still bites on a smoke cell (GATE-OPERAND-VALIDATION)
    bad = cell.eval_gate_prereg(_args(hypothesis="smoke", turns=0), _fixture())
    assert bad["ok"] is False, bad
    # ... and the resolution happened exactly ONCE for two calls
    assert len(cell._CLAIM_CACHE) == 1, cell._CLAIM_CACHE

    # the run stage: a fake runner (no request, no socket) proves the stamp travels
    fake = os.path.join(tempfile.mkdtemp(prefix="fakerunner-"), "fake_runner.py")
    with open(fake, "w", encoding="utf-8") as fh:
        fh.write("import sys\n"
                 "rows = sys.argv[sys.argv.index('--rows') + 1]\n"
                 "open(rows, 'a', encoding='utf-8').write('{\"arm\": \"baseline\"}\\n')\n"
                 "sys.exit(0)\n")
    rows_path = os.path.join(args.out_dir, "rows-cell-baseline-test.jsonl")
    real = cell.RUNNER
    cell.RUNNER = fake
    try:
        detail = cell.stage_run(args, rows_path)
    finally:
        cell.RUNNER = real
    assert detail["claim"] == {"claim": "none", "comparison_eligible": False,
                               "mode": "smoke"}, detail
    assert detail["claim_sidecar"], detail
    with open(detail["claim_sidecar"], encoding="utf-8") as fh:
        side = json.load(fh)
    assert side["claim"] == "none" and side["comparison_eligible"] is False, side
    assert side["resolver"] == "claim_mode.resolve_claim", side


# --- (b) no claim -> exit 12 with the module's sentence, verbatim -------------------
def test_no_claim_refused_exit_12_verbatim():
    args = _args(hypothesis=None)
    cell._CLAIM_CACHE.clear()
    verdict = cell.eval_gate_prereg(args, _fixture())
    assert verdict["ok"] is False, verdict
    exact = claim_mode.refusal_message(None)
    # the module's sentence is carried VERBATIM on the verdict and in the abort message;
    # the pre-wiring clause stays in front of it so G3's existing readers still key on it
    assert verdict["refusal_message"] == exact, verdict["refusal_message"]
    assert exact in verdict["consequence"], verdict["consequence"]
    try:
        cell._enforce(verdict, "3c/7 G3 prereg gate", 12)
    except cell.Abort as exc:
        assert exc.code == 12, exc.code
        assert exc.stage == "3c/7 G3 prereg gate", exc.stage
        assert exact in str(exc), str(exc)
        return
    raise AssertionError("no claim did not refuse")


# --- (c) an unknown value -> exit 12; an explicit "none" -> exit 12 -----------------
def test_unknown_and_explicit_none_refused_exit_12():
    for value in ("H9", "none", "", "   "):
        args = _args(hypothesis=value)
        cell._CLAIM_CACHE.clear()
        verdict = cell.eval_gate_prereg(args, _fixture())
        assert verdict["ok"] is False, (value, verdict)
        assert verdict.get("refusal_code") == 12, (value, verdict)
        try:
            cell._enforce(verdict, "3c/7 G3 prereg gate", 12)
        except cell.Abort as exc:
            assert exc.code == 12, (value, exc.code)
        else:
            raise AssertionError("value %r did not refuse" % (value,))


# --- H1|H2|H3 still behave as today (G3's n/reps check applies) -------------------
def test_hypothesis_claim_still_comparable():
    args = _args(hypothesis="H2")
    cell._CLAIM_CACHE.clear()
    verdict = cell.eval_gate_prereg(args, _fixture())
    assert verdict["ok"] is True, verdict
    assert verdict["claim"] == "H2" and verdict["comparison_eligible"] is True, verdict
    assert verdict["min_n"] if "min_n" in verdict else True


# --- (d) a claim="none" cell handed to the analyser is REFUSED BY NAME -------------
def _rows(claim="none", eligible=False, n=4):
    return [{"arm": "smoke", "rep": 0, "turn": t, "ttft_s": 0.1 + t / 100.0,
             "claim": claim, "comparison_eligible": eligible} for t in range(n)]


def test_analyser_refuses_claim_none_by_name():
    try:
        analyze_stats.require_comparable_claim(_rows(), "synthetic")
    except analyze_stats.IncomparableClaim as exc:
        text = str(exc)
        assert text.startswith("incomparable_claim"), text
        assert exc.kind == "incomparable_claim", exc.kind
    else:
        raise AssertionError("a claim=none cell was allowed into a comparison")

    # the sidecar path: rows WITHOUT claim fields are still refused when the run stage
    # declared claim=none beside them (a smoke cell must not read as legacy)
    tmp = tempfile.mkdtemp(prefix="claimside-")
    rows_path = os.path.join(tmp, "rows.jsonl")
    legacy = [{"arm": "baseline", "rep": 0, "turn": t, "ttft_s": 0.2} for t in range(3)]
    with open(rows_path, "w", encoding="utf-8") as fh:
        for row in legacy:
            fh.write(json.dumps(row) + "\n")
    analyze_stats.require_comparable_claim(legacy, "legacy-ok")     # no sidecar: allowed
    with open(analyze_stats.claim_sidecar_path(rows_path), "w", encoding="utf-8") as fh:
        json.dump({"claim": "none", "comparison_eligible": False, "mode": "smoke"}, fh)
    try:
        analyze_stats.require_comparable_claim(legacy, "sidecar", rows_path)
    except analyze_stats.IncomparableClaim as exc:
        assert str(exc).startswith("incomparable_claim"), str(exc)
    else:
        raise AssertionError("a declared claim=none run was pooled as legacy")

    # and analyze() itself records the refusal instead of computing a number
    report = analyze_stats.analyze(_rows() + [dict(r, arm="other") for r in _rows()])
    assert report["quantile_comparisons"], report
    for rec in report["quantile_comparisons"] + report["pairs"]:
        assert rec["refused_kind"] == "incomparable_claim", rec
        assert rec["refused"].startswith("incomparable_claim"), rec["refused"]
        assert rec.get("mcnemar") is None or rec["statistic"] == "quantile", rec


# --- (e) RED->GREEN: the pre-wiring default (absent -> H2) must fail (b) -----------
def test_red_green_prewiring_default_would_pass_a_silent_run():
    """The wiring's bite, stated as data: the OLD parse made silence declare H2.

    `test_no_claim_refused_exit_12_verbatim` is the green half; the red half is
    reproduced by `tests/red_claim_wiring.py`, which restores the inline parse
    (`absent -> H2`) and re-runs it. Here we only re-state the old rule so the two
    halves cannot drift apart.
    """
    # GATE-CHAIN-FIX D2 removed this: `absent --hypothesis` used to declare PARM-1's
    # primary (H2), so a silent run was ALLOWED and looked comparable.
    old_parse = lambda flag: (str(flag or "").strip().upper() or "H2")  # the deleted parse
    assert old_parse(None) == "H2"
    try:
        claim_mode.resolve_claim(None)
    except claim_mode.ClaimRefusal:
        return
    raise AssertionError("the module accepted silence")


TESTS = [test_smoke_reaches_runner_path_and_stamps_claim_none,
         test_no_claim_refused_exit_12_verbatim,
         test_unknown_and_explicit_none_refused_exit_12,
         test_hypothesis_claim_still_comparable,
         test_analyser_refuses_claim_none_by_name,
         test_red_green_prewiring_default_would_pass_a_silent_run]


def main():
    bad = 0
    for fn in TESTS:
        try:
            fn()
        except Exception as exc:                    # noqa: BLE001
            bad += 1
            print("FAIL %s: %s: %s" % (fn.__name__, type(exc).__name__, exc))
        else:
            print("GREEN %s" % fn.__name__)
    print("%d/%d GREEN" % (len(TESTS) - bad, len(TESTS)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
