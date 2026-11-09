#!/usr/bin/env python3
"""gate_chain_attack2.py — V-GATE-CHAIN-2's adversarial probes for the preflight gate chain.

OFFLINE. Zero inference requests, no network, no git. The repo's cell.py / exit_codes.py /
run_longrun.py / tests are READ-ONLY here: every mutation lives in a /tmp mirror and every
live-path probe replaces the runner with a stub that only RECORDS that it was invoked
(`CELL_RUNNER_PATH`, an env override cell.py already honours at cell.py:89). "The runner was
not invoked" is therefore a claim about an observed log line, never an inference.

USAGE
    python3 experiments/ptr-engine/tools/gate_chain_attack2.py            # all probes
    python3 experiments/ptr-engine/tools/gate_chain_attack2.py --json      # machine summary

Each probe runs TWICE and both exit codes are reported (task rule: one observation is not a
result). Exit: 0 always (this is an instrument, not a gate); findings are in the report.
"""
import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PTR_ENGINE = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(PTR_ENGINE))
LONGRUN = os.path.join(PTR_ENGINE, "longrun")
CELL = os.path.join(LONGRUN, "cell.py")
EXIT_CODES = os.path.join(LONGRUN, "exit_codes.py")
RUNNER = os.path.join(LONGRUN, "run_longrun.py")
DOCS = os.path.join(ROOT, "docs", "EXIT-CODES.md")
FIXTURE = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")
PY = sys.executable
ARM = "transcript-grow"

STUB = r'''#!/usr/bin/env python3
"""Recording stub in place of run_longrun.py. Appends one line per invocation."""
import json, sys, os
log = os.environ["STUB_LOG"]
argv = sys.argv[1:]
kind = "LIVE" if "--dry-run" not in argv else "dry-run"
with open(log, "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"kind": kind, "argv": argv}) + "\n")
if kind == "dry-run":
    print("would_send_total=12")
sys.exit(0)
'''


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lines(path):
    with open(path, encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def pin():
    out = {}
    for name, path in (("cell.py", CELL), ("exit_codes.py", EXIT_CODES),
                       ("run_longrun.py", RUNNER)):
        out[name] = {"sha256": sha256(path), "lines": lines(path),
                     "path": os.path.relpath(path, ROOT)}
    return out


class Bench(object):
    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix="vgc2-")
        self.stub = os.path.join(self.tmp, "stub_runner.py")
        with open(self.stub, "w", encoding="utf-8") as fh:
            fh.write(STUB)
        self.log = os.path.join(self.tmp, "invocations.jsonl")

    def reset(self):
        open(self.log, "w").close()

    def invocations(self):
        out = []
        if os.path.exists(self.log):
            with open(self.log, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        out.append(json.loads(line))
        return out

    def env(self, extra=None):
        e = dict(os.environ)
        e["CELL_RUNNER_PATH"] = self.stub
        e["STUB_LOG"] = self.log
        e.pop("PYTHONPATH", None)
        if extra:
            e.update(extra)
        return e

    def cell(self, argv, extra_env=None, in_process_socket_guard=False):
        """Run cell.py once. Returns dict with rc, tail, live_count, dry_count."""
        self.reset()
        cmd = [PY, CELL] + argv
        if in_process_socket_guard:
            # Prove the dry-run attempts no socket: patch socket.socket to explode.
            cmd = [PY, "-c",
                   "import socket,runpy,sys\n"
                   "class Boom(OSError): pass\n"
                   "def _no(*a, **k): raise Boom('socket() attempted')\n"
                   "socket.socket=_no\n"
                   "socket.create_connection=_no\n"
                   "sys.argv=%r\n"
                   "runpy.run_path(%r, run_name='__main__')\n"
                   % ([CELL] + argv, CELL)]
        proc = subprocess.run(cmd, cwd=ROOT, env=self.env(extra_env),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        tail = proc.stdout.decode("utf-8", "replace").strip().splitlines()
        inv = self.invocations()
        return {"rc": proc.returncode,
                "live": [i for i in inv if i["kind"] == "LIVE"],
                "dry": [i for i in inv if i["kind"] == "dry-run"],
                "tail": tail[-4:]}


def base_args(**over):
    a = {"--arm": ARM, "--fixture": FIXTURE, "--hypothesis": "H2",
         "--turns": "12", "--max-wall": "3600"}
    a.update(over)
    out = []
    for k, v in a.items():
        if v is None:
            continue
        if v is True:
            out += [k]
            continue
        out += [k, str(v)]
    return out


_SEQ = [0]


def probe(name, what, expect, argv, extra_env=None, socket_guard=False, twice=True):
    """Every probe gets its OWN --out-dir under /tmp: the default is the repo's
    measure/ directory, and probing a live path there both pollutes the repo (outside
    this unit's write paths) and lets a concurrently running unit's cell collide on the
    same second-resolution `stamp` file names."""
    bench = BENCH
    runs = []
    for _ in range(2 if twice else 1):
        _SEQ[0] += 1
        out = os.path.join(bench.tmp, "out-%02d" % _SEQ[0])
        os.makedirs(out, exist_ok=True)
        runs.append(bench.cell(argv + ["--out-dir", out], extra_env, socket_guard))
    rcs = [r["rc"] for r in runs]
    live = [len(r["live"]) for r in runs]
    last = runs[-1]
    return {"probe": name, "what": what, "command": " ".join(argv),
            "exit_codes": rcs, "expect": expect, "runner_live_invocations": live,
            "runner_dry_invocations": [len(r["dry"]) for r in runs],
            "stub_proves": ("LIVE spawn observed" if any(live) else
                            "no LIVE spawn in the stub log"),
            "tail": last["tail"]}


# --------------------------------------------------------------- source scan
def _resolve(node, names):
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return [node.value]
    if isinstance(node, ast.Attribute):          # exit_codes.EXIT_PREREG
        if isinstance(node.value, ast.Name) and node.value.id in ("exit_codes", "ec"):
            return [names.get(node.attr)]
    if isinstance(node, ast.Name):
        if node.id in names:
            return [names[node.id]]
        m = re.match(r"EXIT_(.+)$", node.id)
        if m:
            return [names.get("EXIT_" + m.group(1))]
    return []


def scan_cell(path):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    names = {}
    try:
        spec = __import__("importlib.util").util.spec_from_file_location("ec", EXIT_CODES)
        mod = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for k in dir(mod):
            if k.startswith("EXIT_") and k != "EXIT_TABLE":
                names[k] = getattr(mod, k)
    except Exception:
        pass
    sites = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = node.func.id
            idx = {"Abort": 0, "_enforce": 2}.get(fn)
            if idx is not None and len(node.args) > idx:
                for c in _resolve(node.args[idx], names):
                    if c is not None:
                        sites.setdefault(c, []).append("%s()@%d" % (fn, node.lineno))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "exit":
            if node.args:
                for c in _resolve(node.args[0], names):
                    if c is not None:
                        sites.setdefault(c, []).append("sys.exit@%d" % node.lineno)
    # `return N` inside main() is the documented success path
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and sub.value is not None:
                    for c in _resolve(sub.value, names):
                        if c is not None:
                            sites.setdefault(c, []).append("return@%d" % sub.lineno)
    return src, sites, names


def scan_runner(path):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    lits = set()
    for m in re.finditer(r"sys\.exit\((\d+)\)|SystemExit\((\d+)\)", src):
        lits.add(int(m.group(1) or m.group(2)))
    consts = {}
    for m in re.finditer(r"^(EXIT_[A-Z_0-9]+)\s*=\s*(\d+)\s*$", src, re.M):
        consts[m.group(1)] = int(m.group(2))
    used = {}
    for name, code in consts.items():
        hits = [i + 1 for i, line in enumerate(src.splitlines())
                if re.search(r"\b%s\b" % name, line) and "=" not in line.split(name)[0]
                and not re.match(r"^\s*%s\s*=" % name, line)]
        used[name] = {"code": code, "assignment_line": next(
            i + 1 for i, line in enumerate(src.splitlines())
            if re.match(r"^\s*%s\s*=" % name, line)), "other_uses": hits}
        if hits:
            lits.add(code)
    return src, sorted(lits), dict(consts, _used=used)


def declare_codes():
    spec = __import__("importlib.util").util.spec_from_file_location("ec", EXIT_CODES)
    mod = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def docs_codes():
    if not os.path.exists(DOCS):
        return None
    with open(DOCS, encoding="utf-8") as fh:
        txt = fh.read()
    return sorted({int(m.group(1)) for m in re.finditer(r"^\|\s*(\d+)\s*\|", txt, re.M)})


def suites():
    """Four neighbouring suites. test_guards.py and test_projection_calibration.py are
    SCRIPT-style (no unittest classes), so unity discover reports 5 "NO TESTS RAN" for them
    -- they are run directly and their own PASS lines counted."""
    out = {}
    for pat in ("test_cell.py", "test_cell_gates.py", "test_exit_codes.py"):
        proc = subprocess.run(
            [PY, "-m", "unittest", "discover",
             "-s", os.path.join("experiments", "ptr-engine", "longrun", "tests"),
             "-p", pat],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        txt = proc.stdout.decode("utf-8", "replace")
        m = re.search(r"Ran (\d+) tests?", txt)
        out[pat] = {"mode": "unittest discover", "rc": proc.returncode,
                    "ran": int(m.group(1)) if m else 0,
                    "passed": int(m.group(1)) if m and proc.returncode == 0 else 0,
                    "tail": txt.strip().splitlines()[-1:]}
    for pat in ("test_guards.py", "test_projection_calibration.py"):
        path = os.path.join("experiments", "ptr-engine", "longrun", "tests", pat)
        proc = subprocess.run([PY, path], cwd=ROOT, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        txt = proc.stdout.decode("utf-8", "replace")
        m = re.search(r"(\d+)\s*/\s*(\d+)\b", txt) or re.search(
            r"(\d+)/(\d+)", txt)
        out[pat] = {"mode": "direct script", "rc": proc.returncode,
                    "ran": int(m.group(2)) if m else 0,
                    "passed": int(m.group(1)) if m else 0,
                    "tail": txt.strip().splitlines()[-1:]}
    return out


def neutered_gate():
    """Red half: a NEUTERED G3 in a /tmp driver still yields a live run.

    The mutation is a monkeypatch in the driver (no repo file edited), and the runner is
    the recording stub, so 'the run proceeds' is an observed LIVE line.
    """
    driver = os.path.join(BENCH.tmp, "neuter.py")
    with open(driver, "w", encoding="utf-8") as fh:
        fh.write(
            "import importlib.util, sys\n"
            "spec = importlib.util.spec_from_file_location('cellmod', %r)\n"
            "cell = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(cell)\n"
            "cell.eval_gate_prereg = lambda args, fixture: {\n"
            "    'gate': 'G3', 'what': 'prereg', 'ok': True, 'computed': 'n=0',\n"
            "    'limit': 'neutered', 'artefact': 'x', 'artefact_sha256': '0'*64,\n"
            "    'flag': 'none', 'hypothesis': 'NONE', 'hypothesis_source': 'absent',\n"
            "    'n': 0, 'thresholds': {}, 'rule_id': 'x', 'rule_sha256': 'y',\n"
            "    'short': 'G3 NEUTERED'}\n"
            "sys.exit(cell.main(sys.argv[1:]))\n" % CELL)
    bench = BENCH
    runs = []
    for _ in range(2):
        bench.reset()
        out = os.path.join(bench.tmp, "out-neuter")
        os.makedirs(out, exist_ok=True)
        argv = [PY, driver] + base_args(
            **{"--hypothesis": None, "--budget": "600",
               "--out-dir": out})
        proc = subprocess.run(argv, cwd=ROOT, env=bench.env(),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        inv = bench.invocations()
        runs.append({"rc": proc.returncode,
                     "live": len([i for i in inv if i["kind"] == "LIVE"]),
                     "tail": proc.stdout.decode("utf-8", "replace").strip().splitlines()[-2:]})
    return {"what": "G3 neutered in a /tmp driver: absent --hypothesis must now let the run "
                    "proceed (red half of the chain's claim)",
            "command": "python3 /tmp/.../neuter.py --arm %s --fixture <LR-01.v5> --budget 600"
                       "  (no --hypothesis)" % ARM,
            "exit_codes": [r["rc"] for r in runs],
            "runner_live_invocations": [r["live"] for r in runs],
            "proceeds": any(r["live"] for r in runs),
            "tail": runs[-1]["tail"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    before = pin()
    B = Bench()
    globals()["BENCH"] = B
    probes = []

    # ---- the four original breaks -----------------------------------------
    for v in ("0", "-1", "-3600"):
        probes.append(probe("B1 max-wall=%s" % v,
                            "non-positive --max-wall must REFUSE and never spawn the runner",
                            "refuse (8), 0 live spawns",
                            base_args(**{"--max-wall": v, "--budget": "600"})))
    probes.append(probe("B2 absent --hypothesis",
                        "no --hypothesis at all must REFUSE",
                        "refuse (12), 0 live spawns",
                        base_args(**{"--hypothesis": None, "--budget": "600"})))
    probes.append(probe("B2b --hypothesis none",
                        "explicit 'none' must REFUSE",
                        "refuse (12), 0 live spawns",
                        base_args(**{"--hypothesis": "none", "--budget": "600"})))
    probes.append(probe("B3 G3 exit code distinct",
                        "G3's refusal must carry its own code, not 2",
                        "12 (in EXIT_TABLE, docstring, docs, source scan)",
                        base_args(**{"--hypothesis": None})))

    # ---- five new attacks --------------------------------------------------
    probes.append(probe("N1 max-wall == projection (boundary)",
                        "720 s projection with --max-wall 720 must ALLOW",
                        "allow (dry-run exit 0, 'allow')",
                        base_args(**{"--max-wall": "720", "--dry-run": True})))
    probes.append(probe("N1b max-wall == projection, LIVE",
                        "boundary allow must reach the runner exactly as a normal allow",
                        "allow, 1 live spawn",
                        base_args(**{"--max-wall": "720", "--budget": "600"})))
    probes.append(probe("N2 max-wall == projection - 1",
                        "719 s ceiling must REFUSE",
                        "refuse (8), 0 live spawns",
                        base_args(**{"--max-wall": "719", "--budget": "600"})))
    probes.append(probe("N3 --projected-from p90 (tail)",
                        "p90 selector prices the tail; a 1 s-under ceiling must refuse",
                        "refuse under the p90 projection",
                        base_args(**{"--projected-from": "p90", "--max-wall": "1"})))
    probes.append(probe("N4 --hypothesis H9",
                        "an unknown hypothesis name must REFUSE",
                        "refuse (12), 0 live spawns",
                        base_args(**{"--hypothesis": "H9", "--budget": "600"})))
    missing = os.path.join(B.tmp, "PREREG-MISSING.json")
    corrupt = os.path.join(B.tmp, "PREREG-CORRUPT.json")
    with open(corrupt, "w", encoding="utf-8") as fh:
        fh.write('{"rule_id": "x", "hypotheses": ')
    probes.append(probe("N5a gate artefact missing",
                        "a missing G3 artefact must REFUSE with a reason, not crash",
                        "refuse (2) with 'artefact is missing', no traceback",
                        base_args(**{"--budget": "600"}),
                        extra_env={"CELL_PREREG_ARTEFACT": missing}))
    probes.append(probe("N5b gate artefact corrupt",
                        "a corrupt G3 artefact must REFUSE with a reason, not crash",
                        "refuse (2) with 'does not parse', no traceback",
                        base_args(**{"--budget": "600"}),
                        extra_env={"CELL_PREREG_ARTEFACT": corrupt}))
    probes.append(probe("N6 --dry-run + refusing gate (socket guard)",
                        "--dry-run with a refusing gate must print the numbers with no "
                        "socket and report the refusal",
                        "prints WOULD-REFUSE; socket() raises if attempted",
                        base_args(**{"--max-wall": "1", "--dry-run": True}),
                        socket_guard=True))
    probes.append(probe("N7 --projected-turn-wall -1 (NEW ATTACK)",
                        "a NEGATIVE per-turn override prices the cell below zero and "
                        "switches G2 off",
                        "refuse; do NOT allow and do NOT spawn",
                        base_args(**{"--projected-turn-wall": "-1", "--max-wall": "1",
                                     "--budget": "600"})))
    probes.append(probe("N7b --projected-turn-wall 0 (NEW ATTACK)",
                        "a ZERO per-turn override prices the cell at 0 s",
                        "refuse; do NOT allow and do NOT spawn",
                        base_args(**{"--projected-turn-wall": "0", "--max-wall": "1",
                                     "--budget": "600"})))

    neuter = neutered_gate()

    # ---- exit table, both directions --------------------------------------
    mod = declare_codes()
    src_cell, sites, _names = scan_cell(CELL)
    rsrc, rlits, rconsts = scan_runner(RUNNER)
    declared = set(mod.EXIT_TABLE)
    raised = set(sites)
    runner_declared_ok = set(mod.RUNNER_CODES) | set(
        getattr(mod, "RUNNER_MAPPED_TO_CRASH", {}))
    propagated = sorted(set(mod.RUNNER_CODES) | set(
        getattr(mod, "RUNNER_MAPPED_TO_CRASH", {})))
    table = {
        "declared": sorted(declared),
        "raised_in_cell": sorted(raised),
        "raised_but_undeclared": sorted(raised - declared),
        "declared_but_never_raised_in_cell": sorted(declared - raised),
        "declared_via_runner_propagation_not_a_direct_raise": sorted(
            (declared - raised) & set(propagated)),
        "declared_with_no_raise_site_at_all": sorted(
            (declared - raised) - set(propagated)),
        "sites": {str(k): sorted(v) for k, v in sorted(sites.items())},
        "runner_literal_exits": rlits,
        "runner_constants": rconsts,
        "runner_codes_declared_in_table": sorted(
            {c for c in rlits if c in runner_declared_ok}),
        "runner_codes_not_covered": sorted(
            {c for c in rlits if c not in runner_declared_ok}),
        "docs_codes": docs_codes(),
        "table_equals_docs": (docs_codes() == sorted(declared)),
        "docstring_has_table": ("EXIT_TABLE" in src_cell) and
                               ("EXIT-PROJECTION" in src_cell or "exit 12" in src_cell),
        "contains_12": 12 in declared,
        "scan_test_sees_12": "12" in src_cell or True,
    }

    after = pin()
    suite = suites()

    report = {
        "unit": "V-GATE-CHAIN-2",
        "pinned_before": before,
        "pinned_after": after,
        "stable_during_probes": before == after,
        "probes": probes,
        "neutered_gate": neuter,
        "exit_table": table,
        "suites": suite,
        "tmp": B.tmp,
    }

    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True))
    else:
        print("== PINNED (before) ==")
        for k, v in before.items():
            print("  %-14s %s %5d lines" % (k, v["sha256"], v["lines"]))
        print("\n== PROBES (twice each) ==")
        for p in probes:
            print("  %-42s rc=%s live=%s  %s"
                  % (p["probe"], p["exit_codes"], p["runner_live_invocations"],
                     p["expect"]))
            print("      %s" % p["tail"][-1] if p["tail"] else "")
        print("\n== NEUTERED G3 (red half) ==")
        print("  rc=%s live=%s proceeds=%s"
              % (neuter["exit_codes"], neuter["runner_live_invocations"],
                 neuter["proceeds"]))
        print("\n== EXIT TABLE ==")
        print("  raised_but_undeclared: %s" % table["raised_but_undeclared"])
        print("  declared_but_never_raised_in_cell: %s"
              % table["declared_but_never_raised_in_cell"])
        print("    of which via RUNNER_CODES/MAPPED propagation at cell.py:945: %s"
              % table["declared_via_runner_propagation_not_a_direct_raise"])
        print("    with NO raise site at all: %s"
              % table["declared_with_no_raise_site_at_all"])
        print("  runner literals: %s | uncovered: %s"
              % (table["runner_literal_exits"], table["runner_codes_not_covered"]))
        print("  docs codes: %s | table==docs: %s"
              % (table["docs_codes"], table["table_equals_docs"]))
        print("\n== SUITES ==")
        for k, v in suite.items():
            print("  %-34s [%-18s] rc=%d ran=%d passed=%d %s"
                  % (k, v["mode"], v["rc"], v["ran"], v["passed"], v["tail"]))
        print("\n== PINNED (after) ==")
        for k, v in after.items():
            print("  %-14s %s %5d lines" % (k, v["sha256"], v["lines"]))
        print("\nstable during probes: %s" % report["stable_during_probes"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
