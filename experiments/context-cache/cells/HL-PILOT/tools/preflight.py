#!/usr/bin/env python3
"""Preflight: what does this server actually report about cache reuse?

Three requests, one frozen envelope, offline-safe by default. The question is
narrow and is *not* researchable: SGLang's own docs say the usage block may
carry ``prompt_tokens_details``, but whether *this* build emits it on a cold
request, on a repeat, and after a first-token rewrite is a fact about our
stack. The STATE-CLIFF rows cannot answer it — they recorded ``usage: null``
and a numeric 0, so absence and a genuine zero are indistinguishable there.

Usage:
    python3 preflight.py            # live; takes the occamy lock
    python3 preflight.py --dry-run  # prints the plan, sends nothing
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import sys
import time
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
WT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(CELL / "tools"))

from adapter import Adapter  # noqa: E402

LOCK = WT / "experiments/context-cache/.occamy.lock"
ENVELOPE = CELL / "envelopes/PREFLIGHT.json"
ROWS = CELL / "rows/preflight.jsonl"
SUMMARY = CELL / "notes/preflight-summary.json"

PAD = (
    "The pointer engine resolves a reference to a revision-pinned body. "
    "A refusal that is not recorded is a refusal that cannot be audited. "
) * 24


def prompt(salt: str, first_token: str = "ALPHA") -> list[dict[str, str]]:
    return [
        {"role": "system", "content": f"probe={salt}\nYou are a terse checker."},
        {
            "role": "user",
            "content": f"{first_token} sentinel. {PAD}\nReport the sentinel word only.",
        },
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    env = json.loads(ENVELOPE.read_text())
    if env.get("retrospective"):
        raise SystemExit("envelope is marked retrospective; refusing")
    salt = "pf-" + hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:12]
    plan = [
        ("cold", prompt(salt)),
        ("identical_repeat", prompt(salt)),
        ("first_token_rewrite", prompt(salt, first_token="BETA")),
    ]
    if args.dry_run:
        for name, msgs in plan:
            body = json.dumps(msgs, sort_keys=True).encode()
            print(f"{name:22s} bytes={len(body)} sha256={hashlib.sha256(body).hexdigest()[:16]}")
        print(f"planned_calls={len(plan)} cap={env['budgets']['max_calls']}")
        return 0

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+") as lock:
        t0 = time.time()
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() - t0 > 300:
                    raise SystemExit("lock not free after 300s")
                time.sleep(1)
        print(f"lock acquired after {time.time() - t0:.1f}s")

        adapter = Adapter()
        rows = []
        for step, (name, msgs) in enumerate(plan, start=1):
            row = adapter.chat(
                msgs,
                max_tokens=8,
                temperature=0.0,
                seed=7,
                run_id=env["run_id"],
                arm="PREFLIGHT",
                task_id=name,
                step=step,
            )
            rows.append(row)
            print(
                f"{name:22s} status={row['status']} prompt={row['prompt_tokens']} "
                f"cached={row['cached_tokens']} reported={row['cache_usage_reported']} "
                f"ttft={row['ttft_ms']}"
            )

        ROWS.parent.mkdir(parents=True, exist_ok=True)
        with ROWS.open("a") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")

        by_name = {row["task_id"]: row for row in rows}
        summary = {
            "schema": "typed-context-pilot.preflight/1",
            "run_id": env["run_id"],
            "salt": salt,
            "calls": len(rows),
            "usage_keys_observed": sorted(
                {k for row in rows for k in (row.get("usage_raw") or {})}
            ),
            "details_shape": {
                name: row.get("usage_raw", {}).get("prompt_tokens_details")
                for name, row in by_name.items()
            },
            "cached_tokens": {n: r["cached_tokens"] for n, r in by_name.items()},
            "prompt_tokens": {n: r["prompt_tokens"] for n, r in by_name.items()},
            "verdict": {},
        }
        cold = by_name["cold"]
        repeat = by_name["identical_repeat"]
        rewrite = by_name["first_token_rewrite"]
        summary["verdict"] = {
            "cold_reports_no_reuse": cold["cached_tokens"] in (0, None),
            "repeat_hits": bool(repeat["cached_tokens"]),
            "rewrite_first_token_misses": rewrite["cached_tokens"] in (0, None),
            "absence_is_distinguishable": cold["cache_usage_reported"]
            != repeat["cache_usage_reported"],
        }
        SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        print(json.dumps(summary["verdict"], indent=1))
        print(f"details_shape={summary['details_shape']}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
