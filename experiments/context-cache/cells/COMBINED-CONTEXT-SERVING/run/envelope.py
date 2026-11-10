#!/usr/bin/env python3
"""Freeze the immutable consonance.run/1 envelope for COMBINED-CONTEXT-SERVING calibration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
RUN = CELL / "run"
ENV_DIR = RUN / "envelopes"
OUT = ENV_DIR / "CAL.json"

TASK_ID = "T1.discovery"
ARM = "B"
TURNS_CAL = [2, 7]
MAX_TOKENS_OPTIONS = [1200, 2400]
REPS_ON = 3
TEMPERATURE = 0.0
SEED = 7
MAX_CALLS = 24
CAP = 24
LOCK = "/home/zer0null/research extractor/experiments/context-cache/.occamy.lock"
STOP_CONDITIONS = [
    "any watcher alert other than DONE",
    "lost lock",
    "three consecutive non-200 rows",
    "ten minutes with no completed row while a call is outstanding",
    "budget exhaustion",
    "hard deadline",
    "calibration rule unsatisfied inside cap",
]


def build_schedule():
    seq = 0
    rows = []
    # thinking on: both turns x both budgets x 3 reps
    for turn in TURNS_CAL:
        for mt in MAX_TOKENS_OPTIONS:
            for rep in range(1, REPS_ON + 1):
                seq += 1
                rows.append({
                    "seq": seq,
                    "task": TASK_ID,
                    "arm": ARM,
                    "turn": turn,
                    "max_tokens": mt,
                    "temperature": TEMPERATURE,
                    "seed": SEED,
                    "thinking": True,
                    "rep": rep,
                })
    # thinking off: both turns at 2400 x 1
    for turn in TURNS_CAL:
        seq += 1
        rows.append({
            "seq": seq,
            "task": TASK_ID,
            "arm": ARM,
            "turn": turn,
            "max_tokens": 2400,
            "temperature": TEMPERATURE,
            "seed": SEED,
            "thinking": False,
            "rep": 1,
        })
    assert len(rows) == 14, len(rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true", help="write envelopes/CAL.json")
    args = ap.parse_args()

    schedule = build_schedule()
    envelope = {
        "schema": "consonance.run/1",
        "run_id": "CAL-CCS-2026-11-05",
        "max_calls": MAX_CALLS,
        "arms": [ARM],
        "tasks": [TASK_ID],
        "turns": TURNS_CAL,
        "max_tokens_options": MAX_TOKENS_OPTIONS,
        "reps_thinking_on": REPS_ON,
        "schedule": schedule,
        "aggregate_cap": CAP,
        "reservation_file": str(CELL / "ledger" / "RESERVATION-CCS-2026-11-05.json"),
        "lock_path": LOCK,
        "per_call_timeout_seconds": 300,
        "temperature": TEMPERATURE,
        "seed": SEED,
        "stop_conditions": STOP_CONDITIONS,
        "rows_path": "rows/cal.jsonl",
        "graded_dir": "rows/graded",
        "decision_rule": (
            "choose the smallest max_tokens at which all six thinking-on repeats "
            "return non-empty text and a grader-acceptable artifact; if 1200 already "
            "does that, keep 1200; if neither does, record the finding and stop "
            "rather than escalating without bound"
        ),
    }

    if not args.freeze:
        print(json.dumps({"calls": len(schedule), "cap": CAP}, indent=2))
        return

    ENV_DIR.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        raise SystemExit(f"refused: envelope already exists: {OUT}")
    OUT.write_text(json.dumps(envelope, indent=2) + "\n")
    print(f"frozen: {OUT} calls={len(schedule)}")


if __name__ == "__main__":
    main()
