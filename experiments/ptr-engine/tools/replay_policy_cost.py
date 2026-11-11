#!/usr/bin/env python3
"""Replay a real session's content stream through each context policy and price it.

Zero requests. The session transcript supplies the *content* (user turns, assistant
text, tool calls, tool results); this tool supplies the *policy* and the cache model.

The cache model is the point. A prompt is a list of blocks; the cache hit on a turn is
the longest common prefix with the previous turn's prompt, in tokens. A policy that
rewrites an early block (a summary replacing the journal) breaks the prefix and pays a
re-prefill of everything after it. A policy that only appends does not.

Usage:
    python3 tools/replay_policy_cost.py --session <path.jsonl> [--window 131072]
        [--policy none|compact|mask|pins|pins-recency] [--json]

Policies
    none          full history, FIFO-truncated from the front at the window
    compact       at 70% of the window, replace the journal with a fixed-size summary
    mask          replace tool results older than MASK_AFTER turns with a placeholder
    pins          at 70% of the window, drop the journal; keep L0 + PINS + recent turns
    pins-recency  pins, plus a small ACTIVE line at the tail every turn

Cost is reported in prompt tokens, split into cached and billed. On the Occamy endpoint
a cached token is billed at zero (`billed_of`, score_longrun.py:144-190), so
`billed` is the cost column; `cached` is reported so the same run can be re-priced at
any provider's read multiplier.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

# --- constants, all stated so a reader can re-derive them -------------------

CHARS_PER_TOKEN = 3.122  # measured median on the 871-turn session (growth method)
FOLD_AT = 0.70  # fraction of the window that triggers a fold
SUMMARY_TOKENS = 1_200  # opencode-cache-compact's summaryMaxTokens
PIN_TOKENS = 850  # goal 50 + constraints 200 + decisions 300 + facts 300
ACTIVE_TOKENS = 25  # one ACTIVE line
MASK_PLACEHOLDER_TOKENS = 20  # "[masked: N tokens]"
MASK_AFTER = 8  # turns after which a tool result is masked
KEEP_RECENT = 2  # turns kept verbatim after a fold


def tokens(chars: int) -> int:
    return max(1, round(chars / CHARS_PER_TOKEN))


def load_turns(path: Path) -> tuple[int, list[dict]]:
    """Return (L0 tokens, turns). Each turn is {kind, tokens} in prompt order.

    `kind` is one of user|assistant|tool. Thinking content is excluded: it is not
    re-sent in the prompt, and including it inflates the estimate.
    """
    turns: list[dict] = []
    pending: list[dict] = []
    first_prompt = None
    first_chars = 0

    for line in path.open():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = obj.get("message") or {}
        if not msg:
            continue
        role = msg.get("role")
        chars = 0
        for block in msg.get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "thinking":
                continue
            for key in ("text", "arguments"):
                value = block.get(key)
                if isinstance(value, str):
                    chars += len(value)
                elif isinstance(value, dict):
                    chars += len(json.dumps(value))
        if role == "assistant":
            usage = msg.get("usage") or {}
            prompt = (usage.get("input") or 0) + (usage.get("cacheRead") or 0)
            if first_prompt is None and prompt:
                first_prompt = prompt
                first_chars = sum(t["tokens"] for t in pending) * CHARS_PER_TOKEN
            turns.extend(pending)
            turns.append({"kind": "assistant", "tokens": tokens(chars)})
            pending = []
        else:
            kind = "tool" if role == "toolResult" else "user"
            pending.append({"kind": kind, "tokens": tokens(chars)})
    turns.extend(pending)

    if first_prompt is None:
        raise SystemExit(f"no usage rows in {path}")
    l0 = max(0, first_prompt - round(first_chars / CHARS_PER_TOKEN))
    return l0, turns


def lcp(a: list[tuple[str, int]], b: list[tuple[str, int]]) -> int:
    """Longest common prefix length in tokens, block-aligned."""
    total = 0
    for (aid, at), (bid, bt) in zip(a, b):
        if aid != bid or at != bt:
            break
        total += at
    return total


def simulate(l0: int, turns: list[dict], window: int, policy: str) -> dict:
    fold_at = int(window * FOLD_AT)
    journal: list[dict] = []
    pins: list[tuple[str, int]] = []
    folds = 0
    prev: list[tuple[str, int]] = []
    rows = []
    total_prompt = total_cached = total_billed = 0
    reprefill = 0
    summary_billed = 0  # the extra request a fold needs when the policy summarises

    for index, turn in enumerate(turns):
        journal.append(turn)

        if policy == "none":
            blocks = [("L0", l0)] + [(f"t{i}", t["tokens"]) for i, t in enumerate(journal)]
            # FIFO truncate from the front until it fits
            while sum(t for _, t in blocks) > window and len(blocks) > 2:
                blocks.pop(1)
        elif policy == "compact":
            blocks = [("L0", l0)] + [(f"t{i}", t["tokens"]) for i, t in enumerate(journal)]
            if sum(t for _, t in blocks) > fold_at:
                folds += 1
                pre_fold = sum(t for _, t in blocks)
                keep = journal[-KEEP_RECENT:]
                journal = keep
                blocks = (
                    [("L0", l0), (f"summary{folds}", SUMMARY_TOKENS)]
                    + [(f"t{i}", t["tokens"]) for i, t in enumerate(journal)]
                )
                # The summariser reads the whole pre-fold prompt and writes SUMMARY_TOKENS
                # out. That request is a fresh read, not a cache hit.
                summary_billed += pre_fold + SUMMARY_TOKENS
        elif policy == "mask":
            blocks = [("L0", l0)]
            for i, t in enumerate(journal):
                age = len(journal) - i
                if t["kind"] == "tool" and age > MASK_AFTER:
                    blocks.append((f"t{i}", MASK_PLACEHOLDER_TOKENS))
                else:
                    blocks.append((f"t{i}", t["tokens"]))
            while sum(t for _, t in blocks) > window and len(blocks) > 2:
                blocks.pop(1)
        elif policy in ("pins", "pins-recency"):
            if not pins:
                pins = [("P1", 50), ("P2", 200), ("P3", 300), ("P4", 300)]
            blocks = [("L0", l0)] + pins + [(f"t{i}", t["tokens"]) for i, t in enumerate(journal)]
            if sum(t for _, t in blocks) > fold_at:
                folds += 1
                journal = journal[-KEEP_RECENT:]
                blocks = (
                    [("L0", l0)]
                    + pins
                    + [(f"fold{folds}", 12)]
                    + [(f"t{i}", t["tokens"]) for i, t in enumerate(journal)]
                )
            if policy == "pins-recency":
                blocks.append((f"active{index}", ACTIVE_TOKENS))
        else:
            raise SystemExit(f"unknown policy {policy!r}")

        prompt = sum(t for _, t in blocks)
        cached = lcp(prev, blocks)
        billed = prompt - cached
        if prev and cached < sum(t for _, t in prev):
            reprefill += sum(t for _, t in prev) - cached
        rows.append({"turn": index + 1, "prompt": prompt, "cached": cached, "billed": billed})
        total_prompt += prompt
        total_cached += cached
        total_billed += billed
        prev = blocks

    return {
        "policy": policy,
        "turns": len(turns),
        "l0": l0,
        "folds": folds,
        "total_prompt": total_prompt,
        "total_cached": total_cached,
        "total_billed": total_billed,
        "summary_billed": summary_billed,
        "total_cost": total_billed + summary_billed,
        "cache_hit": round(total_cached / total_prompt, 4) if total_prompt else 0.0,
        "reprefill": reprefill,
        "max_prompt": max((r["prompt"] for r in rows), default=0),
        "median_prompt": int(statistics.median([r["prompt"] for r in rows])) if rows else 0,
        "rows": rows,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True, type=Path)
    ap.add_argument("--window", type=int, default=131_072)
    ap.add_argument("--policy", default="all")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--rows", action="store_true", help="include per-turn rows in --json output")
    args = ap.parse_args(argv)

    l0, turns = load_turns(args.session)
    policies = (
        ["none", "compact", "mask", "pins", "pins-recency"]
        if args.policy == "all"
        else [args.policy]
    )
    results = [simulate(l0, turns, args.window, p) for p in policies]

    if args.json:
        if not args.rows:
            for r in results:
                r.pop("rows", None)
        print(json.dumps({"session": str(args.session), "l0": l0, "results": results}, indent=2))
        return 0

    print(f"session {args.session.name}  turns={len(turns)}  L0={l0}  window={args.window}")
    print(
        f"{'policy':<14}{'folds':>6}{'prompt':>12}{'cached':>12}{'billed':>12}"
        f"{'summary':>11}{'cost':>12}{'hit':>8}{'max':>9}"
    )
    for r in results:
        print(
            f"{r['policy']:<14}{r['folds']:>6}{r['total_prompt']:>12,}{r['total_cached']:>12,}"
            f"{r['total_billed']:>12,}{r['summary_billed']:>11,}{r['total_cost']:>12,}"
            f"{r['cache_hit']:>8.3f}{r['max_prompt']:>9,}"
        )
    base = next(r for r in results if r["policy"] == "none")
    print("\ncost vs none (billed + summary calls):")
    for r in results:
        if r["policy"] == "none":
            continue
        delta = (r["total_cost"] - base["total_cost"]) / base["total_cost"] * 100
        print(f"  {r['policy']:<14}{delta:+7.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
