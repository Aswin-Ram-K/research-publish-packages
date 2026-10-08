"""Lane building, publication-type classification and splitting.

* :mod:`resextract.lanes.build` — candidates -> lanes (one lane = one folder).
* :mod:`resextract.lanes.classify` — lanes -> ``paper|report|blog|benchmark_card|memo``
  with an explicit guard table; ``paper`` needs an external anchor *and* a
  measured result.
* :mod:`resextract.lanes.split` — one lane -> two independable items when its
  members genuinely disagree on audience or maturity.

Every ``title``/``thesis`` produced here is derived deterministically from
stored candidates; ``thesis_source`` is ``"derived"`` and only a later unit
that really calls a model may flip it to ``"model"``.
"""

from __future__ import annotations

from .build import (
    AUDIENCE_PRIORITY,
    Lane,
    LaneCandidate,
    attach_evidence,
    audience_for_kind,
    audience_for_members,
    build_lanes,
    candidate_bag,
    derive_thesis,
    dominant_tokens,
    from_store,
    maturity_for_members,
    normalise_tokens,
    persist_lanes,
    similarity,
    write_lanes_md,
)
from .classify import (
    GUARD_NAMES,
    Classification,
    MeasuredResult,
    classify_all,
    classify_lane,
    guards_failed,
    guards_passed,
)
from .split import independent_members, member_audience, member_maturity, split_lane

__all__ = [
    "AUDIENCE_PRIORITY",
    "GUARD_NAMES",
    "Classification",
    "Lane",
    "LaneCandidate",
    "MeasuredResult",
    "attach_evidence",
    "audience_for_kind",
    "audience_for_members",
    "build_lanes",
    "candidate_bag",
    "classify_all",
    "classify_lane",
    "derive_thesis",
    "dominant_tokens",
    "from_store",
    "guards_failed",
    "guards_passed",
    "independent_members",
    "maturity_for_members",
    "member_audience",
    "member_maturity",
    "normalise_tokens",
    "persist_lanes",
    "similarity",
    "split_lane",
    "write_lanes_md",
]
