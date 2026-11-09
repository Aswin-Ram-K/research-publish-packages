"""POOL-REPS-TOOL -- the pooling step H1's n=144/arm reading depends on.

Every test is offline: no socket, no live cell, no measured file is written. The
synthetic reps are three copies of a 48-turn era-B shaped cell, which is exactly
what tranche 1 is expected to put on disk (3 reps x 48 turns = 144).

The payoff test is the point of the unit: at n=48 per rep,
`analyze_stats.quantile_ci(q=0.95)` REFUSES (48 * 0.05 = 2.4 < TAIL_MIN = 3); at
the pooled n=144 it computes a p95 with an interval.
"""

from __future__ import annotations

import glob
import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, "experiments", "ptr-engine", "tools")
LONGRUN = os.path.join(REPO, "experiments", "ptr-engine", "longrun")
for path in (TOOLS, LONGRUN):
    if path not in sys.path:
        sys.path.insert(0, path)

import pool_reps  # noqa: E402
import analyze_stats  # noqa: E402

ARM = "pointer-stable"
TURNS = 48
FIXTURE = "a" * 64
HARNESS = "b" * 64


def make_cell(tmp_path, rep, turns=TURNS, arm=ARM, fixture=FIXTURE, harness=HARNESS,
              stop_reason=None, usable_for=None, rows_sha256=None, rows_override=None):
    """A 48-turn era-B shaped cell + its manifest. Era A is `stop_reason=`."""
    rows, ttft = [], 0.20 + 0.01 * rep
    for turn in range(1, turns + 1):
        row = {
            "arm": arm, "rep": rep, "kind": "turn", "turn": turn,
            "task_id": "LR-01", "claim": "H1", "comparison_eligible": True,
            "ttft_s": round(ttft + 0.001 * turn, 6),
            "latency_s": 10.0 + turn,
            "completion_tokens": 400 + turn,
            "fixture_sha256": fixture,
            "answer_verified": None,
        }
        if stop_reason:
            row["stop_reason"] = stop_reason
        else:
            row["finish_reason"] = "stop"
        rows.append(row)
    if rows_override is not None:
        rows = rows_override(rows)
    rows_path = tmp_path / ("rep%d.jsonl" % rep)
    with open(rows_path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    man = {
        "schema": "consonance.longrun-manifest/1",
        "arm": arm, "rep": rep, "N": turns, "rows_path": str(rows_path),
        "provenance": {
            "fixture_sha256": fixture, "harness_sha256": harness,
            "model": "occamy-1.0-NVFP4", "tools_mode": "off",
        },
    }
    if usable_for is not None:
        man["usable_for"] = usable_for
        man["usable_for_reason"] = "test stamp"
    if rows_sha256 is not None:
        man["rows_sha256"] = rows_sha256
    man_path = tmp_path / ("rep%d.manifest.json" % rep)
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1)
    return str(rows_path), str(man_path)


def three(tmp_path, **kwargs):
    cells = [make_cell(tmp_path, rep, **kwargs) for rep in (1, 2, 3)]
    return [c[0] for c in cells], [c[1] for c in cells]


# ---------------------------------------------------------------------------
# the successful pool: n=144 and the p95 that finally computes
# ---------------------------------------------------------------------------
def test_pool_three_reps_yields_n144(tmp_path):
    rows, mans = three(tmp_path)
    out = tmp_path / "pooled"
    man, man_path = pool_reps.pool(ARM, rows, reps=3, manifest_paths=mans,
                                   out_dir=str(out), stamp="20261026T190000Z")
    assert man["derived"] is True
    assert man["purpose"] == "H1 pooled R-all"
    assert man["n_turns"] == 144
    assert man["n_sources"] == 3
    assert man["h1_admissible"] is True
    assert man["excluded_turns"] == []
    assert len(man["sources"]) == 3
    for source in man["sources"]:
        for key in ("path", "sha256", "rep", "arm", "fixture_sha256",
                    "harness_sha256", "model", "tools_mode", "turns_on_disk"):
            assert key in source, key
        assert source["turns_on_disk"] == TURNS
        assert source["turns_pooled"] == TURNS
        assert len(source["sha256"]) == 64
    assert "created_at" in man and "pooling_rule" in man
    # the artefact is a derived pool, never a rows-cell-*
    jsonl = out / ("pooled-%s-20261026T190000Z.jsonl" % ARM)
    assert os.path.basename(jsonl).startswith("pooled-")
    assert not os.path.basename(jsonl).startswith("rows-")
    assert os.path.exists(jsonl) and os.path.exists(str(jsonl).replace(".jsonl", ".json"))
    on_disk = [json.loads(line) for line in open(jsonl, encoding="utf-8")]
    assert len(on_disk) == 144
    assert all(row["derived"] is True for row in on_disk)
    assert sorted({row["rep"] for row in on_disk}) == [1, 2, 3]


def test_pooled_n144_computes_p95_that_a_single_rep_cannot(tmp_path):
    rows, mans = three(tmp_path)
    out = tmp_path / "pooled"
    man, _ = pool_reps.pool(ARM, rows, reps=3, manifest_paths=mans, out_dir=str(out),
                            stamp="20261026T190000Z")
    pooled = os.path.join(str(out), "pooled-%s-20261026T190000Z.jsonl" % ARM)
    values = [row["ttft_s"] for row in map(json.loads, open(pooled, encoding="utf-8"))
              if row.get("kind") in ("turn", "turn-initial")]
    assert len(values) == 144
    stats = {}
    point, lo, hi, n = analyze_stats.quantile_ci(values, 0.95, stats=stats)
    assert n == 144
    assert lo <= point <= hi
    assert stats["used"] == 144 and stats["dropped_null"] == 0
    # one rep cannot: 48 * (1 - 0.95) = 2.4 < TAIL_MIN = 3
    with pytest.raises(analyze_stats.InsufficientSamples):
        analyze_stats.quantile_ci(values[:TURNS], 0.95)


# ---------------------------------------------------------------------------
# the refusals -- each named, none silent
# ---------------------------------------------------------------------------
def test_refuses_one_rep(tmp_path):
    rows, mans = three(tmp_path)
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, rows[:1], reps=3, manifest_paths=mans[:1],
                       out_dir=str(tmp_path / "out"))
    assert exc.value.code == "insufficient_reps"
    assert "H1 needs n >= 60" in exc.value.message


def test_refuses_two_reps_and_names_h3_and_h1_floors(tmp_path):
    rows, mans = three(tmp_path)
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, rows[:2], reps=3, manifest_paths=mans[:2],
                       out_dir=str(tmp_path / "out"))
    assert exc.value.code == "insufficient_reps"
    assert "b + c >= 6" in exc.value.message
    assert "n >= 60" in exc.value.message
    assert not glob.glob(str(tmp_path / "out" / "*.jsonl"))


def test_refuses_mixed_harness_sha256_naming_field_and_values(tmp_path):
    rows, mans = three(tmp_path)
    man = json.load(open(mans[2], encoding="utf-8"))
    man["provenance"]["harness_sha256"] = "c" * 64
    json.dump(man, open(mans[2], "w", encoding="utf-8"), indent=1)
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, rows, reps=3, manifest_paths=mans,
                       out_dir=str(tmp_path / "out"))
    assert exc.value.code == "incomparable_provenance"
    assert "harness_sha256" in exc.value.message
    assert HARNESS in exc.value.message
    assert "c" * 64 in exc.value.message


def test_refuses_mixed_fixture_sha256(tmp_path):
    rows, _ = three(tmp_path)
    rows[0], mans0 = make_cell(tmp_path, 1, fixture="d" * 64)
    mans = [mans0] + [make_cell(tmp_path, rep)[1] for rep in (2, 3)]
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, [rows[0]] + rows[1:], reps=3, manifest_paths=mans,
                       out_dir=str(tmp_path / "out"))
    assert exc.value.code == "incomparable_provenance"
    assert "fixture_sha256" in exc.value.message


def test_refuses_era_a_source(tmp_path):
    rows, mans = three(tmp_path)
    era_a_rows, era_a_man = make_cell(tmp_path, 4, stop_reason="stop")
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, rows[:2] + [era_a_rows], reps=3,
                       manifest_paths=mans[:2] + [era_a_man],
                       out_dir=str(tmp_path / "out"))
    assert exc.value.code == "era_a_excluded"
    assert "era B is never pooled with era A" in exc.value.message


def test_refuses_source_stamped_unusable(tmp_path):
    rows, mans = three(tmp_path)
    dead_rows, dead_man = make_cell(tmp_path, 4, usable_for=[])
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, rows[:2] + [dead_rows], reps=3,
                       manifest_paths=mans[:2] + [dead_man],
                       out_dir=str(tmp_path / "out"))
    assert exc.value.code == "source_unusable"
    assert "usable_for: []" in exc.value.message


def test_refuses_unreadable_source(tmp_path):
    rows, mans = three(tmp_path)
    missing = str(tmp_path / "missing.jsonl")
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, rows[:2] + [missing], reps=3,
                       manifest_paths=mans[:2], out_dir=str(tmp_path / "out"))
    assert exc.value.code == "source_unreadable"
    assert "missing.jsonl" in exc.value.message


def test_refuses_rows_sha_mismatch(tmp_path):
    rows, mans = three(tmp_path)
    bad_rows, bad_man = make_cell(tmp_path, 4, rows_sha256="0" * 64)
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, rows[:2] + [bad_rows], reps=3,
                       manifest_paths=mans[:2] + [bad_man],
                       out_dir=str(tmp_path / "out"))
    assert exc.value.code == "rows_sha_mismatch"
    assert "0" * 64 in exc.value.message


def test_refuses_duplicate_source(tmp_path):
    rows, mans = three(tmp_path)
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, [rows[0], rows[0], rows[1]], reps=3,
                       manifest_paths=[mans[0], mans[0], mans[1]],
                       out_dir=str(tmp_path / "out"))
    assert exc.value.code == "duplicate_source"


def test_refuses_to_pool_a_pool(tmp_path):
    rows, mans = three(tmp_path)
    out = tmp_path / "pooled"
    pool_reps.pool(ARM, rows, reps=3, manifest_paths=mans, out_dir=str(out),
                   stamp="20261026T190000Z")
    pooled = str(out / ("pooled-%s-20261026T190000Z.jsonl" % ARM))
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, [pooled, rows[1], rows[2]], reps=3,
                       manifest_paths=[None, mans[1], mans[2]],
                       out_dir=str(out / "twice"))
    assert exc.value.code == "source_derived"


# ---------------------------------------------------------------------------
# the honesty rule: a derived artefact is never auto-read as a measurement
# ---------------------------------------------------------------------------
def test_analyze_stats_refuses_derived_file_without_explicit_flag(tmp_path):
    rows, mans = three(tmp_path)
    out = tmp_path / "pooled"
    pool_reps.pool(ARM, rows, reps=3, manifest_paths=mans, out_dir=str(out),
                   stamp="20261026T190000Z")
    pooled = str(out / ("pooled-%s-20261026T190000Z.jsonl" % ARM))
    assert analyze_stats.is_derived_rows(pooled) is True
    assert analyze_stats.is_derived_rows(rows[0]) is False
    with pytest.raises(SystemExit) as exc:
        analyze_stats.main(["--rows", pooled])
    assert "--pooled" in str(exc.value)
    # green: the explicit flag loads it
    rc = analyze_stats.main(["--rows", pooled, "--pooled",
                             "--json", str(tmp_path / "analysis.json")])
    assert rc == 0


def test_pooled_artefact_is_outside_flat_measure_globs(tmp_path):
    """A plain `measure/*.jsonl` glob must not pick the derived file up."""
    measure = tmp_path / "measure"
    measure.mkdir()
    (measure / "rows-cell-x-20261026T190000Z.jsonl").write_text("{}\n", encoding="utf-8")
    rows, mans = three(tmp_path)
    pool_reps.pool(ARM, rows, reps=3, manifest_paths=mans,
                   out_dir=str(measure / "pooled"), stamp="20261026T190000Z")
    flat = glob.glob(str(measure / "*.jsonl"))
    assert len(flat) == 1 and "rows-cell-x" in flat[0]
    assert not any(os.path.basename(path).startswith("pooled-") for path in flat)
    deep = glob.glob(str(measure / "**" / "*.jsonl"), recursive=True)
    assert any("pooled-%s" % ARM in path for path in deep)
    # the repo's own analysis globs are rows-*, which cannot match pooled-*
    assert pool_reps.DEFAULT_OUT_DIR.endswith(os.path.join("measure", "pooled"))
    assert not glob.glob(os.path.join(TOOLS, os.pardir, "measure", "rows-*pooled*"))


def test_default_reps_is_three(tmp_path):
    """Red under a mutation of the minimum: 3 -> 1 would pool two reps silently."""
    rows, mans = three(tmp_path)
    with pytest.raises(pool_reps.PoolRefused) as exc:
        pool_reps.pool(ARM, rows[:2], manifest_paths=mans[:2],
                       out_dir=str(tmp_path / "out"))
    assert exc.value.code == "insufficient_reps"
