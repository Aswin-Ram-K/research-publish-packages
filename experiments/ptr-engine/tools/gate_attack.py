#!/usr/bin/env python3
"""GATE-OPERAND-VALIDATION — the table-driven attack on the three gates' operands.

WHY THIS FILE EXISTS
    ``V-GATE-CHAIN-3``'s closure recorded PASS while the attack script asserted six
    surviving bypasses as its pass condition (F1 ``--max-wall 1e308``, F2 a 1e-9 per-turn
    override, F3 a zero per-turn figure in the artefact, F4 ``--turns 0`` under H3, F5 a
    negative turn count, F8 a zero ledger cap). That script described holes as expected
    behaviour because its expectations were derived from the code's output.

    This attack derives every expectation from the REQUIREMENT instead:

        G1  spend never exceeds ``cap``; a non-positive or non-integer
            ``cap``/``allocation``/``allowance`` is refused before any request; a
            ``cap=0`` never reaches the runner.
        G2  a cell is admitted only when the COMPUTED projected wall is finite, positive
            and <= a finite positive ``--max-wall``; every numeric operand
            (``max_wall``, ``projected_turn_wall``, ``projected_from``, the artefact's
            value) is validated whether it arrives as a flag, a p90, or an artefact
            field.
        G3  a live run declares a hypothesis or ``smoke``; silence is a refusal (12);
            turns/reps are positive integers.

    ``inf``, ``nan``, ``1e308``, ``0``, negative values and non-numeric strings are
    refusals, not admissions.

TABLE, NOT NARRATIVE
    Every row is ``{gate, operand, via, value, expected}``. ``via`` is ``chain`` (the
    value enters through the real evaluator, exactly as a flag/artefact would) or
    ``unit`` (the value is handed to the pure validator, for operands the CLI cannot
    spell -- an arm count, a checkpoint count, a request count). A row PASSES only when
    the refusal exit code equals the requirement-derived expectation AND the spawn
    counter did not move. A refusal that still spawns is a FAIL.

    ``before`` is a RECONSTRUCTION of the pre-fix decision from the quoted original
    source lines (``cell.py`` is untracked at HEAD, so no committed pre-fix copy exists
    to re-run). ``after`` is measured, on every run.

OFFLINE: nothing here opens a socket. The only process primitive, ``cell._run``, is
replaced by a counter, so even an accidental live path cannot leave this process.
"""

from __future__ import annotations

import argparse
import contextlib
import glob
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

__all__ = ["build_rows", "run_rows", "run_chain_cases", "main"]

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)                       # experiments/ptr-engine
LONG = os.path.join(ENGINE, "longrun")
REPO = os.path.dirname(os.path.dirname(ENGINE))      # workspace root
CELL_PATH = os.path.join(LONG, "cell.py")
PROJECTION = os.path.join(ENGINE, "measure", "PROJECTION.json")
PREREG = os.path.join(ENGINE, "measure", "PREREG-ARM-RUN.json")
GATE_DOC = os.path.join(REPO, "docs", "GATE-CHAIN.md")
PINNED_BEFORE_SHA1 = "f53d7bfe68bd0c8321b637ac948ed7384b76bea1"

CLAIM = ("every gate operand is validated; no hostile numeric value is admitted; "
         "no refusal spawns a runner")

# The hostile operand alphabet, in the order the unit contract names it.
HOSTILE = [
    ("0", 0),
    ("-1", -1),
    ("-48", -48),
    ("1e-9", 1e-9),
    ("1e308", 1e308),
    ("inf", float("inf")),
    ("nan", float("nan")),
    ("'abc'", "abc"),
    ("''", ""),
    ("None", None),
]


# --------------------------------------------------------------------- plumbing
def load_cell(path=CELL_PATH):
    spec = importlib.util.spec_from_file_location("cell_under_attack", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path, doc):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return path


def fake_ledger(tmp, cap, spent=5, reserve=0, name="ledger.json"):
    """An artefact shaped like REQUEST-LEDGER.json, plus the rows it counts."""
    rows = os.path.join(tmp, "rows-%s.jsonl" % name)
    with open(rows, "w", encoding="utf-8") as fh:
        for i in range(spent):
            fh.write(json.dumps({"kind": "turn", "turn": i + 1,
                                 "prompt_tokens": 100}) + "\n")
    def sub(a, b):
        try:
            return a - b
        except TypeError:
            return None
    doc = {
        "unit": "REQUEST-LEDGER", "rule": "gate-attack fixture",
        "counting": {}, "total": {"files": 1, "rows": spent, "requests": spent,
                                  "assumed_billed": 0},
        "budget": {"cap": cap, "reserve": reserve, "headroom": sub(cap, reserve),
                   "spent": spent, "would_spend": 0, "projected": spent,
                   "remaining": sub(sub(cap, reserve), spent), "within_budget": True},
        "files": [{"file": rows, "sha256": "0" * 64, "rows": spent, "requests": spent,
                   "assumed_billed": 0, "first_ts": None, "last_ts": None}],
        "suppressed": [],
    }
    return _write_json(os.path.join(tmp, name), doc), rows


def projection_with(tmp, overrides, name="projection.json"):
    """A copy of the real PROJECTION.json with per-mode figures replaced."""
    with open(PROJECTION, encoding="utf-8") as fh:
        doc = json.load(fh)
    defaults = doc.setdefault("defaults", {})
    defaults.setdefault("projected_turn_wall_s_by_mode", {}).update(overrides)
    return _write_json(os.path.join(tmp, name), doc)


def p90_rows(tmp, wall_ms, name="p90-rows.jsonl"):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(10):
            fh.write(json.dumps({"kind": "turn", "turn": i + 1,
                                 "wall_ms": wall_ms}) + "\n")
    return path


def ns(cell, **kw):
    base = dict(arm="transcript-grow", fixture=fixture_path(), turns=48, reps=1,
                budget=1000, endpoint=None, expect_harness=None, offline=None,
                out_dir=os.path.join(tempfile.gettempdir(), "gate-attack-out"),
                thinking="off", turn_wall_cap=180.0, projected_turn_wall=None,
                fetch_followup_allowance=None, hypothesis="H2", dry_run=False,
                projected_from=None, runaway_turns=2, max_wall=3600.0,
                handoff_unit=None, no_cell_handoff=True, allow_inconsistent=False)
    base.update(kw)
    return type("Args", (object,), base)()


_FIXTURE = [None]


def fixture_path():
    if _FIXTURE[0]:
        return _FIXTURE[0]
    candidates = sorted(glob.glob(os.path.join(LONG, "tasks-v5", "runtime-v5",
                                               "*.v5.json")))
    candidates += sorted(glob.glob(os.path.join(LONG, "fixtures", "*.v5.json")))
    candidates += sorted(glob.glob(os.path.join(ENGINE, "fixtures", "*.v5.json")))
    if not candidates:
        raise SystemExit("gate_attack: no fixture (*.v5.json) found under %s" % LONG)
    _FIXTURE[0] = candidates[0]
    return _FIXTURE[0]


def exit_of(cell, verdict, default):
    if verdict.get("ok"):
        return 0
    try:
        cell._enforce(verdict, "attack", default)
    except cell.Abort as exc:
        return exc.code
    return 0


# ------------------------------------------------- requirement-derived expectations
def expected_exit(gate, operand, value):
    """The exit the REQUIREMENT demands for this operand/value pair (never the code's)."""
    if operand == "allowance" and value is None:
        return 0                      # documented default sentinel: derive it
    if operand == "projected_turn_wall" and value is None:
        return 0                      # unset flag: fall back to the artefact
    if operand == "reserve" and value == 0:
        return 0                      # zero reserve is legal
    if operand == "checkpoints":
        if isinstance(value, bool) or not isinstance(value, int):
            return 12                 # a checkpoint count is G3's own operand
        return 0 if value >= 8 else 12
    if operand == "artefact_turn_wall" and value is None:
        return 8                      # a null calibration is the projection gate's
        #                               "no calibrated figure" refusal, not a usage error
    if operand == "projected_from":
        return 8                      # a rows file that carries unusable walls is a
        #                               projection operand, not a usage error
    nonnumeric = value is None or isinstance(value, (str, bool))
    return {  # non-numeric operands are usage/artefact-shape errors: exit 2
        "G1": 2 if nonnumeric else 4,
        "G2": 2 if nonnumeric else 8,
        "G3": 2 if nonnumeric else 12,
    }[gate]


def before_decision(gate, operand, value):
    """RECONSTRUCTION of the pre-fix decision, from the quoted original source lines.

    ``cell.py`` is untracked at HEAD, so there is no committed pre-fix copy to run; this
    encodes the old truthiness idioms (``int(budget["cap"] or 0)``, ``int(args.turns or
    0)``, ``max(0, int(allowance))``, ``ok = max_wall > 0 and projected <= max_wall``,
    ``ok = checkpoints >= 8``) together with the six named bypasses. Returns
    ``"admit"``, ``"crash"`` (uncaught ValueError/OverflowError) or ``"refuse:<code>"``.
    """
    def as_int(v):
        if isinstance(v, bool):
            return 0
        if isinstance(v, float):
            if v != v or v in (float("inf"), float("-inf")):
                return "crash"
            return int(v)
        if v is None or v == "":
            return 0
        if isinstance(v, str):
            return "crash"
        return int(v)

    if gate == "G1":
        if operand == "cap":
            c = as_int(value)
            if c == "crash":
                return "crash"
            if c == 0:                          # old `cap and ...` truthiness: bypass (F8)
                return "admit"
            return "refuse:4"
        if operand in ("turns", "reps"):
            n = as_int(value)
            if n == "crash":
                return "crash"
            return "admit"                      # 0 and negatives were spent as written
        if operand == "allowance":
            n = as_int(value)
            if n == "crash":
                return "crash"
            return "admit"                      # max(0, int(...)) clamped and admitted
        if operand == "reserve":
            n = as_int(value)
            if n == "crash":
                return "crash"
            return "refuse:4" if (n >= 4320 or n < 0) else "admit"
        if operand == "arms":
            return "admit"
    if gate == "G2":
        if operand == "max_wall":
            if value is None or (isinstance(value, str)):
                return "crash"                  # float("abc") / float(None)
            if isinstance(value, float) and value != value:
                return "refuse:8"               # nan failed the finite check
            if isinstance(value, (int, float)) and value > 0:
                return "admit"                  # 1e308/inf were finite-or-positive (F1)
            return "admit"                      # 0 / negative: old ok = not(...) -> True
        if operand == "turn_wall_cap":
            if value is None or isinstance(value, str):
                return "crash"
            return "admit"                      # float(), never validated
        if operand == "projected_turn_wall":
            if value is None:
                return "admit"
            if isinstance(value, str):
                return "crash"
            if isinstance(value, float) and value != value:
                return "refuse:8"
            if isinstance(value, (int, float)) and value > 0:
                return "admit"                  # 1e-9 admitted, projection rounded to 0 (F2)
            return "refuse:8"                   # finite>0 was the only old check
        if operand == "artefact_turn_wall":
            if isinstance(value, str) or value is None:
                return "crash"                  # float(table[mode]) on a string
            return "admit"                      # never validated: 0 admitted (F3)
        if operand == "projected_from":
            if isinstance(value, str) or value is None:
                return "refuse:8"       # rows carry a wall, p90 unusable
            if isinstance(value, float) and value != value:
                return "refuse:8"
            if isinstance(value, (int, float)) and value <= 0:
                return "refuse:8"               # rows carry a wall but p90 <= 0
            return "refuse:8" if value > 86400 else "admit"
        if operand == "requests":
            n = as_int(value)
            if n == "crash":
                return "crash"
            return "admit"                      # 0/negative projected <= max_wall (F8 kin)
    if gate == "G3":
        if operand in ("turns", "reps"):
            n = as_int(value)
            if n == "crash":
                return "crash"
            return "admit"                      # H3 ignored n entirely (F4/F5)
        if operand == "checkpoints":
            if isinstance(value, bool) or not isinstance(value, int):
                return "crash"
            return "admit" if value >= 8 else "refuse:12"
        if operand == "hypothesis":
            if value in (None, "", "none", "None"):
                return "admit"                  # H3 branch ran on silence
            return "admit" if value in ("H1", "H2", "H3") else "refuse:12"
    return "admit"


# ------------------------------------------------------------------------- rows
def build_rows(cell, tmp):
    rows = []

    def add(gate, operand, via, value, expected=None, note="", setup=None,
            kwargs=None, unit=None):
        rows.append({"gate": gate, "operand": operand, "via": via,
                     "label": repr(value), "value": value,
                     "expected": (expected if expected is not None
                                  else expected_exit(gate, operand, value)),
                     "note": note, "setup": setup, "kwargs": kwargs or {},
                     "unit": unit})

    ledger_ok, _ = fake_ledger(tmp, cap=4320, spent=5, name="ledger-ok.json")
    proj_ok = projection_with(tmp, {"off": 60.0}, name="projection-ok.json")
    proj_zero = projection_with(tmp, {"off": 0}, name="projection-zero.json")

    def use(ledger=ledger_ok, projection=proj_ok):
        def apply(module):
            module.LEDGER_ARTEFACT = ledger
            module.PROJECTION_ARTEFACT = projection
            module.PREREG_ARTEFACT = PREREG
        return apply

    # ---- G1 -----------------------------------------------------------------
    for label, value in HOSTILE:
        add("G1", "turns", "chain", value, kwargs={"turns": value}, setup=use())
        add("G1", "reps", "chain", value, kwargs={"reps": value}, setup=use())
        add("G1", "cap", "chain", value,
            setup=(lambda m, v=value, t=tmp: use(
                ledger=fake_ledger(t, cap=v, spent=5, name="ledger-cap-%s.json"
                                   % abs(hash(label)))[0])(m)))
        add("G1", "reserve", "chain", value,
            setup=(lambda m, v=value, t=tmp: use(
                ledger=fake_ledger(t, cap=4320, spent=5, reserve=v,
                                   name="ledger-res-%s.json"
                                   % abs(hash(label)))[0])(m)))
        add("G1", "allowance", "chain", value,
            kwargs={"fetch_followup_allowance": value}, setup=use(), expected=(
                0 if value is None else expected_exit("G1", "allowance", value)))
        add("G1", "arms", "unit", value, setup=use(), unit="g1")
    # ---- G2 -----------------------------------------------------------------
    for label, value in HOSTILE:
        add("G2", "max_wall", "chain", value, kwargs={"max_wall": value}, setup=use())
        add("G2", "turn_wall_cap", "chain", value, kwargs={"turn_wall_cap": value},
            setup=use())
        add("G2", "projected_turn_wall", "chain", value,
            kwargs={"projected_turn_wall": value}, setup=use(),
            expected=(0 if value is None else expected_exit("G2", "projected_turn_wall",
                                                            value)))
        add("G2", "artefact_turn_wall", "chain", value, setup=use(
            projection=projection_with(tmp, {"off": value},
                                       name="projection-art-%s.json" % abs(hash(label)))))
        add("G2", "projected_from", "chain", value, setup=use(),
            kwargs={"projected_from": p90_rows(tmp, value,
                                               name="p90-%s.jsonl" % abs(hash(label)))})
        add("G2", "requests", "unit", value, setup=use(), unit="g2")
    # ---- G3 -----------------------------------------------------------------
    twelve = {"checkpoints": [{"id": "C%d" % (i + 1)} for i in range(12)]}
    for label, value in HOSTILE:
        add("G3", "turns", "chain", value, kwargs={"turns": value, "hypothesis": "H3"},
            setup=use(), note="fixture carries 12 checkpoints")
        add("G3", "reps", "chain", value, kwargs={"reps": value, "hypothesis": "H3"},
            setup=use(), note="fixture carries 12 checkpoints")
        add("G3", "checkpoints", "unit", value, setup=use(), unit="g3")
        add("G3", "turns_h3", "unit", value, setup=use(), unit="g3",
            note="H3 checkpoint branch with n=%r" % (value,))
    for hyp in ("", "NONE", "H9", "H2"):
        add("G3", "hypothesis", "chain", hyp, kwargs={"hypothesis": hyp}, setup=use(),
            expected=(0 if hyp == "H2" else 12),
            note=("silence/unknown is a refusal (12), never a silent default"
                  if hyp != "H2" else "H2 at n=48 is legal"))
    # ---- legal rows: only values the requirement calls legal may assert 0 --------
    add("G1", "turns", "chain", 48, expected=0, kwargs={"turns": 48}, setup=use(),
        note="48 turns x 1 arm + 68/801 allowance fits cap 4320")
    add("G1", "cap", "chain", 4320, expected=0, setup=use(),
        note="cap equals the cell's exact cost headroom")
    add("G1", "allowance", "chain", 96, expected=0,
        kwargs={"fetch_followup_allowance": 96}, setup=use())
    add("G2", "max_wall", "chain", 3600.0, expected=0, kwargs={"max_wall": 3600.0},
        setup=use(), note="48 x 60 s = 2880 s <= 3600 s")
    add("G2", "max_wall", "chain", 2880.0, expected=0, kwargs={"max_wall": 2880.0},
        setup=use(), note="boundary: projected == max-wall is admitted")
    add("G2", "turn_wall_cap", "chain", 180.0, expected=0,
        kwargs={"turn_wall_cap": 180.0}, setup=use())
    add("G2", "projected_turn_wall", "chain", 60.0, expected=0,
        kwargs={"projected_turn_wall": 60.0}, setup=use())
    add("G3", "hypothesis", "chain", "H1", expected=12, setup=use(),
        kwargs={"hypothesis": "H1", "turns": 48}, note="48 < 60: still refused (12)")
    add("G3", "hypothesis", "chain", "H1", expected=0, setup=use(),
        kwargs={"hypothesis": "H1", "turns": 60}, note="60 >= 60: legal")
    add("G3", "hypothesis", "chain", "H2", expected=0, setup=use(),
        kwargs={"hypothesis": "H2", "turns": 1})
    add("G3", "hypothesis", "chain", "H3", expected=0, setup=use(),
        kwargs={"hypothesis": "H3", "turns": 1}, note="12 checkpoints >= 8")
    # ---- permissive-sibling combinations ----------------------------------------
    add("G1", "turns", "chain", 0, expected=4,
        kwargs={"turns": 0, "fetch_followup_allowance": 96}, setup=use(),
        note="a legal allowance next to a hostile turn count")
    add("G1", "cap", "chain", 0, expected=4, kwargs={"turns": 48},
        setup=use(ledger=fake_ledger(tmp, cap=0, spent=0, name="ledger-cap0.json")[0]),
        note="a legal 48-turn shape next to cap=0")
    add("G2", "projected_turn_wall", "chain", 1e308, expected=8,
        kwargs={"max_wall": 3600.0, "turn_wall_cap": 180.0,
                "projected_turn_wall": 1e308}, setup=use(),
        note="legal ceiling and abort cap next to a hostile override")
    add("G2", "turn_wall_cap", "chain", 0, expected=8,
        kwargs={"max_wall": 3600.0, "turn_wall_cap": 0}, setup=use(),
        note="legal ceiling next to a zero abort cap")
    add("G3", "hypothesis", "chain", "", expected=12,
        kwargs={"turns": 48, "reps": 1, "hypothesis": ""}, setup=use(),
        note="legal n next to declared silence")
    add("G3", "turns", "chain", 0, expected=12,
        kwargs={"turns": 0, "hypothesis": "H2"}, setup=use(),
        note="legal hypothesis next to a hostile turn count")
    return rows


# -------------------------------------------------------------------- execution
def run_rows(cell, rows, tmp, spawn):
    out = []
    for row in rows:
        if callable(row.get("setup")):
            row["setup"](cell)
        before_spawns = spawn["n"]
        actual, detail = None, ""
        try:
            if row["via"] == "unit":
                actual, detail = run_unit(cell, row)
            else:
                actual, detail = run_chain_row(cell, row)
        except cell.Abort as exc:
            actual, detail = exc.code, str(exc)
        except (ValueError, TypeError, OverflowError) as exc:
            actual, detail = 1, "%s: %s" % (type(exc).__name__, exc)
        except AssertionError as exc:
            actual, detail = 99, "SPAWN: %s" % (exc,)
        spawned = spawn["n"] - before_spawns
        out.append(dict(row, actual=actual, detail=detail[:400], spawned=spawned,
                        ok=(actual == row["expected"] and spawned == 0),
                        before=before_decision(row["gate"], row["operand"],
                                               row["value"])))
    rows[:] = out
    return out


def run_chain_row(cell, row):
    args = ns(cell, **row["kwargs"])
    fixture = {"checkpoints": [{"id": "C%d" % (i + 1)} for i in range(12)]}
    gate = row["gate"]
    if gate == "G1":
        verdict = cell.eval_gate_ledger(args)
        return exit_of(cell, verdict, 4), cell._gate_message(verdict) if not verdict["ok"] else ""
    if gate == "G2":
        try:
            verdict = cell.eval_gate_projection(args, {})
        except cell.Abort as exc:
            return exc.code, str(exc)
        return (exit_of(cell, verdict, 8),
                cell._gate_message(verdict) if not verdict.get("ok") else "")
    if gate == "G3":
        verdict = cell.eval_gate_prereg(args, fixture)
        return (exit_of(cell, verdict, 12),
                cell._gate_message(verdict) if not verdict.get("ok") else "")
    raise AssertionError(gate)


def run_unit(cell, row):
    gate, value = row["gate"], row["value"]
    if gate == "G1":
        ok, facts = cell.validate_g1(48, 1, value, None, 4320, 0)
    elif gate == "G2":
        ok, facts = cell.validate_g2(3600.0, 180.0, 60.0, value)
    else:
        known = json.load(open(PREREG, encoding="utf-8")).get("hypotheses") or {}
        if row["operand"] == "turns_h3":
            ok, facts = cell.validate_g3("H3", value, 1, 12, known)
        elif row["operand"] == "turns":
            ok, facts = cell.validate_g3("H3", value, 1, 12, known)
        else:
            ok, facts = cell.validate_g3("H3", 48, 1, value, known)
    if ok:
        return 0, ""
    bad = (facts.get("refusals") or [None])[0]
    if bad:
        return bad.get("code", 1), json.dumps(bad)[:300]
    # a threshold refusal (n < min_n, checkpoints < 8) carries the gate's own code
    return {"G1": 4, "G2": 8, "G3": 12}[gate], json.dumps(facts)[:300]


# --------------------------------------------------------------- the F cases, e2e
class Reached(Exception):
    """stage_run / grading was reached: a refusal that spawns is a FAIL."""


def run_chain_cases(cell, tmp):
    """The six named VERDICT-DISPUTE bypasses, end-to-end through cell.main()."""
    ledger, _ = fake_ledger(tmp, cap=4320, spent=5, name="ledger-e2e.json")
    proj_zero = projection_with(tmp, {"off": 0, "absent": 0},
                                name="projection-e2e-zero.json")
    out_dir = os.path.join(tmp, "e2e-out")
    os.makedirs(out_dir, exist_ok=True)
    fixture = fixture_path()

    orig = {name: getattr(cell, name) for name in
            ("LEDGER_ARTEFACT", "PROJECTION_ARTEFACT", "PREREG_ARTEFACT", "RUNNER",
             "_run", "stage_run", "stage_grade", "stage_analyse", "stage_record",
             "stage_consistency", "write_gate_manifest")}

    def base_argv(extra):
        return (["--arm", "transcript-grow", "--fixture", fixture, "--turns", "48",
                 "--reps", "1", "--budget", "1000", "--out-dir", out_dir,
                 "--no-cell-handoff"] + list(extra))

    cases = [
        ("F1", "B2_max_wall_1e308_allows", ["--max-wall", "1e308",
                                            "--hypothesis", "H2"], 8),
        ("F2", "G_tiny_override_allows", ["--max-wall", "1", "--projected-turn-wall",
                                          "1e-9", "--hypothesis", "H2"], 8),
        ("F3", "H_artefact_zero_allows", ["--max-wall", "3600",
                                          "--hypothesis", "H2"], 8),
        ("F4", "D_turns0_H3_runs_full", ["--turns", "0", "--hypothesis", "H3"], 4),
        ("F5", "D2_turns_neg_runs_full", ["--turns", "-1", "--hypothesis", "H3"], 4),
        ("F8", "I2b_cap_zero_passed_to_runner", ["--turn-wall-cap", "0",
                                                 "--hypothesis", "H2"], 8),
    ]
    records = []
    for cid, name, extra, want in cases:
        spawn = {"live": 0, "dry": 0}

        # Mirrors cell._run's CURRENT signature (longrun/cell.py:200):
        #   _run(argv, capture=True, label="", purpose="other", phase="")
        # Every keyword cell.py passes at its call sites must be accepted or the
        # attack dies with a TypeError instead of running the case:
        #   363 preflight_self_check / 1629 grade_v5 / 1655 analyse (purpose, phase, label).
        # DELIBERATELY IGNORED: `purpose` and `phase` are accepted and NOT read here.
        # This double only counts dry vs live spawns; it does not reproduce the real
        # SPAWNS classification. It therefore proves a refusal spawned nothing -- it
        # does NOT prove the refusal classifier ran, and must never be read as that.
        def counted(argv, capture=True, label="", purpose="other", phase=""):
            if "--dry-run" in argv:
                spawn["dry"] += 1
                return 0, "would_send_total=48\n", ""
            spawn["live"] += 1
            return 0, "", ""

        def reached(*a, **k):
            spawn["live"] += 1
            raise Reached("stage_run reached")

        cell.LEDGER_ARTEFACT = ledger
        cell.PROJECTION_ARTEFACT = (proj_zero if cid == "F3" else
                                    projection_with(tmp, {"off": 60.0},
                                                    name="projection-e2e.json"))
        cell.PREREG_ARTEFACT = PREREG
        cell.RUNNER = os.path.join(LONG, "run_longrun.py")
        cell._run = counted
        cell.stage_run = reached
        for name_ in ("stage_grade", "stage_analyse", "stage_record"):
            setattr(cell, name_, lambda *a, **k: ({}, {}))
        cell.stage_consistency = lambda *a, **k: ({}, {})
        cell.write_gate_manifest = lambda *a, **k: None
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = cell.main(base_argv(extra))
        except Reached:
            rc = 99
        except cell.Abort as exc:
            rc = exc.code
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
        log = buf.getvalue()
        refusal = next((ln for ln in log.splitlines() if "REFUSED" in ln), "")
        records.append({"case": cid, "bypass": name, "argv": extra, "expected": want,
                        "actual": rc, "live_spawns": spawn["live"],
                        "dry_run_probes": spawn["dry"],
                        "ok": rc == want and spawn["live"] == 0,
                        "refusal": refusal})
    for name_, value in orig.items():
        setattr(cell, name_, value)
    return records


# -------------------------------------------------------------------- exit table
def exit_table_check():
    sys.path.insert(0, LONG)
    try:
        import exit_codes
    finally:
        sys.path.pop(0)
    declared = sorted(int(k) for k in exit_codes.EXIT_TABLE)
    doc = ""
    if os.path.exists(GATE_DOC):
        with open(GATE_DOC, encoding="utf-8") as fh:
            doc = fh.read()
    documented = []
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.count("|") >= 3:
            cell = stripped.split("|")[1].strip()
            if cell.isdigit():
                documented.append(int(cell))
    documented = sorted(set(documented))
    gate_codes = sorted(exit_codes.GATE_CHAIN_CODES) if hasattr(
        exit_codes, "GATE_CHAIN_CODES") else [2, 3, 4, 8, 12]
    return {"declared": declared, "documented": documented,
            "gate_codes": gate_codes,
            "gate_codes_agree": all(c in declared and c in documented
                                    for c in gate_codes),
            "declared_not_documented": [c for c in declared if c not in documented],
            "documented_not_declared": [c for c in documented if c not in declared],
            "note": ("1 = internal-error is declared in exit_codes.py and is NOT part "
                     "of the gate chain; docs/GATE-CHAIN.md does not list it. No gate "
                     "code disagrees and nothing was renumbered."),
            "runner_codes": sorted(exit_codes.RUNNER_CODES)}


# ------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cell", default=CELL_PATH)
    ap.add_argument("--json", default=None, help="write the measured matrix here")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    cell = load_cell(args.cell)
    tmp = tempfile.mkdtemp(prefix="gate-attack-")
    spawn = {"n": 0}

    def counted_run(*a, **k):
        spawn["n"] += 1
        return 0, "", ""

    cell._run = counted_run
    rows = run_rows(cell, build_rows(cell, tmp), tmp, spawn)
    spawn_after_rows = spawn["n"]

    # every row is a refusal or a legal admission; a legal row may legitimately reach
    # no spawn either, so zero spawns is asserted on every row.
    f_cases = run_chain_cases(cell, tmp)

    failures = [r for r in rows if not r["ok"]]
    f_fail = [c for c in f_cases if not c["ok"]]

    per_gate = {}
    for gate in ("G1", "G2", "G3"):
        sub = [r for r in rows if r["gate"] == gate]
        hostile = [r for r in sub if r["expected"] != 0]
        per_gate[gate] = {
            "rows": len(sub),
            "hostile_rows": len(hostile),
            "hostile_admitted_before": sum(1 for r in hostile
                                           if str(r["before"]).startswith("admit")),
            "hostile_admitted_after": sum(1 for r in hostile if r["actual"] == 0),
            "hostile_crashed_before": sum(1 for r in hostile
                                          if r["before"] == "crash"),
            "rows_failing": sum(1 for r in sub if not r["ok"]),
        }

    result = {
        "unit": "GATE-OPERAND-VALIDATION",
        "claim": CLAIM,
        "offline": True,
        "inference_requests": 0,
        "cell_path": os.path.relpath(args.cell, REPO),
        "cell_sha256": cell_sha256(args.cell),
        "pinned_before_sha1": PINNED_BEFORE_SHA1,
        "requirement": {
            "G1": "spend never exceeds cap; non-positive or non-integer cap/allocation/"
                  "allowance refused before any request; cap=0 never reaches the runner",
            "G2": "admit only when the COMPUTED projected wall is finite, positive and "
                  "<= a finite positive --max-wall; validate every numeric operand "
                  "whether it arrives as a flag, a p90 or an artefact field",
            "G3": "a live run declares a hypothesis or smoke; silence is a refusal (12); "
                  "turns/reps are positive integers",
        },
        "hostile_alphabet": [label for label, _ in HOSTILE],
        "matrix": [{k: r[k] for k in ("gate", "operand", "via", "label", "expected",
                                      "actual", "spawned", "ok", "before", "note",
                                      "detail")} for r in rows],
        "per_gate": per_gate,
        "f_cases": f_cases,
        "spawns": {"evaluator_rows": spawn_after_rows,
                   "refusal_rows_live": sum(c["live_spawns"] for c in f_cases),
                   "note": "cell._run is the only process primitive; all rows and all "
                           "six F cases ran with it replaced by a counter"},
        "exit_table": exit_table_check(),
        "red_green": {
            "source": "orchestration/handoffs/VERDICT-DISPUTE.json (overall: fail); the "
                      "pre-fix decisions are reconstructed from the quoted original "
                      "lines because experiments/ptr-engine/longrun/cell.py is untracked "
                      "at HEAD and has no committed pre-fix copy",
            "F1": "before: --max-wall 1e308 admitted and the runner ran; after: exit 8",
            "F2": "before: --projected-turn-wall 1e-9 admitted (projection rounded to 0); "
                  "after: exit 8",
            "F3": "before: artefact per-mode figure 0 admitted (never validated); after: "
                  "exit 8",
            "F4": "before: --turns 0 under H3 passed G3 (it only counted checkpoints); "
                  "after: G1 exit 4 through the chain, G3 exit 12 directly",
            "F5": "before: --turns -1 under H3 ran in full; after: G1 exit 4 through the "
                  "chain, G3 exit 12 directly",
            "F8": "before: --turn-wall-cap 0 passed to the runner as an abort threshold; "
                  "after: exit 8",
        },
        "failures": [{"gate": r["gate"], "operand": r["operand"], "value": r["label"],
                      "expected": r["expected"], "actual": r["actual"],
                      "detail": r["detail"]} for r in failures]
        + [{"case": c["case"], "expected": c["expected"], "actual": c["actual"],
            "live_spawns": c["live_spawns"]} for c in f_fail],
        "ok": not failures and not f_fail and result_exit_agrees(),
    }

    if not args.quiet:
        print("gate-attack cell=%s sha256=%s" % (result["cell_path"],
                                                 result["cell_sha256"][:16]))
        for gate in ("G1", "G2", "G3"):
            g = per_gate[gate]
            print("%s rows=%d hostile=%d admitted_before=%d admitted_after=%d failing=%d"
                  % (gate, g["rows"], g["hostile_rows"], g["hostile_admitted_before"],
                     g["hostile_admitted_after"], g["rows_failing"]))
        print("F cases: %d/%d refuse with 0 live spawns"
              % (sum(1 for c in f_cases if c["ok"]), len(f_cases)))
        for c in f_cases:
            print("  %-3s exit %-3s spawns=%d expected=%d %s"
                  % (c["case"], c["actual"], c["live_spawns"], c["expected"],
                     "OK" if c["ok"] else "FAIL"))
        for row in failures:
            print("FAIL %s/%s=%s expected %s got %s :: %s"
                  % (row["gate"], row["operand"], row["label"], row["expected"],
                     row["actual"], row["detail"][:160]))
        for c in f_fail:
            print("FAIL %s expected %s got %s spawns=%d"
                  % (c["case"], c["expected"], c["actual"], c["live_spawns"]))
        print("exit table: %s" % json.dumps(result["exit_table"]))
        print("RESULT: %s" % ("PASS" if result["ok"] else "FAIL"))

    if args.json:
        _write_json(args.json, result)
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if result["ok"] else 1


def result_exit_agrees():
    return exit_table_check()["gate_codes_agree"]


def cell_sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    sys.exit(main())
