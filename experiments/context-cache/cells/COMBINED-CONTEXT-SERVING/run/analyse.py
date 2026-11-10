#!/usr/bin/env python3
"""Recompute arm cost and the promotion gate from the recorded rows.

Reads rows as raw as possible: every number is recomputed from prompt_tokens,
cached_tokens and completion_tokens in the row; grader verdicts are read from
the graded JSON the driver stored beside each row. Nothing is trusted from a
prior summary.

Quality first, then cost:
  * quality gate: an arm may not have a lower grader-verified rate than arm A.
  * cost gate: cost per verified success must fall by >= 10 % against arm A.
  * if no arm verifies any call, the gate is UNDEFINED and no promotion happens.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
GATE_MARGIN = 0.10


def load_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def uncaught_tokens(row: dict) -> int:
    """Uncached input for cost purposes.

    Uses the derived value the adapter recorded; when the engine reported no
    cache details at all, the whole prompt was prefill, so prompt_tokens is the
    honest figure. Never substitutes a silent zero for an unknown.
    """
    derived = (row.get("derived") or {}).get("uncached_prefill_tokens_from_prompt_minus_cached")
    if derived is not None:
        return int(derived)
    cached = row.get("cached_tokens")
    prompt = row.get("prompt_tokens")
    if prompt is None:
        raise ValueError(f"row {row.get('send_id')} has no prompt_tokens")
    if cached is None:
        return int(prompt)
    return int(prompt) - int(cached)


def verified(row: dict) -> bool:
    if "verified_success" in row:
        return bool(row["verified_success"])
    graded_path = row.get("graded_path")
    if graded_path and Path(graded_path).is_file():
        return bool(json.loads(Path(graded_path).read_text()).get("verified_success"))
    raise ValueError(f"row {row.get('send_id')} carries no grader verdict")


def summarise(rows: list[dict]) -> dict[str, dict]:
    by_arm: dict[str, list[dict]] = {}
    for row in rows:
        by_arm.setdefault(row["arm"], []).append(row)
    out: dict[str, dict] = {}
    for arm, rs in sorted(by_arm.items()):
        uncached = [uncaught_tokens(r) for r in rs]
        completion = [int(r.get("completion_tokens") or 0) for r in rs]
        reasoning = [
            int((r.get("usage_raw") or {}).get("reasoning_tokens") or 0) for r in rs
        ]
        ok = [verified(r) for r in rs]
        cost = [u + c for u, c in zip(uncached, completion)]
        reported = [r for r in rs if r.get("cached_tokens") is not None]
        out[arm] = {
            "calls": len(rs),
            "verified": sum(ok),
            "verified_rate": round(sum(ok) / len(rs), 4) if rs else 0.0,
            "prompt_tokens": sum(int(r.get("prompt_tokens") or 0) for r in rs),
            "cached_tokens_reported": sum(
                int(r["cached_tokens"]) for r in reported
            ),
            "rows_without_cache_report": len(rs) - len(reported),
            "cache_share_reported_only": (
                round(
                    sum(int(r["cached_tokens"]) for r in reported)
                    / sum(int(r["prompt_tokens"] or 0) for r in reported),
                    4,
                )
                if reported
                else None
            ),
            "uncached_input_tokens": sum(uncached),
            "completion_tokens": sum(completion),
            "reasoning_tokens": sum(reasoning),
            "combined_proxy_tokens": sum(cost),
            "median_combined_proxy": int(statistics.median(cost)) if cost else 0,
            "errors": sum(1 for r in rs if r.get("status") != 200),
            "empty_text": sum(1 for r in rs if not (r.get("text") or "").strip()),
        }
    return out


def gate(summary: dict[str, dict], baseline: str = "A") -> dict:
    if baseline not in summary:
        return {"verdict": "no-baseline", "reason": f"arm {baseline} absent"}
    base = summary[baseline]
    if base["verified"] == 0:
        return {
            "verdict": "undefined-no-verified-success",
            "reason": (
                "arm A verified no call, so cost per verified success has no "
                "denominator; the gate cannot pass"
            ),
            "arms": summary,
        }
    verdicts = {}
    for arm, s in summary.items():
        if arm == baseline:
            continue
        quality_ok = s["verified_rate"] >= base["verified_rate"]
        if s["verified"] == 0:
            cost_ok = False
            per_verified = None
        else:
            per_verified = s["combined_proxy_tokens"] / s["verified"]
            base_per = base["combined_proxy_tokens"] / base["verified"]
            cost_ok = per_verified <= base_per * (1 - GATE_MARGIN)
        verdicts[arm] = {
            "quality_ok": quality_ok,
            "cost_ok": cost_ok,
            "cost_per_verified": None if per_verified is None else round(per_verified, 1),
            "baseline_cost_per_verified": round(
                base["combined_proxy_tokens"] / base["verified"], 1
            ),
            "promote": bool(quality_ok and cost_ok),
        }
    winners = [a for a, v in verdicts.items() if v["promote"]]
    return {
        "verdict": "promote" if winners else "no-promotion",
        "margin": GATE_MARGIN,
        "baseline": baseline,
        "arms": verdicts,
        "promoted": winners,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", required=True, help="notes JSON path")
    ap.add_argument("--baseline", default="A")
    args = ap.parse_args()

    rows = load_rows(Path(args.rows))
    if not rows:
        raise SystemExit("no rows to analyse")
    summary = summarise(rows)
    heldout_tasks = {"T3.heldout", "T4.heldout"}
    heldout = [r for r in rows if r.get("task") in heldout_tasks]
    result = {"rows_path": args.rows, "calls": len(rows), "arms": summary,
              "gate": gate(summary, args.baseline)}
    if heldout:
        hsum = summarise(heldout)
        result["heldout"] = {
            "tasks": sorted(heldout_tasks),
            "calls": len(heldout),
            "arms": hsum,
            "gate": gate(hsum, args.baseline),
        }
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({a: {k: s[k] for k in ("calls", "verified", "combined_proxy_tokens", "empty_text")}
                      for a, s in summary.items()}, indent=1))
    verdict = result["gate"]
    print("gate:", verdict["verdict"], "promoted:", verdict.get("promoted"))
    for arm, v in (verdict.get("arms") or {}).items():
        if isinstance(v, dict):
            print(f"  {arm}: quality_ok={v['quality_ok']} cost_ok={v['cost_ok']} "
                  f"per_verified={v['cost_per_verified']} vs {v['baseline_cost_per_verified']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
