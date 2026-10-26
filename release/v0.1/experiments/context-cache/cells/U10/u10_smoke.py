#!/usr/bin/env python3
"""U10 smoke test: prove an exact 1024 cell is reachable and a repeat hits.

Costs about 6 live requests (counted against the unit's 160-request bound).
"""
from __future__ import annotations

import functools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import u10_cell as cell  # noqa: E402

cell.MAX_REQUESTS = 6
cell.REPS = 2
chat = cell.client_mod.ChatClient()
cell.SEND = functools.partial(chat.chat, max_tokens=2, thinking=False, stream=True, timeout=180.0)

info = cell.run_cell(1024)
print(json.dumps(info))
for r in cell.ROWS:
    print(r.get("role"), r.get("prompt_tokens"), r.get("tail"), r.get("cached_tokens"),
          r.get("expected_cached"), r.get("ttft_ms"))
print("requests=", cell.USED["total"])
