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
from ptr_engine.layers import (  # noqa: E402
    compile_prompt, CompactionState, format_journal_line, RETURN_SYMBOL,
    escape_journal_content, reset_prefix_state, COMPACT_EVERY, _estimate_tokens,
)
from ptr_engine.quantise import StubTokenizer  # noqa: E402  real counter

ARM_C = "masking-no-fetch"
ARM_D = "bounded-context-fetch"
ARM_SPCC = "spcc"
SPCC = ARM_SPCC
# E7's design arms (docs/COMPACTION-CACHE-DESIGN.md §7): D `pinned` and E
# `pinned-recency`.  Both are built on the pointer-stable tool-servicing path
# (run_longrun services tool calls for every arm that is not C/D/spcc) and both
# render through the SAME layer compiler as spcc, so the fold and the prefix
# hash have one definition.  They differ in exactly one thing: `pinned-recency`
# rewrites the two-tier todo's ACTIVE line into L3 every turn, `pinned` does
# not -- which is what lets E7 isolate the todo from the pins (§5.5).
ARM_PINNED = "pinned"
ARM_PINNED_RECENCY = "pinned-recency"
PINNED_ARMS = (ARM_PINNED, ARM_PINNED_RECENCY)
WINDOW_TURNS = 4

# The pin kinds the design admits (§5.2).  A synthesis, not a published
# standard; `fold` is written by the compiler itself and `retired` is a
# tombstone line, not a pin, so neither is a caller-supplied kind.
PIN_KINDS = ("goal", "decision", "constraint", "blocker", "warning", "fact", "ref", "fold")

# The PINS budget, in TOKENS (not lines): the cost of a pin is tokens, and a
# silent truncation is the documented worst outcome (Claude Code's over-limit
# auto-memory writes succeed but "everything past the limit is dropped on the
# next load"), so a write past the cap is REFUSED and the overflow returned.
PIN_CAP_TOKENS = 512

#: Window-pressure fold threshold, as a fraction of the fixture's
#: ``window_tokens``.  A real agent folds because the window fills, not because a
#: turn count is reached (docs/COMPACTION-CACHE-DESIGN.md §7, PREREG-COMPACTION.md
#: "Design": "Fold at 70 % of the window").  The turn interval stays as a floor.
FOLD_AT_FRACTION = 0.70

# Zero-width and bidi control characters.  A pin written from tool output is
# trusted text once it is in the prefix, so the characters that make a poisoned
# rule file invisible to human and PR review (Pillar "Rules File Backdoor",
# 2025-03-18; CVE-2025-54135 is the execution end of that chain) are stripped
# before it enters PINS.
_INVISIBLE_CHARS = dict.fromkeys(map(ord, (
    "\u00ad"                          # SOFT HYPHEN
    "\u180e"                          # MONGOLIAN VOWEL SEPARATOR
    "\u200b\u200c\u200d"              # ZWSP, ZWNJ, ZWJ
    "\u200e\u200f"                    # LRM, RLM
    "\u202a\u202b\u202c\u202d\u202e"  # LRE, RLE, PDF, LRO, RLO
    "\u2060"                          # WORD JOINER
    "\u2066\u2067\u2068\u2069"        # LRI, RLI, FSI, PDI
    "\ufeff"                          # ZERO WIDTH NO-BREAK SPACE / BOM
)), None)


def sanitise_pin_text(text) -> str:
    """Strip zero-width/bidi controls and flatten to one line.

    A pin is one line in a block whose structure is the line, so a newline in
    the text would forge a second pin; it is escaped with the journal's own
    ``RETURN_SYMBOL``, exactly as a journal line escapes its content.
    """
    return str(text).translate(_INVISIBLE_CHARS).replace("\n", RETURN_SYMBOL)


def _pin_tokens(lines) -> int:
    """Token count of a PINS block, in real tokens.

    Uses the compiler's own character-based estimate (``CHARS_PER_TOKEN``), not
    a word count: a word count makes a 200-character unbroken pin cost 1, so a
    cap expressed in "tokens" would admit ~200x the intended block.  The cap is
    a real budget, so it is measured the same way the window trigger is.
    """
    return _estimate_tokens("\n".join(str(x) for x in (lines or [])))


class PinCapExceeded(ValueError):
    """A pin write that would push PINS past its token budget.

    Raised, never swallowed: the write is REFUSED and the overflow is carried
    on the exception, because a truncated pin is unrecoverable while a refused
    write is not.
    """

    def __init__(self, *, cap: int, current: int, added: int):
        self.cap = int(cap)
        self.current = int(current)
        self.added = int(added)
        self.overflow = max(0, self.current + self.added - self.cap)
        super().__init__(
            "PINS cap exceeded: %d current + %d new = %d tokens > cap %d "
            "(overflow %d tokens); the pin was REFUSED, never truncated"
            % (self.current, self.added, self.current + self.added, self.cap, self.overflow))


class ArmCDState:
    """Per-cell state for masking + bounded fetch."""

    def __init__(self, fixture: Optional[dict] = None, tokenizer=None,
                 window_turns: int = WINDOW_TURNS):
        self.fixture = fixture
        self.tokenizer = tokenizer if tokenizer is not None else StubTokenizer()
        # E3's cell dimension: the masking window.  Omitted means the module
        # constant, so a run without --window-turns masks exactly as before; a
        # window above the fixture's turn count masks nothing, which is how E3
        # separates position from eviction with the body retained.
        try:
            window = int(window_turns)
        except (TypeError, ValueError):
            raise ValueError("window_turns must be an integer, got %r" % (window_turns,))
        if window < 1:
            raise ValueError("window_turns must be >= 1, got %r" % (window_turns,))
        self.window_turns = window
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
        cutoff = int(t) - int(self.window_turns)
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


def parse_fetch_calls_from_response(resp: Any,
                                    tool_names: Any = None) -> List[Dict[str, Any]]:
    """Detect fetch tool calls in a model response (structured or text).

    ``tool_names`` is the set of tool names the run DECLARED (``--tools``); it is
    forwarded to :func:`ptr_engine.fetch_tool.parse_fetch_calls` so a call named
    ``read_file`` -- the name the wire schema actually declares -- is serviced instead
    of being filtered out.  ``None`` keeps the parser's own default set.
    """
    resp = resp or {}
    calls: List[Dict[str, Any]] = []
    if isinstance(resp.get("tool_calls"), list):
        try:
            calls.extend(parse_fetch_calls(resp, tool_names=tool_names))
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


# ---------------------------------------------------------------- arm spcc ----
# Stable-prefix context compiler.  This is a REAL arm, not a label: every turn
# appends one journal line, every prompt is rendered by layers.compile_prompt
# with the live CompactionState, fetched bodies enter L3 only, and compaction is
# the only prefix break.

def _spcc_tokenizer(tokenizer):
    return tokenizer if tokenizer is not None else StubTokenizer()


def world_index_lines(fixture: Optional[dict], turn: int = 1) -> List[str]:
    """L1 world-index lines: one per ref the fetch tool accepts at ``turn``.

    INDEX-REF-COHERENCE (U-SPCC-55).  The refs are the ``make_ref`` form
    (``doc-<name>@r<rev>``) taken from the SAME pointer entries
    ``service_fetches`` builds its fetch table from, filtered to
    ``state == "live"``.  A ref the fetch tool would answer NOT_FOUND /
    STALE_OR_REVOKED / SCOPE_UNGRANTED is not part of the addressable world, so
    the index must not advertise it: the index is the only place the model
    learns which refs exist, and an index that names unfetchable refs teaches
    it to guess at a namespace it was never shown.

    Line shape is ``- {ref} {hash8} {bytes}``: the ref, a short digest and the
    body size in bytes, and no body text (no fact-value leak).
    """
    state = ArmCDState(fixture=fixture, tokenizer=StubTokenizer())
    lines: List[str] = []
    for entry in state._doc_entries(int(turn)):
        if getattr(entry, "state", None) != "live":
            continue
        body = getattr(entry, "body", None)
        body = "" if body is None else str(body)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]
        lines.append("- %s %s %d" % (entry.ref, digest, len(body.encode("utf-8"))))
    return lines


def spcc_world_index(fixture: Optional[dict], tokenizer=None) -> List[str]:
    """L1 world-index lines for the stable-prefix arm.

    Byte-identical to the masking/fetch arm's index (``run_longrun.index_lines``
    renders the same lines): both arms read the same L1, so neither may be
    handed a ref list the other lacks.  ``tokenizer`` is accepted for the L1
    call site and is unused -- the line carries the body's byte length, not a
    token count.
    """
    return world_index_lines(fixture)


def spcc_run(fixture: Optional[dict] = None, model: str = "offline-model") -> dict:
    """A run-shaped mapping for layers.compile_prompt (L0 fields + run_id)."""
    fx = fixture or {}
    return {
        "system": fx.get("system_prompt", ""),
        "tool_schema": None,
        "answer_grammar": None,
        "model": model,
        "fixture": fx.get("task_id", "offline-fixture"),
        "generation": "gen-7",
        "run_id": "spcc:%s" % fx.get("task_id", "offline-fixture"),
    }


def pinned_run(fixture: Optional[dict] = None, model: str = "offline-model",
               recency: bool = False) -> dict:
    """A run-shaped mapping for the E7 pin arms.

    Same L0 fields as ``spcc_run`` -- the two arms must be comparable on the
    immutable layer -- with a run_id that names the arm, so two pin cells in one
    process never share an L0 baseline by accident.
    """
    run = spcc_run(fixture, model=model)
    run["run_id"] = "%s:%s" % (ARM_PINNED_RECENCY if recency else ARM_PINNED,
                               (fixture or {}).get("task_id", "offline-fixture"))
    return run


class SpccArmState:
    """Per-cell state for the stable-prefix arm.

    ``state.journal`` is append-only.  The current turn's question lives in L3;
    the journal carries PRIOR turns (one ``T{n}|{role}|{content}`` line each), so
    the 24th pending line is appended on the 25th compile and compaction fires
    there -- exactly ``COMPACT_EVERY`` turns after the previous fold.

    Two kinds of body arrive in L3, and they are NOT the same thing:

    * **Fixture deliveries** (``add_delivery``) are part of the task transcript:
      the world the fixture hands the model, the same bodies the masking arm
      renders inline on their delivery turn.  They are rendered in L3 on the
      delivery turn AND carried in that turn's journal line, so they persist in
      L2 until compaction.  They never touch L1.
    * **Model-initiated fetches** (``add_fetch``) are the fetch mechanism.  They
      are rendered in L3 for their own turn only and are cleared at the end of
      it; they never touch L0, L1 or L2.
    """

    def __init__(self, fixture: Optional[dict] = None, tokenizer=None,
                 run: Optional[dict] = None, index_lines: Optional[List[str]] = None,
                 compact_every: int = COMPACT_EVERY):
        self.fixture = fixture or {}
        self.tokenizer = _spcc_tokenizer(tokenizer)
        self.index_lines = (list(index_lines) if index_lines is not None
                            else spcc_world_index(self.fixture, self.tokenizer))
        # The fold distance is a per-cell parameter (E2 varies it); the default is
        # the module constant, so an unparameterised arm folds exactly as before.
        self.compact_every = int(compact_every)
        self.state = CompactionState(index_lines=list(self.index_lines),
                                     compact_every=self.compact_every)
        self.run = run if run is not None else spcc_run(self.fixture)
        self.fetched: List[str] = []
        self.delivered: List[str] = []
        self.last_refs: List[str] = []
        self._pending_line: Optional[str] = None
        self.last_turn = 0

    def note_refs(self, refs) -> None:
        """Record refs emitted this turn; they ride the next journal line."""
        self.last_refs = [str(r) for r in (refs or [])]

    def add_fetch(self, body) -> None:
        """Queue a MODEL-INITIATED fetch for L3 this turn only (never L0/L1/L2)."""
        if body is not None:
            self.fetched.append(str(body))

    def add_delivery(self, body) -> None:
        """Queue a FIXTURE-DELIVERED body: L3 this turn, then L2 until compaction.

        Deliveries are transcript content, not fetches, so they ride the turn's
        journal line and survive every later compile until the journal folds.
        """
        if body is not None:
            text = str(body)
            self.fetched.append(text)     # L3 on the delivery turn
            self.delivered.append(text)   # L2 from the next compile onward

    def build(self, t: int, work: str, *, role: str = "user"):
        """Render turn ``t``; returns the ``_Prompt`` with stamping metadata."""
        new_lines: List[str] = []
        if self._pending_line is not None:
            new_lines.append(self._pending_line)
        l3 = str(work)
        if self.fetched:
            l3 = l3 + "\n" + "\n".join(self.fetched)
        prompt = compile_prompt(
            self.run, self.state,
            epoch=self.state.epoch, journal=new_lines, work=l3,
            compact_every=self.compact_every,
        )
        content = str(work)
        if self.delivered:
            # Fixture deliveries are transcript, not fetches: they ride the
            # journal line so they persist in L2 until compaction.
            content = content + "\n" + "\n".join(self.delivered)
        if self.last_refs:
            content = content + " refs=" + ",".join(self.last_refs)
        self._pending_line = format_journal_line(int(t), role, content)
        self.last_turn = int(t)
        self.fetched = []
        self.delivered = []
        self.last_refs = []
        return prompt


# -------------------------------------------------------------- arm pinned ----
# E7 arms D (`pinned`) and E (`pinned-recency`).  Rendered by the SAME layer
# compiler as spcc, so the layer set, the fold and the prefix hash are one
# definition; the difference is the PINS layer, which carries the durable facts
# a fold must not lose.  Tool calls are serviced by run_longrun's generic
# read_file channel (the pointer-stable path), which is what makes E7's primary
# mechanism -- `refetch_count` -- measurable on these arms.

class PinnedArmState:
    """Per-cell state for the E7 pin arms.

    ``state.pins`` is the PINS layer: append-only, in the cached prefix, and
    never rewritten.  It holds the durable PLAN pin (tier 1 of the two-tier
    todo), whatever the agent pins as it works, and the compiler's own fold
    record.  ``state.index_lines`` is L1 (the world index, no bodies) and
    ``state.journal`` is L2 (one line per prior turn, droppable).

    ``recency`` selects tier 2 of the two-tier todo: ``pinned-recency`` rewrites
    an ``ACTIVE`` line into L3 every turn, ``pinned`` does not.  That is the
    only difference between the two arms, which is what lets E7 isolate the todo
    from the pins (docs/COMPACTION-CACHE-DESIGN.md §5.5, §7).

    No body is pinned: L1 carries refs, digests and byte lengths only, so
    ``run_longrun.pinned_views`` finds nothing to serve from the prompt and every
    tool call is a real fetch.  That is deliberate -- a body served from the
    prompt would be a fetch that never happened, and the arm's whole claim is
    about re-fetches.
    """

    def __init__(self, fixture: Optional[dict] = None, tokenizer=None,
                 run: Optional[dict] = None, index_lines: Optional[List[str]] = None,
                 compact_every: Optional[int] = None,
                 pin_cap_tokens: int = PIN_CAP_TOKENS, recency: bool = False,
                 fold_at_fraction: Optional[float] = FOLD_AT_FRACTION):
        self.fixture = fixture or {}
        self.tokenizer = _spcc_tokenizer(tokenizer)
        self.index_lines = (list(index_lines) if index_lines is not None
                            else spcc_world_index(self.fixture, self.tokenizer))
        # ``compact_every=None`` (the default) means NO turn-interval fold: the pin
        # arms fold on window pressure only, because a fixed interval folds a prompt
        # that never needed to fold (docs/COMPACTION-CACHE-DESIGN.md §5.3).  A
        # caller that names an interval gets it back as a floor, never as the
        # trigger -- pressure still fires first whenever it fires at all.
        self.compact_every = (int(compact_every) if compact_every is not None else None)
        self.pin_cap_tokens = int(pin_cap_tokens)
        self.recency = bool(recency)
        # Window-pressure fold: a real agent folds when the window fills, not on
        # a turn count.  ``fold_at_fraction`` of the fixture's ``window_tokens``
        # is the threshold; ``None`` disables pressure and leaves only the
        # interval (which is itself off by default, so ``None``/``None`` never
        # folds -- a fixture that never reaches the threshold does not fold).
        self.fold_at_fraction = (float(fold_at_fraction)
                                 if fold_at_fraction is not None else None)
        window = int(self.fixture.get("window_tokens") or 0)
        self.fold_at_tokens = (int(window * self.fold_at_fraction)
                               if self.fold_at_fraction is not None and window > 0
                               else None)
        self.state = CompactionState(index_lines=list(self.index_lines),
                                     compact_every=self.compact_every,
                                     fold_at_tokens=self.fold_at_tokens)
        self.run = run if run is not None else pinned_run(self.fixture, recency=self.recency)
        self.fetched: List[str] = []
        self.delivered: List[str] = []
        self.last_refs: List[str] = []
        self._pending_line: Optional[str] = None
        self.last_turn = 0
        self.plan_id: Optional[str] = None
        self._plan_written = False

    # -- pin API (append-only; never edits, never truncates) --------------
    def _turn(self) -> int:
        """The turn a pin written now is stamped with (1 before the first build)."""
        return max(1, int(self.last_turn or 1))

    def _admit(self, line: str) -> None:
        """Refuse a line that would push PINS past its token budget."""
        current = _pin_tokens(self.state.pins)
        added = _pin_tokens([line])
        if current + added > self.pin_cap_tokens:
            raise PinCapExceeded(cap=self.pin_cap_tokens, current=current, added=added)

    def pin(self, kind: str, text, source=None, supersedes=None) -> str:
        """Append one pin and return its id (``P<n>``).

        Line shape: ``P<n>|kind|T<turn>|text``.  ``n`` is the 1-based index of
        the line in PINS, so an id is stable for the life of the run and a
        tombstone never renumbers a live pin.

        ``supersedes`` names the pin this one corrects: the text is prefixed
        with ``supersedes P<n>|`` so the conflict is visible in the prefix
        instead of being resolved silently.  A pin is never edited.

        ``source`` records provenance.  A pin that names a source is treated as
        externally sourced and is sanitised for zero-width/bidi controls before
        it enters PINS: a pin is trusted text and must not become an injection
        surface.

        Raises ``PinCapExceeded`` (carrying ``.overflow``) rather than
        truncating when the write would exceed the budget.
        """
        kind = str(kind)
        if kind not in PIN_KINDS:
            raise ValueError("unknown pin kind %r; known: %s" % (kind, list(PIN_KINDS)))
        if source is not None:
            body = sanitise_pin_text(text)
            body = "%s [source=%s]" % (body, sanitise_pin_text(source))
        else:
            body = escape_journal_content(text)
        if supersedes is not None:
            # Accept both the id this API returns ("P2") and a bare number (2):
            # a caller that passes back what ``pin()`` gave it must not have to
            # strip the prefix.
            ref = str(supersedes).strip()
            if ref.startswith("P"):
                ref = ref[1:]
            body = "supersedes P%d|%s" % (int(ref), body)
        line = "P%d|%s|T%d|%s" % (len(self.state.pins) + 1, kind, self._turn(), body)
        self._admit(line)
        self.state.pins = list(self.state.pins) + [line]
        return "P%d" % len(self.state.pins)

    def retire(self, pin_id, reason) -> str:
        """Append a tombstone for ``pin_id``; the pin itself is never removed.

        A retirement is a line, not a deletion: removing a pin would rewrite
        PINS, and a rewrite is a re-prefill of everything after it.
        """
        pid = str(pin_id).strip()
        if not pid.startswith("P"):
            pid = "P" + pid
        line = "P%d|retired|T%d|%s retired: %s" % (
            len(self.state.pins) + 1, self._turn(), pid, sanitise_pin_text(reason))
        self._admit(line)
        self.state.pins = list(self.state.pins) + [line]
        return "P%d" % len(self.state.pins)

    def pins(self) -> List[str]:
        """Read back the PINS layer (live pins and tombstones, in write order)."""
        return list(self.state.pins)

    # -- two-tier todo ----------------------------------------------------
    def write_plan(self, text=None) -> str:
        """Write tier 1 of the two-tier todo: the durable PLAN pin, once.

        It lives in PINS, so it is in the cached prefix (zero marginal cost on
        this endpoint) and survives every fold.  It is superseded only when the
        plan genuinely changes, never rewritten.
        """
        if self._plan_written:
            return self.plan_id
        task = str(self.fixture.get("task_id") or "task")
        body = text or ("PLAN: %s -- answer every checkpoint from the pinned index; "
                        "fetch a body only when the index does not carry the fact" % task)
        self.plan_id = self.pin("goal", body)
        self._plan_written = True
        return self.plan_id

    def active_line(self, t: int, work) -> str:
        """Tier 2 of the two-tier todo: the ACTIVE line, derived from THIS turn.

        It is a claim, so it is rebuilt from actual state every turn and never
        carried forward; it names the plan pin it belongs to, so a contradiction
        between the two tiers is visible in the prompt rather than silent.
        """
        question = " ".join(str(work).split())
        if len(question) > 120:
            question = question[:117] + "..."
        return "ACTIVE: T%d -- %s (plan %s)" % (int(t), question, self.plan_id or "P1")

    # -- per-turn inputs (same surface as SpccArmState) -------------------
    def note_refs(self, refs) -> None:
        """Record refs emitted this turn; they ride the next journal line."""
        self.last_refs = [str(r) for r in (refs or [])]

    def add_fetch(self, body) -> None:
        """Queue a MODEL-INITIATED fetch for L3 on the next compile only."""
        if body is not None:
            self.fetched.append(str(body))

    def add_delivery(self, body) -> None:
        """Queue a FIXTURE-DELIVERED body: L3 this turn, then L2 until the fold."""
        if body is not None:
            text = str(body)
            self.fetched.append(text)     # L3 on the delivery turn
            self.delivered.append(text)   # L2 from the next compile onward

    def build(self, t: int, work: str, *, role: str = "user"):
        """Render turn ``t``; returns the ``_Prompt`` with stamping metadata."""
        t = int(t)
        # Tier 1 is written before the first compile, so the PLAN is in the
        # prefix from turn 1 and the prefix is stable across turns 1..24.
        self.write_plan()
        new_lines: List[str] = []
        if self._pending_line is not None:
            new_lines.append(self._pending_line)
        l3 = str(work)
        if self.recency:
            # Tier 2: recency, tail, rewritten every turn (never carried).
            l3 = l3 + "\n" + self.active_line(t, work)
        if self.fetched:
            l3 = l3 + "\n" + "\n".join(self.fetched)
        prompt = compile_prompt(
            self.run, self.state,
            epoch=self.state.epoch, journal=new_lines, work=l3,
            compact_every=self.compact_every,
            fold_at_tokens=self.fold_at_tokens,
        )
        content = str(work)
        if self.delivered:
            # Fixture deliveries are transcript, not fetches: they ride the
            # journal line so they persist in L2 until the fold.
            content = content + "\n" + "\n".join(self.delivered)
        if self.last_refs:
            content = content + " refs=" + ",".join(self.last_refs)
        self._pending_line = format_journal_line(t, role, content)
        self.last_turn = t
        self.fetched = []
        self.delivered = []
        self.last_refs = []
        return prompt
