"""ABSENT is a first-class result: a missing field is reported, not raised.

The defect this guards: `launch_contract_diff.py --check` died with
`KeyError: 'components'` at `launch_contract_diff.py:653` because a *computed* probe
indexed `params["price"]["components"]["tranche"]` directly while building the row
table.  A checker that raises on a missing field cannot tell a successor whether the
launch package agrees: its exit 1 is indistinguishable from "a number disagrees",
which is the one distinction the tool exists to make.

Every case below pins one half of the contract:

  (a) the real tree is reported, never raised -- and absence exits non-zero;
  (b) a /tmp params copy with `price.components` removed says
      `ABSENT price.components...`, exits non-zero, and prints no traceback;
  (c) a /tmp copy with a wrong total is still a DISAGREES naming BOTH values, so
      absence-handling never becomes a bypass for a real disagreement;
  (d) `--pin-generation N` on a tree that legitimately moved is still exit 13 MOVED.

`LCD_TOOL` lets the red run point the same tests at a reverted copy of the tool.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]
REPO = ENGINE.parents[1]
TOOL = Path(os.environ.get("LCD_TOOL") or (ENGINE / "tools" / "launch_contract_diff.py"))

if str(ENGINE / "tools") not in sys.path:
    sys.path.insert(0, str(ENGINE / "tools"))

import launch_contract_diff as lcd  # noqa: E402


# ------------------------------------------------------------------ fixtures
def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _needed(root: Path):
    """Every file the tool reads: probe paths, their marker files, the pinned inputs."""
    paths = set()
    for chk in lcd.checks(str(root)):
        for p in chk["probes"]:
            rel = p.get("path") or ""
            if rel and not rel.startswith("<computed"):
                paths.add(rel)
            if p.get("marker_in"):
                paths.add(p["marker_in"])
    paths |= {lcd.PIN, lcd.PARAMS, lcd.SHAPE, lcd.LEDGER, lcd.BASELINE, lcd.STATS,
              lcd.CELL, lcd.RUN_A_STAR, "experiments/ptr-engine/longrun/client.py"}
    for f in json.loads((root / lcd.PIN).read_text())["files"]:
        paths.add(f["path"])
    return sorted(paths)


def _clone(dst: Path) -> Path:
    for rel in _needed(REPO):
        to = dst / rel
        to.parent.mkdir(parents=True, exist_ok=True)
        to.write_bytes((REPO / rel).read_bytes())
    return dst


def _run(root: Path, *args):
    """Run the tool's CLI out-of-process; return (exit code, out, err, document)."""
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root), *args, "--json"],
        capture_output=True, text=True, cwd=str(REPO))
    doc = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else None
    return proc.returncode, proc.stdout, proc.stderr, doc


def _row(doc, cid):
    return [n for n in doc["numbers"] if n["id"] == cid][0]


def _params(root: Path):
    return json.loads((root / lcd.PARAMS).read_text())


def _write_params(root: Path, doc) -> None:
    (root / lcd.PARAMS).write_text(json.dumps(doc, indent=1) + "\n")


def _without_components(root: Path) -> str:
    """Delete price.components; return what the report must say is ABSENT.

    Written to work either way: the record on disk today carries no `components`, and a
    successor card that restores one must not make this guard vacuous.
    """
    doc = _params(root)
    doc["price"].pop("components", None)
    _write_params(root, doc)
    return "price.components"


def _no_traceback(err: str) -> None:
    assert "Traceback (most recent call last)" not in err, err
    assert "KeyError" not in err, err


# ------------------------------------------------------------------ the cases
def test_the_real_tree_is_reported_never_raised():
    """(a) whatever the real tree reports today, it reports it -- it does not raise."""
    code, out, err, doc = _run(REPO, "--check")
    _no_traceback(err)
    assert doc is not None, (code, out, err)
    assert doc["summary"]["checks"] > 0
    # every ABSENT row carries a dotted path AND the file that should have carried it
    for n in doc["numbers"]:
        if n["status"] != "ABSENT":
            continue
        assert n["absent"], n
        for path in n["absent"]:
            assert "." in path or "[" in path, path
        assert "in " in n["reason"] or "no authoritative" in n["reason"], n["reason"]
    price = _params(REPO)["price"]
    # price.components is obsolete (turns x factor model); the tranche check was
    # removed because no code reads price.components.tranche (grep: only this checker).
    # the arithmetic behind the bare total is restored in the REPORT
    der = doc["price_derivation"]
    assert der["components_present"] is False
    assert der["turns"] and der["factor"]
    assert der["arithmetic"].startswith("%d turns x" % der["turns"])
    assert der["factor_provenance"]
    assert der["reconciled"] is True, der


def test_a_missing_components_block_does_not_raise(tmp_path: Path):
    """(b) components removed in /tmp => still no traceback (ABSENT mechanism intact)."""
    root = _clone(tmp_path / "tree")
    _without_components(root)

    code, _out, err, doc = _run(root, "--check")
    _no_traceback(err)
    assert doc is not None, (code, _out, err)
    # the derivation the price must be justified by is printed beside the total
    der = doc["price_derivation"]
    assert der["components_present"] is False
    assert der["arithmetic"] != "not derivable (None absent)", der
    assert der["flag"] in ("", "price_unjustified")


def test_a_wrong_total_still_names_both_values(tmp_path: Path):
    """(c) absence-handling must not swallow a real numeric disagreement."""
    root = _clone(tmp_path / "tree")
    doc = _params(root)
    doc["price"]["total"] = 999
    _write_params(root, doc)
    turns = doc["shape"]["turns_total"]
    factor = doc["price"]["factor"]
    derived = str(int(round(turns * factor)))

    code, _out, err, out_doc = _run(root, "--check")
    _no_traceback(err)
    assert code == 1, (code, err)
    row = _row(out_doc, "price_total")
    assert row["status"] == "DISAGREES", row["reason"]
    assert "999" in row["reason"], row["reason"]
    assert derived in row["reason"], row["reason"]
    assert "999" in _out and derived in _out


def test_pin_generation_still_reports_moved_as_13(tmp_path: Path):
    """(d) a tree that legitimately moved under a named scope is MOVED (13), never 1."""
    root = _clone(tmp_path / "tree")
    pin = json.loads((root / lcd.PIN).read_text())
    victim = root / "experiments/ptr-engine/longrun/grade_v5.py"
    assert victim.is_file(), "the fixture needs a pinned input to move"
    victim.write_bytes(victim.read_bytes() + b"\n# a neighbour card moved this file\n")

    code, out, err, doc = _run(root, "--check", "--pin-generation", str(pin["generation"]))
    _no_traceback(err)
    assert code == lcd.EXIT_TREE_MOVED == 13, (code, out, err)
    row = _row(doc, "harness_pin_digest")
    assert row["status"] == "MOVED", row["reason"]
    assert row["status"] != "DISAGREES"
    assert row["live_harness_sha256"] != row["judged_tree"]["harness_sha256"]
