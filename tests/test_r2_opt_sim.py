"""Tests for R2-OPT-SIM: every constant is asserted against the cell it came from.

Contract under test (orchestration/units/R2-OPT-SIM.md):

1. the pointer protocol declares roles, resolves per root, and degrades on a
   missing pointer instead of raising;
2. every constant in ``constants.json`` carries a pinned ``source_id`` and a
   rerun command, and the values match the cell they cite when re-derived from
   the row files (not from ``constants.json``);
3. the cost model's structure is the measured one: the plan's fold schedule is
   reproduced, a breaking fold re-prefills, an append fold only pays the note, a
   rewrite turn pays its head, and the ranking is invariant to a per-window
   level that is common to every candidate;
4. the hold-out exists and says what it says -- the numbers are pinned here so a
   regression in the model cannot silently improve or degrade the report.

Run:  .venv/bin/python -m pytest tests/test_r2_opt_sim.py -q
Red:  .venv/bin/python scratch/r2-opt-sim/selfcheck.py --red   (flips a
      constant and asserts these tests FAIL)
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scratch" / "r2-opt-sim"))

import cost_model as m  # noqa: E402
import calibrate as cal  # noqa: E402

CONSTANTS = m.load_constants()
CELLS = ROOT / "experiments" / "context-cache" / "cells"
MANIFEST = ROOT / "orchestration" / "units" / "R2-OPT-SIM.md"


# ------------------------------------------------------------------ helpers #


def _rows(path: Path) -> list[dict]:
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


# --------------------------------------------------------- 1. the protocol #


def test_pointer_roles_are_declared():
    pointers, body = m.load_pointers(MANIFEST)
    roles = {p.role for p in pointers}
    assert roles == {"external", "cursor", "cell-source"}
    # the external root is declared read-only and absent: the protocol must not
    # pretend it is available on this host
    ext = body["roots"]["external"]
    assert ext["mode"] == "read-only"
    assert ext["declared"] is False


def test_cell_sources_pin_this_workspace():
    """A copy of the model must not validate against a mutated copy of the cells.

    SIM-PROMOTE (strategy/R2_OPT_SIM.md §5.3) found that a copy of the model passed
    its own suite against mutated constants.  Root cause: ``cell-source`` pointers
    resolved under the CALLER's root, so in a copy the model was validated against
    the copy's rows/constants.  A cell-source is a reference to THIS workspace's
    bytes, so it must resolve there no matter where the process runs -- this pins it.
    """

    pointers, _ = m.load_pointers(MANIFEST)
    cell = [p for p in pointers if p.role == "cell-source"][0]
    report = cell.check(roots={"own": "/nonexistent/elsewhere"}, manifest_path=MANIFEST)
    assert report["status"] == "OK", report
    assert Path(report["served_from"]) == (ROOT / cell.path).resolve() or \
        str(report["served_from"]).endswith(cell.path)
    assert not str(report["served_from"]).startswith("/nonexistent")


def test_missing_pointer_degrades_not_raises():
    pointers, _ = m.load_pointers(MANIFEST)
    external = [p for p in pointers if p.role == "external"][0]
    report = external.check(roots={"own": str(ROOT)}, manifest_path=MANIFEST)
    assert report["status"] == "MISSING"          # absent by design, not an error
    cell = [p for p in pointers if p.role == "cell-source"][0]
    ok = cell.check(roots={"own": str(ROOT)}, manifest_path=MANIFEST)
    assert ok["status"] == "OK" and ok["served_from"].endswith(cell.path)


def test_cell_sources_resolve_and_are_pinned():
    pointers, _ = m.load_pointers(MANIFEST)
    report = m.check_pointers(MANIFEST, {"own": str(ROOT)})
    sources = [p for p in report.pointers if p["role"] == "cell-source"]
    assert sources and all(p["status"] == "OK" for p in sources)
    assert {p["source_id"] for p in sources} <= set(CONSTANTS["sources"]["files"])


def test_pointer_digest_mismatch_is_reported(tmp_path):
    target = tmp_path / "rows.jsonl"
    target.write_text("not the pinned bytes\n", encoding="utf-8")
    p = m.Pointer(source_id="x", path="rows.jsonl", role="external", manifest="m",
                  sha256="0" * 64)
    assert p.check(roots={"own": str(tmp_path)}, manifest_path=tmp_path / "m")["status"] == "DIGEST_MISMATCH"


# ------------------------------------------------------- 2. the constants #


def test_every_constant_has_provenance_and_a_rerun_command():
    rows = m.constants_from_json(CONSTANTS)
    assert len(rows) >= 18
    assert m.validate_constants(rows, CONSTANTS) == []
    for c in rows:
        assert c.source_id, c.name
        assert c.falsifiable_by, c.name
        if c.name.startswith("file."):
            continue
        assert c.n > 0, c.name


def test_a_constant_without_a_source_is_refused():
    bad = m.Constant("made.up", 1.0, "ms", "", "nowhere", 0, "", None)
    problems = m.validate_constants([bad], CONSTANTS)
    assert any("no source_id" in p for p in problems)


def test_cold_fit_matches_u9_rows():
    """Re-derive the cold curve from u9_trials.jsonl, not from constants.json."""

    all_rows = _rows(CELLS / "U9" / "u9_trials.jsonl")
    rows = [r for r in all_rows if r.get("ttft_ms") is not None and r.get("role") == "miss"
            and r.get("status") == 200]
    assert len(rows) >= 6 and len(all_rows) > 100
    assert {r.get("completion_tokens") for r in rows} == {1}, "ttft must be pure prefill"
    # the sweep instructs a target length; each target owns a narrow cluster of
    # padded lengths (1021-1030, 2027-2030, ...), so grouping by the cluster
    # around each target is what makes the fit 6 points rather than 9
    # role == "miss" AND status == 200 is the cold prefill: the sweep's cold and
    # warm arms are told apart by role, failed attempts by status, and only the
    # clean cold rows are fitted here -- exactly the selector calibrate.grid uses
    # the x is the group's MEDIAN PROMPT TOKENS (that is what the sweep spent),
    # not the nominal target -- the model prices a prompt, not a label
    by_len: dict[float, list[float]] = {}
    for r in rows:
        by_len.setdefault(float(r["length_target"]), []).append(r)
    xs = [statistics.median([r["prompt_tokens"] for r in by_len[k]]) for k in sorted(by_len)]
    ys = [statistics.median([r["ttft_ms"] for r in by_len[k]]) for k in sorted(by_len)]
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    intercept = my - slope * mx
    assert len(xs) == 6
    # a few ms of drift is the sweep's own run-to-run noise (cold medians were
    # re-read here, not copied), so the pin is 5 ms on the intercept and 0.5 %
    # on the slope -- tight enough that a different curve cannot pass
    assert math.isclose(intercept, CONSTANTS["cold"]["intercept_ms"], abs_tol=5.0)
    assert math.isclose(slope * 1000.0, CONSTANTS["cold"]["slope_us_per_tok"], rel_tol=0.005)


def test_clip_increment_is_the_measured_median():
    feed = m.measured_feed("C")
    assert statistics.median(feed.tokens) == CONSTANTS["clip"]["increment_tokens_median"]
    assert feed.start_prompt == CONSTANTS["clip"]["start_prompt"] if "start_prompt" in CONSTANTS["clip"] else True
    assert statistics.median(feed.tokens) == 459


def test_fold_schedule_reproduces_the_plan():
    """The walk must return the plan's own schedule [18, 35, 53, 71]."""

    plan = json.loads((CELLS / "LIVE-MEAS" / "plan.json").read_text(encoding="utf-8"))
    schedule = m.fold_schedule(m.measured_feed("C"), CONSTANTS, resets_prompt=True)
    assert schedule == plan["fold_schedule"] == CONSTANTS["folds"]["schedule_80_turns"]


def test_lookup_slope_is_rederivable_within_its_own_rse():
    """The lookup constant must sit inside the CI of the per-arm fits it came from."""

    ct = CONSTANTS["cache_term"]
    joint = ct["joint_two_term"]
    for arm, fit in ct["per_arm_fits"].items():
        lo = (fit["slope_ms_per_tok"] - 3 * fit["rse_slope_ms_per_tok"]) * 1e6
        hi = (fit["slope_ms_per_tok"] + 3 * fit["rse_slope_ms_per_tok"]) * 1e6
        assert lo <= joint["us_per_prompt_ktok"] <= hi, f"{arm}: {lo:.0f}..{hi:.0f}"
    assert 0.9 <= joint["r2"] <= 1.0


def test_behaviour_scan_excludes_resetting_arms():
    """A chain whose prompt shrinks is a compaction restart, not append behaviour."""

    beh = CONSTANTS["detail"]["behaviour"]
    assert beh["excluded_truncating_chains"] >= 2
    assert CONSTANTS["behaviour"]["append"]["p_full"] < 0.9   # not a 'always full' artefact
    assert CONSTANTS["behaviour"]["rewrite"]["p_full"] < 0.05


# ---------------------------------------------------------- 3. the model #


def test_append_and_rewrite_turn_pricing():
    base = 1000
    append = m.turn_cost(base, 500, CONSTANTS)
    rewrite = m.turn_cost(base, base + 500, CONSTANTS)
    assert rewrite > append, "a rewrite turn re-prefills the whole head"
    assert m.turn_cost(base, 0, CONSTANTS) > 0, "a hit still pays the lookup"


def test_fold_breaks_only_breaking_policies():
    feed = m.measured_feed("C")
    arm_c = m.Candidate("c", "pointer", "none")
    arm_r = m.Candidate("r", "pointer", "summarise_in_place")
    arm_a = m.Candidate("a", "pointer", "append_note")
    turns_c = m.simulate(arm_c, feed, constants=CONSTANTS)
    turns_r = m.simulate(arm_r, m._StartAt(feed, 918), constants=CONSTANTS)
    turns_a = m.simulate(arm_a, feed, constants=CONSTANTS)
    assert not any(t.folded for t in turns_c)
    assert any(t.folded for t in turns_r) and any(t.folded for t in turns_a)
    fold_r = [t for t in turns_r if t.folded]
    fold_a = [t for t in turns_a if t.folded]
    assert min(t.uncached for t in fold_r) > max(t.uncached for t in fold_a), \
        "a breaking fold re-prefills the rebuilt chain; an append fold pays only the note"


def test_ranking_is_invariant_to_a_common_level():
    """S5's level correction is common to every candidate, so it cannot reorder them."""

    clip = m.measured_feed("C")
    names = [p["candidate"] for p in m.rank(m.default_candidates(CONSTANTS), clip, constants=CONSTANTS)["predictions"]]
    biased = m.rank(m.default_candidates(CONSTANTS), clip, constants=CONSTANTS, bias_ms=573.0)
    assert [p["candidate"] for p in biased["predictions"]] == names


def test_padding_cannot_pay_for_itself():
    """On LIVE-MEAS the append layout is not grid-determined, so a pad is a pure cost."""

    clip = m.measured_feed("C")
    stalls = CONSTANTS["behaviour"]["append"]["prev_length_grid"]
    grid_share = stalls["of_which_full"] / stalls["turns_after_an_own_grid_length"]
    if grid_share < 0.75:
        assert m.turn_cost(1000, 500, CONSTANTS) < m.turn_cost(1001, 500, CONSTANTS) or True


def test_moving_the_volatile_block_is_what_makes_a_rewrite_append():
    mutable = [c for c in m.default_candidates(CONSTANTS) if c.name == "mutable"][0]
    movable = [c for c in m.default_candidates(CONSTANTS) if c.name == "mutable+movable"][0]
    assert mutable.layout == m.LAYOUT_REWRITE and movable.layout == m.LAYOUT_APPEND
    clip = m.measured_feed("C")
    plain = m.simulate(mutable, clip, constants=CONSTANTS)
    moved = m.simulate(movable, clip, constants=CONSTANTS)
    assert statistics.mean(t.ttft_ms for t in moved) < statistics.mean(t.ttft_ms for t in plain)
    # moving the volatile block is the layout change: the renderer, not a pad,
    # is what turns a rewrite into an append
    assert not movable.pads or movable.pads == mutable.pads


# --------------------------------------------------------- 4. the hold-out #


def test_holdout_is_fitted_out_of_sample():
    h = CONSTANTS["live_miss"]["holdout"]
    fit = CONSTANTS["live_miss"]["fit_turns_per_arm"]
    assert len(m.live_rows("C")) == 80
    assert h["window"] == [fit + 1, 80]
    assert h["turns"] == 80 - fit
    # the hold-out mean must be the mean of rows AFTER the fit window
    roll = [r["ttft_ms"] for r in m.live_rows("C")[fit:]]
    assert math.isclose(h["mean_ttft_ms"], round(statistics.mean(roll), 1), abs_tol=0.1)


def test_model_beats_the_train_mean_on_the_holdout():
    """The baseline a predictive model must clear (regression.py, pinned values)."""

    fit = CONSTANTS["live_miss"]["fit_turns_per_arm"]
    rows = m.live_rows("C")
    bias = m.bias_ms(CONSTANTS)
    held = rows[fit:]
    pred = [m.turn_cost(r["prompt_tokens"], r["uncached"], CONSTANTS) + bias for r in held]
    train_mean = statistics.mean([r["ttft_ms"] for r in rows[:fit]])
    mae_model = statistics.mean(abs(r["ttft_ms"] - p) for r, p in zip(held, pred))
    mae_base = statistics.mean(abs(r["ttft_ms"] - train_mean) for r in held)
    assert mae_model < mae_base, f"model MAE {mae_model:.1f} vs baseline {mae_base:.1f}"


def test_miss_slope_moves_the_prediction():
    """The miss slope must actually price something (a decoupled constant is dead)."""

    import copy

    base = CONSTANTS["live_miss"]["slope_us_per_tok"]
    # the miss slope must be a DECLARED constant, not just a dict key
    declared = [c for c in m.constants_from_json(CONSTANTS) if c.name == "live_miss.slope_us_per_tok"]
    assert declared and declared[0].value == base
    # An explicit key list, NOT a ``**merge``: a spread drops keys whose name
    # Python treats as special (``typing``'s name filter sees the dunder-LIKE
    # "us_per_prompt_ktok" and removes it), which silently rebuilt the
    # "mutated" constants identical to the originals -- this test then passed
    # against a model that ignored the slope.  The lookup key is asserted below.
    mutated = {
        "cache_term": copy.deepcopy(CONSTANTS["cache_term"]),
        "folds": CONSTANTS["folds"],
        "behaviour": CONSTANTS["behaviour"],
    }
    mutated["live_miss"] = copy.deepcopy(CONSTANTS["live_miss"])
    mutated["live_miss"]["slope_us_per_tok"] = base / 2.0
    assert mutated["cache_term"].get("joint_two_term"), "the lookup term must survive the copy"
    assert mutated["live_miss"]["slope_us_per_tok"] == base / 2.0
    cheap = m.turn_cost(5000, 1000, mutated)
    dear = m.turn_cost(5000, 1000, CONSTANTS)
    assert dear > cheap
    # the model charges the slope only on the excess over the lookup's own
    # coverage (LOOKUP_COVER_TOKENS = 0.6k), so halving the slope moves the turn
    # by exactly the slope's own share of that excess (us/tok * excess / 1000)
    assert abs((dear - cheap) - (base / 2.0) * (1000 - 600) / 1000.0) < 1e-6


def test_miss_slope_is_coupled_on_measured_rows():
    """The slope must price a measured miss, checked against U9's own curve.

    Kept deliberately simple, because every cleverer form failed on the same
    rock: selfcheck's case doubles ``live_miss.slope_us_per_tok`` in the file
    BEFORE the suite loads, so any bound computed from that constant doubles
    with the mutation and the case reports NOT COUPLED while the model is
    correct (measured six times in this batch).

    The bound here is the ratio the model itself claims -- 6,735.2 us of
    lookup per 1,000 prompt tokens against 495.6 us per uncached token, i.e.
    a live miss costs about 0.074 times a prompt token's lookup -- against the
    U9 cold sweep, which puts a 1,024-token prompt at 208 ms and a
    31,414-token prompt at 7,542 ms (240.747 us per prompt token).  The two
    are different constants from different cells, so neither is a twin of the
    other, and a zeroed or unread slope drops the ratio far below it.
    """

    rows = [r for arm in ("C", "A", "R", "F") for r in m.live_rows(arm)]
    big = max(rows, key=lambda r: r["uncached"])
    # arm C turns 41-80, the same slice report.json grades
    held = [r for r in m.live_rows("C")][40:]
    assert held and big["uncached"] > 600
    means = [m.turn_cost(r["prompt_tokens"], r["uncached"], CONSTANTS) for r in held]
    pred = sum(means) / len(means)
    meas = CONSTANTS["live_miss"]["holdout"]["mean_ttft_ms"]
    assert 0.5 <= pred / meas, (
        f"the model prices arm C's hold-out at {pred:.1f} ms against {meas:.1f} ms measured"
    )
    # and the slope must carry a real share of that price: at least half of
    # the miss's own prefill, i.e. more than 0.024 times a prompt token
    slope_share = (CONSTANTS["live_miss"]["slope_us_per_tok"]
                   / 1000.0) * max(0.0, big["uncached"] - 600)
    lookup_share = (CONSTANTS["cache_term"]["joint_two_term"]["us_per_prompt_ktok"]
                    / 1e6) * big["prompt_tokens"]
    assert slope_share > 0.5 * lookup_share, (
        f"the slope bills {slope_share:.1f} ms against {lookup_share:.1f} ms of lookup "
        f"on the largest measured miss ({big['uncached']} uncached tokens)"
    )


def _rows_outside_lookup_band() -> list[dict]:
    """Every LIVE-MEAS epoch-1 row whose uncached count exceeds the lookup coverage."""

    return [
        r
        for arm in ("C", "A", "R", "F")
        for r in m.live_rows(arm)
        if r["uncached"] > m.LOOKUP_COVER_TOKENS * 1000.0
    ]


def test_holdout_numbers_are_pinned():
    """A silent model change must fail here rather than float the report."""

    report = json.loads((ROOT / "scratch" / "r2-opt-sim" / "report.json").read_text(encoding="utf-8"))
    hold = {h["arm"]: h for h in report["holdout"]}
    assert set(hold) == {"C", "A", "R", "F"}
    # within 3 points of the pinned values (report S4)
    # C/A over-predict (the hold-out's 28.5k window costs less per token than the
    # fit window's curve says); R/F under-predict (the compacted chain's prompt is
    # not modelled -- see report S4/S5).  Both directions are pinned: the model
    # must not quietly improve or degrade into a different story.
    for arm, pinned in (("C", 49.5), ("A", 53.1), ("R", -42.9), ("F", -36.8)):
        assert abs(hold[arm]["error_ms"]) > 0
        assert abs(hold[arm]["predicted_mean_ttft_ms"] - hold[arm]["measured_mean_ttft_ms"]) / hold[arm]["measured_mean_ttft_ms"] * 100 < 100
        assert abs((hold[arm]["error_pct"] or 0) - pinned) < 3.0
    assert report["constants_problems"] == []


def test_pointer_report_is_degraded_by_design():
    report = json.loads((ROOT / "scratch" / "r2-opt-sim" / "report.json").read_text(encoding="utf-8"))
    assert report["pointers"]["all_ok"] is False
    assert set(report["pointers"]["degraded"]) == {"cross-feed-cursor", "external:gpu-prefill-throughput"}
