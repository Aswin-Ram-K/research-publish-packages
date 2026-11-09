"""LAUNCH-CONTRACT-DIFF guards.

Three jobs:
  * the card's own regression — the artefact must RECORD a harness-digest
    disagreement when the pinned bytes and the bytes on disk disagree, rather than
    reconcile it silently;
  * both directions of the --check mode, proved on a mutated copy of the tree;
  * the occurrence-set behaviour of an anchor: a literal that legitimately appears
    at two file:line pairs is AGREES with an occurrence count, and two different
    values are DISAGREES naming a file:line for each.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "experiments/ptr-engine/tools/launch_contract_diff.py")
MEAS = "experiments/ptr-engine/measure"
PIN = os.path.join(REPO, MEAS, "HARNESS-PIN.json")
PARAMS = os.path.join(REPO, MEAS, "GRID-PARAMS.json")
DIFF = os.path.join(REPO, "measure/LAUNCH-CONTRACT-DIFF.json")

LAUNCHER = "experiments/ptr-engine/tools/run_a_star.py"
RUNBOOK = "docs/GRID-RUNBOOK.md"

COPY = [
    MEAS + "/HARNESS-PIN.json", MEAS + "/GRID-PARAMS.json", MEAS + "/GRID-SHAPE.json",
    MEAS + "/REQUEST-LEDGER.json", MEAS + "/LEDGER-GRID-BASELINE-2.json",
    "experiments/ptr-engine/tools/run_a_star.py",
    "experiments/ptr-engine/longrun/run_longrun.py",
    "experiments/ptr-engine/longrun/cell.py",
    "experiments/ptr-engine/longrun/client.py",
    "experiments/ptr-engine/longrun/grade_v5.py",
    "experiments/ptr-engine/tools/det_verify.py",
    "experiments/ptr-engine/longrun/analyze_stats.py",
    "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json",
    "docs/GRID-PARAMS.md", "docs/GRID-RUNBOOK.md", "docs/GRID-SHAPE.md",
    "docs/GATE-CHAIN.md",
]


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _copy_tree(tmp_path):
    root = tmp_path / "tree"
    for rel in COPY:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(os.path.join(REPO, rel), dst)
    return root


def _mutate(root, rel, old, new):
    path = root / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, "mutation anchor missing in %s: %r" % (rel, old)
    path.write_text(text.replace(old, new), encoding="utf-8")


def _mutate_tolerant(root, rel, old, new):
    """Apply a reconciliation only if the tree still needs it.

    A legitimate anchor may already carry the reconciled value — the residual card
    fixed the launcher help string and the doc's round constant, so `old` is gone.
    Tolerate that, but never tolerate a tree that carries NEITHER spelling: that
    would mean the anchor moved and the fixture no longer proves anything.
    """
    path = root / rel
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return "reconciled"
    assert new in text, (
        "neither the stale spelling %r nor the reconciled %r is present in %s"
        % (old, new, rel))
    return "already-agreed"


def _sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _repin(root):
    """Re-record the copy's pin over the copy's own bytes.

    A launchable tree is a single-valued contract; the live tree is not, because a
    harness file moved after the pin froze.  Bumping the pin belongs to the card
    that owns it, so this fixture does it on the COPY only — the real pin record is
    never touched, and the tool still recomputes the digest from bytes.
    """
    pin_path = root / MEAS / "HARNESS-PIN.json"
    old = _load(pin_path)["harness_sha256"]
    doc = _load(pin_path)
    files = {f["name"]: _sha256(root / f["path"]) for f in doc["files"]}
    new = hashlib.sha256("".join("%s:%s\n" % (n, files[n])
                                 for n in sorted(files)).encode()).hexdigest()
    for f in doc["files"]:
        f["sha256"] = files[f["name"]]
    doc["harness_sha256"] = new
    pin_path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    for rel in (LAUNCHER, RUNBOOK, MEAS + "/GRID-PARAMS.json"):
        p = root / rel
        p.write_text(p.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
    return new


def _single_valued(root):
    """Leave a copy whose every number carries one distinct value.

    The stale spellings are reconciled (tolerantly — the residual card already
    fixed two of them), and the pin is re-recorded over the copy's own bytes, so
    the only disagreements left in the fixture are the documented staleness.
    """
    pin = _load(root / MEAS / "HARNESS-PIN.json")["harness_sha256"]
    params = _load(root / MEAS / "GRID-PARAMS.json")
    params["harness_pin"]["harness_sha256"] = pin
    (root / MEAS / "GRID-PARAMS.json").write_text(json.dumps(params, indent=1),
                                                  encoding="utf-8")
    _mutate_tolerant(root, LAUNCHER,
                     "handed to cell.py (default 67)",
                     "handed to cell.py (default 108)")
    _mutate_tolerant(root, "docs/GRID-PARAMS.md",
                     "TOOL_FETCH_ROUNDS_PER_ARM = 24",
                     "TOOL_FETCH_ROUNDS_PER_ARM = 48")
    _repin(root)


def _check(root):
    proc = subprocess.run([sys.executable, TOOL, "--check", "--root", str(root)],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def _doc(root):
    proc = subprocess.run([sys.executable, TOOL, "--json", "--root", str(root)],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _number(doc, cid):
    return [n for n in doc["numbers"] if n["id"] == cid][0]


def test_pin_record_matches_launcher():
    """The digest the launcher passes is the pin record's generation-4 digest."""
    sys.path.insert(0, os.path.join(REPO, "experiments/ptr-engine/tools"))
    import run_a_star
    assert _load(PIN)["generation"] == 7
    assert run_a_star.HARNESS_PIN == _load(PIN)["harness_sha256"]


def test_grid_params_digest_is_pin_or_recorded_predecessor():
    """THE TRAP: GRID-PARAMS must not quote a third, unrecorded harness digest."""
    pin_doc = _load(PIN)
    allowed = {pin_doc["harness_sha256"], pin_doc["superseded_harness_sha256"]}
    quoted = _load(PARAMS)["harness_pin"]["harness_sha256"]
    assert quoted in allowed, (
        "GRID-PARAMS.json quotes a harness digest (%s) that is neither the live pin "
        "(%s) nor the predecessor the pin records (%s): a launcher following "
        "GRID-PARAMS would abort at cell.py stage 2/7"
        % (quoted, pin_doc["harness_sha256"], pin_doc["superseded_harness_sha256"]))


def test_check_mode_zero_on_single_valued_tree(tmp_path):
    root = _copy_tree(tmp_path)
    _single_valued(root)
    rc, out = _check(root)
    assert rc == 0, "expected exit 0 on a single-valued contract, got %d\n%s" % (rc, out)
    assert "disagreements:" not in out


def test_check_mode_one_on_disagreement(tmp_path):
    root = _copy_tree(tmp_path)
    _single_valued(root)
    assert _check(root)[0] == 0
    # put the stale generation-3 digest back: exactly one number must disagree
    params = _load(root / MEAS / "GRID-PARAMS.json")
    params["harness_pin"]["harness_sha256"] = _load(PIN)["superseded_harness_sha256"]
    (root / MEAS / "GRID-PARAMS.json").write_text(json.dumps(params, indent=1),
                                                  encoding="utf-8")
    rc, out = _check(root)
    assert rc == 1, "expected exit 1 after mutating the pin, got %d\n%s" % (rc, out)
    assert "harness_pin_digest" in out


def test_artefact_and_check_mode_agree():
    doc = _load(DIFF)
    rc, _ = _check(REPO)
    assert rc == doc["summary"]["check_exit"]
    assert rc == (1 if doc["summary"]["disagreements"] else 0)


def test_duplicate_occurrence_is_agrees_with_count(tmp_path):
    """THE NEW BEHAVIOUR: the same value written twice is AGREES, occurrences=2.

    A launcher constant restated once more is not a contradiction, and a tool that
    cannot say so cannot audit a contract spanning a builder, a doc and a constant.
    """
    root = _copy_tree(tmp_path)
    _single_valued(root)
    before = _number(_doc(root), "canary_max_wall")
    assert before["status"] == "AGREES"
    assert before["occurrence_count"] == 1
    launcher = root / LAUNCHER
    text = launcher.read_text(encoding="utf-8")
    assert "CANARY_MAX_WALL = 900\n" in text
    launcher.write_text(text.replace("CANARY_MAX_WALL = 900\n",
                                     "CANARY_MAX_WALL = 900\n"
                                     "CANARY_MAX_WALL = 900  # restated, same value\n", 1),
                        encoding="utf-8")
    rc, out = _check(root)
    assert rc == 0, out
    after = _number(_doc(root), "canary_max_wall")
    assert after["status"] == "AGREES", after["reason"]
    assert after["occurrence_count"] == 2, after["reason"]
    assert after["reason"] == "single value across 2 occurrence(s)"
    pairs = [(o["value"], o["line"]) for o in after["occurrences"]]
    assert len(pairs) == 2 and len({ln for _, ln in pairs}) == 2, pairs


def test_disagreement_names_both_file_lines(tmp_path):
    """Two different values for one anchor must name a file:line for EACH."""
    root = _copy_tree(tmp_path)
    _single_valued(root)
    assert _check(root)[0] == 0
    launcher = root / LAUNCHER
    text = launcher.read_text(encoding="utf-8")
    old = 'ap.add_argument("--budget", type=int, default=108'
    assert old in text
    launcher.write_text(text.replace(old, old.replace("108", "67"), 1), encoding="utf-8")
    rc, out = _check(root)
    assert rc == 1, out
    assert "per_cell_budget" in out
    entry = _number(_doc(root), "per_cell_budget")
    assert entry["status"] == "DISAGREES"
    assert re.search(r"108 at .*run_a_star\.py:\d+", entry["reason"]), entry["reason"]
    assert re.search(r"67 at .*run_a_star\.py:\d+", entry["reason"]), entry["reason"]


def test_grep_anchor_yields_every_occurrence():
    """Unit-level: one anchor returns the whole ordered pair set, not its first hit."""
    sys.path.insert(0, os.path.join(REPO, "experiments/ptr-engine/tools"))
    import launch_contract_diff as lcd
    probe = lcd.G("docs/GRID-PARAMS.md", r"TOOL_FETCH_ROUNDS_PER_ARM = (\d+)")
    out = lcd.run_probe(REPO, probe)
    assert out["ok"], out["problem"]
    assert len(out["occurrences"]) >= 2, out["occurrences"]
    assert {o["value"] for o in out["occurrences"]} == {"48"}
    lines = [o["line"] for o in out["occurrences"]]
    assert lines == sorted(lines), lines
    assert len(set(lines)) == len(lines), lines
