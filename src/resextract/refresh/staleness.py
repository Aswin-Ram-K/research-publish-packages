"""Did the target move, and which docket items does that invalidate?

Two questions, deliberately kept apart:

* :func:`read_target_state` / :func:`detect_change` answer *what moved* — pure
  git measurement, no judgement, failures returned as values.
* :func:`freshness_for` answers *what that invalidates* — a judgement, but one
  whose vocabulary is fixed to ``current | stale | needs_rework | superseded``
  and which always returns the evidence behind the call (which file, which
  commit range).

Nothing here raises on a git failure: failures land in ``errors``/``warnings``
on the report and in ``reasons`` on the freshness.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

CHANGE_KINDS = ("none", "head_moved", "working_tree_changed", "both")
FRESHNESS_STATES = ("current", "stale", "needs_rework", "superseded")

MAX_CHANGED_FILES = 500
GIT_TIMEOUT_S = 20.0

#: Directory components that are never walked and whose tracked files are
#: excluded from the mtime digest (the digest only ever stats files that
#: ``git ls-files`` names — it never traverses a directory tree).
IGNORE_DIR_PARTS = frozenset(
    {
        ".git",
        "node_modules",
        ".worktrees",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
    }
)


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #


def _git(repo: str | os.PathLike[str], *args: str, timeout: float = GIT_TIMEOUT_S) -> tuple[int, str, str]:
    """Run ``git -C <repo> <args>``; never raises, returns ``(rc, stdout, stderr)``."""
    try:
        proc = subprocess.run(
            ["git", "-C", os.fspath(repo), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return 127, "", f"git not found: {exc}"
    except subprocess.TimeoutExpired:
        return -1, "", f"git timed out after {timeout}s: git {' '.join(args)}"
    except OSError as exc:  # pragma: no cover - exotic
        return 128, "", f"{type(exc).__name__}: {exc}"
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def short_sha(sha: str | None, width: int = 7) -> str:
    return (sha or "?").strip()[:width]


def _as_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def iso_now(now: Any = None) -> str:
    dt = _as_dt(now) or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalise_repo_path(path: str) -> str:
    """Repo-relative form of a reference path (strips ``material/``, ``./``, ``:`` line suffix)."""
    p = (path or "").strip().replace("\\", "/")
    if "#" in p:
        p = p.split("#", 1)[0]
    while p.startswith("./"):
        p = p[2:]
    if p.startswith("material/"):
        p = p[len("material/") :]
    return p.lstrip("/")


def _is_ignored(rel: str) -> bool:
    parts = [p for p in rel.replace("\\", "/").split("/") if p]
    return any(part in IGNORE_DIR_PARTS for part in parts)


def tracked_files(repo: str | os.PathLike[str], *, timeout: float = GIT_TIMEOUT_S) -> list[str]:
    """``git ls-files -z`` as a list; ``[]`` on any failure."""
    rc, out, _err = _git(repo, "ls-files", "-z", timeout=timeout)
    if rc != 0:
        return []
    return [p for p in out.split("\0") if p]


# --------------------------------------------------------------------------- #
# target state
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class TargetState:
    path: str
    head_sha: str | None
    branch: str | None
    dirty_paths: tuple[str, ...]
    mtime_digest: str
    seen_at: str
    warnings: tuple[str, ...] = field(default=())

    @property
    def dirty(self) -> bool:
        return bool(self.dirty_paths)

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "head_sha": self.head_sha,
            "head8": short_sha(self.head_sha, 8),
            "branch": self.branch,
            "dirty_paths": list(self.dirty_paths),
            "mtime_digest": self.mtime_digest,
            "seen_at": self.seen_at,
            "warnings": list(self.warnings),
        }


def mtime_digest(repo: str | os.PathLike[str], files: Sequence[str] | None = None) -> str:
    """Digest of ``(relpath, size, mtime_ns)`` over tracked files only.

    Never walks a directory: it stats exactly the paths ``git ls-files`` names,
    after filtering the ignore list, so ``.worktrees/`` and ``node_modules/``
    are never entered.
    """
    root = Path(os.fspath(repo))
    rels = list(files) if files is not None else tracked_files(repo)
    hasher = hashlib.sha256()
    for rel in sorted(r for r in rels if not _is_ignored(r)):
        full = root / rel
        try:
            st = full.stat()
            row = f"{rel}\0{st.st_size}\0{st.st_mtime_ns}\n"
        except OSError:
            row = f"{rel}\0MISSING\n"
        hasher.update(row.encode("utf-8"))
    return hasher.hexdigest()


def _parse_porcelain(out: str) -> list[str]:
    dirty: list[str] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        rest = line[3:].strip()
        if not rest:
            continue
        if " -> " in rest:  # rename: "R  old -> new"
            rest = rest.split(" -> ", 1)[1]
        rest = rest.strip().strip('"')
        if rest and not _is_ignored(rest):
            dirty.append(rest)
    return dirty


def read_target_state(path: str | os.PathLike[str], *, now: Any = None) -> TargetState:
    """Measure a target repo: HEAD, branch, dirty paths, tracked-file mtime digest."""
    repo = os.fspath(path)
    warnings: list[str] = []

    rc, out, err = _git(repo, "rev-parse", "HEAD")
    head = out.strip() or None
    if rc != 0:
        head = None
        warnings.append(f"git rev-parse HEAD failed (rc={rc}): {err.strip() or 'no output'}")

    rc, out, err = _git(repo, "symbolic-ref", "--short", "-q", "HEAD")
    branch = out.strip() or None
    if rc != 0:
        branch = None
        warnings.append("detached HEAD (or bare/unborn branch): no symbolic ref")

    rc, out, err = _git(repo, "status", "--porcelain")
    if rc == 0:
        dirty = _parse_porcelain(out)
    else:
        dirty = []
        warnings.append(f"git status --porcelain failed (rc={rc}): {err.strip() or 'no output'}")

    files = tracked_files(repo)
    if not files:
        warnings.append("git ls-files returned nothing: mtime digest covers no files")
    digest = mtime_digest(repo, files)

    return TargetState(
        path=repo,
        head_sha=head,
        branch=branch,
        dirty_paths=tuple(dirty),
        mtime_digest=digest,
        seen_at=iso_now(now),
        warnings=tuple(warnings),
    )


# --------------------------------------------------------------------------- #
# change detection
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ChangeReport:
    kind: str
    old_head: str | None
    new_head: str | None
    commits_between: int | None = None
    changed_files: tuple[str, ...] = field(default=())
    renamed: tuple[tuple[str, str], ...] = field(default=())
    added: tuple[str, ...] = field(default=())
    deleted: tuple[str, ...] = field(default=())
    working_tree_files: tuple[str, ...] = field(default=())
    truncated: bool = False
    note: str | None = None
    errors: tuple[str, ...] = field(default=())
    warnings: tuple[str, ...] = field(default=())

    @property
    def range(self) -> str:
        if self.old_head and self.new_head:
            return f"{short_sha(self.old_head)}..{short_sha(self.new_head)}"
        return f"??..{short_sha(self.new_head)}"

    @property
    def moved(self) -> bool:
        return self.kind in ("head_moved", "both")

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "old_head": self.old_head,
            "new_head": self.new_head,
            "range": self.range,
            "commits_between": self.commits_between,
            "changed_files": list(self.changed_files),
            "changed_file_count": len(self.changed_files),
            "renamed": [list(p) for p in self.renamed],
            "added": list(self.added),
            "deleted": list(self.deleted),
            "working_tree_files": list(self.working_tree_files),
            "truncated": self.truncated,
            "note": self.note,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def _diff_files(
    repo: str | os.PathLike[str], old: str, new: str, *, max_files: int
) -> tuple[list[str], list[tuple[str, str]], list[str], list[str], bool, list[str]]:
    """``(changed, renamed, added, deleted, truncated, warnings)`` from name-status."""
    changed: list[str] = []
    renamed: list[tuple[str, str]] = []
    added: list[str] = []
    deleted: list[str] = []
    warnings: list[str] = []
    truncated = False

    rc, out, err = _git(repo, "diff", "--name-status", "-M", f"{old}..{new}")
    if rc != 0:
        warnings.append(f"git diff --name-status {old}..{new} failed (rc={rc}): {err.strip()}")
        return changed, renamed, added, deleted, truncated, warnings

    seen = 0
    for line in out.splitlines():
        parts = [p for p in line.split("\t") if p != ""]
        if len(parts) < 2:
            continue
        status, paths = parts[0], parts[1:]
        seen += 1
        if seen > max_files:
            truncated = True
            break
        if status.startswith("R") and len(paths) >= 2:
            renamed.append((paths[0], paths[1]))
            changed.extend(paths[:2])
        elif status.startswith("C") and len(paths) >= 2:
            changed.append(paths[1])
        elif status.startswith("A"):
            added.append(paths[0])
            changed.append(paths[0])
        elif status.startswith("D"):
            deleted.append(paths[0])
            changed.append(paths[0])
        else:  # M, T, U, X …
            changed.append(paths[0])
    return changed, renamed, added, deleted, truncated, warnings


def detect_change(
    old_head: str | None,
    new_head: str | None,
    repo: str | os.PathLike[str],
    *,
    dirty_paths: Iterable[str] | None = None,
    max_files: int = MAX_CHANGED_FILES,
) -> ChangeReport:
    """Classify the move from ``old_head`` to ``new_head`` in ``repo``.

    ``kind`` is one of ``none | head_moved | working_tree_changed | both``.
    Every git failure is recorded in ``errors``/``warnings``, never raised.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if new_head is None:
        rc, out, err = _git(repo, "rev-parse", "HEAD")
        if rc == 0 and out.strip():
            new_head = out.strip()
        else:
            errors.append(f"cannot resolve current HEAD (rc={rc}): {err.strip() or 'no output'}")

    dirty = tuple(sorted({d for d in (dirty_paths or ()) if d}))
    changed: list[str] = []
    renamed: list[tuple[str, str]] = []
    added: list[str] = []
    deleted: list[str] = []
    truncated = False
    commits: int | None = None
    note: str | None = None
    head_moved = False

    if old_head is None:
        head_moved = new_head is not None
        note = "no_previous_state"
    elif new_head is None:
        note = "no_current_state"
        errors.append("cannot classify change: current HEAD is unknown")
    elif old_head == new_head:
        head_moved = False
    else:
        head_moved = True
        rc_anc, _o, _e = _git(repo, "merge-base", "--is-ancestor", old_head, new_head)
        if rc_anc != 0:
            note = "history_rewritten"
            warnings.append(
                f"{short_sha(old_head)} is not an ancestor of {short_sha(new_head)} "
                f"(force-push / rebase): commits_between is not a meaningful count"
            )
        else:
            rc_c, out_c, err_c = _git(repo, "rev-list", "--count", f"{old_head}..{new_head}")
            if rc_c == 0 and out_c.strip().isdigit():
                commits = int(out_c.strip())
            else:
                errors.append(
                    f"git rev-list --count failed (rc={rc_c}): {err_c.strip() or 'no output'}"
                )
        changed, renamed, added, deleted, truncated, warns = _diff_files(
            repo, old_head, new_head, max_files=max_files
        )
        warnings.extend(warns)

    working_tree_files = tuple(dirty)
    union = sorted({normalise_repo_path(p) for p in changed} | set(dirty))
    if truncated:
        warnings.append(f"changed-file list truncated at {max_files} entries")

    if head_moved and dirty:
        kind = "both"
    elif head_moved:
        kind = "head_moved"
    elif dirty:
        kind = "working_tree_changed"
    else:
        kind = "none"

    return ChangeReport(
        kind=kind,
        old_head=old_head,
        new_head=new_head,
        commits_between=commits,
        changed_files=tuple(union),
        renamed=tuple(renamed),
        added=tuple(added),
        deleted=tuple(deleted),
        working_tree_files=working_tree_files,
        truncated=truncated,
        note=note,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


# --------------------------------------------------------------------------- #
# freshness — what the change invalidates
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Freshness:
    state: str
    reasons: tuple[str, ...] = field(default=())
    age_days: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"state": self.state, "reasons": list(self.reasons), "age_days": self.age_days}


def _as_manifest(docket: Any) -> Any:
    """Accept a manifest, a plain dict, or a docket directory/file path."""
    if docket is None:
        return None
    if isinstance(docket, Mapping):
        from resextract.docket.manifest import DocketManifest

        try:
            return DocketManifest.model_validate(dict(docket))
        except Exception:
            # A partial dict is still usable: freshness only needs claims +
            # freshness.state + web_sources, and the validator is strict.
            return dict(docket)
    if isinstance(docket, (str, os.PathLike)):
        from resextract.docket.manifest import read_manifest

        return read_manifest(docket)
    return docket


def _manifest_dump(manifest: Any) -> dict[str, Any]:
    if manifest is None:
        return {}
    if hasattr(manifest, "model_dump"):
        return manifest.model_dump(mode="json", by_alias=True)
    return dict(manifest)


def _span_text(span: tuple[int, int] | None) -> str:
    if not span:
        return "the file"
    lo, hi = span
    return f"lines {lo}" if lo == hi else f"lines {lo}\u2013{hi}"


def _matches_changed(path: str, changed: Iterable[str]) -> str | None:
    """Return the changed path a reference touches, else ``None``."""
    ref = normalise_repo_path(path)
    if not ref:
        return None
    base = ref.rsplit("/", 1)[-1]
    for cand in changed:
        c = normalise_repo_path(cand)
        if c == ref:
            return c
        if c.rsplit("/", 1)[-1] == base and ("/" in c) == ("/" in ref):
            return c
    return None


def claim_provenance_files(
    manifest: Any, *, graph: Any = None
) -> list[tuple[str, str, str, tuple[int, int] | None, str | None]]:
    """``(claim_id, kind, path_or_node, span, resolved_file)`` for every provenance ref."""
    from resextract.docket.manifest import split_ref

    out: list[tuple[str, str, str, tuple[int, int] | None, str | None]] = []
    for claim in _manifest_dump(manifest).get("claims", []) or []:
        cid = str(claim.get("id") or "?")
        for ref in claim.get("provenance", []) or []:
            kind, target, span = split_ref(ref)
            resolved: str | None = None
            if kind == "file":
                resolved = normalise_repo_path(target)
            elif kind == "graph" and graph is not None:
                node = graph.by_id().get(target)
                if node is not None and getattr(node, "source_file", None):
                    resolved = normalise_repo_path(node.source_file)
            out.append((cid, kind, target, span, resolved))
    return out


def freshness_for(
    docket: Any,
    change: ChangeReport,
    *,
    now: Any = None,
    prior_art_ttl_days: float = 30,
    graph: Any = None,
    link_status: Mapping[str, str] | None = None,
) -> Freshness:
    """Judge a docket against a change: ``needs_rework`` > ``stale`` > ``current``.

    ``superseded`` is only ever returned because the manifest already says so —
    this function never promotes an item out of that state.
    """
    manifest = _as_manifest(docket)
    dump = _manifest_dump(manifest)
    freshness = dump.get("freshness") or {}
    old_state = str(freshness.get("state") or "current")
    now_dt = _as_dt(now) or datetime.now(timezone.utc)
    checked = _as_dt(freshness.get("prior_art_checked_at"))
    verified = _as_dt(freshness.get("verified_at"))
    anchor = max([d for d in (checked, verified) if d is not None], default=None)
    age_days = round((now_dt - anchor).total_seconds() / 86400.0, 3) if anchor else None

    if old_state == "superseded":
        return Freshness("superseded", ("manifest already marked superseded",), age_days)

    changed = tuple(change.changed_files)
    rework_reasons: list[str] = []
    stale_reasons: list[str] = []

    # 1. needs_rework - a cited file moved under the docket's feet.
    for cid, kind, target, span, resolved in claim_provenance_files(manifest, graph=graph):
        if not resolved:
            continue
        hit = _matches_changed(resolved, changed)
        if hit is None:
            continue
        where = f" (via graph node {target})" if kind == "graph" else ""
        if change.moved and change.old_head and change.new_head:
            rework_reasons.append(
                f"`{hit}` changed in `{change.range}` (commit {short_sha(change.new_head)})"
                f"{where}; claim {cid} cites {_span_text(span)}"
            )
        else:
            rework_reasons.append(
                f"`{hit}` has uncommitted changes in the working tree "
                f"(seen {short_sha(change.new_head, 8)}); claim {cid} cites {_span_text(span)}"
            )
    if rework_reasons and change.note == "history_rewritten":
        rework_reasons.append(
            f"history rewritten: `{short_sha(change.old_head)}` is not an ancestor of "
            f"`{short_sha(change.new_head)}` - the recorded range cannot be trusted"
        )

    # 2. stale - prior art aged out, or a cited URL is gone/changed/stubbed.
    if checked is None:
        stale_reasons.append(
            "prior art never checked (`prior_art_checked_at` is null) - "
            "the item cannot be certified against external sources"
        )
    else:
        age = (now_dt - checked).total_seconds() / 86400.0
        if age > float(prior_art_ttl_days):
            stale_reasons.append(
                f"prior art last checked {checked.strftime('%Y-%m-%dT%H:%M:%SZ')} "
                f"({age:.1f}d ago) exceeds the {prior_art_ttl_days:g}d TTL"
            )
    for source in dump.get("web_sources", []) or []:
        url = str(source.get("url") or "")
        status = (link_status or {}).get(url)
        if status == "gone":
            stale_reasons.append(f"cited web source is unreachable: {url}")
        elif status == "changed":
            stale_reasons.append(f"cited web source content changed and no longer matches: {url}")
        elif status == "suspect":
            stale_reasons.append(
                f"cited web source answered with a stub (suspect), not evidence: {url}"
            )

    reasons = tuple(dict.fromkeys(rework_reasons + stale_reasons))
    if rework_reasons:
        return Freshness("needs_rework", reasons, age_days)
    if stale_reasons:
        return Freshness("stale", reasons, age_days)
    return Freshness("current", (), age_days)


def needs_rework(change: ChangeReport, freshness: Freshness) -> bool:
    return freshness.state == "needs_rework"
