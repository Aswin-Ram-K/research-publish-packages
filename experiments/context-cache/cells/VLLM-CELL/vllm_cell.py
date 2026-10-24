#!/usr/bin/env python3
"""VLLM-CELL — a fresh vLLM prefix-cache measurement cell.

Built from the inline spec. Deliberately does not read, import or touch
`cells/R2-VLLM/pmu16_cell.py`, which stays frozen as evidence.

One file. stdlib + requests.

Invariants this file enforces, each with a test that fails when reverted:
  * An absent `prompt_tokens_details` or absent `cached_tokens` yields
    `cached = None`, never 0, and `cache_report = "unavailable"`.
  * A non-200 response raises and writes no row.
  * The four arms must render different bytes (ARMS_IDENTICAL otherwise).
  * Prompts are deterministic: no clock, no randomness, no hash seeding.
"""

import argparse
import hashlib
import json
import os
import sys

import requests

# --------------------------------------------------------------------------
# Prompt construction. Deterministic by construction: derived only from strings
# and integer indices, so two runs render identical bytes.
# --------------------------------------------------------------------------

SCAFFOLD = (
    "You are an offline cache-probe agent working over a transcript.\n"
    "TASK: answer the newest delta. Do not restate the history.\n"
    "OUTPUT CONTRACT: one JSON object per turn with keys "
    "{answer, evidence_ids, confidence}. No prose outside the object.\n"
    "TOOLS: search(query), fetch(fetch_ref), cite(evidence_id), write_json(obj).\n"
)

DELTA_CHARS = 1180
SUMMARY_EVERY = 8
DEFAULT_TURNS = 71
CANARY = "turn-canary-occamy-vllm-cell-0042"


def delta_block(turn):
    """The delta appended at turn `turn`. Length is ~DELTA_CHARS, deterministic."""
    head = "DELTA t=%03d start\n" % turn
    body = ("fact[%03d]  a cache-probe statement about the transcript body. " % turn) * 40
    tail = "\nDELTA t=%03d end" % turn
    return (head + body)[:DELTA_CHARS] + tail


def sha8(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def summarise(text, limit=90):
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "\u2026"


def folded_summary(turn, fold_start):
    """The replacement line for a delta folded into the rolling summary.

    Distinct from a plain clipped summary on purpose: the hybrid arm must really
    compress, not merely relabel, or it is arm A with extra bytes.
    """
    last_line = delta_block(turn).splitlines()[-1]
    return "t%03d | span %03d-%03d | SUMMARY[%d] %s ... %s" % (
        turn, fold_start, turn, SUMMARY_EVERY,
        summarise(" | ".join(delta_block(t)[:24] for t in range(fold_start, turn + 1)), 110),
        last_line)


def body_upto(turn):
    """The growing body: turns 1..turn concatenated, never rewritten."""
    return "".join(delta_block(t) for t in range(1, turn + 1))


def pointer_index(up_to_turn, compacted=False):
    """`id | span | sha8 | summary` lines, one per delta in the body."""
    lines = ["id | span | sha8 | summary"]
    for t in range(1, up_to_turn + 1):
        block = delta_block(t)
        if compacted and t % SUMMARY_EVERY == 0:
            lines.append(folded_summary(t, max(1, t - SUMMARY_EVERY + 1)))
        else:
            lines.append("t%03d | %d | %s | %s" % (t, len(block), sha8(block), summarise(block)))
    return "\n".join(lines)


def render(arm, turn):
    """Render the messages for `arm` at `turn`. Arms MUST differ in bytes."""
    if arm == "R":  # reference: whole body re-sent verbatim, no structure
        text = SCAFFOLD + "HISTORY:\n" + body_upto(turn) + "\n" + CANARY
    elif arm == "A":  # append-only pointer: index + newest delta only
        text = (SCAFFOLD + pointer_index(turn - 1)
                + "\nNEWEST DELTA:\n" + delta_block(turn) + "\n" + CANARY)
    elif arm == "C":  # append-only, delta tagged at its tail: same content + marker
        text = (SCAFFOLD + pointer_index(turn - 1)
                + "\nNEWEST DELTA:\n" + delta_block(turn)
                + "\nTAG[t=%03d sha=%s]\n" % (turn, sha8(delta_block(turn))) + CANARY)
    elif arm == "H":  # hybrid: A, but the index is compacted every SUMMARY_EVERY turns
        # The policy marker is unconditional so H differs from A from turn 1; the
        # compaction itself only bites once a summary boundary is in the index.
        compacted = turn >= SUMMARY_EVERY
        folds = sum(1 for t in range(1, turn) if t % SUMMARY_EVERY == 0) if compacted else 0
        text = (SCAFFOLD + "INDEX (hybrid; folds=%02d):\n" % folds
                + pointer_index(turn - 1, compacted=True)
                + "\nNEWEST DELTA:\n" + delta_block(turn) + "\n" + CANARY)
    else:
        raise ValueError("unknown arm %r" % (arm,))
    return [{"role": "user", "content": text}]


def estimate_tokens(text):
    return len(text) // 4


def fit_budget(messages, budget):
    """Truncate the body to `budget` estimated tokens. Returns (messages, truncated)."""
    text = messages[0]["content"]
    if estimate_tokens(text) <= budget:
        return messages, False
    keep = max(budget * 4, 0)
    head = text[:keep]
    return [{"role": "user", "content": head}], True


# --------------------------------------------------------------------------
# HTTP + row parsing. The parsing is the part that matters.
# --------------------------------------------------------------------------

def parse_row(payload, arm, turn, prompt_sha256, truncated):
    """Build one measured row from a chat-completion payload. Never invents 0."""
    usage = payload.get("usage") or {}
    details = usage.get("prompt_tokens_details")
    prompt_tokens = usage.get("prompt_tokens")

    if not isinstance(details, dict):
        cached, cache_report = None, "unavailable"
    elif details.get("cached_tokens") is None:
        cached, cache_report = None, "unavailable"
    else:
        cached, cache_report = int(details["cached_tokens"]), "reported"

    if prompt_tokens is not None and cached is not None:
        uncached = int(prompt_tokens) - cached
    else:
        uncached = None

    return {
        "arm": arm,
        "turn": turn,
        "prompt_tokens": prompt_tokens,
        "cached_tokens": cached,
        "uncached_tokens": uncached,
        "truncated": truncated,
        "http_status": 200,
        "cache_report": cache_report,
        "prompt_sha256": prompt_sha256,
    }


def post_chat(base_url, model, messages):
    resp = requests.post(
        base_url.rstrip("/") + "/chat/completions",
        json={"model": model, "messages": messages, "max_tokens": 8, "temperature": 0},
        timeout=300,
    )
    if resp.status_code != 200:
        raise RuntimeError("http %d" % resp.status_code)
    return resp.json()


# --------------------------------------------------------------------------
# Guards + run loop
# --------------------------------------------------------------------------

ARMS = ("R", "A", "C", "H")


def assert_arms_distinct(probe_turns=(1, 20)):
    """Refuse to measure if any two arms render byte-identical prompts."""
    for turn in probe_turns:
        rendered = {arm: render(arm, turn)[0]["content"] for arm in ARMS}
        seen = {}
        for arm, text in rendered.items():
            if text in seen:
                raise RuntimeError("ARMS_IDENTICAL")
            seen[text] = arm


def run(base_url, model, arms, turns, budget, out, warmup):
    assert_arms_distinct()
    os.makedirs(out, exist_ok=True)
    rows_path = os.path.join(out, "rows.jsonl")

    if warmup:
        post_chat(base_url, model, render("R", 1))  # the scaffold, not counted

    written = 0
    with open(rows_path, "a", encoding="utf-8") as fh:
        for arm in arms:
            for turn in range(1, turns + 1):
                messages, truncated = fit_budget(render(arm, turn), budget)
                text = messages[0]["content"]
                payload = post_chat(base_url, model, messages)
                row = parse_row(payload, arm, turn, hashlib.sha256(text.encode()).hexdigest(),
                                truncated)
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                written += 1
    return written, rows_path


def main(argv=None):
    p = argparse.ArgumentParser(description="vLLM prefix-cache measurement cell")
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--arm", default="all", choices=("all",) + ARMS)
    p.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    p.add_argument("--budget", type=int, default=32768)
    p.add_argument("--out", required=True)
    p.add_argument("--warmup", action="store_true")
    p.add_argument("--dry-run", action="store_true",
                   help="render + guard only; no HTTP")
    args = p.parse_args(argv)

    arms = ARMS if args.arm == "all" else (args.arm,)

    if args.dry_run:
        assert_arms_distinct()
        for turn in (1, 20):
            sizes = {a: len(render(a, turn)[0]["content"]) for a in ARMS}
            print("turn %2d chars %s" % (turn, sizes))
        return 0

    written, path = run(args.base_url, args.model, arms, args.turns, args.budget,
                        args.out, args.warmup)
    print("wrote %d rows -> %s" % (written, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
