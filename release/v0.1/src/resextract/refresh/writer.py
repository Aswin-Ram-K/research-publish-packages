"""Concurrent-writer detection — can an acceptance run trust a snapshot at all?

An acceptance run measures a target repository.  If somebody else is writing to
that repository at the same time, the measurement is noise: staleness judged
mid-write, a HEAD that moves between "before" and "after", files that change
under a copy.  This module makes the *presence of a writer* itself a measured,
reported fact, so a run must either find the target quiescent or explicitly opt
in to measuring a moving target.

Method: read HEAD + the tracked-file ``(size, mtime_ns)`` digest + the identity
of the untracked-but-*admitted* paths, sleep exactly ``window_s`` once, read all
three again.  A moved HEAD is ``head_moved``; otherwise a tracked file whose
``(size, mtime_ns)`` changed, a **new** untracked entry, or a change to the
identity of an **existing** untracked-but-admitted path is ``active_writer``;
otherwise ``quiescent``.  Nothing here raises: a git failure is recorded in
``note`` and the verdict falls back to what was observable.

Untracked-but-admitted paths (defect U7.2-1): git reports an existing untracked
directory as one ``?? dir/`` entry, so a write *inside* ``dir/`` grows no new
entry and used to read quiescent.  The candidate set is therefore derived from
:class:`resextract.kg.policy.TargetPolicy.admit` — the real admission predicate,
never a second ignore implementation — so only paths that matter are watched,
and ignored/noise directories (``.worktrees/`` above all) are never descended
into.  A bounded identity is computed on both sides of the window: a content
sha256 for small files, ``(size, mtime_ns)`` for files over the size cap.  The
number of watched paths and the bytes hashed are both capped, and every cap that
binds is recorded in the signal (``caps_hit``).

Known limits (NOT closed here — the caller must handle them):

* a writer that mutates a file **and restores it byte-identically** within the
  window is undetectable by any before/after comparison — the change simply is
  not there at either observation;
* a burst can begin **immediately after** the window closes: a quiescent verdict
  is evidence about the window, not a promise about the future.

That is why an acceptance run must use a **sealed window**: assert quiescence
before (:func:`assert_pinned_quiescent` over the untracked paths the docket
depends on) and re-verify HEAD *after* the copy — never check once.

Almost all git plumbing is reused from :mod:`resextract.refresh.staleness` —
``read_target_state`` for HEAD/branch/dirty, ``tracked_files`` plus
``IGNORE_DIR_PARTS``/``_is_ignored`` for the bounded tracked-file walk, and
``_git`` for the one extra porcelain read this module needs (untracked entries,
where the porcelain *code* matters, not just the path).  Nothing re-implements a
git invocation.  The walk only ever ``stat``s files ``git ls-files`` names and
drops ignored components, so ``.worktrees/``, ``node_modules/`` and the like are
never descended into — the file count is bounded by tracked files only.
"""

from __future__ import annotations

import hashlib
import os
import stat as stat_module
import time
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from resextract.refresh.staleness import (
    _git,
    _is_ignored,
    read_target_state,
    short_sha,
    tracked_files,
)

__all__ = [
    "DEFAULT_HASH_SIZE_CAP",
    "DEFAULT_MAX_FILES",
    "DEFAULT_MAX_UNTRACKED_BYTES",
    "DEFAULT_MAX_UNTRACKED_PATHS",
    "WORKER_VERDICTS",
    "MtimeSnapshot",
    "TargetBusyError",
    "UntrackedIdentity",
    "WriterSignal",
    "assert_pinned_quiescent",
    "assert_quiescent",
    "detect_concurrent_writer",
    "policy_for_target",
    "tracked_mtime_snapshot",
]

#: Verdict vocabulary.  Exactly these three strings ever appear in a signal.
WORKER_VERDICTS = ("quiescent", "active_writer", "head_moved")

#: Hard bound on the tracked files a single detection walks.
DEFAULT_MAX_FILES = 20_000

#: Files at or below this size are identity-checked by content sha256; larger
#: files fall back to ``(size, mtime_ns)`` and the sampling is recorded.
DEFAULT_HASH_SIZE_CAP = 1 << 20  # 1 MiB

#: Hard bound on the untracked-but-admitted paths a single detection watches.
DEFAULT_MAX_UNTRACKED_PATHS = 2_000

#: Hard bound on the total bytes a single detection reads to hash untracked paths.
DEFAULT_MAX_UNTRACKED_BYTES = 32 << 20  # 32 MiB

#: Prefix of a sibling-worktree directory under ``.worktrees/`` (e.g. ``run-1``).
WORKTREE_RUN_PREFIX = "run"

#: Cache of ``target_root -> TargetPolicy | None`` so config discovery costs once.
_POLICY_CACHE: dict[str, Any] = {}


# --------------------------------------------------------------------------- #
# signal
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class WriterSignal:
    """What the target did during one observation window."""

    verdict: str
    head_before: str | None
    head_after: str | None
    dirty_before: tuple[str, ...]
    dirty_after: tuple[str, ...]
    files_touched_in_window: int
    newest_mtime_utc: str | None
    worktree_dirs_present: int
    note: str
    path: str = ""
    untracked_watched: int = 0
    untracked_hashed: int = 0
    untracked_changed: tuple[str, ...] = ()
    caps_hit: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.verdict not in WORKER_VERDICTS:
            raise ValueError(
                f"verdict must be one of {WORKER_VERDICTS}, got {self.verdict!r}"
            )

    @property
    def quiescent(self) -> bool:
        return self.verdict == "quiescent"

    @property
    def head_moved(self) -> bool:
        return bool(
            self.head_before and self.head_after and self.head_before != self.head_after
        )

    @property
    def new_untracked(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.dirty_after) - set(self.dirty_before)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "verdict": self.verdict,
            "head_before": self.head_before,
            "head_before8": short_sha(self.head_before, 8),
            "head_after": self.head_after,
            "head_after8": short_sha(self.head_after, 8),
            "dirty_before": list(self.dirty_before),
            "dirty_after": list(self.dirty_after),
            "files_touched_in_window": self.files_touched_in_window,
            "newest_mtime_utc": self.newest_mtime_utc,
            "worktree_dirs_present": self.worktree_dirs_present,
            "note": self.note,
            "untracked_watched": self.untracked_watched,
            "untracked_hashed": self.untracked_hashed,
            "untracked_changed": list(self.untracked_changed),
            "caps_hit": list(self.caps_hit),
        }


class TargetBusyError(RuntimeError):
    """Raised by :func:`assert_quiescent` when the target is moving."""

    def __init__(self, signal: WriterSignal) -> None:
        self.signal = signal
        moved: list[str] = []
        if signal.head_before != signal.head_after:
            moved.append(
                f"HEAD moved {short_sha(signal.head_before, 8)} -> "
                f"{short_sha(signal.head_after, 8)}"
            )
        if signal.files_touched_in_window:
            moved.append(
                f"{signal.files_touched_in_window} tracked file(s) modified "
                f"within the window"
            )
        new_untracked = signal.new_untracked
        if new_untracked:
            moved.append(
                f"{len(new_untracked)} new untracked entr(ies) "
                f"(e.g. {new_untracked[0]!r})"
            )
        if signal.untracked_changed:
            moved.append(
                f"{len(signal.untracked_changed)} watched untracked path(s) changed "
                f"(e.g. {signal.untracked_changed[0]!r})"
            )
        if not moved:
            moved.append("the target could not be shown to be quiescent")
        super().__init__(
            f"target {signal.path or '?'} is not quiescent ({signal.verdict}): "
            + "; ".join(moved)
            + f"; newest tracked-file mtime {signal.newest_mtime_utc or 'unknown'}"
            + f"; note: {signal.note or 'none'}"
            + ". Pass allow_active=True to measure a moving target deliberately."
        )


# --------------------------------------------------------------------------- #
# bounded tracked-file walk (never descends into ignored/untracked trees)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class MtimeSnapshot:
    """``(size, mtime_ns)`` for the tracked files of one repository."""

    root: str
    stats: dict[str, tuple[int, int]] = field(default_factory=dict)
    total_tracked: int = 0
    truncated: bool = False
    newest_mtime_ns: int | None = None
    newest_path: str | None = None
    warnings: tuple[str, ...] = ()

    @property
    def count(self) -> int:
        return len(self.stats)

    @property
    def newest_mtime_utc(self) -> str | None:
        return _utc_from_ns(self.newest_mtime_ns)


def _utc_from_ns(ns: int | None) -> str | None:
    if ns is None:
        return None
    try:
        dt = datetime.fromtimestamp(ns / 1_000_000_000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):  # pragma: no cover - exotic
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def tracked_mtime_snapshot(
    target_path: str | os.PathLike[str], *, max_files: int = DEFAULT_MAX_FILES
) -> MtimeSnapshot:
    """Stat the tracked files only — bounded, and never a directory walk.

    The path list comes from ``git ls-files``, filtered through the staleness
    module's ignore machinery, so ``.worktrees/`` and ``node_modules/`` contents
    are excluded even if they were somehow tracked.  At most ``max_files``
    entries are stat'ed.
    """
    root = os.path.abspath(os.fspath(target_path))
    warnings: list[str] = []
    files = tracked_files(root)
    if not files:
        warnings.append(
            "git ls-files returned nothing (not a git repo, or an unreadable one): "
            "no tracked files were watched"
        )
    rels = [rel for rel in files if not _is_ignored(rel)]
    truncated = len(rels) > max_files
    if truncated:
        warnings.append(
            f"tracked file list bounded at {max_files} of {len(rels)} files; "
            f"files beyond the bound were not watched"
        )
        rels = rels[:max_files]

    stats: dict[str, tuple[int, int]] = {}
    newest_ns: int | None = None
    newest_path: str | None = None
    for rel in rels:
        full = os.path.join(root, *rel.split("/"))
        try:
            st = os.stat(full)
        except OSError as exc:
            warnings.append(f"cannot stat tracked file {rel!r}: {type(exc).__name__}")
            continue
        stats[rel] = (int(st.st_size), int(st.st_mtime_ns))
        if newest_ns is None or st.st_mtime_ns > newest_ns:
            newest_ns = int(st.st_mtime_ns)
            newest_path = rel

    return MtimeSnapshot(
        root=root,
        stats=stats,
        total_tracked=len(files),
        truncated=truncated,
        newest_mtime_ns=newest_ns,
        newest_path=newest_path,
        warnings=tuple(warnings),
    )


def _untracked(root: str | os.PathLike[str]) -> tuple[frozenset[str], str | None]:
    """The untracked (``??``) entries of ``root``; ``(set, error_or_None)``.

    Uses the staleness module's git runner and the same ignore filter; only the
    porcelain status *code* is inspected here, which ``read_target_state``
    discards when it merges modified and untracked paths into one list.

    Default porcelain reports an existing untracked directory as one ``dir/``
    entry, which is exactly the blind spot this module closes by enumerating
    inside admitted entries (see :func:`_untracked_candidates`).
    """
    rc, out, err = _git(root, "status", "--porcelain")
    if rc != 0:
        return frozenset(), f"git status --porcelain failed (rc={rc}): {err.strip() or 'no output'}"
    found: set[str] = set()
    for line in out.splitlines():
        if not line.startswith("??"):
            continue
        rel = line[3:].strip().strip('"')
        if rel and not _is_ignored(rel):
            found.add(rel.rstrip("/"))
    return frozenset(found), None


def _worktree_run_dirs(root: str | os.PathLike[str]) -> int:
    """Count ``.worktrees/run*`` directories — an observation, never logic.

    One ``scandir`` of ``.worktrees`` only: the directory is never entered, so
    its (hundreds of) live files cost nothing and are never touched.
    """
    worktrees = os.path.join(os.path.abspath(os.fspath(root)), ".worktrees")
    try:
        with os.scandir(worktrees) as entries:
            return sum(
                1
                for entry in entries
                if entry.name.startswith(WORKTREE_RUN_PREFIX)
                and entry.is_dir(follow_symlinks=False)
            )
    except OSError:
        return 0


# --------------------------------------------------------------------------- #
# policy discovery (admission decides which untracked paths matter)
# --------------------------------------------------------------------------- #


def _config_candidates() -> list[Path]:
    """Where ``targets.toml`` may live, nearest checkout first."""
    out: list[Path] = []
    env = os.environ.get("RESEXTRACT_TARGETS_CONFIG")
    if env:
        out.append(Path(env))
    for parent in Path(__file__).resolve().parents:
        cand = parent / "config" / "targets.toml"
        if cand.is_file():
            out.append(cand)
            break
    cwd_cand = Path.cwd() / "config" / "targets.toml"
    if cwd_cand.is_file():
        out.append(cwd_cand)
    seen: set[str] = set()
    unique: list[Path] = []
    for cand in out:
        key = str(cand)
        if key not in seen:
            seen.add(key)
            unique.append(cand)
    return unique


def policy_for_target(target_path: str | os.PathLike[str]) -> Any:
    """The configured :class:`TargetPolicy` for *target_path*, or ``None``.

    The raw ``path`` of every ``[targets.<slug>]`` table is compared to the
    resolved target **before** any policy is built, so discovering a policy for
    an unrelated temp repo never reads (or even resolves a predicate against) a
    live registered target.  Never raises.
    """
    try:
        root = Path(os.path.abspath(os.fspath(target_path))).resolve()
    except Exception:  # pragma: no cover - defensive
        return None
    key = str(root)
    if key in _POLICY_CACHE:
        return _POLICY_CACHE[key]
    policy = None
    for cfg in _config_candidates():
        try:
            data = tomllib.loads(cfg.read_text(encoding="utf-8"))
        except Exception:
            continue
        targets = data.get("targets")
        if not isinstance(targets, dict):
            continue
        for slug, block in targets.items():
            if not isinstance(block, dict) or not block.get("path"):
                continue
            try:
                declared = Path(str(block["path"])).resolve()
            except Exception:
                continue
            if declared != root:
                continue
            try:
                from resextract.kg.policy import TargetPolicy

                policy = TargetPolicy.from_config(cfg, str(slug))
            except Exception:
                policy = None
            _POLICY_CACHE[key] = policy
            return policy
    _POLICY_CACHE[key] = None
    return None


# --------------------------------------------------------------------------- #
# identity of untracked-but-admitted paths (defect U7.2-1)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class UntrackedIdentity:
    """A bounded identity for the untracked paths one detection watched."""

    root: str
    entries: dict[str, str] = field(default_factory=dict)
    watched: int = 0
    hashed: int = 0
    sampled: int = 0
    bytes_read: int = 0
    caps_hit: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def changed_from(self) -> list[str]:  # pragma: no cover - convenience
        return []


def _walk_untracked_dir(
    root: str, rel: str, *, limit: int, notes: list[str]
) -> list[str]:
    """Bounded listing *inside* one admitted untracked directory.

    Never follows symlinked directories and never enters an ignored component
    (``.worktrees/``, ``node_modules/``, …), so the sentinel trees stay uncounted.
    """
    out: list[str] = []
    stack = [rel]
    while stack and len(out) < limit:
        cur = stack.pop()
        full = os.path.join(root, *cur.split("/"))
        try:
            with os.scandir(full) as entries:
                for entry in entries:
                    child = f"{cur}/{entry.name}"
                    if _is_ignored(child):
                        continue
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                    except OSError:
                        continue
                    if is_dir:
                        stack.append(child)
                    else:
                        out.append(child)
                        if len(out) >= limit:
                            break
        except OSError as exc:
            notes.append(f"cannot read untracked dir {cur!r}: {type(exc).__name__}")
    return out


def _untracked_candidates(
    root: str,
    untracked: frozenset[str],
    *,
    policy: Any,
    pinned: tuple[str, ...],
    limit: int,
    notes: list[str],
) -> tuple[list[str], tuple[str, ...]]:
    """The untracked paths worth watching: admitted by policy, or pinned.

    Returns ``(candidates, caps_hit)``.  Pinned paths are watched even when the
    policy rejects them — the caller has declared them depended-upon — but the
    ignore/noise filter still applies so ``.worktrees/`` is never entered.
    """
    caps: list[str] = []
    pinned_norm: list[str] = []
    for raw in pinned:
        rel = str(raw).replace("\\", "/").strip().lstrip("/")
        while rel.startswith("./"):
            rel = rel[2:]
        if not rel or _is_ignored(rel):
            continue
        pinned_norm.append(rel)
    pinned_set = set(pinned_norm)

    found: list[str] = []
    seen: set[str] = set()

    def _offer(rel: str) -> None:
        if len(found) >= limit:
            if "max_untracked_paths" not in caps:
                caps.append("max_untracked_paths")
            return
        if rel in seen or _is_ignored(rel):
            return
        seen.add(rel)
        found.append(rel)

    for rel in sorted(untracked):
        if len(found) >= limit:
            if "max_untracked_paths" not in caps:
                caps.append("max_untracked_paths")
            break
        if _is_ignored(rel):
            continue
        full = os.path.join(root, *rel.split("/"))
        if os.path.isdir(full):
            for child in _walk_untracked_dir(root, rel, limit=limit, notes=notes):
                _offer(child)
        else:
            _offer(rel)
    for rel in pinned_norm:
        _offer(rel)
    if len(found) >= limit and "max_untracked_paths" not in caps:
        caps.append("max_untracked_paths")

    if policy is None:
        kept = [rel for rel in found if rel in pinned_set]
    else:
        kept: list[str] = []
        for rel in found:
            if rel in pinned_set:
                kept.append(rel)
                continue
            try:
                if policy.admit(rel).admitted:
                    kept.append(rel)
            except Exception as exc:  # never fatal
                notes.append(f"policy.admit({rel!r}) failed: {type(exc).__name__}")
    return kept[:limit], tuple(caps)


def _sha256_hex(path: str, *, limit: int) -> str | None:
    """sha256 of at most ``limit`` bytes (the file was size-checked first)."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            h.update(fh.read(limit))
    except OSError:
        return None
    return h.hexdigest()


def _untracked_identity(
    root: str,
    candidates: list[str],
    *,
    hash_size_cap: int,
    max_bytes: int,
    prior_caps: tuple[str, ...] = (),
) -> UntrackedIdentity:
    """Bounded identity: content sha256 for small files, ``(size, mtime_ns)`` else."""
    caps = list(prior_caps)
    warnings: list[str] = []
    entries: dict[str, str] = {}
    hashed = 0
    sampled = 0
    bytes_read = 0
    for rel in candidates:
        full = os.path.join(root, *rel.split("/"))
        try:
            st = os.stat(full)
        except OSError:
            entries[rel] = "missing"
            continue
        if not stat_module.S_ISREG(st.st_mode):
            entries[rel] = f"nondir:{st.st_size}:{st.st_mtime_ns}"
            continue
        size = int(st.st_size)
        if size > hash_size_cap:
            sampled += 1
            if "hash_size_cap" not in caps:
                caps.append("hash_size_cap")
            entries[rel] = f"stat:{size}:{st.st_mtime_ns}"
            continue
        if bytes_read + size > max_bytes:
            sampled += 1
            if "max_untracked_bytes" not in caps:
                caps.append("max_untracked_bytes")
            entries[rel] = f"stat:{size}:{st.st_mtime_ns}"
            continue
        digest = _sha256_hex(full, limit=size + 1)
        if digest is None:
            warnings.append(f"cannot hash untracked path {rel!r}")
            entries[rel] = f"stat:{size}:{st.st_mtime_ns}"
            continue
        entries[rel] = f"sha256:{digest}"
        hashed += 1
        bytes_read += size
    if sampled:
        warnings.append(
            f"{sampled} untracked path(s) identity-checked by (size, mtime_ns) only "
            f"(size cap {hash_size_cap} B / byte budget {max_bytes} B)"
        )
    if "max_untracked_paths" in caps:
        warnings.append(
            f"untracked path list bounded at {len(candidates)}: paths beyond the "
            f"bound were not watched"
        )
    return UntrackedIdentity(
        root=root,
        entries=entries,
        watched=len(entries),
        hashed=hashed,
        sampled=sampled,
        bytes_read=bytes_read,
        caps_hit=tuple(caps),
        warnings=tuple(warnings),
    )


# --------------------------------------------------------------------------- #
# detection
# --------------------------------------------------------------------------- #


def detect_concurrent_writer(
    target_path: str | os.PathLike[str],
    *,
    window_s: float = 5.0,
    max_files: int = DEFAULT_MAX_FILES,
    policy: Any = None,
    pinned: tuple[str, ...] | list[str] = (),
    hash_size_cap: int = DEFAULT_HASH_SIZE_CAP,
    max_untracked_paths: int = DEFAULT_MAX_UNTRACKED_PATHS,
    max_untracked_bytes: int = DEFAULT_MAX_UNTRACKED_BYTES,
) -> WriterSignal:
    """Observe ``target_path`` across one ``window_s`` window and classify it.

    Returns a :class:`WriterSignal` with verdict ``quiescent``, ``active_writer``
    or ``head_moved``.  Never raises, and never sleeps longer than ``window_s``
    (exactly one sleep, no polling loop).

    ``policy`` defaults to the configured policy for the target (if any); without
    one, only tracked files and *new* untracked entries are watched.  ``pinned``
    names untracked paths the caller declares depended-upon.
    """
    window = max(0.0, float(window_s))
    try:
        return _detect(
            os.path.abspath(os.fspath(target_path)),
            window=window,
            max_files=max_files,
            policy=policy,
            pinned=tuple(pinned),
            hash_size_cap=hash_size_cap,
            max_untracked_paths=max_untracked_paths,
            max_untracked_bytes=max_untracked_bytes,
        )
    except Exception as exc:  # defensive: this function's contract is "never raises"
        return WriterSignal(
            verdict="quiescent",
            head_before=None,
            head_after=None,
            dirty_before=(),
            dirty_after=(),
            files_touched_in_window=0,
            newest_mtime_utc=None,
            worktree_dirs_present=0,
            note=(
                f"detection failed with {type(exc).__name__}: {exc}; "
                f"no writer was observed, so the verdict is only what was observable"
            ),
            path=os.path.abspath(os.fspath(target_path)),
        )


def _detect(
    target: str,
    *,
    window: float,
    max_files: int,
    policy: Any = None,
    pinned: tuple[str, ...] = (),
    hash_size_cap: int = DEFAULT_HASH_SIZE_CAP,
    max_untracked_paths: int = DEFAULT_MAX_UNTRACKED_PATHS,
    max_untracked_bytes: int = DEFAULT_MAX_UNTRACKED_BYTES,
) -> WriterSignal:
    notes: list[str] = []

    if policy is None and not pinned:
        policy = policy_for_target(target)

    before = read_target_state(target)
    notes.extend(before.warnings)
    snap_before = tracked_mtime_snapshot(target, max_files=max_files)
    notes.extend(snap_before.warnings)
    untracked_before, untracked_err = _untracked(target)
    if untracked_err:
        notes.append(untracked_err)

    candidates, path_caps = _untracked_candidates(
        target,
        untracked_before,
        policy=policy,
        pinned=pinned,
        limit=max_untracked_paths,
        notes=notes,
    )
    if policy is None and not pinned:
        notes.append(
            "no target policy resolved: untracked-but-admitted paths were NOT watched "
            "(only tracked files and new untracked entries are signal)"
        )
    id_before = _untracked_identity(
        target,
        candidates,
        hash_size_cap=hash_size_cap,
        max_bytes=max_untracked_bytes,
        prior_caps=path_caps,
    )
    notes.extend(id_before.warnings)

    if window:
        time.sleep(window)

    after = read_target_state(target)
    notes.extend(after.warnings)
    snap_after = tracked_mtime_snapshot(target, max_files=max_files)
    notes.extend([w for w in snap_after.warnings if w not in snap_before.warnings])
    untracked_after, untracked_err_after = _untracked(target)
    if untracked_err_after and untracked_err_after != untracked_err:
        notes.append(untracked_err_after)
    id_after = _untracked_identity(
        target,
        candidates,
        hash_size_cap=hash_size_cap,
        max_bytes=max_untracked_bytes,
        prior_caps=path_caps,
    )

    touched: set[str] = set()
    for rel, stat_after in snap_after.stats.items():
        stat_before = snap_before.stats.get(rel)
        if stat_before is None or stat_before != stat_after:
            touched.add(rel)
    for rel in snap_before.stats:
        if rel not in snap_after.stats:
            touched.add(rel)
    files_touched = len(touched)

    new_untracked = untracked_after - untracked_before

    changed_untracked: set[str] = set()
    for rel in set(id_before.entries) | set(id_after.entries):
        if id_before.entries.get(rel) != id_after.entries.get(rel):
            changed_untracked.add(rel)
    changed_untracked_tuple = tuple(sorted(changed_untracked))

    head_before = before.head_sha
    head_after = after.head_sha
    if head_before and head_after and head_before != head_after:
        verdict = "head_moved"
    elif files_touched or new_untracked or changed_untracked:
        verdict = "active_writer"
    else:
        verdict = "quiescent"

    newest_ns = snap_after.newest_mtime_ns
    if newest_ns is None:
        newest_ns = snap_before.newest_mtime_ns
    newest_utc = _utc_from_ns(newest_ns)
    if snap_after.newest_path and snap_after.newest_mtime_ns is not None:
        notes.append(
            f"newest tracked file: {snap_after.newest_path} "
            f"@ {_utc_from_ns(snap_after.newest_mtime_ns)}"
        )
    for rel in changed_untracked_tuple[:10]:
        notes.append(
            f"watched untracked path changed: {rel} "
            f"({id_before.entries.get(rel, 'absent')} -> {id_after.entries.get(rel, 'absent')})"
        )

    observed = (
        f"window {window:g}s; HEAD {short_sha(head_before, 8)} -> {short_sha(head_after, 8)}; "
        f"{files_touched} tracked file(s) changed; "
        f"{len(new_untracked)} new untracked entr(ies); "
        f"{len(changed_untracked_tuple)} watched untracked path(s) changed; "
        f"{id_after.watched} untracked path(s) watched ({id_after.hashed} hashed, "
        f"{id_after.bytes_read} B read); "
        f"{snap_after.count} tracked file(s) watched "
        f"(of {snap_after.total_tracked} tracked)"
    )
    if id_after.caps_hit:
        observed += f"; caps hit: {', '.join(id_after.caps_hit)}"
    if before.head_sha is None or after.head_sha is None:
        observed += " [HEAD was not observable for the whole window]"

    return WriterSignal(
        verdict=verdict,
        head_before=head_before,
        head_after=head_after,
        dirty_before=tuple(before.dirty_paths),
        dirty_after=tuple(after.dirty_paths),
        files_touched_in_window=files_touched,
        newest_mtime_utc=newest_utc,
        worktree_dirs_present=_worktree_run_dirs(target),
        note="; ".join([observed, *notes]),
        path=target,
        untracked_watched=id_after.watched,
        untracked_hashed=id_after.hashed,
        untracked_changed=changed_untracked_tuple,
        caps_hit=id_after.caps_hit,
    )


def assert_quiescent(
    target_path: str | os.PathLike[str],
    *,
    window_s: float = 5.0,
    allow_active: bool = False,
    max_files: int = DEFAULT_MAX_FILES,
    policy: Any = None,
    pinned: tuple[str, ...] | list[str] = (),
    hash_size_cap: int = DEFAULT_HASH_SIZE_CAP,
    max_untracked_paths: int = DEFAULT_MAX_UNTRACKED_PATHS,
    max_untracked_bytes: int = DEFAULT_MAX_UNTRACKED_BYTES,
) -> WriterSignal:
    """Raise :class:`TargetBusyError` unless the target is quiescent.

    An acceptance run that wants to measure a moving target on purpose must pass
    ``allow_active=True``; the default makes silence impossible.
    """
    signal = detect_concurrent_writer(
        target_path,
        window_s=window_s,
        max_files=max_files,
        policy=policy,
        pinned=pinned,
        hash_size_cap=hash_size_cap,
        max_untracked_paths=max_untracked_paths,
        max_untracked_bytes=max_untracked_bytes,
    )
    if signal.verdict != "quiescent" and not allow_active:
        raise TargetBusyError(signal)
    return signal


def assert_pinned_quiescent(
    target_path: str | os.PathLike[str],
    pinned_paths: tuple[str, ...] | list[str],
    *,
    window_s: float = 5.0,
    allow_active: bool = False,
    max_files: int = DEFAULT_MAX_FILES,
    policy: Any = None,
    hash_size_cap: int = DEFAULT_HASH_SIZE_CAP,
    max_untracked_paths: int = DEFAULT_MAX_UNTRACKED_PATHS,
    max_untracked_bytes: int = DEFAULT_MAX_UNTRACKED_BYTES,
) -> WriterSignal:
    """Sealed window over the exact untracked paths a docket depends on.

    ``pinned_paths`` are identity-checked across the window whether or not the
    policy admits them (the caller has declared them depended-upon).  The returned
    signal carries ``head_before``/``head_after`` so the caller can **re-verify
    HEAD after** acting on the snapshot — that re-verification is the second half
    of the seal and is not optional (a burst can start after the window closes).
    """
    signal = detect_concurrent_writer(
        target_path,
        window_s=window_s,
        max_files=max_files,
        policy=policy,
        pinned=tuple(pinned_paths),
        hash_size_cap=hash_size_cap,
        max_untracked_paths=max_untracked_paths,
        max_untracked_bytes=max_untracked_bytes,
    )
    if signal.verdict != "quiescent" and not allow_active:
        raise TargetBusyError(signal)
    return signal
