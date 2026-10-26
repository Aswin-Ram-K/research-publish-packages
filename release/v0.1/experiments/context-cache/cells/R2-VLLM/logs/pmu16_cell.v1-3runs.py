#!/usr/bin/env python3
"""R2-VLLM -- run ``--prefix-match-unit 16`` on both vLLM models, then restore.

The two arms this cell exists for, each a one-flag delta on ITS OWN production
record, measured on this box's real deployment (no BF16/NVFP4 swap, because the
counterfactual is "the block-grid baseline, plus one hash flag"):

  OH1  occamy-1.0 on vLLM 0.27.1, port 8020, GPU fraction 0.32 -- prod flags of
       ``docker inspect gx10-occamy-nvfp4`` + ``--prefix-match-unit 16``
  A1   gx10-qwen9b unchanged (BF16, fp8 KV, MTP, --block-size resolved 1056),
       port 8014 -- its own running ``Config.Cmd`` + ``--prefix-match-unit 16``,
       with ``--enable-prompt-tokens-details`` added so usage is measurable

Baselines are the on-disk block-grid cells, re-measured here over a short
window (``baseline`` phase) so the comparison is same-window rather than
cross-session:

  occamy  experiments/context-cache/cells/MOE-VLLM/rows.jsonl   (grid 2096)
  dense   experiments/context-cache/cells/WIN-VLLM/rows.jsonl    (grid 1056)

Hard rules (from the operator tag):
  * gx10-occamy-nvfp4 is NEVER stopped, restarted or removed.  The unit is only
    read (``docker inspect``) and copied (the vllm-cache mount is rsync'd into
    a private cache so the variant does not write into the live container's
    cache).  Its health is re-checked after every step.
  * gx10-qwen9b is stopped only after the occamy phase has finished AND been
    restored, and is proved back the way it was found: same Cmd, same Binds,
    same Image, /health 200, /v1/models qwen3.5-9b, max_model_len 32768, and the
    same ``vllm:cache_config_info`` block_size the pre-capture recorded.

Phases (run in this order by ``--all``):
  pre       read-only capture: inspects, health, metrics, headings
  occamy    launch OH1 -> gate -> grid -> baseline -> battery -> teardown
  leniency  one throwaway launch of OH1 with --prefix-match-unit 8, read the
            startup message, tear down   (0 model requests)
  dense     stop prod -> launch A1 -> gate -> grid -> baseline -> battery ->
            teardown -> prove prod restored
  analyse   0 requests: write analysis.json from rows.jsonl

Every model request is one row in ``rows.jsonl`` and is counted against
``--request-cap`` (default 420).  One request in flight.

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
LOCK_PATH = HERE / ".." / ".." / ".occamy.lock"          # experiments/context-cache/.occamy.lock
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
MOE_BASELINE_ROWS = REPO / "experiments" / "context-cache" / "cells" / "MOE-VLLM" / "rows.jsonl"
DENSE_BASELINE_ROWS = REPO / "experiments" / "context-cache" / "cells" / "WIN-VLLM" / "rows.jsonl"

BOX = "zer0null@serving-host"
SSH = ["ssh", "-F", "/dev/null", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
       "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=8", "-o", "LogLevel=ERROR", BOX]

IMAGE = "sha256:2c211a1273b48e8929f893b267aeb1509e6b84654cdbde1bad56d79e3964224d"
PROD_NAME = "gx10-qwen9b"
OCCAMY_NAME = "gx10-occamy-nvfp4"
OCCAMY_PORT = 8012
PROD_PORT = 8014
VAR_PORT = 8020
ENV = ["VLLM_CACHE_ROOT=/root/.cache/vllm", "HF_HUB_OFFLINE=1", "TRANSFORMERS_OFFLINE=1",
       "VLLM_ENABLE_CUDA_COMPATIBILITY=0"]

# the occamy V3 recipe, measured by WIN-VLLM/MOE-VLLM (no --speculative-config:
# the MTP config dies with "No Qwen3Next layer found in the model.layers"), plus the flag under test
OCCAMY_FLAGS = [
    "--served-model-name", "occamy-1.0",
    "--host", "0.0.0.0",
    "--port", "30000",
    "--tensor-parallel-size", "1",
    "--dtype", "bfloat16",
    "--kv-cache-dtype", "fp8",
    "--max-model-len", "32768",
    "--gpu-memory-utilization", "0.32",
    "--max-num-seqs", "6",
    "--max-num-batched-tokens", "8192",
    "--enable-chunked-prefill",
    "--enable-prefix-caching",
    "--reasoning-parser", "qwen3",
    "--trust-remote-code",
]
OCCAMY_MODEL_ARG = ("/hf-cache/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/"
                    "fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652")
OCCAMY_BINDS = ["<workspace>/.cache/huggingface:/hf-cache:ro",
                f"{HERE}/logs/cache-occamy:/root/.cache/vllm"]
OCCAMY_CACHE_SRC = "<workspace>/.local/share/gx10-qwen9b/vllm-cache"   # no occamy cache exists; compiled kernels only
OCCAMY_VLLM_LOG = "/hf-cache/occamy-1.0-NVFP4.vllm.log"                  # container-side, read-only

DENSE_EXTRA = ["--enable-prompt-tokens-details"]   # instrumentation only; does not touch matching

GRID_TARGETS = [100, 200, 500, 1000, 2100, 4193, 8387]
BASELINE_LENS = [3000, 9000, 17000]
BATTERY_TURNS = 16
TOTAL_REQUEST_CAP = 420
MAX_TOKENS = 4
KEEP_LAST = 2
SUMMARY_CHARS = 750
LOCK_TIMEOUT_S = 900.0

CONFIGS = {
    "OH1": {"config_id": "OH1", "model": "occamy-1.0", "label": "occamy nvfp4-moe pmu16",
            "spec": {"model_arg": OCCAMY_MODEL_ARG, "quantization": "modelopt_fp4",
                     "pmu": 16, "served_model": "occamy-1.0", "max_model_len": 32768,
                     "host_port": VAR_PORT, "container": "r2v-oh1", "binds": OCCAMY_BINDS,
                     "gpu_mem": "0.32", "extra": []}},
    "OH1L": {"config_id": "OH1L", "model": "occamy-1.0", "label": "occamy pmu8 leniency probe",
             "spec": {"model_arg": OCCAMY_MODEL_ARG, "quantization": "modelopt_fp4",
                      "pmu": 8, "served_model": "occamy-1.0", "max_model_len": 32768,
                      "host_port": VAR_PORT, "container": "r2v-oh1l", "binds": OCCAMY_BINDS,
                      "gpu_mem": "0.32", "extra": []}},
    "A1": {"config_id": "A1", "model": "qwen3.5-9b", "label": "qwen9b prod cmd + pmu16",
           "spec": {"prod_cmd": True, "pmu": 16, "served_model": "qwen3.5-9b",
                    "max_model_len": 32768, "host_port": PROD_PORT, "container": "r2v-a1",
                    "binds": None, "extra": DENSE_EXTRA}},
}

ARMS = [
    {"arm": "A", "seed": 3201, "compaction": CompactionPolicy.APPEND_NOTE},
    {"arm": "C", "seed": 3202, "compaction": CompactionPolicy.SUMMARISE_IN_PLACE},
    {"arm": "R", "seed": 3203, "compaction": CompactionPolicy.FORK},
    {"arm": "H", "seed": 3204, "compaction": CompactionPolicy.APPEND_NOTE},
]


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
                      f"http://serving-host:{port}{path} && cat /tmp/r2v.out",
                      timeout=timeout + 5)
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
    import re
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


def build_spec(config_id: str, occamy_inspect: dict, prod_inspect: dict) -> dict:
    """Resolve the launch spec. Dense = the RUNNING container's own Cmd + one flag."""
    base = json.loads(json.dumps(CONFIGS[config_id]))
    s = base["spec"]
    if s.get("prod_cmd"):
        cmd = list(prod_inspect["Config"]["Cmd"])
        binds = list(prod_inspect["HostConfig"]["Binds"])
        image = prod_inspect["Image"]
        if "--quantization" in cmd:            # keep prod's own quantization verbatim
            pass
    else:
        cmd = ["--model", s["model_arg"], *OCCAMY_FLAGS, "--quantization", s["quantization"]]
        binds = list(s["binds"])
        image = IMAGE
    cmd = _replace_value(cmd, "--served-model-name", s["served_model"])
    cmd = _replace_value(cmd, "--max-model-len", str(s["max_model_len"]))
    if s.get("gpu_mem"):
        cmd = _replace_value(cmd, "--gpu-memory-utilization", s["gpu_mem"])
    cmd = [a for a in cmd if a != "--prefix-match-unit"]
    if "--prefix-match-unit" in cmd:  # noqa: SIM108  (kept explicit for the red-green test)
        raise AssertionError("prefix-match-unit survived the scrub")
    cmd += ["--prefix-match-unit", str(s["pmu"])]
    for extra in s["extra"]:
        if extra not in cmd:
            cmd.append(extra)
    s["cmd"] = cmd
    s["binds"] = binds
    s["image"] = image
    s["env"] = ENV
    s["base_image"] = prod_inspect["Image"] if not s.get("model_arg") else IMAGE
    s["config_sha256"] = hashlib.sha256(json.dumps(
        {k: s.get(k) for k in ("config_id", "cmd", "binds", "env", "served_model",
                               "max_model_len", "host_port", "image")},
        sort_keys=True).encode()).hexdigest()
    base["spec"] = s
    return base


def _replace_value(cmd: list, flag: str, value: str) -> list:
    out = list(cmd)
    if flag in out:
        out[out.index(flag) + 1] = value
    return out


# ------------------------------------------------------------------------ client


class Client:
    """Serial OpenAI-compatible caller; returns the 7-tuple the cells all use."""

    def __init__(self, port: int):
        self.base = f"http://serving-host:{port}/v1"
        self.http = httpx.Client(timeout=httpx.Timeout(240.0, connect=10.0))

    def chat(self, messages, max_tokens=MAX_TOKENS, timeout=240.0):
        payload = {"model": self.model, "messages": messages, "max_tokens": max_tokens,
                   "temperature": 0, "stream": True,
                   "stream_options": {"include_usage": True}}
        t0 = time.perf_counter()
        ttft = None
        cached = 0
        prompt = 0
        completion = 0
        text = ""
        try:
            with self.http.stream("POST", f"{self.base}/chat/completions",
                                  json=payload, timeout=timeout) as resp:
                status = resp.status_code
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except Exception:
                        continue
                    usage = obj.get("usage") or {}
                    if usage:
                        prompt = int(usage.get("prompt_tokens") or 0)
                        completion = int(usage.get("completion_tokens") or 0)
                        details = usage.get("prompt_tokens_details") or {}
                        cached = int((details or {}).get("cached_tokens") or 0)
                    for ch in obj.get("choices") or []:
                        delta = (ch.get("delta") or {}).get("content")
                        if delta:
                            if ttft is None:
                                ttft = (time.perf_counter() - t0) * 1000.0
                            text += delta
        except Exception as exc:  # connection refused, timeout, 5xx mid-stream
            return 0, 0, 0, 0.0, (time.perf_counter() - t0) * 1000.0, 0, f"EXC {exc!r}"
        wall = (time.perf_counter() - t0) * 1000.0
        if cached > prompt:
            cached = prompt
        return prompt, cached, completion, round(ttft or 0.0, 2), round(wall, 2), status, text[:400]

    def tokenize(self, messages, model: str) -> int | None:
        """Exact served prompt length for ``messages``.

        vLLM 0.27.1 has NO ``/tokenize`` route (measured: SGLang :8012 answers 200,
        vLLM :8014 answers 404), so the primary path is a non-streaming
        ``/chat/completions`` with ``max_tokens=1`` whose ``usage.prompt_tokens`` is
        the server's own count.  That costs ONE request per call, is counted
        against the cap, and is recorded as a row with ``phase="tokens"`` so the
        count is auditable rather than invisible.  ``/tokenize`` is still tried
        first for servers that have it (poolside's SGLang).
        """
        try:
            r = self.http.post(f"{self.base}/tokenize",
                               json={"model": model, "messages": messages}, timeout=30.0)
            if r.status_code == 200:
                return int(r.json().get("count"))
        except Exception:
            pass
        return None


# ------------------------------------------------------------------------- cells


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
            return sum(1 for _ in fh)

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
                if r.get("phase") == "battery" and r.get("arm") == arm and (
                        rep is None or r.get("rep") == rep):
                    out.append(r)
        out.sort(key=lambda r: r.get("turn") or 0)
        return out

    def send(self, phase, messages, *, salt, target_L=None, arm=None, turn=None, rep=0,
             note="") -> dict:
        if self.n_rows() >= TOTAL_REQUEST_CAP:
            raise RuntimeError(f"request cap reached: {self.n_rows()}/{TOTAL_REQUEST_CAP}")
        t0 = time.perf_counter()
        prompt, cached, completion, ttft, wall, status, text = self.client.chat(messages)
        self.requests += 1
        spec = self.spec
        row = {
            "unit": "R2-VLLM",
            "model": CONFIGS_ACTIVE["model"],
            "cell": f"R2-VLLM/{spec['config_id']}/{phase}",
            "config_id": spec["config_id"],
            "config_sha256": spec["config_sha256"],
            "prefix_match_unit": spec["pmu"],
            "resolved_block_size": self.resolved_block,
            "served_model": spec["served_model"],
            "max_model_len": spec["max_model_len"],
            "phase": phase,
            "arm": arm,
            "turn": turn,
            "salt": salt,
            "target_L": target_L,
            "rep": rep,
            "prompt_tokens": prompt,
            "cached_tokens": cached,
            "completion_tokens": completion,
            "uncached": max(0, prompt - cached),
            "ttft_ms": ttft,
            "wall_ms": wall,
            "status": status,
            "request_index": self.n_rows() + 1,
            "note": note,
            "ts_utc": utc_now(),
        }
        if status != 200:
            row["error"] = text
        self.append(row)
        print(f"ROW {phase} cfg={spec['config_id']} arm={arm} turn={turn} L={prompt} "
              f"cached={cached} uncached={row['uncached']} rep={rep} status={status} "
              f"wall={wall}ms total={self.n_rows()}", flush=True)
        return row


CONFIGS_ACTIVE: dict = {}


def _block_from(log_tail: str | None) -> int | None:
    import re
    m = re.search(r"Setting attention block size to\s+(\d+)", log_tail or "")
    return int(m.group(1)) if m else None


def _resolved_block_from_logs(spec: dict) -> int | None:
    """The block size THIS launch resolved to, from its own startup log (never assumed)."""
    path = LOGS / f"{spec['config_id']}-launch.json"
    if not path.exists():
        return None
    rec = json.loads(path.read_text(encoding="utf-8"))
    return rec.get("resolved_block_size_from_log") or _block_from(rec.get("log_tail"))


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
        if count is None:
            return msgs
        delta = target_L - count
        if abs(delta) <= 3:
            return msgs
        words = max(1, words + (int(delta * 1.05) if abs(delta) > 3 else 0))
    return build(words)


def count_tokens(messages) -> int | None:
    """Served prompt length. One counted request when /tokenize is absent."""
    n = RUNNER.client.tokenize(messages, RUNNER.spec["served_model"])
    if n is not None:
        return n
    row = RUNNER.send("tokens", messages, salt="count", rep=0, note="prompt_tokens probe")
    return int(row["prompt_tokens"]) if row.get("status") == 200 else None


RUNNER: Runner = None  # set in main; make_grid_messages needs the tokenizer


def phase_gate() -> dict:
    """Instrument gate + tokenizer offset, then the launch's own resolved block."""
    msgs = [{"role": "system", "content": "You are a cache-probe assistant. Answer in one word."},
            {"role": "user", "content": " ".join(["retention"] * 3100)}]
    tok = RUNNER.client.tokenize(msgs, RUNNER.spec["served_model"])
    r1 = RUNNER.send("gate", msgs, salt="gate-r2v", rep=0, note="identical-1")
    r2 = RUNNER.send("gate", msgs, salt="gate-r2v", rep=1, note="identical-2")
    return {"tokenize_count": tok, "served_prompt_tokens": r1["prompt_tokens"],
            "offset": (r1["prompt_tokens"] - tok) if tok else None,
            "rep0_cached": r1["cached_tokens"], "rep1_cached": r2["cached_tokens"],
            "gate_pass": r2["cached_tokens"] > 0}


def phase_grid(tag: str = "grid") -> list:
    """Cold + one repeat at each target length: the feasibility probe, not the automaton."""
    out = []
    for i, target in enumerate(GRID_TARGETS, 1):
        salt = f"r2v-{RUNNER.spec['config_id']}-{tag}-{target}"
        msgs = make_grid_messages(target, salt)
        cold = RUNNER.send(tag, msgs, salt=salt, target_L=target, rep=0, note=f"target={target}")
        rep = RUNNER.send(tag, msgs, salt=salt, target_L=target, rep=1, note=f"target={target}")
        out.append({"target": target, "L": cold["prompt_tokens"],
                    "cold_cached": cold["cached_tokens"], "rep_cached": rep["cached_tokens"],
                    "verdict": "BLOCKED" if rep["cached_tokens"] != cold["prompt_tokens"]
                    else "FULL"})
    return out


def phase_baseline() -> list:
    """Same-window replication of the on-disk block-grid baseline (3 long prompts, 2 reps)."""
    out = []
    for target in BASELINE_LENS:
        salt = f"r2v-{RUNNER.spec['config_id']}-base-{target}"
        msgs = make_grid_messages(target, salt)
        cold = RUNNER.send("baseline", msgs, salt=salt, target_L=target, rep=0, note=f"target={target}")
        rep = RUNNER.send("baseline", msgs, salt=salt, target_L=target, rep=1, note=f"target={target}")
        out.append({"target": target, "L": cold["prompt_tokens"],
                    "cold_cached": cold["cached_tokens"], "rep_cached": rep["cached_tokens"],
                    "tail": rep["prompt_tokens"] - rep["cached_tokens"]})
    return out


def load_turns(n: int):
    """The first ``n`` turns of scenario 0 and its preamble -- byte-identical to MOE-VLLM's
    loader, so the 16-turn window here is a true prefix window of the two block-grid cells."""
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    turns = (scenario["turns"] * ((n // len(scenario["turns"])) + 1))[:n]
    assert len(turns) == n, (len(turns), n)
    return scenario["preamble"], turns


def summarise(text: str) -> str:
    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


def phase_battery() -> dict:
    """The 16-turn window that carries the measurement.

    vLLM 0.27.1 has no ``/tokenize`` (measured: SGLang answers, vLLM 404s), so an
    exact prompt length is only available *from a response*.  Sizing a prompt by
    sending it first would insert a cache entry at the length being measured, so
    the window is built the other way round:

    pass 1 (cold)   each arm walks turns 1..16 once, in order, each turn a true
                    first sight of its own prefix.  ``L`` comes from the response.
    pass 2 (repeat) each arm walks turns 1..16 again, in order.  Every prefix is
                    now already in the cache, which is exactly the condition the
                    hit grid is read under -- and, because pass 1 was clean, pass 2
                    is the SECOND occurrence of every prefix, so ``cached << L`` is
                    interpretable rather than saturated by an unknown third hit.

    The grid is therefore read from pass 2 (``rep=1``).  Pass 1's ``cached`` is
    recorded too: it is the contamination control.
    """
    preamble, turns = load_turns(BATTERY_TURNS)
    per_arm = {}
    for spec in ARMS:
        arm = str(spec["arm"])
        salt = make_salt(int(spec["seed"]))
        chain = [StateNode.create(preamble, "invariant")]
        msgs_by_turn = []
        for n, turn in enumerate(turns, 1):
            chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=n)]
            msgs_by_turn.append(render(RenderPolicy.NAIVE_APPEND, chain, preamble=preamble,
                                       volatile={}, salt=salt))
        per_arm[arm] = {"salt": salt, "messages": msgs_by_turn}

    passes = []
    for rep in (0, 1):
        for spec in ARMS:
            arm = str(spec["arm"])
            data = per_arm[arm]
            for n, messages in enumerate(data["messages"], 1):
                row = RUNNER.send("battery", messages, salt=data["salt"], arm=arm, turn=n,
                                  rep=rep, note=f"pass={rep + 1} turns_total={len(turns)}")
                if row["status"] != 200:
                    break
        passes.append(rep)

    lens = {}
    for arm, data in per_arm.items():
        lens[arm] = [int(r["prompt_tokens"]) for r in RUNNER.battery_rows(arm, rep=0)]
    return {"turns": len(turns), "passes": passes, "lens": lens}


# ------------------------------------------------------------------------ launch


def launch(cfg: dict, timeout_s: int = 480) -> dict:
    spec = cfg["spec"]
    record = {"unit": "R2-VLLM", "phase": "launch", "config_id": cfg["config_id"],
              "started_utc": utc_now(), "spec": spec, "steps": []}

    def step(name, rc, out, err):
        record["steps"].append({"step": name, "rc": rc, "stdout": (out or "")[-3000:],
                                "stderr": (err or "")[-2000:]})

    if cfg["config_id"] in ("OH1", "OH1L"):
        # the variant's private compiled-kernel cache, copied from the live mount (read-only)
        rc, out, err = sh(f"mkdir -p {shlex.quote(str(HERE / 'logs' / 'cache-occamy'))} && "
                          f"rsync -a --delete {OCCAMY_CACHE_SRC}/ {shlex.quote(str(HERE / 'logs' / 'cache-occamy'))}/",
                          timeout=600)
        step("seed-compile-cache", rc, out, err)
    else:
        rc, out, err = docker(f"stop {PROD_NAME}", timeout=180)
        step("stop-production", rc, out, err)

    rc, out, err = docker(f"rm -f {spec['container']}", timeout=120)
    step("rm-stale-variant", rc, out, err)
    args = ["run", "-d", "--name", spec["container"], "--restart", "no",
            "--gpus", "all", "--ipc", "host", "--shm-size", "16g", "--ulimit", "memlock=-1",
            "-p", f"{spec['host_port']}:30000"]
    for b in spec["binds"]:
        args += ["-v", b]
    for e in spec["env"]:
        args += ["-e", e]
    args.append(spec["image"])
    args += spec["cmd"]
    rc, out, err = docker(" ".join(shlex.quote(a) for a in args), timeout=300)
    step("docker-run", rc, out, err)
    dead_early = False
    if rc != 0:
        record.update({"launched": False, "reason": "docker run failed", "stderr": (err or "")[-4000:]})
        write_json(LOGS / f"{cfg['config_id']}-launch.json", record)
        print(f"launch {cfg['config_id']}: docker run FAILED", flush=True)
        return record

    started = time.monotonic()
    status = 0
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
    _, logs, _ = docker(f"logs --tail 400 {spec['container']}", timeout=90)
    record["log_tail"] = (logs or "")[-20000:]
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
    """Remove the variant.  NEVER touches gx10-occamy-nvfp4."""
    spec = cfg["spec"]
    rec = {"unit": "R2-VLLM", "phase": "teardown", "config_id": cfg["config_id"],
           "started_utc": utc_now()}
    rc, out, err = docker(f"rm -f {spec['container']}", timeout=180)
    rec["rm_variant"] = {"rc": rc, "stdout": (out or "")[-400:], "stderr": (err or "")[-400:]}
    rec["occamy"] = occamy_health()
    rec["free_port"] = health(spec["host_port"])
    write_json(LOGS / f"{cfg['config_id']}-teardown.json", rec)
    print(f"teardown {cfg['config_id']}: rm rc={rc} occamy={rec['occamy']['status']} "
          f"port={rec['free_port']}", flush=True)
    return rec


def restore_prod(pre: dict, timeout_s: int = 300) -> dict:
    """Start gx10-qwen9b and PROVE it is the same container it was found as."""
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
    rc, out, err = docker(f"inspect {PROD_NAME}", timeout=90)
    try:
        now = json.loads(out)[0]
        before = pre["inspect"]
        rec["cmd_same"] = now["Config"]["Cmd"] == before["Config"]["Cmd"]
        rec["binds_same"] = now["HostConfig"]["Binds"] == before["HostConfig"]["Binds"]
        rec["image_same"] = now["Image"] == before["Image"]
        rec["status_running"] = now["State"]["Status"] == "running"
    except Exception as exc:
        rec["inspect_error"] = repr(exc)
    pre_block = cache_field((pre.get("metrics") or {}).get("cache_config_info"), "block_size")
    now_block = cache_field((rec["metrics"] or {}).get("cache_config_info"), "block_size")
    rec["block_size_pre"], rec["block_size_now"] = pre_block, now_block
    rec["proven"] = bool(status == 200
                        and rec.get("models", {}).get("id") == pre["models"].get("id")
                        and rec.get("models", {}).get("max_model_len") == pre["models"].get("max_model_len")
                        and now_block == pre_block
                        and rec.get("cmd_same") and rec.get("binds_same")
                        and rec.get("image_same") and rec.get("status_running")
                        and rec["occamy"]["status"] == 200)
    rec["finished_utc"] = utc_now()
    write_json(LOGS / "prod-restore.json", rec)
    print(f"restore prod: health={status} id={rec['models'].get('id')} "
          f"block {pre_block}->{now_block} cmd_same={rec.get('cmd_same')} "
          f"binds_same={rec.get('binds_same')} proven={rec['proven']} "
          f"occamy={rec['occamy']['status']}", flush=True)
    return rec


# -------------------------------------------------------------------------- main


def capture_pre() -> dict:
    out = {"unit": "R2-VLLM", "captured_utc": utc_now(), "steps": {}}
    for name in (PROD_NAME, OCCAMY_NAME):
        rc, o, e = docker(f"inspect {name}", timeout=90)
        try:
            out["inspect" + ("_prod" if name == PROD_NAME else "_occamy")] = json.loads(o)[0]
        except Exception:
            out["inspect_error_" + name] = {"rc": rc, "stderr": (e or "")[-800:]}
    out["prod"] = {"health": health(PROD_PORT), "models": capture_models(PROD_PORT),
                   "metrics": capture_metrics(PROD_PORT)}
    out["occamy"] = {"health": health(OCCAMY_PORT), "models": capture_models(OCCAMY_PORT),
                     "metrics": capture_metrics(OCCAMY_PORT)}
    rc, o, e = sh(f"sudo -n docker ps --format '{{{{.Names}}}} {{{{.Status}}}}'", timeout=60)
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
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def run_all(args) -> int:
    global RUNNER, CONFIGS_ACTIVE
    pre = capture_pre()
    summary = {"unit": "R2-VLLM", "phase": "all", "started_utc": utc_now(),
               "pre": {"prod": pre["prod"]["health"], "occamy": pre["occamy"]["health"],
                       "prod_block_size": cache_field(pre["prod"]["metrics"]["cache_config_info"],
                                                      "block_size"),
                       "occamy_block_size": cache_field(pre["occamy"]["metrics"]["cache_config_info"],
                                                        "block_size")},
               "configs": {}, "phases": {}}

    ensure_occamy_up()

    handle, waited = acquire_lock(LOCK_PATH, LOCK_TIMEOUT_S, "R2-VLLM pmu16 both models")
    held_at = time.monotonic()
    summary["lock_wait_s"] = waited
    print(f"lock acquired after {waited}s", flush=True)
    try:
        # ---------------- occamy (production SGLang must stay up throughout) ------
        cfg = build_spec("OH1", pre["inspect_occamy"], pre["inspect_prod"])
        summary["configs"]["OH1"] = cfg["spec"]
        CONFIGS_ACTIVE["model"] = cfg["model"]
        rec = launch(cfg, timeout_s=args.wait)
        if rec["launched"]:
            RUNNER = Runner({**cfg["spec"], "config_id": cfg["config_id"]}, Client(VAR_PORT))
            summary["phases"]["occamy_gate"] = phase_gate()
            summary["phases"]["occamy_grid"] = phase_grid()
            summary["phases"]["occamy_baseline"] = phase_baseline()
            summary["phases"]["occamy_battery"] = phase_battery()
            summary["phases"]["occamy_metrics"] = capture_metrics(VAR_PORT)
        else:
            summary["phases"]["occamy_launch_failed"] = rec.get("reason")
        summary["phases"]["occamy_teardown"] = teardown(cfg)
        maybe_restore_occamy()

        # ---------------- leniency probe (0 requests) -----------------------------
        lcfg = build_spec("OH1L", pre["inspect_occamy"], pre["inspect_prod"])
        summary["configs"]["OH1L"] = lcfg["spec"]
        lrec = launch(lcfg, timeout_s=args.wait)
        summary["phases"]["leniency"] = {"launched": lrec.get("launched"),
                                         "reason": lrec.get("reason"),
                                         "log_tail": (lrec.get("log_tail") or "")[-6000:]}
        teardown(lcfg)
        maybe_restore_occamy()

        # ---------------- dense (prod is stopped here and nothing else) ------------
        dcfg = build_spec("A1", pre["inspect_occamy"], pre["inspect_prod"])
        summary["configs"]["A1"] = dcfg["spec"]
        CONFIGS_ACTIVE["model"] = dcfg["model"]
        drec = launch(dcfg, timeout_s=args.wait)
        if drec["launched"]:
            RUNNER = Runner({**dcfg["spec"], "config_id": dcfg["config_id"]}, Client(PROD_PORT))
            summary["phases"]["dense_gate"] = phase_gate()
            summary["phases"]["dense_grid"] = phase_grid()
            summary["phases"]["dense_baseline"] = phase_baseline()
            summary["phases"]["dense_battery"] = phase_battery()
            summary["phases"]["dense_metrics"] = capture_metrics(PROD_PORT)
        else:
            summary["phases"]["dense_launch_failed"] = drec.get("reason")
        teardown(dcfg)
        summary["phases"]["restore"] = restore_prod(pre)
        summary["requests"] = RUNNER.requests if RUNNER else 0
    finally:
        summary["lock_held_s"] = round(time.monotonic() - held_at, 1)
        release_lock(handle, "R2-VLLM done")
        summary["finished_utc"] = utc_now()
        write_json(LOGS / "run.json", summary)
    return 0 if summary["phases"].get("restore", {}).get("proven") else 1


def ensure_occamy_up() -> dict:
    """gx10-occamy-nvfp4 is never stopped; if it is somehow down, start it (never remove)."""
    status = health(OCCAMY_PORT)
    if status == 200:
        return {"status": 200, "action": "none"}
    rc, out, err = docker(f"start {OCCAMY_NAME}", timeout=180)
    for _ in range(60):
        time.sleep(3)
        if health(OCCAMY_PORT) == 200:
            break
    return {"status": health(OCCAMY_PORT), "action": "start", "rc": rc,
            "stdout": (out or "")[-400:], "stderr": (err or "")[-400:]}


def maybe_restore_occamy() -> None:
    """Recording only: the unit must never have touched it, and this proves it."""
    st = occamy_health()
    print(f"occamy after step: {st['status']}", flush=True)
    if st["status"] != 200:
        write_json(LOGS / "OCCAMY-DOWN.json", st)


def run_analyse(_args) -> int:
    rows = ana.load_rows(ROWS_PATH)
    summary = ana.model_summary(rows)
    summary["_source"] = {"rows": str(ROWS_PATH), "rows_sha256": sha256_file(ROWS_PATH),
                          "n_rows": len(rows)}
    summary["_baselines"] = {
        "occamy_block_grid": {"path": str(MOE_BASELINE_ROWS),
                              "sha256": sha256_file(MOE_BASELINE_ROWS),
                              "analysis": ana.model_summary(
                                  [{**r, "model": "occamy-1.0"} for r in ana.load_rows(MOE_BASELINE_ROWS)])},
        "dense_block_grid": {"path": str(DENSE_BASELINE_ROWS),
                             "sha256": sha256_file(DENSE_BASELINE_ROWS),
                             "analysis": ana.model_summary(
                                 [{**r, "model": "qwen3.5-9b"} for r in ana.load_rows(DENSE_BASELINE_ROWS)])},
    }
    write_json(ANALYSIS_PATH, summary)
    print(json.dumps(summary, indent=1)[:4000])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--phase", choices=["pre", "occamy", "leniency", "dense", "analyse", "health"])
    ap.add_argument("--config", choices=sorted(CONFIGS))
    ap.add_argument("--wait", type=int, default=480)
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()
    if args.phase == "health":
        print(json.dumps({"prod": health(PROD_PORT), "occamy": health(OCCAMY_PORT),
                          "var": health(VAR_PORT)}, indent=1))
        return 0
    if args.phase == "pre":
        capture_pre()
        return 0
    if args.phase == "analyse":
        return run_analyse(args)
    if args.all:
        return run_all(args)
    if args.restore:
        pre = json.loads((LOGS / "pre.json").read_text())
        return 0 if restore_prod(pre)["proven"] else 1
    ap.error("choose --all, --phase, or --restore")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
