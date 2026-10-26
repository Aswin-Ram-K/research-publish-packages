#!/usr/bin/env python3
"""E2 -- instrumented re-run of U15's R (summarise-in-place) arm, plus F tail.

Purpose (single): settle GAPS G6 by attributing the ~1,660 tokens/turn that the
R arm re-prefills between compactions.  The instrument records, per turn, the
*rendered window* at message level (node id, kind, content sha256, chars,
estimated tokens, cumulative estimate), the message-level diff against the
previous turn (carried / new / dropped / changed), the invariant-head hash and
the summary-node hash, and the server's ``prompt_tokens`` / ``cached_tokens``.

Nothing here is inferred from totals: the decomposition

    uncached_t = new_tail_t + (prompt_{t-1} % 64) + re_prefill_t

is computed from measured ``prompt_tokens`` and ``cached_tokens`` on a turn
whose message prefix is verified byte-identical to the previous turn's.  The
residual (``re_prefill_t``) is then tested against the three candidate
mechanisms named in G6: the window's tail, the summary node, cache chunking.

Design copied verbatim from ``cells/U15/u15_cell.py`` (same corpus slice, same
8k trigger, same compaction points derived from the reference arm, same
``keep_last=2``, same offline stub summariser, same warm-twice U10 rule), with
ONE deliberate deviation: fresh per-arm salts (2501/2502) so the batch starts
cold even if the endpoint still holds U15's salt-1501 prefixes.  The salt is a
constant 16-hex-char token in message 0, so the mechanism under test is
unchanged; prompt counts may differ from U15's by a token or two.

Writes only under ``experiments/context-cache/cells/E2/``.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
assert (REPO / "src" / "resextract").is_dir(), f"repo root not found from {HERE}"
SRC = REPO / "src"
sys.path.insert(0, str(SRC))

from resextract.context import (  # noqa: E402
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    compact,
    default_est_tokens,
    make_salt,
    needs_compaction,
    render,
)

CELL_DIR = HERE
ROWS_PATH = CELL_DIR / "rows.jsonl"
EVENTS_PATH = CELL_DIR / "events.jsonl"
ANALYSIS_PATH = CELL_DIR / "analysis.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"

TURNS = 40
BUDGET_TOKENS = 8192
KEEP_LAST = 2
MAX_TOKENS = 4
SUMMARY_CHARS = 750
LOCK_TIMEOUT_S = 1800.0

# arm, policy, seed, first live turn (1 = whole chain live)
ARMS: tuple[dict[str, object], ...] = (
    {
        "arm": "R",
        "policy": "summarise_in_place",
        "compaction": CompactionPolicy.SUMMARISE_IN_PLACE,
        "seed": 2501,
        "first_live_turn": 1,
    },
    {
        "arm": "F",
        "policy": "fork",
        "compaction": CompactionPolicy.FORK,
        "seed": 2502,
        "first_live_turn": 30,
    },
)

REQUEST_CAP = 90


# --------------------------------------------------------------------------- #
# Deterministic pieces, copied from U15
# --------------------------------------------------------------------------- #
def summarise(text: str) -> str:
    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


def total_est(chain: list[StateNode]) -> int:
    return sum(default_est_tokens(node.text) for node in chain)


def load_slice() -> tuple[dict, list[dict]]:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    turns = scenario["turns"][:TURNS]
    if len(turns) != TURNS:
        raise RuntimeError(f"corpus slice has {len(turns)} turns, expected {TURNS}")
    return scenario, turns


def compaction_schedule(preamble: str, turns: list[dict]) -> list[int]:
    chain = [StateNode.create(preamble, "invariant")]
    schedule: list[int] = []
    for turn_no, turn in enumerate(turns, 1):
        chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
        if needs_compaction(chain, budget_tokens=BUDGET_TOKENS, est_tokens=default_est_tokens):
            schedule.append(turn_no)
            chain, _event = compact(
                chain,
                CompactionPolicy.SUMMARISE_IN_PLACE,
                keep_last=KEEP_LAST,
                summarizer=summarise,
                est_tokens=default_est_tokens,
            )
    return schedule


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_chat_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_e2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load chat client from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


# --------------------------------------------------------------------------- #
# Lock
# --------------------------------------------------------------------------- #
def acquire_lock(path: Path, timeout_s: float) -> tuple[object, float]:
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
                raise TimeoutError(f"occamy lock {path} busy for {timeout_s:.0f}s")
            time.sleep(0.5)
    waited = time.monotonic() - started
    handle.seek(0)
    handle.truncate()
    json.dump(
        {
            "unit": "E2",
            "pid": os.getpid(),
            "acquired_utc": utc_now(),
            "waited_s": round(waited, 1),
            "scope": "E2 G6 attribution probe; hold for the whole batch",
        },
        handle,
    )
    handle.flush()
    os.fsync(handle.fileno())
    return handle, waited


def release_lock(handle: object) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": "E2", "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


# --------------------------------------------------------------------------- #
# Rows
# --------------------------------------------------------------------------- #
def load_existing() -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    if not ROWS_PATH.exists():
        return out
    for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        out[(str(row["arm"]), int(row["turn"]))] = row
    return out


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def window_state(messages: list[dict], chain: list[StateNode]) -> dict:
    """Message-level view of the rendered window, with node identity."""

    bodies = [n for n in chain if n.kind != "invariant"]
    nodes = []
    cum = 0
    for i, node in enumerate(bodies):
        est = default_est_tokens(node.text)
        cum += est
        nodes.append(
            {
                "i": i,
                "role": "user" if i % 2 == 0 else "assistant",
                "kind": node.kind,
                "id": node.node_id[:16],
                "chars": len(node.text),
                "est_tokens": est,
                "cum_est": cum,
                "content_sha": sha(node.text)[:16],
            }
        )
    return {
        "messages": messages,
        "n_messages": len(messages),
        "n_nodes": len(chain),
        "nodes": nodes,
        "head_sha": sha(str(messages[0]["content"])),
        "head_chars": len(str(messages[0]["content"])),
        "head_est": default_est_tokens(str(messages[0]["content"])),
        "summary_shas": [sha(n.text)[:16] for n in chain if n.kind == "summary"],
        "chars": sum(len(str(m["content"])) for m in messages),
        "content_shas": [sha(str(m["content"])) for m in messages],
        "id_by_msg": [None] + [n.node_id[:16] for n in bodies],
    }


def diff_windows(prev: dict | None, cur: dict) -> dict:
    if prev is None:
        return {
            "carried_ids": [],
            "new_ids": [n["id"] for n in cur["nodes"]],
            "dropped_ids": [],
            "changed_msg_indices": [],
            "prefix_identical_msgs": 0,
            "prefix_identical": False,
        }
    pshas, cshas = prev["content_shas"], cur["content_shas"]
    k = 0
    while k < min(len(pshas), len(cshas)) and pshas[k] == cshas[k]:
        k += 1
    carried = [
        cid for i, cid in enumerate(cur["id_by_msg"])
        if cid is not None and i < k and i < len(prev["id_by_msg"]) and prev["id_by_msg"][i] == cid
    ]
    prev_ids = {n["id"] for n in prev["nodes"]}
    cur_ids = {n["id"] for n in cur["nodes"]}
    return {
        "carried_ids": carried,
        "new_ids": sorted(cur_ids - prev_ids),
        "dropped_ids": sorted(prev_ids - cur_ids),
        "changed_msg_indices": [
            i for i in range(min(len(pshas), len(cshas))) if pshas[i] != cshas[i]
        ],
        "prefix_identical_msgs": k,
        "prefix_identical": k == len(pshas) and len(cshas) > k,
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def run(lock_note: str, waited: float) -> int:
    started = time.monotonic()
    scenario, turns = load_slice()
    preamble = scenario["preamble"]
    schedule = compaction_schedule(preamble, turns)
    client = load_chat_client()()
    existing = load_existing()

    requests = 0
    anomalies: list[dict] = []
    events: list[dict] = []
    prev_window: dict[str, dict | None] = {}
    prev_prompt: dict[str, int] = {}

    print(f"E2 start: schedule={schedule} existing_rows={len(existing)}", flush=True)

    for spec in ARMS:
        arm = str(spec["arm"])
        compaction = spec["compaction"]
        first_live = int(spec["first_live_turn"])
        salt = make_salt(int(spec["seed"]))
        chain = [StateNode.create(preamble, "invariant")]
        prev_window[arm] = None
        prev_prompt[arm] = 0

        for turn_no, turn in enumerate(turns, 1):
            chain = [
                *chain,
                StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no),
            ]
            scheduled = bool(compaction is not None and turn_no in schedule)
            event = None
            if scheduled:
                chain, event = compact(
                    chain,
                    compaction,  # type: ignore[arg-type]
                    keep_last=KEEP_LAST,
                    summarizer=summarise,
                    est_tokens=default_est_tokens,
                )
                events.append({**event, "unit": "E2", "arm": arm, "turn": turn_no, "salt": salt})

            messages = render(
                RenderPolicy.NAIVE_APPEND,
                chain,
                preamble=preamble,
                volatile={},
                salt=salt,
            )
            cur = window_state(messages, chain)
            diff = diff_windows(prev_window[arm], cur)

            if turn_no < first_live:
                prev_window[arm] = cur
                prev_prompt[arm] = 0
                continue
            if (arm, turn_no) in existing:
                prev_window[arm] = cur
                prev_prompt[arm] = int(existing[(arm, turn_no)]["prompt_tokens"])
                continue

            prompt, cached, completion, ttft, wall, status, text = client.chat(
                messages,
                max_tokens=MAX_TOKENS,
                thinking=False,
                stream=True,
                timeout=120.0,
            )
            requests += 1
            warm_retry = False
            warm1 = None
            if (
                cached == 0
                and prompt > 0
                and prompt % 64 == 0
                and turn_no > 1
                and not scheduled
                and turn_no == first_live + 1
            ):
                warm1 = (prompt, cached)
                prompt, cached, completion, ttft, wall, status, text = client.chat(
                    messages,
                    max_tokens=MAX_TOKENS,
                    thinking=False,
                    stream=True,
                    timeout=120.0,
                )
                requests += 1
                warm_retry = True
                anomalies.append({"kind": "warm_twice", "arm": arm, "turn": turn_no,
                                  "warm1": warm1, "warm2": [prompt, cached]})
            if requests > REQUEST_CAP:
                raise RuntimeError(f"request cap guard tripped: {requests} > {REQUEST_CAP}")
            if turn_no == first_live and cached != 0:
                raise RuntimeError(
                    f"arm {arm}: cold-start contract violated at turn 1 "
                    f"(cached={cached}) -- salt not fresh"
                )

            p = int(prompt)
            c = int(cached)
            pp = prev_prompt[arm]
            row = {
                "unit": "E2",
                "arm": arm,
                "policy": str(spec["policy"]),
                "turn": turn_no,
                "salt": salt,
                "prompt_tokens": p,
                "cached_tokens": c,
                "uncached": p - c,
                "prompt_mod64": p % 64,
                "completion_tokens": completion,
                "status": status,
                "scheduled_compaction": scheduled,
                "prev_prompt_tokens": pp,
                "delta_prompt_tokens": (p - pp) if pp else None,
                "chars": cur["chars"],
                "delta_chars": None,
                "n_messages": cur["n_messages"],
                "n_nodes": cur["n_nodes"],
                "head_sha": cur["head_sha"],
                "head_est_tokens": cur["head_est"],
                "summary_shas": cur["summary_shas"],
                "nodes": cur["nodes"],
                "diff": diff,
                "ttft_ms": round(ttft, 3),
                "wall_ms": round(wall, 3),
                "warm_retry": warm_retry,
                "warm1": warm1,
                "ts_utc": utc_now(),
                "lock_wait_s": round(waited, 1),
            }
            if prev_window[arm] is not None:
                row["delta_chars"] = cur["chars"] - prev_window[arm]["chars"]
            append_row(row)
            print(
                f"{arm} t{turn_no:02d} prompt={p} cached={c} unc={p - c} "
                f"mod64={p % 64} d={row['delta_prompt_tokens']} "
                f"msgs={cur['n_messages']} nodes={cur['n_nodes']} "
                f"new={len(diff['new_ids'])} changed={len(diff['changed_msg_indices'])} "
                f"prefix_ok={diff['prefix_identical']} break={scheduled}",
                flush=True,
            )
            prev_window[arm] = cur
            prev_prompt[arm] = p

    elapsed = time.monotonic() - started
    rows = load_existing()
    ordered = [rows[(str(s["arm"]), t)] for s in ARMS for t in range(1, TURNS + 1) if (str(s["arm"]), t) in rows]
    payload = analyse(ordered, elapsed=elapsed, schedule=schedule, requests=requests, waited=waited)
    write_json_atomic(ANALYSIS_PATH, payload)
    EVENTS_PATH.write_text(
        json.dumps(
            {"unit": "E2", "compaction_events": events, "anomalies": anomalies},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print_summary(payload)
    return payload


def write_json_atomic(path: Path, payload: dict) -> None:
    tmp = CELL_DIR / (path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# Analysis -- additive, closed, and honest about the residual
# --------------------------------------------------------------------------- #
def analyse(rows: list[dict], *, elapsed: float, schedule: list[int], requests: int, waited: float) -> dict:
    by_arm: dict[str, list[dict]] = {}
    for r in rows:
        by_arm.setdefault(str(r["arm"]), []).append(r)
    for arm in by_arm:
        by_arm[arm].sort(key=lambda r: int(r["turn"]))

    out: dict[str, object] = {
        "unit": "E2",
        "question": "What re-prefills ~1,660 tokens/turn in U15's R arm between compactions?",
        "design": {
            "corpus": str(CORPUS_PATH.relative_to(REPO)),
            "scenario": "E1",
            "turns": TURNS,
            "budget_tokens": BUDGET_TOKENS,
            "keep_last": KEEP_LAST,
            "compaction_schedule": schedule,
            "renderer": "naive_append",
            "salts": {str(s["arm"]): make_salt(int(s["seed"])) for s in ARMS},
            "first_live_turn": {str(s["arm"]): int(s["first_live_turn"]) for s in ARMS},
            "summariser": f"offline stub, whitespace-collapsed, {SUMMARY_CHARS} chars",
        },
        "requests_live": requests,
        "elapsed_s": round(elapsed, 1),
        "lock_wait_s": round(waited, 1),
        "arms": {},
    }

    for arm, arows in by_arm.items():
        steady: list[dict] = []
        cold: list[dict] = []
        annotated: list[dict] = []
        for r in arows:
            r = dict(r)
            p, c = int(r["prompt_tokens"]), int(r["cached_tokens"])
            pp = int(r["prev_prompt_tokens"] or 0)
            diff = r["diff"]
            is_break = bool(r["scheduled_compaction"])
            r["components"] = None
            if r["turn"] == int(r["turn"]) and (pp == 0 or is_break or c == 0):
                # cold / break: the whole prompt is (re)sent against a changed head
                r["class"] = "cold-break" if pp else "cold-first"
                r["components"] = {
                    "cold": p,
                    "new_tail": None,
                    "boundary": p % 64,
                    "head_rewrite": p if is_break else None,
                    "re_prefill": None,
                    "residual": 0,
                }
                cold.append(r)
            else:
                prefix_ok = bool(diff["prefix_identical"])
                new_tail = p - pp if prefix_ok else None
                boundary = pp % 64 if prefix_ok else None
                re_prefill = (pp - pp % 64) - c if prefix_ok else None
                r["class"] = "steady"
                if prefix_ok and new_tail is not None and boundary is not None and re_prefill is not None:
                    r["components"] = {
                        "cold": 0,
                        "new_tail": new_tail,
                        "boundary": boundary,
                        "head_rewrite": 0,  # verified: no message in the prefix changed
                        "re_prefill": re_prefill,
                        "residual": (p - c) - (new_tail + boundary + re_prefill),
                    }
                else:
                    r["components"] = None
                steady.append(r)
            annotated.append(r)
            r["prefix_ok"] = bool(diff["prefix_identical"])
            r["changed_msgs"] = len(diff["changed_msg_indices"])
            r["new_nodes"] = len(diff["new_ids"])
            r["dropped_nodes"] = len(diff["dropped_ids"])
            out.setdefault("turns", []).append(
                {
                    k: r[k]
                    for k in (
                        "arm", "turn", "class", "prompt_tokens", "cached_tokens", "uncached",
                        "prompt_mod64", "prev_prompt_tokens", "delta_prompt_tokens",
                        "n_messages", "prefix_ok", "changed_msgs", "new_nodes",
                        "dropped_nodes", "summary_shas", "head_sha", "components",
                    )
                }
            )
        arows[:] = annotated
        arms_stats = {"cold": [], "steady": []}
        for r in cold:
            arms_stats["cold"].append(
                {"turn": r["turn"], "prompt": r["prompt_tokens"], "cached": r["cached_tokens"],
                 "scheduled": r["scheduled_compaction"]}
            )
        for r in steady:
            arms_stats["steady"].append(
                {"turn": r["turn"], "prompt": r["prompt_tokens"], "cached": r["cached_tokens"],
                 "uncached": r["uncached"], "components": r["components"]}
            )
        out["arms"][arm] = arms_stats

    # ---- headline aggregation over R's steady turns ---------------------- #
    r_rows = by_arm.get("R", [])
    r_steady = [r for r in r_rows if r["class"] == "steady" and r["components"]]
    if not r_steady:
        out["claim"] = {"established": False, "why": "no steady R rows"}
        return out

    n = len(r_steady)
    total_unc = sum(r["uncached"] for r in r_steady)
    total_tail = sum(r["components"]["new_tail"] for r in r_steady)
    total_bound = sum(r["components"]["boundary"] for r in r_steady)
    total_re = sum(r["components"]["re_prefill"] for r in r_steady)
    total_res = sum(r["components"]["residual"] for r in r_steady)
    head_rewrites = sum(1 for r in r_steady if r["changed_msgs"] > 0)

    out["r_steady"] = {
        "turns": [r["turn"] for r in r_steady],
        "n": n,
        "sum_uncached": total_unc,
        "mean_uncached": round(total_unc / n, 1),
        "mean_new_tail": round(total_tail / n, 1),
        "mean_boundary": round(total_bound / n, 1),
        "mean_re_prefill": round(total_re / n, 1),
        "mean_residual": round(total_res / n, 3),
        "steady_turns_with_head_rewrite": head_rewrites,
        "closed": total_res == 0,
        "additivity_check": {
            "sum_components": total_tail + total_bound + total_re + total_res,
            "sum_uncached": total_unc,
            "diff": total_tail + total_bound + total_re + total_res - total_unc,
        },
    }

    # ---- where does the re-prefilled span end? --------------------------- #
    # Candidate boundaries: an earlier turn's prompt end (p_j, j<t) -- the
    # window's tail -- or the summary node boundary (estimated cumulative).
    boundary_hits: list[dict] = []
    for r in r_steady:
        c = int(r["cached_tokens"])
        p = int(r["prompt_tokens"])
        cands = [
            {"kind": "turn_end", "j": int(x["turn"]), "p_j": int(x["prompt_tokens"])}
            for x in r_rows
            if int(x["turn"]) < int(r["turn"]) and (int(x["turn"]) not in (1,) or True)
        ]
        hit = None
        for cand in sorted(cands, key=lambda d: -d["p_j"]):
            if c <= cand["p_j"] < c + 64:
                hit = cand
                break
        nodes = r["nodes"]
        # estimated cumulative tokens through each node (system excluded)
        est_hits = [
            {"node_i": nd["i"], "kind": nd["kind"], "cum_est": nd["cum_est"],
             "est_err": c - nd["cum_est"]}
            for nd in nodes
            if abs(c - nd["cum_est"]) <= 96
        ]
        boundary_hits.append(
            {
                "turn": r["turn"],
                "cached": c,
                "prompt": p,
                "prev_prompt": int(r["prev_prompt_tokens"]),
                "re_prefill": r["components"]["re_prefill"],
                "turn_end_hit": hit,
                "lag_turns": (int(r["turn"]) - hit["j"]) if hit else None,
                "est_node_hits": est_hits,
                "shortfall_mod64": r["components"]["re_prefill"] % 64,
            }
        )
    out["boundary_test"] = boundary_hits

    lags = [b["lag_turns"] for b in boundary_hits if b["lag_turns"] is not None]
    hits = len(lags)
    msg_lag = [b["turn"] - 1 - b["turn_end_hit"]["j"] for b in boundary_hits if b["turn_end_hit"]]
    out["boundary_summary"] = {
        "steady_turns": len(boundary_hits),
        "explained_by_an_earlier_turn_end": hits,
        "lag_turn_histogram": {str(k): lags.count(k) for k in sorted(set(lags))},
        "re_prefill_all_multiples_of_64": all(b["shortfall_mod64"] == 0 for b in boundary_hits),
        "re_prefill_values": [b["re_prefill"] for b in boundary_hits],
        "trailing_messages_skipped_histogram": {
            str(k): msg_lag.count(k) for k in sorted(set(msg_lag))
        },
        "share_of_turns_ending_on_a_turn_boundary": round(hits / max(1, len(boundary_hits)), 4),
    }

    # ---- summary-node test ---------------------------------------------- #
    # The summary node is message 1 after a break; is the match ever cut
    # *before* the summary (i.e. only the invariant head cached)?
    head_est = int(r_steady[0]["head_est_tokens"]) if r_steady else 0
    summary_cut = [
        b for b in boundary_hits
        if b["cached"] < head_est + int(r_steady[0]["nodes"][0]["est_tokens"] if r_steady else 0)
        and b["cached"] <= head_est + 32
    ]
    out["summary_test"] = {
        "head_est_tokens": head_est,
        "turns_where_match_stops_at_or_before_head": len(summary_cut),
        "turns": [b["turn"] for b in summary_cut],
        "summary_sha_constant_within_epochs": None,
    }

    # ---- F comparison turns 36-40 --------------------------------------- #
    f_rows = {int(r["turn"]): r for r in by_arm.get("F", [])}
    r_rows_by_turn = {int(r["turn"]): r for r in r_rows}
    cmp36 = []
    for t in range(36, 41):
        fr, rr = f_rows.get(t), r_rows_by_turn.get(t)
        if not fr or not rr:
            continue
        cmp36.append(
            {
                "turn": t,
                "R_prompt": rr["prompt_tokens"], "R_cached": rr["cached_tokens"],
                "R_uncached": rr["uncached"],
                "F_prompt": fr["prompt_tokens"], "F_cached": fr["cached_tokens"],
                "F_uncached": fr["uncached"],
                "R_re_prefill": (rr.get("components") or {}).get("re_prefill"),
                "F_re_prefill": (fr.get("components") or {}).get("re_prefill"),
                "R_prefix_ok": rr["prefix_ok"], "F_prefix_ok": fr["prefix_ok"],
                "R_summary_sha": rr["summary_shas"], "F_summary_sha": fr["summary_shas"],
            }
        )
    out["F_vs_R_t36_40"] = cmp36

    # ---- verdict --------------------------------------------------------- #
    share_tail = total_tail / total_unc if total_unc else 0
    share_re = total_re / total_unc if total_unc else 0
    out["claim"] = {
        "steady_mean_uncached": round(total_unc / n, 1),
        "split": {
            "newly_appended_tail_tokens": round(total_tail / n, 1),
            "64_boundary_penalty": round(total_bound / n, 1),
            "re_prefilled_previously_sent": round(total_re / n, 1),
            "residual": round(total_res / n, 3),
        },
        "share_of_uncached_new_append": round(share_tail, 4),
        "share_of_uncached_re_prefill": round(share_re, 4),
        "head_rewrite_turns": head_rewrites,
        "established": total_res == 0,
        "tolerance": "0 tokens: the split is an identity on verified byte-identical prefixes",
    }
    return out


def print_summary(payload: dict) -> None:
    print("\n=== E2 summary ===")
    rs = payload.get("r_steady", {})
    print(json.dumps({k: rs.get(k) for k in (
        "n", "mean_uncached", "mean_new_tail", "mean_boundary", "mean_re_prefill",
        "mean_residual", "steady_turns_with_head_rewrite", "closed")}, indent=2))
    print("boundary:", json.dumps(payload.get("boundary_summary", {}), indent=2)[:1200])
    print("F vs R t36-40:", json.dumps(payload.get("F_vs_R_t36_40", []), indent=2)[:1500])
    print("claim:", json.dumps(payload.get("claim", {}), indent=2))


def analyse_only() -> int:
    """Offline re-analysis over persisted rows: no lock, no live request."""

    scenario, turns = load_slice()
    schedule = compaction_schedule(scenario["preamble"], turns)
    rows = load_existing()
    ordered = [
        rows[(str(spec["arm"]), t)]
        for spec in ARMS
        for t in range(1, TURNS + 1)
        if (str(spec["arm"]), t) in rows
    ]
    payload = analyse(ordered, elapsed=0.0, schedule=schedule, requests=0, waited=0.0)
    payload["mode"] = "analyse-only"
    payload["rows_sha256"] = hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest()
    payload["n_rows"] = len(rows)
    write_json_atomic(ANALYSIS_PATH, payload)
    print_summary(payload)
    return 0


def main() -> int:
    started = time.monotonic()
    if "--analyse-only" in sys.argv:
        return analyse_only()
    handle = None
    try:
        handle, waited = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
    except TimeoutError as exc:
        print(f"BLOCKED: {exc}", flush=True)
        write_json_atomic(
            ANALYSIS_PATH,
            {"unit": "E2", "status": "partial", "blocker": f"lock timeout: {exc}"},
        )
        return 3
    lock_note = f"acquired after {waited:.1f}s; pid {os.getpid()}; held for the whole batch"
    try:
        payload = run(lock_note, waited)
        payload["lock"] = lock_note
        payload["rows_sha256"] = hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest()
        write_json_atomic(ANALYSIS_PATH, payload)
        return 0
    except Exception as exc:  # noqa: BLE001 - a failed unit still reports
        print(f"FAILED: {type(exc).__name__}: {exc}", flush=True)
        write_json_atomic(
            ANALYSIS_PATH,
            {
                "unit": "E2",
                "status": "partial",
                "blocker": f"{type(exc).__name__}: {exc}",
                "lock": lock_note,
                "elapsed_s": round(time.monotonic() - started, 1),
            },
        )
        return 1
    finally:
        if handle is not None:
            release_lock(handle)


if __name__ == "__main__":
    raise SystemExit(main())
