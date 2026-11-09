#!/usr/bin/env python3
"""test_canary_claim_mode.py - CANARY-CLAIM-MODE: a 12-turn canary is plumbing.

OFFLINE. Zero requests, zero sockets, no live cell. Every row here is produced by the
runner's own `make_row` from a synthetic response, so what is asserted is the row
contract (`claim`, `comparison_eligible`) and the analyser's refusal, not a number.

The hazard this pins: a canary launched with `--hypothesis H2` writes `claim: "H2"`,
`comparison_eligible: true` on 48 ungraded rows, which the analyser would pool with the
arm it is supposed to gate. `--hypothesis smoke` (alias `plumbing`) writes `claim: "none"`
and `analyze_stats` refuses those rows BY NAME (`incomparable_claim`).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.join(os.path.dirname(HERE), "experiments", "ptr-engine", "longrun")
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import analyze_stats  # noqa: E402
import claim_mode     # noqa: E402
import run_longrun    # noqa: E402

FX = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")
ARM = "pointer-stable"


def _cfg(flag):
    with tempfile.TemporaryDirectory(prefix="canaryclaim-") as tmp:
        argv = ["--fixture", FX, "--arms", ARM, "--rows",
                os.path.join(tmp, "rows.jsonl"), "--max-tokens", "4096",
                "--thinking", "off", "--turn-wall-cap", "180",
                "--runaway-turns", "2", "--tools", "read_file"]
        if flag is not None:
            argv += ["--claim-mode", flag]
        cfg = run_longrun.build_parser().parse_args(argv)
    cfg.claim = claim_mode.resolve_claim(flag) if flag is not None else None
    return cfg


def _resp():
    return {"cached_tokens": 10, "raw_cached": 10, "prompt_tokens": 100,
            "content_raw": "ANSWER: NUM 7", "reasoning": "", "ttft_ms": 120.0,
            "ttft_s": 0.12, "latency_s": 1.5, "completion_tokens": 12,
            "content": "ANSWER: NUM 7", "token_source": "usage", "max_tokens": 4096,
            "usage_missing": False, "stop_reason": "stop",
            "request_sha256": "a" * 64, "request_identity_complete": True,
            "finish_reason": "stop", "finish_reasons": ["stop"],
            "first_token_kind": "content", "content_source": "stream",
            "ttft_source": "measured", "cached_source": "usage", "wall_ms": 1500.0,
            "engine_metrics_before": None, "engine_metrics_after": None}


def _rows(flag, turns=12):
    cfg = _cfg(flag)
    fixture = run_longrun.load_fixture(FX)
    return [run_longrun.make_row(cfg, fixture, ARM, 1, "canary-smoke", t,
                                 _resp(), "ANSWER: NUM 7", "turn-initial",
                                 "0" * 64, {}) for t in range(1, turns + 1)]


def test_resolver_table():
    """The three accepted forms, and the refusals, each with its named shape."""
    for flag in ("smoke", "plumbing"):
        rec = claim_mode.resolve_claim(flag)
        assert (rec.mode, rec.claim, rec.comparison_eligible) == ("smoke", "none", False)
    for flag in ("H1", "h2", "H3"):
        rec = claim_mode.resolve_claim(flag)
        assert rec.claim == flag.upper() and rec.comparison_eligible is True
    for bad in (None, "", "  ", "none", "plumbingish", "H9"):
        try:
            claim_mode.resolve_claim(bad)
        except claim_mode.ClaimRefusal as exc:
            assert exc.code == 12 and exc.stage == "3c/7 G3 prereg gate"
        else:
            raise AssertionError("resolve_claim(%r) did not refuse" % (bad,))


def test_twelve_turn_smoke_rows_are_not_eligible():
    """A 12-turn canary's rows all say claim=none / comparison_eligible=false."""
    rows = _rows("smoke")
    assert len(rows) == 12
    assert {(r["claim"], r["comparison_eligible"]) for r in rows} == {("none", False)}
    assert [r["turn"] for r in rows] == list(range(1, 13))


def test_analyser_refuses_smoke_rows_by_name():
    """`require_comparable_claim` raises `incomparable_claim` naming the canary's rows."""
    rows = _rows("smoke")
    try:
        analyze_stats.require_comparable_claim(rows, "canary")
    except analyze_stats.IncomparableClaim as exc:
        text = str(exc)
        assert text.startswith("incomparable_claim"), text[:200]
        assert "claim_free" in text, text[:400]
        assert "turn=12" in text, text[:1200]
    else:
        raise AssertionError("a claim=none canary was accepted into a comparison")


def test_h2_flip_is_accepted_that_is_the_whole_difference():
    """The SAME rows with claim=H2 / eligible=true pass: the marker is what is refused."""
    rows = _rows("H2")
    assert {(r["claim"], r["comparison_eligible"]) for r in rows} == {("H2", True)}
    got = analyze_stats.require_comparable_claim(rows, "canary-h2")
    assert got["legacy_rows"] == 0


def test_cell_forwards_claim_mode_to_the_runner():
    """PIN: `cell.py` passes the resolved claim to run_longrun.py (no wiring needed)."""
    src = open(os.path.join(LONGRUN, "cell.py"), encoding="utf-8").read()
    assert ('argv += ["--claim-mode", "smoke" if _claim_rec.is_smoke '
            'else _claim_rec.claim]') in src
    # and the canary launcher's cell argv is the place the wrong value is written
    launcher = open(os.path.join(LONGRUN, "..", "tools", "run_a_star.py"),
                    encoding="utf-8").read()
    assert '"--hypothesis", "H2"' in launcher
