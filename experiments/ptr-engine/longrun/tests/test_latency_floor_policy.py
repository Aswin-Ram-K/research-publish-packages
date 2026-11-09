#!/usr/bin/env python3
"""test_latency_floor_policy.py - a p95 needs BOTH counts to clear the floor.

The policy (LATENCY-UNDER-DISPUTE): a cell's p95 is produced only if
`n_raw >= 60` AND `n_dedup >= 60`; otherwise it is refused by name with both
counts quoted. Reason: rule R's justification failed `V-DUPLICATE-RULE`
(`content_sha256` is `sha256(assistant content)` - a response hash, 869/869 rows
at `run_longrun.py:1493`), so a disputed de-duplication must not be able to
raise the evidence to publication.

Cases
-----
(a) G7's pair (n_raw 68, n_dedup 51) => NOT publishable, both counts quoted
(b) G8 (72/70) and G9 (72/61) => publishable on both counts
(c) a pair that straddles the floor either way (59/60, 60/59) => NOT publishable
(d) the published artefact: G7 withheld with the dispute label, G8/G9 published
    on both counts with the same label; every cell's p95 state is pinned to the
    artefact's OWN count (`ttft_used`), not to a literal - a point iff that
    count clears 60, a refusal naming the floor below it
(e) what rule R cannot touch: the p50 inventory arithmetic and the G4 four-arm
    table at 48 raw = 48 de-duplicated, 0 removed
(f) the operator number, derived from the cells: no p95 point is published and
    no inter-arm comparison exists
(g) synthetic floor fixture: the analyser produces a p95 at n=65 and REFUSES at
    n=59, 45 and 21 naming the floor - the floor is tested in both directions on
    data independent of the artefact

Re-pinned 2026-10-26 by `LATENCY-FLOOR-TEST-REPIN`, to the artefact at run time
and not to a literal. The previous pin (LATENCY-FIGURE-HONESTY) hard-coded
`NEW_N = {"G8": 45, "G9": 37}`; `LATENCY-DEDUPE-FIX` then changed the turn
de-duplication and the report's own `report_numbers` field records the move
verbatim - "G8 n_turn_dedup 46->48, ttft_used 45->47; G9 37->48, 37->48" - so the
pin went stale while the policy did not. Case (d) now reads `ttft_used` out of
`LATENCY-REPORT.json` itself; no per-turn count is written down here.

Red->green: `LATENCY_FLOOR_POLICY=off` reverts the gate to "either count
clears the floor" (the pre-policy union rule) and this file must FAIL, because
G7 at n_raw=68 would then be publishable.

    python3 experiments/ptr-engine/longrun/tests/test_latency_floor_policy.py
    LATENCY_FLOOR_POLICY=off python3 experiments/ptr-engine/longrun/tests/test_latency_floor_policy.py  # must FAIL

Offline: reads the analyser module and the published report JSON. No request,
no network, no rows / grade / ledger / TVS file is read or modified.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PTR = os.path.dirname(os.path.dirname(HERE))            # experiments/ptr-engine
TOOLS = os.path.join(PTR, "tools")
ANALYZER = os.environ.get("LATENCY_ANALYZER_PATH",
                          os.path.join(PTR, "longrun", "analyze_stats.py"))
REPORT_TOOL = os.environ.get("LATENCY_REPORT_PATH",
                             os.path.join(TOOLS, "latency_report.py"))
REPORT_JSON = os.environ.get(
    "LATENCY_REPORT_JSON", os.path.join(PTR, "measure", "LATENCY-REPORT.json"))

FLOOR95 = 60          # analyze_stats.min_n_for(0.95); asserted from the module
DISPUTE = ("disputed (V-DUPLICATE-RULE fail: response hash, "
           "not request identity)")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


stats = _load("analyze_stats", ANALYZER)
report_tool = _load("latency_report", REPORT_TOOL)
POLICY = report_tool.policy_enabled()


def check_floor():
    assert stats.min_n_for(0.95) == FLOOR95, \
        "the analyser's p95 floor moved: %r" % (stats.min_n_for(0.95),)


def check_p95_pinned(label, p, expected_n=None):
    """Pin one cell's p95 to its OWN count: a point iff n clears the floor.

    Returns "point" or "refused". Every failure names the floor and the count,
    so a mutation that lets a p95 through below 60, or a report that refuses a
    p95 whose count clears 60, fails on the contradiction rather than on a
    stale literal.
    """
    n = p.get("n")
    if expected_n is not None:
        assert n == expected_n, (
            "%s: p95.n %r != the artefact's own count %r: %r"
            % (label, n, expected_n, p))
    if p.get("point") is not None:
        assert isinstance(n, int) and n >= FLOOR95, (
            "%s: a p95 POINT at n=%r, below the floor %d: %r"
            % (label, n, FLOOR95, p))
        assert p.get("lo") is not None and p.get("hi") is not None, (label, p)
        return "point"
    assert p.get("refused"), \
        "%s: neither a p95 point nor a refusal: %r" % (label, p)
    if isinstance(n, int) and n >= FLOOR95:
        raise AssertionError(
            "%s: CONTRADICTION - n=%d clears the floor %d but the cell carries "
            "a refusal instead of a p95: %r" % (label, n, FLOOR95, p))
    assert "minimum n for p95 is %d" % FLOOR95 in p["refused"], \
        "%s: refusal does not name the floor: %r" % (label, p["refused"])
    return "refused"


def case_a_withheld():
    """(a) G7's real pair is NOT publishable, and both counts are quoted."""
    g = report_tool.publication_gate(68, 51, FLOOR95)
    assert g["publish"] is False, \
        "G7 (n_raw=68, n_dedup=51) was PUBLISHED: %r" % (g,)
    assert "n_raw=68" in g["basis"] and "n_dedup=51" in g["basis"], g["basis"]
    assert "60" in g["basis"], g["basis"]
    return g["basis"]


def case_b_survivors():
    """(b) G8 and G9 clear the floor on BOTH counts."""
    out = []
    for n_raw, n_dedup in ((72, 70), (72, 61)):
        g = report_tool.publication_gate(n_raw, n_dedup, FLOOR95)
        assert g["publish"] is True, (n_raw, n_dedup, g)
        out.append("%d/%d" % (n_raw, n_dedup))
    return ", ".join(out)


def case_c_straddle():
    """(c) one count below the floor withholds the cell, whichever side it is."""
    for n_raw, n_dedup in ((59, 60), (60, 59), (0, 60), (68, 0)):
        g = report_tool.publication_gate(n_raw, n_dedup, FLOOR95)
        assert g["publish"] is False, (n_raw, n_dedup, g)
    return "59/60, 60/59, 0/60, 68/0 all withheld"


def case_d_artefact():
    """(d) the published JSON carries the policy, and every p95 matches its n."""
    with open(REPORT_JSON, encoding="utf-8") as fh:
        report = json.load(fh)
    cells = {(c["grid_id"], c["arm"]): c for c in report["cells"]}

    g7 = cells[("G7", "pointer-stable")]
    assert report_tool.publication_gate(
        g7["n_raw"], g7["n_dedup"], FLOOR95)["publish"] is False, g7.get(
            "withdrawal_basis")
    assert g7["p95"].get("point") is None, g7["p95"]
    assert g7["p95"].get("refused"), g7["p95"]
    assert g7["dedup_rule_status"] == DISPUTE, g7.get("dedup_rule_status")
    assert "both count" in g7["withdrawal_basis"] or \
           "both-count" in g7["withdrawal_basis"], g7["withdrawal_basis"]

    # G8/G9 publish on the de-duplicated REQUEST pair while their per-turn p95
    # is decided by the turn population. Both counts are read from the artefact:
    # `ttft_used` is the statistic population (`analyze_stats.quantile_ci`'s
    # n), so no per-turn literal is pinned here.
    states = {}
    for gid in ("G8", "G9"):
        c = cells[(gid, "pointer-stable")]
        assert report_tool.publication_gate(
            c["n_raw"], c["n_dedup"], FLOOR95)["publish"] is True, gid
        assert c["dedup_rule_status"] == DISPUTE, c.get("dedup_rule_status")
        assert c["withdrawal_basis"].startswith("both counts clear the floor"), \
            c["withdrawal_basis"]
        assert "n_raw=%d" % c["n_raw"] in c["withdrawal_basis"], c["withdrawal_basis"]
        assert "n_dedup=%d" % c["n_dedup"] in c["withdrawal_basis"], \
            c["withdrawal_basis"]
        assert isinstance(c.get("ttft_used"), int), (gid, c.get("ttft_used"))
        states[gid] = check_p95_pinned(
            gid, c["p95"], c["ttft_used"])
        assert states[gid] == ("point" if c["ttft_used"] >= FLOOR95
                               else "refused"), (gid, states[gid])

    # whole-report sweep: no bare p95, no point below the floor, no refusal
    # above it, and every point still gated by both request counts.
    sweep = {"point": 0, "refused": 0}
    for c in report["cells"]:
        label = "%s/%s" % (c["grid_id"], c["arm"])
        state = check_p95_pinned(label, c.get("p95") or {},
                                 c.get("ttft_used"))
        sweep[state] += 1
        if state == "point":
            assert c["n_raw"] is not None and c["n_dedup"] is not None, label
            assert report_tool.publication_gate(
                c["n_raw"], c["n_dedup"], FLOOR95)["publish"] is True, label
    assert sweep["point"] + sweep["refused"] == len(report["cells"]), sweep

    w = [x for x in report["withdrawn"] if x["grid_id"] == "G7"]
    assert len(w) == 1, report["withdrawn"]
    assert w[0]["n_raw"] == 68 and w[0]["n_dedup"] == 51, w[0]
    assert w[0]["old"]["point"] == 318.143, w[0]["old"]
    assert w[0]["old"]["n"] == 68, w[0]["old"]
    assert "V-DUPLICATE-RULE" in w[0]["withdrawal_basis"], w[0]
    assert "both count" in w[0]["withdrawal_basis"] or \
           "both-count" in w[0]["withdrawal_basis"], w[0]

    pol = report["floor_policy"]
    assert pol["rule"].startswith("a cell's p95 is produced only if"), pol["rule"]
    assert "disputed" in pol["reason"], pol["reason"]
    assert report["disputed_rule"]["owner"] == "DEDUPE-ROOT-CAUSE"
    return ("G7 withheld on 68/51; G8/G9 pass the both-count gate %d/%d, %d/%d "
            "and their p95 state follows the artefact's own ttft_used (%s); "
            "sweep %d points / %d refusals"
            % (cells[("G8", "pointer-stable")]["n_raw"],
               cells[("G8", "pointer-stable")]["n_dedup"],
               cells[("G9", "pointer-stable")]["n_raw"],
               cells[("G9", "pointer-stable")]["n_dedup"],
               ", ".join("%s=%d" % (g, cells[(g, "pointer-stable")]["ttft_used"])
                         for g in ("G8", "G9")),
               sweep["point"], sweep["refused"]))


def case_e_unaffected():
    """(e) the p50 column and the G4 four-arm table are not rule-R products."""
    with open(REPORT_JSON, encoding="utf-8") as fh:
        report = json.load(fh)
    # Pinned to the artefact and to the arithmetic that must hold between its
    # three numbers, not to a stale count: total == 8 + 3 was true of the
    # LATENCY-FIGURE-HONESTY artefact and is not re-typed here.
    u = report["unaffected_by_rule_r"]
    p50_cells = [c for c in report["cells"]
                 if (c.get("p50") or {}).get("point") is not None]
    assert u["p50_cells_total"] == len(p50_cells), (
        u["p50_cells_total"], len(p50_cells))
    assert (u["p50_cells_bitexact"] + len(u["p50_cells_moved"])
            == u["p50_cells_total"]), u
    g4 = u["g4_run_c_v2"]
    assert g4["arms_count"] == 4, g4
    assert g4["n_raw_per_arm"] == [48] and g4["n_dedup_per_arm"] == [48], g4
    assert g4["excess"] == [0], g4
    assert g4["p50_moved"] is False, g4
    return ("%d p50 cells (%d bit-identical, %d moved; 9+3 not re-typed), "
            "G4 4 arms 48/48, 0 removed"
            % (u["p50_cells_total"], u["p50_cells_bitexact"],
               len(u["p50_cells_moved"])))


def case_f_operator_number():
    """(f) the operator number, derived from the cells: no published p95."""
    with open(REPORT_JSON, encoding="utf-8") as fh:
        report = json.load(fh)
    inv = report["p95_inventory"]
    p95_cells = [c for c in report["cells"]
                 if (c.get("p95") or {}).get("point") is not None]
    refused_cells = [c for c in report["cells"]
                     if (c.get("p95") or {}).get("refused")]
    arms = sorted({c["arm"] for c in p95_cells})
    assert inv["cells_with_p95"] == len(p95_cells), (
        inv["cells_with_p95"], len(p95_cells))
    # `cells_with_p95_raw` counts p95 POINTS in the report's PRIOR artefact
    # (latency_report.py:672-674 reads `prior["cells"]`), not refusals; it is
    # therefore not a function of the current cells and is not re-derived here.
    assert isinstance(inv["cells_with_p95_raw"], int), inv["cells_with_p95_raw"]
    assert inv["cells_with_p95_raw"] >= 0, inv["cells_with_p95_raw"]
    assert len(p95_cells) + len(refused_cells) == len(report["cells"]), (
        len(p95_cells), len(refused_cells), len(report["cells"]))
    assert inv["arms_with_a_p95"] == arms, (inv["arms_with_a_p95"], arms)
    assert inv["arms_with_a_p95_count"] == len(arms), inv
    assert inv["pairs_with_p95"] == 0, inv["pairs_with_p95"]
    assert inv["any_inter_arm_comparison"] is False, inv
    return ("%d published p95, %d refused at their per-turn n, %d arms, "
            "0 p95 pairs" % (len(p95_cells), len(refused_cells), len(arms)))


def case_g_synthetic_floor():
    """(g) the floor cuts both ways on synthetic data, not just on the artefact."""
    values = [float(i) for i in range(1, 66)]          # 65 admissible values
    point, lo, hi, n = stats.quantile_ci(values, 0.95, resamples=200, seed=7)
    assert point is not None and n == 65, (point, n)
    assert lo <= point <= hi, (lo, point, hi)
    for nvals in (59, 45, 21):
        try:
            stats.quantile_ci(values[:nvals], 0.95, resamples=200, seed=7)
        except stats.InsufficientSamples as exc:
            msg = str(exc)
            assert "minimum n for p95 is %d" % FLOOR95 in msg, msg
            assert "n=%d" % nvals in msg, msg
        else:
            raise AssertionError(
                "the analyser produced a p95 at n=%d, below the floor %d"
                % (nvals, FLOOR95))
    return "p95 point at n=65 (lo<=point<=hi); refused at 59/45/21 naming 60"


def main():
    check_floor()
    results = {
        "a_withheld": case_a_withheld(),
        "b_survivors": case_b_survivors(),
        "c_straddle": case_c_straddle(),
        "d_artefact": case_d_artefact(),
        "e_unaffected": case_e_unaffected(),
        "f_operator": case_f_operator_number(),
        "g_synthetic": case_g_synthetic_floor(),
    }
    for name in ("a_withheld", "b_survivors", "c_straddle", "d_artefact",
                 "e_unaffected", "f_operator", "g_synthetic"):
        print("PASS %-12s %s" % (name, results[name]))
    print("floor95=%d policy_enabled=%s env=LATENCY_FLOOR_POLICY"
          % (FLOOR95, POLICY))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
