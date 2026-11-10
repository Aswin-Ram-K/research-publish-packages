"""Renderers for context arms A, B, C."""
# format-contract: question print contract appended per turn

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

# Import canonical/store with package-or-path fallback.
try:
    from .canonical import dumps as _cdumps, digest as _cdigest  # type: ignore
    from .store import BodyStore as _BodyStore, MissingBody as _MissingBody  # type: ignore
except Exception:  # pragma: no cover - path-based import
    _here = Path(__file__).resolve().parent
    if str(_here) not in sys.path:
        sys.path.insert(0, str(_here))
    from canonical import dumps as _cdumps, digest as _cdigest  # type: ignore
    from store import BodyStore as _BodyStore, MissingBody as _MissingBody  # type: ignore


def dumps(obj: Any) -> bytes:
    return _cdumps(obj)


def digest_bytes(data: bytes) -> str:
    return _cdigest(data)


LAST_BUILD_METADATA: dict[str, Any] = {}


# ---------- helpers ----------
def _as_str(x: Any) -> str:
    if x is None:
        return ""
    return x if isinstance(x, str) else str(x)


def _src_digest(src: Any) -> str:
    if not isinstance(src, dict):
        return ""
    if "sha256" in src and src.get("sha256") is not None:
        d = str(src["sha256"])
    elif "digest" in src and src.get("digest") is not None:
        d = str(src["digest"])
    else:
        return ""
    if d.lower().startswith("sha256:"):
        d = d[len("sha256:"):]
    return d


def _ref_from_src(src: Any) -> dict[str, str]:
    if not isinstance(src, dict):
        return {"path": "", "pointer": "", "digest": ""}
    return {
        "path": _as_str(src.get("path", src.get("id", ""))),
        "pointer": _as_str(src.get("pointer", "")),
        "digest": _src_digest(src),
    }


def _ref_from_obj(r: Any) -> dict[str, str]:
    if not isinstance(r, dict):
        return {"path": "", "pointer": "", "digest": ""}
    if "sha256" in r or "digest" in r:
        d = _src_digest(r)
    else:
        d = _as_str(r.get("digest", ""))
        if d.lower().startswith("sha256:"):
            d = d[len("sha256:"):]
    return {
        "path": _as_str(r.get("path", r.get("id", ""))),
        "pointer": _as_str(r.get("pointer", "")),
        "digest": d,
    }


def _instruction_of_turn(t: Any) -> str:
    if not isinstance(t, dict):
        return ""
    for k in ("instruction", "question", "text", "prompt"):
        if k in t and t.get(k) is not None:
            return _as_str(t[k])
    return ""


def _kind_of_turn(t: Any, default: str = "work") -> str:
    if isinstance(t, dict) and t.get("kind") is not None:
        return _as_str(t["kind"])
    return default


def _find_turn(fixture: dict, turn: Any) -> dict | None:
    try:
        ti = int(turn)
    except (TypeError, ValueError):
        return None
    for t in (fixture or {}).get("turns", []) or []:
        if isinstance(t, dict):
            try:
                if int(t.get("turn", -1)) == ti:
                    return t
            except (TypeError, ValueError):
                continue
    turns = (fixture or {}).get("turns", []) or []
    if 1 <= ti <= len(turns):
        return turns[ti - 1]
    return None


def _current_instruction(fixture: dict, turn: Any) -> str:
    t = _find_turn(fixture, turn)
    if t is not None:
        return _instruction_of_turn(t)
    # fallback: last turn
    turns = (fixture or {}).get("turns", []) or []
    if turns:
        return _instruction_of_turn(turns[-1])
    return ""


def _resolve_K(fixture: dict, K: int | None) -> int:
    if K is not None:
        try:
            return int(K)
        except (TypeError, ValueError):
            pass
    for key in ("mask_k", "K", "mask_turns", "observation_mask_k", "k"):
        v = (fixture or {}).get(key)
        if v is not None:
            try:
                return int(v)
            except (TypeError, ValueError):
                continue
    v = os.environ.get("ARMS_MASK_K")
    if v is not None:
        try:
            return int(v)
        except (TypeError, ValueError):
            pass
    return 12


def _hist_turn(h: dict) -> int:
    try:
        return int(h.get("turn", 0))
    except (TypeError, ValueError):
        return 0


def _hist_instruction(h: dict, fixture: dict) -> str:
    for k in ("instruction", "question", "text", "prompt"):
        if k in h and h.get(k) is not None:
            return _as_str(h[k])
    t = _find_turn(fixture, h.get("turn"))
    if t is not None:
        return _instruction_of_turn(t)
    return ""


def _hist_answer(h: dict) -> str:
    for k in ("answer", "produced_answer", "produced", "response", "assistant", "output"):
        if k in h and h.get(k) is not None:
            return _as_str(h[k])
    return ""


def _hist_kind(h: dict, fixture: dict) -> str:
    if isinstance(h, dict) and h.get("kind") is not None:
        return _as_str(h["kind"])
    t = _find_turn(fixture, h.get("turn"))
    if t is not None:
        k = _kind_of_turn(t)
        if k:
            return k
    return "work"


def _hist_claim(h: dict) -> str:
    if isinstance(h, dict) and h.get("claim") is not None:
        c = _as_str(h["claim"])
    else:
        c = _hist_answer(h)
    return c[:240]


def _hist_refs(h: dict, fixture: dict) -> list[dict]:
    if isinstance(h, dict) and h.get("refs") is not None:
        raw = h["refs"]
    else:
        raw = [_ref_from_src(s) for s in (fixture or {}).get("sources", []) or []]
    out = []
    for r in (raw or []):
        out.append(_ref_from_obj(r))
    return out


def _hist_artifact_digest(h: dict) -> str:
    for k in ("produced_artifact_digest", "artifact_digest", "artifact"):
        if isinstance(h, dict) and h.get(k) is not None:
            v = h[k]
            if isinstance(v, str):
                d = v
                if d.lower().startswith("sha256:"):
                    d = d[len("sha256:"):]
                return d
            return _as_str(v)
    ans = _hist_answer(h)
    return _cdigest(ans.encode("utf-8"))


def _hist_notes(h: dict) -> str:
    if not isinstance(h, dict):
        return ""
    v = h.get("notes", "")
    if isinstance(v, (list, tuple, dict)):
        return _as_str(_cdumps(v).decode("utf-8"))
    return _as_str(v)


CAPABILITY_BLOCK = (
    "You have no tools and cannot read files.\n"
    "The grader will execute your reply inside the directory that contains the pinned files, "
    "whose paths are listed in the manifest.\n"
    "Reply with exactly one fenced ```python block that prints the requested values.\n"
    "Do not emit <tool_call>, and do not ask to read anything.\n"
    "The artifact will be executed with the seeded paths present."
)


def _preamble(fixture: dict) -> str:
    lines = []
    lines.append(CAPABILITY_BLOCK)
    lines.append("OBJECTIVE: " + _as_str((fixture or {}).get("objective", "")))
    lines.append("SOURCES:")
    DUVAL_PREFIX = "/home/zer0null/Duval/"
    for s in (fixture or {}).get("sources", []) or []:
        raw_path = _as_str(s.get("path", s.get("id", "")))
        if raw_path.startswith(DUVAL_PREFIX):
            rel_path = raw_path[len(DUVAL_PREFIX):]
        else:
            rel_path = raw_path
        lines.append(
            f"- path={rel_path} "
            f"pointer={_as_str(s.get('pointer', ''))} "
            f"digest={_src_digest(s)} "
            f"origin: {raw_path} (not for opening)"
        )
    lines.append(
        "The artifact runs with the seeded root as its working directory; "
        "absolute paths will not exist there; open files by the relative paths listed."
    )
    acc = (fixture or {}).get("acceptance", {}) or {}
    lines.append("ACCEPTANCE CHECKS:")
    for c in acc.get("checks", []) or []:
        desc = c.get("description", c.get("expected", ""))
        lines.append(f"- {c.get('id', '')}: {_as_str(desc)}")
    lines.append("NEGATIVE CONSTRAINTS:")
    for n in acc.get("negative_constraints", []) or []:
        lines.append(f"- {n.get('id', '')}: {_as_str(n.get('prose', ''))}")
    if acc.get("rule"):
        lines.append("RULE: " + _as_str(acc["rule"]))
    return "\n".join(lines)


def _record_for(h: dict, fixture: dict) -> dict:
    return {
        "kind": _hist_kind(h, fixture),
        "turn": _hist_turn(h),
        "instruction": _hist_instruction(h, fixture),
        "claim": _hist_claim(h),
        "refs": _hist_refs(h, fixture),
        "produced_artifact_digest": _hist_artifact_digest(h),
        "notes": _hist_notes(h),
    }


def _canonical_messages(messages: list[dict]) -> bytes:
    return dumps(messages)


def build_messages(
    arm: str,
    fixture: dict,
    history: list[dict],
    turn: int,
    K: int | None = None,
    return_metadata: bool = False,
):
    global LAST_BUILD_METADATA
    arm_u = str(arm).upper()
    fixture = fixture or {}
    history = list(history or [])
    hist = sorted(history, key=_hist_turn)
    k = _resolve_K(fixture, K)

    preamble = _preamble(fixture)
    messages: list[dict] = [{"role": "system", "content": preamble}]

    meta = {
        "arm": arm_u,
        "turn": int(turn) if _is_int(turn) else turn,
        "masked_turns": [],
        "replaced_bytes": 0,
        "divergence_turn": None,
    }

    if arm_u == "A":
        for h in hist:
            messages.append({"role": "user", "content": _hist_instruction(h, fixture)})
            messages.append({"role": "assistant", "content": _hist_answer(h)})
        messages.append({"role": "user", "content": _current_instruction(fixture, turn)})

    elif arm_u == "B":
        for h in hist:
            rec = _record_for(h, fixture)
            messages.append({"role": "user", "content": dumps(rec).decode("utf-8")})
        messages.append({"role": "user", "content": _current_instruction(fixture, turn)})

    elif arm_u == "C":
        # Determine masked set: keep last K completed turns unmasked.
        n = len(hist)
        mask_count = max(0, n - k + 1) if k >= 0 else 0
        masked_indices = set(range(0, mask_count))
        masked_turns = []
        replaced_bytes = 0
        divergence_turn = None
        for idx, h in enumerate(hist):
            if idx in masked_indices:
                full_rec = _record_for(h, fixture)
                full_bytes = dumps(full_rec)
                replaced_bytes += len(full_bytes)
                masked_turns.append(_hist_turn(h))
                if divergence_turn is None:
                    divergence_turn = _hist_turn(h)
                ref_rec = {
                    "kind": "ref",
                    "turn": _hist_turn(h),
                    "digest": _hist_artifact_digest(h),
                    "note": "masked: observation body replaced by reference",
                }
                messages.append({"role": "user", "content": dumps(ref_rec).decode("utf-8")})
            else:
                rec = _record_for(h, fixture)
                messages.append({"role": "user", "content": dumps(rec).decode("utf-8")})
        messages.append({"role": "user", "content": _current_instruction(fixture, turn)})
        meta["masked_turns"] = masked_turns
        meta["replaced_bytes"] = replaced_bytes
        meta["divergence_turn"] = divergence_turn

    else:
        raise ValueError(f"unknown arm {arm!r}")

    meta["arm"] = arm_u
    try:
        meta["turn"] = int(turn)
    except (TypeError, ValueError):
        pass
    LAST_BUILD_METADATA = meta

    if return_metadata:
        return messages, meta
    return messages


def _is_int(x: Any) -> bool:
    try:
        int(x)
        return True
    except (TypeError, ValueError):
        return False


def build_metadata(arm, fixture, history, turn, K=None):
    _, meta = build_messages(arm, fixture, history, turn, K=K, return_metadata=True)
    return meta


__all__ = ["build_messages", "build_metadata", "LAST_BUILD_METADATA", "dumps", "digest_bytes"]
