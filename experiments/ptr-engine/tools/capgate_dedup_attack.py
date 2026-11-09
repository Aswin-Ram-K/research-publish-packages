#!/usr/bin/env python3
"""CAPGATE-DEDUP attack harness — offline, /tmp mirrors only.

Verifies the ONE thing REQUEST-LEDGER-2's assumption[1] leaves untested: does the
cap gate in run_longrun.py spend against the DE-DUPLICATED request count (1,071),
and what does it do when a duplicate mirror appears on disk (delta<0)?

Absolute rules honoured here:
  * the repository's longrun/run_longrun.py, tools/request_ledger.py, every
    measure/rows-*.jsonl and measure/REQUEST-LEDGER.json are READ, never written;
  * every mutation happens inside a /tmp mirror;
  * no socket is opened: a "run" is the gate object driven in-process
    (RequestCapGate -> acquire -> _gate_finish), which is the launch path minus
    send_chat.  A refusal therefore costs nothing; rows are written as synthetic
    mirrors so the exit reconciliation is honest rather than trivially short.

Usage:  python3 experiments/ptr-engine/tools/capgate_dedup_attack.py
Exit 0 always (a probe FAILING is a result, not a crash); every observed exit code
is printed.  No network, no repository write.
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(ENGINE, "..", ".."))
RUNNER = os.path.join(ENGINE, "longrun", "run_longrun.py")
LEDGER = os.path.join(ENGINE, "tools", "request_ledger.py")
MEASURE = os.path.join(ENGINE, "measure")
ARTEFACT = os.path.join(MEASURE, "REQUEST-LEDGER.json")

MIRROR = os.path.join(tempfile.gettempdir(), "capgate-dedup-mirror")

# --- the shim that simulates the CLAIMED world -------------------------------------
# The card says "the cap gate now spends against the de-duplicated count".  Today it does
# NOT (request_ledger.DEDUCTION_RULE_SOUND is False, so build_report publishes the raw
# 1,101).  To attack the seam the claim describes we need a ledger whose `spent` really is
# the de-duplicated figure.  We get it WITHOUT editing the repo: a /tmp shim wraps the real
# module's build_report and passes deduction_rule_sound=True plus the evidence key it
# demands.  Nothing in the repository changes.
SHIM_SOURCE = '''\
import importlib.util
def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
_repo = _load({repo_ledger!r}, "ptr_request_ledger_repo")
RULE = _repo.RULE
DEFAULT_CAP = _repo.DEFAULT_CAP
DEFAULT_RESERVE = _repo.DEFAULT_RESERVE
RowsUnreadable = _repo.RowsUnreadable
EVIDENCE = {{"request_identity_hash": "attack-simulated-request-identity-hash"}}
def build_report(paths, cap, reserve, would_spend, **kw):
    return _repo.build_report(paths, cap, reserve, would_spend,
                              deduction_rule_sound=True, sound_rule_evidence=EVIDENCE)
'''


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_shim(path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(SHIM_SOURCE.format(repo_ledger=LEDGER))
    return path


def fresh_mirror(name):
    """Copy the corpus rows into a fresh /tmp mirror; return (root, files)."""
    root = os.path.join(MIRROR, name)
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root)
    srcs = sorted(os.path.join(MEASURE, f) for f in os.listdir(MEASURE)
                  if f.startswith("rows-") and f.endswith(".jsonl"))
    files = []
    for src in srcs:
        dst = os.path.join(root, os.path.basename(src))
        shutil.copyfile(src, dst)
        files.append(dst)
    return root, files


def append_row(path, row):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def last_row(path):
    with open(path, "r", encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    return json.loads(lines[-1])


def synthetic_row(n):
    """A countable row (kind=turn) that no de-dupe tuple can merge with another."""
    return {"ts": "2026-10-26T12:00:00.%03dZ" % (n % 1000),
            "content_sha256": "%064x" % (0xCA11 + n),
            "prompt_tokens": 100 + n, "completion_tokens": 7 + n, "kind": "turn"}


def drive(mod, ledger_mod, paths, cap, reserve, allocation, turns, own_rows,
          reconcile=True):
    """Construct the gate exactly as build_cap_gate does, drive `turns`, reconcile."""
    gate = mod.RequestCapGate(ledger_mod, paths, cap, reserve, allocation,
                             own_rows=own_rows)
    acquired, refusal = 0, None
    for t in range(1, turns + 1):
        try:
            gate.acquire(t, "turn")
            acquired += 1
            append_row(own_rows, synthetic_row(t))
        except mod.CapRefusal as exc:
            refusal = str(exc)
            break
    rec = rc = None
    if reconcile:
        rec, rc = mod._gate_finish(gate, None, None, own_rows)
    return gate, acquired, refusal, rec, rc


def main():
    print("=" * 78)
    print("V-CAPGATE-DEDUP — offline attack on the request cap gate")
    print("=" * 78)
    mod = load_module(RUNNER, "ptr_run_longrun")
    real = load_module(LEDGER, "ptr_request_ledger")
    os.makedirs(MIRROR, exist_ok=True)
    shim = mod.load_request_ledger(write_shim(
        os.path.join(MIRROR, "sound_dedup_ledger.py")))

    rows_glob = sorted(os.path.join(MEASURE, f) for f in os.listdir(MEASURE)
                       if f.startswith("rows-") and f.endswith(".jsonl"))
    rep_raw = real.build_report(rows_glob, real.DEFAULT_CAP, 0, 0)
    rep_dedup = shim.build_report(rows_glob, real.DEFAULT_CAP, 0, 0)
    spent_raw = int(rep_raw["budget"]["spent"])
    spent_dedup = int(rep_dedup["budget"]["spent"])

    # ------------------------------------------------------------------ P1 source
    print("\nP1 SOURCE — which count the gate compares, against which cap")
    print(f"  RULE                 : {real.RULE}")
    print(f"  DEFAULT_CAP          : {real.DEFAULT_CAP} (reserve {real.DEFAULT_RESERVE})")
    print(f"  DEDUCTION_RULE_SOUND : {getattr(real, 'DEDUCTION_RULE_SOUND', 'ABSENT')}")
    print(f"  build_report publishes requests={rep_raw['requests']} "
          f"(raw={rep_raw['requests_raw']} dedup={rep_raw['requests_deduplicated']}) "
          f"deduction.applied={rep_raw['deduction']['applied']}")
    print("  gate: headroom = cap - reserve")
    print("        spent_at_start = build_report(paths,cap,reserve,0)['budget']['spent']")
    print("        acquire(): projected = spent_at_start + used_in_run + 1; "
          "over_cap = projected > headroom -> CapRefusal (exit 4, nothing sent)")
    print("        reconcile(): delta = spent_after - (spent_at_start + used_in_run)")
    print("        delta>0 -> CAP GATE RECONCILE DIVERGENCE, exit 9 (BUG, fails the run)")
    print("        delta==0 -> 'cap-gate: reconciled', exit unaffected")
    print("        delta<0 -> CAP GATE UNRECORDED, prints and returns 0 (WARNS)")

    # ------------------------------------------------------------------ P5 today
    print("\nP5 LEDGER vs GATE TODAY")
    art = json.load(open(ARTEFACT, encoding="utf-8"))
    bud = art["budget"]
    live = mod.build_cap_gate
    root0, files0 = fresh_mirror("today")
    g0 = mod.RequestCapGate(real, files0, real.DEFAULT_CAP, 0, 1)
    rec0, rc0 = mod._gate_finish(g0, None, None, os.path.join(root0, "no-rows.jsonl"))
    print(f"  REQUEST-LEDGER.json budget: spent={bud['spent']} spent_raw={bud['spent_raw']} "
          f"spent_deduplicated={bud['spent_deduplicated']} remaining={bud['remaining']}")
    print(f"  gate reconciled over the same corpus: spent_at_start={g0.spent_at_start} "
          f"spent_after={rec0['spent_after']} delta={rec0['delta']} rc={rc0}")
    print(f"  gate uses RAW today? {g0.spent_at_start == bud['spent_raw']}  "
          f"uses DEDUP today? {g0.spent_at_start == bud['spent_deduplicated']}")
    print(f"  same figure printed by ledger and gate? "
          f"{g0.spent_at_start == bud['spent']} ({g0.spent_at_start} vs {bud['spent']})")

    # ------------------------------------------------------------------ P2 duplicate
    print("\nP2 DUPLICATE MIRROR — a row the ledger has never seen")
    big = max(rows_glob, key=lambda p: os.path.getsize(p))
    # (a)+(b) AS SHIPPED: raw counting means an extra duplicate row IS spend.
    root_a, files_a = fresh_mirror("shipped")
    before_a = int(real.build_report(files_a, real.DEFAULT_CAP, 0, 0)["budget"]["spent"])
    own_a = os.path.join(root_a, "rows-own.jsonl")
    open(own_a, "w").close()
    dup = last_row(os.path.join(root_a, os.path.basename(big)))
    for n_dups, label in ((1, "+1 mirror row"), (2, "+2 mirror rows")):
        # reset the mirror rows file and the own-row file for each sub-probe
        shutil.copyfile(big, os.path.join(root_a, os.path.basename(big)))
        open(own_a, "w").close()
        for _ in range(n_dups):
            append_row(os.path.join(root_a, os.path.basename(big)), dup)
        g = mod.RequestCapGate(real, files_a, before_a + 50, 0, 5, own_rows=own_a)
        g.spent_at_start = before_a          # latched BEFORE the mirror appeared
        g.used_in_run = 1                    # one request this run sent
        rec, rc = mod._gate_finish(g, None, None, own_a)
        print(f"  [as shipped, deduction OFF] {label}: spent_at_start={before_a} "
              f"used_in_run=1 spent_after={rec['spent_after']} delta={rec['delta']} rc={rc}")
        print(f"    OBSERVED_EXIT_CODE={rc}")
    # (c) THE CLAIMED WORLD: the duplicate is invisible, so the count under-runs.
    root_b, files_b = fresh_mirror("dedup")
    own_b = os.path.join(root_b, "rows-own.jsonl")
    open(own_b, "w").close()
    before_b = int(shim.build_report(files_b, shim.DEFAULT_CAP, 0, 0)["budget"]["spent"])
    append_row(os.path.join(root_b, os.path.basename(big)), last_row(
        os.path.join(root_b, os.path.basename(big))))
    g = mod.RequestCapGate(shim, files_b, before_b + 50, 0, 5, own_rows=own_b)
    g.spent_at_start = before_b
    g.used_in_run = 1
    rec, rc = mod._gate_finish(g, None, None, own_b)
    print(f"  [claimed world, deduction ON] +1 mirror row: spent_at_start={before_b} "
          f"used_in_run=1 spent_after={rec['spent_after']} delta={rec['delta']} rc={rc}")
    print(f"    OBSERVED_EXIT_CODE={rc}   <- refusal would be 4 or 9; 0 = warn only")

    # ------------------------------------------------------------------ P3 boundary
    print("\nP3 BOUNDARY — spent + planned == cap, then one over")
    root_c, files_c = fresh_mirror("boundary")
    own_c = os.path.join(root_c, "rows-own.jsonl")
    for label, cap, turns in (("spent+planned == cap exactly (planned 2, cap spent+2)",
                              spent_raw + 2, 2),
                              ("one request over (planned 3, cap spent+2)", spent_raw + 2, 3)):
        open(own_c, "w").close()
        g = mod.RequestCapGate(real, files_c, cap, 0, 3, own_rows=own_c)
        acquired, refusal = 0, None
        for t in range(1, turns + 1):
            try:
                g.acquire(t, "turn")
                acquired += 1
                append_row(own_c, synthetic_row(t))
            except mod.CapRefusal as exc:
                refusal = str(exc)
                break
        rec, rc = mod._gate_finish(g, None, None, own_c)
        print(f"  cap={cap} ({label}): acquired={acquired}/{turns} "
              f"spent_at_start={g.spent_at_start} headroom={g.headroom} "
              f"last_allowed_projected={g.spent_at_start + acquired} rc={rc}")
        if refusal:
            print(f"    REFUSAL: {refusal}")
            print(f"    OBSERVED_EXIT_CODE={4 if rc == 0 else rc} (CapRefusal -> exit 4)")
        else:
            print(f"    PRINTED: no refusal — every request fit "
                  f"(projected <= headroom={g.headroom})")

    # the 30-apart discrimination: cap leaves exactly 30 for the DEDUP reading only
    print("\nP3b WHICH COUNT — cap=1101 leaves 30 for dedup, 0 for raw")
    for label, led in (("as shipped (raw)", real), ("claimed world (dedup)", shim)):
        open(own_c, "w").close()
        g = mod.RequestCapGate(led, files_c, 1101, 0, 30, own_rows=own_c)
        acquired, refusal = 0, None
        for t in range(1, 31):
            try:
                g.acquire(t, "turn")
                acquired += 1
                append_row(own_c, synthetic_row(t))
            except mod.CapRefusal as exc:
                refusal = str(exc)
                break
        print(f"  {label}: spent_at_start={g.spent_at_start} "
              f"believed_unspent={g.headroom - g.spent_at_start} acquired={acquired}/30")
        if refusal:
            print(f"    REFUSAL: {refusal}")

    # ------------------------------------------------------------------ P4 unsafe
    print("\nP4 UNSAFE DIRECTION — ledger 1,071 vs rows 1,101, cap room exactly 30")
    root_d, files_d = fresh_mirror("unsafe")
    own_d = os.path.join(root_d, "rows-own.jsonl")
    print(f"  rows on disk bill {spent_raw}; dedup reading {spent_dedup}; cap=1101")
    for label, led in (("as shipped (raw)", real), ("claimed world (dedup)", shim)):
        open(own_d, "w").close()
        g = mod.RequestCapGate(led, files_d, 1101, 0, 30, own_rows=own_d)
        acquired, refusal = 0, None
        for t in range(1, 31):
            try:
                g.acquire(t, "turn")
                acquired += 1
                append_row(own_d, synthetic_row(t))
            except mod.CapRefusal as exc:
                refusal = str(exc)
                break
        print(f"  {label}: spent_at_start={g.spent_at_start} cap={g.cap} "
              f"headroom={g.headroom} believed_unspent={g.headroom - g.spent_at_start} "
              f"acquired={acquired}/30")
        if refusal:
            print(f"    REFUSAL: {refusal}")
        else:
            print(f"    LAUNCHED: 30 requests would be sent with 0 requests of true room "
                  f"(engine bills {spent_raw})")
        if acquired:
            rec, rc = mod._gate_finish(g, None, None, own_d)
            print(f"    exit reconciliation: delta={rec['delta']} rc={rc}")

    # ------------------------------------------------------------------ dry run path
    print("\nDRY-RUN PATH — does --dry-run construct the gate at all?")
    fx = os.path.join(MIRROR, "fixture-tiny.json")
    json.dump({"schema": "consonance.longrun-fixture/1", "task_id": "CAPGATE-TINY",
               "class": "repo-fix", "objective": "one turn, offline",
               "N": 1, "bytes_per_token": 4.0, "system_prompt": "Answer briefly.",
               "wall_tokens": 4096,
               "turns": [{"turn": 1, "question": "state the time", "kind": "work"}],
               "items": [{"id": "capgate-1", "body": "offline cap probe"}],
               "checkpoints": [], "sources": [],
               "long_run": {"turns": 1, "what_grows": "nothing"}}, open(fx, "w"))
    cmd = [sys.executable, RUNNER, "--dry-run", "--fixture", fx,
           "--budget-cap", "1", "--arms", "transcript-grow", "--reps", "1",
           "--manifest-dir", os.path.join(MIRROR, "manifests")]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=REPO,
                          env=dict(os.environ, PYTHONPATH=REPO))
    print(f"  command: {' '.join(cmd)}")
    print(f"  OBSERVED_EXIT_CODE={proc.returncode}  (cap=1 against {spent_raw} spent: exit 4 "
          f"if the gate were consulted, 0 = the dry run never consults it)")
    for line in ((proc.stdout or "").strip().splitlines()[-3:]
                 + (proc.stderr or "").strip().splitlines()[-2:]):
        print(f"  out: {line}")

    print("\nSUMMARY")
    print(f"  cap gate today spends against: {spent_raw} (RAW) "
          f"not {spent_dedup} (DEDUP)")
    print("  delta<0 prints 'CAP GATE UNRECORDED' and returns exit 0 — it WARNS")
    print("DONE — no network, no repo write; mirrors under", MIRROR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
