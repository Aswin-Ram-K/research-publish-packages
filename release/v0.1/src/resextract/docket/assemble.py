"""Docket assembler: turn stored facts + copied material into a docket folder.

One lane = one folder = one publishable item.  :func:`assemble` renders the
whole contract (plan §3.5) deterministically from supplied structure and
*refuses* — via :class:`AssemblyRefused` — rather than emitting a docket that
contains an unsupported claim, a broken material reference, or a publication
type its §3.6 guards do not allow.

Honesty rules baked in here:

* ``EVIDENCE.md`` quotes bytes read from the *copied* files under
  ``material/`` using the line spans in ``material/EXCERPTS.md``.  It never
  reads the source repository, so a docket stays self-contained.
* ``RESULTS.md`` renders only from the structured ``results`` list; with no
  results it says so instead of inventing numbers.
* ``UPDATE_BACKLOG.md`` marks every entry that came from a model rather than a
  measurement with ``model-suggested``.
* ``HISTORY.md`` is append-only; a prior ``ITEM.md`` survives as
  ``ITEM.md.r<N>``.
* **Qualifier (U5.16).**  A bare re-assembly is information-preserving *only
  once the fields are recorded*.  ``lane.title`` and ``evidence`` became
  manifest fields only in U5.14; a manifest written before that records
  neither, so a bare pass over it still loses both (V5E reproduced exactly
  that).  The caller must supply them **once**; after that a bare pass is
  stable and lossless.
* Gates run *before* a single byte is written, so a refusal leaves no
  ``MANIFEST.json`` behind.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, ValidationError

import resextract
from resextract.docket.copy import CopyItem, CopyPlan, CopyReport, sha256_file
from resextract.docket.manifest import (
    EvidenceRecord,
    DOCKET_TYPES,
    PRODUCERS,
    SCHEMA,
    Claim,
    DocketManifest,
    Freshness,
    GeneratedBy,
    Lane,
    MaterialItem,
    Target,
    WebSource,
    docket_material_path,
    material_dest,
    producer_gate_reason,
    read_manifest,
    split_ref,
    validate_manifest,
    write_manifest,
    PriorArtRecord,
    ResultRecord,
)

APP = "resextract"

#: files whose only rule is "rewrite deterministically"
FILE_INDEX: tuple[tuple[str, str], ...] = (
    ("README.md", "entry point: what this is, status, index, one-paragraph pitch"),
    ("ITEM.md", "the publishable artifact (type-specific skeleton, TODO markers)"),
    ("MANIFEST.json", f"machine-readable contract (schema {SCHEMA})"),
    ("CLAIMS.md", "claim sheet → provenance → verification state"),
    ("EVIDENCE.md", "verbatim excerpts read from material/ (path + line + sha256)"),
    ("PRIOR_ART.md", "external anchors + verdicts, or the stub explaining none"),
    ("REFERENCES.md", "citations from actually-fetched sources"),
    ("REFERENCES.bib", "the same citations as BibTeX"),
    ("RESULTS.md", "measured numbers + the exact command that produced each"),
    ("METHOD.md", "rebuilt from graph node ids + file refs"),
    ("CHECKLIST.md", "type-specific publication checklist incl. the licence gate"),
    ("OPEN_QUESTIONS.md", "what remains unproven"),
    ("UPDATE_BACKLOG.md", "work that would bring this item up to date"),
    ("HISTORY.md", "append-only runs, refreshes, verdict changes"),
    ("material/", "byte-copied source material (never link-only)"),
    ("web/", "copied external pages + extracted text"),
    ("repro/", "commands, env pins, run script"),
)

#: type → (item title, section headings)
ITEM_SKELETONS: dict[str, tuple[str, tuple[str, ...]]] = {
    "paper": (
        "Paper draft",
        (
            "Abstract",
            "Introduction",
            "Related work (see PRIOR_ART.md)",
            "Method",
            "Results (see RESULTS.md)",
            "Threats to validity",
            "Conclusion",
        ),
    ),
    "report": (
        "Technical report",
        ("Summary", "Context", "What was measured", "Findings", "Limitations", "Recommendations"),
    ),
    "blog": (
        "Blog post",
        ("Hook", "The problem", "What we found", "How to reproduce it", "Takeaways"),
    ),
    "benchmark_card": (
        "Benchmark card",
        (
            "Benchmark scope",
            "Environment",
            "Metrics",
            "Measured results (see RESULTS.md)",
            "Reproduction commands",
            "Known deviations",
        ),
    ),
    "memo": (
        "Memo",
        ("Question", "What we know (with evidence)", "What we do not know (see OPEN_QUESTIONS.md)", "Next step"),
    ),
}

ITEM_RULE = (
    "> **Evidence rule.** No external claim may be asserted in this item without a\n"
    "> corresponding entry in `PRIOR_ART.md`.  A claim whose external verdict is\n"
    "> `UNVERIFIED` must stay labelled `UNVERIFIED` here.\n"
)

CHECKLIST_COMMON: tuple[str, ...] = (
    "Every claim in `CLAIMS.md` has provenance and evidence (enforced by the assembler).",
    "`EVIDENCE.md` quotes resolve inside `material/` and every sha256 verifies.",
    "`RESULTS.md` numbers match `repro/` commands exactly.",
    "`OPEN_QUESTIONS.md` lists what is still unproven; nothing unproven is stated as fact.",
    "`HISTORY.md` was appended to, not rewritten.",
)

CHECKLIST_BY_TYPE: dict[str, tuple[str, ...]] = {
    "paper": (
        "≥1 claim with verdict `CONFIRMS`/`EXTENDS` (external anchor) — §3.6 guard.",
        "≥1 measured result in `RESULTS.md` — §3.6 guard.",
        "Threats-to-validity section is specific, not generic.",
        "`ITEM.tex` (if produced) compiles with no unresolved references.",
    ),
    "report": (
        "Findings are traceable to a claim id and an evidence quote.",
        "Limitations section names every `UNVERIFIED` claim.",
    ),
    "blog": (
        "Every technical assertion links to a claim id in `CLAIMS.md`.",
        "No measured number appears without its command in `RESULTS.md`.",
    ),
    "benchmark_card": (
        "Every number is recomputable: numeric value + exact command recorded.",
        "Hardware / OS / toolchain versions pinned in `repro/`.",
        "Known deviations from the reference harness are listed.",
    ),
    "memo": (
        "Scope is explicitly limited: this is not a published result.",
        "Any claim promoted later must gain an external anchor first.",
    ),
}

RENDERERS: tuple[str, ...] = ("pdflatex", "pandoc", "tectonic")


# --------------------------------------------------------------------------- #
# input models (loose enough to downgrade an unknown type)
# --------------------------------------------------------------------------- #


class _LaneIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    type: str = "memo"  # noqa: A003
    title: str | None = None
    thesis: str = ""
    audience: str = ""
    status: str | None = None


@dataclass(frozen=True)
class MeasuredResult:
    name: str
    value: float | int | str
    unit: str = ""
    command: str = ""
    source_ref: str = ""


@dataclass(frozen=True)
class BacklogItem:
    text: str
    provenance: str = "unspecified"


@dataclass(frozen=True)
class EvidenceItem:
    ref: str
    source_kind: str = "local"
    quote: str | None = None
    context: str | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class PriorArt:
    url: str
    title: str | None = None
    page_date: str | None = None
    quote: str | None = None
    verdict: str = "UNVERIFIED"
    sha256: str | None = None


@dataclass
class AssembledDocket:
    docket_dir: str
    manifest: DocketManifest
    files: list[str] = field(default_factory=list)
    claims: int = 0
    material: int = 0
    downgrades: list[str] = field(default_factory=list)
    #: U5.9 — one line per *healed* provenance class, e.g. ``material provenance
    #: preserved for 9/9 entries``.  Healing is the normal, good outcome, so it is
    #: summarised (not alarmed per entry); an entry that could NOT be preserved
    #: stays loud per-entry in ``downgrades``.
    preserved: list[str] = field(default_factory=list)
    preserved_item: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "docket_dir": self.docket_dir,
            "files": list(self.files),
            "claims": self.claims,
            "material": self.material,
            "downgrades": list(self.downgrades),
            "preserved": list(self.preserved),
            "preserved_item": self.preserved_item,
            "type": self.manifest.lane.type,
            "status": self.manifest.status,
            "refused": False,
        }


class AssemblyRefused(RuntimeError):
    """Raised instead of emitting a docket that would be dishonest or broken."""

    def __init__(self, reasons: Iterable[str]) -> None:
        self.reasons = list(dict.fromkeys(str(r) for r in reasons if r))
        super().__init__("docket assembly refused: " + "; ".join(self.reasons))


@dataclass
class DocketVerification:
    ok: bool
    problems: list[str]
    claims: int
    material: int
    manifest: DocketManifest | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "problems": list(self.problems),
            "claims": self.claims,
            "material": self.material,
        }


# --------------------------------------------------------------------------- #
# reading what U5.1 already wrote
# --------------------------------------------------------------------------- #

_EXCERPT_ROW = re.compile(
    r"^\|\s*`(?P<dest>[^`]+)`\s*\|\s*(?P<lo>\d+)-(?P<hi>\d+)\s*\|\s*(?P<reason>.*?)\s*\|\s*$"
)
_LINK_ROW = re.compile(
    r"^\|\s*`(?P<dest>[^`]+)`\s*\|\s*`(?P<src>[^`]+)`\s*\|\s*(?P<sha>[0-9a-fA-F]{8,})\s*"
    r"\|\s*(?P<bytes>\d+)\s*\|\s*(?P<cmd>.*?)\s*\|\s*$"
)


def parse_excerpts(path: str | os.PathLike[str]) -> dict[str, tuple[int, int, str]]:
    """``material/EXCERPTS.md`` → ``{dest: (lo, hi, reason)}``."""
    out: dict[str, tuple[int, int, str]] = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        match = _EXCERPT_ROW.match(line.strip())
        if match:
            out[match.group("dest")] = (
                int(match.group("lo")),
                int(match.group("hi")),
                match.group("reason"),
            )
    return out


def parse_links(path: str | os.PathLike[str]) -> dict[str, dict[str, Any]]:
    """``material/LINKS.md`` → ``{dest: {src, sha256, bytes, command}}``."""
    out: dict[str, dict[str, Any]] = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        match = _LINK_ROW.match(line.strip())
        if match:
            out[match.group("dest")] = {
                "src": match.group("src"),
                "sha256": match.group("sha").lower(),
                "bytes": int(match.group("bytes")),
                "command": match.group("cmd"),
            }
    return out


def material_report_from_docket(
    source_docket: str | os.PathLike[str],
    *,
    source_root: str | None = None,
) -> CopyReport:
    """Bridge an existing docket's copied material into a :class:`CopyReport`.

    Used to re-assemble a docket's facts *without* re-copying: spans come from
    ``material/EXCERPTS.md``, over-cap stubs from ``material/LINKS.md``, and
    sha256/bytes are taken from the *copied* bytes inside the docket (never
    from the source repository).  Copying itself stays U5.1's job.
    """
    docket = os.path.abspath(os.fspath(source_docket))
    material_dir = os.path.join(docket, "material")
    excerpts = parse_excerpts(os.path.join(material_dir, "EXCERPTS.md"))
    links = parse_links(os.path.join(material_dir, "LINKS.md"))
    by_dest: dict[str, CopyItem] = {}
    for root, dirs, names in os.walk(material_dir):
        dirs.sort()
        for name in sorted(names):
            if name in ("EXCERPTS.md", "LINKS.md"):
                continue
            full = os.path.join(root, name)
            if not os.path.isfile(full) or os.path.islink(full):
                continue
            dest = os.path.relpath(full, material_dir).replace(os.sep, "/")
            lo_hi = excerpts.get(dest)
            src = os.path.join(source_root, dest) if source_root else dest
            by_dest[dest] = CopyItem(
                src=src,
                dest=dest,
                sha256=sha256_file(full),
                bytes=os.path.getsize(full),
                excerpt=(lo_hi[0], lo_hi[1]) if lo_hi else None,
                reason=lo_hi[2] if lo_hi else "",
                status="copied",
            )
    report = CopyReport()
    for dest in sorted(links):
        row = links[dest]
        item = CopyItem(
            src=row["src"],
            dest=dest,
            sha256=row["sha256"],
            bytes=row["bytes"],
            reason=row.get("command", ""),
            status="linked",
            refusal_reason="over_cap",
        )
        by_dest.setdefault(dest, item)
    report.items = [by_dest[d] for d in sorted(by_dest)]
    report.copied = [i for i in report.items if i.status == "copied"]
    report.linked = [i for i in report.items if i.status == "linked"]
    report.unchanged = [i for i in report.items if i.status == "unchanged"]
    report.total_bytes = sum(i.bytes for i in report.copied) + sum(
        i.bytes for i in report.unchanged
    )
    report.verified = len(report.copied)
    return report


def _coerce_report(material_report: Any, *, source_root: str | None) -> CopyReport:
    if isinstance(material_report, CopyReport):
        return material_report
    if isinstance(material_report, CopyPlan):
        report = CopyReport()
        report.items = list(material_report.items)
        report.copied = list(material_report.to_copy)
        report.linked = list(material_report.to_link)
        report.total_bytes = material_report.total_bytes
        return report
    if isinstance(material_report, (str, os.PathLike)):
        return material_report_from_docket(material_report, source_root=source_root)
    if isinstance(material_report, Mapping):
        report = CopyReport()
        for raw in material_report.get("items", []):
            if isinstance(raw, CopyItem):
                report.items.append(raw)
            else:
                data = dict(raw)
                if isinstance(data.get("excerpt"), list):
                    data["excerpt"] = tuple(data["excerpt"])
                report.items.append(CopyItem(**data))
        report.copied = [i for i in report.items if i.status == "copied"]
        report.unchanged = [i for i in report.items if i.status == "unchanged"]
        report.linked = [i for i in report.items if i.status == "linked"]
        report.refused = [i for i in report.items if i.status == "refused"]
        report.missing = [i for i in report.items if i.status == "missing"]
        report.total_bytes = int(material_report.get("total_bytes", 0))
        return report
    raise AssemblyRefused(
        [f"material_report must be a CopyReport/CopyPlan/path/mapping, got {type(material_report).__name__}"]
    )


def _material_items(report: CopyReport, docket_dir: str) -> list[MaterialItem]:
    """Manifest material rows, spans taken from EXCERPTS.md, stubs from LINKS.md."""
    material_dir = os.path.join(docket_dir, "material")
    excerpts = parse_excerpts(os.path.join(material_dir, "EXCERPTS.md"))
    links = parse_links(os.path.join(material_dir, "LINKS.md"))
    items: dict[str, MaterialItem] = {}
    for item in report.items:
        if item.status not in ("copied", "unchanged", "linked"):
            continue
        dest = item.dest
        span = excerpts.get(dest)
        if span is None and item.excerpt is not None:
            span = (int(item.excerpt[0]), int(item.excerpt[1]), item.reason)
        sha = item.sha256
        if dest in links and sha is None:
            sha = links[dest]["sha256"]
        if not sha:
            continue
        items[dest] = MaterialItem(
            src=item.src,
            dest=dest,
            sha256=sha,
            bytes=int(item.bytes),
            excerpt=[span[0], span[1]] if span else None,
            excerpt_reason=span[2] if span else None,
            linked=item.status == "linked",
            note=links.get(dest, {}).get("command") if item.status == "linked" else None,
        )
    return [items[d] for d in sorted(items)]


def _inherit_material_provenance(
    material: list[MaterialItem],
    previous: DocketManifest | None,
) -> tuple[list[str], list[str], bool]:
    """U5.8 + U5.9: keep the material *record* across a *bare* re-assembly.

    ``_material_items`` rebuilds every row from the current copy report, and a
    report bridged from a docket's own copies
    (:func:`material_report_from_docket`) carries no provenance at all.  So a
    bare re-assembly used to rewrite ``git_object``/``blob_sha`` rows as
    ``working_tree``, re-synthesise ``src`` as ``<source_root>/<dest>``, and drop
    the machine-readable ``note`` — with no error, no ``downgrades`` entry, and
    ``verify_docket`` still ``ok``.  Silently dissolving the docket's central
    promise ("this material is verifiable at commit X, and came from path Y").

    Same discipline U5.7 applied to ``generated_by.producer``: inherit from the
    *existing manifest* rather than regenerating from scratch.  Never blind,
    though — carried only when the row still refers to the same bytes (same
    ``dest`` **and** same ``sha256``).  A row whose bytes changed is
    **recomputed**, because any inherited field on different bytes is a
    fabricated claim, which is worse than the loss being fixed here.  A row with
    no counterpart is new and keeps whatever the current resolution produced
    (nothing is invented).

    ``src`` is the one that is *not* merely inheritance but **preference for the
    authoritative record**: the manifest's recorded ``src`` is the ledger of
    where the bytes actually came from, while the value the bridge re-synthesises
    is ``<source_root>/<dest>`` — a *fallback* that is WRONG whenever ``dest`` and
    the source-relative path differ (``materialize_lane`` repairs exactly this by
    hand at ``materialize.py:1854-1860``, which is the tell that synthesis is the
    lossy direction).  So a bare re-assembly must never overwrite a known-good
    recorded source path with a re-synthesised one; only a row with no matching
    predecessor is left with the synthesised value.  A wrong ``src`` is a *false*
    fact, not merely a missing one.

    ``note`` (the machine-readable unpinned reason) is inherited under the same
    guard; dropping it downgrades an explainable unpinned entry to an unexplained
    one.

    Every entry that could *not* be preserved is returned as a per-entry warning,
    so it is recorded in the assembly report and appended to ``HISTORY.md`` —
    loud, never silent again.  Healed entries are instead summarised in one line
    (the third return value's ``preserved`` line) because healing is the normal
    outcome, not an anomaly.

    Returns ``(warnings, preserved_lines, bytes_preserved)``; ``bytes_preserved``
    is ``True`` only when every previously recorded row is still present with
    byte-identical ``sha256`` (the guard the sealed-window inheritance needs).
    """
    warnings: list[str] = []
    if previous is None:
        return warnings, [], False
    prior = {row.dest: row for row in previous.material}
    healed = 0
    lost = 0
    for item in material:
        old = prior.get(item.dest)
        if old is None:  # new entry: invented provenance is the one thing to avoid
            continue
        if old.sha256 != item.sha256:
            # The bytes moved; every field of the old record describes a different
            # artifact, so nothing may be carried onto this row.
            lost += 1
            dropped: list[str] = []
            if old.src and item.src != old.src:
                dropped.append("src")
            if old.note and not item.note:
                dropped.append("note")
            if old.resolved_from == "git_object" or old.blob_sha:
                dropped.append(f"{old.resolved_from}/blob_sha {old.blob_sha}")
            if old.unpinned:
                dropped.append("unpinned")
            warnings.append(
                f"material/{item.dest}: bytes changed (sha256 "
                f"{old.sha256[:12]}\u2026 \u2192 {item.sha256[:12]}\u2026), provenance recomputed \u2014 "
                f"the previous record was NOT inherited (inheriting it would be a "
                f"fabricated pin on different bytes): {', '.join(dropped) or '(no provenance fields)'}"
            )
            continue
        # Same dest **and** same sha256: the previous record describes exactly
        # these bytes, so its src/note are authoritative, not re-synthesised.
        if old.src and item.src != old.src:
            item.src = old.src
        if old.note and not item.note:
            item.note = old.note
        pinned = old.resolved_from == "git_object"
        if pinned and not old.blob_sha:
            lost += 1
            warnings.append(
                f"material/{item.dest}: previous manifest claimed resolved_from="
                "'git_object' with no blob_sha — not inherited, provenance recomputed"
            )
            continue
        if pinned:
            if item.blob_sha is not None and item.blob_sha != old.blob_sha:
                # Identical bytes, two different pins: pick neither, say so.
                lost += 1
                warnings.append(
                    f"material/{item.dest}: identical bytes but blob_sha disagrees "
                    f"(manifest {old.blob_sha}\u2026 vs resolved {item.blob_sha}\u2026) \u2014 previous "
                    "claim dropped, provenance recomputed"
                )
                continue
            item.resolved_from = "git_object"
            item.blob_sha = old.blob_sha
            item.unpinned = False
        elif old.unpinned and not (item.resolved_from == "git_object" and item.blob_sha):
            # No pin to inherit: keep the current resolution, but do not drop the
            # honest "no commit backs these bytes" flag either.
            item.unpinned = True
        healed += 1
    preserved = (
        [f"material provenance preserved for {healed}/{len(material)} entries"]
        if healed
        else []
    )
    dests = {i.dest: i.sha256 for i in material}
    bytes_preserved = set(prior) == set(dests) and all(
        prior[d].sha256 == dests[d] for d in prior
    )
    return warnings, preserved, bytes_preserved


def _inherit_sealed_window(
    manifest: DocketManifest,
    previous: DocketManifest | None,
    *,
    bytes_preserved: bool,
) -> tuple[list[str], list[str]]:
    """U5.9: keep a verified ``window_sealed`` across a *bare* re-assembly.

    **Deliberate decision: inherited, as a historical fact.**  ``window_sealed``
    records whether the target's HEAD did not move while the material was copied
    (``_seal_window`` / ``materialize.py:1906``).  A bare re-assembly performs
    **no window check at all** — it only re-renders facts from the docket's own
    copies — so writing ``None`` there claims "no check was done" when the check
    *was* done and passed, and *that verified quiescence is precisely the property
    the sealed-window work exists to establish*.  Carrying the historical value
    is therefore informative, not misleading, **provided it can never be
    fabricated**: the value is inherited only when (a) the previous manifest
    recorded a non-``None`` value (never invent one), (b) this assembly did not
    establish a new one, and (c) every previously recorded material row is still
    present with byte-identical ``sha256`` — if the bytes moved, the sealed window
    no longer describes this docket and is *not* carried.

    The alternative (record ``None`` = "this run verified nothing") was rejected:
    it would silently delete a verified property from the artifact on every
    refresh, which is the same silent-provenance-loss family this unit closes.
    The inheritance is summarised once, never alarmed per entry; a value that
    could not be carried IS loud.

    Returns ``(preserved_lines, warning_lines)``.
    """
    if previous is None or previous.window_sealed is None:
        return [], []
    if manifest.window_sealed is not None:  # pragma: no cover - no caller sets it
        return [], []
    if not bytes_preserved:
        return [], [
            f"window_sealed={previous.window_sealed} NOT inherited: material bytes "
            "changed since that window was verified, so the seal no longer "
            "describes this docket (re-run materialization to re-seal)"
        ]
    manifest.window_sealed = previous.window_sealed
    return [
        f"window_sealed={previous.window_sealed} preserved from the previous manifest "
        "(historical fact \u2014 a bare re-assembly performs no window check)"
    ], []


def _same_target(previous_target: Target, current_target: Target) -> bool:
    """Do two ``target`` blocks name the same revision of the same target?"""
    return (
        previous_target.slug,
        previous_target.head_sha,
        previous_target.graph_hash,
    ) == (
        current_target.slug,
        current_target.head_sha,
        current_target.graph_hash,
    )


def _describe_target(target: Target) -> str:
    return (
        f"{target.slug}@{target.head_sha or '(no head)'}"
        f"/{target.graph_hash or '(no graph)'}"
    )


def _inherit_title(
    previous: DocketManifest | None,
    lane_in: _LaneIn,
    *,
    target: Target,
) -> tuple[str | None, list[str], list[str]]:
    """U5.14: the descriptive lane title is a *stored* fact, inherited.

    The same discipline as :func:`_inherit_render_inputs` -- deliberately not a
    parallel scheme:

    * an explicitly supplied ``title`` is used verbatim (``""`` included: an
      explicit empty title is a deliberate **clear**, honoured silently);
    * ``None`` (not supplied) inherits the previous manifest's own
      ``lane.title`` when the target is unchanged;
    * a changed target **refuses** and says so, dropping the stale title rather
      than carrying it;
    * a previous manifest that never recorded a title (every pre-U5.14
      manifest, ``_smoke``) has nothing to inherit and nothing is invented.

    Returns ``(title, preserved_lines, warning_lines)``.
    """
    if lane_in.title is not None:
        return (lane_in.title or None), [], []
    if previous is None or previous.lane.title is None:
        return None, [], []
    if not _same_target(previous.target, target):
        return None, [], [
            "lane.title: NOT inherited -- the target changed "
            f"({_describe_target(previous.target)} -> {_describe_target(target)}); "
            f"the recorded title {previous.lane.title!r} described the previous "
            "target and was dropped rather than carried as stale"
        ]
    return previous.lane.title, [
        f"lane.title preserved from the previous manifest: {previous.lane.title!r}"
    ], []


def _inherit_manifest_lists(
    previous: DocketManifest | None,
    *,
    target: Target,
    supplied_open_questions: Iterable[str] | None,
    supplied_rework: Iterable[Any] | None,
    supplied_web_sources: Iterable[Any] | None,
    current_open_questions: list[str],
    current_rework: list[BacklogItem],
    current_web: list[WebSource],
) -> tuple[list[str], list[BacklogItem], list[WebSource], list[str], list[str]]:
    """U5.10: keep the manifest's *lists* across a bare re-assembly.

    **The hole.**  ``assemble`` built ``open_questions``/``rework_open``/
    ``web_sources`` from its *arguments* only.  A bare re-assembly -- the
    documented refresh entry point (re-render from the docket's own copies;
    ``state/U5.9_bare.py``) -- supplies none of them, so every list was
    rewritten ``[...] -> []`` with no error, no ``downgrades`` entry and
    ``verify_docket`` still ``ok``.  Measured on the fixture docket
    (``state/U5.10-fixture/dock``, manifest sha ``60223b55...`` before the bare
    re-assembly): ``open_questions 2->0``, ``rework_open 1->0``,
    ``web_sources 2->0`` -- the same silent-loss family as U5.8/U5.9.

    **Empty vs absent (the deliberate rule).**  A caller CAN tell the two apart,
    and this function requires it to.  ``None`` means "not supplied -- inherit
    the previous manifest's own recorded value"; an explicit empty iterable
    (``[]``) means "replace it with nothing", i.e. a deliberate **clear**, used
    verbatim, not a downgrade, and raising no alarm.  That is why the
    parameters default to ``None`` rather than ``()``: with ``()`` a bare
    re-assembly and a deliberate clear were the same call, so a genuine clear
    could not be expressed at all.

    **Changed target (the deliberate rule): REFUSE, and say so.**  If the
    previous manifest's target (``slug``/``head_sha``/``graph_hash``) differs
    from the one being assembled, the recorded lists may describe a different
    revision, so they are NOT carried; each non-empty list that could not be
    carried gets its own loud warning naming both revisions, and the list is
    emptied rather than quietly kept stale.  Inheriting them *marked* was
    rejected: marking would either mutate the recorded text of
    ``open_questions``/``rework_open`` (they are ``list[str]``, and this unit
    guarantees inherited values are byte-identical) or add an ``inherited``
    field to ``WebSource`` in a contract that is ``extra="forbid"`` with a
    deliberately un-bumped schema.  To keep the lists across a target change,
    re-supply them for the new target.

    **No fabrication.**  An inherited list is a copy of the previous manifest's
    own values -- never a merge, never a guess, never re-derived from rendered
    markdown.  A list the previous manifest did not record (empty) stays as the
    current assembly produced it.

    Returns ``(open_questions, rework, web, preserved_lines, warning_lines)``;
    healing collapses into ONE summary line, refusals stay per-list and loud.
    """
    preserved: list[str] = []
    warnings: list[str] = []
    if previous is None:
        return current_open_questions, current_rework, current_web, preserved, warnings
    same_target = _same_target(previous.target, target)
    effective: dict[str, Any] = {
        "open_questions": current_open_questions,
        "rework_open": current_rework,
        "web_sources": current_web,
    }
    #: the previous manifest's own values -- byte-identical copies, never aliases
    recorded: dict[str, Any] = {
        "open_questions": list(previous.open_questions),
        "rework_open": [BacklogItem(text=text) for text in previous.rework_open],
        "web_sources": [w.model_copy(deep=True) for w in previous.web_sources],
    }
    supplied: dict[str, Any] = {
        "open_questions": supplied_open_questions,
        "rework_open": supplied_rework,
        "web_sources": supplied_web_sources,
    }
    healed: list[str] = []
    for name in ("open_questions", "rework_open", "web_sources"):
        if supplied[name] is not None:
            continue  # explicit replacement -- INCLUDING an explicit [] (a clear)
        if not recorded[name]:
            continue  # nothing recorded: nothing to preserve, nothing to invent
        if not same_target:
            warnings.append(
                f"{name}: NOT inherited -- the target changed "
                f"({_describe_target(previous.target)} -> {_describe_target(target)}); "
                f"{len(recorded[name])} recorded value(s) describe the previous target and "
                "were dropped rather than carried as stale (re-supply them for the new "
                "target to keep them)"
            )
            continue
        effective[name] = recorded[name]
        healed.append(f"{name} {len(recorded[name])}/{len(recorded[name])}")
    if healed:
        preserved.append(
            "manifest lists preserved from the previous manifest for target "
            + _describe_target(target)
            + ": "
            + ", ".join(healed)
        )
    return (
        effective["open_questions"],
        effective["rework_open"],
        effective["web_sources"],
        preserved,
        warnings,
    )


def _inherit_render_inputs(
    previous: DocketManifest | None,
    *,
    target: Target,
    supplied_results: Iterable[Any] | None,
    supplied_prior_art: Iterable[Any] | None,
    supplied_evidence: Iterable[Any] | None,
    current_results: list[MeasuredResult],
    current_prior_art: list[PriorArt],
    current_evidence: list[EvidenceItem],
) -> tuple[
    list[MeasuredResult], list[PriorArt], list[EvidenceItem], list[str], list[str], list[str]
]:
    """U5.11: the two *render inputs* are manifest fields now -- store + inherit.

    ``results``/``prior_art`` were the last members of the silent re-assembly
    family: rendered to ``RESULTS.md``/``PRIOR_ART.md`` but stored nowhere, so a
    bare re-assembly could only *alarm* about them (U5.10).  ``DocketManifest``
    now carries them as additive, optional records, and this function gives them
    the same discipline as :func:`_inherit_manifest_lists`:

    * ``None`` (not supplied) -> inherit the previous manifest's own records,
      byte-identical, when the target is unchanged; both rendered files then
      round-trip and no alarm is raised.
    * an explicit ``[]`` -> a deliberate **clear**, used verbatim, silent.
    * a changed target -> **REFUSE** per branch with a loud warning naming both
      revisions; stale records are dropped rather than carried.
    * a previous manifest that never recorded them (``None``: every pre-U5.11
      manifest, ``dockets/_smoke`` and ``duval-u55-pinned``) -> nothing to
      inherit; the U5.10 alarm still fires and nothing is re-derived from the
      rendered markdown.

    The ``None``/``[]`` distinction survives on the way *out* too: whether a
    record list is stored at all depends on it (see ``assemble``), so a legacy
    docket does not silently acquire a "deliberately empty" record that would
    later silence the alarm.

    **No fabrication.**  An inherited record is a copy of the previous manifest's
    own values -- never a merge, a guess, or a parse of rendered markdown.

    Returns ``(results, prior_art, preserved_lines, warning_lines,
    recorded_files)``.  ``recorded_files`` names the *manifest* branches the
    previous manifest had recorded (even when empty), which is what lets the
    U5.10 alarm stay silent for them without inventing anything.
    """
    preserved: list[str] = []
    warnings: list[str] = []
    recorded_files: list[str] = []
    if previous is None:
        return (
            current_results,
            current_prior_art,
            current_evidence,
            preserved,
            warnings,
            recorded_files,
        )
    same_target = _same_target(previous.target, target)
    #: the previous manifest's own values -- byte-identical copies, never aliases
    recorder: dict[str, list[Any]] = {
        "results": [
            MeasuredResult(
                name=r.name,
                value=r.value,
                unit=r.unit,
                command=r.command,
                source_ref=r.source_ref,
            )
            for r in (previous.results or [])
        ],
        "prior_art": [
            PriorArt(
                url=a.url,
                title=a.title,
                page_date=a.page_date,
                quote=a.quote,
                verdict=a.verdict,
                sha256=a.sha256,
            )
            for a in (previous.prior_art or [])
        ],
        "evidence": [
            EvidenceItem(
                ref=e.ref,
                source_kind=e.source_kind,
                quote=e.quote,
                context=e.context,
                sha256=e.sha256,
            )
            for e in (previous.evidence or [])
        ],
    }
    #: ``False`` = the previous manifest never recorded this branch at all
    recorded_at_all: dict[str, bool] = {
        "results": previous.results is not None,
        "prior_art": previous.prior_art is not None,
        "evidence": previous.evidence is not None,
    }
    supplied: dict[str, Any] = {
        "results": supplied_results,
        "prior_art": supplied_prior_art,
        "evidence": supplied_evidence,
    }
    effective: dict[str, list[Any]] = {
        "results": current_results,
        "prior_art": current_prior_art,
        "evidence": current_evidence,
    }
    healed: list[str] = []
    for name in ("results", "prior_art", "evidence"):
        if supplied[name] is not None:
            continue  # explicit replacement -- INCLUDING an explicit [] (a clear)
        if not recorded_at_all[name]:
            continue  # never recorded: nothing to inherit, nothing to invent
        recorded_files.append(name)
        if not same_target:
            if recorder[name]:
                warnings.append(
                    f"{name}: NOT inherited -- the target changed "
                    f"({_describe_target(previous.target)} -> {_describe_target(target)}); "
                    f"{len(recorder[name])} recorded value(s) describe the previous target and "
                    "were dropped rather than carried as stale (re-supply them for the new "
                    "target to keep them)"
                )
            continue
        effective[name] = recorder[name]
        if recorder[name]:
            healed.append(f"{name} {len(recorder[name])}/{len(recorder[name])}")
    if healed:
        preserved.append(
            "render inputs preserved from the previous manifest for target "
            + _describe_target(target)
            + ": "
            + ", ".join(healed)
        )
    return (
        effective["results"],
        effective["prior_art"],
        effective["evidence"],
        preserved,
        warnings,
        recorded_files,
    )


#: The exact stubs the renderers emit when there is nothing to render -- their
#: ABSENCE in an existing docket file is the tell that it held real content.
_NO_RESULTS_STUB = "**No measured results recorded.**"
_NO_PRIOR_ART_STUB = "**No external prior art was supplied.**"


def _warn_unsupplied_render_inputs(
    docket: str,
    *,
    supplied_results: Iterable[Any] | None,
    supplied_prior_art: Iterable[Any] | None,
    rendered_results: list[MeasuredResult],
    rendered_prior_art: list[PriorArt],
    recorded_files: Iterable[str] = (),
) -> list[str]:
    """U5.10's alarm, kept for the UNRECORDED case only (U5.11 narrowed it).

    Before U5.11 ``DocketManifest`` was ``extra="forbid"`` and carried no
    ``results``/``prior_art`` key, so those two assembly *inputs* -- rendered to
    ``RESULTS.md``/``PRIOR_ART.md`` and otherwise not persisted -- were
    unrecoverable: a bare re-assembly rewrote real measured numbers to the
    renderer's "No measured results recorded" stub, and no part of the manifest
    could restore them.  U5.11 records them (:func:`_inherit_render_inputs`), so
    this alarm is **suppressed** for a branch the manifest recorded
    (``recorded_files``): those are either healed (silent, one summary line) or
    refused per branch, loudly.  It stays exactly as before for the *unrecorded*
    docket -- every pre-U5.11 manifest, ``dockets/_smoke`` and
    ``dockets/duval/duval-u55-pinned`` included -- which still cannot inherit and
    must still alarm rather than be invented back from rendered markdown.

    This unit does not invent those values back from rendered markdown (that
    would be fabrication, and lossy).  It makes the loss **loud** instead: when
    the existing file held content (detected by the absence of the renderer's
    own stub) and this assembly supplies none, one warning per file is recorded
    in the assembly report and ``HISTORY.md``.  ``None`` (absent) alarms; an
    explicit empty list is a deliberate clear and stays silent -- the same
    empty-vs-absent rule as :func:`_inherit_manifest_lists`.
    """
    warnings: list[str] = []
    recorded = set(recorded_files)
    # the *branch* name (not the file name) is what a recorded manifest holds
    for name, supplied, rendered, stub, branch in (
        ("RESULTS.md", supplied_results, rendered_results, _NO_RESULTS_STUB, "results"),
        ("PRIOR_ART.md", supplied_prior_art, rendered_prior_art, _NO_PRIOR_ART_STUB, "prior_art"),
    ):
        if supplied is not None or rendered or branch in recorded:
            continue  # replaced on purpose, rendered now, or recorded (inherited/refused)
        try:
            existing = Path(os.path.join(docket, name)).read_text(encoding="utf-8")
        except OSError:
            continue  # no previous file: nothing was lost
        if stub not in existing:
            warnings.append(
                f"{name}: NOT preserved -- this docket previously rendered content here "
                "and a bare re-assembly supplies none; 'results'/'prior_art' are not "
                'manifest fields (extra="forbid"), so the values cannot be inherited and '
                "are NOT re-derived from the rendered markdown (re-supply them to re-render)"
            )
    return warnings


def _read_span(docket_dir: str, dest: str, lo: int, hi: int) -> list[str]:
    path = docket_material_path(docket_dir, dest)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        return []
    return [ln.rstrip("\n") for ln in lines[lo - 1 : hi]]


def _line_count(docket_dir: str, dest: str) -> int:
    try:
        with open(docket_material_path(docket_dir, dest), "r", encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp-{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def _as_results(raw: Iterable[Any]) -> list[MeasuredResult]:
    out: list[MeasuredResult] = []
    for item in raw or ():
        if isinstance(item, MeasuredResult):
            out.append(item)
        elif isinstance(item, Mapping):
            out.append(MeasuredResult(**dict(item)))
    return out


def _as_backlog(raw: Iterable[Any]) -> list[BacklogItem]:
    out: list[BacklogItem] = []
    for item in raw or ():
        if isinstance(item, BacklogItem):
            out.append(item)
        elif isinstance(item, str):
            out.append(BacklogItem(text=item))
        elif isinstance(item, Mapping):
            data = dict(item)
            data.setdefault("provenance", data.pop("source", "unspecified"))
            out.append(BacklogItem(**data))
    return out


def _as_evidence(raw: Iterable[Any]) -> list[EvidenceItem]:
    out: list[EvidenceItem] = []
    for item in raw or ():
        if isinstance(item, EvidenceItem):
            out.append(item)
        elif isinstance(item, str):
            out.append(EvidenceItem(ref=item))
        elif isinstance(item, Mapping):
            out.append(EvidenceItem(**dict(item)))
    return out


def _as_prior_art(raw: Iterable[Any]) -> list[PriorArt]:
    out: list[PriorArt] = []
    for item in raw or ():
        if isinstance(item, PriorArt):
            out.append(item)
        elif isinstance(item, Mapping):
            out.append(PriorArt(**dict(item)))
    return out


def _numeric(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    return isinstance(value, str) and bool(re.fullmatch(r"-?\d+(?:\.\d+)?", value.strip()))


def _fmt_span(excerpt: Sequence[int] | None) -> str:
    if not excerpt:
        return "—"
    return f"{excerpt[0]}-{excerpt[1]}"


def _freshness_label(freshness: Freshness) -> str:
    label = freshness.state
    if freshness.age_days is not None:
        label = f"{label} (age {freshness.age_days:g} d)"
    return label


# --------------------------------------------------------------------------- #
# the assembler
# --------------------------------------------------------------------------- #


def _cap_uncapped_claims(claims: list[Claim]) -> list[str]:
    """Cap a passed-in ``CONFIRMS`` whose own producer is not ``model``.

    U5.22 ITEM 1.  The honesty rule already held where a claim is *made*:
    :func:`materialize._claim_standing` caps a verdict-row ``CONFIRMS`` whose
    producer is not exactly ``model``.  It did **not** hold where a claim is
    *written*: ``assemble(claims=...)`` copied the caller's verdict verbatim,
    so a re-render that re-supplied a pre-damage manifest's claims wrote
    ``C-curated -- CONFIRMS`` beside ``generated_by.producer = "replay"``.

    This reuses -- it does not restate -- the permission rule: the single
    predicate :func:`store.producer_is_model`, which is exactly what
    :func:`materialize._claim_standing` calls at its own cap site.  A second
    string comparison against ``"model"`` here would be the very defect this
    unit exists to remove.  ``materialize._claim_standing`` is
    ``MemberSpec``-typed and cannot be called from here without fabricating a
    member row, so the reuse is at the level the two sites genuinely share: the
    predicate, plus the cap-and-record-the-reason shape (never a raise --
    ``materialize`` notes that a typed error would make a rendering typo abort
    a whole docket).

    Fail-closed, as in ``materialize``: ``Claim.producer`` defaults to
    ``"unknown"``, which grants no model standing, so an unattributed
    ``CONFIRMS`` is capped rather than trusted.  Returns one reason per capped
    claim, on ``Claim.verdict_reason`` -- the field the manifest schema
documents for a cap reason, and the one ``CLAIMS.md`` renders verbatim.
That field now also carries the U5.19 provenance-divergence note, which
this function *preserves* when it appends its own reason below (it runs
while ``claim.verdict`` is still ``CONFIRMS``, so an existing note cannot
itself be a cap reason).
The same qualifier applies to the comment at :1241-1243.
    """
    from resextract import store as _store

    recorded: list[str] = []
    for i, claim in enumerate(claims):
        if claim.verdict != "CONFIRMS" or _store.producer_is_model(claim.producer):
            continue
        reason = (
            f"verdict CONFIRMS was passed to assemble() but the claim's producer is "
            f"{claim.producer!r}, not 'model'; capped at EXTENDS by the same rule as "
            "materialize._claim_standing (a non-model run may not assert CONFIRMS)"
        )
        if claim.verdict_reason:
            reason = f"{claim.verdict_reason}; {reason}"
        claims[i] = claim.model_copy(
            update={"verdict": "EXTENDS", "verdict_reason": reason}
        )
        recorded.append(f"claim {claim.id}: {reason}")
    return recorded


def assemble(
    docket_dir: str | os.PathLike[str],
    *,
    lane: Any,
    claims: Iterable[Any],
    #: U5.14 -- ``None`` = not supplied, so it *inherits* the previous
    #: manifest's recorded evidence (a bare re-assembly must not empty it);
    #: an explicit empty iterable is a deliberate clear.  Same rule as the five
    #: below, which it now matches instead of being the one silent hole.
    evidence: Iterable[Any] | None = None,
    material_report: Any,
    #: U5.10 — these five default to ``None`` (= "not supplied"), NOT to ``()``.
    #: The distinction is load-bearing and deliberate: ``None`` means *inherit
    #: what the existing manifest already recorded* (a bare re-assembly passes
    #: nothing and must not empty the lists), while an explicit empty iterable
    #: means *replace it with nothing* — a deliberate clear.  With a default of
    #: ``()`` the two were indistinguishable and a deliberate clear could not be
    #: expressed at all.  See :func:`_inherit_manifest_lists`.
    web_sources: Iterable[Any] | None = None,
    target_meta: Any,
    freshness: Any,
    open_questions: Iterable[str] | None = None,
    rework: Iterable[Any] | None = None,
    model: str = "",
    generated_at: str | None = None,
    results: Iterable[Any] | None = None,
    prior_art: Iterable[Any] | None = None,
    graph_path: str | None = None,
    licence: str | None = None,
    status: str | None = None,
    producer: str | None = None,
    status_reason: str | None = None,
    source_root: str | None = None,
) -> AssembledDocket:
    """Render a docket folder, or raise :class:`AssemblyRefused`.

    Every gate is evaluated before anything is written, so a refusal never
    leaves a ``MANIFEST.json`` (or any other file) behind.

    **Empty vs absent (U5.10, deliberate).**  ``web_sources``,
    ``open_questions``, ``rework``, ``results`` and ``prior_art`` default to
    ``None``, which means "not supplied — inherit the existing manifest's own
    value where it recorded one (and the target is unchanged)".  An explicit
    empty iterable means "replace it with nothing", i.e. a **deliberate clear**;
    that is honoured verbatim and raises no alarm.  A caller can therefore tell
    the two apart, and a genuine clear is possible — but it must be *said*.
    Inheritance across a **changed target** is refused and recorded, never
    silent: see :func:`_inherit_manifest_lists`.
    """
    docket = os.path.abspath(os.fspath(docket_dir))
    reasons: list[str] = []
    downgrades: list[str] = []
    preserved_notes: list[str] = []

    # -- inputs ---------------------------------------------------------------
    try:
        lane_in = lane if isinstance(lane, _LaneIn) else _LaneIn.model_validate(dict(lane))
    except (ValidationError, TypeError, ValueError) as exc:
        raise AssemblyRefused([f"lane: {exc}"]) from exc

    requested_type = lane_in.type
    ctype = requested_type
    if ctype not in DOCKET_TYPES:
        ctype = "memo"
        downgrades.append(
            f"requested type {requested_type!r} is not one of {list(DOCKET_TYPES)} — "
            "downgraded to 'memo' (§3.6: anything unverifiable defaults to memo, never paper)"
        )

    target: Target | None = None
    try:
        target = target_meta if isinstance(target_meta, Target) else Target.model_validate(dict(target_meta))
    except (ValidationError, TypeError, ValueError) as exc:
        reasons.append(f"target: {exc}")

    try:
        fresh = freshness if isinstance(freshness, Freshness) else Freshness.model_validate(dict(freshness))
    except (ValidationError, TypeError, ValueError) as exc:
        reasons.append(f"freshness: {exc}")

    parsed_claims: list[Claim] = []
    for raw in claims or ():
        try:
            parsed_claims.append(raw if isinstance(raw, Claim) else Claim.model_validate(dict(raw)))
        except (ValidationError, TypeError, ValueError) as exc:
            cid = raw.get("id", "?") if isinstance(raw, Mapping) else "?"
            reasons.append(f"claim {cid}: invalid claim structure: {exc}")
    parsed_claims.sort(key=lambda c: c.id)
    # U5.22 ITEM 1 -- the cap is enforced where claims are *written*, not only
    # where they are made: a caller-supplied standing that its own producer
    # cannot back is normalised here, exactly as materialize would.  Like
    # materialize._claim_standing, the reason travels ON the claim
    # (Claim.verdict_reason) rather than through a second, assemble-only
    # channel -- that field is what the manifest schema documents for it.
    _cap_uncapped_claims(parsed_claims)

    evidence_items = _as_evidence(evidence or ())
    measured = _as_results(results)
    backlog = _as_backlog(rework)
    art = _as_prior_art(prior_art)

    try:
        report = _coerce_report(material_report, source_root=source_root)
    except AssemblyRefused as exc:
        reasons.extend(exc.reasons)
        report = CopyReport()

    material = _material_items(report, docket)
    by_dest = {item.dest: item for item in material}

    try:
        web = [
            w if isinstance(w, WebSource) else WebSource.model_validate(dict(w))
            for w in (web_sources or ())
        ]
    except (ValidationError, TypeError, ValueError) as exc:
        reasons.append(f"web_sources: {exc}")
        web = []
    web_urls = {w.url for w in web}

    # -- conflicting prior docket --------------------------------------------
    previous: DocketManifest | None = None
    existing_manifest = os.path.join(docket, "MANIFEST.json")
    if os.path.isfile(existing_manifest):
        try:
            previous = read_manifest(existing_manifest)
        except Exception as exc:  # noqa: BLE001 - report, never crash on prior state
            reasons.append(f"{existing_manifest} exists but cannot be read: {exc}")
        else:
            if previous.lane.slug != lane_in.slug:
                reasons.append(
                    f"docket_dir already holds a docket for lane {previous.lane.slug!r}; "
                    f"refusing to overwrite it with lane {lane_in.slug!r} "
                    "(one lane = one folder = one publishable item)"
                )

    # -- U5.10 manifest-list inheritance (bare re-assembly keeps the lists) ----
    # ``None`` = "not supplied" => inherit the existing manifest's own recorded
    # lists (target unchanged); an explicit ``[]`` = a deliberate clear.  A
    # changed target refuses inheritance per list, loudly (never quietly stale).
    _effective_open = list(open_questions) if open_questions is not None else []
    _effective_web = web
    _effective_rework = backlog
    _lq_preserved: list[str] = []
    _lq_warnings: list[str] = []
    if previous is not None and target is not None:
        (
            _effective_open,
            _effective_rework,
            _effective_web,
            _lq_preserved,
            _lq_warnings,
        ) = _inherit_manifest_lists(
            previous,
            target=target,
            supplied_open_questions=open_questions,
            supplied_rework=rework,
            supplied_web_sources=web_sources,
            current_open_questions=_effective_open,
            current_rework=_effective_rework,
            current_web=_effective_web,
        )
    web = _effective_web
    backlog = _effective_rework
    web_urls = {w.url for w in web}
    downgrades.extend(_lq_warnings)
    preserved_notes.extend(_lq_preserved)
    # -- U5.11 render-input inheritance (results/prior_art are manifest fields) --
    # Same discipline as the lists above: ``None`` inherits (unchanged target
    # only), an explicit ``[]`` is a deliberate clear, a changed target refuses
    # per branch naming both revisions.  ``_ri_recorded`` names the branches the
    # *previous* manifest recorded, which is what silences the U5.10 alarm for
    # them -- and what keeps it firing for an unrecorded (pre-U5.11) docket.
    _ri_preserved: list[str] = []
    _ri_warnings: list[str] = []
    _ri_recorded: list[str] = []
    if previous is not None and target is not None:
        (
            measured,
            art,
            evidence_items,
            _ri_preserved,
            _ri_warnings,
            _ri_recorded,
        ) = _inherit_render_inputs(
            previous,
            target=target,
            supplied_results=results,
            supplied_prior_art=prior_art,
            supplied_evidence=evidence,
            current_results=measured,
            current_prior_art=art,
            current_evidence=evidence_items,
        )
    downgrades.extend(_ri_warnings)
    preserved_notes.extend(_ri_preserved)

    # Store exactly what was rendered -- but only when it *was* recorded (an
    # explicit clear, or an inherited record).  A legacy bare re-assembly stores
    # ``None``, which keeps "never recorded" distinct from "deliberately empty"
    # and keeps the U5.10 alarm honest instead of silencing it with a fake ``[]``.
    stored_results: list[ResultRecord] | None = None
    stored_prior_art: list[PriorArtRecord] | None = None
    stored_evidence: list[EvidenceRecord] | None = None
    try:
        if results is not None or "results" in _ri_recorded:
            stored_results = [
                ResultRecord(
                    name=r.name,
                    value=r.value,
                    unit=r.unit,
                    command=r.command,
                    source_ref=r.source_ref,
                )
                for r in measured
            ]
        if prior_art is not None or "prior_art" in _ri_recorded:
            stored_prior_art = [
                PriorArtRecord(
                    url=a.url,
                    title=a.title,
                    page_date=a.page_date,
                    quote=a.quote,
                    verdict=a.verdict,
                    sha256=a.sha256,
                )
                for a in art
            ]
        if evidence is not None or "evidence" in _ri_recorded:
            stored_evidence = [
                EvidenceRecord(
                    ref=e.ref,
                    source_kind=e.source_kind,
                    sha256=e.sha256,
                    context=e.context,
                    quote=e.quote,
                )
                for e in evidence_items
            ]
    except ValidationError as exc:
        reasons.append(
            f"results/prior_art/evidence: cannot be recorded in MANIFEST.json: {exc}"
        )

    downgrades.extend(
        _warn_unsupplied_render_inputs(
            docket,
            supplied_results=results,
            supplied_prior_art=prior_art,
            rendered_results=measured,
            rendered_prior_art=art,
            recorded_files=_ri_recorded,
        )
    )

    # -- U5.8/U5.9 material provenance inheritance (U5.7 discipline, applied) --
    # A bare re-assembly must not dissolve the material record: each row that
    # still describes the same bytes takes its src/note/resolved_from/blob_sha/
    # unpinned back from the existing manifest (src by *preference for the
    # authoritative record*, never re-synthesis from dest); a row whose bytes
    # changed keeps nothing from the old record and is reported per-entry; and
    # healed rows are summarised in one line (report + HISTORY.md), never silent.
    _mp_warnings, _mp_preserved, _bytes_preserved = _inherit_material_provenance(
        material, previous
    )
    downgrades.extend(_mp_warnings)
    preserved_notes.extend(_mp_preserved)

    # -- gates: claims --------------------------------------------------------
    for claim in parsed_claims:
        if not claim.provenance:
            reasons.append(f"claim {claim.id}: no provenance recorded (every claim needs ≥1)")
        if not claim.evidence:
            reasons.append(f"claim {claim.id}: no evidence recorded (every claim needs ≥1)")
        for ref in claim.evidence:
            kind, path, span = split_ref(ref)
            if kind == "web":
                if path not in web_urls:
                    reasons.append(
                        f"claim {claim.id}: evidence ref {ref!r} names a web source "
                        "that is not in web_sources"
                    )
                continue
            dest = material_dest(path)
            item = by_dest.get(dest)
            if item is None:
                reasons.append(
                    f"claim {claim.id}: evidence ref {ref!r} is not a copied material file "
                    "(a docket must be self-contained)"
                )
                continue
            if item.linked:
                continue
            full = docket_material_path(docket, dest)
            if not os.path.isfile(full):
                reasons.append(
                    f"claim {claim.id}: evidence ref {ref!r} — material file missing: material/{dest}"
                )
                continue
            actual = sha256_file(full)
            if actual != item.sha256:
                reasons.append(
                    f"claim {claim.id}: evidence ref {ref!r} — sha256 mismatch for material/{dest} "
                    f"(manifest {item.sha256[:12]}…, disk {actual[:12]}…)"
                )
                continue
            if span is not None:
                lo, hi = span
                lines = _line_count(docket, dest)
                if lo < 1 or hi < lo or hi > lines:
                    reasons.append(
                        f"claim {claim.id}: evidence ref {ref!r} — line span {lo}-{hi} is "
                        f"outside material/{dest} ({lines} lines)"
                    )
        for ref in claim.provenance:
            kind, path, span = split_ref(ref)
            if kind == "graph":
                continue
            if kind == "web":
                if path not in web_urls:
                    reasons.append(
                        f"claim {claim.id}: provenance ref {ref!r} names a web source "
                        "that is not in web_sources"
                    )
                continue
            dest = material_dest(path)
            item = by_dest.get(dest)
            if item is None:
                reasons.append(
                    f"claim {claim.id}: provenance ref {ref!r} does not resolve to copied "
                    "material (fabricated provenance)"
                )
                continue
            if span is not None and not item.linked:
                lo, hi = span
                lines = _line_count(docket, dest)
                if lo < 1 or hi < lo or hi > lines:
                    reasons.append(
                        f"claim {claim.id}: provenance ref {ref!r} — line span {lo}-{hi} is "
                        f"outside material/{dest} ({lines} lines)"
                    )

    # -- gates: graph anchors -------------------------------------------------
    graph_nodes: dict[str, Any] = {}
    if graph_path:
        try:
            from resextract.kg import read_graph

            graph_nodes = dict(read_graph(graph_path).by_id())
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"graph_path {graph_path!r} cannot be read: {exc}")
    for claim in parsed_claims:
        for ref in claim.provenance:
            kind, path, _span = split_ref(ref)
            if kind != "graph":
                continue
            if graph_nodes and path not in graph_nodes:
                reasons.append(
                    f"claim {claim.id}: provenance ref {ref!r} — graph node {path!r} "
                    "does not exist (fabricated provenance)"
                )

    # -- gates: §3.6 publication-type guards ----------------------------------
    if ctype == "paper":
        anchored = [c.id for c in parsed_claims if c.verdict in ("CONFIRMS", "EXTENDS")]
        if not anchored:
            reasons.append(
                "§3.6 guard: 'paper' requires ≥1 claim with verdict CONFIRMS or EXTENDS "
                "(external anchor) — refused"
            )
        if not measured:
            reasons.append(
                "§3.6 guard: 'paper' requires ≥1 measured result — refused"
            )
    elif ctype == "benchmark_card":
        recomputable = [r for r in measured if _numeric(r.value) and r.command.strip()]
        if not recomputable:
            reasons.append(
                "§3.6 guard: 'benchmark_card' requires ≥1 recomputable measured result "
                "(numeric value + exact command) — refused"
            )

    if reasons:
        raise AssemblyRefused(reasons)

    # -- rendering ------------------------------------------------------------
    assert target is not None and fresh is not None  # narrowed by the gates above
    generated_at = generated_at or _now()
    version = getattr(resextract, "__version__", "0.1.0")
    final_type: Any = ctype
    # U5.14: the descriptive title is inherited on the render-input discipline,
    # so a bare re-assembly keeps "Duval replay-sourced material" instead of
    # collapsing to the lane slug -- *once the title is recorded*: a pre-U5.14
    # manifest recorded none, so that first pass must supply it.
    effective_title, _title_preserved, _title_warnings = _inherit_title(
        previous, lane_in, target=target
    )
    preserved_notes.extend(_title_preserved)
    downgrades.extend(_title_warnings)
    lane_model = Lane(
        slug=lane_in.slug,
        type=final_type,
        title=effective_title,
        thesis=lane_in.thesis,
        audience=lane_in.audience,
    )
    # -- U5.7 producer gate (derived from the manifest, never ad hoc) ---------
    # The effective producer is taken from the *existing manifest* whenever the
    # caller does not state one, so re-assembling a docket cannot drop its
    # provenance line and cannot silently upgrade itself to `model`.  With no
    # prior manifest the default is `unknown`, and unknown never promotes.
    effective_producer = (
        producer
        if producer is not None
        else (previous.generated_by.producer if previous is not None else "unknown")
    )
    if effective_producer not in PRODUCERS:  # pragma: no cover - defensive
        raise AssemblyRefused(
            [f"producer {effective_producer!r} is not one of {list(PRODUCERS)}"]
        )
    requested_status = status or lane_in.status or "draft"
    gate_reason = producer_gate_reason(effective_producer)
    effective_reason = status_reason
    final_status = requested_status
    if gate_reason is not None:
        # assemble is a writer, so the gate holds here too: a non-`model` docket
        # is *never* rendered `ready`, whatever the caller asked for.
        if requested_status == "ready":
            final_status = "draft"
        effective_reason = effective_reason or gate_reason

    manifest = DocketManifest(
        schema_=SCHEMA,
        lane=lane_model,
        target=target,
        status=final_status,
        status_reason=effective_reason,
        freshness=fresh,
        claims=parsed_claims,
        material=material,
        web_sources=web,
        open_questions=_effective_open,
        rework_open=[b.text for b in backlog],
        generated_by=GeneratedBy(
            app=APP, version=version, model=model, producer=effective_producer
        ),
        generated_at=generated_at,
        results=stored_results,
        prior_art=stored_prior_art,
        evidence=stored_evidence,
    )
    # -- U5.9 sealed-window inheritance (historical fact, never fabricated) ----
    _ws_preserved, _ws_warnings = _inherit_sealed_window(
        manifest, previous, bytes_preserved=_bytes_preserved
    )
    preserved_notes.extend(_ws_preserved)
    downgrades.extend(_ws_warnings)
    if preserved_notes:
        # Healing is the normal outcome: ONE summary line, not an alarm per entry.
        preserved_notes = ["; ".join(preserved_notes)]

    ctx = {
        "docket": docket,
        "lane": lane_in,
        "title": effective_title,
        "lane_model": lane_model,
        "target": target,
        "freshness": fresh,
        "manifest": manifest,
        "producer": effective_producer,
        "status": final_status,
        "status_reason": effective_reason,
        "claims": parsed_claims,
        "material": material,
        "by_dest": by_dest,
        "web": web,
        "evidence": evidence_items,
        "results": measured,
        "prior_art": art,
        "open_questions": list(_effective_open),
        "backlog": backlog,
        "model": model,
        "generated_at": generated_at,
        "version": version,
        "ctype": ctype,
        "requested_type": requested_type,
        "downgrades": downgrades,
        "preserved_notes": preserved_notes,
        "licence": licence,
        "graph_nodes": graph_nodes,
        "excerpts": parse_excerpts(os.path.join(docket, "material", "EXCERPTS.md")),
        "links": parse_links(os.path.join(docket, "material", "LINKS.md")),
    }

    # U5.14: one provenance line near the top of EVERY rendered file -- a reader
    # may open RESULTS.md, CLAIMS.md or repro/run.sh first, not only README.md.
    # U5.16: this mapping is the renderer's own list (``BANNER_FILES``) and IS
    # what is written below, so coverage cannot drift from the write path.
    rendered = rendered_banner_texts(ctx)

    # -- writes (all gates passed) -------------------------------------------
    os.makedirs(docket, exist_ok=True)
    preserved = _preserve_item(docket)
    written: list[str] = []
    for name in sorted(rendered):
        dest = os.path.join(docket, *name.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        _write_text(dest, rendered[name])
        written.append(name)
    history_block = _history_block(ctx, preserved)
    _append_history(docket, history_block)
    write_manifest(docket, manifest)
    written.extend(["web/README.md", "repro/README.md", "repro/run.sh", "HISTORY.md", "MANIFEST.json"])

    return AssembledDocket(
        docket_dir=docket,
        manifest=manifest,
        files=sorted(set(written)) + [f"material/{m.dest}" for m in material],
        claims=len(parsed_claims),
        material=len(material),
        downgrades=downgrades,
        preserved=preserved_notes,
        preserved_item=preserved,
    )


# --------------------------------------------------------------------------- #
# history + prior ITEM preservation
# --------------------------------------------------------------------------- #


#: U5.22 ITEM 3 -- how many prior ``ITEM.md`` snapshots a docket keeps.
#:
#: Justification (not "it has always been like that"): this rotation is the only
#: unbounded growth in a docket tree -- every assembly appends one file forever
#: (the two real dockets already hold 4 and 3).  ``5`` is the smallest bound
#: that prunes nothing that exists today (deepest real chain = 4), so it stops
#: the growth without destroying any snapshot currently on disk, while still
#: leaving a reviewer the five most recent ``ITEM.md`` revisions.  ``HISTORY.md``
#: stays append-only and unbounded *by design* -- it is the audit log -- so the
#: snapshots are redundant copies of a record that is still kept in full.
ITEM_SNAPSHOT_KEEP = 5


# A re-render is **not byte-identical**, by construction (U5.31).  Two
# deliberate effects make it so: :func:`_append_history` *appends* a new block
# to ``HISTORY.md`` (the append-only audit log -- never rewritten), and
# :func:`_preserve_item` writes the outgoing ``ITEM.md`` as a fresh
# ``ITEM.md.rN`` snapshot.  That rotation is **destructive**: it keeps only the
# newest :data:`ITEM_SNAPSHOT_KEEP` = 5 snapshots, so once the window is full
# each render also *deletes the oldest* ``ITEM.md.rN`` (V5.30 measured
# r5 -> r6 (+ delete r1) -> r7 (+ delete r2); U5.33 measured the file counts:
# banner-marked files +1 per render **while the window fills**, **net 0 once it
# is full** -- one new snapshot added, the oldest deleted).  What *is* stable is
# ``ITEM.md``'s own content: its sha256 is constant across re-renders (U8.43
# measured it unchanged at every render r0-r7, on both sides of a clock second).
# ``MANIFEST.json`` is **not** stable -- it is rewritten on every render and its
# bytes move as soon as ``generated_at`` (the real clock, :func:`_now`) crosses a
# second (U8.43: identical sha within one second, different across the
# boundary).  A verifier diffing a re-rendered docket must therefore expect a new
# ``HISTORY.md`` block, one new ``ITEM.md.rN``, the loss of the oldest snapshot,
# and a possibly-new ``MANIFEST.json``; byte identity across renders is not a
# contract.
def _preserve_item(docket: str) -> str | None:
    """Preserve the current ``ITEM.md`` as ``ITEM.md.rN``, keeping the newest N.

    U5.22 ITEM 3.  The old allocator took the *first free* index and never
    pruned, so every assembly added a file forever.  The index is now
    ``max(existing) + 1`` -- deliberately **not** first-free: once the bound
    prunes the oldest snapshot, first-free would hand the *newest* content a low
    index and the next round would classify it as oldest and delete the most
    recent prior revision (silent loss of exactly what a reviewer wants).  Only
    the newest :data:`ITEM_SNAPSHOT_KEEP` snapshots are kept.  ``ITEM.md``
    itself is never touched here -- the caller re-renders it afterwards -- so
    the live document survives pruning by construction.
    """
    item = os.path.join(docket, "ITEM.md")
    if not os.path.isfile(item):
        return None
    prior = Path(item).read_text(encoding="utf-8")
    snaps = sorted(
        (int(m.group(1)), name)
        for name in os.listdir(docket)
        if (m := re.match(r"^ITEM\.md\.r(\d+)$", name))
    )
    n = snaps[-1][0] + 1 if snaps else 1
    dest = f"ITEM.md.r{n}"
    _write_text(os.path.join(docket, dest), prior)
    # Keep at most ITEM_SNAPSHOT_KEEP snapshots *including* the one just written.
    excess = len(snaps) - (ITEM_SNAPSHOT_KEEP - 1)
    for _index, name in snaps[: max(0, excess)]:
        os.remove(os.path.join(docket, name))
    return dest


def _history_block(ctx: Mapping[str, Any], preserved: str | None) -> str:
    lines = [
        f"## {ctx['generated_at']} — assembly",
        "",
        f"- lane `{ctx['lane'].slug}` · type `{ctx['ctype']}` · status `{ctx['status']}`",
        f"- claims: {len(ctx['claims'])} · material files: {len(ctx['material'])}",
        f"- model: `{ctx['model'] or '(none)'}` · app {APP} {ctx['version']}",
    ]
    if ctx["downgrades"]:
        for note in ctx["downgrades"]:
            lines.append(f"- **downgrade** — {note}")
    if ctx["preserved_notes"]:
        for note in ctx["preserved_notes"]:
            lines.append(f"- **preserved** — {note}")
    if preserved:
        lines.append(f"- previous `ITEM.md` preserved as `{preserved}`")
    return "\n".join(lines) + "\n"


def _append_history(docket: str, block: str) -> None:
    path = os.path.join(docket, "HISTORY.md")
    header = "# HISTORY — append-only\n"
    try:
        existing = Path(path).read_text(encoding="utf-8")
    except OSError:
        existing = header
    if not existing.strip():
        existing = header
    if not existing.endswith("\n"):
        existing += "\n"
    _write_text(path, existing + "\n" + block.rstrip("\n") + "\n")


# --------------------------------------------------------------------------- #
# renderers
# --------------------------------------------------------------------------- #


def provenance_warning(ctx: Mapping[str, Any]) -> str | None:
    """The visible provenance line for a docket, or ``None`` for a model docket.

    Derived from the manifest that *is being written* — ``ctx["manifest"]`` —
    never from a caller-supplied string, so re-assembly cannot drop it: the same
    manifest field that gates promotion drives the warning.  ``model`` returns
    ``None`` deliberately: a warning shown on every docket would be trained away
    by its readers.
    """
    producer = getattr(ctx.get("manifest"), "generated_by", None)
    producer = getattr(producer, "producer", "unknown") or "unknown"
    if producer == "model":
        return None
    if producer == "mixed":
        detail = (
            "these candidates are **mixed** — at least one was mined by a model "
            "and at least one was not (replay/fixture)"
        )
    elif producer == "unknown":
        detail = "no producer was recorded for these candidates"
    else:
        detail = "no model mined or assessed these candidates"
    return (
        f"> **PROVENANCE: {producer}-produced** — {detail}. "
        "Not eligible for publication until real mining runs."
    )


def _stamp_banner(
    text: str,
    ctx: Mapping[str, Any],
    *,
    bib: bool = False,
    hash_comment: bool = False,
) -> str:
    """U5.14: put the one-line provenance warning near the top of a file.

    V5C measured the warning in ``README.md`` and ``CHECKLIST.md`` **only**, so a
    reader opening ``RESULTS.md`` (or ``EVIDENCE.md``/``CLAIMS.md``/
    ``PRIOR_ART.md``/``ITEM.md``/``METHOD.md``/``UPDATE_BACKLOG.md``/
    ``REFERENCES.*``) first saw no provenance warning at all.  Stamping at the
    single write point makes coverage total and keeps it honest: exactly one
    line, immediately after the H1, and ``None`` for a ``model`` producer -- a
    warning shown on every docket would be trained away by its readers.
    """
    warning = provenance_warning(ctx)
    if not warning:
        return text
    plain = warning.lstrip("> ").replace("**", "")
    if bib:
        # A blockquote is not valid BibTeX; a ``%`` line is the same one line.
        return "% " + plain + "\n" + text
    if hash_comment:
        # U5.16: ``repro/run.sh`` is rendered too and is the file an operator
        # runs first, so it carries the same one line as a ``#`` comment -- a
        # ``>`` blockquote there is a shell syntax error.  It goes *after* the
        # shebang: line 1 must stay ``#!/usr/bin/env bash`` or the script stops
        # being directly executable.
        lines = text.splitlines()
        at = 1 if lines and lines[0].startswith("#!") else 0
        body = "\n".join(lines[:at] + ["# " + plain, ""] + lines[at:])
        return body + ("\n" if text.endswith("\n") else "")
    lines = text.splitlines()
    at = 1
    while at < len(lines) and not lines[at].strip():
        at += 1
    body = "\n".join(lines[:at] + [warning, ""] + lines[at:])
    return body + ("\n" if text.endswith("\n") else "")


#: U5.16 -- the rendered files that DO carry the provenance line.  ``assemble``
#: writes exactly these keys (through :func:`rendered_banner_texts`), so this
#: table and what lands on disk cannot drift: a rendered file must be listed
#: here to be written at all, and ``test_banner_covers_every_rendered_file``
#: parametrises over this same tuple instead of a hand-kept copy.  The previous
#: silent omission was ``repro/run.sh`` (rendered, and the file an operator
#: opens first); ``HISTORY.md`` was, and stays, exempt *with a stated reason*.
BANNER_FILES: tuple[str, ...] = (
    "README.md",
    "CLAIMS.md",
    "EVIDENCE.md",
    "PRIOR_ART.md",
    "REFERENCES.md",
    "REFERENCES.bib",
    "RESULTS.md",
    "METHOD.md",
    "CHECKLIST.md",
    "OPEN_QUESTIONS.md",
    "UPDATE_BACKLOG.md",
    "ITEM.md",
    "web/README.md",
    "repro/README.md",
    "repro/run.sh",
)

#: Rendered-but-deliberately-exempt files, each with the reason it is exempt
#: (U5.16: an unexplained omission is how coverage silently rots).
BANNER_EXEMPT: Mapping[str, str] = {
    "HISTORY.md": (
        "append-only: _append_history only ever appends, so a stamped line "
        "would be re-added on every re-assembly and accumulate"
    ),
    "MANIFEST.json": (
        "machine-readable record, not prose; generated_by.producer already IS "
        "the provenance field the banner only reports"
    ),
}

#: A title made only of markdown punctuation / whitespace -- no heading text.
_PUNCT_ONLY_RE = re.compile(r"""^[\s#*_`|>~=+\-\[\]()!.,:;"\'/\\{}]+$""")


def _h1_text(title: str) -> str:
    """U5.16: a title placed directly after the one ``# `` H1 marker.

    A markdown title beginning with ``#`` used to render ``# # ...`` -- the
    second marker is stray.  Exactly one *leading* run of ``#`` (and the spaces
    after it) is removed; everything else is passed through verbatim: V5E
    confirmed ``|``, backticks, ``_``, ``**`` and the 600-char title survive
    intact and no table breaks.  A title that is *only* markdown punctuation
    (or empty after that strip) cannot form a heading, so it renders as a
    visible placeholder rather than a silently invented value.
    """
    text = re.sub(r"^#+\s*", "", title.strip())
    if text.strip() and not _PUNCT_ONLY_RE.match(text):
        return text
    return "_(untitled)_"


def rendered_banner_texts(ctx: Mapping[str, Any]) -> dict[str, str]:
    """U5.16: the single source of truth for every banner-carrying rendered file.

    Returns ``{docket-relative path: stamped text}`` for exactly
    :data:`BANNER_FILES`.  :func:`assemble` writes this mapping and
    ``tests/test_docket_reassembly.py`` imports :data:`BANNER_FILES`, so the
    coverage list and the renderer share one source and cannot drift.
    """
    bodies: dict[str, str] = {
        "README.md": _render_readme(ctx),
        "CLAIMS.md": _render_claims(ctx),
        "EVIDENCE.md": _render_evidence(ctx),
        "PRIOR_ART.md": _render_prior_art(ctx),
        "REFERENCES.md": _render_references(ctx),
        "REFERENCES.bib": _render_references_bib(ctx),
        "RESULTS.md": _render_results(ctx),
        "METHOD.md": _render_method(ctx),
        "CHECKLIST.md": _render_checklist(ctx),
        "OPEN_QUESTIONS.md": _render_open_questions(ctx),
        "UPDATE_BACKLOG.md": _render_backlog(ctx),
        "ITEM.md": _render_item(ctx),
        "web/README.md": _render_web_readme(ctx),
        "repro/README.md": _render_repro(ctx),
        "repro/run.sh": _render_run_sh(ctx),
    }
    return {
        name: _stamp_banner(
            bodies[name],
            ctx,
            bib=name.endswith(".bib"),
            hash_comment=name.endswith(".sh"),
        )
        for name in BANNER_FILES
    }


def _render_readme(ctx: Mapping[str, Any]) -> str:
    lane = ctx["lane"]
    target = ctx["target"]
    pitch = lane.thesis.strip() or "TODO: one paragraph on what this item claims and why it matters."
    head = target.head_sha or "(unknown)"
    title = ctx.get("title") or lane.title or lane.slug
    lines = [
        f"# {_h1_text(title)} — {ctx['ctype']} docket",
        "",
        f"**Status:** {ctx['status']} · **Type:** {ctx['ctype']} · **Target:** `{target.slug}` @ `{head}`",
        f"**Freshness:** {_freshness_label(ctx['freshness'])} · **Generated:** {ctx['generated_at']} "
        f"by {APP} {ctx['version']}"
        + (f" (model: `{ctx['model']}`)" if ctx["model"] else ""),
        "",
    ]
    if ctx.get("status_reason"):
        lines.extend([f"**Why not `ready`:** {ctx['status_reason']}", ""])
    lines.extend(
        [
            "## What this is",
            "",
            pitch,
            "",
            f"**Audience.** {lane.audience.strip() or 'TODO: name the reader.'}",
            "",
            "One lane = one folder = one publishable item. Every claim below is backed by a",
            "byte-copy inside `material/`; nothing here links only to the source repository.",
            "",
        ]
    )
    if ctx["downgrades"]:
        lines.extend(["## Downgrades recorded", ""])
        lines.extend(f"- {note}" for note in ctx["downgrades"])
        lines.append("")
    lines.extend(["## Index", "", "| path | what it holds |", "| --- | --- |"])
    for name, what in FILE_INDEX:
        lines.append(f"| `{name}` | {what} |")
    lines.append("")
    if ctx["material"]:
        lines.extend(["## Material", "", "| dest | lines | bytes | sha256 |", "| --- | --- | --- | --- |"])
        for item in ctx["material"]:
            sha = item.sha256[:12] + "…"
            suffix = " (LINKS.md stub)" if item.linked else ""
            lines.append(
                f"| `material/{item.dest}`{suffix} | {_fmt_span(item.excerpt)} | {item.bytes} | `{sha}` |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _render_claims(ctx: Mapping[str, Any]) -> str:
    lines = [
        "# CLAIMS — claim sheet",
        "",
        "Each claim carries its provenance (where it came from) and its evidence refs",
        "(the copied material that backs it). The assembler refuses a docket in which",
        "either list is empty.",
        "",
    ]
    for claim in ctx["claims"]:
        lines.extend(
            [
                f"## {claim.id} — {claim.verdict}",
                "",
                f"**Claim.** {claim.text}",
                "",
                f"**Kind.** {claim.kind or '(unspecified)'}",
                "",
                f"**Verification state.** {claim.verdict}"
                # U5.13/U5.14: a *capped* standing must be legible -- the reason
                # travels with the state, on the same line, and an uncapped claim
                # prints no empty reason line.  U5.16 (V5E): the old label read
                # "— capped: <reason>" beside a reason that itself said "capped at
                # EXTENDS", so the word appeared twice and the reason's "maps to
                # CONFIRMS" sat next to a rendered EXTENDS.  The frame no longer
                # restates the cap: it says a note was recorded on write (true for
                # a cap and for a producer note alike) and quotes it once,
                # verbatim -- the *declared* value stays visibly declared.
                + (
                    " — a standing note was recorded on write and is quoted "
                    f"verbatim: {claim.verdict_reason}"
                    if getattr(claim, "verdict_reason", None)
                    else ""
                ),
                "",
                "**Provenance.** " + ", ".join(f"`{p}`" for p in claim.provenance),
                "",
                "**Evidence.** " + ", ".join(f"`{e}`" for e in claim.evidence),
                "",
            ]
        )
    return "\n".join(lines).rstrip("\n") + "\n"


def _render_evidence(ctx: Mapping[str, Any]) -> str:
    docket = ctx["docket"]
    # U5.14: ``evidence`` is a *stored* render input now, so its source-kind /
    # sha256 / context prose survives a bare re-assembly -- *once the field is
    # recorded*.  A manifest written before U5.14 recorded none, so a bare pass
    # over it still loses this prose; the caller must supply ``evidence`` once
    # (V5E reproduced exactly that).  It is **merged** into
    # the per-material block for the same ref rather than printed a second time:
    # the de-duplication the verifier saw is kept, the prose is not dropped.
    by_ref: dict[str, list[Any]] = {}
    for ev in ctx["evidence"]:
        by_ref.setdefault(ev.ref, []).append(ev)

    def _context_lines(ref: str) -> list[str]:
        entries = by_ref.get(ref) or []
        if not entries:
            return []
        kinds = sorted({e.source_kind for e in entries})
        shas = sorted({e.sha256 for e in entries if e.sha256})
        contexts: list[str] = []
        for e in entries:
            if e.context and e.context not in contexts:
                contexts.append(e.context)
        line = "- source kind: " + ", ".join(f"`{k}`" for k in kinds)
        if shas:
            line += " · sha256 " + ", ".join(f"`{s}`" for s in shas)
        if contexts:
            line += " · context: " + " · ".join(contexts)
        out = [line, ""]
        for e in entries:
            if e.quote:
                out.extend(["```text", e.quote.rstrip("\n"), "```", ""])
        return out

    lines = [
        "# EVIDENCE — verbatim excerpts from this docket's own `material/`",
        "",
        "> Every quote below is read from a byte-copy inside `material/`, using the line",
        "> spans in `material/EXCERPTS.md`. Nothing is quoted from the source repository,",
        "> so this docket can be verified without the repo. The sha256 is of the copied file.",
        "",
        "## Copied material",
        "",
        "| dest | lines | bytes | sha256 |",
        "| --- | --- | --- | --- |",
    ]
    for item in ctx["material"]:
        lines.append(
            f"| `material/{item.dest}` | {_fmt_span(item.excerpt)} | {item.bytes} | `{item.sha256}` |"
        )
    if not ctx["material"]:
        lines.append("| _(no material copied)_ | — | — | — |")
    lines.append("")
    covered: set[str] = set()
    for item in ctx["material"]:
        ref = f"material/{item.dest}"
        if item.linked:
            lines.extend(
                [
                    f"## `material/{item.dest}` — over cap, not copied",
                    "",
                    f"Source path, sha256 and byte size are recorded in `material/LINKS.md`; "
                    f"sha256 `{item.sha256}`, {item.bytes} bytes.",
                    "",
                ]
            )
            if item.note:
                lines.extend(["```sh", item.note, "```", ""])
            lines.extend(_context_lines(ref))
            covered.add(ref)
            continue
        if not item.excerpt:
            # no block is emitted for this ref, so its evidence prose stays in
            # the "Other evidence entries" section below rather than vanishing
            continue
        lo, hi = item.excerpt
        excerpt = _read_span(docket, item.dest, lo, hi)
        lines.extend(
            [
                f"## `material/{item.dest}` — lines {lo}-{hi}",
                "",
                f"sha256 `{item.sha256}` · {item.bytes} bytes"
                + (f" · reason: {item.excerpt_reason}" if item.excerpt_reason else ""),
                "",
            ]
        )
        lines.extend(_context_lines(ref))
        if not excerpt:
            lines.extend(["> **WARNING:** the span could not be read from the copied file.", ""])
        else:
            lines.extend(["```text", *excerpt, "```", ""])
        covered.add(ref)
    lines.extend(["## Other evidence entries", ""])
    unmerged = [ev for ev in ctx["evidence"] if ev.ref not in covered]
    if not ctx["evidence"]:
        lines.append("_(none supplied)_")
        lines.append("")
    elif not unmerged:
        lines.append(
            "_(none unmerged — every entry's source kind, sha256 and context is merged "
            "into its `material/` block above; no datum is printed twice)_"
        )
        lines.append("")
    for ev in unmerged:
        lines.extend(
            [
                f"### `{ev.ref}`",
                "",
                f"- source kind: `{ev.source_kind}`"
                + (f" · sha256 `{ev.sha256}`" if ev.sha256 else ""),
            ]
        )
        if ev.context:
            lines.append(f"- context: {ev.context}")
        if ev.quote:
            lines.extend(["", "```text", ev.quote.rstrip("\n"), "```"])
        else:
            lines.append("")
            lines.append("_No stored quote; see the copied material above._")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _render_results(ctx: Mapping[str, Any]) -> str:
    lines = [
        "# RESULTS — measured numbers",
        "",
        "Rendered only from structured measured results; the assembler never invents a",
        "number. Each row records the exact command that produced it.",
        "",
    ]
    if not ctx["results"]:
        lines.extend(["**No measured results recorded.** Nothing in this docket is a measurement.", ""])
        return "\n".join(lines)
    lines.extend(["| name | value | unit | command | source |", "| --- | --- | --- | --- | --- |"])
    for r in ctx["results"]:
        lines.append(
            f"| {r.name} | `{r.value}` | {r.unit or '—'} | `{r.command or '(none)'}` | `{r.source_ref or '—'}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _graph_label(node: Any) -> str:
    for attr in ("kind", "type", "label", "name", "title"):
        value = getattr(node, attr, None)
        if isinstance(value, str) and value:
            return value
    return "node"


def _render_method(ctx: Mapping[str, Any]) -> str:
    lines = [
        "# METHOD — reconstructed from provenance",
        "",
        "This is not copied prose: it is the provenance ledger, rebuilt from the graph",
        "node ids and file references attached to each claim.",
        "",
        "## Graph anchors",
        "",
    ]
    graph_nodes = ctx["graph_nodes"]
    if graph_nodes:
        lines.extend(["| node | present | kind |", "| --- | --- | --- |"])
        seen: set[str] = set()
        for claim in ctx["claims"]:
            for ref in claim.provenance:
                kind, path, _ = split_ref(ref)
                if kind == "graph" and path not in seen:
                    seen.add(path)
                    node = graph_nodes.get(path)
                    lines.append(f"| `{path}` | {'yes' if node else 'no'} | {_graph_label(node) if node else '—'} |")
        if not seen:
            lines.append("| _(none)_ | — | — |")
    else:
        lines.append(
            "_No knowledge graph was supplied, so graph node ids below are recorded as"
            " unverified (they were not checked against a graph)._"
        )
    lines.append("")
    lines.extend(["## File anchors", "", "| claim | ref | material dest | sha256 |", "| --- | --- | --- | --- |"])
    any_file = False
    for claim in ctx["claims"]:
        for ref in claim.provenance:
            kind, path, _ = split_ref(ref)
            if kind != "file":
                continue
            any_file = True
            dest = material_dest(path)
            item = ctx["by_dest"].get(dest)
            lines.append(
                f"| {claim.id} | `{ref}` | `material/{dest}` | "
                f"{'`' + item.sha256[:12] + '…`' if item else '(not copied)'} |"
            )
    if not any_file:
        lines.append("| _(none)_ | — | — | — |")
    lines.append("")
    lines.extend(["## Per-claim provenance", ""])
    for claim in ctx["claims"]:
        lines.append(f"- **{claim.id}** — " + ", ".join(f"`{p}`" for p in claim.provenance))
    lines.append("")
    return "\n".join(lines)


def _render_prior_art(ctx: Mapping[str, Any]) -> str:
    art = ctx["prior_art"]
    lines = ["# PRIOR_ART — external anchors", "", ITEM_RULE]
    if not art:
        pending = [c.id for c in ctx["claims"] if c.verdict in ("UNVERIFIED", "CONTRADICTS")] or [
            c.id for c in ctx["claims"]
        ]
        lines.extend(
            [
                "**No external prior art was supplied.** This docket therefore makes no",
                "externally-anchored claim: any claim without an entry here is `UNVERIFIED`",
                "as a statement about the outside world.",
                "",
                "Claims still needing external verification: "
                + (", ".join(pending) if pending else "_(none)_"),
                "",
            ]
        )
        return "\n".join(lines)
    lines.extend(["| url | page date | verdict | sha256 |", "| --- | --- | --- | --- |"])
    for a in art:
        lines.append(
            f"| {a.url} | {a.page_date or '—'} | {a.verdict} | `{a.sha256 or '—'}` |"
        )
    lines.append("")
    for a in art:
        lines.append(f"## {a.title or a.url}")
        lines.append("")
        lines.append(f"- URL: {a.url}")
        lines.append(f"- Page date: {a.page_date or '(unknown)'}")
        lines.append(f"- Verdict: `{a.verdict}`")
        if a.quote:
            lines.extend(["", "```text", a.quote.rstrip("\n"), "```"])
        lines.append("")
    return "\n".join(lines)


def _render_references(ctx: Mapping[str, Any]) -> str:
    lines = [
        "# REFERENCES — citations from actually-fetched sources",
        "",
    ]
    entries = list(ctx["prior_art"])
    if ctx["web"]:
        for w in ctx["web"]:
            entries.append(PriorArt(url=w.url, page_date=w.page_date, sha256=w.sha256))
    if not entries:
        lines.extend(
            [
                "**No sources were fetched for this assembly.** No citation is listed here,",
                "because a citation that was never fetched would not be a reference.",
                "",
            ]
        )
        return "\n".join(lines)
    for i, a in enumerate(entries, start=1):
        date = a.page_date or "n.d."
        lines.append(f"{i}. {a.title or a.url} — {date} — {a.url}")
    lines.append("")
    return "\n".join(lines)


def _render_references_bib(ctx: Mapping[str, Any]) -> str:
    entries = list(ctx["prior_art"])
    for w in ctx["web"]:
        entries.append(PriorArt(url=w.url, page_date=w.page_date, sha256=w.sha256))
    lines = ["% generated by resextract docket assembler — only actually-fetched sources"]
    for i, a in enumerate(entries, start=1):
        year = (a.page_date or "n.d.")[:4]
        lines.append(f"@misc{{resextract{i}, title={{{a.title or a.url}}}, year={{{year}}}, url={{{a.url}}}}}")
    lines.append("")
    return "\n".join(lines)


def _render_open_questions(ctx: Mapping[str, Any]) -> str:
    lines = ["# OPEN_QUESTIONS — what remains unproven", ""]
    questions = list(ctx["open_questions"])
    for claim in ctx["claims"]:
        if claim.verdict in ("UNVERIFIED", "CONTRADICTS"):
            q = f"What would settle `{claim.id}` ({claim.verdict}): {claim.text}"
            if q not in questions:
                questions.append(q)
    if not questions:
        lines.append("_(none recorded)_")
    else:
        lines.extend(f"- {q}" for q in questions)
    lines.append("")
    return "\n".join(lines)


def _render_backlog(ctx: Mapping[str, Any]) -> str:
    lines = [
        "# UPDATE_BACKLOG — what would bring this item up to date",
        "",
        "> Entries marked `model-suggested` came from a model, not from a measurement.",
        "> Never treat them as measured fact.",
        "",
    ]
    if not ctx["backlog"]:
        lines.append("_(nothing open)_")
    for item in ctx["backlog"]:
        provenance = item.provenance or "unspecified"
        lines.append(f"- **[{provenance}]** {item.text}")
    lines.append("")
    return "\n".join(lines)


def _render_item(ctx: Mapping[str, Any]) -> str:
    title, sections = ITEM_SKELETONS.get(ctx["ctype"], ITEM_SKELETONS["memo"])
    lane = ctx["lane"]
    lines = [
        f"# {_h1_text(ctx.get('title') or lane.title or lane.slug)} — {title}",
        "",
        ITEM_RULE,
        f"> **Skeleton.** Type `{ctx['ctype']}`; every heading below still carries a `TODO`.",
        f"> Fill it from `CLAIMS.md` / `EVIDENCE.md` / `RESULTS.md` only — those are the ledger.",
        "",
    ]
    if ctx["prior_art"]:
        lines.append(f"> External anchors currently recorded: {len(ctx['prior_art'])} (see `PRIOR_ART.md`).")
    else:
        lines.append("> **No `PRIOR_ART.md` entries exist yet**, so this item may not assert anything about the outside world.")
    lines.append("")
    for section in sections:
        lines.extend(
            [
                f"## {section}",
                "",
                f"<!-- TODO(U5.2): {section} — write from the claim/evidence ledger; no new facts. -->",
                "",
            ]
        )
    lines.extend(
        [
            "## Licence and attribution",
            "",
            "<!-- TODO(U5.2): state the target's licence and how material/ is attributed. -->",
            "",
        ]
    )
    return "\n".join(lines)


def _installed_renderers() -> dict[str, str | None]:
    return {name: shutil.which(name) for name in RENDERERS}


def _render_checklist(ctx: Mapping[str, Any]) -> str:
    ctype = ctx["ctype"]
    lines = [f"# CHECKLIST — {ctype}", ""]
    if ctx.get("status_reason"):
        lines.extend([f"> **Status reason:** {ctx['status_reason']}", ""])
    if ctx["requested_type"] != ctype:
        lines.extend(
            [
                f"> Requested type `{ctx['requested_type']}` was downgraded to `{ctype}` (§3.6).",
                "",
            ]
        )
    lines.extend(["## Always", ""])
    lines.append(
        "- [ ] **Licence gate** — confirm the target's licence permits publication of this "
        "item and of the copied `material/`."
    )
    if ctx["licence"]:
        lines.append(f"      Target licence: **{ctx['licence']}**.")
    for item in CHECKLIST_COMMON:
        lines.append(f"- [ ] {item}")
    lines.extend(["", f"## Type: {ctype}", ""])
    for item in CHECKLIST_BY_TYPE.get(ctype, CHECKLIST_BY_TYPE["memo"]):
        lines.append(f"- [ ] {item}")
    tools = _installed_renderers()
    available = {k: v for k, v in tools.items() if v}
    lines.extend(["", "## Export", ""])
    if available:
        for name, path in available.items():
            lines.append(f"- [ ] Render PDF/HTML with `{name}` (`{path}`) and attach it.")
    else:
        lines.append(
            "- [ ] **PDF export unavailable** — none of `pdflatex`, `pandoc` or `tectonic` "
            "is installed. Install TeX Live (`pdflatex`), Pandoc (`pandoc`) or Tectonic "
            "(`tectonic`) to render this item to PDF."
        )
    lines.extend(["", "## Integrity", ""])
    lines.append("- [ ] `MANIFEST.json` validates with `verify_docket()` (schema, enums, sha256).")
    lines.append("- [ ] `HISTORY.md` append-only: no prior line was removed.")
    lines.append("")
    return "\n".join(lines)


def _render_web_readme(ctx: Mapping[str, Any]) -> str:
    lines = [
        "# web/ — copied external pages",
        "",
    ]
    if not ctx["web"]:
        lines.extend(
            [
                "**No external pages have been copied into this docket.**",
                "",
                "Web research has not run for this lane; `PRIOR_ART.md` says so explicitly.",
                "",
            ]
        )
        return "\n".join(lines)
    lines.extend(["| url | page date | http status | sha256 |", "| --- | --- | --- | --- |"])
    for w in ctx["web"]:
        lines.append(f"| {w.url} | {w.page_date or '—'} | {w.http_status if w.http_status is not None else '—'} | `{w.sha256 or '—'}` |")
    lines.append("")
    return "\n".join(lines)


def _render_repro(ctx: Mapping[str, Any]) -> str:
    lines = [
        "# repro/ — reproduction",
        "",
        "Environment pins:",
        "",
        f"- app: {APP} {ctx['version']}",
        f"- assembled at: {ctx['generated_at']}",
        f"- schema: {SCHEMA}",
        f"- target: `{ctx['target'].slug}` @ `{ctx['target'].head_sha or '(unknown)'}`",
        f"- graph hash: `{ctx['target'].graph_hash or '(none)'}`",
        "",
    ]
    if ctx["results"]:
        lines.extend(["## Commands", "", "```sh"])
        for r in ctx["results"]:
            lines.append(f"# {r.name} = {r.value} {r.unit}".rstrip())
            lines.append(r.command or "# (no command recorded)")
        lines.extend(["```", ""])
    else:
        lines.extend(
            [
                "## Commands",
                "",
                "_(no measured results recorded, so there is nothing to reproduce yet)_",
                "",
            ]
        )
    lines.append("Run `bash repro/run.sh` to replay the recorded commands.")
    lines.append("")
    return "\n".join(lines)


def _render_run_sh(ctx: Mapping[str, Any]) -> str:
    lines = ["#!/usr/bin/env bash", "# generated by the resextract docket assembler", "set -euo pipefail", ""]
    if not ctx["results"]:
        lines.extend(['echo "no measured results recorded in this docket"'])
    for r in ctx["results"]:
        lines.append(f"# {r.name} = {r.value} {r.unit}".rstrip())
        lines.append(r.command or "true")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# verification (what `resextract status` / the refresh engine calls)
# --------------------------------------------------------------------------- #


def _claim_standing_problems(manifest: DocketManifest) -> list[str]:
    """U5.22 ITEM 2 -- claims whose standing contradicts their backing producer.

    Condition checked, exactly::

        claim.verdict == "CONFIRMS" and not store.producer_is_model(claim.producer)

    ``claim.producer`` is the *assessing* producer (``materialize._claim_for``
    records the verdict row's producer when a verdict assesses the claim, the
    candidate's otherwise -- U5.15/U5.19), so it is the value the cap is judged
    on and the only value that can contradict the standing.  The docket-level
    ``generated_by.producer`` is deliberately **not** the gate: a model verdict
    may legitimately bless replay-mined material
    (``store.may_back_model_claim_verdict``, recorded as ``materialize`` F2), so
    gating on it would flag a correct docket.  It is quoted as context only.

    Fail-closed: ``producer`` defaults to ``"unknown"``, which grants no model
    standing, so a claim that recorded no assessor is flagged rather than
    trusted.  A pre-existing manifest is **flagged, never rewritten** -- this
    is a reader; the render-side cap is :func:`_cap_uncapped_claims`.  Together
    they are the two-sided fix: the writer can no longer *produce* the
    contradiction and the verifier can no longer *pass* it.
    """
    from resextract import store as _store

    mine = manifest.generated_by.producer
    problems: list[str] = []
    for claim in manifest.claims:
        if claim.verdict != "CONFIRMS" or _store.producer_is_model(claim.producer):
            continue
        problems.append(
            f"claim {claim.id}: standing CONFIRMS contradicts its backing producer "
            f"{claim.producer!r}, not 'model' (docket generated_by.producer={mine!r}) "
            "-- a non-model run may not assert CONFIRMS; re-derive the claim through "
            "materialize so the cap applies, or record mechanically-verified facts as "
            "a distinct standing (U5.22 follow-up)"
        )
    return problems


def verify_docket(docket_dir: str | os.PathLike[str]) -> DocketVerification:
    """Re-read ``MANIFEST.json`` and verify it against what is on disk.

    U5.22 ITEM 2: the structural check in :func:`validate_manifest` is
    extended with :func:`_claim_standing_problems`, so a docket whose claim
    asserts a standing its own producer cannot back is **not** reported ok.
    """
    docket = os.path.abspath(os.fspath(docket_dir))
    path = os.path.join(docket, "MANIFEST.json")
    if not os.path.isfile(path):
        return DocketVerification(False, [f"MANIFEST.json not found in {docket}"], 0, 0, None)
    try:
        manifest = read_manifest(path)
    except Exception as exc:  # noqa: BLE001
        return DocketVerification(False, [f"MANIFEST.json is invalid: {exc}"], 0, 0, None)
    problems = list(validate_manifest(manifest, docket_dir=docket))
    problems.extend(_claim_standing_problems(manifest))
    return DocketVerification(
        ok=not problems,
        problems=problems,
        claims=len(manifest.claims),
        material=len(manifest.material),
        manifest=manifest,
    )
