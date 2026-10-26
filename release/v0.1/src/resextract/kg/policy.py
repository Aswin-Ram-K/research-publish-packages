"""Explicit, configurable and *asserted* admission policy for extraction targets.

Why this exists: the knowledge graph can only ever see what graphify's ignore
machinery admits, and a file that stops being admitted simply never appears as a
finding. Nothing downstream reports its absence. ``U1.5`` flagged exactly that
risk for ``<workspace>`` — untracked scratch that is
*not* gitignored, so graphify's real predicate admits it, and it holds the
densest publishable material in the repo. The decision (already made) is to
**admit it**, and to make that decision recorded, honoured and asserted so a
future ignore-rule or config change cannot drop it silently.

Discipline: this module is a **thin** layer over the real predicate. It never
re-lists ignore semantics; it imports ``graphify.detect``'s own
``ignored_predicate``, ``_is_noise_dir`` and ``_SKIP_FILES`` and reuses
``resextract.kg.ingest._walk`` for the directory walk, so a policy decision and
a graphify decision cannot drift apart.

Rules:

* admission starts from graphify's real predicate (``.graphifyignore`` +
  ``.gitignore`` chains + ``$GIT_DIR/info/exclude`` + the tracked-file
  exemption) and its noise/cache-dir pruning;
* config ``exclude`` globs may only **narrow** admission (admit -> reject);
* config ``include`` entries are documented intent. An entry that names a path
  graphify structurally prunes (``.git/``, ``.worktrees/``, ``node_modules/`` …)
  is a **widening attempt** and is refused with
  :class:`PolicyWideningError` — the predicate is not overridable from config;
* every decision carries a reason and a ``source``, so an exclusion is never
  mysterious;
* ``assert_present`` names repo-relative paths that MUST be admitted. A missing
  expected path is a violation too: the assertion documents intent that drifted.

Deterministic, offline, stdlib-only. A path that cannot be read or resolved is
recorded, never fatal.
"""

from __future__ import annotations

import fnmatch
import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from graphify import detect as _gdetect

__all__ = [
    "ADMISSION_SOURCES",
    "GRAPHIFY_SOURCES",
    "Admission",
    "AssertionResult",
    "PolicyAudit",
    "PolicyDiff",
    "PolicyError",
    "PolicyWideningError",
    "TargetPolicy",
    "policy_audit",
    "policy_diff",
]

#: Every ``Admission.source`` is one of these: an exclusion always names *why*.
ADMISSION_SOURCES = frozenset(
    {
        "graphify_predicate",
        "config_exclude",
        "config_assert",
        "noise_dir",
        "ignored_dir",
        "skip_file",
    }
)

#: Sources that delegate to graphify's own machinery (no local reimplementation).
GRAPHIFY_SOURCES = frozenset({"graphify_predicate", "noise_dir", "ignored_dir", "skip_file"})


class PolicyError(ValueError):
    """A target policy could not be loaded or is malformed."""


class PolicyWideningError(PolicyError):
    """Config tried to *widen* admission past graphify's predicate. Refused."""


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _norm_rel(value: str | os.PathLike[str]) -> str:
    """Normalise a repo-relative path to a clean POSIX string (no leading '/').

    Never raises: a value that cannot be stringified is turned into ``str()``.
    """
    try:
        text = os.fspath(value)
    except TypeError:
        text = str(value)
    if isinstance(text, bytes):                       # pragma: no cover - defensive
        text = text.decode("utf-8", "replace")
    text = text.replace("\\", "/").strip()
    while text.startswith("./"):
        text = text[2:]
    text = text.lstrip("/")
    while text.endswith("/") and len(text) > 1:
        text = text[:-1]
    return text


def _glob_match(rel: str, pattern: str) -> bool:
    """gitignore-ish glob match of a repo-relative path against *pattern*.

    Supports ``**`` (any depth), ``*``/``?`` (within one path segment) and a
    bare-basename pattern such as ``*.min.js``. Matching is anchored at the
    repo root when the pattern contains a ``/``.
    """
    pat = _norm_rel(pattern)
    if not pat:
        return False
    if "**" in pat:
        rx = ""
        i = 0
        while i < len(pat):
            if pat.startswith("**", i):
                rx += ".*"
                i += 2
                if i < len(pat) and pat[i] == "/":
                    i += 1
            elif pat[i] == "*":
                rx += "[^/]*"
                i += 1
            elif pat[i] == "?":
                rx += "[^/]"
                i += 1
            else:
                rx += re.escape(pat[i])
                i += 1
        try:
            return re.fullmatch(rx, rel) is not None
        except re.error:                              # pragma: no cover - defensive
            return False
    if "/" in pat:
        return fnmatch.fnmatchcase(rel, pat)
    return fnmatch.fnmatchcase(Path(rel).name, pat)


_PRED_CACHE: dict[str, Callable[[Path], bool]] = {}


def _predicate_for(root: Path) -> Callable[[Path], bool]:
    """graphify's real ignore predicate for *root* (built once per root)."""
    key = str(root)
    predicate = _PRED_CACHE.get(key)
    if predicate is None:
        predicate = _gdetect.ignored_predicate(Path(key), extra_excludes=None, gitignore=True)
        _PRED_CACHE[key] = predicate
    return predicate


def _skip_files() -> frozenset[str]:
    return frozenset(getattr(_gdetect, "_SKIP_FILES", frozenset()))


# --------------------------------------------------------------------------- #
# Decision types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Admission:
    """One admission decision: the verdict, *why*, and which layer decided it."""

    admitted: bool
    reason: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {"admitted": self.admitted, "reason": self.reason, "source": self.source}


@dataclass
class AssertionResult:
    """Whether one ``assert_present`` path exists and is actually admitted."""

    path: str
    expected_admitted: bool
    actual: bool
    size_bytes: int
    ok: bool
    exists: bool = True
    source: str = ""
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "expected_admitted": self.expected_admitted,
            "actual": self.actual,
            "admitted": self.actual,
            "size_bytes": self.size_bytes,
            "bytes": self.size_bytes,
            "ok": self.ok,
            "exists": self.exists,
            "source": self.source,
            "reason": self.reason,
        }


@dataclass
class PolicyAudit:
    """The whole-target result: who was admitted, who was rejected and why."""

    target_root: str = ""
    admitted: dict[str, int] = field(default_factory=dict)          # relpath -> bytes
    rejected_by_reason: dict[str, int] = field(default_factory=dict)  # source -> count
    assertions: list[AssertionResult] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    rejected: dict[str, Admission] = field(default_factory=dict)     # relpath -> decision
    unreadable: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_root": self.target_root,
            "admitted": dict(sorted(self.admitted.items())),
            "rejected_by_reason": dict(sorted(self.rejected_by_reason.items())),
            "assertions": [a.as_dict() for a in self.assertions],
            "violations": list(self.violations),
            "rejected": {k: v.as_dict() for k, v in sorted(self.rejected.items())},
            "unreadable": sorted(self.unreadable),
            "notes": list(self.notes),
        }


@dataclass
class PolicyDiff:
    """Which paths changed admission status between two policies."""

    before: str = ""
    after: str = ""
    changed: dict[str, tuple[bool, bool]] = field(default_factory=dict)
    newly_admitted: list[str] = field(default_factory=list)
    newly_rejected: list[str] = field(default_factory=list)
    added_excludes: list[str] = field(default_factory=list)
    removed_excludes: list[str] = field(default_factory=list)
    added_asserts: list[str] = field(default_factory=list)
    removed_asserts: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "before": self.before,
            "after": self.after,
            "changed": {k: list(v) for k, v in sorted(self.changed.items())},
            "newly_admitted": list(self.newly_admitted),
            "newly_rejected": list(self.newly_rejected),
            "added_excludes": list(self.added_excludes),
            "removed_excludes": list(self.removed_excludes),
            "added_asserts": list(self.added_asserts),
            "removed_asserts": list(self.removed_asserts),
        }


# --------------------------------------------------------------------------- #
# The policy
# --------------------------------------------------------------------------- #
@dataclass
class TargetPolicy:
    """Admission policy for one extraction target.

    ``path`` is the target root; ``include`` documents the intent; ``exclude``
    globs narrow admission; ``assert_present`` names paths that must be admitted.
    """

    slug: str
    path: str
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    assert_present: list[str] = field(default_factory=list)
    config_path: str = ""
    read_only: bool = False
    widen_attempts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    # -- construction ------------------------------------------------------- #
    @classmethod
    def from_config(cls, path: str | os.PathLike[str], slug: str, *, strict: bool = True) -> "TargetPolicy":
        """Load ``[targets.<slug>]`` from a TOML config.

        With ``strict=True`` (default) a config whose ``include`` entries try to
        re-admit a path graphify prunes raises :class:`PolicyWideningError`.
        """
        cfg = Path(path)
        try:
            with cfg.open("rb") as fh:
                data = tomllib.load(fh)
        except FileNotFoundError as exc:
            raise PolicyError(f"target config not found: {cfg}") from exc
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise PolicyError(f"target config {cfg} could not be read: {exc!r}") from exc

        targets = data.get("targets")
        if not isinstance(targets, dict):
            raise PolicyError(f"{cfg}: no [targets.*] tables")
        block = targets.get(slug)
        if not isinstance(block, dict):
            raise PolicyError(f"{cfg}: no [targets.{slug}] table")

        def _strs(key: str) -> list[str]:
            value = block.get(key) or []
            if isinstance(value, str):
                return [value]
            if not isinstance(value, (list, tuple)):
                raise PolicyError(f"{cfg}: [targets.{slug}].{key} must be a list of strings")
            return [str(v) for v in value]

        policy = cls(
            slug=slug,
            path=str(block.get("path", "")),
            include=_strs("include"),
            exclude=_strs("exclude"),
            assert_present=_strs("assert_present"),
            config_path=str(cfg),
            read_only=bool(block.get("read_only", False)),
        )
        if not policy.path:
            raise PolicyError(f"{cfg}: [targets.{slug}].path is empty")
        policy.widen_attempts = policy._detect_widen_attempts()
        if strict and policy.widen_attempts:
            raise PolicyWideningError(policy._widen_message())
        return policy

    # -- properties --------------------------------------------------------- #
    @property
    def root(self) -> Path:
        p = Path(self.path)
        if not p.is_absolute():
            p = Path.cwd() / p
        return p.resolve()

    @property
    def asserted(self) -> frozenset[str]:
        return frozenset(_norm_rel(p) for p in self.assert_present)

    def _widen_message(self) -> str:
        joined = "; ".join(self.widen_attempts)
        return (
            f"[targets.{self.slug}] include would WIDEN admission past graphify's predicate — refused "
            f"(config may narrow admission, never widen it): {joined}"
        )

    def _include_literal(self, entry: str) -> str:
        """The literal directory prefix of an ``include`` entry (globs dropped)."""
        text = _norm_rel(entry)
        for i, ch in enumerate(text):
            if ch in "*?[":
                text = text[:i]
                break
        return text.strip("/")

    def _detect_widen_attempts(self) -> list[str]:
        """Refuse config that tries to re-admit something graphify prunes."""
        root = self.root
        predicate = _predicate_for(root)
        attempts: list[str] = []
        for entry in self.include:
            literal = self._include_literal(entry)
            if not literal:
                continue
            head = literal.split("/")[0]
            try:
                if _gdetect._is_noise_dir(head, root) or _gdetect._is_noise_dir(literal, root):
                    attempts.append(
                        f"{entry!r}: refused — graphify prunes {head!r} as a noise/cache dir "
                        "(_is_noise_dir); config may narrow admission, never widen it"
                    )
                    continue
                if predicate(root / literal) or predicate(root / head):
                    attempts.append(
                        f"{entry!r}: refused — graphify's predicate (.gitignore/.graphifyignore) "
                        f"excludes {literal!r}; config may narrow admission, never widen it"
                    )
            except Exception as exc:                  # pragma: no cover - defensive
                attempts.append(f"{entry!r}: refused — could not be evaluated ({exc!r})")
        return attempts

    # -- the decision ------------------------------------------------------- #
    def admit(self, relpath: str | os.PathLike[str]) -> Admission:
        """Decide one repo-relative (or absolute) path. Never raises."""
        rel = _norm_rel(relpath)
        try:
            return self._admit(rel)
        except Exception as exc:                      # never fatal: record it
            return Admission(
                False,
                f"could not evaluate {rel!r} against graphify's predicate: {exc!r}",
                "graphify_predicate",
            )

    def _admit(self, rel: str) -> Admission:
        if not rel:
            return Admission(False, "empty path", "graphify_predicate")

        root = self.root
        parts = rel.split("/")
        name = parts[-1]

        if name in _skip_files():
            return Admission(
                False,
                f"{name!r} is a graphify skip file (_SKIP_FILES: lockfiles and manifests)",
                "skip_file",
            )

        # 1. graphify's real machinery, never reimplemented here.
        predicate = _predicate_for(root)
        parent = root
        for comp in parts[:-1]:
            if _gdetect._is_noise_dir(comp, parent):
                return Admission(
                    False,
                    f"directory {comp!r} pruned by graphify's noise/cache rules (_is_noise_dir)",
                    "noise_dir",
                )
            if predicate(parent / comp):
                return Admission(
                    False,
                    f"directory {comp!r} excluded by graphify's predicate "
                    "(.gitignore/.graphifyignore/info-exclude)",
                    "ignored_dir",
                )
            parent = parent / comp

        if predicate(root / rel.replace("/", os.sep)):
            return Admission(
                False,
                "excluded by graphify's predicate (.graphifyignore + .gitignore chains + "
                "$GIT_DIR/info/exclude + git tracked-file exemption)",
                "graphify_predicate",
            )

        # 2. config may only NARROW: an excluded glob turns an admit into a reject.
        for pattern in self.exclude:
            if _glob_match(rel, pattern):
                return Admission(
                    False,
                    f"excluded by [targets.{self.slug}].exclude glob {pattern!r} "
                    "(config may narrow admission, never widen it)",
                    "config_exclude",
                )

        # 3. positive confirmation for asserted paths.
        if rel in self.asserted:
            return Admission(
                True,
                f"admitted by graphify's predicate and confirmed by assert_present entry {rel!r}",
                "config_assert",
            )
        return Admission(True, "admitted by graphify's predicate", "graphify_predicate")

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "path": self.path,
            "config_path": self.config_path,
            "read_only": self.read_only,
            "include": list(self.include),
            "exclude": list(self.exclude),
            "assert_present": list(self.assert_present),
            "widen_attempts": list(self.widen_attempts),
            "notes": list(self.notes),
        }


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
def _missing_expected(rel: str, root: Path) -> str:
    return (
        f"missing_expected: asserted path {rel!r} does not exist under {root} — "
        "violation: the assertion documents intent that has drifted"
    )


def _not_admitted(rel: str, size: int, adm: Admission) -> str:
    return (
        f"asserted path {rel!r} EXISTS ({size} bytes) but is NOT admitted "
        f"({adm.source}: {adm.reason}) — violation: the corpus would SILENTLY lose it"
    )


def policy_audit(
    target_root: str | os.PathLike[str],
    policy: TargetPolicy,
    *,
    cap_files: int = 200_000,
) -> PolicyAudit:
    """Audit *target_root* under *policy*: admitted bytes, rejections, assertions.

    Walks with ``resextract.kg.ingest._walk`` — the same graphify predicate,
    noise-dir pruning and skip-file logic the real ingest uses — then applies the
    policy's narrowing excludes. Never raises: unreadable paths are recorded.
    """
    audit = PolicyAudit()
    try:
        root = Path(target_root).resolve()
    except Exception as exc:                          # pragma: no cover - defensive
        audit.notes.append(f"target root could not be resolved: {exc!r}")
        return audit
    audit.target_root = str(root)
    audit.notes.append(
        "admission decisions reuse graphify.detect.ignored_predicate/_is_noise_dir/_SKIP_FILES "
        "via resextract.kg.ingest._walk; config excludes can only narrow"
    )

    def _bump(source: str) -> None:
        audit.rejected_by_reason[source] = audit.rejected_by_reason.get(source, 0) + 1

    if not root.is_dir():
        audit.notes.append(f"not a directory: {root}")
        return audit

    try:
        from .ingest import _walk
    except Exception as exc:                          # pragma: no cover - defensive
        audit.notes.append(f"could not import the shared walk: {exc!r}")
        return audit

    seen = 0
    try:
        walked: Iterable[tuple[Path, str]] = _walk(root, gitignore=True, extra_excludes=None)
    except Exception as exc:                          # pragma: no cover - defensive
        audit.notes.append(f"walk could not be built: {exc!r}")
        return audit

    for path, kind in walked:
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:                            # pragma: no cover - defensive
            rel = str(path)
        if kind == "file":
            seen += 1
            if seen > cap_files:
                audit.notes.append(f"file cap reached: audit stopped after cap_files={cap_files}")
                break
            decision = policy.admit(rel)
            if decision.admitted:
                try:
                    audit.admitted[rel] = path.stat().st_size
                except OSError:
                    audit.admitted[rel] = 0
                    audit.unreadable.append(rel)
            else:
                audit.rejected[rel] = decision
                _bump(decision.source)
        elif kind in ("noise_dir", "ignored_dir", "skip_file"):
            source = {"noise_dir": "noise_dir", "ignored_dir": "ignored_dir", "skip_file": "skip_file"}[kind]
            reason = {
                "noise_dir": "cache/vendor directory pruned by graphify's noise rules (_is_noise_dir); never walked",
                "ignored_dir": "directory excluded by graphify's predicate; never walked",
                "skip_file": "graphify skip file (_SKIP_FILES)",
            }[kind]
            audit.rejected[rel.rstrip("/") + "/"] = Admission(False, reason, source)
            _bump(source)
        elif kind == "ignored_file":
            decision = policy.admit(rel)
            if decision.admitted:                     # pragma: no cover - defensive
                decision = Admission(False, "excluded by graphify's predicate", "graphify_predicate")
            audit.rejected[rel] = decision
            _bump(decision.source)
        elif kind == "unreadable":
            audit.unreadable.append(rel)
        # "symlink" / "sensitive": not admission decisions; graphify's own policy,
        # recorded in notes by ingest.coverage_audit rather than claimed here.

    for raw in policy.assert_present:
        rel = _norm_rel(raw)
        absolute = root / rel.replace("/", os.sep)
        try:
            exists = absolute.exists()
        except OSError:
            exists = False
        size = -1
        decision = Admission(False, "path does not exist", "graphify_predicate")
        if exists:
            try:
                size = absolute.stat().st_size
            except OSError:
                size = 0
                audit.unreadable.append(rel)
            if rel in audit.admitted:
                decision = policy.admit(rel)
            else:
                decision = audit.rejected.get(rel) or policy.admit(rel)
        admitted_now = rel in audit.admitted
        if not exists:
            audit.violations.append(_missing_expected(rel, root))
        elif not admitted_now:
            audit.violations.append(_not_admitted(rel, size, decision))
        audit.assertions.append(
            AssertionResult(
                path=rel,
                expected_admitted=True,
                actual=admitted_now,
                size_bytes=size,
                ok=bool(exists and admitted_now),
                exists=exists,
                source=decision.source,
                reason=decision.reason,
            )
        )

    if audit.unreadable:
        audit.notes.append(f"{len(audit.unreadable)} unreadable path(s) recorded (not fatal)")
    if not audit.violations:
        audit.notes.append("assert_present: every asserted path exists and is admitted")
    audit.rejected_by_reason = dict(sorted(audit.rejected_by_reason.items()))
    return audit


def policy_diff(
    before: TargetPolicy,
    after: TargetPolicy,
    *,
    paths: Iterable[str] | None = None,
) -> PolicyDiff:
    """Report which paths changed admission status between two policies.

    *paths* is the universe to test (defaults to both policies' assert_present
    lists). Intended for reviewing a config change before it is applied.
    """
    if paths is None:
        universe = sorted(set(before.assert_present) | set(after.assert_present))
    else:
        universe = [_norm_rel(p) for p in paths]
    diff = PolicyDiff(before=before.config_path or before.slug, after=after.config_path or after.slug)
    for raw in universe:
        rel = _norm_rel(raw)
        was = before.admit(rel).admitted
        now = after.admit(rel).admitted
        if was != now:
            diff.changed[rel] = (was, now)
            (diff.newly_admitted if now else diff.newly_rejected).append(rel)
    diff.added_excludes = [p for p in after.exclude if p not in before.exclude]
    diff.removed_excludes = [p for p in before.exclude if p not in after.exclude]
    diff.added_asserts = [p for p in after.assert_present if p not in before.assert_present]
    diff.removed_asserts = [p for p in before.assert_present if p not in after.assert_present]
    return diff
