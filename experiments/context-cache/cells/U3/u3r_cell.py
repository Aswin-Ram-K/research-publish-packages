"""U3-R — prefix volatility (E1) live cell.

Question: when the SAME logical transcript is rendered three ways that differ
only in WHERE the volatile values (timestamps, counters, run ids) live, how much
of the served prefix survives in the KV cache?

Arms
----
``pointer``        immutable system preamble, then one message per turn.  Volatile
                   values live ONLY in the final (delta) turn's prompt suffix.
``naive_append``   byte-identical messages to ``pointer`` (equal information);
                   volatile values likewise only in the delta.  It is the
                   recipe control: it must reproduce ``pointer``'s curve.
``naive_mutable``  volatile values interpolated into the mutable system/header
                   block, which is rewritten on every turn.

HARD BOUND: 200 live requests maximum, strictly serial, one in flight.
KILL CONDITION (pre-registered): if ``naive_mutable`` retains more than 50% of
its cached tokens after turn 2, report the volatility claim REFUTED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util  # noqa: E402

from resextract.context.meter import CacheMeter, clamp_stats  # noqa: E402
from resextract.context.nodes import StateNode  # noqa: E402
from resextract.context.render import RenderPolicy, render  # noqa: E402

CELL_DIR = Path(__file__).resolve().parent
CORPUS = ROOT / "experiments" / "context-cache" / "corpora" / "volatility.json"
CORPUS_SHA_EXPECTED = "6e2fe8979f67e1fe762c3daaa0ff53c30bd59c0d607b796d503e7d710e2bc7db"
LOCK_PATH = ROOT / ".occamy.lock"

MAX_REQUESTS = 200
LOCK_DEADLINE_S = 600.0
CONSECUTIVE_FAILURE_STOP = 3
MAX_TOKENS = 8
THINKING = False

ARMS = {
    "pointer": RenderPolicy.POINTER,
    "naive_append": RenderPolicy.NAIVE_APPEND,
    "naive_mutable": RenderPolicy.NAIVE_MUTABLE,
}


# --------------------------------------------------------------------------- #
# Corpus
# --------------------------------------------------------------------------- #
def load_corpus() -> tuple[dict, str]:
    raw = CORPUS.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    return json.loads(raw), sha


def volatile_for(scenario_id: str, turn: int) -> dict[str, str]:
    """Volatile values: timestamps, counters, run ids.

    Deterministic in (scenario, turn) so a rerun renders the same bytes.
    Crucially they CHANGE on every turn: that is what makes the mutable header
    churn.  Values are built from the corpus seed so nothing here uses a clock.
    """

    seed = 1729
    h = hashlib.sha256(f"{scenario_id}:{turn}:{seed}".encode()).hexdigest()
    minutes = (int(h[:4], 16) + turn * 7) % (24 * 60)
    return {
        "ts": f"2026-10-21T{minutes // 60:02d}:{minutes % 60:02d}:{(int(h[4:6], 16)) % 60:02d}Z",
        "counter": str(turn * 3 + int(h[6:8], 16) % 5),
        "run_id": f"run-{h[8:16]}",
        "tool_calls": str(int(h[16:18], 16) % 40 + turn),
    }


def build_chain(scenario: dict, n_turns: int) -> list[StateNode]:
    """Immutable append-only chain: invariant root + one delta per turn."""

    nodes: list[StateNode] = []
    root = StateNode.create(scenario["preamble"], "invariant")
    nodes.append(root)
    prev = root
    for i in range(n_turns):
        turn = scenario["turns"][i]
        node = StateNode.create(
            turn["text"],
            "delta",
            parent=prev,
            role=turn.get("role", "user"),
            turn=i + 1,
        )
        nodes.append(node)
        prev = node
    return nodes


def salt_id(scenario_id: str) -> str:
    """Cell salt tag, WITHOUT the arm name.

    ``pointer`` and ``naive_append`` render equal information, so they must
    carry the same salt tag or the recipe control could never reproduce the
    treated arm.  Radix conflict is prevented structurally instead: the arms
    run in separate passes over all scenarios (``pointer`` completes before
    ``naive_append`` starts), and every turn is a strict prefix extension, so a
    later request is the byte-prefix of nothing already cached under another
    arm's salt.  ``naive_mutable`` gets its own tag because it is a different
    rendering, not a control for the same bytes.
    """

    return f"U3-R:e1:20261021:{scenario_id}"


def salt_for(scenario_id: str, arm: str) -> str:
    if arm == "naive_mutable":
        return f"{salt_id(scenario_id)}:naive_mutable"
    return salt_id(scenario_id)


# --------------------------------------------------------------------------- #
# Offline plan: proves the arms differ only in WHERE volatile values live
# --------------------------------------------------------------------------- #
def first_diff(a: str, b: str) -> int:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else -1


def plan(corpus: dict, corpus_sha: str) -> dict:
    scenarios = corpus["scenarios"]
    max_turns = max(len(s["turns"]) for s in scenarios)
    plan_arms = {}
    per_turn = []
    for sc in scenarios:
        sid = sc["id"]
        nodes = build_chain(sc, max_turns)
        turns = []
        for t in range(1, max_turns + 1):
            chain = nodes[: t + 1]
            vol = volatile_for(sid, t)
            msgs = {
                arm: render(pol, chain, preamble=sc["preamble"], volatile=vol, salt=salt_for(sid, arm))
                for arm, pol in ARMS.items()
            }
            content = {a: "\n".join(m["content"] for m in v) for a, v in msgs.items()}
            turns.append(
                {
                    "scenario": sid,
                    "turn": t,
                    "n_messages": {a: len(v) for a, v in msgs.items()},
                    "chars": {a: len(c) for a, c in content.items()},
                    "sha256": {a: hashlib.sha256(c.encode()).hexdigest() for a, c in content.items()},
                    "pointer_vs_naive_append_first_diff": first_diff(
                        content["pointer"], content["naive_append"]
                    ),
                    "pointer_vs_naive_mutable_first_diff": first_diff(
                        content["pointer"], content["naive_mutable"]
                    ),
                }
            )
        per_turn.extend(turns)
    # Equal-information check on the concatenated content, per turn.
    eq = all(t["pointer_vs_naive_append_first_diff"] == -1 for t in per_turn)
    # Mutable must differ from pointer from turn 1 (header churn).
    mut_differs = all(t["pointer_vs_naive_mutable_first_diff"] >= 0 for t in per_turn)
    return {
        "corpus_sha256": corpus_sha,
        "corpus_sha_expected": CORPUS_SHA_EXPECTED,
        "corpus_sha_match": corpus_sha == CORPUS_SHA_EXPECTED,
        "scenarios": [s["id"] for s in scenarios],
        "depths": corpus["meta"]["depths"],
        "max_turns": max_turns,
        "pointer_equals_naive_append_cells": eq,
        "naive_mutable_differs_from_pointer_all_turns": mut_differs,
        "rows": per_turn,
        "arms": plan_arms,
    }


# --------------------------------------------------------------------------- #
# Lock
# --------------------------------------------------------------------------- #
def acquire_lock(deadline_s: float = LOCK_DEADLINE_S):
    import fcntl

    fh = open(LOCK_PATH, "a+")
    t0 = time.time()
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fh, time.time() - t0
        except BlockingIOError:
            if time.time() - t0 > deadline_s:
                fh.close()
                raise TimeoutError(f"lock {LOCK_PATH} not acquired in {deadline_s}s")
            time.sleep(2.0)


# --------------------------------------------------------------------------- #
# Live
# --------------------------------------------------------------------------- #
def _load_shared_client():
    """Load experiments/context-cache/client.py by path (it is not a package)."""

    path = Path(__file__).resolve().parents[2] / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client", path)
    mod = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotations via sys.modules[cls.__module__]
    sys.modules["ctx_client"] = mod
    spec.loader.exec_module(mod)
    return mod.ChatClient


def run_live(corpus: dict, max_turns: int, arms: list[str], out_rows: Path) -> dict:
    ChatClient = _load_shared_client()

    lock_fh = None
    waited = 0.0
    try:
        lock_fh, waited = acquire_lock()
        client = ChatClient(timeout=180.0)
        meter = CacheMeter()
        rows: list[dict] = []
        spent = 0
        consecutive_failures = 0
        stop_reason = ""
        failures: list[str] = []

        def flush():
            out_rows.parent.mkdir(parents=True, exist_ok=True)
            with out_rows.open("w", encoding="utf-8") as fh:
                for r in rows:
                    fh.write(json.dumps(r, sort_keys=True) + "\n")

        for arm in arms:
            policy = ARMS[arm]
            for sc in corpus["scenarios"]:
                sid = sc["id"]
                nodes = build_chain(sc, max_turns)
                salt = salt_for(sid, arm)
                prev_sha = None
                for t in range(1, max_turns + 1):
                    if spent >= MAX_REQUESTS:
                        stop_reason = f"hard bound {MAX_REQUESTS} live requests reached"
                        break
                    chain = nodes[: t + 1]
                    vol = volatile_for(sid, t)
                    messages = render(
                        policy, chain, preamble=sc["preamble"], volatile=vol, salt=salt
                    )
                    content = "\n".join(m["content"] for m in messages)
                    prefix_sha = hashlib.sha256(content.encode()).hexdigest()
                    cached_from_trailing = 0
                    if prev_sha is not None and prefix_sha.startswith(prev_sha):
                        cached_from_trailing = 1
                    ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
                    try:
                        prompt, cached, completion, ttft, wall, status, text = client.chat(
                            messages, max_tokens=MAX_TOKENS, thinking=THINKING
                        )
                        consecutive_failures = 0
                    except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
                        consecutive_failures += 1
                        failures.append(f"{arm}/{sid}/t{t}: {type(exc).__name__}: {exc}")
                        spent += 1
                        if consecutive_failures >= CONSECUTIVE_FAILURE_STOP:
                            stop_reason = (
                                f"{CONSECUTIVE_FAILURE_STOP} consecutive failures; "
                                f"last={type(exc).__name__}: {exc}"
                            )
                            break
                        continue
                    spent += 1
                    rows.append(
                        {
                            "arm": arm,
                            "scenario": sid,
                            "turn": t,
                            "prompt_tokens": prompt,
                            "cached_tokens": cached,
                            "uncached": prompt - cached,
                            "ts": ts,
                            "ttft_ms": round(ttft, 3),
                            "wall_ms": round(wall, 3),
                            "completion_tokens": completion,
                            "status": status,
                            "prefix_sha256": prefix_sha,
                            "prev_prefix_is_prefix": cached_from_trailing,
                            "n_messages": len(messages),
                            "chars": len(content),
                        }
                    )
                    prev_sha = prefix_sha
                    if t % 8 == 0:
                        flush()
                        print(
                            f"[{arm}/{sid}] turn {t}: prompt={prompt} cached={cached} "
                            f"uncached={prompt - cached} spent={spent}",
                            flush=True,
                        )
                if stop_reason:
                    break
            if stop_reason:
                break
        flush()
        return {
            "requests_spent": spent,
            "rows": len(rows),
            "stop_reason": stop_reason,
            "failures": failures,
            "lock_wait_s": round(waited, 3),
            "clamp_stats": clamp_stats(),
        }
    finally:
        if lock_fh is not None:
            lock_fh.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["plan", "live"], required=True)
    ap.add_argument("--turns", type=int, default=16)
    ap.add_argument("--arms", default="pointer,naive_append,naive_mutable")
    ap.add_argument("--out", default=str(CELL_DIR / "rows.jsonl"))
    args = ap.parse_args(argv)

    corpus, sha = load_corpus()
    if args.mode == "plan":
        p = plan(corpus, sha)
        out = CELL_DIR / "plan.json"
        out.write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")
        print(
            f"corpus_sha_match={p['corpus_sha_match']} "
            f"pointer==naive_append={p['pointer_equals_naive_append_cells']} "
            f"mutable_differs_all_turns={p['naive_mutable_differs_from_pointer_all_turns']}"
        )
        return 0

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    res = run_live(corpus, args.turns, arms, Path(args.out))
    (CELL_DIR / "live_meta.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "failures"}, indent=2))
    return 0 if not res["stop_reason"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
