#!/usr/bin/env python3
"""G5-FANOUT cell: measured race-free fan-out ratio.

Three layouts A/B/C, 8 fan-outs each, K=8 branches. Shared prefix warmed
(cold insert + warm probe) before branch dispatch for A and C.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

CELL = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(CELL, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "context-cache"))
from resextract.context.salt import make_salt, salted  # noqa: E402
import client as occ  # noqa: E402
import g5_analyze  # noqa: E402

REPO = Path(ROOT)
CELL_DIR = Path(CELL)
ROWS_PATH = CELL_DIR / "rows.jsonl"
ANALYSIS_PATH = CELL_DIR / "analysis.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CONFIG_PATH = REPO / "state" / "config" / "live-server-config.json"
HANDOFF_PATH = REPO / "orchestration" / "handoffs" / "G5.json"
UNIT_CARD_PATH = REPO / "orchestration" / "units" / "G5.md"

LAYOUTS = ("A", "B", "C")
FANOUTS = 8
K = 8
BASE_SEEDS = {"A": 50000, "B": 60000, "C": 70000}
REQUEST_CAP = 600
INTERNAL_CAP = 580
LOCK_TIMEOUT_S = 3600.0
STACK = "sglang"
CONFIG_ID = "S0"
MAX_TOKENS = 2
TIMEOUT_S = 120.0

requests_used = 0
lock_handle = None


def shared_body():
    return "".join(
        "Sentence about repository work item %d: the maintainer reviewed the "
        "pending diff, noted the flaky test in the integration suite, and "
        "scheduled a follow-up review for the next release cycle.\n" % i
        for i in range(46)
    )


def delta(k):
    return (
        "Delta payload for branch %d records the query plan, the failing assertion, "
        "the fixture corpus, the log excerpt, the reproduction command, the expected "
        "duration, the review checklist and the rollback note for this shard. It also "
        "notes the operator that owns the shard and the date the snapshot was taken.\n"
        % k
    )


def tag(k):
    return "[BRANCH-%d]\n" % k


def arm_prompts(arm, P):
    if arm == "A":
        return [P + tag(k) + delta(k) for k in range(1, K + 1)]
    if arm == "B":
        return [tag(k) + P + delta(k) for k in range(1, K + 1)]
    return [P + delta(k) + "\n" + tag(k) for k in range(1, K + 1)]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def config_sha256() -> str:
    return hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()


def acquire_lock(path: Path, timeout_s: float):
    handle = path.open("a+", encoding="utf-8")
    started = time.monotonic()
    deadline = started + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError(f"occamy lock busy for {timeout_s:.0f}s")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": "G5", "pid": os.getpid(), "acquired_utc": utc_now(),
               "waited_s": round(time.monotonic() - started, 1)}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle, time.monotonic() - started


def release_lock(handle):
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": "G5", "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def load_existing() -> dict[tuple[str, int, int], dict]:
    out = {}
    if not ROWS_PATH.exists():
        return out
    for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        out[(str(row["layout"]), int(row["fanout_index"]), int(row["branch_index"]))] = row
    return out


def append_row(row: dict) -> None:
    ROWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ROWS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def chat_once(messages):
    global requests_used
    if requests_used >= INTERNAL_CAP:
        raise RuntimeError(f"request cap guard: {requests_used} >= {INTERNAL_CAP}")
    client = occ.ChatClient()
    refusal_streak = 0
    while True:
        try:
            prompt, cached, _comp, ttft, _wall, status, _text = client.chat(
                messages, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=TIMEOUT_S)
            requests_used += 1
            return prompt, cached, ttft, status
        except Exception as exc:  # noqa: BLE001
            text = str(exc).lower()
            if "refus" in text or "connect" in text or "connection" in text or "timeout" in text:
                refusal_streak += 1
                if refusal_streak >= 3:
                    raise RuntimeError(f"3 consecutive transport/refusal failures: {exc}")
                time.sleep(2.0)
                continue
            raise


def fanout_branches_done(existing, layout, fi, salt):
    for k in range(1, K + 1):
        r = existing.get((layout, fi, k))
        if r is None or str(r.get("salt")) != salt:
            return False
    return True


def run_fanout(layout, fi, existing, cfg_sha):
    global requests_used
    salt = make_salt(BASE_SEEDS[layout] + fi * 1000)
    P = salted(salt, shared_body())
    body = shared_body()

    # warm probe for A/C (shared prefix)
    shared_prefix_resident = None
    warm_probe_prompt = 0
    warm_probe_cached = 0
    cold_insert_cached = None
    if layout in ("A", "C"):
        # cold insert
        pp, pc, _tt, _st = chat_once([{"role": "user", "content": P}])
        cold_insert_cached = pc
        # warm probe (up to 3)
        for attempt in range(3):
            wp, wc, _tt, _st = chat_once([{"role": "user", "content": P}])
            warm_probe_prompt = wp
            warm_probe_cached = wc
            if wc > 0:
                break
        shared_prefix_resident = warm_probe_cached > 0

    prompts = arm_prompts(layout, P)
    for k in range(1, K + 1):
        if fanout_branches_done(existing, layout, fi, salt) and (layout, fi, k) in existing:
            # already have this branch with matching salt
            row = existing[(layout, fi, k)]
            if str(row.get("salt")) == salt:
                continue
        if (layout, fi, k) in existing and str(existing[(layout, fi, k)].get("salt")) == salt:
            continue
        text = prompts[k - 1]
        prompt, cached, ttft, status = chat_once([{"role": "user", "content": text}])
        row = {
            "unit": "G5",
            "layout": layout,
            "arm": layout,
            "fanout_index": fi,
            "branch_index": k,
            "stack": STACK,
            "config_id": CONFIG_ID,
            "config_sha256": cfg_sha,
            "salt": salt,
            "chars": len(text),
            "prompt_tokens": prompt,
            "cached_tokens": cached,
            "uncached": prompt - cached,
            "uncached_tokens": prompt - cached,
            "status": status,
            "ttft_ms": round(ttft, 1),
            "shared_prefix_resident": shared_prefix_resident if layout in ("A", "C") else None,
            "warm_probe_prompt_tokens": warm_probe_prompt if layout in ("A", "C") else 0,
            "warm_probe_cached_tokens": warm_probe_cached if layout in ("A", "C") else 0,
            "cold_insert_cached_tokens": cold_insert_cached if layout in ("A", "C") else None,
            "ts_utc": utc_now(),
            "request_index": requests_used,
        }
        append_row(row)
        existing[(layout, fi, k)] = row
        print(f"L{layout} f{fi} b{k} status={status} prompt={prompt} cached={cached} uncached={prompt-cached} resident={shared_prefix_resident}", flush=True)


def main():
    global lock_handle
    cfg_sha = config_sha256()
    existing = load_existing()
    handle, waited = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
    lock_handle = handle
    try:
        for layout in LAYOUTS:
            for fi in range(1, FANOUTS + 1):
                if fanout_branches_done(existing, layout, fi, make_salt(BASE_SEEDS[layout] + fi * 1000)):
                    # verify salt matches; if yes skip probe too
                    salt = make_salt(BASE_SEEDS[layout] + fi * 1000)
                    if fanout_branches_done(existing, layout, fi, salt):
                        print(f"SKIP L{layout} f{fi} (already complete)", flush=True)
                        continue
                run_fanout(layout, fi, existing, cfg_sha)
                if requests_used >= INTERNAL_CAP:
                    raise RuntimeError("internal cap reached")
        # analysis
        import subprocess
        subprocess.run([sys.executable, str(CELL_DIR / "g5_analyze.py"),
                        "--rows", str(ROWS_PATH), "--out", str(ANALYSIS_PATH)], check=True)
        analysis = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
        # handoff
        handoff = {
            "unit": "G5",
            "status": "done" if analysis.get("g5_closed") else "partial",
            "artifacts": [
                "experiments/context-cache/cells/G5/rows.jsonl",
                "experiments/context-cache/cells/G5/analysis.json",
                "experiments/context-cache/cells/G5/g5_cell.py",
                "experiments/context-cache/cells/G5/g5_analyze.py",
                "orchestration/units/G5.md",
            ],
            "evidence": {
                "requests_used": requests_used,
                "n_rows": analysis["n_rows"],
                "B_over_A_mean": analysis["ratios"]["B_over_A"]["mean"],
                "B_over_A_ci95": [analysis["ratios"]["B_over_A"]["ci95_low"],
                                  analysis["ratios"]["B_over_A"]["ci95_high"]],
                "C_over_A_mean": analysis["ratios"]["C_over_A"]["mean"],
                "warm_hit_fraction_A": analysis["layouts"]["A"]["warm_hit_fraction"],
                "warm_hit_fraction_C": analysis["layouts"]["C"]["warm_hit_fraction"],
                "any_missed_after_serialisation": analysis["any_missed_after_serialisation"],
                "g5_closed": analysis["g5_closed"],
                "commands": [
                    ".venv/bin/python experiments/context-cache/cells/G5/g5_cell.py",
                    ".venv/bin/python experiments/context-cache/cells/G5/g5_analyze.py",
                ],
            },
            "blocker": "",
            "next_unit_hint": "G5 measured fan-out ratio" + (" closed" if analysis.get("g5_closed") else " narrowed"),
            "write_paths": [
                "experiments/context-cache/cells/G5/rows.jsonl",
                "experiments/context-cache/cells/G5/analysis.json",
                "experiments/context-cache/cells/G5/g5_cell.py",
                "experiments/context-cache/cells/G5/g5_analyze.py",
                "orchestration/handoffs/G5.json",
                "orchestration/units/G5.md",
            ],
        }
        HANDOFF_PATH.parent.mkdir(parents=True, exist_ok=True)
        HANDOFF_PATH.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
        # unit card
        UNIT_CARD_PATH.parent.mkdir(parents=True, exist_ok=True)
        UNIT_CARD_PATH.write_text(
            "# G5 — Fan-out ratio (race-free)\n\n"
            "Measured fan-out ratio with serialised branch dispatch behind cache insert.\n"
            "Command: `.venv/bin/python experiments/context-cache/cells/G5/g5_cell.py`\n",
            encoding="utf-8",
        )
        print("DONE " + json.dumps(handoff["evidence"]), flush=True)
    except BaseException as exc:  # noqa: BLE001
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        try:
            partial = {
                "unit": "G5",
                "status": "partial",
                "artifacts": ["experiments/context-cache/cells/G5/rows.jsonl"],
                "evidence": {"requests_used": requests_used, "traceback_tail": tb[-2000:]},
                "blocker": str(exc),
                "next_unit_hint": "inspect traceback",
                "write_paths": ["experiments/context-cache/cells/G5/rows.jsonl", "orchestration/handoffs/G5.json"],
            }
            HANDOFF_PATH.parent.mkdir(parents=True, exist_ok=True)
            HANDOFF_PATH.write_text(json.dumps(partial, indent=2) + "\n", encoding="utf-8")
        except Exception:
            pass
        sys.exit(1)
    finally:
        if lock_handle is not None:
            release_lock(lock_handle)


if __name__ == "__main__":
    main()
