#!/usr/bin/env python3
"""test_analyze_stats.py - EVAL-STATS guards: a number without n and an interval
must be unprintable.

Offline. Synthetic rows only: no request is issued and no existing row file,
fixture, grader, client or row writer is read or modified.

Green (all pass, exit 0):

    python3 experiments/ptr-engine/longrun/tests/test_analyze_stats.py
    python3 -m pytest experiments/ptr-engine/longrun/tests/test_analyze_stats.py -q

Red (the guard is not vacuous): point the suite at a mutated copy of the module
with ANALYZE_STATS_PATH and it must fail in exactly the place the mutation
removed - e.g. delete the `n * (1.0 - q) < TAIL_MIN` clause and case (c) fails;
delete the interval requirement in `render_estimate` and case (g) fails.

Set EVAL_STATS_VERBOSE=1 to see every assertion's measured values.
"""
from __future__ import annotations

import importlib.util
import io
import json
import math
import os
import sys
import tempfile
import traceback
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
MODULE_PATH = os.environ.get(
    "ANALYZE_STATS_PATH", os.path.join(LONGRUN, "analyze_stats.py"))

_spec = importlib.util.spec_from_file_location("analyze_stats", MODULE_PATH)
stats = importlib.util.module_from_spec(_spec)
sys.modules["analyze_stats"] = stats
_spec.loader.exec_module(stats)

VERBOSE = os.environ.get("EVAL_STATS_VERBOSE") == "1"


def _close(a, b, tol=1e-4):
    return abs(a - b) <= tol


def _rows(n, base=100.0, step=3.0, arm="pointer-stable", passed_every=3):
    """Synthetic rows in the old shape: no new contract fields at all."""
    return [
        {"arm": arm, "turn": i, "ttft_ms": base + step * i,
         "passed": (i % passed_every == 0)}
        for i in range(n)
    ]


# (a) Wilson interval at the boundaries: non-degenerate, known values ---------
def test_wilson_bounds_known():
    point, lo, hi = stats.wilson_ci(3, 3)
    assert point == 1.0, point
    assert hi == 1.0, hi
    # Wilson 95 % upper half for 3/3: n/(n+z^2) with z=1.959964 -> 0.43850
    assert _close(lo, 0.4385029682), lo
    assert hi - lo > 0.5, (lo, hi)  # not a zero-width interval
    if VERBOSE:
        print("    wilson 3/3 ->", (point, lo, hi))

    point0, lo0, hi0 = stats.wilson_ci(0, 3)
    assert point0 == 0.0, point0
    assert lo0 == 0.0, lo0
    assert _close(hi0, 0.5614970318), hi0
    assert hi0 - lo0 > 0.5, (lo0, hi0)
    if VERBOSE:
        print("    wilson 0/3 ->", (point0, lo0, hi0))


# (b) bootstrap quantile CI: known p95, brackets the point, width shrinks ------
def _grid(n):
    """n points spanning [0,100] exactly: for U(0,100) the true p95 is 95.0."""
    return [100.0 * i / (n - 1) for i in range(n)]


def test_quantile_ci_known_p95_and_width():
    vals100 = _grid(100)
    st = {}
    point, lo, hi, n = stats.quantile_ci(vals100, 0.95, resamples=2000, stats=st)
    assert n == 100, n
    assert _close(point, 95.0, 0.2), point  # true p95 of the [0,100] grid
    assert lo <= point <= hi, (lo, point, hi)
    assert st["dropped_null"] == 0, st
    assert st["rank_span"] == (91, 100), st["rank_span"]
    width100 = hi - lo
    assert width100 > 0, width100
    if VERBOSE:
        print("    n=100 p95 ->", (point, lo, hi, n), "width", round(width100, 3))

    vals400 = _grid(400)
    p4, l4, h4, n4 = stats.quantile_ci(vals400, 0.95, resamples=2000,
                                       seed=stats.SEED)
    assert n4 == 400, n4
    assert _close(p4, 95.0, 0.2), p4
    assert l4 <= p4 <= h4, (l4, p4, h4)
    width400 = h4 - l4
    # 4x the sample must narrow the p95 interval (approx. 1/sqrt(n))
    assert width400 < width100, (width100, width400)
    if VERBOSE:
        print("    n=400 p95 ->", (p4, l4, h4), "width", round(width400, 3))
    assert _close(width400 / width100, 0.5, 0.25), (width100, width400)


# (c) refusal at n=48 for p95, with the exact message -------------------------
def test_insufficient_samples_at_48_exact_message():
    declared = (
        "refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 "
        "(p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60"
    )
    for q in (0.95,):
        try:
            stats.quantile_ci([float(i) for i in range(1, 49)], q)
        except stats.InsufficientSamples as exc:
            assert str(exc) == declared, "\n got: %r\nwant: %r" % (str(exc), declared)
        else:
            raise AssertionError("quantile_ci accepted n=48 for q=%r" % (q,))
    # the first admissible p95 is n=60 (60 * 0.05 = 3.0 >= TAIL_MIN)
    assert stats.min_n_for(0.95) == 60, stats.min_n_for(0.95)
    p, lo, hi, n = stats.quantile_ci([float(i) for i in range(1, 61)], 0.95,
                                     resamples=2000)
    assert n == 60, n
    assert lo <= p <= hi, (lo, p, hi)
    if VERBOSE:
        print("    n=60 p95 accepted ->", (p, lo, hi, n))


# (d) exact McNemar: p=0.25 at b=3,c=0, refusal at b=2,c=1 -------------------
def test_mcnemar_exact_025_and_refusals():
    assert stats.mcnemar_p(3, 0) == 0.25, stats.mcnemar_p(3, 0)
    # b=3, c=0 is the survey arithmetic: 2 * C(3,0) / 2^3 = 0.25. It is also
    # below the licensing floor, so mcnemar_exact REFUSES while carrying 0.25.
    pairs_3 = [(False, True)] * 3
    try:
        stats.mcnemar_exact(pairs_3)
    except stats.RefusedTest as exc:
        assert exc.b == 3 and exc.c == 0, (exc.b, exc.c)
        assert _close(exc.p, 0.25, 1e-12), exc.p
        assert "3" in str(exc), str(exc)
    else:
        raise AssertionError("mcnemar_exact licensed 3 discordant pairs")

    try:
        stats.mcnemar_exact([(False, True)] * 2 + [(True, False)])
    except stats.RefusedTest as exc:
        assert (exc.b, exc.c, exc.discordant) == (2, 1, 3), (exc.b, exc.c)
    else:
        raise AssertionError("mcnemar_exact licensed b=2,c=1")

    # 6 discordant pairs IS licensed, and p=0.03125 clears 0.05
    b, c, p = stats.mcnemar_exact([(False, True)] * 6)
    assert (b, c) == (6, 0), (b, c)
    assert _close(p, 0.03125, 1e-12), p
    if VERBOSE:
        print("    mcnemar p(3,0)=%r refused; p(6,0)=%r licensed" %
              (stats.mcnemar_p(3, 0), p))


# (e) null ttft is dropped and counted, never coerced to zero -----------------
def test_null_ttft_dropped_and_counted():
    rows = _rows(30)
    for i in (0, 7, 19):
        rows[i]["ttft_ms"] = None
    rows[5]["ttft_ms"] = float("nan")
    vals, nulls, unavailable = stats.ttft_values(rows)
    assert len(vals) == 26, len(vals)
    assert nulls == 4, nulls
    assert unavailable == 0, unavailable
    # an unavailable first delta is not a zero either, even if a fallback
    # number sits in ttft_ms
    rows[6]["ttft_source"] = "unavailable"
    vals, nulls, unavailable = stats.ttft_values(rows)
    assert len(vals) == 25, len(vals)
    assert unavailable == 1, unavailable

    # quantile_ci itself drops nulls in the column it is handed, and counts them
    # (source-based exclusion happens in ttft_values, above)
    raw = list(vals) + [None] * 4
    st = {}
    point, lo, hi, n = stats.quantile_ci(raw, 0.5, resamples=1000, stats=st)
    assert n == 25, n
    assert st["dropped_null"] == 4, st
    assert point > 50.0, point  # zeros would drag the median down towards 0
    if VERBOSE:
        print("    dropped nulls=%d unavailable=%d n=%d median=%.2f" %
              (st["dropped_null"], unavailable, n, point))


# (f) a row file missing every new field still analyses ----------------------
def test_old_row_file_without_new_fields():
    rows = _rows(60)
    assert set(rows[0]) == {"arm", "turn", "ttft_ms", "passed"}, rows[0]
    tmpdir = tempfile.mkdtemp(prefix="evalstats-")
    path = os.path.join(tmpdir, "old-rows.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = stats.main(["--rows", path, "--resamples", "800"])
    out = buf.getvalue()
    assert rc == 0, rc
    assert "ttft_p95 n=60" in out, out
    assert "[" in out and "]" in out, out  # the interval is printed
    assert "accuracy" in out and "wilson95" in out, out
    if VERBOSE:
        print("    CLI output:\n" + out)


# (g) render_estimate refuses a bare number ----------------------------------
def test_render_estimate_refuses_bare():
    line = stats.render_estimate("ttft_p95", 95.0, 91.0, 99.0, 60, unit="ms")
    assert "n=60" in line and "[" in line, line
    for bad in ((95.0, None, 99.0, 60), (95.0, 91.0, None, 60),
                (95.0, 91.0, 99.0, 0), (95.0, 91.0, 99.0, None)):
        try:
            stats.render_estimate("ttft_p95", *bad)
        except stats.BareMetricError:
            pass
        else:
            raise AssertionError("render_estimate printed %r" % (bad,))
    if VERBOSE:
        print("    ", line)


# (h) pass@k guard and paired_by_turn bookkeeping ----------------------------
def test_pass_hat_k_and_paired_by_turn():
    assert _close(stats.pass_hat_k(10, 3, 1), 0.3, 1e-12)
    assert stats.pass_hat_k(10, 0, 5) == 0.0
    assert stats.pass_hat_k(10, 10, 5) == 1.0
    # n - c < k is 1.0 by definition (no incorrect sample can fill a slot)
    assert stats.pass_hat_k(10, 9, 5) == 1.0
    for args in ((10, 3, 0), (10, 11, 1), (0, 0, 1)):
        try:
            stats.pass_hat_k(*args)
        except (stats.InsufficientSamples, ValueError):
            pass
        else:
            raise AssertionError("pass_hat_k accepted %r" % (args,))

    a = [{"turn_index": 1, "passed": True}, {"turn_index": 2, "passed": False},
         {"passed": True}]
    b = [{"turn_index": 1, "passed": False}, {"turn_index": 2, "passed": False},
         {"turn_index": 3, "passed": True}]
    pairs, pst = stats.paired_by_turn(a, b)
    assert pst["formed"] == 2, pst
    assert pst["dropped_missing_key"] == 1, pst
    assert pst["dropped_unpaired"] == 1, pst  # turn 3 exists only in arm b
    assert [k for k, _x, _y in pairs] == [1, 2], pairs
    if VERBOSE:
        print("    paired:", pst)


def _run_all():
    tests = sorted((name, fn) for name, fn in globals().items()
                   if name.startswith("test_") and callable(fn))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print("PASS %s" % name)
        except Exception:
            failures += 1
            print("FAIL %s" % name)
            traceback.print_exc()
    print("\n%d/%d passed (module: %s)" % (len(tests) - failures, len(tests),
                                           MODULE_PATH))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_all())
