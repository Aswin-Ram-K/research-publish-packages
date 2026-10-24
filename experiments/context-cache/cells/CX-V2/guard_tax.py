#!/usr/bin/env python3
"""CX-V2 guard: the null->0 cache coercion the cold-isolation evidence rests on.

Three assertions over the units' own raw-usage files (offline, read-only):

  A1  every usage record whose ``prompt_tokens_details`` is null derives
      cached_tokens == 0  (a null block means "not reported", never "all
      cached").
  A2  the first usage record of every U4 cell derives uncached == prompt -- the
      cold-start contract every cell's turn 1 relies on.
  A3  0 <= cached <= prompt on every record.

Break A1's coercion in ``null_coerce.py`` and this exits 1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELLS = HERE.parent
sys.path.insert(0, str(HERE))

from null_coerce import normalise_cache  # noqa: E402


def rows(path: Path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


u2 = rows(CELLS / "U2" / "u2_raw_usage.jsonl")
u4 = [r for r in rows(CELLS / "U4" / "u4_usage_raw.jsonl") if r.get("usage")]

failures: list[str] = []

# ---- A1: null details must coerce to cached == 0 ---------------------------
null_rows = [("U2", r) for r in u2 if (r.get("usage") or {}).get("prompt_tokens_details") is None]
null_rows += [("U4", r) for r in u4 if (r.get("usage") or {}).get("prompt_tokens_details") is None]
bad_a1 = []
for unit, rec in null_rows:
    prompt, cached = normalise_cache(rec["usage"])
    if cached != 0:
        bad_a1.append((unit, prompt, cached))
if bad_a1:
    failures.append(
        f"A1 null->0 coercion: {len(bad_a1)}/{len(null_rows)} null-details records derived "
        f"cached>0 (first: {bad_a1[:3]})")
print(f"A1 null-details records: {len(null_rows)} "
      f"(U2 {sum(1 for u, _ in null_rows if u == 'U2')}, U4 {sum(1 for u, _ in null_rows if u == 'U4')}); "
      f"derived cached>0: {len(bad_a1)} -> {'FAIL' if bad_a1 else 'ok'}")

# ---- A2: first record of each U4 cell must be a full miss -------------------
first: dict[str, dict] = {}
for rec in u4:
    first.setdefault(rec["cell"], rec)
bad_a2 = []
for cell, rec in sorted(first.items()):
    prompt, cached = normalise_cache(rec["usage"])
    if prompt - cached != prompt:
        bad_a2.append((cell, prompt, cached))
if bad_a2:
    failures.append(
        f"A2 cold-start contract: {len(bad_a2)}/{len(first)} U4 cells' first record derived "
        f"as a cache hit (first: {bad_a2[:3]})")
print(f"A2 U4 cells checked: {len(first)}; first record not a full miss: {len(bad_a2)} "
      f"-> {'FAIL' if bad_a2 else 'ok'}")

# ---- A3: clamp --------------------------------------------------------------
bad_a3 = []
for unit, recs in (("U2", u2), ("U4", u4)):
    for rec in recs:
        prompt, cached = normalise_cache(rec["usage"])
        if not 0 <= cached <= prompt:
            bad_a3.append((unit, prompt, cached))
if bad_a3:
    failures.append(f"A3 clamp: {len(bad_a3)} records violate 0 <= cached <= prompt")
print(f"A3 records checked: {len(u2) + len(u4)}; clamp violations: {len(bad_a3)} "
      f"-> {'FAIL' if bad_a3 else 'ok'}")

if failures:
    print("\nGUARD FAILED")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("\nGUARD PASSED: 3/3")
