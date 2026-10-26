"""Canned research-directed query battery for the knowledge graph.

The battery is **data-driven**: :data:`BATTERY` is an ordered tuple of
:class:`Query` records and every helper in this module reads from it.  A future
unit extends the battery by appending to ``BATTERY`` (or by passing its own
sequence to :func:`dedupe`) — no code changes are required here.

Every template is *generic*: it contains no repo-specific strings, only
``{placeholder}`` slots that :func:`render` fills in.  Rendering a template
without supplying a placeholder leaves the placeholder text intact, so an
unrendered query is still a valid, searchable question.

The eleven ``intent`` areas mirror stage 2 of ``docs/PLAN.md``: novel
primitives; invariants and enforcement; measured deltas and performance
numbers; negative results and regressions; reversed or superseded decisions;
unreproduced or unfalsifiable claims; capability/permission boundaries; data
formats and schemas; external interfaces and adapters; test/verification
strategy; operational limits and failure modes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

__all__ = [
    "KINDS",
    "BATTERY",
    "Query",
    "all_queries",
    "queries_for",
    "render",
    "dedupe",
]


def _slug(text: str) -> str:
    """Lowercase ``text`` and collapse every non-alphanumeric run to ``-``."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# --------------------------------------------------------------------------- #
# The record
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Query:
    """One canned research question.

    ``name``     short stable identifier (unique across the battery)
    ``intent``   which stage-2 research area the question serves
    ``template`` the question itself, with optional ``{placeholder}`` slots
    ``why``      what a good answer lets the downstream stage do
    """

    name: str
    intent: str
    template: str
    why: str

    @property
    def kind(self) -> str:
        """Slug form of :attr:`intent`, e.g. ``"novel primitives"`` -> ``"novel-primitives"``."""
        return _slug(self.intent)

    def fields(self) -> tuple[str, ...]:
        """Placeholder names used by :attr:`template`, in first-seen order."""
        return tuple(dict.fromkeys(_PLACEHOLDER.findall(self.template)))

    def render(self, **subs: object) -> str:
        """Return :attr:`template` with ``subs`` substituted (see :func:`render`)."""
        return render(self.template, **subs)


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

# Deliberately matches only simple ``{identifier}`` slots: format specs, nested
# braces and literal braces are all left alone rather than raising.
_PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def render(template: str, **subs: object) -> str:
    """Substitute ``{name}`` slots in ``template`` from ``subs``.

    Substitution is *safe*: a placeholder with no matching keyword is left in
    the output verbatim (``"{symbol}"`` stays ``"{symbol}"``), extra keywords
    are ignored, and malformed or literal braces never raise.  This means a
    template can be handed to a query engine before its slots are known.
    """
    def _sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in subs:
            return match.group(0)
        value = subs[key]
        return value if isinstance(value, str) else str(value)

    return _PLACEHOLDER.sub(_sub, template)


# --------------------------------------------------------------------------- #
# The eleven stage-2 areas
# --------------------------------------------------------------------------- #

KINDS: tuple[str, ...] = (
    "novel primitives",
    "invariants and enforcement",
    "measured deltas and performance numbers",
    "negative results and regressions",
    "reversed or superseded decisions",
    "unreproduced or unfalsifiable claims",
    "capability and permission boundaries",
    "data formats and schemas",
    "external interfaces and adapters",
    "test and verification strategy",
    "operational limits and failure modes",
)


def _q(intent: str, name: str, template: str, why: str) -> Query:
    return Query(name=name, intent=intent, template=template, why=why)


BATTERY: tuple[Query, ...] = (
    # -- novel primitives -------------------------------------------------- #
    _q(
        "novel primitives",
        "novel-primitives-inventory",
        "what new primitives, abstractions or types does this project define that do not exist upstream",
        "Separates genuine inventions from thin wrappers before any of them are re-implemented.",
    ),
    _q(
        "novel primitives",
        "primitive-definition-sites",
        "where is {primitive} defined and what does it wrap or extend",
        "Points at the one authoritative definition instead of a copy.",
    ),
    _q(
        "novel primitives",
        "primitive-uniqueness",
        "which modules redefine a concept that another module already provides for {concept}",
        "Finds duplicate primitives that will drift apart.",
    ),
    # -- invariants and enforcement ---------------------------------------- #
    _q(
        "invariants and enforcement",
        "invariants-stated",
        "what invariants must hold for {subject} and where are they asserted or validated",
        "Turns prose claims into checkable conditions.",
    ),
    _q(
        "invariants and enforcement",
        "invariants-unenforced",
        "which invariants are documented for {subject} but never enforced in code",
        "Surfaces documented-but-unchecked contracts.",
    ),
    _q(
        "invariants and enforcement",
        "invariant-violation-path",
        "what code path can violate the invariant on {subject}",
        "Locates the enforcement gap rather than the rule.",
    ),
    # -- measured deltas and performance numbers ---------------------------- #
    _q(
        "measured deltas and performance numbers",
        "measured-deltas",
        "which performance numbers or measured deltas are recorded for {metric}",
        "Collects the actual measurements instead of re-deriving them.",
    ),
    _q(
        "measured deltas and performance numbers",
        "benchmark-harness",
        "how is {metric} measured and what code produces the number",
        "Identifies the harness so a claim can be reproduced.",
    ),
    _q(
        "measured deltas and performance numbers",
        "delta-regression-guard",
        "is there a test or threshold that fails when {metric} regresses",
        "Tells whether a measured delta is actually protected.",
    ),
    # -- negative results and regressions ----------------------------------- #
    _q(
        "negative results and regressions",
        "negative-results",
        "what approaches for {subject} were tried and reported as not working",
        "Prevents re-running a known dead end.",
    ),
    _q(
        "negative results and regressions",
        "known-regressions",
        "which known regressions or failure reports reference {subject}",
        "Collects the failure history around a subsystem.",
    ),
    _q(
        "negative results and regressions",
        "abandoned-branches",
        "which incomplete or abandoned implementations remain for {subject}",
        "Distinguishes unfinished work from rejected work.",
    ),
    # -- reversed or superseded decisions ----------------------------------- #
    _q(
        "reversed or superseded decisions",
        "superseded-decisions",
        "which earlier decisions about {subject} were later reversed or superseded",
        "Stops the extractor from quoting an obsolete decision as current.",
    ),
    _q(
        "reversed or superseded decisions",
        "decision-history",
        "what is the chronological order of the decisions made about {subject}",
        "Orders the record so the latest ruling wins.",
    ),
    _q(
        "reversed or superseded decisions",
        "stale-references",
        "which code or documentation still references the superseded {artifact}",
        "Finds leftovers of a reverted decision.",
    ),
    # -- unreproduced or unfalsifiable claims ------------------------------- #
    _q(
        "unreproduced or unfalsifiable claims",
        "unreproduced-claims",
        "which claims about {subject} have no reproducible evidence attached",
        "Flags assertions that cannot be checked.",
    ),
    _q(
        "unreproduced or unfalsifiable claims",
        "unfalsifiable-claims",
        "which statements about {subject} cannot be falsified by any test or measurement",
        "Marks claims to treat as opinion, not fact.",
    ),
    _q(
        "unreproduced or unfalsifiable claims",
        "evidence-forward-claims",
        "which claims about {subject} cite an external source that is not in this repository",
        "Separates in-repo evidence from borrowed authority.",
    ),
    # -- capability and permission boundaries ------------------------------- #
    _q(
        "capability and permission boundaries",
        "permission-boundaries",
        "what capabilities or permissions does {component} require and who grants them",
        "Maps what the component is allowed to touch.",
    ),
    _q(
        "capability and permission boundaries",
        "privilege-escalation-path",
        "where does {component} cross a trust or privilege boundary",
        "Finds the boundary crossings worth auditing.",
    ),
    _q(
        "capability and permission boundaries",
        "read-write-scope",
        "which paths or resources can {component} write to and which are read-only",
        "Establishes the blast radius of a component.",
    ),
    # -- data formats and schemas ------------------------------------------- #
    _q(
        "data formats and schemas",
        "schema-definitions",
        "what data formats or schemas does {component} read and write",
        "Inventories the on-disk and on-wire contracts.",
    ),
    _q(
        "data formats and schemas",
        "schema-versioning",
        "how are the schemas used by {component} versioned and migrated",
        "Finds whether format changes are backward compatible.",
    ),
    _q(
        "data formats and schemas",
        "schema-validators",
        "where is the schema for {artifact} validated on input",
        "Checks that malformed data is rejected early.",
    ),
    # -- external interfaces and adapters ----------------------------------- #
    _q(
        "external interfaces and adapters",
        "external-interfaces",
        "what external interfaces or services does {component} depend on",
        "Lists everything that can break from outside.",
    ),
    _q(
        "external interfaces and adapters",
        "adapter-layer",
        "which adapters or shims translate between {component} and an external system",
        "Locates the seam where an external change lands.",
    ),
    _q(
        "external interfaces and adapters",
        "protocol-assumptions",
        "what protocol or API-version assumptions does {component} encode",
        "Surfaces assumptions a dependency upgrade would break.",
    ),
    # -- test and verification strategy ------------------------------------- #
    _q(
        "test and verification strategy",
        "test-strategy",
        "how is {subject} verified and which tests cover it",
        "Gives the verification route for a claim.",
    ),
    _q(
        "test and verification strategy",
        "untested-surface",
        "which part of {component} has no test coverage",
        "Names the unverified surface explicitly.",
    ),
    _q(
        "test and verification strategy",
        "offline-vs-network-tests",
        "which tests for {component} require the network or an external service",
        "Separates hermetic tests from ones needing live systems.",
    ),
    # -- operational limits and failure modes ------------------------------- #
    _q(
        "operational limits and failure modes",
        "operational-limits",
        "what limits bound {component} and what happens when they are reached",
        "Finds the ceilings and their behaviour at the ceiling.",
    ),
    _q(
        "operational limits and failure modes",
        "failure-modes",
        "what failure modes or error paths does {component} define",
        "Enumerates the ways it can fail.",
    ),
    _q(
        "operational limits and failure modes",
        "timeout-and-retry",
        "where are timeouts, retries or backoff configured for {component}",
        "Shows how transient failure is absorbed.",
    ),
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def all_queries() -> list[Query]:
    """Return the whole battery as a fresh list (safe to sort or filter)."""
    return list(BATTERY)


def queries_for(kind: str) -> list[Query]:
    """Return the queries serving ``kind``.

    ``kind`` matches either an area slug (``"novel-primitives"``), the area text
    (``"novel primitives"``, case-insensitive) or the intent-``kind`` of any
    query.  An unknown or empty ``kind`` yields an empty list.
    """
    wanted = _slug(kind or "")
    if not wanted:
        return []
    return [q for q in BATTERY if q.kind == wanted]


def dedupe(queries: Iterable[Query]) -> list[Query]:
    """Drop exact duplicates, keeping the first occurrence and input order.

    A query is a duplicate when its ``name`` *or* its ``template`` has already
    been seen — two records that ask the same thing under different names still
    collapse to one.
    """
    seen_names: set[str] = set()
    seen_templates: set[str] = set()
    out: list[Query] = []
    for q in queries:
        if q.name in seen_names or q.template in seen_templates:
            continue
        seen_names.add(q.name)
        seen_templates.add(q.template)
        out.append(q)
    return out


def render_battery(queries: Sequence[Query] | None = None, **subs: object) -> list[tuple[str, str]]:
    """Render every query to ``(name, question)`` pairs (convenience for callers)."""
    return [(q.name, q.render(**subs)) for q in (queries if queries is not None else BATTERY)]
