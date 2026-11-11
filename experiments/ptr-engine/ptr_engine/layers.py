"""Stable-prefix context compiler.

Builds a byte-stable prefix ``L0+PINS+L1`` from bytes that do not change between
compactions, plus an append-only journal ``L2`` that grows after it.

``PINS`` is the durable, append-only layer between the immutable system prompt
(``L0``) and the world index (``L1``): the agent's goal/decision/constraint/
blocker/warning/fact/ref pins and the compiler's own fold record.  It is
rendered only when it carries a pin, so an arm that never pins has exactly the
prefix bytes it had before the layer existed.

``prefix_sha256`` covers ``L0+PINS+L1`` only: hashing the growing ``L2`` tail
would report drift on every legitimate append and could not distinguish an
append from a destructive rewrite.  Compaction alone -- at the epoch boundary --
may break the prefix; it rewrites ``L2`` and appends one ``fold`` pin to
``PINS``.  Rationale: ``compile_prompt`` below and
``research-seed-concepts/PROMPT-ENGINE-V1.md`` (lines 48-56).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from .errors import PtrError
from .resume import RunState


class PtrPrefixDrift(PtrError):
    """L0 bytes changed within a run -- the cached prefix is no longer stable."""

    code = "PTR_PREFIX_DRIFT"


COMPACT_EVERY = 24

RETURN_SYMBOL = "\u23ce"  # ⏎


@dataclass
class CompactionState:
    index_lines: list = field(default_factory=list)
    # PINS: durable, append-only facts that must survive a fold -- the agent's
    # goal/decision/constraint/blocker/warning/fact/ref pins and the compiler's
    # own fold record.  Rendered as its own block between L0 and L1 and hashed
    # into the prefix, so a pin EXTENDS the cached prefix instead of rewriting
    # it.  Empty by default: an arm that never pins renders no PINS block and
    # its prefix bytes are byte-identical to the pre-PINS compiler.
    pins: list = field(default_factory=list)
    epoch: int = 0
    journal: list = field(default_factory=list)
    compactions: int = 0
    prefix_sha256: str = ""
    layer_tokens: dict = field(default_factory=dict)
    # The compaction interval this state folds at.  It is a per-state field, not a
    # module global, so two cells in one process can run different intervals (E2
    # varies it) without either one rewriting the other's fold distance.  The
    # default is the module constant, so a caller that never names it is unchanged.
    # ``None`` disables the interval entirely: the E7 pin arms fold on window
    # pressure only, because a fixed interval folds a prompt that never needed to
    # fold (docs/COMPACTION-CACHE-DESIGN.md §5.3).
    compact_every: int | None = COMPACT_EVERY
    # Window-pressure fold trigger.  ``None`` (the default) means the interval
    # above is the only trigger, so every existing arm folds exactly as before.
    # When set, the compiler also folds as soon as the estimated prompt size
    # exceeds this many tokens -- the real-session behaviour, where a fold is
    # forced by the window filling rather than by a turn count.  The estimate
    # uses ``CHARS_PER_TOKEN`` because the compiler has no tokenizer.
    fold_at_tokens: int | None = None
    # Per-run L0 stability state.  It lives on the state object (one per run),
    # never in a module global, so two runs that happen to share a ``run_id``
    # in one process cannot raise a false PtrPrefixDrift against each other.
    l0_hash: str = ""
    l0_run_id: Any = None
    # Why the last compile folded (``"pressure"``, ``"interval"`` or ``None``) and
    # the pre-fold prompt size estimate that decided it.  Evidence only: the fold
    # itself is already recorded as a pin, and this never enters the prompt.
    fold_trigger: str | None = None
    estimated_tokens: int | None = None


class _Prompt(str):
    """str subclass carrying per-prompt metadata (still compares as str)."""

    def __new__(cls, value, *, prefix_sha256, layer_tokens, epoch, compactions,
                fold_trigger=None, estimated_tokens=None):
        obj = super().__new__(cls, value)
        obj.prefix_sha256 = prefix_sha256
        obj.layer_tokens = layer_tokens
        obj.epoch = epoch
        obj.compactions = compactions
        obj.fold_trigger = fold_trigger
        obj.estimated_tokens = estimated_tokens
        return obj


# Legacy module-level map retained only so ``reset_prefix_state()`` has a
# well-defined target for callers that reused the old implementation.  The
# drift check itself is per-``CompactionState`` (see ``compile_prompt``).
_L0_HASHES: dict = {}


def reset_prefix_state() -> None:
    """Clear process-level prefix state.

    The authoritative L0 hash belongs to ``CompactionState``; this hook exists
    for callers that run several independent cells inside one process and want
    a single explicit reset point (tests, long-lived workers).
    """
    global _L0_HASHES
    _L0_HASHES = {}


def _run_id(run: Any) -> Any:
    for attr in ("run_id", "id", "name", "run"):
        v = getattr(run, attr, None)
        if v is not None:
            return v
    if isinstance(run, Mapping):
        for key in ("run_id", "id", "name", "run"):
            if key in run and run[key] is not None:
                return run[key]
    return id(run)


def _get(run: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if isinstance(run, Mapping) and name in run:
            v = run[name]
            if v is not None:
                return v
        v = getattr(run, name, None)
        if v is not None:
            return v
    return default


def _canonical_schema(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    if isinstance(value, (list, tuple)):
        if all(isinstance(x, str) for x in value):
            return json.dumps(sorted(value), sort_keys=True, separators=(",", ":"))
        return json.dumps(list(value), sort_keys=True, separators=(",", ":"), default=str)
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    except Exception:
        return str(value)


def _l0_text(run: Any) -> str:
    system = _get(run, "system", "system_text", "system_prompt", "prompt_system", default="")
    schema = _get(run, "tool_schema", "tool_schemas", "tools", "fetch_tool_spec", default=None)
    grammar = _get(run, "answer_grammar", "grammar", "answer_contract", default=None)
    model_id = _get(run, "model", "model_id", "model_name", default="unknown-model")
    fixture_id = _get(run, "fixture", "fixture_id", "task_id", default="unknown-fixture")
    generation = _get(run, "generation", "gen", default="gen-7")
    if grammar is None:
        grammar = ("ANSWER: NUM <int>\nANSWER: TEXT <value>\n"
                   "ANSWER: CALL <callee>(<kwargs>)\nANSWER: NONE")
    parts = [
        str(system),
        _canonical_schema(schema),
        str(grammar),
        "RUN model=%s fixture=%s generation=%s" % (model_id, fixture_id, generation),
    ]
    return "\n".join(parts)


def _layer_tokens(text: str) -> int:
    return len(text.split())


#: Characters per token, measured on a real 871-turn session transcript (growth
#: method, median).  The compiler has no tokenizer, so a window-pressure fold
#: needs a conversion; this is the measured one, not a guess.  ``_layer_tokens``
#: is a WORD count and must not be used as a token estimate.
CHARS_PER_TOKEN = 3.122


def _estimate_tokens(text: str) -> int:
    """Approximate token count of ``text`` at the measured chars/token ratio."""
    return int(len(text) / CHARS_PER_TOKEN)


def _sort_index_lines(lines: list) -> list:
    ref_lines = []
    other = []
    for ln in lines:
        s = str(ln)
        if s.lstrip().startswith("@"):
            ref_lines.append(s)
        else:
            other.append(s)
    ref_lines.sort()
    return ref_lines + other


def escape_journal_content(content: Any) -> str:
    return str(content).replace("\n", RETURN_SYMBOL)


def format_journal_line(n: int, role: str, content: Any) -> str:
    return "T%d|%s|%s" % (n, role, escape_journal_content(content))


_JOURNAL_TURN_RE = re.compile(r"^T(\d+)\|")


def _journal_turn(lines: list) -> int:
    """The turn number of the last journal line a fold drops.

    The fold record names the turn whose content was dropped, not the turn the
    fold ran on: ``P1|fold|T24|24 turns dropped at epoch 1`` says the 24th
    turn's line is gone.  Falls back to the line count when no line carries a
    ``T<n>`` stamp, so the record always names a number.
    """
    for line in reversed(list(lines or [])):
        match = _JOURNAL_TURN_RE.match(str(line))
        if match:
            return int(match.group(1))
    return len(lines or [])


def compile_prompt(run: Any, state: CompactionState, *, epoch: int, journal: list, work: str,
                   compact_every: int | None = None,
                   fold_at_tokens: int | None = None) -> str:
    """Render one prompt from a live ``CompactionState``.

    Journal lifecycle (owned by this function, not by the caller):
      * ``journal`` carries only the lines for the current compile (normally one
        ``T{n}|{role}|{content}`` line for the turn).  They are APPENDED to
        ``state.journal``; the caller must not re-pass lines already folded.
      * When the accumulated journal reaches the compaction interval, the whole
        journal is DROPPED -- no content survives the fold -- and a single
        deterministic pin ``P<n>|fold|T<t>|<n> turns dropped at epoch <e>`` is
        appended to ``state.pins``.  ``state.epoch`` is incremented,
        ``state.compactions`` is incremented and ``state.journal`` is reset to
        ``[]``.  The post-compaction state is what the caller must use on the
        next turn (read it back from ``state`` or from the returned prompt).
        The record is a PIN, not an ``index_lines`` entry: it must persist on
        every later turn, and PINS is append-only, so the record extends the
        cached prefix instead of rewriting L1.
      * ``state.epoch`` is authoritative: the ``epoch`` argument is a
        convenience only, and a stale caller value can never regress an epoch
        the state has already advanced past a compaction.
      * Compaction happens at the start of a compile, never between layers, so it
        can never fire mid-turn.

    ``compact_every`` is the fold distance.  ``None`` (the default) means "use the
    state's own interval", which itself defaults to ``COMPACT_EVERY``; a caller
    that names it overrides the state and the state records the new value, so the
    interval a run folds at is always readable from the state it folded.  A state
    whose ``compact_every`` is ``None`` has NO interval fold at all -- the E7 pin
    arms run that way, because the design's trigger is window pressure, not a turn
    count (docs/COMPACTION-CACHE-DESIGN.md §5.3).

    ``fold_at_tokens`` is the window-pressure trigger: when set, the compiler also
    folds as soon as the prompt would exceed that many tokens.  The size is
    estimated from characters at ``CHARS_PER_TOKEN`` (3.122, measured) because the
    compiler has no tokenizer; ``_layer_tokens`` is a WORD count and is not a
    token estimate.  The interval, when set, remains a floor, so a fixture that
    never reaches the threshold still folds at least once; with
    ``compact_every=None`` there is no floor and such a fixture does not fold.

    ``prefix_sha256`` is the hash of the CACHEABLE prefix: ``L0+PINS+L1``.  ``L2``
    is the append-only journal tail -- growing it extends the cached prefix
    without rewriting a byte already cached, so the stability metric that must
    hold within an epoch is ``L0+PINS+L1``; the only permitted change is
    compaction (which drops ``L2`` and appends one ``fold`` pin to ``PINS``).
    Hashing the growing ``L2`` would report a "change" on every append and could
    not distinguish an append from a rewrite.
    """
    if not isinstance(state, CompactionState):
        if isinstance(state, Mapping):
            st = CompactionState(
                index_lines=list(state.get("index_lines", [])),
                pins=list(state.get("pins", [])),
                epoch=int(state.get("epoch", epoch)),
                journal=list(state.get("journal", [])),
                compactions=int(state.get("compactions", 0)),
                compact_every=int(state.get("compact_every", COMPACT_EVERY)),
                l0_hash=state.get("l0_hash", "") or "",
                l0_run_id=state.get("l0_run_id"),
            )
            mapping_state = state
        else:
            raise TypeError("state must be CompactionState or mapping")
    else:
        st = state
        mapping_state = None

    # Drift check on L0.  The hash belongs to the run's own state, so two runs
    # sharing a run_id in one process never see each other's L0.
    rid = _run_id(run)
    l0 = _l0_text(run)
    l0_hash = hashlib.sha256(l0.encode("utf-8")).hexdigest()
    if st.l0_run_id is not None and st.l0_run_id != rid:
        # A different run is reusing this state object: its L0 baseline restarts.
        st.l0_hash = ""
    if st.l0_hash and st.l0_hash != l0_hash:
        raise PtrPrefixDrift("L0 bytes changed within run", run_id=rid)
    st.l0_hash = l0_hash
    st.l0_run_id = rid

    # Journal lifecycle: append the current compile's lines, never overwrite.
    st.index_lines = list(st.index_lines)
    st.journal = list(st.journal) + list(journal or [])
    # ``epoch`` is a convenience argument; the state is authoritative and an
    # already-advanced epoch must never be regressed by a stale caller value.
    st.epoch = max(int(st.epoch or 0), int(epoch or 0))

    # The fold distance: an explicit argument wins and is recorded on the state;
    # otherwise the state's own interval (default COMPACT_EVERY) is authoritative.
    if compact_every is not None:
        st.compact_every = int(compact_every)
    every = st.compact_every
    if fold_at_tokens is not None:
        st.fold_at_tokens = int(fold_at_tokens)
    fold_at = st.fold_at_tokens

    # Window pressure: the real-session trigger.  A real agent folds because the
    # window fills, not because a turn count is reached, so when a threshold is
    # set the compiler folds as soon as the prompt would exceed it.  The size is
    # estimated from characters at ``CHARS_PER_TOKEN`` because the compiler has
    # no tokenizer.  The interval, when set, stays as a floor, so a fixture that
    # never reaches the threshold still folds at least once; ``compact_every=None``
    # removes the floor and leaves pressure as the only trigger.
    over_window = False
    est_tokens = None
    if fold_at is not None and st.journal:
        prospective = "\n\n".join(
            [l0]
            + (["\n".join(str(x) for x in st.pins)] if st.pins else [])
            + ["\n".join(_sort_index_lines(st.index_lines)),
               "\n".join(str(x) for x in st.journal),
               str(work)]
        )
        est_tokens = _estimate_tokens(prospective)
        over_window = est_tokens >= int(fold_at)

    # compaction (start of compile only -- never mid-turn)
    compacted_now = False
    interval_due = every is not None and len(st.journal) >= int(every)
    if interval_due or over_window:
        # The journal is DROPPED, not summarised: no content survives the fold.
        # The record is a PIN, not an L1 line.  It is a durable fact about the
        # conversation ("24 turns were dropped at epoch 1"), it must persist on
        # every later turn, and PINS is append-only -- so the record EXTENDS the
        # cached prefix instead of rewriting L1, which would re-prefill every
        # byte after it.  The marker states exactly what happened, so nothing
        # downstream can read it as a claim that the folded turns are available.
        dropped = len(st.journal)
        st.pins = list(st.pins) + [
            "P%d|fold|T%d|%d turns dropped at epoch %d"
            % (len(st.pins) + 1, _journal_turn(st.journal), dropped, st.epoch + 1)
        ]
        st.epoch = st.epoch + 1
        st.compactions = st.compactions + 1
        st.journal = []
        compacted_now = True
        st.fold_trigger = "pressure" if over_window else "interval"
    else:
        st.fold_trigger = None
    st.estimated_tokens = est_tokens

    # The state is authoritative for the epoch.  A caller that keeps passing a
    # stale ``epoch`` (e.g. 0 every turn) must never regress an epoch the state
    # has already advanced past a compaction.
    epoch = st.epoch

    # contract line (L4)
    contract_line = _get(run, "contract_line", "answer_contract_line", default=None)
    if contract_line is None:
        contract_line = "ANSWER: NONE"

    # PINS (durable, append-only; between L0 and L1)
    pins_text = "\n".join(str(x) for x in st.pins)
    # L1
    l1 = "\n".join(_sort_index_lines(st.index_lines))
    # L2
    l2 = "\n".join(str(x) for x in st.journal)
    # L3
    l3 = str(work)
    # L4
    l4 = str(contract_line)

    # The PINS block is rendered ONLY when it carries a pin.  An empty block
    # would insert a second separator ("\n\n".join([l0, "", l1])) and change the
    # prefix bytes of every arm that never pins -- minting a new prefix
    # generation and making the no-pin control incomparable with existing rows.
    pins_block = [pins_text] if pins_text else []
    layers = [l0] + pins_block + [l1, l2, l3, l4]
    prompt = "\n\n".join(layers) + "\n"

    # The byte-stable prefix: L0+PINS+L1.  L2 is the append-only tail (see docstring).
    prefix_text = "\n\n".join([l0] + pins_block + [l1])
    prefix_sha = hashlib.sha256(prefix_text.encode("utf-8")).hexdigest()

    lt = {"L0": _layer_tokens(l0)}
    if pins_text:
        lt["PINS"] = _layer_tokens(pins_text)
    lt.update({
        "L1": _layer_tokens(l1),
        "L2": _layer_tokens(l2),
        "L3": _layer_tokens(l3),
        "L4": _layer_tokens(l4),
    })

    # write back to state
    st.prefix_sha256 = prefix_sha
    st.layer_tokens = lt
    # ``st.epoch`` is already authoritative (see above); ``epoch`` mirrors it.

    if mapping_state is not None:
        mapping_state["index_lines"] = st.index_lines
        mapping_state["pins"] = st.pins
        mapping_state["epoch"] = st.epoch
        mapping_state["journal"] = st.journal
        mapping_state["compactions"] = st.compactions
        mapping_state["compact_every"] = st.compact_every
        mapping_state["fold_trigger"] = st.fold_trigger
        mapping_state["estimated_tokens"] = st.estimated_tokens
        mapping_state["prefix_sha256"] = prefix_sha
        mapping_state["layer_tokens"] = lt
        mapping_state["l0_hash"] = st.l0_hash
        mapping_state["l0_run_id"] = st.l0_run_id

    try:
        run.prefix_sha256 = prefix_sha
        run.layer_tokens = lt
        run.epoch = epoch
        run.compactions = st.compactions
    except Exception:
        pass

    return _Prompt(prompt, prefix_sha256=prefix_sha, layer_tokens=lt, epoch=epoch,
                   compactions=st.compactions, fold_trigger=st.fold_trigger,
                   estimated_tokens=st.estimated_tokens)


__all__ = [
    "compile_prompt",
    "CompactionState",
    "PtrPrefixDrift",
    "COMPACT_EVERY",
    "RunState",
    "escape_journal_content",
    "format_journal_line",
    "RETURN_SYMBOL",
    "reset_prefix_state",
]
