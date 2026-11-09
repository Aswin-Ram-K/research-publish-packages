#!/usr/bin/env python3
"""matrix_audit.py — declared-cell inventory and honesty audit of the LR-01 grid.

WHY
---
The regrade of the whole on-disk record reported 56 answered triples / 92 cells =
5 pass · 38 fail · 36 missing · 13 undecidable.  A *missing* cell and a *failed*
cell are both "not pass", so every rate computed over the grid silently changes
its denominator depending on which one you think it is.  This tool never conflates
them: it builds the **declared cell space** independently from the fixture and the
row files on disk, classifies every declared cell into exactly one state with a
machine-readable reason, and prints every accuracy as ``passed / decidable`` with
all four counts on the same line.

Contract
--------
* Zero model requests.  The only judge is ``det_verify`` (AST-derived ground truth),
  imported and called — no matching logic is re-implemented here.
* Read-only on every existing matrix, grade and row file.  The only file written is
  the audit artifact named by ``--out`` (default ``measure/MATRIX-COVERAGE.json``).
* A cell's state is one of:

  ``pass`` / ``fail``            graded, carrying the judge's own reason string
  ``missing_row_absent``         no row file for that arm exists
  ``missing_turn_absent``        the row file exists but has no row for that turn
  ``missing_answer_empty``       the row exists but carries no answer text
  ``missing_checkpoint_absent``  the fixture declares no checkpoint with that id
  ``undecidable``                the judge returns undecidable / pass:null

Declared cell space
-------------------
``(rows_file, arm, checkpoint_id, rep)`` where:

* ``rows_file`` ranges over the LR-01 long-run grid batches on disk
  (``rows-longrun-*.jsonl`` in ``--rows-dir``) whose rows carry the fixture's
  ``task_id``.  Single-cell probe files (``rows-cell-*``), pilots
  (``rows-pilot-*``) and the non-longrun corpus files never enter the grid.
* ``arm`` is every arm that actually appears in that file (derived from the rows,
  never from a matrix).
* ``checkpoint_id`` is every checkpoint the fixture declares — ``cp.<i>.t<turn>``
  for ``fixture["checkpoints"]`` plus ``repair.t<repair.at_turn>`` when declared.
* ``rep`` is each rep value the rows declare (1 on every batch on disk).

92 = 23 run/arm pairs x 4 declared checkpoint ids x 1 rep.
"""

import argparse
import collections
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import det_verify  # noqa: E402  (instrument: AST-derived ground truth, offline)

ROOT = det_verify.ROOT
MEASURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure")
DEFAULT_OUT = os.path.join(MEASURE, "MATRIX-COVERAGE.json")
LONGRUN_GLOB = "rows-longrun-*.jsonl"
# The two artefacts that DECLARE the population.  Neither of them is a row file.
ARMS_REGISTRY = os.path.join(ROOT, "experiments", "ptr-engine", "longrun",
                             "run_longrun.py")
MANIFEST_GLOB = os.path.join(ROOT, "experiments", "ptr-engine", "longrun",
                             "manifests", "*.json")

STATES = (
    "extraneous_cell",
    "pass",
    "fail",
    "missing_row_absent",
    "missing_turn_absent",
    "missing_answer_empty",
    "missing_checkpoint_absent",
    "undecidable",
)
MISSING_STATES = tuple(s for s in STATES if s.startswith("missing_"))
PARTIAL_MARK = " \u2013 PARTIAL GRID"


# --------------------------------------------------------------------------- #
# declared space — derived from the fixture and the row files, never a matrix
# --------------------------------------------------------------------------- #
def _key_line(path, key):
    """1-based line of the first ``"key":`` at the start of a line, else None."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            if line.strip().startswith('"%s"' % key):
                return i
    return None


def declared_checkpoints(fixture):
    """[(checkpoint_id, turn)] in fixture order, plus the declared repair turn.

    The id is the FIXTURE's own ``id`` field when it carries one, so a row that
    names an id the fixture never declared cannot be mistaken for a declared cell.
    """
    out = []
    for i, cp in enumerate(fixture.get("checkpoints") or []):
        cid = cp.get("id") or ("cp.%d.t%d" % (i, int(cp["turn"])))
        out.append((cid, int(cp["turn"])))
    repair = fixture.get("repair") or {}
    if "at_turn" in repair:
        out.append(("repair.t%d" % int(repair["at_turn"]), int(repair["at_turn"])))
    return out


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def declared_arms_from_registry(path=ARMS_REGISTRY):
    """``(arms, arms_line, refusal_line)`` read from the runner by AST, not import.

    ``run_longrun.py`` is the only thing that can emit a long-run cell, and its
    per-arm builder raises ``ValueError("unknown arm ...")`` for any name outside
    this tuple — so the tuple, not the rows, is what makes an arm name legal.
    """
    import ast

    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    arms = None
    arms_line = None
    for node in ast.parse(source).body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, (ast.Tuple, ast.List)):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "ARMS":
                arms = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
                arms_line = node.lineno
    if arms is None:
        raise RuntimeError("%s declares no ARMS tuple" % path)
    refusal_line = None
    for i, line in enumerate(source.splitlines(), 1):
        if "unknown arm" in line:
            refusal_line = i
            break
    return arms, arms_line, refusal_line


def declared_run_arms(manifest_glob=MANIFEST_GLOB):
    """``({rows_basename: set(arms)}, {rows_basename: [manifest names]})``.

    The per-run manifests are written by the runner *before* the run and each
    carries ``arm`` and ``rows_path``: they say which arm produced which rows
    file, independently of what the rows later contain.
    """
    declared = {}
    sources = {}
    for path in sorted(glob.glob(manifest_glob)):
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        base = os.path.basename(manifest.get("rows_path") or "")
        arm = manifest.get("arm")
        if not base or not arm:
            continue
        declared.setdefault(base, set()).add(arm)
        sources.setdefault(base, []).append(os.path.basename(path))
    return declared, sources


def declared_space(rows_dir, fixture, manifests=MANIFEST_GLOB,
                   registry=ARMS_REGISTRY, fixture_path=None):
    """Build the declared cell space from the DECLARATIONS; return (cells, derivation).

    An arm is admitted only when an artefact that is not a row file names it:
    the run manifest for that rows file, else the runner's ``ARMS`` registry.
    """
    task_id = fixture.get("task_id")
    cps = declared_checkpoints(fixture)
    derivation_fixture_path = fixture_path or det_verify.FIXTURE
    registry_arms, arms_line, refusal_line = declared_arms_from_registry(registry)
    registry_set = set(registry_arms)
    mdecl, msources = declared_run_arms(manifests)
    files = sorted(glob.glob(os.path.join(rows_dir, LONGRUN_GLOB)))
    declared_reps = [1]
    gaps = []
    unknown_manifest_arms = {}
    runs = []
    for path in files:
        base = os.path.basename(path)
        rows = load_rows(path)
        rows = [r for r in rows if r.get("task_id") == task_id]
        if not rows:
            continue
        present = sorted({r.get("arm") for r in rows if r.get("arm")})
        from_manifest = mdecl.get(base)
        if from_manifest:
            arms_source = "manifest"
            arms = [a for a in sorted(from_manifest) if a in registry_set]
            unknown = sorted(from_manifest - registry_set)
            if unknown:
                unknown_manifest_arms[base] = unknown
        else:
            arms_source = "registry"
            arms = list(registry_arms)
            gaps.append({"rows_file": base,
                         "issue": "no run manifest declares this rows file",
                         "fallback": "runner ARMS registry (all declared arms)"})
        reps = list(declared_reps)
        by_arm = collections.defaultdict(list)
        for r in rows:
            by_arm[r.get("arm")].append(r)
        runs.append({
            "rows_file": base,
            "path": path,
            "sha256": sha256_file(path),
            "arms": arms,
            "arms_source": arms_source,
            "arms_present_in_rows": present,
            "reps": reps,
            "manifest_declarations": len(msources.get(base, [])),
            "rows": by_arm,
            "rows_count": len(rows),
        })

    cells = []
    for run in runs:
        for arm in run["arms"]:
            for rep in run["reps"]:
                for cp_id, turn in cps:
                    cells.append({
                        "rows_file": run["rows_file"],
                        "path": run["path"],
                        "arm": arm,
                        "rep": rep,
                        "checkpoint": cp_id,
                        "turn": turn,
                        "state": None,
                        "reason": None,
                    })
    derivation = {
        "rule": ("(rows_file, arm, checkpoint_id, rep): rows_file ranges over "
                 "rows-longrun-*.jsonl in the rows dir whose rows carry the fixture "
                 "task_id; arm is DECLARED OUTSIDE THE ROWS — by the run manifest "
                 "that produced the file (manifests/<run>.json: arm + rows_path), "
                 "falling back to the runner's ARMS registry when no manifest "
                 "declares the file; a name found in neither is `extraneous_cell`, "
                 "never a discovery.  checkpoint_id is every id the FIXTURE "
                 "declares (cp.<i>.t<turn>) plus the declared repair turn; rep is "
                 "the single rep the fixture's run contract declares."),
        "task_id": task_id,
        "fixture": fixture_path or det_verify.FIXTURE,
        "longrun_glob": LONGRUN_GLOB,
        "reps": list(declared_reps),
        "declaration": {
            "arm_registry": {
                "path": os.path.relpath(registry, ROOT),
                "line": arms_line,
                "refusal_line": refusal_line,
                "why_authoritative": (
                    "run_longrun.py is the only cell driver: its ARMS tuple at "
                    "line %s names every arm it will build, and its per-arm builder "
                    "raises ValueError('unknown arm ...') at line %s for any other "
                    "name, so an arm absent from this tuple cannot have been run "
                    "honestly." % (arms_line, refusal_line)),
                "arms": registry_arms,
            },
            "run_manifests": {
                "glob": os.path.relpath(manifests, ROOT),
                "why_authoritative": (
                    "each manifest is written before its run and pairs `arm` with "
                    "`rows_path`, so it declares which arm may appear in which rows "
                    "file without consulting the rows."),
                "files": sum(len(v) for v in msources.values()),
                "arms_by_file": {r["rows_file"]: r["arms"] for r in runs},
                "arms_source_by_file": {r["rows_file"]: r["arms_source"] for r in runs},
            },
            "checkpoints": {
                "path": os.path.relpath(derivation_fixture_path, ROOT),
                "checkpoints_line": _key_line(derivation_fixture_path, "checkpoints"),
                "repair_line": _key_line(derivation_fixture_path, "repair"),
            },
            "declaration_gaps": gaps,
            "manifest_arms_not_in_registry": unknown_manifest_arms,
        },
        "runs": [{"rows_file": r["rows_file"], "sha256": r["sha256"],
                  "arms": r["arms"], "arms_source": r["arms_source"],
                  "arms_present_in_rows": r["arms_present_in_rows"],
                  "reps": r["reps"],
                  "rows": r["rows_count"]} for r in runs],
        "checkpoints": [{"id": c, "turn": t} for c, t in cps],
        "run_arm_pairs": sum(len(r["arms"]) for r in runs),
        "cells": len(cells),
        "formula": "%d run/arm pairs x %d checkpoint ids x 1 rep = %d cells" % (
            sum(len(r["arms"]) for r in runs), len(cps), len(cells)),
        "excluded_from_grid": {
            "rows-cell-*": "single-cell probe runs (6 turns, never reach a checkpoint turn)",
            "rows-pilot-*": "5-turn pilot; never reaches checkpoint turn 12",
            "rows-baseline/equalinfo/live": "not LR-01 long-run batches (no task_id LR-01)",
        },
        "sensitivity": ("Including the two sub-grid probe files (rows-cell-*, "
                        "rows-pilot-*) would add 8 cells, all missing_turn_absent; "
                        "it would change no pass, no fail and no denominator."),
    }
    return cells, derivation


# --------------------------------------------------------------------------- #
# the fifth state: a cell the rows contain and the declaration does not
# --------------------------------------------------------------------------- #
def row_checkpoint_id(row):
    """The checkpoint id a row names, when it names one at all."""
    cp = row.get("checkpoint")
    if isinstance(cp, str):
        return cp
    if isinstance(cp, dict):
        for key in ("id", "checkpoint", "checkpoint_id"):
            if isinstance(cp.get(key), str):
                return cp[key]
    return None


def scan_extraneous(rows_dir, fixture, derivation):
    """Every row whose (arm, checkpoint) pair the declaration does not contain.

    The asymmmetry is the point: a DECLARED cell with no rows stays ``missing_*``
    (an unrun arm must not scream), while a row whose pair is undeclared is
    ``extraneous_cell`` and makes the audit non-clean.
    """
    task_id = fixture.get("task_id")
    declared = {c["id"]: c["turn"] for c in derivation["checkpoints"]}
    declared_turns = set(declared.values())
    declaration = derivation["declaration"]
    arms_by_file = declaration["run_manifests"]["arms_by_file"]
    reps = set(derivation["reps"])
    found = collections.OrderedDict()
    for path in sorted(glob.glob(os.path.join(rows_dir, LONGRUN_GLOB))):
        base = os.path.basename(path)
        arms = arms_by_file.get(base)
        if arms is None:
            continue
        for row in load_rows(path):
            if row.get("task_id") != task_id:
                continue
            arm = row.get("arm")
            turn = row.get("turn")
            rep = row.get("rep", 1)
            cp_id = row_checkpoint_id(row)
            kind = label = reason = None
            if arm not in arms:
                kind, label = "arm", str(arm)
                reason = ("arm %r appears in %s but no declaration admits it "
                          "(declared for this file: %s)"
                          % (arm, base, ", ".join(arms) or "none"))
            elif rep not in reps:
                kind, label = "rep", "rep.%s" % (rep,)
                reason = "rep %r is not declared (declared: %s)" % (rep, sorted(reps))
            elif cp_id is not None and cp_id not in declared:
                kind, label = "checkpoint", cp_id
                reason = ("row at turn %s carries checkpoint %r; the fixture "
                          "declares %s" % (turn, cp_id, ", ".join(sorted(declared))))
            elif row.get("is_checkpoint") and turn not in declared_turns:
                kind, label = "checkpoint", "turn.%s" % (turn,)
                reason = ("row is flagged is_checkpoint at turn %s, where the "
                          "fixture declares no checkpoint (declared turns: %s)"
                          % (turn, sorted(declared_turns)))
            if kind is None:
                continue
            key = (base, str(arm), kind, label)
            if key not in found:
                found[key] = {
                    "rows_file": base,
                    "path": path,
                    "arm": arm,
                    "rep": rep,
                    "checkpoint": cp_id if kind == "checkpoint" else None,
                    "turn": turn if isinstance(turn, int) else None,
                    "kind": kind,
                    "label": label,
                    "declared": False,
                    "state": "extraneous_cell",
                    "reason": reason,
                    "rows": 0,
                }
            found[key]["rows"] += 1
    return list(found.values())


# --------------------------------------------------------------------------- #
# classification
# --------------------------------------------------------------------------- #
def answer_text(row):
    """The assistant answer a row carries, or '' when it carries none."""
    content = row.get("content") or ""
    return content if content.strip() else ""


def pick_answer(texts):
    """Canonical answer when a turn carries several distinct texts: longest wins."""
    return sorted(texts, key=lambda t: (-len(t), t))[0]


def classify_cells(cells, fixture, truth):
    """Fill state/reason for every declared cell.  Pure file reading + AST judge."""
    by_file = {}
    path_of = {}
    for c in cells:
        path_of[c["rows_file"]] = c["path"]
        by_file.setdefault(c["rows_file"], []).append(c)

    declared = {cid: turn for cid, turn in declared_checkpoints(fixture)}
    for rows_file, group in by_file.items():
        path = path_of[rows_file]
        rows = load_rows(path) if os.path.exists(path) else []
        for arm in sorted({c["arm"] for c in group}):
            arm_rows = [r for r in rows if r.get("arm") == arm]
            for c in group:
                if c["arm"] != arm:
                    continue
                if c["checkpoint"] not in declared:
                    c["state"] = "missing_checkpoint_absent"
                    c["reason"] = "fixture declares no checkpoint %r" % c["checkpoint"]
                    continue
                if c["turn"] != declared[c["checkpoint"]]:
                    c["reason"] = ("declared turn for %s is %d, cell says %d"
                                   % (c["checkpoint"], declared[c["checkpoint"]], c["turn"]))
                turn_rows = [r for r in arm_rows if r.get("turn") == c["turn"]]
                c["rows_at_turn"] = len(turn_rows)
                texts = sorted({answer_text(r) for r in turn_rows if answer_text(r)})
                c["distinct_texts"] = len(texts)
                if not turn_rows:
                    c["state"] = "missing_turn_absent"
                    c["reason"] = ("no row for arm %r at turn %d in %s"
                                   % (arm, c["turn"], rows_file))
                    continue
                if not texts:
                    c["state"] = "missing_answer_empty"
                    c["reason"] = ("%d row(s) for arm %r at turn %d in %s, every one "
                                   "with empty content" % (len(turn_rows), arm,
                                                           c["turn"], rows_file))
                    continue
                answer = pick_answer(texts)
                c["answer_sha256"] = hashlib.sha256(answer.encode()).hexdigest()
                c["answer_chars"] = len(answer)
                try:
                    ok, reason, _detail = det_verify.verify_probe(
                        {"checkpoint": c["checkpoint"]}, answer, truth)
                except KeyError:
                    c["state"] = "missing_checkpoint_absent"
                    c["reason"] = "fixture declares no checkpoint %r" % c["checkpoint"]
                    continue
                if reason == "undecidable" or ok is None:
                    c["state"] = "undecidable"
                    c["reason"] = "undecidable" if reason == "undecidable" else str(reason)
                else:
                    c["state"] = "pass" if ok else "fail"
                    c["reason"] = reason
    return cells


# --------------------------------------------------------------------------- #
# counting and the denominator rule
# --------------------------------------------------------------------------- #
def count_states(cells):
    return dict(collections.Counter(c["state"] for c in cells))


def per_arm_counts(cells):
    out = collections.defaultdict(lambda: collections.Counter())
    for c in cells:
        out[c["arm"]][c["state"]] += 1
    return {arm: dict(counts) for arm, counts in sorted(out.items())}


def per_run_arm_counts(cells):
    out = collections.defaultdict(lambda: collections.Counter())
    for c in cells:
        out[(c["rows_file"], c["arm"])][c["state"]] += 1
    return {"%s :: %s" % k: dict(v) for k, v in sorted(out.items())}


def accuracy_line(label, counts):
    """``label passed/decidable (pass P, fail F, missing M, undecidable U)[ – PARTIAL GRID]``

    decidable is ALWAYS pass + fail.  A bare ``1/3`` or bare ``33 %`` is the defect
    this tool exists to prevent, so the four counts are printed in the same line and
    the partial-grid marker is appended whenever anything is missing or undecidable.
    """
    p = counts.get("pass", 0)
    f = counts.get("fail", 0)
    m = sum(counts.get(s, 0) for s in MISSING_STATES)
    u = counts.get("undecidable", 0)
    line = "%s %d/%d (pass %d, fail %d, missing %d, undecidable %d)" % (
        label, p, p + f, p, f, m, u)
    if m + u > 0:
        line += PARTIAL_MARK
    return line


def render_table(cells):
    """`arm x state` table with totals, one row per arm plus a TOTAL row."""
    arms = sorted({c["arm"] for c in cells})
    header = "%-20s %5s %5s %6s %6s %6s %6s %6s %6s" % (
        "arm", "pass", "fail", "m_row", "m_turn", "m_ans", "m_cp", "undec", "total")
    lines = [header, "-" * len(header)]
    totals = collections.Counter()
    for arm in arms:
        counts = collections.Counter(c["state"] for c in cells if c["arm"] == arm)
        totals.update(counts)
        lines.append("%-20s %5d %5d %6d %6d %6d %6d %6d %6d" % (
            arm, counts["pass"], counts["fail"],
            counts["missing_row_absent"], counts["missing_turn_absent"],
            counts["missing_answer_empty"], counts["missing_checkpoint_absent"],
            counts["undecidable"], sum(counts.values())))
    lines.append("-" * len(header))
    lines.append("%-20s %5d %5d %6d %6d %6d %6d %6d %6d" % (
        "TOTAL", totals["pass"], totals["fail"],
        totals["missing_row_absent"], totals["missing_turn_absent"],
        totals["missing_answer_empty"], totals["missing_checkpoint_absent"],
        totals["undecidable"], sum(totals.values())))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# audit
# --------------------------------------------------------------------------- #
def audit(rows_dir=MEASURE, fixture_path=det_verify.FIXTURE, truth=None,
          manifests=MANIFEST_GLOB, registry=ARMS_REGISTRY):
    with open(fixture_path, encoding="utf-8") as fh:
        fixture = json.load(fh)
    truth = truth or det_verify.Truth(fixture_path)
    cells, derivation = declared_space(rows_dir, fixture, manifests, registry,
                                      fixture_path=fixture_path)
    classify_cells(cells, fixture, truth)
    declared_cells = len(cells)
    extraneous = scan_extraneous(rows_dir, fixture, derivation)
    cells = cells + extraneous

    counts = count_states(cells)
    per_arm = per_arm_counts(cells)
    per_run_arm = per_run_arm_counts(cells)
    total = dict((s, counts.get(s, 0)) for s in STATES)
    total["cells"] = len(cells)

    acc = {
        "rule": "passed / decidable, decidable = pass + fail; missing and "
                "undecidable are printed beside it and never enter the denominator",
        "overall": accuracy_line("overall", counts),
        "per_arm": {arm: accuracy_line(arm, c) for arm, c in per_arm.items()},
        "per_run_arm": {k: accuracy_line(k, c) for k, c in per_run_arm.items()},
    }
    result = {
        "unit": "MATRIX-HONESTY",
        "generated_by": "experiments/ptr-engine/tools/matrix_audit.py",
        "live_requests": 0,
        "instrument": {
            "path": "experiments/ptr-engine/tools/det_verify.py",
            "sha256": sha256_file(os.path.join(HERE, "det_verify.py")),
            "api_used": "det_verify.Truth() + det_verify.verify_probe(...)",
        },
        "fixture": {"path": os.path.relpath(fixture_path, ROOT),
                    "sha256": sha256_file(fixture_path)},
        "declared_space": derivation,
        "states": total,
        "per_arm": per_arm,
        "per_run_arm": per_run_arm,
        "accuracy": acc,
        "declared_cells": declared_cells,
        "extraneous": extraneous,
        "cells": cells,
    }
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rows-dir", default=MEASURE)
    ap.add_argument("--fixture", default=det_verify.FIXTURE)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--manifests", default=MANIFEST_GLOB,
                    help="glob of the run manifests that declare arm x rows_path")
    ap.add_argument("--arm-registry", dest="registry", default=ARMS_REGISTRY,
                    help="the runner whose ARMS tuple declares the legal arm names")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero when any cell is missing_*")
    args = ap.parse_args(argv)

    result = audit(args.rows_dir, args.fixture, manifests=args.manifests,
                   registry=args.registry)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1, sort_keys=False)
            fh.write("\n")

    print("declared cell space: %s" % result["declared_space"]["formula"])
    print(render_table(result["cells"]))
    print()
    for line in result["accuracy"]["per_arm"].values():
        print(line)
    print(result["accuracy"]["overall"])

    missing = sum(result["states"][s] for s in MISSING_STATES)
    extraneous = result["states"].get("extraneous_cell", 0)
    if extraneous:
        print("\nEXTRANEOUS CELLS (in the rows, absent from the declaration): %d"
              % extraneous)
        for cell in result["extraneous"]:
            print("  %-11s %-18s %-12s %s  [%s, %d row(s)]" % (
                cell["kind"], cell["arm"], cell["label"], cell["reason"],
                cell["rows_file"], cell["rows"]))
        print("EXTRANEOUS: %d cell(s) the declaration does not contain"
              % extraneous, file=sys.stderr)
        return 11
    if args.strict and missing:
        print("\nSTRICT: %d missing cell(s)" % missing, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
