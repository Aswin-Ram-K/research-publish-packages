"""Lane splitting — when one lane is really two publishable items.

The user's rule: *"i get sometimes you might have to [output] multiple — but
again then just separate it as 2 items; each folder is one separate publishable
item."*

This module implements exactly that, and nothing more:

* a lane is split only when it holds **>= 2 independent primary members** that
  disagree on **audience** or on **maturity**;
* *independent* means their provenance references share no file — two members
  cut from the same file are one thread, not two;
* *primary* means the member carries provenance at all; a member with no
  provenance is supporting material and is attached to the first sibling
  rather than spawning an item of its own;
* siblings share ``parent_slug`` and each carries a ``split_reason`` naming the
  members and the axis that separated them;
* **a split never loses a member**: the union of the siblings' ``member_ids``
  equals the parent's ``member_ids``, checked in code;
* no disagreement (or no independent pair) means the original lane is returned
  unchanged — as the very same object.

Determinism: the same input yields the same siblings in the same order.
"""

from __future__ import annotations

import re
from dataclasses import replace
from itertools import combinations
from typing import Any, Iterable, Mapping, Sequence

from .build import (
    Lane,
    LaneCandidate,
    audience_for_members,
    derive_thesis,
    maturity_for_members,
)

__all__ = [
    "independent_members",
    "member_audience",
    "member_maturity",
    "split_lane",
]

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return _SLUG_RE.sub("-", str(text).lower()).strip("-") or "group"


def member_audience(member: LaneCandidate) -> str:
    """Audience of a single member (same rule the builder uses for lanes)."""
    return audience_for_members([member])


def member_maturity(member: LaneCandidate) -> str:
    """Maturity of a single member (same rule the builder uses for lanes)."""
    return maturity_for_members([member])


def _ref_files(member: LaneCandidate) -> frozenset[str]:
    """File identity of a member's provenance refs.

    ``file:path#L1-L2`` and ``path#L1`` both reduce to ``path``; a bare
    ``graph:node`` ref keeps its node identity (without a graph loaded we cannot
    map a node back to its file, and pretending otherwise would be dishonest).
    """
    keys: set[str] = set()
    for ref in member.provenance_refs or ():
        text = str(ref)
        if text.startswith("graph:"):
            keys.add(text)
            continue
        if text.startswith("file:"):
            text = text[5:]
        key = text.split("#", 1)[0].strip()
        if key:
            keys.add(key)
    return frozenset(keys)


def independent_members(left: LaneCandidate, right: LaneCandidate) -> bool:
    """``True`` when the two members' provenance refs share no file."""
    left_files, right_files = _ref_files(left), _ref_files(right)
    if not left_files or not right_files:
        return False
    return not (left_files & right_files)


def _axis(lane: Lane, primaries: Sequence[LaneCandidate]) -> str | None:
    """The first axis (audience, then maturity) on which two independent primaries differ."""
    for axis in ("audience", "maturity"):
        def value(member: LaneCandidate) -> str:
            return member_audience(member) if axis == "audience" else member_maturity(member)

        for left, right in combinations(sorted(primaries, key=lambda c: c.id), 2):
            if independent_members(left, right) and value(left) != value(right):
                return axis
    return None


def split_lane(
    lane: Lane,
    candidates: Sequence[LaneCandidate],
    *,
    verdicts: Sequence[Any] = (),
    results: Sequence[Any] = (),
) -> list[Lane]:
    """Split ``lane`` into siblings when its members genuinely disagree.

    ``verdicts`` / ``results`` are accepted for interface parity with
    :func:`resextract.lanes.classify.classify_lane`; the split decision itself
    is evidence-strength based (maturity already folds measured results and
    external verdicts in).  Returns ``[lane]`` when no split is warranted.
    """
    member_ids = tuple(getattr(lane, "member_ids", ()) or ())
    by_id: Mapping[int, LaneCandidate] = {candidate.id: candidate for candidate in candidates}
    missing = [member_id for member_id in member_ids if member_id not in by_id]
    if missing:
        raise ValueError(f"lane {lane.slug!r} references candidates not supplied: {missing}")
    members = sorted((by_id[member_id] for member_id in member_ids), key=lambda c: c.id)
    if len(members) < 2:
        return [lane]

    primaries = [member for member in members if member.provenance_refs]
    if len(primaries) < 2:
        return [lane]

    axis = _axis(lane, primaries)
    if axis is None:
        return [lane]

    value_of = member_audience if axis == "audience" else member_maturity
    groups: dict[str, list[LaneCandidate]] = {}
    for member in primaries:
        groups.setdefault(value_of(member), []).append(member)
    if len(groups) < 2:
        return [lane]

    supporting = [member for member in members if not member.provenance_refs]
    ordered_keys = sorted(groups, key=lambda key: (min(m.id for m in groups[key]), key))
    if supporting:  # supporting material follows the first sibling, deterministically
        groups[ordered_keys[0]] = sorted(groups[ordered_keys[0]] + supporting, key=lambda c: c.id)

    detail = []
    for key in ordered_keys:
        ids = ", ".join(str(member.id) for member in sorted(groups[key], key=lambda c: c.id))
        detail.append(f"{key}: {ids}")
    reason = (
        f"{axis} axis differs across independent primary members whose provenance files are disjoint "
        f"({'; '.join(detail)}); split into {len(ordered_keys)} item(s), one per {axis}."
    )

    siblings: list[Lane] = []
    for key in ordered_keys:
        group = sorted(groups[key], key=lambda c: c.id)
        slug = f"{lane.slug}-{_slug(key)}"
        siblings.append(
            replace(
                lane,
                slug=slug,
                title=f"{lane.title} - {key}",
                thesis=derive_thesis(group, theme=key),
                thesis_source=lane.thesis_source or "derived",
                member_ids=tuple(member.id for member in group),
                kinds=tuple(sorted({member.kind or "unknown" for member in group})),
                maturity=maturity_for_members(group),
                audience=audience_for_members(group),
                parent_slug=lane.slug,
                split_reason=reason,
            )
        )

    # The guarantee, enforced: no member may be dropped or duplicated.
    union = [member_id for sibling in siblings for member_id in sibling.member_ids]
    assert sorted(union) == sorted(member_ids), (
        f"split of {lane.slug!r} lost or duplicated members: {sorted(union)} != {sorted(member_ids)}"
    )
    assert len(set(sibling.slug for sibling in siblings)) == len(siblings), "split produced duplicate slugs"
    return siblings
