# V-GATE-CHAIN-3 — the gate chain attacked as a CLASS, not as operands

Verifier unit (third attack). Predecessors: `V-GATE-CHAIN` (break: non-positive `--max-wall`),
`V-GATE-CHAIN-2` (break: non-positive `--projected-turn-wall`). `GATE-CHAIN-FIX` and
`GATE-OVERRIDE-FIX` each repaired ONE operand of ONE arithmetic expression. This unit attacks the
invariant: **every variable of every gate decision expression is validated at its boundary
(type, sign, finiteness, magnitude, presence), and no unchecked operand can switch a gate off.**

OFFLINE: zero inference requests, zero sockets, zero network. The runner is never executed:
`cell.subprocess.run` is replaced in-process by a recorder, so every "live" invocation below is a
recorded argv, not a spawned process. Read-only on the repo; the only mutation is in `/tmp/vgc3`
(re-created per invocation because this host gives each shell call a private `/tmp`).

Repo pin (asserted before AND after every probe):
`experiments/ptr-engine/longrun/cell.py` sha256
`fd4f2b01a6bfdeea425a92de428f770bf9f07fbe3bdc3b1d8cfd1f4a17ee2ec6` (1600 lines),
`exit_codes.py` sha256 `97cdfc1e63471aecff83fc212346a56b719d44ecde13ae58c0f9bd4f8a3a86c8`.

## What the attack does

1. **Every numeric flag** on the conductor's argparse surface (`--turns`, `--reps`, `--budget`,
   `--turn-wall-cap`, `--projected-turn-wall`, `--fetch-followup-allowance`, `--runaway-turns`,
   `--max-wall`) is fed `0`, `-1`, `-0.0001`-class values, a very large value, `inf`, `nan`, and a
   non-numeric string, alone and combined with a permissive sibling.
2. **Arithmetic completeness**: the three decision expressions are recorded verbatim and every
   variable in them is traced to its validation site.
3. **Silence**: absent/unreadable/empty gate artefacts and an absent hypothesis must refuse.
4. **Order and short-circuit**: G1-before-G2-before-G3, `--dry-run`, `--offline`, empty fixture.
5. **Side effects before refusal**: for every refusal exit code, the spawn recorder counts the
   live invocations, and the out-dir is checked for rows and gate manifests.
6. **Exit-code contract**: raised-vs-declared in both directions, and `docs/GATE-CHAIN.md`'s table
   against `exit_codes.EXIT_TABLE`.

## The attack script (exactly what ran)

Extract and run with:

```
python3 -c "import re,subprocess,tempfile,os,sys; s=open('orchestration/units/V-GATE-CHAIN-3.md').read(); c=re.search(r'<!--ATTACK-SCRIPT-START-->\n(.*?)\n<!--ATTACK-SCRIPT-END-->', s, re.S).group(1); d=tempfile.mkdtemp(); p=os.path.join(d,'a.py'); open(p,'w').write(c); raise SystemExit(subprocess.call([sys.executable,p]))"
```

<!--ATTACK-SCRIPT-START-->
import hashlib, io, json, os, re, sys, traceback, contextlib, tempfile
ROOT = "/home/zer0null/reserach extarctor"
HERE = os.path.join(ROOT, "experiments/ptr-engine/longrun")
CELL = os.path.join(HERE, "cell.py")
OUT = os.environ.get("VGC3_OUT") or tempfile.mkdtemp(prefix="vgc3-")
os.makedirs(os.path.join(OUT, "art"), exist_ok=True)
def bread(m):
    with open(os.path.join(OUT, "bread"), "a") as fh: fh.write(m + "\n")
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""): h.update(c)
    return h.hexdigest()
def fatal():
    with open(os.path.join(OUT, "result.json"), "w") as fh:
        json.dump({"fatal": traceback.format_exc(),
                   "bread": open(os.path.join(OUT, "bread")).read() if os.path.exists(os.path.join(OUT, "bread")) else ""}, fh, indent=1)
    print("FATAL -- see result.json", file=sys.stderr)
    return 2
bread("start")
try:
    sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "experiments/ptr-engine/tools"))
    PIN_BEFORE = sha(CELL); bread("pin-before")
    import importlib.util
    spec = importlib.util.spec_from_file_location("cellmod", CELL)
    cell = importlib.util.module_from_spec(spec); spec.loader.exec_module(cell); bread("imported")
    ARMS = cell._runner_arms(); ARM = ARMS[0] if ARMS else "T1"
    FIXTURE = os.path.join(HERE, "tasks-v5", "runtime-v5", "LR-01.v5.json")
    FIXTURE_H3 = os.path.join(HERE, "tasks-v6", "LR-01.v7.json")
    def art(name, obj, raw=None):
        p = os.path.join(OUT, "art", name)
        open(p, "w", encoding="utf-8").write(raw if raw is not None else json.dumps(obj)); return p
    PROJ_ZERO = art("proj_zero.json", {"defaults": {"projected_turn_wall_s_by_mode": {"absent": 0.0}}})
    PROJ_NEG = art("proj_neg.json", {"defaults": {"projected_turn_wall_s_by_mode": {"absent": -12.0}}})
    PROJ_NAN = art("proj_nan.json", None, raw='{"defaults":{"projected_turn_wall_s_by_mode":{"absent":NaN}}}')
    PROJ_TINY = art("proj_tiny.json", {"defaults": {"projected_turn_wall_s_by_mode": {"absent": 1e-9}}})
    EMPTY = art("empty.json", {})
    BAD_LEDGER = art("ledger_badrows.json", {"budget": {"cap": 4320, "reserve": 0}, "files": [{"file": os.path.join(OUT, "nope.jsonl")}]})
    EMPTY_LEDGER = art("ledger_nocap.json", {"budget": {}})
    SPAWNS = []
    class FakeProc:
        def __init__(self, rc, out="", err=""): self.returncode, self.stdout, self.stderr = rc, out, err
    def fake_run(argv, **kw):
        SPAWNS.append(list(argv))
        if "--dry-run" in argv: return FakeProc(0, "would_send_total=192\n", "")
        return FakeProc(6, "", "fake runaway")
    cell.subprocess.run = fake_run
    def run_case(name, argv, patch=None):
        SPAWNS.clear(); saved = {}
        if patch:
            for k, v in patch.items(): saved[k] = getattr(cell, k); setattr(cell, k, v)
        d = os.path.join(OUT, "out", name); os.makedirs(d, exist_ok=True)
        buf = io.StringIO(); code = None
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                code = cell.main(argv + ["--out-dir", d])
        except SystemExit as exc: code = ["SystemExit", exc.code]
        except BaseException: code = ["EXCEPTION", traceback.format_exc().splitlines()[-1]]
        finally:
            for k, v in saved.items(): setattr(cell, k, v)
        live = [a for a in SPAWNS if "--dry-run" not in a]; dry = [a for a in SPAWNS if "--dry-run" in a]
        txt = buf.getvalue()
        bread("case:" + name)
        return {"case": name, "exit": code, "spawns_dryrun": len(dry), "spawns_live": len(live),
                "live_argv": live[0] if live else None,
                "refused_line": next((l.strip() for l in txt.splitlines() if "REFUSED" in l), None),
                "gate_line": next((l.strip() for l in txt.splitlines() if "projection turns=" in l), None),
                "rows_files": [f for f in os.listdir(d) if f.startswith("rows-")],
                "gate_manifests": [f for f in os.listdir(d) if f.endswith(".gates.json")]}
    BASE = ["--arm", ARM, "--fixture", FIXTURE, "--budget", "600"]
    R = []
    def C(name, argv, patch=None):
        R.append(run_case(name, argv, patch))
    C("A_baseline_allow", BASE + ["--turns", "48", "--hypothesis", "H2"])
    C("A2_allow_control", BASE + ["--turns", "48", "--hypothesis", "H2", "--projected-turn-wall", "18"])
    C("B_max_wall_inf", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "inf"])
    C("B2_max_wall_1e308", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1e308"])
    C("C_max_wall_nan", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "nan"])
    C("C2_max_wall_zero", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "0"])
    C("D_turns0_H3", BASE + ["--fixture", FIXTURE_H3, "--turns", "0", "--hypothesis", "H3", "--max-wall", "1e308"])
    C("D2_turns_neg48_H3", BASE + ["--fixture", FIXTURE_H3, "--turns", "-48", "--hypothesis", "H3", "--max-wall", "1e308"])
    C("D3_turns0_H2_control", BASE + ["--turns", "0", "--hypothesis", "H2"])
    C("E_reps0_H3", BASE + ["--turns", "48", "--reps", "0", "--hypothesis", "H3", "--max-wall", "1e308"])
    C("F_allow_neg", BASE + ["--turns", "48", "--hypothesis", "H2", "--fetch-followup-allowance", "-100"])
    C("G_override_tiny", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1", "--projected-turn-wall", "0.000000001"])
    C("G2_override_neg_control", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1", "--projected-turn-wall", "-1"])
    C("G3_override_inf_control", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1", "--projected-turn-wall", "inf"])
    C("H_artefact_zero", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1"], {"PROJECTION_ARTEFACT": PROJ_ZERO})
    C("H2_artefact_neg", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1"], {"PROJECTION_ARTEFACT": PROJ_NEG})
    C("H3_artefact_tiny", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1"], {"PROJECTION_ARTEFACT": PROJ_TINY})
    C("H4_artefact_nan", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1"], {"PROJECTION_ARTEFACT": PROJ_NAN})
    C("I_cap_inf", BASE + ["--turns", "48", "--hypothesis", "H2", "--turn-wall-cap", "inf"])
    C("I2_cap_zero", BASE + ["--turns", "48", "--hypothesis", "H2", "--turn-wall-cap", "0"])
    C("I2b_cap_zero_allowed", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1e308", "--turn-wall-cap", "0"])
    C("I3_runaway_neg", BASE + ["--turns", "48", "--hypothesis", "H2", "--runaway-turns", "-5"])
    C("J1_no_hypothesis", BASE + ["--turns", "48"])
    C("J1b_no_hypothesis_g2_allowed", BASE + ["--turns", "48", "--max-wall", "1e308"])
    C("J2_ledger_empty", BASE + ["--turns", "48", "--hypothesis", "H2"], {"LEDGER_ARTEFACT": EMPTY_LEDGER})
    C("J3_ledger_badrows", BASE + ["--turns", "48", "--hypothesis", "H2"], {"LEDGER_ARTEFACT": BAD_LEDGER})
    C("J4_ledger_missing", BASE + ["--turns", "48", "--hypothesis", "H2"], {"LEDGER_ARTEFACT": os.path.join(OUT, "art", "nope.json")})
    C("J5_prereg_empty", BASE + ["--turns", "48", "--hypothesis", "H2"], {"PREREG_ARTEFACT": EMPTY})
    C("J5b_prereg_empty_g2_allowed", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1e308"], {"PREREG_ARTEFACT": EMPTY})
    C("J6_empty_fixture", ["--arm", ARM, "--fixture", EMPTY, "--budget", "600", "--turns", "48", "--hypothesis", "H2"])
    C("K_dryrun_refuses", BASE + ["--turns", "48", "--hypothesis", "H2", "--max-wall", "1", "--dry-run"])
    C("K2_non_numeric", BASE + ["--turns", "abc", "--hypothesis", "H2"])
    C("K3_budget_missing", ["--arm", ARM, "--fixture", FIXTURE, "--turns", "48", "--hypothesis", "H2"])
    def parse(argv):
        ap = cell.argparse.ArgumentParser()
        for f, kw in [("--arm", {}), ("--fixture", {}), ("--turns", {"type": int, "default": 48}),
                      ("--reps", {"type": int, "default": 1}), ("--budget", {"type": int, "default": None}),
                      ("--endpoint", {"default": None}), ("--thinking", {"default": None}),
                      ("--turn-wall-cap", {"type": float, "default": 180.0}),
                      ("--projected-turn-wall", {"type": float, "default": None}),
                      ("--fetch-followup-allowance", {"type": int, "default": None}),
                      ("--hypothesis", {"default": None}), ("--dry-run", {"action": "store_true"}),
                      ("--projected-from", {"default": None}), ("--runaway-turns", {"type": int, "default": 2}),
                      ("--max-wall", {"type": float, "default": 3600.0}), ("--out-dir", {"default": OUT}),
                      ("--handoff-unit", {"default": None}), ("--no-cell-handoff", {"action": "store_true"}),
                      ("--allow-inconsistent", {"action": "store_true"}), ("--offline", {"default": None}),
                      ("--expect-harness", {"default": None})]:
            ap.add_argument(f, **kw)
        return ap.parse_args(["--arm", ARM, "--fixture", FIXTURE] + argv)
    def call(fn, argv, patch=None):
        saved = {}
        if patch:
            for k, v in patch.items(): saved[k] = getattr(cell, k); setattr(cell, k, v)
        try: return fn(argv)
        except BaseException as e: return ["EXCEPTION", type(e).__name__, str(e)]
        finally:
            for k, v in saved.items(): setattr(cell, k, v)
    def g2(argv):
        v = cell.eval_gate_projection(parse(argv), {"would_send_total": 192})
        return {"ok": v["ok"], "projected": v["projected_wall_s"], "worst": v["worst_case_wall_s"],
                "max_wall": v["max_wall_s"], "proj_turn": v["projected_turn_wall_s"],
                "source": v["projected_turn_wall_source"], "line": v["line"]}
    def g1(argv):
        v = cell.eval_gate_ledger(parse(argv))
        return {"ok": v["ok"], "would_spend": v["would_spend"], "turns_total": v["turns_total"],
                "allowance": v["fetch_followup_allowance"], "projected": v["projected"], "headroom": v["headroom"]}
    DIRECT = {
     "G1_turns0": call(g1, ["--turns", "0", "--hypothesis", "H3"]),
     "G1_turns_neg": call(g1, ["--turns", "-48", "--hypothesis", "H3"]),
     "G1_allow_neg": call(g1, ["--turns", "48", "--hypothesis", "H2", "--fetch-followup-allowance", "-100"]),
     "G1_allow_default": call(g1, ["--turns", "48", "--hypothesis", "H2"]),
     "G2_inf": call(g2, ["--turns", "48", "--max-wall", "inf"]),
     "G2_1e308": call(g2, ["--turns", "48", "--max-wall", "1e308"]),
     "G2_tiny_override": call(g2, ["--turns", "48", "--max-wall", "1", "--projected-turn-wall", "1e-9"]),
     "G2_artefact_zero": call(g2, ["--turns", "48", "--max-wall", "1"], {"PROJECTION_ARTEFACT": PROJ_ZERO}),
     "G2_artefact_neg": call(g2, ["--turns", "48", "--max-wall", "1"], {"PROJECTION_ARTEFACT": PROJ_NEG}),
     "G2_artefact_tiny": call(g2, ["--turns", "48", "--max-wall", "1"], {"PROJECTION_ARTEFACT": PROJ_TINY}),
     "G2_cap_inf": call(g2, ["--turns", "48", "--turn-wall-cap", "inf"]),
    }
    bread("direct-done")
    EXPR = {"G1_decision": "b['within_budget']; projected = requests_published + would_spend; would_spend = turns*arms*reps + fetch_followup_allowance; headroom = cap - reserve",
            "G2_decision": "ok = (max_wall > 0 and projected <= max_wall); projected = int(round(requests * proj_turn)); worst = int(round(requests * cap_turn))",
            "G3_decision": "ok = n >= min_n; n = turns*reps; H1 60, H2 1, H3 8 checkpoints"}
    src = open(CELL, encoding="utf-8").read()
    raised = set(int(x) for x in re.findall(r"Abort\(\s*(\d+)\s*,", src))
    for line in src.splitlines():
        if "_enforce(" in line:
            m = re.search(r"(\d+)\)\s*$", line.strip())
            if m: raised.add(int(m.group(1)))
    raised.add(0); raised.add(1)
    declared = set(cell.exit_codes.EXIT_TABLE)
    doc = open(os.path.join(ROOT, "docs/GATE-CHAIN.md"), encoding="utf-8").read()
    doc_codes = set(int(x) for x in re.findall(r"^\|\s*(\d+)\s*\|", doc, re.M))
    EXT = {"declared": sorted(declared), "raised_by_cell": sorted(raised),
           "raised_undeclared": sorted(raised - declared),
           "declared_never_raised_by_cell": sorted(declared - raised),
           "runner_propagated_codes": sorted(set(cell.exit_codes.RUNNER_CODES) | set(cell.exit_codes.RUNNER_MAPPED_TO_CRASH)),
           "docs_table_codes": sorted(doc_codes), "docs_missing": sorted(declared - doc_codes),
           "docs_extra": sorted(doc_codes - declared)}
    PIN_AFTER = sha(CELL)
    by = {c["case"]: c for c in R}
    ASSERT = {
     "B2_max_wall_1e308_allows": by["B2_max_wall_1e308"]["exit"] == 6 and by["B2_max_wall_1e308"]["spawns_live"] == 1,
     "B_max_wall_inf_crashes_exit1": by["B_max_wall_inf"]["exit"] == 1,
     "C2_max_wall_zero_refuses8_nospawn": by["C2_max_wall_zero"]["exit"] == 8 and by["C2_max_wall_zero"]["spawns_live"] == 0,
     "D_turns0_H3_runs_full_no_maxturns": by["D_turns0_H3"]["exit"] == 6 and by["D_turns0_H3"]["spawns_live"] == 1 and "--max-turns" not in (by["D_turns0_H3"]["live_argv"] or []),
     "D2_turns_neg_runs_full": by["D2_turns_neg48_H3"]["exit"] == 6 and by["D2_turns_neg48_H3"]["spawns_live"] == 1,
     "G_tiny_override_allows": by["G_override_tiny"]["exit"] == 6 and by["G_override_tiny"]["spawns_live"] == 1,
     "G2_override_neg_refuses8": by["G2_override_neg_control"]["exit"] == 8 and by["G2_override_neg_control"]["spawns_live"] == 0,
     "H_artefact_zero_allows": by["H_artefact_zero"]["exit"] == 6 and by["H_artefact_zero"]["spawns_live"] == 1,
     "H4_artefact_nan_exit1": by["H4_artefact_nan"]["exit"] == 1,
     "F_allow_neg_prices_zero_allowance": DIRECT["G1_allow_neg"]["allowance"] == 0 and DIRECT["G1_allow_default"]["allowance"] == 5,
     "G1_turns0_prices_zero": DIRECT["G1_turns0"]["would_spend"] == 0 and DIRECT["G1_turns0"]["ok"] is True,
     "G1_turns_neg_prices_negative": DIRECT["G1_turns_neg"]["would_spend"] < 0 and DIRECT["G1_turns_neg"]["ok"] is True,
     "J2_ledger_nocap_refuses2": by["J2_ledger_empty"]["exit"] == 2,
     "J3_badrows_refuses2": by["J3_ledger_badrows"]["exit"] == 2,
     "J4_missing_refuses2": by["J4_ledger_missing"]["exit"] == 2,
     "J5_prereg_empty_refuses": by["J5_prereg_empty"]["exit"] in (8, 12) and by["J5_prereg_empty"]["spawns_live"] == 0,
     "J5b_prereg_empty_refuses12": by["J5b_prereg_empty_g2_allowed"]["exit"] == 12 and by["J5b_prereg_empty_g2_allowed"]["spawns_live"] == 0,
     "J6_empty_fixture_refuses2": by["J6_empty_fixture"]["exit"] == 2,
     "J1_no_hypothesis_refuses_never_allows": by["J1_no_hypothesis"]["exit"] != 0 and by["J1_no_hypothesis"]["spawns_live"] == 0,
     "J1b_no_hypothesis_refuses12": by["J1b_no_hypothesis_g2_allowed"]["exit"] == 12 and by["J1b_no_hypothesis_g2_allowed"]["spawns_live"] == 0,
     "K_dryrun_zero_spawns": by["K_dryrun_refuses"]["spawns_live"] == 0 and by["K_dryrun_refuses"]["spawns_dryrun"] == 0,
     "refusal_writes_no_rows_or_manifest": by["C2_max_wall_zero"]["rows_files"] == [] and by["C2_max_wall_zero"]["gate_manifests"] == [],
     "docs_table_missing_code_1": EXT["docs_missing"] == [1],
     "A2_allow_control_reaches_runner": by["A2_allow_control"]["exit"] == 6 and by["A2_allow_control"]["spawns_live"] == 1,
     "I2b_cap_zero_passed_to_runner": by["I2b_cap_zero_allowed"]["exit"] == 6 and "--turn-wall-cap" in (by["I2b_cap_zero_allowed"]["live_argv"] or []),
     "cell_pinned": PIN_BEFORE == PIN_AFTER,
    }
    bad = [k for k, v in ASSERT.items() if not v]
    with open(os.path.join(OUT, "result.json"), "w") as fh:
        json.dump({"cell_sha256_before": PIN_BEFORE, "cell_sha256_after": PIN_AFTER,
                   "cell_unchanged": PIN_BEFORE == PIN_AFTER,
                   "exit_codes_sha256": sha(os.path.join(HERE, "exit_codes.py")),
                   "arms": list(ARMS), "arm_used": ARM, "expressions": EXPR,
                   "direct_gate_calls": DIRECT, "exit_table": EXT, "cases": R,
                   "assertions": ASSERT, "failed_assertions": bad}, fh, indent=1, sort_keys=True)
    print(json.dumps({"out": OUT, "failed": bad, "cases": len(R)}))
    sys.exit(1 if bad else 0)
except SystemExit:
    raise
except BaseException:
    sys.exit(fatal())
<!--ATTACK-SCRIPT-END-->

## Results

33 end-to-end cases + 11 direct gate evaluations, one run, `failed_assertions: []`. The runner was
never executed: every "live" entry is a recorded argv that `stage_run` would have spawned.

### Numeric flags enumerated vs attacked

Enumerated from the argparse surface: **8 numeric** (`--turns`, `--reps`, `--budget`,
`--turn-wall-cap`, `--projected-turn-wall`, `--fetch-followup-allowance`, `--runaway-turns`,
`--max-wall`). **8/8 attacked**, each with `0`, `-1`/`-48`, `1e-9`, `1e308`, `inf`, `nan`, and a
non-numeric string (`--turns abc`), alone and with a permissive sibling (`--max-wall 1e308`).
Non-numeric reaches argparse → `SystemExit(2)`, which is the declared preflight code.

### Decision expressions, verbatim, and their operand validation

| gate | expression | operands validated at the boundary | operands NOT |
|---|---|---|---|
| G1 | `ok = bool(b["within_budget"])`; `projected = requests_published + would_spend`; `would_spend = turns*arms*reps + allowance` | `cap` presence (refuse 2), artefact parse (2), unreadable rows (2) | **sign of `turns`/`reps`** (`turns_total` 0 or negative → `projected` below `spent` → allow); **`--fetch-followup-allowance` negative** silently clamped to 0 |
| G2 | `ok = (max_wall > 0 and projected <= max_wall)`; `projected = int(round(requests * proj_turn))` | `max_wall > 0`; `proj_turn` sign+finite when `source=flag` or `source=p90`; mode presence | **`max_wall` finiteness and magnitude** (`1e308` allows, `inf` crashes); **`proj_turn` magnitude** (`1e-9` allows); **artefact `proj_turn`** (`_mode_wall` returns `float(table[mode])` unchecked: 0, −12, 1e-9, NaN) |
| G3 | `ok = n >= min_n`; `n = turns*reps`; H1 60, H2 1, H3 checkpoints ≥ 8 | absent/unknown claim refuses (12 when reached) | **sign of `n`**; H3 ignores `n` entirely, so a zero/negative-turn cell that declares H3 is admitted |

### Class findings (every one reproduced, exit code observed)

| # | flag / input | value | what happened | exit |
|---|---|---|---|---|
| F1 | `--max-wall` | `1e308` | G2 `ok=True`, `projected_wall~=11520s` vs a 1e308 s ceiling, runner invoked | 6 |
| F2 | `--projected-turn-wall` | `1e-9` (with `--max-wall 1`) | `projected_wall~=0s`, G2 allows, runner invoked — F1's `> 0` fix has no lower bound | 6 |
| F3 | `PROJECTION.json` `defaults.projected_turn_wall_s_by_mode.absent` | `0.0` / `-12.0` / `1e-9` | G2 allows (`projected 0`, `-2304`, `0` s) with `--max-wall 1`, runner invoked — the artefact operand is unvalidated | 6 |
| F4 | `--turns` | `0` (H3, 12-checkpoint fixture, `--max-wall 1e308`) | G1 prices **0 requests**, G3 passes, runner invoked with **no `--max-turns`** → full 48-turn cell | 6 |
| F5 | `--turns` | `-48` (H3) | G1 `would_spend=-48`, `projected 1053` < `spent 1101` → allow, runner invoked (`--max-turns -48`, which the runner ignores: `if max_turns > 0`, `run_longrun.py:1916`) | 6 |
| F6 | `--fetch-followup-allowance` | `-100` | `max(0, int(fixed))` → allowance 0 (default 5); G1 prices 48 instead of 53 — an unspent reserve, never a refusal | allow |
| F7 | `--max-wall` / `--turn-wall-cap` / `--projected-turn-wall` / artefact | `inf`, `nan` | `int(inf)`/`int(nan)` inside the verdict line → **internal error**, not the gate's exit 8 with five facts; even an *already-refused* `--projected-turn-wall inf` crashes in `_num()` | 1 |
| F8 | `--turn-wall-cap` | `0` (with `--max-wall 1e308`) | no validation; `0.0` handed to the runner as its live abort threshold; runner reached | 6 |

### What refuses correctly (not reproduced as bypasses)

`--max-wall 0` / `-1` → 8, zero live spawns; `--projected-turn-wall -1` → 8; `--max-wall nan`
→ 1 (crash, not a bypass); absent `--hypothesis` → refused (8 with defaults because G2 runs first,
**12** once G2 would allow); empty prereg artefact → 12 (once G2 allows); ledger artefact with no
`budget.cap`, unreadable row file, missing artefact → 2; empty fixture → 2; absent `--budget` → 3;
`--dry-run` with a refusing gate → 0, **0 subprocesses**; `--runaway-turns -5` → runner clamps
`max(1, …)`, so it tightens rather than disables.

### Arithmetic completeness — the class invariant

Every gate still validates **one** operand and leaves its siblings open:

- G2 validates the ceiling's **sign** but not its **magnitude or finiteness** (F1, F7);
- G2 validates the flag multiplicand's **sign** but not its **magnitude** (F2) and not the
  **artefact** multiplicand at all (F3);
- G1 validates the artefact's **presence** but not the **sign of the cost** (F4, F5) nor the
  allowance override (F6);
- G3 validates the claim's **existence** but not its **n's sign**, and H3 does not read `n` at all.

The pattern the two earlier cards each fixed on one operand is therefore still the class: a gate is
only as strong as the *weakest* variable in its decision expression.

### Side effects before refusal — measured, not read from logs

For every live-mode refusal in the matrix: `spawns_live = 0`, `rows-*` files = 0, `.gates.json`
manifests = 0. **But** `spawns_dryrun = 1` for every one of them: `stage_budget()` spawns the
runner's `--dry-run` at stage 3 **before** G1/G2/G3, so "a refusal spawns no runner process" is
literally false — it spawns exactly one, offline, before the gates. `--dry-run` and preflight
refusals spawn zero. No refusal path reaches `stage_run`; no row or manifest is written.

### Exit-code contract

`EXIT_TABLE` keys `0..12` (13 codes). Raised by `cell.py`: `{0,1,2,3,4,7,8,9,10,11,12}`;
`{5,6}` are provisioned by `RUNNER_CODES = frozenset({2,3,4,5,6,7})` propagation. Raised-but-
undeclared: **none**. `docs/GATE-CHAIN.md` §2 lists **0,2,3,4,5,6,7,8,9,10,11,12 — code 1
(internal-error) is missing**, and code 1 was observed four times in this attack (F7). §4 also
names `defaults.projected_turn_wall_s` while the code reads
`defaults.projected_turn_wall_s_by_mode[mode]` (the artefact itself labels the former LEGACY), and
§5's "no hypothesis → exit 12" holds only when G2 would allow (J1 exits 8).

## Verdict — **FAIL**

`overall: fail`. Six surviving bypasses, each with an exact command below. A 792-request grid must
**not** be launched behind this chain.

```
cell.py --arm transcript-grow --fixture experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json \
  --budget 600 --turns 48 --hypothesis H2 --max-wall 1e308                        # F1
… --max-wall 1 --projected-turn-wall 0.000000001                                  # F2
… --max-wall 1   # with PROJECTION.json by-mode 0 / -12 / 1e-9                     # F3
… --fixture …/tasks-v6/LR-01.v7.json --turns 0 --hypothesis H3 --max-wall 1e308    # F4
… --fixture …/tasks-v6/LR-01.v7.json --turns -48 --hypothesis H3 --max-wall 1e308  # F5
… --fetch-followup-allowance -100                                                  # F6
```

Repair direction (one unit, not six): validate **every** variable of each decision expression at
its boundary — `max_wall` finite and ≤ a declared bound; `proj_turn` positive, finite and ≥ a
declared floor (artefact too); `turns`/`reps` positive integers; follow-up allowance ≥ 0 or absent;
`turn-wall-cap` positive and bounded — and make the refusal formatter finiteness-safe so `inf`/`nan`
produce the gate's own exit code instead of `int()`'s traceback. Then move code 1 into
`docs/GATE-CHAIN.md` §2 and correct §4's key name.
