#!/usr/bin/env python3
"""R2-SGL-CAP measurement cell — 4-arm battery, then an M4-shaped eviction pressure run.

WHY THIS FILE IS A MODULE AND NOT A SCRIPT
==========================================
The window driver (`window.py`) owns the clock, the lock, the container dance and the request cap;
this file owns only *what is measured*.  Keeping them apart is what lets the battery be read and
reviewed without the host in the same file, and lets the eviction run reuse the M4 corpus verbatim
so its resident-window bracket is comparable to Round 1's 0.1592-0.1645.

TWO MEASUREMENTS, ONE QUESTION
==============================
1. **Battery** — the four arms R/A/C/H x 71 turns at 32k = 284 rows, the same task content and the
   same prefix discipline as `cells/G3`, so a hit fraction here is comparable to G3's and to the
   Round-1 numbers.  Answers "does this configuration cache the working set better?"
2. **Eviction pressure** — M4-EVICT's shape: push `1.5x token_capacity` of documents through the pool
   in the newest-first-replay order M4 used, then replay oldest/middle/newest bands.  The bracket
   between the oldest replay that still hits and the newest replay that misses is the **resident
   window**, expressed as a ratio of declared `token_capacity`.  That is the number the manuscript
   reports (C54) and the number this card must re-measure on any config it claims holds more.

The eviction run imports M4's own corpus (`cells/M4/corpus.jsonl`, sha256 pinned in its manifest) and
M4's own bracket arithmetic, so a change in the measured ratio is a change in the *engine*, not in
the estimator.  Extracting the estimator rather than re-deriving it is deliberate: a re-derived
estimator would make the new ratio incomparable to 0.1592-0.1645 while looking comparable.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CELLS = REPO / "experiments" / "context-cache" / "cells"

#: Pinned by cells/M4/corpus_manifest.json — 300 docs, seed 20261023.
M4_CORPUS = CELLS / "M4" / "corpus.jsonl"
M4_MANIFEST = CELLS / "M4" / "corpus_manifest.json"
M4_CORPUS_SHA256 = "02ad7f89fc1c2eec82ed3c7d874734255c6fecfd2a3d8906c466a7ac1fef9471"

#: M4 measured 4.8547 chars/token on this corpus; kept as the same constant so pressure is equal.
M4_CHARS_PER_TOKEN = 4.8547
M4_PRESSURE_TARGET = 1.5
BAND_SIZE = 10


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Battery — the four G3 arms
# --------------------------------------------------------------------------- #
ARMS = ("R", "A", "C", "H")
TURNS_PER_ARM = 71
BUDGET_TOKENS = 32768


def arm_messages(arm: str, turns: Sequence[Mapping[str, Any]], preamble: str,
                 upto: int, summarise: Callable[[str], str]) -> list[dict[str, str]]:
    """Turn-by-turn message list for one arm.

    The arms differ only in *how earlier state is carried*, which is what makes their hit fractions
    comparable:

    * **C** (`none`)  — every turn is its own user message: the transcript is re-sent whole, newest
      last.  A full-context baseline with no structure.
    * **A** (`append_note`) — one system preamble plus one appended note per turn: **append-only**,
      so the prefix never changes and a hit is expected from turn 2 onward.
    * **R** (`summarise_in_place`) — the accumulated history is compacted into a rewritten summary
      block whenever it would cross the budget: the prefix *changes*, so a hit collapses at each
      compaction.  This is the arm that shows what a mid-context rewrite costs.
    * **H** (`hybrid`) — append-only until the budget is crossed, then summarise: the arms above
      composed in the order a real agent would hit them.

    Compaction is scheduled deterministically from the *estimated* length of the chain, exactly as
    `cells/G3/g3_cell.py:compaction_schedule` does, so the schedule is reproducible without the
    server's tokenizer and is identical across arms at the same turn.
    """
    est = lambda s: max(1, math.ceil(len(s) / 4))

    def schedule(total_turns: int) -> set[int]:
        chain = preamble
        crossing: set[int] = set()
        for t in range(1, total_turns + 1):
            chain = chain + "\n" + turns[t - 1]["text"]
            if est(chain) > BUDGET_TOKENS:
                crossing.add(t)
                # emulate the post-compaction state: preamble + the kept tail
                chain = preamble + "\n" + summarise(chain)
        return crossing

    cross = schedule(len(turns))
    kept: list[str] = []
    messages: list[dict[str, str]] = []
    if arm == "C":
        for t in range(1, upto + 1):
            messages.append({"role": "user", "content": turns[t - 1]["text"]})
        return messages

    if arm in ("A", "H"):
        notes = [f"note {t}: {turns[t - 1]['text']}" for t in range(1, upto + 1)]
        if arm == "A" or not any(t in cross for t in range(1, upto + 1)):
            return [{"role": "system", "content": preamble},
                    {"role": "user", "content": "Context so far (append-only):\n" + "\n".join(notes)}]
        # H past its first crossing: the pre-crossing notes become one summary, then append again
        first = min(t for t in cross if t <= upto)
        head = "note %d: %s" % (first, turns[first - 1]["text"])
        tail = [f"note {t}: {turns[t - 1]['text']}" for t in range(first + 1, upto + 1)]
        body = summarise("\n".join(notes[: first]))
        return [{"role": "system", "content": preamble},
                {"role": "user", "content": body},
                {"role": "user", "content": "Context since (append-only):\n" + "\n".join([head, *tail])}]

    # arm R: summarise in place at each crossing
    blocks: list[str] = []
    for t in range(1, upto + 1):
        blocks.append(f"note {t}: {turns[t - 1]['text']}")
        if t in cross:
            blocks = [summarise("\n".join(blocks))]
    return [{"role": "system", "content": preamble},
            {"role": "user", "content": "Compacted context (rewritten in place):\n" + "\n".join(blocks)}]


def default_summarise(text: str, chars: int = 750) -> str:
    body = " ".join(text.split())
    return body if len(body) <= chars else body[:chars] + " …"


def run_battery(send: Callable[..., Mapping[str, Any]], *, preamble: str,
                turns: Sequence[Mapping[str, Any]], config_id: str, config_sha256: str,
                salt_fn: Callable[[str], str], log: Callable[[str], None] = lambda _m: None,
                warmup: bool = True) -> list[dict[str, Any]]:
    """284 measured rows: 4 arms x 71 turns. One request in flight, `max_tokens 4`, temperature 0.

    A **warm-up** request precedes each arm's turn 1 and is tagged `warm1_*`, never measured.  Round 1's
    vLLM cell had no per-arm warm-up and the verifier (`V-R2-VLLM`) flagged it: A/C/H turn 1 read
    `cached=0` and the arm's first measured turn carried an establishment cost that was not the thing
    being measured.  Paying one request per arm removes that confound.
    """
    rows: list[dict[str, Any]] = []
    for arm in ARMS:
        salt = salt_fn(arm)
        warm = None
        if warmup:
            warm = send(arm_messages(arm, turns, preamble, 1, default_summarise),
                        salt=salt, rep=-1, phase="warmup")
            log(f"battery {arm}: warm-up prompt={warm['prompt_tokens']} cached={warm['cached_tokens']}")
        for turn in range(1, TURNS_PER_ARM + 1):
            messages = arm_messages(arm, turns, preamble, turn, default_summarise)
            got = send(messages, salt=salt, rep=0, phase="battery")
            prompt = int(got["prompt_tokens"])
            cached = got["cached_tokens"]
            rows.append({
                "unit": "R2-SGL-CAP",
                "stack": "sglang",
                "cell": f"R2-SGL/{config_id}/battery/{arm}",
                "config_id": config_id,
                "config_sha256": config_sha256,
                "arm": arm,
                "turn": turn,
                "turns_total": TURNS_PER_ARM,
                "budget_tokens": BUDGET_TOKENS,
                "salt": salt,
                "http_status": int(got["status"]),
                "prompt_tokens": prompt,
                # a value we cannot observe is "unavailable", never 0
                "cached_tokens": "unavailable" if cached is None else int(cached),
                "uncached_tokens": "unavailable" if cached is None else prompt - int(cached),
                "completion_tokens": int(got.get("completion_tokens") or 0),
                "ttft_ms": round(float(got.get("ttft_ms") or 0.0), 3),
                "wall_ms": round(float(got.get("wall_ms") or 0.0), 3),
                "prefix_sha256": sha256_bytes(json.dumps(messages, sort_keys=True).encode()),
                "messages": len(messages),
                "warm1_prompt_tokens": None if warm is None else int(warm["prompt_tokens"]),
                "warm1_cached_tokens": None if warm is None else warm["cached_tokens"],
                "ts_utc": utc_now(),
            })
            if turn % 10 == 0 or turn == 1:
                log(f"battery {arm} t{turn}: prompt={prompt} cached={cached}")
    return rows


# --------------------------------------------------------------------------- #
# Eviction pressure — M4's shape, M4's corpus, M4's bracket arithmetic
# --------------------------------------------------------------------------- #
def load_m4_corpus() -> list[dict[str, Any]]:
    """The M4 corpus verbatim, digest-checked against its manifest.

    A digest mismatch is a hard stop: the whole point of importing M4's corpus is that a ratio change
    is attributable to the engine.  A silently different corpus would break that attribution.
    """
    digest = sha256_file(M4_CORPUS)
    manifest = json.loads(M4_MANIFEST.read_text(encoding="utf-8"))
    if digest != M4_CORPUS_SHA256 or digest != manifest.get("corpus_sha256"):
        raise RuntimeError(f"M4 corpus digest {digest} != pinned {M4_CORPUS_SHA256}; refusing to "
                           f"re-measure a ratio against a corpus it was not measured on")
    docs = [json.loads(line) for line in M4_CORPUS.read_text(encoding="utf-8").splitlines() if line]
    return docs


def doc_messages(doc: Mapping[str, Any]) -> list[dict[str, str]]:
    """M4's append-only two-message prompt for one document — `cells/M4/corpus.py:173-179`.

    head is the *system* message and body the *user* message; concatenating them into one user
    message would produce a different prefix and therefore a different cache behaviour, which is
    exactly the estimator drift this cell must avoid.
    """
    return [{"role": "system", "content": doc["head"]},
            {"role": "user", "content": doc["body"]}]


def band_positions(n: int) -> dict[str, list[int]]:
    """M4's band choice: oldest 10, a middle 10, newest 10 (`cells/M4/battery.py:392-397`)."""
    middle_start = max(1, n // 2 - (BAND_SIZE // 2 - 1))
    return {
        "newest": list(range(max(1, n - BAND_SIZE + 1), n + 1)),
        "middle": list(range(middle_start, min(n, middle_start + BAND_SIZE) + 1))[:BAND_SIZE],
        "oldest": list(range(1, min(n, BAND_SIZE) + 1)),
    }


def run_eviction(send: Callable[..., Mapping[str, Any]], *, token_capacity: int,
                 config_id: str, config_sha256: str, salt_fn: Callable[[str], str],
                 request_cap: int, log: Callable[[str], None] = lambda _m: None,
                 docs: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Push 1.5x capacity, then replay the three bands; return the resident-window bracket.

    Requests in flight: **1**.  `max_tokens 4`, temperature 0.  Stops early (and says so) when the
    request cap would be crossed, rather than truncating a band and reporting a half-measured window.
    """
    docs = list(docs or load_m4_corpus())
    cap_target = int(round(token_capacity * M4_PRESSURE_TARGET))
    salt = salt_fn("evict")
    rows: list[dict[str, Any]] = []
    pushed: list[dict[str, Any]] = []
    cum = 0
    used = 0
    shortened = False

    # Phase P — fill the pool past capacity, newest-first replay order preserved by document id
    for doc in docs:
        if used + 1 + 2 * BAND_SIZE > request_cap:
            shortened = True
            break
        messages = doc_messages(doc)
        got = send(messages, salt=salt, rep=0, phase="pressure")
        used += 1
        prompt = int(got["prompt_tokens"])
        cum += prompt
        pushed.append({"doc": doc["doc_id"], "prompt_tokens": prompt, "cum": cum,
                       "cached_tokens": got["cached_tokens"]})
        rows.append({"phase": "P", "doc": doc["doc_id"], "prompt_tokens": prompt,
                     "cached_tokens": got["cached_tokens"], "cum_prompt_tokens": cum,
                     "http_status": got["status"]})
        if cum >= cap_target:
            break
    log(f"eviction: pushed {len(pushed)} docs, cum={cum} target={cap_target} "
        f"(ratio {cum / token_capacity:.4f})")

    # Phase R — replay the bands, oldest first is what makes the bracket monotone
    positions = band_positions(len(pushed))
    bands: dict[str, dict[str, Any]] = {}
    for band in ("newest", "middle", "oldest"):
        per_doc = []
        for pos in positions[band]:
            if used >= request_cap:
                per_doc.append({"position": pos, "hit_ratio": None, "skipped": "request cap"})
                continue
            entry = pushed[pos - 1]
            got = send(doc_messages(docs[pos - 1]), salt=salt, rep=0, phase="replay")
            used += 1
            prompt = int(got["prompt_tokens"])
            cached = got["cached_tokens"]
            hit = "unavailable" if cached is None else (cached / prompt if prompt else 0.0)
            per_doc.append({"position": pos, "doc": entry["doc"], "prompt_tokens": prompt,
                            "cached_tokens": cached, "hit_ratio": hit})
            rows.append({"phase": "R", "band": band, "position": pos, "doc": entry["doc"],
                         "prompt_tokens": prompt, "cached_tokens": cached, "cum_prompt_tokens": cum,
                         "http_status": got["status"]})
        hits = [d["hit_ratio"] for d in per_doc if isinstance(d.get("hit_ratio"), float)]
        bands[band] = {
            "positions": positions[band],
            "docs": per_doc,
            "mean_hit_ratio": (round(statistics.fmean(hits), 6) if hits else None),
        }
        log(f"eviction {band}: mean_hit={bands[band]['mean_hit_ratio']}")

    bracket = resident_bracket(pushed, bands)
    return {
        "unit": "R2-SGL-CAP",
        "config_id": config_id,
        "config_sha256": config_sha256,
        "token_capacity": token_capacity,
        "pressure_target_ratio": M4_PRESSURE_TARGET,
        "pressure_ratio": round(cum / token_capacity, 6),
        "pressure_target_tokens": cap_target,
        "total_pressure_tokens": cum,
        "pressure_shortened": shortened,
        "docs_pushed": len(pushed),
        "chars_per_token_assumed": M4_CHARS_PER_TOKEN,
        "requests_used": used,
        "requests_cap": request_cap,
        "bands": bands,
        "bracket": bracket,
        "rows": rows,
        "rows_sha256": sha256_bytes(json.dumps(rows, sort_keys=True).encode()),
        "ts_utc": utc_now(),
    }


def resident_bracket(pushed: Sequence[Mapping[str, Any]], bands: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """M4's bracket: between the oldest replay that still hits and the newest replay that misses.

    Reported as a **document count** and, through the pushed documents' cumulative token positions, as
    a **token count** and a **ratio of declared token_capacity** — the same three numbers M4 reported
    (30-31 docs, 258,035-266,636 tokens, 0.1592-0.1645), which is what makes the comparison honest.
    """
    def first_miss(band: str) -> int | None:
        for d in bands[band]["docs"]:
            if isinstance(d.get("hit_ratio"), float) and d["hit_ratio"] <= 0.0:
                return int(d["position"])
        return None

    def last_hit(band: str) -> int | None:
        positions = [int(d["position"]) for d in bands[band]["docs"]
                     if isinstance(d.get("hit_ratio"), float) and d["hit_ratio"] > 0.0]
        return max(positions) if positions else None

    hit_pos = last_hit("oldest")
    miss_pos = first_miss("newest")
    if hit_pos is None or miss_pos is None:
        return {
            "verdict": "unbracketed",
            "why": ("no replay hit at all" if hit_pos is None else "no replay miss at all"),
            "resident_docs": None, "resident_tokens": None, "ratio_of_capacity": None,
        }
    # one document is evicted per inserted document => the resident window in documents is
    # (docs_pushed - miss_position + 1) at the newest edge and (docs_pushed - hit_position + 1) at
    # the oldest edge.  The true window lies inside that interval.
    total = len(pushed)
    lo = total - miss_pos + 1
    hi = total - hit_pos + 1
    lo, hi = min(lo, hi), max(lo, hi)
    # token positions: the window's start is the cumulative position at which the first resident doc
    # begins, i.e. where the evicted prefix ends.
    tok_hi = pushed[-lo]["cum"] - pushed[-lo]["prompt_tokens"] if lo else 0
    tok_lo = pushed[-hi]["cum"] - pushed[-hi]["prompt_tokens"] if hi else 0
    return {
        "verdict": "bracketed",
        "resident_docs": [lo, hi],
        "oldest_hit_position": hit_pos,
        "newest_miss_position": miss_pos,
        "resident_tokens": [tok_lo, tok_hi],
        "ratio_of_capacity": None,  # filled by the caller, which knows capacity
        "note": "documents evict one-per-insert; the interval is the bracket M4 reported",
    }


def analyse_battery(rows: Sequence[Mapping[str, Any]], *, capacity_tokens: int | None = None,
                    bootstrap: int = 10_000, seed: int = 20251023) -> dict[str, Any]:
    """Per-arm hit fraction, mean uncached tokens/turn, and a bootstrap CI over turns."""
    import random

    rng = random.Random(seed)
    out: dict[str, Any] = {"arms": {}, "rows": len(rows)}
    for arm in ARMS:
        arm_rows = [r for r in rows if r["arm"] == arm]
        if not arm_rows:
            continue
        usable = [r for r in arm_rows if r["cached_tokens"] != "unavailable"]
        non200 = [r for r in arm_rows if int(r["http_status"]) != 200]
        prompt = sum(int(r["prompt_tokens"]) for r in usable)
        cached = sum(int(r["cached_tokens"]) for r in usable)
        unc = [int(r["uncached_tokens"]) for r in usable]
        hits = [int(r["cached_tokens"]) / int(r["prompt_tokens"]) if r["prompt_tokens"] else 0.0
                for r in usable]

        def boot(vals: list[float]) -> list[float]:
            means = []
            for _ in range(bootstrap):
                means.append(statistics.fmean(rng.choice(vals) for _ in vals))
            means.sort()
            return [round(means[int(0.025 * len(means))], 6), round(means[int(0.975 * len(means)) - 1], 6)]

        out["arms"][arm] = {
            "rows": len(arm_rows),
            "non200": len(non200),
            "hit_fraction": round(cached / prompt, 6) if prompt else None,
            "hit_fraction_ci": boot(hits) if hits else None,
            "mean_uncached_tokens_per_turn": round(statistics.fmean(unc), 4) if unc else None,
            "mean_uncached_ci": boot([float(u) for u in unc]) if unc else None,
            "prompt_tokens_total": prompt,
            "cached_tokens_total": cached,
            "zero_cached_turns": sum(1 for r in usable if int(r["cached_tokens"]) == 0),
        }
    usable_all = [r for r in rows if r["cached_tokens"] != "unavailable"]
    if usable_all:
        prompt = sum(int(r["prompt_tokens"]) for r in usable_all)
        cached = sum(int(r["cached_tokens"]) for r in usable_all)
        unc = [int(r["uncached_tokens"]) for r in usable_all]
        out["pooled"] = {
            "hit_fraction": round(cached / prompt, 6),
            "mean_uncached_tokens_per_turn": round(statistics.fmean(unc), 4),
            "note": "descriptive only: four different policies",
        }
    if capacity_tokens:
        out["capacity_tokens"] = capacity_tokens
    return out
