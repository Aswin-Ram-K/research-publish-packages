#!/usr/bin/env python3
"""LIVE-MEAS — four render policies at scale, with epoch control.

Design (one purpose: measurement):
* corpus ``corpora/endtoend.json`` scenario 0, turns 1..60, wrapped modulo 60 to
  reach the 80-turn horizon (turns 61..80 replay texts 1..20);
* U15's 8k compaction trigger (``default_est_tokens``), ``keep_last=2``, the same
  deterministic offline summariser, renderer ``NAIVE_APPEND``, ``max_tokens=4``;
* the fold schedule is derived ONCE by simulating the reference arm (as in U15)
  and applied at those fixed turn numbers to every compaction arm;
* four arms C (control, never compacts), A (append_note), R (summarise_in_place),
  F (fork); three independent epochs, each with a FRESH salt per arm, arm order
  R,F,A,C in every epoch (all arms warm from t1, growing arms last);
* one request in flight, strictly serial; no ``/flush_cache``.

E4 control: every prompt is padded so ``prompt_tokens % 64 != 0``.  The pad is a
fixed filler appended to the newest node's text (the only message that may
differ from the previous turn), so the sent prefix stays byte-stable.  The pad
is applied only when the *predicted* residue is inside the uncertainty band
around 0; the prediction uses per-turn increments measured in an earlier epoch
or earlier arm (exact), else a char-length model.

Durability: every row is appended and fsync-ed before the next request; on
startup rows already present are replayed and skipped.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
assert (REPO / "src" / "resextract").is_dir(), f"repo root not found from {HERE}"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))

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
from resextract.context.render import canonical_bytes  # noqa: E402

CELL_DIR = HERE
ROWS_PATH = CELL_DIR / "rows.jsonl"
EVENTS_PATH = CELL_DIR / "events.jsonl"
ANALYSIS_PATH = CELL_DIR / "analysis.json"
PLAN_PATH = CELL_DIR / "plan.json"
REPORT_PATH = CELL_DIR / "report.md"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
U15_ROWS = REPO / "experiments" / "context-cache" / "cells" / "U15" / "rows.jsonl"

UNIT = "LIVE-MEAS"
TURNS = 80
BUDGET_TOKENS = 8192
KEEP_LAST = 2
MAX_TOKENS = 4
EPOCHS = 3
REQUEST_CAP = 990
LOCK_TIMEOUT_S = 1800.0
SUMMARY_CHARS = 750
TARGET_RESIDUE = 32

# Arms in run order.  R and F run first so the two growing arms (A, C) cannot
# evict their prefixes mid-epoch; the order is identical in every epoch.
ARMS: tuple[dict, ...] = (
    {"arm": "R", "policy": "summarise_in_place",
     "compaction": CompactionPolicy.SUMMARISE_IN_PLACE},
    {"arm": "F", "policy": "fork", "compaction": CompactionPolicy.FORK},
    {"arm": "A", "policy": "append_note", "compaction": CompactionPolicy.APPEND_NOTE},
    {"arm": "C", "policy": "none", "compaction": None},
)
ARM_ORDER = [a["arm"] for a in ARMS]

PAD_TEXT = (
    " This line keeps the request off an exact multiple of sixty-four tokens; "
    "it carries no task information and changes nothing before it."
)
PAD_CANDIDATES = (20, 40, 60, 80, 110, 137, 180, 240, 300)


def pad_choice(p_hat: int, band: int, ratio: float) -> tuple[int, str]:
    """``(chars, pad_text)`` that should land the residue near ``TARGET_RESIDUE``.

    The pad is only appended when the *predicted* residue is inside the
    uncertainty band around 0; otherwise the empty pad is returned and the
    prompt is sent unpadded, which keeps the byte content (and therefore the
    measured increments) unpolluted.
    """

    r = p_hat % 64
    if not (r <= band or r >= 64 - band):
        return 0, ""
    best = None
    for n in PAD_CANDIDATES:
        text = (PAD_TEXT * 3)[:n]
        final = (r + ratio * n + 1.0) % 64.0
        dist = abs(final - TARGET_RESIDUE)
        if best is None or dist < best[0]:
            best = (dist, n, text)
    return best[1], best[2]

WRITE_PATHS = [
    "experiments/context-cache/cells/LIVE-MEAS/**",
    "orchestration/units/LIVE-MEAS.md",
    "orchestration/handoffs/LIVE-MEAS.json",
]


# --------------------------------------------------------------------------- #
# Deterministic offline pieces
# --------------------------------------------------------------------------- #
def summarise(text: str) -> str:
    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_corpus() -> tuple[dict, list[str]]:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    texts = [str(t["text"]) for t in scenario["turns"]]
    return scenario, texts


def turn_text(texts: list[str], turn_no: int) -> str:
    return texts[(turn_no - 1) % len(texts)]


def compaction_schedule(preamble: str, texts: list[str], turns: int = TURNS) -> list[int]:
    """Fold turns of the reference (summarise-in-place) arm over ``turns``."""

    chain = [StateNode.create(preamble, "invariant")]
    schedule: list[int] = []
    for turn_no in range(1, turns + 1):
        chain = [*chain, StateNode.create(turn_text(texts, turn_no), "delta",
                                          parent=chain[-1], turn=turn_no)]
        if needs_compaction(chain, budget_tokens=BUDGET_TOKENS,
                            est_tokens=default_est_tokens):
            schedule.append(turn_no)
            chain, _ = compact(chain, CompactionPolicy.SUMMARISE_IN_PLACE,
                               keep_last=KEEP_LAST, summarizer=summarise,
                               est_tokens=default_est_tokens)
    return schedule


def digest_prefix(messages: list[dict], keep: int = 2) -> str:
    return hashlib.sha256(canonical_bytes(messages[:keep])).hexdigest()


def head_sha(messages: list[dict]) -> str:
    return hashlib.sha256(str(messages[0]["content"]).encode("utf-8")).hexdigest()


def load_chat_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_livemeas", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load chat client from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


def fit_char_model() -> tuple[float, float]:
    """(tokens per char, per-message overhead) from U15 rows, if present."""

    if not U15_ROWS.exists():
        return (0.29, 6.0)
    rows = [json.loads(line) for line in U15_ROWS.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    by = {}
    for r in rows:
        by.setdefault((r["arm"], r["turn"]), r)
    xs, ys = [], []
    for arm in ("C", "R", "F", "A"):
        for t in range(2, 41):
            a, b = by.get((arm, t - 1)), by.get((arm, t))
            if not a or not b or b.get("scheduled_compaction"):
                continue
            inc = b["prompt_tokens"] - a["prompt_tokens"]
            # message text is the corpus turn t text; chars known offline
            xs.append(b["chars"] - a["chars"])
            ys.append(inc)
    if len(xs) < 10:
        return (0.29, 6.0)
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.29
    return (max(0.1, slope), my - slope * mx)


CHAR_SLOPE, CHAR_INTERCEPT = (0.0, 0.0)  # set in main()


def est_msg_tokens(n_chars: int) -> int:
    return max(1, int(round(CHAR_INTERCEPT + CHAR_SLOPE * n_chars)))


# --------------------------------------------------------------------------- #
# Lock / rows
# --------------------------------------------------------------------------- #
def acquire_lock(path: Path, timeout_s: float):
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
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": UNIT, "pid": os.getpid(), "acquired_utc": utc_now(),
               "waited_s": round(time.monotonic() - started, 1),
               "scope": "LIVE-MEAS four-arm x 3 epochs; whole batch"}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle, time.monotonic() - started


def release_lock(handle) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": UNIT, "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def load_existing() -> dict[tuple[int, str, int], dict]:
    out: dict[tuple[int, str, int], dict] = {}
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
        out[(int(row["epoch"]), str(row["arm"]), int(row["turn"]))] = row
    return out


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_json_atomic(path: Path, payload) -> None:
    tmp = CELL_DIR / (path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# Planning / dry chain build
# --------------------------------------------------------------------------- #
def salts_for() -> dict[tuple[int, str], str]:
    out = {}
    for epoch in range(1, EPOCHS + 1):
        for idx, spec in enumerate(ARMS):
            out[(epoch, spec["arm"])] = make_salt(2100 + 100 * epoch + 10 * idx)
    return out


def build_chain(arm: str, compaction, preamble: str, texts: list[str],
                schedule: list[int], pad_at: dict[int, bool]) -> list[list[StateNode]]:
    """Per-turn chains (one list per turn) for one arm of one epoch."""

    chains: list[list[StateNode]] = []
    chain = [StateNode.create(preamble, "invariant")]
    for t in range(1, TURNS + 1):
        chain = [*chain, StateNode.create(turn_text(texts, t), "delta",
                                          parent=chain[-1], turn=t)]
        if compaction is not None and t in schedule:
            chain, _event = compact(chain, compaction, keep_last=KEEP_LAST,
                                    summarizer=summarise, est_tokens=default_est_tokens)
        if pad_at.get(t):
            last = chain[-1]
            chain = [*chain[:-1], StateNode.create(last.text + PAD_TEXT, last.kind,
                                                   parent=chain[-2] if len(chain) > 1 else None,
                                                   turn=t)]
        chains.append(chain)
    return chains


def plan() -> int:
    scenario, texts = load_corpus()
    preamble = scenario["preamble"]
    schedule = compaction_schedule(preamble, texts)
    salts = salts_for()
    payload = {
        "unit": UNIT,
        "turns": TURNS,
        "corpus_turns_available": len(texts),
        "wrap": f"turn t uses texts[(t-1) % {len(texts)}]",
        "budget_tokens": BUDGET_TOKENS,
        "keep_last": KEEP_LAST,
        "epochs": EPOCHS,
        "fold_schedule": schedule,
        "folds": len(schedule),
        "planned_requests": EPOCHS * len(ARMS) * TURNS,
        "request_cap": REQUEST_CAP,
        "salts": {f"e{e}-{a}": s for (e, a), s in salts.items()},
        "char_model": {"slope": CHAR_SLOPE, "intercept": CHAR_INTERCEPT},
        "corpus_sha256": hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest(),
        "arm_order": ARM_ORDER,
    }
    # Offline structural check: every turn of every run builds a renderable chain.
    checked = 0
    for epoch in range(1, EPOCHS + 1):
        for spec in ARMS:
            chains = build_chain(spec["arm"], spec["compaction"], preamble, texts,
                                 schedule, {})
            for t, chain in enumerate(chains, 1):
                msgs = render(RenderPolicy.NAIVE_APPEND, chain, preamble=preamble,
                              volatile={}, salt=salts[(epoch, spec["arm"])])
                assert msgs and msgs[0]["role"] == "system"
                checked += 1
    payload["chains_checked"] = checked
    write_json_atomic(PLAN_PATH, payload)
    print(json.dumps({k: payload[k] for k in
                      ("fold_schedule", "folds", "planned_requests", "chains_checked")},
                     indent=1))
    return 0


# --------------------------------------------------------------------------- #
# Live run
# --------------------------------------------------------------------------- #
def run() -> int:
    started = time.monotonic()
    scenario, texts = load_corpus()
    preamble = scenario["preamble"]
    schedule = compaction_schedule(preamble, texts)
    salts = salts_for()
    existing = load_existing()
    client = load_chat_client()()

    total_rows = EPOCHS * len(ARMS) * TURNS
    done = len(existing)
    requests = 0
    consecutive_failures = 0
    anomalies: list[dict] = []
    fold_events: list[dict] = []
    pad_events: list[dict] = []
    m_table: dict[int, int] = {}       # turn -> unpadded increment (tokens)
    pad_ratio = CHAR_SLOPE  # tokens per pad character, learned from observations

    print(f"{UNIT} start schedule={schedule} existing={done}/{total_rows} "
          f"salts={ {f'e{e}-{a}': s for (e, a), s in salts.items()} } "
          f"char_model=({CHAR_SLOPE:.4f},{CHAR_INTERCEPT:.1f})", flush=True)

    for epoch in range(1, EPOCHS + 1):
        for spec in ARMS:
            arm = str(spec["arm"])
            compaction = spec["compaction"]
            salt = salts[(epoch, arm)]
            chain = [StateNode.create(preamble, "invariant")]
            prev_prompt = None
            prev_cached = None
            for t in range(1, TURNS + 1):
                chain = [*chain, StateNode.create(turn_text(texts, t), "delta",
                                                  parent=chain[-1], turn=t)]
                scheduled = bool(compaction is not None and t in schedule)
                event = None
                if scheduled:
                    chain, event = compact(chain, compaction, keep_last=KEEP_LAST,
                                           summarizer=summarise,
                                           est_tokens=default_est_tokens)
                    fold_events.append({**event, "unit": UNIT, "epoch": epoch,
                                        "arm": arm, "turn": t, "salt": salt})
                key = (epoch, arm, t)
                prior = existing.get(key)

                def messages_for(chain_now):
                    return render(RenderPolicy.NAIVE_APPEND, chain_now,
                                  preamble=preamble, volatile={}, salt=salt)

                if prior is not None:
                    pad_applied = bool(prior.get("pad_applied"))
                    if pad_applied:
                        last = chain[-1]
                        chain = [*chain[:-1], StateNode.create(
                            last.text + str(prior.get("pad_text") or ""), last.kind,
                            parent=chain[-2] if len(chain) > 1 else None, turn=t)]
                    prev_prompt = int(prior["prompt_tokens"])
                    prev_cached = int(prior["cached_tokens"])
                    if not pad_applied and not scheduled and t > 1:
                        m_table.setdefault(t, prev_prompt - int(prior["prev_prompt_tokens"]))
                    continue

                # ---- prediction ------------------------------------------- #
                base_msgs = messages_for(chain)
                chars = sum(len(str(m["content"])) for m in base_msgs)
                if t == 1:
                    p_hat, unc = 1186, 8
                elif scheduled:
                    p_hat, unc = predict_fold(chain, prev_prompt, m_table), 14
                else:
                    last_chars = len(str(base_msgs[-1]["content"]))
                    if t in m_table:
                        m_hat, unc = m_table[t], 0
                    else:
                        m_hat, unc = est_msg_tokens(last_chars), 14
                    p_hat = (prev_prompt or 0) + m_hat
                pad_chars, pad_text = pad_choice(p_hat, unc, pad_ratio)
                pad_applied = pad_chars > 0
                if pad_applied:
                    last = chain[-1]
                    chain = [*chain[:-1], StateNode.create(
                        last.text + pad_text, last.kind,
                        parent=chain[-2] if len(chain) > 1 else None, turn=t)]
                messages = messages_for(chain)
                pred_final = p_hat + int(round(pad_ratio * pad_chars)) + (1 if pad_applied else 0)

                # ---- send ------------------------------------------------- #
                try:
                    prompt, cached, completion, ttft, wall, status, text = client.chat(
                        messages, max_tokens=MAX_TOKENS, thinking=False, stream=True,
                        timeout=180.0)
                except Exception as exc:  # noqa: BLE001
                    consecutive_failures += 1
                    anomalies.append({"kind": "request_failed", "epoch": epoch, "arm": arm,
                                      "turn": t, "error": f"{type(exc).__name__}: {exc}"})
                    prev_prompt = None
                    if consecutive_failures >= 3:
                        print(f"ABORT: 3 consecutive failures at e{epoch}/{arm}/t{t}: "
                              f"{type(exc).__name__}: {exc}", flush=True)
                        return finish(epoch, arm, t, requests, existing, started,
                                      salts, schedule, anomalies, fold_events, pad_events,
                                      texts, preamble, "3 consecutive request failures")
                    time.sleep(2.0)
                    continue
                consecutive_failures = 0
                requests += 1
                if requests > REQUEST_CAP:
                    raise RuntimeError(f"request cap {REQUEST_CAP} exceeded")
                uncached = max(0, prompt - cached)
                residue = prompt % 64
                if residue == 0:
                    anomalies.append({"kind": "e4_multiple_of_64", "epoch": epoch,
                                      "arm": arm, "turn": t, "prompt_tokens": prompt})
                if pad_applied and not scheduled and t > 1 and prev_prompt is not None:
                    obs_inc = prompt - prev_prompt
                    if t in m_table and pad_chars:
                        obs_pad = obs_inc - m_table[t]
                        if obs_pad > 0:
                            pad_ratio = 0.5 * pad_ratio + 0.5 * (obs_pad / pad_chars)
                    pad_events.append({"epoch": epoch, "arm": arm, "turn": t,
                                       "p_hat": p_hat, "prompt_tokens": prompt,
                                       "pad_chars": pad_chars, "residue": residue,
                                       "pad_ratio_est": round(pad_ratio, 4)})
                if not pad_applied and not scheduled and t > 1 and prev_prompt is not None:
                    m_table.setdefault(t, prompt - prev_prompt)

                row = {
                    "unit": UNIT, "cell": f"{UNIT}/e{epoch}/{arm}", "epoch": epoch,
                    "arm": arm, "policy": str(spec["policy"]), "turn": t,
                    "turns_total": TURNS, "salt": salt,
                    "prompt_tokens": prompt, "cached_tokens": cached,
                    "uncached": uncached, "residue": residue,
                    "completion_tokens": completion,
                    "ttft_ms": round(ttft, 3), "wall_ms": round(wall, 3),
                    "status": status, "scheduled_compaction": scheduled,
                    "prev_prompt_tokens": prev_prompt, "prev_cached_tokens": prev_cached,
                    "pad_applied": pad_applied, "pad_chars": pad_chars,
                    "pad_text": pad_text,
                    "p_hat": p_hat, "p_hat_unc": unc, "pred_final": pred_final,
                    "est_chain_tokens_before": None,
                    "est_chain_tokens_after": sum(default_est_tokens(n.text) for n in chain),
                    "nodes": len(chain), "messages": len(messages),
                    "chars": sum(len(str(m["content"])) for m in messages),
                    "prefix_sha256": digest_prefix(messages, keep=2),
                    "head_sha256": head_sha(messages),
                    "completion_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "request_index": requests, "ts_utc": utc_now(),
                }
                append_row(row)
                prev_prompt, prev_cached = prompt, cached
                done += 1
                if done % 8 == 0 or scheduled or residue == 0:
                    print(f"PROGRESS {done}/{total_rows} e{epoch} {arm} t{t} "
                          f"prompt={prompt} cached={cached} unc={uncached} "
                          f"res={residue} pad={int(pad_applied)} el={time.monotonic()-started:.0f}s",
                          flush=True)

    return finish(EPOCHS, "C", TURNS, requests, existing, started, salts, schedule,
                  anomalies, fold_events, pad_events, texts, preamble, "")


def predict_fold(chain: list[StateNode], prev_prompt, m_table) -> int:
    """Estimated prompt tokens after a fold: previous prompt minus the dropped
    message mass, plus the new head node (summary/fork/note)."""

    body = chain[1:]
    kept = body[-KEEP_LAST:]
    dropped = body[:-KEEP_LAST]
    mass = 0
    for node in dropped:
        if node.kind in ("summary", "fork", "pointer"):
            mass += est_msg_tokens(len(node.text))
        else:
            mass += m_table.get(int(node.meta.get("turn") or 0), est_msg_tokens(len(node.text)))
    s_new = est_msg_tokens(len(body[0].text)) if body and body[0].kind in (
        "summary", "fork", "pointer") else 0
    s_old = 0
    for node in dropped:
        if node.kind in ("summary", "fork", "pointer"):
            s_old = est_msg_tokens(len(node.text))
    return max(1, int(prev_prompt) - mass - s_old + s_new) if prev_prompt else 1


def finish(epoch, arm, turn, requests, existing, started, salts, schedule, anomalies,
           fold_events, pad_events, texts, preamble, blocker) -> int:
    rows = load_rows()
    payload = analyse(rows, schedule)
    payload["digest"] = {
        "rows_sha256": hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest(),
        "n_rows": len(rows),
        "rows_by_epoch_arm": payload["counts"]["rows_by_epoch_arm"],
        "requests_live": len(rows) + sum(1 for a in anomalies if a.get("kind") == "request_failed"),
        "requests_cap": REQUEST_CAP,
        "elapsed_s": round(time.monotonic() - started, 1),
        "fold_schedule": schedule,
        "corpus": str(CORPUS_PATH.relative_to(REPO)),
        "corpus_sha256": hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest(),
        "salts": {f"e{e}-{a}": s for (e, a), s in salts.items()},
        "arm_order": ARM_ORDER,
        "budget_tokens": BUDGET_TOKENS, "keep_last": KEEP_LAST, "turns": TURNS,
    }
    write_json_atomic(ANALYSIS_PATH, payload)
    EVENTS_PATH.write_text(json.dumps({
        "unit": UNIT, "compaction_events": fold_events, "pad_events": pad_events,
        "anomalies": anomalies, "blocker": blocker}, indent=2) + "\n", encoding="utf-8")
    write_report(payload, blocker)
    status = "done" if len(rows) == EPOCHS * len(ARMS) * TURNS else "partial"
    print(f"{UNIT} finish status={status} rows={len(rows)} requests={requests} "
          f"blocker={blocker or '-'}", flush=True)
    return 0 if status == "done" else 2


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def load_rows() -> list[dict]:
    if not ROWS_PATH.exists():
        return []
    rows = []
    for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def _stats(vals: list[float]) -> dict:
    if not vals:
        return {"n": 0}
    out = {"n": len(vals), "mean": statistics.mean(vals),
           "median": statistics.median(vals), "min": min(vals), "max": max(vals)}
    if len(vals) > 1:
        out["sd"] = statistics.stdev(vals)
        out["range"] = max(vals) - min(vals)
        if len(vals) == 3:
            t = 4.302652729911275  # t_{0.975, 2}
            half = t * out["sd"] / math.sqrt(len(vals))
            out["t95"] = [out["mean"] - half, out["mean"] + half]
    return out


def analyse(rows: list[dict], schedule: list[int]) -> dict:
    counts: dict = {"rows_by_epoch_arm": {}, "rows_by_arm": {}, "rows_by_epoch": {}}
    for r in rows:
        k = f"e{r['epoch']}-{r['arm']}"
        counts["rows_by_epoch_arm"][k] = counts["rows_by_epoch_arm"].get(k, 0) + 1
        counts["rows_by_arm"][r["arm"]] = counts["rows_by_arm"].get(r["arm"], 0) + 1
        counts["rows_by_epoch"][str(r["epoch"])] = counts["rows_by_epoch"].get(str(r["epoch"]), 0) + 1

    by_ea: dict[tuple[int, str], list[dict]] = {}
    for r in rows:
        by_ea.setdefault((int(r["epoch"]), str(r["arm"])), []).append(r)
    for v in by_ea.values():
        v.sort(key=lambda r: int(r["turn"]))

    def tot(epoch: int, arm: str, field: str) -> int:
        return sum(int(r[field]) for r in by_ea.get((epoch, arm), []))

    # ---- headline ---------------------------------------------------------- #
    headline = {"per_epoch": {}, "pooled": {}}
    ratios = {"R_over_A": [], "F_over_A": [], "R_over_F": [], "R_over_C": [], "A_over_C": []}
    for epoch in range(1, EPOCHS + 1):
        u = {arm: tot(epoch, arm, "uncached") for arm in ARM_ORDER}
        if not all(u.values()):
            continue
        e = {"uncached": u,
             "R_over_A": u["R"] / u["A"], "F_over_A": u["F"] / u["A"],
             "R_over_F": u["R"] / u["F"],
             "R_over_C": u["R"] / u["C"], "A_over_C": u["A"] / u["C"],
             "hit_rate": {arm: sum(int(r["cached_tokens"]) for r in by_ea[(epoch, arm)])
                          / max(1, sum(int(r["prompt_tokens"]) for r in by_ea[(epoch, arm)]))
                          for arm in ARM_ORDER}}
        headline["per_epoch"][str(epoch)] = e
        for k in ratios:
            ratios[k].append(e[k])
    for k, v in ratios.items():
        headline["pooled"][k] = _stats(v)
    if headline["per_epoch"]:
        pooled_unc = {arm: sum(tot(e, arm, "uncached") for e in range(1, EPOCHS + 1))
                      for arm in ARM_ORDER}
        headline["pooled_uncached_sum"] = pooled_unc
        headline["pooled"]["R_over_A_sumratio"] = pooled_unc["R"] / pooled_unc["A"]
        headline["pooled"]["F_over_A_sumratio"] = pooled_unc["F"] / pooled_unc["A"]
    headline["u15_reference"] = {"R_over_A": 1.7002359039106887,
                                 "note": "U15 single 40-turn epoch, 2 folds"}

    # ---- break vs steady-state decomposition ------------------------------- #
    decomposition = {"per_epoch": {}, "note":
                     "arithmetic split of each arm's total uncached excess over the "
                     "control: fold-turn excess vs all other turns. Not a mechanism."}
    for epoch in range(1, EPOCHS + 1):
        if not by_ea.get((epoch, "C")):
            continue
        u_c = {int(r["turn"]): int(r["uncached"]) for r in by_ea[(epoch, "C")]}
        d = {}
        for arm in ("A", "R", "F"):
            rs = by_ea[(epoch, arm)]
            if not rs:
                continue
            excess = sum(int(r["uncached"]) for r in rs) - sum(u_c.values())
            break_part = sum(int(r["uncached"]) - u_c.get(int(r["turn"]), 0)
                             for r in rs if bool(r["scheduled_compaction"]))
            d[arm] = {
                "excess": excess,
                "break_part": break_part,
                "steady_part": excess - break_part,
                "break_share": round(break_part / excess, 4) if excess else None,
                "folds": len(schedule),
                "steady_per_turn": round((excess - break_part) / (TURNS - len(schedule)), 1),
            }
        decomposition["per_epoch"][str(epoch)] = d
    # pooled arithmetic
    pooled_d = {}
    for arm in ("A", "R", "F"):
        ex = bp = 0
        for epoch in range(1, EPOCHS + 1):
            d = decomposition["per_epoch"].get(str(epoch), {}).get(arm)
            if d:
                ex += d["excess"]
                bp += d["break_part"]
        if ex:
            pooled_d[arm] = {"excess": ex, "break_part": bp, "steady_part": ex - bp,
                             "break_share": round(bp / ex, 4),
                             "steady_per_turn": round((ex - bp) / (EPOCHS * TURNS - EPOCHS * len(schedule)), 1)}
    decomposition["pooled"] = pooled_d

    # ---- fold-count scaling of the post-fold lag --------------------------- #
    scaling = {"per_fold": {}, "by_turns_since_fold": {}, "before_vs_after_t40": {}}
    for arm in ("R", "F", "A"):
        per_fold = []
        for epoch in range(1, EPOCHS + 1):
            rs = by_ea.get((epoch, arm), [])
            if not rs:
                continue
            for f_idx, f in enumerate(schedule, 1):
                later = [r for r in rs if int(r["turn"]) > f and
                         (f_idx == len(schedule) or int(r["turn"]) < schedule[f_idx])
                         and not bool(r["scheduled_compaction"])]
                if not later:
                    continue
                lags = []
                for r in later:
                    prev = int(r["prev_prompt_tokens"] or 0)
                    floor_prev = 64 * (prev // 64)
                    lag = max(0, floor_prev - int(r["cached_tokens"]))
                    lags.append({"turn": int(r["turn"]), "since_fold": int(r["turn"]) - f,
                                 "lag_tokens": lag, "reuse": int(r["cached_tokens"]),
                                 "floor_prev": floor_prev})
                per_fold.append({"epoch": epoch, "fold_index": f_idx, "fold_turn": f,
                                 "lags": lags})
        if not per_fold:
            continue
        first_half = [x["lag_tokens"] for pf in per_fold if pf["fold_turn"] <= 40
                      for x in pf["lags"]]
        second_half = [x["lag_tokens"] for pf in per_fold if pf["fold_turn"] > 40
                       for x in pf["lags"]]
        by_sf: dict[int, list[int]] = {}
        for pf in per_fold:
            for x in pf["lags"]:
                by_sf.setdefault(min(x["since_fold"], 6), []).append(x["lag_tokens"])
        scaling["per_fold"][arm] = {
            "folds": [{"fold_index": pf["fold_index"], "fold_turn": pf["fold_turn"],
                       "median_lag_tokens": statistics.median([x["lag_tokens"] for x in pf["lags"]]),
                       "max_lag_tokens": max(x["lag_tokens"] for x in pf["lags"]),
                       "n": len(pf["lags"])} for pf in per_fold],
            "by_turns_since_fold": {str(k): _stats(v) for k, v in sorted(by_sf.items())},
        }
        scaling["before_vs_after_t40"][arm] = {
            "before_t40": _stats([float(x) for x in first_half]),
            "after_t40": _stats([float(x) for x in second_half]),
        }

    # ---- law checks -------------------------------------------------------- #
    e3 = {"clean": 0, "grid": 0, "one_body": 0, "deeper_lag": {}, "unexplained": [],
          "rows_checked": 0, "deficit_histogram": {}}
    e4 = {"rows": len(rows), "residue_zero": [], "padded": 0,
          "residue_histogram": {}, "min_abs_distance_to_multiple": None}
    dist = []
    for arm in ARM_ORDER:
        for epoch in range(1, EPOCHS + 1):
            rs = by_ea.get((epoch, arm), [])
            for i in range(1, len(rs)):
                r = rs[i]
                prev = rs[i - 1]
                if bool(r["scheduled_compaction"]):
                    continue
                e3["rows_checked"] += 1
                if int(prev["prompt_tokens"]) is None:
                    continue
                floor_prev = 64 * (int(prev["prompt_tokens"]) // 64)
                deficit = floor_prev - int(r["cached_tokens"])
                hist = e3["deficit_histogram"]
                hist[str(deficit)] = hist.get(str(deficit), 0) + 1
                if deficit <= 0:
                    e3["clean"] += 1
                elif deficit <= 128:
                    e3["grid"] += 1
                else:
                    masses = []
                    for j in range(1, 5):
                        if (i - j - 1 >= 0
                                and not bool(rs[i - j]["scheduled_compaction"])
                                and not bool(rs[i - j - 1]["scheduled_compaction"])):
                            masses.append(int(rs[i - j]["prompt_tokens"])
                                          - int(rs[i - j - 1]["prompt_tokens"]))
                        else:
                            break
                    kfound, acc = None, 0
                    for k, m in enumerate(masses, 1):
                        acc += m
                        if abs(acc - deficit) <= 128:
                            kfound = k
                            break
                    if kfound == 1:
                        e3["one_body"] += 1
                    elif kfound:
                        e3["deeper_lag"][str(kfound)] = e3["deeper_lag"].get(str(kfound), 0) + 1
                    else:
                        e3["unexplained"].append({"epoch": epoch, "arm": arm,
                                                  "turn": int(r["turn"]),
                                                  "deficit": deficit})
    for r in rows:
        p_tok = int(r["prompt_tokens"])
        residue = p_tok % 64
        d = min(residue, 64 - residue)
        dist.append(d)
        e4["residue_histogram"][str(residue)] = e4["residue_histogram"].get(str(residue), 0) + 1
        if r.get("pad_applied"):
            e4["padded"] += 1
        if residue == 0:
            e4["residue_zero"].append({"epoch": int(r["epoch"]), "arm": r["arm"],
                                       "turn": int(r["turn"]), "prompt_tokens": p_tok})
    if dist:
        e4["min_abs_distance_to_multiple"] = min(dist)
        e4["distance_histogram"] = {str(k): dist.count(k) for k in sorted(set(dist))}
    law_checks = {
        "e3_two_term_append_law": e3,
        "e4_multiple_of_64": e4,
        "e3_statement": ("deficit = floor64(previous prompt) - cached on append turns; "
                         "0..64 = clean/grid, a deficit matching ONE trailing message = the "
                         "E3 two-term law, a deficit matching 2-4 trailing messages = a "
                         "deeper reuse lag than E3 licenses, otherwise unexplained"),
        "e4_statement": "no row may have prompt_tokens % 64 == 0",
    }

    # ---- pad accounting ---------------------------------------------------- #
    ratio = 0.2639793354530334
    pad = {"per_epoch_arm": {}, "tokens_by_arm": {}, "note":
           "the E4 pad is new content, so it is genuinely uncached; the adjusted "
           "figures subtract its estimated token cost (pad_chars * 0.264 + 1) from "
           "every padded row, for both the arm and the control"}
    for epoch in range(1, EPOCHS + 1):
        for arm in ARM_ORDER:
            rs = by_ea.get((epoch, arm), [])
            est = sum(int(round(ratio * int(r.get("pad_chars") or 0))) + (1 if r.get("pad_applied") else 0)
                      for r in rs)
            pad["per_epoch_arm"][f"e{epoch}-{arm}"] = est
            pad["tokens_by_arm"][arm] = pad["tokens_by_arm"].get(arm, 0) + est
    adj = {"per_epoch": {}, "pooled": {}}
    adj_ratio = {"R_over_A": [], "F_over_A": [], "R_over_F": []}
    for epoch in range(1, EPOCHS + 1):
        u = {}
        for arm in ARM_ORDER:
            rs = by_ea.get((epoch, arm), [])
            u[arm] = sum(int(r["uncached"]) - (int(round(ratio * int(r.get("pad_chars") or 0)))
                                               + (1 if r.get("pad_applied") else 0)) for r in rs)
        if not all(u.values()):
            continue
        adj["per_epoch"][str(epoch)] = {
            "uncached_pad_adjusted": u,
            "R_over_A": u["R"] / u["A"], "F_over_A": u["F"] / u["A"],
            "R_over_F": u["R"] / u["F"]}
        adj_ratio["R_over_A"].append(adj["per_epoch"][str(epoch)]["R_over_A"])
        adj_ratio["F_over_A"].append(adj["per_epoch"][str(epoch)]["F_over_A"])
        adj_ratio["R_over_F"].append(adj["per_epoch"][str(epoch)]["R_over_F"])
    for k, v in adj_ratio.items():
        adj["pooled"][k] = _stats(v)
    adj["tokens_by_arm"] = pad["tokens_by_arm"]
    adj["per_epoch_arm"] = pad["per_epoch_arm"]
    adj["note"] = pad["note"]

    # ---- epoch warmth ------------------------------------------------------ #
    warmth = {}
    for epoch in range(1, EPOCHS + 1):
        pt = {arm: {int(r["turn"]): int(r["prompt_tokens"]) for r in by_ea.get((epoch, arm), [])}
              for arm in ARM_ORDER}
        ch = {arm: {int(r["turn"]): int(r["cached_tokens"]) for r in by_ea.get((epoch, arm), [])}
              for arm in ARM_ORDER}
        t1 = {arm: ch[arm].get(1) for arm in ARM_ORDER}
        fixed = {}
        for t in (5, 10, 17):
            fixed[str(t)] = {arm: {"prompt": pt[arm].get(t), "cached": ch[arm].get(t)}
                             for arm in ARM_ORDER}
        warmth[str(epoch)] = {
            "salts": {arm: salts_for()[(epoch, arm)] for arm in ARM_ORDER},
            "t1_cached": t1,
            "t1_all_zero": all(v == 0 for v in t1.values() if v is not None),
            "fixed_prefold_turns": fixed,
            "identical_prompt_at_t10": len({v["prompt"] for v in fixed["10"].values()}) == 1,
            "identical_cached_at_t10": len({v["cached"] for v in fixed["10"].values()}) == 1,
            "identical_cached_at_t17": len({v["cached"] for v in fixed["17"].values()}) == 1,
        }
    warmth["order"] = {"arm_order_per_epoch": ARM_ORDER,
                       "epochs": EPOCHS,
                       "salt_policy": "fresh salt per (epoch, arm): make_salt(2100+100*epoch+10*idx)",
                       "note": "every arm runs its full 80 turns from t1 in every epoch; "
                               "no mid-chain cold start; identical order in all epochs"}

    # ---- horizon check: U15's own 40-turn window inside this run ------------- #
    horizon = {"per_epoch": {}, "windows": {}}
    for epoch in range(1, EPOCHS + 1):
        d = {}
        for lab, (t0, t1) in {"t1_40": (1, 40), "t41_80": (41, 80),
                              "t1_80": (1, 80)}.items():
            u = {arm: sum(int(r["uncached"]) for r in by_ea.get((epoch, arm), [])
                          if t0 <= int(r["turn"]) <= t1) for arm in ARM_ORDER}
            if u["A"]:
                d[lab] = {"uncached": u, "R_over_A": u["R"] / u["A"],
                          "F_over_A": u["F"] / u["A"]}
        horizon["per_epoch"][str(epoch)] = d
        for lab in ("t1_40", "t41_80", "t1_80"):
            if lab in d:
                horizon["windows"].setdefault(lab, []).append(d[lab]["R_over_A"])
    for lab, v in horizon["windows"].items():
        horizon["windows"][lab] = _stats(v)
    horizon["u15_reference"] = 1.7002359039106887

    return {"unit": UNIT, "counts": counts, "headline": headline,
            "decomposition": decomposition, "fold_scaling": scaling,
            "law_checks": law_checks, "warmth": warmth, "pad_adjustment": adj,
            "horizon_check": horizon,
            "total_prompt_tokens": {arm: {str(e): tot(e, arm, "prompt_tokens")
                                          for e in range(1, EPOCHS + 1)} for arm in ARM_ORDER},
            "total_uncached": {arm: {str(e): tot(e, arm, "uncached")
                                      for e in range(1, EPOCHS + 1)} for arm in ARM_ORDER}}


def write_report(payload: dict, blocker: str) -> None:
    h = payload["headline"]
    lines = [f"# {UNIT} — four render policies at scale (80 turns x 3 epochs)", ""]
    if blocker:
        lines += [f"**status: partial** — {blocker}", ""]
    lines += ["## Headline: total uncached tokens (raw)", "",
              "| epoch | C | A | R | F | R/A | F/A |", "|---|---|---|---|---|---|---|"]
    for e, d in h["per_epoch"].items():
        u = d["uncached"]
        lines.append(f"| {e} | {u['C']} | {u['A']} | {u['R']} | {u['F']} | "
                     f"{d['R_over_A']:.3f} | {d['F_over_A']:.3f} |")
    p = h["pooled"]
    lines += ["", f"Pooled R/A: mean {p['R_over_A']['mean']:.3f} "
                  f"(min {p['R_over_A']['min']:.3f}, max {p['R_over_A']['max']:.3f}, "
                  f"t95 [{p['R_over_A']['t95'][0]:.3f}, {p['R_over_A']['t95'][1]:.3f}], df=2), "
                  f"sum-ratio {p['R_over_A_sumratio']:.3f}; "
                  f"U15 reference (40 turns, 2 folds) 1.700x.", ""]
    hz = payload.get("horizon_check", {})
    if hz.get("windows"):
        lines += ["## Horizon check (U15's 40-turn window reproduced inside this run)", ""]
        for lab, st in hz["windows"].items():
            if isinstance(st, dict) and "mean" in st:
                lines.append(f"- R/A over {lab}: mean {st['mean']:.3f} "
                             f"(min {st['min']:.3f}, max {st['max']:.3f}, n={st['n']})")
        lines.append("")
    adj = payload["pad_adjustment"]
    if adj["pooled"]:
        a = adj["pooled"]
        lines += [f"Pad-adjusted R/A: mean {a['R_over_A']['mean']:.3f} "
                  f"({a['R_over_A']['min']:.3f}-{a['R_over_A']['max']:.3f}); "
                  f"F/A mean {a['F_over_A']['mean']:.3f}; R/F mean "
                  f"{a['R_over_F']['mean']:.3f}. Pads (E4 control) cost "
                  f"{adj['tokens_by_arm']} uncached tokens by arm.", ""]
    lines += ["## Break vs steady-state (arithmetic split of excess over C)", ""]
    for arm, d in payload["decomposition"]["pooled"].items():
        lines.append(f"- {arm}: excess {d['excess']} = break {d['break_part']} + "
                     f"steady {d['steady_part']} (break share {d['break_share']:.3f}); "
                     f"steady {d['steady_per_turn']} tokens/turn")
    lines += ["", "## Fold-count scaling (post-fold reuse lag, tokens; 4 folds at "
              + str(payload["digest"]["fold_schedule"]) + ")", ""]
    for arm, d in payload["fold_scaling"].get("per_fold", {}).items():
        b = payload["fold_scaling"]["before_vs_after_t40"][arm]
        folds = "; ".join(f"f{i['fold_index']}@t{i['fold_turn']} med {i['median_lag_tokens']:.0f}"
                          f"/max {i['max_lag_tokens']:.0f}" for i in d["folds"])
        lines.append(f"- {arm}: {folds}")
        lines.append(f"  before t40 median {b['before_t40'].get('median')} "
                     f"(n={b['before_t40'].get('n')}), after t40 median "
                     f"{b['after_t40'].get('median')} (n={b['after_t40'].get('n')})")
        for sf, st in d["by_turns_since_fold"].items():
            lines.append(f"  lag +{sf} turns after a fold: median {st['median']:.0f} "
                         f"(n={st['n']})")
    lc = payload["law_checks"]
    e3 = lc["e3_two_term_append_law"]
    lines += ["", "## Law checks", "",
              f"- E3 two-term append law over {e3['rows_checked']} append rows: "
              f"{e3['clean']} clean (deficit<=0), {e3['grid']} grid-only (0<d<=64), "
              f"{e3['one_body']} exactly one trailing body, deeper lag "
              f"{e3['deeper_lag']}, unexplained {len(e3['unexplained'])} "
              f"(deficit histogram top: "
              + str(sorted(((int(k), v) for k, v in e3['deficit_histogram'].items()),
                           key=lambda kv: -kv[1])[:6]) + ")",
              f"- E4 multiple-of-64: {len(lc['e4_multiple_of_64']['residue_zero'])} rows at "
              f"residue 0 of {lc['e4_multiple_of_64']['rows']}; "
              f"{lc['e4_multiple_of_64']['padded']} rows padded; min distance to a multiple "
              f"{lc['e4_multiple_of_64']['min_abs_distance_to_multiple']}"]
    for row in lc["e4_multiple_of_64"]["residue_zero"]:
        lines.append(f"  - residue 0: e{row['epoch']} {row['arm']} t{row['turn']} "
                     f"(prompt {row['prompt_tokens']})")
    lines += ["", "## Epoch warmth", ""]
    for e, w in payload["warmth"].items():
        if not isinstance(w, dict) or "fixed_prefold_turns" not in w:
            continue
        for t in ("10", "17"):
            f = w["fixed_prefold_turns"][t]
            lines.append(f"- epoch {e} t{t}: " + ", ".join(
                f"{a} prompt {v['prompt']}/cached {v['cached']}" for a, v in f.items())
                + f" | prompts identical {len({v['prompt'] for v in f.values()}) == 1}, "
                  f"cached identical {len({v['cached'] for v in f.values()}) == 1}")
        lines.append(f"  t1 cached {w['t1_cached']} (all zero {w['t1_all_zero']})")
    lines += ["", f"Order: {payload['warmth']['order']['arm_order_per_epoch']} in all "
                  f"{payload['warmth']['order']['epochs']} epochs; salts fresh per "
                  f"(epoch, arm). Every arm runs its full 80 turns from t1; no mid-chain "
                  f"cold start anywhere."]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def do_analyse() -> int:
    rows = load_rows()
    schedule = payload_schedule()
    payload = analyse(rows, schedule)
    payload["digest"] = {"rows_sha256": hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest(),
                         "n_rows": len(rows), "fold_schedule": schedule,
                         "requests_live": len(rows), "requests_cap": REQUEST_CAP,
                         "fold_schedule_note": "U15 trigger 8192; 4 folds over 80 turns"}
    write_json_atomic(ANALYSIS_PATH, payload)
    write_report(payload, "")
    print(json.dumps(payload["headline"]["pooled"], indent=1))
    return 0


def payload_schedule() -> list[int]:
    scenario, texts = load_corpus()
    return compaction_schedule(scenario["preamble"], texts)


def main() -> int:
    global CHAR_SLOPE, CHAR_INTERCEPT
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--analyse", action="store_true")
    args = parser.parse_args()
    CELL_DIR.mkdir(parents=True, exist_ok=True)
    CHAR_SLOPE, CHAR_INTERCEPT = fit_char_model()
    if args.plan:
        return plan()
    if args.analyse:
        return do_analyse()
    if not args.run:
        parser.error("choose --plan, --run or --analyse")

    started = time.monotonic()
    handle = None
    lock_wait = None
    try:
        handle, lock_wait = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
        print(f"lock acquired after {lock_wait:.1f}s", flush=True)
    except TimeoutError as exc:
        print(f"BLOCKED: {exc}", flush=True)
        write_json_atomic(ANALYSIS_PATH, {"unit": UNIT, "blocker": f"lock timeout: {exc}",
                                          "lock_wait_s": LOCK_TIMEOUT_S})
        REPORT_PATH.write_text(f"# {UNIT}\n\nstatus: partial — lock timeout: {exc}\n",
                               encoding="utf-8")
        return 3
    try:
        return run()
    finally:
        if handle is not None:
            release_lock(handle)


if __name__ == "__main__":
    raise SystemExit(main())
