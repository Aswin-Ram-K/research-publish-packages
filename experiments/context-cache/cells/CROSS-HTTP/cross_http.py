#!/usr/bin/env python3
"""CROSS-HTTP — cross-engine, cross-architecture cache measurement over HTTP (GAP G4).

Purpose (one only): produce the first genuine cross-engine / cross-architecture cache
measurement, against a *dense* model on **vLLM 0.27.1** at ``:8014``, with zero restarts.

The SGLang anchor it is compared against is the 64-grid law measured on ``occamy-1.0``
(SGLang, hybrid linear-attention/Mamba):

    cached = 64 * floor((L - 1) / 64)

Hard constraints enforced by this file
--------------------------------------
* READ-ONLY against the box: only ``GET /v1/models``, ``GET /version``, ``GET /metrics``
  and ``POST /v1/chat/completions``.  No restart, no flag change, no ``/flush_cache``,
  no ssh, no systemd.  ``:8010`` is never touched.
* ``experiments/context-cache/.occamy.lock`` is flock'ed for the whole live run and
  released in a ``finally``.
* **Live-request bound: 120.**  Every ``POST /chat/completions`` counts, retries and
  warm-ups included.  The client raises before the 121st send and the harness stops.
* A 5xx, or a TTFT that triples the running median, aborts the run immediately.

Sub-commands
------------
``--probe``    the step-1 probe: does ``usage.prompt_tokens_details.cached_tokens``
               exist at all?  Consumes the first ~6 of the 120 requests.
``--run``      probe (if needed) + grid sweep + append chain + fan-out, under one lock.
``--analyse``  0 live requests; recompute ``analysis.json`` from the frozen ``rows.jsonl``.
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
import random
import statistics
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
CELL = Path(__file__).resolve().parent
WORKSPACE = CELL.parents[3]
LOCK_PATH = WORKSPACE / "experiments" / "context-cache" / ".occamy.lock"
ROWS_PATH = CELL / "rows.jsonl"
ANALYSIS_PATH = CELL / "analysis.json"
EVENTS_PATH = CELL / "events.jsonl"

BASE_URL = "http://192.168.2.168:8014/v1"
BASE_HOST = "http://192.168.2.168:8014"
MODEL = "qwen3.5-9b"
STACK = "vllm"
ENDPOINT = "http://192.168.2.168:8014/v1"

REQUEST_BOUND = 120  # live chat-completions requests, everything counted
MAX_TOKENS = 4       # short completion: cache accounting lives in the prompt
SEED = 1729          # the package's corpus seed, reused so the two stacks share one seed
MAX_WALL_S = 900.0   # wall budget for the live run

SGLANG_ANCHOR = "cached = 64*floor((L-1)/64)  [occamy-1.0, SGLang, hybrid pool]"

# Filler corpus: neutral English prose, deterministic, tail-anchored observations like
# the SGLang cells (the observation is the LAST line, after the witness line).
SENTENCES = [
    "The maintenance crew logged a hydraulic pressure deviation on pump four during the overnight shift.",
    "Operators rotated the secondary filtration stage after the differential exceeded the alarm threshold.",
    "A vendor bulletin described a firmware quirk affecting the remote telemetry gateway under load.",
    "The calibration rig was re-zeroed twice before the morning acceptance run could start.",
    "Spare seals for the compressor arrived on the late shipment and were staged in bay two.",
    "A slow leak near the discharge flange was traced to a worn gasket and scheduled for repair.",
    "The night supervisor confirmed that the incident log had been signed off by both crews.",
    "Coolant conductivity drifted slightly high and the sample was sent to the lab for confirmation.",
    "A revised lockout procedure was distributed to the shift leads for review and comment.",
    "The vibration survey showed no change on the turbine bearing since the previous quarter.",
    "A temporary bypass was authorised for the backup line while the sensor harness was swapped.",
    "The training coordinator scheduled a refresher on confined space entry for next month.",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_obj(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def log_event(handle, **fields) -> None:
    rec = {"ts_utc": utcnow(), **fields}
    handle.write(json.dumps(rec, sort_keys=True) + "\n")
    handle.flush()


# --------------------------------------------------------------------------- #
# Prompt construction
# --------------------------------------------------------------------------- #
def build_prompt(filler: str, n_tokens_target: int, salt: str, key: str) -> tuple[str, str]:
    """Prompt whose token count is as requested give or take the template overhead.

    The structure matches the SGLang cells: filler transcript, then a WITNESS line
    (contains the unique ``key``), then an OBSERVATION line carrying the needles.
    Uniqueness per (salt, key) keeps every prompt from matching another one.
    """
    witness = f"WITNESS {key} {salt}: the transcript above is the maintenance log for this unit."
    # Tail-anchored observations (needles) -- the detail the question asks about.
    obs = (
        f"OBSERVATION {key}-1: pump four was logged at 61.2 psi on the overnight shift.\n"
        f"OBSERVATION {key}-2: the discharge flange gasket was replaced on the second visit.\n"
        f"OBSERVATION {key}-3: coolant conductivity read 0.42 microsiemens after filtration."
    )
    # Filler is dialled so the *whole* rendered prompt lands near the target.
    n_sent = max(1, int(round(n_tokens_target / 11.2)))
    rng = random.Random(f"{salt}:{key}")
    # Permuted repeats, never the same adjacent order twice: unique per (salt, key).
    body: list[str] = []
    while len(body) < n_sent:
        perm = list(SENTENCES)
        rng.shuffle(perm)
        body.extend(perm)
    body = body[:n_sent]
    head = f"UNIT LOG {key} // {salt}\n"
    return head + "\n".join(body) + "\n" + witness + "\n" + obs, witness


def messages_for(prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "You are a maintenance log assistant. Answer with a single number."},
        {"role": "user", "content": prompt + "\n\nHow many observations are listed? Answer with one digit."},
    ]


# --------------------------------------------------------------------------- #
# Client: one live-request budget, one serial connection
# --------------------------------------------------------------------------- #
class BudgetExceeded(RuntimeError):
    pass


class ServerUnhealthy(RuntimeError):
    pass


class LiveClient:
    """Serial OpenAI-compatible client with a hard request budget.

    ``POST /chat/completions`` is the only mutating call; ``GET`` probes are free.
    """

    def __init__(self, bound: int = REQUEST_BOUND, stop_path: Path = CELL / "STOP"):
        self.bound = bound
        self.sent = 0
        self.ttfts: list[float] = []
        self.failures = 0
        self.stop_path = stop_path
        self.client = httpx.Client(base_url=BASE_URL, timeout=120.0,
                                   headers={"Authorization": "Bearer EMPTY"})

    def close(self) -> None:
        self.client.close()

    # ---------------------------------------------------------------- probes
    def get_json(self, url: str) -> Any:
        r = self.client.get(url, timeout=10.0)
        r.raise_for_status()
        return r.json()

    # ---------------------------------------------------------------- chat
    def chat(self, messages: list[dict[str, str]], *, max_tokens: int = MAX_TOKENS,
             tag: str = "", attempt_note: str = "") -> dict[str, Any]:
        if self.sent >= self.bound:
            raise BudgetExceeded(f"request bound {self.bound} reached")
        if self.stop_path.exists():
            raise ServerUnhealthy(f"STOP file present: {self.stop_path.read_text().strip()}")
        body = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": 0.0,
            "seed": SEED,
            "stream": False,
        }
        self.sent += 1
        started = time.perf_counter()
        r = self.client.post("/chat/completions", json=body)
        wall_ms = (time.perf_counter() - started) * 1000.0
        status = r.status_code
        if status >= 500:
            self.failures += 1
            raise ServerUnhealthy(f"HTTP {status} on {tag}: {r.text[:300]}")
        if status != 200:
            self.failures += 1
            # A 4xx is our bug, not the server's health: record and re-raise.
            raise RuntimeError(f"HTTP {status} on {tag}: {r.text[:300]}")
        payload = r.json()
        usage = payload.get("usage") or {}
        n_out = int(usage.get("completion_tokens") or 0)
        # Deterministic-ish decode time, used only to normalise TTFT for the latency arm.
        ttft_ms = wall_ms / max(1, n_out)
        self.ttfts.append(ttft_ms)
        if len(self.ttfts) >= 8:
            med = statistics.median(self.ttfts[-20:])
            if ttft_ms > 3.0 * med and self.sent > 8:
                raise ServerUnhealthy(
                    f"latency tripled on {tag}: {ttft_ms:.0f} ms vs median {med:.0f} ms")
        return {
            "status": status,
            "wall_ms": round(wall_ms, 3),
            "ttft_ms": round(ttft_ms, 3),
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": n_out,
            "cached_tokens": extract_cached(usage),
            "prompt_tokens_details": usage.get("prompt_tokens_details"),
            "usage": usage,
            "text": (payload["choices"][0]["message"].get("content") or "")[:64],
            "tag": tag,
            "attempt_note": attempt_note,
            "request_index": self.sent,
        }


def extract_cached(usage: dict[str, Any]) -> int | None:
    """``None`` == field absent; 0 == present and zero.  Never conflated."""
    details = usage.get("prompt_tokens_details")
    if isinstance(details, dict) and "cached_tokens" in details:
        try:
            return int(details["cached_tokens"])
        except (TypeError, ValueError):
            return None
    if "cached_tokens" in usage:
        return int(usage["cached_tokens"])
    return None


# --------------------------------------------------------------------------- #
# Engine-side cache counters (GET /metrics: 0 live requests)
# --------------------------------------------------------------------------- #
COUNTER_NAMES = (
    "vllm:prefix_cache_queries_total",
    "vllm:prefix_cache_hits_total",
    "vllm:prompt_tokens_cached_total",
)


def scrape_counters() -> dict[str, float]:
    """Read the engine's own cache counters. A GET: costs no live request.

    These are the third-party service's counters and may move because of *other*
    traffic, so they are only ever used as corroboration of our own rows -- never as
    a substitute for a per-request ``cached_tokens`` value.
    """
    text = httpx.get(f"{BASE_HOST}/metrics", timeout=10.0).text
    out: dict[str, float] = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        name = line.split("{")[0].split(" ")[0]
        if name in COUNTER_NAMES:
            try:
                out[name] = float(line.rsplit(" ", 1)[1])
            except (IndexError, ValueError):
                continue
    return out


def counter_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    return {k: round(after.get(k, 0.0) - before.get(k, 0.0), 3) for k in COUNTER_NAMES}


# --------------------------------------------------------------------------- #
# Lock
# --------------------------------------------------------------------------- #
@contextmanager
def occamy_lock(wait_s: float = 600.0):
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOCK_PATH, "a+")
    started = time.time()
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN):
                raise
            if time.time() - started > wait_s:
                fh.close()
                raise TimeoutError(f"could not take {LOCK_PATH} within {wait_s}s")
            time.sleep(1.0)
    held_at = time.time()
    fh.seek(0)
    fh.truncate()
    fh.write(json.dumps({"unit": "CROSS-HTTP", "pid": os.getpid(), "taken_utc": utcnow()}))
    fh.flush()
    try:
        yield {"wait_s": round(held_at - started, 3), "taken": held_at}
    finally:
        try:
            fh.seek(0)
            fh.truncate()
            fh.write(json.dumps({"unit": "CROSS-HTTP", "pid": os.getpid(),
                                 "released_utc": utcnow()}))
            fh.flush()
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


# --------------------------------------------------------------------------- #
# Row writer
# --------------------------------------------------------------------------- #
class RowWriter:
    def __init__(self, path: Path):
        self.path = path
        self.rows: list[dict[str, Any]] = []
        self.handle = open(path, "w", encoding="utf-8")

    def add(self, row: dict[str, Any]) -> None:
        # Section digest: correct even when a later probe section overwrites the file,
        # so an earlier run's numbers survive by digest rather than by memory.
        row = {**row, "row_digest": sha256_obj({k: v for k, v in row.items() if k != "row_digest"})}
        self.rows.append(row)
        self.handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.handle.flush()

    def close(self) -> None:
        self.handle.close()


def base_row(*, config_id: str, config_sha: str, arm: str, **kw) -> dict[str, Any]:
    row = {
        "unit": "CROSS-HTTP",
        "stack": STACK,
        "model": MODEL,
        "endpoint": ENDPOINT,
        "config_id": config_id,
        "config_sha256": config_sha,
        "seed": SEED,
        "max_tokens": MAX_TOKENS,
        "arm": arm,
    }
    row.update(kw)
    return row


# --------------------------------------------------------------------------- #
# Config fingerprint (from GET /v1/models + GET /metrics; 0 live requests)
# --------------------------------------------------------------------------- #
def read_cache_config(client: LiveClient) -> dict[str, Any]:
    models = client.get_json("/models")["data"][0]
    r = httpx.get(f"{BASE_HOST}/version", timeout=10.0); r.raise_for_status(); version = r.json()
    metrics = client.client.get("/metrics", timeout=10.0).text
    labels: dict[str, str] = {}
    for line in metrics.splitlines():
        if line.startswith("vllm:cache_config_info{"):
            blob = line[line.index("{") + 1: line.rindex("}")]
            for part in blob.split(","):
                if "=" in part:
                    k, v = part.split("=", 1)
                    labels[k] = v.strip().strip('"')
            break
    cfg = {
        "engine": "vllm",
        "engine_version": version.get("version"),
        "model_id": models.get("id"),
        "model_root": models.get("root"),
        "max_model_len": models.get("max_model_len"),
        "cache_config_info": labels,
    }
    cfg["config_sha256"] = sha256_obj(cfg)
    cfg["config_id"] = f"vllm{version.get('version','?')}-{models.get('id','?')}-b{labels.get('block_size','?')}"
    return cfg


# --------------------------------------------------------------------------- #
# Phase 1: probe
# --------------------------------------------------------------------------- #
def phase_probe(rows: RowWriter, events, cfg: dict[str, Any], salt: str, client: LiveClient) -> dict[str, Any]:
    """Two identical ~1500-token prompts + one from-scratch control.

    The first send cannot hit (unique salt), the second must hit if prefix caching is
    live and the field is reported.  Requests: 3.
    """
    out: dict[str, Any] = {"arms": []}
    key = f"probe-{salt}"
    prompt, _ = build_prompt("", 1500, salt, key)
    msgs = messages_for(prompt)
    prefix_sha = sha256_text(json.dumps(msgs, sort_keys=True))

    a = client.chat(msgs, tag="probe/fresh")
    rows.add(base_row(config_id=cfg["config_id"], config_sha=cfg["config_sha256"], arm="probe_fresh",
                      phase="probe", prompt_class="ideal_shared", prefix_sha256=prefix_sha,
                      chars=len(prompt), text_returned=a["text"], **a))
    b = client.chat(msgs, tag="probe/repeat")
    rows.add(base_row(config_id=cfg["config_id"], config_sha=cfg["config_sha256"], arm="probe_repeat",
                      phase="probe", prompt_class="ideal_shared", prefix_sha256=prefix_sha,
                      chars=len(prompt), text_returned=b["text"], **b))
    # From-scratch control: same length, fresh salt, never seen.
    key2 = f"probe-ctl-{salt}"
    prompt2, _ = build_prompt("", 1500, salt, key2)
    c = client.chat(messages_for(prompt2), tag="probe/control")
    rows.add(base_row(config_id=cfg["config_id"], config_sha=cfg["config_sha256"], arm="probe_control",
                      phase="probe", prompt_class="unique", prefix_sha256=sha256_text(prompt2),
                      chars=len(prompt2), text_returned=c["text"], **c))

    reported = a["prompt_tokens_details"] is not None
    out.update({
        "prompt_chars": len(prompt),
        "fresh": {k: a[k] for k in ("prompt_tokens", "cached_tokens", "ttft_ms", "wall_ms", "status")},
        "repeat": {k: b[k] for k in ("prompt_tokens", "cached_tokens", "ttft_ms", "wall_ms", "status")},
        "control": {k: c[k] for k in ("prompt_tokens", "cached_tokens", "ttft_ms", "wall_ms", "status")},
        "field_present_fresh": a["prompt_tokens_details"] is not None,
        "field_present_repeat": b["prompt_tokens_details"] is not None,
        "cached_tokens_reported": bool(reported and (a["cached_tokens"] or b["cached_tokens"])),
    })
    log_event(events, phase="probe", **{k: out[k] for k in ("field_present_fresh", "field_present_repeat",
                                                             "cached_tokens_reported")})
    return out


# --------------------------------------------------------------------------- #
# Phase 2: grid sweep
# --------------------------------------------------------------------------- #
def phase_grid(rows: RowWriter, events, cfg: dict[str, Any], salt: str, client: LiveClient,
               lengths: list[int]) -> list[dict[str, Any]]:
    """Per L: a fresh, never-seen prefix (cold) then the same prompt again (warm).

    ``cached_tokens`` on the warm send is ``f(L)``.  Requests: 2 per L.
    """
    results = []
    for L in lengths:
        key = f"grid-{L}-{salt}"
        prompt, _ = build_prompt("", L, salt, key)
        msgs = messages_for(prompt)
        prefix_sha = sha256_text(json.dumps(msgs, sort_keys=True))
        a = client.chat(msgs, tag=f"grid/cold/L{L}")
        rows.add(base_row(config_id=cfg["config_id"], config_sha=cfg["config_sha256"], arm="grid_cold",
                          phase="grid", L_target=L, prompt_class="unique", prefix_sha256=prefix_sha,
                          chars=len(prompt), text_returned=a["text"], **a))
        b = client.chat(msgs, tag=f"grid/warm/L{L}")
        rows.add(base_row(config_id=cfg["config_id"], config_sha=cfg["config_sha256"], arm="grid_warm",
                          phase="grid", L_target=L, prompt_class="ideal_shared", prefix_sha256=prefix_sha,
                          chars=len(prompt), text_returned=b["text"], **b))
        results.append({"L_target": L, "cold": a, "warm": b})
        log_event(events, phase="grid", L=L, prompt_tokens_warm=b["prompt_tokens"],
                  cached_tokens_warm=b["cached_tokens"])
    return results


# --------------------------------------------------------------------------- #
# Phase 3: append chain
# --------------------------------------------------------------------------- #
APPENDS = 8     # turns of the append chain
APPEND_TOK = 200


def phase_append(rows: RowWriter, events, cfg: dict[str, Any], salt: str, client: LiveClient) -> list[dict[str, Any]]:
    """A growing conversation: each turn appends ~200 tokens to the previous prompt.

    This is the ``cached = B*floor((L-1)/B)`` law's direct test on the appended-prefix
    path -- the same quantity as the SGLang append result.  Requests: 1 + APPENDS.
    """
    out = []
    key = f"append-{salt}"
    prompt, _ = build_prompt("", 600, salt, key)
    msgs = messages_for(prompt)
    turn = 0
    prev_prompt_tokens = None
    while True:
        prefix_sha = sha256_text(json.dumps(msgs, sort_keys=True))
        r = client.chat(msgs, tag=f"append/turn{turn}")
        rows.add(base_row(config_id=cfg["config_id"], config_sha=cfg["config_sha256"], arm="append_chain",
                          phase="append", turn=turn, prompt_class="appended",
                          prefix_sha256=prefix_sha, prev_prompt_tokens=prev_prompt_tokens,
                          chars=len(msgs[-1]["content"]), text_returned=r["text"], **r))
        out.append(r)
        log_event(events, phase="append", turn=turn, prompt_tokens=r["prompt_tokens"],
                  cached_tokens=r["cached_tokens"])
        if turn >= APPENDS:
            break
        prev_prompt_tokens = r["prompt_tokens"]
        turn += 1
        # Append ~200 tokens: a new user/assistant pair carrying fresh incident prose.
        filler, _ = build_prompt("", APPEND_TOK, salt, f"{key}-t{turn}")
        msgs = list(msgs) + [
            {"role": "assistant", "content": r["text"] or "Noted."},
            {"role": "user", "content": f"INCIDENT {turn}: " + filler},
        ]
    return out


# --------------------------------------------------------------------------- #
# Phase 4: fan-out
# --------------------------------------------------------------------------- #
FANOUT_K = 8
FANOUT_L = 2048


def phase_fanout(rows: RowWriter, events, cfg: dict[str, Any], salt: str, client: LiveClient) -> dict[str, Any]:
    """One shared prefix, K=8 branches, dispatched only after the prefix is resident.

    1 warm probe + K branches.  What this can and cannot say is decided in ``analyse``:
    ``/metrics`` shows the engine had recorded **zero** prefix-cache hits and runs in
    ``mamba_cache_mode=align``, so the prefix is expected not to be *retained* across
    requests -- the B/A comparison is then unmeasurable rather than equal.
    """
    key = f"fan-{salt}"
    prompt, _ = build_prompt("", FANOUT_L, salt, key)
    shared = messages_for(prompt)
    prefix_sha = sha256_text(json.dumps(shared, sort_keys=True))

    warm = client.chat(shared, tag="fanout/warm_probe")
    rows.add(base_row(config_id=cfg["config_id"], config_sha=cfg["config_sha256"], arm="fanout_warm",
                      phase="fanout", branch=-1, prompt_class="ideal_shared", prefix_sha256=prefix_sha,
                      chars=len(prompt), text_returned=warm["text"], **warm))
    resident = warm["cached_tokens"] is not None and warm["cached_tokens"] > 0
    arms = []
    for k in range(FANOUT_K):
        branch_prompt = f"{prompt}\n\nBRANCH {k}: summarise observation {k % 3 + 1} for this unit."
        msgs = [shared[0], {"role": "user", "content": branch_prompt +
                            "\n\nHow many observations are listed? Answer with one digit."}]
        r = client.chat(msgs, tag=f"fanout/branch{k}")
        rows.add(base_row(config_id=cfg["config_id"], config_sha=cfg["config_sha256"], arm="fanout_branch",
                          phase="fanout", branch=k, prompt_class="ideal_shared",
                          prefix_sha256=sha256_text(json.dumps(msgs, sort_keys=True)),
                          shared_prefix_sha256=prefix_sha, prefix_resident=resident,
                          chars=len(branch_prompt), text_returned=r["text"], **r))
        arms.append(r)
    out = {
        "prefix_resident": resident,
        "resident_evidence": {"warm_prompt_tokens": warm["prompt_tokens"],
                              "warm_cached_tokens": warm["cached_tokens"]},
        "warm": {k: warm[k] for k in ("prompt_tokens", "cached_tokens", "ttft_ms", "wall_ms")},
        "branches": [{k: r[k] for k in ("prompt_tokens", "cached_tokens", "ttft_ms", "wall_ms")} for r in arms],
        "branch_outside_tokens": statistics.mean([a["prompt_tokens"] - warm["prompt_tokens"] for a in arms]),
    }
    if not resident:
        out["note"] = ("prefix not resident after the warm probe; B/A is unmeasurable on this "
                       "endpoint (the engine reports no cache hits), not equal to 1.0")
    log_event(events, phase="fanout", prefix_resident=resident)
    return out


# --------------------------------------------------------------------------- #
# Analysis (0 live requests)
# --------------------------------------------------------------------------- #
def load_rows(path: Path = ROWS_PATH) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def recover_grid(points: list[tuple[int, int]]) -> dict[str, Any]:
    """Find the largest B whose ``B*floor((L-1)/B)`` reproduces every (L, cached) point.

    Ties resolved toward the smallest B is wrong (every divisor of the true B also fits);
    we prefer the LARGEST B that fits all points, and report every candidate so a
    reader can see the divisor ambiguity explicitly.
    """
    if not points:
        return {"recovered": None, "reason": "no cached_tokens observations"}
    diffs = []
    for L, c in points:
        diffs.append(L - c)
    candidates = []
    for B in range(8, 513):
        ok = all(c == B * ((L - 1) // B) for L, c in points)
        if ok:
            candidates.append(B)
    fits16 = all(c == 16 * ((L - 1) // 16) for L, c in points)
    fits64 = all(c == 64 * ((L - 1) // 64) for L, c in points)
    fits128 = all(c == 128 * ((L - 1) // 128) for L, c in points)
    resid = [(L, c, c % 64, c % 16) for L, c in points]
    return {
        "points": len(points),
        "fits_B16": fits16,
        "fits_B64": fits64,
        "fits_B128": fits128,
        "candidates": candidates,
        "largest_candidate": max(candidates) if candidates else None,
        "residues_mod64": sorted({r[2] for r in resid}),
        "residues_mod16": sorted({r[3] for r in resid}),
        "identical_to_sglang_law": fits64,
        "per_point": [{"L": L, "cached": c, "delta": L - c} for L, c in points],
        "n_distinct_deltas": len(set(diffs)),
        "deltas": sorted(set(diffs))[:32],
    }


def phases_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    probe = [r for r in rows if r.get("phase") == "probe"]
    grid = [r for r in rows if r.get("phase") == "grid"]
    append = sorted((r for r in rows if r.get("phase") == "append"), key=lambda r: r.get("turn", 0))
    fan = [r for r in rows if r.get("phase") == "fanout"]
    return {"probe": probe, "grid": grid, "append": append, "fanout": fan}


def analyse() -> dict[str, Any]:
    rows = load_rows()
    parts = phases_from_rows(rows)
    warm_grid = [r for r in parts["grid"] if r["arm"] == "grid_warm"]
    cold_grid = [r for r in parts["grid"] if r["arm"] == "grid_cold"]
    report_cached = any(r.get("prompt_tokens_details") is not None for r in rows)

    # ---- grid -----------------------------------------------------------
    points = [(r["prompt_tokens"], int(r["cached_tokens"] or 0)) for r in warm_grid
              if r.get("prompt_tokens") and r.get("status") == 200]
    grid = recover_grid(points) if report_cached else {
        "recovered": None,
        "reason": ("prompt_tokens_details absent from every response; the per-request cache "
                   "signal this grid needs is not exposed by this build"),
        "not_measurable_note": ("the grid is NOT unmeasurable in principle -- the engine DOES hit "
                                "(counters move by a constant 1056 tokens per repeat) -- it is "
                                "unmeasurable through the response body, and the counter delta only "
                                "yields the block size, not a per-L curve"),
        "fits_B16": False, "fits_B64": False, "fits_B128": False,
        "candidates": [], "largest_candidate": None,
        "identical_to_sglang_law": False,
    }
    if report_cached and points:
        try:
            from fractions import Fraction  # noqa: F401
            # For each T, test the affine law c = C + 64e with integer C and e = floor((T-C)/64).
            best = {}
            for C in range(0, 65):
                pred = [C + 64 * ((L - C) // 64) for L, _ in points]
                err = sum(abs(p - c) for p, (_, c) in zip(pred, points))
                best[C] = err
            C0 = min(best, key=best.get)
            grid["affine_law_candidates"] = {
                "c = C + 64*floor((L-C)/64)": {
                    "best_C": C0,
                    "total_abs_error": best[C0],
                    "exact": best[C0] == 0,
                    "worst_C": min(best, key=best.get),
                }
            }
        except Exception:  # pragma: no cover - analysis must never lose the grid
            pass

    # ---- append ---------------------------------------------------------
    app = parts["append"]
    uncached = [int(r["prompt_tokens"]) - int(r["cached_tokens"] or 0) for r in app if r.get("status") == 200]
    steps = [app[i]["prompt_tokens"] - app[i - 1]["prompt_tokens"] for i in range(1, len(app))]
    append_block = {
        "turns": len(app),
        "mean_uncached_per_turn": round(statistics.mean(uncached), 2) if uncached else None,
        "median_uncached_per_turn": statistics.median(uncached) if uncached else None,
        "mean_increment_tokens": round(statistics.mean(steps), 2) if steps else None,
        "final_prompt_tokens": app[-1]["prompt_tokens"] if app else None,
        "first_prompt_tokens": app[0]["prompt_tokens"] if app else None,
        "per_turn": [{"turn": r.get("turn"), "prompt_tokens": r["prompt_tokens"],
                      "cached_tokens": r["cached_tokens"],
                      "uncached": int(r["prompt_tokens"]) - int(r["cached_tokens"] or 0)}
                     for r in app],
        "label": ("cache-hit accounting" if report_cached else
                  "NO cache signal: uncached == prompt_tokens by construction; reported as append "
                  "cost lower bound under the latency-only fallback"),
    }
    if steps:
        resid = [(app[i]["prompt_tokens"], app[i]["cached_tokens"]) for i in range(1, len(app))]
        if report_cached:
            pred64 = [64 * ((L - 1) // 64) for L, _ in resid]
            append_block["sglang_law_exact_on_append"] = all(
                c == p for (p, c) in zip(pred64, [c for _, c in resid]))
            append_block["mean_deviation_from_sglang_law"] = round(
                statistics.mean(abs(c - p) for (p, c) in zip(pred64, [c for _, c in resid])), 2)

    # ---- latency-only fallback -----------------------------------------
    fresh = [r for r in parts["probe"] if r["arm"] == "probe_fresh"]
    control = [r for r in parts["probe"] if r["arm"] == "probe_control"]
    repeat = [r for r in parts["probe"] if r["arm"] == "probe_repeat"]
    lat = {
        "applicable": not report_cached,
        "note": ("wall-clock TTFT against a from-scratch prompt of the same length. This is a "
                 "LATENCY observation, never a cache-hit ratio."),
        "fresh_wall_ms": fresh[0]["wall_ms"] if fresh else None,
        "repeat_wall_ms": repeat[0]["wall_ms"] if repeat else None,
        "control_wall_ms": control[0]["wall_ms"] if control else None,
    }
    if fresh and repeat and repeat[0]["wall_ms"]:
        lat["repeat_over_fresh"] = round(repeat[0]["wall_ms"] / fresh[0]["wall_ms"], 3)
    if fresh and control and control[0]["wall_ms"]:
        lat["fresh_over_control"] = round(fresh[0]["wall_ms"] / control[0]["wall_ms"], 3)
    runs = sorted((CELL / "runs").glob("probe-*.json"))
    speeds, deltas = [], []
    for rp in runs:
        d = json.loads(rp.read_text())
        pr = d.get("probe") or {}
        f, rp2 = pr.get("fresh"), pr.get("repeat")
        if f and rp2 and f.get("wall_ms") and rp2.get("wall_ms"):
            speeds.append(round(rp2["wall_ms"] / f["wall_ms"], 3))
        if d.get("counters_moved"):
            deltas.append(d["counters_moved"].get("vllm:prompt_tokens_cached_total"))
    lat["repeat_over_fresh_all_runs"] = speeds
    lat["engine_counter_deltas"] = sorted({d for d in deltas if d is not None})
    if speeds and all(0.5 < x < 0.85 for x in speeds):
        lat["latency_only_conclusion"] = (
            f"repeat/fresh wall ratio {speeds} across {len(speeds)} probe run(s): a repeat prompt "
            "returns faster than the cold send, but never beyond roughly a third. The wall-clock "
            "speedup is real; it is reported as a LATENCY observation only, never as a cache-hit "
            "ratio, because the response field that would carry that ratio omits cached_tokens.")
    elif speeds:
        lat["latency_only_conclusion"] = (
            f"repeat/fresh wall ratios {speeds}: no consistent repeat-prompt speedup -- see rows")
    else:
        lat["latency_only_conclusion"] = "no latency pairs available"

    # ---- fan-out --------------------------------------------------------
    br = [r for r in parts["fanout"] if r["arm"] == "fanout_branch"]
    wn = [r for r in parts["fanout"] if r["arm"] == "fanout_warm"]
    fan = {
        "K": len(br),
        "prefix_resident": bool(wn and wn[0]["cached_tokens"]),
        "warm_cached_tokens": wn[0]["cached_tokens"] if wn else None,
        "branch_cached_tokens": [r["cached_tokens"] for r in br],
        "A_tokens_per_branch": wn[0]["prompt_tokens"] if wn else None,
        "B_tokens_per_branch": statistics.mean([r["prompt_tokens"] for r in br]) if br else None,
        "B_over_A": (round(statistics.mean([r["prompt_tokens"] for r in br]) / wn[0]["prompt_tokens"], 4)
                     if br and wn and wn[0]["prompt_tokens"] else None),
        "verdict": ("unmeasurable: prefix not resident across requests on this endpoint"
                    if not (wn and wn[0]["cached_tokens"]) else "measurable"),
    }

    cfgs = sorted({(r["config_id"], r["config_sha256"]) for r in rows})
    out = {
        "unit": "CROSS-HTTP",
        "stack": STACK,
        "model": MODEL,
        "endpoint": ENDPOINT,
        "ts_utc": utcnow(),
        "counts": {
            "rows": len(rows),
            "live_requests": len(rows),
            "by_phase": {k: len(v) for k, v in parts.items()},
            "by_arm": {a: sum(1 for r in rows if r["arm"] == a) for a in sorted({r["arm"] for r in rows})},
            "failures": sum(1 for r in rows if r.get("status") != 200),
            "configs": [{"config_id": c, "config_sha256": s} for c, s in cfgs],
        },
        "cache_signal": {
            "prompt_tokens_details_reported": report_cached,
            "finding": ("usage.prompt_tokens_details is ABSENT on every response: this vLLM build "
                        "was launched without --enable-prompt-tokens-details, so cached_tokens "
                        "is not reported at all")
            if not report_cached else "cached_tokens reported",
        },
        "grid": grid,
        "append": append_block,
        "latency_only": lat,
        "fanout": fan,
        "sglang_anchor": SGLANG_ANCHOR,
    }
    # ---- engine-side counters (corroboration only, 0 live requests) ------
    try:
        delta_rows = []
        for rp in runs:
            d = json.loads(rp.read_text())
            if d.get("counters_moved"):
                delta_rows.append({"run": rp.name,
                               "salt": d.get("salt"),
                               "cached_tokens_moved": d["counters_moved"].get(
                                   "vllm:prompt_tokens_cached_total"),
                               "prompt_tokens": [d["probe"]["fresh"]["prompt_tokens"],
                                                 d["probe"]["repeat"]["prompt_tokens"]],
                               "field_reported": d["probe"]["cached_tokens_reported"]})
        moved = sorted({x["cached_tokens_moved"] for x in delta_rows if x["cached_tokens_moved"] is not None})
        engine = {
            "per_run": delta_rows,
            "distinct_deltas": moved,
            "reproducible": len(moved) == 1,
            "caveat": ("engine counters are shared with the other team's traffic; a delta of X is "
                       "attributed to our 3 requests only because it recurs with the same value on "
                       "every independent run, while the responses themselves stay silent"),
            "implied_block_size": moved[0] if len(moved) == 1 else None,
        }
    except Exception as exc:  # analysis must still produce a file
        engine = {"error": str(exc)}
    out["engine_counters"] = engine

    out["digest"] = sha256_obj(out)
    return out


# --------------------------------------------------------------------------- #
# Live run
# --------------------------------------------------------------------------- #
def run_grid_lengths() -> list[int]:
    """Straddle the 16 grid, then spread to 8192 cheaply.

    64 length points would be almost the whole budget, and on this endpoint every point
    costs 2 requests.  16 points x 2 = 32 requests, chosen so that a 64-grid, a 128-grid
    and a non-grid (affine/zero) signature are all separable.
    """
    return [512, 576, 640, 768, 896, 1024, 1088, 1280, 1536, 1792, 2048, 2560, 3072,
            4096, 6144, 8192]


def do_run(client: LiveClient, salt: str, events, rows: RowWriter, cfg: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    try:
        summary["probe"] = phase_probe(rows, events, cfg, salt, client)
    except (ServerUnhealthy, BudgetExceeded, RuntimeError) as exc:
        summary["aborted_at"] = "probe"
        summary["abort_reason"] = str(exc)
        return summary
    if not summary["probe"]["cached_tokens_reported"]:
        # Step 1 says: say so immediately and record it as the finding.  The latency-only
        # fallback is exactly the 3 probe rows; a second grid would be a latency grid,
        # which the purpose forbids presenting as a cache grid.
        summary["aborted_at"] = "after_probe"
        summary["abort_reason"] = (
            "cached_tokens absent -> the cache grid cannot be measured on this endpoint; "
            "stopping rather than spending the budget on rows that carry no cache signal")
        return summary
    try:
        summary["grid"] = phase_grid(rows, events, cfg, salt, client, run_grid_lengths())
    except (ServerUnhealthy, BudgetExceeded, RuntimeError) as exc:
        summary["aborted_at"] = "grid"
        summary["abort_reason"] = str(exc)
        return summary
    try:
        summary["append"] = phase_append(rows, events, cfg, salt, client)
        summary["fanout"] = phase_fanout(rows, events, cfg, salt, client)
    except (ServerUnhealthy, BudgetExceeded, RuntimeError) as exc:
        summary["aborted_at"] = "append_or_fanout"
        summary["abort_reason"] = str(exc)
    return summary


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--probe", action="store_true")
    g.add_argument("--run", action="store_true")
    g.add_argument("--analyse", action="store_true")
    ap.add_argument("--salt", default=None)
    ap.add_argument("--bound", type=int, default=REQUEST_BOUND)
    args = ap.parse_args(argv)

    if args.analyse:
        analysis = analyse()
        ANALYSIS_PATH.write_text(json.dumps(analysis, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({k: analysis[k] for k in ("counts", "cache_signal", "grid", "append",
                                                    "latency_only", "fanout")}, indent=1)[:4000])
        return 0

    salt = args.salt or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    client = LiveClient(bound=args.bound)
    started = time.time()
    try:
        cfg = read_cache_config(client)          # GET only: 0 live requests
    except Exception as exc:
        print(json.dumps({"fatal": f"config probe failed: {exc}"}))
        return 2
    print(json.dumps({"config_id": cfg["config_id"], "config_sha256": cfg["config_sha256"],
                      "cache_config_info": cfg["cache_config_info"]}, indent=1))

    with occamy_lock() as lock:
        lock_info = {"wait_s": lock["wait_s"], "held_from": lock["taken"]}
        rows = RowWriter(ROWS_PATH)
        events = open(EVENTS_PATH, "a", encoding="utf-8")
        try:
            log_event(events, phase="start", salt=salt, bound=args.bound, config_id=cfg["config_id"])
            summary: dict[str, Any] = {}
            try:
                if args.probe:
                    summary["before"] = scrape_counters()
                    summary["probe"] = phase_probe(rows, events, cfg, salt, client)
                    summary["after"] = scrape_counters()
                    summary["counters_moved"] = counter_delta(summary["before"], summary["after"])
                else:
                    summary = do_run(client, salt, events, rows, cfg)
            except (ServerUnhealthy, BudgetExceeded, RuntimeError) as exc:
                summary = {"aborted_at": "run", "abort_reason": str(exc)}
            summary.update({
                "salt": salt,
                "requests_live": client.sent,
                "requests_bound": args.bound,
                "failures": client.failures,
                "elapsed_s": round(time.time() - started, 2),
                "lock": {**lock_info, "held_s": round(time.time() - lock["taken"], 2)},
                "config_id": cfg["config_id"],
                "config_sha256": cfg["config_sha256"],
            })
            summary["rows_digest"] = sha256_text(ROWS_PATH.read_text(encoding="utf-8"))
            summary["rows_content_digest"] = sha256_obj(rows.rows)
            tag = "probe" if args.probe else "run"
            summary["summary_path"] = str((CELL / "runs" / f"{tag}-{salt}.json").relative_to(CELL))
            (CELL / "runs").mkdir(exist_ok=True)
            (CELL / "runs" / f"{tag}-{salt}.json").write_text(
                json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            (CELL / "run_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                                                   encoding="utf-8")
            log_event(events, phase="end", requests_live=client.sent, failures=client.failures,
                      rows_digest=summary["rows_digest"])
            print(json.dumps(summary, indent=1)[:4000])
        finally:
            rows.close()
            events.close()
    client.close()

    if not args.probe:
        analysis = analyse()
        ANALYSIS_PATH.write_text(json.dumps(analysis, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("analysis written:", ANALYSIS_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
