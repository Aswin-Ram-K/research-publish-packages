#!/usr/bin/env python3
"""Resumable driver for COMBINED-CONTEXT-SERVING. Sends model requests."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
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

# import adapter from HL-PILOT tools
ADAPTER_PATH = CELL.parents[0] / "HL-PILOT" / "tools"
if str(ADAPTER_PATH) not in sys.path:
    sys.path.insert(0, str(ADAPTER_PATH))
from adapter import Adapter  # type: ignore

ENV = json.loads((RUN / "envelopes" / "CCS.json").read_text())
FINGERPRINTS = json.loads((RUN / "FINGERPRINTS.json").read_text())
RESERVATION = json.loads((CELL / "ledger" / "RESERVATION-CCS-2026-11-05.json").read_text())

CAP_DEFAULT = int(RESERVATION["granted_count"])
LOCK_DEFAULT = ENV["lock_path"]
ROWS_DEFAULT = CELL / "rows" / "ccs.jsonl"
INTENTS_DEFAULT = CELL / "rows" / "intents.jsonl"
COUNTER_DEFAULT = CELL / "ledger" / "SPENT-CCS.json"
GRADED_DEFAULT = CELL / "rows" / "graded"
ARTIFACTS_DEFAULT = RUN / "artifacts"

TASKS = ENV["tasks"]
ARMS = ENV["arms"]
TURNS = ENV["turns_per_task"]
MAX_TOKENS = ENV["max_tokens"]
MASK_AFTER = int(ENV.get("mask_after", 6))
TEMPERATURE = ENV["temperature"]
SEED = ENV["seed"]


def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_fixture(task_id):
    return json.loads((CELL / "tasks" / f"{task_id}.json").read_text())


def load_rows(path):
    rows = []
    p = Path(path)
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_counter(path, cap):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        data = {"spent": 0, "cap": cap}
        p.write_text(json.dumps(data) + "\n")
        return data
    return json.loads(p.read_text())


def write_counter(path, data):
    Path(path).write_text(json.dumps(data) + "\n")


def ensure_lock(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.touch()
    return p


def fingerprints_dict():
    return {
        "model": FINGERPRINTS["model"]["digest"],
        "tokenizer_template": FINGERPRINTS["tokenizer_template"]["digest"],
        "renderer": FINGERPRINTS["renderer"]["digest"],
        "engine_flags": FINGERPRINTS["engine_flags"]["digest"],
    }


def make_history(fixture, prior_rows):
    hist = []
    for r in sorted(prior_rows, key=lambda x: x["turn"]):
        hist.append({
            "turn": r["turn"],
            "answer": r.get("text", "") or "",
            "claim": (r.get("text", "") or "")[:240],
            "refs": None,
            "notes": "",
        })
    return hist


def grade_artifact(task, artifact_path, graded_dir):
    graded_dir = Path(graded_dir)
    out_dir = graded_dir / task
    # arm/turn filled by caller via path; here store caller passes full path
    grader = CELL / "tasks" / "grade" / "run.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(grader), "--task", task, "--artifact", str(artifact_path)],
            cwd=str(CELL),
            text=True,
            capture_output=True,
            timeout=120,
        )
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        objs = []
        for ln in lines:
            try:
                objs.append(json.loads(ln))
            except Exception:
                pass
        verified = None
        for o in objs:
            if "verified_success" in o:
                verified = bool(o["verified_success"])
        result = {
            "returncode": proc.returncode,
            "lines": objs,
            "verified_success": verified,
            "stderr": proc.stderr.strip()[:2000],
        }
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}", "verified_success": None}
    return result


def run_experiment(
    *,
    envelope_path=None,
    rows_path=None,
    intents_path=None,
    resume_arm=False,
    limit=None,
    counter_path=None,
    cap=None,
    lock_path=None,
    graded_dir=None,
    artifacts_dir=None,
    watcher_check=None,
    transport=None,
    adapter=None,
):
    global ENV, MAX_TOKENS, TURNS, MASK_AFTER, TEMPERATURE, SEED, TASKS, ARMS
    if envelope_path is not None:
        ENV = json.loads(Path(envelope_path).read_text())
    else:
        ENV = json.loads((RUN / "envelopes" / "CCS.json").read_text())
    MAX_TOKENS = ENV['max_tokens']
    TURNS = ENV.get('turns_per_task', TURNS)
    MASK_AFTER = int(ENV.get('mask_after', MASK_AFTER))
    TEMPERATURE = ENV['temperature']
    SEED = ENV['seed']
    TASKS = ENV['tasks']
    ARMS = ENV['arms']
    rows_path = Path(rows_path) if rows_path else ROWS_DEFAULT
    intents_path = Path(intents_path) if intents_path else INTENTS_DEFAULT
    counter_path = Path(counter_path) if counter_path else COUNTER_DEFAULT
    graded_dir = Path(graded_dir) if graded_dir else GRADED_DEFAULT
    artifacts_dir = Path(artifacts_dir) if artifacts_dir else ARTIFACTS_DEFAULT
    lock_path = lock_path if lock_path else LOCK_DEFAULT
    cap = cap if cap is not None else CAP_DEFAULT

    rows_path.parent.mkdir(parents=True, exist_ok=True)
    intents_path.parent.mkdir(parents=True, exist_ok=True)
    graded_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(rows_path)
    completed = {(r["task"], r["arm"], r["turn"]) for r in rows}

    # partial-arm guard
    from collections import defaultdict
    by_arm = defaultdict(set)
    for r in rows:
        by_arm[(r["task"], r["arm"])].add(r["turn"])
    if not resume_arm:
        for (task, arm), turns in by_arm.items():
            if 0 < len(turns) < TURNS:
                raise RuntimeError(
                    f"partially finished arm {task}/{arm} ({len(turns)}/{TURNS}); "
                    "pass --resume-arm to continue"
                )

    if adapter is None:
        adapter = Adapter(transport=transport, timeout=300.0)

    schedule = ENV["schedule"]
    if limit is not None:
        schedule = schedule[:limit]

    fps = fingerprints_dict()

    for call in schedule:
        task = call["task"]
        arm = call["arm"]
        turn = call["turn"]
        key = (task, arm, turn)
        if key in completed:
            continue

        if watcher_check is not None:
            alert = watcher_check(completed_count=len(completed))
            if alert and alert != "DONE":
                raise RuntimeError(f"watcher alert: {alert}")

        # budget check
        counter = read_counter(counter_path, cap)
        if counter.get("spent", 0) >= cap:
            raise RuntimeError("budget exhaustion: spent >= cap")

        fixture = load_fixture(task)
        prior_rows = [r for r in rows if r["task"] == task and r["arm"] == arm and r["turn"] < turn]
        hist = make_history(fixture, prior_rows)
        msgs = ra.build_messages(arm, fixture, hist, turn, K=MASK_AFTER)

        lock_p = ensure_lock(lock_path)
        send_id = str(uuid.uuid4())
        started = utcnow()

        with open(lock_p, "r+") as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
            try:
                # re-check + decrement under lock
                counter = read_counter(counter_path, cap)
                if counter.get("spent", 0) >= cap:
                    raise RuntimeError("budget exhaustion: spent >= cap")
                counter["spent"] = int(counter.get("spent", 0)) + 1
                write_counter(counter_path, counter)

                intent = {
                    "send_id": send_id,
                    "task": task,
                    "arm": arm,
                    "turn": turn,
                    "started_utc": started,
                    "max_tokens": MAX_TOKENS,
                }
                with open(intents_path, "a") as f:
                    f.write(json.dumps(intent) + "\n")
                    f.flush()

                row = adapter.chat(
                    msgs,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    seed=SEED,
                    run_id="CCS-2026-11-05",
                    arm=arm,
                    task_id=task,
                    step=turn,
                )
            finally:
                fcntl.flock(lf.fileno(), fcntl.LOCK_UN)

        ended = utcnow()

        # extend schema
        row["send_id"] = send_id
        row["started_utc"] = started
        row["ended_utc"] = ended
        row["task"] = task
        row["arm"] = arm
        row["turn"] = turn
        row["max_tokens"] = MAX_TOKENS
        row["fingerprints"] = fps
        # ensure derived null-safe
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

        # grade if artifact-bearing
        text = row.get("text") or ""
        if row.get("status") == 200 and text.strip():
            artifact_path = artifacts_dir / task / arm / f"{turn}.py"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(text)
            graded_path = graded_dir / task / arm / f"{turn}.json"
            graded_path.parent.mkdir(parents=True, exist_ok=True)
            graded = grade_artifact(task, artifact_path, graded_dir)
            # store at exact required path
            graded_path.write_text(json.dumps(graded, indent=2) + "\n")
            row["graded_path"] = str(graded_path)
            row["verified_success"] = graded.get("verified_success")

        # append + flush
        with open(rows_path, "a") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        rows.append(row)
        completed.add(key)

    return rows


def _watcher_check_factory(events_path, ignored=None):
    ignored = set(ignored or {"NO_ROWS_YET"})

    def _check(completed_count):
        alerts = []
        if events_path and os.path.exists(events_path):
            try:
                with open(events_path) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        for a in (obj.get("alerts") or []):
                            if a not in alerts:
                                alerts.append(a)
            except Exception:
                pass
        for a in alerts:
            if a == "DONE":
                continue
            if a in ignored:
                continue
            return a
        return None

    return _check


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume-arm", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--envelope", default=None)
    ap.add_argument("--rows", default=None)
    ap.add_argument("--watcher-events", default=None)
    ap.add_argument("--watcher-ignored-alerts", default="NO_ROWS_YET")
    args = ap.parse_args()
    wc = None
    if args.watcher_events is not None:
        ignored = [x.strip() for x in args.watcher_ignored_alerts.split(",") if x.strip()]
        wc = _watcher_check_factory(args.watcher_events, ignored)
    run_experiment(resume_arm=args.resume_arm, limit=args.limit, envelope_path=args.envelope, rows_path=args.rows, watcher_check=wc)
    print("DONE")


if __name__ == "__main__":
    main()
