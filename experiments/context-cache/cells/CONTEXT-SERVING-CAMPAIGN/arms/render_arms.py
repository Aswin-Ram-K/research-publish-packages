"""Renderers for context arms A, B, C, D over a cs.task/1 trajectory.

All four arms present identical total task information at the decision point:
every observation body is stored content-addressed in the BodyStore, and the
final question text is identical.  What differs is stability (prefix reuse).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

# Import canonical/store with package-or-path fallback.
try:
    from .canonical import dumps as _cdumps, digest as _cdigest  # type: ignore
    from .store import BodyStore as _BodyStore  # type: ignore
except Exception:  # pragma: no cover - path-based import
    _here = Path(__file__).resolve().parent
    if str(_here) not in sys.path:
        sys.path.insert(0, str(_here))
    from canonical import dumps as _cdumps, digest as _cdigest  # type: ignore
    from store import BodyStore as _BodyStore  # type: ignore

RENDERER_VERSION = "cs.arms/1"
DEFAULT_MASK_AFTER = 6


def dumps(obj: Any) -> bytes:
    return _cdumps(obj)


def digest_bytes(data) -> str:
    return _cdigest(data)


# ---------- helpers ----------

def _as_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (dict, list, tuple)):
        try:
            return _cdumps(x).decode("utf-8")
        except Exception:
            return str(x)
    return str(x)


def _body_text(turn: Any) -> str:
    if not isinstance(turn, dict):
        return _as_str(turn)
    q = _question_text(turn)
    obs = ""
    for key in ("observation", "body", "content", "notes"):
        if key in turn and turn.get(key) is not None:
            v = turn[key]
            if isinstance(v, (dict, list, tuple)):
                obs = _cdumps(v).decode("utf-8")
            else:
                obs = _as_str(v)
            break
    if not obs:
        ev = turn.get("event")
        if isinstance(ev, dict):
            # cs.task/1: event.observation holds the text
            for key in ("observation", "text", "content", "body"):
                if key in ev and ev.get(key) is not None:
                    v = ev[key]
                    if isinstance(v, (dict, list, tuple)):
                        obs = _cdumps(v).decode("utf-8")
                    else:
                        obs = _as_str(v)
                    break
            if not obs:
                obs = _cdumps(ev).decode("utf-8")
    if not obs and "event" in turn and turn.get("event") is not None and not isinstance(turn.get("event"), dict):
        obs = _as_str(turn.get("event"))
    if q and obs and q not in obs:
        return q + "\n" + obs
    if q and not obs:
        return q
    return obs if obs else q


def _question_text(turn: Any) -> str:
    if not isinstance(turn, dict):
        return ""
    for key in ("question", "instruction", "prompt", "query", "text"):
        if key in turn and turn.get(key) is not None:
            return _as_str(turn[key])
    return ""


def _turn_n(turn: Any, fallback: int) -> int:
    if isinstance(turn, dict):
        for key in ("n", "turn", "turn_n", "index"):
            if key in turn and turn.get(key) is not None:
                try:
                    return int(turn[key])
                except (TypeError, ValueError):
                    pass
    try:
        return int(turn)
    except (TypeError, ValueError):
        return fallback


def _task_preamble(task: Any) -> str:
    if not isinstance(task, dict):
        return "TASK"
    lines = []
    tid = task.get("task_id") or task.get("id") or "task"
    lines.append(f"TASK: {tid}")
    obj = task.get("objective") or task.get("goal") or ""
    if obj:
        lines.append(f"OBJECTIVE: {_as_str(obj)}")
    # sources
    for s in task.get("sources", []) or []:
        if isinstance(s, dict):
            lines.append(f"SOURCE: {_as_str(s.get('path', s.get('id', '')))} digest={_src_digest(s)}")
    acc = task.get("acceptance") or {}
    if isinstance(acc, dict):
        for c in acc.get("checks", []) or []:
            lines.append(f"CHECK: {_as_str(c.get('id', ''))}: {_as_str(c.get('description', c.get('expected', '')))}")
    lines.append(
        "Some earlier observations may appear only as a `#body:<digest>` reference "
        "with a structural gist. If you need the exact bytes of a referenced body, "
        "reply with exactly one line `GET <digest>` and nothing else. The body will "
        "be supplied in the next message and you may then answer. At most one such "
        "request per turn."
    )
    lines.append(
        "Answer format: end your reply with a single line of the form key=value, "
        "using exactly the key names the question names. Do not add prefixes, "
        "bullets, or explanation on that line. Tokens such as `</think>`, "
        "`Here is`, or markdown formatting before it are ignored; only the final "
        "key=value line is read."
    )
    return "\n".join(lines)


def _src_digest(src: Any) -> str:
    if not isinstance(src, dict):
        return ""
    for key in ("sha256", "digest"):
        if key in src and src.get(key) is not None:
            d = str(src[key])
            if d.lower().startswith("sha256:"):
                d = d[len("sha256:"):]
            return d
    return ""


def _resolve_mask_after(task: Any, mask_after: Optional[int]) -> int:
    if mask_after is not None:
        try:
            return int(mask_after)
        except (TypeError, ValueError):
            pass
    if isinstance(task, dict):
        for key in ("mask_after", "mask_k", "K", "mask_turns", "k"):
            v = task.get(key)
            if v is not None:
                try:
                    return int(v)
                except (TypeError, ValueError):
                    continue
    v = os.environ.get("ARMS_MASK_AFTER")
    if v is not None:
        try:
            return int(v)
        except (TypeError, ValueError):
            pass
    return DEFAULT_MASK_AFTER


import json as _json

def _gist(turn_n: int, body: str) -> str:
    b = body.encode("utf-8")
    return _json.dumps(
        {
            "turn": int(turn_n),
            "kind": "observation",
            "bytes": len(b),
            "sha256_8": hashlib.sha256(b).hexdigest()[:8],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _default_store(store):
    if store is None:
        return _BodyStore()
    return store


def _ensure_body(store, text: str) -> str:
    return store.put(text.encode("utf-8"))


def _ref_token(digest: str) -> str:
    return f"#body:{digest}"


# ---------- rendering ----------

def _history_turns(task, history):
    # normalise history to list of turn dicts
    out = []
    for i, h in enumerate(history or []):
        if isinstance(h, dict):
            out.append(h)
        else:
            out.append({"turn": i + 1, "observation": _as_str(h)})
    return out


def render_messages(
    arm: str,
    task: Any,
    history: list,
    turn: Any,
    *,
    store=None,
    mask_after=None,
    salt: str = None,
    return_metadata: bool = False,
):
    arm_u = str(arm).upper()
    if arm_u not in ("A", "B", "C", "D"):
        raise ValueError(f"unknown arm {arm!r}")
    store = _default_store(store)
    hist = _history_turns(task, history)
    k = _resolve_mask_after(task, mask_after)
    n = len(hist)
    # number of turns to mask in C/D: mask older beyond k
    if n <= k:
        mask_count = 0
    else:
        mask_count = n - k
    masked_indices = set(range(0, mask_count))

    preamble = _task_preamble(task)
    if salt is not None:
        preamble = preamble + "\nsession=" + str(salt)
    preamble = preamble + "\nARM: " + arm_u
    messages: list[dict] = [{"role": "system", "content": preamble}]

    meta = {
        "arm": arm_u,
        "turn": _turn_n(turn, n + 1),
        "masked_turns": [],
        "body_refs": 0,
        "digests": [],
        "current_question": "",
    }

    # track seen digests for B "first appearance inline"
    seen_digests: set[str] = set()

    all_digests: list[str] = []

    if arm_u == "A":
        for h in hist:
            body = _body_text(h)
            d = _ensure_body(store, body)
            all_digests.append(d)
            messages.append({"role": "user", "content": body})
            ans = _as_str(h.get("answer") or h.get("claim") or h.get("produced") or "")
            if ans:
                messages.append({"role": "assistant", "content": ans})
        # current question
        tq = _question_text(turn if isinstance(turn, dict) else {"question": turn})
        if not tq:
            tq = _question_text(_find_task_turn(task, turn))
        meta["current_question"] = tq
        all_digests.append(_ensure_body(store, _body_text(turn if isinstance(turn, dict) else {"question": tq})))
        messages.append({"role": "user", "content": tq})

    elif arm_u == "B":
        for h in hist:
            body = _body_text(h)
            d = _ensure_body(store, body)
            all_digests.append(d)
            first = d not in seen_digests
            seen_digests.add(d)
            rec = {
                "kind": "event",
                "turn": _turn_n(h, 0),
                "ref": _ref_token(d),
                "digest": d,
                "question": _question_text(h),
            }
            if first:
                rec["body"] = body
            else:
                rec["body_ref"] = _ref_token(d)
            content = dumps(rec).decode("utf-8")
            # ensure ref token present
            if _ref_token(d) not in content:
                content = content + "\n" + _ref_token(d)
            messages.append({"role": "user", "content": content})
            ans = _as_str(h.get("answer") or h.get("claim") or "")
            if ans:
                messages.append({"role": "assistant", "content": ans})
        tq = _question_text(turn if isinstance(turn, dict) else {})
        if not tq:
            tq = _question_text(_find_task_turn(task, turn))
        meta["current_question"] = tq
        cur_body = _body_text(turn if isinstance(turn, dict) else {"question": tq})
        cur_d = _ensure_body(store, cur_body)
        all_digests.append(cur_d)
        first = cur_d not in seen_digests
        seen_digests.add(cur_d)
        rec = {"kind": "event", "turn": _turn_n(turn, n + 1), "ref": _ref_token(cur_d), "digest": cur_d, "question": tq}
        if first:
            rec["body"] = cur_body
        else:
            rec["body_ref"] = _ref_token(cur_d)
        content = dumps(rec).decode("utf-8")
        if _ref_token(cur_d) not in content:
            content = content + "\n" + _ref_token(cur_d)
        messages.append({"role": "user", "content": content})

    elif arm_u == "C":
        masked_turns = []
        for idx, h in enumerate(hist):
            body = _body_text(h)
            d = _ensure_body(store, body)
            all_digests.append(d)
            if idx in masked_indices:
                masked_turns.append(_turn_n(h, idx + 1))
                rec = {
                    "kind": "ref",
                    "turn": _turn_n(h, idx + 1),
                    "ref": _ref_token(d),
                    "digest": d,
                    "gist": _gist(_turn_n(h, idx + 1), body),
                }
                content = dumps(rec).decode("utf-8")
                if _ref_token(d) not in content:
                    content = content + "\n" + _ref_token(d)
                messages.append({"role": "user", "content": content})
            else:
                rec = {
                    "kind": "event",
                    "turn": _turn_n(h, idx + 1),
                    "ref": _ref_token(d),
                    "digest": d,
                    "body": body,
                }
                messages.append({"role": "user", "content": dumps(rec).decode("utf-8")})
        meta["masked_turns"] = masked_turns
        tq = _question_text(turn if isinstance(turn, dict) else {})
        if not tq:
            tq = _question_text(_find_task_turn(task, turn))
        meta["current_question"] = tq
        all_digests.append(_ensure_body(store, _body_text(turn if isinstance(turn, dict) else {"question": tq})))
        messages.append({"role": "user", "content": tq})

    elif arm_u == "D":
        # bounded summary of older turns + raw bodies recoverable
        old_digests = []
        recent_start = mask_count
        # summary message for masked older turns
        if mask_count > 0:
            summary_lines = ["SUMMARY of older turns:"]
            for idx in range(0, mask_count):
                h = hist[idx]
                body = _body_text(h)
                d = _ensure_body(store, body)
                all_digests.append(d)
                old_digests.append(d)
                summary_lines.append(f"- turn {_turn_n(h, idx+1)}: {_gist(_turn_n(h, idx+1), body)} {_ref_token(d)}")
            summary_msg = "\n".join(summary_lines)
            messages.append({"role": "user", "content": summary_msg})
        for idx in range(recent_start, n):
            h = hist[idx]
            body = _body_text(h)
            d = _ensure_body(store, body)
            all_digests.append(d)
            rec = {
                "kind": "event",
                "turn": _turn_n(h, idx + 1),
                "ref": _ref_token(d),
                "digest": d,
                "body": body,
            }
            messages.append({"role": "user", "content": dumps(rec).decode("utf-8")})
        tq = _question_text(turn if isinstance(turn, dict) else {})
        if not tq:
            tq = _question_text(_find_task_turn(task, turn))
        meta["current_question"] = tq
        all_digests.append(_ensure_body(store, _body_text(turn if isinstance(turn, dict) else {"question": tq})))
        messages.append({"role": "user", "content": tq})

    # count body refs in rendered text
    full_text = "\n".join(m["content"] for m in messages)
    meta["body_refs"] = len(re.findall(r"#body:[0-9a-f]{64}", full_text))
    meta["digests"] = list(dict.fromkeys(all_digests))
    meta["turn"] = _turn_n(turn, n + 1) if not isinstance(turn, dict) else _turn_n(turn, n + 1)

    # ensure all digests recorded (dedup)
    # also store all bodies (already done)

    if return_metadata:
        return messages, meta
    return messages


def _find_task_turn(task, turn):
    if not isinstance(task, dict):
        return None
    turns = task.get("turns", []) or []
    ti = None
    try:
        ti = int(turn) if not isinstance(turn, dict) else int(turn.get("n", turn.get("turn", 0)))
    except (TypeError, ValueError):
        ti = None
    for t in turns:
        if isinstance(t, dict):
            try:
                if ti is not None and int(t.get("n", t.get("turn", -1))) == ti:
                    return t
            except (TypeError, ValueError):
                pass
    if isinstance(turn, dict):
        return turn
    return None


def build_messages(arm, task, history, turn, *, store=None, mask_after=None, salt=None, return_metadata=False):
    return render_messages(arm, task, history, turn, store=store, mask_after=mask_after, salt=salt, return_metadata=return_metadata)


def render_text(arm, task, history, turn, *, store=None, mask_after=None, salt=None) -> str:
    msgs = render_messages(arm, task, history, turn, store=store, mask_after=mask_after, salt=salt, return_metadata=False)
    return "\n".join(m["content"] for m in msgs)


def build_metadata(arm, task, history, turn, *, store=None, mask_after=None, salt=None):
    _, meta = render_messages(arm, task, history, turn, store=store, mask_after=mask_after, salt=salt, return_metadata=True)
    return meta


def extract_body_refs(text: str):
    return re.findall(r"#body:[0-9a-f]{64}", text)


def renderer_sha256(arm=None) -> str:
    src = Path(__file__).read_bytes()
    payload = src + RENDERER_VERSION.encode("utf-8")
    if arm is not None:
        payload += str(arm).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


import re as _re

_GET_RE = _re.compile(r"^GET\s+([0-9a-f]{64})\s*$", _re.MULTILINE)


def resolve_requests(output: str, store=None) -> list[str]:
    """Parse `GET <digest>` requests from a model output.

    Validates 64-hex and presence in the store; raises BodyMissing/DigestMismatch
    on unknown or mismatched digests. Never silently satisfies.
    """
    store = _default_store(store)
    digests = []
    for line in (output or "").splitlines():
        line = line.strip()
        m = _re.fullmatch(r"GET\s+([0-9a-fA-F]{64})", line)
        if not m:
            # ignore non-request lines
            continue
        d = m.group(1).lower()
        # validate presence (raises BodyMissing/DigestMismatch if bad)
        store.get(d)
        digests.append(d)
    # de-dup preserving order
    seen = set()
    out = []
    for d in digests:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def recovery_message(digest: str, store=None) -> dict:
    """Return the message supplying the verified body for digest."""
    store = _default_store(store)
    data = store.get(digest)  # raises BodyMissing/DigestMismatch
    return {"role": "user", "content": data.decode("utf-8"), "digest": digest}


# back-compat alias for historical tests
LAST_BUILD_METADATA: dict = {}


__all__ = [
    "build_messages",
    "render_text",
    "build_metadata",
    "extract_body_refs",
    "resolve_requests",
    "recovery_message",
    "renderer_sha256",
    "RENDERER_VERSION",
    "DEFAULT_MASK_AFTER",
    "dumps",
    "digest_bytes",
]
