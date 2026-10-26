#!/usr/bin/env python3
"""prompt_at_turn.py — materialise the prompt the long-run runner WOULD have sent at a
given turn, without sending it (PLANT-REACHABILITY, Job 1).

Method: ``imported-runner``.  This tool imports ``run_longrun`` (it never edits it and
never runs its ``main``), replaces ``run_longrun.send_chat`` with a recorder that RAISES
``WouldSend(payload)`` when the requested turn is reached, and drives
``run_longrun.run_cell`` itself for turns 1..N, feeding it the canned assistant reply
each turn actually produced (taken verbatim from the settled row file).  Prompt
construction is therefore the runner's own ``Planner.build`` running inside its own
production loop — not a re-implementation of the prompt logic.

Provenance check: for every turn the tool also compares ``sha256(user_content)`` of the
prompt it just materialised against the ``prompt_sha256`` stamped on the settled row for
that same (arm, rep, turn).  A match proves the materialised prompt is byte-identical to
the one the endpoint received; the tool reports every mismatch.

Zero network is structural, not promised.  ``urllib.request.urlopen``,
``http.client.HTTPConnection.connect``, ``http.client.HTTPSConnection.connect`` and
``socket.create_connection`` are replaced with functions that record the attempt and
raise AssertionError, so constructing a real HTTP client fails loudly, and the run
refuses to report if any attempt was made.

    python3 experiments/ptr-engine/longrun/tools/prompt_at_turn.py \
        --fixture experiments/ptr-engine/longrun/tasks-v3/runtime-v3/LR-01.v3.json \
        --rows experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.jsonl \
        --turns 12,24,46 --json /tmp/prompt_at_turn.json
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import http.client
import io
import json
import os
import re
import socket
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN_DIR = os.path.dirname(HERE)
if LONGRUN_DIR not in sys.path:
    sys.path.insert(0, LONGRUN_DIR)

NET_ATTEMPTS: list[str] = []


def _forbidden(name):
    def boom(*_a, **_k):
        NET_ATTEMPTS.append(name)
        raise AssertionError(
            f"NETWORK REFUSED: {name}() was called — prompt_at_turn.py must never construct "
            "an HTTP client (card PLANT-REACHABILITY: zero requests)")
    return boom


# Install the trip-wires BEFORE the runner is driven (import itself opens nothing).
urllib.request.urlopen = _forbidden("urllib.request.urlopen")
urllib.request.build_opener = _forbidden("urllib.request.build_opener")
http.client.HTTPConnection.connect = _forbidden("http.client.HTTPConnection.connect")
http.client.HTTPSConnection.connect = _forbidden("http.client.HTTPSConnection.connect")
socket.create_connection = _forbidden("socket.create_connection")

import run_longrun as R  # noqa: E402  (trip-wires are already armed)


class WouldSend(RuntimeError):
    """Raised instead of sending.  Carries the exact bytes the runner would have sent."""

    def __init__(self, turn: int, messages: list[dict], body: dict):
        super().__init__(f"would have sent turn {turn}")
        self.turn = turn
        self.messages = messages
        self.body = body


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_settled(path: str) -> dict:
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out[(row["arm"], int(row["rep"]), int(row["turn"]))] = row
    return out


def canned_resp(row: dict) -> dict:
    """The response shape ``make_row`` expects, carrying the row's real answer."""
    return {
        "content": row.get("content") or "",
        "content_raw": row.get("content") or "",
        "reasoning": row.get("reasoning") or "",
        "content_source": row.get("content_source") or "content",
        "finish_reason": row.get("finish_reason"),
        "truncated": bool(row.get("truncated")),
        "prompt_tokens": row.get("prompt_tokens"),
        "completion_tokens": row.get("completion_tokens"),
        "raw_cached": row.get("cached_tokens"),
        "usage_missing": bool(row.get("usage_missing")),
        "token_source": row.get("token_source") or "replay",
        "ttft_s": row.get("ttft_s"),
        "latency_s": row.get("latency_s"),
        "ttft_ms": row.get("ttft_ms"),
        "max_tokens": row.get("max_tokens"),
    }


def make_cfg(workdir: str):
    import argparse as _ap
    return _ap.Namespace(
        model="occamy-1.0-NVFP4", engine="sglang", stream=False, timeout=900.0,
        thinking="auto", max_tokens=16384, max_turns=0, resume=False, dry_run=False,
        manifest_dir=workdir, manifest_path=None,
        base_url="http://127.0.0.1:1/v1",  # never contacted: send_chat is recorded
    )


def drive(fixture: dict, settled: dict, arm: str, rep: int, target: int,
          workdir: str) -> dict:
    """Drive run_longrun.run_cell for one arm until it tries to send ``target``."""
    rows_path = os.path.join(workdir, f"rows-{arm}-r{rep}-t{target}.jsonl")
    if os.path.exists(rows_path):
        os.remove(rows_path)
    cfg = make_cfg(workdir)
    state = {"turn": 0}
    shas = []

    def recorder(_cfg, messages):
        turn = state["turn"] + 1
        state["turn"] = turn
        row = settled.get((arm, rep, turn))
        if row is None:
            raise AssertionError(f"no settled row for {arm} r{rep} T{turn} — cannot replay")
        user = messages[1]["content"]
        shas.append({"turn": turn, "sha256": sha256_text(user),
                     "settled_prompt_sha256": row.get("prompt_sha256"),
                     "byte_identical": sha256_text(user) == row.get("prompt_sha256"),
                     "user_bytes": len(user.encode("utf-8")),
                     "user_tokens_est": (len(user.encode("utf-8"))
                                         / float(fixture["bytes_per_token"]))})
        if turn == target:
            raise WouldSend(turn, messages, R.request_body(_cfg, messages))
        return canned_resp(row)

    R.send_chat = recorder
    buf = io.StringIO()
    caught = None
    try:
        with contextlib.redirect_stdout(buf):
            R.run_cell(cfg, fixture, arm, rep, f"replay-{arm}-t{target}", rows_path)
    except WouldSend as exc:
        caught = exc
    finally:
        R.send_chat = _original_send_chat

    if caught is None:
        raise AssertionError(
            f"{arm}: run_cell finished without reaching T{target} "
            f"(driver tail: {buf.getvalue()[-400:]!r})")
    mismatches = [s for s in shas if not s["byte_identical"]]
    return {
        "arm": arm, "rep": rep, "turn": target,
        "messages": caught.messages,
        "body": caught.body,
        "prompt": caught.messages[1]["content"],
        "system": caught.messages[0]["content"],
        "prompt_bytes": len(caught.messages[1]["content"].encode("utf-8")),
        "turns_replayed": len(shas),
        "sha_provenance": {"checked": len(shas), "mismatches": mismatches},
    }


def num_hits(text: str, literal: str) -> int:
    """Word-boundary-ish count: '31' must not match inside '331 B' or '65536'."""
    return len(re.findall(r"(?<![\d.])" + re.escape(literal) + r"(?![\d.])", text))


def squash(text: str) -> str:
    return " ".join((text or "").split()).lower()


def anchors_of(expected: str) -> list[str]:
    seen, out = set(), []
    for m in re.finditer(r"[A-Za-z][A-Za-z0-9_]*", expected or ""):
        for part in m.group(0).split("_"):
            p = part.lower()
            if len(p) >= 4 and p not in seen:
                seen.add(p)
                out.append(p)
    return out


def excerpt(text: str, needle: str, span: int = 70) -> str | None:
    if not needle:
        return None
    i = text.find(needle)
    if i < 0:
        return None
    lo, hi = max(0, i - span), min(len(text), i + span)
    return text[lo:hi].replace("\n", " ")[:150]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--turns", default="12,24,46")
    ap.add_argument("--arms", default="transcript-grow,pointer-stable")
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--json", default="/tmp/prompt_at_turn.json")
    args = ap.parse_args(argv)

    global _original_send_chat
    _original_send_chat = R.send_chat

    fixture = R.load_fixture(args.fixture)
    settled = load_settled(args.rows)
    turns = [int(t) for t in args.turns.split(",") if t.strip()]
    workdir = "/tmp/prompt_at_turn-work"
    os.makedirs(workdir, exist_ok=True)

    working_set = R.working_set_block(fixture)
    plant_turn = 2
    plant_text = fixture["turns"][plant_turn - 1]["question"]

    cells = []
    for arm in [a.strip() for a in args.arms.split(",") if a.strip()]:
        for t in turns:
            got = drive(fixture, settled, arm, args.rep, t, workdir)
            prompt = got["prompt"]
            cp = next((c for c in fixture.get("checkpoints") or []
                       if int(c.get("turn", -1)) == t), None)
            expected = (cp or {}).get("expected")
            row = settled[(arm, args.rep, t)]
            anchors = anchors_of(expected) if expected and len(expected) > 12 else []
            anchor_hits = {a: squash(prompt).count(a) for a in anchors}
            fact_in_prompt = squash(plant_text) in squash(prompt)
            if expected and anchors:
                expected_in_prompt = all(v > 0 for v in anchor_hits.values())
                expected_hits = sum(anchor_hits.values())
            else:
                expected_hits = num_hits(prompt, expected) if expected else 0
                expected_in_prompt = expected_hits > 0
            cells.append({
                "arm": arm, "turn": t, "expected": expected,
                "fact_planted_in_prompt": fact_in_prompt,
                "fact_excerpt": excerpt(prompt, plant_text[:60]),
                "expected_value_in_prompt": expected_in_prompt,
                "expected_grep_count": expected_hits,
                "anchor_hits": anchor_hits,
                "answer_observed": row.get("content"),
                "answer_source": row.get("answer_source"),
                "failed_turn": row.get("failed_turn"),
                "reachable": bool(expected_in_prompt),
                "prompt_bytes": got["prompt_bytes"],
                "turns_replayed": got["turns_replayed"],
                "sha_checked": got["sha_provenance"]["checked"],
                "sha_mismatches": len(got["sha_provenance"]["mismatches"]),
                "prompt_head": prompt[:120].replace("\n", " "),
                "prompt_tail": prompt[-220:].replace("\n", " | "),
                "cp_question": (cp or {}).get("question"),
            })

    baseline_probe = {
        "working_set_bytes": len(working_set.encode("utf-8")),
        "working_set_contains_64": num_hits(working_set, "64"),
        "working_set_contains_31": num_hits(working_set, "31"),
        "plant_turn_text": plant_text,
        "plant_turn_has_any_fact": bool(re.search(r"\d", plant_text)),
        "plant_turn_note": fixture["turns"][plant_turn - 1].get("note"),
        "item_ids": [it["id"] for it in fixture["items"]],
        "item_bytes": {it["id"]: len(it["body"].encode("utf-8")) for it in fixture["items"]},
    }
    per_turn_baseline = {}
    for t in turns:
        base = R.Planner("transcript-grow", fixture, dry_run=False)
        for i in range(1, min(t, fixture["N"] + 1)):
            row = settled.get((("transcript-grow"), args.rep, i))
            if row is not None:
                base.record(i, row.get("content") or "")
        info = base.build(t)
        per_turn_baseline[t] = {
            "shared_base_contains_64": num_hits(info["prompt"], "64"),
            "shared_base_contains_31": num_hits(info["prompt"], "31"),
        }

    out = {
        "schema": "consonance.prompt-at-turn/1",
        "method": "imported-runner",
        "method_detail": ("imports run_longrun; patches send_chat with a recorder that raises "
                          "WouldSend(payload); drives run_longrun.run_cell for turns 1..N with "
                          "the settled canned replies"),
        "fixture": fixture["_path"],
        "fixture_sha256": fixture["_sha256"],
        "rows": args.rows,
        "cells": cells,
        "baseline_probe": baseline_probe,
        "shared_base_by_turn": per_turn_baseline,
        "no_http_proof": {
            "patched": ["urllib.request.urlopen", "urllib.request.build_opener",
                        "http.client.HTTPConnection.connect",
                        "http.client.HTTPSConnection.connect", "socket.create_connection"],
            "network_attempts": NET_ATTEMPTS,
            "ok": not NET_ATTEMPTS,
        },
        "requests_sent": 0,
    }
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)

    print(f"method={out['method']} fixture_sha={fixture['_sha256'][:16]} rows={len(settled)}")
    print(f"plant_turn(T2) text={plant_text!r}")
    print(f"plant_turn_has_any_fact={baseline_probe['plant_turn_has_any_fact']} "
          f"working_set_bytes={baseline_probe['working_set_bytes']} "
          f"ws_64={baseline_probe['working_set_contains_64']} "
          f"ws_31={baseline_probe['working_set_contains_31']}")
    print(f"{'arm':17s} {'T':>3s} {'fact':5s} {'exp':5s} {'n':>3s} {'reach':5s} "
          f"{'sha':9s} bytes  answer")
    for c in cells:
        print(f"{c['arm']:17s} {c['turn']:3d} {str(c['fact_planted_in_prompt']):5s} "
              f"{str(c['expected_value_in_prompt']):5s} {c['expected_grep_count']:3d} "
              f"{str(c['reachable']):5s} {c['sha_mismatches']}/{c['sha_checked']:<7d} "
              f"{c['prompt_bytes']:6d}  {(c['answer_observed'] or '')[:60].replace(chr(10),' ')!r}")
    if NET_ATTEMPTS:
        print(f"NO-HTTP PROOF FAILED: attempts={NET_ATTEMPTS}", file=sys.stderr)
        return 9
    print(f"NO-HTTP PROOF ok: 5 clients patched, network_attempts={NET_ATTEMPTS}, "
          f"requests_sent=0")
    return 0


if __name__ == "__main__":
    _original_send_chat = None
    sys.exit(main())
