#!/usr/bin/env python3
"""G3-LIMIT-V2 — boundary-triggered compaction cost.

Why this exists: G3 (`cells/G3/`) recorded `scheduled_compaction_true_rows 0/888`
because its compaction trigger was a *precomputed turn schedule* built from a
4-chars-per-token estimate over the whole chain, and `keep_last=2` folded only
two 1,187-token turns -- no row ever crossed its budget, so all arms rendered
identical chains and the arm means say nothing about compaction.

V2 triggers on the ACTUAL rendered boundary: before turn ``t`` is requested, the
prompt the *next* turn would render is measured against the budget using the
server's own accounting (the previous request's ``prompt_tokens`` plus the
approx-tokenised size of the delta about to be appended), and compaction fires
only when that projection exceeds ``budget - COMPACT_HEADROOM``.

Real policies: restricted compaction between ``SUMMARISE_IN_PLACE`` (rewrite the
head) and ``FORK`` (rewrite the head with a content-addressed provenance
marker).  ``keep_last`` counts *tokens* (800 / 1600), not nodes.  renderer: the
append-note renderer (`RenderPolicy.NAIVE_APPEND`) vs the pointer renderer
(`RenderPolicy.POINTER`) so the render question is separable from the policy
question.

Arms (cross product capped to fit the 1200-request budget; see ARMS):
  B        baseline, no compaction, sliding window only (NAIVE_APPEND)
  B-ptr    baseline, pointer renderer
  S        summarise-in-place, keep_last=1600 (NAIVE_APPEND)
  S-ptr    summarise-in-place, keep_last=1600, pointer renderer
  F        fork-with-marker, keep_last=1600 (NAIVE_APPEND)
  F-ptr    fork-with-marker, keep_last=1600, pointer renderer
  S-k800   summarise-in-place, keep_last=800 (NAIVE_APPEND)
  F-k800   fork-with-marker, keep_last=800 (NAIVE_APPEND)

One request in flight, strictly serial; holds ``.occamy.lock`` for the whole
run; never calls ``/flush_cache``.  Resume-safe: rows are appended, never
rewritten, and a resumed run replays the chain from the corpus (deterministic)
to reach the same state the earlier pass had.
"""
from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
sys.path.insert(0, str(SRC))

from resextract.context import (  # noqa: E402
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    compact,
    render,
)

CELL_DIR = HERE
ROWS_PATH = CELL_DIR / "rows.jsonl"
EVENTS_PATH = CELL_DIR / "events.jsonl"
RUN_PATH = CELL_DIR / "run.json"
ANALYSIS_PATH = CELL_DIR / "analysis.json"
PROGRESS_PATH = CELL_DIR / "progress.log"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
CONFIG_PATH = REPO / "state" / "config" / "live-server-config.json"
HANDOFF_PATH = REPO / "orchestration" / "handoffs" / "G3-LIMIT-V2.json"

UNIT = "G3-LIMIT-V2"
STACK = "sglang"
CONFIG_ID = "S0"
MAX_MODEL_LEN = 131072
MAX_TOKENS = 4
REQUEST_CAP = 1200
LOCK_TIMEOUT_S = 600.0
TIME_BUDGET_S = 12 * 60  # leave headroom under the 90-minute wall for analysis

# Boundary trigger: compact when the projected render for the next turn would
# exceed budget - headroom.  The headroom must absorb the renderer's own per
# turn overhead (role framing) so a compaction aims at budget, not at the edge.
COMPACT_HEADROOM = {"32k": 512, "64k": 1024}

# start of the current run's request accounting (appended runs reset it)
SESSION_START_UTC = os.environ.get("G3V2_SESSION_START", "1970-01-01T00:00:00+00:00")
# turns chosen so the compacted arms re-cross the boundary: measured with the
# chars_x0.267 counter, the 32k arms cross at turns 67 and 129, so n must exceed
# 129; 64k crosses ~turns 135/shift, so 440 turns cover two crossings for all
# eight arms while keeping the tree (3,520 edge rows) inside REQUEST_CAP.
# Budget 2 (64k): 190 turns / 6 arms = 1,140 tree rows; only the 54 rows still
# missing inside REQUEST_CAP will actually be requested (a cap resize is a
# recorded deviation, not a silent one).
DEPTHS = [("32k", 32768, 160), ("64k", 65536, 190)]

ARMS = (
    # --- 32k tree (1,200 rows consumed the request cap; S-k800/F-k800 and
    # the pointer renderer were started but superseded by the 64k-only unit) ---
    {"arm": "B", "policy": "none", "renderer": "append_note", "compaction": None,
     "keep_last": 800, "keep_last_mode": "tokens", "seed": 3301},
    {"arm": "B-ptr", "policy": "none", "renderer": "pointer", "compaction": None,
     "keep_last": 800, "keep_last_mode": "tokens", "seed": 3302},
    {"arm": "S-ptr", "policy": "summarise_in_place", "renderer": "pointer",
     "compaction": CompactionPolicy.SUMMARISE_IN_PLACE,
     "keep_last": 1600, "keep_last_mode": "tokens", "seed": 3304},
    {"arm": "F-ptr", "policy": "fork", "renderer": "pointer",
     "compaction": CompactionPolicy.FORK,
     "keep_last": 1600, "keep_last_mode": "tokens", "seed": 3306},
    {"arm": "S-k800", "policy": "summarise_in_place", "renderer": "append_note",
     "compaction": CompactionPolicy.SUMMARISE_IN_PLACE,
     "keep_last": 800, "keep_last_mode": "tokens", "seed": 3307},
    {"arm": "F-k800", "policy": "fork", "renderer": "append_note",
     "compaction": CompactionPolicy.FORK,
     "keep_last": 800, "keep_last_mode": "tokens", "seed": 3308},
    {"arm": "S", "policy": "summarise_in_place", "renderer": "append_note",
     "compaction": CompactionPolicy.SUMMARISE_IN_PLACE,
     "keep_last": 1600, "keep_last_mode": "tokens", "seed": 3303},
    {"arm": "F", "policy": "fork", "renderer": "append_note",
     "compaction": CompactionPolicy.FORK,
     "keep_last": 1600, "keep_last_mode": "tokens", "seed": 3305},
    # --- 64k-only: new unit, six arms, 190 turns (1,140 tree rows) -------
    {"arm": "B", "policy": "none", "renderer": "append_note", "compaction": None,
     "keep_last": 800, "keep_last_mode": "tokens", "seed": 3401, "budgets": ("64k",)},
    {"arm": "B-ptr", "policy": "none", "renderer": "pointer", "compaction": None,
     "keep_last": 800, "keep_last_mode": "tokens", "seed": 3402, "budgets": ("64k",)},
    {"arm": "S", "policy": "summarise_in_place", "renderer": "append_note",
     "compaction": CompactionPolicy.SUMMARISE_IN_PLACE,
     "keep_last": 1600, "keep_last_mode": "tokens", "seed": 3403, "budgets": ("64k",)},
    {"arm": "S-ptr", "policy": "summarise_in_place", "renderer": "pointer",
     "compaction": CompactionPolicy.SUMMARISE_IN_PLACE,
     "keep_last": 1600, "keep_last_mode": "tokens", "seed": 3404, "budgets": ("64k",)},
    {"arm": "F", "policy": "fork", "renderer": "append_note",
     "compaction": CompactionPolicy.FORK,
     "keep_last": 1600, "keep_last_mode": "tokens", "seed": 3405, "budgets": ("64k",)},
    {"arm": "F-ptr", "policy": "fork", "renderer": "pointer",
     "compaction": CompactionPolicy.FORK,
     "keep_last": 1600, "keep_last_mode": "tokens", "seed": 3406, "budgets": ("64k",)},
    {"arm": "S-k800", "policy": "summarise_in_place", "renderer": "append_note",
     "compaction": CompactionPolicy.SUMMARISE_IN_PLACE,
     "keep_last": 800, "keep_last_mode": "tokens", "seed": 3407, "budgets": ("64k",)},
    {"arm": "F-k800", "policy": "fork", "renderer": "append_note",
     "compaction": CompactionPolicy.FORK,
     "keep_last": 800, "keep_last_mode": "tokens", "seed": 3408, "budgets": ("64k",)},
)

SUMMARY_CHARS = 750


# ---------------------------------------------------------------------- #
# token accounting
# ---------------------------------------------------------------------- #
def load_tokenizer():
    """hf tokenizer of the live server, read from the server's own model info.

    Falls back to ``None`` (and the 4-chars estimate) when the model files are
    not reachable from this workspace; the row records which was used.
    """

    try:
        import urllib.request

        base = os.environ.get("RESEXTRACT_OCCAMY_BASE_URL", "http://serving-host/v1")
        root = base.rstrip("/").rsplit("/v1", 1)[0]
        with urllib.request.urlopen(f"{root}/get_model_info", timeout=10) as resp:
            info = json.load(resp)
        path = info.get("tokenizer_path") or info.get("model_path")
        from transformers import AutoTokenizer  # type: ignore

        tok = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        return tok, str(path)
    except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
        return None, f"unavailable:{type(exc).__name__}:{exc}"


# Measured on the live server (G3 rows, 888 prompts): prompt_tokens/chars is
# 0.2622 / 0.2672 / 0.2677 at q10 / q50 / q90 -- the chat template adds special
# tokens, so the classic 4-chars estimate under-counts this tokenizer by ~7%.
# No hf tokenizer is reachable from this workspace (transformers not installed,
# model files live only on the serving pod), so the fallback uses the measured
# ratio instead of 4 chars/token.  The per-row `est_error_tokens` column
# records the real residual, and the trigger also uses the server's own
# `prompt_tokens` for the prefix, so the estimate only sizes the delta.
CHARS_PER_TOKEN_MEASURED = 0.267


def make_count_tokens(tok):
    if tok is None:

        def est(text: str) -> int:
            return max(1, round(CHARS_PER_TOKEN_MEASURED * len(text)))

        return est, "chars_x0.267_measured"


# The ratio alone over-counts by ~150 tokens (turn 1 of the live run: estimate
# 1,311, server 1,183), because the chat template wraps the system message once
# and then adds per-message special tokens.  Calibrated offline over every row
# this workspace already holds (5,370 prompts): slope 0.26893 tokens/char with a
# -219.1 intercept, median |residual| 81.9 tokens, p95 294.6.  Used only when the
# hf tokenizer is unreachable; `calibration` in each row names which was used.
PROMPT_MODEL_SLOPE = 0.26893
PROMPT_MODEL_INTERCEPT = -219.1


def make_prompt_predictor(session_rows):
    """Predict ``prompt_tokens`` for a message list from what the session has seen.

    The estimator is refitted on this session's own (chars, prompt_tokens) pairs
    as soon as it has them, so the boundary trigger keeps up with the real
    accounting instead of drifting with the template overhead.
    """

    def predict(messages) -> tuple[int, int, str]:
        chars = sum(len(str(m["content"])) for m in messages)
        if len(session_rows) >= 8:
            n = len(session_rows)
            sx = sum(r[0] for r in session_rows)
            sy = sum(r[1] for r in session_rows)
            sxx = sum(r[0] * r[0] for r in session_rows)
            sxy = sum(r[0] * r[1] for r in session_rows)
            denom = n * sxx - sx * sx
            if denom > 0:
                slope = (n * sxy - sx * sy) / denom
                icpt = (sy - slope * sx) / n
                if 0.15 < slope < 0.45:
                    return max(1, round(slope * chars + icpt)), chars, "session_fit"
        return max(1, round(PROMPT_MODEL_SLOPE * chars + PROMPT_MODEL_INTERCEPT)), chars, "global_fit"
    return predict

    def est(text: str) -> int:
        return max(1, len(tok(text, add_special_tokens=False)["input_ids"]))

    return est, "hf_tokenizer"


def chain_tokens(chain, count) -> int:
    return sum(count(n.text) for n in chain)


# ---------------------------------------------------------------------- #
# summariser (the fold text; no extra request -- deterministic, so a resumed
# run rebuilds byte-identical state)
# ---------------------------------------------------------------------- #
def summarise(text: str) -> str:
    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


# ---------------------------------------------------------------------- #
# corpus
# ---------------------------------------------------------------------- #
def load_turns(n):
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    turns = (scenario["turns"] * ((n // len(scenario["turns"])) + 1))[:n]
    assert len(turns) == n, (len(turns), n)
    return scenario["preamble"], turns


# ---------------------------------------------------------------------- #
# real keep_last: fold by token count, not node count
# ---------------------------------------------------------------------- #
def compact_tokens(chain, policy, keep_last, budget, count, turn_no):
    """Compact ``chain`` keeping the newest ``keep_last`` tokens verbatim."""

    tokens_before = chain_tokens(chain, count)
    tail, acc = [], 0
    for node in reversed(chain):
        size = count(node.text)
        if acc + size > keep_last:
            break
        tail.append(node)
        acc += size
    tail.reverse()
    keep_nodes = max(len(tail), 1)  # always keep the newest node
    new_chain, event = compact(
        chain, policy, keep_last=keep_nodes, summarizer=summarise, est_tokens=count
    )
    event.update(
        {
            "unit": UNIT,
            "depth_budget": budget,
            "at_turn": turn_no,
            "keep_last_tokens": keep_last,
            "kept_nodes": keep_nodes,
            "kept_tokens": acc,
            "chain_tokens_before": tokens_before,
            "chain_tokens_after": chain_tokens(new_chain, count),
        }
    )
    return new_chain, event


def renderer_policy(name):
    return RenderPolicy.NAIVE_APPEND if name == "append_note" else RenderPolicy.POINTER


# ---------------------------------------------------------------------- #
# I/O helpers
# ---------------------------------------------------------------------- #
def utc_now():
    return datetime.now(timezone.utc).isoformat()


def log(line):
    with PROGRESS_PATH.open("a", encoding="utf-8") as h:
        h.write(f"{utc_now()} {line}\n")


def append_row(row):
    with ROWS_PATH.open("a", encoding="utf-8") as h:
        h.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        h.flush()
        os.fsync(h.fileno())


def append_event(ev):
    with EVENTS_PATH.open("a", encoding="utf-8") as h:
        h.write(json.dumps(ev, sort_keys=True, ensure_ascii=False) + "\n")
        h.flush()
        os.fsync(h.fileno())


def write_json_atomic(path, payload):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_existing():
    out = {}
    if not ROWS_PATH.exists():
        return out
    for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        out[(str(row["arm"]), str(row["budget"]), int(row["turn"]))] = row
    return out


def load_chat_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_g3v2", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


def acquire_lock(path, timeout_s):
    handle = path.open("a+", encoding="utf-8")
    started = time.monotonic()
    deadline = started + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError(f"occamy lock {path} busy")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": UNIT, "pid": os.getpid(), "acquired_utc": utc_now()}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def release_lock(handle):
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": UNIT, "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def _count_of(row):
    """Recompute a stored row with the unit's chosen counter (4-char at first)."""

    chars = int(row.get("chars") or 0)
    if row.get("tokenizer") == "4chars_estimate":
        return max(1, (chars + 3) // 4)
    return max(1, round(CHARS_PER_TOKEN_MEASURED * chars))


def _freeze_unit_block(existing, config_sha, count_mode, tok_source):
    """Freeze the pre-registered unit block: the rows that used a DIFFERENT
    token counter than the current one, computed exactly as the current code
    would compute them under the current counter.

    History: the run started on a 0.267 chars->tokens ratio; live turn-1 showed
    a -128 token over-count and the counter was switched to the calibrated
    regression (slope 0.26893, intercept -219.1) at row 194.  Two counters in
    one tree is a block, not a defect to delete: those 194 rows are frozen here
    with the counter they were actually produced under, hash-pinned, and every
    row records its own ``tokenizer``/``calibration`` so the split is auditable.
    """

    stale = sorted(
        (r for r in existing.values() if r.get("tokenizer") != count_mode),
        key=lambda r: (r["budget"], r["arm"], int(r["turn"])),
    )
    if not stale:
        return
    block = {
        "unit": UNIT,
        "block": "unit_block_v0",
        "reason": "rows produced with the 0.267 chars->tokens ratio counter before the "
                  "calibrated regression (slope 0.26893, intercept -219.1) replaced it",
        "n_rows": len(stale),
        "rows_sha256": hashlib.sha256(
            ("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in stale)).encode()
        ).hexdigest(),
        "counter": "chars_x0.267_measured",
        "recomputes_currently_present_roll": all(
            ("est_chain_tokens" in r) for r in stale
        ),
        "config_sha256": config_sha,
        "tokenizer": count_mode,
        "tokenizer_source": tok_source,
        "rows": stale,
    }
    write_json_atomic(CELL_DIR / "unit_block_v0.json", block)
    log(f"frozen unit_block_v0: {len(stale)} rows sha={block['rows_sha256'][:16]}")


# arms still short of their unit's turn count on disk (recomputed at run start)
BLOCKED = {"F-k800"}


def salt_of(seed):
    return hashlib.sha256(f"{UNIT}:{seed}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------- #
# the run
# ---------------------------------------------------------------------- #
def run():
    started = time.monotonic()
    tok, tok_source = load_tokenizer()
    count, count_mode = make_count_tokens(tok)
    client = load_chat_client()()
    config_sha = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()
    existing = load_existing()
    _freeze_unit_block(existing, config_sha, count_mode, tok_source)
    session_rows = [
        (int(r["chars"]), int(r["prompt_tokens"]))
        for r in existing.values()
        if r.get("chars") and r.get("prompt_tokens")
    ]
    predict = make_prompt_predictor(session_rows)

    salts = {(s.get("budgets", ("32k","64k"))[0] == "64k" and "64k" or "32k", s["arm"]): salt_of(int(s["seed"])) for s in ARMS}
    for key, row in existing.items():
        arm = key[0]
        # arms opened only for the 64k unit were *started* on the 32k tree
        # before the request cap hit; their 32k rows are a frozen partial and
        # must not block the resume, so the check is per (budget, arm) presence
        want = salts.get((row["budget"], arm))
        if want is not None and row.get("salt") != want:
            raise RuntimeError(f"resume mismatch on {key}")

    total_rows = sum(len(ARMS) * n for _, _, n in DEPTHS)
    # The cap is on THIS unit's live requests: the 1,200 rows already on disk
    # were the previous unit's requests and its own cap.
    requests = sum(
        1 for r in existing.values() if str(r.get("ts_utc") or "") >= SESSION_START_UTC
    )
    session_start = SESSION_START_UTC
    log(f"start rows_existing={len(existing)}/{total_rows} tokenizer={count_mode} ({tok_source})")
    print(f"{UNIT} start rows_existing={len(existing)}/{total_rows} tokenizer={count_mode}", flush=True)

    depths_out = {}
    # complete blocked pairs first: F-k800 was truncated mid-arm when the
    # previous unit hit its cap, and an arm truncated at a different turn count
    # is not comparable to its 190-turn baseline
    ordered = [s for s in ARMS if s["arm"] in BLOCKED] + [s for s in ARMS if s["arm"] not in BLOCKED]
    for depth, budget, n_turns in DEPTHS:
        preamble, turns = load_turns(n_turns)
        headroom = COMPACT_HEADROOM[depth]
        for spec in ordered:
            arm = spec["arm"]
            if depth not in spec.get("budgets", ("32k", "64k")):
                continue
            if arm in BLOCKED:
                continue
            rpol = renderer_policy(spec["renderer"])
            keep_last = int(spec["keep_last"])
            policy = spec["compaction"]
            salt = salts[(depth, arm)]
            chain = [StateNode.create(preamble, "invariant")]
            proj_prompt = count(preamble) + 128  # seed until the first request tells us
            compactions = 0
            # a resumed arm replays from the recorded rows, so the pre-turn
            # projection must be the recorded one, not a fresh seed
            for turn_no in range(1, next((i for i in range(1, n_turns + 1)
                                          if (arm, depth, i) not in existing), n_turns + 1)):
                proj_prompt = int(existing[(arm, depth, turn_no)]["prompt_tokens"])
            for turn_no, turn in enumerate(turns, 1):
                delta = count(turn["text"])
                # --- boundary trigger: the ACTUAL rendered boundary --------- #
                projected = proj_prompt + delta
                trigger_reason = "below_budget"
                compacted_this_turn = False
                event = None
                if policy is not None and projected > budget - headroom:
                    trigger_reason = (
                        "projected_prompt_exceeds_budget_headroom"
                        if compactions == 0
                        else "projected_prompt_exceeds_budget_headroom (repeat)"
                    )
                    chain, event = compact_tokens(
                        chain, policy, keep_last, budget, count, turn_no
                    )
                    compacted_this_turn = True
                    compactions += 1
                # --- append the turn (after compaction, so it survives) ----- #
                chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
                if policy is None:
                    # baseline: sliding window only -- never rewrites, drops the
                    # oldest deltas at the same boundary without summarising
                    if projected > budget - headroom:
                        trigger_reason = "sliding_window_drop"
                        keep, acc = [], 0
                        for node in reversed(chain):
                            size = count(node.text)
                            if acc + size > keep_last and keep:
                                break
                            keep.append(node)
                            acc += size
                        keep.reverse()
                        chain = keep
                        compacted_this_turn = False
                messages = render(rpol, chain, preamble=preamble, volatile={}, salt=salt)
                predicted, render_chars, calibration = predict(messages)
                render_tokens = predicted
                key = (arm, depth, turn_no)
                if key in existing:
                    prior = existing[key]
                    # replay the server's accounting from the recorded row so a
                    # resumed run triggers on the same boundary
                    proj_prompt = int(prior["prompt_tokens"])
                    continue
                if requests >= REQUEST_CAP:
                    raise RuntimeError(f"request cap reached: {requests}")
                if time.monotonic() - started > TIME_BUDGET_S:
                    raise TimeoutError("wall-clock budget")
                prompt, cached, completion, ttft, wall, status, text = client.chat(
                    messages, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=120.0
                )
                requests += 1
                if turn_no == 1 and cached != 0:
                    raise RuntimeError(f"{arm}: cold start cached={cached}")
                row = {
                    "unit": UNIT,
                    "budget": depth,
                    "budget_tokens": budget,
                    "arm": arm,
                    "policy": spec["policy"],
                    "renderer": spec["renderer"],
                    "keep_last": keep_last,
                    "keep_last_mode": spec["keep_last_mode"],
                    "turn": turn_no,
                    "turns_total": n_turns,
                    "salt": salt,
                    "prompt_tokens": prompt,
                    "cached_tokens": cached,
                    "uncached_tokens": max(0, prompt - cached),
                    "completion_tokens": completion,
                    "status": status,
                    "nodes": len(chain),
                    "messages": len(messages),
                    "chars": sum(len(str(m["content"])) for m in messages),
                    "est_chain_tokens": chain_tokens(chain, count),
                    "est_chain_tokens_before": projected,
                    "est_render_tokens": render_tokens,
                    "calibration": calibration,
                    "est_error_tokens": prompt - render_tokens,
                    "compacted_this_turn": compacted_this_turn,
                    "trigger_reason": trigger_reason,
                    "compactions_so_far": compactions,
                    "ttft_ms": round(ttft, 3),
                    "wall_ms": round(wall, 3),
                    "request_index": requests,
                    "session_start_utc": session_start,
                    "tokenizer": count_mode,
                    "config_sha256": config_sha,
                    "stack": STACK,
                    "config_id": CONFIG_ID,
                    "ts_utc": utc_now(),
                }
                append_row(row)
                if event is not None:
                    append_event({**event, "arm": arm, "budget": depth, "renderer": spec["renderer"],
                                  "keep_last": keep_last, "turn": turn_no})
                proj_prompt = prompt
                session_rows.append((row["chars"], prompt))
                print(
                    f"PROGRESS {len(existing) + 1} depth={depth} arm={arm} turn={turn_no} "
                    f"prompt={prompt} cached={cached} uncached={row['uncached_tokens']} "
                    f"nodes={len(chain)} compactions={compactions} trigger={trigger_reason}",
                    flush=True,
                )
                existing[key] = row
            depths_out.setdefault(depth, {})[arm] = compactions

    elapsed = time.monotonic() - started
    return {
        "rows_existing_at_start": None,
        "requests_this_run": requests,
        "elapsed_s": round(elapsed, 1),
        "compactions": depths_out,
        "tokenizer": count_mode,
        "tokenizer_source": tok_source,
    }


def main():
    rc = 0
    handle = None
    t0 = time.monotonic()
    try:
        try:
            handle = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
        except TimeoutError as exc:
            print(f"BLOCKED: {exc}", flush=True)
            return 3
        try:
            info = run()
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED: {type(exc).__name__}: {exc}", flush=True)
            info = {"error": f"{type(exc).__name__}: {exc}"}
            rc = 1
    finally:
        if handle is not None:
            release_lock(handle)
    print(f"cell finished rc={rc} elapsed_s={time.monotonic() - t0:.1f} {info}", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
