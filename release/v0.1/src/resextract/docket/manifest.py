"""``MANIFEST.json`` — the machine-readable docket contract (plan §3.5 / §3.6).

Pure contract + validation: no rendering, no store access, no copying.

Typo safety comes from ``extra="forbid"`` on every model, so a misspelled key
cannot silently become a manifest field.  The semantic gates that go beyond
types — enumerations, non-empty provenance/evidence on every claim, and
on-disk sha256 agreement for every docket-local evidence/material reference —
live in :func:`validate_manifest` so they surface as a list of human-readable
problems instead of a pydantic traceback.  An empty list means valid.

Two deliberate supersets of the plan's literal key list, both needed by the
assembler and both still ``extra="forbid"``:

``claims[].kind``        the claim sheet wishes to print a kind column.
``generated_at``         §5 requires ``MANIFEST.json`` to hold the timeline.
``material[].linked``    an over-cap ``LINKS.md`` stub has no file on disk, so
                         the sha256 gate must be able to tell the two apart.

U5.7 adds three more keys, all optional and all additive, so every pre-U5.7
manifest keeps validating (the schema string is deliberately not bumped):

``generated_by.producer``  who produced the docket's candidates (U5.7).
``generated_by.model``     now ``str | None`` — ``None`` means "no model id to
                           record", never "a model called None".
``status_reason``          why ``status`` is not ``ready``.

U5.11 adds the last two optional, additive keys -- the final members of the
silent re-assembly family -- and again the schema string is deliberately *not*
bumped:

``results``    the measured results that rendered to ``RESULTS.md``.
``prior_art``  the external anchors that rendered to ``PRIOR_ART.md``.

For both: ``None`` means the docket never recorded them (every pre-U5.11
manifest) and ``[]`` means a caller deliberately cleared them.  That difference
is load-bearing -- only a *recorded* value may be inherited, and only ``None``
is alarm-eligible.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from resextract.docket.copy import sha256_file

from resextract.store import PRODUCER_VOCAB

MANIFEST_NAME = "MANIFEST.json"
SCHEMA = "resextract/docket/1"

DOCKET_TYPES: tuple[str, ...] = ("paper", "report", "blog", "benchmark_card", "memo")
LANE_STATUSES: tuple[str, ...] = (
    "draft",
    "ready",
    "stale",
    "needs_rework",
    "superseded",
)
FRESHNESS_STATES: tuple[str, ...] = ("current", "stale", "needs_rework", "superseded")
#: U5.7 — who produced the candidates a docket rests on.  ``model`` is the *only*
#: value that may back a model-derived claim.  A manifest written before this
#: field existed loads as ``unknown``, which is the safe default: every value
#: other than ``model`` blocks promotion.
#:
#: U5.15 — the per-row classes are the **store's own vocabulary, imported**, not
#: restated here, so a docket and a store row cannot drift into two readings of
#: one column.  ``mixed`` is the single addition, and it is deliberately *not* a
#: per-row declaration: the store's ``CHECK`` rightly refuses it on a row, and
#: only the lane-level aggregation in
#: :func:`~resextract.docket.materialize.derive_producer` ever emits it (>=1
#: ``model`` row **and** >=1 non-``model`` row).  It stays in this tuple because
#: ``assemble.py`` validates an already-written manifest's producer against it;
#: no row and no claim can ever carry ``mixed``.
PRODUCERS: tuple[str, ...] = PRODUCER_VOCAB + ("mixed",)
VERDICTS: tuple[str, ...] = ("CONFIRMS", "EXTENDS", "CONTRADICTS", "UNVERIFIED")
EVIDENCE_SOURCE_KINDS: tuple[str, ...] = ("local", "web")

DType = Literal["paper", "report", "blog", "benchmark_card", "memo"]
DStatus = Literal["draft", "ready", "stale", "needs_rework", "superseded"]
DFreshness = Literal["current", "stale", "needs_rework", "superseded"]
DVerdict = Literal["CONFIRMS", "EXTENDS", "CONTRADICTS", "UNVERIFIED"]
#: Mirrors :data:`PRODUCERS` (a ``Literal`` cannot be built from a tuple).
DProducer = Literal["model", "replay", "fixture", "unknown", "mixed"]

#: ``<path>[#L<lo>[-L<hi>]]`` with an optional ``file:``/``graph:``/``web:`` scheme.
_SPAN_RE = re.compile(r"#L(?P<lo>\d+)(?:-L?(?P<hi>\d+))?$")


class _Forbid(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- #
# models
# --------------------------------------------------------------------------- #


class Lane(_Forbid):
    slug: str
    type: DType  # noqa: A003 - matches the store/schema vocabulary
    #: U5.14 additive.  The lane's *descriptive* title (e.g. "Duval
    #: replay-sourced material"), as distinct from its machine ``slug``.  It is
    #: a stored fact, not a derivation: no other field carries it, and a bare
    #: re-assembly can therefore only fall back to the slug unless it is
    #: persisted.  Optional (``None`` = never recorded), so every pre-U5.14
    #: manifest -- ``_smoke`` included -- still validates and the schema string
    #: is deliberately NOT bumped.
    title: str | None = None
    thesis: str = ""
    audience: str = ""


class Target(_Forbid):
    slug: str
    head_sha: str | None = None
    graph_hash: str | None = None


class Freshness(_Forbid):
    verified_at: str | None = None
    prior_art_checked_at: str | None = None
    age_days: float | None = None
    state: DFreshness = "current"


class Claim(_Forbid):
    id: str
    text: str
    kind: str | None = None
    provenance: list[str] = Field(default_factory=list)
    verdict: DVerdict = "UNVERIFIED"
    evidence: list[str] = Field(default_factory=list)
    # -- U5.13 additive standing attribution (both optional, so every manifest
    # written before this unit still validates; ``extra="forbid"`` is kept and
    # the schema string is NOT bumped) -------------------------------------
    #: who/what assessed this claim: the producer class of the member
    #: candidate(s) backing it (``model`` / ``replay`` / ``fixture`` /
    #: ``mixed`` / ``unknown``).  Written by this build, so a ``CONFIRMS`` can
    #: no longer be rendered unattributed.  ``unknown`` is the honest default
    #: and grants **no** model standing: it declares ignorance, not provenance.
    #: Typed ``str`` rather than :data:`DProducer` because
    #: :func:`materialize.derive_producer` also emits the docket-level ``mixed``.
    producer: str = "unknown"
    #: a free-text note about this claim's *standing* or its *attribution*;
    #: ``None`` when there is nothing to record.  It carries **two distinct
    #: meanings** (U5.19 added the second), so -- stated plainly -- since U5.19
    #: a non-``None`` value does **not** imply that this claim was downgraded:
    #:
    #: 1. **cap reason** -- a *declared* standing was capped below ``CONFIRMS``
    #:    because the backing producer was not a model.  This is how the
    #:    downgrade stays visible instead of silent: the reason travels with
    #:    the claim, and ``verdict`` reads ``EXTENDS`` beside it.
    #: 2. **provenance-divergence note** (U5.19, F2) -- ``producer`` names the
    #:    *assessing* authority (a model verdict) while the material was mined
    #:    by a different producer, so the mining provenance is recorded here
    #:    beside it.  This is **attribution, not permission**: ``verdict`` may
    #:    legitimately remain ``CONFIRMS``.
    #:
    #: The two are **not mutually exclusive**: each writer *appends* rather
    #: than overwrites (``materialize._claim_for``, and
    #: ``assemble._cap_uncapped_claims``, which preserves an existing note when
    #: it caps), so one field can carry both statements ``"; "``-joined.  A
    #: consumer must therefore not read ``verdict_reason is not None`` as "this
    #: claim was downgraded" -- the authoritative downgrade signal is
    #: ``verdict`` itself.  Nor is the value structured: a clause may itself
    #: contain ``"; "`` (the divergence note does, before ``the material was
    #: mined by``), so splitting on ``"; "`` does **not** reliably recover
    #: clauses.  What *is* reliable is substring detection of the known
    #: writers: ``"capped at EXTENDS"`` is emitted by every cap site and by
    #: nothing else, and ``"is the *assessing* producer"`` by the divergence
    #: site alone.
    #:
    #: Invariant (unchanged): the cap is applied when a claim is
    #: **materialized**, never when a manifest is **read** -- a pre-existing
    #: manifest whose claim says ``CONFIRMS`` still loads (that is what
    #: ``_smoke`` witnesses); it is re-materialized once, by a later unit,
    #: after the render fix.
    verdict_reason: str | None = None


class MaterialItem(_Forbid):
    src: str
    dest: str
    sha256: str
    bytes: int = 0
    excerpt: list[int] | None = None
    excerpt_reason: str | None = None
    linked: bool = False
    note: str | None = None
    # -- U5.5 additive provenance (all optional, so older manifests validate) --
    #: git object id of the pinned blob (``git rev-parse <commit>:<path>``);
    #: ``None`` when the bytes were not read from the object store.
    blob_sha: str | None = None
    #: ``git_object`` (commit-pinned) or ``working_tree`` (the default, matching
    #: the pre-U5.5 manifests, which were all working-tree reads).
    resolved_from: str = "working_tree"
    #: True when the bytes correspond to no commit — untracked at the recorded
    #: commit, or the target is not a git repository.
    unpinned: bool = False


class WebSource(_Forbid):
    url: str
    sha256: str | None = None
    page_date: str | None = None
    http_status: int | None = None


class EvidenceRecord(_Forbid):
    """One evidence entry, exactly as ``EVIDENCE.md`` renders it (U5.14).

    The renderer prints, per entry, its ``source_kind``/``sha256`` line, its
    ``context`` prose and its ``quote`` -- so these five fields are *exactly*
    what a rendered line needs.  Until U5.14 this was an assembly input that
    reached the renderer and was then thrown away, so a bare re-assembly
    replaced the whole "Other evidence entries" prose with ``(none supplied)``
    (the verifier measured 174 -> 120 and 84 -> 23 lines on the two real
    dockets).  Recording it makes the manifest self-sufficient, like
    :class:`ResultRecord` and :class:`PriorArtRecord`.

    ``None`` on the docket = never recorded (a pre-U5.14 manifest); ``[]`` = a
    deliberate clear.  Optional, so every pre-U5.14 manifest keeps validating.
    """

    ref: str
    source_kind: str = "local"
    sha256: str | None = None
    context: str | None = None
    quote: str | None = None


class ResultRecord(_Forbid):
    """One measured result, exactly as ``RESULTS.md`` renders it (U5.11).

    The renderer's row is
    ``| {name} | `{value}` | {unit} | `{command}` | `{source_ref}` |``, so these
    five fields are *exactly* what a rendered line needs: nothing is stored that
    the renderer does not print, and nothing it prints is left out.  That is what
    makes a bare re-assembly byte-identical rather than approximate.

    **Provenance.**  ``command`` is the exact command that produced the number
    (the docket's own rule: no measured number appears without its command) and
    ``source_ref`` is the docket-local reference it came from; both are carried
    verbatim, never re-derived.  When neither was recorded, both stay empty and
    the renderer prints its own ``(none)``/``—`` marker, so the manifest says
    "no provenance was recorded" instead of inventing one.

    ``value`` keeps its JSON type, ``bool`` included *deliberately*: ``True``
    must not be re-rendered as ``1``, which is also why ``bool`` precedes ``int``
    in the union.
    """

    name: str
    value: bool | float | int | str
    unit: str = ""
    command: str = ""
    source_ref: str = ""


class PriorArtRecord(_Forbid):
    """One external anchor, exactly as ``PRIOR_ART.md`` renders it (U5.11).

    The renderer prints a table row (``url``/``page_date``/``verdict``/
    ``sha256``) and then a section per entry (``title``/``url``/``page_date``/
    ``verdict``/``quote``), so all six fields are needed to reproduce the file
    byte-identically.  ``url`` + ``sha256`` are the provenance (which source was
    fetched, and its bytes) and ``verdict`` says what it was taken to establish.

    ``verdict`` is ``str`` deliberately, not :data:`DVerdict`: it mirrors the
    assembler's own ``PriorArt.verdict`` (a free ``str``), so recording a value
    that previously rendered fine can never become a new validation refusal.
    """

    url: str
    title: str | None = None
    page_date: str | None = None
    quote: str | None = None
    verdict: str = "UNVERIFIED"
    sha256: str | None = None


class GeneratedBy(_Forbid):
    app: str = "resextract"
    version: str = "0.1.0"
    model: str | None = None
    #: U5.7 additive.  Who produced the candidates this docket rests on, derived
    #: from the lane's member candidates (never guessed by the renderer).  Any
    #: pre-U5.7 manifest has no such key, so it loads as ``unknown`` — and
    #: ``unknown`` cannot back a model-derived claim, which is the honest answer
    #: for a manifest that never recorded a producer.
    producer: DProducer = "unknown"


class DocketManifest(_Forbid):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: str = Field(default=SCHEMA, alias="schema")
    lane: Lane
    target: Target
    status: DStatus = "draft"
    #: U5.7 additive.  *Why* ``status`` is what it is — in particular, why a
    #: docket is **not** ``ready``.  The producer gate writes its refusal reason
    #: here, so the reason travels with the artifact instead of living only in a
    #: terminal log.  Optional: every pre-U5.7 manifest still validates.
    status_reason: str | None = None
    freshness: Freshness = Field(default_factory=Freshness)
    claims: list[Claim] = Field(default_factory=list)
    material: list[MaterialItem] = Field(default_factory=list)
    web_sources: list[WebSource] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    rework_open: list[str] = Field(default_factory=list)
    generated_by: GeneratedBy = Field(default_factory=GeneratedBy)
    generated_at: str | None = None
    #: U5.11 additive fields.  The two assembly *inputs* that render to
    #: ``RESULTS.md`` / ``PRIOR_ART.md``, recorded so the manifest is
    #: self-sufficient.  ``None`` = never recorded (a pre-U5.11 manifest, or a
    #: docket whose bare re-assembly could only alarm); ``[]`` = a deliberate
    #: clear.  Both optional, so every pre-U5.11 manifest keeps validating and
    #: the schema string is deliberately NOT bumped.
    results: list[ResultRecord] | None = None
    prior_art: list[PriorArtRecord] | None = None
    #: U5.14 additive.  The third recorded render input, on the same
    #: ``None``/``[]`` discipline as the two above.  Without it the
    #: source-kind/context prose of ``EVIDENCE.md`` died on re-assembly.
    evidence: list[EvidenceRecord] | None = None
    #: U5.5 additive field.  ``True`` = the target's HEAD did not move between
    #: the start and the end of the materialization run; ``False`` = it did, and
    #: ``freshness.state`` is then ``needs_rework``.  Optional (default ``None``)
    #: so every pre-U5.5 manifest still validates and the schema string is not
    #: bumped.
    window_sealed: bool | None = None


# --------------------------------------------------------------------------- #
# derived gates (never stored)
# --------------------------------------------------------------------------- #


def producer_gate_reason(producer: str) -> str | None:
    """The one-line refusal reason for a non-``model`` producer, else ``None``."""
    if producer == "model":
        return None
    return (
        f"producer is {producer}: no model mined these candidates; "
        "not publication-eligible"
    )


def promotion_eligible(manifest: "DocketManifest") -> tuple[bool, str | None]:
    """``(True, None)`` only for a docket a model produced **and** that is ``ready``.

    **Derived, never stored.**  The verdict is a pure function of
    ``generated_by.producer`` and ``status``, so it cannot drift out of sync with
    the two fields it depends on: change either field and the verdict changes
    with it.  A stored ``promotable`` flag could sit in a manifest disagreeing
    with that manifest's own producer; this cannot.  Everything the gate refuses —
    ``replay``, ``mixed``, ``fixture``, ``unknown``, and any ``model`` docket not
    yet marked ``ready`` — returns ``(False, <reason>)``.
    """
    producer = manifest.generated_by.producer
    reason = producer_gate_reason(producer)
    if reason is not None:
        return False, reason
    if manifest.status != "ready":
        return False, f"status is {manifest.status!r}, not 'ready'"
    return True, None


# --------------------------------------------------------------------------- #
# reference grammar (shared with assemble.py)
# --------------------------------------------------------------------------- #


def split_ref(ref: str) -> tuple[str, str, tuple[int, int] | None]:
    """Parse ``ref`` into ``(kind, path_or_target, span)``.

    ``kind`` is one of ``file`` (the default), ``graph`` or ``web``.  The span
    is an inclusive 1-based line range or ``None``.
    """
    text = (ref or "").strip()
    kind = "file"
    for scheme in ("file:", "graph:", "web:"):
        if text.startswith(scheme):
            kind = scheme[:-1]
            text = text[len(scheme) :]
            break
    span: tuple[int, int] | None = None
    match = _SPAN_RE.search(text)
    if match:
        lo = int(match.group("lo"))
        hi = int(match.group("hi")) if match.group("hi") else lo
        span = (lo, hi)
        text = text[: match.start()]
    return kind, text, span


def material_dest(path: str) -> str:
    """Normalise a docket-local reference path to a ``material/``-relative dest."""
    p = (path or "").strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    if p.startswith("material/"):
        p = p[len("material/") :]
    return p


def docket_material_path(docket_dir: str | os.PathLike[str], dest: str) -> str:
    return os.path.join(os.fspath(docket_dir), "material", dest)


# --------------------------------------------------------------------------- #
# write / read
# --------------------------------------------------------------------------- #


def dumps_manifest(manifest: DocketManifest) -> str:
    """Deterministic serialisation: sorted keys, indent 2, trailing newline."""
    payload = manifest.model_dump(mode="json", by_alias=True)
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def write_manifest(
    docket_dir: str | os.PathLike[str], manifest: DocketManifest | dict[str, Any]
) -> str:
    """Atomically write ``<docket_dir>/MANIFEST.json``; return the path."""
    if isinstance(manifest, dict):
        manifest = DocketManifest.model_validate(manifest)
    problems = validate_manifest(manifest, docket_dir=os.fspath(docket_dir))
    if problems:
        raise ValueError("refusing to write an invalid MANIFEST.json: " + "; ".join(problems))
    directory = os.fspath(docket_dir)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, MANIFEST_NAME)
    tmp = f"{path}.tmp-{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(dumps_manifest(manifest))
    os.replace(tmp, path)
    return path


def read_manifest(path: str | os.PathLike[str]) -> DocketManifest:
    """Read ``MANIFEST.json`` (path to the file *or* to the docket folder)."""
    p = Path(path)
    if p.is_dir():
        p = p / MANIFEST_NAME
    raw = json.loads(p.read_text(encoding="utf-8"))
    return DocketManifest.model_validate(raw)


# --------------------------------------------------------------------------- #
# validation
# --------------------------------------------------------------------------- #


def _check_local_ref(
    ref: str,
    *,
    docket_dir: str,
    by_dest: dict[str, MaterialItem],
    where: str,
) -> list[str]:
    """Existence + sha256 checks for one docket-local reference."""
    kind, path, span = split_ref(ref)
    if kind in ("graph", "web"):
        return []
    dest = material_dest(path)
    item = by_dest.get(dest)
    if item is None:
        return [
            f"{where}: reference {ref!r} is not a copied material file "
            f"(the docket must be self-contained)"
        ]
    if item.linked:
        return []  # over-cap LINKS.md stub: deliberately not present on disk
    full = docket_material_path(docket_dir, dest)
    if not os.path.isfile(full):
        return [f"{where}: referenced file is missing on disk: material/{dest}"]
    try:
        actual = sha256_file(full)
    except OSError as exc:  # pragma: no cover - unreadable file
        return [f"{where}: cannot hash material/{dest}: {exc}"]
    if actual != item.sha256:
        return [
            f"{where}: sha256 mismatch for material/{dest} "
            f"(manifest {item.sha256[:12]}…, disk {actual[:12]}…)"
        ]
    if span is not None:
        lo, hi = span
        if lo < 1 or hi < lo:
            return [f"{where}: invalid line span {lo}-{hi} for material/{dest}"]
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError as exc:  # pragma: no cover
            return [f"{where}: cannot read material/{dest}: {exc}"]
        if hi > len(lines):
            return [
                f"{where}: line span {lo}-{hi} is past EOF of material/{dest} "
                f"({len(lines)} lines)"
            ]
    return []


def validate_manifest(
    obj_or_path: DocketManifest | dict[str, Any] | str | os.PathLike[str],
    *,
    docket_dir: str | os.PathLike[str] | None = None,
) -> list[str]:
    """Return human-readable problems; an empty list means the manifest is valid."""
    directory: str | None = os.fspath(docket_dir) if docket_dir is not None else None
    if isinstance(obj_or_path, DocketManifest):
        raw: Any = obj_or_path.model_dump(mode="json", by_alias=True)
    elif isinstance(obj_or_path, (str, os.PathLike)):
        p = Path(obj_or_path)
        if p.is_dir():
            p = p / MANIFEST_NAME
        if directory is None:
            directory = os.fspath(p.parent)
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return [f"cannot read {p}: {exc}"]
    else:
        raw = obj_or_path

    problems: list[str] = []
    if not isinstance(raw, dict):
        return [f"manifest must be a JSON object, got {type(raw).__name__}"]
    if raw.get("schema") != SCHEMA:
        problems.append(
            f"schema: expected {SCHEMA!r}, got {raw.get('schema')!r}"
        )

    try:
        manifest = DocketManifest.model_validate(raw)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"])
            problems.append(f"{loc}: {err['msg']}")
        return problems  # structural failure: later checks would be noise

    by_dest = {item.dest: item for item in manifest.material}
    for claim in manifest.claims:
        if not claim.provenance:
            problems.append(f"claims[{claim.id}]: no provenance")
        if not claim.evidence:
            problems.append(f"claims[{claim.id}]: no evidence")
        if directory is not None:
            for ref in claim.evidence:
                problems.extend(
                    _check_local_ref(
                        ref,
                        docket_dir=directory,
                        by_dest=by_dest,
                        where=f"claims[{claim.id}].evidence",
                    )
                )
    if directory is not None:
        for item in manifest.material:
            if item.linked:
                continue
            full = docket_material_path(directory, item.dest)
            if not os.path.isfile(full):
                problems.append(f"material[{item.dest}]: file missing on disk")
                continue
            actual = sha256_file(full)
            if actual != item.sha256:
                problems.append(
                    f"material[{item.dest}]: sha256 mismatch "
                    f"(manifest {item.sha256[:12]}…, disk {actual[:12]}…)"
                )
    return problems
