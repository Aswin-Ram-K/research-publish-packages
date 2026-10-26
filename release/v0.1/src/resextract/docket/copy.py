"""Material copy engine — the docket's byte-exact copy contract.

The contract, in one paragraph: given a strictly read-only target repository and a
list of requested source files, this module produces **byte-exact, hash-verified**
copies inside a docket's ``material/`` tree — it never writes into the source repo,
never follows a symlink out of the target root (every request whose path contains a
symlink component, or whose realpath escapes the root, is refused rather than
silently followed), refuses secret-shaped paths and secret-shaped content by shape
before any bytes are copied, enforces a per-file and a per-docket byte cap (over-cap
items are **linked**, never silently truncated, by appending a ``LINKS.md`` entry
carrying the absolute source path, sha256, byte size and a ready-to-run ``cp``
command), re-hashes every destination after writing and raises ``CopyIntegrityError``
if a single byte differs, preserves the executable bit while stripping
setuid/setgid/sticky, is idempotent (an already-present destination with a matching
sha256 is reported ``unchanged`` and rewritten never), records binary-ness and
excerpt spans for downstream ``EVIDENCE.md``/``MANIFEST.json`` use, and is honest
about what it refused: every request ends as exactly one of ``copied``,
``unchanged``, ``linked``, ``refused`` or ``missing``, with a machine-readable
reason.
"""

from __future__ import annotations

import dataclasses
import fnmatch
import hashlib
import json
import os
import re
import shutil
import stat
from dataclasses import dataclass, field
from typing import Iterable, Sequence

__all__ = [
    "CopyIntegrityError",
    "CopyItem",
    "CopyPlan",
    "CopyReport",
    "CopyRequest",
    "Copier",
    "is_binary",
    "sha256_file",
]

CHUNK = 1024 * 1024  # 1 MiB
SNIFF = 8 * 1024  # NUL-byte sniff window
SECRET_SCAN_BYTES = 64 * 1024  # content-shape scan window

STATUSES = ("copied", "unchanged", "linked", "refused", "missing")

# ---------------------------------------------------------------------------
# secret shapes
# ---------------------------------------------------------------------------

#: Path shapes that are refused outright, matched on the basename (fnmatch).
SECRET_PATH_GLOBS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa*",
    "id_dsa*",
    "id_ecdsa*",
    "id_ed25519*",
    "*.netrc",
    "netrc",
    "credentials.json",
    "credentials.yaml",
    "credentials.yml",
    "secrets.json",
    "secrets.yaml",
    "secrets.yml",
    "secrets.txt",
    "secrets",
    "*.p12",
    "*.pfx",
    "known_hosts",
)

#: Content shapes that are refused when found in the first 64 KiB.
SECRET_CONTENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("okr_token", re.compile(r"okr_[A-Za-z0-9]{16,}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("aws_akid", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("bearer_header", re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9._\-]{20,}")),
)


class CopyIntegrityError(RuntimeError):
    """Raised when a destination's sha256 does not match its source's."""

    def __init__(self, src: str, dest: str, sha_src: str, sha_dest: str) -> None:
        super().__init__(
            f"copy integrity failure: {dest!r} (sha256 {sha_dest}) != "
            f"source {src!r} (sha256 {sha_src})"
        )
        self.src = src
        self.dest = dest
        self.sha_src = sha_src
        self.sha_dest = sha_dest


# ---------------------------------------------------------------------------
# low-level helpers
# ---------------------------------------------------------------------------


def sha256_file(path: str | os.PathLike[str], chunk: int = CHUNK) -> str:
    """Return the hex sha256 of ``path``, read in ``chunk``-sized blocks."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def is_binary(path: str | os.PathLike[str], sniff: int = SNIFF) -> bool:
    """True when the first ``sniff`` bytes contain a NUL byte.

    Purely informational: it changes nothing about the copy — this engine always
    copies bytes, never decodes and re-encodes text.
    """
    try:
        with open(path, "rb") as fh:
            return b"\x00" in fh.read(sniff)
    except OSError:
        return False


def _within(path: str, root: str) -> bool:
    """True when realpath(``path``) is ``root`` itself or lives under it."""
    p = os.path.realpath(path)
    r = os.path.realpath(root)
    return p == r or p.startswith(r + os.sep)


def _lexically_inside(path: str, root_abs: str) -> bool:
    """True when ``abspath(path)`` is ``root_abs`` or sits under it, ignoring links."""
    p = os.path.abspath(path)
    return p == root_abs or p.startswith(root_abs + os.sep)


def _symlink_component(src: str, root_abs: str) -> str | None:
    """Return the first symlink component of ``src``, if any.

    Components shared with the target root are trusted (the root may itself be
    reached through a symlinked ancestor such as ``/home`` — that ancestor is
    the trusted boundary), so the walk starts at ``commonpath(src, root)``.
    This catches a link *anywhere* in the request, including one above the root
    such as ``/tmp/alias -> <target>``, while never flagging the root's own
    ancestors.
    """
    src_abs = os.path.abspath(src)
    try:
        common = os.path.commonpath([src_abs, root_abs])
    except ValueError:  # pragma: no cover - different drives (not on POSIX)
        common = os.sep
    rel = os.path.relpath(src_abs, common)
    if rel == os.curdir:
        return None
    current = common
    for part in rel.split(os.sep):
        current = os.path.join(current, part)
        if os.path.islink(current):
            return current
    return None


def _secret_path_reason(src: str) -> str | None:
    base = os.path.basename(src.rstrip(os.sep))
    for glob in SECRET_PATH_GLOBS:
        if fnmatch.fnmatch(base, glob):
            return "secret_path"
    return None


def _secret_content_reason(src: str) -> str | None:
    try:
        with open(src, "rb") as fh:
            head = fh.read(SECRET_SCAN_BYTES)
    except OSError:
        return None
    text = head.decode("utf-8", errors="replace")
    for _name, pattern in SECRET_CONTENT_PATTERNS:
        if pattern.search(text):
            return "secret_content"
    return None


def _safe_dest_rel(dest_rel: str) -> str | None:
    """Normalise ``dest_rel``; return None when it is unsafe/escaping."""
    if not dest_rel or os.path.isabs(dest_rel):
        return None
    normalised = os.path.normpath(dest_rel)
    if normalised in (os.curdir, os.pardir) or normalised.startswith(os.pardir + os.sep):
        return None
    return normalised


# ---------------------------------------------------------------------------
# dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CopyRequest:
    """One requested source file and where it should land inside ``material/``."""

    src: str
    dest_rel: str
    reason: str = ""
    excerpt: tuple[int, int] | None = None  # inclusive, 1-based line span


@dataclass
class CopyItem:
    """The outcome of one request.  ``status`` is one of :data:`STATUSES`."""

    src: str
    dest: str
    sha256: str | None = None
    bytes: int = 0
    mode: int | None = None
    excerpt: tuple[int, int] | None = None
    reason: str = ""
    status: str = "refused"
    refusal_reason: str | None = None
    binary: bool = False

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        if self.excerpt is not None:
            d["excerpt"] = list(self.excerpt)
        return d


@dataclass
class CopyPlan:
    """What :meth:`Copier.plan` decided, before any byte is written."""

    items: list[CopyItem] = field(default_factory=list)
    to_copy: list[CopyItem] = field(default_factory=list)
    to_link: list[CopyItem] = field(default_factory=list)
    refused: list[CopyItem] = field(default_factory=list)
    missing: list[CopyItem] = field(default_factory=list)
    total_bytes: int = 0  # bytes that would be copied into material/

    def to_dict(self) -> dict:
        return {
            "items": [i.to_dict() for i in self.items],
            "to_copy": [i.dest for i in self.to_copy],
            "to_link": [i.dest for i in self.to_link],
            "refused": [i.dest for i in self.refused],
            "missing": [i.dest for i in self.missing],
            "total_bytes": self.total_bytes,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


@dataclass
class CopyReport:
    """What :meth:`Copier.execute` actually did."""

    items: list[CopyItem] = field(default_factory=list)
    copied: list[CopyItem] = field(default_factory=list)
    unchanged: list[CopyItem] = field(default_factory=list)
    linked: list[CopyItem] = field(default_factory=list)
    refused: list[CopyItem] = field(default_factory=list)
    missing: list[CopyItem] = field(default_factory=list)
    total_bytes: int = 0  # bytes present in material/ (copied + unchanged)
    verified: int = 0  # destinations re-hashed and confirmed == source sha256
    written_paths: list[str] = field(default_factory=list)

    #: convenience counts (the handoff/verdict format asks for numbers)
    @property
    def copied_count(self) -> int:
        return len(self.copied)

    @property
    def unchanged_count(self) -> int:
        return len(self.unchanged)

    @property
    def linked_count(self) -> int:
        return len(self.linked)

    @property
    def refused_count(self) -> int:
        return len(self.refused)

    @property
    def missing_count(self) -> int:
        return len(self.missing)

    def to_dict(self) -> dict:
        return {
            "items": [i.to_dict() for i in self.items],
            "copied": len(self.copied),
            "unchanged": len(self.unchanged),
            "linked": len(self.linked),
            "refused": len(self.refused),
            "missing": len(self.missing),
            "total_bytes": self.total_bytes,
            "verified": self.verified,
            "written_paths": list(self.written_paths),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


# ---------------------------------------------------------------------------
# the copier
# ---------------------------------------------------------------------------


class Copier:
    """Plan and execute byte-exact copies from a read-only target into a docket."""

    def __init__(
        self,
        target_root: str | os.PathLike[str],
        docket_dir: str | os.PathLike[str],
        *,
        per_file_cap: int = 2 * 1024 * 1024,
        per_docket_cap: int = 200 * 1024 * 1024,
        secret_scan: bool = True,
        emit_excerpt_index: bool = True,
    ) -> None:
        self.target_root = os.path.abspath(os.fspath(target_root))
        self.docket_dir = os.path.abspath(os.fspath(docket_dir))
        self.per_file_cap = per_file_cap
        self.per_docket_cap = per_docket_cap
        self.secret_scan = secret_scan
        self.emit_excerpt_index = emit_excerpt_index
        self._root_abs = self.target_root
        self._root_real = os.path.realpath(self.target_root)
        self._material = os.path.join(self.docket_dir, "material")

    # -- paths ---------------------------------------------------------------

    @property
    def material_dir(self) -> str:
        return self._material

    def material_path(self, dest_rel: str) -> str:
        return os.path.join(self._material, dest_rel)

    @property
    def links_path(self) -> str:
        return os.path.join(self._material, "LINKS.md")

    @property
    def excerpts_path(self) -> str:
        return os.path.join(self._material, "EXCERPTS.md")

    # -- planning ------------------------------------------------------------

    def plan(self, requests: Sequence[CopyRequest]) -> CopyPlan:
        """Validate every request and bucket it.  Never raises on bad input.

        Requests are processed in sorted ``dest_rel`` order so that the
        per-docket cap result is reproducible: once the running total would
        exceed ``per_docket_cap``, that item and every later copy candidate is
        ``linked`` with ``refusal_reason="docket_cap"``.
        """
        plan = CopyPlan()
        ordered = sorted(requests, key=lambda r: (r.dest_rel, r.src))
        running = 0
        docket_full = False

        for req in ordered:
            item = self._classify(req, docket_full)
            if item is None:  # unreachable; _classify never raises
                continue
            if item.status == "copied":
                if running + item.bytes > self.per_docket_cap:
                    item = dataclasses.replace(
                        item,
                        status="linked",
                        refusal_reason="docket_cap",
                    )
                    docket_full = True
                else:
                    running += item.bytes
            elif item.status == "linked" and item.refusal_reason == "per_file_cap":
                # counted as linked, but the docket total is not consumed
                pass
            if item.status == "linked":
                plan.to_link.append(item)
            elif item.status == "refused":
                plan.refused.append(item)
            elif item.status == "missing":
                plan.missing.append(item)
            else:
                plan.to_copy.append(item)
            plan.items.append(item)

        plan.items.sort(key=lambda i: (i.dest, i.src))
        plan.total_bytes = sum(i.bytes for i in plan.to_copy)
        return plan

    def _classify(self, req: CopyRequest, docket_full: bool) -> CopyItem:
        """Classify one request.  Wrapped by :meth:`plan` so it cannot raise."""
        item = CopyItem(
            src=req.src,
            dest=req.dest_rel,
            excerpt=tuple(req.excerpt) if req.excerpt else None,
            reason=req.reason,
        )
        try:
            return self._classify_inner(item, req, docket_full)
        except Exception as exc:  # defensive: validation must never raise
            return dataclasses.replace(
                item,
                status="refused",
                refusal_reason=f"validation_error:{type(exc).__name__}",
            )

    def _classify_inner(
        self, item: CopyItem, req: CopyRequest, docket_full: bool
    ) -> CopyItem:
        src = req.src

        safe_dest = _safe_dest_rel(req.dest_rel)
        if safe_dest is None:
            return dataclasses.replace(
                item, status="refused", refusal_reason="unsafe_dest"
            )
        dest = safe_dest

        # 1. symlinks — never followed.  Checked *before* containment so that a
        #    link which leaves the root is reported as the symlink it is, not as
        #    a plain out-of-root path.
        if _symlink_component(src, self._root_abs) is not None:
            return dataclasses.replace(
                item, status="refused", refusal_reason="symlink"
            )
        # a lexically-inside path whose realpath escapes did so through a link
        if _lexically_inside(src, self._root_abs) and not _within(
            os.path.realpath(src), self._root_real
        ):
            return dataclasses.replace(
                item, status="refused", refusal_reason="symlink"
            )

        # 2. containment — realpath must live inside the target root
        if not _within(src, self._root_abs):
            return dataclasses.replace(
                item, status="refused", refusal_reason="outside_target_root"
            )

        # 3. missing
        if not os.path.lexists(src):
            return dataclasses.replace(
                item, status="missing", refusal_reason="not_found"
            )

        # 4. regular file
        if os.path.isdir(src):
            return dataclasses.replace(
                item, status="refused", refusal_reason="is_directory"
            )
        if not os.path.isfile(src):
            return dataclasses.replace(
                item, status="refused", refusal_reason="not_regular_file"
            )

        # 5. secrets — path shape, then content shape.  Before caps, so an
        #    over-cap path can never smuggle a secret past the gate.
        if self.secret_scan:
            reason = _secret_path_reason(src)
            if reason is None:
                reason = _secret_content_reason(src)
            if reason is not None:
                return dataclasses.replace(
                    item, status="refused", refusal_reason=reason
                )

        st = os.stat(src)
        size = int(st.st_size)
        digest = sha256_file(src)
        item = dataclasses.replace(
            item,
            dest=dest,
            sha256=digest,
            bytes=size,
            mode=stat.S_IMODE(st.st_mode),
            binary=is_binary(src),
        )

        # 6. caps
        if size > self.per_file_cap:
            return dataclasses.replace(
                item, status="linked", refusal_reason="per_file_cap"
            )
        if docket_full:
            return dataclasses.replace(
                item, status="linked", refusal_reason="docket_cap"
            )
        return dataclasses.replace(item, status="copied", refusal_reason=None)

    # -- execution -----------------------------------------------------------

    def execute(self, plan: CopyPlan) -> CopyReport:
        """Write the plan's copies, verify them, and emit stub/index files."""
        report = CopyReport()
        os.makedirs(self._material, exist_ok=True)
        consumed = 0

        for item in sorted(plan.items, key=lambda i: (i.dest, i.src)):
            if item.status in ("refused", "missing"):
                out = item
            elif item.status == "linked":
                out = item
            elif item.status == "copied":
                out = self._write_one(item)
                if out.status in ("copied", "unchanged"):
                    consumed += out.bytes
                if out.status == "copied":
                    report.written_paths.append(self.material_path(out.dest))
                if out.status in ("copied", "unchanged"):
                    report.verified += 1
            else:  # pragma: no cover - unknown status is treated as refused
                out = dataclasses.replace(
                    item,
                    status="refused",
                    refusal_reason=item.refusal_reason or "unknown_status",
                )

            report.items.append(out)
            bucket = {
                "copied": report.copied,
                "unchanged": report.unchanged,
                "linked": report.linked,
                "refused": report.refused,
                "missing": report.missing,
            }.get(out.status)
            if bucket is not None:
                bucket.append(out)

        report.total_bytes = consumed

        links = [i for i in report.items if i.status == "linked"]
        if links and self._write_links(links):
            report.written_paths.append(self.links_path)

        if self.emit_excerpt_index:
            excerpted = [
                i
                for i in report.items
                if i.excerpt and i.status in ("copied", "unchanged")
            ]
            if excerpted and self._write_excerpts(excerpted):
                report.written_paths.append(self.excerpts_path)

        report.items.sort(key=lambda i: (i.dest, i.src))
        report.written_paths.sort()
        return report

    # -- one file ------------------------------------------------------------

    def _write_one(self, item: CopyItem) -> CopyItem:
        dest = self.material_path(item.dest)
        if not _within(os.path.dirname(dest) or self._material, self._material):
            return dataclasses.replace(
                item, status="refused", refusal_reason="escape_dest"
            )
        src_sha = item.sha256 or sha256_file(item.src)

        os.makedirs(os.path.dirname(dest), exist_ok=True)

        # idempotent: an already-present, byte-identical destination is not
        # rewritten (mtime survives; later docket stages can trust it).
        if os.path.isfile(dest) and sha256_file(dest) == src_sha:
            mode = stat.S_IMODE(os.stat(dest).st_mode)
            return dataclasses.replace(
                item, sha256=src_sha, status="unchanged", mode=mode,
                refusal_reason=None,
            )

        tmp = f"{dest}.tmp-{os.getpid()}-{abs(hash(item.dest)) & 0xFFFF:x}"
        try:
            # copyfile semantics: bytes only, no metadata copy, no follow
            shutil.copyfile(item.src, tmp)
            final_mode = (item.mode if item.mode is not None else
                          stat.S_IMODE(os.stat(item.src).st_mode)) & 0o777
            os.chmod(tmp, final_mode)
            os.replace(tmp, dest)  # atomic: no partial file ever visible
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

        dest_sha = sha256_file(dest)
        if dest_sha != src_sha:
            # a bad copy is never reported as good
            raise CopyIntegrityError(item.src, dest, src_sha, dest_sha)

        return dataclasses.replace(
            item,
            sha256=src_sha,
            status="copied",
            mode=stat.S_IMODE(os.stat(dest).st_mode),
            refusal_reason=None,
        )

    # -- stub/index writers --------------------------------------------------

    def _write_links(self, links: Iterable[CopyItem]) -> bool:
        """Merge over-cap items into LINKS.md.  True when the file changed."""
        entries: dict[str, str] = {}
        if os.path.isfile(self.links_path):
            entries.update(self._parse_links())
        for item in links:
            src = os.path.abspath(item.src)
            size = item.bytes
            sha = item.sha256 or ""
            dest_path = self.material_path(item.dest)
            cmd = f"cp -- {_shq(src)} {_shq(dest_path)}"
            entries[src] = (
                f"| `{item.dest}` | `{src}` | `{sha}` | {size} | `{cmd}` |"
            )

        lines = [
            "# LINKS — material too large to copy into this docket",
            "",
            f"Per-file cap: {self.per_file_cap} bytes. "
            f"Per-docket cap: {self.per_docket_cap} bytes.",
            "",
            "Each row is a file that was requested but not copied. The absolute",
            "source path, its sha256 and byte size are recorded so the material can",
            "be re-obtained or verified later; the `cp` command is ready to run.",
            "",
            "| dest | source | sha256 | bytes | copy command |",
            "| --- | --- | --- | --- | --- |",
        ]
        for src in sorted(entries):
            lines.append(entries[src])
        lines.append("")
        return _write_text_if_changed(self.links_path, "\n".join(lines))

    def _parse_links(self) -> dict[str, str]:
        """Recover existing LINKS.md rows, keyed by absolute source path."""
        rows: dict[str, str] = {}
        pattern = re.compile(r"^\|\s*`(?P<dest>[^`]*)`\s*\|\s*`(?P<src>[^`]*)`\s*\|")
        try:
            with open(self.links_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    m = pattern.match(line.strip())
                    if m:
                        rows[m.group("src")] = line.strip()
        except OSError:
            pass
        return rows

    def _write_excerpts(self, items: Iterable[CopyItem]) -> bool:
        lines = [
            "# EXCERPTS — copied material carrying a cited line span",
            "",
            "| dest | lines | reason |",
            "| --- | --- | --- |",
        ]
        rows = []
        for item in items:
            lo, hi = item.excerpt  # type: ignore[misc]
            rows.append(f"| `{item.dest}` | {lo}-{hi} | {item.reason} |")
        lines.extend(sorted(rows))
        lines.append("")
        return _write_text_if_changed(self.excerpts_path, "\n".join(lines))


def _shq(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def _write_text_if_changed(path: str, text: str) -> bool:
    """Atomically write ``text``; return False (no write) if already identical."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            if fh.read() == text:
                return False
    except OSError:
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp-{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
    return True
