"""Staging corpus + semantic-ingest orchestration.

Two halves close the coverage gap measured in U1.4: ``graphify`` ingests 453 of
``Duval``'s 533 files (84.99%), and the invisible block is dominated by
``.jsonl`` (38) measured results and ``.xml`` (29).  A normaliser exists
(:mod:`resextract.kg.ingest`) but nothing fed its markdown to the graph.

* :func:`build_staging_corpus` — copies the repo's documentation-family files
  **byte-for-byte** and normalises uncovered-but-valuable types (``.jsonl`` via
  the existing normaliser, ``.xml`` via the bounded stdlib one added here),
  writing ``MANIFEST.json`` so every staged path maps back to its real
  repo-relative original.  Nothing is dropped silently: ignored trees,
  oversized files, binaries without a normaliser and cap overruns are all
  recorded as ``skipped`` with a reason.
* :func:`semantic_ingest` — the LLM half, **gated honestly**: one pre-flight
  HTTP probe, and if it fails the function returns ``blocked_endpoint_down``
  carrying the exact argv while executing nothing.
* :func:`merge_with_code_graph` — the merge half, which needs no LLM and can be
  proven now.

Design rules re-used rather than reinvented: the walk is
:func:`resextract.kg.ingest._walk` (which itself calls graphify's real
``ignored_predicate`` / ``_is_noise_dir`` / ``_SKIP_FILES``), classification is
``graphify.detect.classify_file``, and the document set is graphify's own
``DOC_EXTENSIONS``.  No new dependency: XML is stdlib ``xml.etree`` and never
resolves external entities or DTDs.

Never raises for a single bad file: a malformed input becomes a recorded skip
or a ``kind="xml"`` note, not a traceback that aborts the corpus.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from graphify import detect as _gdetect

from . import ingest as _ingest
from .graphify import (
    DEFAULT_BINARY,
    GRAPH_DIR_NAME,
    GRAPH_FILE_NAME,
    graph_stats,
    read_graph,
)

__all__ = [
    "StagedFile",
    "StagingCorpus",
    "SemanticResult",
    "MergedResult",
    "build_staging_corpus",
    "normalize_xml",
    "resolve_provenance",
    "staging_summary",
    "semantic_argv",
    "semantic_ingest",
    "merge_with_code_graph",
    "combined_graph_report",
    "DOC_EXTENSIONS",
    "MANIFEST_NAME",
]

# --------------------------------------------------------------------------- #
# Bounds. Everything is capped so a 3.8 MB JSONL is sampled, not slurped, and a
# pathological XML cannot blow memory or the output budget.
# --------------------------------------------------------------------------- #
MANIFEST_NAME = "MANIFEST.json"
MANIFEST_VERSION = 1

# graphify's real document family, not an invented list.
DOC_EXTENSIONS: frozenset[str] = frozenset(_gdetect.DOC_EXTENSIONS)

# Types we can turn into markdown. ``.xml`` is routed to :func:`normalize_xml`;
# the rest go through :func:`resextract.kg.ingest.normalize`.
_XML_EXTS = frozenset({".xml"})
_NORMALIZABLE_EXTS = frozenset(
    {".jsonl", ".ndjson", ".xml", ".csv", ".tsv", ".ipynb"}
)

MAX_SINGLE_FILE_BYTES = 32 * 1024 * 1024     # per-file copy/normalise cap
MAX_XML_BYTES = 4 * 1024 * 1024              # bytes of XML actually parsed
XML_MAX_ELEMENTS = 200_000                   # elements counted before we stop
XML_TABLE_ROWS = 200                         # element rows rendered
MAX_XML_OUTPUT_BYTES = 512 * 1024            # markdown cap for the XML summary

_STD_ENTITIES = frozenset({b"amp", b"lt", b"gt", b"quot", b"apos"})
_ENTITY_REF_RE = re.compile(rb"&(#\d+|#x[0-9A-Fa-f]+|[A-Za-z_][\w.:-]*);")
_SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(name: str) -> str:
    slug = _SLUG_RE.sub("-", name).strip("-.")
    return slug or "file"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: str | os.PathLike[str]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Result types
# --------------------------------------------------------------------------- #
@dataclass
class StagedFile:
    """One file the corpus decided about — staged, normalised, or skipped."""

    staged_path: str          # path relative to the corpus root ("" if skipped)
    original_path: str        # repo-relative path of the real file
    kind: str                 # doc_copy | normalized | skipped
    bytes_in: int = 0
    bytes_out: int = 0
    sampled: bool = False
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "staged_path": self.staged_path,
            "original_path": self.original_path,
            "kind": self.kind,
            "bytes_in": self.bytes_in,
            "bytes_out": self.bytes_out,
            "sampled": self.sampled,
            "note": self.note,
        }


@dataclass
class StagingCorpus:
    """The staged tree plus the provenance manifest that makes it honest."""

    out_dir: str
    staged: list[StagedFile] = field(default_factory=list)
    manifest_path: str = ""
    counts: dict[str, int] = field(default_factory=dict)
    total_bytes: int = 0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "out_dir": self.out_dir,
            "manifest_path": self.manifest_path,
            "counts": dict(self.counts),
            "total_bytes": self.total_bytes,
            "notes": list(self.notes),
            "staged": [s.as_dict() for s in self.staged],
        }


@dataclass
class SemanticResult:
    """Outcome of the LLM half — including the honest refusal to run it."""

    status: str = "failed"    # ok | blocked_endpoint_down | failed | dry_run
    command: str = ""
    http_code: int | None = None
    exit_code: int | None = None
    wall_s: float = 0.0
    nodes: int = 0
    edges: int = 0
    communities: int = 0
    semantic_nodes: int = 0
    graph_path: str = ""
    error: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "command": self.command,
            "http_code": self.http_code,
            "exit_code": self.exit_code,
            "wall_s": self.wall_s,
            "nodes": self.nodes,
            "edges": self.edges,
            "communities": self.communities,
            "semantic_nodes": self.semantic_nodes,
            "graph_path": self.graph_path,
            "error": self.error,
        }


@dataclass
class MergedResult:
    """Outcome of ``graphify merge-graphs`` (never an LLM call)."""

    ok: bool = False
    command: str = ""
    exit_code: int | None = None
    nodes: int = 0
    edges: int = 0
    communities: int = 0
    graph_path: str = ""
    code_sha256: str = ""
    semantic_sha256: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "command": self.command,
            "exit_code": self.exit_code,
            "nodes": self.nodes,
            "edges": self.edges,
            "communities": self.communities,
            "graph_path": self.graph_path,
            "code_sha256": self.code_sha256,
            "semantic_sha256": self.semantic_sha256,
        }


# --------------------------------------------------------------------------- #
# Two explicit seams (also the red→green reverts)
# --------------------------------------------------------------------------- #
def _repo_relative(path: str | os.PathLike[str], root: str | os.PathLike[str]) -> str:
    """Provenance seam: the real repo-relative path recorded in the manifest.

    Reverting this to ``Path(path).name`` (directory dropped) makes
    :func:`resolve_provenance` hand back a path that does not exist in the repo,
    which is the exact failure the round-trip guard exists to catch.
    """
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except Exception:
        return Path(path).name


def _endpoint_executable(http_code: int | None) -> bool:
    """Honesty seam: only HTTP 200 may launch the LLM pass.

    Reverting this to ``return True`` runs the pass against a dead endpoint,
    which the endpoint-down guard fails on.
    """
    return http_code == 200


# --------------------------------------------------------------------------- #
# Bounded, hardened XML normaliser (stdlib only; no entity/DTD resolution)
# --------------------------------------------------------------------------- #
def _strip_markup_declarations(raw: bytes) -> tuple[bytes, bool]:
    """Remove ``<!DOCTYPE …>`` / ``<!ENTITY …>`` declarations by scanning.

    A manual bracket-aware scan, not a backtracking regex, so a hostile
    document cannot make the sanitiser itself quadratic.  Nothing is ever
    fetched: this only *deletes* declarations, and the caller then neutralises
    any now-undefined entity reference to literal text.
    """
    removed = False
    out = raw
    while True:
        low = out.lower()
        idx = low.find(b"<!")
        if idx < 0:
            break
        i = idx
        depth = 0
        end = -1
        while i < len(out):
            ch = out[i : i + 1]
            if ch == b"[":
                depth += 1
            elif ch == b"]":
                depth = max(0, depth - 1)
            elif ch == b">" and depth == 0:
                end = i
                break
            i += 1
        if end < 0:
            out = out[:idx]
        else:
            out = out[:idx] + out[end + 1 :]
        removed = True
    return out, removed


def _neutralise_entities(raw: bytes) -> tuple[bytes, int]:
    """Rewrite non-standard entity references to literal ``&name;`` text.

    Standard XML entities and numeric character references are left alone; any
    other reference becomes ``&amp;name;`` so it renders as the literal text the
    author wrote.  This is what proves an internal-entity payload is **not**
    expanded.
    """
    count = 0

    def repl(match: "re.Match[bytes]") -> bytes:
        nonlocal count
        name = match.group(1)
        if name.startswith(b"#") or name in _STD_ENTITIES:
            return match.group(0)
        count += 1
        return b"&amp;" + name + b";"

    return _ENTITY_REF_RE.sub(repl, raw), count


def _xml_element_path(parent_path: str, tag: str, seen: dict[str, int]) -> str:
    key = parent_path + "/" + tag
    seen[key] = seen.get(key, 0) + 1
    return f"{key}[{seen[key]}]"


def normalize_xml(
    path: str | os.PathLike[str],
    out_dir: str | os.PathLike[str] | None = None,
) -> "NormalizedFile":  # noqa: F821 - returned from ingest
    """Structural summary + bounded element/attribute table for a ``.xml`` file.

    Hardened: DOCTYPE/ENTITY declarations are stripped by a bounded scanner and
    non-standard entity references are neutralised, so no internal entity is
    ever expanded and no external entity/DTD is ever resolved (stdlib
    ``xml.etree`` is never asked to).  Malformed input yields a
    ``kind="xml"`` report with a note and the raw prefix — it does not raise.
    """
    src = Path(path)
    dest_dir = Path(out_dir) if out_dir is not None else src.parent / "normalized"
    notes: list[str] = []

    size = src.stat().st_size if src.exists() else 0
    with src.open("rb") as fh:
        raw = fh.read(MAX_XML_BYTES)
    truncated = size > MAX_XML_BYTES
    if truncated:
        notes.append(f"input truncated at MAX_XML_BYTES={MAX_XML_BYTES}")

    sanitized, had_decls = _strip_markup_declarations(raw)
    sanitized, neutralised = _neutralise_entities(sanitized)
    if had_decls:
        notes.append("DOCTYPE/ENTITY declarations stripped; no DTD or external entity resolved")
    if neutralised:
        notes.append(f"{neutralised} non-standard entity reference(s) rendered literally (not expanded)")

    lines: list[str] = [f"# XML: {src.name}", f"<!-- source: {src.name} size={size} -->"]
    total_elements = 0
    max_depth = 0
    tags: dict[str, int] = {}
    attr_count = 0
    rows: list[tuple[str, str, str, str]] = []
    root_tag = ""
    parse_error = ""

    try:
        root = ET.fromstring(sanitized)
        root_tag = _local(root.tag)
        # Iterative walk so a deeply nested hostile document cannot recurse.
        stack: list[tuple[str, Any, int, dict[str, int]]] = [("", root, 0, {})]
        while stack:
            parent_path, elem, depth, seen = stack.pop()
            total_elements += 1
            if total_elements > XML_MAX_ELEMENTS:
                notes.append(f"element count capped at XML_MAX_ELEMENTS={XML_MAX_ELEMENTS}")
                break
            tag = _local(elem.tag)
            tags[tag] = tags.get(tag, 0) + 1
            this_depth = depth + 1
            max_depth = max(max_depth, this_depth)
            path_str = _xml_element_path(parent_path, tag, seen) if parent_path or depth else f"/{tag}"
            attrs = {k: v for k, v in elem.attrib.items()}
            attr_count += len(attrs)
            if len(rows) < XML_TABLE_ROWS:
                rows.append(
                    (
                        path_str,
                        tag,
                        " ".join(f'{k}="{v}"' for k, v in sorted(attrs.items())),
                        (elem.text or "").strip()[:120],
                    )
                )
            for child in reversed(list(elem)):
                stack.append((path_str, child, this_depth, seen))
    except ET.ParseError as exc:  # malformed XML: report, never crash
        parse_error = str(exc)
        notes.append(f"malformed XML: {parse_error}")
    except Exception as exc:  # pragma: no cover - defensive
        parse_error = repr(exc)
        notes.append(f"unparsable XML: {parse_error}")

    lines.append("")
    lines.append("## Structure")
    lines.append(f"- root: `{root_tag or '<none>'}`")
    lines.append(f"- elements: {total_elements}")
    lines.append(f"- distinct tags: {len(tags)}")
    lines.append(f"- max depth: {max_depth}")
    lines.append(f"- attributes: {attr_count}")
    if truncated:
        lines.append(f"- input truncated at {MAX_XML_BYTES} bytes")
    if tags:
        lines.append("")
        lines.append("### tag counts")
        for tag, count in sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))[:50]:
            lines.append(f"- `{tag}`: {count}")

    lines.append("")
    lines.append("## Elements")
    if parse_error:
        lines.append(f"<!-- parse error: {parse_error} -->")
        snippet = raw[:500].decode("utf-8", "replace").replace("\n", " ")
        lines.append(f"- raw prefix: `{snippet}`")
    elif rows:
        lines.append("| # | path | tag | attributes | text |")
        lines.append("|---|---|---|---|---|")
        for i, (p, tag, attrs, text) in enumerate(rows, 1):
            lines.append(f"| {i} | `{p}` | `{tag}` | {attrs} | {text} |")
        if total_elements > len(rows):
            lines.append("")
            lines.append(f"<!-- table truncated: {len(rows)} of {total_elements} elements -->")
    else:
        lines.append("- (no elements)")

    text = "\n".join(lines) + "\n"
    raw_out = text.encode("utf-8")
    if len(raw_out) > MAX_XML_OUTPUT_BYTES:
        raw_out = raw_out[:MAX_XML_OUTPUT_BYTES]
        notes.append(f"output truncated at MAX_XML_OUTPUT_BYTES={MAX_XML_OUTPUT_BYTES}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{_slug(src.stem)}.md"
    dest.write_bytes(raw_out)

    return _ingest.NormalizedFile(
        kind="xml",
        source=str(src),
        output=dest,
        records=total_elements,
        bytes_out=len(raw_out),
        sampled=len(rows),
        notes=notes,
    )


def _local(tag: Any) -> str:
    if not isinstance(tag, str):
        return str(tag)
    return tag.rsplit("}", 1)[-1]


# --------------------------------------------------------------------------- #
# Staging corpus
# --------------------------------------------------------------------------- #
def _normalize_one(path: Path, dest_dir: Path) -> Any:
    """Route one file to the right normaliser (XML handled here)."""
    if path.suffix.lower() in _XML_EXTS:
        return normalize_xml(path, dest_dir)
    return _ingest.normalize(path, dest_dir)


def build_staging_corpus(
    target_root: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    *,
    include_doc_exts: Iterable[str] | None = None,
    normalize_uncovered: bool = True,
    max_files: int = 500,
    max_total_bytes: int = 64 * 1024 * 1024,
    max_normalize_files: int = 200,
) -> StagingCorpus:
    """Stage a repo's non-code material into *out_dir* with a provenance manifest.

    Documentation-family files are copied byte-for-byte under ``docs/``;
    uncovered types are normalised to markdown under ``normalized/``; everything
    else is recorded as ``skipped`` with a reason.  Deterministic: the same tree
    always yields byte-identical ``MANIFEST.json``.
    """
    root = Path(target_root).resolve()
    out = Path(out_dir).resolve()
    doc_exts = (
        frozenset(e.lower() for e in include_doc_exts)
        if include_doc_exts is not None
        else DOC_EXTENSIONS
    )
    docs_dir = out / "docs"
    norm_root = out / "normalized"
    # A re-stage must not inherit stale artifacts from a previous, larger run.
    for stale in (docs_dir, norm_root):
        if stale.exists():
            shutil.rmtree(stale, ignore_errors=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    norm_root.mkdir(parents=True, exist_ok=True)

    notes: list[str] = []
    skipped_by_reason: dict[str, int] = {}
    staged: list[StagedFile] = []
    staged_artifacts = 0
    normalized_count = 0
    total_bytes = 0
    capped = {"max_files": False, "max_total_bytes": False, "max_normalize_files": False}
    stop = False

    def _skip(rel: str, reason: str, note: str = "") -> None:
        skipped_by_reason[reason] = skipped_by_reason.get(reason, 0) + 1
        staged.append(
            StagedFile(
                staged_path="",
                original_path=rel,
                kind="skipped",
                note=note or reason,
            )
        )

    for path, walk_kind in _ingest._walk(root, gitignore=True, extra_excludes=None):
        if stop:
            break
        try:
            rel = _repo_relative(path, root)
        except Exception:  # pragma: no cover - defensive
            rel = str(path)

        if walk_kind != "file":
            _skip(rel, walk_kind)
            continue

        ext = path.suffix.lower()
        is_doc = ext in doc_exts
        is_norm = normalize_uncovered and ext in _NORMALIZABLE_EXTS

        if not is_doc and not is_norm:
            try:
                classified = _gdetect.classify_file(path)
            except Exception:  # pragma: no cover - defensive
                classified = None
            reason = "covered-by-graphify" if classified is not None else "unsupported-no-normalizer"
            _skip(rel, reason)
            continue

        if staged_artifacts >= max_files:
            capped["max_files"] = True
            notes.append(f"cap hit: max_files={max_files} reached; staging stopped")
            stop = True
            _skip(rel, "over-max-files")
            continue

        try:
            size = path.stat().st_size
        except OSError:
            _skip(rel, "unreadable")
            continue

        if size > MAX_SINGLE_FILE_BYTES:
            _skip(rel, "oversized", f"oversized: {size} > MAX_SINGLE_FILE_BYTES={MAX_SINGLE_FILE_BYTES}")
            continue

        if total_bytes + size > max_total_bytes:
            capped["max_total_bytes"] = True
            notes.append(
                f"cap hit: max_total_bytes={max_total_bytes} would be exceeded; staging stopped"
            )
            _skip(rel, "over-total-bytes")
            stop = True
            continue

        if is_norm and normalized_count >= max_normalize_files:
            if not capped["max_normalize_files"]:
                capped["max_normalize_files"] = True
                notes.append(
                    f"cap hit: max_normalize_files={max_normalize_files} reached; "
                    "further normalisation skipped (docs still staged)"
                )
            _skip(rel, "over-normalize-files")
            continue

        if is_doc:
            dest = docs_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            raw = path.read_bytes()
            dest.write_bytes(raw)
            staged_artifacts += 1
            total_bytes += len(raw)
            staged.append(
                StagedFile(
                    staged_path=dest.relative_to(out).as_posix(),
                    original_path=rel,
                    kind="doc_copy",
                    bytes_in=size,
                    bytes_out=len(raw),
                    sampled=False,
                    note="",
                )
            )
            continue

        # normalize
        dest_dir = norm_root / Path(rel).parent / ext.lstrip(".")
        nf = _normalize_one(path, dest_dir)
        if getattr(nf, "output", None) is None or nf.kind == "unsupported":
            _skip(rel, "unsupported-no-normalizer", "; ".join(getattr(nf, "notes", []) or []))
            continue
        out_path = Path(nf.output)
        staged_artifacts += 1
        normalized_count += 1
        total_bytes += nf.bytes_out
        staged.append(
            StagedFile(
                staged_path=out_path.relative_to(out).as_posix(),
                original_path=rel,
                kind="normalized",
                bytes_in=size,
                bytes_out=nf.bytes_out,
                sampled=bool(nf.sampled) and nf.records > nf.sampled,
                note=f"kind={nf.kind}" + (("; " + "; ".join(nf.notes)) if nf.notes else ""),
            )
        )

    staged.sort(key=lambda s: (s.kind, s.original_path, s.staged_path))
    counts: dict[str, int] = {"doc_copy": 0, "normalized": 0, "skipped": 0}
    for s in staged:
        counts[s.kind] = counts.get(s.kind, 0) + 1
    if not capped["max_files"] and max_files and staged_artifacts >= max_files:
        capped["max_files"] = True
        notes.append(f"cap hit: max_files={max_files} reached; staging stopped")

    entries: list[dict[str, Any]] = []
    for s in staged:
        sha = ""
        if s.staged_path:
            fp = out / s.staged_path
            if fp.exists():
                sha = _sha256_file(fp)
        entry = s.as_dict()
        entry["sha256"] = sha
        entries.append(entry)

    manifest = {
        "version": MANIFEST_VERSION,
        "generated_by": "resextract.kg.staging",
        "out_dir_rel": out.name,
        "target_root": root.as_posix(),
        "counts": dict(counts),
        "total_bytes": total_bytes,
        "caps": {
            "max_files": max_files,
            "max_total_bytes": max_total_bytes,
            "max_normalize_files": max_normalize_files,
            "max_single_file_bytes": MAX_SINGLE_FILE_BYTES,
            "hit": dict(capped),
        },
        "skipped_by_reason": dict(sorted(skipped_by_reason.items())),
        "notes": list(notes),
        "files": entries,
    }
    manifest_path = out / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    corpus = StagingCorpus(
        out_dir=str(out),
        staged=staged,
        manifest_path=str(manifest_path),
        counts=counts,
        total_bytes=total_bytes,
        notes=notes,
    )
    # Extra, non-declared bookkeeping used by staging_summary (kept off the
    # declared field list so the constructor stays exactly as specified).
    corpus.caps = manifest["caps"]  # type: ignore[attr-defined]
    corpus.skipped_by_reason = dict(sorted(skipped_by_reason.items()))  # type: ignore[attr-defined]
    return corpus


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #
def _load_manifest(source: Any) -> tuple[list[dict[str, Any]], Path | None]:
    """Accept a corpus, a manifest path, or a parsed manifest dict."""
    if isinstance(source, StagingCorpus):
        mp = Path(source.manifest_path)
        out_dir = Path(source.out_dir)
    elif isinstance(source, (str, os.PathLike)):
        mp = Path(source)
        out_dir = mp.parent
    elif isinstance(source, dict):
        return list(source.get("files", [])), None
    else:
        raise TypeError(f"cannot read a staging manifest from {type(source)!r}")
    if not mp.exists():
        return [], out_dir
    data = json.loads(mp.read_text(encoding="utf-8"))
    return list(data.get("files", [])), out_dir


def resolve_provenance(staged_path: str | os.PathLike[str], corpus_or_manifest: Any) -> str | None:
    """Inverse of staging: a staged path → the real repo-relative original.

    A graph node whose ``source_file`` is a staged path MUST resolve back to a
    path that exists in the repo, or a later docket cites a file that does not
    exist.  Accepts an absolute staged path, a path relative to the corpus
    root, a suffix of either, or a bare basename when it is unambiguous.
    Returns ``None`` when nothing matches.
    """
    entries, out_dir = _load_manifest(corpus_or_manifest)
    mapped = [e for e in entries if e.get("staged_path")]
    if not mapped:
        return None
    cand = str(staged_path).replace("\\", "/").lstrip("./")
    if not cand:
        # A node with no ``source_file`` must not suffix-match every entry.
        return None

    # 1. exact relative match
    for e in mapped:
        if e["staged_path"] == cand:
            return e["original_path"]

    # 2. absolute path under the corpus root
    if out_dir is not None:
        try:
            rel = Path(staged_path).resolve().relative_to(Path(out_dir).resolve()).as_posix()
            for e in mapped:
                if e["staged_path"] == rel:
                    return e["original_path"]
        except Exception:
            pass

    # 3. suffix match on either side, but only for path-shaped candidates: a
    #    bare basename falls through to step 4, where it must be unambiguous.
    if "/" in cand:
        suffix = [
            e
            for e in mapped
            if cand.endswith(e["staged_path"]) or e["staged_path"].endswith(cand)
        ]
        if len({e["staged_path"] for e in suffix}) == 1:
            return suffix[0]["original_path"]
        if suffix:
            suffix.sort(key=lambda e: len(e["staged_path"]), reverse=True)
            return suffix[0]["original_path"]

    # 4. unambiguous basename
    base = Path(cand).name
    by_name = [e for e in mapped if Path(e["staged_path"]).name == base]
    if len(by_name) == 1:
        return by_name[0]["original_path"]
    return None


def staging_summary(corpus: StagingCorpus) -> dict[str, Any]:
    """Deterministic counts: by kind, by original extension, caps, uncovered types."""
    by_ext: dict[str, int] = {}
    for s in corpus.staged:
        if s.kind == "skipped":
            continue
        ext = Path(s.original_path).suffix.lower() or "<none>"
        by_ext[ext] = by_ext.get(ext, 0) + 1
    by_norm_kind: dict[str, int] = {}
    for s in corpus.staged:
        if s.kind != "normalized":
            continue
        k = s.note.split(";", 1)[0].replace("kind=", "") if s.note else "unknown"
        by_norm_kind[k] = by_norm_kind.get(k, 0) + 1
    skipped = dict(getattr(corpus, "skipped_by_reason", {}))
    caps = dict(getattr(corpus, "caps", {}))
    uncovered: dict[str, int] = {}
    for s in corpus.staged:
        if s.kind == "skipped" and s.note.startswith("unsupported-no-normalizer"):
            ext = Path(s.original_path).suffix.lower() or "<none>"
            uncovered[ext] = uncovered.get(ext, 0) + 1
    return {
        "out_dir": corpus.out_dir,
        "manifest_path": corpus.manifest_path,
        "counts": dict(sorted(corpus.counts.items())),
        "normalized_by_kind": dict(sorted(by_norm_kind.items())),
        "staged_by_original_extension": dict(sorted(by_ext.items())),
        "total_bytes": corpus.total_bytes,
        "caps": caps,
        "caps_hit": sorted(k for k, v in caps.get("hit", {}).items() if v),
        "skipped_by_reason": dict(sorted(skipped.items())),
        "uncovered_types": [ext for ext, _ in sorted(uncovered.items(), key=lambda kv: (-kv[1], kv[0]))],
        "notes": list(corpus.notes),
    }


# --------------------------------------------------------------------------- #
# Semantic ingest (the gated LLM half)
# --------------------------------------------------------------------------- #
def semantic_argv(
    staging_dir: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    *,
    backend: str = "openai",
    model: str = "occamy-1.0",
    token_budget: int = 1500,
    max_concurrency: int = 1,
    api_timeout: float = 300,
) -> list[str]:
    """The exact argv the semantic pass runs under.

    ``stdbuf -oL -eL`` is not decoration: graphify block-buffers stdout off-TTY,
    so without it a timeout silently discards every progress line.
    """
    return [
        "stdbuf",
        "-oL",
        "-eL",
        str(DEFAULT_BINARY),
        "extract",
        str(staging_dir),
        "--backend",
        backend,
        "--model",
        model,
        "--max-concurrency",
        str(max_concurrency),
        "--token-budget",
        str(token_budget),
        "--api-timeout",
        str(int(api_timeout)),
        "--out",
        str(out_dir),
    ]


@dataclass
class _RunOutcome:
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    wall_s: float = 0.0


def _http_probe(url: str, timeout: float = 10.0) -> int:
    """One HTTP GET → status code, or 0 for any failure. Never raises."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed local base_url
            return int(getattr(resp, "status", 0) or 0)
    except urllib.error.HTTPError as exc:
        return int(exc.code or 0)
    except Exception:
        return 0


def _run_command(argv: list[str], env: dict[str, str] | None, timeout_s: float) -> _RunOutcome:
    """Run *argv* with line-buffered output; a timeout reports exit code -1."""
    started = time.monotonic()
    try:
        proc = subprocess.run(  # noqa: S603 - argv is built above, not user input
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
        )
        return _RunOutcome(proc.returncode, proc.stdout or "", proc.stderr or "", time.monotonic() - started)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return _RunOutcome(-1, out, err, time.monotonic() - started)
    except FileNotFoundError as exc:
        return _RunOutcome(127, "", str(exc), time.monotonic() - started)


def semantic_ingest(
    corpus: StagingCorpus | str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    *,
    backend: str = "openai",
    model: str = "occamy-1.0",
    base_url: str = "http://serving-host/v1",
    token_budget: int = 1500,
    max_concurrency: int = 1,
    api_timeout: float = 300,
    timeout_s: float = 1800,
    dry_run: bool = False,
) -> SemanticResult:
    """Run graphify's LLM pass over a staged corpus — or refuse, honestly.

    Pre-flight is one HTTP call.  If it is not 200 the function returns
    ``blocked_endpoint_down`` carrying the exact argv and executes **nothing**:
    no partially-built semantic graph, no silently-empty success.  ``dry_run``
    returns the argv without even probing.
    """
    staging_dir = Path(corpus.out_dir) if isinstance(corpus, StagingCorpus) else Path(corpus)
    out = Path(out_dir)
    argv = semantic_argv(
        staging_dir,
        out,
        backend=backend,
        model=model,
        token_budget=token_budget,
        max_concurrency=max_concurrency,
        api_timeout=api_timeout,
    )
    command = shlex.join(argv)
    graph_path = out / GRAPH_DIR_NAME / GRAPH_FILE_NAME

    if dry_run:
        return SemanticResult(status="dry_run", command=command, graph_path="")

    probe_url = base_url.rstrip("/") + "/models"
    http_code = _http_probe(probe_url, timeout=min(float(api_timeout), 10.0))
    if not _endpoint_executable(http_code):
        return SemanticResult(
            status="blocked_endpoint_down",
            command=command,
            http_code=http_code,
            error=(
                f"pre-flight GET {probe_url} returned HTTP {http_code}; "
                "LLM pass not executed (no partial pass)"
            ),
            graph_path="",
        )

    env = os.environ.copy()
    env["OPENAI_BASE_URL"] = base_url
    env["OPENAI_MODEL"] = model
    env.setdefault("OPENAI_API_KEY", "not-needed")

    outcome = _run_command(argv, env, timeout_s)
    result = SemanticResult(
        command=command,
        http_code=http_code,
        exit_code=outcome.exit_code,
        wall_s=round(outcome.wall_s, 3),
    )
    if outcome.exit_code == -1:
        result.status = "failed"
        result.error = f"timed out after {timeout_s}s (graphify stdout is line-buffered via stdbuf)"
        return result
    if outcome.exit_code != 0:
        result.status = "failed"
        result.error = (outcome.stderr or outcome.stdout or "").strip()[-2000:]
        return result
    if not graph_path.exists():
        result.status = "failed"
        result.error = f"exit 0 but no graph at {graph_path}"
        return result

    stats = graph_stats(graph_path)
    semantic_nodes = 0
    for node in read_graph(graph_path).nodes:
        if node.file_type in ("document", "concept") or node.source_location in (None, ""):
            semantic_nodes += 1
    result.status = "ok"
    result.nodes = stats.nodes
    result.edges = stats.edges
    result.communities = stats.communities
    result.semantic_nodes = semantic_nodes
    result.graph_path = str(graph_path)
    return result


# --------------------------------------------------------------------------- #
# Merge (no LLM)
# --------------------------------------------------------------------------- #
def merge_with_code_graph(
    code_graph: str | os.PathLike[str],
    semantic_graph: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    *,
    dry_run: bool = False,
) -> MergedResult:
    """Union the code graph with the semantic graph via ``graphify merge-graphs``.

    ``merge-graphs --out`` is a *file* path (unlike ``extract --out``), so the
    combined graph lands exactly at ``<out_dir>/graph.json``.  Needs no LLM.
    """
    code = Path(code_graph)
    sem = Path(semantic_graph)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    merged = out / GRAPH_FILE_NAME
    argv = [
        str(DEFAULT_BINARY),
        "merge-graphs",
        str(code),
        str(sem),
        "--out",
        str(merged),
    ]
    command = shlex.join(argv)
    code_sha = _sha256_file(code) if code.exists() else ""
    sem_sha = _sha256_file(sem) if sem.exists() else ""

    if dry_run:
        return MergedResult(
            ok=False,
            command=command,
            exit_code=None,
            graph_path=str(merged),
            code_sha256=code_sha,
            semantic_sha256=sem_sha,
        )

    outcome = _run_command(argv, None, 300.0)
    result = MergedResult(
        ok=outcome.exit_code == 0 and merged.exists(),
        command=command,
        exit_code=outcome.exit_code,
        graph_path=str(merged) if merged.exists() else "",
        code_sha256=code_sha,
        semantic_sha256=sem_sha,
    )
    if result.ok:
        stats = graph_stats(merged)
        result.nodes = stats.nodes
        result.edges = stats.edges
        result.communities = stats.communities
    else:
        result.error = (outcome.stderr or outcome.stdout or "").strip()[-2000:]  # type: ignore[attr-defined]
    return result


# --------------------------------------------------------------------------- #
# Combined-graph reporting
# --------------------------------------------------------------------------- #
def _discover_manifests(root: Path | None = None) -> list[Path]:
    base = root or Path.cwd() / "state" / "staging"
    if not base.is_dir():
        return []
    return sorted(p for p in base.glob(f"*/{MANIFEST_NAME}") if p.is_file())


def combined_graph_report(
    path: str | os.PathLike[str],
    *,
    manifests: Iterable[str | os.PathLike[str]] | None = None,
) -> dict[str, Any]:
    """Counts, top directories, and how many nodes resolve via a staging manifest."""
    graph_path = Path(path)
    stats = graph_stats(graph_path)
    graph = read_graph(graph_path)

    resolved = 0
    staged_like = 0
    resolved_exts: dict[str, int] = {}
    manifest_paths: list[str] = []
    if manifests is None:
        manifest_paths = [str(p) for p in _discover_manifests()]
    else:
        manifest_paths = [str(p) for p in manifests]
    loaders = [p for p in manifest_paths if Path(p).exists()]

    for node in graph.nodes:
        src = node.source_file or ""
        hit = None
        for manifest in loaders:
            hit = resolve_provenance(src, manifest)
            if hit:
                break
        if hit:
            resolved += 1
            ext = Path(hit).suffix.lower() or "<none>"
            resolved_exts[ext] = resolved_exts.get(ext, 0) + 1
        elif src and any(part in src for part in ("staging/", "/docs/", "normalized/")):
            staged_like += 1

    return {
        "path": str(graph_path),
        "nodes": stats.nodes,
        "edges": stats.edges,
        "communities": stats.communities,
        "top_dirs": dict(stats.top_dirs),
        "node_kinds": dict(stats.node_kinds),
        "manifest_paths": manifest_paths,
        "staging_resolved_nodes": resolved,
        "staging_resolved_original_exts": dict(sorted(resolved_exts.items())),
        "staging_like_nodes": staged_like,
    }
