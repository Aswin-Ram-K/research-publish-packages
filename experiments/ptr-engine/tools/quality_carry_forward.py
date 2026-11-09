#!/usr/bin/env python3
"""QUALITY-CARRY-FORWARD -- recompute era A's answer-production figures from their own artefacts.

Additive unit: this tool reads `measure/MODAL-ANSWER.json`, `measure/QUALITY-ERAS.json`,
`measure/GRID-SHAPE.json` and the rows/fixture files those name, recomputes every figure the
carry-forward record publishes, and writes `measure/QUALITY-CARRY-FORWARD.json`.

Offline: no request, no socket. Every figure carries `source_path` + `source_sha256`.

Usage:
  python3 experiments/ptr-engine/tools/quality_carry_forward.py --write
  python3 experiments/ptr-engine/tools/quality_carry_forward.py --check [--record PATH]

--check exits 1 if any recorded figure stops matching a fresh recomputation (drifted source
digest, changed count, moved citation line, or a statements block that lost a sentence or its
attribution) and 0 when everything matches.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MEASURE = ROOT / "experiments" / "ptr-engine" / "measure"
DEFAULT_RECORD = MEASURE / "QUALITY-CARRY-FORWARD.json"

MODAL = MEASURE / "MODAL-ANSWER.json"
ERAS = MEASURE / "QUALITY-ERAS.json"
SHAPE = MEASURE / "GRID-SHAPE.json"
ROWS_C = MEASURE / "rows-longrun-c-2026-10-26.jsonl"
FIXTURE = ROOT / "experiments" / "ptr-engine" / "longrun" / "tasks-v6" / "LR-01.v8.json"

STATEMENT_1 = (
    "era A's checkpoint answers are answer-production measurements under an instruction to read "
    "sources the arm could not read (46 of 48 turns in v5/v6/v7/v8 invite a read; `@knowledge:` "
    "0/48, literal `read_file` 0/48)"
)
STATEMENT_2 = (
    "under the modal-answer reading every arm scores 0/12; the three observed passes are one-off, "
    "one-arm, and none is the arm's most frequent answer."
)

# path, needle that must occur on exactly one line, why this page must now cite the record.
CITATIONS = [
    {
        "path": "docs/OPERATOR-BRIEF.md",
        "needle": "| **H3** quality | lose no more than 2 of 12 checkpoints",
        "figure_ids": ["counterfactual_modal_pass_per_arm", "none_id_counterfactual_pass"],
        "why": "the H3 contract quotes the 12-checkpoint denominator without saying what the answers were",
    },
    {
        "path": "docs/OPERATOR-BRIEF.md",
        "needle": "Pointer-stable \u2265 8 of 12 decidable and losing > 2 checkpoints",
        "figure_ids": ["counterfactual_modal_pass_per_arm"],
        "why": "the H3 veto is stated on `x/12` without the era-A reading",
    },
    {
        "path": "orchestration/STATUS.md",
        "needle": "**H3 quality \u2014 not evaluable at this n.**",
        "figure_ids": ["counterfactual_modal_pass_per_arm", "distinct_answers"],
        "why": "the current-programme section says H3 measures answer production but not that every arm is 0/12 under the modal reading",
    },
    {
        "path": "orchestration/STATUS.md",
        "needle": "Spend and quality figures live in",
        "figure_ids": ["era_a_grade_v5_pass"],
        "why": "the pointer to quality figures must also point at the carry-forward record",
    },
    {
        "path": "docs/QUALITY-ERAS.md",
        "needle": "that grid reads **3/27 = 11.1 %** as recorded and **3/25 = 12.0 %**",
        "figure_ids": ["era_a_grade_v5_pass"],
        "why": "the epoch table is the QUALITY record this carry-forward is appended to",
    },
    {
        "path": "docs/QUALITY-ERAS.md",
        "needle": "| as recorded on disk | **3/27** |",
        "figure_ids": ["era_a_grade_v5_pass"],
        "why": "the rows-table denominator is quoted without the 0/12 counterfactual",
    },
    {
        "path": "docs/QUALITY-ERAS.md",
        "needle": "| all pairs under the current grader | **3/25** |",
        "figure_ids": ["era_a_grade_v5_pass"],
        "why": "same table, current-grader line",
    },
    {
        "path": "docs/QUALITY-ERAS.md",
        "needle": "The `grade_v5.py` grid, if quoted at all, is **3/25 = 12.0 %**",
        "figure_ids": ["era_a_grade_v5_pass", "counterfactual_modal_pass_per_arm"],
        "why": "the sentence that tells the next reader what the grid is worth must carry the modal reading",
    },
    {
        "path": "docs/GRID-SHAPE.md",
        "needle": "**Counts.** 46/48 turns invite a read.",
        "figure_ids": ["turns_with_path_read_invitation", "turns_with_at_knowledge"],
        "why": "the invitation count is the premise of the carry-forward statement",
    },
    {
        "path": "docs/GRID-SHAPE.md",
        "needle": "on a tool-inviting turn**; 0/12 sit on a turn that does not.",
        "figure_ids": ["counterfactual_modal_pass_per_arm"],
        "why": "the grid-shape page states checkpoint turns invite a read; it must point at what the answers then scored",
    },
]

MISSING_PAGES = [
    {
        "path": "docs/OPERATOR-BRIEF-4.md",
        "status": "absent",
        "note": "no such file in this tree at recompute time; the operator contract lives at docs/OPERATOR-BRIEF.md:18 and :85, which are listed in needs_citation",
    },
    {
        "path": "docs/OPERATOR-BRIEF-5.md",
        "status": "absent",
        "note": "no such file in this tree at recompute time; same substitute as OPERATOR-BRIEF-4.md",
    },
]

WHAT_THIS_DOES_NOT_SAY = [
    "It does not say era A's arms are equally good. It says the instrument could not separate them on this measure.",
    "It does not license differencing era B against era A.",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def recompute() -> dict:
    modal = load(MODAL)
    eras = load(ERAS)
    shape = load(SHAPE)
    fixture = load(FIXTURE)
    rows = [json.loads(line) for line in ROWS_C.read_text(encoding="utf-8").splitlines() if line.strip()]

    drift: list[str] = []
    figures: list[dict] = []

    def add(fid, label, value, denominator, source_path, method, **extra):
        figure = {
            "id": fid,
            "label": label,
            "value": value,
            "denominator": denominator,
            "source_path": rel(source_path),
            "source_sha256": sha256(source_path),
            "method": method,
        }
        figure.update(extra)
        figures.append(figure)

    # ---- (a) counterfactual modal pass count -------------------------------------------
    none_ids = [c["id"] for c in modal["checkpoints"] if c["kind"] == "NONE"]
    cf_grades = cf_pass = cf_cells = groups = 0
    arms_with_zero = 0
    max_arm_pass = 0
    none_cf_pass = 0
    for grid, gd in modal["grids"].items():
        for arm, ad in gd["arms"].items():
            groups += 1
            grades = ad.get("counterfactual_grades") or {}
            totals = {"pass": 0, "fail": 0, "text": 0, "undecidable": 0}
            for cid, graded in grades.items():
                verdict = graded.get("verdict")
                totals[verdict] = totals.get(verdict, 0) + 1
                cf_cells += 1
                cf_grades += 1
                if verdict == "pass":
                    cf_pass += 1
                    if cid in none_ids:
                        none_cf_pass += 1
            arm_pass = totals["pass"]
            max_arm_pass = max(max_arm_pass, arm_pass)
            if arm_pass == 0 and len(grades) == 12:
                arms_with_zero += 1
            if len(grades) != 12:
                drift.append(f"{grid}/{arm}: {len(grades)} counterfactual grades, expected 12")
            if totals != ad.get("counterfactual_totals"):
                drift.append(
                    f"{grid}/{arm}: recomputed counterfactual totals {totals} != recorded {ad.get('counterfactual_totals')}"
                )

    add(
        "counterfactual_modal_pass_per_arm",
        "counterfactual (modal-answer) checkpoint passes in the worst arm",
        max_arm_pass,
        12,
        MODAL,
        "every arm's modal string graded at each of the 12 declared checkpoint ids; value is the largest per-arm pass count",
        arms_checked=groups,
        arms_scoring_zero_of_twelve=arms_with_zero,
        checkpoint_grades=cf_cells,
    )
    add(
        "counterfactual_modal_pass_total",
        "counterfactual (modal-answer) checkpoint passes over every era-A grid/arm",
        cf_pass,
        cf_cells,
        MODAL,
        "sum of counterfactual_grades verdict=='pass' over all 29 grid/arm groups",
    )
    add(
        "none_id_counterfactual_pass",
        "counterfactual passes on the three NONE-kinded checkpoint ids",
        none_cf_pass,
        len(none_ids),
        MODAL,
        "checkpoint kinds read from MODAL-ANSWER.json checkpoints[]; NONE ids are " + ", ".join(none_ids),
        none_ids=none_ids,
    )

    # ---- (b) observed passes and whether any is modal ----------------------------------
    obs_passes = []
    obs_cells = 0
    none_obs_pass = 0
    for grid, gd in modal["grids"].items():
        for arm, ad in gd["arms"].items():
            for cid, observed in (ad.get("observed") or {}).items():
                obs_cells += 1
                if observed.get("verdict") == "pass":
                    obs_passes.append(
                        {
                            "arm": arm,
                            "file": gd.get("file", grid),
                            "id": cid,
                            "reason": observed.get("reason"),
                            "is_modal": bool(observed.get("is_modal")),
                        }
                    )
                    if cid in none_ids:
                        none_obs_pass += 1
    modal_obs = sum(1 for p in obs_passes if p["is_modal"])
    recorded_passes = [
        {"arm": p["arm"], "file": p["file"], "id": p["id"], "reason": p["reason"]}
        for p in modal["tables"]["observed_passes"]
    ]
    recomputed_passes = [{k: p[k] for k in ("arm", "file", "id", "reason")} for p in obs_passes]
    if sorted(map(json.dumps, recorded_passes)) != sorted(map(json.dumps, recomputed_passes)):
        drift.append("observed pass list does not match tables.observed_passes")
    if modal_obs != 0:
        drift.append(f"{modal_obs} observed passes are modal; the recorded claim is none is")

    add(
        "observed_pass_total",
        "observed checkpoint passes, one per arm where a turn row exists",
        len(obs_passes),
        groups,
        MODAL,
        "count of observed[*].verdict=='pass' over every grid/arm group",
        passes=recomputed_passes,
    )
    add(
        "observed_passes_that_are_modal",
        "observed passes that are the arm's own most frequent answer",
        modal_obs,
        len(obs_passes),
        MODAL,
        "observed[*].is_modal over the observed passes",
    )
    add(
        "none_id_observed_pass",
        "observed passes on the three NONE-kinded checkpoint ids",
        none_obs_pass,
        len(none_ids),
        MODAL,
        "observed[*].verdict=='pass' restricted to the NONE ids; distinct from the counterfactual NONE figure",
    )

    # ---- (c) distinct answers per arm --------------------------------------------------
    by_arm: dict[str, list[str]] = collections.defaultdict(list)
    for row in rows:
        if row.get("kind") not in (None, "turn"):
            continue
        content = row.get("content")
        if content is None:
            continue
        by_arm[row["arm"]].append(normalise(content))
    for arm in ("pointer-stable", "lease-reopen", "transcript-grow", "transcript-compact"):
        texts = by_arm.get(arm, [])
        distinct = len(set(texts))
        recorded = modal["grids"][ROWS_C.name]["arms"][arm]["distinct_normalised"]
        if distinct != recorded:
            drift.append(f"{arm}: recomputed distinct {distinct} != MODAL-ANSWER {recorded}")
        add(
            f"distinct_answers.{arm}",
            f"distinct normalised answers, {arm}",
            distinct,
            len(texts),
            ROWS_C,
            "kind in (absent,'turn'), content stripped, whitespace collapsed, casefolded; distinct count over 48 turns",
        )
    add(
        "distinct_answers",
        "distinct normalised answers across the four arms of the row grid",
        "/".join(str(len(set(by_arm.get(a, [])))) for a in ("pointer-stable", "lease-reopen", "transcript-grow", "transcript-compact")),
        48,
        ROWS_C,
        "same normalisation, one entry per arm, order pointer-stable/lease-reopen/transcript-grow/transcript-compact",
    )

    # ---- (d) read invitation, recomputed from the fixture itself -----------------------
    turns = fixture["turns"]
    inviting = sum(1 for t in turns if re.search(r"[A-Za-z0-9_/]+\.py", t.get("question", "")))
    at_knowledge = sum(1 for t in turns if "@knowledge:" in t.get("question", ""))
    literal_read = sum(1 for t in turns if "read_file" in t.get("question", ""))
    recorded = shape["fixture"]
    for key, value in (
        ("turns", len(turns)),
        ("turns_with_path_read_invitation", inviting),
        ("turns_with_at_knowledge", at_knowledge),
        ("turns_with_literal_read_file", literal_read),
    ):
        if recorded.get(key) != value:
            drift.append(f"GRID-SHAPE fixture.{key}={recorded.get(key)} but recomputed {value}")
    add(
        "turns_with_path_read_invitation",
        "turns whose question names a .py path (a read invitation)",
        inviting,
        len(turns),
        FIXTURE,
        "regex [A-Za-z0-9_/]+\\.py over each turn's question; 46/48 in v5/v6/v7/v8 per GRID-SHAPE.json invitation_era",
        turns_without=[t["turn"] for t in turns if not re.search(r"[A-Za-z0-9_/]+\.py", t.get("question", ""))],
    )
    add(
        "turns_with_at_knowledge",
        "turns whose question names an @knowledge: ref",
        at_knowledge,
        len(turns),
        FIXTURE,
        "literal '@knowledge:' substring over each turn's question",
    )
    add(
        "turns_with_literal_read_file",
        "turns whose question names read_file",
        literal_read,
        len(turns),
        FIXTURE,
        "literal 'read_file' substring over each turn's question",
    )

    # ---- (e) the QUALITY record this is appended to ------------------------------------
    pairs = eras["pairs"]
    cur_pass = sum(p["current_grader"]["passed"] for p in pairs)
    cur_dec = sum(p["current_grader"]["decidable"] for p in pairs)
    if (cur_pass, cur_dec) != (eras["headline"]["current_grader"]["passed"], eras["headline"]["current_grader"]["decidable"]):
        drift.append("QUALITY-ERAS pairs do not sum to the published current-grader headline")
    add(
        "era_a_grade_v5_pass",
        "era-A grade_v5 checkpoint grid, current grader",
        cur_pass,
        cur_dec,
        ERAS,
        "sum over QUALITY-ERAS.json pairs[*].current_grader (passed, decidable)",
        pct=round(100.0 * cur_pass / cur_dec, 1) if cur_dec else None,
    )

    # ---- statements, citations ---------------------------------------------------------
    modal_sha = sha256(MODAL)
    statements = [
        {
            "id": "statement-1",
            "text": STATEMENT_1,
            "attribution": {
                "unit": "MODAL-ANSWER-ACCURACY",
                "path": rel(MODAL),
                "sha256": modal_sha,
                "figure_ids": [
                    "turns_with_path_read_invitation",
                    "turns_with_at_knowledge",
                    "turns_with_literal_read_file",
                ],
                "note": "quoted verbatim from the MODAL-ANSWER-ACCURACY handoff hint; figures re-derived here from the fixture",
            },
        },
        {
            "id": "statement-2",
            "text": STATEMENT_2,
            "attribution": {
                "unit": "MODAL-ANSWER-ACCURACY",
                "path": rel(MODAL),
                "sha256": modal_sha,
                "figure_ids": [
                    "counterfactual_modal_pass_per_arm",
                    "observed_pass_total",
                    "observed_passes_that_are_modal",
                ],
                "note": "quoted verbatim from the MODAL-ANSWER-ACCURACY handoff hint; 0/12 and the three one-off passes re-derived from MODAL-ANSWER.json",
            },
        },
    ]

    citations = []
    for cite in CITATIONS:
        path = ROOT / cite["path"]
        lines = path.read_text(encoding="utf-8").splitlines()
        hits = [i + 1 for i, line in enumerate(lines) if cite["needle"] in line]
        if len(hits) != 1:
            raise SystemExit(f"citation needle not unique in {cite['path']}: {len(hits)} hits for {cite['needle']!r}")
        citations.append(
            {
                "path": cite["path"],
                "line": hits[0],
                "current_wording": lines[hits[0] - 1].strip(),
                "figure_ids": cite["figure_ids"],
                "why": cite["why"],
            }
        )

    return {
        "schema": "consonance.quality-carry-forward/1",
        "unit": "QUALITY-CARRY-FORWARD",
        "recomputed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "offline": {"requests_sent": 0, "network_events": 0, "live_cells": 0},
        "rule": "Every figure is re-derived from the artefact it names at recompute time; nothing is copied from a prior report.",
        "era": "era A = tools off (no read_file serviced), per MODAL-ANSWER.json population.era_a_definition",
        "grid_population": {
            "rows_files_included": modal["population"]["included"],
            "turn_rows": modal["tables"]["turn_rows"],
            "excluded_with_reason": modal["population"]["excluded_with_reason"],
        },
        "figures": figures,
        "statements": statements,
        "needs_citation": citations,
        "missing_pages": MISSING_PAGES,
        "what_this_does_not_say": WHAT_THIS_DOES_NOT_SAY,
        "drift": drift,
    }


def check(record_path: Path) -> int:
    problems: list[str] = []
    record = load(record_path)
    fresh = recompute()
    fresh_by_id = {f["id"]: f for f in fresh["figures"]}
    recorded_by_id = {f["id"]: f for f in record.get("figures", [])}

    for fid, figure in recorded_by_id.items():
        if fid not in fresh_by_id:
            problems.append(f"{fid}: recorded figure no longer recomputed")
            continue
        new = fresh_by_id[fid]
        for field in ("value", "denominator", "source_path", "source_sha256"):
            if figure.get(field) != new[field]:
                problems.append(f"{fid}.{field}: recorded {figure.get(field)!r} != recomputed {new[field]!r}")
    for fid in fresh_by_id:
        if fid not in recorded_by_id:
            problems.append(f"{fid}: recomputed figure missing from the record")

    texts = [s.get("text") for s in record.get("statements", [])]
    for required in (STATEMENT_1, STATEMENT_2):
        if required not in texts:
            problems.append(f"statements block lost a required sentence: {required[:60]}...")
    fresh_statements = {s["id"]: s for s in fresh["statements"]}
    for statement in record.get("statements", []):
        attribution = statement.get("attribution") or {}
        sid = statement.get("id")
        if not attribution.get("unit") or not attribution.get("path") or not attribution.get("sha256"):
            problems.append(f"{sid}: attribution incomplete (unit/path/sha256 required)")
            continue
        want = fresh_statements.get(sid, {}).get("attribution", {})
        if attribution.get("sha256") != want.get("sha256"):
            problems.append(f"{sid}: attributed source sha256 drifted from {want.get('sha256')}")

    fresh_cites = {(c["path"], c["line"]) for c in fresh["needs_citation"]}
    recorded_cites = {(c["path"], c["line"]) for c in record.get("needs_citation", [])}
    if fresh_cites != recorded_cites:
        problems.append(f"needs_citation lines moved: only-in-record {sorted(recorded_cites - fresh_cites)}, only-in-fresh {sorted(fresh_cites - recorded_cites)}")

    if fresh["drift"]:
        problems.extend(f"recompute drift: {d}" for d in fresh["drift"])

    if problems:
        for problem in problems:
            print(f"DRIFT {problem}")
        return 1
    print(f"OK {len(fresh_by_id)} figures, {len(fresh['statements'])} statements, {len(fresh['needs_citation'])} citations match a fresh recomputation")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    gate = parser.add_mutually_exclusive_group(required=True)
    gate.add_argument("--write", action="store_true", help="write measure/QUALITY-CARRY-FORWARD.json")
    gate.add_argument("--check", action="store_true", help="exit 1 if any figure stops matching a fresh recomputation")
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD, help="record path (default measure/QUALITY-CARRY-FORWARD.json)")
    args = parser.parse_args(argv)

    if args.write:
        record = recompute()
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(record, indent=1, sort_keys=False) + "\n", encoding="utf-8")
        print(f"wrote {args.record} ({len(record['figures'])} figures) drift={record['drift']}")
        return 0
    return check(args.record)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
