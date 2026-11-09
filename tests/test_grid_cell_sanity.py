#!/usr/bin/env python3
"""GRID-CELL-SANITY — is a grid cell *analysable*?

Read-only audit of one cell's row file against the seven checks the unit card names:
row model (TURN-ROW-ATTRIBUTION), provenance (ROW-PROVENANCE, v8 fixture sha), claim
stamp (CLAIM-ROW-STAMP), cache attribution, stop-reason census (RECORD-STOP-REASON),
treatment markers per arm, and the 180 s wall guardrail.

It computes NO outcome statistic: no accuracy, no tvs, no token percentile is emitted.
The only central-tendency number is check 7's own explicit ask, the wall-guardrail p50 —
a guardrail descriptor for whether a turn ran away, not an analyser output.

Usage:
    python tests/test_grid_cell_sanity.py            # unittest (red + green cases)
    python tests/test_grid_cell_sanity.py --emit     # rewrite GRID-CELL-SANITY.json
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEASURE = ROOT / "experiments/ptr-engine/measure"
CLIENT = ROOT / "experiments/ptr-engine/longrun/client.py"

# The v8 fixture digest, quoted from the unit card. A v7/v5 sha in a v8-era cell is STOP.
V8_FIXTURE_SHA256 = "0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641"

PROVENANCE_FIELDS = (
    "arm", "model", "endpoint", "fixture_id", "fixture_sha256",
    "harness_sha256", "max_tokens", "thinking", "tools_mode",
)

TURN_INITIAL_KINDS = ("turn-initial", "turn")   # legacy cell: kind="turn" + row_measurement_source


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stop_reason_vocabulary() -> tuple:
    """Parse client.STOP_REASONS offline (no import: client.py pulls in requests)."""
    try:
        text = CLIENT.read_text(encoding="utf-8")
    except OSError:
        return ()
    names = re.findall(r'^(STOP_REASON_\w+)\s*=\s*"([^"]+)"', text, re.MULTILINE)
    block = re.search(r"^STOP_REASONS\s*=\s*\((.*?)\)", text, re.MULTILINE | re.DOTALL)
    if not names or not block:
        return ()
    by_name = dict(names)
    out = []
    for token in re.findall(r"STOP_REASON_\w+|\"[^\"]+\"", block.group(1)):
        out.append(token.strip('"') if token.startswith('"') else by_name.get(token, token))
    return tuple(out)


def load_rows(path: Path) -> tuple[list[dict], list[str], bool]:
    """Rows, unparseable-line notes, and whether a partial final line was skipped."""
    rows, notes, partial = [], [], False
    raw = path.read_bytes()
    lines = raw.splitlines()
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            partial = i == len(lines)
            notes.append(f"line {i}: {'partial final line skipped' if partial else 'unparseable'}")
    return rows, notes, partial


def _under_measure(path: Path) -> bool:
    try:
        path.relative_to(MEASURE)
        return True
    except ValueError:
        return False


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _sibling(path: Path, suffix: str) -> Path:
    return path.with_name(path.name[: -len(".jsonl")] + suffix)


def _declared_n(path: Path, observed_max_turn: int) -> tuple[int, str]:
    gates = sorted(path.parent.glob("cell-*" + path.stem.replace("rows-cell-", "") + "*.gates.json"))
    for g in gates:
        try:
            data = json.loads(g.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        n = (data.get("hypothesis") or {}).get("n")
        if not n:
            for v in data.get("verdicts", []):
                if v.get("gate") == "G3" and v.get("n"):
                    n = v["n"]
        if n:
            return int(n), str(g.relative_to(ROOT))
    return observed_max_turn, ""


def check_row_model(rows: list[dict]) -> dict:
    groups = defaultdict(list)
    for r in rows:
        groups[(r.get("task_id"), r.get("rep"), r.get("turn"))].append(r)
    problems = []
    turn_map = defaultdict(set)
    for (task, rep, turn), rs in groups.items():
        turn_map[(task, rep)].add(turn)
        initials = [r for r in rs if r.get("kind") in TURN_INITIAL_KINDS]
        legacy = [r for r in initials if r.get("kind") == "turn"]
        if len(initials) != 1:
            problems.append(f"turn {turn!r}: {len(initials)} initial rows (need exactly 1)")
        shas = [r.get("request_sha256") for r in rs]
        if len(set(shas)) != len(rs):
            problems.append(f"turn {turn!r}: {len(rs)} rows share {len(set(shas))} distinct request_sha256")
        sends = sorted(int(r.get("send_index") or 0) for r in rs)
        if sends != list(range(len(rs))):
            problems.append(f"turn {turn!r}: send_index {sends} != 0..{len(rs) - 1}")
        if len(legacy) == 1 and legacy[0].get("row_measurement_source") not in (None, "turn-initial"):
            problems.append(f"turn {turn!r}: legacy turn row is not the initial measurement")
    per_turn = Counter(len(v) for v in groups.values())
    outside = sum(n for n in per_turn if n != 1)
    if outside:
        problems.append(f"{outside} turn(s) carry more than one row")
    # no two turns may reuse one measurement
    seen = defaultdict(set)
    for r in rows:
        seen[r.get("request_sha256")].add((r.get("task_id"), r.get("rep"), r.get("turn")))
    reused = {s: sorted(map(str, t)) for s, t in seen.items() if len(t) > 1}
    if reused:
        problems.append(f"request_sha256 reused across turns: {reused}")
    gaps = []
    for key, turns in turn_map.items():
        missing = sorted(set(range(1, max(turns) + 1)) - turns)
        if missing:
            gaps.append(f"{key}: missing turns {missing}")
    problems.extend(gaps)
    return {
        "status": "fail" if problems else "pass",
        "measured": {
            "turns": len(groups),
            "rows_per_turn": dict(Counter(per_turn.values())),
            "kinds": dict(Counter(r.get("kind") for r in rows)),
            "distinct_request_sha256": len(seen),
            "rows": len(rows),
            "definition_fallback_turns": sum(
                1 for rs in groups.values() if all(r.get("kind") == "turn" for r in rs)),
        },
        "problems": problems,
    }


def check_provenance(rows: list[dict]) -> dict:
    missing = defaultdict(int)
    for r in rows:
        for f in PROVENANCE_FIELDS:
            if r.get(f) in (None, ""):
                missing[f] += 1
    shas = sorted({r.get("fixture_sha256") for r in rows if r.get("fixture_sha256")})
    fixture_ids = sorted({r.get("fixture_id") for r in rows if r.get("fixture_id")})
    v8_era = any("v8" in str(f) for f in fixture_ids)
    problems, stop_level = [], False
    if missing:
        problems.append("missing provenance: " + ", ".join(f"{k}x{v}" for k, v in sorted(missing.items())))
    if len(shas) > 1:
        problems.append(f"cell mixes {len(shas)} fixture_sha256 values: {shas}")
    if v8_era and V8_FIXTURE_SHA256 not in shas:
        problems.append(f"v8-era cell carries fixture_sha256 {shas} != v8 {V8_FIXTURE_SHA256[:8]}…")
        stop_level = True
    if not v8_era and shas and V8_FIXTURE_SHA256 in shas:
        problems.append("non-v8 fixture_id carries the v8 digest")
    return {
        "status": "fail" if problems else "pass",
        "stop_level": stop_level,
        "measured": {
            "fixture_id": fixture_ids,
            "fixture_sha256": shas,
            "v8_era": v8_era,
            "v8_sha_matches": V8_FIXTURE_SHA256 in shas,
            "arms": sorted({r.get("arm") for r in rows}),
            "models": sorted({r.get("model") for r in rows}),
            "missing_fields": dict(missing),
        },
        "problems": problems,
    }


def check_claim(path: Path, rows: list[dict]) -> dict:
    twin = path.with_name(path.name + ".claim.json")
    claim_meta = {}
    if twin.exists():
        try:
            claim_meta = json.loads(twin.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            claim_meta = {}
    row_claim = sorted({str(r.get("claim")) for r in rows if r.get("claim") not in (None, "")})
    unstamped = [r.get("turn") for r in rows
                 if r.get("claim") in (None, "") or not isinstance(r.get("comparison_eligible"), bool)]
    claim = claim_meta.get("claim") or (row_claim[0] if row_claim else None)
    problems = []
    if unstamped:
        problems.append(f"{len(unstamped)} row(s) without a claim stamp: turns {unstamped[:12]}")
    if claim in (None, "none"):
        problems.append(f"claim={claim!r}: the analyser must refuse this cell, it is never pooled")
    return {
        "status": "fail" if problems else "pass",
        "measured": {
            "claim": claim,
            "claim_meta": claim_meta or None,
            "row_claim": row_claim,
            "comparison_eligible": sorted({r.get("comparison_eligible") for r in rows}, key=str),
            "unstamped_rows": len(unstamped),
        },
        "problems": problems,
    }


def check_cache(rows: list[dict]) -> dict:
    none_rows = [r.get("turn") for r in rows if r.get("cached_tokens") is None]
    declared = [r for r in rows if "prompt_tokens_details" in str(r.get("token_source") or "")]
    undeclared = [r.get("turn") for r in rows if not r.get("token_source")]
    sources = Counter(str(r.get("token_source")) for r in rows)
    engines = sorted({str(r.get("engine")) for r in rows})
    problems = []
    if none_rows:
        problems.append(
            f"cached_tokens is None on {len(none_rows)} row(s) "
            f"(turns {none_rows[:12]}); token_source {dict(sources)}")
    if undeclared:
        problems.append(f"{len(undeclared)} row(s) carry no token_source at all")
    return {
        "status": "fail" if problems else "pass",
        "measured": {
            "rows_with_cached_tokens": len(rows) - len(none_rows),
            "rows_cached_tokens_none": len(none_rows),
            "rows_declaring_prompt_tokens_details": len(declared),
            "token_source": dict(sources),
            "engine": engines,
            "cached_source": dict(Counter(str(r.get("cached_source")) for r in rows)),
        },
        "problems": problems,
    }


def check_stops(rows: list[dict]) -> dict:
    vocab = stop_reason_vocabulary()
    census = Counter(str(r.get("stop_reason")) for r in rows)
    out_of_vocab = {k: v for k, v in census.items() if vocab and k not in vocab}
    unknown = [r.get("turn") for r in rows if r.get("stop_reason") == "unknown"]
    length = [r for r in rows if r.get("stop_reason") == "length"]
    flagged, problems = [], []
    for r in length:
        excluded = bool(r.get("failed_turn")) or r.get("timing_usable") is False
        flagged.append({
            "turn": r.get("turn"),
            "max_tokens": r.get("max_tokens"),
            "truncated": r.get("truncated"),
            "completion_tokens": r.get("completion_tokens"),
            "excluded_in_row": excluded,
        })
        if not excluded:
            problems.append(f"turn {r.get('turn')}: stop_reason=length at max_tokens={r.get('max_tokens')} "
                            "and the row does NOT mark the turn excluded")
    if unknown:
        problems.append(f"stop_reason=unknown on turns {unknown}")
    if out_of_vocab:
        problems.append(f"stop_reason outside client.STOP_REASONS: {out_of_vocab}")
    return {
        "status": "fail" if problems else "pass",
        "measured": {
            "census": dict(census),
            "vocabulary_size": len(vocab),
            "unknown": len(unknown),
            "length": len(length),
            "length_rows": flagged,
            "truncated_rows": sum(1 for r in rows if r.get("truncated")),
        },
        "problems": problems,
    }


def check_treatments(rows: list[dict], declared_n: int, observed_turns: int) -> dict:
    arms = sorted({str(r.get("arm")) for r in rows})
    horizon_reached = observed_turns >= declared_n
    per_arm, problems, zero = {}, [], []
    for arm in arms:
        rs = [r for r in rows if str(r.get("arm")) == arm]
        if arm == "transcript-grow":
            fires = [(r.get("turn"), int(r.get("evicted") or 0)) for r in rs if int(r.get("evicted") or 0) > 0]
            marker = "evicted>0"
        elif arm == "transcript-compact":
            fires = [(r.get("turn"), 1) for r in rs
                     if r.get("kind") == "digest" or r.get("digest_at") is not None]
            marker = 'kind=="digest" or digest_at'
        elif arm == "lease-reopen":
            fires = [(r.get("turn"), int(r.get("lease") or 1)) for r in rs if int(r.get("lease") or 1) >= 2]
            marker = "lease>=2"
        elif arm == "pointer-stable":
            fires = []
            marker = None
        else:
            fires = []
            marker = "unmapped-arm"
        first = min((t for t, _ in fires), default=None)
        entry = {
            "arm": arm,
            "predicate": marker,
            "marker_events": len(fires),
            "first_fire_turn": first,
            "max_evicted": max((int(r.get("evicted") or 0) for r in rs), default=0),
            "digest_rows": sum(1 for r in rs if r.get("kind") == "digest"),
            "digest_at_rows": sum(1 for r in rs if r.get("digest_at") is not None),
            "max_lease": max((int(r.get("lease") or 1) for r in rs), default=1),
            "turns_with_cached_tokens_gt0": sum(1 for r in rs if int(r.get("cached_tokens") or 0) > 0),
            "rows": len(rs),
        }
        if marker is None:
            entry["status"] = "not_applicable"
            entry["note"] = (
                "pointer-stable has no row-level treatment field: the frozen index prefix "
                "(run_longrun.py:1125-1126 prefix_sha256) is runner-internal and is not written "
                "to a row. Its marker is structural (stable by construction), so a zero count "
                "here is NOT evidence the arm ran untreated; cached_tokens>0 turns are the only "
                "row proxy for a live prefix cache.")
            per_arm[arm] = entry
            continue
        if entry["marker_events"] == 0:
            entry["status"] = "fail" if horizon_reached else "not_applicable"
            entry["zero_marker"] = True
            if horizon_reached:
                problems.append(
                    f"arm {arm}: treatment marker {marker} is ZERO across all {len(rs)} rows over "
                    f"{observed_turns} turns — the cell is not evidence about {arm}")
            else:
                entry["note"] = (
                    f"horizon not reached: {observed_turns}/{declared_n} turns on disk, so a zero "
                    f"marker for {marker} is not yet a finding")
                zero.append(arm)
        else:
            entry["status"] = "pass"
            if not horizon_reached:
                entry["note"] = f"fired at T{first} with {observed_turns}/{declared_n} turns on disk"
        per_arm[arm] = entry
    statuses = [v["status"] for v in per_arm.values()]
    if "fail" in statuses:
        status = "fail"
    elif statuses and all(s == "not_applicable" for s in statuses):
        status = "not_applicable"
    elif "pass" in statuses:
        status = "pass"
    else:
        status = "not_applicable"
    return {
        "status": status,
        "measured": {
            "horizon_reached": horizon_reached,
            "declared_n": declared_n,
            "observed_turns": observed_turns,
            "per_arm": per_arm,
            "zero_marker_arms": zero,
        },
        "problems": problems,
    }


def check_walls(rows: list[dict]) -> dict:
    walls = [float(r.get("wall_ms") or 0.0) for r in rows]
    over = [(r.get("turn"), r.get("wall_ms")) for r in rows if float(r.get("wall_ms") or 0.0) > 180_000]
    excluded = [r for r in rows if r.get("timing_usable") is False or r.get("failed_turn")]
    problems = []
    if over:
        problems.append(f"{len(over)} turn(s) over the 180,000 ms cap: {over[:12]}")
    unrecorded = [r.get("turn") for r in excluded
                  if r.get("timing_usable") is None and r.get("failed_turn") is None]
    if unrecorded:
        problems.append(f"turn(s) {unrecorded} excluded without a row-level exclusion flag")
    walls_sorted = sorted(walls)
    median = 0.0
    if walls_sorted:
        n = len(walls_sorted)
        median = walls_sorted[n // 2] if n % 2 else (walls_sorted[n // 2 - 1] + walls_sorted[n // 2]) / 2
    return {
        "status": "fail" if problems else "pass",
        "measured": {
            "max_wall_ms": max(walls) if walls else None,
            "p50_wall_ms": median,
            "wall_cap_ms": 180_000,
            "turns_over_cap": len(over),
            "excluded_turns": [
                {"turn": r.get("turn"), "timing_usable": r.get("timing_usable"),
                 "failed_turn": r.get("failed_turn"), "stop_reason": r.get("stop_reason"),
                 "recorded_in_row": r.get("timing_usable") is not None
                 or r.get("failed_turn") is not None}
                for r in excluded
            ],
            "guardrail_note": "max and p50 of wall_ms are check 7's own guardrail ask, "
                              "not an outcome statistic",
        },
        "problems": problems,
    }


def _usable_for(cell: dict) -> tuple[list[str], str]:
    checks = cell["checks"]
    if cell["scope"] == "pre_run_a":
        return [], "pre-RUN-A cell: outside this audit's batch and never pooled with RUN-A*"
    if cell["cell_state"] != "complete":
        return [], (f"cell in progress: {cell['turns_on_disk']}/{cell['declared_n']} turns on disk "
                    f"— a statistic computed now would be from a truncated cell")
    if checks["provenance"]["status"] == "fail":
        return [], "provenance failed (fixture identity) — the cell is not attributable"
    if checks["treatments"]["status"] == "fail":
        return [], "treatment marker is zero — the cell is not evidence about its arm"
    if checks["claim_stamp"]["status"] == "fail":
        return [], "claim stamp failed or claim=none — the analyser must refuse it"
    if checks["row_model"]["status"] == "fail":
        return [], "row model failed — turns cannot be attributed"
    usable = []
    if checks["claim_stamp"]["measured"].get("comparison_eligible") and True in \
            set(map(bool, checks["claim_stamp"]["measured"].get("comparison_eligible") or [])):
        usable.append("h1_pooled")
    if checks["claim_stamp"]["measured"].get("claim") == "H2":
        usable.append("h2")
    if checks["wall_guardrails"]["status"] == "pass" and checks["stop_reasons"]["status"] == "pass":
        usable.append("h3")
    return usable, ""


def analyse_cell(path: Path, files_read: list[Path] | None = None) -> dict:
    rows, notes, partial = load_rows(path)
    if files_read is not None:
        files_read.append(path)
    observed_turns = max((int(r.get("turn") or 0) for r in rows), default=0)
    declared_n, gates_ref = _declared_n(path, observed_turns)
    has_gates = bool(gates_ref)
    if gates_ref and files_read is not None:
        files_read.append(ROOT / gates_ref)
    cell_state = "complete" if observed_turns >= declared_n else "in_progress"
    checks = {
        "row_model": check_row_model(rows),
        "provenance": check_provenance(rows),
        "claim_stamp": check_claim(path, rows),
        "cache_attribution": check_cache(rows),
        "stop_reasons": check_stops(rows),
        "treatments": check_treatments(rows, declared_n, observed_turns),
        "wall_guardrails": check_walls(rows),
    }
    cell = {
        "path": _rel(path),
        "sha256": sha256_file(path),
        "scope": "run_a" if (has_gates or not _under_measure(path)) else "pre_run_a",
        "declared_n_from": gates_ref or None,
        "declared_n": declared_n,
        "turns_on_disk": observed_turns,
        "cell_state": cell_state,
        "rows": len(rows),
        "rows_per_kind": dict(Counter(r.get("kind") for r in rows)),
        "stop_reason_census": checks["stop_reasons"]["measured"]["census"],
        "sha256_is_snapshot": cell_state != "complete",
        "partial_last_line_skipped": partial,
        "parse_notes": notes,
        "checks": checks,
    }
    if cell["scope"] == "pre_run_a":
        # A pre-RUN-A row file predates CLAIM-ROW-STAMP / turn-initial / digest rows: its
        # schema cannot answer these checks, and its "failures" would be schema-era, not
        # defects. Keep the measurements, withdraw the verdicts.
        for name, check in checks.items():
            check["schema_verdict"] = check["status"]
            check["status"] = "not_applicable"
            check["problems"] = [
                "pre-RUN-A schema (no claim/provenance/stop_reason fields): " + p
                for p in check.get("problems", [])
            ]
        checks["treatments"]["problems"] = [
            "pre-RUN-A schema: treatment markers not comparable with RUN-A*" ]
    usable, reason = _usable_for(cell)
    cell["usable_for"] = usable
    cell["usable_reason"] = reason
    return cell


def discover() -> list[Path]:
    return sorted(MEASURE.glob("rows-cell-*.jsonl"))


def emit() -> dict:
    files_read: list[Path] = [CLIENT]
    before = {str(p.relative_to(ROOT)): sha256_file(p) for p in files_read if p.exists()}
    cells = [analyse_cell(p, files_read) for p in discover()]
    before = {str(p.relative_to(ROOT)): sha256_file(p) for p in files_read if p.exists()}
    after = {str(p.relative_to(ROOT)): sha256_file(p) for p in dict.fromkeys(files_read) if p.exists()}
    proof = {k: {"sha256": after.get(k), "unchanged": before.get(k) == after.get(k),
                 "before": before.get(k)} for k in after}
    doc = {
        "unit": "GRID-CELL-SANITY",
        "check": "are the grid's cells analysable before anyone computes a statistic from them",
        "requests_spent": 0,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "v8_fixture_sha256_expected": V8_FIXTURE_SHA256,
        "checks_legend": {
            "row_model": "TURN-ROW-ATTRIBUTION: one initial row per turn, distinct request_sha256 == sends",
            "provenance": "ROW-PROVENANCE: arm/model/endpoint/fixture/harness/max_tokens/thinking/tools_mode + v8 sha",
            "claim_stamp": "CLAIM-ROW-STAMP: claim + comparison_eligible on every row; claim=none is refused",
            "cache_attribution": "cached_tokens present where prompt_tokens_details existed, token_source names it",
            "stop_reasons": "every stop_reason in client.STOP_REASONS; unknown and length counted",
            "treatments": "each arm's marker non-zero by turn 48; a zero marker is not evidence about the arm",
            "wall_guardrails": "no wall_ms > 180,000; max and p50 reported",
        },
        "cells": cells,
        "read_only_proof": proof,
        "verdict": {
            "cells_on_disk": len(cells),
            "analysable_today": [c["path"] for c in cells if c["usable_for"]],
            "must_not_enter_analysis": [c["path"] for c in cells if not c["usable_for"]],
        },
    }
    out = MEASURE / "GRID-CELL-SANITY.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return doc


# ----------------------------------------------------------------- the red/green tests
def _row(turn: int, *, arm="lease-reopen", sha=None, evicted=0, digest_at=None, lease=None,
         stop="stop", claim="H2", eligible=True, wall=1000.0, failed=False, timing=True):
    return {
        "task_id": "LR-01", "rep": 1, "turn": turn, "send_index": 0, "row_seq": turn,
        "kind": "turn", "row_measurement_source": "turn-initial",
        "arm": arm, "model": "m", "endpoint": "http://127.0.0.1:1/v1",
        "fixture_id": "LR-01.v8-treatments-reachable", "fixture_sha256": V8_FIXTURE_SHA256,
        "harness_sha256": "h", "max_tokens": 4096, "thinking": "off", "tools_mode": "off",
        "claim": claim, "comparison_eligible": eligible,
        "request_sha256": sha or f"sha-turn-{turn}",
        "cached_tokens": 128, "token_source": "usage.prompt_tokens;usage.prompt_tokens_details.cached_tokens",
        "cached_source": "prompt_tokens_details", "engine": "sglang",
        "stop_reason": stop, "truncated": stop == "length", "failed_turn": failed,
        "timing_usable": timing, "wall_ms": wall, "lease": lease, "evicted": evicted,
        "digest_at": digest_at, "completion_tokens": 10,
    }


def _write_cell(rows, *, name="rows-cell-test-20261026T000000Z.jsonl"):
    path = Path(tempfile.mkdtemp()) / name
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


class GridCellSanityTests(unittest.TestCase):
    def test_green_complete_lease_cell_is_usable(self):
        rows = [_row(t, lease=2 if t >= 3 else 1) for t in range(1, 5)]
        cell = analyse_cell(_write_cell(rows))
        self.assertEqual(cell["cell_state"], "complete")
        self.assertEqual(cell["checks"]["treatments"]["status"], "pass")
        self.assertEqual(cell["checks"]["treatments"]["measured"]["per_arm"]["lease-reopen"]["first_fire_turn"], 3)
        self.assertEqual(cell["usable_for"], ["h1_pooled", "h2", "h3"])

    def test_red_duplicate_request_sha256(self):
        rows = [_row(t) for t in range(1, 5)]
        rows[2]["request_sha256"] = rows[1]["request_sha256"]   # two turns, one measurement
        cell = analyse_cell(_write_cell(rows))
        self.assertEqual(cell["checks"]["row_model"]["status"], "fail")
        joined = " ".join(cell["checks"]["row_model"]["problems"])
        self.assertIn("reused across turns", joined)
        self.assertEqual(cell["usable_for"], [])
        print("\nRED duplicate request_sha256 ->", cell["checks"]["row_model"]["problems"])

    def test_red_zero_treatment_marker(self):
        rows = [_row(t, arm="transcript-grow", evicted=0) for t in range(1, 5)]
        cell = analyse_cell(_write_cell(rows))
        self.assertEqual(cell["checks"]["treatments"]["status"], "fail")
        self.assertTrue(cell["checks"]["treatments"]["measured"]["per_arm"]["transcript-grow"]["zero_marker"])
        self.assertEqual(cell["usable_for"], [])
        print("\nRED zero treatment marker ->", cell["checks"]["treatments"]["problems"])

    def test_red_v8_era_cell_with_v7_sha(self):
        rows = [_row(t) for t in range(1, 4)]
        for r in rows:
            r["fixture_sha256"] = "9" * 64
        cell = analyse_cell(_write_cell(rows))
        self.assertEqual(cell["checks"]["provenance"]["status"], "fail")
        self.assertTrue(cell["checks"]["provenance"]["stop_level"])
        self.assertEqual(cell["usable_for"], [])

    def test_red_length_row_not_excluded(self):
        rows = [_row(t) for t in range(1, 4)]
        rows[1].update(stop_reason="length", truncated=True, failed_turn=False, timing_usable=True)
        cell = analyse_cell(_write_cell(rows))
        self.assertEqual(cell["checks"]["stop_reasons"]["status"], "fail")
        # and once the row is properly excluded it is a recorded truncation, not a defect
        rows[1].update(failed_turn=True, timing_usable=False)
        cell = analyse_cell(_write_cell(rows))
        self.assertEqual(cell["checks"]["stop_reasons"]["status"], "pass")

    def test_claim_none_is_refused(self):
        rows = [_row(t, claim="none", eligible=False) for t in range(1, 4)]
        cell = analyse_cell(_write_cell(rows))
        self.assertEqual(cell["checks"]["claim_stamp"]["status"], "fail")
        self.assertEqual(cell["usable_for"], [])

    def test_partial_last_line_is_skipped(self):
        rows = [_row(t) for t in range(1, 4)]
        path = _write_cell(rows)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write('{"turn": 4, "arm": "lease-reop')
        cell = analyse_cell(path)
        self.assertTrue(cell["partial_last_line_skipped"])
        self.assertEqual(cell["turns_on_disk"], 3)


if __name__ == "__main__":
    if "--emit" in sys.argv:
        result = emit()
        print(json.dumps(result["verdict"], indent=1))
        for c in result["cells"]:
            print(c["path"], c["cell_state"], {k: v["status"] for k, v in c["checks"].items()},
                  "usable_for=", c["usable_for"])
    else:
        unittest.main(verbosity=2)
