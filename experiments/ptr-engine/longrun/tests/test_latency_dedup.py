#!/usr/bin/env python3
"""test_latency_dedup.py - the de-duplication rule must not lower the p95 floor.

Cases
-----
(a) a synthetic grid whose duplicate rows push n below 60  => p95 REFUSED by name
(b) the same grid without duplicates                      => p95 produced WITH interval and n
(c) a legacy-schema file (no content_sha256, one-second ts_utc) => rule NOT applied
(d) red->green: with de-duplication disabled, case (a) must FAIL (the refusal
    disappears and a duplicate-inflated p95 comes back). Shown by running this
    file with LATENCY_DEDUP=off, then restored by running it normally.

Offline. Synthetic rows only: no request, no network, and no existing row file,
grade file, TVS / ledger artefact or report is read or modified.

    python3 experiments/ptr-engine/longrun/tests/test_latency_dedup.py
    LATENCY_DEDUP=off python3 experiments/ptr-engine/longrun/tests/test_latency_dedup.py   # must FAIL
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PTR = os.path.dirname(os.path.dirname(HERE))            # experiments/ptr-engine
TOOLS = os.path.join(PTR, "tools")
ANALYZER = os.path.join(PTR, "longrun", "analyze_stats.py")
REPORT_TOOL = os.environ.get("LATENCY_REPORT_PATH",
                             os.path.join(TOOLS, "latency_report.py"))

# The red->green switch. Default ON; LATENCY_DEDUP=off disables rule R only.
DEDUP_ENABLED = os.environ.get("LATENCY_DEDUP", "on") != "off"

FLOOR95 = 60          # analyze_stats.min_n_for(0.95); asserted from the module below


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


stats = _load("analyze_stats", ANALYZER)
report_tool = _load("latency_report", REPORT_TOOL)


def _row(i, ttft=None, duplicated=False):
    """A row in the tool-era shape: content_sha256 + millisecond ts."""
    if ttft is None:
        ttft = 100.0 + i
    return {
        "arm": "pointer-stable", "kind": "turn" if not duplicated else "tool-followup",
        "ts": "2026-10-26T12:00:%02d.%03dZ" % (i // 1000, i % 1000),
        "content_sha256": "sha-%d" % i,
        "prompt_tokens": 1000 + i, "completion_tokens": 10 + (i % 7),
        "ttft_ms": ttft, "ttft_source": "first_delta",
        "latency_s": 1.0, "rep": 0, "turn": i % 12,
    }


def grid(n_unique=51, n_dupes=17):
    """51 distinct measurements + 17 second writes of them = 68 rows."""
    rows = [_row(i) for i in range(n_unique)]
    for j in range(n_dupes):
        base = _row(j, duplicated=True)
        base["ts"] = rows[j]["ts"]      # same millisecond ts
        rows.append(base)               # same sha / tokens -> rule R duplicate
    return rows


def p95_of(rows):
    out = stats.analyze(rows, resamples=2000)
    return out["arms"]["pointer-stable"]["p95"]


def check_floor():
    assert stats.min_n_for(0.95) == FLOOR95, \
        "the analyser's p95 floor moved: %r" % (stats.min_n_for(0.95),)


def case_a_refusal():
    """(a) duplicates push n below 60 => p95 refused BY NAME, no bare number."""
    rows = grid()
    kept, groups, excess, status = report_tool.dedupe_rows(
        rows, enabled=DEDUP_ENABLED)
    assert status == "decided", status
    p95 = p95_of(kept)
    # THE guard: with rule R applied, n is 51 and the analyser must refuse.
    assert "point" not in p95, "p95 was produced at n=%r after de-dup: %r" % (p95.get("n"), p95)
    assert "refused" in p95, p95
    assert p95["n"] == 51, p95
    assert (groups, excess) == (17, 17), (groups, excess)
    assert len(kept) == 51, len(kept)
    msg = p95["refused"]
    assert "refusing p95 at n=51" in msg, msg
    assert "minimum n for p95 is 60" in msg, msg
    # the published-defect sentence: the refusal names the p95 and the floor
    return msg


def case_b_interval():
    """(b) the same grid without duplicates => p95 with an interval and n."""
    rows = grid(n_unique=68, n_dupes=0)
    kept, groups, excess, status = report_tool.dedupe_rows(rows)
    assert status == "decided" and excess == 0 and len(kept) == 68
    p95 = p95_of(kept)
    assert "refused" not in p95, p95
    for key in ("point", "lo", "hi", "n"):
        assert p95.get(key) is not None, (key, p95)
    assert p95["n"] == 68, p95
    assert p95["lo"] <= p95["point"] <= p95["hi"], p95
    return "p95 %.2f [%.2f, %.2f] n=%d" % (p95["point"], p95["lo"], p95["hi"], p95["n"])


def case_c_legacy():
    """(c) a legacy-schema file is NOT de-duplicated."""
    rows = []
    for rep in range(3):
        for turn in range(4):
            rows.append({
                "arm": "pointer-stable", "kind": "turn",
                "ts_utc": "2026-10-26T05:49:00Z",   # one-second resolution
                "content_sha256": None,             # field absent on this schema
                "prompt_tokens": None, "completion_tokens": None,
                "http_status": 400, "rep": rep, "turn": turn,
                "ttft_ms": 100.0 + rep * 10 + turn,
            })
    kept, groups, excess, status = report_tool.dedupe_rows(rows)
    assert status == "not_applicable", status
    assert len(kept) == len(rows) == 12, (len(kept), len(rows))
    assert (groups, excess) == (0, 0), (groups, excess)
    # and the lesson the boundary encodes: the literal tuple WOULD collapse them
    _k, lit_groups, lit_excess = report_tool.dedupe(rows)
    assert (lit_groups, lit_excess) == (1, 11), (lit_groups, lit_excess)
    assert report_tool.rule_status(rows) == "not_applicable"
    return "12 rows kept, literal R would have removed 11"


def case_d_missing_sha_is_undecidable():
    """A file that merely lacks content_sha256 never gets R applied."""
    rows = [_row(i) for i in range(3)]
    for r in rows:
        r.pop("content_sha256")
    kept, _g, excess, status = report_tool.dedupe_rows(rows)
    assert status == "not_applicable"
    assert excess == 0 and len(kept) == 3


def main():
    check_floor()
    results = {}
    results["a_refusal"] = case_a_refusal()
    results["b_interval"] = case_b_interval()
    results["c_legacy"] = case_c_legacy()
    case_d_missing_sha_is_undecidable()
    for name in ("a_refusal", "b_interval", "c_legacy"):
        print("PASS %-12s %s" % (name, results[name]))
    print("PASS d_missing_sha not_applicable, excess 0")
    print("dedupe_enabled=%s floor95=%d rows_file='legacy test rows only'"
          % (DEDUP_ENABLED, FLOOR95))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
