"""GRID-2-FINAL — guards on the final report's honesty rules.

Every test here is offline and reads only files on disk.  The invariants they
protect are the ones this report could get wrong quietly:

* `ABSENT` must never be rendered as usable (analyze_stats.py:749 keeps an
  unstamped cell, which is how a rejected cell enters an analysis);
* a refused p95 keeps its refusal text and is never replaced by a number;
* `n_eff` sits beside every interval and is the frozen formula;
* the frozen H1 reading is reproduced from the rows, not copied from a handoff;
* the replicate collapse (288 turn rows -> 96 analysed) is reported, not hidden;
* H3 is a placeholder, never a computed numerator;
* TVS is `UNDEFINED`, never a token count;
* the price line states BOTH the asserted 162/cell and the recomputed
  marginal 79.4/cell, because only one of them is a measurement.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
TOOLS = os.path.join(PKG, "tools")
LONGRUN = os.path.join(PKG, "longrun")
for _p in (TOOLS, LONGRUN):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import analyze_stats as S          # noqa: E402
import grid2_final_report as G     # noqa: E402
import run_grid_report as RG       # noqa: E402


@pytest.fixture(scope="module")
def body():
    return G.build()


def test_census_covers_all_sixteen_cells(body):
    assert len(body["census"]) == 16
    assert [c["cell"] for c in body["census"]] == list(range(1, 17))


def test_request_rows_sum_to_the_ledger_delta(body):
    """The billing column is a measurement: rows == requests == ledger delta."""
    total = sum(c["requests_billed"] for c in body["census"])
    assert total == 1270
    assert body["price"]["grid_delta"] == 1270


def test_absent_stamp_is_never_usable(body):
    absent = [c for c in body["census"] if c["usable_for"] == "ABSENT"]
    assert len(absent) == 2, "the two exit-4 cells have no manifest at all"
    usable_files = set(body["usable"])
    for c in absent:
        assert c["rows_file"] not in usable_files
        assert c["turns_match_manifest"] == "ABSENT"
    # and the reader this report exists to correct would have kept them
    kept, records = S.select_usable_cells(
        [(c["rows_file"], c["rows_on_disk"], []) for c in absent], manifests={})
    assert len(kept) == len(absent), (
        "analyze_stats.select_usable_cells keeps unstamped cells; the report must "
        "exclude them by name instead")


def test_exactly_six_usable_and_they_are_the_two_arms(body):
    assert len(body["usable"]) == 6
    assert sorted({c["arm"] for c in body["census"]
                   if c["rows_file"] in set(body["usable"])}) == \
        ["lease-reopen", "pointer-stable"]


def test_stamped_out_cells_are_excluded_by_name(body):
    stamped_out = [c for c in body["census"] if c["usable_for"] == []]
    assert len(stamped_out) == 8
    assert all(c["rows_file"] not in set(body["usable"]) for c in stamped_out)
    assert all(c["reason"].startswith("zero-marker") for c in stamped_out)


def test_manifest_nests_rows_path_under_run(body):
    """The (A) defect the census must walk around: top-level path is null."""
    for c in body["census"]:
        if c["manifest"] == "ABSENT":
            continue
        assert c["rows_path_nesting"]["rows_path_top"] in (None, "ABSENT")
        assert c["rows_path_nesting"]["run.rows_path"].endswith(".jsonl")


def test_usable_turn_counts_match_declared_n(body):
    for c in body["census"]:
        if c["usable_for"] == "ABSENT":
            continue
        if isinstance(c["usable_for"], list) and c["usable_for"]:
            assert c["turns_on_disk"] == 48
            assert c["turns_match_manifest"] is True


def test_h1_reproduces_the_frozen_reading_exactly(body):
    ps = body["h1"]["per_arm"]["pointer-stable"]
    lr = body["h1"]["per_arm"]["lease-reopen"]
    assert ps["n_used"] == 48 and lr["n_used"] == 48
    assert ps["p50"]["point"] == pytest.approx(156.151, abs=1e-3)
    assert ps["p50"]["lo"] == pytest.approx(146.306, abs=1e-3)
    assert ps["p50"]["hi"] == pytest.approx(291.926, abs=1e-3)
    assert ps["r_lag1"] == pytest.approx(0.2949, abs=5e-4)
    assert ps["n_eff"] == pytest.approx(26.14, abs=5e-2)
    assert lr["p50"]["point"] == pytest.approx(198.395, abs=1e-3)
    assert lr["r_lag1"] == pytest.approx(-0.1188, abs=5e-4)
    assert lr["n_eff"] == pytest.approx(60.95, abs=5e-2)


def test_p95_is_refused_with_its_text_verbatim(body):
    for arm in ("pointer-stable", "lease-reopen"):
        p95 = body["h1"]["per_arm"][arm]["p95"]
        assert "refused" in p95, "p95 must not exist below the floor"
        assert "minimum n for p95 is 60" in p95["refused"]
        assert "point" not in p95


def test_n_eff_is_the_frozen_formula_beside_every_interval(body):
    for arm, rec in body["h1"]["per_arm"].items():
        n, r = rec["n_used"], rec["r_lag1"]
        assert rec["n_eff"] == pytest.approx(n * (1 - r) / (1 + r), rel=1e-9)
        assert rec["n_eff_formula"].startswith("n(1-r)/(1+r)")


def test_floor_is_untouched(body):
    assert S.min_n_for(0.95) == 60
    assert RG.EFFECTIVE_N_FLOOR == 60


def test_h1_verdict_is_the_floor_refusal(body):
    assert body["h1"]["verdict"] == "not_adjudicable_floor"
    assert body["h1"]["binding_arm"] == "pointer-stable"
    assert body["h1"]["binding_n_eff"] < 60


def test_replicate_collapse_is_reported_not_hidden(body):
    """288 turn rows on disk, 96 analysed -- the finding, stated as counts."""
    assert body["collapse"]["turns_on_disk_in_usable_cells"] == 288
    assert body["collapse"]["turns_analysed"] == 96
    assert body["collapse"]["dropped_by_selector"] == 192
    for rec in body["h1"]["per_arm"].values():
        assert sum(rec["turns_contributed_by_cell"].values()) == rec["n_used"]


def test_collapse_mix_is_visible_in_contributed_turns(body):
    ps = body["h1"]["per_arm"]["pointer-stable"]["turns_contributed_by_cell"]
    assert max(ps.values()) < 48, "one 48-turn series must not come from one cell"
    assert len(ps) > 1


def test_sensitivity_is_labelled_and_not_the_reading(body):
    for rec in body["h1"]["per_arm"].values():
        sens = rec["sensitivity_rep_preserving"]
        assert sens is not None
        assert sens["n_used"] > rec["n_used"], (
            "rep-preserving pooling must increase n; otherwise the finding is wrong")
    assert body["h1"]["series"].startswith("frozen")


def test_h2_reports_both_limbs_n_and_sign(body):
    h2 = body["h2"]
    assert set(h2["per_arm"]) == {"lease-reopen", "pointer-stable"}
    for rec in h2["per_arm"].values():
        assert rec["n"] > 0
        assert rec["difference_sign"] == 1
        assert rec["cached_inclusive_tokens_per_turn"] > rec["uncached_tokens_per_turn"]
    assert h2["same_sign_across_usable_arms"] is True
    # the frozen pair cannot be formed: transcript-grow has no usable cell
    assert h2["pair"]["present"] is False
    assert h2["pair"]["verdict"] == "not_adjudicable"


def test_h3_is_a_placeholder_never_a_number(body):
    h3 = body["h3"]
    assert h3["x_12"] == "x/12" and h3["x_9"] == "x/9"
    assert h3["answered_ratio"] == "answered_ratio"
    assert not isinstance(h3["x_12"], (int, float))
    assert h3["only_contributing_arm"] == "pointer-stable"


def test_tvs_is_undefined_with_a_counted_reason(body):
    tvs = body["tvs"]
    assert tvs["value"] == "UNDEFINED"
    assert tvs["n_verified_success_arm_level"] == 0
    assert tvs["n_first_checkpoint_pass"] == 0
    assert "n_verified_success" in tvs["why"]
    for token in ("tokens_to_verified", "prompt_tokens", "completion_tokens"):
        assert token not in json.dumps(tvs["value"])


def test_price_states_the_asserted_arithmetic_verbatim(body):
    p = body["price"]
    assert p["pair_only_gen7"]["cost_asserted"] == 1944
    assert p["pair_only_gen7"]["short_asserted"] == 215
    assert p["full_gen7"]["cost_asserted"] == 2592
    assert p["full_gen7"]["short_asserted"] == 863
    assert p["remaining"] == 1729


def test_price_recomputes_the_marginal_cost(body):
    p = body["price"]
    assert p["measured_requests_per_cell"] == pytest.approx(1270 / 16)
    assert p["prior_spend_before_grid"] == 1321
    assert p["full_gen7"]["cost_marginal_measured"] == pytest.approx(1270)
    assert p["full_gen7"]["affordable_marginal_measured"] is True
    assert p["binding"] == "instrument", (
        "at the measured marginal price the budget does not bind")
    assert "LEDGER TOTAL" in p["asserted_recomputation"]


def test_report_writes_nothing_but_its_two_artefacts(tmp_path):
    out_json = tmp_path / "G.json"
    out_md = tmp_path / "G.md"
    assert G.main(["--json", str(out_json), "--md", str(out_md)]) == 0
    assert json.loads(out_json.read_text())["schema"] == "grid-2-final/1"
    md = out_md.read_text()
    for needle in ("## 0. Census", "REFUSED — *refusing p95", "UNDEFINED",
                   "not_adjudicable", "79.4 requests/cell"):
        assert needle in md
