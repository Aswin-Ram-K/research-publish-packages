"""W3-COLLECT -- shared plumbing (lock, raw-usage writer, record-access check).

Derived from experiments/context-cache/cells/DENSE-SGL/dense_sgl_cell.py, but
two things are deliberately different:

  * ROWS go to THIS cell's directory, never into DENSE-SGL's (that cell's
    rows.jsonl is a frozen artifact of the earlier 894-request run).
  * Every row carries the RAW usage object the server returned, plus the
    source of the cached-token count, so the G0 "usage is live" property is
    re-proven on the battery rows themselves and not just at the gate.
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

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments" / "context-cache"))
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
from resextract.context.meter import normalise_cache  # noqa: E402
from resextract.context.render import canonical_bytes  # noqa: E402

BASE_URL = "http://serving-host"          # dense 9B on SGLang (W3-LAUNCH), NEVER 127.0.0.1
OCCAMY_URL = "http://serving-host"        # production, never touched by this unit
VLLM_URL = "http://serving-host"          # production, never touched by this unit
SERVED_MODEL = "qwen3.5-9b"
CONFIG_ID = "P2"                                # P1 = the frozen DENSE-SGL launch (ctx 65536)
CONFIG_SHA256 = "w3collect-p2-ctx32768-memfrac0.08"
CONTEXT_LENGTH = 32768                          # measured on /v1/models
QUANT = "modelopt_fp4"
STACK = "sglang"

ROWS_PATH = HERE / "rows.jsonl"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
CORPUS_PATH = REPO / "experiments" / "context-cache" / "corpora" / "endtoend.json"
LOGS = HERE / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

TOTAL_REQUEST_CAP = 400          # gate 2 | grid 26 | battery 284 | probe 24 = 336, +64 headroom
MAX_TOKENS = 4
KEEP_LAST = 2
SUMMARY_CHARS = 750
LOCK_TIMEOUT_S = 900.0

# The shared 2x2 schedule: 71 turns at budget 32768 (MATRIX-2x2.md, C63).
BAND = {"depth": "32k", "budget": 32768, "planned_turns": 74, "prompt_limit": 32768}

ARMS = (
    {"arm": "R", "policy": "summarise_in_place", "compaction": CompactionPolicy.SUMMARISE_IN_PLACE, "seed": 3201},
    {"arm": "A", "policy": "append_note", "compaction": CompactionPolicy.APPEND_NOTE, "seed": 3202},
    {"arm": "C", "policy": "none", "compaction": None, "seed": 3203},
    {"arm": "H", "policy": "hybrid", "compaction": CompactionPolicy.SUMMARISE_IN_PLACE, "seed": 3204},
)

GRID_TARGETS = (63, 64, 65, 127, 128, 129, 191, 192, 193, 255, 256, 257, 511, 512, 513)
PROBE_TARGETS = (1100, 1164, 1228, 1292)   # WIN-SGL discrimination targets, reused verbatim


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarise(text: str) -> str:
    body = " ".join(text.split())
    if len(body) <= SUMMARY_CHARS:
        return body
    tail_len = SUMMARY_CHARS - 500 - len(" [...] ")
    return f"{body[:500]} [...] {body[-tail_len:]}"


def load_turns(n: int):
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    scenario = corpus["scenarios"][0]
    turns = (scenario["turns"] * ((n // len(scenario["turns"])) + 1))[:n]
    assert len(turns) == n, (len(turns), n)
    return scenario["preamble"], turns


def compaction_schedule(preamble, turns, budget, prompts):
    """Turn numbers at which compaction fires (unchanged logic from DENSE-SGL)."""
    chain = [StateNode.create(preamble, "invariant")]
    schedule = []
    for turn_no, turn in enumerate(turns, 1):
        chain = [*chain, StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)]
        if needs_compaction(chain, budget_tokens=budget, est_tokens=default_est_tokens):
            schedule.append(turn_no)
    return schedule


def digest_prefix(messages, keep=2):
    return hashlib.sha256(canonical_bytes(messages[:keep])).hexdigest()


def acquire_lock(path: Path, timeout_s: float, note: str):
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
                raise TimeoutError(f"lock {path} busy")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": "W3-COLLECT", "pid": os.getpid(), "note": note,
               "acquired_utc": utc_now()}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle, time.monotonic() - started


def release_lock(handle, note: str) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": "W3-COLLECT", "pid": os.getpid(), "note": note,
                   "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def write_json_atomic(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_chat_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    spec = importlib.util.spec_from_file_location("ctx_client_w3collect", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_HTTP = None


def get_http():
    global _HTTP
    if _HTTP is None:
        import httpx
        _HTTP = httpx.Client(base_url=BASE_URL, timeout=120.0,
                             headers={"Authorization": "Bearer EMPTY"})
    return _HTTP


def count_tokens(messages) -> int | None:
    try:
        r = get_http().post("/tokenize", json={"model": SERVED_MODEL, "messages": messages})
        if r.status_code != 200:
            return None
        return int(r.json()["count"])
    except Exception:
        return None


_PORT_CHECKED = False


def assert_port() -> None:
    """Refuse to run against anything but :8017 (the persisted tag rule)."""
    global _PORT_CHECKED
    if _PORT_CHECKED:
        return
    if not BASE_URL.endswith(":8017"):
        raise RuntimeError(f"BASE_URL must be :8017, got {BASE_URL}")
    if "127.0.0.1" in BASE_URL:
        raise RuntimeError("127.0.0.1 is never a valid endpoint for this unit")
    _PORT_CHECKED = True


def make_grid_messages(target_L: int, salt: str, index: bool = False) -> list:
    """A 2-message prompt whose served length is exactly target_L tokens."""
    sys_txt = (f"[grid {salt}] Prefix-cache boundary probe. Target prompt length {target_L} "
               f"tokens. Reply with the single word ok.")
    filler_words = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
                    "tempor incididunt ut labore et dolore magna aliqua").split()

    def build(n_words: int):
        body = " ".join(filler_words[i % len(filler_words)] for i in range(n_words))
        content = f"{salt}\n{body}" if index else body
        return [{"role": "system", "content": sys_txt},
                {"role": "user", "content": content}]

    words = max(1, int((target_L - 30) * 1.3))
    msgs = build(words)
    for _ in range(16):
        count = count_tokens(msgs)
        if count is None:
            return msgs
        delta = target_L - count
        if delta == 0:
            return msgs
        if abs(delta) > 3:
            words = max(1, words + int(delta * 1.05))
            msgs = build(words)
            continue
        body = msgs[1]["content"]
        for _ in range(64):
            count = count_tokens(msgs)
            if count is None or count == target_L:
                break
            body = body[:-1] if (count > target_L and len(body) > 1) else body + " x"
            msgs = [msgs[0], {"role": "user", "content": body}]
    return msgs


class RawChatClient:
    """ChatClient.chat() plus the raw usage object (the G0 evidence)."""

    CHAT_PATH = "/chat/completions"        # httpx joins base_url (…/v1) with this

    def __init__(self):
        self.client = load_chat_client().ChatClient(
            base_url=BASE_URL + "/v1", model=SERVED_MODEL)
        self.last_usage = None

    def chat(self, messages, *, max_tokens=MAX_TOKENS, thinking=False, stream=True, timeout=240.0):
        payload = self.client.payload(messages, max_tokens=max_tokens, thinking=thinking,
                                      stream=stream)
        started = time.perf_counter()
        self.last_usage = None
        with self.client._http(timeout) as http:
            if stream:
                return self._stream(http, payload, started)
            return self._once(http, payload, started)

    def _stream(self, http, payload, started):
        ttft_ms = None
        text_parts = []
        usage = None
        with http.stream("POST", self.CHAT_PATH, json=payload) as resp:
            status = resp.status_code
            for line in resp.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                chunk = line[5:].strip()
                if chunk == "[DONE]":
                    break
                try:
                    event = json.loads(chunk)
                except json.JSONDecodeError:
                    continue
                if isinstance(event.get("usage"), dict):
                    usage = dict(event["usage"])
                for choice in event.get("choices") or []:
                    piece = (choice.get("delta") or {}).get("content")
                    if piece:
                        if ttft_ms is None:
                            ttft_ms = (time.perf_counter() - started) * 1000.0
                        text_parts.append(piece)
        wall_ms = (time.perf_counter() - started) * 1000.0
        self.last_usage = usage
        return self._row_from(usage, text_parts, ttft_ms, wall_ms, status)

    def _once(self, http, payload, started):
        resp = http.post(self.CHAT_PATH, json=payload)
        wall_ms = (time.perf_counter() - started) * 1000.0
        data = resp.json()
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else None
        self.last_usage = usage
        text = "".join((c.get("message") or {}).get("content") or ""
                       for c in data.get("choices") or [])
        return self._row_from(usage, [text], wall_ms, wall_ms, resp.status_code)

    @staticmethod
    def _row_from(usage, text_parts, ttft_ms, wall_ms, status):
        prompt, cached = normalise_cache(usage)
        completion = int((usage or {}).get("completion_tokens") or 0)
        details = (usage or {}).get("prompt_tokens_details")
        if isinstance(details, dict) and "cached_tokens" in details:
            source = "prompt_tokens_details"
        elif isinstance(usage, dict) and "cached_tokens" in usage:
            source = "usage.cached_tokens"
        else:
            source = "absent"          # normalise_cache returns 0 for a cold request too
        return {"prompt": prompt, "cached": cached, "completion": completion,
                "ttft": ttft_ms or 0.0, "wall": wall_ms, "status": status,
                "text": "".join(text_parts), "usage_raw": usage, "usage_source": source}


class Runner:
    def __init__(self):
        assert_port()
        self.client = RawChatClient()
        self.requests = 0
        self.existing = self._load_existing()

    def _load_existing(self) -> set:
        out = set()
        if not ROWS_PATH.exists():
            return out
        for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            out.add((row.get("phase"), row.get("arm"), row.get("depth"), row.get("turn"),
                     row.get("target_L"), row.get("rep")))
        return out

    def n_rows(self) -> int:
        if not ROWS_PATH.exists():
            return 0
        return sum(1 for line in ROWS_PATH.read_text(encoding="utf-8").splitlines() if line.strip())

    def append(self, row: dict) -> None:
        with ROWS_PATH.open("a", encoding="utf-8") as h:
            h.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            h.flush()
            os.fsync(h.fileno())

    def send(self, phase: str, messages, *, salt: str, depth=None, budget=None,
             target_L=None, arm=None, turn=None, policy=None, rep=0, note="",
             allow_failed_retry=False) -> dict:
        key = (phase, arm, depth, turn, target_L, rep)
        if allow_failed_retry:
            # Bootstrap repair: a row that recorded a hard failure (no usage, no
            # vector) is not a measurement.  Only such rows may be re-sent.
            prior = [json.loads(l) for l in ROWS_PATH.read_text().splitlines()
                     if l.strip()] if ROWS_PATH.exists() else []
            bad = [r for r in prior
                   if (r.get("phase"), r.get("arm"), r.get("depth"), r.get("turn"),
                       r.get("target_L"), r.get("rep")) == key]
            if bad and all(r.get("usage_raw") is None for r in bad):
                key = None   # fall through and send
            elif bad:
                raise RuntimeError(f"row exists WITH usage, refusing: {key}")
        if key in self.existing:
            raise RuntimeError(f"duplicate row refused: {key}")
        if self.n_rows() >= TOTAL_REQUEST_CAP:
            raise RuntimeError(f"request cap reached: {self.n_rows()}/{TOTAL_REQUEST_CAP}")
        res = self.client.chat(messages)
        if res["status"] != 200 and res["usage_raw"] is not None:
            pass
        self.requests += 1
        prompt, cached = res["prompt"], res["cached"]
        row = {
            "unit": "W3-COLLECT",
            "cell": f"W3-COLLECT/{CONFIG_ID}/{phase}",
            "phase": phase,
            "depth": depth,
            "budget_tokens": budget,
            "arm": arm,
            "policy": policy,
            "turn": turn,
            "salt": salt,
            "target_L": target_L,
            "rep": rep,
            "prompt_tokens": prompt,
            "cached_tokens": cached,
            "uncached": max(0, prompt - cached),
            "usage_raw": res["usage_raw"],
            "usage_source": res["usage_source"],
            "completion_tokens": res["completion"],
            "ttft_ms": round(res["ttft"], 3),
            "wall_ms": round(res["wall"], 3),
            "status": res["status"],
            "response_chars": len(res["text"] or ""),
            "prefix_sha256": digest_prefix(messages, keep=2),
            "messages": len(messages),
            "chars": sum(len(str(m.get("content") or "")) for m in messages),
            "request_index": self.n_rows() + 1,
            "ts_utc": utc_now(),
            "note": note,
            "stack": STACK,
            "config_id": CONFIG_ID,
            "config_sha256": CONFIG_SHA256,
            "quant": QUANT,
            "served_model": SERVED_MODEL,
            "context_length": CONTEXT_LENGTH,
            "endpoint": BASE_URL,
        }
        self.append(row)
        if key is not None:
            self.existing.add(key)
        print(f"ROW {phase} arm={arm} turn={turn} L={prompt} cached={cached} "
              f"uncached={row['uncached']} rep={rep} status={res['status']} "
              f"src={res['usage_source']} wall={row['wall_ms']}ms total={self.n_rows()}",
              flush=True)
        if res["status"] != 200:
            row["error"] = (res["text"] or "")[:400]
        return row
