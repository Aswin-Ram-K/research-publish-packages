#!/usr/bin/env python3
"""test_spawn_classification.py — a diagnostic spawn is not a runner launch.

WHY THIS EXISTS. V-GATE-REPIN recorded `not_reproduced` against the literal rule
"`popen_calls == 0` on every refusal": a refusing cell makes exactly one raw Popen call,
the pre-gate `run_longrun.py --dry-run` self-check that stage 3/7 uses to price the cell
BEFORE any gate is evaluated. The old rule was unsatisfiable, so it was replaced — not
weakened — by a rule that keeps the strict part strict:

    A refusing invocation must have zero `runner_launch` spawns; any
    `preflight_self_check` spawn must be declared in the same record with its phase;
    an undeclared spawn (`purpose == other`, or a launch with no gate record) is a
    failure.

These three tests hold that rule to account against an INDEPENDENT oracle, so the
record cannot pass by saying nothing:

  (a) every refusal code in {2,3,4,8,12} yields `runner_launch == 0`, every spawn it
      declares carries a phase, and the declared spawn count equals the number of real
      `subprocess.Popen` calls a `sitecustomize` tripwire observed.
  (b) a `/tmp` mutant cell that spawns with `purpose=other`/no record FAILS the same
      comparison, with the word "undeclared" in the failure.
  (c) the oracle sees a real spawn at all (so (a) cannot pass vacuously) and the one
      declared spawn is the stage-3/7 budget dry-run, not the runner.

Every test is offline: the runner is the gate suite's stub, which only records that it
was invoked. No request is sent, no endpoint is contacted.
"""
import glob
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
PY = sys.executable
FIXTURE = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")

sys.path.insert(0, HERE)
import test_cell_gates as gates  # noqa: E402  (the offline refusal harness, reused)


def _load_sibling(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(LONGRUN, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


spawn_record = _load_sibling("spawn_record")

CELL = gates.CELL
CASES = (2, 3, 4, 8, 12)
#: an independent, in-child oracle: it counts real Popen constructions, not declarations
_SITECUSTOMIZE = '''
import os, subprocess
_log = os.environ.get("SPAWN_ORACLE_LOG")
_orig = subprocess.Popen
if _log:
    class _OraclePopen(_orig):
        def __init__(self, *a, **k):
            try:
                with open(_log, "a", encoding="utf-8") as fh:
                    fh.write("%r\\n" % ((a[0] if a else k.get("args")),))
            except OSError:
                pass
            super().__init__(*a, **k)
    subprocess.Popen = _OraclePopen
'''


# ------------------------------------------------------------------- fixtures
def _silent_runner(tmp):
    """A runner whose --dry-run prints no would_send_total, so stage 3/7 refuses (3)."""
    path = os.path.join(tmp, "silent_runner.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("import sys\n"
                 "if '--dry-run' in sys.argv:\n"
                 "    print('no total here')\n"
                 "    sys.exit(0)\n"
                 "sys.exit(0)\n")
    return path


def _oracle_env(tmp, env):
    oracle_dir = os.path.join(tmp, "oracle")
    os.makedirs(oracle_dir, exist_ok=True)
    with open(os.path.join(oracle_dir, "sitecustomize.py"), "w",
              encoding="utf-8") as fh:
        fh.write(_SITECUSTOMIZE)
    e = dict(env)
    e["PYTHONPATH"] = (oracle_dir + os.pathsep + e["PYTHONPATH"]
                       if e.get("PYTHONPATH") else oracle_dir)
    e["SPAWN_ORACLE_LOG"] = os.path.join(tmp, "spawn-oracle.log")
    return e


def _case_inputs(tmp, code):
    """(argv, env) that makes the real cell.py refuse with `code`, offline."""
    out = os.path.join(tmp, "out")
    os.makedirs(out, exist_ok=True)
    base = ["--arm", gates.ARM, "--fixture", FIXTURE, "--turns", "48", "--reps", "1",
            "--budget", "1000", "--out-dir", out, "--no-cell-handoff"]
    ledger, _rows = gates._fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = gates._fake_runner(tmp)
    if code == 2:
        base[3] = os.path.join(tmp, "missing-fixture.json")
        return base, gates._env(tmp, ledger, runner, marker)
    if code == 3:
        return base, gates._env(tmp, ledger, _silent_runner(tmp), marker)
    if code == 4:
        tight, _r = gates._fake_ledger(tmp, cap=120, spent=100, name="tight.json")
        return base, gates._env(tmp, tight, runner, marker)
    if code == 8:
        return (base + ["--projected-turn-wall", "180"],
                gates._env(tmp, ledger, runner, marker))
    if code == 12:
        return (base + ["--hypothesis", "H1"],
                gates._env(tmp, ledger, runner, marker))
    raise AssertionError("no refusal case for exit %r" % (code,))


def _oracle_count(tmp):
    path = os.path.join(tmp, "spawn-oracle.log")
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        return len([ln for ln in fh if ln.strip()])


def _refusal_doc(tmp):
    hits = sorted(glob.glob(os.path.join(tmp, "out", "*.refusal.json")))
    assert hits, ("no refusal record was written under %s/out/ — a refusal must publish "
                  "its spawns" % tmp)
    with open(hits[-1], encoding="utf-8") as fh:
        return json.load(fh)


def run_case(tmp, code, cell=CELL):
    """Run one refusal through the real conductor and read back its own record."""
    argv, env = _case_inputs(tmp, code)
    rc, log = gates._run(argv, _oracle_env(tmp, env), cell=cell)
    doc = _refusal_doc(tmp)
    return {
        "exit": rc,
        "log": log,
        "doc": doc,
        "spawns": doc.get("spawns") or [],
        "counts": doc.get("counts") or {},
        "runner_launch": (doc.get("counts") or {}).get("runner_launch"),
        "preflight_self_check": (doc.get("counts") or {}).get("preflight_self_check"),
        "declared": len(doc.get("spawns") or []),
        "oracle": _oracle_count(tmp),
        "validation": doc.get("validation") or spawn_record.validate_refusal(
            doc, doc.get("exit")),
    }


def check_declared_matches_oracle(case):
    """The record must account for EVERY real spawn the oracle saw."""
    if case["oracle"] != case["declared"]:
        raise AssertionError(
            "undeclared spawn: the oracle counted %d real subprocess.Popen call(s) but "
            "the refusal record declares %d — a spawn happened that the record does not "
            "name (purpose=other or no record at all)" % (case["oracle"], case["declared"]))
    assert case["validation"]["ok"], ("the refusal record fails its own rule: %s"
                                      % (case["validation"]["failures"],))


def _mutant_cell(tmp):
    """A /tmp mutant that spawns WITHOUT recording, then refuses honestly."""
    path = os.path.join(tmp, "mutant_cell.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("import subprocess, sys\n"
                 "sys.path.insert(0, %r)\n"
                 "import cell\n"
                 "# INDUCED DEFECT: an undeclared spawn (purpose=other, no record)\n"
                 "subprocess.run([sys.executable, '-c', 'pass'])\n"
                 "sys.exit(cell.main(sys.argv[1:]))\n" % (LONGRUN,))
    return path


# --------------------------------------------------------------------- checks
class SpawnClassification(unittest.TestCase):

    def test_a_every_refusal_declares_its_spawns_and_launches_none(self):
        for code in CASES:
            tmp = tempfile.mkdtemp(prefix="spawn-a-%d-" % code)
            try:
                case = run_case(tmp, code)
                self.assertEqual(case["exit"], code, case["log"][-2500:])
                self.assertEqual(case["doc"].get("exit"), code,
                                 "the refusal record's exit disagrees with the process")
                self.assertEqual(case["runner_launch"], 0,
                                 "exit %d reached a runner_launch" % code)
                for s in case["spawns"]:
                    self.assertIn(s["purpose"], spawn_record.PURPOSES)
                    self.assertTrue(str(s["phase"]).strip(),
                                    "spawn %r has no phase" % (s,))
                # exit 2 refuses in stage 1/7, before the dry-run self-check exists
                self.assertEqual(case["preflight_self_check"], 0 if code == 2 else 1,
                                 "exit %d: the budget self-check is not the expected "
                                 "one" % code)
                check_declared_matches_oracle(case)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def test_b_an_undeclared_spawn_fails(self):
        tmp = tempfile.mkdtemp(prefix="spawn-b-")
        try:
            case = run_case(tmp, 4, cell=_mutant_cell(tmp))
            self.assertEqual(case["exit"], 4, case["log"][-2500:])
            self.assertEqual(case["declared"], 1,
                             "the mutant should have recorded only the honest spawn")
            with self.assertRaises(AssertionError) as ctx:
                check_declared_matches_oracle(case)
            self.assertIn("undeclared spawn", str(ctx.exception))

            # a record-level mutant: purpose=other, or a launch with no gate record
            doc = json.loads(json.dumps(case["doc"]))
            doc["spawns"].append({"seq": 99, "purpose": "other", "phase": "4/7 run",
                                  "declared": True, "argv": ["/bin/true"],
                                  "pid_argv": "- /bin/true"})
            verdict = spawn_record.validate_refusal(doc, 4)
            self.assertFalse(verdict["ok"])
            self.assertTrue(any("purpose=other" in f for f in verdict["failures"]),
                            verdict["failures"])

            doc2 = json.loads(json.dumps(case["doc"]))
            doc2["spawns"][0]["purpose"] = "runner_launch"
            doc2["spawns"][0]["gate_record"] = None
            verdict2 = spawn_record.validate_refusal(doc2, 4)
            self.assertFalse(verdict2["ok"])
            self.assertTrue(any("runner_launch" in f for f in verdict2["failures"]),
                            verdict2["failures"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_c_the_oracle_sees_a_real_spawn(self):
        tmp = tempfile.mkdtemp(prefix="spawn-c-")
        try:
            case = run_case(tmp, 8)
            self.assertEqual(case["exit"], 8, case["log"][-2500:])
            self.assertGreaterEqual(
                case["oracle"], 1,
                "the oracle observed no real spawn: the equivalence check would be "
                "vacuous")
            self.assertEqual(case["declared"], 1)
            entry = case["spawns"][0]
            self.assertEqual(entry["purpose"], "preflight_self_check")
            self.assertEqual(entry["phase"], "3/7 budget")
            # the harness stubs the runner; the SHAPE (a --dry-run self-check) is
            # what matters, not this tree's runner path
            self.assertIn("--dry-run", entry["pid_argv"])
            self.assertIn("--arms", entry["pid_argv"])
            self.assertNotIn("runner_launch", [s["purpose"] for s in case["spawns"]])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)



# ---------------------------------------------- the validator must be able to say NO
class ValidateRefusalBites(unittest.TestCase):
    """Five rejections, each with a NONZERO CLI exit and a message naming the part,
    plus one green case: the real refusal record still validates.

    A validator that answers `ok=True` to an empty or truncated record accepts nothing
    as proof. These tests are the red for that: reverting the hardening in
    `spawn_record.validate_refusal` (or the oracle comparison) makes them fail.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="spawn-v-")
        cls.case = run_case(cls.tmp, 4)
        assert cls.case["doc"], "no refusal record to mutate"
        cls.doc = cls.case["doc"]
        cls.exit = cls.doc.get("exit")
        cls.observed = cls.case["oracle"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # -- helpers -----------------------------------------------------------
    def _copy(self):
        return json.loads(json.dumps(self.doc))

    def _verdict(self, doc, observed=None):
        return spawn_record.validate_refusal(doc, self.exit, observed=observed)

    def _cli(self, doc, observed=None):
        """Write the mutant and judge it through the real CLI, returning the process."""
        path = os.path.join(self.tmp, "mutant.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        cmd = [PY, os.path.join(LONGRUN, "spawn_record.py"),
               "--validate", path, "--exit-code", str(self.exit)]
        if observed is not None:
            cmd += ["--observed", str(observed)]
        return subprocess.run(cmd, capture_output=True, text=True)

    def _assert_rejected(self, doc, needle, observed=None):
        verdict = self._verdict(doc, observed)
        self.assertFalse(verdict["ok"], "validator ACCEPTED a record it must reject")
        joined = " | ".join(verdict["failures"])
        self.assertIn(needle, joined)
        proc = self._cli(doc, observed)
        self.assertNotEqual(proc.returncode, 0,
                            "CLI exited 0 on a record it must reject: %s"
                            % (proc.stdout,))
        self.assertIn(needle, proc.stderr)
        return verdict, proc

    # -- 1: no `spawns` key at all -----------------------------------------
    def test_1_no_spawns_key_is_rejected(self):
        doc = self._copy()
        del doc["spawns"]
        verdict, _ = self._assert_rejected(doc, "no `spawns` key")
        # keeping `counts` cannot rescue it: the declaration now disagrees with the
        # (absent) instrumentation, which is the whole point of recomputation.
        self.assertTrue(any("declared 1 vs recomputed 0" in f or "declared 0 vs "
                            "recomputed 1" in f for f in verdict["failures"]),
                        verdict["failures"])

    # -- 2: `spawns: []` with no declaration block = empty claim -----------
    def test_2_empty_spawns_and_no_declaration_block_is_rejected(self):
        doc = self._copy()
        for key in ("spawns", "counts", "classification", "rule", "validation"):
            doc.pop(key, None)
        self._assert_rejected(doc, "empty claim", observed=self.observed)
        # an empty `spawns` list alone is not enough either
        doc2 = self._copy()
        doc2.pop("counts", None)
        doc2.pop("classification", None)
        doc2.pop("rule", None)
        doc2.pop("validation", None)
        doc2["spawns"] = []
        self._assert_rejected(doc2, "empty claim", observed=0)

    # -- 3: declaration block that names no phase --------------------------
    def test_3_declaration_with_no_phase_is_rejected(self):
        doc = self._copy()
        for entry in doc["spawns"]:
            entry["phase"] = ""
        self._assert_rejected(doc, "phase", observed=self.observed)

    # -- 4: declared counts disagree with instrumentation by 1 -------------
    def test_4a_declared_counts_disagree_with_recomputed_entries(self):
        doc = self._copy()
        doc["counts"]["preflight_self_check"] += 1
        verdict, _ = self._assert_rejected(
            doc, "counts[preflight_self_check]", observed=self.observed)
        pair = [f for f in verdict["failures"]
                if "counts[preflight_self_check]" in f][0]
        self.assertIn("declared", pair)
        self.assertIn("recomputed", pair)
        self.assertIn("exit %r" % (self.exit,), pair)

    def test_4b_declared_spawns_disagree_with_the_oracle_by_one(self):
        verdict, _ = self._assert_rejected(
            self.doc, "from instrumentation", observed=self.observed + 1)
        pair = [f for f in verdict["failures"] if "from instrumentation" in f][0]
        self.assertIn("declared %d" % len(self.doc["spawns"]), pair)
        self.assertIn("recomputed %d" % (self.observed + 1), pair)
        self.assertIn("exit %r" % (self.exit,), pair)

    # -- 5: a runner_launch entry published for a refusal exit code --------
    def test_5_runner_launch_on_a_refusal_exit_is_rejected(self):
        doc = self._copy()
        doc["spawns"].append({
            "seq": 99, "purpose": "runner_launch", "phase": "4/7 run",
            "gate_record": "gate-manifest.json", "declared": True,
            "argv": ["python3", "run_longrun.py"], "pid_argv": "- run_longrun.py"})
        # keep the counts consistent so ONLY the refusal-launch rule can fire
        doc["counts"]["runner_launch"] = doc["counts"].get("runner_launch", 0) + 1
        verdict, _ = self._assert_rejected(
            doc, "refusal exit code %r" % (self.exit,),
            observed=self.observed + 1)
        self.assertGreaterEqual(verdict["runner_launch"], 1)

    # -- green: the real record still validates ----------------------------
    def test_6_green_real_refusal_record_still_validates(self):
        # D4 requires the record to declare its instrumentation, and D6 (RECORDED, not
        # fixed: cell.py is pinned) says the on-disk refusal document drops that block
        # because cell.py's writer publishes a fixed key list. The declaration belongs to
        # the RECORDER, not the run, so it is restored from the module constant -- the
        # spawns/counts/observed under test are the real ones, untouched.
        verdict = spawn_record.validate_refusal(
            spawn_record.complete_refusal_document(self.doc), self.exit,
            observed=self.observed)
        self.assertTrue(verdict["ok"], verdict["failures"])
        self.assertEqual(verdict["runner_launch"], 0)
        self.assertEqual(verdict["recomputed"].get("runner_launch"), 0)
        proc = self._cli(spawn_record.complete_refusal_document(self.doc),
                         self.observed)
        self.assertEqual(proc.returncode, 0, proc.stderr)




# ------------------------------------- D2/D3/D4: what an independent attack broke
class RecordBindings(unittest.TestCase):
    """The three record defects V-SPAWN-ATTACK-2 found, each held by a real CLI refusal.

    Every case is judged through `spawn_record.py` as a subprocess (its exit status is the
    verdict) and paired with its GREEN twin, so a guard that rejects everything would fail
    these tests too.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="spawn-bind-")
        cls.case = run_case(cls.tmp, 4)
        cls.doc = spawn_record.complete_refusal_document(cls.case["doc"])
        cls.exit = cls.doc.get("exit")
        cls.observed = cls.case["oracle"]
        cls.cli = os.path.join(LONGRUN, "spawn_record.py")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _copy(self):
        return json.loads(json.dumps(self.doc))

    def _run(self, path, *extra):
        cmd = [PY, self.cli, "--validate", path, "--exit-code", str(self.exit)] + list(extra)
        return subprocess.run(cmd, capture_output=True, text=True)

    def _run_doc(self, doc, *extra, name="mutant.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        return self._run(path, *extra)

    def _run_text(self, text, *extra, name="mutant-raw.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return self._run(path, *extra)

    def _trace(self, spawns, name="trace.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([{"pid": 100 + i, "argv": list(s["argv"])}
                       for i, s in enumerate(spawns)], fh)
        return path

    # -- D2: coverage of the refusal set, not of the shape of one run -------
    def test_d2_coverage_naming_only_0_and_7_is_refused(self):
        bad = self._copy()
        bad["per_exit_code"] = [{"exit": 0, "declared_spawns": 0},
                                {"exit": 7, "declared_spawns": 1}]
        proc = self._run_doc(bad)
        self.assertEqual(proc.returncode, 1,
                         "a record covering only exits 0/7 validated OK: %s" % proc.stdout)
        self.assertIn("missing refusal coverage: 2,3,4,8,12", proc.stderr)
        # GREEN twin: the same record naming every refusal exit is accepted, so the guard
        # is about the SET and not about the field's presence.
        good = self._copy()
        good["per_exit_code"] = [{"exit": e, "declared_spawns": 1}
                                 for e in (2, 3, 4, 8, 12)]
        proc = self._run_doc(good, name="good-coverage.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_d2b_single_exit_coverage_is_not_coverage(self):
        # "single-exit coverage is also accepted" was the hole: one entry is an aggregate
        # claim with four exits missing, and it must be refused as such.
        one = self._copy()
        one["per_exit_code"] = [{"exit": self.exit}]
        proc = self._run_doc(one)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        missing = sorted(set((2, 3, 4, 8, 12)) - {self.exit})
        self.assertIn("missing refusal coverage: %s"
                      % ",".join(str(x) for x in missing), proc.stderr)
        # the explicit override is how a caller narrows the required set on purpose
        proc = self._run_doc(one, "--required-exits", str(self.exit))
        self.assertEqual(proc.returncode, 0, proc.stderr)

    # -- D3: a duplicated key may not rewrite a declaration by key ORDER ----
    def test_d3_duplicate_key_is_refused_by_name(self):
        text = json.dumps(self.doc, indent=1)
        # inject a duplicate of an EXISTING counts key whose first value is a lie and
        # whose last value is the true one: last-wins would validate OK, so only the
        # duplicate guard can reject this.
        marker = '"counts": {'
        self.assertIn(marker, text)
        text = text.replace(marker, marker + '\n  "runner_launch": 9,', 1)
        proc = self._run_text(text)
        self.assertEqual(proc.returncode, 1,
                         "a duplicated key validated OK (last-wins rewrite): %s"
                         % proc.stdout)
        self.assertIn("duplicate key 'counts.runner_launch' at record.counts",
                      proc.stderr)
        # GREEN twin: the identical document WITHOUT the duplicated key exits 0
        proc = self._run_doc(self._copy(), name="dedup.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_d3b_duplicate_at_root_is_refused(self):
        text = json.dumps(self.doc, indent=1)
        text = text.replace('"exit":', '"exit": 0,\n "exit":', 1)
        proc = self._run_text(text, name="dup-root.json")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("duplicate key 'exit' at record", proc.stderr)

    # -- D4: the instrumentation scope is declared, not implied -------------
    def test_d4_record_without_instrumentation_is_refused(self):
        bare = self._copy()
        bare.pop("instrumentation")
        proc = self._run_doc(bare)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("no `instrumentation` declaration", proc.stderr)
        # a half-declared scope is not a scope either
        half = self._copy()
        half["instrumentation"] = {"primitive": "subprocess.Popen"}
        proc = self._run_doc(half, name="half-instr.json")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("`instrumentation` omits 'covers'", proc.stderr)

    def test_d4b_syscall_trace_exceeding_the_declaration_is_refused(self):
        # os.system-shaped: invisible to a Popen subclass, visible to the kernel
        extra = {"pid": 999, "argv": ["/bin/sh", "-c", "/bin/true"]}
        path = os.path.join(self.tmp, "excess-trace.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([{"pid": 100, "argv": self.doc["spawns"][0]["argv"]}, extra], fh)
        proc = self._run_doc(self._copy(), "--observed-from-syscall", path)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("outside the record", proc.stderr)
        self.assertIn("/bin/sh -c /bin/true", proc.stderr)

    def test_d4c_real_record_with_matching_trace_is_accepted(self):
        trace = self._trace(self.doc["spawns"])
        proc = self._run_doc(self._copy(), "--observed-from-syscall", trace)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("syscall=1", proc.stdout)

    def test_d4d_strace_text_drops_the_traced_process_itself(self):
        argv = " ".join('"%s",' % a for a in self.doc["spawns"][0]["argv"])
        text = ("1001  execve(\"/usr/bin/python3\", [\"python3\", \"cell.py\"], 0x7f) = 0\n"
                "1001  execve(\"%s\", [%s], 0x7f) = 0\n"
                % (self.doc["spawns"][0]["argv"][0], argv))
        path = os.path.join(self.tmp, "trace.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        entries = spawn_record.read_syscall_trace(path)
        self.assertEqual(len(entries), 1, entries)
        self.assertEqual(entries[0]["argv"], self.doc["spawns"][0]["argv"])
        proc = self._run_doc(self._copy(), "--observed-from-syscall", path)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
