#!/usr/bin/env python3
"""test_analyze_provenance.py - the provenance refusal actually bites comparisons.

What this suite pins (WIRE-PROVENANCE-INTO-STATS):

  (a) two cells differing in `fixture_sha256`  -> `incomparable_provenance` naming
      `fixture_sha256`, and NO interval is printed on that comparison;
  (b) differing `thinking`                     -> the same named refusal;
  (c) differing only in `arm`, same fixture    -> the comparison PROCEEDS and prints
      both intervals (the arm is what a comparison is for);
  (d) `--assume-comparable`                    -> proceeds AND records
      `provenance_override: true` + the differing fields in stdout and in --json;
  (e) the refusal cannot be bypassed by calling McNemar instead of the quantile
      path: `compare()` gates before it dispatches on the statistic;
  (f) red->green: delete the `same_provenance` call inside `compare()` and (a) must
      go RED. The mutation is built here, in a temp copy, so the committed module is
      never touched.

Offline: synthetic rows only. No request is issued; no existing row file, fixture,
grader, client or row writer is read or modified.

Green:

    python3 experiments/ptr-engine/longrun/tests/test_analyze_provenance.py
    python3 -m pytest experiments/ptr-engine/longrun/tests/test_analyze_provenance.py -q
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import traceback
from contextlib import redirect_stdout
import io

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE = os.path.dirname(LONGRUN)
TOOLS = os.path.join(ENGINE, "tools")
MODULE_PATH = os.path.join(LONGRUN, "analyze_stats.py")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


stats = _load(MODULE_PATH, "analyze_stats")

FIX_A = "a" * 64
FIX_B = "b" * 64


def _cell(**over):
    cell = {"fixture_sha256": FIX_A, "model": "occamy-test",
            "thinking": "off", "tools_mode": "off"}
    cell.update(over)
    return cell


def _rows(arm, n=48, base=100.0, step=2.0, fixture=FIX_A, thinking="off",
          with_model=True):
    rows = []
    for i in range(n):
        row = {"arm": arm, "turn": i, "ttft_ms": base + step * i,
               "passed": (i % 3 == 0), "fixture_sha256": fixture,
               "thinking": thinking}
        if with_model:
            row["model"] = "occamy-test"
            row["tools_mode"] = "off"
        rows.append(row)
    return rows


def _run_cli(argv):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            stats.main(argv)
        code = 0
    except SystemExit as exc:                      # argparse / explicit exit
        code = int(exc.code or 0)
    return code, buf.getvalue()


def _write_rows(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


# --- (a) differing fixture_sha256 ------------------------------------------
def test_a_differing_fixture_refuses_and_names_the_field():
    cell_a = _cell()
    cell_b = _cell(fixture_sha256=FIX_B)
    try:
        stats.compare(cell_a, cell_b, statistic="quantile", q=0.50,
                      values_a=[1.0] * 48, values_b=[2.0] * 48, label="a vs b")
    except stats.IncomparableProvenance as exc:
        assert exc.differing == ["fixture_sha256"], exc.differing
        assert str(exc).startswith("incomparable_provenance"), str(exc)
        assert exc.kind == "incomparable_provenance"
        assert "fixture_sha256" in str(exc)
        assert "no interval" in str(exc).lower(), str(exc)
        return
    raise AssertionError("compare() computed a comparison across two fixtures")


def test_a_cli_prints_no_interval_for_the_refused_comparison():
    with tempfile.TemporaryDirectory() as tmp:
        rows = _rows("arm-a", fixture=FIX_A) + _rows("arm-b", fixture=FIX_B,
                                                     base=200.0)
        path = os.path.join(tmp, "rows.jsonl")
        hour_json = os.path.join(tmp, "out.json")
        _write_rows(path, rows)
        code, out = _run_cli(["--rows", path, "--json", hour_json])
        assert code == 0, code
        assert "incomparable_provenance" in out, out
        refused = [ln for ln in out.splitlines() if "incomparable_provenance" in ln]
        assert refused, out
        for line in refused:
            assert "[" not in line.split("refusing")[0], (
                "a refused comparison printed an interval: %r" % line)
        assert "fixture_sha256" in out, out
        with open(hour_json, encoding="utf-8") as fh:
            doc = json.load(fh)
        assert doc["provenance_override"] is False, doc["provenance_override"]
        qcs = doc["quantile_comparisons"]
        assert qcs, "no quantile comparisons recorded"
        assert all(qc["incomparable_provenance"] for qc in qcs), qcs
        assert all("a" not in qc or "point" not in qc["a"] for qc in qcs), qcs


# --- (b) differing thinking -------------------------------------------------
def test_b_differing_thinking_refuses():
    try:
        stats.compare(_cell(), _cell(thinking="auto"), statistic="quantile",
                      q=0.50, values_a=[1.0] * 48, values_b=[1.0] * 48)
    except stats.IncomparableProvenance as exc:
        assert exc.differing == ["thinking"], exc.differing
        assert str(exc).startswith("incomparable_provenance")
        return
    raise AssertionError("compare() ignored a thinking mismatch")


def test_b_cli_refuses_differing_thinking():
    with tempfile.TemporaryDirectory() as tmp:
        rows = _rows("arm-a", thinking="off") + _rows("arm-b", thinking="auto",
                                                      base=200.0)
        path = os.path.join(tmp, "rows.jsonl")
        _write_rows(path, rows)
        code, out = _run_cli(["--rows", path])
        assert code == 0, code
        assert "incomparable_provenance" in out, out
        assert "thinking" in out, out


# --- (c) differing only in `arm` -------------------------------------------
def test_c_arm_difference_alone_is_comparable_and_prints_an_interval():
    values_a = [100.0 + i for i in range(48)]
    values_b = [200.0 + i for i in range(48)]
    rec = stats.compare(_cell(arm="arm-a"), _cell(arm="arm-b"),
                        statistic="quantile", q=0.50,
                        values_a=values_a, values_b=values_b, label="c")
    assert rec["refused"] is None, rec
    assert rec["provenance"]["differing"] == [], rec["provenance"]
    assert rec["provenance_override"] is False
    assert rec["a"]["n"] == 48 and rec["b"]["n"] == 48
    lines = stats._format_quantile_comparison(dict(rec, quantile="p50",
                                                   arm_a="arm-a",
                                                   arm_b="arm-b"))
    text = "\n".join(lines)
    assert "ms [" in text, text                 # both intervals rendered
    assert "REFUSED" not in text, text
    assert "intervals_overlap = no" in text, text


# --- (d) the loud override -------------------------------------------------
def test_d_assume_comparable_proceeds_and_records_the_override():
    rec = stats.compare(_cell(), _cell(fixture_sha256=FIX_B),
                        statistic="quantile", q=0.50,
                        values_a=[1.0] * 48, values_b=[2.0] * 48,
                        assume_comparable=True, label="d")
    assert rec["provenance_override"] is True
    assert rec["incomparable_provenance"]["differing"] == ["fixture_sha256"]
    assert rec["refused"] is None
    assert rec["a"]["n"] == 48 and rec["b"]["n"] == 48
    lines = stats._format_quantile_comparison(dict(rec, quantile="p50",
                                                   arm_a="arm-a",
                                                   arm_b="arm-b"))
    text = "\n".join(lines)
    assert "PROVENANCE OVERRIDE" in text, text
    assert "fixture_sha256" in text, text


def test_d_cli_override_is_visible_in_stdout_and_json():
    with tempfile.TemporaryDirectory() as tmp:
        rows = _rows("arm-a", fixture=FIX_A) + _rows("arm-b", fixture=FIX_B,
                                                     base=200.0)
        path = os.path.join(tmp, "rows.jsonl")
        out_json = os.path.join(tmp, "out.json")
        _write_rows(path, rows)
        code, out = _run_cli(["--rows", path, "--assume-comparable",
                              "--json", out_json])
        assert code == 0, code
        assert "PROVENANCE OVERRIDE" in out, out
        assert "incomparable_provenance" not in out, (
            "the override still emitted a refusal:\n%s" % out)
        with open(out_json, encoding="utf-8") as fh:
            doc = json.load(fh)
        assert doc["provenance_override"] is True, doc["provenance_override"]
        assert doc["assume_comparable"] is True
        assert "fixture_sha256" in doc["provenance_override_differing"]
        assert doc["quantile_comparisons"], doc.keys()
        first = doc["quantile_comparisons"][0]
        assert first["provenance_override"] is True
        assert "fixture_sha256" in first["incomparable_provenance"]["differing"]
        assert first["a"]["point"] is not None      # it really did compute


# --- (e) McNemar cannot route around the gate ------------------------------
def test_e_mcnemar_path_is_gated_too():
    pairs = [(False, True)] * 6
    for statistic in ("mcnemar", "quantile"):
        try:
            if statistic == "mcnemar":
                stats.compare(_cell(), _cell(fixture_sha256=FIX_B),
                              statistic="mcnemar", pairs=pairs)
            else:
                stats.compare(_cell(), _cell(fixture_sha256=FIX_B),
                              statistic="quantile", q=0.50,
                              values_a=[1.0] * 48, values_b=[1.0] * 48)
        except stats.IncomparableProvenance as exc:
            assert exc.differing == ["fixture_sha256"], (statistic, exc.differing)
            continue
        raise AssertionError("statistic %r bypassed the provenance gate"
                             % statistic)


# --- (f) red -> green: remove the same_provenance call --------------------
_GATE_LINES = ("    gate = require_comparable(cell_a, cell_b,\n"
               "                              assume_comparable=assume_comparable,"
               " label=label)\n")

_GATE_MUTANT = ('    gate = {"comparable": True, "differing": [],\n'
                '            "overridden": False,\n'
                '            "a": cell_provenance(cell_a),\n'
                '            "b": cell_provenance(cell_b)}\n')


def test_f_red_green_removing_the_gate_call_makes_case_a_fail():
    with open(MODULE_PATH, encoding="utf-8") as fh:
        source = fh.read()
    assert _GATE_LINES in source, (
        "the gate call moved; (f) must be pointed at the new line before it can "
        "prove anything")
    mutated = source.replace(_GATE_LINES, _GATE_MUTANT, 1)
    assert mutated != source

    with tempfile.TemporaryDirectory() as tmp:
        mutant_path = os.path.join(tmp, "analyze_stats_mutant.py")
        with open(mutant_path, "w", encoding="utf-8") as fh:
            fh.write(mutated)
        mutant = _load(mutant_path, "analyze_stats_mutant")
        # RED: with the same_provenance call gone, case (a) no longer refuses.
        red = True
        try:
            rec = mutant.compare(_cell(), _cell(fixture_sha256=FIX_B),
                                 statistic="quantile", q=0.50,
                                 values_a=[1.0] * 48, values_b=[2.0] * 48)
            red = False
            assert rec["refused"] is None
        except mutant.IncomparableProvenance:
            red = True
        assert red is False, (
            "mutation did not go RED: the mutant still refused, so case (a) does "
            "not depend on the same_provenance call")

    # GREEN: the committed module refuses on exactly the same input.
    try:
        stats.compare(_cell(), _cell(fixture_sha256=FIX_B), statistic="quantile",
                      q=0.50, values_a=[1.0] * 48, values_b=[2.0] * 48)
    except stats.IncomparableProvenance:
        return
    raise AssertionError("the committed module failed to refuse (green is broken)")


def main():
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("ok   %s" % name)
        except Exception:
            failed += 1
            print("FAIL %s" % name)
            traceback.print_exc()
    print("\n%d passed, %d failed" % (len(tests) - failed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
