"""``resextract materialize`` — lane → material → docket, end to end.

This is the module that turns the *parts* (U5.1's copy engine, U5.2's folder
assembler + verifier, the store) into one finished artifact produced by a
single command.  Nothing here calls a model.

The job, in one paragraph: read a :class:`LaneSpec` (from the ``lanes`` table or
from a JSON escape hatch), turn every provenance reference it carries into a
**containment-checked** :class:`~resextract.docket.copy.CopyRequest`, copy the
material the lane's claims actually rest on out of the read-only target repo,
assemble the docket from *those copies* (never re-reading the source repo), run
:func:`~resextract.docket.assemble.verify_docket` and fail loudly if it is not
ok, then upsert the ``dockets`` row.  It is idempotent: a second run reports
``unchanged`` copies, preserves ``ITEM.md.r1``, appends (never truncates)
``HISTORY.md``, and updates — never duplicates — the ``dockets`` row.

Two honesty guards, both red→green tested in
``tests/test_docket_materialize.py``:

* a lane whose every reference is unresolvable/uncopyable **refuses** to
  materialize (:class:`MaterializeRefused`) and writes nothing — no half-docket;
* a reference that escapes the target root (``../``, ``/etc/passwd``, a symlink)
  is recorded as unresolved and is **never copied**.

Unresolvable references are never silently dropped: they are carried in
:attr:`MaterializedDocket.unresolved_refs` with a machine-readable reason.

U5.5 — commit-pinned material and a sealed window
=================================================

A live acceptance target is written by somebody else.  ``Copier`` reads the
working tree, so a docket that records ``head_sha = A`` and copies afterwards can
hold bytes that **no commit ever contained** — its "verifiable at commit A" claim
would simply be false.  Two mechanisms close that hole, and one deliberate
carve-out keeps the highest-value material:

* :data:`SOURCE_MODES` — ``commit`` (the default) resolves every request through
  :class:`~resextract.docket.git_source.GitObjectSource` at the recorded commit
  and records the **blob sha**; ``working-tree`` is an explicit opt-out that says
  so in the manifest.  **There is no silent fallback**: a path that is untracked
  at that commit (or a target that is not a git repo) is copied from the working
  tree but is marked ``unpinned=true`` with a machine-readable ``reason``
  (``untracked_at_commit`` / ``not_a_git_repo``), listed in
  :attr:`MaterializedDocket.unpinned_material`, and printed as a warning.
  ``unpinned_material`` is a **report field on the returned result, not a
  MANIFEST key**: ``MANIFEST.json`` has no such key and folds the same fact into
  ``material[].note`` (beside ``material[].unpinned`` / ``resolved_from``).  The
  alternative — refusing to materialize — would silently drop the untracked
  ``.lane-j-scratch/`` monograph and evidence review from every docket.
* **tree-first resolution** in ``commit`` mode: the *commit* is asked before the
  working tree, because pinning exists to carry the bytes that existed at commit
  X.  A path the commit holds is material even when the working tree has moved on
  — the extreme case being **deletion**, where the blob is still in the object
  store and is exactly what a docket should carry.  ``not_a_file_in_target`` is
  kept only for a path absent from **both** the commit and the working tree (a
  path that is a directory or symlink at the commit is unchanged: still
  ``not_a_file_in_target`` when it is also gone from disk).  The content scan
  still runs over the **pinned** bytes, so a secret living only in committed
  content is refused, never copied.
* the **sealed window**: the target is shown quiescent before the run
  (:func:`~resextract.refresh.writer.assert_quiescent`) and HEAD is re-read after
  the copies and assembly.  A HEAD that moved marks the docket
  ``freshness.state="needs_rework"`` — the docket is still produced, but it is
  honest about being mid-move.

Refusals are the **union of two passes** — the working-tree pass and the
pinned-bytes pass — and the overlap is structural rather than re-implemented.
The working-tree :class:`~resextract.docket.copy.Copier` runs its own predicates
first (containment, symlink, secret path, secret content, caps) and its outcome is
kept verbatim; pinned bytes are staged into a mirror tree and put through **the
same Copier**, so pinned bytes cannot bypass any predicate.  Both modes reach the
same outcome on four cases, none of which needs bytes on disk to decide:

* a **secret path** — refused identically in both modes;
* a **containment escape** — an *unresolved ref* (reason ``outside_target_root``)
  in both modes;
* a ref under **``.worktrees/``** — an *unresolved ref* (reason ``unsafe_path``)
  in both modes, **not** a refusal: it is never walked and never copied;
* a secret present **only** in the working tree — refused identically in both
  modes.

There is exactly one deliberate **asymmetry**, and it is the safety win, not a
parity bug: a secret present **only** in committed content is **refused by the
commit path** while the working-tree path copies the clean-looking working-tree
bytes.  The pinned path never relaxes the content scan.  (``.worktrees/`` is an
unresolved reference, not a refusal, wherever it is named.)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from resextract.docket.assemble import (
    EvidenceItem,
    assemble as assemble_docket,
    material_report_from_docket,
    verify_docket,
)
from resextract.docket.copy import (
    CopyItem,
    CopyPlan,
    CopyReport,
    CopyRequest,
    Copier,
    is_binary,
    sha256_file,
)
from resextract.docket.git_source import (
    CommitNotFound,
    GitCommandError,
    GitObjectSource,
    PathIsDirectoryAtCommit,
    PathIsSymlinkAtCommit,
    PathNotFoundAtCommit,
    PinnedFile,
    PinnedIntegrityError,
    SourcePathRefused,
    commit_exists,
    normalise_repo_relative,
    verify_pinned,
)
from resextract.docket.manifest import (
    PRODUCERS,
    producer_gate_reason,
    split_ref,
    write_manifest,
)
from resextract.refresh.writer import TargetBusyError, WriterSignal, assert_quiescent
from resextract import store as _store

__all__ = [
    "CATEGORY_BY_EXT",
    "DEFAULT_DOCKET_ROOT",
    "DEFAULT_WINDOW_S",
    "LaneSpec",
    "MaterializeError",
    "MaterializeRefused",
    "MaterializedDocket",
    "PromotionRefused",
    "MemberSpec",
    "RefPlan",
    "SOURCE_MODES",
    "TargetBusyError",
    "UnresolvedRef",
    "WriterSignal",
    "derive_producer",
    "lane_member_candidates",
    "materialize_lane",
    "model_id_for",
    "read_head_sha",
    "refs_to_copy_requests",
    "resolve_target_root",
    "target_category",
]

DEFAULT_DOCKET_ROOT = "dockets"
DEFAULT_GRAPH_REL = os.path.join("state", "kg")

#: Source-selection vocabulary.  ``commit`` pins at the recorded HEAD (default);
#: ``working-tree`` is the explicit, self-declaring opt-out.
SOURCE_MODES: tuple[str, ...] = ("commit", "working-tree")

#: Quiescence window, in seconds, observed before a run copies anything.
DEFAULT_WINDOW_S = 5.0

#: Extension → material folder.  The four folders are the copy plan's convention
#: (``material/{code,docs,figures,data}/``); anything unknown lands in ``data``.
CATEGORY_BY_EXT: dict[str, str] = {
    # code
    ".py": "code", ".ts": "code", ".tsx": "code", ".js": "code", ".jsx": "code",
    ".mjs": "code", ".cjs": "code", ".go": "code", ".rs": "code", ".java": "code",
    ".rb": "code", ".sh": "code", ".bash": "code", ".zsh": "code", ".c": "code",
    ".h": "code", ".cc": "code", ".cpp": "code", ".hpp": "code", ".cs": "code",
    ".kt": "code", ".swift": "code", ".sql": "code", ".lua": "code", ".php": "code",
    ".pl": "code", ".r": "code", ".jl": "code", ".scala": "code", ".vue": "code",
    # docs
    ".md": "docs", ".markdown": "docs", ".txt": "docs", ".rst": "docs",
    ".adoc": "docs", ".cff": "docs", ".tex": "docs", ".bib": "docs",
    ".org": "docs", ".1": "docs", ".license": "docs",
    # figures
    ".png": "figures", ".jpg": "figures", ".jpeg": "figures", ".gif": "figures",
    ".svg": "figures", ".webp": "figures", ".pdf": "figures", ".eps": "figures",
    ".bmp": "figures", ".tiff": "figures", ".drawio": "figures",
    # data
    ".json": "data", ".jsonl": "data", ".ndjson": "data", ".csv": "data",
    ".tsv": "data", ".yaml": "data", ".yml": "data", ".toml": "data",
    ".xml": "data", ".ini": "data", ".cfg": "data", ".parquet": "data",
    ".npy": "data", ".npz": "data", ".sqlite": "data", ".db": "data",
}

#: ``path:L120`` / ``path:L120-L160`` — the graph-node-id shape U2.1 reported
#: (e.g. ``src/decisions.ts:L1``).  ``split_ref`` already handles ``#L`` spans.
_COLON_SPAN = re.compile(
    r"^(?P<path>.+):L(?P<lo>\d+)(?:-L?(?P<hi>\d+))?$"
)
_SOURCE_LOC = re.compile(r"^L?(?P<lo>\d+)(?:-L?(?P<hi>\d+))?$")
_GIT_TIMEOUT_S = 10

_VERDICT_BY_STATE = {
    "confirmed": "CONFIRMS",
    "confirms": "CONFIRMS",
    "verified": "CONFIRMS",
    "extends": "EXTENDS",
    "extended": "EXTENDS",
    "contradicts": "CONTRADICTS",
    "contradicted": "CONTRADICTS",
    "refuted": "CONTRADICTS",
}

#: Reasons an entry can be unpinned.  ``None`` means "this entry is pinned".
UNPINNED_REASONS: tuple[str, ...] = (
    "untracked_at_commit",
    "not_a_git_repo",
    "commit_not_found",
    "source_mode_working_tree",
)


# --------------------------------------------------------------------------- #
# errors
# --------------------------------------------------------------------------- #


class MaterializeError(RuntimeError):
    """A hard failure while materializing (assembly/verification did not hold)."""


class MaterializeRefused(MaterializeError):
    """Raised instead of materializing a lane whose evidence cannot be copied.

    ``reasons`` names *why*, one line per cause, so a refusal is diagnosable
    without re-running with a debugger.
    """

    def __init__(self, reasons: Iterable[str]) -> None:
        self.reasons = list(dict.fromkeys(str(r) for r in reasons if r))
        super().__init__("materialize refused: " + "; ".join(self.reasons))


class PromotionRefused(MaterializeError):
    """Raised when a caller explicitly asks for ``status="ready"`` on a non-model docket.

    The gate's *default* behaviour is to build the docket **labelled**
    ``draft`` — a replay docket is still an honest docket.  A caller that
    explicitly requests a promotion attempt gets this refusal instead of a
    silently promoted artifact.
    """

    def __init__(self, reasons: Iterable[str], *, producer: str = "unknown") -> None:
        self.reasons = list(dict.fromkeys(str(r) for r in reasons if r))
        self.producer = producer
        super().__init__("promotion refused: " + "; ".join(self.reasons))


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #


def _short(sha: str | None, width: int = 8) -> str:
    return (sha or "?")[:width]


def _warn(message: str) -> None:
    """Print one warning line naming the thing that is wrong (never silent)."""
    print(f"WARNING: {message}", file=sys.stderr)


def _mtime_utc(path: str) -> str | None:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


# --------------------------------------------------------------------------- #
# lane spec
# --------------------------------------------------------------------------- #


@dataclass
class MemberSpec:
    """One claim-bearing member of a lane (built from one candidate row)."""

    id: str
    kind: str = "claim"
    title: str = ""
    summary: str = ""
    provenance_refs: list[str] = field(default_factory=list)
    confidence: float | None = None
    verification_state: str = "unverified"
    #: U5.13: the producer class of the candidate row this member came from.
    #: ``unknown`` when the spec did not say -- which, like every other
    #: non-``model`` value, may not back a ``CONFIRMS`` claim.
    producer: str = "unknown"
    #: U5.15: the candidate row this member came from -- the join key to a
    #: verdict (``verdicts.claim_id = claims.id``, ``claims.candidate_id =
    #: candidates.id``).  ``None`` on the curated ``LaneSpec.from_json`` path,
    #: which has no store row and therefore no verdict.
    candidate_id: int | None = None
    #: U5.15: the ``verdicts`` row that assessed this claim, resolved from the
    #: store and attached by :func:`_attach_verdicts`.  ``verdict``/``verdict_id``
    #: come from ``verdicts.verdict``, ``verdict_producer`` from
    #: ``verdicts.producer``.  All ``None`` = **no verdict row**: nothing has
    #: assessed this claim, which is why it can never render ``CONFIRMS``.
    verdict: str | None = None
    verdict_producer: str | None = None
    verdict_id: int | None = None


@dataclass
class LaneSpec:
    """A lane and the members whose provenance refs must be materialized."""

    slug: str
    title: str = ""
    thesis: str = ""
    audience: str = ""
    type: str = "memo"  # noqa: A003 - matches the store/schema vocabulary
    members: list[MemberSpec] = field(default_factory=list)
    target_slug: str = ""
    head_sha: str | None = None

    # -- constructors --------------------------------------------------------

    @classmethod
    def from_store(
        cls,
        lane_row: Mapping[str, Any],
        candidate_rows: Iterable[Mapping[str, Any]] = (),
    ) -> "LaneSpec":
        """Build a spec from a ``lanes`` row plus its candidate rows."""
        members: list[MemberSpec] = []
        for index, row in enumerate(candidate_rows):
            cid = row.get("id")
            mid = f"C{cid}" if cid is not None else f"C{index + 1}"
            refs: list[str] = []
            for ref in _candidate_refs(row):
                if ref not in refs:
                    refs.append(ref)
            members.append(
                MemberSpec(
                    id=str(mid),
                    kind=str(row.get("kind") or "claim"),
                    title=str(row.get("title") or ""),
                    summary=str(row.get("summary") or ""),
                    provenance_refs=refs,
                    confidence=_as_float(row.get("score")),
                    verification_state=str(row.get("state") or "unverified"),
                    producer=str(row.get("producer") or "unknown"),
                    candidate_id=int(cid) if cid is not None else None,
                )
            )
        return cls(
            slug=str(lane_row.get("slug") or ""),
            title=str(lane_row.get("title") or ""),
            thesis=str(lane_row.get("thesis") or ""),
            audience=str(lane_row.get("audience") or ""),
            type=str(lane_row.get("type") or lane_row.get("kind") or "memo"),
            members=members,
            target_slug=str(lane_row.get("target") or ""),
            head_sha=lane_row.get("head_sha"),
        )

    @classmethod
    def from_json(cls, path: str | os.PathLike[str]) -> "LaneSpec":
        """Load a spec from a JSON file (the curated-docket escape hatch).

        Accepts ``members[].provenance_refs`` or ``members[].refs``, and a member
        ``kind`` that doubles as the member class.  Unknown keys are ignored so
        a hand-curated file stays readable; missing required ones are defaulted
        rather than raising a traceback at the user.
        """
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: lane spec must be a JSON object")
        members: list[MemberSpec] = []
        for index, entry in enumerate(raw.get("members") or ()):
            if not isinstance(entry, dict):
                raise ValueError(f"{path}: members[{index}] must be an object")
            refs = entry.get("provenance_refs", entry.get("refs", [])) or []
            if isinstance(refs, str):
                refs = [refs]
            members.append(
                MemberSpec(
                    id=str(entry.get("id") or f"C{index + 1}"),
                    kind=str(entry.get("kind") or "claim"),
                    title=str(entry.get("title") or ""),
                    summary=str(entry.get("summary") or ""),
                    provenance_refs=[str(r) for r in refs],
                    confidence=_as_float(entry.get("confidence", entry.get("score"))),
                    verification_state=str(
                        entry.get("verification_state")
                        or entry.get("state")
                        or "unverified"
                    ),
                    producer=str(entry.get("producer") or "unknown"),
                )
            )
        lane_type = str(raw.get("type") or raw.get("kind") or "memo")
        return cls(
            slug=str(raw.get("slug") or ""),
            title=str(raw.get("title") or ""),
            thesis=str(raw.get("thesis") or ""),
            audience=str(raw.get("audience") or ""),
            type=lane_type,
            members=members,
            target_slug=str(raw.get("target_slug") or raw.get("target") or ""),
            head_sha=raw.get("head_sha"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "thesis": self.thesis,
            "audience": self.audience,
            "type": self.type,
            "target_slug": self.target_slug,
            "head_sha": self.head_sha,
            "members": [
                {
                    "id": m.id,
                    "kind": m.kind,
                    "title": m.title,
                    "summary": m.summary,
                    "provenance_refs": list(m.provenance_refs),
                    "confidence": m.confidence,
                    "verification_state": m.verification_state,
                }
                for m in self.members
            ],
        }


def _as_float(value: Any) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _candidate_refs(row: Mapping[str, Any]) -> list[str]:
    """Every provenance ref a candidate row carries, in row order.

    The mining units store ``provenance_json`` as a list of dicts such as
    ``{"kind": "graph_node", "ref": "src_lease_hold", ...}`` and
    ``{"kind": "file_lines", "ref": "src/lease.ts#L169", ...}``; graph node ids
    also live in ``graph_nodes_json``.  Both shapes are read, as are plain-string
    provenance lists (older / hand-written rows).
    """
    out: list[str] = []
    for key in ("provenance_json", "provenance"):
        raw = row.get(key)
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (ValueError, TypeError):
                raw = [raw]
        if not isinstance(raw, (list, tuple)):
            continue
        for entry in raw:
            if isinstance(entry, str):
                out.append(entry)
            elif isinstance(entry, Mapping):
                ref = entry.get("ref") or entry.get("path") or entry.get("node")
                if ref:
                    out.append(str(ref))
    for key in ("graph_nodes_json", "graph_nodes"):
        raw = row.get(key)
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (ValueError, TypeError):
                raw = [raw]
        if isinstance(raw, (list, tuple)):
            for node in raw:
                if isinstance(node, str):
                    out.append(f"graph:{node}")
                elif isinstance(node, Mapping) and node.get("id"):
                    out.append(f"graph:{node['id']}")
    return out


# --------------------------------------------------------------------------- #
# producer derivation (U5.7)
# --------------------------------------------------------------------------- #


def lane_member_candidates(
    con: Any, *, target_slug: str, lane_slug: str
) -> list[dict[str, Any]]:
    """A lane's member candidate rows, read through the store's own join.

    The store owns both facts this needs — the lane<->candidate relation
    (:func:`store.lane_candidate_ids`) and the producer vocabulary
    (:func:`store.candidates_by_producer`) — so this reads them rather than
    re-deriving either.  An unknown lane (or an unreadable store) yields ``[]``,
    which derives ``unknown``: the gate's safe side.
    """
    if not lane_slug:
        return []
    lane_row = _store.get_lane_by_slug(con, target_slug, lane_slug)
    if not lane_row:
        return []
    by_id = {
        int(row["id"]): row
        for row in _store.candidates_by_producer(con)
        if row.get("id") is not None
    }
    return [
        by_id[cid]
        for cid in _store.lane_candidate_ids(con, int(lane_row["id"]))
        if cid in by_id
    ]


def _normalise_producer(raw: Any) -> str:
    """Exact-match vocabulary membership: the string, or ``unknown``.

    U5.15.  No ``strip()``, no ``lower()``: ``"Model"``/``"MODEL"``/``"  model  "``
    are **not** ``model`` and collapse to ``unknown`` -- the same
    reject-don't-coerce rule ``assess.verdicts`` applies when it raises
    :class:`~resextract.assess.verdicts.ProducerDeclarationError`.  A non-string
    (dict, list, int) is likewise not a declaration.  This is the *one*
    normalisation shared by :func:`derive_producer` and :func:`_claim_producer`.
    """
    if isinstance(raw, str) and raw in PRODUCERS:
        return raw
    return "unknown"


#: The producer classes a **claim** may render -- a strict *subset* of
#: :data:`PRODUCERS`.  ``fixture`` (harness/verification material) and
#: ``unknown`` are real vocabulary values, but neither is a claim-provenance
#: class a reader may rely on, and ``mixed`` is aggregate-only (a single member
#: cannot be a mixture).  Everything outside this subset collapses to
#: ``unknown`` -- the fail-closed direction, because only ``model`` grants model
#: standing (:func:`store.producer_is_model`) and ``replay`` is the only other
#: honest mining provenance.  It is **named** so the subset says *why* it is a
#: subset, instead of an inline literal tuple restated at each site.
_CLAIM_PRODUCER_VOCAB: tuple[str, ...] = (_store.MODEL_PRODUCER, "replay")


def _claim_level_producer(raw: Any) -> str:
    """The **one** claim-level rendering: exact vocabulary, then the subset collapse.

    U5.19.  :func:`_normalise_producer` is the one *normalisation* (exact
    membership, no ``strip``/``lower``); this is the one *collapse* applied on
    top of it.  Before this unit the collapse lived inline in
    :func:`_claim_producer` only, so :func:`_claim_for`'s verdict branch skipped
    it and rendered a fixture verdict as ``producer="fixture"`` where the other
    two sites said ``unknown`` -- a third rendering site the two-way table did
    not compare.  All three sites now route through this function.
    """
    value = _normalise_producer(raw)
    return value if value in _CLAIM_PRODUCER_VOCAB else "unknown"


def derive_producer(member_rows: Iterable[Mapping[str, Any]]) -> str:
    """Collapse member-candidate producers into the docket's provenance class.

    all ``model`` ⇒ ``model``; any ``replay`` ⇒ ``replay``; a mixture of model and
    non-model ⇒ ``mixed``; nothing recognisable (no rows, or rows whose producer
    is ``fixture``/``unknown``/absent) ⇒ ``unknown``.  Every value other than
    ``model`` blocks promotion, so the fixture case collapses to the safe answer
    instead of inventing a fifth outcome.
    """
    seen: set[str] = set()
    for row in member_rows or ():
        raw = row.get("producer") if isinstance(row, Mapping) else None
        seen.add(_normalise_producer(raw))
    if not seen:
        return "unknown"
    if seen == {_store.MODEL_PRODUCER}:
        return "model"
    if "replay" in seen:
        return "replay"
    if "model" in seen:
        return "mixed"
    return "unknown"


def model_id_for(producer: str, member_rows: Iterable[Mapping[str, Any]]) -> str | None:
    """The model id to record, or ``None``.

    Only a ``model`` producer may name a model: a model id on a replay docket
    would be exactly the indistinguishability U5.7 exists to remove.
    """
    if producer != "model":
        return None
    for row in member_rows or ():
        value = row.get("model") if isinstance(row, Mapping) else None
        if value:
            return str(value)
    return None


# --------------------------------------------------------------------------- #
# refs → copy requests
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class UnresolvedRef:
    """A reference that could not become a verifiable copy request."""

    ref: str
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"ref": self.ref, "reason": self.reason, "detail": self.detail}

    def __str__(self) -> str:  # pragma: no cover - display helper
        tail = f" ({self.detail})" if self.detail else ""
        return f"{self.ref}: {self.reason}{tail}"


@dataclass
class RefPlan:
    """The outcome of turning refs into copy requests."""

    requests: list[CopyRequest] = field(default_factory=list)
    by_ref: dict[str, str] = field(default_factory=dict)  # ref → dest_rel
    unresolved: list[UnresolvedRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "requests": [
                {
                    "src": r.src,
                    "dest_rel": r.dest_rel,
                    "reason": r.reason,
                    "excerpt": list(r.excerpt) if r.excerpt else None,
                }
                for r in self.requests
            ],
            "by_ref": dict(sorted(self.by_ref.items())),
            "unresolved": [u.to_dict() for u in self.unresolved],
        }


def target_category(path: str) -> str:
    """``code``/``docs``/``figures``/``data`` for ``path``, by extension."""
    return CATEGORY_BY_EXT.get(os.path.splitext(path)[1].lower(), "data")


def _dest_for(rel: str, used: dict[str, str]) -> str:
    rel = rel.replace(os.sep, "/").lstrip("/")
    base = os.path.basename(rel)
    category = target_category(base)
    dest = f"{category}/{base}"
    if used.get(dest, rel) != rel:
        stem, ext = os.path.splitext(base)
        digest = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:6]
        dest = f"{category}/{stem}-{digest}{ext}"
    return dest


def _contained(src: str, target_root: str) -> bool:
    real = os.path.realpath(src)
    root = os.path.realpath(target_root)
    return real == root or real.startswith(root + os.sep)


def _line_count(path: str) -> int:
    """Lines as ``readlines()`` would count them (what the verifier uses)."""
    try:
        with open(path, "rb") as fh:
            return len(fh.read().splitlines())
    except OSError:  # pragma: no cover - existence checked earlier
        return 0


def _read_head(target_root: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", target_root, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip()
    return sha or None


def read_head_sha(target_root: str, fallback: str | None = None) -> tuple[str | None, str]:
    """Return ``(head_sha, source)`` reading the target's real HEAD.

    ``source`` is ``"git"`` when ``git rev-parse HEAD`` answered and
    ``"lane_spec"`` when it did not (a fixture repo, a missing ``git``), in which
    case the spec's own ``head_sha`` is used and recorded honestly.
    """
    sha = _read_head(target_root)
    if sha:
        return sha, "git"
    return (fallback or None), "lane_spec"


def _resolve_one(
    ref: str,
    *,
    target_root: str,
    by_id: Mapping[str, Any] | None,
    graph_available: bool,
    reason_prefix: str,
    used: dict[str, str],
    pinned_source: GitObjectSource | None = None,
) -> tuple[CopyRequest | None, UnresolvedRef | None]:
    text = (ref or "").strip()
    if not text:
        return None, UnresolvedRef(ref, "empty_ref")
    kind, path, span = split_ref(text)
    if span is None:
        match = _COLON_SPAN.match(path)
        if match:
            path = match.group("path")
            span = (
                int(match.group("lo")),
                int(match.group("hi") or match.group("lo")),
            )
    if kind == "web":
        return None, UnresolvedRef(ref, "web_ref_not_local", text)
    if not path:
        return None, UnresolvedRef(ref, "empty_ref", text)

    # -- graph node ids (bare id, or an explicit ``graph:`` ref) -------------
    is_node = kind == "graph" or (by_id is not None and path in by_id)
    if is_node:
        if not graph_available or by_id is None:
            return None, UnresolvedRef(ref, "graph_unavailable", path)
        node = by_id.get(path)
        if node is None:
            return None, UnresolvedRef(ref, "graph_node_not_found", path)
        source_file = str(getattr(node, "source_file", "") or "").strip()
        if not source_file:
            kind_label = getattr(node, "type", None) or getattr(node, "file_type", None)
            return None, UnresolvedRef(
                ref, "graph_node_has_no_source_file", f"{path} ({kind_label})"
            )
        if span is None:
            loc = str(getattr(node, "source_location", "") or "").strip()
            match = _SOURCE_LOC.match(loc)
            if match:
                span = (
                    int(match.group("lo")),
                    int(match.group("hi") or match.group("lo")),
                )
        path = source_file

    # -- containment (realpath) before anything is read ----------------------
    src = path if os.path.isabs(path) else os.path.join(target_root, path)
    if not _contained(src, target_root):
        return None, UnresolvedRef(ref, "outside_target_root", src)
    src = os.path.realpath(src)

    tree_only: PinnedFile | None = None
    if not os.path.isfile(src):
        if pinned_source is None:
            return None, UnresolvedRef(ref, "not_a_file_in_target", src)
        # -- tree-first in commit mode ---------------------------------------
        # Pinning exists to carry the bytes that existed at commit X, so ask the
        # *commit* before the working tree.  A blob the commit holds is material
        # even when the working tree has moved on — the extreme case being
        # deletion, where the bytes are still in the object store and are exactly
        # what a docket should carry.  ``not_a_file_in_target`` survives ONLY for
        # a path absent from BOTH the commit and the working tree.
        probe_rel = os.path.relpath(src, os.path.realpath(target_root))
        try:
            probe_rel = normalise_repo_relative(probe_rel.replace(os.sep, "/"))
        except SourcePathRefused as exc:
            return None, UnresolvedRef(ref, "unsafe_path", str(exc))
        try:
            tree_only = pinned_source.resolve(probe_rel)
        except (
            PathNotFoundAtCommit,
            PathIsDirectoryAtCommit,
            PathIsSymlinkAtCommit,
            SourcePathRefused,
            CommitNotFound,
            GitCommandError,
        ):
            tree_only = None
        if tree_only is None:
            return None, UnresolvedRef(ref, "not_a_file_in_target", src)

    rel = os.path.relpath(src, os.path.realpath(target_root)).replace(os.sep, "/")
    # ``.worktrees/`` is where a foreign writer churns through live sibling
    # worktrees.  A ref naming it is an *unresolved ref* (reason ``unsafe_path``,
    # never a refusal) in BOTH source modes, so it can never be walked or copied.
    # (``normalise_repo_relative`` owns that rule.)
    try:
        rel = normalise_repo_relative(rel)
    except SourcePathRefused as exc:
        return None, UnresolvedRef(ref, "unsafe_path", str(exc))
    dest = _dest_for(rel, used)

    if span is not None:
        span = (int(span[0]), int(span[1]))
        if span[0] < 1 or span[1] < span[0]:
            return None, UnresolvedRef(ref, "invalid_span", f"{span[0]}-{span[1]}")
        if tree_only is not None:
            # there are no working-tree bytes to quote: the pinned blob is the
            # material, so the cited span is validated against *it*.
            body = tree_only.bytes_
            if b"\x00" in body:
                span = None
            else:
                lines = len(body.splitlines())
                if span[1] > lines:
                    return None, UnresolvedRef(
                        ref, "span_past_eof", f"L{span[0]}-L{span[1]} of {lines}"
                    )
        elif is_binary(src):
            span = None  # a byte range has no lines to quote
        else:
            lines = _line_count(src)
            if span[1] > lines:
                return None, UnresolvedRef(
                    ref, "span_past_eof", f"L{span[0]}-L{span[1]} of {lines}"
                )

    used.setdefault(dest, rel)
    return (
        CopyRequest(
            src=src,
            dest_rel=dest,
            reason=f"{reason_prefix}:{ref}",
            excerpt=span,
        ),
        None,
    )


def refs_to_copy_requests(
    refs: Iterable[str],
    *,
    target_root: str,
    graph: Any = None,
    reason_prefix: str = "materialize",
    pinned_source: GitObjectSource | None = None,
) -> RefPlan:
    """Turn every ref shape this build produces into a :class:`CopyRequest`.

    Handled shapes: ``file:path#L120-L160``, ``path#L120-L160``, ``path#L120``,
    ``path:L120`` (the graph-node-id shape U2.1 reported, e.g.
    ``src/decisions.ts:L1``), a bare graph node id (resolved through ``graph`` to
    its ``source_file`` — plus ``source_location`` when present), and a bare
    relative path with no line info.

    Every request is containment-checked against ``target_root`` by realpath
    *before* it is emitted, and destinations are deduplicated.  Anything that
    cannot be resolved is returned in :attr:`RefPlan.unresolved` with a
    machine-readable reason — never silently dropped.  A ref naming
    ``.worktrees/`` is an *unresolved ref* (reason ``unsafe_path``) in both source
    modes — reported, not refused.

    ``pinned_source`` is the commit-mode :class:`GitObjectSource`, or ``None`` for
    the working-tree mode.  When it is given, resolution is **tree-first**: a path
    the commit holds becomes a request even when the working tree no longer has it
    (deletion is the extreme case of drift), while ``not_a_file_in_target`` is
    reserved for a path absent from the commit *and* the working tree.

    ``graph`` may be a :class:`resextract.kg.Graph` or a plain node dict.
    """
    by_id: Mapping[str, Any] | None = None
    if graph is not None:
        if hasattr(graph, "by_id"):
            try:
                by_id = dict(graph.by_id())
            except Exception:  # noqa: BLE001 - a broken graph is not fatal here
                by_id = None
        elif isinstance(graph, Mapping):
            by_id = graph
        elif isinstance(graph, (list, tuple)):
            by_id = {
                str(getattr(n, "id", None) or (n.get("id") if isinstance(n, Mapping) else "")): n
                for n in graph
            }
            by_id.pop("", None)

    requests: list[CopyRequest] = []
    by_ref: dict[str, str] = {}
    unresolved: list[UnresolvedRef] = []
    used: dict[str, str] = {}
    by_dest: dict[str, CopyRequest] = {}

    for ref in refs or ():
        request, problem = _resolve_one(
            ref,
            target_root=target_root,
            by_id=by_id,
            graph_available=by_id is not None,
            reason_prefix=reason_prefix,
            used=used,
            pinned_source=pinned_source,
        )
        if request is None:
            assert problem is not None
            unresolved.append(problem)
            continue
        existing = by_dest.get(request.dest_rel)
        if existing is None:
            by_dest[request.dest_rel] = request
            requests.append(request)
        elif existing.excerpt is None and request.excerpt is not None:
            # keep the *deduplicated* request but carry the cited span forward so
            # EXCERPTS.md still records why the bytes matter.
            existing.excerpt = request.excerpt
        by_ref[ref] = request.dest_rel

    return RefPlan(requests=requests, by_ref=by_ref, unresolved=unresolved)


# --------------------------------------------------------------------------- #
# commit-pinned source resolution
# --------------------------------------------------------------------------- #


@dataclass
class _ResolvedSource:
    """Where one request's bytes will come from, and how that is recorded."""

    dest: str
    real_src: str
    rel: str
    request: CopyRequest | None = None
    pinned: PinnedFile | None = None
    resolved_from: str = "working_tree"
    unpinned: bool = True
    reason: str | None = None
    mtime: str | None = None
    refusal_reason: str | None = None


def _open_pinned_source(
    target_root: str, head_sha: str | None, head_source: str
) -> tuple[GitObjectSource | None, str | None]:
    """Return ``(source, why_it_is_unavailable)`` for commit-pinned reads.

    ``None`` as the source is *not* a licence to read the working tree silently:
    the caller records the returned reason on every entry and says so.
    """
    if not head_sha or head_source != "git":
        return None, "not_a_git_repo"
    if not commit_exists(target_root, head_sha):
        return None, "commit_not_found"
    try:
        return GitObjectSource(target_root, head_sha), None
    except (CommitNotFound, GitCommandError):
        return None, "commit_not_found"


def _resolve_sources(
    requests: Sequence[CopyRequest],
    *,
    wt_item_by_dest: Mapping[str, CopyItem],
    target_root: str,
    source_mode: str,
    pinned_source: GitObjectSource | None,
    pin_failure_reason: str | None,
) -> dict[str, _ResolvedSource]:
    """Decide, per request, whether its bytes are pinned or working-tree.

    A request the *working-tree* copier accepted is resolved here; a request it
    refused or capped is left alone, so its own refusal is kept verbatim and
    reaches both modes unchanged.  In ``commit`` mode a request the working tree
    cannot serve because the path is gone from disk is resolved **tree-first**
    anyway — that is the deleted-but-committed case, and its bytes come from the
    object store.
    """
    root_real = os.path.realpath(target_root)
    out: dict[str, _ResolvedSource] = {}
    for req in requests:
        wt_item = wt_item_by_dest.get(req.dest_rel)
        on_disk = os.path.isfile(req.src)
        if on_disk and (wt_item is None or wt_item.status != "copied"):
            continue
        if not on_disk and (source_mode != "commit" or pinned_source is None):
            # a deleted path is only material when a commit still holds it
            continue
        rel = os.path.relpath(req.src, root_real).replace(os.sep, "/")
        rec = _ResolvedSource(
            dest=req.dest_rel, real_src=req.src, rel=rel, request=req
        )

        if source_mode == "working-tree":
            rec.resolved_from = "working_tree"
            rec.unpinned = True
            rec.reason = "source_mode_working_tree"
            rec.mtime = _mtime_utc(req.src)
            out[req.dest_rel] = rec
            continue

        if pinned_source is None:
            rec.resolved_from = "working_tree"
            rec.unpinned = True
            rec.reason = pin_failure_reason or "not_a_git_repo"
            rec.mtime = _mtime_utc(req.src)
            out[req.dest_rel] = rec
            continue

        try:
            safe_rel = normalise_repo_relative(rel)
        except SourcePathRefused as exc:
            rec.refusal_reason = (
                "worktrees_refused"
                if ".worktrees" in rel.split("/")
                else "unsafe_path"
            )
            rec.reason = str(exc)
            out[req.dest_rel] = rec
            continue

        try:
            pinned = pinned_source.resolve(safe_rel)
        except PathNotFoundAtCommit:
            # The deliberate carve-out: untracked at that commit, but present in
            # the working tree.  Copy it — marked unpinned, never silently.
            rec.resolved_from = "working_tree"
            rec.unpinned = True
            rec.reason = "untracked_at_commit"
            rec.mtime = _mtime_utc(req.src)
            out[req.dest_rel] = rec
            continue
        except PathIsSymlinkAtCommit:
            rec.refusal_reason = "symlink"
            out[req.dest_rel] = rec
            continue
        except PathIsDirectoryAtCommit:
            rec.refusal_reason = "is_directory"
            out[req.dest_rel] = rec
            continue
        except SourcePathRefused as exc:
            rec.refusal_reason = "unsafe_path"
            rec.reason = str(exc)
            out[req.dest_rel] = rec
            continue
        except (CommitNotFound, GitCommandError) as exc:
            rec.refusal_reason = "git_error"
            rec.reason = f"{type(exc).__name__}: {exc}"
            out[req.dest_rel] = rec
            continue

        rec.pinned = pinned
        rec.resolved_from = "git_object"
        rec.unpinned = False
        rec.reason = None
        rec.mtime = None
        out[req.dest_rel] = rec
    return out


def _mirror_tree(
    resolutions: Mapping[str, _ResolvedSource], *, mirror_dir: str
) -> list[CopyRequest]:
    """Stage the bytes that will actually be copied into a private mirror tree.

    Pinned entries get the committed bytes (:meth:`PinnedFile.write_to`);
    unpinned entries get a copy of the working-tree bytes.  The *unmodified*
    :class:`Copier` is then run over this mirror, so every refusal predicate
    (secret path, secret content, caps, containment) sees exactly the bytes the
    docket would hold — pinned bytes cannot bypass any of them.
    """
    requests: list[CopyRequest] = []
    for dest in sorted(resolutions):
        rec = resolutions[dest]
        if rec.refusal_reason or rec.request is None:
            continue
        mirror_path = os.path.join(mirror_dir, *rec.rel.split("/"))
        os.makedirs(os.path.dirname(mirror_path), exist_ok=True)
        if rec.pinned is not None:
            rec.pinned.write_to(mirror_path)
        else:
            if os.path.islink(rec.real_src):
                rec.refusal_reason = "symlink"
                continue
            shutil.copyfile(rec.real_src, mirror_path)
        requests.append(
            CopyRequest(
                src=mirror_path,
                dest_rel=dest,
                reason=rec.request.reason,
                excerpt=rec.request.excerpt,
            )
        )
    return requests


def _merge_plan(
    wt_plan: CopyPlan,
    resolutions: Mapping[str, _ResolvedSource],
    mirror_items: Sequence[CopyItem],
) -> CopyPlan:
    """Combine the working-tree outcome with the mirror (pinned-byte) outcome.

    The working-tree item wins whenever it is not a plain ``copied`` — that is
    what makes a working-tree refusal identical in both modes.  For entries the
    working tree accepted, the mirror item (whose predicates ran over the pinned
    bytes) wins; a pinned-only refusal — a secret visible only in committed
    content — becomes a refusal here.  An entry the working tree could not serve
    at all (the tree-first, deleted-but-committed case) takes the mirror's
    verdict, whether that verdict is a copy or a refusal.
    """
    mirror_by_dest = {item.dest: item for item in mirror_items}
    items: list[CopyItem] = []
    for wt_item in wt_plan.items:
        rec = resolutions.get(wt_item.dest)
        if rec is None:
            items.append(wt_item)
            continue
        if rec.refusal_reason:
            items.append(
                CopyItem(
                    src=rec.real_src,
                    dest=wt_item.dest,
                    reason=wt_item.reason,
                    excerpt=wt_item.excerpt,
                    status="refused",
                    refusal_reason=rec.refusal_reason,
                )
            )
            continue
        mirror_item = mirror_by_dest.get(wt_item.dest)
        if wt_item.status == "copied":
            items.append(mirror_item if mirror_item is not None else wt_item)
            continue
        if mirror_item is not None:
            # tree-first: absent from the working tree, present at the commit
            items.append(mirror_item)
            continue
        items.append(wt_item)

    plan = CopyPlan()
    for item in sorted(items, key=lambda i: (i.dest, i.src)):
        plan.items.append(item)
        bucket = {
            "linked": plan.to_link,
            "refused": plan.refused,
            "missing": plan.missing,
        }.get(item.status, plan.to_copy)
        bucket.append(item)
    plan.total_bytes = sum(i.bytes for i in plan.to_copy)
    return plan


def _build_final_plan(
    ref_plan: RefPlan,
    wt_plan: CopyPlan,
    *,
    target_root: str,
    source_mode: str,
    pinned_source: GitObjectSource | None,
    pin_failure_reason: str | None,
    copier: Copier,
    docket_dir: str,
) -> tuple[str | None, CopyPlan, dict[str, _ResolvedSource], dict[str, str]]:
    """Resolve sources, stage the pinned subset, and return the merged plan."""
    wt_item_by_dest = {item.dest: item for item in wt_plan.items}
    resolutions = _resolve_sources(
        ref_plan.requests,
        wt_item_by_dest=wt_item_by_dest,
        target_root=target_root,
        source_mode=source_mode,
        pinned_source=pinned_source,
        pin_failure_reason=pin_failure_reason,
    )
    real_src_by_dest = {d: r.real_src for d, r in resolutions.items()}

    mirror_dir: str | None = None
    mirror_items: list[CopyItem] = []
    if source_mode == "commit" and pinned_source is not None:
        if any(not r.refusal_reason for r in resolutions.values()):
            mirror_dir = tempfile.mkdtemp(prefix="resextract-pinned-")
            mirror_requests = _mirror_tree(resolutions, mirror_dir=mirror_dir)
            if mirror_requests:
                mirror_copier = Copier(
                    mirror_dir,
                    docket_dir,
                    per_file_cap=copier.per_file_cap,
                    per_docket_cap=copier.per_docket_cap,
                    secret_scan=copier.secret_scan,
                    emit_excerpt_index=copier.emit_excerpt_index,
                )
                mirror_items = list(mirror_copier.plan(mirror_requests).items)

    return mirror_dir, _merge_plan(wt_plan, resolutions, mirror_items), resolutions, real_src_by_dest


def _provenance_for(
    resolutions: Mapping[str, _ResolvedSource],
    final_item_by_dest: Mapping[str, CopyItem],
    head_sha: str | None,
) -> dict[str, dict[str, Any]]:
    """Per-dest provenance: pinned (blob sha) or unpinned (reason + mtime)."""
    out: dict[str, dict[str, Any]] = {}
    for dest in sorted(resolutions):
        rec = resolutions[dest]
        item = final_item_by_dest.get(dest)
        if item is None or item.status not in ("copied", "unchanged", "linked"):
            continue
        sha = rec.pinned.sha256 if rec.pinned is not None else (item.sha256 or "")
        out[dest] = {
            "dest": dest,
            "path": rec.real_src,
            "resolved_from": rec.resolved_from,
            "blob_sha": rec.pinned.blob_sha if rec.pinned is not None else None,
            "unpinned": bool(rec.unpinned),
            "reason": rec.reason,
            "sha256": sha,
            "mtime": rec.mtime,
            "commit_sha": head_sha,
            "bytes": int(item.bytes),
        }
    return out


def _unpinned_material(provenance: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [provenance[d] for d in sorted(provenance) if provenance[d].get("unpinned")]


def _warn_unpinned(entries: Sequence[Mapping[str, Any]]) -> list[str]:
    """One warning line per unpinned file; returned so callers can record them."""
    lines: list[str] = []
    for entry in entries:
        line = (
            f"unpinned material {entry.get('dest')} (working tree {entry.get('path')}): "
            f"{entry.get('reason') or 'unknown'}; "
            f"sha256={str(entry.get('sha256') or '')[:8]}; "
            f"mtime={entry.get('mtime') or 'unknown'}"
        )
        _warn(line)
        lines.append(line)
    return lines


# --------------------------------------------------------------------------- #
# sealed window
# --------------------------------------------------------------------------- #


def _seal_window(
    target_root: str,
    head_sha: str | None,
    head_probe: Callable[[str], str | None] | None,
) -> tuple[bool, str, str | None]:
    """Re-read HEAD after the copies and decide whether the window stayed sealed.

    ``head_probe`` is a test seam: it substitutes for the closing read only (the
    opening read always goes through :func:`_read_head`), so a test can present a
    moved HEAD without racing a real repository.
    """
    probe = head_probe or _read_head
    try:
        head_end = probe(target_root)
    except Exception:  # noqa: BLE001 - an unreadable HEAD cannot seal a window
        head_end = None
    # A target that never had an observable HEAD (a non-git directory, or a lane
    # spec's own recorded sha) has no commit to move away from: nothing to seal.
    # A *real* commit that became unreadable mid-run does not get that excuse.
    if head_sha is None or not commit_exists(target_root, head_sha):
        return True, "target has no observable HEAD; no commit to seal", head_end
    if head_end == head_sha:
        return True, "", head_end
    return (
        False,
        f"target head moved during materialization "
        f"({_short(head_sha)} -> {_short(head_end)}); re-materialize to obtain "
        f"bytes pinned to a single commit",
        head_end,
    )


def _append_history(
    docket_dir: str, lines: Sequence[str], *, heading: str = "sealed window"
) -> None:
    """Append (never rewrite) one block to ``HISTORY.md``."""
    os.makedirs(docket_dir, exist_ok=True)
    path = os.path.join(docket_dir, "HISTORY.md")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"\n### {heading}\n")
        for line in lines:
            fh.write(f"- {line}\n")


def _record_manifest_evidence(
    manifest: Any,
    *,
    provenance: Mapping[str, dict[str, Any]],
    window_sealed: bool,
    window_reason: str,
) -> None:
    """Additively stamp the manifest with provenance + the sealed-window result."""
    try:
        manifest.window_sealed = bool(window_sealed)
    except (AttributeError, ValueError):  # pragma: no cover - older manifest
        pass
    by_dest = {row.dest: row for row in getattr(manifest, "material", []) or []}
    for dest, prov in provenance.items():
        row = by_dest.get(dest)
        if row is None:
            continue
        row.blob_sha = prov.get("blob_sha")
        row.resolved_from = str(prov.get("resolved_from") or "working_tree")
        row.unpinned = bool(prov.get("unpinned"))
        if row.unpinned:
            bits = [f"unpinned: {prov.get('reason') or 'unknown'}"]
            if prov.get("mtime"):
                bits.append(f"mtime {prov['mtime']}")
            extra = "; ".join(bits)
            row.note = f"{row.note}; {extra}" if row.note else extra
    if not window_sealed:
        try:
            manifest.freshness.state = "needs_rework"
        except (AttributeError, ValueError):  # pragma: no cover - older manifest
            pass
        if window_reason:
            try:
                if window_reason not in manifest.rework_open:
                    manifest.rework_open.append(window_reason)
            except (AttributeError, ValueError):  # pragma: no cover
                pass


# --------------------------------------------------------------------------- #
# result
# --------------------------------------------------------------------------- #


@dataclass
class MaterializedDocket:
    """What one materialize run produced (or would produce, on ``dry_run``)."""

    docket_dir: str
    copy_report: CopyReport | None = None
    manifest: Any = None
    verification: Any = None
    files_written: list[str] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)
    unresolved_refs: list[UnresolvedRef] = field(default_factory=list)
    plan: CopyPlan | None = None
    head_sha: str | None = None
    head_sha_source: str = ""
    dockets_row_id: int | None = None
    dry_run: bool = False
    notes: list[str] = field(default_factory=list)
    # -- U5.5: commit-pinned source selection + sealed window -----------------
    source_mode: str = "commit"
    pinned: bool = False
    provenance: dict[str, dict[str, Any]] = field(default_factory=dict)
    unpinned_material: list[dict[str, Any]] = field(default_factory=list)
    window_sealed: bool | None = None
    window_reason: str = ""
    head_sha_end: str | None = None
    writer_signal: Any = None
    needs_rework: bool = False
    # -- U5.7: the derived producer and the gate's verdict --------------------
    producer: str = "unknown"
    status: str = "draft"
    status_reason: str | None = None
    member_candidate_count: int = 0

    @property
    def ok(self) -> bool:
        return bool(self.verification is not None and self.verification.ok)

    def counts(self) -> dict[str, int]:
        report = self.copy_report
        pinned_entries = sum(
            1 for p in self.provenance.values() if not p.get("unpinned")
        )
        return {
            "copied": report.copied_count if report else 0,
            "unchanged": report.unchanged_count if report else 0,
            "linked": report.linked_count if report else 0,
            "refused": report.refused_count if report else 0,
            "missing": report.missing_count if report else 0,
            "unresolved": len(self.unresolved_refs),
            "files_written": len(self.files_written),
            "pinned_entries": pinned_entries,
            "unpinned_entries": len(self.unpinned_material),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dry_run": self.dry_run,
            "docket_dir": self.docket_dir,
            "head_sha": self.head_sha,
            "head_sha_source": self.head_sha_source,
            "head_sha_end": self.head_sha_end,
            "dockets_row_id": self.dockets_row_id,
            "counts": self.counts(),
            "files_written": list(self.files_written),
            "refusals": list(self.refusals),
            "unresolved_refs": [u.to_dict() for u in self.unresolved_refs],
            "copy_report": self.copy_report.to_dict() if self.copy_report else None,
            "verification": self.verification.to_dict() if self.verification else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "notes": list(self.notes),
            "source_mode": self.source_mode,
            "pinned": self.pinned,
            "provenance": {d: self.provenance[d] for d in sorted(self.provenance)},
            "unpinned_material": list(self.unpinned_material),
            "window_sealed": self.window_sealed,
            "window_reason": self.window_reason,
            "writer_signal": (
                self.writer_signal.as_dict()
                if hasattr(self.writer_signal, "as_dict")
                else None
            ),
            "needs_rework": self.needs_rework,
            "producer": self.producer,
            "status": self.status,
            "status_reason": self.status_reason,
            "member_candidate_count": self.member_candidate_count,
        }


# --------------------------------------------------------------------------- #
# target resolution
# --------------------------------------------------------------------------- #


def _config_target_path(slug: str, config_dir: str = "config") -> str | None:
    path = os.path.join(config_dir, "targets.toml")
    if not os.path.isfile(path):
        return None
    try:
        try:
            import tomllib  # Python ≥ 3.11
        except ModuleNotFoundError:  # pragma: no cover - older interpreters
            import tomli as tomllib  # type: ignore[no-redef]
        with open(path, "rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, ValueError):
        return None
    entry = ((raw.get("targets") or {}) if isinstance(raw, dict) else {}).get(slug)
    if isinstance(entry, dict) and entry.get("path"):
        return str(entry["path"])
    return None


def resolve_target_root(
    slug: str,
    *,
    con: Any = None,
    config_dir: str = "config",
) -> str | None:
    """Resolve a target slug to a directory: store row, then config, then path.

    The store's ``targets`` table is authoritative when a row exists; otherwise
    ``config/targets.toml`` is consulted (that is where the read-only acceptance
    target is declared); otherwise the slug is accepted as a directory path.
    """
    if con is not None:
        try:
            row = _store.get_target(con, slug)
        except Exception:  # noqa: BLE001 - an unreadable store falls through
            row = None
        if row and row.get("path") and os.path.isdir(str(row["path"])):
            return str(row["path"])
    from_config = _config_target_path(slug, config_dir)
    if from_config and os.path.isdir(from_config):
        return from_config
    if os.path.isdir(slug):
        return slug
    return None


# --------------------------------------------------------------------------- #
# the command
# --------------------------------------------------------------------------- #


def _docket_dir_for(lane: LaneSpec, target_slug: str, docket_root: str) -> str:
    return os.path.join(docket_root, target_slug, lane.slug)


def _store_dir(docket_dir: str) -> str:
    rel = os.path.relpath(os.path.abspath(docket_dir))
    return docket_dir if rel.startswith(os.pardir) else rel


def _default_graph_path(target_slug: str) -> str | None:
    candidate = os.path.join(
        DEFAULT_GRAPH_REL, target_slug, "graphify-out", "graph.json"
    )
    return candidate if os.path.isfile(candidate) else None


def _verdicts_by_candidate(con: Any) -> dict[int, dict[str, Any]]:
    """``candidate_id`` -> the verdict row that assessed a claim on it.

    U5.15.  The real join, read from the schema rather than assumed:
    ``verdicts.claim_id = claims.id`` **and** ``claims.candidate_id =
    candidates.id``.  There is no ``settled_by`` column in the store -- the
    decompose-side ``settled_by`` is a :class:`~resextract.claims.decompose`
    dataclass field and is never persisted -- so candidate -> claims -> verdicts
    is the only honest link.  Where a candidate has more than one assessed claim,
    the highest ``verdicts.id`` wins: the latest assessment.  A candidate with no
    claim, or a claim with no verdict, is simply absent from the map, which
    fail-closes it at materialisation.
    """
    rows = con.execute(
        "SELECT v.id, v.claim_id, v.verdict, v.producer, c.candidate_id "
        "FROM verdicts v JOIN claims c ON c.id = v.claim_id "
        "WHERE c.candidate_id IS NOT NULL ORDER BY v.id"
    ).fetchall()
    out: dict[int, dict[str, Any]] = {}
    for row in rows:
        record = dict(row)
        out[int(record["candidate_id"])] = record
    return out


def _attach_verdicts(
    lane: LaneSpec, verdicts_by_candidate: Mapping[int, Mapping[str, Any]]
) -> None:
    """Stamp each member with the verdict that assessed it, when one exists.

    A member whose ``candidate_id`` has no verdict is left alone (all three
    fields ``None``), which :func:`_claim_standing` renders as "not assessed, no
    CONFIRMS".
    """
    for member in lane.members:
        if member.candidate_id is None:
            continue
        record = verdicts_by_candidate.get(int(member.candidate_id))
        if not record:
            continue
        member.verdict = str(record.get("verdict") or "UNVERIFIED")
        member.verdict_producer = record.get("producer")
        member.verdict_id = record.get("id")


def _claim_producer(member: MemberSpec) -> str:
    """The producer class backing one claim member, collapsed like one docket row.

    The rule is :func:`derive_producer` applied to the member's single row:
    exactly ``model`` -> ``model``, exactly ``replay`` -> ``replay``, everything
    else (``fixture``, ``mixed``, ``unknown``, a missing field, a non-string, or
    an **off-vocabulary / wrong-case** value) -> ``unknown``.  That is what makes
    the claim-level and docket-level attribution one scheme; the equivalence is
    pinned by a table-driven test, not asserted.

    The comparison is **exact**: ``"Model"``, ``"MODEL"`` and ``"  model  "`` are
    not ``model`` here, matching :func:`store.producer_is_model` and the assess
    layer's reject-don't-coerce rule.  A wrong-case declaration is therefore
    **capped fail-closed** (a typed error would make a rendering typo abort
    materialisation of an otherwise honest docket); the reason is recorded on the
    claim's ``verdict_reason`` by :func:`_producer_declaration_note`, so it is
    never silent and never grants model standing.

    U5.19: the subset collapse is no longer inline here -- it is
    :data:`_CLAIM_PRODUCER_VOCAB` applied by :func:`_claim_level_producer`, the
    single function all three claim-level rendering sites call.
    """
    return _claim_level_producer(getattr(member, "producer", None))


def _producer_declaration_note(member: MemberSpec) -> str | None:
    """A visible note when the declared producer is not exactly in the vocabulary.

    U5.15: the curated ``LaneSpec.from_json`` path is unvalidated, so a
    wrong-case or off-vocabulary ``producer`` can reach materialisation.  It never
    grants model standing -- :func:`_claim_producer` collapses it to ``unknown``
    -- and this records *why*, so the cap is auditable rather than silent.  Only
    materialisation is strict in this way; *loading* a manifest never consults
    this.
    """
    raw = getattr(member, "producer", None)
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw:
        return (
            f"declared producer {raw!r} is not a non-empty string; treated as "
            "'unknown' (no model standing)"
        )
    if raw not in PRODUCERS:
        return (
            f"declared producer {raw!r} is not exactly one of {list(PRODUCERS)} "
            "(the comparison is case-sensitive); treated as 'unknown' "
            "(no model standing)"
        )
    return None


def _claim_standing(member: MemberSpec) -> tuple[str, str | None]:
    """``(verdict, reason)`` for one claim, keyed off the **verdict** row.

    U5.15.  The authority for a claim's standing is the ``verdicts`` row that
    assessed it (``verdicts.verdict`` / ``verdicts.producer``, joined through
    ``claims.candidate_id`` by :func:`_verdicts_by_candidate`), **not**
    ``candidates.state``: nothing writes ``candidates.state`` from a verdict, so
    a model-mined candidate with ``state='confirmed'`` and zero verdicts used to
    render ``CONFIRMS`` with nothing having assessed it.  With no verdict row the
    declared ``verification_state`` may not reach ``CONFIRMS`` -- it is capped at
    ``EXTENDS`` with the reason recorded.  When a verdict row exists, a
    ``CONFIRMS`` it carries is capped only if its own producer is not exactly
    ``model`` (the same predicate the assess layer uses).
    """
    declared = _VERDICT_BY_STATE.get(
        (member.verification_state or "").lower(), "UNVERIFIED"
    )
    if member.verdict is None:
        if declared == "CONFIRMS":
            return "EXTENDS", (
                f"declared verification state {member.verification_state!r} maps to "
                f"CONFIRMS, but no verdicts row assesses this claim (candidate "
                f"producer {member.producer!r}); capped at EXTENDS (a candidate "
                "row's state is not an assessment)"
            )
        return declared, None
    verdict = str(member.verdict)
    if verdict not in _store.VERDICT_VOCAB:
        verdict = "UNVERIFIED"
    if verdict == "CONFIRMS" and not _store.producer_is_model(member.verdict_producer):
        return "EXTENDS", (
            f"verdict {member.verdict_id} says CONFIRMS but its producer is "
            f"{member.verdict_producer!r}, not 'model'; capped at EXTENDS by the "
            "same rule as assess.verdicts (a non-model run may not assert CONFIRMS)"
        )
    return verdict, None


def _claim_for(
    member: MemberSpec,
    pairs: Sequence[tuple[str, str, CopyItem]],
) -> dict[str, Any]:
    provenance: list[str] = []
    evidence: list[str] = []
    for _ref, dest, item in pairs:
        suffix = ""
        if item.excerpt:
            suffix = f"#L{item.excerpt[0]}-L{item.excerpt[1]}"
        provenance.append(f"file:{dest}{suffix}")
        evidence.append(f"material/{dest}{suffix}")
    text = member.summary or member.title or f"Material claim {member.id}."
    verdict, verdict_reason = _claim_standing(member)
    note = _producer_declaration_note(member)
    if note:
        verdict_reason = f"{verdict_reason}; {note}" if verdict_reason else note
    # U5.15: the claim's ``producer`` names the **verdict's** producer when a
    # verdict row assesses this claim (the authoritative source, and the one the
    # CONFIRMS cap is judged on), and the candidate row's producer otherwise.
    # U5.19: **both** branches go through the single claim-level collapse
    # (:func:`_claim_level_producer`), so this third rendering site agrees with
    # :func:`_claim_producer` and :func:`derive_producer` on every input.
    mining_producer = _claim_producer(member)
    if member.verdict is not None:
        producer = _claim_level_producer(member.verdict_producer)
        if producer != mining_producer:
            # F2 (U5.19): attribution, not permission.  A model verdict may
            # bless replay-mined material (store.may_back_model_claim_verdict),
            # but ``producer`` then names the *assessor*, so the mining
            # provenance is carried beside it in the claim's own reason --
            # otherwise a reader sees ``model`` and concludes the *material* was
            # model-mined while ``generated_by.producer`` says ``replay``.
            which = (
                f"verdict {member.verdict_id}"
                if member.verdict_id is not None
                else "the verdict row"
            )
            mining_note = (
                f"claim producer {producer!r} is the *assessing* producer "
                f"({which}); the material was mined by {mining_producer!r} "
                "(docket-level provenance is the mining producer, not this one)"
            )
            verdict_reason = (
                f"{verdict_reason}; {mining_note}" if verdict_reason else mining_note
            )
    else:
        producer = mining_producer
    return {
        "id": member.id,
        "text": text,
        "kind": member.kind,
        "provenance": sorted(set(provenance)),
        "verdict": verdict,
        "evidence": sorted(set(evidence)),
        "producer": producer,
        "verdict_reason": verdict_reason,
    }


def _upsert_docket_row(
    con: Any,
    *,
    lane: LaneSpec,
    target_slug: str,
    docket_dir: str,
    manifest: Any,
    head_sha: str | None,
    graph_hash: str | None,
    freshness: str,
    verified_at: str | None,
) -> int:
    stored_dir = _store_dir(docket_dir)
    lane_row = None
    if lane.slug:
        try:
            lane_row = _store.get_lane_by_slug(con, target_slug, lane.slug)
        except Exception:  # noqa: BLE001 - the row is optional metadata
            lane_row = None
    existing = None
    for row in con.execute(
        "SELECT id, dir FROM dockets WHERE dir=? OR dir=?", (stored_dir, docket_dir)
    ).fetchall():
        existing = dict(row)
        break
    manifest_json = (
        manifest.model_dump(mode="json", by_alias=True) if manifest is not None else None
    )
    now = _store.utcnow()
    if existing:
        _store.upsert_docket(
            con,
            id=int(existing["id"]),
            lane_id=(lane_row or {}).get("id"),
            dir=stored_dir,
            manifest_json=manifest_json,
            source_head=head_sha,
            graph_hash=graph_hash,
            freshness=freshness,
            verified_at=verified_at or now,
            last_refresh_at=now,
        )
        return int(existing["id"])
    return int(
        _store.upsert_docket(
            con,
            lane_id=(lane_row or {}).get("id"),
            dir=stored_dir,
            manifest_json=manifest_json,
            source_head=head_sha,
            graph_hash=graph_hash,
            freshness=freshness,
            verified_at=verified_at or now,
            last_refresh_at=now,
        )
    )


def materialize_lane(
    lane: LaneSpec,
    *,
    target_root: str,
    docket_root: str = DEFAULT_DOCKET_ROOT,
    graph_path: str | None = None,
    dry_run: bool = False,
    db_path: str | os.PathLike[str] | None = None,
    config_dir: str = "config",
    source_mode: str = "commit",
    window_s: float = DEFAULT_WINDOW_S,
    allow_active: bool = False,
    head_probe: Callable[[str], str | None] | None = None,
    status: str = "draft",
) -> MaterializedDocket:
    """Copy a lane's material, assemble + verify its docket, record the row.

    See the module docstring for the guarantees.  ``source_mode`` is ``commit``
    (default: resolve every request at the recorded commit and record the blob
    sha) or ``working-tree`` (the explicit opt-out).  The run opens with
    :func:`~resextract.refresh.writer.assert_quiescent` — a moving target raises
    :class:`TargetBusyError` unless ``allow_active=True`` — and closes by
    re-reading HEAD, marking ``freshness.state="needs_rework"`` when it moved.

    Raises :class:`MaterializeRefused` when the lane has no verifiable material
    (and writes nothing), :class:`MaterializeError` when assembly/verification
    does not hold, :class:`TargetBusyError` when the target is not quiescent.
    """
    target_root = os.path.abspath(target_root)
    if not os.path.isdir(target_root):
        raise MaterializeError(f"target root is not a directory: {target_root}")
    if not lane.slug:
        raise MaterializeRefused(["lane spec has no slug"])
    if source_mode not in SOURCE_MODES:
        raise MaterializeError(
            f"unknown source_mode {source_mode!r}; expected one of {SOURCE_MODES}"
        )

    target_slug = lane.target_slug or os.path.basename(target_root.rstrip(os.sep))
    docket_dir = os.path.abspath(_docket_dir_for(lane, target_slug, docket_root))
    notes: list[str] = []

    # 0. the producer gate (U5.7): derive provenance from the lane's *member
    # candidates* in the store, then refuse to call anything but a model-mined
    # docket promotable.  Derivation failing is not a licence to promote: an
    # unreadable store records `unknown`, which blocks `ready` like any other
    # non-model producer.
    member_rows: list[dict[str, Any]] = []
    producer = "unknown"
    derived_con = None
    verdicts_by_candidate: dict[int, dict[str, Any]] = {}
    try:
        derived_con = (
            _store.connect(db_path) if db_path is not None else _store.connect()
        )
        member_rows = lane_member_candidates(
            derived_con, target_slug=target_slug, lane_slug=lane.slug
        )
        producer = derive_producer(member_rows)
        # U5.15: the claim's standing comes from the verdict that assessed it,
        # never from the candidate row's ``state``.
        verdicts_by_candidate = _verdicts_by_candidate(derived_con)
    except Exception as exc:  # noqa: BLE001 - a store we cannot read cannot promote
        notes.append(
            f"producer derivation unavailable ({type(exc).__name__}: {exc}); "
            "recording producer='unknown'"
        )
    finally:
        if derived_con is not None:
            derived_con.close()
    _attach_verdicts(lane, verdicts_by_candidate)
    model_id = model_id_for(producer, member_rows)
    gate_reason = producer_gate_reason(producer)
    if gate_reason is not None and status == "ready":
        raise PromotionRefused([gate_reason], producer=producer)
    docket_status = status if producer == "model" else "draft"
    if gate_reason is not None:
        notes.append(f"PROVENANCE GATE: {gate_reason}")
    notes.append(
        f"producer={producer} derived from {len(member_rows)} lane member "
        f"candidate(s); docket status={docket_status}"
    )

    # 0. the sealed window opens: is a foreign writer active right now? --------
    signal = assert_quiescent(target_root, window_s=window_s, allow_active=allow_active)
    notes.append(
        f"writer signal: {signal.verdict} over {window_s:g}s "
        f"(HEAD {_short(signal.head_before)} -> {_short(signal.head_after)}; "
        f"{signal.files_touched_in_window} tracked file(s) touched; "
        f"{signal.worktree_dirs_present} .worktrees/run* dir(s))"
    )
    if signal.verdict != "quiescent":
        notes.append(
            "WARNING: the target was moving and the run continued because "
            f"allow_active=True: {signal.note}"
        )

    # 1. the target's real HEAD, at the moment material is copied --------------
    head_sha, head_source = read_head_sha(target_root, lane.head_sha)
    if head_source != "git":
        notes.append(
            "head_sha: `git rev-parse HEAD` did not answer for "
            f"{target_root}; recorded the LaneSpec head_sha instead"
        )

    # 2. refs → requests ------------------------------------------------------
    if graph_path is None:
        graph_path = _default_graph_path(target_slug)
    graph = None
    graph_hash: str | None = None
    if graph_path and os.path.isfile(graph_path):
        try:
            from resextract.kg import read_graph

            graph = read_graph(graph_path)
            graph_hash = sha256_file(graph_path)
        except Exception as exc:  # noqa: BLE001 - node ids become unresolvable
            notes.append(f"graph_path {graph_path!r} could not be read: {exc}")
            graph = None
            graph_path = None

    # 2b. commit-pinned source selection, opened BEFORE refs become requests: in
    # commit mode the commit is asked first, which is what makes resolution
    # tree-first (a deleted-but-committed path is still material).
    pinned_source: GitObjectSource | None = None
    pin_failure_reason: str | None = None
    if source_mode == "commit":
        pinned_source, pin_failure_reason = _open_pinned_source(
            target_root, head_sha, head_source
        )
        if pinned_source is None:
            notes.append(
                f"commit pinning unavailable ({pin_failure_reason}); every material "
                "entry is working-tree bytes, marked unpinned in the manifest"
            )
    else:
        notes.append(
            "source_mode=working-tree: this run is NOT commit-pinned; every "
            "material entry is working-tree bytes, marked unpinned"
        )
    pinned_run = pinned_source is not None

    owners: dict[str, str] = {}
    all_refs: list[str] = []
    for member in lane.members:
        for ref in member.provenance_refs:
            if ref not in owners:
                owners[ref] = member.id
            all_refs.append(ref)
    ref_plan = refs_to_copy_requests(
        all_refs,
        target_root=target_root,
        graph=graph,
        reason_prefix=f"lane:{lane.slug}",
        pinned_source=pinned_source,
    )
    unresolved: list[UnresolvedRef] = list(ref_plan.unresolved)

    copier = Copier(target_root, docket_dir)
    # the working-tree copier runs FIRST and its outcome is authoritative for
    # every refusal: containment, symlink, secret path, secret content, caps.
    wt_plan = copier.plan(ref_plan.requests)

    mirror_dir, final_plan, resolutions, real_src_by_dest = _build_final_plan(
        ref_plan,
        wt_plan,
        target_root=target_root,
        source_mode=source_mode,
        pinned_source=pinned_source,
        pin_failure_reason=pin_failure_reason,
        copier=copier,
        docket_dir=docket_dir,
    )
    final_item_by_dest = {item.dest: item for item in final_plan.items}

    try:
        # 3. the refusal guard — before anything is written -------------------
        verifiable = [i for i in final_plan.items if i.status in ("copied", "linked")]
        if not verifiable:
            reasons = [f"unresolved ref {u}" for u in unresolved]
            reasons += [
                f"ref {i.src} ({i.dest}) refused: {i.refusal_reason}"
                for i in final_plan.items
                if i.status in ("refused", "missing")
            ]
            if not reasons:
                reasons = ["lane has no resolvable provenance references at all"]
            raise MaterializeRefused(reasons)

        # a refused/missing planned item is an unresolved ref, reported as such
        for ref, dest in ref_plan.by_ref.items():
            item = final_item_by_dest.get(dest)
            if item is None or item.status in ("refused", "missing"):
                unresolved.append(
                    UnresolvedRef(
                        ref,
                        (item.refusal_reason if item is not None else "not_planned"),
                        dest,
                    )
                )
        unresolved = list({(u.ref, u.reason): u for u in unresolved}.values())

        member_pairs: dict[str, list[tuple[str, str, CopyItem]]] = {}
        for ref, dest in ref_plan.by_ref.items():
            item = final_item_by_dest.get(dest)
            if item is None or item.status in ("refused", "missing"):
                continue
            member_pairs.setdefault(owners.get(ref, ""), []).append((ref, dest, item))

        provenance = _provenance_for(resolutions, final_item_by_dest, head_sha)
        unpinned_material = _unpinned_material(provenance)
        for line in _warn_unpinned(unpinned_material):
            notes.append(line)
        if pinned_run:
            notes.append(
                f"commit-pinned at {_short(head_sha)}: "
                f"{len(provenance) - len(unpinned_material)} entry(ies) from the "
                f"object store, {len(unpinned_material)} unpinned"
            )

        # -- dry run: write nothing, report the plan --------------------------
        if dry_run:
            window_sealed, window_reason, head_end = _seal_window(
                target_root, head_sha, head_probe
            )
            would_write = sorted(
                {
                    "MANIFEST.json", "README.md", "CLAIMS.md", "EVIDENCE.md",
                    "PRIOR_ART.md", "REFERENCES.md", "REFERENCES.bib", "RESULTS.md",
                    "METHOD.md", "CHECKLIST.md", "OPEN_QUESTIONS.md",
                    "UPDATE_BACKLOG.md", "ITEM.md", "HISTORY.md",
                    "web/README.md", "repro/README.md", "repro/run.sh",
                }
            ) + [f"material/{i.dest}" for i in final_plan.items if i.status == "copied"]
            report = CopyReport(items=list(final_plan.items))
            return MaterializedDocket(
                docket_dir=docket_dir,
                copy_report=report,
                manifest=None,
                verification=None,
                files_written=would_write,
                refusals=[],
                unresolved_refs=unresolved,
                plan=final_plan,
                head_sha=head_sha,
                head_sha_source=head_source,
                dockets_row_id=None,
                dry_run=True,
                notes=notes,
                source_mode=source_mode,
                pinned=pinned_run,
                provenance=provenance,
                unpinned_material=unpinned_material,
                window_sealed=window_sealed,
                window_reason=window_reason,
                head_sha_end=head_end,
                writer_signal=signal,
                producer=producer,
                status=docket_status,
                status_reason=gate_reason,
                member_candidate_count=len(member_rows),
                needs_rework=False,
            )

        # 4. execute the copies -------------------------------------------------
        # linked/refused items are never read from ``src``; put the real path back
        # on them now so LINKS.md names the target, not the mirror.
        for item in final_plan.items:
            if item.status != "copied":
                item.src = real_src_by_dest.get(item.dest, item.src)
        report = copier.execute(final_plan)
        # ... and put the real source path back on every executed item so the
        # docket records where the bytes actually came from.
        for item in report.items:
            item.src = real_src_by_dest.get(item.dest, item.src)
        for item in final_plan.items:
            item.src = real_src_by_dest.get(item.dest, item.src)
        executed_by_dest = {item.dest: item for item in report.items}

        # 4b. pinned integrity: the docket's bytes are the pinned bytes ---------
        for dest, rec in resolutions.items():
            if rec.pinned is None:
                continue
            item = executed_by_dest.get(dest)
            if item is None or item.status not in ("copied", "unchanged"):
                continue
            try:
                verify_pinned(rec.pinned, copier.material_path(dest))
            except PinnedIntegrityError as exc:
                raise MaterializeError(
                    f"pinned material did not survive the copy into the docket: {exc}"
                ) from exc
    finally:
        if mirror_dir is not None:
            shutil.rmtree(mirror_dir, ignore_errors=True)

    # provenance from the *executed* statuses (a linked stub is still material)
    provenance = _provenance_for(resolutions, executed_by_dest, head_sha)
    unpinned_material = _unpinned_material(provenance)

    claims: list[dict[str, Any]] = []
    for member in lane.members:
        pairs = member_pairs.get(member.id) or []
        live_pairs = [
            (ref, dest, executed_by_dest[dest])
            for ref, dest, _ in pairs
            if executed_by_dest.get(dest) is not None
            and executed_by_dest[dest].status in ("copied", "unchanged", "linked")
        ]
        if not live_pairs:
            for ref in member.provenance_refs:
                if not any(u.ref == ref for u in unresolved):
                    unresolved.append(
                        UnresolvedRef(ref, "not_materialized_for_this_member", member.id)
                    )
            continue
        claims.append(_claim_for(member, live_pairs))
    claims.sort(key=lambda c: c["id"])

    if not claims:
        raise MaterializeRefused(
            [f"unresolved ref {u}" for u in unresolved]
            or ["no member ended with verifiable copied material"]
        )

    # 5. assemble from the docket's *own* copies ------------------------------
    material_report = material_report_from_docket(docket_dir, source_root=target_root)
    # ``material_report_from_docket`` only knows the docket-internal dest; put the
    # real source path back on each item so MANIFEST.json records where the bytes
    # actually came from (the copied dest keeps the folder convention).
    src_by_dest = {r.dest_rel: r.src for r in ref_plan.requests}
    for item in material_report.items:
        if item.dest in src_by_dest:
            item.src = src_by_dest[item.dest]
    verified_at = _store.utcnow()
    freshness = {
        "verified_at": verified_at,
        "prior_art_checked_at": None,
        "age_days": 0.0,
        "state": "current",
    }
    target_meta = {
        "slug": target_slug,
        "head_sha": head_sha,
        "graph_hash": graph_hash,
    }
    evidence = [
        EvidenceItem(
            ref=f"material/{item.dest}",
            source_kind="local",
            sha256=item.sha256,
            context=f"{item.bytes} bytes copied from the read-only target",
        )
        for item in report.items
        if item.status in ("copied", "unchanged")
    ]
    assembled = assemble_docket(
        docket_dir,
        lane={
            "slug": lane.slug,
            "type": lane.type,
            "title": lane.title,
            "thesis": lane.thesis,
            "audience": lane.audience,
            "status": docket_status,
        },
        claims=claims,
        evidence=evidence,
        material_report=material_report,
        target_meta=target_meta,
        freshness=freshness,
        graph_path=graph_path if graph is not None else None,
        source_root=target_root,
        model=model_id or "",
        status=docket_status,
        producer=producer,
        status_reason=gate_reason,
    )

    # 6. the sealed window closes: did HEAD move while we copied? --------------
    window_sealed, window_reason, head_end = _seal_window(
        target_root, head_sha, head_probe
    )
    needs_rework = not window_sealed
    if needs_rework:
        freshness["state"] = "needs_rework"
        notes.append(f"WARNING: {window_reason}")
    _record_manifest_evidence(
        assembled.manifest,
        provenance=provenance,
        window_sealed=window_sealed,
        window_reason=window_reason,
    )
    # U5.7: stamp the derived provenance and the gate's verdict into the
    # artifact itself, then re-write the manifest through the same validating
    # writer (so a bad producer value cannot reach disk either).
    assembled.manifest.generated_by.producer = producer
    assembled.manifest.generated_by.model = model_id
    assembled.manifest.status = docket_status
    assembled.manifest.status_reason = gate_reason
    write_manifest(docket_dir, assembled.manifest)
    if needs_rework:
        _append_history(docket_dir, [window_reason])
    if gate_reason is not None:
        _append_history(docket_dir, [gate_reason], heading="producer gate (U5.7)")

    # 7. verify — fail loudly, never register an unverified docket -------------
    verification = verify_docket(docket_dir)
    if not verification.ok:
        raise MaterializeError(
            "docket verification failed for "
            f"{docket_dir}: " + "; ".join(verification.problems)
        )

    # 8. the dockets row (idempotent: same dir updates, never duplicates) ------
    con = _store.connect(db_path) if db_path is not None else _store.connect()
    try:
        row_id = _upsert_docket_row(
            con,
            lane=lane,
            target_slug=target_slug,
            docket_dir=docket_dir,
            manifest=assembled.manifest,
            head_sha=head_sha,
            graph_hash=graph_hash,
            freshness=str(freshness["state"]),
            verified_at=verified_at,
        )
    finally:
        con.close()

    files_written = list(assembled.files)
    return MaterializedDocket(
        docket_dir=docket_dir,
        copy_report=report,
        manifest=assembled.manifest,
        verification=verification,
        files_written=files_written,
        refusals=[
            f"{i.dest}: {i.refusal_reason}" for i in report.items if i.status == "refused"
        ],
        unresolved_refs=unresolved,
        plan=final_plan,
        head_sha=head_sha,
        head_sha_source=head_source,
        dockets_row_id=row_id,
        dry_run=False,
        notes=notes,
        source_mode=source_mode,
        pinned=pinned_run,
        provenance=provenance,
        unpinned_material=unpinned_material,
        window_sealed=window_sealed,
        window_reason=window_reason,
        head_sha_end=head_end,
        writer_signal=signal,
        producer=producer,
        status=docket_status,
        status_reason=gate_reason,
        member_candidate_count=len(member_rows),
        needs_rework=needs_rework,
    )
