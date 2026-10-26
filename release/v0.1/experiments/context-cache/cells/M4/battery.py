#!/usr/bin/env python3
"""M4-EVICT — eviction pressure: what does the LRU do **past** the KV capacity?

Every context-cache cell measured before M4 ran inside the cache.  The live
server reports a KV pool of ``token_capacity`` tokens (re-profiled at every
start, so it is *measured here per run* from ``/get_server_info`` rather than
read from ``state/config/live-server-config.json``).  This cell fills that pool
past its capacity and then asks two questions:

* **Phase R (replay)** — after 1.5x capacity has been pushed through, which
  documents are still resident?  If the policy is LRU: the oldest band is gone
  (≈0 cached) and the newest band is intact (≈full hit).  Whatever the profile
  actually is, it is reported.
* **Phase D (discipline under pressure)** — the append-note/pointer discipline
  claims that an append never rewrites the cacheable prefix, so extending a
  document costs only the appended tokens.  Past capacity that claim is worth
  exactly as much as the prefix's residency: this cell measures both shapes on
  the middle band's adjacent slice (3 documents each).

One request in flight, strictly serial, ``temperature 0``, ``max_tokens 4``.
Holds ``experiments/context-cache/.occamy.lock`` for the whole run.

The cell never restarts, stops or reconfigures the model; it only sends chat
completions and one ``/get_server_info`` diagnostic at the start.
"""
from __future__ import annotations

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

import httpx

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

import corpus as corpus_mod  # noqa: E402

CELL_DIR = HERE
ROWS_PATH = CELL_DIR / "rows.jsonl"
ANALYSIS_PATH = CELL_DIR / "analysis.json"
CORPUS_PATH = CELL_DIR / "corpus.jsonl"
MANIFEST_PATH = CELL_DIR / "corpus_manifest.json"
SERVER_INFO_PATH = CELL_DIR / "server_info.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CONFIG_PATH = REPO / "state" / "config" / "live-server-config.json"
HANDOFF_PATH = REPO / "orchestration" / "handoffs" / "M4-EVICT.json"

UNIT = "M4-EVICT"
STACK = "sglang"
ENDPOINT = "http://serving-host"
CONFIG_ID = "LIVE"
CONFIG_SHA256 = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()

# ---------------------------------------------------------------------------
# Bounds from the unit card
# ---------------------------------------------------------------------------
REQUEST_CAP = 600          # live chat completions, hard cap
MAX_DOCS = 300             # if the corpus would exceed 300 documents, resize the documents
DOC_TARGET_EST = 10400     # per-document size for the offline estimator (see assumptions)
TARGET_RATIO = 1.5         # pressure target: cumulative prompt tokens / capacity
FALLBACK_RATIO = 1.2       # card's shortened pressure if Phase P would blow the wall bound
WALL_BOUND_S = 90 * 60     # 90 minutes
P_WALL_GUARD_S = 40 * 60   # leave room for R and D
LOCK_TIMEOUT_S = 300.0
MAX_TOKENS = 4
TIMEOUT_S = 120.0
CONSECUTIVE_FAILURE_LIMIT = 3

# Phase R bands: the oldest 10, a middle 10, the newest 10.
BAND_SIZE = 10
# Phase D: 3 documents per shape, taken from the slice immediately after the
# middle band so the Phase-R replay set cannot double-warm them.
D_DOCS_PER_SHAPE = 3

# Prefill throughput floor used only for the wall-time projection in Phase P.
P_PROJECTION_SAMPLE = 25
CALIBRATION_REQUESTS = 69  # the aborted sizing run kept in calibration_aborted_run.jsonl


# ---------------------------------------------------------------------------
# Small utilities (same conventions as the G3 cell)
# ---------------------------------------------------------------------------
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, payload) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_prompt(messages) -> str:
    return sha256_bytes(json.dumps(messages, sort_keys=True).encode("utf-8"))


def load_chat_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_m4", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.ChatClient


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
                raise TimeoutError(f"occamy lock {path} busy")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": UNIT, "pid": os.getpid(), "acquired_utc": utc_now()}, handle)
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


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def log(path: Path, message: str) -> None:
    line = f"{utc_now()} {message}"
    print(line, flush=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()


# ---------------------------------------------------------------------------
# Capacity, measured per run
# ---------------------------------------------------------------------------
def measure_capacity() -> dict:
    """``token_capacity`` from the server itself, never from a stale sample."""

    started = time.monotonic()
    with httpx.Client(timeout=30.0) as http:
        response = http.get(f"{ENDPOINT}/get_server_info")
    response.raise_for_status()
    raw = response.content
    payload = response.json()
    states = payload.get("internal_states") or [{}]
    state = states[0] if states else {}
    memory = state.get("memory_usage") or {}
    capacity = memory.get("token_capacity") or payload.get("max_total_num_tokens")
    if not isinstance(capacity, int) or capacity <= 0:
        raise RuntimeError(f"no usable token_capacity in /get_server_info: {capacity!r}")
    info = {
        "endpoint": f"{ENDPOINT}/get_server_info",
        "http_status": response.status_code,
        "sampled_utc": utc_now(),
        "latency_ms": round((time.monotonic() - started) * 1000, 3),
        "token_capacity": capacity,
        "token_capacity_swa": memory.get("token_capacity_swa"),
        "max_total_num_tokens": payload.get("max_total_num_tokens"),
        "kvcache_gib": memory.get("kvcache"),
        "weight_gib": memory.get("weight"),
        "server_version": payload.get("version"),
        "server_status": payload.get("status"),
        "max_running_requests": state.get("max_running_requests"),
        "page_size": state.get("page_size"),
        "radix_eviction_policy": state.get("radix_eviction_policy"),
        "disable_radix_cache": state.get("disable_radix_cache"),
        "disable_chunked_prefix_cache": state.get("disable_chunked_prefix_cache"),
        "chunked_prefill_size": state.get("chunked_prefill_size"),
        "max_prefill_tokens": state.get("max_prefill_tokens"),
        "context_length": state.get("context_length"),
        "max_mamba_cache_size": state.get("max_mamba_cache_size"),
        "mamba_track_interval": state.get("mamba_track_interval"),
        "uses_mamba_radix_cache": state.get("uses_mamba_radix_cache"),
        "_mamba_cache_chunk_size": state.get("_mamba_cache_chunk_size"),
        "info_sha256": sha256_bytes(raw),
        "info_bytes": len(raw),
    }
    SERVER_INFO_PATH.write_bytes(raw)
    return info


# ---------------------------------------------------------------------------
# One request
# ---------------------------------------------------------------------------
class Sender:
    """Serial sender: one request in flight, counted against the hard cap."""

    def __init__(self) -> None:
        client_cls = load_chat_client()
        self._client = client_cls()
        self.sent = 0
        self.failures = 0
        self.consecutive_failures = 0
        self.first_error = None

    def send(self, messages) -> dict:
        if self.sent >= REQUEST_CAP:
            raise RuntimeError(f"request cap reached: {self.sent}/{REQUEST_CAP}")
        started = time.perf_counter()
        self.sent += 1
        out = {"request_index": self.sent, "status": None, "error": "", "ts_utc": utc_now()}
        try:
            prompt, cached, completion, ttft, wall, status, _text = self._client.chat(
                messages, max_tokens=MAX_TOKENS, thinking=False, stream=True,
                timeout=TIMEOUT_S,
            )
            out.update(
                prompt_tokens=int(prompt),
                cached_tokens=int(cached),
                completion_tokens=int(completion),
                ttft_ms=round(float(ttft), 3),
                latency_ms=round(float(wall), 3),
                status=int(status) if status is not None else None,
            )
            if status is not None and int(status) != 200:
                raise RuntimeError(f"non-200 status {status}")
            self.consecutive_failures = 0
        except Exception as exc:  # noqa: BLE001 - the failure text is evidence
            self.failures += 1
            self.consecutive_failures += 1
            out["error"] = f"{type(exc).__name__}: {exc}"
            out["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            out.setdefault("prompt_tokens", 0)
            out.setdefault("cached_tokens", 0)
            out.setdefault("completion_tokens", 0)
            out.setdefault("ttft_ms", 0.0)
            if self.first_error is None:
                self.first_error = out["error"]
        out["uncached_tokens"] = max(0, out["prompt_tokens"] - out["cached_tokens"])
        return out


def run_level(info: dict, capacity: int, total_pressure: int, docs_pushed: int,
              requests_used: int, **extra) -> dict:
    return {
        "unit": UNIT,
        "stack": STACK,
        "config_id": CONFIG_ID,
        "config_sha256": CONFIG_SHA256,
        "server_info_sha256": info.get("info_sha256"),
        "token_capacity": capacity,
        "total_pressure_tokens": total_pressure,
        "pressure_ratio": round(total_pressure / capacity, 6) if capacity else None,
        "docs_pushed": docs_pushed,
        "requests_used": requests_used,
        "request_cap": REQUEST_CAP,
        **extra,
    }


def make_row(phase: str, doc: dict, position: int, sent: dict, run: dict, **extra) -> dict:
    messages = extra.pop("_messages", None)
    row = {
        "unit": UNIT,
        "phase": phase,
        "doc_id": doc["doc_id"],
        "doc_position": position,
        "prompt_tokens": sent["prompt_tokens"],
        "cached_tokens": sent["cached_tokens"],
        "uncached_tokens": sent["uncached_tokens"],
        "completion_tokens": sent["completion_tokens"],
        "latency_ms": sent["latency_ms"],
        "ttft_ms": sent["ttft_ms"],
        "status": sent["status"],
        "error": sent["error"],
        "request_index": sent["request_index"],
        "ts_utc": sent["ts_utc"],
        "doc_chars": doc["chars"],
        "doc_body_sha256": doc["body_sha256"],
        "doc_head_sha256": doc["head_sha256"],
        "prompt_sha256": sha256_prompt(messages) if messages is not None else None,
        "messages": len(messages) if messages is not None else None,
    }
    row.update(run)
    row.update(extra)
    return row


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------
def phase_p(sender: Sender, docs: list[dict], capacity: int, log_path: Path):
    """Push documents one at a time until cumulative prompt tokens >= target."""

    requested_target = TARGET_RATIO
    target_tokens = int(math.ceil(TARGET_RATIO * capacity))
    rows: list[dict] = []
    cumulative = 0
    pushed: list[dict] = []
    wall_started = time.monotonic()
    projection_checked = False
    shortened = False
    aborted = False
    abort_reason = ""

    for doc in docs[:MAX_DOCS]:
        if cumulative >= target_tokens:
            break
        messages = corpus_mod.messages_for(doc)
        sent = sender.send(messages)
        position = len(pushed) + 1
        cumulative += sent["prompt_tokens"]
        row = make_row("P", doc, position, sent, {"token_capacity": capacity}, _messages=messages,
                       cum_prompt_tokens=cumulative)
        append_row(row)
        rows.append(row)
        pushed.append({**doc, "position": position, "prompt_tokens": sent["prompt_tokens"],
                       "cum_end": cumulative})
        log(log_path, f"P {position:3d} {doc['doc_id']} prompt={sent['prompt_tokens']} "
                      f"cached={sent['cached_tokens']} cum={cumulative} "
                      f"ratio={cumulative / capacity:.3f} status={sent['status']} "
                      f"lat={sent['latency_ms']:.0f}ms")
        if sender.consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT:
            aborted = True
            abort_reason = sender.first_error or "3 consecutive failures"
            log(log_path, f"ABORT phase P: {abort_reason}")
            break

        # After the projection sample, decide whether the full 1.5x target can
        # be reached inside the wall bound; if not, fall back to 1.2x (card).
        if not projection_checked and position == P_PROJECTION_SAMPLE:
            projection_checked = True
            elapsed = time.monotonic() - wall_started
            mean_s = elapsed / position
            docs_needed = math.ceil(target_tokens / max(1, cumulative / position))
            projected = mean_s * docs_needed
            log(log_path, f"P projection: {mean_s:.2f}s/request, ~{docs_needed} docs, "
                          f"~{projected / 60:.1f} min")
            if projected > P_WALL_GUARD_S:
                shortened = True
                requested_target = FALLBACK_RATIO
                target_tokens = int(math.ceil(FALLBACK_RATIO * capacity))
                log(log_path, f"P SHORTENED to {FALLBACK_RATIO}x capacity "
                              f"({target_tokens} tokens) - wall bound")
            if docs_needed > MAX_DOCS:
                log(log_path, f"P WARNING: {docs_needed} docs needed > {MAX_DOCS}-doc pool; "
                              f"the run will report the pressure ratio it actually reached")

    pool_exhausted = cumulative < target_tokens and len(pushed) >= min(MAX_DOCS, len(docs))
    return {
        "rows": rows,
        "docs": pushed,
        "total_pressure_tokens": cumulative,
        "target_ratio": requested_target,
        "target_tokens": target_tokens,
        "shortened": shortened,
        "pool_exhausted": pool_exhausted,
        "aborted": aborted,
        "abort_reason": abort_reason,
        "phase_wall_s": round(time.monotonic() - wall_started, 3),
    }


def band_positions(n: int) -> dict[str, list[int]]:
    middle_start = max(1, n // 2 - (BAND_SIZE // 2 - 1))
    middle = list(range(middle_start, min(n, middle_start + BAND_SIZE) + 1))[:BAND_SIZE]
    return {
        "newest": list(range(max(1, n - BAND_SIZE + 1), n + 1)),
        "middle": middle,
        "oldest": list(range(1, min(n, BAND_SIZE) + 1)),
    }


def phase_r(sender: Sender, pushed: list[dict], capacity: int, log_path: Path):
    """Replay three bands of earlier documents and record what is still cached.

    Order is **newest -> middle -> oldest**: a replayed document that misses is
    re-inserted at MRU, which evicts documents from the resident window's oldest
    end.  Replaying the (expected) evicted band last keeps that insertion from
    perturbing the bands measured before it.
    """

    n = len(pushed)
    by_position = {doc["position"]: doc for doc in pushed}
    plan = band_positions(n)
    rows: list[dict] = []
    for band in ("newest", "middle", "oldest"):
        for position in plan[band]:
            doc = by_position[position]
            messages = corpus_mod.messages_for(doc)
            sent = sender.send(messages)
            row = make_row("R", doc, position, sent, {"token_capacity": capacity},
                           _messages=messages, band=band,
                           cum_prompt_tokens=doc["cum_end"],
                           cum_prompt_tokens_start=doc["cum_end"] - doc["prompt_tokens"],
                           prompt_tokens_phase_p=doc["prompt_tokens"])
            append_row(row)
            rows.append(row)
            log(log_path, f"R {band:6s} pos={position:3d} {doc['doc_id']} "
                          f"prompt={sent['prompt_tokens']} cached={sent['cached_tokens']} "
                          f"hit={sent['cached_tokens'] / max(1, sent['prompt_tokens']):.3f} "
                          f"status={sent['status']}")
            if sender.consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT:
                log(log_path, f"ABORT phase R: {sender.first_error}")
                return rows, plan, True
    return rows, plan, False


def phase_d(sender: Sender, pushed: list[dict], plan: dict[str, list[int]],
            capacity: int, log_path: Path):
    """Full resend vs append-note-at-delta-end, 3 documents each.

    Both shapes re-send a byte-identical document prefix; the note shape adds
    one ``[note]`` node at the delta end, exactly as ``CompactionPolicy.
    APPEND_NOTE`` does.  The discipline's claim is therefore measurable in one
    number: ``incremental_uncached = uncached_note - appended_tokens``.  If the
    prefix is resident this is the block tax (one 64-token block); if the
    prefix was evicted the note re-pays the whole document.
    """

    n = len(pushed)
    by_position = {doc["position"]: doc for doc in pushed}
    after_middle = (max(plan["middle"]) if plan["middle"] else n // 2) + 1
    d_positions = [p for p in range(after_middle, min(n, after_middle + 2 * D_DOCS_PER_SHAPE - 1) + 1)]
    if len(d_positions) < 2 * D_DOCS_PER_SHAPE:
        d_positions = [p for p in range(max(1, n - 2 * D_DOCS_PER_SHAPE + 1), n + 1)]
    rows: list[dict] = []
    pairs = []
    for i, position in enumerate(d_positions):
        doc = by_position[position]
        shape = "full_resend" if i % 2 == 0 else "append_note"
        if shape == "full_resend":
            messages = corpus_mod.messages_for(doc)
            note_tokens = 0
        else:
            note = corpus_mod.note_text_for(doc)
            messages = corpus_mod.note_messages_for(doc, note)
            note_tokens = None  # measured below, from the paired baseline
        sent = sender.send(messages)
        row = make_row("D", doc, position, sent, {"token_capacity": capacity},
                       _messages=messages, band="middle_adjacent", shape=shape,
                       cum_prompt_tokens=doc["cum_end"],
                       prompt_tokens_phase_p=doc["prompt_tokens"],
                       note_chars=len(corpus_mod.note_text_for(doc)) if shape == "append_note" else 0)
        if shape == "append_note":
            delta = sent["prompt_tokens"] - doc["prompt_tokens"]
            row["appended_tokens"] = delta
            row["incremental_uncached"] = sent["uncached_tokens"] - delta
        else:
            row["appended_tokens"] = 0
            row["incremental_uncached"] = sent["uncached_tokens"]
        append_row(row)
        rows.append(row)
        pairs.append({"doc_id": doc["doc_id"], "position": position, "shape": shape,
                      "prompt_tokens": sent["prompt_tokens"],
                      "cached_tokens": sent["cached_tokens"],
                      "uncached_tokens": sent["uncached_tokens"],
                      "hit_ratio": round(sent["cached_tokens"] / max(1, sent["prompt_tokens"]), 6),
                      "prompt_tokens_phase_p": doc["prompt_tokens"],
                      "appended_tokens": row["appended_tokens"],
                      "incremental_uncached": row["incremental_uncached"],
                      "status": sent["status"]})
        log(log_path, f"D {shape:12s} pos={position:3d} {doc['doc_id']} "
                      f"prompt={sent['prompt_tokens']} cached={sent['cached_tokens']} "
                      f"uncached={sent['uncached_tokens']} appended={row['appended_tokens']} "
                      f"incr_uncached={row['incremental_uncached']}")
        if sender.consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT:
            log(log_path, f"ABORT phase D: {sender.first_error}")
            return rows, pairs, True
    return rows, pairs, False


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def mean_or_none(values):
    values = [v for v in values if v is not None]
    return round(statistics.fmean(values), 6) if values else None


def band_summary(rows: list[dict]) -> dict:
    out = {}
    for band in ("oldest", "middle", "newest"):
        sel = [r for r in rows if r.get("band") == band]
        out[band] = {
            "n": len(sel),
            "docs": [
                {
                    "doc_id": r["doc_id"],
                    "doc_position": r["doc_position"],
                    "prompt_tokens": r["prompt_tokens"],
                    "cached_tokens": r["cached_tokens"],
                    "uncached_tokens": r["uncached_tokens"],
                    "hit_ratio": round(r["cached_tokens"] / max(1, r["prompt_tokens"]), 6),
                    "cum_tokens_start": r.get("cum_prompt_tokens_start"),
                    "cum_tokens_end": r.get("cum_prompt_tokens"),
                    "status": r["status"],
                }
                for r in sel
            ],
            "mean_prompt_tokens": mean_or_none([r["prompt_tokens"] for r in sel]),
            "mean_cached_tokens": mean_or_none([r["cached_tokens"] for r in sel]),
            "mean_uncached_tokens": mean_or_none([r["uncached_tokens"] for r in sel]),
            "mean_hit_ratio": mean_or_none(
                [r["cached_tokens"] / max(1, r["prompt_tokens"]) for r in sel]
            ),
            "n_full_hit": sum(
                1 for r in sel if r["prompt_tokens"] and r["cached_tokens"] >= r["prompt_tokens"] - 64
            ),
            "n_zero_hit": sum(1 for r in sel if r["cached_tokens"] == 0),
            "n_partial_hit": sum(
                1 for r in sel
                if 0 < r["cached_tokens"] < max(1, r["prompt_tokens"]) - 64
            ),
        }
    return out


def eviction_analysis(p_rows: list[dict], r_rows: list[dict], capacity: int,
                      total_pressure: int, docs_pushed: int) -> dict:
    """Where the pool stops holding, predicted and observed."""

    mean_doc = mean_or_none([r["prompt_tokens"] for r in p_rows]) or 1
    predicted_resident_start = total_pressure - capacity
    # The first document whose cumulative end exceeds the predicted window start
    # is the predicted oldest survivor.
    predicted_oldest_survivor = None
    for row in p_rows:
        if row["cum_prompt_tokens"] - row["prompt_tokens"] >= predicted_resident_start:
            predicted_oldest_survivor = row["doc_position"]
            break
    hits = [r for r in r_rows if r["cached_tokens"] > 0]
    misses = [r for r in r_rows if r["cached_tokens"] == 0]
    observed = {
        "oldest_hit_cum_tokens_start": min(
            (r["cum_prompt_tokens_start"] for r in hits), default=None
        ),
        "newest_miss_cum_tokens_end": max(
            (r["cum_prompt_tokens"] for r in misses), default=None
        ),
        "oldest_hit_doc_position": min((r["doc_position"] for r in hits), default=None),
        "newest_miss_doc_position": max((r["doc_position"] for r in misses), default=None),
    }
    # The observed boundary is bracketed, never pinpointed, because only 30 of
    # ~n documents were replayed.
    bracket = {
        "evicted_up_to_cum_tokens": observed["newest_miss_cum_tokens_end"],
        "resident_from_cum_tokens": observed["oldest_hit_cum_tokens_start"],
    }
    return {
        "predicted_resident_start_tokens": predicted_resident_start,
        "predicted_resident_start_doc_position": predicted_oldest_survivor,
        "predicted_resident_docs": round(capacity / mean_doc, 2),
        "mean_doc_tokens": mean_doc,
        "observed": observed,
        "bracket": bracket,
        "replay_hits": len(hits),
        "replay_misses": len(misses),
        "replay_partial": len(r_rows) - len(hits) - len(misses),
        "capacity_tokens": capacity,
        "total_pressure_tokens": total_pressure,
        "pressure_over_capacity_tokens": total_pressure - capacity,
    }


def lru_verdict(bands: dict, ev: dict) -> dict:
    """Mechanical verdict: is the replay profile what an LRU predicts?

    Criteria, all stated so a reader can re-apply them:

    1. newest band intact (mean hit >= 0.90);
    2. oldest band gone (mean hit <= 0.10);
    3. hit rate non-decreasing oldest -> middle -> newest;
    4. no replayed doc inside the predicted resident window is a full miss
       while a replayed doc outside it is a hit.
    """

    oldest = bands["oldest"]["mean_hit_ratio"] or 0.0
    middle = bands["middle"]["mean_hit_ratio"] or 0.0
    newest = bands["newest"]["mean_hit_ratio"] or 0.0
    checks = {
        "newest_intact": newest >= 0.90,
        "oldest_gone": oldest <= 0.10,
        "monotone_oldest_middle_newest": oldest <= middle <= newest,
    }
    anomalies = []
    window_start = ev["bracket"]["resident_from_cum_tokens"]
    window_end = ev["bracket"]["evicted_up_to_cum_tokens"]
    if window_start is not None:
        for band, payload in bands.items():
            for doc in payload["docs"]:
                start = doc["cum_tokens_start"]
                if start is None:
                    continue
                if start >= window_start and doc["cached_tokens"] == 0:
                    anomalies.append(
                        f"{doc['doc_id']} (pos {doc['doc_position']}, cum_start {start}) "
                        f"sits inside the observed resident window but got 0 cached tokens"
                    )
                if window_end is not None and start < window_end and doc["cached_tokens"] > 0:
                    anomalies.append(
                        f"{doc['doc_id']} (pos {doc['doc_position']}, cum_start {start}) "
                        f"sits below the observed evicted boundary but got "
                        f"{doc['cached_tokens']} cached tokens"
                    )
    checks["no_residency_anomaly"] = not anomalies
    passed = sum(1 for v in checks.values() if v)
    if passed == len(checks):
        verdict = "consistent_with_lru"
    elif checks["newest_intact"] and checks["oldest_gone"]:
        verdict = "consistent_with_lru_with_partial_hits"
    elif not checks["newest_intact"] and not checks["oldest_gone"]:
        verdict = "inconsistent_with_lru"
    else:
        verdict = "mixed"
    return {
        "verdict": verdict,
        "checks": checks,
        "checks_passed": passed,
        "checks_total": len(checks),
        "anomalies": anomalies,
        "criterion": (
            "newest band mean hit >= 0.90; oldest band mean hit <= 0.10; hit rate "
            "non-decreasing oldest->middle->newest; no replayed doc inside the observed "
            "resident window is a full miss while one below it is a hit"
        ),
    }


def phase_d_analysis(rows: list[dict]) -> dict:
    if not rows:
        return {
            "by_shape": {},
            "note_verdict": "not_run",
            "note_verdict_sentence": "phase D did not run (phase R skipped or aborted)",
            "full_resend_hit_ratio": None,
            "note_shape_hit_ratio": None,
            "comparison": "not measured",
        }
    by_shape: dict[str, list[dict]] = {}
    for row in rows:
        by_shape.setdefault(row["shape"], []).append(row)
    summary = {}
    for shape, sel in by_shape.items():
        summary[shape] = {
            "n": len(sel),
            "mean_prompt_tokens": mean_or_none([r["prompt_tokens"] for r in sel]),
            "mean_cached_tokens": mean_or_none([r["cached_tokens"] for r in sel]),
            "mean_uncached_tokens": mean_or_none([r["uncached_tokens"] for r in sel]),
            "mean_hit_ratio": mean_or_none(
                [r["cached_tokens"] / max(1, r["prompt_tokens"]) for r in sel]
            ),
            "mean_appended_tokens": mean_or_none([r["appended_tokens"] for r in sel]),
            "mean_incremental_uncached": mean_or_none([r["incremental_uncached"] for r in sel]),
            "docs": [
                {
                    "doc_id": r["doc_id"],
                    "doc_position": r["doc_position"],
                    "prompt_tokens": r["prompt_tokens"],
                    "cached_tokens": r["cached_tokens"],
                    "uncached_tokens": r["uncached_tokens"],
                    "prompt_tokens_phase_p": r["prompt_tokens_phase_p"],
                    "appended_tokens": r["appended_tokens"],
                    "incremental_uncached": r["incremental_uncached"],
                    "hit_ratio": round(r["cached_tokens"] / max(1, r["prompt_tokens"]), 6),
                    "status": r["status"],
                }
                for r in sel
            ],
        }
    note = summary.get("append_note") or {}
    full = summary.get("full_resend") or {}
    note_hit = note.get("mean_hit_ratio") or 0.0
    incr = note.get("mean_incremental_uncached")
    appended = note.get("mean_appended_tokens") or 0.0
    if note_hit >= 0.90 and incr is not None and incr <= 128:
        verdict = "discipline_holds"
        sentence = (
            "the byte-identical prefix was still resident at this depth, so the appended "
            f"note cost {incr} incremental uncached tokens (appended {appended}); the "
            "append-note discipline still buys reuse"
        )
    elif note_hit <= 0.10:
        verdict = "note_unusable"
        sentence = (
            "the byte-identical prefix was evicted at this depth, so the appended note "
            f"re-paid the whole document ({incr} incremental uncached tokens for an "
            f"appended {appended}); the append-note discipline buys nothing past capacity"
        )
    else:
        verdict = "partial_residency"
        sentence = (
            f"the prefix was partially resident (mean hit {note_hit}), so the appended note "
            f"cost {incr} incremental uncached tokens for an appended {appended}"
        )
    return {
        "by_shape": summary,
        "note_verdict": verdict,
        "note_verdict_sentence": sentence,
        "full_resend_hit_ratio": full.get("mean_hit_ratio"),
        "note_shape_hit_ratio": note.get("mean_hit_ratio"),
        "comparison": (
            "both shapes re-send a byte-identical document prefix. full_resend adds nothing; "
            "append_note adds one [note] node at the delta end. incremental_uncached is what "
            "the note shape pays beyond its own appended tokens - the block tax (~64) when "
            "the prefix is resident, the whole document when it is not."
        ),
    }


def build_analysis(*, info, capacity, p, p_rows, r_rows, plan, d_rows, d_pairs,
                   sender, lock_held_s, wall_s, band_order, started_utc) -> dict:
    bands = band_summary(r_rows)
    ev = eviction_analysis(p_rows, r_rows, capacity, p["total_pressure_tokens"], len(p["docs"]))
    lru = lru_verdict(bands, ev)
    discipline = phase_d_analysis(d_rows)
    latencies = [r["latency_ms"] for r in p_rows if r["status"] == 200]
    rows_all = p_rows + r_rows + d_rows
    rows_sha = sha256_bytes(ROWS_PATH.read_bytes()) if ROWS_PATH.exists() else None
    return {
        "unit": UNIT,
        "purpose": "eviction pressure: does the LRU evict as claimed, and does the "
                   "append-note/pointer discipline still buy reuse past capacity?",
        "run": {
            "stack": STACK,
            "config_id": CONFIG_ID,
            "config_sha256": CONFIG_SHA256,
            "live_config_path": "state/config/live-server-config.json",
            "endpoint": info["endpoint"],
            "server_version": info.get("server_version"),
            "server_status": info.get("server_status"),
            "server_info_sha256": info.get("info_sha256"),
            "server_info_bytes": info.get("info_bytes"),
            "token_capacity": capacity,
            "capacity_sampled_utc": info["sampled_utc"],
            "capacity_source": "/get_server_info internal_states[0].memory_usage.token_capacity",
            "stale_sampled_capacity_in_live_config": json.loads(
                CONFIG_PATH.read_text(encoding="utf-8")
            ).get("token_capacity"),
            "radix_eviction_policy": info.get("radix_eviction_policy"),
            "page_size": info.get("page_size"),
            "max_mamba_cache_size": info.get("max_mamba_cache_size"),
            "mamba_track_interval": info.get("mamba_track_interval"),
            "disable_chunked_prefix_cache": info.get("disable_chunked_prefix_cache"),
            "max_running_requests": info.get("max_running_requests"),
            "temperature": 0.0,
            "max_tokens": MAX_TOKENS,
            "requests_in_flight": 1,
            "total_pressure_tokens": p["total_pressure_tokens"],
            "pressure_ratio": round(p["total_pressure_tokens"] / capacity, 6),
            "pressure_target_ratio": p["target_ratio"],
            "pressure_shortened": p["shortened"],
            "pool_exhausted": p["pool_exhausted"],
            "docs_pushed": len(p["docs"]),
            "doc_pool": len(corpus_mod.load_corpus(CORPUS_PATH)),
            "doc_target_est_tokens": DOC_TARGET_EST,
            "measured_chars_per_token": (
                round(sum(r["doc_chars"] for r in p_rows)
                      / max(1, sum(r["prompt_tokens"] for r in p_rows)), 4)
                if p_rows else None
            ),
            "corpus_sha256": json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["corpus_sha256"],
            "requests_used": sender.sent,
            "requests_cap": REQUEST_CAP,
            "requests_by_phase": {"P": len(p_rows), "R": len(r_rows), "D": len(d_rows)},
            "failures": sender.failures,
            "first_error": sender.first_error,
            "band_replay_order": band_order,
            "phase_p_wall_s": p["phase_wall_s"],
            "wall_s": round(wall_s, 3),
            "lock_held_s": round(lock_held_s, 3),
            "started_utc": started_utc,
            "finished_utc": utc_now(),
            "rows": len(rows_all),
            "rows_sha256": rows_sha,
            "phase_p_latency_ms": {
                "mean": mean_or_none(latencies),
                "median": round(statistics.median(latencies), 3) if latencies else None,
                "max": max(latencies) if latencies else None,
            },
        },
        "phase_p": {
            "n": len(p_rows),
            "mean_prompt_tokens": mean_or_none([r["prompt_tokens"] for r in p_rows]),
            "min_prompt_tokens": min((r["prompt_tokens"] for r in p_rows), default=None),
            "max_prompt_tokens": max((r["prompt_tokens"] for r in p_rows), default=None),
            "n_zero_cached_on_first_submission": sum(
                1 for r in p_rows if r["cached_tokens"] == 0
            ),
            "max_cached_on_first_submission": max(
                (r["cached_tokens"] for r in p_rows), default=None
            ),
            "cumulative_curve_every_25": [
                {"doc_position": r["doc_position"], "cum_prompt_tokens": r["cum_prompt_tokens"],
                 "ratio": round(r["cum_prompt_tokens"] / capacity, 4)}
                for r in p_rows if r["doc_position"] % 25 == 0 or r is p_rows[-1]
            ],
        },
        "phase_r": {
            "band_replay_order": band_order,
            "bands": bands,
            "note": "hit_ratio = cached_tokens / prompt_tokens for a byte-identical replay",
        },
        "lru": lru,
        "eviction": ev,
        "phase_d": {
            "documents": d_pairs,
            **discipline,
        },
        "digest": {
            "n_rows": len(rows_all),
            "rows_sha256": rows_sha,
            "requests_used": sender.sent,
            "requests_cap": REQUEST_CAP,
            "token_capacity": capacity,
            "total_pressure_tokens": p["total_pressure_tokens"],
            "pressure_ratio": round(p["total_pressure_tokens"] / capacity, 6),
            "config_sha256": CONFIG_SHA256,
            "stack": STACK,
            "config_id": CONFIG_ID,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    started = time.monotonic()
    started_utc = utc_now()
    log_path = CELL_DIR / "run.log"
    log_path.write_text("", encoding="utf-8")
    ROWS_PATH.write_text("", encoding="utf-8")

    handle = None
    lock_held = 0.0
    try:
        handle, waited = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S)
        lock_started = time.monotonic()
        log(log_path, f"lock acquired after {waited:.1f}s")
    except TimeoutError as exc:
        log(log_path, f"BLOCKED: {exc}")
        return 3

    try:
        info = measure_capacity()
        capacity = info["token_capacity"]
        log(log_path, f"capacity={capacity} version={info.get('server_version')} "
                      f"eviction={info.get('radix_eviction_policy')} "
                      f"page_size={info.get('page_size')} "
                      f"mamba_cache={info.get('max_mamba_cache_size')}")

        if not CORPUS_PATH.exists():
            docs = corpus_mod.build_documents(MAX_DOCS, DOC_TARGET_EST)
            corpus_mod.write_corpus(docs, CELL_DIR, DOC_TARGET_EST)
        docs = corpus_mod.load_corpus(CORPUS_PATH)
        log(log_path, f"corpus: {len(docs)} docs, est {sum(d['est_tokens'] for d in docs)} tokens")

        sender = Sender()
        p = phase_p(sender, docs, capacity, log_path)
        p_rows = p["rows"]
        total = p["total_pressure_tokens"]
        log(log_path, f"phase P done: {len(p['docs'])} docs, pressure={total} "
                      f"ratio={total / capacity:.4f} requests={sender.sent}")

        run_ctx = run_level(info, capacity, total, len(p["docs"]), sender.sent)
        r_rows: list[dict] = []
        plan: dict[str, list[int]] = {"oldest": [], "middle": [], "newest": []}
        d_rows: list[dict] = []
        d_pairs: list[dict] = []
        band_order = ["newest", "middle", "oldest"]
        if p["aborted"] or len(p["docs"]) < 3 * BAND_SIZE:
            log(log_path, "phase R/D skipped: pressure run aborted or too few documents")
        else:
            r_rows, plan, r_aborted = phase_r(sender, p["docs"], capacity, log_path)
            if not r_aborted:
                d_rows, d_pairs, _ = phase_d(sender, p["docs"], plan, capacity, log_path)

        # Finalise every row with the run-level facts that only exist at the end:
        # total pressure, the final ratio and the request count.
        final_run = run_level(info, capacity, total, len(p["docs"]), sender.sent)
        with ROWS_PATH.open("w", encoding="utf-8") as out:
            for row in p_rows + r_rows + d_rows:
                merged = {**row, **final_run}
                out.write(json.dumps(merged, sort_keys=True, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())

        lock_held = time.monotonic() - lock_started
        analysis = build_analysis(
            info=info, capacity=capacity, p=p, p_rows=p_rows, r_rows=r_rows, plan=plan,
            d_rows=d_rows, d_pairs=d_pairs, sender=sender, lock_held_s=lock_held,
            wall_s=time.monotonic() - started, band_order=band_order, started_utc=started_utc,
        )
        write_json_atomic(ANALYSIS_PATH, analysis)

        status = "done"
        blocker = ""
        if p["aborted"]:
            status, blocker = "partial", f"phase P aborted: {p['abort_reason']}"
        elif len(p["docs"]) < 3 * BAND_SIZE or not r_rows:
            status, blocker = "partial", "not enough documents for the replay bands"
        elif sender.failures:
            status, blocker = "partial", f"{sender.failures} failed requests: {sender.first_error}"

        handoff = {
            "unit": UNIT,
            "status": status,
            "artifacts": [
                "experiments/context-cache/cells/M4/rows.jsonl",
                "experiments/context-cache/cells/M4/analysis.json",
                "experiments/context-cache/cells/M4/corpus.py",
                "experiments/context-cache/cells/M4/battery.py",
                "experiments/context-cache/cells/M4/corpus.jsonl",
                "experiments/context-cache/cells/M4/corpus_manifest.json",
                "experiments/context-cache/cells/M4/server_info.json",
                "experiments/context-cache/cells/M4/calibration_aborted_run.jsonl",
                "experiments/context-cache/cells/M4/run.log",
            ],
            "evidence": {
                "command": ".venv/bin/python experiments/context-cache/cells/M4/battery.py",
                "token_capacity": capacity,
                "capacity_source": "/get_server_info 200, internal_states[0].memory_usage.token_capacity",
                "total_pressure_tokens": total,
                "pressure_ratio": round(total / capacity, 4),
                "docs_pushed": len(p["docs"]),
                "requests_used": sender.sent,
                "requests_cap": REQUEST_CAP,
                "rows": len(p_rows) + len(r_rows) + len(d_rows),
                "rows_sha256": analysis["digest"]["rows_sha256"],
                "replay_hit_profile": {
                    band: analysis["phase_r"]["bands"][band]["mean_hit_ratio"]
                    for band in ("oldest", "middle", "newest")
                },
                "lru_verdict": analysis["lru"]["verdict"],
                "note_verdict": analysis["phase_d"]["note_verdict"],
                "failures": sender.failures,
                "lock_held_s": round(lock_held, 1),
                "requests_used_total_including_calibration": sender.sent + CALIBRATION_REQUESTS,
            },
            "blocker": blocker,
            "next_unit_hint": (
                "verifier: re-run the offline analysis from rows.jsonl (no requests) and "
                "check the replay bands against the rows; a second pressure run at 2x "
                "capacity would separate a capacity-bounded LRU from a mamba-checkpoint cap"
            ),
            "write_paths": [
                "experiments/context-cache/cells/M4/**",
                "orchestration/handoffs/M4-EVICT.json",
                "orchestration/units/M4-EVICT.md",
            ],
            "assumptions": [
                "documents are sized with the repo's offline estimator (ceil(chars/4)); the "
                "pressure target is enforced on MEASURED prompt_tokens, not on the estimate",
                "4-word salts stand in for the card's '4-token salt'",
                "documents were resized from the card's ~8k to an offline-estimator target of "
                f"{DOC_TARGET_EST} tokens after an aborted calibration run measured this text at "
                "4.8491 chars/token (8k-est documents came out at 7,126 prompt tokens, so a "
                "300-document pool could only reach 1.31x capacity); the calibration rows are kept "
                "in calibration_aborted_run.jsonl and its 69 requests are counted against the cap",
                "the pressure target is enforced on measured prompt_tokens; if the 300-document "
                "pool runs out first, the achieved ratio is reported instead of the target",
                "Phase D documents are the slice immediately after the middle band, because "
                "the middle band itself was replayed in Phase R and would be double-warmed",
                "band replay order is newest->middle->oldest so the (expected) evicted band's "
                "re-insertion cannot perturb the resident bands measured before it",
            ],
        }
        tmp = CELL_DIR / "M4-EVICT.handoff.tmp"
        tmp.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, HANDOFF_PATH)
        log(log_path, f"handoff written: status={status} requests={sender.sent} "
                      f"rows={len(p_rows) + len(r_rows) + len(d_rows)} "
                      f"lru={analysis['lru']['verdict']} "
                      f"note={analysis['phase_d']['note_verdict']}")
        print("SUMMARY " + json.dumps({
            "status": status,
            "capacity": capacity,
            "pressure_ratio": round(total / capacity, 4),
            "requests": sender.sent,
            "bands": {b: analysis["phase_r"]["bands"][b]["mean_hit_ratio"]
                      for b in ("oldest", "middle", "newest")},
            "lru": analysis["lru"]["verdict"],
            "note": analysis["phase_d"]["note_verdict"],
            "blocker": blocker,
        }, sort_keys=True), flush=True)
        return 0 if status == "done" else 2
    except Exception as exc:  # noqa: BLE001 - a dead run must still leave a stub
        log(log_path, f"FAILED: {type(exc).__name__}: {exc}")
        rows = []
        if ROWS_PATH.exists():
            for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
        handoff = {
            "unit": UNIT,
            "status": "failed",
            "artifacts": ["experiments/context-cache/cells/M4/rows.jsonl"],
            "evidence": {
                "command": ".venv/bin/python experiments/context-cache/cells/M4/battery.py",
                "error": f"{type(exc).__name__}: {exc}",
                "rows_written": len(rows),
            },
            "blocker": f"{type(exc).__name__}: {exc}",
            "next_unit_hint": "re-delegate to a fresh unit with this failure text",
            "write_paths": ["experiments/context-cache/cells/M4/**",
                            "orchestration/handoffs/M4-EVICT.json"],
        }
        tmp = CELL_DIR / "M4-EVICT.handoff.tmp"
        tmp.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, HANDOFF_PATH)
        return 1
    finally:
        if handle is not None:
            release_lock(handle)


if __name__ == "__main__":
    raise SystemExit(main())
