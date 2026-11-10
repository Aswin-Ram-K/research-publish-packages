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


#: Tool names a fetch-arm reply may use when the caller does not supply the set the run
#: actually DECLARED.  ``fetch`` is what the ARM_D prompt teaches (``fetch(ref=...)``);
#: ``read_file`` is what the wire schema declares (``TOOL_NAMES`` in ``run_longrun``).
#: Keeping both here is what stops the parser and the wire schema drifting apart again:
#: a ``read_file`` call used to be filtered out at the name check, so ``_calls`` came
#: back empty, no follow-up was bought, and the checkpoint scored ``unparsed``.
DEFAULT_FETCH_TOOL_NAMES: Tuple[str, ...] = ("fetch", "read_file")


def _accepted_tool_names(tool_names: Any) -> Tuple[str, ...]:
    """The names this parse accepts: the caller's declared set, else the default."""
    if tool_names is None:
        return DEFAULT_FETCH_TOOL_NAMES
    if isinstance(tool_names, str):
        tool_names = (tool_names,)
    try:
        names = tuple(str(n) for n in tool_names if n)
    except TypeError:
        return DEFAULT_FETCH_TOOL_NAMES
    return names or DEFAULT_FETCH_TOOL_NAMES


def parse_fetch_calls(assistant_message: Any,
                      tool_names: Any = None) -> List[Dict[str, Any]]:
    """Structured fetch calls in one assistant message.

    ``tool_names`` is the set of tool names the run DECLARED (``--tools``); a call whose
    name is outside it is rejected -- not silently rewritten into a fetch.  ``None``
    falls back to :data:`DEFAULT_FETCH_TOOL_NAMES`, so a caller that does not know the
    declared set still services both the prompt-taught ``fetch`` and the wire's
    ``read_file``.  A call with no name at all is still parsed, as it always was.
    """
    out: List[Dict[str, Any]] = []
    if not isinstance(assistant_message, dict):
        return out
    calls = assistant_message.get("tool_calls")
    if not isinstance(calls, list):
        return out
    accepted = _accepted_tool_names(tool_names)
    for c in calls:
        if not isinstance(c, dict):
            continue
        fn = c.get("function") if isinstance(c.get("function"), dict) else c
        if not isinstance(fn, dict):
            continue
        name = fn.get("name")
        if name is not None and name not in accepted:
            # An undeclared name is REJECTED here and reported by the caller
            # (`run_longrun.unserviced_structured_calls`), never dropped silently.
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
            # A `read_file` call carries no `ref`; its `path` is the only ref-bearing
            # field the wire schema gives it, so that is what the table is asked for.
            ref = args.get("path")
        if ref is None:
            ref = ""
        ref = str(ref) if ref is not None else ""
        # `range` stays BYTE offsets into the stored body, exactly as before.  A
        # `read_file` call's `start_line`/`end_line` are LINE numbers and are
        # deliberately NOT mapped onto it: the pointer table has no line index, so
        # passing them as bytes would slice the wrong text (or refuse the range)
        # instead of returning the body the model asked about.
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
