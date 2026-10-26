#!/usr/bin/env python3
"""run_longrun.py — turn driver for the long-run arms (LONGRUN-PREREG §1-§6).

One invocation runs one (task x arm x rep) cell (or a list of arms) against an
OpenAI-compatible endpoint and appends ONE NDJSON row per request-turn to
``experiments/ptr-engine/measure/rows-longrun-<date>.jsonl``.  It never scores:
checkpoint answers are recorded raw and the scorer judges them.

Arms (exactly as LONGRUN-PREREG §1):
  transcript-grow     replay the whole history every turn; FIFO-truncate from the
                      front once the declared 64,000-token cap is crossed.
  transcript-compact  same replay, but at the cap the older turns are replaced by a
                      ~700-token digest (one extra digest request per wall); the recent
                      4 turns stay raw.
  pointer-stable      byte-identical frozen index prefix, bodies appended after it in
                      the suffix (one new body per turn, prefetched one turn ahead),
                      tail = short state line + current question.  Nothing before the
                      tail is ever rewritten.
  lease-reopen        close at the wall and reopen a fresh session carrying only the
                      frozen pointer index + a host-distilled state line (<=400 tok).
                      Reopens are host-side; only the turn itself is a request.

Fixture schema ``consonance.longrun-fixture/1`` (the real fixture is card 2a6c4761's
deliverable; the stub tree carries only ``{"stub": true}`` and is refused):
  {schema, task_id, N, window_tokens, wall_tokens, bytes_per_token, system_prompt,
   items:[{id, body, fact?}], turns:[{turn, question, note?{id,body}, checkpoint?}],
   lease_reopen_turns?:[23,56]}

Null semantics: ``normalize_cached_tokens`` below is the ONE place that decides what a
missing ``cached_tokens`` means, per RECORD.md "Endpoint null semantics settled"
(SGLang omits the key when it is 0 => 0; vLLM null is preserved as null).

Dry-run is fully offline: it writes the frozen manifest(s), prints the first three
request bodies per arm (byte count + sha256, exact bytes in the preview files), the
request count it would send, and exits 0.  It sends nothing and writes no row file.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from math import ceil

ARMS = ("transcript-grow", "transcript-compact", "pointer-stable", "lease-reopen")
DEFAULT_BASE_URL = "http://192.168.2.168:8012/v1"
DEFAULT_MODEL = "occamy-1.0-NVFP4"
DEFAULT_ENGINE = "sglang"

PREDICTIONS = {
    "transcript-grow": ("P2: A's tokens-to-verified-success >= 1.5x C's; at N=60 it hits the "
                        "window/cap and repairs from a front-truncated prefix."),
    "transcript-compact": ("P4: B lands within 2x of C on p95 TTFT but fails t30 where its "
                           "digest dropped the turn-2 code."),
    "pointer-stable": ("P1: C's p95 TTFT <= 0.5x A's, cached share >= 0.80 after turn 12; "
                       "P2: A's tokens-to-verified-success >= 1.5x C's."),
    "lease-reopen": ("P3: D has the lowest p95 TTFT but loses t30/t60 accuracy unless the "
                     "<=400-token state line carries the turn-2 fact and the turn-24 correction."),
}


# --------------------------------------------------------------------------- util
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def est_tokens(text: str, bytes_per_token: float) -> int:
    return ceil(len(text.encode("utf-8")) / float(bytes_per_token))


# ------------------------------------------------------------------- null semantics
def normalize_cached_tokens(raw_cached, engine: str):
    """THE null-semantics function — the only place a missing ``cached_tokens`` is decided.

    RECORD.md, "Endpoint null semantics settled 2026-10-26": SGLang *returns
    prompt_tokens_details but omits cached_tokens when it is 0*, so a null there is a
    measured zero; on vLLM the detail object is null and no cache counter exists, so a
    null is preserved as null and must never be imputed as 0.

    SGLang: None -> 0.   vLLM: None -> None.   Anything else: refuse to guess.
    """
    if raw_cached is not None:
        return int(raw_cached)
    if engine == "sglang":
        return 0
    if engine == "vllm":
        return None
    raise ValueError(f"no null semantics declared for engine={engine!r} (expected sglang|vllm)")


# ------------------------------------------------------------------------ fixture
class FixtureError(RuntimeError):
    pass


def load_fixture(path: str) -> dict:
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise FixtureError(f"cannot read fixture {path}: {exc}") from exc
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureError(f"fixture {path} is not JSON: {exc}") from exc
    if doc.get("stub") or not doc.get("items"):
        raise FixtureError(
            f"fixture {path} is a STUB (no items/turns). The real fixture tree is card "
            "2a6c4761's deliverable; use a constructed fixture with --fixture."
        )
    for key in ("schema", "task_id", "N", "wall_tokens", "bytes_per_token", "system_prompt",
                "items", "turns"):
        if key not in doc:
            raise FixtureError(f"fixture {path} missing required key {key!r}")
    if doc["schema"] != "consonance.longrun-fixture/1":
        raise FixtureError(f"unsupported fixture schema {doc['schema']!r}")
    if not doc["items"] or not all({"id", "body"} <= set(it) for it in doc["items"]):
        raise FixtureError("fixture items must be non-empty {id, body} objects")
    turns = sorted(doc["turns"], key=lambda t: int(t["turn"]))
    if [int(t["turn"]) for t in turns] != list(range(1, int(doc["N"]) + 1)):
        raise FixtureError("fixture turns must be numbered 1..N contiguously")
    for t in turns:
        if not isinstance(t.get("question"), str) or not t["question"]:
            raise FixtureError(f"fixture turn {t['turn']} has no question")
    doc["turns"] = turns
    doc["_path"] = os.path.abspath(path)
    doc["_sha256"] = sha256_bytes(raw)
    return doc


def index_lines(fixture: dict) -> str:
    """Frozen pointer index: id, hash8, body length — no fact values (no AUD-/lumen leak)."""
    lines = []
    for item in fixture["items"]:
        body = item["body"]
        lines.append(f"- @knowledge:{item['id']}@1 {sha256_text(body)[:8]} {len(body.encode('utf-8'))}")
    return "\n".join(lines) + "\n"


def body_block(item: dict) -> str:
    return f"BODY {item['id']} ({len(item['body'].encode('utf-8'))} B)\n{item['body']}\n"


def working_set_block(fixture: dict) -> str:
    bodies = "\n".join(body_block(it) for it in fixture["items"])
    return f"WORKING SET\nINDEX\n{index_lines(fixture)}\n{bodies}"


def turn_user(t: int, turn: dict) -> str:
    text = ""
    note = turn.get("note")
    if note:
        text += f"[WORK NOTE {note.get('id', 'n' + str(t))}]\n{note['body']}\n"
    return text + f"QUESTION (T{t}): {turn['question']}"


def turn_block(t: int, turn: dict, answer: str) -> str:
    return f"{turn_user(t, turn)}\nANSWER (T{t}): {answer}"


# ------------------------------------------------------------------- tool channel
# OPT-IN, bounded `read_file` fetch channel (FETCH-CHANNEL).
# DEFAULT OFF: with `--tools` absent (or empty) none of the code below executes, no
# key is added to any row or manifest, and every request body is byte-identical to
# the runs recorded before this flag existed.  The channel exists because the
# pointer arms emit `<tool_call>…read_file…` and nothing ever served it
# (RUN-V4-GRID checkpoint 3, arm pointer-stable): the designed resolution path —
# pointer plus on-demand fetch — is what this implements.
TOOL_READ_CAP_LINES = 200
TOOL_READ_CAP_CHARS = 8000
TOOL_CALLS_PER_TURN = 2
TOOL_FETCH_ROUNDS_PER_ARM = 8
TOOL_NAMES = ("read_file",)

_SECRET_BASENAMES = (".env", ".netrc")
_SECRET_PREFIXES = (".env.", "id_rsa", "id_ed25519", "id_dsa", "id_ecdsa")
_SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
_SECRET_STEMS = ("credentials", "secrets", "secret", "keys", "clients")


def tool_names(cfg) -> list[str]:
    return [n.strip() for n in str(getattr(cfg, "tools", "") or "").split(",") if n.strip()]


def tools_enabled(cfg) -> bool:
    return "read_file" in tool_names(cfg)


class BudgetExhausted(RuntimeError):
    """A fetch follow-up would exceed the request budget."""


def _decode_json_objects(text: str) -> list:
    """Every decodable JSON value in `text`, in order. Never raises."""
    dec = json.JSONDecoder()
    out: list = []
    i = 0
    while True:
        j = text.find("{", i)
        if j < 0:
            return out
        try:
            obj, end = dec.raw_decode(text, j)
        except ValueError:
            i = j + 1
            continue
        out.append(obj)
        i = end


def parse_tool_calls(text: str) -> list[dict]:
    """Parse read_file requests out of one model turn. Never raises.

    Accepts the observed shape, where the marker is repeated as a separator:

      <tool_call>2629 <tool_call>read_file <tool_call>{"path": "...", "start_line": 66, "end_line": 71}

    and a single well-formed JSON object following the token `read_file`.  A turn
    that never names `read_file` yields no calls, so prose JSON cannot trigger a read.
    """
    if not text or "read_file" not in text:
        return []
    anchor = text.find("<tool_call>")
    region = text[anchor:] if anchor >= 0 else text[text.find("read_file"):]
    calls: list[dict] = []
    for obj in _decode_json_objects(region):
        if not isinstance(obj, dict):
            continue
        path = obj.get("path")
        if not isinstance(path, str) or not path.strip():
            continue
        try:
            start = int(obj.get("start_line", obj.get("start", 1)))
            end = int(obj.get("end_line", obj.get("end", start)))
        except (TypeError, ValueError):
            continue
        if start > end:
            start, end = end, start
        call = {"path": path.strip(), "start_line": max(1, start), "end_line": max(1, end)}
        if call not in calls:
            calls.append(call)
    return calls


def limit_calls(calls: list[dict], per_turn: int = TOOL_CALLS_PER_TURN):
    """Split one turn's calls into (executed batch, refused overflow). Hard 2-per-turn."""
    return list(calls[:per_turn]), list(calls[per_turn:])


def _is_secret_shaped(name: str) -> bool:
    low = name.lower()
    if low in _SECRET_BASENAMES or low.startswith(_SECRET_PREFIXES):
        return True
    if low.endswith(_SECRET_SUFFIXES):
        return True
    return any(low == stem or low.startswith(stem + ".") for stem in _SECRET_STEMS)


def resolve_read_path(path: str, root: str) -> tuple:
    """Return (absolute_path, None) or (None, refusal_reason). Never opens the file."""
    if not isinstance(path, str) or not path.strip():
        return None, "path_refused"
    raw = path.strip().replace("\\", "/")
    if raw.startswith("/") or raw.startswith("~") or os.path.isabs(raw):
        return None, "path_refused"
    if any(part == ".." for part in raw.split("/")):
        return None, "path_refused"
    if _is_secret_shaped(raw.rsplit("/", 1)[-1]):
        return None, "path_refused"
    root_abs = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root_abs, raw))
    try:
        if os.path.commonpath([root_abs, target]) != root_abs:
            return None, "path_refused"
    except ValueError:
        return None, "path_refused"
    if target == root_abs or not os.path.isfile(target):
        return None, "path_not_found"
    return target, None


def execute_tool_call(call: dict, root: str) -> dict:
    """Perform one bounded read. Returns {record, block, text}.

    `block` is the delimited tool result appended to the conversation; `record` is
    the `tool_calls` entry written to the row.  A refused or unsafe path injects
    `<tool_result error="path_refused"/>` and is never read.
    """
    target, reason = resolve_read_path(call["path"], root)
    rec = {"path": call["path"], "start_line": call["start_line"],
           "end_line": call["end_line"], "executed": False, "truncated": False}
    if target is None:
        rec["error"] = reason
        return {"record": rec, "block": f'<tool_result error="{reason}"/>', "text": ""}
    try:
        with open(target, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        rec["error"] = "read_failed"
        return {"record": rec, "block": '<tool_result error="read_failed"/>', "text": ""}
    total = len(lines)
    if call["start_line"] > total:
        rec["error"] = "range_out_of_bounds"
        return {"record": rec, "block": '<tool_result error="range_out_of_bounds"/>', "text": ""}
    start = max(1, call["start_line"])
    end = min(max(start, call["end_line"]), total)
    truncated = False
    if end - start + 1 > TOOL_READ_CAP_LINES:
        end = start + TOOL_READ_CAP_LINES - 1
        truncated = True
    body = "".join(lines[start - 1:end]).rstrip("\n")
    if len(body) > TOOL_READ_CAP_CHARS:
        body = body[:TOOL_READ_CAP_CHARS]
        truncated = True
    rec.update({"executed": True, "truncated": truncated, "lines_returned": end - start + 1})
    path_attr = call["path"].replace('"', "'")
    attrs = f'for="read_file" path="{path_attr}" lines="{start}-{end}"'
    if truncated:
        attrs += ' truncated="true"'
    return {"record": rec, "block": f"<tool_result {attrs}>\n{body}\n</tool_result>", "text": body}


def fetch_rounds(cfg, fixture, arm, rep, run_id, t, manifest_sha, extras, messages, resp,
                 sent, budget, rounds_used):
    """Run the bounded read_file channel after one model turn.

    Bounds: <= TOOL_CALLS_PER_TURN (2) calls per turn, exactly one follow-up model
    request per fetch round, <= TOOL_FETCH_ROUNDS_PER_ARM (8) rounds per arm.  Each
    follow-up is a REAL request: it is counted in `sent`, recorded as its own row
    with `fetch_followup: true`, and its cost is visible in the run's request count.
    Returns (messages, resp, sent, rounds_used, turn_calls, followup_rows).
    """
    turn_calls: list[dict] = []
    followups: list[dict] = []
    if not tools_enabled(cfg):
        return messages, resp, sent, rounds_used, turn_calls, followups
    root = os.getcwd()
    content = resp.get("content") or ""
    pending = parse_tool_calls(content)
    while pending:
        if rounds_used >= TOOL_FETCH_ROUNDS_PER_ARM:
            # Per-arm cap already spent: refuse the calls, spend no request.
            for call in pending:
                turn_calls.append({"path": call["path"], "start_line": call["start_line"],
                                   "end_line": call["end_line"], "executed": False,
                                   "truncated": False, "error": "fetch_budget_exhausted"})
            pending = []
            break
        batch, overflow = limit_calls(pending)
        round_calls: list[dict] = []
        blocks: list[str] = []
        for call in batch:
            res = execute_tool_call(call, root)
            round_calls.append(res["record"])
            blocks.append(res["block"])
        for call in overflow:
            round_calls.append({"path": call["path"], "start_line": call["start_line"],
                                "end_line": call["end_line"], "executed": False,
                                "truncated": False, "error": "turn_call_cap"})
        turn_calls.extend(round_calls)
        rounds_used += 1
        if rounds_used >= TOOL_FETCH_ROUNDS_PER_ARM:
            blocks.append('<tool_result error="fetch_budget_exhausted"/>')
        next_messages = messages + [
            {"role": "assistant", "content": content},
            {"role": "user", "content": "\n".join(blocks)
             + "\n\nUse the tool result above. Answer the QUESTION now, within the word budget."},
        ]
        if sent >= budget:
            raise BudgetExhausted(f"fetch at T{t} would exceed the request budget of {budget}")
        resp = send_chat(cfg, next_messages)
        sent += 1
        messages = next_messages
        content = resp.get("content") or ""
        followups.append(make_row(
            cfg, fixture, arm, rep, run_id, t, resp, content, "tool-followup", manifest_sha,
            dict(extras, prompt_sha256=sha256_text(next_messages[-1]["content"]),
                 fetch_followup=True, tool_calls=round_calls)))
        pending = parse_tool_calls(content)
    return messages, resp, sent, rounds_used, turn_calls, followups


# ------------------------------------------------------------------------ planner
class Planner:
    """Builds the next prompt for one arm from the answers already recorded."""

    def __init__(self, arm: str, fixture: dict, dry_run: bool):
        self.arm = arm
        self.fixture = fixture
        self.dry_run = dry_run
        self.answers: list[str] = []
        self.bpt = float(fixture["bytes_per_token"])
        self.wall_tokens = int(fixture["wall_tokens"])
        self.wall_bytes = self.wall_tokens * self.bpt
        # B state
        self.digest: str | None = None
        self.raw: list[str] = []
        # D state
        self.walls = list(fixture.get("lease_reopen_turns") or [])
        self.lease_state = ""
        self.lease = 1
        self.lease_start = 1

    # -- helpers ---------------------------------------------------------
    def messages(self, user: str) -> list[dict]:
        return [{"role": "system", "content": self.fixture["system_prompt"]},
                {"role": "user", "content": user}]

    def record(self, t: int, answer: str) -> None:
        while len(self.answers) < t - 1:
            self.answers.append("")
        self.answers.append(answer)
        if self.arm == "transcript-compact":
            self.raw.append(turn_block(t, self.fixture["turns"][t - 1], answer))

    def _b_base(self) -> str:
        if self.digest:
            return f"DIGEST OF EARLIER TRANSCRIPT\n{self.digest}\n\n"
        return working_set_block(self.fixture) + "\n\n"

    def _distill(self, upto_turn: int) -> str:
        """Host-side state line (no request): pointers + the tail of this lease's answers."""
        lines = ["POINTERS: " + ", ".join(it["id"] for it in self.fixture["items"])]
        start = max(self.lease_start, upto_turn - 6)
        for i in range(start, upto_turn):
            text = (self.answers[i - 1] or "").replace("\n", " ")[:200] if i - 1 < len(self.answers) else ""
            if text:
                lines.append(f"T{i}: {text}")
        return "\n".join(lines).encode("utf-8")[:1800].decode("utf-8", "ignore")

    def replay(self, rows: list[dict]) -> None:
        """Rebuild prompt state from a partial cell (resume) — no requests."""
        for row in rows:
            t = int(row.get("turn") or 0)
            content = row.get("content") or ""
            if (self.arm == "lease-reopen" and t in self.walls and self.lease_start <= t):
                self.lease_state = self._distill(t)
                self.lease = 1 + sum(1 for w in self.walls if w <= t)
                self.lease_start = t
            if row.get("kind") == "digest":
                self.digest = content
                self.raw = self.raw[-4:]
            else:
                self.record(t, content)

    # -- build -----------------------------------------------------------
    def build(self, t: int) -> dict:
        turn = self.fixture["turns"][t - 1]
        arm = self.arm
        info: dict = {"t": t, "turn": turn, "digest_request": None, "evicted": 0,
                      "lease": None, "prefix_sha256": None}
        if arm == "transcript-grow":
            parts = [working_set_block(self.fixture)]
            parts += [turn_block(i, self.fixture["turns"][i - 1], self.answers[i - 1])
                      for i in range(1, t) if i - 1 < len(self.answers)]
            current = turn_user(t, turn)
            evicted = 0
            while len(parts) > 1 and est_tokens("\n\n".join(parts + [current]), self.bpt) > self.wall_tokens:
                parts.pop(0)
                evicted += 1
            text = "\n\n".join(parts + [current])
            if est_tokens(text, self.bpt) > self.wall_bytes:
                keep = int(self.wall_bytes)
                cut = text.encode("utf-8")[-keep:]
                text = cut.decode("utf-8", "ignore").split("\n", 1)[-1]
                evicted += 1
            info["evicted"] = evicted
            info["prompt"] = text
            return info

        if arm == "transcript-compact":
            current = turn_user(t, turn)
            base = self._b_base()
            window = base + "\n\n".join(self.raw + [current])
            if t > 1 and est_tokens(window, self.bpt) > self.wall_tokens:
                transcript = base + "\n\n".join(self.raw)
                instruction = (
                    "COMPRESS the transcript below into at most 700 tokens. Preserve every item id, "
                    "every audit/retention code, and every correction.\n\nTRANSCRIPT:\n" + transcript
                )
                info["digest_request"] = self.messages(instruction)
                if self.dry_run:
                    self.digest = "<<digest produced by the digest request at this turn (dry-run placeholder)>>"
                    self.raw = self.raw[-4:]
                    base = self._b_base()
            info["prompt"] = base + "\n\n".join(self.raw + [current])
            return info

        if arm == "pointer-stable":
            upto = min(t + 1, len(self.fixture["items"]))
            bodies = "\n".join(body_block(it) for it in self.fixture["items"][:upto])
            prefix = f"INDEX\n{index_lines(self.fixture)}\n{bodies}"
            info["prefix_sha256"] = sha256_text(prefix)
            tail = ["STATE"]
            for i in range(max(1, t - 3), t):
                ans = self.answers[i - 1] if i - 1 < len(self.answers) else ""
                tail.append(f"T{i}: {ans.replace(chr(10), ' ')[:120]}")
            if len(tail) == 1:
                tail.append("(no prior turns in this lease)")
            note = turn.get("note")
            if note:
                tail.append(f"[WORK NOTE {note.get('id', 'n' + str(t))}]\n{note['body']}")
            tail.append(f"QUESTION (T{t}): {turn['question']}")
            info["prompt"] = prefix + "\n\n" + "\n".join(tail)
            return info

        if arm == "lease-reopen":
            if t in self.walls and self.lease_start <= t:
                self.lease_state = self._distill(t)
                self.lease = 1 + sum(1 for w in self.walls if w <= t)
                self.lease_start = t
            info["lease"] = self.lease
            note = turn.get("note")
            text = f"INDEX\n{index_lines(self.fixture)}\n"
            if self.lease_state:
                closed = min([w for w in self.walls if w <= t], default=0)
                text += f"\nLEASE STATE (closed at T{closed})\n{self.lease_state}\n"
            text += "\n"
            if note:
                text += f"[WORK NOTE {note.get('id', 'n' + str(t))}]\n{note['body']}\n"
            text += f"QUESTION (T{t}): {turn['question']}"
            info["prompt"] = text
            return info

        raise ValueError(f"unknown arm {arm!r}")


def expected_digests(fixture: dict) -> int:
    """Declared digest budget for arm B: two walls (pre-registered turns 23 and 53)."""
    return 2


# ----------------------------------------------------------------------- manifest
def build_manifest(cfg, fixture: dict, arm: str, rep: int, run_id: str, rows_path: str) -> dict:
    return {
        "schema": "consonance.longrun-manifest/1",
        "run_id": run_id,
        "created_utc": iso(utc_now()),
        "dry_run": bool(cfg.dry_run),
        # Thinking switch (consonance.longrun-manifest/1, added RUNNER-THINKING-FLAG).
        # "auto" = the key is absent from the request body (byte-identical to pre-flag runs);
        # rows from different settings must never be pooled, so it is frozen here AND per row.
        "thinking": thinking_setting(cfg),
        "arm": arm,
        "rep": rep,
        "N": int(fixture["N"]),
        "model": {
            "name": cfg.model,
            "endpoint": cfg.base_url.rstrip("/"),
            "engine": cfg.engine,
            "tokenizer": "server-reported (usage.prompt_tokens); no client tokenizer",
        },
        "renderer": {
            "api": "POST /chat/completions",
            "stream": bool(cfg.stream),
            "include_usage": bool(cfg.stream),
            "temperature": 0,
            "max_tokens": int(cfg.max_tokens),
            "thinking": thinking_setting(cfg),
            "chat_template_kwargs": thinking_kwargs(thinking_setting(cfg)),
            "messages": "system + user; content is one user string per turn",
        },
        "engine_flags": {
            "ctx_window": int(fixture.get("window_tokens", 131072)),
            "design_cap_tokens": int(fixture["wall_tokens"]),
            "cache_block_tokens": 64,
            "concurrency_B": 64,
            "source": "LONGRUN-PREREG §0/§2; RECORD.md C5 (cached = P1 - P1 mod 64)",
            "knowable": "ctx/cap/block from the prereg; server build flags are not exposed via /v1",
        },
        "fixture": {
            "path": fixture["_path"],
            "sha256": fixture["_sha256"],
            "schema": fixture["schema"],
            "task_id": fixture["task_id"],
            "bytes_per_token": float(fixture["bytes_per_token"]),
            "wall_tokens": int(fixture["wall_tokens"]),
        },
        "prereg": {
            "path": "experiments/ptr-engine/LONGRUN-PREREG.md",
            "sha256": sha256_file("experiments/ptr-engine/LONGRUN-PREREG.md")
            if os.path.exists("experiments/ptr-engine/LONGRUN-PREREG.md") else None,
        },
        "prediction": PREDICTIONS[arm],
        "rows_path": rows_path,
        # FETCH-CHANNEL: present only on a --tools run, so a tools-off manifest keeps
        # the exact bytes it had before this flag existed.
        **({"tools": {"names": tool_names(cfg), "max_calls_per_turn": TOOL_CALLS_PER_TURN,
                      "max_fetch_rounds_per_arm": TOOL_FETCH_ROUNDS_PER_ARM,
                      "read_cap_lines": TOOL_READ_CAP_LINES,
                      "read_cap_chars": TOOL_READ_CAP_CHARS,
                      "followups_are_requests": True}}
           if tools_enabled(cfg) else {}),
    }


def write_manifest(path: str, doc: dict) -> tuple[bytes, str]:
    """Write the frozen manifest atomically; fail loudly (never start a run without it)."""
    data = (json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return data, sha256_bytes(data)


# ------------------------------------------------------------------- HTTP / usage
class RequestFailure(RuntimeError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def thinking_setting(cfg) -> str:
    """The --thinking setting, tolerant of plain namespaces built without the flag."""
    return str(getattr(cfg, "thinking", "auto") or "auto")


def thinking_kwargs(thinking: str):
    """chat_template_kwargs for one thinking setting.

    'auto' -> None: the key is OMITTED entirely, so the request body stays byte-identical
    to the pre-flag runner.  'on'/'off' -> the SGLang chat-template thinking switch.
    Rows from different settings must never be pooled, so the setting is stamped on every
    row and in the frozen manifest as well.
    """
    if thinking == "auto":
        return None
    if thinking == "on":
        return {"enable_thinking": True}
    if thinking == "off":
        return {"enable_thinking": False}
    raise ValueError(f"unknown thinking setting {thinking!r} (expected auto|on|off)")


def request_body(cfg, messages: list[dict]) -> dict:
    body = {
        "model": cfg.model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": int(cfg.max_tokens),
        "stream": bool(cfg.stream),
    }
    if cfg.stream:
        body["stream_options"] = {"include_usage": True}
    kwargs = thinking_kwargs(thinking_setting(cfg))
    if kwargs is not None:
        body["chat_template_kwargs"] = kwargs
    return body





def extract_usage(payload: dict, engine: str):
    """Return (prompt_tokens, raw_cached, token_source) from an OpenAI-ish response."""
    payload = payload or {}
    usage = payload.get("usage") or {}
    meta = payload.get("meta_info") or {}
    prompt, src = None, []
    if usage.get("prompt_tokens") is not None:
        prompt = int(usage["prompt_tokens"])
        src.append("usage.prompt_tokens")
    elif meta.get("prompt_tokens") is not None:
        prompt = int(meta["prompt_tokens"])
        src.append("meta_info.prompt_tokens")
    raw_cached = None
    details = usage.get("prompt_tokens_details")
    if isinstance(details, dict) and "cached_tokens" in details:
        raw_cached = details.get("cached_tokens")
        src.append("usage.prompt_tokens_details.cached_tokens")
    elif "cached_tokens" in usage:
        raw_cached = usage.get("cached_tokens")
        src.append("usage.cached_tokens")
    elif "cached_tokens" in meta:
        raw_cached = meta.get("cached_tokens")
        src.append("meta_info.cached_tokens")
    return prompt, raw_cached, (";".join(src) or "absent")


def send_chat(cfg, messages: list[dict]) -> dict:
    body = request_body(cfg, messages)
    data = json.dumps(body).encode("utf-8")
    url = cfg.base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json",
                 "Accept": "text/event-stream" if cfg.stream else "application/json"},
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=float(cfg.timeout)) as resp:
            if not cfg.stream:
                payload = json.loads(resp.read().decode("utf-8"))
                latency = time.perf_counter() - t0
                choice0 = (payload.get("choices") or [{}])[0]
                message = choice0.get("message") or {}
                content_raw = message.get("content") or ""
                reasoning_raw = message.get("reasoning_content") or message.get("reasoning") or ""
                finish_reason = choice0.get("finish_reason")
                usage_payload = payload
                ttft = None
            else:
                content_parts: list[str] = []
                reasoning_parts: list[str] = []
                usage_payload = None
                ttft = None
                finish_reason = None
                for raw_line in resp:
                    line = raw_line.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    payload_raw = line[5:].strip()
                    if payload_raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload_raw)
                    except json.JSONDecodeError:
                        continue
                    if chunk.get("usage"):
                        usage_payload = chunk
                    for choice in chunk.get("choices") or []:
                        # occamy-1.0 is a reasoning model: its tokens arrive on
                        # delta.reasoning_content first, then delta.content.  Reading only
                        # delta.content recorded 99/192 empty turns in Stage 1 (LR01 defect).
                        delta = choice.get("delta") or {}
                        piece_c = delta.get("content")
                        piece_r = delta.get("reasoning_content")
                        if piece_r is None:
                            piece_r = delta.get("reasoning")
                        # TTFT = dispatch -> first token on EITHER channel.
                        if (piece_c or piece_r) and ttft is None:
                            ttft = time.perf_counter() - t0
                        if piece_c:
                            content_parts.append(piece_c)
                        if piece_r:
                            reasoning_parts.append(piece_r)
                        if choice.get("finish_reason"):
                            finish_reason = choice.get("finish_reason")
                latency = time.perf_counter() - t0
                content_raw = "".join(content_parts)
                reasoning_raw = "".join(reasoning_parts)

    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read()[:500].decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            detail = ""
        raise RequestFailure(exc.code, f"HTTP {exc.code}: {detail}") from exc
    except Exception as exc:  # noqa: BLE001 - recorded, never retried
        raise RequestFailure(None, f"{type(exc).__name__}: {exc}") from exc

    # Answer-bearing text: the content channel when the model emitted one, else the
    # reasoning channel (a reasoning model answers there when content is empty).
    content_source = ("both" if (content_raw and reasoning_raw)
                      else "content" if content_raw
                      else "reasoning" if reasoning_raw
                      else "none")
    answer = content_raw if content_raw else reasoning_raw

    prompt, raw_cached, token_source = extract_usage(usage_payload or {}, cfg.engine)
    usage = (usage_payload or {}).get("usage") or {}
    completion = int(usage["completion_tokens"]) if usage.get("completion_tokens") is not None else None
    # Truncation: finish_reason=="length" is the authoritative signal; when the server
    # omits finish_reason, a completion sitting exactly on the cap is truncated too.
    cap = int(cfg.max_tokens)
    truncated = bool(finish_reason == "length"
                     or (finish_reason is None and completion is not None and completion >= cap))
    return {
        "content": answer,
        "content_raw": content_raw,
        "reasoning": reasoning_raw,
        "content_source": content_source,
        "finish_reason": finish_reason,
        "truncated": truncated,
        "max_tokens": cap,
        "prompt_tokens": prompt,
        "raw_cached": raw_cached,
        "token_source": token_source,
        "completion_tokens": completion,
        "ttft_s": ttft,
        "ttft_ms": round(ttft * 1000.0, 3) if ttft is not None else None,
        "latency_s": latency,
        "usage_missing": prompt is None,
    }


# ------------------------------------------------------------ reasoning policy
# occamy-1.0 is a reasoning model: it streams `delta.reasoning_content` before any
# `delta.content`, and it will spend an unbounded budget on the reasoning channel.
# Raising max_tokens alone therefore cannot deliver "0 truncated" (RUN-STAGE1-LR01:
# 4096 still truncated grow T3 with `content_source="reasoning"` and no answer).
# The policy below is explicit and is applied to EVERY row:
#   answer_source="content"            the content channel carries text (clean).
#   answer_source="reasoning-fallback" no content, but the reasoning channel either
#                                      completed (finish_reason != "length") or the
#                                      checkpoint's expected value appears in it
#                                      verbatim.  Marked, never mixed with clean rows.
#   answer_source="none"               no answer-bearing text: a failed turn.
#   failed_turn = truncated and the expected value is absent: the answer is
#   incomplete, so the row never enters a latency average as a success.
_REASONING_POLICY = "content-channel-first; reasoning-only accepted only when complete "\
                    "or carrying the checkpoint expected value verbatim; truncated rows "\
                    "without the expected value are failed turns"
_TOKENIZER = None
_TOKENIZER_METHOD = None


def count_channel_tokens(text: str, fallback_bpt: float = 4.0477) -> tuple[int, str]:
    """Token count for one channel. tiktoken cl100k_base when importable (the fixture's
    own estimator, see adapt_fixture.py), else bytes / fixture bytes_per_token."""
    global _TOKENIZER, _TOKENIZER_METHOD
    if not text:
        return 0, (_TOKENIZER_METHOD or "tiktoken:cl100k_base")
    if _TOKENIZER is None:
        try:
            import tiktoken  # type: ignore
            _TOKENIZER = tiktoken.get_encoding("cl100k_base")
            _TOKENIZER_METHOD = "tiktoken:cl100k_base"
        except Exception:  # noqa: BLE001 - fall back, never fail a measurement
            _TOKENIZER = False
            _TOKENIZER_METHOD = f"bytes/{fallback_bpt:g} (fixture bytes_per_token)"
    if _TOKENIZER:
        return len(_TOKENIZER.encode(text, disallowed_special=())), _TOKENIZER_METHOD
    return int(ceil(len(text.encode("utf-8")) / float(fallback_bpt or 4.0))), _TOKENIZER_METHOD


def checkpoint_expected(fixture: dict, t: int) -> tuple[str | None, str | None]:
    for cp in fixture.get("checkpoints") or []:
        if int(cp.get("turn", -1)) == int(t):
            return cp.get("expected"), cp.get("question")
    return None, None


def _squash(text: str) -> str:
    return " ".join((text or "").split()).lower()


def contains_expected(text: str, expected: str | None) -> bool:
    if not expected:
        return False
    return _squash(expected) in _squash(text)


# --------------------------------------------------------------------------- rows
def make_row(cfg, fixture, arm, rep, run_id, t, resp, content, kind, manifest_sha, extra):
    if resp is None:
        # A failed turn has no measurement: null, never a measured zero.
        cached, prompt, uncached = None, None, None
    else:
        cached = normalize_cached_tokens(resp.get("raw_cached"), cfg.engine)
        prompt = resp.get("prompt_tokens")
        uncached = None if (prompt is None or cached is None) else int(prompt) - int(cached)
    expected, cp_question = checkpoint_expected(fixture, t)
    if resp is None:
        # A failed request is a failed turn with no channel measurement.
        content_raw = reasoning_raw = ""
        r_tok = c_tok = None
        tok_method = None
        truncated = None
        answer_source = "none"
        failed_turn = True
        expected_present = False
        answer_verified = None
    else:
        content_raw = resp.get("content_raw") or ""
        reasoning_raw = resp.get("reasoning") or ""
        bpt = float(fixture.get("bytes_per_token") or 4.0477)
        c_tok, tok_method = count_channel_tokens(content_raw, bpt)
        r_tok, _ = count_channel_tokens(reasoning_raw, bpt)
        truncated = bool(resp.get("truncated"))
        expected_present = bool(contains_expected(reasoning_raw, expected)) if expected else False
        content_has_expected = bool(contains_expected(content_raw, expected)) if expected else False
        if content_raw.strip():
            answer_source = "content"
        elif reasoning_raw.strip() and (not truncated or expected_present):
            # Reasoning-only completion: usable ONLY when it finished, or when it
            # literally carries the checkpoint's expected value.  Marked, not clean.
            answer_source = "reasoning-fallback"
        else:
            answer_source = "none"
        # "length" without the expected value is an incomplete answer = failed turn,
        # on either channel; it must never enter a latency average as a success.
        failed_turn = bool(truncated and not (expected_present or content_has_expected))
        answer_verified = (bool(content_has_expected or expected_present)
                           if expected is not None else None)
    row = {
        "arm": arm, "task_id": fixture["task_id"], "rep": rep, "turn": t,
        "prompt_tokens": prompt,
        "cached_tokens": cached,
        "uncached_tokens": uncached,
        "ttft_s": round(resp["ttft_s"], 6) if resp and resp.get("ttft_s") is not None else None,
        "latency_s": round(resp["latency_s"], 6) if resp else None,
        "completion_tokens": resp.get("completion_tokens") if resp else None,
        "content_sha256": sha256_text(content) if content is not None else None,
        "content": content,
        "fixture_sha256": fixture["_sha256"],
        "run_manifest_sha256": manifest_sha,
        "token_source": resp.get("token_source") if resp else "absent",
        "ts": iso(utc_now()),
        # extras (analysis may use; never replace the contracted keys)
        # instrument-fix fields: TTFT per row, both channels, truncation provenance
        "ttft_ms": resp.get("ttft_ms") if resp else None,
        "content_source": resp.get("content_source") if resp else None,
        "reasoning": resp.get("reasoning") if resp else None,
        "reasoning_sha256": sha256_text(resp["reasoning"]) if resp and resp.get("reasoning") else None,
        "finish_reason": resp.get("finish_reason") if resp else None,
        "truncated": bool(resp.get("truncated")) if resp else None,
        "max_tokens": resp.get("max_tokens") if resp else int(cfg.max_tokens),
        # reasoning-policy fields: per-channel split, the verdict, and its provenance
        "reasoning_tokens": r_tok,
        "content_tokens": c_tok,
        "channel_token_method": tok_method,
        "answer_source": answer_source,
        "failed_turn": bool(failed_turn),
        "timing_usable": bool(resp is not None and resp.get("ttft_ms") is not None
                              and not failed_turn),
        "expected": expected,
        "expected_question": cp_question,
        "expected_present": expected_present,
        "answer_verified": answer_verified,
        "reasoning_policy": _REASONING_POLICY,
        "stream": bool(cfg.stream),
        # thinking switch: rows from different settings must NEVER be pooled; a later
        # analysis must be able to read the setting from the row alone.
        "thinking": thinking_setting(cfg),
        "run_id": run_id, "engine": cfg.engine, "kind": kind,
        "is_checkpoint": bool(extra.get("is_checkpoint")), "checkpoint": extra.get("checkpoint"),
        "cached_reported": bool(resp and resp.get("raw_cached") is not None),
        "usage_missing": bool(resp and resp.get("usage_missing")),
        "lease": extra.get("lease"), "evicted": extra.get("evicted"),
        "prompt_sha256": extra.get("prompt_sha256"),
        "http_status": extra.get("http_status"), "error": extra.get("error"),
    }
    if extra.get("fetch_followup"):
        # FETCH-CHANNEL: a follow-up model request served a tool result (real request).
        row["fetch_followup"] = True
    if extra.get("tool_calls") is not None:
        row["tool_calls"] = extra["tool_calls"]
    return row


def append_row(path: str, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def read_cell_rows(rows_path: str, run_id: str, task_id: str, arm: str, rep: int) -> list[dict]:
    rows: list[dict] = []
    if not os.path.exists(rows_path):
        return rows
    with open(rows_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (row.get("run_id"), row.get("task_id"), row.get("arm"), row.get("rep")) == (
                    run_id, task_id, arm, rep):
                rows.append(row)
    return rows


def resume_start(rows: list[dict]) -> int:
    if not rows:
        return 0
    if any(row.get("error") for row in rows):
        raise SystemExit("RESUME REFUSED: this cell already holds a failed row; a failure is "
                         "recorded, not retried past the budget. Start a new --run-id.")
    return max(int(row.get("turn") or 0) for row in rows)


# ---------------------------------------------------------------------- dry-run
def preview_write(path: str, text: str) -> tuple[int, str]:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))
    return len(text.encode("utf-8")), sha256_text(text)


def preview_body(cfg, planner: Planner, prompt: str) -> str:
    return json.dumps(request_body(cfg, planner.messages(prompt)), sort_keys=True, indent=2,
                      ensure_ascii=False)


def run_dry(cfg, fixture: dict, cells: list[tuple[str, int]]) -> int:
    root = os.path.join("/tmp/longrun-previews", fixture["task_id"])
    order: list[str] = []
    reps_by_arm: dict[str, int] = {}
    for arm, _rep in cells:
        if arm not in reps_by_arm:
            order.append(arm)
            reps_by_arm[arm] = 0
        reps_by_arm[arm] += 1
    previews: dict[str, list[str]] = {arm: [] for arm in order}
    counts: dict[str, dict] = {}

    for arm in order:
        planner = Planner(arm, fixture, dry_run=True)
        c = {"reps": reps_by_arm[arm], "digest_requests": 0, "wall_turn": None,
             "trunc_turn": None, "post_wall": None}
        counts[arm] = c
        for t in range(1, int(fixture["N"]) + 1):
            info = planner.build(t)
            body = preview_body(cfg, planner, info["prompt"])
            digest_body = None
            if info["digest_request"] is not None:
                c["digest_requests"] += 1
                digest_body = json.dumps(request_body(cfg, info["digest_request"]), sort_keys=True,
                                         indent=2, ensure_ascii=False)
                if c["wall_turn"] is None:
                    c["wall_turn"] = t
                    dpath = os.path.join(root, arm, f"wall-{t:02d}-digest-request.json")
                    dbytes, dsha = preview_write(dpath, digest_body)
                    print(f"  [{arm}] first wall at T{t}: digest request {dbytes} B sha256={dsha} ({dpath})")
            if len(previews[arm]) < 3:
                previews[arm].append(sha256_text(body))
                path = os.path.join(root, arm, f"turn-{t:02d}.json")
                nbytes, digest = preview_write(path, body)
                user0 = info["prompt"].replace("\n", " ")[:100]
                print(f"  [{arm}] T{t}: {nbytes} B sha256={digest} user=\"{user0}\"")
                if cfg.show_prompts:
                    print(body)
            if arm == "transcript-grow" and c["trunc_turn"] is None and info["evicted"]:
                c["trunc_turn"] = t
                print(f"  [{arm}] first FIFO truncation at T{t}: evicted {info['evicted']} history block(s)")
            if arm == "transcript-compact" and c["wall_turn"] is not None and c["post_wall"] is None:
                c["post_wall"] = (t, sha256_text(body))
                ppath = os.path.join(root, arm, f"post-wall-{t:02d}.json")
                pbytes, psha = preview_write(ppath, body)
                print(f"  [{arm}] post-wall body at T{t}: {pbytes} B sha256={psha} "
                      "(digest text is a placeholder offline; the digest REQUEST above is exact)")
            # simulate the answer the model would have produced
            planner.record(t, f"<<answer from turn {t}: not produced in dry-run>>")

    print("\nREQUEST COUNTS (what --dry-run would send)")
    total = 0
    for arm in order:
        c = counts[arm]
        turns = int(fixture["N"]) * c["reps"]
        extra = c["digest_requests"] * c["reps"]
        cell_total = turns + extra
        total += cell_total
        assert turns == int(fixture["N"]) * c["reps"], "turn count must be N x reps"
        print(f"  {arm:19s} turn_requests={turns} (N={fixture['N']} x reps={c['reps']})  "
              f"digest_requests={extra}  cell_total={cell_total}")
    print(f"  would_send_total={total}")
    if tools_enabled(cfg):
        # Offline there is no model turn, so no <tool_call> can be parsed and no fetch
        # is possible: the cap below is the ceiling, not a predicted spend.
        print(f"  tool_channel={','.join(tool_names(cfg))} fetch_rounds_cap="
              f"{TOOL_FETCH_ROUNDS_PER_ARM} (per arm) max_calls_per_turn={TOOL_CALLS_PER_TURN} "
              f"fetch_requests_in_this_preview=0 (no model turn offline)")

    print("\nPREVIEW PAIRWISE (first three request bodies; 0/3 differ = identical)")
    for i, a in enumerate(order):
        for b in order[i + 1:]:
            diff = sum(1 for x, y in zip(previews[a], previews[b]) if x != y)
            note = ""
            if (a, b) == ("transcript-grow", "transcript-compact"):
                note = "  <- identical BY DESIGN before B's first wall"
            print(f"  {a} vs {b}: {diff}/3 differ{note}")
    return 0


# ---------------------------------------------------------------------- self-test
def self_test() -> int:
    sglang = normalize_cached_tokens(None, "sglang")
    vllm = normalize_cached_tokens(None, "vllm")
    line = inspect.getsourcelines(normalize_cached_tokens)[1]
    print("NULL SEMANTICS — normalize_cached_tokens(None, engine)")
    print(f"  sglang: None -> {sglang!r}")
    print(f"  vllm:   None -> {vllm!r}")
    print(f"  function: {normalize_cached_tokens.__module__}.{normalize_cached_tokens.__name__} "
          f"at {inspect.getsourcefile(normalize_cached_tokens)}:{line}")
    print(f"  reported 32: sglang -> {normalize_cached_tokens(32, 'sglang')!r}, "
          f"vllm -> {normalize_cached_tokens(32, 'vllm')!r}")
    assert sglang == 0 and isinstance(sglang, int), "SGLang null must be the integer 0"
    assert vllm is None, "vLLM null must stay null"
    print("  PASS: None -> 0 on the SGLang path; None -> null on the vLLM path")
    return 0


# --------------------------------------------------------------------------- cell
def run_cell(cfg, fixture: dict, arm: str, rep: int, run_id: str, rows_path: str) -> int:
    manifest_path = cfg.manifest_path or os.path.join(cfg.manifest_dir, run_id + ".json")
    rows = read_cell_rows(rows_path, run_id, fixture["task_id"], arm, rep) if cfg.resume else []
    if cfg.resume and rows and os.path.exists(manifest_path):
        with open(manifest_path, "rb") as fh:
            data = fh.read()
        manifest_sha = sha256_bytes(data)
        if rows[0].get("run_manifest_sha256") != manifest_sha:
            print(f"RESUME REFUSED: manifest {manifest_path} sha {manifest_sha} does not match the "
                  f"rows ({rows[0].get('run_manifest_sha256')})", file=sys.stderr)
            return 5
        print(f"resume: reusing frozen manifest {manifest_path} sha256={manifest_sha}")
    else:
        try:
            data, manifest_sha = write_manifest(manifest_path,
                                                build_manifest(cfg, fixture, arm, rep, run_id, rows_path))
        except OSError as exc:
            print(f"MANIFEST ABORT: cannot write {manifest_path}: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            print("MANIFEST ABORT: the run did not start — no request was sent (Consonance: no "
                  "frozen manifest, no result).", file=sys.stderr)
            return 3
        print(f"manifest: {manifest_path} ({len(data)} B) sha256={manifest_sha}")

    planner = Planner(arm, fixture, dry_run=False)
    start = 1
    if rows:
        start = resume_start(rows) + 1
        planner.replay(rows)
        print(f"resume: cell has turns 1..{start - 1}; continuing at {start}")
    n_turns = int(fixture["N"])
    max_turns = int(getattr(cfg, "max_turns", 0) or 0)
    if max_turns > 0:
        n_turns = min(n_turns, max_turns)
    budget = n_turns + (expected_digests(fixture) if arm == "transcript-compact" else 0)
    if tools_enabled(cfg):
        # The tool channel authorises exactly the fetch rounds it is allowed to spend,
        # so a fetch run's request count can legitimately exceed N.  With --tools off
        # this branch does not run and `budget` is the same expression as before.
        budget += TOOL_FETCH_ROUNDS_PER_ARM
    sent = 0
    fetch_rounds_used = 0

    for t in range(start, n_turns + 1):
        info = planner.build(t)
        turn = info["turn"]
        # The fixture marks a checkpoint with kind == "checkpoint" and names it in
        # fixture["checkpoints"], not with a per-turn "checkpoint" key: reading only
        # turn.get("checkpoint") left is_checkpoint False on every row (found here at T12).
        declared = next((c for c in fixture.get("checkpoints") or []
                         if int(c.get("turn", -1)) == int(t)), None)
        extras = {"is_checkpoint": bool(turn.get("checkpoint")) or turn.get("kind") == "checkpoint"
                  or declared is not None,
                  "checkpoint": turn.get("checkpoint") or declared,
                  "lease": info.get("lease"), "evicted": info.get("evicted")}
        digest_attempts = 0
        while info["digest_request"] is not None and digest_attempts < 2:
            if sent >= budget:
                print(f"BUDGET ABORT at T{t}: {sent} requests already sent (budget {budget})",
                      file=sys.stderr)
                return 4
            msg = info["digest_request"]
            try:
                resp = send_chat(cfg, msg)
            except RequestFailure as exc:
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, None, None, "digest", manifest_sha,
                    dict(extras, http_status=exc.status, error=str(exc),
                         prompt_sha256=sha256_text(msg[1]["content"]))))
                print(f"TURN FAILED (digest) T{t}: {exc} — cell stopped, failure row recorded",
                      file=sys.stderr)
                return 4
            sent += 1
            append_row(rows_path, make_row(
                cfg, fixture, arm, rep, run_id, t, resp, resp["content"], "digest", manifest_sha,
                dict(extras, prompt_sha256=sha256_text(msg[1]["content"]))))
            print(f"  [T{t}] digest request sent (prompt_tokens={resp['prompt_tokens']})")
            planner.digest = resp["content"]
            planner.raw = planner.raw[-4:]
            digest_attempts += 1
            info = planner.build(t)

        if sent >= budget:
            print(f"BUDGET ABORT at T{t}: {sent} requests already sent (budget {budget})",
                  file=sys.stderr)
            return 4
        try:
            resp = send_chat(cfg, planner.messages(info["prompt"]))
        except RequestFailure as exc:
            append_row(rows_path, make_row(
                cfg, fixture, arm, rep, run_id, t, None, None, "turn", manifest_sha,
                dict(extras, http_status=exc.status, error=str(exc),
                     prompt_sha256=sha256_text(info["prompt"]))))
            print(f"TURN FAILED T{t}: {exc} — cell stopped, failure row recorded", file=sys.stderr)
            return 4
        sent += 1
        # FETCH-CHANNEL: if the turn asked for the exact lines it needs, serve them.
        # The FINAL response of the turn is what the row records and what the planner
        # replays, so a checkpoint answer lives on the checkpoint turn's own row;
        # every follow-up request is appended BEFORE that row with kind="tool-followup"
        # and fetch_followup=true, so `by_turn[t]` still resolves to the real answer.
        turn_calls: list[dict] = []
        followup_rows: list[dict] = []
        if tools_enabled(cfg):
            try:
                _m, resp, sent, fetch_rounds_used, turn_calls, followup_rows = fetch_rounds(
                    cfg, fixture, arm, rep, run_id, t, manifest_sha, extras,
                    planner.messages(info["prompt"]), resp, sent, budget, fetch_rounds_used)
            except BudgetExhausted as exc:
                print(f"BUDGET ABORT at T{t}: {exc}", file=sys.stderr)
                return 4
            except RequestFailure as exc:
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, None, None, "tool-followup", manifest_sha,
                    dict(extras, http_status=exc.status, error=str(exc),
                         fetch_followup=True)))
                print(f"TURN FAILED (fetch follow-up) T{t}: {exc} — cell stopped, failure row "
                      "recorded", file=sys.stderr)
                return 4
        row_extra = dict(extras, prompt_sha256=sha256_text(info["prompt"]))
        if tools_enabled(cfg):
            row_extra["tool_calls"] = turn_calls
        row = make_row(cfg, fixture, arm, rep, run_id, t, resp, resp["content"], "turn", manifest_sha,
                       row_extra)
        for frow in followup_rows:
            append_row(rows_path, frow)
        append_row(rows_path, row)
        planner.record(t, resp["content"])
        print(f"  [T{t}] prompt={row['prompt_tokens']} cached={row['cached_tokens']} "
              f"ttft_ms={row['ttft_ms']} src={row['content_source']} "
              f"finish={row['finish_reason']} truncated={row['truncated']} "
              f"lat={row['latency_s']} comp={row['completion_tokens']}")
        if tools_enabled(cfg) and turn_calls:
            done = sum(1 for c in turn_calls if c.get("executed"))
            print(f"  [T{t}] tool_calls={len(turn_calls)} executed={done} "
                  f"fetch_followups={len(followup_rows)} fetch_rounds_used={fetch_rounds_used}"
                  f"/{TOOL_FETCH_ROUNDS_PER_ARM} requests_sent={sent}")
    if tools_enabled(cfg):
        print(f"requests_sent={sent} (budget {budget}; fetch rounds "
              f"{fetch_rounds_used}/{TOOL_FETCH_ROUNDS_PER_ARM})")
    return 0


# ------------------------------------------------------------------------ summary
def rows_for_run(rows_path: str, run_base: str) -> list[dict]:
    out: list[dict] = []
    if not os.path.exists(rows_path):
        return out
    with open(rows_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("run_id", "")).startswith(run_base):
                out.append(row)
    return out


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(ceil(q * len(ordered))) - 1))
    return ordered[idx]


def token_distribution(rows: list[dict]) -> dict:
    """reasoning_tokens + content_tokens per answered turn (nearest-rank p95)."""
    totals = [float((r.get("reasoning_tokens") or 0) + (r.get("content_tokens") or 0))
              for r in rows if r.get("error") is None and r.get("reasoning_tokens") is not None]
    if not totals:
        return {"n": 0, "mean": None, "p95": None, "max": None}
    return {
        "n": len(totals),
        "mean": round(sum(totals) / len(totals), 1),
        "p95": percentile(totals, 0.95),
        "max": max(totals),
    }


def summarise_rows(rows: list[dict]) -> dict:
    """Counts the card requires: truncated rows, content_source mix, per-row TTFT,
    the reasoning-policy verdict per row, and the per-turn token distribution."""
    sources = {"content": 0, "reasoning": 0, "both": 0, "none": 0, None: 0}
    for r in rows:
        sources[r.get("content_source")] = sources.get(r.get("content_source"), 0) + 1
    answers = {"content": 0, "reasoning-fallback": 0, "none": 0}
    for r in rows:
        answers[r.get("answer_source") or "none"] = answers.get(r.get("answer_source") or "none", 0) + 1
    usable = [r["latency_s"] for r in rows
              if r.get("timing_usable") and r.get("latency_s") is not None]
    return {
        "rows": len(rows),
        "truncated": sum(1 for r in rows if r.get("truncated")),
        "ttft_n": sum(1 for r in rows if r.get("ttft_ms") is not None),
        "content_source_counts": {str(k): v for k, v in sources.items() if v},
        "answer_source_counts": answers,
        "finish_reasons": _count(r.get("finish_reason") for r in rows),
        "requests_spent": sum(1 for r in rows if r.get("error") is None),
        "failed_rows": sum(1 for r in rows if r.get("error") is not None),
        "failed_turns": sum(1 for r in rows if r.get("failed_turn")),
        "reasoning_fallback_rows": sum(1 for r in rows
                                       if r.get("answer_source") == "reasoning-fallback"),
        "timing_usable_n": len(usable),
        "latency_usable_mean_s": round(sum(usable) / len(usable), 3) if usable else None,
        "token_distribution": token_distribution(rows),
        "channel_token_method": next((r.get("channel_token_method") for r in rows
                                      if r.get("channel_token_method")), None),
    }


def _count(values) -> dict:
    out: dict = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return out


def report_run(rows_path: str, run_base: str, cfg, smoke: bool = False) -> int:
    rows = rows_for_run(rows_path, run_base)
    if not rows:
        print("SUMMARY ABORT: no rows for this run base", file=sys.stderr)
        return 6
    s = summarise_rows(rows)
    print("\n=== SUMMARY ===")
    print(f"rows={s['rows']} requests={s['requests_spent']} truncated={s['truncated']} "
          f"ttft_n={s['ttft_n']} max_tokens={cfg.max_tokens}")
    print(f"content_source: {json.dumps(s['content_source_counts'], sort_keys=True)}")
    print(f"answer_source:  {json.dumps(s['answer_source_counts'], sort_keys=True)}")
    print(f"finish_reason:  {json.dumps(s['finish_reasons'], sort_keys=True)}")
    print(f"failed_turns={s['failed_turns']} reasoning_fallback={s['reasoning_fallback_rows']} "
          f"timing_usable={s['timing_usable_n']} token_dist={json.dumps(s['token_distribution'])} "
          f"tok_method={s['channel_token_method']}")
    if smoke:
        print("\nturn arm prompt_tokens cached_tokens ttft_ms r_tok c_tok answer_source "
              "finish_reason truncated")
        for r in rows:
            print(f"{r['turn']:>4} {r['arm']:<18} {str(r['prompt_tokens']):>6} "
                  f"{str(r['cached_tokens']):>6} {str(r['ttft_ms']):>10} "
                  f"{str(r.get('reasoning_tokens')):>6} {str(r.get('content_tokens')):>6} "
                  f"{str(r.get('answer_source')):>18} {str(r['finish_reason']):>13} "
                  f"{str(r['truncated']):>9}")
        bad = [r for r in rows if r.get("answer_source") == "none"]
        print(f"\nsmoke: {len(rows)} rows, {len(bad)} answer_source=none, "
              f"truncated={s['truncated']}, failed_turns={s['failed_turns']}, "
              f"ttft_n={s['ttft_n']}")
        if bad:
            print(f"SMOKE FAIL: {len(bad)} row(s) carry no answer on either channel",
                  file=sys.stderr)
            return 7
        # RUN-INSTRUMENT-FIX requirement: a smoke row that hits the cap is a truncated
        # measurement and must fail the smoke, not merely be annotated.
        if s["truncated"]:
            print(f"SMOKE FAIL: {s['truncated']} row(s) TRUNCATED at "
                  f"max_tokens={cfg.max_tokens}", file=sys.stderr)
            return 7
        print("SMOKE PASS: every row answer-bearing and none truncated "
              "(0 rows answer_source=none, 0 truncated)")
    if s["truncated"]:
        print(f"NOTE: {s['truncated']} row(s) TRUNCATED at max_tokens={cfg.max_tokens} — "
              f"failed_turn rows are excluded from latency averages.", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fixture", default="experiments/ptr-engine/longrun/fixtures/LR-01.json")
    ap.add_argument("--task", default=None)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--manifest-dir", default="experiments/ptr-engine/longrun/manifests")
    ap.add_argument("--manifest-path", default=None)
    ap.add_argument("--rows", default=None)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--engine", default=DEFAULT_ENGINE, choices=("sglang", "vllm"))
    ap.add_argument("--stream", dest="stream", action="store_true", default=True)
    ap.add_argument("--no-stream", dest="stream", action="store_false")
    # Chat-template thinking switch (SGLang).  'auto' (default) sends NO chat_template_kwargs
    # key at all, so the body stays byte-identical to every run before this flag existed;
    # 'on'/'off' add {"enable_thinking": <bool>}.  The setting is frozen in the manifest and
    # stamped on every row, because rows from different settings must never be pooled.
    ap.add_argument("--thinking", choices=("auto", "on", "off"), default="auto",
                    help="chat-template thinking switch: auto (omit the key, today's payload), "
                         "on (enable_thinking: true), off (enable_thinking: false)")
    # 16384 (was 128 -> 1024 -> 4096): Stage 1 (RUN-STAGE1-LR01) truncated 140/192 rows at
    # 128; at 1024 a measured 7/12 smoke rows still hit finish_reason="length"; at 4096 the
    # 4-row fix run still truncated transcript-grow T3 at 4096 completion tokens with
    # completion on the reasoning channel only and no answer.  16384 is 4x that measured
    # truncation ceiling and ~4.5x the largest CLEAN completion (3592 tok), so a reasoning
    # preamble of the observed shape can finish; worst case ~455 s at the measured ~36 tok/s
    # stays inside --timeout 900.  The cap is NOT the policy on its own: see
    # _REASONING_POLICY (reasoning-only rows are marked, truncated-without-value rows are
    # failed turns), and it stays configurable via --max-tokens.
    ap.add_argument("--max-tokens", type=int, default=16384)
    ap.add_argument("--max-turns", type=int, default=0,
                    help="stop each cell after this many turns (0 = the fixture's N)")
    ap.add_argument("--smoke", action="store_true",
                    help="4 arms x 3 turns = 12 requests; per-row table with reasoning/content "
                         "token split and answer_source; non-zero exit if any row has "
                         "answer_source == 'none'")
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--show-prompts", action="store_true")
    # FETCH-CHANNEL (opt-in). Default OFF: no tool code runs, no row/manifest key is
    # added, and request bodies are byte-identical to runs made before this flag.
    # With `read_file` on, a turn that emits `<tool_call>…read_file…` gets its lines
    # read back, bounded by 2 calls/turn, 1 follow-up request per fetch, 8 fetch
    # rounds per arm; every follow-up is a real request and is row-recorded.
    ap.add_argument("--tools", default="", metavar="LIST",
                    help="comma-separated tool channel(s) to enable (default: none / off); "
                         "supported: read_file")
    cfg = ap.parse_args(argv)

    if cfg.self_test:
        return self_test()

    if cfg.smoke:
        cfg.arms = ",".join(ARMS)
        cfg.reps = 1
        cfg.max_turns = 3
        cfg.stream = True
        if not cfg.rows or cfg.rows.endswith("rows-longrun-2026-10-26.jsonl"):
            cfg.rows = "experiments/ptr-engine/measure/rows-longrun-2026-10-26-policy.jsonl"
        cfg.run_id = cfg.run_id or f"smoke-{utc_now().strftime('%Y%m%dT%H%M%SZ')}"
        print(f"SMOKE: {len(ARMS)} arms x 3 turns = 12 requests, max_tokens={cfg.max_tokens}")
        print(f"POLICY: {_REASONING_POLICY}")
    arms = [a.strip() for a in cfg.arms.split(",") if a.strip()]
    bad = [a for a in arms if a not in ARMS]
    if bad:
        print(f"unknown arm(s): {bad}; known: {list(ARMS)}", file=sys.stderr)
        return 2
    try:
        fixture = load_fixture(cfg.fixture)
    except FixtureError as exc:
        print(f"FIXTURE ERROR: {exc}", file=sys.stderr)
        return 2
    if cfg.task and cfg.task != fixture["task_id"]:
        print(f"task {cfg.task} != fixture task_id {fixture['task_id']}", file=sys.stderr)
        return 2
    date = utc_now().strftime("%Y-%m-%d")
    rows_path = cfg.rows or f"experiments/ptr-engine/measure/rows-longrun-{date}.jsonl"
    run_base = cfg.run_id or f"longrun-{date}T{utc_now().strftime('%H%M%S')}Z"
    cells = [(arm, rep) for arm in arms for rep in range(1, int(cfg.reps) + 1)]

    if cfg.dry_run:
        for arm, rep in cells:
            rid = f"dryrun-{fixture['task_id']}-{arm}-r{rep}"
            mid = cfg.manifest_path or os.path.join(cfg.manifest_dir, rid + ".json")
            doc = build_manifest(cfg, fixture, arm, rep, rid, rows_path)
            try:
                data, msha = write_manifest(mid, doc)
            except OSError as exc:
                print(f"MANIFEST ABORT: cannot write {mid}: {type(exc).__name__}: {exc}",
                      file=sys.stderr)
                print("MANIFEST ABORT: dry-run stopped before printing any prompt or touching the "
                      "network (Consonance: no frozen manifest, no result).", file=sys.stderr)
                return 3
            print(f"manifest[{arm} r{rep}]: {mid} ({len(data)} B) sha256={msha}")
        print(f"\nDRY-RUN task={fixture['task_id']} N={fixture['N']} fixture={fixture['_path']} "
              f"sha256={fixture['_sha256']}")
        print("(offline: zero requests; exact request bodies under /tmp/longrun-previews/)")
        print("\nFIRST THREE REQUEST BODIES PER ARM")
        return run_dry(cfg, fixture, cells)

    print(f"rows: {rows_path}  run_id base: {run_base}")
    for arm, rep in cells:
        rid = f"{run_base}-{arm}-r{rep}"
        rc = run_cell(cfg, fixture, arm, rep, rid, rows_path)
        if rc != 0:
            return rc
    return report_run(rows_path, run_base, cfg, smoke=bool(cfg.smoke))


if __name__ == "__main__":
    sys.exit(main())
