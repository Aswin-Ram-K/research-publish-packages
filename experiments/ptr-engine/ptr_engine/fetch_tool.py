"""OpenAI-style fetch tool wrapping the pointer table."""

from __future__ import annotations

import json
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
        if isinstance(args_raw, dict):
            args = dict(args_raw)
        elif isinstance(args_raw, str):
            try:
                parsed = json.loads(args_raw)
                if isinstance(parsed, dict):
                    args = parsed
            except (json.JSONDecodeError, ValueError):
                args = {}
        else:
            args = {}
        ref = args.get("ref")
        if ref is None:
            # maybe nested
            ref = ""
        ref = str(ref) if ref is not None else ""
        rng = _coerce_range(args.get("range"))
        out.append({"ref": ref, "range": rng})
    return out


        call_id = c.get("id")
        if call_id is None and isinstance(c.get("tool_call"), dict):
            call_id = c["tool_call"].get("id")
        if call_id is None:
            raise ValueError("fetch tool call missing id")
        entry = {"ref": ref, "range": rng}
        if invalid:
            entry["invalid"] = True
        entry["tool_call_id"] = call_id
        entry["id"] = call_id
        out.append(entry)
        return out
            "text": result.text,
        }),
    }


def batched_fetch(table: Mapping[str, Any], requests: List[Dict[str, Any]],
                  *, budget_tokens_per_turn: int) -> List[FetchResult]:
    results: List[FetchResult] = []
    # deterministic: request order preserved
    for req in requests:
        ref = req.get("ref") if isinstance(req, dict) else getattr(req, "ref", "")
        ref = "" if ref is None else str(ref)
        rng = req.get("range") if isinstance(req, dict) else getattr(req, "range", None)
        try:
            r = fetch(table, ref, rng, budget_tokens=budget_tokens_per_turn)
        except Exception:
            r = FetchResult(ref=ref, outcome="NOT_FOUND", text=None,
                            body_tokens=0, truncated=False)
        results.append(r)
    return results
""" i">
Writing fetch_tool.py with plain import