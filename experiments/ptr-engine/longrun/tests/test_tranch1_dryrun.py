#!/usr/bin/env python3
"""TRANCH1-DRYRUN / -2 — red -> green on the 3,838 wall trap AND on the claim switch.

GREEN: `tranch1_dryrun.py --check` over the ten real manifests never names the trap; the
       manifests carry design_cap_tokens=10616 for every arm and all four treatments fire
       inside the 48-turn horizon. Two runs exist, and the claim is what separates them:
       `--hypothesis H1` (TRANCH1-DRYRUN) exits 1, because G3 refuses n=48 < 60 for all ten
       cells; `--hypothesis H2` (TRANCH1-DRYRUN-2) exits 0, because H2 needs n >= 1.
RED:   the same driver against a /tmp copy of v8 whose `wall_tokens_by_arm` is lowered to
       3,838 must make `--check` exit 1 and NAME THE TRAP. 3,838 is the dead top-level
       value, below v8's own first prompt (3,848), so the wall/first-eviction treatments
       fire near T2 and both transcript arms collapse into each other.

The H1-vs-H2 exit codes are the claim guard: switching the flag cannot make a held grid
green without the cells genuinely making a claim their own n supports.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONG, "..", "..", ".."))
DRIVER = os.path.join(ROOT, "experiments", "ptr-engine", "tools", "tranch1_dryrun.py")
FIXTURE = os.path.join(LONG, "tasks-v6", "LR-01.v8.json")
MEASURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure")
REPORT = os.path.join(MEASURE, "TRANCH1-DRYRUN.json")
REPORT2 = os.path.join(MEASURE, "TRANCH1-DRYRUN-2.json")


def run(args):
    p = subprocess.run([sys.executable, DRIVER] + args, cwd=ROOT,
                       capture_output=True, text=True, timeout=900)
    return p.returncode, p.stdout + p.stderr


def test_rehearsal_report_shape():
    with open(REPORT, encoding="utf-8") as f:
        rep = json.load(f)
    assert len(rep["cells"]) == 10
    names = [os.path.basename(c["manifest_path"]) for c in rep["cells"]]
    assert len(set(names)) == 10, names
    for c in rep["cells"]:
        assert c["design_cap_tokens"] == 10616, (c["arm"], c["design_cap_tokens"])
        assert c["spawns"] == 0 and c["network_events"] == 0
        key = {"transcript-grow": "grow_evict_turn", "transcript-compact": "compact_wall_turn",
               "lease-reopen": "lease_step_turn", "pointer-stable": "pointer_prefix_turn"}[c["arm"]]
        assert c["treatments"][key] is not None, (c["arm"], key)
        assert c["treatments"][key] <= 48, (c["arm"], key, c["treatments"][key])
    firsts = {a: c["treatments"][k] for c in rep["cells"]
              for a, k in (("transcript-grow", "grow_evict_turn"),
                           ("transcript-compact", "compact_wall_turn"),
                           ("lease-reopen", "lease_step_turn"),
                           ("pointer-stable", "pointer_prefix_turn"))
              if c["arm"] == a}
    assert firsts == {"transcript-grow": 21, "transcript-compact": 21,
                      "lease-reopen": 23, "pointer-stable": 2}, firsts
    assert rep["total_projected_requests"] == 530
    assert rep["stamp"] == "stamped"


def test_green_check_never_names_the_trap():
    rc, out = run(["--check", "--manifests", MEASURE, "--hypothesis", "H1"])
    assert "THE TRAP" not in out, out
    assert "design_cap_tokens=3838" not in out, out
    # the held grid is reported as a refusal of the ten cells, not a silent pass
    assert rc == 1, out
    assert out.lower().count("g3 refused") == 10, out


def test_h2_check_passes_where_h1_fails():
    """The claim switch: same ten cells' shape, a claim their own n can carry."""
    rc1, out1 = run(["--check", "--manifests", MEASURE, "--hypothesis", "H1"])
    rc2, out2 = run(["--check", "--manifests", MEASURE, "--hypothesis", "H2"])
    assert rc1 == 1 and "g3 refused" in out1.lower(), out1
    assert rc2 == 0, out2
    assert "PASS" in out2, out2


def test_h2_rehearsal_all_ten_allowed():
    with open(REPORT2, encoding="utf-8") as f:
        rep = json.load(f)
    assert rep["all_ten_allowed"] is True, rep["all_ten_allowed"]
    assert rep["zero_network"] is True and rep["zero_spawns"] is True
    assert rep["stamp"] == "stamped" and rep["pins_moved"] == []
    assert rep["claim_frame"]["per_cell_hypothesis"] == "H2"
    assert len(rep["cells"]) == 10
    for c in rep["cells"]:
        assert c["g1"]["decision"] == "allow", c
        assert c["g2"]["decision"] == "allow", c
        assert c["g3"]["decision"] == "allow", c
        assert c["g3"]["n"] == 48
        assert c["design_cap_tokens"] == 10616
        assert c["spawns"] == 0 and c["network_events"] == 0
        assert c["manifest_path"].endswith(".json")
    names = [os.path.basename(c["manifest_path"]) for c in rep["cells"]]
    assert len(set(names)) == 10 and all(n.startswith("dryrun2-t2-") for n in names), names
    assert rep["total_projected_requests"] == 530


def test_both_gates_behave_under_the_rehearsal():
    with open(REPORT2, encoding="utf-8") as f:
        pr = json.load(f)["gate_probes"]
    assert pr["g3_h2_n48"]["decision"] == "allow"
    assert pr["g3_h2_n48"]["n"] == 48 and pr["g3_h2_n48"]["min_n"] == 1
    assert pr["g3_h1_n48"]["decision"] == "refused"
    assert "only at n >= 60" in pr["g3_h1_n48"]["verbatim"]
    assert "n=48" in pr["g3_h1_n48"]["verbatim"]
    assert pr["g2_2880"]["decision"] == "allow"
    assert pr["g2_2880"]["ratio"] == 1.0
    assert pr["g2_2881"]["decision"] == "refused"
    assert "2881" in pr["g2_2881"]["verbatim"]


def test_h1_is_not_smuggled_into_the_launch():
    with open(REPORT2, encoding="utf-8") as f:
        rep = json.load(f)
    assert rep["h1_occurrences"]["count"] == 0, rep["h1_occurrences"]
    assert rep["h1_occurrences"]["scanned"] == {"launch_commands": 10, "manifests": 10}
    cmds = rep["launch_commands"]
    assert len(cmds) == 10
    for c in cmds:
        argv, shell = c["argv"], c["shell"]
        assert "H1" not in " ".join(argv) + shell
        assert argv[argv.index("--hypothesis") + 1] == "H2"
        assert argv[argv.index("--reps") + 1] == "1"
        assert argv[argv.index("--max-wall") + 1] == "2880"
        assert "LR-01.v8.json" in " ".join(argv)
        assert c["warmup"]["prompt_tokens"] == 8
    assert sum(c["warmup"]["requests"] for c in cmds) == 4, "one 8-token warm-up per arm"
    plan = rep["pooled_analysis_plan"]
    assert plan["n_per_arm"]["pointer-stable"]["n"] == 144
    assert plan["n_per_arm"]["transcript-grow"]["n"] == 144
    assert all(v["above_h1_floor_60"] for v in plan["n_per_arm"].values())
    assert "quantile_ci" in plan["call"] and "turn_latency_rows" in plan["selector"]
    price = rep["price"]
    assert price["requests_per_cell"] == 53
    assert price["total_new_requests"] == 530
    assert price["g1_displayed_per_cell"] == 1154
    assert "CUMULATIVE" in price["g1_is_cumulative"]


def test_red_trap_fixture_is_named():
    tmp = tempfile.mkdtemp(prefix="tdr-red-")
    with open(FIXTURE, encoding="utf-8") as f:
        fx = json.load(f)
    fx["wall_tokens_by_arm"] = {a: 3838 for a in fx["wall_tokens_by_arm"]}
    trap = os.path.join(tmp, "LR-01.v8.trap.json")
    with open(trap, "w", encoding="utf-8") as f:
        json.dump(fx, f)
    mans = os.path.join(tmp, "manifests")
    rc_run, out_run = run(["--fixture", trap, "--out-dir", mans, "--hypothesis", "H2"])
    assert rc_run == 0, out_run
    rc, out = run(["--check", "--fixture", trap, "--manifests", mans,
                   "--hypothesis", "H2"])
    assert rc == 1, out
    assert "THE TRAP" in out, out
    assert "3838" in out, out
    assert "dead top-level" in out, out
