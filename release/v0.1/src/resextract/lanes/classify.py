"""Publication-type classifier — refuse ``paper`` unless the evidence earns it.

The user's rule: not everything found becomes the same kind of output, and when
two things are genuinely different they become **two items, one per folder**.
This module decides *which* kind of item a lane is, using a small table of
deterministic guards and nothing else.  There is no model call here and no
heuristic scoring: every decision names the guard that decided it.

The guard table (approved plan section 3.6, implemented exactly)
---------------------------------------------------------------
``paper``
    requires **>= 1 verdict in {CONFIRMS, EXTENDS}** (an *external anchor*)
    **and >= 1 measured result**.  Missing either one downgrades the lane and
    the rationale records which guard failed.
``benchmark_card``
    requires **recomputable numbers**: a measured result that carries the
    command that produced it (:attr:`MeasuredResult.recomputable`).  A result
    with no command cannot satisfy this guard.
``memo``
    is the default for anything **unverifiable** — and never ``paper``.
``report`` / ``blog``
    the downgrade order for a paper-ineligible lane: ``report`` when there is a
    measured result or a substantive thesis, else ``blog`` when the lane is
    accessible narrative material, else ``memo``.

Precedence between ``benchmark_card`` and ``report`` is explicit and tested:
a lane with recomputable numbers but no external anchor becomes a
``benchmark_card`` (that is precisely the artifact recomputable numbers
support); a lane whose measured result carries **no** command cannot be a
benchmark card and falls through to ``report``.

Determinism: identical inputs produce an identical
:class:`Classification` (same type, same rationale, same guard outcomes).  The
function reads no clock, no environment and no store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "GUARD_NAMES",
    "Classification",
    "MeasuredResult",
    "classify_all",
    "classify_lane",
    "guards_failed",
    "guards_passed",
]

#: Every guard this classifier checks, in evaluation order.
GUARD_NAMES: tuple[str, ...] = (
    "verifiable",
    "external_anchor",
    "measured_result",
    "recomputable",
    "substantive_thesis",
    "accessible_narrative",
)

#: Verdicts that count as an external anchor for a paper.
ANCHOR_VERDICTS: frozenset[str] = frozenset({"CONFIRMS", "EXTENDS"})

#: A thesis is "substantive" at this many words and characters.
_THESIS_MIN_WORDS = 8
_THESIS_MIN_CHARS = 40


@dataclass(frozen=True)
class MeasuredResult:
    """One measured number and the command that produced it.

    A result *without* a command is not recomputable and therefore cannot
    satisfy the ``benchmark_card`` guard.
    """

    name: str
    value: float | int | str
    unit: str = ""
    command: str | None = ""
    source_ref: str = ""

    @property
    def recomputable(self) -> bool:
        """``True`` only when the producing command is present and non-blank."""
        return bool((self.command or "").strip())

    @property
    def numeric(self) -> bool:
        return isinstance(self.value, (int, float)) and not isinstance(self.value, bool)


@dataclass(frozen=True)
class Classification:
    """The chosen publication type, why, and the outcome of every guard."""

    type: str
    rationale: str
    guards: Mapping[str, bool] = field(default_factory=dict)

    def guard(self, name: str) -> bool:
        """Outcome of one named guard (``KeyError`` when the guard does not exist)."""
        return bool(dict(self.guards)[name])


# --------------------------------------------------------------------------- #
# Guard helpers: one rule at a time
# --------------------------------------------------------------------------- #


def _guard_mapping(target: Any) -> Mapping[str, bool]:
    if isinstance(target, Classification):
        return dict(target.guards)
    if isinstance(target, Mapping):
        return {str(key): bool(value) for key, value in target.items()}
    guards = getattr(target, "guards", None)
    if guards is not None:
        return {str(key): bool(value) for key, value in dict(guards).items()}
    raise TypeError(f"cannot read guards from {type(target).__name__}")


def guards_passed(target: Any, *names: str) -> bool:
    """``True`` when every named guard passed (all guards when no name is given)."""
    guards = _guard_mapping(target)
    checked = names or tuple(guards)
    for name in checked:
        if name not in guards:
            raise KeyError(f"unknown guard {name!r}; known guards: {sorted(guards)}")
    return all(guards[name] for name in checked)


def guards_failed(target: Any, *names: str) -> bool:
    """``True`` when any named guard failed (all guards when no name is given)."""
    guards = _guard_mapping(target)
    checked = names or tuple(guards)
    for name in checked:
        if name not in guards:
            raise KeyError(f"unknown guard {name!r}; known guards: {sorted(guards)}")
    return any(not guards[name] for name in checked)


# --------------------------------------------------------------------------- #
# Input normalisation
# --------------------------------------------------------------------------- #


def _as_result(item: Any) -> MeasuredResult:
    if isinstance(item, MeasuredResult):
        return item
    if isinstance(item, Mapping):
        return MeasuredResult(
            name=str(item.get("name") or ""),
            value=item.get("value"),
            unit=str(item.get("unit") or ""),
            command=item.get("command"),
            source_ref=str(item.get("source_ref") or ""),
        )
    return MeasuredResult(
        name=str(getattr(item, "name", "")),
        value=getattr(item, "value", None),
        unit=str(getattr(item, "unit", "") or ""),
        command=getattr(item, "command", None),
        source_ref=str(getattr(item, "source_ref", "") or ""),
    )


def _record(item: Any) -> Mapping[str, Any]:
    if isinstance(item, Mapping):
        return item
    data = getattr(item, "__dict__", None)
    if isinstance(data, Mapping):
        return data
    return {name: getattr(item, name, None) for name in ("candidate_id", "claim_id", "lane_slug", "verdict")}


def _belongs(record: Mapping[str, Any], member_ids: set[int], slug: str) -> bool:
    """A record belongs to the lane when unlinked, or linked by candidate_id/slug."""
    lane_slug = record.get("lane_slug")
    if lane_slug is not None and str(lane_slug) != slug:
        return False
    candidate_id = record.get("candidate_id")
    if candidate_id is not None:
        try:
            if int(candidate_id) not in member_ids:
                return False
        except (TypeError, ValueError):
            return False
    return True


def _relevant_verdicts(lane: Any, verdicts: Iterable[Any]) -> list[str]:
    member_ids = set(getattr(lane, "member_ids", ()) or ())
    slug = str(getattr(lane, "slug", ""))
    out: list[str] = []
    for item in verdicts or ():
        record = _record(item)
        if not _belongs(record, member_ids, slug):
            continue
        out.append(str(record.get("verdict") or "").upper())
    return out


def _relevant_results(lane: Any, results: Iterable[Any]) -> list[MeasuredResult]:
    member_ids = set(getattr(lane, "member_ids", ()) or ())
    slug = str(getattr(lane, "slug", ""))
    out: list[MeasuredResult] = []
    for item in results or ():
        if not _belongs(_record(item), member_ids, slug):
            continue
        out.append(_as_result(item))
    return out


def _relevant_evidence(lane: Any, evidence: Iterable[Any]) -> list[Any]:
    member_ids = set(getattr(lane, "member_ids", ()) or ())
    slug = str(getattr(lane, "slug", ""))
    return [item for item in (evidence or ()) if _belongs(_record(item), member_ids, slug)]


# --------------------------------------------------------------------------- #
# The classifier
# --------------------------------------------------------------------------- #


def classify_lane(
    lane: Any,
    *,
    verdicts: Sequence[Any] = (),
    results: Sequence[Any] = (),
    evidence: Sequence[Any] = (),
) -> Classification:
    """Classify one lane against the guard table.  Pure and deterministic.

    ``verdicts`` are records with ``verdict`` plus an optional ``candidate_id``
    or ``lane_slug``; a record with neither is treated as supplied for this
    lane.  ``results`` are :class:`MeasuredResult` objects (or mappings with
    ``name``/``value``/``unit``/``command``/``source_ref``).  ``evidence`` is
    any evidence rows already gathered for the lane; their presence is what
    makes a lane verifiable when its maturity is coarse.
    """
    relevant_verdicts = _relevant_verdicts(lane, verdicts)
    relevant_results = _relevant_results(lane, results)
    relevant_evidence = _relevant_evidence(lane, evidence)

    thesis = str(getattr(lane, "thesis", "") or "")
    maturity = str(getattr(lane, "maturity", "") or "low")
    words = len(thesis.split())

    anchors = [verdict for verdict in relevant_verdicts if verdict in ANCHOR_VERDICTS]
    guards: dict[str, bool] = {
        "verifiable": bool(relevant_evidence) or maturity != "low",
        "external_anchor": bool(anchors),
        "measured_result": bool(relevant_results),
        "recomputable": any(result.recomputable for result in relevant_results),
        "substantive_thesis": words >= _THESIS_MIN_WORDS and len(thesis) >= _THESIS_MIN_CHARS,
        "accessible_narrative": bool(getattr(lane, "kinds", ()) or ()) and bool(getattr(lane, "title", "")),
    }

    def show(name: str) -> str:
        return "true" if guards[name] else "false"

    if not guards["verifiable"]:
        rationale = (
            "type=memo: guard verifiable="
            + show("verifiable")
            + " (no evidence row for the lane and maturity "
            + repr(maturity)
            + "); unverifiable material defaults to memo, never paper."
        )
        return Classification(type="memo", rationale=rationale, guards=guards)

    if guards["external_anchor"] and guards["measured_result"]:
        rationale = (
            "type=paper: guards external_anchor="
            + show("external_anchor")
            + f" (verdict {anchors[0]} from an external check) and measured_result="
            + show("measured_result")
            + f" ({len(relevant_results)} measured result(s)) both hold."
        )
        return Classification(type="paper", rationale=rationale, guards=guards)

    refused = []
    if not guards["external_anchor"]:
        refused.append("external_anchor=false (no CONFIRMS/EXTENDS verdict)")
    if not guards["measured_result"]:
        refused.append("measured_result=false (no measured result)")

    if guards["recomputable"]:
        rationale = (
            "type=benchmark_card: paper refused ("
            + "; ".join(refused)
            + "); recomputable="
            + show("recomputable")
            + f" ({len(relevant_results)} measured result(s) carry the producing command), so the "
            "downgrade path paper -> benchmark_card is taken."
        )
        return Classification(type="benchmark_card", rationale=rationale, guards=guards)

    if guards["measured_result"] or guards["substantive_thesis"]:
        decided = "measured_result=true" if guards["measured_result"] else "substantive_thesis=true"
        extra = (
            " the measured result(s) carry no command, so recomputable=false refuses benchmark_card;"
            if guards["measured_result"]
            else ""
        )
        rationale = (
            "type=report: paper refused ("
            + "; ".join(refused)
            + ");"
            + extra
            + " downgrade report <- "
            + decided
            + "."
        )
        return Classification(type="report", rationale=rationale, guards=guards)

    if guards["accessible_narrative"]:
        rationale = (
            "type=blog: paper refused ("
            + "; ".join(refused)
            + "); measured_result=false and substantive_thesis=false, but accessible_narrative="
            + show("accessible_narrative")
            + " so the downgrade path paper -> report -> blog is taken."
        )
        return Classification(type="blog", rationale=rationale, guards=guards)

    rationale = (
        "type=memo: paper refused ("
        + "; ".join(refused)
        + "); no measured result, no substantive thesis and no accessible narrative material, "
        "so the downgrade path paper -> report -> blog -> memo ends at memo."
    )
    return Classification(type="memo", rationale=rationale, guards=guards)


def classify_all(
    lanes: Sequence[Any],
    *,
    verdicts: Sequence[Any] = (),
    results: Sequence[Any] = (),
    evidence: Sequence[Any] = (),
) -> list[tuple[Any, Classification]]:
    """Classify every lane, in input order (convenience for the live run)."""
    return [
        (lane, classify_lane(lane, verdicts=verdicts, results=results, evidence=evidence))
        for lane in lanes
    ]
