#!/usr/bin/env python3
"""test_claim_rows.py - CLAIM-ROW-STAMP: the claim reaches EVERY row the runner writes.

`claim_mode` owns the decision. `run_longrun.py` resolves `--claim-mode` ONCE and
`make_row` stamps the two fields on every row literal it builds. This file tests the
ROW (not a document): a smoke run's rows, an H2 run's rows, a failure row, the omitted
flag's exit 12 with the module's sentence verbatim, the analyser's refusal on a
two-cell corpus, and a red->green that deletes the stamp from make_row.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
for path in (LONGRUN, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

import claim_mode   # noqa: E402
import run_longrun  # noqa: E402

# the built runtime fixture the neighbouring row tests use (fixtures/LR-01.json is a
# STUB by design; the real tree is generated from fixtures-spec/LR-01.spec.json)
FX = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")
ARM = "transcript-grow"
# a corpus-shaped target OUTSIDE the OS temp dir; the omitted-flag run refuses before
# writing it, so this path is never created
CORPUS_ROWS = os.path.join(LONGRUN, "..", "measure", "rows-claimrowstest.jsonl")
KINDS = ("turn-initial", "turn", "tool-followup")


def _cfg(flag):
    argv = ["--fixture", FX, "--arms", ARM, "--rows",
            os.path.join(tempfile.mkdtemp(prefix="claimrows-"), "rows.jsonl")]
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


def _row(cfg, kind, resp=True):
    fixture = run_longrun.load_fixture(FX)
    return run_longrun.make_row(cfg, fixture, ARM, 1, "rid-claimrows", 1,
                                _resp() if resp else None, "ANSWER: NUM 7", kind,
                                "0" * 64, {})


def test_smoke_rows_all_carry_claim_none():
    """--claim-mode smoke: EVERY kind of row says claim=none / comparison_eligible=false."""
    cfg = _cfg("smoke")
    for kind in KINDS:
        row = _row(cfg, kind)
        assert row["claim"] == "none", (kind, row.get("claim"))
        assert row["comparison_eligible"] is False, (kind, row.get("comparison_eligible"))
    failed = _row(cfg, "turn", resp=False)          # a FAILURE row is stamped too
    assert failed["claim"] == "none", failed.get("claim")
    assert failed["comparison_eligible"] is False, failed.get("comparison_eligible")
    # plumbing is the module's synonym and lands on the same shape
    plumb = _cfg("plumbing")
    assert _row(plumb, "turn")["claim"] == "none"


def test_h2_rows_comparable():
    cfg = _cfg("H2")
    for kind in KINDS:
        row = _row(cfg, kind)
        assert row["claim"] == "H2", (kind, row.get("claim"))
        assert row["comparison_eligible"] is True, (kind, row.get("comparison_eligible"))


def test_omitted_flag_exit_12_verbatim():
    """No --claim-mode, corpus-shaped rows target -> exit 12, module sentence verbatim."""
    proc = subprocess.run([sys.executable, os.path.join(LONGRUN, "run_longrun.py"),
                           "--fixture", FX, "--arms", ARM, "--rows", CORPUS_ROWS],
                          cwd=LONGRUN, capture_output=True, text=True, timeout=120)
    exact = claim_mode.refusal_message(None)
    assert proc.returncode == 12, (proc.returncode, proc.stderr[-1200:])
    assert exact in proc.stderr, proc.stderr[-2000:]
    assert not os.path.exists(CORPUS_ROWS), "a refused run wrote its rows target"


def test_two_cell_corpus_refused_by_name_in_one_call():
    """Comparable cell + smoke cell side by side: the analyser refuses, naming the smoke one."""
    comparable = [{"cell": "cmp-1", "arm": "transcript-grow", "rep": 1, "turn": i,
                   "claim": "H2", "comparison_eligible": True} for i in (1, 2, 3)]
    smoke = [{"cell": "smoke-1", "arm": "transcript-grow", "rep": 1, "turn": 1,
              "claim": "none", "comparison_eligible": False}]
    try:
        claim_mode.assert_comparable(comparable + smoke, "synthetic corpus")
    except claim_mode.IncomparableClaim as exc:
        text = str(exc)
        assert text.startswith("incomparable_claim"), text[:200]
        assert "cell=smoke-1" in text, text[:400]
        assert "claim_free" in text, text[:400]
    else:
        raise AssertionError("a smoke cell was pooled with a comparable cell")
    # and rows with NO claim fields are legacy, never claim-free -> still comparable
    legacy = [{"arm": "x", "rep": 1, "turn": 1}]
    got = claim_mode.assert_comparable(legacy)
    assert got["legacy_rows"] == 1, got


def test_red_green_stamp_removed_from_make_row():
    """RED: a /tmp copy of run_longrun.py with the stamp deleted fails, naming the field."""
    src = open(os.path.join(LONGRUN, "run_longrun.py"), encoding="utf-8").read()
    stamp = ('    claim_fields = (claim_mode.row_fields(cfg.claim)\n'
             '                    if getattr(cfg, "claim", None)\n'
             '                    else {"claim": claim_mode.CLAIM_NONE,\n'
             '                          "comparison_eligible": False})\n')
    assert stamp in src, "the stamp block moved; the red half no longer targets it"
    mutant = src.replace(stamp, "", 1).replace('"arm": arm, **claim_fields,',
                                               '"arm": arm,', 1)
    tmp = tempfile.mkdtemp(prefix="claimrows-red-")
    path = os.path.join(tmp, "run_longrun.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(mutant)
    spec = importlib.util.spec_from_file_location("run_longrun_unstamped", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg = mod.build_parser().parse_args(["--fixture", FX, "--arms", ARM,
                                         "--rows", os.path.join(tmp, "rows.jsonl")])
    cfg.claim = claim_mode.resolve_claim("smoke")
    fixture = mod.load_fixture(FX)
    row = mod.make_row(cfg, fixture, ARM, 1, "rid-red", 1, _resp(), "x", "turn",
                       "0" * 64, {})
    missing = [f for f in claim_mode.ROW_FIELDS if f not in row]
    assert missing == ["claim", "comparison_eligible"], (
        "RED was not red for the stamp: missing fields were %r" % (missing,))
    # GREEN half: the in-tree make_row carries both
    green = _row(_cfg("smoke"), "turn")
    assert [f for f in claim_mode.ROW_FIELDS if f not in green] == [], green.keys()


TESTS = [test_smoke_rows_all_carry_claim_none, test_h2_rows_comparable,
         test_omitted_flag_exit_12_verbatim,
         test_two_cell_corpus_refused_by_name_in_one_call,
         test_red_green_stamp_removed_from_make_row]


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
