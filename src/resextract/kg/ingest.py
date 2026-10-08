"""Ingestion coverage audit + bounded normalisers for uncovered research data.

The knowledge graph can only see what graphify's classifier admits. A file type
that is *silently* dropped is material that can never become a finding, and
nothing else in the pipeline would ever say it was missing. This module closes
that blind spot in two steps:

* :func:`coverage_audit` — walk a repo exactly as ``graphify.detect`` would, and
  report precisely which files it ingests, which it silently skips, and the
  biggest gaps. Read-only; never raises.
* :func:`normalize_notebook` / :func:`normalize_jsonl` / :func:`normalize_csv`
  (dispatched by :func:`normalize`) — deterministic, bounded, stdlib-only
  conversions of those skipped types into markdown, so the docs pass can ingest
  them. Notebook outputs (streams, execute results, tracebacks, base64 images)
  are preserved; images are written as real files beside the markdown.

Ignore semantics are **not** reimplemented: the walk calls graphify's own
``graphify.detect.ignored_predicate`` (which loads ``.graphifyignore``,
``.gitignore`` chains, ``$GIT_DIR/info/exclude`` and honours git's
tracked-file exemption), ``graphify.detect._is_noise_dir`` and
``graphify.detect._SKIP_FILES``, and classifies with ``graphify.detect.classify_file``
and its real extension sets. Nothing here executes repository code.

Layout: ``state/ingest/<slug>/`` by default.
"""

from __future__ import annotations

import base64
import csv
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from graphify import detect as _gdetect

__all__ = [
    "CoverageReport",
    "NormalizedFile",
    "coverage_audit",
    "ingest_uncovered",
    "normalize",
    "normalize_csv",
    "normalize_jsonl",
    "normalize_notebook",
]

# --------------------------------------------------------------------------- #
# Bounds. Every normaliser is capped so a 500 MB JSONL / a 400 MB notebook
# cannot be slurped into memory. The caps in force are recorded in the output.
# --------------------------------------------------------------------------- #
MAX_OUTPUT_BYTES = 4 * 1024 * 1024      # markdown cap per source file
MAX_IMAGE_BYTES = 2 * 1024 * 1024       # per embedded notebook image
JSONL_SAMPLE_SIZE = 200                 # records parsed to infer the schema
JSONL_TABLE_ROWS = 50                   # rows rendered in the markdown table
JSONL_MAX_SCAN_RECORDS = 100_000        # records scanned before we stop counting
CSV_TABLE_ROWS = 50
CSV_MAX_SCAN_ROWS = 100_000
CSV_SNIFF_BYTES = 8192                  # dialect sniffing sample window
HUGEFILE_BYTES = 50 * 1024 * 1024       # "surprising, may blow the budget"
_LFS_MAGIC = b"version https://git-lfs.github.com/spec"

_NOTEBOOK_EXTS = {".ipynb"}
_JSONL_EXTS = {".jsonl", ".ndjson"}
_CSV_EXTS = {".csv", ".tsv"}

_MIME_SUFFIX = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
}

_SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


# --------------------------------------------------------------------------- #
# Report types
# --------------------------------------------------------------------------- #
@dataclass
class CoverageReport:
    """What a repo's files actually become, and what they never can."""

    target_root: str = ""
    supported: dict[str, int] = field(default_factory=dict)
    unsupported: dict[str, int] = field(default_factory=dict)
    no_extension: dict[str, int] = field(default_factory=dict)
    unreadable: list[str] = field(default_factory=list)
    symlinks_skipped: int = 0
    total_files: int = 0
    supported_files: int = 0
    unsupported_files: int = 0
    coverage_pct: float = 0.0
    top_gaps: list[tuple[str, int]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_root": self.target_root,
            "supported": dict(self.supported),
            "unsupported": dict(self.unsupported),
            "no_extension": dict(self.no_extension),
            "unreadable": list(self.unreadable),
            "symlinks_skipped": self.symlinks_skipped,
            "total_files": self.total_files,
            "supported_files": self.supported_files,
            "unsupported_files": self.unsupported_files,
            "coverage_pct": self.coverage_pct,
            "top_gaps": [list(g) for g in self.top_gaps],
            "notes": list(self.notes),
        }


@dataclass
class NormalizedFile:
    """The typed outcome of normalising one source file."""

    kind: str                 # notebook | jsonl | csv | unsupported | *-error
    source: str
    output: Path | None
    records: int = 0          # total records/cells/rows, bounded by the scan cap
    bytes_out: int = 0
    sampled: int = 0          # records actually parsed/rendered
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "output": str(self.output) if self.output else None,
            "records": self.records,
            "bytes_out": self.bytes_out,
            "sampled": self.sampled,
            "notes": list(self.notes),
        }


# --------------------------------------------------------------------------- #
# Walk — faithful to graphify.detect's ignore decisions
# --------------------------------------------------------------------------- #
def _walk(root: Path, *, gitignore: bool, extra_excludes: list[str] | None):
    """Yield ``(path, kind)`` for files graphify would consider, plus bookkeeping.

    ``kind`` is ``"file"`` for a candidate regular file, ``"symlink"`` for a
    symlink we deliberately did not follow, and ``"unreadable"`` for a
    non-regular path (FIFO, socket, device). Mirrors ``detect()``'s os.walk:
    ``followlinks=False``, in-place noise-dir pruning, and the shared
    ``ignored_predicate`` for both directory pruning and per-file decisions.
    """
    predicate = _gdetect.ignored_predicate(root, extra_excludes=extra_excludes, gitignore=gitignore)
    skip_files = getattr(_gdetect, "_SKIP_FILES", frozenset())
    is_noise_dir = getattr(_gdetect, "_is_noise_dir", lambda part, parent=None: False)
    is_regular = getattr(_gdetect, "_is_regular_file", lambda p: True)
    is_sensitive = getattr(_gdetect, "_is_sensitive", lambda p: False)
    root_str = str(root)

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dp = Path(dirpath)
        kept: list[str] = []
        for name in sorted(dirnames):
            child = dp / name
            if child.is_symlink():
                yield child, "symlink"          # never descended (followlinks=False)
                continue
            try:
                if is_noise_dir(name, dp):
                    yield child, "noise_dir"
                    continue
                if predicate(child):
                    yield child, "ignored_dir"
                    continue
            except Exception:                    # pragma: no cover - defensive
                continue
            kept.append(name)
        dirnames[:] = kept

        for name in sorted(filenames):
            path = dp / name
            if name in skip_files:
                yield path, "skip_file"
                continue
            try:
                if path.is_symlink():
                    try:
                        resolved = Path(os.path.realpath(path))
                    except OSError:
                        yield path, "symlink"
                        continue
                    if resolved != root and not str(resolved).startswith(root_str + os.sep):
                        yield path, "symlink"    # outside the scan root: never indexed
                        continue
                if predicate(path):
                    yield path, "ignored_file"
                    continue
                if not is_regular(path):
                    yield path, "unreadable"
                    continue
                if is_sensitive(path):
                    yield path, "sensitive"
                    continue
            except Exception:                    # pragma: no cover - defensive
                yield path, "unreadable"
                continue
            yield path, "file"


def _record_unsupported(unsupported: dict[str, int], no_extension: dict[str, int], rel: str) -> None:
    """Count a file graphify cannot classify.

    This is the seam the coverage guard tests revert: a build that drops
    unclassified files here leaves no trace that the material ever existed,
    which is exactly the failure this module exists to prevent.
    """
    ext = Path(rel).suffix.lower()
    if ext:
        unsupported[ext] = unsupported.get(ext, 0) + 1
    else:
        no_extension[Path(rel).name] = no_extension.get(Path(rel).name, 0) + 1


def coverage_audit(
    target_root: str | os.PathLike[str],
    *,
    ignore: Iterable[str] | bool | None = None,
    cap_files: int = 200_000,
) -> CoverageReport:
    """Audit which files in *target_root* graphify actually ingests.

    ``ignore=None`` (default) honours ``.gitignore`` + ``.git/info/exclude``.
    A list of gitignore-style patterns is passed through as extra excludes;
    ``ignore=False`` disables the gitignore machinery entirely (graphify's
    ``--no-gitignore``). Never raises: unreadable paths are recorded.
    """
    report = CoverageReport()
    try:
        root = Path(target_root).resolve()
    except Exception as exc:                      # pragma: no cover - defensive
        report.notes.append(f"target root could not be resolved: {exc!r}")
        return report
    report.target_root = str(root)

    if ignore is False:
        gitignore, extra = False, None
        report.notes.append("ignore=False: .gitignore / .git/info/exclude NOT honoured (graphify --no-gitignore)")
    else:
        gitignore = True
        extra = [str(p) for p in ignore] if ignore else None
        report.notes.append(
            "ignore decisions reused from graphify.detect.ignored_predicate "
            "(.graphifyignore + .gitignore chains + $GIT_DIR/info/exclude + git tracked-file exemption)"
        )

    if not root.is_dir():
        report.notes.append(f"not a directory: {root}")
        return report

    supported: dict[str, int] = {}
    unsupported: dict[str, int] = {}
    no_extension: dict[str, int] = {}
    unreadable: list[str] = []
    symlinks = 0
    sensitive: list[str] = []
    ignored_dirs: list[str] = []
    noise_dirs: list[str] = []
    ignored_files = 0
    huge: list[tuple[str, int]] = []
    lfs: list[str] = []
    seen = 0
    capped = False

    for path, kind in _walk(root, gitignore=gitignore, extra_excludes=extra):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = str(path)

        if kind == "symlink":
            symlinks += 1
            continue
        if kind in ("noise_dir", "ignored_dir"):
            (noise_dirs if kind == "noise_dir" else ignored_dirs).append(rel + "/")
            continue
        if kind == "ignored_file":
            ignored_files += 1
            continue
        if kind == "skip_file":
            continue
        if kind == "sensitive":
            sensitive.append(rel)
            continue
        if kind == "unreadable":
            unreadable.append(rel)
            continue

        seen += 1
        if seen > cap_files:
            capped = True
            break

        # Surprises worth surfacing before we classify.
        try:
            size = path.stat().st_size
        except OSError:
            size = -1
        if size > HUGEFILE_BYTES:
            huge.append((rel, size))
        elif 0 <= size < 1024:
            try:
                with path.open("rb") as fh:
                    if fh.read(len(_LFS_MAGIC)) == _LFS_MAGIC:
                        lfs.append(rel)
            except OSError:
                pass

        try:
            ftype = _gdetect.classify_file(path)
        except Exception:
            ftype = None

        if ftype is None:
            _record_unsupported(unsupported, no_extension, rel)
            continue
        ext = path.suffix.lower()
        if not ext:
            # Extensionless but admitted (e.g. a shebang script graphify reads).
            key = f"<shebang> {path.name}"
        elif path.name.lower().endswith(".blade.php"):
            key = ".blade.php"
        else:
            key = ext
        supported[key] = supported.get(key, 0) + 1

    unsupported_files = sum(unsupported.values()) + sum(no_extension.values())
    supported_files = sum(supported.values())
    report.supported = dict(sorted(supported.items()))
    report.unsupported = dict(sorted(unsupported.items()))
    report.no_extension = dict(sorted(no_extension.items()))
    report.unreadable = sorted(unreadable)
    report.symlinks_skipped = symlinks
    report.total_files = supported_files + unsupported_files + len(unreadable)
    report.supported_files = supported_files
    report.unsupported_files = unsupported_files
    report.coverage_pct = round(100.0 * supported_files / report.total_files, 2) if report.total_files else 0.0
    report.top_gaps = sorted(unsupported.items(), key=lambda kv: (-kv[1], kv[0]))

    notes = report.notes
    if capped:
        notes.append(f"file cap reached: audit stopped after cap_files={cap_files}; counts are a lower bound")
    if noise_dirs:
        notes.append(
            f"{len(noise_dirs)} cache/vendor dirs pruned by graphify's noise rules, e.g. "
            + ", ".join(sorted(noise_dirs)[:5]) + " (never walked)"
        )
    if ignored_dirs:
        notes.append(
            f"{len(ignored_dirs)} dirs excluded by .gitignore/info-exclude, e.g. "
            + ", ".join(sorted(ignored_dirs)[:5])
        )
    if ignored_files:
        notes.append(f"{ignored_files} individual files excluded by .gitignore/info-exclude")
    if sensitive:
        notes.append(f"{len(sensitive)} files deliberately dropped as secret-shaped (graphify policy, not a gap)")
    if huge:
        biggest = sorted(huge, key=lambda kv: (-kv[1], kv[0]))[:5]
        notes.append(
            "very large files (>50 MiB): " + ", ".join(f"{p} ({s / 1048576:.1f} MiB)" for p, s in biggest)
        )
    if lfs:
        notes.append(f"{len(lfs)} git-lfs pointer file(s) (content not local), e.g. " + ", ".join(sorted(lfs)[:5]))
    if unreadable:
        notes.append(f"{len(unreadable)} unreadable/non-regular paths recorded (not fatal)")
    if symlinks:
        notes.append(f"{symlinks} symlinks skipped (outside scan root or dangling; graphify follows none by default)")
    return report


# --------------------------------------------------------------------------- #
# Bounds / helpers
# --------------------------------------------------------------------------- #
def _slug(name: str) -> str:
    cleaned = _SLUG_RE.sub("_", name).strip("._-")
    return cleaned or "ingest"


def _default_dir(source: Path) -> Path:
    return Path("state") / "ingest" / _slug(source.stem)


def _caps_line(**caps: Any) -> str:
    body = ", ".join(f"{k}={v}" for k, v in caps.items())
    return f"<!-- bounds: {body} -->"


def _write(out_dir: Path, source: Path, text: str, notes: list[str]) -> tuple[Path, int]:
    """Write *text* under *out_dir*, capped, and return (path, bytes_out)."""
    raw = text.encode("utf-8")
    capped = False
    if len(raw) > MAX_OUTPUT_BYTES:
        raw = raw[:MAX_OUTPUT_BYTES]
        # Do not end mid-codepoint.
        while raw and (raw[-1] & 0xC0) == 0x80:
            raw = raw[:-1]
        if raw and raw[-1] >= 0xC0:
            raw = raw[:-1]
        capped = True
    if capped:
        notes.append(f"output truncated at MAX_OUTPUT_BYTES={MAX_OUTPUT_BYTES}")
        raw += f"\n\n<!-- TRUNCATED at {MAX_OUTPUT_BYTES} bytes -->\n".encode("utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{_slug(source.stem)}.md"
    dest.write_bytes(raw)
    return dest, len(raw)


def _as_text(value: Any) -> str:
    if isinstance(value, list):
        return "".join(str(v) for v in value)
    return "" if value is None else str(value)


# --------------------------------------------------------------------------- #
# Notebook
# --------------------------------------------------------------------------- #
def _notebook_language(nb: dict) -> str:
    meta = nb.get("metadata") or {}
    for key in ("language_info", "kernelspec", "language"):
        block = meta.get(key)
        if isinstance(block, dict):
            for field_name in ("name", "language"):
                val = block.get(field_name)
                if isinstance(val, str) and val.strip():
                    return val.strip().lower()
        elif isinstance(block, str) and block.strip():
            return block.strip().lower()
    return "python"


def _render_outputs(cell: dict, out_dir: Path, index: list[int], notes: list[str], lang: str) -> list[str]:
    """Render one code cell's outputs: streams, execute results, errors, images."""
    lines: list[str] = []
    for out in cell.get("outputs") or []:
        if not isinstance(out, dict):
            continue
        otype = out.get("output_type")
        if otype == "stream":
            text = _as_text(out.get("text"))
            if text.strip():
                lines.append(f"**stdout/stderr** ({out.get('name', 'stream')}):")
                lines.append("")
                lines.extend("> " + ln for ln in text.rstrip("\n").split("\n"))
                lines.append("")
        elif otype in ("execute_result", "display_data"):
            data = out.get("data") or {}
            text = data.get("text/plain")
            if text:
                lines.append("**result**:" if otype == "execute_result" else "**display** (text/plain):")
                lines.append("")
                lines.extend("> " + ln for ln in _as_text(text).rstrip("\n").split("\n"))
                lines.append("")
            lines.extend(_render_images(data, out_dir, index, notes))
        elif otype == "error":
            ename = out.get("ename") or "Error"
            evalue = out.get("evalue") or ""
            lines.append(f"**error** ({ename}): {evalue}")
            lines.append("")
            tb = out.get("traceback") or []
            if isinstance(tb, str):
                tb = [tb]
            cleaned = [re.sub(r"\x1b\[[0-9;]*m", "", _as_text(t)) for t in tb]
            if cleaned:
                lines.append("```text")
                lines.extend(cleaned)
                lines.append("```")
                lines.append("")
    return lines


def _render_images(data: dict, out_dir: Path, index: list[int], notes: list[str]) -> list[str]:
    """Save embedded images beside the markdown; reference them relatively."""
    lines: list[str] = []
    for mime in sorted(data):
        if not isinstance(mime, str) or not mime.startswith("image/"):
            continue
        payload = data[mime]
        index[0] += 1
        name = f"fig-{index[0]:03d}{_MIME_SUFFIX.get(mime, '.bin')}"
        try:
            if mime == "image/svg+xml":
                blob = _as_text(payload).encode("utf-8")
            else:
                b64 = _as_text(payload)
                blob = base64.b64decode(b64, validate=False)
        except Exception as exc:
            notes.append(f"image {name} could not be decoded ({mime}): {exc!r}")
            continue
        if len(blob) > MAX_IMAGE_BYTES:
            notes.append(f"image {name} truncated at MAX_IMAGE_BYTES={MAX_IMAGE_BYTES} ({len(blob)} bytes)")
            blob = blob[:MAX_IMAGE_BYTES]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / name).write_bytes(blob)
        lines.append(f"![cell output figure {index[0]}]({name})")
        lines.append("")
    return lines


def _render_code_cell(cell: dict, lang: str, out_dir: Path, index: list[int], notes: list[str]) -> list[str]:
    """Emit one code cell: the fenced input followed by its preserved outputs.

    This is the seam the notebook-preservation guard reverts: returning ``[]``
    for every code cell yields a "markdown-only" notebook render in which the
    code, its outputs and its figures are all gone — and nothing says so.
    """
    source = _as_text(cell.get("source")).rstrip("\n")
    lines: list[str] = []
    if source:
        lines.append(f"```{lang}")
        lines.extend(source.split("\n"))
        lines.append("```")
        lines.append("")
    return lines + _render_outputs(cell, out_dir, index, notes, lang)


def normalize_notebook(path: str | os.PathLike[str], out_dir: str | os.PathLike[str] | None = None) -> NormalizedFile:
    """Normalise an ``.ipynb`` to markdown, preserving code inputs and outputs.

    A malformed / non-JSON notebook returns a typed ``ipynb-error`` result that
    records the parse error: it must not crash and must not be silently skipped.
    """
    src = Path(path)
    dest_dir = Path(out_dir) if out_dir is not None else _default_dir(src)
    notes: list[str] = []
    try:
        with src.open("r", encoding="utf-8", errors="replace") as fh:
            nb = json.load(fh)
    except Exception as exc:
        notes.append(f"notebook parse error: {type(exc).__name__}: {exc}")
        return NormalizedFile(kind="ipynb-error", source=str(src), output=None, notes=notes)
    if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
        notes.append("notebook parse error: no 'cells' list in the JSON document")
        return NormalizedFile(kind="ipynb-error", source=str(src), output=None, notes=notes)

    cells = nb["cells"]
    lang = _notebook_language(nb)
    markdown_cells = sum(1 for c in cells if isinstance(c, dict) and c.get("cell_type") == "markdown")
    code_cells = sum(1 for c in cells if isinstance(c, dict) and c.get("cell_type") == "code")
    raw_cells = sum(1 for c in cells if isinstance(c, dict) and c.get("cell_type") == "raw")
    outputs = sum(len(c.get("outputs") or []) for c in cells if isinstance(c, dict))

    parts: list[str] = [
        f"<!-- normalized from {src.name} (notebook) -->",
        "",
        f"# {src.name}",
        "",
        f"cells: {len(cells)} (markdown {markdown_cells}, code {code_cells}, raw {raw_cells}) · "
        f"code inputs: {code_cells} · outputs: {outputs} · language: {lang} · "
        f"nbformat: {nb.get('nbformat', '?')}.{nb.get('nbformat_minor', '?')}",
        "",
        _caps_line(
            max_output_bytes=MAX_OUTPUT_BYTES,
            max_image_bytes=MAX_IMAGE_BYTES,
        ),
        "",
    ]
    index = [0]
    for n, cell in enumerate(cells, 1):
        if not isinstance(cell, dict):
            continue
        ctype = cell.get("cell_type")
        if ctype == "markdown":
            body = _as_text(cell.get("source")).strip()
            if body:
                parts.extend([body, ""])
        elif ctype == "code":
            try:
                parts.extend(_render_code_cell(cell, lang, dest_dir, index, notes))
            except Exception as exc:              # pragma: no cover - defensive
                notes.append(f"cell {n} render error: {exc!r}")
        elif ctype == "raw":
            body = _as_text(cell.get("source")).strip()
            if body:
                parts.extend(["```text", body, "```", ""])
    if index[0]:
        notes.append(f"{index[0]} embedded image(s) written beside the markdown")
    dest, size = _write(dest_dir, src, "\n".join(parts).rstrip("\n") + "\n", notes)
    return NormalizedFile(
        kind="notebook", source=str(src), output=dest, records=len(cells), bytes_out=size,
        sampled=len(cells), notes=notes,
    )


# --------------------------------------------------------------------------- #
# JSONL
# --------------------------------------------------------------------------- #
def _scalar_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def normalize_jsonl(
    path: str | os.PathLike[str],
    out_dir: str | os.PathLike[str] | None = None,
    *,
    sample_size: int | None = None,
    table_rows: int | None = None,
    max_scan: int | None = None,
) -> NormalizedFile:
    """Normalise a ``.jsonl`` to a markdown table, streaming and bounded.

    Records are read one line at a time: at most *max_scan* records are even
    counted, at most *sample_size* are parsed to infer the schema, and at most
    *table_rows* are rendered. Unflattened nested fields are named, never
    dropped silently.
    """
    sample_size = JSONL_SAMPLE_SIZE if sample_size is None else sample_size
    table_rows = JSONL_TABLE_ROWS if table_rows is None else table_rows
    max_scan = JSONL_MAX_SCAN_RECORDS if max_scan is None else max_scan
    src = Path(path)
    dest_dir = Path(out_dir) if out_dir is not None else _default_dir(src)
    notes: list[str] = []

    total = 0
    sampled = 0
    bytes_read = 0
    keys: list[str] = []
    key_types: dict[str, set[str]] = {}
    rows: list[dict[str, Any]] = []
    nested: set[str] = set()
    bad_lines = 0
    capped = False

    try:
        with src.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                bytes_read += len(line.encode("utf-8", "replace"))
                stripped = line.strip()
                if not stripped:
                    continue
                if total >= max_scan:
                    capped = True
                    break
                total += 1
                if sampled >= sample_size and len(rows) >= table_rows:
                    continue                       # keep counting, stop parsing
                try:
                    rec = json.loads(stripped)
                except Exception:
                    bad_lines += 1
                    continue
                if not isinstance(rec, dict):
                    rec = {"_value": rec}
                sampled += 1
                for key, value in rec.items():
                    if key not in key_types:
                        keys.append(key)
                        key_types[key] = set()
                    key_types[key].add(_scalar_type(value))
                    if isinstance(value, (dict, list)):
                        nested.add(key)
                if len(rows) < table_rows:
                    rows.append(rec)
    except OSError as exc:
        notes.append(f"could not read jsonl: {exc}")
        return NormalizedFile(kind="jsonl-error", source=str(src), output=None, notes=notes)

    scalar_keys = [k for k in keys if k not in nested]
    parts: list[str] = [
        f"<!-- normalized from {src.name} (jsonl) -->",
        "",
        f"# {src.name}",
        "",
        f"records: {total}{'+' if capped else ''} · sampled for schema: {sampled} · "
        f"delimiter: newline-delimited JSON (one object per line) · "
        f"schema fields: {len(keys)} ({len(scalar_keys)} scalar, {len(nested)} nested)",
        "",
        _caps_line(
            max_scan_records=max_scan,
            sample_size=sample_size,
            table_rows=table_rows,
            max_output_bytes=MAX_OUTPUT_BYTES,
        ),
        "",
    ]
    if capped:
        notes.append(f"scan stopped at max_scan={max_scan} records; total is a lower bound")
    if bad_lines:
        notes.append(f"{bad_lines} line(s) were not valid JSON and were skipped")
    if bytes_read and src.exists():
        try:
            notes.append(f"read {bytes_read} of {src.stat().st_size} bytes (streamed, never slurped)")
        except OSError:
            pass

    if scalar_keys:
        parts.append("| " + " | ".join(f"`{k}`" for k in scalar_keys) + " |")
        parts.append("| " + " | ".join("---" for _ in scalar_keys) + " |")
        for rec in rows:
            parts.append("| " + " | ".join(_cell(rec.get(k)) for k in scalar_keys) + " |")
        parts.append("")
    elif keys:
        parts.extend(["_(no scalar fields; every field is nested)_", ""])

    if nested:
        ordered = sorted(nested)
        parts.append(
            f"**Nested fields not flattened ({len(ordered)}):** "
            + ", ".join(f"`{k}`" for k in ordered)
        )
        parts.append("")
        notes.append("nested fields not flattened: " + ", ".join(ordered))
    if len(rows) < total:
        parts.append(
            f"_Table shows {len(rows)} of {total}{'+' if capped else ''} records; "
            f"{sampled} parsed for the schema._"
        )
        parts.append("")

    dest, size = _write(dest_dir, src, "\n".join(parts).rstrip("\n") + "\n", notes)
    return NormalizedFile(
        kind="jsonl", source=str(src), output=dest, records=total,
        bytes_out=size, sampled=sampled, notes=notes,
    )


# --------------------------------------------------------------------------- #
# CSV / TSV
# --------------------------------------------------------------------------- #
def _sniff_delimiter(sample: str, suffix: str) -> tuple[str, str]:
    """Return (delimiter, how-it-was-decided)."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        return dialect.delimiter, "sniffed"
    except Exception:
        pass
    if suffix == ".tsv":
        return "\t", "from extension .tsv"
    return ",", "default (sniffing failed)"


def normalize_csv(
    path: str | os.PathLike[str],
    out_dir: str | os.PathLike[str] | None = None,
    *,
    table_rows: int | None = None,
    max_scan: int | None = None,
) -> NormalizedFile:
    """Normalise ``.csv``/``.tsv`` to a markdown table, streaming and bounded."""
    table_rows = CSV_TABLE_ROWS if table_rows is None else table_rows
    max_scan = CSV_MAX_SCAN_ROWS if max_scan is None else max_scan
    src = Path(path)
    suffix = src.suffix.lower()
    dest_dir = Path(out_dir) if out_dir is not None else _default_dir(src)
    notes: list[str] = []

    try:
        with src.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            sample = fh.read(CSV_SNIFF_BYTES)
            fh.seek(0)
            delimiter, how = _sniff_delimiter(sample, suffix)
            reader = csv.reader(fh, delimiter=delimiter)
            header: list[str] = []
            rows: list[list[str]] = []
            total = 0
            bytes_read = 0
            capped = False
            try:
                header = next(reader)
            except StopIteration:
                header = []
            for row in reader:
                if total >= max_scan:
                    capped = True
                    break
                total += 1
                bytes_read += sum(len(c) for c in row) + len(row)
                if len(rows) < table_rows:
                    rows.append(row)
            try:
                size_bytes = src.stat().st_size
            except OSError:
                size_bytes = 0
    except OSError as exc:
        notes.append(f"could not read csv: {exc}")
        return NormalizedFile(kind="csv-error", source=str(src), output=None, notes=notes)

    delim_repr = json.dumps(delimiter)  # quote the delimiter, unambiguously
    ncols = len(header)
    ragged = sorted({len(r) for r in rows if len(r) != ncols})
    notes.append(f"delimiter {delim_repr} ({how}); header from row 1; {ncols} columns")
    if ragged:
        notes.append(f"ragged rows with widths {ragged} (vs header width {ncols})")
    if capped:
        notes.append(f"scan stopped at max_scan={max_scan} rows; total is a lower bound")

    parts: list[str] = [
        f"<!-- normalized from {src.name} (csv/tsv) -->",
        "",
        f"# {src.name}",
        "",
        f"rows: {total}{'+' if capped else ''} · delimiter: {delim_repr} ({how}) · "
        f"columns: {ncols} · header: {json.dumps(header, ensure_ascii=False)}",
        "",
        _caps_line(
            max_scan_rows=max_scan,
            table_rows=table_rows,
            sniff_bytes=CSV_SNIFF_BYTES,
            max_output_bytes=MAX_OUTPUT_BYTES,
        ),
        "",
    ]
    if header:
        parts.append("| " + " | ".join(_cell(c) for c in header) + " |")
        parts.append("| " + " | ".join("---" for _ in header) + " |")
        for row in rows:
            cells = [_cell(c) for c in row][:ncols]
            cells += [""] * (ncols - len(cells))
            parts.append("| " + " | ".join(cells) + " |")
        parts.append("")
    else:
        parts.extend(["_(empty file: no header row)_", ""])
    if len(rows) < total:
        parts.append(f"_Table shows {len(rows)} of {total}{'+' if capped else ''} data rows._")
        parts.append("")
    notes.append(f"read sample of {min(bytes_read, size_bytes)} byte(s) of ~{size_bytes} (streamed, bounded)")

    dest, size = _write(dest_dir, src, "\n".join(parts).rstrip("\n") + "\n", notes)
    return NormalizedFile(
        kind="csv" if suffix != ".tsv" else "tsv", source=str(src), output=dest,
        records=total, bytes_out=size, sampled=len(rows), notes=notes,
    )


# --------------------------------------------------------------------------- #
# Dispatch + gap-closing driver
# --------------------------------------------------------------------------- #
def normalize(path: str | os.PathLike[str], out_dir: str | os.PathLike[str] | None = None) -> NormalizedFile:
    """Route *path* to the right normaliser by extension."""
    src = Path(path)
    ext = src.suffix.lower()
    if ext in _NOTEBOOK_EXTS:
        return normalize_notebook(src, out_dir)
    if ext in _JSONL_EXTS:
        return normalize_jsonl(src, out_dir)
    if ext in _CSV_EXTS:
        return normalize_csv(src, out_dir)
    dest_dir = Path(out_dir) if out_dir is not None else _default_dir(src)
    return NormalizedFile(
        kind="unsupported", source=str(src), output=None, notes=[
            f"no normaliser for {ext or '<no extension>'}; "
            "the docs pass cannot ingest this file as-is"
        ],
    )


def ingest_uncovered(
    report: CoverageReport,
    target_root: str | os.PathLike[str],
    out_dir: str | os.PathLike[str] | None = None,
    *,
    max_files: int = 200,
    ignore: Iterable[str] | bool | None = None,
) -> list[NormalizedFile]:
    """Normalise the highest-value uncovered types *report* found.

    Walks the same tree with the same ignore rules, taking files whose extension
    is one of the top gaps, highest-count extension first, and normalising each
    through :func:`normalize`. Bounded by *max_files*.
    """
    root = Path(target_root).resolve()
    dest_dir = Path(out_dir) if out_dir is not None else Path("state") / "ingest" / _slug(root.name)
    gap_order = [ext for ext, _count in report.top_gaps if _has_normaliser(ext)]
    if not gap_order:
        return []

    if ignore is False:
        gitignore, extra = False, None
    else:
        gitignore = True
        extra = [str(p) for p in ignore] if ignore else None

    wanted = set(gap_order)
    results: list[NormalizedFile] = []
    for path, kind in _walk(root, gitignore=gitignore, extra_excludes=extra):
        if kind != "file" or len(results) >= max_files:
            continue
        if path.suffix.lower() not in wanted:
            continue
        results.append(normalize(path, dest_dir))
    results.sort(key=lambda r: (gap_order.index(Path(r.source).suffix.lower()), r.source))
    return results


def _has_normaliser(ext: str) -> bool:
    return ext in _NOTEBOOK_EXTS or ext in _JSONL_EXTS or ext in _CSV_EXTS
