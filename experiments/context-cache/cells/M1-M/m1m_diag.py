#!/usr/bin/env python3
"""M1-M diagnostic — is the truncated-prefix shortfall a first-send artefact?

The main matrix found that a prompt truncated to items 1..165 (8623-8625
tokens), sent immediately after its byte-identical base, recovered only 8192
tokens.  Two questions decide how to read that:

1. Does a **second identical truncation send** recover more?  If yes, the
   shortfall is a first-send/visibility artefact, not a limit of prefix
   matching; if no, a truncated prompt genuinely cannot recover its own head.
2. Does the shortfall scale with length?  Send truncations at ~10,350 tokens
   (items 1..199) as well as at ~8,600 (items 1..165).

Budget: 7 live requests (main matrix used 99 of 120).
Writes only under this cell dir.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))

import m1m_cell as cell  # noqa: E402

DIAG_ROWS = HERE / "diag_rows.jsonl"
DIAG_JSON = HERE / "diag.json"
MAX_TOKENS = 2
GRID = 64


def main() -> int:
    lock = cell.acquire_lock(cell.LOCK_PATH, 300.0)
    requests = 0
    rows: list[dict] = []
    try:
        client = cell.load_chat_client()()
        # base once, then the same truncation sent twice: does the second send
        # recover what the first did not?
        runs = [
            ("trunc_retry_a", 9400, 165, 3),
            ("trunc_retry_b", 9401, 199, 3),
        ]
        for name, seed, trunc_item, sends in runs:
            salt = cell.make_salt(seed)
            bodies = [("base", cell.base_body())]
            for k in range(sends):
                bodies.append((f"trunc{k + 1}", cell.trunc_body(trunc_item)))
            for kind, body in bodies:
                prompt, cached, completion, ttft, wall, status, _ = client.chat(
                    cell.messages_for(body, salt),
                    max_tokens=MAX_TOKENS,
                    thinking=False,
                    stream=True,
                    timeout=120.0,
                )
                requests += 1
                row = {
                    "unit": "M1-M",
                    "diag": name,
                    "trunc_item": trunc_item,
                    "kind": kind,
                    "salt": salt,
                    "request_index": requests,
                    "prompt_tokens": prompt,
                    "cached_tokens": cached,
                    "prompt_mod64": prompt % GRID,
                    "floor64": (prompt // GRID) * GRID,
                    "full_hit": int(cached >= prompt),
                    "grid_hit": int(cached == (prompt // GRID) * GRID),
                    "wall_ms": round(wall, 1),
                    "status": status,
                    "ts_utc": datetime.now(timezone.utc).isoformat(),
                }
                rows.append(row)
                with DIAG_ROWS.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                print(
                    f"{name} {kind:6s} prompt={prompt:6d} cached={cached:6d} "
                    f"floor={row['floor64']:6d} status={status}",
                    flush=True,
                )
    finally:
        cell.release_lock(lock)

    DIAG_JSON.write_text(
        json.dumps({"unit": "M1-M", "requests": requests, "rows": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"requests": requests}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
