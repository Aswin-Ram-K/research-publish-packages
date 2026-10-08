"""Commit-pinned source resolution — bytes that cannot move under the reader.

Why this module exists
----------------------
``resextract.docket.copy.Copier`` reads the **working tree**: it opens a path and
hashes what it finds.  That is correct for a repository nobody else touches, and
wrong for one that is being written while we read it.  If the target's own
self-build loop commits ``b44e0e1`` and then edits a file, a docket that recorded
``head_sha = b44e0e1`` and copied the file afterwards holds bytes that *no
commit ever contained*.  Nothing in the copy path would notice; the docket's
"verifiable at commit X" claim would simply be false.

:class:`GitObjectSource` removes the race by reading the **object store**, not the
working tree: the bytes are the bytes git committed, and they are immutable.  The
working tree is left to :class:`WorkingTreeSource`, which reproduces the old
behaviour explicitly and for callers who genuinely want it.

Design decisions (and why)
--------------------------
* ``git cat-file blob <commit>:<path>`` is the content read.  ``git show`` also
  works but applies textconv/``--textconv``-style presentation and paging
  affordances around content; ``cat-file blob`` is the plumbing command that
  emits the raw object with no interpretation, which is what byte-exactness and
  a NUL byte require.
* ``git ls-tree -z <commit> -- <path>`` is the *identity* read: one call returns
  the git mode, the object type and the **blob sha** — the same value
  ``git rev-parse <commit>:<path>`` would print, plus the mode needed to tell a
  regular file (``100644``/``100755``) from a directory (``040000``) and a
  symlink (``120000``).  Reusing that one call avoids a second TOCTOU window.
* **There is no working-tree fallback.**  A path absent at that commit raises
  :class:`PathNotFoundAtCommit`; a path that is a directory raises
  :class:`PathIsDirectoryAtCommit`; a symlink raises :class:`PathIsSymlinkAtCommit`
  (git stores a symlink as a blob whose bytes are the link target — copying it as
  file content would be a silent lie).  A fallback would defeat the entire point
  of the module.
* Containment is enforced *before* any git call: absolute paths, ``..`` anywhere,
  and anything under ``.worktrees/`` are refused.  ``.worktrees/`` is refused
  because a live target's sibling worktrees are exactly the trees a foreign
  writer is churning through (see ``docs/LIVE_TARGET_NOTES.md``).
* :func:`verify_pinned` is the material gate's re-check: it re-hashes the
  destination and raises :class:`PinnedIntegrityError` on any mismatch, mirroring
  the copy engine's ``CopyIntegrityError`` discipline.

Secret-shaped paths are refused by default here too (reusing the copy engine's
glob list) so a commit-pinned read cannot hand a docket the bytes of an ``.env``
that the copier would have refused.
"""

from __future__ import annotations

import fnmatch
import hashlib
import os
import posixpath
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any, Protocol

from resextract.docket.copy import SECRET_PATH_GLOBS, sha256_file
from resextract.refresh.staleness import GIT_TIMEOUT_S

__all__ = [
    "CommitNotFound",
    "GitCommandError",
    "GitObjectSource",
    "GitSourceError",
    "PathIsDirectoryAtCommit",
    "PathIsSymlinkAtCommit",
    "PathNotFoundAtCommit",
    "PinnedFile",
    "PinnedIntegrityError",
    "RESOLVED_FROM",
    "SourcePathRefused",
    "SourceResolver",
    "WorkingTreeSource",
    "commit_exists",
    "normalise_repo_relative",
    "resolve_head",
    "verify_pinned",
]

#: Provenance of resolved bytes.  Exactly one of these two strings.
RESOLVED_FROM = ("git_object", "working_tree")

#: Directory whose contents belong to live sibling worktrees; never resolved.
_WORKTREE_DIR = ".worktrees"


# --------------------------------------------------------------------------- #
# typed failures
# --------------------------------------------------------------------------- #


class GitSourceError(RuntimeError):
    """Base class for every typed failure raised by this module."""

    def __init__(
        self,
        message: str,
        *,
        path: str | None = None,
        commit_sha: str | None = None,
    ) -> None:
        super().__init__(message)
        self.path = path
        self.commit_sha = commit_sha


class SourcePathRefused(GitSourceError):
    """The requested path is unsafe, out of root, or under ``.worktrees/``."""


class PathNotFoundAtCommit(GitSourceError):
    """The path does not exist at that commit — and was **not** read from disk."""


class PathIsDirectoryAtCommit(GitSourceError):
    """The path names a tree at that commit, not a blob."""


class PathIsSymlinkAtCommit(GitSourceError):
    """The path names a symlink at that commit (git stores its target as a blob)."""


class CommitNotFound(GitSourceError):
    """``commit_sha`` is not a commit in this repository."""


class GitCommandError(GitSourceError):
    """A git invocation failed for a reason other than the ones above."""


class PinnedIntegrityError(RuntimeError):
    """A destination's sha256 does not match the pinned source's."""

    def __init__(self, path: str, dest: str, expected: str, actual: str) -> None:
        super().__init__(
            f"pinned integrity failure: {dest!r} (sha256 {actual}) != "
            f"pinned {path!r} (sha256 {expected})"
        )
        self.path = path
        self.dest = dest
        self.expected = expected
        self.actual = actual


# --------------------------------------------------------------------------- #
# git plumbing (bytes-capable)
# --------------------------------------------------------------------------- #


def _git_raw(
    root: str | os.PathLike[str], *args: str, timeout: float = GIT_TIMEOUT_S
) -> tuple[int, bytes, bytes]:
    """Run ``git -C <root> <args>`` returning ``(rc, stdout_bytes, stderr_bytes)``.

    This is deliberately a *bytes* runner: ``cat-file blob`` output can contain
    NUL bytes and must never pass through a text codec.  It mirrors
    ``resextract.refresh.staleness._git`` (same timeout, same never-raise
    contract) but cannot reuse it, because that one decodes as UTF-8 text.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", os.fspath(root), *args],
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return 127, b"", f"git not found: {exc}".encode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return -1, b"", f"git timed out after {timeout}s: git {' '.join(args)}".encode()
    except OSError as exc:  # pragma: no cover - exotic
        return 128, b"", f"{type(exc).__name__}: {exc}".encode("utf-8", "replace")
    return proc.returncode, proc.stdout or b"", proc.stderr or b""


def _err_text(err: bytes) -> str:
    return err.decode("utf-8", "replace").strip() or "no output"


def _short(sha: str | None, width: int = 8) -> str:
    return (sha or "?")[:width]


# --------------------------------------------------------------------------- #
# containment
# --------------------------------------------------------------------------- #


def normalise_repo_relative(path: str) -> str:
    """Return a safe repo-relative POSIX path, or raise :class:`SourcePathRefused`.

    Refuses (in this order): the empty path; absolute paths (POSIX ``/`` and
    Windows drive forms); any ``..`` component; a path that normalises to the
    repository root; and any path with a ``.worktrees`` component.
    """
    raw = (path or "").strip()
    if not raw:
        raise SourcePathRefused("empty path refused", path=path)
    candidate = raw.replace("\\", "/")
    if candidate.startswith("/") or (len(candidate) > 1 and candidate[1] == ":"):
        raise SourcePathRefused(f"absolute path refused: {raw!r}", path=path)
    normalised = posixpath.normpath(candidate)
    parts = [p for p in normalised.split("/") if p not in ("", ".")]
    if normalised.startswith("..") or ".." in parts:
        raise SourcePathRefused(
            f"path escapes the repository root ('..' component): {raw!r}", path=path
        )
    if not parts:
        raise SourcePathRefused(
            f"path normalises to the repository root: {raw!r}", path=path
        )
    if any(part == _WORKTREE_DIR for part in parts):
        raise SourcePathRefused(
            f"paths under {_WORKTREE_DIR}/ are refused "
            f"(live sibling worktrees of a target under concurrent write): {raw!r}",
            path=path,
        )
    return "/".join(parts)


def _secret_path_shape(rel: str) -> bool:
    base = rel.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(base, glob) for glob in SECRET_PATH_GLOBS)


# --------------------------------------------------------------------------- #
# pinned bytes
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PinnedFile:
    """Bytes resolved for one repo-relative path, with the identity that pins them.

    ``mode`` carries POSIX permission bits (``0o644`` / ``0o755``), matching
    ``CopyItem.mode`` so downstream writers behave identically; ``git_mode``
    keeps the raw git mode (``0o100644``, ``0o100755``, …) for provenance.
    ``blob_sha`` is git's own object id — the ground-truth identity that
    ``sha256`` (the content hash of the bytes) is reported alongside.
    """

    path_repo_relative: str
    commit_sha: str | None
    bytes_: bytes
    sha256: str
    mode: int
    resolved_from: str
    blob_sha: str | None = None
    git_mode: int | None = None

    def __post_init__(self) -> None:
        if self.resolved_from not in RESOLVED_FROM:
            raise ValueError(
                f"resolved_from must be one of {RESOLVED_FROM}, got {self.resolved_from!r}"
            )

    @property
    def size(self) -> int:
        return len(self.bytes_)

    @property
    def executable(self) -> bool:
        return bool(stat.S_IMODE(self.mode) & 0o111)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_repo_relative": self.path_repo_relative,
            "commit_sha": self.commit_sha,
            "commit8": _short(self.commit_sha),
            "blob_sha": self.blob_sha,
            "blob8": _short(self.blob_sha),
            "sha256": self.sha256,
            "sha8": self.sha256[:8],
            "bytes": self.size,
            "mode": oct(stat.S_IMODE(self.mode)),
            "git_mode": oct(self.git_mode) if self.git_mode is not None else None,
            "resolved_from": self.resolved_from,
        }

    def write_to(self, dest: str | os.PathLike[str]) -> str:
        """Write the pinned bytes to ``dest`` atomically; return the absolute path.

        Temp file in the destination directory, ``fsync``, ``chmod`` to the mode
        with ``0o777`` applied — which preserves the executable bit and strips
        setuid/setgid/sticky — then ``os.replace``, so no partial file is ever
        visible and the copy engine's discipline is mirrored exactly.
        """
        target = os.path.abspath(os.fspath(dest))
        parent = os.path.dirname(target) or os.curdir
        os.makedirs(parent, exist_ok=True)
        final_mode = stat.S_IMODE(self.mode) & 0o777
        fd, tmp = tempfile.mkstemp(prefix=os.path.basename(target) + ".tmp-", dir=parent)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(self.bytes_)
                fh.flush()
                os.fsync(fh.fileno())
            os.chmod(tmp, final_mode)
            os.replace(tmp, target)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return target


def verify_pinned(pinned: PinnedFile, dest: str | os.PathLike[str]) -> str:
    """Re-hash ``dest`` and confirm it equals ``pinned.sha256``.

    Returns the confirmed sha256; raises :class:`PinnedIntegrityError` if the
    destination is missing, unreadable, or differs by a single byte.
    """
    target = os.fspath(dest)
    try:
        actual = sha256_file(target)
    except OSError as exc:
        raise PinnedIntegrityError(
            pinned.path_repo_relative, target, pinned.sha256, f"unreadable: {exc}"
        ) from exc
    if actual != pinned.sha256:
        raise PinnedIntegrityError(
            pinned.path_repo_relative, target, pinned.sha256, actual
        )
    return actual


# --------------------------------------------------------------------------- #
# resolvers
# --------------------------------------------------------------------------- #


class SourceResolver(Protocol):
    """What a source is, from the docket's point of view."""

    def resolve(self, path_repo_relative: str) -> PinnedFile | None:  # pragma: no cover
        ...


class GitObjectSource:
    """Resolve repo-relative paths to the bytes committed at ``commit_sha``.

    Reads only the object store.  The working tree is never consulted, so a
    dirty or concurrently-rewritten checkout cannot change the answer.
    """

    def __init__(
        self,
        root: str | os.PathLike[str],
        commit_sha: str,
        *,
        timeout: float = GIT_TIMEOUT_S,
        refuse_secret_paths: bool = True,
    ) -> None:
        self.root = os.path.abspath(os.fspath(root))
        self.commit_sha = (commit_sha or "").strip()
        self.timeout = timeout
        self.refuse_secret_paths = refuse_secret_paths
        if not self.commit_sha:
            raise GitCommandError(
                "GitObjectSource requires an explicit commit sha", commit_sha=commit_sha
            )
        if not commit_exists(self.root, self.commit_sha, timeout=timeout):
            raise CommitNotFound(
                f"commit {_short(self.commit_sha)} does not exist in {self.root!r}",
                commit_sha=self.commit_sha,
            )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"GitObjectSource(root={self.root!r}, commit_sha={_short(self.commit_sha)!r})"

    def _ls_tree(self, rel: str) -> tuple[int, str, str]:
        """``(git_mode, object_type, blob_sha)`` for ``rel`` at ``commit_sha``.

        An empty listing means "absent at this commit" — that is the signal the
        typed error is built from, and it is *not* an error of git itself.
        """
        rc, out, err = _git_raw(
            self.root, "ls-tree", "-z", self.commit_sha, "--", rel, timeout=self.timeout
        )
        if rc != 0:
            raise GitCommandError(
                f"git ls-tree {_short(self.commit_sha)} -- {rel!r} failed (rc={rc}): "
                f"{_err_text(err)}",
                path=rel,
                commit_sha=self.commit_sha,
            )
        if not out:
            raise PathNotFoundAtCommit(
                f"{rel!r} does not exist at commit {_short(self.commit_sha)} "
                f"(refusing to fall back to the working tree)",
                path=rel,
                commit_sha=self.commit_sha,
            )
        first = out.split(b"\0", 1)[0]
        meta, _sep, _path = first.partition(b"\t")
        fields = meta.split()
        if len(fields) < 3:
            raise GitCommandError(
                f"unparseable ls-tree entry for {rel!r}: {first!r}",
                path=rel,
                commit_sha=self.commit_sha,
            )
        try:
            git_mode = int(fields[0], 8)
        except ValueError as exc:  # pragma: no cover - git always prints octal
            raise GitCommandError(
                f"unparseable git mode for {rel!r}: {fields[0]!r}",
                path=rel,
                commit_sha=self.commit_sha,
            ) from exc
        return git_mode, fields[1].decode("ascii", "replace"), fields[2].decode("ascii")

    def resolve(self, path_repo_relative: str) -> PinnedFile:
        """Return the bytes committed at ``commit_sha``; never the working tree."""
        rel = normalise_repo_relative(path_repo_relative)
        if self.refuse_secret_paths and _secret_path_shape(rel):
            raise SourcePathRefused(
                f"secret-shaped path refused: {rel!r}", path=rel, commit_sha=self.commit_sha
            )
        git_mode, obj_type, blob_sha = self._ls_tree(rel)
        if git_mode == 0o120000:
            raise PathIsSymlinkAtCommit(
                f"{rel!r} is a symlink at commit {_short(self.commit_sha)}; "
                f"a symlink's blob is its target path, not file content",
                path=rel,
                commit_sha=self.commit_sha,
            )
        if obj_type == "tree" or git_mode == 0o040000:
            raise PathIsDirectoryAtCommit(
                f"{rel!r} is a directory (tree) at commit {_short(self.commit_sha)}",
                path=rel,
                commit_sha=self.commit_sha,
            )
        if obj_type != "blob":
            raise GitCommandError(
                f"{rel!r} is a {obj_type} at commit {_short(self.commit_sha)}, not a blob",
                path=rel,
                commit_sha=self.commit_sha,
            )
        rc, out, err = _git_raw(
            self.root, "cat-file", "blob", f"{self.commit_sha}:{rel}", timeout=self.timeout
        )
        if rc != 0:
            # Never a fallback: a failure here is a failure, reported as one.
            raise GitCommandError(
                f"git cat-file blob {_short(self.commit_sha)}:{rel} failed (rc={rc}): "
                f"{_err_text(err)}",
                path=rel,
                commit_sha=self.commit_sha,
            )
        data = out
        return PinnedFile(
            path_repo_relative=rel,
            commit_sha=self.commit_sha,
            bytes_=data,
            sha256=hashlib.sha256(data).hexdigest(),
            mode=0o755 if git_mode == 0o100755 else 0o644,
            resolved_from="git_object",
            blob_sha=blob_sha,
            git_mode=git_mode,
        )

    def resolve_many(self, paths: list[str]) -> list[PinnedFile]:
        """Resolve several paths; the first failure propagates (no silent gaps)."""
        return [self.resolve(p) for p in paths]


class WorkingTreeSource:
    """Resolve repo-relative paths from the working tree — the old behaviour.

    Explicitly *not* the default for a live target: bytes read here correspond to
    no commit in particular, and can change between the recording of a head sha
    and the copy.  Kept for callers that genuinely want the filesystem.
    """

    def __init__(self, root: str | os.PathLike[str], *, timeout: float = GIT_TIMEOUT_S) -> None:
        self.root = os.path.abspath(os.fspath(root))
        self.timeout = timeout

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"WorkingTreeSource(root={self.root!r})"

    def resolve(self, path_repo_relative: str) -> PinnedFile | None:
        """Return the working-tree bytes, ``None`` when the path is absent."""
        rel = normalise_repo_relative(path_repo_relative)
        full = os.path.join(self.root, *rel.split("/"))
        if os.path.isdir(full):
            raise PathIsDirectoryAtCommit(
                f"{rel!r} is a directory in the working tree of {self.root!r}", path=rel
            )
        if not os.path.isfile(full):
            return None
        with open(full, "rb") as fh:
            data = fh.read()
        st = os.stat(full)
        return PinnedFile(
            path_repo_relative=rel,
            commit_sha=_head_or_none(self.root),
            bytes_=data,
            sha256=hashlib.sha256(data).hexdigest(),
            mode=stat.S_IMODE(st.st_mode),
            resolved_from="working_tree",
            blob_sha=None,
            git_mode=0o100755 if st.st_mode & 0o111 else 0o100644,
        )


# --------------------------------------------------------------------------- #
# repository probes
# --------------------------------------------------------------------------- #


def commit_exists(
    root: str | os.PathLike[str], sha: str, *, timeout: float = GIT_TIMEOUT_S
) -> bool:
    """True when ``sha`` resolves to a commit object in ``root``."""
    candidate = (sha or "").strip()
    if not candidate:
        return False
    rc, _out, _err = _git_raw(
        root, "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}", timeout=timeout
    )
    return rc == 0


def resolve_head(root: str | os.PathLike[str], *, timeout: float = GIT_TIMEOUT_S) -> str:
    """Return the current HEAD sha; raise :class:`GitCommandError` if unresolvable."""
    rc, out, err = _git_raw(root, "rev-parse", "HEAD", timeout=timeout)
    sha = out.decode("ascii", "replace").strip()
    if rc != 0 or not sha:
        raise GitCommandError(
            f"cannot resolve HEAD in {os.fspath(root)!r} (rc={rc}): {_err_text(err)}"
        )
    return sha


def _head_or_none(root: str | os.PathLike[str]) -> str | None:
    try:
        return resolve_head(root)
    except GitCommandError:
        return None
