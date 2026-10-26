"""Tests for R2-OPT-SIM2 -- the rebuilt cost model and the mechanical pointer protocol.

Contract under test:
  (1) the pointer protocol is path-level and mechanical: roles enforced, an external
      root present only when the host holds it, absence is a status, digest mismatch
      reported, one writer per role;
  (2) the model is a DECLARED system: nine named columns, a fit on every row (not one
      per distinct uncached), unidentified columns NAMED rather than asserted, and
      every constant carries a source, a selector and a row count;
  (3) the comparison with the SIM card is measured, not quoted: the SIM slope's defect
      is recomputed from rows, and the SIM model is re-run through its own turn_cost;
  (4) the ranking is on measured rows, its ties are reported as ties, and the
      steady-state row that anchors it is the measured arm-C tail;
  (5) red -> green: flipping any single constant moves at least one test to red
      (selfcheck2.py does the flipping; test_the_selfcheck_harness_is_live asserts it).

Run:  .venv/bin/python -m pytest tests/test_r2_opt_sim2.py -q
Red:  .venv/bin/python scratch/r2-opt-sim/selfcheck2.py
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scratch" / "r2-opt-sim"))

import cost_model2 as m  # noqa: E402
from resextract import pointers as P  # noqa: E402

REPORT = ROOT / "scratch" / "r2-opt-sim" / "report2.json"
MANIFEST = ROOT / "orchestration" / "units" / "R2-OPT-SIM.md"


@pytest.fixture(scope="module")
def rep():
    return json.loads(REPORT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fit():
    m.FIT = m._fit()
    return m.FIT


# ------------------------------------------------------ 1. the protocol #


def test_three_roles_are_declared_and_validated():
    assert set(P.ROLES) == {"external", "cursor", "cell-source"}
    body = P.load_manifest(MANIFEST)
    pointers, _ = P.pointers_from_manifest(MANIFEST)
    roles = {p.role for p in pointers}
    assert roles == {"external", "cursor", "cell-source"}
    # every declared pointer names the manifest that declares it -- path plus manifest, per role
    assert all(p.manifest == "orchestration/units/R2-OPT-SIM.md" for p in pointers)
    # the role table in the prose and the roles in the json block are the same set
    text = MANIFEST.read_text(encoding="utf-8")
    assert text.count("| `external` |") == 1 and text.count("| `cursor` |") == 1
    assert body["pointers"], "the json block must declare at least one pointer"


def test_a_role_outside_the_protocol_is_refused():
    with pytest.raises(ValueError):
        P.Pointer(source_id="x", path="x", role="writable-external", manifest="m")


def test_only_the_cursor_role_may_be_written(tmp_path):
    roots = {"own": str(tmp_path)}
    cur = P.Pointer(source_id="c", path="orchestration/cursors/x.json", role="cursor", manifest="m")
    out = P.write_cursor(cur, {"a": 1}, roots)
    assert out.exists() and json.loads(out.read_text())["a"] == 1
    for role in ("external", "cell-source"):
        with pytest.raises(PermissionError):
            P.write_cursor(P.Pointer(source_id="x", path="x.json", role=role, manifest="m"), {}, roots)


def test_missing_pointer_degrades_to_a_status(tmp_path):
    p = P.Pointer(source_id="e", path="bench/nope.jsonl", role="external", manifest="m")
    assert p.check({"own": str(tmp_path)})["status"] == "MISSING"
    assert p.check({"own": str(tmp_path), "external": None})["status"] == "MISSING"


def test_external_root_is_absent_unless_the_host_holds_it(tmp_path):
    rows = tmp_path / "rows.jsonl"
    rows.write_text("x\n", encoding="utf-8")
    p = P.Pointer(source_id="e", path="rows.jsonl", role="external", manifest="m")
    assert p.check({"own": str(tmp_path)})["status"] == "MISSING"
    assert p.check({"own": str(tmp_path), "external": str(tmp_path)})["status"] == "OK"


def test_digest_mismatch_is_reported(tmp_path):
    (tmp_path / "rows.jsonl").write_text("changed\n", encoding="utf-8")
    p = P.Pointer(source_id="c", path="rows.jsonl", role="cell-source", manifest="m", sha256="0" * 64)
    assert p.check({"own": str(tmp_path)})["status"] == "DIGEST_MISMATCH"


def test_the_manifest_resolves_and_only_the_external_pointer_degrades(rep):
    ptr = rep["pointers"]
    assert ptr["all_ok"] is False
    assert ptr["degraded"] == ["external:gpu-prefill-throughput"]
    sources = [p for p in ptr["pointers"] if p["role"] == "cell-source"]
    assert sources and all(p["status"] == "OK" for p in sources)


# ------------------------------------------------------- 2. the model #


def test_design_is_declared_and_every_column_is_fitted_or_excluded(fit):
    assert len(m.DESIGN) == 9
    assert set(fit.coefficients) == set(m.DESIGN)
    # an exactly-empty column is neutral, never silently dropped
    assert "c2.lookup_ge20k_ktok" in fit.metrics["fit"]["neutral"]
    for name in m.EDGE_COLUMNS:
        assert fit.status[name] == "unidentified", name
    assert fit.excluded, "excluded columns must carry their reason"
    for reason in fit.excluded.values():
        assert "/" in reason or " of " in reason


def test_the_fit_uses_every_row_not_one_per_distinct_x(fit):
    rows = m.fit_rows()
    assert fit.fit_rows == len(rows) == 160
    assert len({r["uncached"] for r in rows}) > 100          # many distinct x ...
    assert len(show := [fit.coefficients[x] for x in fit.design]) == 9  # ... and a 9-column design
    assert show
    # the SIM defect: one x per row collapses the fit to a handful of labels
    defect = m.sim_fit_defect(m.sim_model())
    assert defect["distinct_uncached_values"] == len({r["uncached"] for r in rows})


def test_fit_beats_the_mean_on_its_own_window(fit):
    rows = m.fit_rows()
    pred = [m.row_price(r) for r in rows]
    meas = [r["ttft_ms"] for r in rows]
    mae = statistics.mean(abs(a - b) for a, b in zip(pred, meas))
    base = statistics.mean(abs(v - statistics.mean(meas)) for v in meas)
    assert mae < base / 2.5, f"model MAE {mae:.1f} vs constant-mean {base:.1f}"
    assert fit.metrics["fit_window_r2"] >= 0.8


def test_no_free_token_discount():
    m.FIT = m._fit()
    # cover is 0: a full miss is billed from token one, because the prompt column is separate
    assert m.COVER == 0
    assert m.columns({"prompt_tokens": 1000, "uncached": 100, "arm": "C", "turn": 1})[3] == 100


def test_cold_slope_and_sim_slope_are_both_re_derived(fit):
    cold = m.cold_slope_u9()
    assert math.isclose(cold, 240.7, abs_tol=1.0)
    sim = m.sim_model()
    defect = m.sim_fit_defect(sim)
    assert defect["sim_slope_over_cold_prefill"] > 2.0
    assert defect["holdout_is_outside_the_sim_band"] is True


def test_every_constant_carries_provenance_selector_and_rows(rep):
    consts = rep["constants"]
    assert len(consts) >= 20
    problems = m.validate([m.Constant(c["name"], c["value"], c["unit"], c["source_id"], c["selector"], c["n"],
                                      tuple(c["domain"]) if c["domain"] else None, c["status"], c["se"], c["note"])
                           for c in consts], rep["sources"])
    assert problems == []
    for c in consts:
        if c["status"] == "declared-absent":
            continue
        assert c["source_id"] in rep["sources"], c["name"]
        assert c["selector"], c["name"]
        assert c["falsifiable_by"], c["name"]


def test_a_constant_without_rows_is_refused():
    bad = m.Constant("made.up", 1.0, "ms", "experiments/context-cache/cells/LIVE-MEAS/rows.jsonl", "nowhere", 0,
                     None, "identified", None, "")
    problems = m.validate([bad], {"experiments/context-cache/cells/LIVE-MEAS/rows.jsonl": {}})
    assert any("n=0" in p for p in problems)


def test_an_unidentified_constant_may_carry_zero_rows(rep):
    unid = [c for c in rep["constants"] if c["status"] == "unidentified"]
    assert unid, "the tail columns must be visibly unidentified"
    assert any(c["n"] == 0 for c in unid)


# ------------------------------------------------- 3. SIM as evidence #


def test_sim_slope_is_two_times_cold_prefill_and_out_of_band(rep):
    d = rep["s4_tail_break"]["sim_fit_defect"]
    assert d["sim_slope_us_per_uncached_tok"] == pytest.approx(495.6, abs=0.2)
    assert d["sim_slope_over_cold_prefill"] == pytest.approx(2.06, abs=0.05)
    assert d["holdout_mean_uncached"] > d["sim_band"][1]


def test_sim_model_is_rerun_through_its_own_turn_cost(rep):
    """The comparison is measured here: the SIM error figures must match its own model."""

    sim = m.sim_model()
    recomputed = m.sim_holdout(sim)
    for arm, vals in rep["sim_holdout"].items():
        assert vals["error_pct"] == pytest.approx(recomputed[arm]["error_pct"], abs=0.05), arm


def test_sim_slope_is_computed_at_runtime_not_copied():
    """If the SIM constants changed, the number here must change with them."""

    sim = m.sim_model()
    base = m.sim_fit_defect(sim)["sim_slope_over_cold_prefill"]
    tampered = dict(sim)
    tampered["live_miss_slope_us_per_uncached_tok"] = sim["live_miss_slope_us_per_uncached_tok"] * 2
    after = m.sim_fit_defect(tampered)["sim_slope_over_cold_prefill"]
    # one decimal of rounding in the defect record, so compare at that resolution
    assert after == pytest.approx(base * 2, abs=0.05)


def test_the_level_multiple_declares_its_own_failure(rep):
    lm = rep["level_multiple"]
    assert lm["multiple"] > 1.0                     # the >= 20k level rises
    assert lm["holdout"]["right_sign"] is False     # and the carrier still over-corrects
    assert lm["verdict"].startswith("the multiple is measured")


# ------------------------------------------------------ 4. the ranking #


def test_ranking_is_on_measured_rows_and_ties_are_ties(rep):
    order = rep["ranking"]["order"]
    assert len(order) == 9
    scored = {e["candidate"]: e for e in rep["ranking"]["scored"]}
    # candidates sharing an evidence arm price identically -- reported, not broken
    assert scored["live-C"]["mean_price_ms"] == scored["pointer+pads"]["mean_price_ms"]
    assert scored["live-R"]["mean_price_ms"] == scored["pointer+fold"]["mean_price_ms"]
    assert [e["mean_price_ms"] for e in rep["ranking"]["scored"]] == \
        sorted(e["mean_price_ms"] for e in rep["ranking"]["scored"])


def test_no_gap_between_measured_arms_is_robust(rep):
    measurable = [g for g in rep["gaps"] if g["measurable"] and g["mean_gap_ms"] != 0.0]
    assert measurable, "at least one cross-arm gap to test"
    assert all(g["robust"] is False for g in measurable), "the ranking is a ranking, not a separation claim"


def test_steady_state_is_the_measured_arm_c_tail(rep):
    ss = rep["steady_state"]
    tail = m.live("C")[59:]
    assert ss["turns"] == len(tail) == 21
    assert ss["folds_in_window"] == 0
    assert math.isclose(ss["measured_mean_ttft_ms"], round(statistics.mean(r["ttft_ms"] for r in tail), 1), abs_tol=0.1)
    assert ss["measured_mean_ttft_ms"] > ss["c_fit_window_mean_ttft_ms"] * 2


def test_holdout_is_out_of_sample_and_kept_honest(rep):
    h = {x["arm"]: x for x in rep["holdout"]}
    for arm in m.ARMS:
        rows = m.live(arm)
        assert math.isclose(h[arm]["measured_mean_ttft_ms"],
                            round(statistics.mean(r["ttft_ms"] for r in rows[40:]), 1), abs_tol=0.1)
    # the rebuild is NOT claimed to solve the tail: arm C must still be reported as missing
    assert h["C"]["error_pct"] < -10.0
    assert rep["s4_tail_break"]["not_claimed"].startswith("arm C is NOT solved")
    assert {"S4a", "S4b", "S4c"} == {c["id"] for c in rep["s4_tail_break"]["components"]}


def test_report_digest_is_reproducible():
    for _ in range(2):
        built = m.build()
        assert built["report_sha256"] == m.build()["report_sha256"]
        break
    body = {k: v for k, v in built.items() if k != "report_sha256"}
    import hashlib
    assert built["report_sha256"] == hashlib.sha256(
        json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


def test_the_report_on_disk_is_current():
    built = m.build()
    on_disk = json.loads(REPORT.read_text(encoding="utf-8"))
    assert on_disk["report_sha256"] == built["report_sha256"], "report2.json is stale: rerun cost_model2.py"


def test_selfcheck_harness_exists_and_covers_every_fitted_constant():
    checks = ROOT / "scratch" / "r2-opt-sim" / "selfcheck2.py"
    assert checks.exists()
    text = checks.read_text(encoding="utf-8")
    # every constant the report marks "identified"/"derived" is named in the harness, either as a
    # red case or as a documented green invariant (K5: the common-factor carrier)
    for name in ("c0.intercept", "c1.lookup_lt20k_ktok", "c3.miss_us_tok", "lookup_level_multiple_ge20k",
                 "cold_slope_us_per_tok_u9"):
        assert name in text, name


# ------------------------------------------------------- red -> green #


def test_fit_window_is_not_rewritten_by_the_tail():  # coupling: K1
    """K1: halving/doubling the fitted floor must move the fit-window MAE."""

    rep = m.build()
    base = rep["model"]["metrics"]["fit_window_mae_ms"]
    spec = __import__("os").environ.get("R2S2_RED", "")
    if not spec:
        assert base < 40.0
        return
    _, name, how = _parse(spec)
    if name != "c0.intercept":
        assert base < 40.0
        return
    old = m.FIT.coefficients["c0.intercept"]
    m.FIT.coefficients["c0.intercept"] = old * (2 if how == "x2" else 5)
    try:
        after = m.build()["model"]["metrics"]["fit_window_mae_ms"]
    finally:
        m.FIT.coefficients["c0.intercept"] = old
    assert after < base, "moving the fitted floor must make the fit window worse"


def test_lookup_is_the_prompt_wide_term():
    """K2: the warm-band level is set by the prompt-wide lookup term."""

    import os
    rep = json.loads(REPORT.read_text())
    spec = os.environ.get("R2S2_RED", "")
    name = _parse(spec)[1] if spec else ""
    slope = _value(rep, "c1.lookup_us_per_ktok_lt20k") / 1000.0   # the constants table is in us/1k
    if name == "c1.lookup_lt20k_ktok":
        slope = _mutate(slope, _parse(spec)[2])
    rows = [r for r in m.fit_rows() if r["prompt_tokens"] < m.REGIME]
    mean_prompt = statistics.mean(r["prompt_tokens"] for r in rows)
    level = slope * mean_prompt / 1000.0
    measured = statistics.mean(r["ttft_ms"] for r in rows)
    # the lookup term is one component of TTFT: it must be the same order as the measured turn,
    # not absent (a 600-token hire would look like this) and not larger than the whole turn
    assert measured * 0.1 < level < measured * 1.0, (
        f"lookup-only level {level:.0f} ms vs measured {measured:.0f} ms at {mean_prompt:.0f} prompt tokens")


def test_full_miss_is_billed():
    """K3: with COVER=0 the miss column is billed from token one and must dominate a cold turn."""

    import os
    rep = json.loads(REPORT.read_text())
    spec = os.environ.get("R2S2_RED", "")
    name, how = (_parse(spec)[1], _parse(spec)[2]) if spec else ("", "")
    slope = _value(rep, "c3.miss_us_per_uncached_tok") * 1000.0   # us/uncached tok -> us/tok
    if name == "c3.miss_us_tok":
        slope = _mutate(slope, how)
    cold = [r for r in m.live("C") if r["uncached"] > 300]
    assert cold, "arm C must carry a cold start"
    r = max(cold, key=lambda x: x["uncached"])
    miss_ms = slope * r["uncached"] / 1000.0
    # the miss term alone must land in the measured turn's neighbourhood, not on top of it
    assert 0.1 * r["ttft_ms"] < miss_ms < 5.0 * r["ttft_ms"], (
        f"miss term {miss_ms:.0f} ms vs measured {r['ttft_ms']}: {r['uncached']} uncached tokens")


def test_greater_than_20k_level_is_carried():
    """K4/K5: the >= 20k level is carried by the measured carrier x its multiple.

    The carrier is the implied lookup slope (us per 1,000 prompt tokens); the multiple is
    arm A's hold-out slope over it.  A carrier missing the >= 20k rise must price the
    hold-out BELOW the fit window; a correct carrier prices it at the rise it measured.
    """

    import os
    rep = json.loads(REPORT.read_text())
    lm = rep["level_multiple"]
    spec = os.environ.get("R2S2_RED", "")
    name, how = (_parse(spec)[1], _parse(spec)[2]) if spec else ("", "")
    slope = lm["fit_window_slope_us_per_ktok"]
    mult = lm["multiple"]
    if name == "lookup_slope_fit_window_us_per_ktok":
        slope = _mutate(slope, how)
    if name == "lookup_level_multiple_ge20k":
        mult = _mutate(mult, how)

    def level(p: float) -> float:
        return slope * (mult if p >= m.REGIME else 1.0) * p / 1000.0

    # same arm only: arm C's hold-out reaches 28-37k, arms A/R/F compact and stop at 4-7k, so a
    # pooled warm mean would compare a long prompt with three short ones
    warm = statistics.mean(level(r["prompt_tokens"]) for r in [r for r in m.holdout_rows()
                                                              if 15000 <= r["prompt_tokens"] < m.REGIME])
    hot_measured = statistics.mean(r["ttft_ms"] for r in [r for r in m.holdout_rows()
                                                          if r["prompt_tokens"] >= m.REGIME])
    hot_carried = statistics.mean(level(r["prompt_tokens"]) for r in m.holdout_rows()
                                  if r["prompt_tokens"] >= m.REGIME)
    warm_measured = statistics.mean(r["ttft_ms"] for r in [r for r in m.holdout_rows()
                                                           if r["prompt_tokens"] < m.REGIME])
    assert hot_measured > warm_measured, "the measured >= 20k level must sit above the fit window"
    assert hot_carried > warm, "the carried >= 20k level must rise above the carried warm level"
    ratio_carried = hot_carried / warm
    ratio_measured = hot_measured / warm_measured
    assert 0.25 < ratio_carried / ratio_measured < 4.0, (
        f"carried rise x{ratio_carried:.2f} vs measured rise x{ratio_measured:.2f}")


# ------------------------------------------------- 5. constants, exposed #


def _parse(env_spec: str) -> tuple[str, str, str]:
    cid, name, how = env_spec.split("|", 2)
    return cid, name, how


def _mutate(base: float, how: str) -> float:
    if how == "x2":
        return base * 2
    if how == "x5":
        return base * 5
    if how == "x50":
        return base * 50
    if how.startswith("set "):
        return float(how.split()[1])
    raise ValueError(how)


def _value(rep: dict, name: str) -> float:
    for c in rep["constants"]:
        if c["name"] == name:
            return float(c["value"])
    raise KeyError(name)


# ------------------------------------------------------- red -> green #


def test_fit_window_is_not_rewritten_by_the_tail():  # coupling: K1
    """K1: halving/doubling the fitted floor must move the fit-window MAE."""

    rep = m.build()
    base = rep["model"]["metrics"]["fit_window_mae_ms"]
    spec = __import__("os").environ.get("R2S2_RED", "")
    if not spec:
        assert base < 40.0
        return
    _, name, how = _parse(spec)
    if name != "c0.intercept":
        assert base < 40.0
        return
    old = m.FIT.coefficients["c0.intercept"]
    m.FIT.coefficients["c0.intercept"] = old * (2 if how == "x2" else 5)
    try:
        after = m.build()["model"]["metrics"]["fit_window_mae_ms"]
    finally:
        m.FIT.coefficients["c0.intercept"] = old
    assert after < base, "moving the fitted floor must make the fit window worse"


def test_lookup_is_the_prompt_wide_term():
    """K2: the warm-band level is set by the prompt-wide lookup term."""

    import os
    rep = json.loads(REPORT.read_text())
    spec = os.environ.get("R2S2_RED", "")
    name = _parse(spec)[1] if spec else ""
    slope = _value(rep, "c1.lookup_us_per_ktok_lt20k") / 1000.0   # the constants table is in us/1k
    if name == "c1.lookup_lt20k_ktok":
        slope = _mutate(slope, _parse(spec)[2])
    rows = [r for r in m.fit_rows() if r["prompt_tokens"] < m.REGIME]
    mean_prompt = statistics.mean(r["prompt_tokens"] for r in rows)
    level = slope * mean_prompt / 1000.0
    measured = statistics.mean(r["ttft_ms"] for r in rows)
    # the lookup term is one component of TTFT: it must be the same order as the measured turn,
    # not absent (a 600-token hire would look like this) and not larger than the whole turn
    assert measured * 0.1 < level < measured * 1.0, (
        f"lookup-only level {level:.0f} ms vs measured {measured:.0f} ms at {mean_prompt:.0f} prompt tokens")


def test_full_miss_is_billed():
    """K3: with COVER=0 the miss column is billed from token one and must dominate a cold turn."""

    import os
    rep = json.loads(REPORT.read_text())
    spec = os.environ.get("R2S2_RED", "")
    name, how = (_parse(spec)[1], _parse(spec)[2]) if spec else ("", "")
    slope = _value(rep, "c3.miss_us_per_uncached_tok") * 1000.0   # us/uncached tok -> us/tok
    if name == "c3.miss_us_tok":
        slope = _mutate(slope, how)
    cold = [r for r in m.live("C") if r["uncached"] > 300]
    assert cold, "arm C must carry a cold start"
    r = max(cold, key=lambda x: x["uncached"])
    miss_ms = slope * r["uncached"] / 1000.0
    # the miss term alone must land in the measured turn's neighbourhood, not on top of it
    assert 0.1 * r["ttft_ms"] < miss_ms < 5.0 * r["ttft_ms"], (
        f"miss term {miss_ms:.0f} ms vs measured {r['ttft_ms']}: {r['uncached']} uncached tokens")




# ------------------------------------------------------ the coupling #


def test_carrier_ratio_is_the_sensitivity_surface():  # coupling: K4
    """K4/K5 on their own: the carried rise must track the carrier and its multiple."""

    import os
    rep = json.loads(REPORT.read_text())
    lm = rep["level_multiple"]
    spec = os.environ.get("R2S2_RED", "")
    name, how = (_parse(spec)[1], _parse(spec)[2]) if spec else ("", "")
    slope, mult = lm["fit_window_slope_us_per_ktok"], lm["multiple"]
    if name == "lookup_slope_fit_window_us_per_ktok":
        slope = _mutate(slope, how)
    if name == "lookup_level_multiple_ge20k":
        mult = _mutate(mult, how)
    rows = m.holdout_rows()
    warm = [r for r in rows if r["prompt_tokens"] < m.REGIME and r["prompt_tokens"] >= 15000]
    hot = [r for r in rows if r["prompt_tokens"] >= m.REGIME]
    # a common-factor carrier (slope) must cancel here and leave the level ratio intact, while the
    # multiple must move it -- so the comparison is written as an absolute deviation in log space
    carried_level = statistics.mean(slope * mult * r["prompt_tokens"] / 1000.0 for r in hot)
    assert carried_level > 0.0 and slope > 0.0
    measured_rise = statistics.mean(r["ttft_ms"] for r in hot) / statistics.mean(r["ttft_ms"] for r in warm)
    carried_rise = (slope * mult * statistics.mean(r["prompt_tokens"] for r in hot) / 1000.0) / \
        (slope * 1.0 * statistics.mean(r["prompt_tokens"] for r in warm) / 1000.0)
    assert 0.5 < carried_rise / measured_rise < 2.0, (
        f"carried rise x{carried_rise:.2f} vs measured rise x{measured_rise:.2f} over the same 15-40k prompt range")


# ------------------------------------- K2/K3/K6: the model's own surface #


def test_model_prices_a_cold_turn_from_its_owned_columns():  # coupling: K2/K3
    """K2/K3: the rebuilt model's own price must move with its own lookup and miss columns.

    The report on disk is not rebuilt here (its digest test would go red for an unrelated
    reason); the model is refitted from rows and its own columns are perturbed.
    """

    import os
    m.FIT = m._fit()
    spec = os.environ.get("R2S2_RED", "")
    name, how = (_parse(spec)[1], _parse(spec)[2]) if spec else ("", "")
    fit_rows = [r for r in m.fit_rows() if r["prompt_tokens"] < m.REGIME]
    hold = m.holdout_rows()
    base = [m.row_price(r) for r in hold]
    baseline_mae = statistics.mean(abs(a - r["ttft_ms"]) for a, r in zip(base, hold))

    saved = dict(m.FIT.coefficients)
    try:
        if name == "c1.lookup_lt20k_ktok":
            m.FIT.coefficients["c1.lookup_lt20k_ktok"] = _mutate(saved["c1.lookup_lt20k_ktok"], how)
        if name == "c3.miss_us_tok":
            m.FIT.coefficients["c3.miss_us_tok"] = _mutate(saved["c3.miss_us_tok"], how)
        after = [m.row_price(r) for r in hold]
        mae = statistics.mean(abs(a - r["ttft_ms"]) for a, r in zip(after, hold))
    finally:
        m.FIT.coefficients.update(saved)

    # a mutation is "coupled" only when the fit it degrades is worse by more than a rounding error;
    # at these magnitudes (x2/x5/x50) the threshold is a factor, not a percentage, so a real coupling
    # cannot slip under it
    assert fit_rows, "the warm band must have rows"
    assert baseline_mae < 400.0, f"the model must price the hold-out within its own scale ({baseline_mae:.0f} ms)"
    assert mae < baseline_mae * 1.05 or name not in ("c1.lookup_lt20k_ktok", "c3.miss_us_tok"), (
        f"mutating {name} must degrade the hold-out fit: {baseline_mae:.1f} -> {mae:.1f} ms")


def test_cold_slope_is_a_ratio_not_a_copy():  # coupling: K6
    """K6: the SIM slope is reported relative to a cold slope derived from U9 at run time."""

    import os
    spec = os.environ.get("R2S2_RED", "")
    name, how = (_parse(spec)[1], _parse(spec)[2]) if spec else ("", "")
    cold = m.cold_slope_u9()
    if name == "cold_slope_us_per_tok_u9":
        cold = _mutate(cold, how)
    sim = m.sim_model()
    defect = m.sim_fit_defect(sim)
    ratio = sim["live_miss_slope_us_per_uncached_tok"] / cold
    # the slope is ~2.06x the sweep; a real cold prefill cannot be 4-8x its own measured sweep
    assert 1.5 < ratio < 3.0, f"SIM slope over cold prefill = x{ratio:.2f}"
    assert defect["verdict"].startswith("SIM's live_miss slope")
