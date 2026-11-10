#!/usr/bin/env python3
"""Calibration pilot driver for COMBINED-CONTEXT-SERVING."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
RUN = CELL / "run"
ARMS_DIR = CELL / "arms"
if str(ARMS_DIR) not in sys.path:
    sys.path.insert(0, str(ARMS_DIR))
import render_arms as ra  # type: ignore

ADAPTER_PATH = CELL.parents[0] / "HL-PILOT" / "tools"
if str(ADAPTER_PATH) not in sys.path:
    sys.path.insert(0, str(ADAPTER_PATH))
from adapter import Adapter  # type: ignore

sys.path.insert(0, str(RUN))
import driver  # type: ignore

ENV = json.loads((RUN / "envelopes" / "CAL5.json").read_text())
FINGERPRINTS = json.loads((RUN / "FINGERPRINTS.json").read_text())
RESERVATION = json.loads((CELL / "ledger" / "RESERVATION-CCS-2026-11-05.json").read_text())

ROWS_PATH = CELL / "rows" / "cal5.jsonl"
INTENTS_PATH = CELL / "rows" / "cal3-intents.jsonl"
COUNTER_PATH = CELL / "ledger" / "SPENT-CCS.json"
GRADED_DIR = CELL / "rows" / "graded"
ARTIFACTS_DIR = RUN / "artifacts" / "cal5"
LOCK_PATH = ENV["lock_path"]
CAP = 61
WATCHER_LOG = CELL / "watcher" / "cal5-events.jsonl"


def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fingerprints_dict():
    return {
        "model": FINGERPRINTS["model"]["digest"],
        "tokenizer_template": FINGERPRINTS["tokenizer_template"]["digest"],
        "renderer": FINGERPRINTS["renderer"]["digest"],
        "engine_flags": FINGERPRINTS["engine_flags"]["digest"],
    }


def load_rows(path):
    return driver.load_rows(path)


def read_counter(path, cap):
    return driver.read_counter(path, cap)


def write_counter(path, data):
    driver.write_counter(path, data)


def ensure_lock(path):
    return driver.ensure_lock(path)


def grade_artifact(task, artifact_path, graded_dir):
    return driver.grade_artifact(task, artifact_path, graded_dir)


def watcher_alert():
    if not WATCHER_LOG.exists():
        return None
    try:
        lines = [ln for ln in WATCHER_LOG.read_text().splitlines() if ln.strip()]
    except Exception:
        return None
    if not lines:
        return None
    try:
        last = json.loads(lines[-1])
    except Exception:
        return None
    alerts = last.get("alerts") or []
    for a in alerts:
        if a != "DONE":
            return a
    return None


def call_key(r):
    return (r.get("task"), r.get("arm"), r.get("turn"), r.get("max_tokens"),
            r.get("thinking"), r.get("rep"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    rows_path = ROWS_PATH
    intents_path = INTENTS_PATH
    counter_path = COUNTER_PATH
    graded_dir = GRADED_DIR
    artifacts_dir = ARTIFACTS_DIR
    lock_path = LOCK_PATH

    rows_path.parent.mkdir(parents=True, exist_ok=True)
    intents_path.parent.mkdir(parents=True, exist_ok=True)
    graded_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(rows_path)
    completed = {call_key(r) for r in rows}

    adapter = Adapter(timeout=300.0)
    fps = fingerprints_dict()
    schedule = ENV["schedule"]

    for call in schedule:
        task = call["task"]
        arm = call["arm"]
        turn = call["turn"]
        max_tokens = call["max_tokens"]
        thinking = bool(call["thinking"])
        rep = call["rep"]
        temperature = call["temperature"]
        seed = call["seed"]

        key = (task, arm, turn, max_tokens, thinking, rep)
        if key in completed:
            continue

        alert = watcher_alert()
        if alert:
            raise RuntimeError(f"watcher alert: {alert}")

        counter = read_counter(counter_path, CAP)
        if counter.get("spent", 0) >= CAP:
            raise RuntimeError("budget exhaustion: spent >= cap")

        fixture = driver.load_fixture(task)
        prior_rows = [r for r in rows if r["task"] == task and r["arm"] == arm
                      and r["turn"] < turn and r.get("rep") == rep
                      and r.get("thinking") == thinking and r.get("max_tokens") == max_tokens]
        hist = driver.make_history(fixture, prior_rows)
        msgs = ra.build_messages(arm, fixture, hist, turn, K=6)

        lock_p = ensure_lock(lock_path)
        send_id = str(uuid.uuid4())
        started = utcnow()

        with open(lock_p, "r+") as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
            try:
                counter = read_counter(counter_path, CAP)
                if counter.get("spent", 0) >= CAP:
                    raise RuntimeError("budget exhaustion: spent >= cap")
                counter["spent"] = int(counter.get("spent", 0)) + 1
                write_counter(counter_path, counter)

                intent = {
                    "send_id": send_id,
                    "task": task,
                    "arm": arm,
                    "turn": turn,
                    "max_tokens": max_tokens,
                    "thinking": thinking,
                    "rep": rep,
                    "started_utc": started,
                }
                with open(intents_path, "a") as f:
                    f.write(json.dumps(intent) + "\n")
                    f.flush()

                row = adapter.chat(
                    msgs,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    seed=seed,
                    run_id="CAL5-CCS-2026-11-05",
                    arm=arm,
                    task_id=task,
                    step=turn,
                    thinking=thinking,
                )
            finally:
                fcntl.flock(lf.fileno(), fcntl.LOCK_UN)

        ended = utcnow()

        row["send_id"] = send_id
        row["started_utc"] = started
        row["ended_utc"] = ended
        row["task"] = task
        row["arm"] = arm
        row["turn"] = turn
        row["max_tokens"] = max_tokens
        row["thinking"] = thinking
        row["rep"] = rep
        row["temperature"] = temperature
        row["seed"] = seed
        row["fingerprints"] = fps
        row["run_id"] = "CAL5-CCS-2026-11-05"

        # null-safe cached_tokens derived
        derived = row.setdefault("derived", {})
        if not isinstance(derived, dict):
            derived = {}
            row["derived"] = derived
        cached = row.get("cached_tokens")
        pt = row.get("prompt_tokens")
        if cached is not None and pt is not None:
            derived["uncached_prefill_tokens_from_prompt_minus_cached"] = max(0, int(pt) - int(cached))
        else:
            derived["uncached_prefill_tokens_from_prompt_minus_cached"] = None
        if "cached_tokens" not in row:
            row["cached_tokens"] = None

        text = row.get("text") or ""
        if row.get("status") == 200 and text.strip():
            artifact_path = artifacts_dir / task / f"turn{turn}_mt{max_tokens}_think{'on' if thinking else 'off'}_rep{rep}.py"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(text)
            graded_path = graded_dir / task / f"turn{turn}_mt{max_tokens}_think{'on' if thinking else 'off'}_rep{rep}.json"
            graded_path.parent.mkdir(parents=True, exist_ok=True)
            graded = grade_artifact(task, artifact_path, graded_dir)
            graded_path.write_text(json.dumps(graded, indent=2) + "\n")
            row["graded_path"] = str(graded_path)
            row["artifact_path"] = str(artifact_path)
            row["verified_success"] = graded.get("verified_success")

        with open(rows_path, "a") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        rows.append(row)
        completed.add(key)

    # print DONE to stdout (watcher watches log file separately)
    print("DONE")


if __name__ == "__main__":
    main()
