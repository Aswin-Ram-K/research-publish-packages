"""OpenAI-style fetch tool wrapping the pointer table."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Mapping, Optional, Tuple
from .pointer_table import FetchResult, PointerEntry, build_table, fetch

FETCH_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "fetch",
        "description": (
            "Retrieve a masked body by reference. Ranges are byte offsets into "
            "the stored body."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Pointer reference."},
                "range": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "integer"},
                        "end": {"type": "integer"},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
            "required": ["ref"],
            "additionalProperties": False,
        },
    },
}


def _coerce_range(raw: Any) -> Optional[Tuple[int, int]]:
    if not isinstance(raw, dict):
        return None
    if "start" not in raw and "end" not in raw:
        return None
    start = raw.get("start", 0)
    end = raw.get("end")
    try:
        start = int(start)
    except (TypeError, ValueError):
        start = 0
    if end is None:
        return (start, start)  # placeholder handled by caller? keep tuple
    try:
        end = int(end)
    except (TypeError, ValueError):
        end = start
    return (start, end)




MARKER_RE = re.compile(r"\[\s*MASKED\s+([^\]]+?)\s*\]")


def extract_marker_refs(text: Any) -> List[str]:
    """Extract every fetchable ref from ``[MASKED <ref>]`` markers in text."""
    if text is None:
        return []
    s = text if isinstance(text, str) else str(text)
    return [m.group(1).strip() for m in MARKER_RE.finditer(s)]


def marker_to_fetch_message(marker: str) -> Dict[str, Any]:
    """Wrap a marker's ref as a fetch tool call for parse_fetch_calls."""
    ref = ""
    m = MARKER_RE.search(str(marker or ""))
    if m:
        ref = m.group(1).strip()
    return {"tool_calls": [{"function": {"name": "fetch",
                                        "arguments": {"ref": ref}}}]}


def parse_fetch_calls(assistant_message: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(assistant_message, dict):
        return out
    calls = assistant_message.get("tool_calls")
    if not isinstance(calls, list):
        return out
    for c in calls:
        if not isinstance(c, dict):
            continue
        fn = c.get("function") if isinstance(c.get("function"), dict) else c
        if not isinstance(fn, dict):
            continue
        name = fn.get("name")
        if name != "fetch":
            # still parse? spec says fetch calls; filter by name
            if name is not None and name != "fetch":
                continue
        args_raw = fn.get("arguments", "{}")
        args: Dict[str, Any] = {}
        invalid = False
        if isinstance(args_raw, dict):
            args = dict(args_raw)
        elif isinstance(args_raw, str):
            try:
                parsed = json.loads(args_raw)
                if isinstance(parsed, dict):
                    args = parsed
                else:
                    invalid = True
            except (json.JSONDecodeError, ValueError):
                args = {}
                invalid = True
        else:
            args = {}
        ref = args.get("ref")
        if ref is None:
            # maybe nested
            ref = ""
        ref = str(ref) if ref is not None else ""
        rng = _coerce_range(args.get("range"))
        call_id = c.get("id")
        if call_id is None and isinstance(c.get("tool_call"), dict):
            call_id = c["tool_call"].get("id")
        entry = {"ref": ref, "range": rng}
        if invalid:
            entry["invalid"] = True
        if call_id is not None:
            entry["tool_call_id"] = call_id
            entry["id"] = call_id
        out.append(entry)
    return out


def render_fetch_result(result: FetchResult) -> Dict[str, Any]:
    return {
        "role": "tool",
        "tool_call_id": getattr(result, "tool_call_id", None),
        "name": "fetch",
        "content": json.dumps({
            "outcome": result.outcome,
            "ref": result.ref,
            "body_tokens": result.body_tokens,
            "truncated": result.truncated,
            "text": result.text,
        }),
    }


def batched_fetch(table: Mapping[str, Any], requests: List[Dict[str, Any]],
                  *, budget_tokens_per_turn: int, tokenizer=None) -> List[FetchResult]:
    results: List[FetchResult] = []
    # deterministic: request order preserved
    for req in requests:
        tcid = None
        if isinstance(req, dict):
            tcid = req.get("tool_call_id", req.get("id"))
        else:
            tcid = getattr(req, "tool_call_id", getattr(req, "id", None))
        if tcid is None:
            raise ValueError("fetch request missing tool_call_id")
        if isinstance(req, dict) and req.get("invalid"):
            results.append(FetchResult(ref="", outcome="INVALID_ARGS", text=None,
                                     body_tokens=0, truncated=False, tool_call_id=tcid))
            continue
        ref = req.get("ref") if isinstance(req, dict) else getattr(req, "ref", "")
        ref = "" if ref is None else str(ref)
        rng = req.get("range") if isinstance(req, dict) else getattr(req, "range", None)
        r = fetch(table, ref, rng, budget_tokens=budget_tokens_per_turn, tokenizer=tokenizer, tool_call_id=tcid)
        results.append(r)
    return results
