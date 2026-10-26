"""Lane builder — turn a pile of mined candidates into *one lane = one folder*.

A **lane** is one publishable item: a paper, a report, a blog post, a benchmark
card or a memo (see :mod:`resextract.lanes.classify` for the type decision).
This module only *builds* lanes out of candidates that already exist in the
store; it never invents material and it never calls a model.

Determinism and stability are the contract
------------------------------------------
Everything here is pure stdlib and pure function of the input:

* candidates are grouped by a **lexical similarity** over normalised
  ``title + summary`` tokens (a weighted Jaccard: a token occurring in the
  title counts twice, because the title is the query-authored label), plus a
  small **community-overlap bonus** when the knowledge-graph communities of two
  candidates agree;
* tokens that occur in exactly **one** candidate are dropped before scoring —
  a node-local identifier (``tsconfig_compileroptions_types``) is identity
  noise, not a theme;
* ties are broken by candidate id and by alphabetical token order, so a
  shuffled input produces the same lanes, the same slugs and byte-identical
  ``lanes.json`` output.

THE HONESTY RULE (this is the point of the module)
--------------------------------------------------
Every ``title`` and ``thesis`` written here is **derived deterministically**
from member candidates (their titles, summaries and kinds).  The Occamy
endpoint may well be unreachable, and a later unit may legitimately upgrade a
thesis with a model — but that unit must then flip ``thesis_source`` from
``"derived"`` to ``"model"``.  **Nothing may claim a model wrote text it did
not write.**  :attr:`Lane.thesis_source` therefore defaults to ``"derived"``
and is never set to ``"model"`` anywhere in this module.

Evidence strength (``maturity``) and audience are computed from what the
candidates actually carry — verified provenance, measured results, external
verdicts, kinds — never guessed.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .. import store as _store

__all__ = [
    "AUDIENCE_PRIORITY",
    "Lane",
    "LaneCandidate",
    "audience_for_kind",
    "audience_for_members",
    "attach_evidence",
    "build_lanes",
    "candidate_bag",
    "derive_thesis",
    "dominant_tokens",
    "from_store",
    "maturity_for_members",
    "normalise_tokens",
    "persist_lanes",
    "similarity",
    "write_lanes_md",
]

#: Audience names, most demanding first.  A mixed lane reports the highest one.
AUDIENCE_PRIORITY: tuple[str, ...] = (
    "evaluators",
    "verifiers",
    "maintainers",
    "practitioners",
    "technical readers",
)

# English function words plus miner boilerplate ("Node X is a candidate
# primitive for <query>") and the replay-run marker.  None of these carry a
# theme, and every one of them is shared by unrelated candidates.
_STOPWORDS: frozenset[str] = frozenset(
    """
    a an and are as at be been being by can did do does for from had has have
    how if in into is it its may must no not of on onto or should so than that
    the their them then there these this those to up upon was were what when
    where which while who why will with within without would
    candidate candidates node nodes primitive primitives item items finding
    findings research relevant carries carry replay extract extractor source
    sources kind kinds lane lanes
    """.split()
)

# Kind markers -> audience.  First matching marker in this order wins, which is
# what makes a mixed lane's audience deterministic.
_KIND_AUDIENCE: tuple[tuple[str, str], ...] = (
    ("measured", "evaluators"),
    ("benchmark", "evaluators"),
    ("eval", "evaluators"),
    ("performance", "evaluators"),
    ("unreproduced", "verifiers"),
    ("unverified", "verifiers"),
    ("unfalsifiable", "verifiers"),
    ("claim", "verifiers"),
    ("contradict", "verifiers"),
    ("superseded", "maintainers"),
    ("decision", "maintainers"),
    ("regression", "maintainers"),
    ("novel", "practitioners"),
    ("primitive", "practitioners"),
    ("invariant", "practitioners"),
    ("enforcement", "practitioners"),
    ("boundary", "practitioners"),
    ("implementation", "practitioners"),
)

_WORD_RE = re.compile(r"[a-z0-9]+")

# Similarity contributions.
_COMMUNITY_BONUS = 0.15
_DEFAULT_THRESHOLD = 0.34
_SLUG_TOKENS = 3


# --------------------------------------------------------------------------- #
# Tokenisation
# --------------------------------------------------------------------------- #


def _singularise(token: str) -> str:
    """Very small, deterministic singulariser (``deltas`` -> ``delta``)."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def normalise_tokens(text: str | None) -> list[str]:
    """Lowercase ``text``, split on non-alphanumerics, drop stopwords, singularise."""
    if not text:
        return []
    out: list[str] = []
    for raw in _WORD_RE.findall(text.lower()):
        token = _singularise(raw)
        if len(token) < 3 or token in _STOPWORDS:
            continue
        out.append(token)
    return out


def candidate_bag(candidate: "LaneCandidate") -> dict[str, int]:
    """Weighted token bag for one candidate: title counts 2, summary counts 1."""
    bag: Counter[str] = Counter()
    for token in normalise_tokens(candidate.title):
        bag[token] += 2
    for token in normalise_tokens(candidate.summary):
        bag[token] += 1
    return dict(bag)


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    union = len(a | b)
    if union == 0:
        return 0.0
    return len(a & b) / union


def similarity(a: "LaneCandidate", b: "LaneCandidate", *, signature=None) -> float:
    """Deterministic similarity in ``[0, 1]``: lexical Jaccard + community bonus.

    ``signature`` may be a pre-computed ``{candidate_id: frozenset[str]}`` map
    (the theme-token signature used by :func:`build_lanes`).
    """
    if signature is None:
        sig_a = frozenset(candidate_bag(a))
        sig_b = frozenset(candidate_bag(b))
    else:
        sig_a = signature.get(a.id, frozenset())
        sig_b = signature.get(b.id, frozenset())
    score = _jaccard(sig_a, sig_b)
    score += _COMMUNITY_BONUS * _jaccard(a.communities, b.communities)
    return min(1.0, score)


# --------------------------------------------------------------------------- #
# Records
# --------------------------------------------------------------------------- #


@dataclass
class LaneCandidate:
    """One mined candidate, flattened for lane building.

    ``verified_refs`` / ``total_refs`` are the provenance counts; the two
    ``has_*`` flags are evidence annotations that :func:`from_store` leaves
    ``False`` (there is no measured-results table yet) and that
    :func:`attach_evidence` sets from verdict/result records.
    """

    id: int
    kind: str
    title: str
    summary: str
    provenance_refs: tuple[str, ...] = ()
    graph_nodes: tuple[str, ...] = ()
    communities: frozenset[int] = frozenset()
    score: float = 0.0
    state: str = ""
    verified_refs: int = 0
    total_refs: int = 0
    has_measured_result: bool = False
    has_external_verdict: bool = False


@dataclass
class Lane:
    """One publishable item, ready for a folder of its own."""

    slug: str
    title: str
    thesis: str
    thesis_source: str
    member_ids: tuple[int, ...]
    kinds: tuple[str, ...]
    maturity: str
    audience: str
    parent_slug: str | None = None
    split_reason: str | None = None

    @property
    def size(self) -> int:
        return len(self.member_ids)

    def as_dict(self) -> dict[str, Any]:
        """Plain, JSON-safe, key-sorted-ready form (no timestamps)."""
        return {
            "audience": self.audience,
            "kinds": list(self.kinds),
            "maturity": self.maturity,
            "member_ids": list(self.member_ids),
            "parent_slug": self.parent_slug,
            "slug": self.slug,
            "split_reason": self.split_reason,
            "thesis": self.thesis,
            "thesis_source": self.thesis_source,
            "title": self.title,
        }


# --------------------------------------------------------------------------- #
# Store -> LaneCandidate
# --------------------------------------------------------------------------- #


def _node_index(graph: Any) -> Mapping[str, Any]:
    if graph is None:
        return {}
    by_id = getattr(graph, "by_id", None)
    if callable(by_id):
        try:
            return by_id() or {}
        except Exception:  # pragma: no cover - defensive, never fatal
            return {}
    if isinstance(graph, Mapping):
        return graph
    return {}


def _communities(node_ids: Iterable[str], graph: Any) -> frozenset[int]:
    index = _node_index(graph)
    out: set[int] = set()
    for node_id in node_ids:
        node = index.get(str(node_id))
        if node is None:
            continue
        community = node.get("community") if isinstance(node, Mapping) else getattr(node, "community", None)
        if community is None:
            continue
        try:
            out.add(int(community))
        except (TypeError, ValueError):
            continue
    return frozenset(out)


def _decode(value: Any) -> Any:
    """Tolerate raw ``sqlite3`` rows: ``*_json`` columns may still be strings."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return value
    return value


def _refs_of(value: Any) -> list[str]:
    value = _decode(value)
    out: list[str] = []
    for item in value or ():
        if isinstance(item, Mapping):
            ref = item.get("ref") or item.get("source_ref")
        else:
            ref = item
        if ref:
            out.append(str(ref))
    return out


def from_store(candidate_rows: Sequence[Mapping[str, Any]], graph: Any = None) -> list[LaneCandidate]:
    """Build :class:`LaneCandidate` records from ``store`` candidate rows.

    ``graph`` is any object exposing ``by_id()`` (a :class:`resextract.kg.Graph`)
    or a plain mapping of node id -> node; each candidate's ``community`` set is
    attached when its ``graph_nodes_json`` ids resolve in the graph.
    """
    out: list[LaneCandidate] = []
    for row in candidate_rows:
        provenance = _decode(row.get("provenance_json")) or []
        if not isinstance(provenance, (list, tuple)):
            provenance = []
        refs = _refs_of(provenance)
        verified = sum(1 for item in provenance if isinstance(item, Mapping) and item.get("exists"))
        decoded_nodes = _decode(row.get("graph_nodes_json")) or []
        if not isinstance(decoded_nodes, (list, tuple)):
            decoded_nodes = []
        nodes = tuple(str(n) for n in decoded_nodes)
        try:
            score = float(row.get("score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        out.append(
            LaneCandidate(
                id=int(row["id"]),
                kind=str(row.get("kind") or ""),
                title=str(row.get("title") or ""),
                summary=str(row.get("summary") or ""),
                provenance_refs=tuple(refs),
                graph_nodes=nodes,
                communities=_communities(nodes, graph),
                score=score,
                state=str(row.get("state") or ""),
                verified_refs=verified,
                total_refs=len(refs),
            )
        )
    out.sort(key=lambda c: c.id)
    return out


def attach_evidence(
    candidates: Sequence[LaneCandidate],
    *,
    verdicts: Sequence[Any] = (),
    results: Sequence[Any] = (),
) -> list[LaneCandidate]:
    """Return copies of ``candidates`` with measured/external-verdict flags set.

    ``verdicts`` are records with a ``verdict`` and (optionally) a
    ``candidate_id``; ``results`` are records with a ``candidate_id``.
    """
    measured: set[int] = set()
    anchored: set[int] = set()
    for verdict in verdicts or ():
        record = verdict if isinstance(verdict, Mapping) else getattr(verdict, "__dict__", {})
        candidate_id = record.get("candidate_id")
        if candidate_id is None:
            continue
        if str(record.get("verdict") or "").upper() in ("CONFIRMS", "EXTENDS"):
            anchored.add(int(candidate_id))
    for result in results or ():
        record = result if isinstance(result, Mapping) else getattr(result, "__dict__", {})
        candidate_id = record.get("candidate_id")
        if candidate_id is None:
            continue
        measured.add(int(candidate_id))
    out = []
    for candidate in candidates:
        out.append(
            replace(
                candidate,
                has_measured_result=candidate.has_measured_result or candidate.id in measured,
                has_external_verdict=candidate.has_external_verdict or candidate.id in anchored,
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Derived labels (the honesty rule lives here)
# --------------------------------------------------------------------------- #


def dominant_tokens(
    members: Sequence[LaneCandidate], *, limit: int = _SLUG_TOKENS, shared_only: bool = False
) -> list[str]:
    """Most characteristic tokens of a lane, stable and order-independent.

    ``shared_only`` keeps tokens carried by at least two members when such
    tokens exist, so a slug names the *theme* rather than one node's local
    identifier.
    """
    bags = [candidate_bag(member) for member in members]
    counts: Counter[str] = Counter()
    for bag in bags:
        for token, weight in bag.items():
            counts[token] += weight
    if shared_only and len(bags) > 1:
        shared = {token for token in counts if sum(1 for bag in bags if token in bag) >= 2}
        if shared:
            counts = Counter({token: counts[token] for token in shared})
    if not counts:
        return []
    # Highest weight first, then alphabetical: never insertion order.
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [token for token, _ in ranked[:limit]]


def maturity_for_members(members: Sequence[LaneCandidate]) -> str:
    """Coarse ``low|medium|high`` from evidence strength only.

    Member level: ``high`` when the candidate has verified provenance **and** a
    measured result or an external verdict, ``medium`` when it has verified
    provenance, ``low`` otherwise.  Lane level: ``high`` when every member is
    high; ``medium`` when at least half the members are non-low; else ``low``.
    """
    levels: list[str] = []
    for member in members:
        if member.verified_refs <= 0:
            levels.append("low")
        elif member.has_measured_result or member.has_external_verdict:
            levels.append("high")
        else:
            levels.append("medium")
    if not levels:
        return "low"
    if all(level == "high" for level in levels):
        return "high"
    non_low = sum(1 for level in levels if level != "low")
    if non_low and non_low * 2 >= len(levels):
        return "medium"
    return "low"


def audience_for_kind(kind: str | None) -> str:
    """Deterministic audience for one candidate kind (first marker wins)."""
    text = (kind or "").lower()
    for marker, audience in _KIND_AUDIENCE:
        if marker in text:
            return audience
    return "technical readers"


def audience_for_members(members: Sequence[LaneCandidate]) -> str:
    """Highest-priority audience across the members' kinds and evidence."""
    audiences = {audience_for_kind(member.kind) for member in members}
    if any(member.has_measured_result for member in members):
        audiences.add("evaluators")
    if not audiences:
        return "technical readers"
    return max(audiences, key=lambda name: -AUDIENCE_PRIORITY.index(name))


def _kind_summary(members: Sequence[LaneCandidate]) -> str:
    counts = Counter(member.kind or "unknown" for member in members)
    return " + ".join(kind for kind, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def derive_thesis(members: Sequence[LaneCandidate], theme: str | None = None) -> str:
    """One deterministic sentence naming the members' kinds and count."""
    if not members:
        return "Derived lane: no members. This text was generated from stored candidates, not written by a model."
    counts = Counter(member.kind or "unknown" for member in members)
    kinds_txt = ", ".join(f"{kind} x{n}" for kind, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
    theme_txt = f" around the theme {theme}" if theme else ""
    return (
        f"Derived from {len(members)} mined candidate(s) of kind(s) {kinds_txt}{theme_txt}; "
        "this sentence was generated from stored candidate titles and summaries, not written by a model."
    )


# --------------------------------------------------------------------------- #
# Clustering
# --------------------------------------------------------------------------- #


def _signatures(candidates: Sequence[LaneCandidate]) -> dict[int, frozenset[str]]:
    """Theme tokens: drop tokens that occur in exactly one candidate."""
    frequency: Counter[str] = Counter()
    bags = {candidate.id: candidate_bag(candidate) for candidate in candidates}
    for bag in bags.values():
        for token in set(bag):
            frequency[token] += 1
    return {
        candidate_id: frozenset(token for token in bag if frequency[token] >= 2)
        for candidate_id, bag in bags.items()
    }


def _components(candidates: Sequence[LaneCandidate], threshold: float) -> list[list[LaneCandidate]]:
    """Single-link components over pairwise similarity, in candidate-id order."""
    ordered = sorted(candidates, key=lambda c: c.id)
    signature = _signatures(ordered)
    parent = {candidate.id: candidate.id for candidate in ordered}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, left in enumerate(ordered):
        for right in ordered[i + 1 :]:
            if similarity(left, right, signature=signature) >= threshold:
                root_a, root_b = find(left.id), find(right.id)
                if root_a != root_b:
                    parent[max(root_a, root_b)] = min(root_a, root_b)

    groups: dict[int, list[LaneCandidate]] = {}
    for candidate in ordered:
        groups.setdefault(find(candidate.id), []).append(candidate)
    return [groups[root] for root in sorted(groups)]


def _group_similarity(a: Sequence[LaneCandidate], b: Sequence[LaneCandidate], signature) -> float:
    return max(
        (similarity(x, y, signature=signature) for x in a for y in b),
        default=0.0,
    )


def _apply_max_lanes(groups: list[list[LaneCandidate]], max_lanes: int) -> list[list[LaneCandidate]]:
    """Merge the most similar groups until at most ``max_lanes`` remain."""
    if max_lanes is None or max_lanes < 1:
        return groups
    working = [list(group) for group in groups]
    while len(working) > max_lanes:
        all_candidates = [candidate for group in working for candidate in group]
        signature = _signatures(all_candidates)
        best: tuple[float, int, int] | None = None
        for i in range(len(working)):
            for j in range(i + 1, len(working)):
                score = _group_similarity(working[i], working[j], signature)
                key = (-score, min(c.id for c in working[i]), min(c.id for c in working[j]))
                if best is None or key < best[0]:
                    best = (key, i, j)  # type: ignore[assignment]
        _, i, j = best  # type: ignore[misc]
        working[i] = sorted(working[i] + working[j], key=lambda c: c.id)
        working.pop(j)
    return [sorted(group, key=lambda c: c.id) for group in working]


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #


def _lane_from_members(members: Sequence[LaneCandidate], *, used_slugs: set[str] | None = None) -> Lane:
    members = sorted(members, key=lambda c: c.id)
    tokens = dominant_tokens(members, shared_only=True)
    base = "-".join(tokens) if tokens else f"lane-{members[0].id}" if members else "lane-empty"
    slug = base
    if used_slugs is not None:
        suffix = 2
        while slug in used_slugs:
            slug = f"{base}-{suffix}"
            suffix += 1
        used_slugs.add(slug)
    if tokens:
        label = " ".join(token.title() for token in tokens)
    else:
        label = f"Lane {members[0].id}" if members else "Empty lane"
    title = f"{label} - {_kind_summary(members)}" if members else label
    return Lane(
        slug=slug,
        title=title,
        thesis=derive_thesis(members, theme="-".join(tokens) if tokens else None),
        thesis_source="derived",
        member_ids=tuple(member.id for member in members),
        kinds=tuple(sorted({member.kind or "unknown" for member in members})),
        maturity=maturity_for_members(members),
        audience=audience_for_members(members),
    )


def build_lanes(
    candidates: Sequence[LaneCandidate],
    *,
    min_size: int = 1,
    max_lanes: int | None = None,
    similarity_threshold: float = _DEFAULT_THRESHOLD,
) -> list[Lane]:
    """Group candidates into one lane per publishable item.

    ``min_size`` drops groups smaller than that (the candidates stay in the
    store; no lane is published for them).  ``max_lanes`` merges the most
    similar groups instead of dropping anything.  The returned list is sorted
    by ``(slug, first member id)`` — never by input order.
    """
    ordered = sorted(candidates, key=lambda c: c.id)
    if not ordered:
        return []
    groups = _components(ordered, similarity_threshold)
    if min_size and min_size > 1:
        groups = [group for group in groups if len(group) >= min_size]
    groups = _apply_max_lanes(groups, max_lanes) if max_lanes else groups
    # Deterministic lane ordering before slug disambiguation.
    groups.sort(key=lambda group: (dominant_tokens(group), min(c.id for c in group)))
    used: set[str] = set()
    lanes = [_lane_from_members(group, used_slugs=used) for group in groups]
    lanes.sort(key=lambda lane: (lane.slug, lane.member_ids[0] if lane.member_ids else -1))
    return lanes


# --------------------------------------------------------------------------- #
# Persistence and rendering
# --------------------------------------------------------------------------- #


def _connection(store: Any) -> tuple[sqlite3.Connection, bool]:
    """Accept a live connection, a path, or the ``resextract.store`` module."""
    if isinstance(store, sqlite3.Connection):
        return store, False
    if isinstance(store, (str, os.PathLike)):
        return _store.connect(store), True
    connect = getattr(store, "connect", None)
    if callable(connect):
        return connect(), True
    raise TypeError(f"cannot use {type(store).__name__} as a store; pass a sqlite3.Connection or a path")


def persist_lanes(
    lanes: Sequence[Lane],
    store: Any,
    target: str,
    *,
    types: Mapping[str, str] | None = None,
    status: str = "draft",
) -> list[int]:
    """Upsert lanes via :mod:`resextract.store`; idempotent per ``(target, slug)``.

    ``types`` optionally maps ``slug -> lane type`` (from
    :mod:`resextract.lanes.classify`); without it the ``type`` column is NULL,
    which the CHECK vocabulary allows.  A second call with the same input
    updates the same rows and never duplicates them.  ``parent_lane_id`` is
    resolved from ``parent_slug`` when the parent row already exists.
    """
    con, owned = _connection(store)
    try:
        ids: list[int] = []
        ordered = sorted(lanes, key=lambda lane: (lane.slug, lane.member_ids[0] if lane.member_ids else -1))
        for lane in ordered:
            existing = _store.get_lane_by_slug(con, target, lane.slug)
            parent_id = None
            if lane.parent_slug:
                parent = _store.get_lane_by_slug(con, target, lane.parent_slug)
                parent_id = parent["id"] if parent else None
            lane_id = _store.upsert_lane(
                con,
                id=existing["id"] if existing else None,
                target=target,
                slug=lane.slug,
                title=lane.title,
                thesis=lane.thesis,
                audience=lane.audience,
                type=(types or {}).get(lane.slug),
                parent_lane_id=parent_id,
                maturity=lane.maturity,
                status=status,
            )
            ids.append(lane_id)
        return ids
    finally:
        if owned:
            con.close()


def _lane_payload(lane: Lane, classifications: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = lane.as_dict()
    entry = (classifications or {}).get(lane.slug)
    if entry is not None:
        payload["type"] = getattr(entry, "type", None) or (entry.get("type") if isinstance(entry, Mapping) else None)
        payload["rationale"] = getattr(entry, "rationale", None) or (
            entry.get("rationale") if isinstance(entry, Mapping) else None
        )
        guards = getattr(entry, "guards", None)
        if guards is None and isinstance(entry, Mapping):
            guards = entry.get("guards")
        if guards is not None:
            payload["guards"] = {str(k): bool(v) for k, v in dict(guards).items()}
    return payload


def write_lanes_md(
    lanes: Sequence[Lane],
    out_dir: str | os.PathLike[str],
    *,
    classifications: Mapping[str, Any] | None = None,
) -> tuple[Path, Path]:
    """Write deterministic ``LANES.md`` + ``lanes.json`` (``sort_keys=True``).

    No timestamps and no input-order dependence: the same lanes always produce
    byte-identical files.
    """
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    ordered = sorted(lanes, key=lambda lane: (lane.slug, lane.member_ids[0] if lane.member_ids else -1))
    payload = {"lanes": [_lane_payload(lane, classifications) for lane in ordered]}
    json_path = directory / "lanes.json"
    json_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Lanes",
        "",
        "<!-- generated by resextract.lanes.build; deterministic: no timestamps, no input-order dependence -->",
        "",
        "One lane = one folder = one publishable item.",
        "",
    ]
    for lane in ordered:
        entry = _lane_payload(lane, classifications)
        lines.append(f"## {lane.slug}")
        lines.append("")
        lines.append(f"- title: {lane.title}")
        lines.append(f"- thesis ({lane.thesis_source}): {lane.thesis}")
        lines.append(f"- members: {', '.join(str(m) for m in lane.member_ids) or 'none'}")
        lines.append(f"- kinds: {', '.join(lane.kinds) or 'unknown'}")
        lines.append(f"- maturity: {lane.maturity}")
        lines.append(f"- audience: {lane.audience}")
        lines.append(f"- parent_slug: {lane.parent_slug or '-'}")
        if lane.split_reason:
            lines.append(f"- split_reason: {lane.split_reason}")
        if entry.get("type"):
            lines.append(f"- type: {entry['type']}")
        if entry.get("rationale"):
            lines.append(f"- rationale: {entry['rationale']}")
        lines.append("")
    md_path = directory / "LANES.md"
    md_path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    return md_path, json_path
