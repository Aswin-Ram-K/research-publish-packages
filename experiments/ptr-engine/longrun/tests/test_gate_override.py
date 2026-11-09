#!/usr/bin/env python3
"""test_gate_override.py - the G2 multiplicand and the manifest name, offline.

WHY THIS EXISTS: V-GATE-CHAIN-2 closed four bypasses of the gate chain and then found a
fifth of the same class as the first, on a different operand. `--max-wall` was made to
refuse a non-positive ceiling, but `--projected-turn-wall` still accepted 0 or a negative
number: `--projected-turn-wall -1 --max-wall 1 --budget 600` printed
`projected_wall~=-12s ... source=flag` and INVOKED THE RUNNER (GATE-CHAIN-OVERRIDE-FIX
F1). The same attack observed two cells started in one second sharing one manifest
filename because the stamp was second-resolution and the default out-dir is the repo's
`measure/` (FIX 2). And it recorded the dry-run exit-code divergence as a contract gap
(FIX 3), which is now a documented sentence a test pins.

(a) a non-positive --projected-turn-wall refuses (exit 8, zero runner spawns); a positive
    value equal to the projection still allows;
(b) a --projected-from row file whose p90 prices at <= 0 refuses (exit 8, no runner) and
    never falls back to the artefact's p50;
(c) two manifests written with the SAME stamp in one second do not share a path;
(d) `--dry-run` exits 0 when a gate would refuse and its line says callers MUST parse it,
    which is what docs/GATE-CHAIN.md section 7 states.

Every test is OFFLINE: no socket, no endpoint, the live runner replaced by a stub that
only records that it was invoked.
"""
import glob
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
PTR_ENGINE = os.path.dirname(LONGRUN)
ROOT = os.path.dirname(os.path.dirname(PTR_ENGINE))
CELL = os.path.join(LONGRUN, "cell.py")
FIXTURE = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")
DOCS = os.path.join(ROOT, "docs", "GATE-CHAIN.md")
REAL_LEDGER = os.path.join(PTR_ENGINE, "measure", "REQUEST-LEDGER.json")
REAL_PROJECTION = os.path.join(PTR_ENGINE, "measure", "PROJECTION.json")
REAL_PREREG = os.path.join(PTR_ENGINE, "measure", "PREREG-ARM-RUN.json")
ARM = "transcript-grow"
PY = sys.executable


def _fake_runner(tmp, would_send=48):
    """A runner stub: answers --dry-run offline, records every real invocation."""
    marker = os.path.join(tmp, "live-runner-invoked.marker")
    path = os.path.join(tmp, "fake_runner.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("import sys, os\n"
                 "if '--dry-run' in sys.argv:\n"
                 "    print('  would_send_total=%d')\n"
                 "    sys.exit(0)\n"
                 "open(os.environ['CELL_MARKER'], 'w').write(' '.join(sys.argv))\n"
                 "sys.exit(0)\n" % would_send)
    return path, marker


def _cell_run(tmp, turns, extra, name="proj", dry_run=False):
    out = os.path.join(tmp, name)
    os.makedirs(out, exist_ok=True)
    fake, marker = _fake_runner(tmp, would_send=turns)
    argv = [PY, CELL, "--arm", ARM, "--fixture", FIXTURE,
            "--turns", str(turns), "--reps", "1",
            "--budget", "1000", "--out-dir", out, "--no-cell-handoff",
            "--hypothesis", "H2"]
    if dry_run:
        argv.append("--dry-run")
    argv += list(extra)
    # The three artefact paths are pinned HERE rather than inherited: a sibling suite
    # (test_cell_gates) mutates os.environ with fixture paths under a temp dir it deletes,
    # and an inherited dead path makes every subprocess here exit 2 for the wrong reason.
    env = dict(os.environ, CELL_RUNNER_PATH=fake, CELL_MARKER=marker,
               CELL_LEDGER_ARTEFACT=REAL_LEDGER,
               CELL_PROJECTION_ARTEFACT=REAL_PROJECTION,
               CELL_PREREG_ARTEFACT=REAL_PREREG)
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=LONGRUN,
                          env=env, timeout=180)
    return proc.returncode, proc.stdout + proc.stderr, marker


def _rows_file(tmp, walls_s, name="rows-prior.jsonl"):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        for i, w in enumerate(walls_s):
            fh.write(json.dumps({"turn": i, "wall_ms": int(round(w * 1000)),
                                 "completion_tokens": 1000}) + "\n")
    return path


def _load_cell():
    spec = importlib.util.spec_from_file_location("cell_override_under_test", CELL)
    cell = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cell)
    return cell


# --------------------------------------------------------------------- (a)
def check_nonpositive_override_refuses(tmp, value, label=None):
    """A non-positive --projected-turn-wall is REFUSED (exit 8) with G2's five facts.

    RED before FIX 1: exit 10 (the runner ran on a stub and the cell then failed), or
    any non-8 code, and the marker file exists -- the projection was switched off.
    """
    rc, log, marker = _cell_run(
        tmp, 48, ["--projected-turn-wall", str(value), "--max-wall", "1"],
        name=label or ("override-%s" % value))
    assert rc == 8, ("expected exit 8 for --projected-turn-wall %s (a per-turn wall of "
                     "zero or less is not 'unlimited'), got %d\n%s"
                     % (value, rc, log[-3000:]))
    assert not os.path.exists(marker), (
        "--projected-turn-wall %s reached the runner past a refusal" % value)
    for fact in ("G2 projection REFUSED", "positive per-turn ceiling",
                 "projected-turn-wall", "artefact", "sha256",
                 "must not be switched off"):
        assert fact in log, ("the refusal is missing the fact %r:\n%s"
                             % (fact, log[-3000:]))


def check_positive_override_equal_to_projection_allows(tmp):
    """Boundary: a positive per-turn wall whose projection EQUALS --max-wall passes.

    The guard refuses the unsafe direction only; it must not refuse the boundary that
    G2 already admits (`projected <= max_wall`).
    """
    rc, log, marker = _cell_run(tmp, 2, ["--projected-turn-wall", "5",
                                        "--max-wall", "10"], name="boundary")
    assert "projected_wall~=10s" in log, log[-3000:]
    assert rc != 8, ("2 turns x 5 s = 10 s == --max-wall 10 must be admitted, got exit 8"
                     "\n%s" % log[-3000:])
    assert os.path.exists(marker), "the runner was never invoked after a boundary allow"


# --------------------------------------------------------------------- (b)
def check_row_file_pricing_at_zero_refuses(tmp):
    """A --projected-from row file whose p90 is <= 0 refuses (exit 8), no fallback.

    RED before FIX 1's second half: this file used to be refused as exit 2 ("no usable
    turn wall") or, worse, a file with zero walls multiplies the projection to nothing.
    Either way it is not exit 8 and the message does not name the p90.
    """
    rows = _rows_file(tmp, [0, -5, -12.5], "rows-nonpositive.jsonl")
    rc, log, marker = _cell_run(tmp, 48, ["--projected-from", rows, "--max-wall", "1"],
                                name="rows-zero")
    assert rc == 8, ("expected exit 8 for a row file that prices at <= 0 s, got %d\n%s"
                     % (rc, log[-3000:]))
    assert not os.path.exists(marker), "the runner ran on a file priced at <= 0 s"
    assert "G2 projection REFUSED" in log, log[-3000:]
    assert "p90" in log and "projected-from" in log, log[-3000:]


def check_row_file_with_positive_walls_still_allows(tmp):
    """The same flag with measured positive walls is still admitted (the guard is narrow)."""
    rows = _rows_file(tmp, [10] * 10, "rows-positive.jsonl")
    rc, log, marker = _cell_run(tmp, 2, ["--projected-from", rows, "--max-wall", "30"],
                                name="rows-positive")
    assert rc != 8, "10 s p90 over 2 turns = 20 s <= 30 s must be admitted\n%s" % log[-3000:]
    assert os.path.exists(marker), "the runner was never invoked after an admission"


# --------------------------------------------------------------------- (c)
def check_two_manifests_in_one_second_do_not_collide(tmp):
    """Two runs with the SAME stamp in one second get two paths and two verdict sets.

    RED before FIX 2: `gate_manifest_path` did not exist / the name was
    `cell-<arm>-<stamp>.gates.json`, so both writes landed on one file and the second
    run's verdicts silently replaced the first's.
    """
    cell = _load_cell()
    out = os.path.join(tmp, "manifests")
    os.makedirs(out, exist_ok=True)
    stamp = "20260101T000000Z"          # fixed: the same second, twice
    arm = "transcript-grow"
    p1 = cell.gate_manifest_path(out, stamp, arm)
    p2 = cell.gate_manifest_path(out, stamp, arm)
    assert os.path.abspath(p1) != os.path.abspath(p2), (
        "two runs in one second share a manifest path: %s" % p1)

    def gates(tag):
        return [{"gate": "G2", "ok": True, "computed": tag, "limit": "1 s",
                 "artefact": "a.json", "artefact_sha256": "0" * 64, "flag": "--x"}]

    first = cell.write_gate_manifest(out, stamp, arm, gates("run-one"), {"name": "H2"})
    second = cell.write_gate_manifest(out, stamp, arm, gates("run-two"), {"name": "H2"})
    assert os.path.abspath(first) != os.path.abspath(second), (
        "write_gate_manifest reused %s for two runs" % first)
    written = sorted(glob.glob(os.path.join(out, "cell-%s-%s-*.gates.json" % (arm, stamp))))
    assert len(written) == 2, "expected two manifests under the same stamp, got %r" % written
    docs = []
    for rel in (first, second):
        with open(os.path.join(ROOT, rel) if not os.path.isabs(rel) else rel,
                  encoding="utf-8") as fh:
            docs.append(json.load(fh))
    assert {d["verdicts"][0]["computed"] for d in docs} == {"run-one", "run-two"}, (
        "the two manifests do not carry their own run's verdicts: %r"
        % [d["verdicts"][0]["computed"] for d in docs])


# --------------------------------------------------------------------- (d)
def check_dry_run_contract(tmp):
    """FIX 3's documented sentence: dry-run exits 0 and the CALLER parses the line.

    The contract chosen in docs/GATE-CHAIN.md section 7 is: `--dry-run` exits 0 even when
    a gate would refuse (it authorises nothing), and callers MUST parse the WOULD-REFUSE
    verdict lines / the final count, never the exit code. This test pins both halves --
    the code's behaviour and the document's sentence -- so they cannot drift apart.
    """
    rc, log, marker = _cell_run(tmp, 48, ["--max-wall", "1"], name="dry", dry_run=True)
    assert rc == 0, ("the documented contract is exit 0 for a dry run even when a gate "
                     "would refuse; got %d\n%s" % (rc, log[-3000:]))
    assert not os.path.exists(marker), "a dry run invoked the runner"
    assert "WOULD-REFUSE" in log, "the dry run did not mark the refusing gate:\n%s" % log[-3000:]
    assert "1 of 3 gate(s) would refuse" in log, log[-3000:]
    assert "callers MUST parse" in log, (
        "the dry-run line no longer tells the caller it must parse it:\n%s" % log[-3000:])
    with open(DOCS, encoding="utf-8") as fh:
        doc = fh.read()
    assert "callers MUST parse" in doc, (
        "docs/GATE-CHAIN.md no longer states the dry-run contract the code prints")
    assert "exit 0" in doc and "WOULD-REFUSE" in doc, (
        "docs/GATE-CHAIN.md section 7 does not describe the exit-0 / WOULD-REFUSE split")


# --------------------------------------------------------------------- (e)
# G2-BOUND-PRICE re-asserts GATE-OPERAND-VALIDATION's class repair: no hostile
# --projected-turn-wall may price a turn, so none may reach the runner. The numeric
# domain is the gate's own refusal (exit 8); a non-numeric operand is argparse's usage
# error (exit 2) and is recorded here rather than renumbered.
HOSTILE_NUMERIC = ("0", "-1", "1e-9", "nan", "inf")


def check_hostile_override_values_still_refuse(tmp, value, label):
    rc, log, marker = _cell_run(
        tmp, 48, ["--projected-turn-wall", value, "--max-wall", "1"],
        name="hostile-%s" % label)
    if label == "nonnumeric":
        assert rc == 2, ("--projected-turn-wall %r is a usage error (exit 2), the code "
                         "tools/gate_attack.py assigns a non-numeric G2 operand; got "
                         "%d\n%s" % (value, rc, log[-3000:]))
    else:
        assert rc == 8, ("--projected-turn-wall %r must be refused by G2 (exit 8), got "
                         "%d\n%s" % (value, rc, log[-3000:]))
        assert "G2 projection REFUSED" in log, log[-3000:]
    assert not os.path.exists(marker), (
        "--projected-turn-wall %r reached the runner past a refusal" % value)


def check_every_hostile_override_refuses_one_place(tmp):
    """All six named hostile values, each in its own run: none prices a turn."""
    for i, value in enumerate(HOSTILE_NUMERIC):
        check_hostile_override_values_still_refuse(tmp, value, "n%d-%s" % (i, value))
    check_hostile_override_values_still_refuse(tmp, "abc", "nonnumeric")


CHECKS = [
    ("a-override-negative", lambda t: check_nonpositive_override_refuses(t, -1)),
    ("a-override-zero", lambda t: check_nonpositive_override_refuses(t, 0)),
    ("a-boundary-allows", check_positive_override_equal_to_projection_allows),
    ("b-rows-priced-zero", check_row_file_pricing_at_zero_refuses),
    ("b-rows-positive-allows", check_row_file_with_positive_walls_still_allows),
    ("c-manifest-unique", check_two_manifests_in_one_second_do_not_collide),
    ("d-dry-run-contract", check_dry_run_contract),
    ("e-hostile-override-values", check_every_hostile_override_refuses_one_place),
]


class GateOverride(unittest.TestCase):
    def _case(self, name):
        tmp = tempfile.mkdtemp(prefix="gate-override-%s-" % name)
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        return tmp

    def test_a_nonpositive_override_refuses_negative(self):
        check_nonpositive_override_refuses(self._case("a-neg"), -1)

    def test_a_nonpositive_override_refuses_zero(self):
        check_nonpositive_override_refuses(self._case("a-zero"), 0)

    def test_a_positive_override_equal_to_projection_allows(self):
        check_positive_override_equal_to_projection_allows(self._case("a-boundary"))

    def test_b_row_file_pricing_at_zero_refuses(self):
        check_row_file_pricing_at_zero_refuses(self._case("b-zero"))

    def test_b_row_file_with_positive_walls_allows(self):
        check_row_file_with_positive_walls_still_allows(self._case("b-positive"))

    def test_c_manifests_are_unique_per_run(self):
        check_two_manifests_in_one_second_do_not_collide(self._case("c"))

    def test_d_dry_run_contract_matches_the_document(self):
        check_dry_run_contract(self._case("d"))

    def test_hostile_values_still_refuse_exit_8(self):
        check_every_hostile_override_refuses_one_place(self._case("hostile"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
