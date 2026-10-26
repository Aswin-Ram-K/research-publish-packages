#!/usr/bin/env python3
"""QUALITY-ARM runner: does the pointer engine let a task FINISH when the answer
lives in an old body, and what does that cost relative to destructive compaction?

Four arms over ONE corpus, ONE turn plan, ONE model, ONE question (all pre-registered
in ``PREREG.json`` before the first request):

    A  warmpool                every body retained and resolvable
    B  cap-3                   only the last 3 bodies retained; older resolves must
                               raise a PtrError code (honest failure, no rescue)
    C  destructive-compaction  old bodies replaced by a 200-byte digest: still
                               resolvable, deliberately lossy
    D  no-body                 control: no body is ever resolved; index only

Request shape. Turn 1 is the PRIME: ``system = <index block> + "\\n\\n" + <task note>``,
``user = "Begin."``. Turns 2..4 are appends on the same conversation: the assistant's
previous reply plus a new user turn. That is exactly the one-append-onto-a-primed-prefix
shape `experiments/miss-law/LAW.md` §2 measured, so the billing law

    uncached = (P1 mod 64) + L                     L = the measured append P2 - P1
    uncached = 64 + L            if P1 mod 64 == 0        (one block, NOT the prefix)

applies per turn, with ``P1`` the measured ``prompt_tokens`` of the turn and ``L`` the
measured append ``P2 - P1`` once that prefix is resident; only the PRIME turn (no
previous turn) falls back to ``n_payload + 12`` (`experiments/ptr-engine/RECORD.md`
§2 framing), and the path taken is recorded on every row as ``L_source``. Both a
modelled and a measured column are recorded; the prediction is written to the row
BEFORE the request.

V2 INSTRUMENT (``runner_v2.py``).  This file is a copy of the audited ``runner.py`` with
exactly four changes, each marked ``# V2 (defect N):``: the append is the delta, the
server's ``cached_tokens`` and the refusals are PERSISTED, and an alignment guard runs
before any aggregate is written.  The audited runner set ``L = prompt_tokens + FRAMING``
-- the whole prefix as the append -- which collapses the law to ``billed = sum(P1)``.

Rows: ``quality/rows.jsonl`` — one per request (plus one ``corpus`` row), flushed and
fsynced per row. Nothing is retried into looking successful: an HTTP error is a row.

Usage:  python3 quality/runner.py [--arms A,B,C,D] [--reps 3]
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import shutil
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_ROOT = HERE.parent
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import corpus  # noqa: E402

READ_ALL = (
    "\n\nYou have the fetch tool, `fetch(ref)`. If any item in the index might hold "
    "it, call it now; a one-line index entry names an item, not its contents.\n"
    "When you are done, reply with the audit code on its own line and nothing else."
)
_CALLS = {"n": 0}

FETCH_TOOL = {
    "type": "function",
    "function": {
        "name": "fetch",
        "description": "Resolve one pointer reference from the index and return its full body text.",
        "parameters": {
            "type": "object",
            "properties": {"ref": {"type": "string", "description": "e.g. @knowledge:k01@1"}},
            "required": ["ref"],
        },
    },
}
from ptr_engine import (  # noqa: E402
    BodyStore,
    Ledger,
    PtrError,
    Reference,
    Scope,
    append_cost,
    build_prompt,
    compile_turn,
    parse,
    resolve as engine_resolve,
)

HOST, PORT = "192.168.2.168", 8012
MODEL = "occamy-1.0"
SCOPE = "quality"
BLOCK_SIZE = 64
FRAMING = 12
ROWS = HERE / "rows.jsonl"
PREREG = HERE / "PREREG.json"

QUESTION = (
    "Each knowledge item records one calibration constant's audit code. Naming one "
    "constant is meaningful only if its own audit code is known. Which audit code "
    "belongs to the constant named 'lumen'?"
)
ANSWER_FORMAT = "Reply with the audit code only."
EXPECTED_ITEM = "knowledge:k01"
EXPECTED_FACT = "AUD-4417"
NO_TOOL = "Do not use any tools in this turn."

#: (turn, refs resolved in that turn, user text). Turn 1 is the prime.
TURN_PLAN = [
    (1, ["@knowledge:k12@1"],
     "Begin. The system message is a pointer index: each line names one item's "
     "reference, a short digest and its body size in bytes. Read @knowledge:k12@1 "
     "and reply with the single word OK."),
    (2, ["@knowledge:k10@1"],
     "Now read @knowledge:k10@1 and reply with the single word OK."),
    (3, ["@knowledge:k08@1", "@knowledge:k02@1"],
     "Now read @knowledge:k08@1 and also read @knowledge:k02@1, then reply with the "
     "single word OK."),
    (4, [], f"{QUESTION} {ANSWER_FORMAT} {NO_TOOL}"),
]

RETENTION_KEPT = 3  # arm B keeps the 3 most recent bodies
RETENTION_KEPT = 3  # arm B keeps the 3 most recent bodies
#: Bodies known NOT to carry the fact, resolved before the one that does.  This is
#: what pushes the fact-bearing body out of cap-3's window, so arm B must fail.
DISTRACTOR_REFS = ["@knowledge:k02@1"]


DIGEST_BYTES = 200  # arm C digest = first 200 bytes + a marker


# -- bookkeeping ---------------------------------------------------------------
def _now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


_SEQ = {"n": 0, "rep": None, "arm": None}


def write_row(row: dict) -> None:
    row.setdefault("observed_at", _now())
    if _SEQ["rep"] is not None:
        row.setdefault("rep", _SEQ["rep"])
    if _SEQ["arm"] is not None:
        row.setdefault("arm", _SEQ["arm"])
    _SEQ["n"] += 1
    row.setdefault("seq", _SEQ["n"])
    ROWS.parent.mkdir(parents=True, exist_ok=True)
    with ROWS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def post_json(path: str, payload: dict, timeout: float = 600.0) -> dict:
    body = json.dumps(payload).encode("utf-8")
    conn = http.client.HTTPConnection(HOST, PORT, timeout=timeout)
    try:
        conn.request("POST", path, body, {"Content-Type": "application/json"})
        response = conn.getresponse()
        raw = response.read()
        status = response.status
    finally:
        conn.close()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception:
        parsed = {"unparsed": raw[:2000].decode("utf-8", "replace")}
    if status >= 400:
        raise RuntimeError(f"HTTP {status} {path}: {json.dumps(parsed)[:1500]}")
    return parsed


def token_count(messages: list[dict]) -> int:
    """Rendered prompt length, counted the way the REQUEST renders it.

    ``chat_template_kwargs`` is passed because it changes the token count: the
    template emits the empty reasoning block only on that branch.  Measured on this
    build, a 1,400-token prompt counts 1,400 without it and 1,402 with it, and the
    endpoint's own ``usage.prompt_tokens`` is the 1,402.  Counting without it made
    every recorded ``P1`` 2 tokens short of the prompt it was supposed to predict.
    """
    return post_json(
        "/v1/tokenize",
        {
            "model": MODEL,
            "messages": messages,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    )["count"]


def chat(messages: list[dict], tools=None, max_tokens: int = 300) -> dict:
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if tools is not None:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    return post_json("/v1/chat/completions", payload)


def fetch_bodies(messages: list[dict], tools, resolve_ref) -> tuple[list[str], list[dict]]:
    """Model-initiated fetches. ``resolve_ref(text) -> (body|None, refusal_code|None)``.

    A refusal is fed back to the model as the exact PtrError code, so an arm that
    cannot resolve says so on the wire instead of silently returning nothing.
    """
    fetched: list[str] = []
    log: list[dict] = []
    _CALLS["n"] = 0
    for _ in range(6):  # bounded; a runaway loop fails by name, not by cost
        _CALLS["n"] += 1
        response = chat(messages, tools) if tools else chat(messages)
        message = response["choices"][0]["message"]
        calls = message.get("tool_calls") or []
        if not calls:
            return fetched, log + [{"content": message.get("content") or "",
                                    "usage": response.get("usage"),
                                    "api_calls": _CALLS["n"]}]
        messages.append(
            {"role": "assistant", "content": message.get("content") or "", "tool_calls": calls}
        )
        for call in calls:
            name = call["function"]["name"]
            try:
                argument = json.loads(call["function"]["arguments"] or "{}")
            except Exception:
                argument = {}
            ref = argument.get("ref", "")
            if name != "fetch":
                result = f"error: unknown tool {name!r}"
                log.append({"ref": ref, "outcome": "unknown_tool"})
            else:
                body, code = resolve_ref(ref)
                if body is None:
                    result = (
                        f"ERROR {code}: this session's retention policy cannot open {ref}. "
                        "Its body is not available to this session; say so plainly."
                    )
                    log.append({"ref": ref, "outcome": "refused", "code": code})
                else:
                    result = body
                    fetched.append(ref)
                    log.append({"ref": ref, "outcome": "resolved", "bytes": len(body)})
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
    return fetched, log + [{"content": "(fetch budget exhausted)", "usage": None}]


# -- the arm policies ----------------------------------------------------------
class Warmpool:
    """A: every body retained for the whole run."""

    name = "warmpool"

    def __init__(self, store: BodyStore, index) -> None:
        self.store = store
        self.retained: dict[str, str] = {}
        self.evicted: dict[str, str] = {}

    def retain(self, text: str, target) -> str:
        self.retained[text] = target.locator
        return "retained"

    def read(self, text: str, target):
        return self.store.get(target)


class NoBody:
    """D: the control. Bodies exist in the store; the host never resolves them."""

    name = "no-body"

    def __init__(self, store: BodyStore, index) -> None:
        self.store = store
        self.retained: dict[str, str] = {}
        self.evicted: dict[str, str] = {}

    def retain(self, *args, **kwargs) -> str:
        return "withheld"

    def read(self, text: str, target):
        raise LookupError("no-body control: this arm has no body-reading path")


class CapThree:
    """B: only the 3 most recent bodies are retained; older ones are gone."""

    name = "cap-3"

    def __init__(self, store: BodyStore, index) -> None:
        self.store = store
        self.retained: dict[str, str] = {}
        self.evicted: dict[str, str] = {}
        self.keep = RETENTION_KEPT

    def retain(self, text: str, target) -> str:
        self.retained[text] = target.locator
        self.retained = dict(list(self.retained.items())[-self.keep:])
        for gone in [t for t in self.evicted if t in self.retained]:
            self.evicted.pop(gone)
        return "retained"

    def evict_older_than(self, keep_texts: list[str]) -> list[str]:
        gone = [t for t in self.retained if t not in keep_texts]
        for text in gone:
            self.evicted[text] = self.retained.pop(text)
        return gone

    def read(self, text: str, target):
        if text in self.evicted:
            # The bytes are genuinely removed from this arm's warmpool.
            path = self.store.path_of(target)
            if path.is_file():
                path.unlink()
        return self.store.get(target)


class DestructiveCompaction:
    """C: old bodies replaced by a short digest. First 200 bytes, then a marker."""

    name = "destructive-compaction"

    def __init__(self, store: BodyStore, index) -> None:
        self.store = store
        self.retained: dict[str, str] = {}
        self.evicted: dict[str, str] = {}
        self.keep = RETENTION_KEPT

    def retain(self, text: str, target) -> str:
        self.retained[text] = target.locator
        self.retained = dict(list(self.retained.items())[-self.keep:])
        return "retained"

    def compact(self, texts: list[str]) -> list[dict]:
        """Replace each named body by its digest, in this arm's own warmpool."""
        done = []
        from ptr_engine import ResourceRef

        for text in texts:
            locator = self.retained.get(text)
            if locator is None:
                continue
            target = ResourceRef(scheme="artifact", locator=locator, hash=_hash_of(locator))
            body = self.store.get(target)
            head = body[:DIGEST_BYTES]
            digest = head + (
                f"\n[... body compacted: {len(body)} bytes retained, first "
                f"{DIGEST_BYTES} kept by policy ...]\n"
            ).encode("utf-8")
            self.store.put(digest)
            path = self.store.path_of(target)
            path.write_bytes(digest)  # DESTRUCTIVE: same locator, lossy bytes
            self.evicted[text] = locator
            self.retained.pop(text, None)
            done.append(
                {
                    "ref": text,
                    "original_bytes": len(body),
                    "digest_bytes": len(digest),
                    "original_sha256": hashlib.sha256(body).hexdigest(),
                    "digest_sha256": hashlib.sha256(digest).hexdigest(),
                    "lost_fact": (corpus.FACT_CODE.encode() in body and corpus.FACT_CODE.encode() not in digest),
                }
            )
        return done

    def read(self, text: str, target):
        return self.store.get(target)


def _hash_of(locator: str) -> str:
    return "sha256:" + Path(locator).stem


# -- one rep -------------------------------------------------------------------
def run_rep(arm: str, rep: int) -> dict:
    _SEQ["rep"] = rep
    _SEQ["arm"] = arm
    run_root = Path(tempfile.mkdtemp(prefix=f"ptr-quality-{arm}-r{rep}-"))
    items = corpus.material()
    store = BodyStore(run_root / "warmpool")
    revision = 1
    index = compile_turn(items, revision=revision, scope=SCOPE, block_size=BLOCK_SIZE, store=store)
    scope = Scope(name=SCOPE, index=index, block_size=BLOCK_SIZE)
    ledger = Ledger(run_root / "ledger.jsonl", block_size=BLOCK_SIZE)

    policies = {
        "A": Warmpool,
        "B": CapThree,
        "C": DestructiveCompaction,
        "D": NoBody,
    }
    policy = policies[arm](store, index)

    if rep == 0:
        write_row(
            {
                "row": "corpus",
                "arm": arm,
                "run_root": str(run_root),
                "index_sha256": index.index_sha256,
                "index_bytes": index.index_size,
                "index_text": index.index_text,
                "index_lines": len(index.lines),
                "body_bytes": sum(len(i["body"].encode()) for i in items),
                "leak_check": corpus.leak_check(items, index.index_text),
                "prereg_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
            }
        )

    conversation: list[dict] = [{"role": "system", "content": ""}]
    turns: list[dict] = []
    refusals: Counter = Counter()
    recent: list[str] = []          # the refs of the most recent turns, oldest first
    request_rows: list[dict] = []
    for turn_no, plan_refs, user_text in TURN_PLAN:
        # -- host side: resolve what this turn asks for ------------------------
        resolutions: list[dict] = []
        resolved_bodies: dict[Reference, bytes] = {}
        host_entries = plan_refs + (DISTRACTOR_REFS if turn_no == 4 else [])
        for text in host_entries:
            if arm == "D":
                resolutions.append(
                    {"ref": text, "outcome": "withheld", "code": None, "bytes": 0,
                     "error": "no-body control: the host does not resolve in this arm"}
                )
                continue
            ref = parse(text)
            try:
                target = engine_resolve(ref, scope, ledger)          # position
            except PtrError as error:
                resolutions.append({"ref": text, "outcome": "refused", "code": error.code,
                                    "bytes": 0, "error": str(error)[:500]})
                continue
            policy.retain(text, target)                              # content
            try:
                body = policy.read(text, target)                     # bytes
            except PtrError as error:                                # a refusal is a row
                resolutions.append({"ref": text, "outcome": "refused", "code": error.code,
                                    "bytes": 0, "error": str(error)[:500]})
                continue
            resolved_bodies[ref] = body
            resolutions.append({"ref": text, "outcome": "resolved", "code": None,
                                "locator": target.locator, "bytes": len(body),
                                "append_cost": append_cost(ref, BLOCK_SIZE)})
            recent.append(text)

        # Retention follows the same rule in B and C: the 3 most recent bodies stay
        # warm; older ones leave the warm set.  B drops the bytes, C replaces them
        # with a digest at the SAME locator (destructive, still resolvable).
        if arm in ("B", "C"):
            # Retention caps the WARM SET (what the session keeps live), so every
            # body older than the window is compacted -- including bodies the model
            # fetched within the same turn.
            older = [t for t in list(dict.fromkeys(recent)) if t not in recent[-RETENTION_KEPT:]]
            if arm == "B":
                policy.evict_older_than(recent[-RETENTION_KEPT:])
            else:
                for entry in policy.compact(older):
                    if entry["ref"] in [r["ref"] for r in resolutions]:
                        for row in resolutions:
                            if row["ref"] == entry["ref"]:
                                row["outcome"] = "compacted"
                                row["bytes"] = entry["digest_bytes"]
                                row["original_bytes"] = entry["original_bytes"]
                    write_row({"row": "compaction", "turn": turn_no, **entry})

        asked = user_text + (READ_ALL if turn_no == len(TURN_PLAN) and arm != "D" else "")
        body_text = (
            build_prompt(index, resolved_bodies, ledger) if resolved_bodies else index.index_text
        )
        # The system message is fixed at the head of the conversation and grows by
        # appending (index first, then each resolved body). Appending to it keeps one
        # live prefix; re-sending it as a later message is not a chat conversation.
        conversation[0]["content"] += "\n\n" + body_text
        conversation.append({"role": "user", "content": asked})

        # -- the request: prediction row first, then the request ---------------
        # ``prompt_tokens`` is the tokenizer's count of the rendered conversation with
        # the SAME ``chat_template_kwargs`` the request carries (thinking off) -- so it
        # is the render the endpoint serves and is comparable with the endpoint's own
        # ``usage.prompt_tokens``.  BILL-AUDIT measured the 2-token gap that appears
        # when this is counted without that kwarg.
        prompt_tokens = token_count(conversation)
        # V2 (defect 1).  ``L`` is the MEASURED APPEND ``P2 - P1``, never the prefix.
        # The audited line (runner.py:495) read ``L = prompt_tokens + FRAMING``, which
        # telescopes ``(P1 mod B) + L`` into ``billed = sum(P1)``.  Only the PRIME has no
        # previous turn to subtract against, so only it falls back to ``n_payload + 12``;
        # the path taken is written to every row as ``L_source``.
        previous_prompt_tokens = turns[-1]["prompt_tokens"] if turns else 0
        pre = billing_row(turn_no, prompt_tokens, previous_prompt_tokens)
        L, L_source, n_payload = pre["L"], pre["L_source"], pre["n_payload"]
        residue = pre["residue"]
        avalanche = pre["avalanche"]
        # The law's residue-0/1 branch is a ONE-BLOCK miss, not a whole-prefix avalanche
        # (BILL-AUDIT: server ``uncached = 64 + L`` at residue 0, ``1 + L`` at residue 1).
        # The column is kept only so the law stays comparable with its published form;
        # NO server number is ever taken from it.
        predicted_uncached = BLOCK_SIZE + L if residue == 0 else (residue + L)
        write_row(
            {
                "row": "prediction",
                "turn": turn_no,
                "P1": prompt_tokens,
                "P1_previous": previous_prompt_tokens,
                "residue": residue,
                "avalanche": avalanche,
                "L": L,
                "L_source": L_source,
                "n_payload": n_payload,
                "predicted_uncached": predicted_uncached,
                "law_note": "L = P2-P1 (delta); framing fallback on the prime only",
                "prediction_basis": "tokenizer_prompt, written before the request",
                "prompt_bytes": len(body_text.encode()),
            }
        )

        started = time.time()
        error_text = None
        text = ""
        usage: dict = {}

        def resolve_ref(raw: str):
            """The one model-visible tool: resolve a ref, keep it warm, read it."""
            if arm == "D":
                return None, "PTR_UNRESOLVED_REF"        # the control has no body path
            try:
                ref = parse(raw.strip())
            except PtrError as error:
                return None, error.code
            try:
                target = engine_resolve(ref, scope, ledger)
            except PtrError as error:
                return None, error.code
            key = raw.strip()
            policy.retain(key, target)
            # The retention rule applies to model-initiated fetches too: in B the
            # bytes of the 4th-oldest body are gone, in C they are replaced by a
            # digest at the same locator.
            if arm in ("B", "C"):
                window = [t for t in recent if t != key][-RETENTION_KEPT:]
                if arm == "B":
                    policy.evict_older_than(window)
                else:
                    policy.compact(
                        [t for t in policy.retained if t not in window and t != key]
                    )
            try:
                return policy.read(key, target).decode("utf-8", "replace"), None
            except PtrError as error:
                return None, error.code

        if turn_no == len(TURN_PLAN):
            tool_table = [FETCH_TOOL] if arm != "D" else None
            _SEQ["req_arm"] = arm
            try:
                fetched, exchanges = fetch_bodies(conversation, tool_table, resolve_ref)
                text = (exchanges[-1]["content"] or "").strip()
                usage = exchanges[-1]["usage"] or {}
                api_calls = exchanges[-1].get("api_calls")
                fetch_log = exchanges[:-1]
            except Exception as error:  # a failed request is a row, never a retry
                error_text = str(error)[:2000]
                fetched, fetch_log, api_calls = [], [], None
        else:
            fetched, fetch_log, api_calls = [], [], None
            try:
                response = chat(conversation)
                api_calls = 1
                text = (response["choices"][0]["message"].get("content") or "").strip()
                usage = response.get("usage") or {}
            except Exception as error:  # a failed request is a row, never a retry
                error_text = str(error)[:2000]
        elapsed = time.time() - started
        resolutions.extend(
            {"ref": f["ref"], "outcome": f["outcome"] + "_by_model",
             "code": f.get("code"), "bytes": f.get("bytes", 0), "origin": "fetch_tool"}
            for f in fetch_log
        )
        # V2 (defect 3): the refusal ledger, by code, model-initiated refusals included.
        turn_refusals = Counter(
            r["code"]
            for r in resolutions
            if r.get("code") and str(r.get("outcome", "")).startswith("refused")
        )
        refusals.update(turn_refusals)

        finish_reason = None
        if usage:
            finish_reason = "recorded"
        # -- the server's own accounting for this turn -------------------------
        # V2 (defect 2).  ``/v1/chat/completions`` reports
        # ``usage.prompt_tokens_details.cached_tokens`` and leaves the object NULL on a
        # cold request.  The audited runner read it here and then dropped it, so its
        # "measured" column was a recomputation from ``prompt_tokens``.  V2 persists the
        # raw value: null stays null with ``cached_reported: false``, never a plain 0.
        accounting = _server_accounting(usage)
        server_prompt_tokens = accounting["prompt_tokens"]
        cached_tokens_raw = accounting["cached_tokens"]
        cached_reported = accounting["cached_reported"]
        server_uncached = accounting["server_uncached"]
        # The per-turn bill is built only after the server has spoken (or stayed silent).
        bill = billing_row(
            turn_no,
            int(server_prompt_tokens or prompt_tokens),
            previous_prompt_tokens,
            usage,
        )
        request_row = {
                "row": "request",
                "turn": turn_no,
                "request_messages": len(conversation),
                "user_text": asked,
                "resolutions": resolutions,
                "resolved_count": sum(1 for r in resolutions if r["outcome"] in ("resolved", "compacted")),
                "compacted_count": sum(1 for r in resolutions if r["outcome"] == "compacted"),
                "refused_count": sum(1 for r in resolutions if r["outcome"].startswith("refused")),
                # V2 (defect 3): every refusal this turn, counted from the CODE that was
                # raised.  The audited filter (``== "refused"``) dropped each
                # model-initiated ``refused_by_model``, which is why the 33
                # PTR_STORE_MISS refusals existed only in prose.
                "refused_total": sum(turn_refusals.values()),
                "refused_by_code": dict(turn_refusals),
                "withheld_count": sum(1 for r in resolutions if r["outcome"] == "withheld"),
                "codes": sorted({r["code"] for r in resolutions if r.get("code")}),
                "prompt_tokens": server_prompt_tokens or prompt_tokens,
                "billed": bill["billed"],
                "billed_source": bill["billed_source"],
                "templated_prompt_tokens": prompt_tokens,
                "P1_tokenizer": prompt_tokens,
                "P1_previous": previous_prompt_tokens,
                "residue": residue,
                "avalanche": avalanche,
                "L": bill["L"],
                "L_source": bill["L_source"],
                "n_payload": bill["n_payload"],
                "predicted_uncached": predicted_uncached,
                # V2 (defect 2): the RAW field, persisted; null means "not reported".
                "cached_tokens": cached_tokens_raw,
                "cached_reported": cached_reported,
                "server_uncached": server_uncached,
                "server_keys": (
                    ["usage.prompt_tokens", "usage.prompt_tokens_details.cached_tokens"]
                    if cached_reported else ["usage.prompt_tokens"]
                ),
                "completion_tokens": usage.get("completion_tokens"),
                "reasoning_tokens": (usage.get("prompt_tokens_details") or {}).get("reasoning_tokens")
                if isinstance(usage.get("prompt_tokens_details"), dict) else usage.get("reasoning_tokens"),
                "answer_text": text,
                "answer_has_fact": EXPECTED_FACT in text,
                "answer_is_too_long": len(text) > 200,
                "error": error_text,
                "elapsed_s": round(elapsed, 3),
                "api_calls": api_calls,
                "retention_retained": list(policy.retained.keys()),
                "retention_evicted": list(policy.evicted.keys()),
        }
        write_row(request_row)
        request_rows.append(request_row)
        turns.append(
            {
                "turn": turn_no,
                "prompt_tokens": usage.get("prompt_tokens") or prompt_tokens,
                "P1_tokenizer": prompt_tokens,
                "P1_previous": previous_prompt_tokens,
                "L": bill["L"],
                "L_source": bill["L_source"],
                "n_payload": bill["n_payload"],
                "billed": bill["billed"],
                "billed_source": bill["billed_source"],
                "completion_tokens": usage.get("completion_tokens"),
                "cached_tokens": cached_tokens_raw,
                "cached_reported": cached_reported,
                "server_uncached": server_uncached,
                "resolved": sum(1 for r in resolutions if r["outcome"] in ("resolved", "compacted")),
                "refused": sum(turn_refusals.values()),
                "refused_by_code": dict(turn_refusals),
                "withheld": sum(1 for r in resolutions if r["outcome"] == "withheld"),
                "codes": sorted({r["code"] for r in resolutions if r.get("code")}),
                "answer": text,
                "has_fact": EXPECTED_FACT in text,
                "error": error_text,
            }
        )
        conversation.append({"role": "assistant", "content": text or "(no reply)"})

    # V2 (defect 4): the alignment guard runs BEFORE any aggregate is written, so a
    # turn whose bill is not the server's own reading fails THIS rep instead of being
    # averaged into a total.  The aborted in-place repair died on the sibling guard
    # (rerun-corrected.log:16); this one is reachable from tests, offline.
    assert_billing_alignment(request_rows, where=f"{arm} rep{rep}: ")

    final = turns[-1]
    billed = _billed(turns, request_rows)
    # V2 (defect 2): the measured column is a SUM OF READINGS.  A turn whose server
    # reported ``cached_tokens`` contributes ``prompt_tokens - cached_tokens``; a turn
    # whose server reported nothing contributes its whole prompt and is counted, not
    # silently priced.  Nothing here is recomputed from the prompt alone.
    measured_turns = [t for t in turns if t.get("billed_source") == "server"]
    measured_total = sum(int(t["billed"]) for t in turns)
    summary = {
        "row": "rep",
        "arm": arm,
        "arm_policy": policy.name,
        "turns": len(turns),
        "task_success": bool(final["has_fact"]),
        "final_answer": final["answer"],
        "expected_fact": EXPECTED_FACT,
        "resolved_total": sum(t["resolved"] for t in turns),
        # V2 (defect 3): refusals are counted from the PtrError codes actually raised.
        "refused_total": sum(refusals.values()),
        "refused_by_code": dict(refusals),
        "refusal_codes": sorted(refusals),
        "withheld_total": sum(t["withheld"] for t in turns),
        "codes": sorted({c for t in turns for c in t["codes"]}),
        # The law column.  NOT a server number -- see _billed's docstring.
        "billed_tokens": billed["billed"],
        "billed_tokens_source": "law_model",
        # The SERVER's accounting, read from the response bodies.
        "server_uncached_tokens": billed["server_uncached_reported"],
        "server_uncached_lower_bound": billed["server_uncached_lower_bound"],
        "server_cached_tokens": billed["server_cached_reported"],
        "server_null_turns": billed["server_null_turns"],
        "server_all_reported": billed["server_all_reported"],
        "billed_tokens_measured": measured_total,
        "billed_tokens_measured_source": "server_readings",
        "billed_tokens_measured_reported_turns": len(measured_turns),
        "billed_tokens_measured_null_turns": len(turns) - len(measured_turns),
        "per_turn": billed["per_turn"],
        "needed_refetch": any(t["resolved"] == 0 and t["refused"] > 0 for t in turns),
        "errors": [t["error"] for t in turns if t["error"]],
        "run_root": str(run_root),
        "turns_detail": turns,
    }
    write_row(summary)
    return summary


def _body_len(store: BodyStore, target) -> int:
    try:
        return len(store.get(target))
    except Exception:
        return 0


def _billed(turns: list[dict], request_rows: list[dict] | None = None, L_rule=None) -> dict:
    """``L_rule`` exists ONLY so ``tests/test_quality_billing.py`` can re-apply the
    shipped prefix rule and prove the guard fires; production never passes it."""
    """Billed tokens for one run — from the SERVER where it spoke, from the law only as
    a clearly-labelled secondary column.

    Law (`SPEC.md` §13, `LAW.md`): for a primed prefix of ``P1`` tokens receiving an
    append of ``L`` tokens at block size ``B = 64``,

        uncached = (P1 mod B) + L          unless P1 mod B in {0}
        uncached = B + L                   then (one block re-billed, NOT P1 + L)

    BILL-REPAIR (defect 2).  This function used to build ``per_turn`` by iterating
    ``turns[1:]`` and appending one entry per iteration, so the array started at turn 2
    and every entry sat one turn early relative to the request rows it claimed to
    describe.  Two further defects came with it: ``L`` was ``P1 + FRAMING`` (the whole
    prefix, when the append is ``P1[k] - P1[k-1]``), and the turn-1 element carried no
    ``P1`` key at all, so anything reading ``per_turn[i]["P1"]`` silently shifted.

    ``per_turn`` is now ONE ENTRY PER REQUEST ROW, in row order, indexed by turn.  When
    the caller passes the ``request_rows`` the run wrote, every entry is checked against
    the row it claims to bill: :func:`_assert_aligned` raises if the row's own
    ``prompt_tokens`` is not the ``P1`` billed in that slot.  A one-turn shift cannot
    recur silently -- it fails the run instead.

    Server totals are reported separately and are never derived from the law: a turn
    where the server reported no ``cached_tokens`` contributes ``prompt_tokens`` to
    ``server_uncached_lower_bound`` and is counted in ``server_null_turns``; nothing is
    invented for it.
    """
    if not turns:
        return {"billed": 0, "per_turn": [], "server_uncached_reported": 0,
                "server_uncached_lower_bound": 0, "server_cached_reported": 0,
                "server_null_turns": [], "server_all_reported": True}

    per_turn: list[dict] = []
    total = 0
    previous = 0
    for index, entry in enumerate(turns):
        P1 = entry["prompt_tokens"]
        # V2 (defect 1): the append comes from the path the row recorded -- "delta" is
        # P1 - P1_previous, "framing" is n_payload + 12 and is legal on the prime only.
        # ``L_rule`` remains for the shipped test that replays the prefix formula.
        source = entry.get("L_source")
        if L_rule is not None:
            L = L_rule(P1, previous, index)
        elif source == "framing":
            L = int(entry.get("n_payload") or 0) + FRAMING
        else:
            L = max(P1 - previous, 0)
        residue = P1 % BLOCK_SIZE
        uncached = (BLOCK_SIZE if residue == 0 else residue) + L
        total += uncached
        per_turn.append(
            {"turn": entry["turn"], "index": index, "P1": P1, "L": L,
             "L_source": source, "billed": entry.get("billed"),
             "billed_source": entry.get("billed_source"),
             "residue": residue, "avalanche": residue in (0, 1), "uncached": uncached,
             "requested_now": entry.get("resolved", 0) > 0 or entry.get("withheld", 0) > 0,
             "completion": entry.get("completion"),
             "cached_tokens": entry.get("cached_tokens"),
             "cached_reported": entry.get("cached_reported"),
             "server_uncached": entry.get("server_uncached")}
        )
        previous = P1

    if request_rows is not None:
        _assert_aligned(turns, per_turn, request_rows)

    reported = [t for t in turns if t.get("server_uncached") is not None]
    null_turns = [t["turn"] for t in turns if t.get("server_uncached") is None]
    return {
        "billed": total,                                       # the LAW column
        "per_turn": per_turn,
        "server_uncached_reported": sum(int(t["server_uncached"]) for t in reported),
        "server_uncached_lower_bound": sum(
            int(t["server_uncached"]) if t.get("server_uncached") is not None
            else int(t["prompt_tokens"]) for t in turns
        ),
        "server_cached_reported": sum(
            int(t["cached_tokens"]) for t in turns if t.get("cached_reported")
        ),
        "server_null_turns": null_turns,
        "server_all_reported": not null_turns,
    }


def _assert_aligned(turns: list[dict], per_turn: list[dict], request_rows: list[dict]) -> None:
    """Prove ``per_turn`` addresses the same turn as the request row it bills.

    THE GUARD FOR DEFECT 2.  Three independent checks; any failure raises, so a future
    off-by-one turns a silent wrong number into a failed run:

    1. cardinality -- one ``per_turn`` entry per request row, per turn;
    2. turn identity -- ``per_turn[i]["turn"] == request_rows[i]["turn"]``;
    3. value identity -- the row's own ``prompt_tokens`` IS the ``P1`` billed in slot
       ``i`` (and, when the row recorded one, the tokenizer's ``P1_tokenizer`` too).

    Check 3 is the one that catches a shift the first two miss: shifting the array by
    one keeps the length and the turn labels aligned with ``turns`` while billing turn
    ``k``'s append against turn ``k-1``'s prefix.
    """
    rows = [r for r in request_rows if r.get("row") == "request"]
    if not (len(rows) == len(turns) == len(per_turn)):
        raise AssertionError(
            f"per_turn misaligned: {len(per_turn)} entries for {len(turns)} turns "
            f"and {len(rows)} request rows"
        )
    for index, (turn, slot, row) in enumerate(zip(turns, per_turn, rows)):
        if slot["turn"] != row["turn"] or turn["turn"] != row["turn"]:
            raise AssertionError(
                f"per_turn[{'%d' % index}] is turn {slot['turn']}, the request row is turn "
                f"{row['turn']}, the summary is turn {turn['turn']}"
            )
        if slot["P1"] != row["prompt_tokens"]:
            raise AssertionError(
                f"per_turn['%d'] bills P1={slot['P1']} but the request row for turn "
                f"{row['turn']} recorded prompt_tokens={row['prompt_tokens']}"
            )
        if row.get("P1_tokenizer") is not None and slot["P1"] != row["P1_tokenizer"]:
            raise AssertionError(
                f"per_turn['%d'] bills P1={slot['P1']} but the row's own tokenizer count "
                f"was {row['P1_tokenizer']}"
            )


# -- the V2 instrument -----------------------------------------------------------
def _server_accounting(usage: dict | None) -> dict:
    """Read the server's per-turn billing fields -- never invent one.

    V2 (defect 2).  ``usage.prompt_tokens_details.cached_tokens`` is NULL on a cold
    request.  A plain ``0`` for that null would repeat the error that manufactured the
    "avalanche".  So: ``cached_tokens`` is ``None`` and ``cached_reported`` is False
    when the server did not speak, and ``server_uncached`` is computed only from a
    number the server actually reported (a REPORTED zero is a zero, not a null).
    """
    usage = usage or {}
    prompt = usage.get("prompt_tokens")
    details = usage.get("prompt_tokens_details")
    reported = isinstance(details, dict) and details.get("cached_tokens") is not None
    cached = details.get("cached_tokens") if reported else None
    uncached = None
    if reported and prompt is not None and cached is not None:
        uncached = int(prompt) - int(cached)
    return {
        "prompt_tokens": prompt,
        "cached_tokens": cached,
        "cached_reported": bool(reported),
        "server_uncached": uncached,
    }


def _l_source_consistent(row: dict) -> int:
    """The append term the row claims is NOT already inside the server's count.

    V2 (defect 1/4).  Zero on every row this instrument writes: the server's
    ``prompt_tokens - cached_tokens`` already prices the append, so a second term is
    exactly the double count the audited formula committed -- it folded the whole
    prefix in as ``L``.  A row may declare a non-zero term only through
    ``append_extra``, which the guard then holds it to.
    """
    return int(row.get("append_extra") or 0)


def billing_row(turn, prompt_tokens, previous_prompt_tokens=0, usage=None, *,
                block_size: int = BLOCK_SIZE, framing: int = FRAMING) -> dict:
    """One turn's billing fields, computed ONE way -- the V2 way.

    ``L`` is the append delta ``P2 - P1`` whenever a previous turn exists.  The PRIME
    (no previous prompt) is the only turn that cannot be a delta; its fallback is the
    framing model ``n_payload + 12`` with ``n_payload = P1 - 12`` (the prime's whole
    cold prompt).  ``L_source`` records which path ran, so no later reader has to infer
    it from the numbers.

    ``billed`` is a READING: ``prompt_tokens - cached_tokens`` when the server reported
    ``cached_tokens``, and ``prompt_tokens`` (everything, the upper bound) when it did
    not.  It is never ``residue + L`` and never ``billed = sum(prompt_tokens)``.
    """
    P1 = int(prompt_tokens)
    previous = int(previous_prompt_tokens or 0)
    if previous:
        L = P1 - previous
        if L < 0:
            raise AssertionError(
                f"turn {turn}: prompt shrank (P2={P1} < P1={previous}); a negative append "
                "is not a bill this instrument can price"
            )
        L_source, n_payload = "delta", None
    else:
        n_payload = max(P1 - framing, 0)
        L = n_payload + framing
        L_source = "framing"
    accounting = _server_accounting(usage)
    cached, reported = accounting["cached_tokens"], accounting["cached_reported"]
    server_uncached = accounting["server_uncached"]
    from_server = bool(reported and server_uncached is not None)
    residue = P1 % block_size
    return {
        "row": "request",
        "turn": turn,
        "P1": P1,
        "prompt_tokens": P1,
        "P1_previous": previous,
        "residue": residue,
        "avalanche": residue in (0, 1),
        "L": L,
        "L_source": L_source,
        "n_payload": n_payload,
        "predicted_uncached": (block_size if residue == 0 else residue) + L,
        "cached_tokens": cached,
        "cached_reported": reported,
        "server_uncached": server_uncached,
        "billed": server_uncached if from_server else P1,
        "billed_source": "server" if from_server else "server_lower_bound",
    }


def assert_billing_alignment(rows: list[dict], *, block_size: int = BLOCK_SIZE,
                             framing: int = FRAMING, where: str = "") -> None:
    """THE GUARD FOR DEFECTS 1-3 -- run BEFORE any aggregate is written.

    Per row (one per turn), the bill must satisfy

        billed == prompt_tokens - cached_tokens + L_source_consistent

    ``prompt_tokens - cached_tokens`` is the server's own uncached reading (a null
    ``cached_tokens`` reads as 0: nothing was reported cached, so the whole prompt is
    billed).  ``L_source_consistent`` is 0 for every row this instrument writes, and
    the recorded ``L`` must separately equal the value its own ``L_source`` implies --
    the delta ``P1 - P1_previous``, or ``n_payload + 12`` on the prime only.

    Any failure raises with the row index and both counts.  The aborted in-place
    repair died on the sibling of this check (``rerun-corrected.log:16``:
    ``per_turn['0'] bills P1=18794 but the row's own tokenizer count was 10902``);
    this one is importable, so a test can drive it without a server.
    """
    for index, row in enumerate(rows):
        if row.get("row") not in (None, "request"):
            raise AssertionError(f"{where}row {index}: not a request row ({row.get('row')!r})")
        if row.get("prompt_tokens") is None or row.get("billed") is None:
            raise AssertionError(
                f"{where}row {index} (turn {row.get('turn')}): no billed/prompt_tokens -- "
                "a bill that is not a reading cannot be aligned"
            )
        P1 = int(row["prompt_tokens"])
        previous = int(row.get("P1_previous") or 0)
        cached_raw = row.get("cached_tokens")
        cached = 0 if cached_raw is None else int(cached_raw)
        append_term = _l_source_consistent(row)
        expected_billed = P1 - cached + append_term
        if int(row["billed"]) != expected_billed:
            raise AssertionError(
                f"{where}row {index} (turn {row.get('turn')}): billed={row['billed']} but "
                f"prompt_tokens - cached_tokens + L_source_consistent = {P1} - {cached} + "
                f"{append_term} = {expected_billed} [L={row.get('L')}, "
                f"L_source={row.get('L_source')!r}, P1_previous={previous}, "
                f"cached_reported={row.get('cached_reported')}]"
            )
        source = row.get("L_source")
        if source == "delta":
            if previous <= 0:
                raise AssertionError(
                    f"{where}row {index} (turn {row.get('turn')}): L_source='delta' with no "
                    f"previous prompt (P1_previous={previous})"
                )
            implied = P1 - previous
        elif source == "framing":
            if previous:
                raise AssertionError(
                    f"{where}row {index} (turn {row.get('turn')}): L_source='framing' on a "
                    f"non-prime row (P1_previous={previous}) -- the framing fallback is "
                    "legal only when no previous turn exists"
                )
            implied = int(row.get("n_payload") or 0) + framing
        else:
            raise AssertionError(
                f"{where}row {index} (turn {row.get('turn')}): L_source={source!r}, expected "
                "'delta' or 'framing'"
            )
        if int(row["L"]) != implied:
            raise AssertionError(
                f"{where}row {index} (turn {row.get('turn')}): L={row['L']} but "
                f"L_source={source!r} implies L={implied} (prompt_tokens={P1}, "
                f"P1_previous={previous}, n_payload={row.get('n_payload')})"
            )
    return None


# -- main ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arms", default="A,B,C,D")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--fresh", action="store_true", help="truncate rows.jsonl first")
    args = parser.parse_args(argv)
    if args.fresh and ROWS.exists():
        ROWS.unlink()
    results = []
    for arm in [a.strip() for a in args.arms.split(",") if a.strip()]:
        if arm not in ("A", "B", "C", "D"):
            raise SystemExit(f"unknown arm {arm!r}")
        for rep in range(args.reps):
            summary = run_rep(arm, rep)
            results.append(summary)
            print(
                f"{arm} rep{rep}: success={summary['task_success']} "
                f"answer={summary['final_answer'][:40]!r} resolved={summary['resolved_total']} "
                f"refused={summary['refused_total']} withheld={summary['withheld_total']} "
                f"codes={summary['codes']} server_uncached={summary['server_uncached_tokens']} "
                f"null_turns={summary['server_null_turns']} law={summary['billed_tokens']}",
                flush=True,
            )
            if summary["errors"]:
                for err in summary["errors"]:
                    print(f"   ERROR {err[:300]}", flush=True)
    print(json.dumps({"reps": len(results)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
