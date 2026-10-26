#!/usr/bin/env python3
"""R2-VLLM -- measure ``--prefix-match-unit 16`` on both vLLM models, then restore.

Arms (each a one-flag delta on a record that has already served traffic here):

  OH1  occamy-1.0 on vLLM 0.27.1, :8020, GPU fraction 0.32 -- the measured occamy
       recipe (WIN-VLLM V3 / MOE-VLLM) + ``--prefix-match-unit 16``
       + ``--enable-prompt-tokens-details`` (REPAIR A: without it vLLM never
       populates ``usage.prompt_tokens_details`` and every ``cached_tokens``
       recorded by the previous run was a fabricated 0 -- 0/219 OH1 rows).
  OH1L the same recipe with ``--prefix-match-unit 8``: a LENIENCY PROBE.  2096 is
       not divisible by 8, so if the divisibility rule in
       ``vllm/config/cache.py:56-67`` is enforced this launch must be REFUSED or
       coerced.  0 model requests; it separates "the flag is inert" from "the flag
       is silently ignored".
  A1   gx10-qwen9b's OWN running ``Config.Cmd`` (BF16, fp8 KV, MTP) + the same
       flag + ``--enable-prompt-tokens-details`` for usage accounting

Baselines are the on-disk block-grid cells (``MOE-VLLM`` grid 2096,
``WIN-VLLM`` grid 1056), re-measured here over a same-window baseline phase.

Repairs applied after the V-R2VLLM-TRIAGE verdict (``state/logs/R2-VLLM-triage.json``).
The previous run's 420 rows are a discarded dry run; nothing about cache reuse may
be cited from them.

  A  usage accounting.  ``--enable-prompt-tokens-details`` is now in the OH1 and
     OH1L spec ``extra`` (and in ``OCCAMY_FLAGS``, so any non-prod-cmd launch path
     that splices those flags gets it too).  ``Client.chat`` returns
     ``cached=None`` when ``usage.prompt_tokens_details`` is ABSENT -- absence is
     "unobserved", never a miss -- and every row carries ``usage_has_details``.
     ``uncached`` is ``None`` whenever ``cached`` is None.
  B  row schema (additive; ``status`` is kept).  ``http_status`` is the captured
     ``resp.status_code``; ``prefix_sha256`` is the digest of the exact POSTed
     messages bytes and ``prefix_sha256_basis`` names that surface.
  C  true cold pass.  The old docstring's "cold by construction" claim was
     FALSIFIED: the battery is one sequential append chain, so turn N's prompt is
     a superset of turn N-1's and A1 recorded 1056 cached tokens on a rep=0 turn 3.
     Pass 1 now renders every turn under its own per-turn salt (genuine first
     sight); pass 2 re-uses the pass-1 salts, so it is the repeat.  Each row
     carries ``blocks_available = prompt_tokens // resolved_block_size``.
  D  real arms.  ``phase_battery`` reads ``ARMS[i]["compaction"]`` and selects a
     ``CompactionPolicy`` + matching ``RenderPolicy``; it refuses to run when two
     arms render identical bodies (the old defect: A/C/H/R differed only by salt).
  E  the stale ``analysis.json`` guard lives in ``run_analyse``: a rows digest
     mismatch refuses the overwrite.

Hard rules:
  * gx10-occamy-nvfp4 is NEVER stopped, restarted or removed -- it is only read
    (``docker inspect``, ``/health``) and its health is re-checked after every
    step.  The variant's compiled-kernel cache is COPIED into ``logs/cache-occamy``
    so it never writes into another container's cache mount.
  * gx10-qwen9b is stopped only after the occamy phase is finished and torn down,
    and is proved back exactly as found: same Cmd, Binds, Image, /health 200,
    same served id, same ``vllm:cache_config_info`` block_size.

Fault tolerance (each rule was paid for in this unit's own runs):
  * any failed request (status != 200) stops the step that issued it -- a server
    answering 500 is not measured through;
  * a failed A1 launch RESTORES production before the next phase;
  * the restore proof reads the ``pre`` capture's nested ``prod.models`` block,
    not ``pre["models"]`` (that KeyError crashed v1 AFTER the restart had already
    succeeded -- the restore itself worked).

Phases (``--all``): pre, occamy, leniency, dense(+restore), analyse.

Usage:
  .venv/bin/python pmu16_cell.py --all
  .venv/bin/python pmu16_cell.py --phase analyse
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

import httpx  # noqa: E402

import pmu16_analyze as ana  # noqa: E402

from resextract.context import (  # noqa: E402
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    compact,
    default_est_tokens,
    make_salt,
    render,
)

LOGS = HERE / "logs"
ROWS_PATH = HERE / "rows.jsonl"
ANALYSIS_PATH = HERE / "analysis.json"
LOCK_PATH = HERE / ".." / ".." / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
MOE_BASELINE_ROWS = REPO / "experiments" / "context-cache" / "cells" / "MOE-VLLM" / "rows.jsonl"
DENSE_BASELINE_ROWS = REPO / "experiments" / "context-cache" / "cells" / "WIN-VLLM" / "rows.jsonl"

SSH = ["ssh", "-F", "/dev/null", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
       "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=8", "-o", "LogLevel=ERROR",
       "zer0null@serving-host"]

IMAGE = "sha256:2c211a1273b48e8929f893b267aeb1509e6b84654cdbde1bad56d79e3964224d"
PROD_NAME = "gx10-qwen9b"
OCCAMY_NAME = "gx10-occamy-nvfp4"
OCCAMY_PORT = 8012
PROD_PORT = 8014
VAR_PORT = 8020
ENV = ["VLLM_CACHE_ROOT=/root/.cache/vllm", "HF_HUB_OFFLINE=1", "TRANSFORMERS_OFFLINE=1",
       "VLLM_ENABLE_CUDA_COMPATIBILITY=0"]

OCCAMY_FLAGS = [
    "--served-model-name", "occamy-1.0", "--host", "0.0.0.0", "--port", "30000",
    "--tensor-parallel-size", "1", "--dtype", "bfloat16", "--kv-cache-dtype", "fp8",
    "--max-model-len", "32768", "--gpu-memory-utilization", "0.32", "--max-num-seqs", "6",
    "--max-num-batched-tokens", "8192", "--enable-chunked-prefill", "--enable-prefix-caching",
    "--reasoning-parser", "qwen3", "--trust-remote-code",
    # REPAIR A: one legal way only.  The specs below carry this too, and
    # build_spec de-duplicates, so the flag appears exactly once either way.
    "--enable-prompt-tokens-details",
]
OCCAMY_MODEL_ARG = ("/hf-cache/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/"
                    "fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652")
OCCAMY_BINDS = ["<workspace>/.cache/huggingface:/hf-cache:ro",
                f"{HERE}/logs/cache-occamy:/root/.cache/vllm"]
OCCAMY_CACHE_SRC = "<workspace>/.local/share/gx10-qwen9b/vllm-cache"

GRID_TARGETS = [100, 200, 500, 1000, 2100, 4193, 8387]
BASELINE_LENS = [3000, 9000, 17000]
BATTERY_TURNS = 16
TOTAL_REQUEST_CAP = 1000      # whole unit; the dense 16-turn battery alone is ~160
# Per config.  REPAIR2 FIX 2: 200 -> 260.  200 counted EVERY row for a config, but the
# pre-battery phases spend ~54 and the battery needs 2*16*4 = 128, so a full config needs
# ~182 and a relaunch that replays its earlier rows needs ~219.  A cap of 200 therefore
# killed the run MID-battery twice ('arm cap reached for OH1: 219/200' in logs/run.json).
# 260 = the 219 measured worst case + 41 headroom.  The real global bound stays
# TOTAL_REQUEST_CAP; phase_battery now PROVES the fit before the first request via
# battery_budget_preflight() instead of discovering it mid-battery.
# NOTE: R2-VLLM-RERUN's note below measured ~190 per BATTERY, not per arm, and named
# only OH1 + A1 while the run drives three configs (OH1, OH1L, A1).
ARM_REQUEST_CAP = 260
MAX_TOKENS = 4
LOCK_TIMEOUT_S = 900.0
# REPAIR B: the named surface for ``prefix_sha256``.  Canonical JSON of the exact
# ``messages`` list POSTed (sorted keys, no spaces, utf-8).
PREFIX_SHA_BASIS = "canonical_json(messages, sort_keys=True, separators=(',',':'))|utf-8"
# REPAIR C/D: compaction geometry for the battery arms, in offline estimated tokens.
COMPACT_KEEP_LAST = 4
COMPACT_TRIGGER_TOKENS = 3000
COMPACT_BUDGET_FRACTION = 0.5
# Per-arm render policy.  A and H share the APPEND_NOTE chain build and differ by
# seed (same policy, different salt) -- they are a salt replicate pair, and are
# labelled as such rather than sold as a policy contrast.
ARM_RENDER = {
    CompactionPolicy.APPEND_NOTE: RenderPolicy.POINTER,
    CompactionPolicy.SUMMARISE_IN_PLACE: RenderPolicy.NAIVE_APPEND,
    CompactionPolicy.FORK: RenderPolicy.POINTER_FORK,
}

CONFIGS = {
    "OH1": {"config_id": "OH1", "model": "occamy-1.0", "label": "occamy nvfp4-moe pmu16",
            "spec": {"model_arg": OCCAMY_MODEL_ARG, "quantization": "modelopt_fp4", "pmu": 16,
                     "served_model": "occamy-1.0", "max_model_len": 32768, "host_port": VAR_PORT,
                     "container": "r2v-oh1", "binds": OCCAMY_BINDS, "gpu_mem": "0.32",
                     "extra": ["--enable-prompt-tokens-details"]}},
    "OH1L": {"config_id": "OH1L", "model": "occamy-1.0", "label": "occamy pmu8 leniency probe",
             "spec": {"model_arg": OCCAMY_MODEL_ARG, "quantization": "modelopt_fp4", "pmu": 8,
                      "served_model": "occamy-1.0", "max_model_len": 32768, "host_port": VAR_PORT,
                      "container": "r2v-oh1l", "binds": OCCAMY_BINDS, "gpu_mem": "0.32",
                      "extra": ["--enable-prompt-tokens-details"]}},
    "A1": {"config_id": "A1", "model": "qwen3.5-9b", "label": "qwen9b prod cmd + pmu16",
           "spec": {"prod_cmd": True, "pmu": 16, "served_model": "qwen3.5-9b",
                    "max_model_len": 32768, "host_port": PROD_PORT, "container": "r2v-a1",
                    "binds": None, "extra": ["--enable-prompt-tokens-details"]}},
}

ARMS = [
    {"arm": "A", "seed": 3201, "compaction": CompactionPolicy.APPEND_NOTE},
    {"arm": "C", "seed": 3202, "compaction": CompactionPolicy.SUMMARISE_IN_PLACE},
    {"arm": "R", "seed": 3203, "compaction": CompactionPolicy.FORK},
    {"arm": "H", "seed": 3204, "compaction": CompactionPolicy.APPEND_NOTE},
]
# REPAIR D, said out loud so no reader can manufacture a policy contrast: A and H
# run the SAME compaction policy and differ only by seed.  They are a salt
# replicate pair; C (in-place rewrite) and R (fork) are the policy contrasts.
ARM_NOTE = ("A/H share CompactionPolicy.APPEND_NOTE and differ by seed only -- a salt "
            "replicate pair, not a policy contrast. Policy contrasts: C (SUMMARISE_IN_PLACE, "
            "head rewritten) and R (FORK, content-addressed provenance marker).")

class CapReached(RuntimeError):
    """The arm used its whole request budget.  A clean stop, not a failure."""


CONFIGS_ACTIVE: dict = {}
RUNNER: "Runner | None" = None
# Set only by ``run_analyse`` (never a module-level default), so importing this
# module or calling the guard from a test never rewrites an analysis file.
FORCE: dict = {"on": False}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- box


def sh(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
    proc = subprocess.run([*SSH, "bash -s"], input=cmd, capture_output=True, text=True,
                          timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def docker(cmd: str, timeout: int = 240) -> tuple[int, str, str]:
    return sh(f"sudo -n docker {cmd}", timeout=timeout)


def http_on_box(path: str, port: int, timeout: int = 10) -> tuple[int, str]:
    code, out, _ = sh(f"curl -s -m {timeout} -o /tmp/r2v.out -w '%{{http_code}}' "
                      f"http://serving-host:{port}{path} && cat /tmp/r2v.out", timeout=timeout + 5)
    status, body = 0, out or ""
    if body[:3].isdigit():
        status, body = int(body[:3]), body[3:]
    return status, body


def capture_models(port: int) -> dict:
    s, body = http_on_box("/v1/models", port)
    out = {"http_status": s, "id": None, "max_model_len": None}
    try:
        entry = (json.loads(body).get("data") or [{}])[0]
        out["id"], out["max_model_len"] = entry.get("id"), entry.get("max_model_len")
    except Exception:
        out["raw"] = body[:800]
    return out


def capture_metrics(port: int) -> dict:
    s, body = http_on_box("/metrics", port, timeout=15)
    info = None
    for line in body.splitlines():
        if line.startswith("vllm:cache_config_info"):
            info = line
            break
    return {"http_status": s, "cache_config_info": info}


def cache_field(line: str | None, field: str) -> str | None:
    if not line:
        return None
    m = re.search(r'[(,{]' + re.escape(field) + r'="([^"]*)"', line)
    return m.group(1) if m else None


def health(port: int) -> int:
    return http_on_box("/health", port)[0]


def occamy_health() -> dict:
    return {"port": OCCAMY_PORT, "status": health(OCCAMY_PORT), "checked_utc": utc_now()}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


# ----------------------------------------------------------------------- config


def _replace_value(cmd: list, flag: str, value: str) -> list:
    out = list(cmd)
    if flag in out:
        out[out.index(flag) + 1] = value
    return out


def build_spec(config_id: str, occamy_inspect: dict, prod_inspect: dict) -> dict:
    base = json.loads(json.dumps(CONFIGS[config_id]))
    s = base["spec"]
    if s.get("prod_cmd"):
        cmd = list(prod_inspect["Config"]["Cmd"])
        binds = list(prod_inspect["HostConfig"]["Binds"])
        image = prod_inspect["Image"]
    else:
        cmd = ["--model", s["model_arg"], *OCCAMY_FLAGS, "--quantization", s["quantization"]]
        binds = list(s["binds"])
        image = IMAGE
    cmd = _replace_value(cmd, "--served-model-name", s["served_model"])
    cmd = _replace_value(cmd, "--max-model-len", str(s["max_model_len"]))
    if s.get("gpu_mem"):
        cmd = _replace_value(cmd, "--gpu-memory-utilization", s["gpu_mem"])
    if "--prefix-match-unit" in cmd:                 # scrub anything inherited
        i = cmd.index("--prefix-match-unit")
        del cmd[i:i + 2]
    cmd += ["--prefix-match-unit", str(s["pmu"])]
    for extra in s["extra"]:
        if extra not in cmd:
            cmd.append(extra)
    s.update({"cmd": cmd, "binds": binds, "image": image, "env": ENV})
    s["config_sha256"] = hashlib.sha256(json.dumps(
        {k: s.get(k) for k in ("config_id", "cmd", "binds", "env", "served_model",
                               "max_model_len", "host_port", "image")}, sort_keys=True).encode()
    ).hexdigest()
    base["spec"] = s
    return base


# ------------------------------------------------------------------------ client


def parse_usage(usage: dict | None) -> dict:
    """REPAIR A: never collapse "details absent" into a zero.

    Returns ``{"prompt_tokens", "completion_tokens", "cached", "usage_has_details"}``
    where ``cached`` is ``int`` when ``usage.prompt_tokens_details.cached_tokens``
    is present, and ``None`` when the details block (or the field) is missing.
    ``0`` therefore means an observed miss, and only that.
    """
    usage = usage or {}
    details = usage.get("prompt_tokens_details")
    has = isinstance(details, dict) and "cached_tokens" in details
    raw = details.get("cached_tokens") if has else None
    cached = None if raw is None else int(raw)
    return {"prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "cached": cached,
            "usage_has_details": bool(has and cached is not None)}


class Client:
    def __init__(self, port: int):
        self.base = f"http://serving-host:{port}/v1"
        self.model = ""
        self.http = httpx.Client(timeout=httpx.Timeout(240.0, connect=10.0))

    def chat(self, messages, max_tokens=MAX_TOKENS, timeout=240.0):
        """POST one chat request.

        Contract (7 fields): ``(prompt_tokens, cached, completion_tokens, ttft_ms,
        wall_ms, status, text)``.  ``cached`` is ``None`` -- never 0 -- when the
        server did not report ``usage.prompt_tokens_details`` (see :func:`parse_usage`).
        ``usage_has_details`` rides along in :meth:`chat_full`.
        """
        full = self.chat_full(messages, max_tokens=max_tokens, timeout=timeout)
        return (full["prompt_tokens"], full["cached"], full["completion_tokens"],
                full["ttft_ms"], full["wall_ms"], full["http_status"], full["text"])

    def chat_full(self, messages, max_tokens=MAX_TOKENS, timeout=240.0) -> dict:
        payload = {"model": self.model, "messages": messages, "max_tokens": max_tokens,
                   "temperature": 0, "stream": True,
                   "stream_options": {"include_usage": True}}
        t0 = time.perf_counter()
        ttft, usage = None, None
        status = 0
        try:
            with self.http.stream("POST", f"{self.base}/chat/completions", json=payload,
                                  timeout=timeout) as resp:
                status = resp.status_code
                body = resp.read().decode("utf-8", "replace")
            if status != 200:
                return {"prompt_tokens": 0, "cached": None, "completion_tokens": 0,
                        "usage_has_details": False, "ttft_ms": 0.0,
                        "wall_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                        "http_status": status, "text": body[:400]}
            text = ""
            for line in body.splitlines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except Exception:
                    continue
                if obj.get("usage"):
                    usage = obj["usage"]
                for ch in obj.get("choices") or []:
                    delta = (ch.get("delta") or {}).get("content")
                    if delta:
                        if ttft is None:
                            ttft = (time.perf_counter() - t0) * 1000.0
                        text += delta
        except Exception as exc:
            return {"prompt_tokens": 0, "cached": None, "completion_tokens": 0,
                    "usage_has_details": False, "ttft_ms": 0.0,
                    "wall_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                    "http_status": 0, "text": f"EXC {exc!r}"}
        u = parse_usage(usage)
        return {"prompt_tokens": u["prompt_tokens"],
                "cached": None if u["cached"] is None else min(u["cached"], u["prompt_tokens"]),
                "completion_tokens": u["completion_tokens"],
                "usage_has_details": u["usage_has_details"],
                "ttft_ms": round(ttft or 0.0, 2),
                "wall_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                "http_status": status, "text": text[:400]}

    def tokenize(self, messages, model: str) -> int | None:
        """``/tokenize`` if the server has it.  R2-VLLM's vLLM build does NOT, so the
        caller falls back to a counted ``phase="tokens"`` request."""
        try:
            r = self.http.post(f"{self.base}/tokenize",
                               json={"model": model, "messages": messages}, timeout=30.0)
            if r.status_code == 200:
                return int(r.json().get("count"))
        except Exception:
            pass
        return None


# ------------------------------------------------------------------------- cells


def messages_sha256(messages) -> str:
    """REPAIR B: sha256 over the messages bytes named by :data:`PREFIX_SHA_BASIS`."""
    blob = json.dumps(messages, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def blocks_available(prompt_tokens, resolved_block) -> int | None:
    """REPAIR C: how many COMPLETE prompt blocks the engine could have served."""
    if not resolved_block or not prompt_tokens:
        return None
    return int(prompt_tokens) // int(resolved_block)


def uncached_of(prompt_tokens, cached) -> int | None:
    """``None`` propagates: an unobserved ``cached`` is neither a miss nor a hit."""
    if cached is None:
        return None
    return max(0, int(prompt_tokens or 0) - int(cached))


def _config_id_of(spec: dict) -> str | None:
    """The config id a bare spec dict belongs to (build_spec returns it one level up)."""
    for cid, cfg in CONFIGS.items():
        if cfg.get("spec") and all(cfg["spec"].get(k) == spec.get(k)
                                   for k in ("pmu", "container", "host_port")):
            return cid
    return spec.get("container")


def build_row(spec: dict, client_out: dict, *, phase, messages, salt, target_L=None,
              arm=None, turn=None, rep=0, note="", resolved_block=None,
              request_index=0, extra: dict | None = None) -> dict:
    """The row the writer appends.  Pure (no I/O) so the offline test can build one."""
    prompt = client_out.get("prompt_tokens") or 0
    cached = client_out.get("cached")
    status = client_out.get("http_status", client_out.get("status", 0))
    config_id = spec.get("config_id") or _config_id_of(spec)
    row = {
        "unit": "R2-VLLM", "model": CONFIGS_ACTIVE.get("model"),
        "cell": f"R2-VLLM/{config_id}/{phase}",
        "config_id": config_id, "config_sha256": spec.get("config_sha256"),
        "prefix_match_unit": spec["pmu"], "resolved_block_size": resolved_block,
        "served_model": spec["served_model"], "max_model_len": spec["max_model_len"],
        "phase": phase, "arm": arm, "turn": turn, "salt": salt, "target_L": target_L,
        "rep": rep, "prompt_tokens": prompt, "cached_tokens": cached,
        "usage_has_details": bool(client_out.get("usage_has_details")),
        "completion_tokens": client_out.get("completion_tokens") or 0,
        "uncached": uncached_of(prompt, cached),
        "blocks_available": blocks_available(prompt, resolved_block),
        "ttft_ms": client_out.get("ttft_ms"), "wall_ms": client_out.get("wall_ms"),
        "status": status,                 # kept: every existing consumer reads this
        "http_status": status,            # REPAIR B: same value, new consumers read this
        "prefix_sha256": messages_sha256(messages),
        "prefix_sha256_basis": PREFIX_SHA_BASIS,
        "request_index": request_index, "note": note, "ts_utc": utc_now(),
    }
    if extra:
        row.update(extra)
    if status != 200:
        row["error"] = client_out.get("text", "")
    return row


class Runner:
    def __init__(self, spec: dict, client: Client):
        self.spec = spec
        self.client = client
        self.client.model = spec["served_model"]
        self.resolved_block = _resolved_block_from_logs(spec)
        self.requests = 0
        LOGS.mkdir(parents=True, exist_ok=True)
        if not ROWS_PATH.exists():
            ROWS_PATH.write_text("", encoding="utf-8")
        self.handle = ROWS_PATH.open("a", encoding="utf-8")

    def n_rows(self) -> int:
        with ROWS_PATH.open(encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())

    def append(self, row: dict) -> None:
        self.handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def battery_rows(self, arm: str, rep: int | None = None) -> list[dict]:
        out = []
        with ROWS_PATH.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                if (r.get("phase") == "battery" and r.get("config_id") == self.spec["config_id"]
                        and r.get("arm") == arm and (rep is None or r.get("rep") == rep)):
                    out.append(r)
        out.sort(key=lambda r: r.get("turn") or 0)
        return out

    def send(self, phase, messages, *, salt, target_L=None, arm=None, turn=None, rep=0,
             note="", extra: dict | None = None) -> dict:
        spec = self.spec
        if self.n_rows() >= TOTAL_REQUEST_CAP:
            raise RuntimeError(f"request cap reached: {self.n_rows()}/{TOTAL_REQUEST_CAP}")
        # `spec` is bound AFTER the guard only by the row construction below; inside the
        # guard it must come from self (v5 crashed with a NameError on the closure var).
        mine = sum(1 for r in _rows() if r.get("config_id") == self.spec["config_id"])
        if mine >= ARM_REQUEST_CAP:
            # This arm has used its whole budget before the next request.  That is a
            # budget outcome, not a fault: stop THIS arm cleanly (the other arm and the
            # restore still run) and record it as a cap stop, not as an error.
            raise CapReached(f"arm cap reached for {self.spec['config_id']}: "
                             f"{mine}/{ARM_REQUEST_CAP}")
        out = self.client.chat_full(messages)
        self.requests += 1
        # REPAIR2 FIX 1: ``extra`` must reach build_row.  A version of this method
        # accepted the keyword but never forwarded it, so every battery row silently
        # lost arm_compaction/arm_render/prompt_nodes (the live run before that died
        # on the signature instead, which only LOOKED like the whole bug).
        # build_row is the ONLY owner of the merge (``row.update(extra)`` after the
        # base fields); this call forwards and never re-merges, so a key lives in
        # exactly one place.
        row = build_row(spec, out, phase=phase, messages=messages, salt=salt,
                        target_L=target_L, arm=arm, turn=turn, rep=rep, note=note,
                        resolved_block=self.resolved_block,
                        request_index=self.n_rows() + 1, extra=extra)
        self.append(row)
        status, cached = row["status"], row["cached_tokens"]
        print(f"ROW {phase} cfg={spec['config_id']} arm={arm} turn={turn} L={row['prompt_tokens']} "
              f"cached={'None' if cached is None else cached} "
              f"details={row['usage_has_details']} status={status} total={self.n_rows()}",
              flush=True)
        if status != 200:
            raise RuntimeError(f"request failed {spec['config_id']}/{phase}: {status} "
                               f"{out.get('text', '')[:200]}")
        return row


def _rows() -> list[dict]:
    if not ROWS_PATH.exists():
        return []
    out = []
    with ROWS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def _partial_analysis(config_id: str) -> dict:
    """Analyse whatever this arm produced, at the moment it stopped.

    Run-level summaries live in ``logs/run.json``; without this, a run that stops
    between phases (a cap, a failed request) leaves its battery summary nowhere.
    """
    rows = [r for r in _rows() if r.get("config_id") == config_id]
    if not rows:
        return {"n_rows": 0}
    try:
        summ = ana.model_summary(rows)
        return {"n_rows": len(rows),
                "by_phase": {p: sum(1 for r in rows if r.get("phase") == p)
                             for p in sorted({r.get("phase") for r in rows})},
                "model_summary": summ.get(next(iter(summ)), {}),
                "contests": {"grid": ana.contests(rows, "grid"),
                             "baseline": ana.contests(rows, "baseline")}}
    except Exception as exc:
        return {"n_rows": len(rows), "analysis_error": repr(exc)}


def _block_from(log_tail: str | None) -> int | None:
    m = re.search(r"Setting attention block size to\s+(\d+)", log_tail or "")
    return int(m.group(1)) if m else None


def _resolved_block_from_logs(spec: dict) -> int | None:
    """The block size THIS launch resolved to, from its own recorded startup log."""
    path = LOGS / f"{spec['config_id']}-launch.json"
    if not path.exists():
        return None
    rec = json.loads(path.read_text(encoding="utf-8"))
    return rec.get("resolved_block_size_from_log") or _block_from(rec.get("log_tail"))


def count_tokens(messages) -> int:
    n = RUNNER.client.tokenize(messages, RUNNER.spec["served_model"])
    if n is not None:
        return n
    return int(RUNNER.send("tokens", messages, salt="count",
                           note="prompt_tokens probe")["prompt_tokens"])


def make_grid_messages(target_L: int, salt: str) -> list:
    sys_txt = (f"[grid {salt}] Prefix-cache boundary probe. Target prompt length {target_L} "
               f"tokens. Reply with the single word ok.")
    filler = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
              "tempor incididunt ut labore et dolore magna aliqua").split()

    def build(n_words):
        body = " ".join(filler[i % len(filler)] for i in range(n_words))
        return [{"role": "system", "content": sys_txt},
                {"role": "user", "content": f"{salt}\n{body}"}]

    words = max(1, int((target_L - 30) * 1.3))
    for _ in range(10):
        msgs = build(words)
        count = count_tokens(msgs)
        if abs(target_L - count) <= 3:
            return msgs
        words = max(1, words + int((target_L - count) * 1.05))
    return build(words)


def phase_gate() -> dict:
    msgs = [{"role": "system", "content": "You are a cache-probe assistant. Answer in one word."},
            {"role": "user", "content": " ".join(["retention"] * 3100)}]
    tok = RUNNER.client.tokenize(msgs, RUNNER.spec["served_model"])
    r1 = RUNNER.send("gate", msgs, salt="gate-r2v", rep=0, note="identical-1")
    r2 = RUNNER.send("gate", msgs, salt="gate-r2v", rep=1, note="identical-2")
    c1, c2 = r1.get("cached_tokens"), r2.get("cached_tokens")
    return {"tokenize_count": tok, "served_prompt_tokens": r1["prompt_tokens"],
            "offset": (r1["prompt_tokens"] - tok) if tok else None,
            "rep0_cached": c1, "rep1_cached": c2,
            # REPAIR A: None (unobserved) is not False (observed miss).  ``None`` here
            # means the gate could not answer, and phase_grid says so instead of
            # calling a blind instrument "dead".
            "gate_pass": (None if c2 is None else c2 > 0)}


def phase_grid(tag: str = "grid") -> dict:
    """Feasibility probe, then the identical-prompt gate, then a contingency control.

    Each point is a PAIR (cold, repeat) of one prompt with its own fresh salt.
    7 points reading ``rep_cached == 0`` says nothing about the flag: it says the
    instrument is dead on this launch.  So:

      1. any point with reuse -> verdict "reuse-seen";
      2. none, and the literal identical-prompt gate also reports 0 -> verdict
         "instrument-dead": the flag's effect is UNOBSERVABLE on this server;
      3. none, but the gate reports reuse -> verdict "flag-blocks-reuse", and this
         run then issues ONE control at a target that is an exact multiple of the
         resolved block (2096 / 1056) and one at an exact multiple of 16.  A cache
         that serves the block multiple but not the 16 multiple is still on the
         block grid; one that serves both is on a 16 grid; one that serves neither
         is not caching this prompt shape at all.
    """
    out = []
    for target in GRID_TARGETS:
        salt = f"r2v-{RUNNER.spec['config_id']}-{tag}-{target}"
        msgs = make_grid_messages(target, salt)
        cold = RUNNER.send(tag, msgs, salt=salt, target_L=target, rep=0, note=f"target={target}")
        rep = RUNNER.send(tag, msgs, salt=salt, target_L=target, rep=1, note=f"target={target}")
        out.append({"target": target, "L": cold["prompt_tokens"],
                    "cold_cached": cold["cached_tokens"], "rep_cached": rep["cached_tokens"],
                    "reuse": bool((rep["cached_tokens"] or 0) > 0),
                    "verdict": _reuse_verdict(rep["cached_tokens"], cold["prompt_tokens"])})
    result = {"points": out, "n_reuse": sum(1 for p in out if p["reuse"])}
    gate = phase_gate()
    result["gate"] = gate
    if result["n_reuse"]:
        result["verdict"] = "reuse-seen"
    elif gate["gate_pass"] is None:
        result["verdict"] = "usage-unobserved"   # blind accounting, NOT a dead cache
    elif not gate["gate_pass"]:
        result["verdict"] = "instrument-dead"
    else:
        result["verdict"] = "flag-blocks-reuse"
        g = RUNNER.resolved_block
        ctrl = []
        for label, target in (("block_multiple", g), ("sixteen_multiple", 4096)):
            salt = f"r2v-{RUNNER.spec['config_id']}-ctrl-{label}"
            msgs = make_grid_messages(target, salt)
            c0 = RUNNER.send("control", msgs, salt=salt, target_L=target, rep=0, note=label)
            c1 = RUNNER.send("control", msgs, salt=salt, target_L=target, rep=1, note=label)
            ctrl.append({"label": label, "target": target, "L": c0["prompt_tokens"],
                         "cold_cached": c0["cached_tokens"],
                         "rep_cached": c1["cached_tokens"],
                         "reuse": bool((c1["cached_tokens"] or 0) > 0)})
        result["control"] = ctrl
    return result


def phase_baseline() -> list:
    out = []
    for target in BASELINE_LENS:
        salt = f"r2v-{RUNNER.spec['config_id']}-base-{target}"
        msgs = make_grid_messages(target, salt)
        cold = RUNNER.send("baseline", msgs, salt=salt, target_L=target, rep=0, note=f"target={target}")
        rep = RUNNER.send("baseline", msgs, salt=salt, target_L=target, rep=1, note=f"target={target}")
        rc = rep["cached_tokens"]
        out.append({"target": target, "L": cold["prompt_tokens"],
                    "cold_cached": cold["cached_tokens"], "rep_cached": rc,
                    "tail": None if rc is None else rep["prompt_tokens"] - rc})
    return out


def load_turns(n: int):
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    turns = (scenario["turns"] * ((n // len(scenario["turns"])) + 1))[:n]
    assert len(turns) == n, (len(turns), n)
    return scenario["preamble"], turns


def offline_summarizer(text: str) -> str:
    """REPAIR D: deterministic offline summariser stub -- no model, no network.

    Keeps the first and last line of the folded text (so the fold is visible in the
    prompt without fabricating prose) and states how much was folded.  It exists so
    ``compact()`` can be exercised for real: the arm's identity is the compaction
    *policy*, not the quality of the summary.
    """
    lines = [ln for ln in str(text).splitlines() if ln.strip()]
    head = lines[0][:160] if lines else ""
    tail = lines[-1][:160] if len(lines) > 1 else ""
    return (f"[offline-summary v1] folded {len(lines)} lines; "
            f"first={head!r} last={tail!r}")


def battery_salt(seed: int, turn: int | None = None) -> str:
    """Per-arm salt on pass 2, per-(arm, turn) salt on pass 1.

    REPAIR C: one salt per arm made pass 1 a sequential walk (turn N's prompt is a
    superset of turn N-1's), so a "cold" row could and did report cache hits.  A
    per-turn seed gives every turn of pass 1 its own first-sight prefix.
    """
    if turn is None:
        return make_salt(int(seed))
    return make_salt(int(seed) * 1000 + int(turn))


def build_arm_messages(spec: dict, preamble: str, turns: list, *,
                       salt_for_turn, policy=None,
                       keep_last: int = COMPACT_KEEP_LAST,
                       trigger_tokens: int = COMPACT_TRIGGER_TOKENS,
                       summarizer=offline_summarizer) -> list[list[dict]]:
    """REPAIR D: one arm's 16 rendered prompts, built by its OWN compaction policy.

    The compaction policy comes from ``spec["compaction"]`` (a ``CompactionPolicy``
    or its string value) and the renderer from :data:`ARM_RENDER`; nothing is
    hardcoded to ``NAIVE_APPEND``.  ``salt_for_turn(n)`` is what makes pass 1 cold
    and pass 2 a repeat.
    """
    policy = CompactionPolicy(policy if policy is not None else spec["compaction"])
    render_policy = ARM_RENDER[policy]
    chain = [StateNode.create(preamble, "invariant")]
    events: list[dict] = []
    out: list[list[dict]] = []
    nodes: list[dict] = []
    for n, turn in enumerate(turns, 1):
        chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=n)]
        est = sum(default_est_tokens(node.text) for node in chain)
        if est > trigger_tokens:
            chain, event = compact(chain, policy, keep_last=keep_last,
                                   summarizer=summarizer, est_tokens=default_est_tokens)
            event = {**event, "turn": n, "est_tokens": est,
                     "budget_tokens": trigger_tokens * COMPACT_BUDGET_FRACTION}
            events.append(event)
        out.append(render(render_policy, chain, preamble=preamble, volatile={},
                          salt=salt_for_turn(n)))
        nodes.append({"turn": n, "head": chain[-1].node_id, "chain": chain[-1].chain_hash,
         "events": len(events)})
    # the arm's DECLARED policy is observable on every row: two arms that differ only
    # by seed share a plan (that is what a salt replicate is) and every other pair
    # does not.  A collapsed renderer leaves this identical for all four arms.
    plan = {"compaction": policy.value, "render": render_policy.value,
            "keep_last": keep_last, "trigger_tokens": trigger_tokens}
    for meta in nodes:
        meta.update(plan)
    # reachable for the run summary / per-row metadata without changing the return shape
    build_arm_messages.last_events[spec["arm"]] = events
    build_arm_messages.last_nodes[spec["arm"]] = nodes
    return out


build_arm_messages.last_events: dict = {}
build_arm_messages.last_nodes: dict = {}


def same_policy_pairs(per_arm: dict) -> list[tuple]:
    """Arm pairs that share a DECLARED compaction policy -- the only merges allowed.

    A pair that shares a policy must still be separated by its seed at the POSTed
    bytes (``prefix_sha256``), so an allowed merge here is never a collapsed arm.
    """
    out = []
    arms = sorted(per_arm)
    for ai, a in enumerate(arms):
        for b in arms[ai + 1:]:
            pa = per_arm[a].get("declared_policy", per_arm[a].get("compaction"))
            pb = per_arm[b].get("declared_policy", per_arm[b].get("compaction"))
            if pa == pb:
                out.append((a, b))
    return out


def expected_seed_pairs(per_arm: dict) -> list[tuple]:
    """Arm pairs that MUST merge: same compaction policy, and A/H share no seed -- so
    none do.  A pair merges only when it is the same policy AND the same seed, which
    no real arm pair is; the helper exists so the rule is testable (the selftest
    calls it with a synthetic pair)."""
    out = []
    arms = sorted(per_arm)
    for ai, a in enumerate(arms):
        for b in arms[ai + 1:]:
            pa = per_arm[a].get("declared_policy", per_arm[a].get("compaction"))
            pb = per_arm[b].get("declared_policy", per_arm[b].get("compaction"))
            same_seed = per_arm[a].get("seed") == per_arm[b].get("seed")
            if pa == pb and same_seed:
                out.append((a, b))
    return out


def transcript_without_pointer(messages: list[dict]) -> str:
    """Rendered content minus the header's ``[pointer ...]`` line.

    The pointer line is the per-arm salt by construction; the remaining content is
    what the arm's chain build actually contributed.  ``POINTER`` and
    ``NAIVE_APPEND`` are equal-information renderers (``render.equal_information``),
    so on the same chain they differ only there -- and that is exactly why the
    per-turn salt alone was never a policy.
    """
    msgs = list(messages)
    if msgs:
        head = str(msgs[0].get("content", ""))
        head = re.sub(r"^\[cell-[0-9a-f]+\]\n", "", head)
        msgs = [{**msgs[0], "content": head}, *msgs[1:]]
    return json.dumps(msgs, sort_keys=True)


def arm_identity_report(per_arm: dict) -> dict:
    """REPAIR D's assertion, computed: is each arm observable as its own prompt?

    For every turn, count distinct ``prefix_sha256`` across arms; for every pass,
    count distinct non-header message BODY tuples across arms (which catches a
    renderer that differs only in the header).  Returns the evidence, and the
    caller refuses to run when any arm is indistinguishable from another.
    """
    turns = max((len(v["messages"]) for v in per_arm.values()), default=0)
    per_turn_distinct = []
    collisions: list[dict] = []
    for i in range(turns):
        digests = {a: messages_sha256(v["messages"][i]) for a, v in per_arm.items()}
        bodies = {}
        for a, v in per_arm.items():
            msgs = v["messages"][i]
            bodies[a] = tuple(json.dumps(m, sort_keys=True) for m in msgs[1:])
        n_distinct = len(set(digests.values()))
        groups: dict[str, list[str]] = {}
        for a, d in digests.items():
            groups.setdefault(d, []).append(a)
        if n_distinct < len(per_arm):
            collisions.append({"turn": i + 1, "distinct": n_distinct,
                               "identical_groups": [g for g in groups.values() if len(g) > 1]})
        per_turn_distinct.append({"turn": i + 1, "distinct_prefix_sha256": n_distinct,
                                  "distinct_body_sets": len(set(bodies.values()))})
    arms = sorted(per_arm)
    body_differs = {f"{a}_vs_{b}": any(
        tuple(json.dumps(m, sort_keys=True) for m in per_arm[a]["messages"][i][1:])
        != tuple(json.dumps(m, sort_keys=True) for m in per_arm[b]["messages"][i][1:])
        for i in range(turns))
        for ai, a in enumerate(arms) for b in arms[ai + 1:]}
    # A BODY comparison alone cannot separate two append-note arms on the same
    # chain, and the rendered transcript is not a fair test either: POINTER and
    # NAIVE_APPEND are equal-information renderers by contract (they differ only on
    # a fork chain).  So identity is asserted at TWO levels, each of which is a
    # real observable on every row:
    #   * ``prefix_sha256`` -- distinct per arm at every turn (the header salt is
    #     part of the POSTed bytes, so the arms are different cache keys);
    #   * ``prompt_nodes``    -- the content-addressed compaction state each arm
    #     built; two arms merge only if one never folded where the other did.
    # ``prompt_nodes`` carries the arm's DECLARED compaction+render policy (and the
    # chain head it produced), so the plan is observable on every row.  Two arms
    # merge exactly when they share a policy AND a seed (the A/H salt replicate);
    # any other merge means the renderer/policy selection collapsed.
    expected_merges = same_policy_pairs(per_arm)
    per_turn_distinct_nodes = []
    plan_seqs = {a: set() for a in arms}
    for i in range(turns):
        plan_keys = {}
        for a, v in per_arm.items():
            plan = ((v.get("nodes") or [])[i] if i < len(v.get("nodes") or []) else {}) or {}
            plan_keys[a] = json.dumps({k: plan.get(k) for k in
                                       ("compaction", "render", "keep_last", "trigger_tokens")},
                                      sort_keys=True)
            plan_seqs[a].add(plan_keys[a])
        groups = {}
        for a, cid in sorted(plan_keys.items()):
            groups.setdefault(cid, []).append(a)
        merged = sorted(g for g in groups.values() if len(g) > 1)
        per_turn_distinct_nodes.append(
            {"turn": i + 1, "n_arms": len(plan_keys),
             "distinct_plans": len(groups), "merged_arms_at_this_turn": merged,
             "merge_allowed": all(tuple(sorted(g)) in {tuple(sorted(p)) for p in expected_merges}
                                  for g in merged)})
    plan_differ = {f"{a}_vs_{b}": plan_seqs[a] != plan_seqs[b]
                   for ai, a in enumerate(arms) for b in arms[ai + 1:]
                   if (a, b) not in {tuple(sorted(p)) for p in expected_merges}}
    # ``body_differs`` is the WEAKEST level (equal-information renderers share bodies
    # on a shared chain, and a same-policy salt pair has no reason to differ), so it
    # is reported, not required.  Identity is required at two levels that are real
    # observables: distinct POSTed bytes per turn, and a plan that separates every
    # arm pair that does not share a compaction policy.
    ok = ((not collisions) and all(plan_differ.values())
          and all(d["merge_allowed"] for d in per_turn_distinct_nodes))
    return {"ok": bool(ok), "n_arms": len(per_arm), "turns": turns,
            "min_distinct_prefix_sha256_per_turn":
                min((d["distinct_prefix_sha256"] for d in per_turn_distinct), default=0),
            "per_turn_prompt_nodes": per_turn_distinct_nodes,
            "prompt_plan_differ": plan_differ,
            "expected_salt_merges": [list(p) for p in expected_merges],
            "per_turn_plans": per_turn_distinct_nodes,
            "min_distinct_prefix_sha256_per_turn":
                min((d["distinct_prefix_sha256"] for d in per_turn_distinct), default=0),
            "per_turn": per_turn_distinct, "collisions": collisions,
            "body_differs": body_differs}


class BatteryBudgetExceeded(RuntimeError):
    """The battery cannot fit in the remaining budget.  Raised BEFORE any request."""


BATTERY_COST_EXPR = "2 * len(ARMS) * BATTERY_TURNS"


def battery_request_cost(n_turns: int | None = None, n_arms: int | None = None) -> int:
    """REPAIR2 FIX 2: the battery's exact request cost, in one named place."""
    turns = BATTERY_TURNS if n_turns is None else int(n_turns)
    arms = len(ARMS) if n_arms is None else int(n_arms)
    return 2 * arms * turns


def battery_budget_preflight(runner, n_turns: int | None = None) -> dict:
    """REPAIR2 FIX 2: prove the battery fits BEFORE spending a single request.

    ``ARM_REQUEST_CAP = 200`` counted every row for a config, but the pre-battery
    phases (gate+grid+control+tokens+baseline) already spend ~54 and the battery
    adds 2*16*4 = 128, so a full config needs ~182 -- a cap of 200 killed the run
    MID-battery twice (``arm cap reached for OH1: 219/200`` in logs/run.json) after
    the earlier rows had been paid for.  The cap is now satisfiable; this check is
    what makes it explicit rather than hopeful: it raises
    :class:`BatteryBudgetExceeded` at ZERO cost when the battery cannot fit.

    ``runner=None`` (no global RUNNER) is treated as "a fresh config": the config's
    own pre-battery rows are the 0 it has spent so far.
    """
    spec = getattr(runner, "spec", None)
    config_id = (spec or {}).get("config_id")
    if runner is None:
        already = 0
    else:
        already = sum(1 for r in _rows()
                      if config_id is not None and r.get("config_id") == config_id)
    cost = battery_request_cost(n_turns)
    out = {"config_id": config_id, "cost": cost, "cost_expr": BATTERY_COST_EXPR,
           "already_spent": already, "needed": already + cost,
           "arm_cap": ARM_REQUEST_CAP, "total_cap": TOTAL_REQUEST_CAP,
           "total_rows_before": (runner.n_rows() if runner is not None else len(_rows()))}
    out["fits_arm_cap"] = out["needed"] <= ARM_REQUEST_CAP
    out["fits_total_cap"] = out["total_rows_before"] + cost <= TOTAL_REQUEST_CAP
    if not (out["fits_arm_cap"] and out["fits_total_cap"]):
        raise BatteryBudgetExceeded(
            f"battery budget exceeded for {config_id}: needed {out['needed']} "
            f"(already {already} + battery {cost} [{BATTERY_COST_EXPR}]) vs "
            f"ARM_REQUEST_CAP {ARM_REQUEST_CAP}"
            f"{'' if out['fits_total_cap'] else f', TOTAL_REQUEST_CAP {TOTAL_REQUEST_CAP}'}"
            f" -- raised before any request was sent (0 cost).")
    return out


def phase_battery() -> dict:
    """16-turn window per arm: a genuinely cold pass 1, then a repeat pass 2.

    CORRECTION OF THE PREVIOUS CLAIM.  The old docstring said pass 1 was "cold by
    construction".  That was FALSIFIED by ``state/logs/R2-VLLM-triage.json``: the
    battery is a single sequential append chain, so turn N's prompt is a SUPERSET of
    turn N-1's prompt that was just served -- A1 recorded 1056 cached tokens on a
    rep=0 turn 3.  So:

    * pass 1 (``rep=0``) renders every turn under its own per-turn salt
      (:func:`battery_salt` with the turn number): each turn's prompt shares no
      prefix with anything else this run sent.  A non-zero ``cached`` there is
      contamination, and a real finding.
    * pass 2 (``rep=1``) re-renders with the pass-1 salts, so it is the repeat of
      exactly the byte strings pass 1 sent.
    * each arm is built by its own ``CompactionPolicy`` (:func:`build_arm_messages`)
      and rendered by the matching ``RenderPolicy`` (:data:`ARM_RENDER`).  A and H
      share APPEND_NOTE and differ by seed -- a salt replicate pair, not a policy
      contrast -- and ``ARM_NOTE`` says so on every row.
    * the arm identity assertion is checked BEFORE the first request: if two arms
      render the same bodies at any turn, the phase refuses to spend requests.
    """
    preamble, turns = load_turns(BATTERY_TURNS)
    per_arm: dict[str, dict] = {}
    for spec in ARMS:
        arm = str(spec["arm"])
        seed = int(spec["seed"])
        messages = build_arm_messages(spec, preamble, turns,
                                      salt_for_turn=lambda n, s=seed: battery_salt(s, n))
        per_arm[arm] = {"salt": battery_salt(seed), "seed": seed,
                        "declared_policy": CompactionPolicy(spec["compaction"]).value,
                        "nodes": build_arm_messages.last_nodes.get(arm),
                        "compaction": CompactionPolicy(spec["compaction"]).value,
                        "render_policy": ARM_RENDER[CompactionPolicy(spec["compaction"])].value,
                        "messages": messages}
    identity = arm_identity_report(per_arm)
    if not identity["ok"]:
        raise AssertionError(f"arm identity collapsed, refusing to spend requests: "
                             f"{json.dumps(identity)[:600]}")
    # REPAIR2 FIX 2: named, explicit budget check -- BEFORE the first request, so a
    # capped run fails loudly at zero cost instead of dying mid-battery with the
    # earlier rows already paid for (logs/run.json: 'arm cap reached for OH1: 219/200').
    budget = battery_budget_preflight(RUNNER, n_turns=len(turns))  # raises before 1st request
    for rep in (0, 1):
        for spec in ARMS:
            arm = str(spec["arm"])
            seed = int(spec["seed"])
            nodes = build_arm_messages.last_nodes.get(arm) or [None] * len(turns)
            for n, messages in enumerate(per_arm[arm]["messages"], 1):
                RUNNER.send("battery", messages,
                            salt=battery_salt(seed) if rep == 1 else battery_salt(seed, n),
                            arm=arm, turn=n, rep=rep,
                            note=f"pass={rep + 1} turns_total={len(turns)} "
                                 f"cold={'per-turn-salt' if rep == 0 else 'repeat-of-pass-1'}",
                            extra={"arm_compaction": per_arm[arm]["compaction"],
                                   "arm_render": per_arm[arm]["render_policy"],
                                   "prompt_nodes": nodes[n - 1]})
    lens = {arm: [int(r["prompt_tokens"]) for r in RUNNER.battery_rows(arm, rep=0)]
            for arm in per_arm}
    return {"turns": len(turns), "passes": [0, 1], "lens": lens,
            "salt_scheme": {"pass1": "per-(seed,turn) salt -- first sight",
                            "pass2": "per-arm seed salt re-used -- repeat"},
            "arm_identity": identity,
            "arm_policies": {a: {"compaction": v["compaction"],
                                 "render": v["render_policy"],
                                 "compaction_events": build_arm_messages.last_events.get(a, [])}
                             for a, v in per_arm.items()},
            "arm_note": ARM_NOTE}


# ------------------------------------------------------------------------ launch


def launch(cfg: dict, timeout_s: int = 480) -> dict:
    spec = cfg["spec"]
    record = {"unit": "R2-VLLM", "phase": "launch", "config_id": cfg["config_id"],
              "started_utc": utc_now(), "spec": spec, "steps": []}

    def step(name, rc, out, err):
        record["steps"].append({"step": name, "rc": rc, "stdout": (out or "")[-3000:],
                                "stderr": (err or "")[-2000:]})

    if cfg["config_id"].startswith("OH1"):
        rc, out, err = sh(f"mkdir -p {shlex.quote(str(HERE / 'logs' / 'cache-occamy'))} && "
                          f"rsync -a --delete {OCCAMY_CACHE_SRC}/ "
                          f"{shlex.quote(str(HERE / 'logs' / 'cache-occamy'))}/", timeout=900)
        step("seed-compile-cache", rc, out, err)
    else:
        rc, out, err = docker(f"stop {PROD_NAME}", timeout=180)
        step("stop-production", rc, out, err)

    rc, out, err = docker(f"rm -f {spec['container']}", timeout=120)
    step("rm-stale-variant", rc, out, err)
    args = ["run", "-d", "--name", spec["container"], "--restart", "no", "--gpus", "all",
            "--ipc", "host", "--shm-size", "16g", "--ulimit", "memlock=-1",
            "-p", f"{spec['host_port']}:30000"]
    for b in spec["binds"]:
        args += ["-v", b]
    for e in spec["env"]:
        args += ["-e", e]
    args += [spec["image"], *spec["cmd"]]
    rc, out, err = docker(" ".join(shlex.quote(a) for a in args), timeout=300)
    step("docker-run", rc, out, err)
    if rc != 0:
        record.update({"launched": False, "reason": "docker run failed",
                       "stderr": (err or "")[-4000:]})
        write_json(LOGS / f"{cfg['config_id']}-launch.json", record)
        print(f"launch {cfg['config_id']}: docker run FAILED", flush=True)
        return record

    started = time.monotonic()
    status, dead_early = 0, False
    while time.monotonic() - started < timeout_s:
        time.sleep(3)
        status = health(spec["host_port"])
        if status == 200:
            break
        _, ps, _ = docker(f"inspect -f '{{{{.State.Status}}}}' {spec['container']}", timeout=60)
        if ps.strip() in {"exited", "dead"}:
            dead_early = True
            break
    record["health_wait_s"] = round(time.monotonic() - started, 1)
    record["health_status"] = status
    _, logs, _ = docker(f"logs {spec['container']}", timeout=120)
    record["log_tail"] = (logs or "")[-60000:]
    record["resolved_block_size_from_log"] = _block_from(logs)
    record["models"] = capture_models(spec["host_port"]) if status == 200 else None
    record["metrics"] = capture_metrics(spec["host_port"]) if status == 200 else None
    record["occamy"] = occamy_health()
    record["launched"] = status == 200
    record["died_early"] = dead_early
    record["reason"] = "" if status == 200 else (
        "container exited during startup" if dead_early else "health never returned 200")
    write_json(LOGS / f"{cfg['config_id']}-launch.json", record)
    print(f"launch {cfg['config_id']}: health={status} waited={record['health_wait_s']}s "
          f"block={record['resolved_block_size_from_log']} launched={record['launched']} "
          f"occamy={record['occamy']['status']}", flush=True)
    return record


def teardown(cfg: dict) -> dict:
    """Remove the variant.  Never touches gx10-occamy-nvfp4."""
    spec = cfg["spec"]
    rec = {"unit": "R2-VLLM", "phase": "teardown", "config_id": cfg["config_id"],
           "started_utc": utc_now()}
    rc, out, err = docker(f"rm -f {spec['container']}", timeout=180)
    rec["rm_variant"] = {"rc": rc, "stdout": (out or "")[-400:], "stderr": (err or "")[-400:]}
    rec["occamy"] = occamy_health()
    rec["port_after"] = health(spec["host_port"])
    write_json(LOGS / f"{cfg['config_id']}-teardown.json", rec)
    print(f"teardown {cfg['config_id']}: rm rc={rc} occamy={rec['occamy']['status']}", flush=True)
    return rec


def restore_prod(pre: dict, timeout_s: int = 300) -> dict:
    """Start gx10-qwen9b and PROVE it is the container it was found as.

    Proof fields are compared against the ``pre`` capture: same Cmd, Binds, Image,
    running state, /health 200, same served id and max_model_len, same
    ``cache_config_info`` block_size, and occamy :8012 still 200.
    """
    rec = {"unit": "R2-VLLM", "phase": "restore", "started_utc": utc_now()}
    rc, out, err = docker(f"rm -f {CONFIGS['A1']['spec']['container']}", timeout=180)
    rec["rm_variant"] = {"rc": rc, "stdout": (out or "")[-400:], "stderr": (err or "")[-400:]}
    rc, out, err = docker(f"start {PROD_NAME}", timeout=180)
    rec["start"] = {"rc": rc, "stdout": (out or "")[-400:], "stderr": (err or "")[-400:]}
    started = time.monotonic()
    status = 0
    while time.monotonic() - started < timeout_s:
        time.sleep(3)
        status = health(PROD_PORT)
        if status == 200:
            break
    rec["health_wait_s"] = round(time.monotonic() - started, 1)
    rec["health"] = status
    rec["models"] = capture_models(PROD_PORT)
    rec["metrics"] = capture_metrics(PROD_PORT)
    rec["occamy"] = occamy_health()
    _, out, _ = docker(f"inspect {PROD_NAME}", timeout=90)
    now = json.loads(out)[0]
    before = pre["inspect_prod"]
    rec["cmd_same"] = now["Config"]["Cmd"] == before["Config"]["Cmd"]
    rec["binds_same"] = now["HostConfig"]["Binds"] == before["HostConfig"]["Binds"]
    rec["image_same"] = now["Image"] == before["Image"]
    rec["status_running"] = now["State"]["Status"] == "running"
    pre_block = cache_field(((pre.get("prod") or {}).get("metrics") or {})
                            .get("cache_config_info"), "block_size")
    now_block = cache_field(rec["metrics"]["cache_config_info"], "block_size")
    rec["block_size_pre"], rec["block_size_now"] = pre_block, now_block
    pre_models = (pre.get("prod") or {}).get("models") or {}
    rec["proven"] = bool(
        status == 200
        and rec["models"].get("id") == pre_models.get("id")
        and rec["models"].get("max_model_len") == pre_models.get("max_model_len")
        and now_block == pre_block
        and rec["cmd_same"] and rec["binds_same"] and rec["image_same"]
        and rec["status_running"] and rec["occamy"]["status"] == 200)
    rec["finished_utc"] = utc_now()
    write_json(LOGS / "prod-restore.json", rec)
    print(f"restore prod: health={status} id={rec['models'].get('id')} block "
          f"{pre_block}->{now_block} proven={rec['proven']} occamy={rec['occamy']['status']}",
          flush=True)
    return rec


# -------------------------------------------------------------------------- main


def capture_pre() -> dict:
    out = {"unit": "R2-VLLM", "captured_utc": utc_now()}
    _, o, _ = docker(f"inspect {PROD_NAME}", timeout=90)
    out["inspect_prod"] = json.loads(o)[0]
    _, o, _ = docker(f"inspect {OCCAMY_NAME}", timeout=90)
    out["inspect_occamy"] = json.loads(o)[0]
    out["prod"] = {"health": health(PROD_PORT), "models": capture_models(PROD_PORT),
                   "metrics": capture_metrics(PROD_PORT)}
    out["occamy"] = {"health": health(OCCAMY_PORT), "models": capture_models(OCCAMY_PORT),
                     "metrics": capture_metrics(OCCAMY_PORT)}
    _, o, _ = sh("sudo -n docker ps --format '{{.Names}} {{.Status}}'", timeout=60)
    out["ps"] = (o or "").strip()
    write_json(LOGS / "pre.json", out)
    print(f"pre: prod health={out['prod']['health']} id={out['prod']['models']['id']} "
          f"block={cache_field(out['prod']['metrics']['cache_config_info'], 'block_size')} "
          f"occamy health={out['occamy']['health']} id={out['occamy']['models']['id']}", flush=True)
    return out


def acquire_lock(path: Path, timeout_s: float, note: str):
    handle = path.open("a+", encoding="utf-8")
    waited = time.monotonic()
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() - waited > timeout_s:
                handle.close()
                raise TimeoutError(f"lock {path} busy")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": "R2-VLLM", "pid": os.getpid(), "note": note,
               "acquired_utc": utc_now()}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle, round(time.monotonic() - waited, 1)


def release_lock(handle, note: str) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": "R2-VLLM", "released_utc": utc_now(), "note": note}, handle)
        handle.flush()
    finally:
        fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()


def ensure_occamy_up() -> dict:
    if health(OCCAMY_PORT) == 200:
        return {"status": 200, "action": "none"}
    rc, out, err = docker(f"start {OCCAMY_NAME}", timeout=180)
    for _ in range(60):
        time.sleep(3)
        if health(OCCAMY_PORT) == 200:
            break
    return {"status": health(OCCAMY_PORT), "action": "start", "rc": rc,
            "stdout": (out or "")[-400:], "stderr": (err or "")[-400:]}


def run_config(cfg: dict, pre: dict, summary: dict, wait_s: int) -> dict:
    """Launch one arm, run gate/grid/baseline/battery, tear down.  Any failure stops it."""
    global RUNNER
    summary["configs"][cfg["config_id"]] = cfg["spec"]
    CONFIGS_ACTIVE["model"] = cfg["model"]
    rec = launch(cfg, timeout_s=wait_s)
    result = {"launched": rec.get("launched"), "reason": rec.get("reason"),
              "metrics_pmu": cache_field((rec.get("metrics") or {}).get("cache_config_info"),
                                         "prefix_match_unit") if rec.get("metrics") else None,
              "health_wait_s": rec.get("health_wait_s"),
              "resolved_block_size": rec.get("resolved_block_size_from_log"),
              "config_sha256": cfg["spec"]["config_sha256"]}
    if not rec.get("launched"):
        summary["phases"][f"{cfg['config_id']}_launch_failed"] = rec.get("reason")
        if cfg["config_id"] == "A1":
            summary["phases"]["restore"] = restore_prod(pre)   # never leave prod down
        return result
    result["rows_before_this_attempt"] = sum(
        1 for r in _rows() if r.get("config_id") == cfg["config_id"])
    RUNNER = Runner({**cfg["spec"], "config_id": cfg["config_id"]},
                    Client(cfg["spec"]["host_port"]))
    try:
        grid = phase_grid()
        result["gate"] = grid.get("gate")
        result["grid"] = grid
        if grid.get("verdict") == "usage-unobserved":
            # REPAIR A: the server reported no usage details, so any battery read
            # would be "unobserved" x 128 -- spend nothing on it.
            result["skipped"] = ("usage-unobserved: gate carried no "
                                 "usage.prompt_tokens_details (launch lacks "
                                 "--enable-prompt-tokens-details?)")
        elif grid.get("verdict") == "instrument-dead":
            # no cache hits at all on this launch: baseline/battery would only record
            # more observed zeroes, so they are skipped and the reason is written down.
            result["skipped"] = "instrument-dead: identical-prompt gate reported 0"
        else:
            result["baseline"] = phase_baseline()
            result["battery"] = phase_battery()
        result["metrics"] = capture_metrics(cfg["spec"]["host_port"])
    except CapReached as exc:
        result["cap_reached"] = str(exc)
        print(f"CAP {cfg['config_id']}: {exc}", flush=True)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        last = _rows()
        result["stopped_at_row"] = ({"config_id": last[-1].get("config_id"),
                                     "phase": last[-1].get("phase"),
                                     "request_index": last[-1].get("request_index")}
                                    if last else None)
        print(f"PHASE FAILED {cfg['config_id']}: {exc}", flush=True)
    finally:
        result["analysis"] = _partial_analysis(cfg["config_id"])
        result["teardown"] = teardown(cfg)
        summary["phases"][cfg["config_id"]] = result
    return result


def run_all(args) -> int:
    global RUNNER
    pre = capture_pre()
    summary = {"unit": "R2-VLLM", "phase": "all", "started_utc": utc_now(),
               "pre": {"prod_health": pre["prod"]["health"],
                       "occamy_health": pre["occamy"]["health"],
                       "prod_block_size": cache_field(pre["prod"]["metrics"]["cache_config_info"],
                                                      "block_size"),
                       "prod_pmu": cache_field(pre["prod"]["metrics"]["cache_config_info"],
                                               "prefix_match_unit")},
               "configs": {}, "phases": {}}
    summary["phases"]["occamy_ensure"] = ensure_occamy_up()
    handle, waited = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S, "R2-VLLM pmu16 both models")
    held_at = time.monotonic()
    summary["lock_wait_s"] = waited
    print(f"lock acquired after {waited}s", flush=True)
    try:
        oh1 = build_spec("OH1", pre["inspect_occamy"], pre["inspect_prod"])
        run_config(oh1, pre, summary, args.wait)

        oh1l = build_spec("OH1L", pre["inspect_occamy"], pre["inspect_prod"])
        summary["configs"]["OH1L"] = oh1l["spec"]
        lrec = launch(oh1l, timeout_s=args.wait)
        summary["phases"]["leniency"] = {
            "launched": lrec.get("launched"), "reason": lrec.get("reason"),
            "resolved_block_size": lrec.get("resolved_block_size_from_log"),
            "metrics_pmu": (cache_field((lrec.get("metrics") or {}).get("cache_config_info"),
                                        "prefix_match_unit") if lrec.get("metrics") else None),
            "log_tail": (lrec.get("log_tail") or "")[-12000:]}
        teardown(oh1l)

        a1 = build_spec("A1", pre["inspect_occamy"], pre["inspect_prod"])
        run_config(a1, pre, summary, args.wait)
        summary["phases"]["restore"] = restore_prod(pre)
    finally:
        summary["lock_held_s"] = round(time.monotonic() - held_at, 1)
        summary["requests_this_run"] = RUNNER.requests if RUNNER else 0
        summary["finished_utc"] = utc_now()
        write_json(LOGS / "run.json", summary)
        release_lock(handle, "R2-VLLM done")
    return 0


def _reuse_verdict(cached, prompt) -> str:
    """UNOBSERVED / FULL / PARTIAL / BLOCKED -- an unobserved row is never BLOCKED."""
    if cached is None:
        return "UNOBSERVED"
    if cached == prompt:
        return "FULL"
    return "PARTIAL" if cached > 0 else "BLOCKED"


def _battery_pass(rows: list[dict], rep: int) -> dict:
    """Per config/arm: turns, observed zeros, unobserved rows, and observed cached sum.

    REPAIR A: rows whose ``cached_tokens`` is ``None`` are counted in
    ``unobserved`` and contribute NOTHING to ``total_cached`` -- they are not
    summed as zero, and they are not counted as misses.
    """
    out: dict[str, dict] = {}
    for r in rows:
        if r.get("phase") != "battery" or r.get("rep") != rep:
            continue
        key = f"{r.get('config_id')}/{r.get('arm')}"
        d = out.setdefault(key, {"turns": 0, "zero_cached": 0, "unobserved": 0,
                                 "total_cached": 0, "pass_kind": "cold" if rep == 0 else "repeat"})
        d["turns"] += 1
        c = r.get("cached_tokens")
        if c is None:
            d["unobserved"] += 1
            continue
        d["total_cached"] += int(c)
        if int(c) == 0:
            d["zero_cached"] += 1
    return out


def analysis_guard(rows_path: Path, analysis_path: Path,
                   rows: list[dict] | None = None) -> dict:
    """REPAIR E: refuse to overwrite an analysis whose rows digest no longer matches.

    The triage found ``analysis.json`` written at 21:03:58 while rows.jsonl kept
    growing until 21:17:21 (198 further rows), so every downstream reader inherited
    zeros that the rows on disk contradict.  Rules, in order:

      * content digest -- ``submitted_rows_sha256`` (the digest of the rows this
        analysis was actually computed from) is compared with the digest of the
        file as it stands BEFORE the write.  A mismatch means the rows moved under
        the analysis.
      * legacy analysis (no digest): if it holds different row counts per chain
        than the rows now do, the write is refused.
      * ``submitted_rows_sha256`` != ``rows_sha256``: refused.
      * ``force`` -> the target is moved to ``<name>.stale-<digest8>.json`` and the
        analysis is written to a NEW file, so no digest-relevant file is clobbered.
    """
    rows = ana.load_rows(rows_path) if rows is None else rows
    digest = sha256_file(rows_path)
    n_rows = len(rows)
    out = {"rows": str(rows_path), "rows_sha256": digest, "n_rows": n_rows,
           "analysis": str(analysis_path), "refused": False, "action": "write"}
    if not analysis_path.exists():
        out["previous"] = None
        return out
    prev = json.loads(analysis_path.read_text(encoding="utf-8"))
    prev_src = prev.get("_source") or {}
    prev_sha = prev_src.get("rows_sha256")
    submitted = prev_src.get("submitted_rows_sha256")
    out["previous"] = {"rows_sha256": prev_sha, "n_rows": prev_src.get("n_rows"),
                       "submitted_rows_sha256": submitted,
                       "mtime_utc": datetime.fromtimestamp(
                           analysis_path.stat().st_mtime, timezone.utc).isoformat()}
    why = []
    if submitted is not None:
        if submitted != digest:
            why.append(f"rows moved under the analysis: submitted {submitted[:12]} != "
                       f"on-disk {str(digest)[:12]}")
    else:
        prev_counts = {(m, a): v.get("n") for m, d in prev.items() if not m.startswith("_")                        and isinstance(d, dict) for a, v in (d.get("arms") or {}).items()}
        now_counts: dict = {}
        for m, d in ana.model_summary(rows).items():
            for a, v in d["arms"].items():
                now_counts[(m, a)] = v["n"]
        stale = {k: (prev_counts.get(k), now_counts.get(k)) for k in set(prev_counts) | set(now_counts)
                 if prev_counts.get(k) != now_counts.get(k)}
        out["legacy_mismatch"] = {str(k): v for k, v in list(stale.items())[:12]}
        if stale or prev_sha != digest or prev_src.get("n_rows") != n_rows:
            why.append(f"legacy analysis predates the rows: previous n_rows "
                       f"{prev_src.get('n_rows')} / chains {len(prev_counts)} vs now "
                       f"{n_rows} / {len(now_counts)}")
    if why:
        out["refused"] = bool(not FORCE.get("on"))
        out["why"] = why
        if FORCE.get("on"):
            backup = analysis_path.with_name(
                f"{analysis_path.stem}.stale-{str(prev_sha or 'nodigest')[:8]}"
                f"{analysis_path.suffix}")
            backup.write_text(analysis_path.read_text(encoding="utf-8"), encoding="utf-8")
            out["action"] = f"forced: previous copied to {backup.name}"
            out["backup"] = str(backup)
    return out


def run_analyse(args) -> int:
    force = bool(getattr(args, "force", False))
    FORCE["on"] = force
    try:
        rows = ana.load_rows(ROWS_PATH)
        guard = analysis_guard(ROWS_PATH, ANALYSIS_PATH, rows)
        write_json(LOGS / "analysis-guard.json", guard)
        print(json.dumps({"guard": {k: guard.get(k) for k in
                                    ("refused", "action", "rows_sha256", "n_rows", "why")}},
                         indent=1), flush=True)
        if guard["refused"]:
            print("ANALYSIS REFUSED: rows_sha256/n_rows do not match the previous "
                  "analysis; re-run with --force to keep a backup and write separately.",
                  flush=True)
            return 3
        summary = ana.model_summary(rows)
        summary["_contests"] = {
            "grid": ana.contests(rows, "grid"),
            "baseline": ana.contests(rows, "baseline"),
            "battery_cold_pass_cached": _battery_pass(rows, 0),
            "battery_repeat_pass_cached": _battery_pass(rows, 1),
        }
        summary["_usage"] = ana.usage_coverage(rows)
        summary["_blocks"] = ana.blocks_summary(rows)
        summary["_arm_identity"] = ana.arm_identity(rows)
        summary["_source"] = {"rows": str(ROWS_PATH), "rows_sha256": sha256_file(ROWS_PATH),
                              "n_rows": len(rows),
                              # what this analysis was computed from; compared on the next write
                              "submitted_rows_sha256": guard["rows_sha256"],
                              "analysis_guard": guard.get("action"),
                              "previous_analysis": guard.get("previous")}
    finally:
        FORCE["on"] = False
    summary["_baselines"] = {}
    for name, path, model in (("occamy_block_grid", MOE_BASELINE_ROWS, "occamy-1.0"),
                              ("dense_block_grid", DENSE_BASELINE_ROWS, "qwen3.5-9b")):
        brows = [{**r, "model": model} for r in ana.load_rows(path)]
        summary["_baselines"][name] = {"path": str(path), "sha256": sha256_file(path),
                                       "analysis": ana.model_summary(brows)}
    write_json(ANALYSIS_PATH, summary)
    summary["_baselines"] = {}
    for name, path, model in (("occamy_block_grid", MOE_BASELINE_ROWS, "occamy-1.0"),
                              ("dense_block_grid", DENSE_BASELINE_ROWS, "qwen3.5-9b")):
        brows = [{**r, "model": model} for r in ana.load_rows(path)]
        summary["_baselines"][name] = {"path": str(path), "sha256": sha256_file(path),
                                       "analysis": ana.model_summary(brows)}
    write_json(ANALYSIS_PATH, summary)
    print(json.dumps({k: {"grids": v.get("grids"), "grid_16_reached": v.get("grid_16_reached"),
                          "pmu": v.get("prefix_match_unit_reported")}
                      for k, v in summary.items() if not k.startswith("_")}, indent=1))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--phase", choices=["pre", "analyse", "health"])
    ap.add_argument("--wait", type=int, default=480)
    ap.add_argument("--force", action="store_true",
                    help="analyse: keep the stale analysis as a backup and write separately")
    args = ap.parse_args()
    if args.phase == "health":
        print(json.dumps({"prod": health(PROD_PORT), "occamy": health(OCCAMY_PORT),
                          "var": health(VAR_PORT)}))
        return 0
    if args.phase == "pre":
        capture_pre()
        return 0
    if args.phase == "analyse":
        return run_analyse(args)
    if args.all:
        return run_all(args)
    ap.error("choose --all or --phase")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
