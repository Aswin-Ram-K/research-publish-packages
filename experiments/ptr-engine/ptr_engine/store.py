"""Content-addressed body store -- the warmpool.

Key = ``sha256`` of the body bytes. Layout ``<root>/<aa>/<sha256><ext>``, where
``aa`` is the first two hex characters, so a warmpool of a hundred thousand bodies
does not become one flat directory. Identical content is stored once: writing the
same bytes twice is idempotent and returns the same ``ResourceRef``.

The warmpool is an **isolated filespace**, not a workspace subdirectory. A root that
resolves inside the repository working tree is refused with
``PTR_WARMPOOL_INSIDE_REPO``: a store under the repo would be swept by every
`git clean`, copied by every archive, and would make "the warmpool" mean two
different things on two machines. It is a cache with content identity, and
content-addressed caches live outside the tree they cache.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import Optional, Union

from .errors import (
    PtrExtensionError,
    PtrHashMismatchError,
    PtrStoreMissError,
    PtrWarmpoolViolationError,
)
from .reference import ResourceRef

#: Files that mark a directory as the top of this repository. The engine looks for
#: them walking up from its own file, not from the process cwd: a store root is
#: judged against the tree the *engine* lives in, so `cd /tmp && compile(...)`
#: cannot smuggle a warmpool into the repo.
REPO_MARKERS: tuple[str, ...] = (".git", "pyproject.toml")

_EXT_RE = re.compile(r"^(\.[A-Za-z0-9_]+)*$")


def find_repo_root(start: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Return the outermost ancestor of ``start`` carrying a repo marker.

    ``start`` defaults to this package's directory. Returns ``None`` when no marker
    exists -- a vendored copy of the engine outside any repository has no tree to
    protect, and inventing one would refuse every warmpool in the host's``/tmp``.
    """
    here = Path(start).resolve() if start is not None else Path(__file__).resolve().parent
    if here.is_file():
        here = here.parent
    for candidate in (here, *here.parents):
        if any((candidate / marker).exists() for marker in REPO_MARKERS):
            return candidate
    return None


def assert_warmpool_root(
    root: Union[str, Path], repo_root: Optional[Union[str, Path]] = None
) -> Path:
    """Validate and normalise a warmpool root; refuse one inside the repo tree."""
    resolved = Path(root).expanduser().resolve()
    repo = (
        Path(repo_root).expanduser().resolve()
        if repo_root is not None
        else find_repo_root()
    )
    if repo is not None and (resolved == repo or repo in resolved.parents):
        raise PtrWarmpoolViolationError(
            "the warmpool root resolves inside the repository working tree "
            f"({resolved} is under {repo}); the warmpool is an isolated filespace",
            root=str(resolved),
            repo_root=str(repo),
        )
    return resolved


def default_root() -> Path:
    """The default warmpool root: ``$PTR_WARMPOOL_ROOT`` or the XDG cache dir."""
    override = os.environ.get("PTR_WARMPOOL_ROOT")
    if override:
        return assert_warmpool_root(override)
    cache = os.environ.get("XDG_CACHE_HOME")
    base = Path(cache).expanduser() if cache else Path.home() / ".cache"
    return assert_warmpool_root(base / "ptr-engine" / "warmpool")


def content_hash(body: bytes) -> str:
    """The content identity hash string, ``sha256:<64 hex>``."""
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _normalise_ext(ext: str) -> str:
    if not isinstance(ext, str):
        raise PtrExtensionError(f"ext must be a string, got {type(ext).__name__}")
    normalized = ext if not ext or ext.startswith(".") else "." + ext
    if not _EXT_RE.match(normalized):
        raise PtrExtensionError(
            f"ext {ext!r} is not a plain dotted suffix (e.g. '.txt')", ext=ext
        )
    return normalized


class BodyStore:
    """A content-addressed body store rooted at an isolated warmpool path."""

    def __init__(
        self,
        root: Union[str, Path],
        *,
        repo_root: Optional[Union[str, Path]] = None,
        create: bool = True,
    ) -> None:
        self.root = assert_warmpool_root(root, repo_root=repo_root)
        if create:
            self.root.mkdir(parents=True, exist_ok=True)

    # -- identity ---------------------------------------------------------
    @staticmethod
    def hash_of(body: bytes) -> str:
        return content_hash(body)

    def locator_for(self, body: bytes, ext: str = ".txt") -> str:
        """The store-relative path a body would occupy. Pure; touches no disk."""
        digest = hashlib.sha256(body).hexdigest()
        return f"{digest[:2]}/{digest}{_normalise_ext(ext)}"

    def path_of(self, ref: ResourceRef) -> Path:
        """Absolute path of a content identity, refusing a locator that escapes."""
        candidate = (self.root / ref.locator).resolve()
        if self.root not in candidate.parents:
            raise PtrStoreMissError(
                f"locator {ref.locator!r} escapes the warmpool root",
                locator=ref.locator,
            )
        return candidate

    def has(self, ref: ResourceRef) -> bool:
        try:
            return self.path_of(ref).is_file()
        except PtrStoreMissError:
            return False

    # -- read / write ------------------------------------------------------
    def put(self, body: bytes, *, ext: str = ".txt", pin: str = "") -> ResourceRef:
        """Store ``body`` once and return its content identity."""
        if isinstance(body, str):
            body = body.encode("utf-8")
        if not isinstance(body, (bytes, bytearray)):
            raise PtrExtensionError(
                f"body must be bytes, got {type(body).__name__}"  # pragma: no cover
            )
        body = bytes(body)
        digest = hashlib.sha256(body).hexdigest()
        ext = _normalise_ext(ext)
        locator = f"{digest[:2]}/{digest}{ext}"
        target = self.root / locator
        ref = ResourceRef(
            scheme="artifact", locator=locator, hash="sha256:" + digest, pin=pin
        )
        if target.is_file():
            if target.stat().st_size == len(body):
                return ref  # identical content, stored once
            raise PtrHashMismatchError(
                "a file already occupies this content address with a different size",
                locator=locator,
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".put-")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, target)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        return ref

    def get(self, ref: ResourceRef) -> bytes:
        """Read the bytes a content identity names, verifying the hash on read."""
        if not isinstance(ref, ResourceRef):
            raise PtrStoreMissError(
                "get() takes a ResourceRef (a resolved Reference), not "
                f"{type(ref).__name__}"
            )
        path = self.path_of(ref)
        if not path.is_file():
            raise PtrStoreMissError(
                f"no body at {ref.locator}", locator=ref.locator, hash=ref.hash
            )
        body = path.read_bytes()
        actual = hashlib.sha256(body).hexdigest()
        if "sha256:" + actual != ref.hash:
            raise PtrHashMismatchError(
                f"body at {ref.locator} hashes to sha256:{actual}, identity says {ref.hash}",
                locator=ref.locator,
                expected=ref.hash,
                actual="sha256:" + actual,
            )
        return body


__all__ = [
    "BodyStore",
    "content_hash",
    "default_root",
    "find_repo_root",
    "assert_warmpool_root",
    "REPO_MARKERS",
]
