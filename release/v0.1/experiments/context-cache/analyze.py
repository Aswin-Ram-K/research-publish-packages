"""Pure analysis over ``CacheRow`` lists.  No file I/O except ``main()``.

The "64-token grid" is the measured fact this module encodes: SGLang serves
prefixes on 64-token blocks, so ``uncached == prompt_tokens % 64``.  Any
residue is *tax* -- tokens re-prefilled that should have been cached.  The
error should be zero on a clean stream; a nonzero value means the harness,
not the server, broke the prefix.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

from resextract.context.meter import CacheRow, rows_from_jsonl

GRID = 64


def tax_error(rows: Iterable[CacheRow]) -> int:
    """Total absolute deviation of ``uncached`` from ``prompt_tokens % 64``."""

    return sum(abs(row.uncached - (row.prompt_tokens % GRID)) for row in rows)


def tax_error_detail(rows: Iterable[CacheRow]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        expected = row.prompt_tokens % GRID
        if row.uncached != expected:
            out.append(
                {
                    "cell": row.cell,
                    "rep": row.rep,
                    "turn": row.turn,
                    "prompt_tokens": row.prompt_tokens,
                    "uncached": row.uncached,
                    "expected": expected,
                    "error": row.uncached - expected,
                }
            )
    return out


def hit_rate(rows: Iterable[CacheRow], weighted: bool = True) -> float:
    """Cached fraction of prompt tokens.

    ``weighted=True`` -> sum(cached)/sum(prompt); ``False`` -> mean of the
    per-row rates (short turns count as much as long ones).
    """

    rows = list(rows)
    if not rows:
        return 0.0
    if weighted:
        total_prompt = sum(row.prompt_tokens for row in rows)
        if total_prompt <= 0:
            return 0.0
        return sum(row.cached_tokens for row in rows) / total_prompt
    per_row = [
        (row.cached_tokens / row.prompt_tokens) if row.prompt_tokens else 0.0
        for row in rows
    ]
    return sum(per_row) / len(per_row)


def per_turn_series(rows: Iterable[CacheRow]) -> list[dict[str, Any]]:
    """One dict per row, ordered by (cell, rep, turn)."""

    ordered = sorted(rows, key=lambda r: (r.cell, r.rep, r.turn))
    return [
        {
            "cell": row.cell,
            "policy": row.policy,
            "rep": row.rep,
            "turn": row.turn,
            "prompt_tokens": row.prompt_tokens,
            "cached_tokens": row.cached_tokens,
            "uncached": row.uncached,
            "hit_rate": (row.cached_tokens / row.prompt_tokens) if row.prompt_tokens else 0.0,
            "ttft_ms": row.ttft_ms,
            "evicted": row.evicted,
        }
        for row in ordered
    ]


def compaction_effect(rows: Iterable[CacheRow]) -> dict[str, Any]:
    """Effect of prefix breaks (a changed ``prefix_sha256``) on TTFT and cache.

    A break is a row whose rendered-prefix digest differs from the previous
    row in the same (cell, rep): exactly what compaction or preamble mutation
    causes.  Reported as before/after TTFT means plus the cached tokens on the
    first row after the break.
    """

    grouped: dict[tuple[str, int], list[CacheRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.cell, row.rep)].append(row)

    before: list[float] = []
    after: list[float] = []
    cached_after: list[int] = []
    breaks = 0
    for series in grouped.values():
        series.sort(key=lambda r: r.turn)
        for prev, cur in zip(series, series[1:]):
            if cur.prefix_sha256 != prev.prefix_sha256:
                breaks += 1
                before.append(prev.ttft_ms)
                after.append(cur.ttft_ms)
                cached_after.append(cur.cached_tokens)

    return {
        "prefix_breaks": breaks,
        "cells": len(grouped),
        "ttft_before_ms": statistics.fmean(before) if before else 0.0,
        "ttft_after_ms": statistics.fmean(after) if after else 0.0,
        "delta_ttft_ms": (statistics.fmean(after) - statistics.fmean(before)) if before else 0.0,
        "cached_after_mean": statistics.fmean(cached_after) if cached_after else 0.0,
    }


def summary_table(rows: Iterable[CacheRow]) -> list[dict[str, Any]]:
    """Per-cell aggregate, one row per (cell, arm, policy)."""

    grouped: dict[tuple[str, str, str], list[CacheRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.cell, row.arm, row.policy)].append(row)

    table: list[dict[str, Any]] = []
    for (cell, arm, policy), group in sorted(grouped.items()):
        prompts = [r.prompt_tokens for r in group]
        table.append(
            {
                "cell": cell,
                "arm": arm,
                "policy": policy,
                "rows": len(group),
                "reps": len({r.rep for r in group}),
                "mean_prompt_tokens": statistics.fmean(prompts) if prompts else 0.0,
                "cached_tokens": sum(r.cached_tokens for r in group),
                "hit_rate": hit_rate(group, weighted=True),
                "mean_ttft_ms": statistics.fmean([r.ttft_ms for r in group]),
                "tax_error": tax_error(group),
                "evicted": any(r.evicted for r in group),
            }
        )
    return table


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: analyze.py <rows.jsonl>", file=sys.stderr)
        return 2
    rows = rows_from_jsonl(Path(argv[0]))
    report = {
        "rows": len(rows),
        "tax_error": tax_error(rows),
        "hit_rate": hit_rate(rows),
        "compaction": compaction_effect(rows),
        "summary": summary_table(rows),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
