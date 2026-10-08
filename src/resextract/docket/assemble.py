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
    DOCKET_TYPES,
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
    read_manifest,
    split_ref,
    validate_manifest,
    write_manifest,
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
    preserved_item: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "docket_dir": self.docket_dir,
            "files": list(self.files),
            "claims": self.claims,
            "material": self.material,
            "downgrades": list(self.downgrades),
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


def assemble(
    docket_dir: str | os.PathLike[str],
    *,
    lane: Any,
    claims: Iterable[Any],
    evidence: Iterable[Any] = (),
    material_report: Any,
    web_sources: Iterable[Any] = (),
    target_meta: Any,
    freshness: Any,
    open_questions: Iterable[str] = (),
    rework: Iterable[Any] = (),
    model: str = "",
    generated_at: str | None = None,
    results: Iterable[Any] = (),
    prior_art: Iterable[Any] = (),
    graph_path: str | None = None,
    licence: str | None = None,
    status: str | None = None,
    source_root: str | None = None,
) -> AssembledDocket:
    """Render a docket folder, or raise :class:`AssemblyRefused`.

    Every gate is evaluated before anything is written, so a refusal never
    leaves a ``MANIFEST.json`` (or any other file) behind.
    """
    docket = os.path.abspath(os.fspath(docket_dir))
    reasons: list[str] = []
    downgrades: list[str] = []

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

    evidence_items = _as_evidence(evidence)
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
    lane_model = Lane(
        slug=lane_in.slug,
        type=final_type,
        thesis=lane_in.thesis,
        audience=lane_in.audience,
    )
    ctx = {
        "docket": docket,
        "lane": lane_in,
        "lane_model": lane_model,
        "target": target,
        "freshness": fresh,
        "status": status or lane_in.status or "draft",
        "claims": parsed_claims,
        "material": material,
        "by_dest": by_dest,
        "web": web,
        "evidence": evidence_items,
        "results": measured,
        "prior_art": art,
        "open_questions": list(open_questions or ()),
        "backlog": backlog,
        "model": model,
        "generated_at": generated_at,
        "version": version,
        "ctype": ctype,
        "requested_type": requested_type,
        "downgrades": downgrades,
        "licence": licence,
        "graph_nodes": graph_nodes,
        "excerpts": parse_excerpts(os.path.join(docket, "material", "EXCERPTS.md")),
        "links": parse_links(os.path.join(docket, "material", "LINKS.md")),
    }

    files: dict[str, str] = {
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
    }
    item_text = _render_item(ctx)
    web_readme = _render_web_readme(ctx)
    repro_readme = _render_repro(ctx)

    manifest = DocketManifest(
        schema_=SCHEMA,
        lane=lane_model,
        target=target,
        status=ctx["status"],
        freshness=fresh,
        claims=parsed_claims,
        material=material,
        web_sources=web,
        open_questions=ctx["open_questions"],
        rework_open=[b.text for b in backlog],
        generated_by=GeneratedBy(app=APP, version=version, model=model),
        generated_at=generated_at,
    )

    # -- writes (all gates passed) -------------------------------------------
    os.makedirs(docket, exist_ok=True)
    preserved = _preserve_item(docket)
    written: list[str] = []
    for name in sorted(files):
        _write_text(os.path.join(docket, name), files[name])
        written.append(name)
    _write_text(os.path.join(docket, "ITEM.md"), item_text)
    written.append("ITEM.md")
    os.makedirs(os.path.join(docket, "web"), exist_ok=True)
    _write_text(os.path.join(docket, "web", "README.md"), web_readme)
    os.makedirs(os.path.join(docket, "repro"), exist_ok=True)
    _write_text(os.path.join(docket, "repro", "README.md"), repro_readme)
    _write_text(os.path.join(docket, "repro", "run.sh"), _render_run_sh(ctx))
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
        preserved_item=preserved,
    )


# --------------------------------------------------------------------------- #
# history + prior ITEM preservation
# --------------------------------------------------------------------------- #


def _preserve_item(docket: str) -> str | None:
    item = os.path.join(docket, "ITEM.md")
    if not os.path.isfile(item):
        return None
    n = 1
    while os.path.exists(os.path.join(docket, f"ITEM.md.r{n}")):
        n += 1
    prior = Path(item).read_text(encoding="utf-8")
    _write_text(os.path.join(docket, f"ITEM.md.r{n}"), prior)
    return f"ITEM.md.r{n}"


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


def _render_readme(ctx: Mapping[str, Any]) -> str:
    lane = ctx["lane"]
    target = ctx["target"]
    pitch = lane.thesis.strip() or "TODO: one paragraph on what this item claims and why it matters."
    head = target.head_sha or "(unknown)"
    title = lane.title or lane.slug
    lines = [
        f"# {title} — {ctx['ctype']} docket",
        "",
        f"**Status:** {ctx['status']} · **Type:** {ctx['ctype']} · **Target:** `{target.slug}` @ `{head}`",
        f"**Freshness:** {_freshness_label(ctx['freshness'])} · **Generated:** {ctx['generated_at']} "
        f"by {APP} {ctx['version']}"
        + (f" (model: `{ctx['model']}`)" if ctx["model"] else ""),
        "",
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
                f"**Verification state.** {claim.verdict}",
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
    for item in ctx["material"]:
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
            continue
        if not item.excerpt:
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
        if not excerpt:
            lines.extend(["> **WARNING:** the span could not be read from the copied file.", ""])
            continue
        lines.extend(["```text", *excerpt, "```", ""])
    lines.extend(["## Other evidence entries", ""])
    if not ctx["evidence"]:
        lines.append("_(none supplied)_")
        lines.append("")
    for ev in ctx["evidence"]:
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
            " unverified (they were not checked against a graph)."
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
        f"# {lane.title or lane.slug} — {title}",
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


def verify_docket(docket_dir: str | os.PathLike[str]) -> DocketVerification:
    """Re-read ``MANIFEST.json`` and verify it against what is on disk."""
    docket = os.path.abspath(os.fspath(docket_dir))
    path = os.path.join(docket, "MANIFEST.json")
    if not os.path.isfile(path):
        return DocketVerification(False, [f"MANIFEST.json not found in {docket}"], 0, 0, None)
    try:
        manifest = read_manifest(path)
    except Exception as exc:  # noqa: BLE001
        return DocketVerification(False, [f"MANIFEST.json is invalid: {exc}"], 0, 0, None)
    problems = validate_manifest(manifest, docket_dir=docket)
    return DocketVerification(
        ok=not problems,
        problems=problems,
        claims=len(manifest.claims),
        material=len(manifest.material),
        manifest=manifest,
    )
