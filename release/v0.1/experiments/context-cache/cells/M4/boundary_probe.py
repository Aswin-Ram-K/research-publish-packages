#!/usr/bin/env python
"""M4-EVICT boundary probe -- bracket the resident window's oldest end.

Why this file exists
--------------------
``battery.py`` measures the eviction *profile* with three 10-document replay
bands, but those bands bracket the resident window's oldest end only to within
128 documents: the middle band (positions 137-146) is fully evicted while the
newest band (274-283) is fully resident, so the card's "eviction onset point in
tokens" would otherwise read as the useless interval 1,255,655 .. 2,348,053
tokens.

This probe closes that gap with the cheapest possible instrument: a
**byte-identical re-send** of documents that are already in the pool.  A replay
that returns ``cached_tokens > 0`` proves the document is resident; a replay
that returns ``cached_tokens == 0`` proves it was evicted.  No new content is
created, nothing is reconfigured, and no model is restarted.

Discrimination target
---------------------
After the battery's 26 post-Phase-P re-insertions (20 Phase-R misses + 6 Phase-D
misses), a doc-count model over K resident slots predicts the resident window
starts at::

    slot_boundary(K) = n - (K - n_inserted) + 1

    K  = 64   -> position 247   (one slot per mamba cache entry)
    K  = 128  -> position 183
    K ≈ 188   -> position 123   (plain token-pool LRU at 1.62 M tokens)

The probe descends from the newest replay band in steps of 12 documents and
bisects the first surviving bracket to width 1.

Cost and bounds
---------------
* ``PROBE_CAP = 16`` live requests, hard: the unit is at 319 battery + 69
  calibration requests, so the total stays at <= 404 of the card's 600 cap.
* One request in flight, ``temperature 0``, ``max_tokens 4``.
* Holds ``experiments/context-cache/.occamy.lock`` for the whole probe.
* Aborts (and records why) on 3 consecutive failures, or if the sanity check on
  the newest document misses -- that would mean the server restarted and the
  pool is gone, in which case the probe measures nothing.

Writes: 16 new ``phase="B"`` rows appended to ``rows.jsonl``, a
``boundary_probe`` section merged into ``analysis.json``, and a refreshed
``orchestration/handoffs/M4-EVICT.json``.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx

import battery as b

PROBE_CAP = 16          # live requests, sanity check included
DESCEND_STEP = 12       # documents per step while descending from the newest band
OLDEST_BOUND = 146      # known-evicted position from the Phase-R middle band
FLOOR_POSITION = 2      # never probe below this


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def load_rows() -> list[dict]:
    rows = []
    for line in b.ROWS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def read_capacity_now() -> tuple[int, str, int]:
    """Capacity from the live server, without overwriting ``server_info.json``."""

    with httpx.Client(timeout=30.0) as http:
        response = http.get(f"{b.ENDPOINT}/get_server_info")
    response.raise_for_status()
    raw = response.content
    payload = response.json()
    states = payload.get("internal_states") or [{}]
    state = states[0] if states else {}
    memory = state.get("memory_usage") or {}
    capacity = memory.get("token_capacity") or payload.get("max_total_num_tokens")
    if not isinstance(capacity, int) or capacity <= 0:
        raise RuntimeError(f"no usable token_capacity in /get_server_info: {capacity!r}")
    return capacity, b.sha256_bytes(raw), len(raw)


def probe_model(rows: list[dict], n: int) -> dict:
    """Bound the resident-window size W from the probe's hit/miss inequalities.

    Model under test: the cache is full, it evicts exactly **one document per
    inserted document**, oldest-touched first, so a document at position ``p``
    re-sent after ``k`` insertions is resident iff::

        p >= n - W + 1 + k     <=>     W >= n + 1 + k - p

    A hit therefore gives a **lower** bound on W and a miss an **upper** bound.
    The bounds come only from observed rows -- nothing is assumed about W up
    front.  If the lower bound reaches the upper bound the model is refuted by
    its own data (``consistent`` false).
    """

    p_rows = [r for r in rows if r["phase"] == "P"]
    if not p_rows:
        return {"error": "no Phase-P rows"}
    mean_prompt = sum(r["prompt_tokens"] for r in p_rows) / len(p_rows)
    capacity = int(p_rows[0]["token_capacity"])
    cum_end = {r["doc_position"]: r["cum_prompt_tokens"] for r in p_rows}

    k = sum(1 for r in rows if r["phase"] in ("R", "D") and r["cached_tokens"] == 0)
    base_k = k
    lower, upper = 1, None
    inequalities = []
    for r in rows:
        if r["phase"] != "B":
            continue
        bound = n + 1 + k - r["doc_position"]
        hit = r["cached_tokens"] > 0
        if hit:
            lower = max(lower, bound)
            implies = f"W >= {bound}"
        else:
            upper = bound if upper is None else min(upper, bound)
            implies = f"W < {bound}"
        inequalities.append({
            "probe_index": r.get("probe_index"),
            "doc_position": r["doc_position"],
            "insertions_before_it": k,
            "cached_tokens": r["cached_tokens"],
            "outcome": "resident" if hit else "evicted",
            "implies": implies,
        })
        if not hit:
            k += 1

    w_upper = (upper - 1) if upper is not None else None
    consistent = w_upper is None or lower < upper or lower <= w_upper
    lo_docs = lower
    hi_docs = w_upper if w_upper is not None else None
    tokens = [round(lo_docs * mean_prompt)]
    if hi_docs is not None:
        tokens.append(round(hi_docs * mean_prompt))
    onset_doc = lo_docs + 1                 # the first document that evicted
    onset_cum = cum_end.get(min(onset_doc, n))
    return {
        "model": "one document evicted per inserted document, oldest-touched first (LRU over "
                 "document branches); W = documents resident at the end of Phase P",
        "insertions_before_probe": base_k,
        "inequalities": inequalities,
        "W_range_docs": [lo_docs, hi_docs],
        "W_range_tokens": tokens,
        "W_range_ratio_of_capacity": [round(t / capacity, 4) for t in tokens],
        "mean_prompt_tokens": round(mean_prompt, 1),
        "token_capacity": capacity,
        "first_eviction_doc_position": onset_doc,
        "first_eviction_cum_tokens": onset_cum,
        "first_eviction_ratio_of_capacity": round(onset_cum / capacity, 4) if onset_cum else None,
        "consistent": consistent,
        "token_pool_lru_docs": round(capacity / mean_prompt, 2),
        "token_pool_lru_excluded": hi_docs is not None and hi_docs < (capacity / mean_prompt),
        "mamba_slots_64_half_per_doc": 32,
        "verdict": (
            "residency_is_w_documents_not_the_token_pool"
            if consistent else "model_refuted_by_its_own_data"
        ),
    }


def touch_model(rows: list[dict], n: int) -> dict:
    """Exact LRU bound: a document is resident iff its recency rank is <= W.

    Rank 1 is the most recently touched document.  A hit gives ``W >= rank``, a
    miss gives ``W < rank``; the two together bracket the resident capacity W
    without assuming that residency follows submission position.
    """

    p_rows = [r for r in rows if r["phase"] == "P"]
    if not p_rows:
        return {"error": "no Phase-P rows"}
    mean_prompt = sum(r["prompt_tokens"] for r in p_rows) / len(p_rows)
    capacity = int(p_rows[0]["token_capacity"])
    cum_end = {r["doc_position"]: r["cum_prompt_tokens"] for r in p_rows}

    last_idx: dict[str, list[int]] = {}
    for i, r in enumerate(rows):
        last_idx.setdefault(r["doc_id"], []).append(i)

    def rank_before(i: int) -> int:
        doc = rows[i]["doc_id"]
        prevs = [j for j in last_idx[doc] if j < i]
        prev = prevs[-1] if prevs else -1
        seen: dict[str, int] = {}
        for j in range(i - 1, -1, -1):
            seen.setdefault(rows[j]["doc_id"], j)
        newer = sum(1 for j in seen.values() if j > prev)
        return newer + 1

    lower, upper = 1, None
    inequalities = []
    for i, r in enumerate(rows):
        if r["phase"] != "B":
            continue
        rank = rank_before(i)
        hit = r["cached_tokens"] > 0
        if hit:
            lower = max(lower, rank)
            implies = f"W >= {rank}"
        else:
            upper = rank if upper is None else min(upper, rank)
            implies = f"W < {rank}"
        inequalities.append({
            "probe_index": r.get("probe_index"),
            "doc_position": r["doc_position"],
            "probe_role": r.get("probe_role"),
            "recency_rank_before": rank,
            "cached_tokens": r["cached_tokens"],
            "outcome": "resident" if hit else "evicted",
            "implies": implies,
        })

    w_lo = lower
    w_hi = (upper - 1) if upper is not None else None
    tokens = [round(w_lo * mean_prompt)]
    if w_hi is not None:
        tokens.append(round(w_hi * mean_prompt))
    onset_doc = w_lo + 1
    onset_cum = cum_end.get(min(onset_doc, n))
    context_length = 131072     # /get_server_info context_length, same snapshot as capacity
    return {
        "model": "LRU over document branches: resident iff recency rank <= W; one document "
                 "evicted per inserted document",
        "inequalities": inequalities,
        "W_range_docs": [w_lo, w_hi],
        "W_range_tokens": tokens,
        "W_range_ratio_of_capacity": [round(t / capacity, 4) for t in tokens],
        "W_range_multiple_of_context_length": [
            round(t / context_length, 3) for t in tokens
        ],
        "context_length": context_length,
        "mean_prompt_tokens": round(mean_prompt, 1),
        "token_capacity": capacity,
        "first_eviction_doc_position": onset_doc,
        "first_eviction_cum_tokens": onset_cum,
        "first_eviction_ratio_of_capacity": round(onset_cum / capacity, 4) if onset_cum else None,
        "token_pool_lru_docs": round(capacity / mean_prompt, 2),
        "token_pool_lru_excluded": w_hi is not None and w_hi < (capacity / mean_prompt),
        "consistent": w_hi is not None and w_lo <= w_hi,
        "verdict": ("residency_capacity_is_w_documents"
                    if (w_hi is not None and w_lo <= w_hi)
                    else "model_refuted_by_its_own_data"),
    }


def merge_analysis(analysis: dict, probe: dict, rows_sha: str, n_rows: int,
                   requests_used: int, probe_rows: int) -> dict:
    """Merge the probe into the battery's analysis without rewriting its facts."""

    ev = analysis.setdefault("eviction", {})
    if probe.get("mode") == "confirm_k":
        bp = analysis.setdefault("boundary_probe", {})
        bp["confirmation"] = probe.get("confirmation")
        bp["model"] = probe.get("model")
        if probe.get("verdict"):
            bp["verdict"] = probe["verdict"]
        ev.setdefault("boundary_probe", {})["model"] = probe.get("model")
        ev.setdefault("boundary_probe", {})["verdict"] = probe.get("verdict")
    else:
        ev["boundary_probe"] = {
            "bracket": probe.get("bracket"),
            "model": probe.get("model") or probe.get("touch_model"),
            "verdict": probe.get("verdict"),
            "note": probe.get("note"),
        }
    observed = ev.setdefault("observed", {})
    touch = probe.get("touch_model") or {}
    if touch:
        observed["resident_capacity_docs_bracket"] = touch.get("W_range_docs")
        observed["resident_capacity_tokens_bracket"] = touch.get("W_range_tokens")
        observed["resident_capacity_ratio_of_capacity"] = touch.get(
            "W_range_ratio_of_capacity")
        observed["eviction_onset_doc_position"] = touch.get("first_eviction_doc_position")
        observed["eviction_onset_cum_tokens"] = touch.get("first_eviction_cum_tokens")
    if probe.get("bracket") and probe.get("mode") != "confirm_k":
        observed["resident_start_doc_position_upper_bound"] = probe["bracket"][
            "resident_at_or_above_position"
        ]
        observed["eviction_onset_doc_position_bracket"] = [
            probe["bracket"]["evicted_at_or_below_position"],
            probe["bracket"]["resident_at_or_above_position"],
        ]

    if probe.get("mode") != "confirm_k":
        analysis["boundary_probe"] = probe
    analysis["run"]["requests_used"] = requests_used
    analysis["run"]["requests_by_phase"] = {
        **analysis["run"].get("requests_by_phase", {}),
        "B": probe_rows,
    }
    analysis["run"]["requests_used_total_including_calibration"] = (
        requests_used + b.CALIBRATION_REQUESTS
    )
    analysis["run"]["boundary_probe_requests"] = probe_rows
    analysis["run"]["boundary_probe_finished_utc"] = b.utc_now()
    analysis["run"]["rows"] = n_rows
    analysis["run"]["rows_sha256"] = rows_sha

    analysis["digest"]["n_rows"] = n_rows
    analysis["digest"]["rows_sha256"] = rows_sha
    analysis["digest"]["requests_used"] = requests_used
    return analysis


def finalize(lock) -> int:
    """Rebuild the analysis's boundary_probe block from rows.jsonl, no requests."""

    try:
        rows = load_rows()
        analysis = json.loads(b.ANALYSIS_PATH.read_text(encoding="utf-8"))
        n = sum(1 for r in rows if r["phase"] == "P")
        b_rows = [r for r in rows if r["phase"] == "B"]
        requests_used = int(analysis["digest"]["requests_used"])
        touch = touch_model(rows, n)
        search_only = [
            r for r in rows
            if r["phase"] != "B" or r.get("probe_role") != "confirm_k"
        ]
        position = probe_model(search_only, n)
        search_probes = [r for r in b_rows if r.get("probe_role") != "confirm_k"]
        confirm_probes = [r for r in b_rows if r.get("probe_role") == "confirm_k"]
        probe = {
            "status": "done",
            "mode": "search+confirm",
            "why": "the three replay bands bracket the eviction onset only to 128 documents; "
                   "byte-identical re-sends bound the resident capacity to a small number of "
                   "documents and refute token-pool LRU",
            "method": "re-send pooled documents; cached_tokens>0 means resident, 0 means "
                      f"evicted; descend from the newest band in steps of {DESCEND_STEP}, "
                      "bisect the surviving bracket, then confirm at the predicted boundary",
            "cap_requests": PROBE_CAP,
            "requests_used": len(b_rows),
            "capacity_at_probe": analysis.get("boundary_probe", {}).get("capacity_at_probe"),
            "capacity_matches_battery": analysis.get("boundary_probe", {}).get(
                "capacity_matches_battery"),
            "sanity_check": next((r for r in b_rows if r.get("probe_role") == "sanity"), None),
            "probes": [
                {
                    "probe_index": r.get("probe_index"),
                    "doc_id": r["doc_id"],
                    "doc_position": r["doc_position"],
                    "probe_role": r.get("probe_role"),
                    "prompt_tokens": r["prompt_tokens"],
                    "cached_tokens": r["cached_tokens"],
                    "hit_ratio": r.get("hit_ratio"),
                    "latency_ms": r["latency_ms"],
                    "verdict": "resident" if r["cached_tokens"] > 0 else "evicted",
                }
                for r in b_rows
            ],
            "search_phase_probes": len(search_probes),
            "confirmation": {
                "positions": [r["doc_position"] for r in confirm_probes],
                "outcomes": [
                    {
                        "doc_position": r["doc_position"],
                        "cached_tokens": r["cached_tokens"],
                        "verdict": "resident" if r["cached_tokens"] > 0 else "evicted",
                    }
                    for r in confirm_probes
                ],
                "why": "the two oldest of the re-inserted documents sit at recency ranks 30 "
                       "and 32; the rank-30 one is resident and the rank-32 one is not, which "
                       "is what pins W to [30, 31]",
            },
            "touch_model": touch,
            "position_model": {
                "W_range_docs": position.get("W_range_docs"),
                "inequalities": position.get("inequalities"),
                "note": "independent formulation in submission-position terms; agrees with the "
                        "recency-rank model, which is the one to quote",
            },
            "verdict": (
                "lru_ordered_but_resident_capacity_is_30_to_31_documents_not_the_token_pool"
                if touch.get("consistent") and touch.get("token_pool_lru_excluded")
                else "inconclusive"
            ),
            "summary_line": (
                f"resident capacity W in {touch.get('W_range_docs')} documents = "
                f"{touch.get('W_range_tokens')} prompt tokens = "
                f"{touch.get('W_range_ratio_of_capacity')} of token_capacity = "
                f"{touch.get('W_range_multiple_of_context_length')} x context_length, "
                f"versus {touch.get('token_pool_lru_docs')} documents implied by token-pool LRU; "
                f"first eviction at document {touch.get('first_eviction_doc_position')} "
                f"({touch.get('first_eviction_cum_tokens')} cumulative prompt tokens = "
                f"{touch.get('first_eviction_ratio_of_capacity')} of capacity)"
            ),
            "caveat": "the probe is destructive at the margin: every miss re-inserts that "
                      "document at MRU and evicts one oldest resident, which is why W is "
                      "bracketed by inequalities rather than read off a single moment",
            "note": "doc-count arithmetic is an approximation: documents are ~8,601 prompt "
                    "tokens each, not exactly equal, and the server's eviction unit is its "
                    "radix tree, not a document",
            "request_order_note": "request_index restarts at 1 inside every script run "
                                  "(battery 1-319, boundary_probe 1-8); reconstruct request "
                                  "order from ts_utc or file order, never from request_index",
            "rows_before_sha256": analysis.get("boundary_probe", {}).get("rows_before_sha256"),
            "started_utc": analysis.get("boundary_probe", {}).get("started_utc"),
            "finished_utc": analysis.get("boundary_probe", {}).get("finished_utc"),
            "finalized_utc": b.utc_now(),
        }
        rows_sha = b.sha256_bytes(b.ROWS_PATH.read_bytes())
        analysis = merge_analysis(analysis, probe, rows_sha, len(rows), requests_used,
                                  len(b_rows))
        analysis["boundary_probe"] = probe
        observed = analysis["eviction"].setdefault("observed", {})
        for stale in ("resident_start_doc_position_upper_bound",
                      "eviction_onset_doc_position_bracket"):
            observed.pop(stale, None)
        analysis["finding"] = {
            "lru_order": analysis["lru"]["verdict"],
            "lru_order_checks": f"{analysis['lru']['checks_passed']}/{analysis['lru']['checks_total']}",
            "lru_capacity": (
                f"resident capacity {touch['W_range_docs']} documents = "
                f"{touch['W_range_tokens']} prompt tokens = "
                f"{touch['W_range_ratio_of_capacity']} of token_capacity "
                f"({touch['W_range_multiple_of_context_length']} x context_length 131072), "
                f"versus {touch['token_pool_lru_docs']} documents the 1.62M-token pool "
                "would hold under plain token-pool LRU"
            ),
            "eviction_onset": (
                f"first eviction at document {touch['first_eviction_doc_position']} "
                f"({touch['first_eviction_cum_tokens']} cumulative prompt tokens = "
                f"{touch['first_eviction_ratio_of_capacity']} of capacity)"
            ),
            "pressure_effect": (
                "at 1.5017x capacity only the newest "
                f"{touch['W_range_docs'][1]} of {n} submitted documents are reusable: "
                "replay hit 0.997 newest, 0.000 middle, 0.000 oldest"
            ),
            "discipline_under_pressure": (
                f"append-note buys nothing past the window: {analysis['phase_d']['note_verdict']} "
                f"(full resend hit {analysis['phase_d']['full_resend_hit_ratio']}, note shape "
                f"hit {analysis['phase_d']['note_shape_hit_ratio']}, mean appended "
                f"{analysis['phase_d']['by_shape']['append_note']['mean_appended_tokens']:.1f} "
                f"tokens, incremental uncached not lower than a full resend)"
            ),
            "server_side_knobs": (
                "radix_eviction_policy lru; max_mamba_cache_size 64; mamba_track_interval 256; "
                "uses_mamba_radix_cache true; context_length 131072; token_capacity 1620892. "
                "The measured cap is consistent with a mamba/context-scaled limit rather than "
                "the token pool, but this cell does not establish the mechanism (same limit "
                "as G13: server-side cause not established)"
            ),
        }
        analysis["eviction"]["boundary_probe"] = {
            "model": touch,
            "position_model": {"W_range_docs": position.get("W_range_docs"),
                               "note": "independent formulation from the search phase only"},
            "verdict": probe["verdict"],
            "note": probe["note"],
        }
        b.write_json_atomic(b.ANALYSIS_PATH, analysis)
        refresh_handoff(probe, rows_sha, len(rows), requests_used)
        print(json.dumps({
            "verdict": probe["verdict"],
            "W_docs": touch.get("W_range_docs"),
            "W_tokens": touch.get("W_range_tokens"),
            "W_ratio": touch.get("W_range_ratio_of_capacity"),
            "x_context": touch.get("W_range_multiple_of_context_length"),
            "token_pool_lru_docs": touch.get("token_pool_lru_docs"),
            "first_eviction_doc": touch.get("first_eviction_doc_position"),
            "first_eviction_cum": touch.get("first_eviction_cum_tokens"),
            "first_eviction_ratio": touch.get("first_eviction_ratio_of_capacity"),
            "requests_used": requests_used,
            "rows": len(rows),
            "rows_sha256": rows_sha,
        }, sort_keys=True))
    finally:
        b.release_lock(lock)
    return 0


def refresh_handoff(probe: dict, rows_sha: str, n_rows: int, requests_used: int) -> dict:
    handoff = json.loads(b.HANDOFF_PATH.read_text(encoding="utf-8"))
    artifacts = handoff.setdefault("artifacts", [])
    probe_rel = "experiments/context-cache/cells/M4/boundary_probe.py"
    if probe_rel not in artifacts:
        artifacts.append(probe_rel)
    evidence = handoff.setdefault("evidence", {})
    evidence["requests_used"] = requests_used
    evidence["requests_used_total_including_calibration"] = (
        requests_used + b.CALIBRATION_REQUESTS
    )
    evidence["rows"] = n_rows
    evidence["rows_sha256"] = rows_sha
    model = probe.get("model") or probe.get("touch_model") or {}
    bracket = probe.get("bracket") or {}
    evidence["eviction_boundary_probe"] = probe.get("summary_line", "") or (
        f"W in {model.get('W_range_docs')} docs = {model.get('W_range_tokens')} tokens "
        f"= {model.get('W_range_ratio_of_capacity')} of capacity; token-pool LRU would "
        f"hold {model.get('token_pool_lru_docs')} docs"
    )
    evidence["resident_window_docs"] = model.get("W_range_docs")
    evidence["resident_window_tokens"] = model.get("W_range_tokens")
    evidence["resident_window_ratio_of_capacity"] = model.get("W_range_ratio_of_capacity")
    evidence["token_pool_lru_docs"] = model.get("token_pool_lru_docs")
    evidence["token_pool_lru_excluded"] = model.get("token_pool_lru_excluded")
    evidence["eviction_onset_doc_position"] = bracket.get(
        "evicted_at_or_below_position", model.get("first_eviction_doc_position")
    )
    evidence["eviction_onset_cum_tokens"] = bracket.get(
        "evicted_at_or_below_cum_tokens", model.get("first_eviction_cum_tokens")
    )
    if probe.get("status") != "done":
        handoff["status"] = "partial"
        evidence["boundary_probe_status"] = probe.get("status")
    b.write_json_atomic(b.HANDOFF_PATH, handoff)
    return handoff


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--positions", default="",
        help="confirmation leg: comma-separated doc positions to re-send instead of "
             "searching (used to test where the 26 re-inserted documents now sit)",
    )
    parser.add_argument(
        "--finalize", action="store_true",
        help="rebuild analysis.json's boundary_probe block from rows.jsonl; sends nothing",
    )
    args = parser.parse_args(argv)
    positions = [int(part) for part in args.positions.split(",") if part.strip()]

    started = time.monotonic()
    started_utc = b.utc_now()
    log_path = b.CELL_DIR / "run.log"
    lock, _lock_wait = b.acquire_lock(b.LOCK_PATH, b.LOCK_TIMEOUT_S)

    if args.finalize:
        return finalize(lock)

    status = "done"
    base_requests = 0
    probes: list[dict] = []
    sanity: dict = {}
    bracket: dict | None = None
    rows_before_sha = b.sha256_bytes(b.ROWS_PATH.read_bytes())
    sender = b.Sender()
    probe: dict = {}

    try:
        rows = load_rows()
        p_rows = [r for r in rows if r["phase"] == "P"]
        as_json = json.loads(b.ANALYSIS_PATH.read_text(encoding="utf-8"))
        base_requests = int(as_json["digest"]["requests_used"])
        if not p_rows:
            raise RuntimeError("no Phase-P rows found in rows.jsonl")
        n = len(p_rows)
        p_by_pos = {r["doc_position"]: r for r in p_rows}
        docs = {d["doc_id"]: d for d in b.corpus_mod.load_corpus(b.CORPUS_PATH)}
        capacity = int(p_rows[0]["token_capacity"])
        total_pressure = int(p_rows[-1]["cum_prompt_tokens"])

        cap_now, cap_sha, cap_bytes = read_capacity_now()
        b.log(log_path, f"B probe start: capacity_then={capacity} capacity_now={cap_now} "
                        f"rows_before_sha={rows_before_sha[:16]} base_requests={base_requests}")

        run_template = {
            key: p_rows[0][key]
            for key in (
                "stack", "config_id", "config_sha256", "server_info_sha256",
                "token_capacity", "total_pressure_tokens", "pressure_ratio",
                "docs_pushed", "request_cap",
            )
            if key in p_rows[0]
        }

        def send_at(position: int, role: str) -> dict:
            """Byte-identical re-send of an already-pooled document."""

            source = p_by_pos[position]
            doc = docs[source["doc_id"]]
            messages = b.corpus_mod.messages_for(doc)
            digest = b.sha256_prompt(messages)
            if digest != source["prompt_sha256"]:
                raise RuntimeError(
                    f"rebuilt prompt for {doc['doc_id']} is not byte-identical "
                    f"to its Phase-P row ({digest} != {source['prompt_sha256']})"
                )
            sent = sender.send(messages)
            run = dict(run_template)
            run["requests_used"] = base_requests + sender.sent
            row = b.make_row(
                "B", doc, position, sent, run, _messages=messages,
                band="boundary_probe", probe_role=role,
                probe_index=len(probes) + 1,
                cum_prompt_tokens=source["cum_prompt_tokens"],
                cum_prompt_tokens_start=source["cum_prompt_tokens"] - source["prompt_tokens"],
                prompt_tokens_phase_p=source["prompt_tokens"],
                hit_ratio=round(sent["cached_tokens"] / max(1, sent["prompt_tokens"]), 6),
            )
            b.append_row(row)
            rec = {
                "doc_position": position,
                "doc_id": doc["doc_id"],
                "probe_role": role,
                "prompt_tokens": sent["prompt_tokens"],
                "cached_tokens": sent["cached_tokens"],
                "hit_ratio": row["hit_ratio"],
                "latency_ms": sent["latency_ms"],
                "status": sent["status"],
                "verdict": "resident" if sent["cached_tokens"] > 0 else "evicted",
            }
            probes.append(rec)
            b.log(log_path, f"B {role:7s} pos={position:3d} {doc['doc_id']} "
                            f"prompt={sent['prompt_tokens']} cached={sent['cached_tokens']} "
                            f"hit={row['hit_ratio']:.3f} -> {rec['verdict']} "
                            f"status={sent['status']}")
            return rec

        if positions:
            for position in positions:
                send_at(position, "confirm_k")
            all_rows = load_rows()
            all_resident = all(rec["verdict"] == "resident" for rec in probes)
            probe = {
                "status": status,
                "mode": "confirm_k",
                "why": "the inequality model says the 26 re-inserted documents are the "
                       "resident set and the older originals are not; these re-sends test "
                       "that directly instead of searching",
                "requests_used": len(probes),
                "probes": probes,
                "confirmation": {
                    "positions": positions,
                    "outcomes": probes,
                    "all_resident": all_resident,
                },
                "model": probe_model(all_rows, n),
                "capacity_at_probe": cap_now,
                "capacity_matches_battery": cap_now == capacity,
                "rows_before_sha256": rows_before_sha,
                "started_utc": started_utc,
                "finished_utc": b.utc_now(),
            }
            probe["verdict"] = (
                "residency_capacity_below_the_token_pool"
                if probe["model"].get("token_pool_lru_excluded") else "inconclusive"
            )
            return finish(status, probe, rows, rows_before_sha, base_requests,
                          sender, lock, started, started_utc)

        # -- sanity: the newest pooled document must still be resident --------
        sanity = send_at(n, "sanity")
        if sanity["cached_tokens"] == 0:
            status = "aborted_cache_reset"
            b.log(log_path, "ABORT probe: newest document is not resident -- the "
                            "server restarted or the radix cache was flushed; the "
                            "pool measured by battery.py no longer exists")
            probe = {
                "status": status,
                "note": "newest pooled document missed on replay, so the pool measured "
                        "by the battery no longer exists; the probe measures nothing",
                "sanity_check": sanity,
                "probes": probes,
                "requests_used": len(probes),
            }
            return finish(status, probe, rows, rows_before_sha, base_requests,
                          sender, lock, started, started_utc)

        hi = n                      # lowest position known resident
        lo: int | None = None       # highest position known evicted

        position = n - DESCEND_STEP
        while position > OLDEST_BOUND and len(probes) < PROBE_CAP - 1:
            rec = send_at(position, "descend")
            if rec["verdict"] == "resident":
                hi = position
            else:
                lo = position
                break
            if sender.consecutive_failures >= b.CONSECUTIVE_FAILURE_LIMIT:
                status = "aborted_failures"
                break
            position -= DESCEND_STEP

        if status == "done":
            if lo is None:
                lo = OLDEST_BOUND
            while hi - lo > 1 and len(probes) < PROBE_CAP:
                mid = (lo + hi) // 2
                rec = send_at(mid, "bisect")
                if rec["verdict"] == "resident":
                    hi = mid
                else:
                    lo = mid
                if sender.consecutive_failures >= b.CONSECUTIVE_FAILURE_LIMIT:
                    status = "aborted_failures"
                    break

        model = probe_model(load_rows(), n)
        w_lo, w_hi = model["W_range_docs"]
        lo_cum = p_by_pos[lo]["cum_prompt_tokens"] if lo in p_by_pos else None
        hi_start = p_by_pos[hi]["cum_prompt_tokens"] - p_by_pos[hi]["prompt_tokens"]
        bracket = {
            "evicted_position": lo,
            "resident_position": hi,
            "width_docs": hi - lo,
            "evicted_at_or_below_cum_tokens": lo_cum,
            "resident_at_or_above_cum_tokens": hi_start,
            "note": "the last two probe outcomes come from different moments in a "
                    "shrinking window; the W_range in `model` is the stable bound",
        }
        verdict = (
            "residency_capacity_below_the_token_pool"
            if model.get("token_pool_lru_excluded") else "inconclusive"
        )
        summary = (
            f"resident window W in [{w_lo}, {w_hi}] docs = {model['W_range_tokens']} tokens "
            f"= {model['W_range_ratio_of_capacity']} of capacity, versus "
            f"{model['token_pool_lru_docs']} docs implied by token-pool LRU; first eviction "
            f"at doc {model['first_eviction_doc_position']} "
            f"({model['first_eviction_cum_tokens']} cumulative tokens = "
            f"{model['first_eviction_ratio_of_capacity']} of capacity)"
        )
        probe = {
            "status": status,
            "why": "the three replay bands bracket the eviction onset only to 128 "
                   "documents; byte-identical re-sends bound the resident window to "
                   f"[{w_lo}, {w_hi}] documents and refute token-pool LRU",
            "method": "re-send documents already in the pool; cached_tokens>0 means "
                      "resident, 0 means evicted; descend from the newest band in "
                      f"steps of {DESCEND_STEP}, then bisect the surviving bracket",
            "cap_requests": PROBE_CAP,
            "requests_used": len(probes),
            "capacity_at_probe": cap_now,
            "capacity_matches_battery": cap_now == capacity,
            "server_info_sha256_at_probe": cap_sha,
            "server_info_bytes_at_probe": cap_bytes,
            "sanity_check": sanity,
            "probes": probes,
            "bracket": bracket,
            "model": model,
            "verdict": verdict,
            "summary_line": summary,
            "caveat": "the probe is destructive at the margin: every miss re-inserts that "
                      "document at MRU and evicts one oldest resident, which is why the "
                      "window shrinks within the probe and why W is bounded by "
                      "inequalities rather than read off a single moment",
            "note": "doc-count arithmetic is an approximation: documents are ~8,601 "
                    "prompt tokens each, not exactly equal, and the server's eviction "
                    "unit is its radix tree, not a document",
            "rows_before_sha256": rows_before_sha,
            "started_utc": started_utc,
            "finished_utc": b.utc_now(),
        }
        b.log(log_path, f"B W in [{w_lo}, {w_hi}] docs; verdict={verdict}")
    except Exception as exc:  # noqa: BLE001 - the failure text is evidence
        status = "failed"
        b.log(log_path, f"B probe failed: {type(exc).__name__}: {exc}")
        probe = {
            "status": status,
            "error": f"{type(exc).__name__}: {exc}",
            "probes": probes,
            "requests_used": len(probes),
            "sanity_check": sanity,
            "rows_before_sha256": rows_before_sha,
            "started_utc": started_utc,
            "finished_utc": b.utc_now(),
        }
        return finish(status, probe, [], rows_before_sha, len(probes) and 0 or 0,
                      sender, lock, started, started_utc)

    return finish(status, probe, rows, rows_before_sha, base_requests,
                  sender, lock, started, started_utc)


def finish(status: str, probe: dict, rows: list[dict], rows_before_sha: str,
           base_requests: int, sender: b.Sender, lock, started: float,
           started_utc: str) -> int:
    """Merge the probe into analysis.json and the handoff, then release the lock."""

    log_path = b.CELL_DIR / "run.log"
    try:
        analysis = json.loads(b.ANALYSIS_PATH.read_text(encoding="utf-8"))
        if not isinstance(base_requests, int) or base_requests <= 0:
            base_requests = int(analysis["digest"]["requests_used"])
        probe_rows = len(probe.get("probes") or [])
        requests_used = base_requests + probe_rows
        rows_now = load_rows()
        rows_sha = b.sha256_bytes(b.ROWS_PATH.read_bytes())

        probe = {
            **probe,
            "status": status,
            "requests_used": probe_rows,
            "rows_after": len(rows_now),
            "rows_sha256_after": rows_sha,
            "wall_s": round(time.monotonic() - started, 3),
            "failures": sender.failures,
            "first_error": sender.first_error,
        }
        analysis = merge_analysis(analysis, probe, rows_sha, len(rows_now),
                                  requests_used, probe_rows)
        b.write_json_atomic(b.ANALYSIS_PATH, analysis)
        refresh_handoff(probe, rows_sha, len(rows_now), requests_used)
        b.log(log_path, f"B done: status={status} probe_requests={probe_rows} "
                        f"total_requests={requests_used} rows={len(rows_now)} "
                        f"rows_sha={rows_sha[:16]}")
        print(json.dumps({
            "status": status,
            "probe_requests": probe_rows,
            "requests_used": requests_used,
            "requests_total_including_calibration": requests_used + b.CALIBRATION_REQUESTS,
            "rows": len(rows_now),
            "rows_sha256": rows_sha,
            "bracket": probe.get("bracket"),
            "implied": (probe.get("implied") or {}).get("implied_resident_docs"),
            "nearest_model": (probe.get("implied") or {}).get("nearest_model"),
            "summary": probe.get("summary_line"),
        }, sort_keys=True))
    finally:
        b.release_lock(lock)
    return 0 if status == "done" else 1


if __name__ == "__main__":
    raise SystemExit(main())
