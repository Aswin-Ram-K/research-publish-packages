"""Arm logic for context-policy arms C (masking-no-fetch) and D (bounded-context-fetch).

run_longrun.py only dispatches; the masking + fetch behaviour lives here so the
runner stays a driver.  Pure-ish: no network, no model calls beyond what the
caller (run_longrun) performs via send_chat.
"""
from __future__ import annotations

import hashlib

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

_LONGRUN_HERE = os.path.dirname(os.path.abspath(__file__))
# ptr_engine lives one directory up (experiments/ptr-engine); single honest path.
_PTR_ENGINE_ROOT = os.path.dirname(_LONGRUN_HERE)
if _PTR_ENGINE_ROOT not in sys.path:
    sys.path.insert(0, _PTR_ENGINE_ROOT)

from ptr_engine.pointer_table import (  # noqa: E402
    mask_output, build_table, fetch, FetchResult, PointerEntry, tokenizer_calls as _pt_tokenizer_calls,
)
from ptr_engine.fetch_tool import (  # noqa: E402
    FETCH_TOOL, parse_fetch_calls, render_fetch_result, batched_fetch,
)
from ptr_engine.quantise import token_len, StubTokenizer  # noqa: E402  real counter

ARM_C = "masking-no-fetch"
ARM_D = "bounded-context-fetch"
WINDOW_TURNS = 4


class ArmCDState:
    """Per-cell state for masking + bounded fetch."""

    def __init__(self, fixture: Optional[dict] = None, tokenizer=None):
        self.fixture = fixture
        self.tokenizer = tokenizer if tokenizer is not None else StubTokenizer()
        if self.fixture is None:
            self._discover_fixture()
        self.masked_turns: set = set()
        self._turn_entries: List[PointerEntry] = []
        self._doc_entries_cache: dict = {}
        self.masked_rows_this_turn: int = 0
        self.masked_entry_this_turn: Optional[List[Dict[str, Any]]] = None
        self.checkpoint_forecast: bool = False
        self._turn: int = 0

    # -- fixture discovery: none; fixture is passed explicitly via ArmCDState(fixture=...) --
    def _discover_fixture(self) -> None:
        return None

    def _doc_entries(self, t: int) -> List[PointerEntry]:
        try:
            t_int = int(t)
        except (TypeError, ValueError):
            t_int = t
        cache_key = (id(self.fixture), id(self.tokenizer), t_int)
        cached = self._doc_entries_cache.get(cache_key)
        if cached is not None:
            return [e for e in cached]
        fx = self.fixture or {}
        out: List[PointerEntry] = []
        for doc in (fx.get("documents") or []):
            if not isinstance(doc, dict):
                continue
            doc_id = doc.get("doc_id")
            if not doc_id:
                continue
            doc_id = str(doc_id)
            scope = doc.get("scope", "granted")
            revoked = bool(doc.get("revoked", False))
            revoked_at = doc.get("revoked_at_turn", None)
            revisions = doc.get("revisions") or []
            # current live revision at turn t
            current_rev = None
            for rev in revisions:
                if not isinstance(rev, dict):
                    continue
                lf = rev.get("live_from_turn", 1)
                try:
                    if int(lf) <= int(t):
                        current_rev = rev.get("revision")
                except (TypeError, ValueError):
                    current_rev = rev.get("revision")
            for rev in revisions:
                if not isinstance(rev, dict):
                    continue
                rnum = rev.get("revision")
                try:
                    rnum_int = int(rnum)
                except (TypeError, ValueError):
                    continue
                value = rev.get("value", "")
                body = "" if value is None else str(value)
                lf = rev.get("live_from_turn", 1)
                try:
                    lf_int = int(lf)
                except (TypeError, ValueError):
                    lf_int = 1
                # state derived from schedule at current turn
                if scope != "granted":
                    state = "ungranted"
                elif revoked and revoked_at is not None:
                    try:
                        if int(t) >= int(revoked_at):
                            state = "revoked"
                        elif current_rev is not None and rnum_int != current_rev:
                            state = "stale"
                        else:
                            state = "live"
                    except (TypeError, ValueError):
                        state = "live" if rnum_int == current_rev else "stale"
                else:
                    if lf_int > int(t):
                        state = "stale"
                    elif current_rev is not None and rnum_int != current_rev:
                        state = "stale"
                    elif current_rev is None:
                        state = "stale"
                    else:
                        state = "live"
                _marker, entry = mask_output(
                    body, logical_id=doc_id, revision=rnum_int, since_turn=lf_int,
                    tokenizer=self.tokenizer,
                    task_id=(self.fixture or {}).get("task_id") if isinstance(self.fixture, dict) else None,
                )
                # override state (mask_output stamps "live")
                entry = PointerEntry(
                    ref=entry.ref,
                    logical_id=entry.logical_id,
                    revision=entry.revision,
                    since_turn=entry.since_turn,
                    body_tokens=entry.body_tokens,
                    digest=entry.digest,
                    state=state,
                    body_tokens_basis=getattr(entry, "body_tokens_basis", "estimate:none"),
                    body=getattr(entry, "body", None),
                )
                out.append(entry)
        self._doc_entries_cache[cache_key] = [e for e in out]
        return out

    @property
    def masked_entries(self) -> List[PointerEntry]:
        # doc entries first so fetch/state resolution prefers current document state
        return list(self._doc_entries(self._turn or 1)) + list(self._turn_entries)

    @masked_entries.setter
    def masked_entries(self, value: Any) -> None:
        # runner assigns? keep as no-op compatibility; we derive instead
        # but preserve any externally provided turn entries if list given
        if isinstance(value, list):
            # split: keep PointerEntries whose ref looks like a turn ref
            self._turn_entries = [e for e in value if isinstance(e, PointerEntry)
                                  and str(getattr(e, "ref", "")).startswith("turn-")]

    def mask_old_turns(self, t: int, fixture: Optional[dict] = None) -> Tuple[int, List[Dict[str, Any]]]:
        if fixture is not None:
            self.fixture = fixture
        self._turn = int(t)
        self.masked_rows_this_turn = 0
        entries_this: List[Dict[str, Any]] = []
        cutoff = int(t) - WINDOW_TURNS
        turns = (self.fixture or {}).get("turns", []) if isinstance(self.fixture, dict) else []
        # existing refs for dedup of pointer entries
        existing_refs = {getattr(e, "ref", None) for e in self._turn_entries}
        for i in range(1, cutoff + 1):
            if i in self.masked_turns:
                continue
            turn = turns[i - 1] if (isinstance(turns, list) and i - 1 < len(turns)) else None
            tool_outputs = turn.get("tool_outputs") if isinstance(turn, dict) else None
            if not isinstance(tool_outputs, list):
                tool_outputs = []
            masked_this_turn = False
            for to in tool_outputs:
                if not isinstance(to, dict):
                    continue
                doc_id = to.get("doc_id")
                if not doc_id:
                    continue
                doc_id = str(doc_id)
                try:
                    revision = int(to.get("revision"))
                except (TypeError, ValueError):
                    continue
                body = to.get("body")
                if body is None:
                    body = ""
                body = str(body)
                marker, entry = mask_output(
                    body,
                    logical_id=doc_id,
                    revision=revision,
                    since_turn=i,
                    tokenizer=self.tokenizer,
                    task_id=(self.fixture or {}).get("task_id") if isinstance(self.fixture, dict) else None,
                )
                self.masked_rows_this_turn += 1
                entries_this.append({"ref": entry.ref, "since_turn": entry.since_turn})
                if entry.ref not in existing_refs:
                    self._turn_entries.append(entry)
                    existing_refs.add(entry.ref)
                masked_this_turn = True
            if masked_this_turn or (isinstance(turn, dict) and "tool_outputs" in turn):
                # mark turn processed only when it carried tool_outputs (masked or legitimately 0)
                if isinstance(turn, dict) and isinstance(turn.get("tool_outputs"), list):
                    self.masked_turns.add(i)
        self.masked_entry_this_turn = entries_this if entries_this else None
        return self.masked_rows_this_turn, (self.masked_entry_this_turn or [])

    def all_entries(self, turn: Optional[int] = None) -> List[PointerEntry]:
        if turn is not None:
            try:
                self._turn = int(turn)
            except (TypeError, ValueError):
                pass
        if self._turn == 0:
            self._turn = 1
        return list(self._doc_entries(self._turn)) + list(self._turn_entries)


def normalise_ref_revision(ref):
    """Normalise a bare integer revision ``@1`` to ``@r1`` for lookup only.

    Returns (normalised_ref, was_normalised).  Already-canonical refs and refs
    without a trailing integer revision are returned unchanged.
    """
    s = "" if ref is None else str(ref)
    m = re.search(r"@(\d+)$", s)
    if m:
        return ("%s@r%s" % (s[:m.start()], m.group(1))), True
    return s, False


def _text_call_refs(content):
    """Extract fetch refs from a text-form call ``ANSWER: CALL(fetch(ref=...))``."""
    text = content or ""
    if not re.search(r"CALL\s*\(?\s*fetch\b", text, re.IGNORECASE):
        return []
    refs = []
    for m in re.finditer(r"fetch\s*\(\s*ref\s*=\s*[\"']([^\"']+)[\"']", text, re.IGNORECASE):
        refs.append(m.group(1))
    if not refs:
        for m in re.finditer(r"fetch\s*\(\s*ref\s*=\s*([^\s,)]+)", text, re.IGNORECASE):
            refs.append(m.group(1).strip("\"'"))
    return refs


def parse_text_call(content):
    """Parse a text-form fetch request into at most one fetch call."""
    refs = _text_call_refs(content)
    if not refs:
        return []
    raw_ref = refs[0]
    norm_ref, changed = normalise_ref_revision(raw_ref)
    tcid = "text-fetch-0"
    return [{
        "ref": norm_ref,
        "ref_as_emitted": raw_ref,
        "range": None,
        "tool_call_id": tcid,
        "id": tcid,
        "protocol_variant": "text_call",
        "ref_revision_normalised": changed,
        "text_call": True,
    }]


def parse_fetch_calls_from_response(resp: Any) -> List[Dict[str, Any]]:
    """Detect fetch tool calls in a model response (structured or text)."""
    resp = resp or {}
    calls: List[Dict[str, Any]] = []
    if isinstance(resp.get("tool_calls"), list):
        try:
            calls.extend(parse_fetch_calls(resp))
        except (TypeError, AttributeError):
            pass
    content = resp.get("content") or resp.get("content_raw") or ""
    if not calls and isinstance(content, str) and "fetch" in content:
        try:
            from run_longrun import _decode_json_objects  # lazy
        except (ImportError, AttributeError):
            def _decode_json_objects(text):
                import json as _j
                dec = _j.JSONDecoder()
                out = []
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
                return out
        for idx, obj in enumerate(_decode_json_objects(content)):
            if isinstance(obj, dict) and "ref" in obj:
                rng = obj.get("range")
                if isinstance(rng, dict):
                    rng = (rng.get("start", 0), rng.get("end"))
                tcid = obj.get("tool_call_id", obj.get("id"))
                if tcid is None:
                    tcid = "text-fetch-%d" % idx
                calls.append({"ref": str(obj["ref"]), "range": rng,
                              "tool_call_id": tcid, "id": tcid})
    if not calls and isinstance(content, str):
        tc = parse_text_call(content)
        if tc:
            calls.extend(tc)
    if any(c.get("text_call") for c in calls):
        first_tc = next((c for c in calls if c.get("text_call")), None)
        if first_tc is not None:
            calls = [first_tc]
    return calls


def resolve_fetch_budget(state=None, fixture=None, budget_tokens=None) -> int:
    if budget_tokens is not None:
        try:
            return int(budget_tokens)
        except (TypeError, ValueError):
            raise ValueError("fetch_budget_tokens must be an integer")
    fx = fixture
    if fx is None and state is not None:
        fx = getattr(state, "fixture", None)
    if not isinstance(fx, dict) or "fetch_budget_tokens" not in fx:
        raise ValueError("fixture missing required key: fetch_budget_tokens")
    try:
        return int(fx["fetch_budget_tokens"])
    except (TypeError, ValueError):
        raise ValueError("fetch_budget_tokens must be an integer")


def service_fetches(state: ArmCDState, calls: List[Dict[str, Any]], budget_tokens=None,
                    turn: Optional[int] = None, *, tokenizer=None):
    if turn is not None:
        try:
            state._turn = int(turn)
        except (TypeError, ValueError):
            pass
    if state._turn == 0:
        state._turn = 1
    budget = resolve_fetch_budget(state=state, budget_tokens=budget_tokens)
    entries = state.all_entries(state._turn)
    seen = set()
    uniq = []
    for e in entries:
        if e.ref in seen:
            continue
        seen.add(e.ref)
        uniq.append(e)
    table = build_table(uniq)
    results = []
    for req in (calls or []):
        ref = req.get("ref") if isinstance(req, dict) else getattr(req, "ref", "")
        ref = "" if ref is None else str(ref)
        rng = req.get("range") if isinstance(req, dict) else getattr(req, "range", None)
        tcid = None
        if isinstance(req, dict):
            tcid = req.get("tool_call_id", req.get("id"))
        else:
            tcid = getattr(req, "tool_call_id", getattr(req, "id", None))
        if tcid is None:
            raise ValueError("fetch request missing tool_call_id")
        tok = tokenizer if tokenizer is not None else getattr(state, "tokenizer", None)
        r = fetch(table, ref, rng, budget_tokens=budget, tokenizer=tok, tool_call_id=tcid)
        results.append(r)
    outcomes = [getattr(r, "outcome", None) for r in results]
    attempt = None
    if calls:
        first = calls[0]
        first_ref = first.get("ref") if isinstance(first, dict) else getattr(first, "ref", None)
        attempt = {"ref": first_ref, "outcome": outcomes[0] if outcomes else None}
    return results, attempt, outcomes


def fetch_tokens_for(results) -> int:
    return sum(getattr(r, "body_tokens", 0) or 0 for r in (results or []))


def tokenizer_calls() -> int:
    return _pt_tokenizer_calls()
