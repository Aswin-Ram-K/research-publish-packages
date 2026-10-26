#!/usr/bin/env python3
"""E2 follow-up -- does U15's F advantage (turns 36-40) reproduce?

The main E2 probe reproduced U15's R arm to the token (t19 768, t21 1920,
t36 896, t40 2688 -- identical), but its F arm, live only from turn 30 after
an offline replay, did **not** reproduce U15's F rows: at t36 it matched 768
tokens where U15's F matched 2,048.  R and F then looked the same, which would
make U15's t36-40 "F advantage" an artefact of cache state rather than of the
fork policy.

This script is the control for that: F again, **full warm epoch** (live from
turn 1), fresh salt 2503, same corpus/comaction points/policy.  If F2 t36-38
matches ~2,048 like U15's F, the advantage replicates and is a property of
running F after a warm epoch; if it matches ~768 like E2's cold-start F, U15's
F rows are not reproducible and the advantage has no mechanism to inherit.

38 live requests (t1-t38); the unit cap is 90 and the main probe used 51.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("e2_probe", HERE / "e2_probe.py")
e2 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = e2
spec.loader.exec_module(e2)

from resextract.context import CompactionPolicy  # noqa: E402

U15_ROWS = HERE.parents[0] / "U15" / "rows.jsonl"

e2.ROWS_PATH = HERE / "rows_f2.jsonl"
e2.EVENTS_PATH = HERE / "events_f2.json"
e2.ANALYSIS_PATH = HERE / "analysis_f2.json"
e2.TURNS = 38
e2.ARMS = (
    {
        "arm": "F2",
        "policy": "fork",
        "compaction": CompactionPolicy.FORK,
        "seed": 2503,
        "first_live_turn": 1,
    },
)


def load(path: Path) -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        out[(str(row["arm"]), int(row["turn"]))] = row
    return out


def main() -> int:
    handle, waited = e2.acquire_lock(e2.LOCK_PATH, e2.LOCK_TIMEOUT_S)
    started = time.monotonic()
    try:
        payload = e2.run(
            f"acquired after {waited:.1f}s; pid {e2.os.getpid()}; held for the whole batch",
            waited,
        )
    finally:
        e2.release_lock(handle)
    payload["status"] = "done"
    payload["rows_sha256"] = hashlib.sha256(e2.ROWS_PATH.read_bytes()).hexdigest()
    e2.write_json_atomic(e2.ANALYSIS_PATH, payload)

    f2 = load(e2.ROWS_PATH)
    cold = load(HERE / "rows.jsonl")
    u15 = load(U15_ROWS)
    print("\n=== F epochs at turns 30-40 (U15 F, E2 F cold@30, E2 F2 warm) ===")
    rows_out = []
    for t in range(30, 39):
        rec = {"turn": t}
        for label, src, arm in (
            ("U15F", u15, "F"),
            ("E2F", cold, "F"),
            ("E2F2", f2, "F2"),
        ):
            r = src.get((arm, t))
            if not r:
                continue
            rec[label] = {
                "prompt": r["prompt_tokens"],
                "cached": r["cached_tokens"],
                "uncached": r["uncached"],
                "mod64": r["prompt_mod64"],
                "break": bool(r.get("scheduled_compaction")),
                "prefix_ok": bool(r.get("diff", {}).get("prefix_identical")),
            }
        rows_out.append(rec)
        print(json.dumps(rec))
    payload["f_epoch_comparison"] = rows_out
    payload["elapsed_s"] = round(time.monotonic() - started, 1)
    e2.write_json_atomic(e2.ANALYSIS_PATH, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
