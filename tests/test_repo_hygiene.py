"""Repository-hygiene guard: ``.gitignore`` semantics and generated artifacts.

Why this test exists
--------------------
``.gitignore`` line 3 used to be the *unanchored* rule ``dockets/``, which
matches a directory named ``dockets`` at **any depth**.  That silently swallowed
the fixture tree ``tests/fixtures/dashboard-store/dockets/**``, so those
ok-docket/broken-docket fixtures were untracked and simply absent on a fresh
clone -- a clone behaved differently from the working tree.  This module pins
the *semantics* of the ignore rules rather than their text, so re-introducing an
unanchored rule fails loudly and **names the offending rule**.

Method
------
Assertions shell out to ``git check-ignore``: ``--quiet`` for the boolean case
and ``-v`` to name the matching rule and line.  The rules are not re-parsed by
hand -- git is the authority on its own matching.  ``--no-index`` makes a probe
independent of whether the path happens to be tracked.  If ``git`` is missing,
or the checkout is not a git work tree, every test skips with a clear reason.

Red -> green transcript
-----------------------
Reverting ``.gitignore`` to its pre-fix, unanchored form re-introduces the bug
and this guard fails, naming the rule::

    $ sha256sum .gitignore          # unanchored form
    a1fd0ba9f7a18f2cdd2d07eafb1594f791a19deac78db8096f46cccd04de5696
    $ .venv/bin/python -m pytest tests/test_repo_hygiene.py -q
    E  AssertionError: tests/fixtures/dashboard-store/dockets/ok-docket is
       ignored by rule '.gitignore:3:dockets/\\ttests/fixtures/dashboard-store/dockets/ok-docket';
       an unanchored 'dockets/' rule swallows the test fixture tree and a fresh
       clone will not have it
    FAILED tests/test_repo_hygiene.py::test_fixture_dockets_tree_is_not_ignored[tests/fixtures/dashboard-store/dockets/ok-docket]
    FAILED tests/test_repo_hygiene.py::test_fixture_dockets_tree_is_not_ignored[tests/fixtures/dashboard-store/dockets/broken-docket]
    FAILED tests/test_repo_hygiene.py::test_root_dockets_is_still_ignored
    FAILED tests/test_repo_hygiene.py::test_nested_state_component_is_not_ignored
    FAILED tests/test_repo_hygiene.py::test_generated_artifacts_are_not_tracked[...state.sqlite]
    FAILED tests/test_repo_hygiene.py::test_generated_artifacts_are_not_tracked[...state.sqlite-wal]
    FAILED tests/test_repo_hygiene.py::test_generated_artifacts_are_not_tracked[...state.sqlite-shm]
    FAILED tests/test_repo_hygiene.py::test_generated_artifacts_are_ignored_on_disk[...state.sqlite]
    FAILED tests/test_repo_hygiene.py::test_generated_artifacts_are_ignored_on_disk[...state.sqlite-wal]
    FAILED tests/test_repo_hygiene.py::test_generated_artifacts_are_ignored_on_disk[...state.sqlite-shm]
    10 failed, 1 passed in 0.04s

(The red run predates ``git rm --cached``, which is why the three
``are_not_tracked`` cases fail there too.)

With the fix restored -- and the generated DB + sidecars untracked -- the guard
passes::

    $ sha256sum .gitignore          # fixed form
    bf267002a8b3f0911d62fffe6568217481e330204c9b2eec7ac84167044f6ee7
    $ .venv/bin/python -m pytest tests/test_repo_hygiene.py -q
    ...........                                                              [100%]
    11 passed in 0.02s

sha256(``.gitignore``): before (unanchored) = ``a1fd0ba9f7a18f2cdd2d07eafb1594f791a19deac78db8096f46cccd04de5696``
                         after  (fixed)      = ``bf267002a8b3f0911d62fffe6568217481e330204c9b2eec7ac84167044f6ee7``

U8.74 addendum -- the ``**/*.tmp`` rule
--------------------------------------
``U8.70`` committed the global ``**/*.tmp`` rule (``.gitignore:41``, checkpoint 4)
after ``U8.67``'s staging rehearsal found that root-anchored ``/state/`` never
reached a root-level or source-tree ``*.tmp``.  The rule was present but nothing
tested it, so nothing stopped it being deleted again.  Section 5 pins it two ways
so the guard is about *behaviour* rather than a snapshot of one line:

1. ``git check-ignore`` probes -- git is the authority on its own matching --
   at three depths, each deliberately **outside ``state/**`` so the assertion
   cannot be satisfied transitively by ``/state/``.
2. a parse of the **real** ``.gitignore`` asserting that a rule whose trailing
   component is a global ``*.tmp`` glob exists.  This survives a change of the
   exact matching mechanism (``**/*.tmp`` vs ``*.tmp``) and it is what makes the
   red cycle cheap: ``U874_GITIGNORE`` points the parse at a mutated copy under
   ``state/verify/U8.74/`` instead of the committed file, so nothing on disk has
   to change to prove the guard can fail.

Section 5 also re-asserts the ``dockets/**`` deliverable guard -- an
already-true property of the root-anchored ``/dockets/`` rule -- at the extra
path the build's own smoke run produces.

U8.76 addendum -- the SQLite sidecar rules
----------------------------------------
``U8.74`` handed up the same "un-anchored-by-design" treatment for the sqlite
sidecar rules ``*.sqlite-wal`` / ``*.sqlite-shm`` / ``*.sqlite-journal``
(``.gitignore:20-22``).  Section 6 checks them the same two ways.

**Verdict for U8.76: nothing was broken.**  All three rules are already written
unanchored (no leading ``/``, no directory component), i.e. *global by design*,
and behave that way in the repo as committed -- ``git check-ignore --no-index``
ignores a sidecar at the repository root *and* several directories deep
(``orchestration/units/state.sqlite-shm``, ``src/resextract/state.sqlite-journal``),
with the match attributed to ``.gitignore:20/21/22`` and not to a parent-directory
rule.  So no ``.gitignore`` edit was made and no root-anchored form exists to
replace; what was missing was *coverage*, so section 6 adds the guard.  Without
these tests nothing would stop someone "tidying" the three global rules into
root-anchored ones and silently un-ignoring a sidecar that lives next to a
database outside ``state/``.

One deliberate scope limit: **``state/state.sqlite`` is not covered or named by
anything added here.**  Whether the root-level DB itself should be versioned is
an open decision for the user (the same class of open question recorded above for
``/dockets/``), so section 6 asserts the *sidecar suffix* rules and nothing about
the database file.
"""

from __future__ import annotations

import fnmatch
import hashlib
import os
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path, PurePosixPath

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Real paths in the fixture tree that the unanchored ``dockets/`` rule swallowed.
FIXTURE_DOCKET_PATHS = [
    "tests/fixtures/dashboard-store/dockets/ok-docket",
    "tests/fixtures/dashboard-store/dockets/broken-docket",
]
# Generated artifacts that must never be tracked.
GENERATED_ARTIFACTS = [
    "tests/fixtures/dashboard-store/state.sqlite",
    "tests/fixtures/dashboard-store/state.sqlite-wal",
    "tests/fixtures/dashboard-store/state.sqlite-shm",
]


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _git_in(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="module", autouse=True)
def _require_git() -> None:
    if shutil.which("git") is None:
        pytest.skip("git is not available on PATH; cannot test ignore semantics")
    probe = _git("rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        pytest.skip("not inside a git work tree; cannot test ignore semantics")


def is_ignored(path: str) -> bool:
    """True if git considers ``path`` ignored (index status ignored).

    U8.76: the probe runs in the real repo, unless the ``U874_GITIGNORE`` seam
    (defined below, section 5) points it at a mutated copy -- see
    ``_check_ignore_cwd``.
    """
    return _git("check-ignore", "--quiet", "--no-index", "--", path, cwd=_check_ignore_cwd()).returncode == 0


def ignored_by(path: str) -> str:
    """The rule that ignores ``path`` (``.gitignore:LINE:pattern``), or ``""``."""
    result = _git("check-ignore", "-v", "--no-index", "--", path, cwd=_check_ignore_cwd())
    if result.returncode != 0:
        return ""
    # ``-v`` prints "<source>:<linenum>:<pattern>\t<pathname>".
    line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    return line.split("\t", 1)[0]


# --------------------------------------------------------------------------- #
# 1. the fixture tree must be visible to git (a clone would carry it)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", FIXTURE_DOCKET_PATHS)
def test_fixture_dockets_tree_is_not_ignored(path: str) -> None:
    rule = ignored_by(path)
    assert not is_ignored(path), (
        f"{path} is ignored by rule {rule!r}; an unanchored 'dockets/' rule "
        "swallows the test fixture tree and a fresh clone will not have it"
    )


# --------------------------------------------------------------------------- #
# 2. the real top-level dockets/ must stay ignored (current behaviour, preserved)
# --------------------------------------------------------------------------- #
# U8.74: the extra path is the one the build's own smoke run assembles, which is
# what keeps the deliverable directory out of commits.
DOCKET_DELIVERABLE_PATHS = [
    "dockets/example-docket/MANIFEST.json",
    "dockets/_smoke/MANIFEST.json",
]


@pytest.mark.parametrize("path", DOCKET_DELIVERABLE_PATHS)
def test_root_dockets_is_still_ignored(path: str) -> None:
    assert is_ignored(path), f"{path} should be ignored by the root-anchored rule"
    rule = ignored_by(path)
    assert rule.endswith(":/dockets/"), (
        f"expected the root-anchored '/dockets/' rule to match, got {rule!r}"
    )


# --------------------------------------------------------------------------- #
# 3. state/ is root-only: a nested "state" component must not be swallowed
# --------------------------------------------------------------------------- #
def test_root_state_is_ignored() -> None:
    assert is_ignored("state/state.sqlite"), "root state/ must stay ignored"


def test_nested_state_component_is_not_ignored() -> None:
    # No nested "state/" directory currently exists, so probe a synthetic path
    # under a *real* fixture root: this proves the rule no longer matches at any
    # depth, which is exactly the failure mode that hit dockets/.
    nested = "tests/fixtures/dashboard-store/state/runs.sqlite"
    rule = ignored_by(nested)
    assert not is_ignored(nested), (
        f"{nested} is ignored by rule {rule!r}; an unanchored 'state/' rule "
        "matches a 'state' component at any depth"
    )


# --------------------------------------------------------------------------- #
# 4. generated DB + SQLite sidecars must not be tracked
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", GENERATED_ARTIFACTS)
def test_generated_artifacts_are_not_tracked(path: str) -> None:
    tracked = _git("ls-files", "--error-unmatch", "--", path)
    assert tracked.returncode != 0, (
        f"{path} is tracked; generated SQLite artifacts (and their -wal/-shm "
        "sidecars) must never be committed -- they can silently disagree with "
        "the generator in tests/fixtures/dashboard-store/build.py"
    )
    listed = _git("ls-files", "--", path).stdout.strip()
    assert listed == "", f"{path} still appears in the index: {listed!r}"


@pytest.mark.parametrize("path", GENERATED_ARTIFACTS)
def test_generated_artifacts_are_ignored_on_disk(path: str) -> None:
    # They stay on disk (untracking is not deletion); ignoring them keeps a
    # stale local copy from showing up as untracked noise.
    assert is_ignored(path), f"{path} is on disk but not ignored by any rule"


# --------------------------------------------------------------------------- #
# 5. U8.74: **/*.tmp is ignored at any depth (global by design, U8.70 ckpt 4)
# --------------------------------------------------------------------------- #
# Chosen *outside* state/** on purpose.  /state/ (line 7) already ignores
# everything beneath it, so a probe placed under state/ would stay green even if
# the **/*.tmp rule were deleted.  Each path below is ignored *only* because of
# the *.tmp rule -- proven by test_tmp_rule_is_not_inherited_from_an_ignored_parent.
TMP_PATHS = [
    "note.tmp",  # repo root: editor scratch, the gap /state/ never reached
    "src/resextract/build.tmp",  # spill inside the source tree
    "orchestration/units/scan.tmp",  # a hand-written dir with no rule of its own
]

# Environment seam for the gitignore parse: point it at a copy of .gitignore
# with the *.tmp rule removed to watch the structural assertion go red, without
# editing the committed file.  Unset -> the repo's real .gitignore.
GITIGNORE_OVERRIDE_ENV = "U874_GITIGNORE"


def _gitignore_under_test() -> Path:
    override = os.environ.get(GITIGNORE_OVERRIDE_ENV, "").strip()
    return Path(override) if override else REPO_ROOT / ".gitignore"


def _effective_rule_lines(text: str) -> list[str]:
    """Non-comment, non-blank lines of ``text``, stripped."""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _tmp_rule_patterns(lines: Iterable[str]) -> list[tuple[str, str]]:
    """``(rule, pattern)`` for rules whose last component globs ``*.tmp`` files."""
    found: list[tuple[str, str]] = []
    for rule in lines:
        pattern = rule[1:] if rule.startswith("!") else rule
        if not pattern:
            continue
        basename = pattern.rsplit("/", 1)[-1]
        if fnmatch.fnmatch("note.tmp", basename) and fnmatch.fnmatch("build.tmp", basename):
            found.append((rule, pattern))
    return found


def _pattern_is_global(pattern: str) -> bool:
    """True when the pattern applies at any depth, not to one pinned directory."""
    if pattern.startswith("/"):
        return False  # anchored at the repository root
    return "/" not in pattern or pattern.startswith("**/")


# --------------------------------------------------------------------------- #
# 5b. U8.76: where the ``check-ignore`` probes run -- and the stub repo that
#     makes the *behavioural* half of the guard go red too.
# --------------------------------------------------------------------------- #
# U8.74's seam only redirected the *parse* (``_gitignore_under_test``);
# ``git check-ignore`` has no flag for "use this other .gitignore", and
# ``core.excludesFile`` is *lower* precedence than the repo's own ``.gitignore``,
# so it cannot cancel a rule that lives in the committed file.  A scratch work
# tree whose single ``.gitignore`` IS the copy under test is the honest way to
# watch the probes fail without editing anything on disk.  Unset env -> the real
# repository, which is the default and what every other test in this module uses.
_STUB_STATE_DIR = REPO_ROOT / "state" / "verify" / "U8.76" / "redrepo"
_STUB_ROOTS: dict[str, Path] = {}


def _check_ignore_cwd() -> Path:
    override = os.environ.get(GITIGNORE_OVERRIDE_ENV, "").strip()
    if not override:
        return REPO_ROOT
    return _stub_repo(Path(override))


def _stub_repo(copy: Path) -> Path:
    """A throwaway git work tree whose only ignore file is ``copy``.

    Rebuilt whenever the copy's contents change, so one copy file can drive
    several red runs.  Lives under ``state/verify/U8.76/**`` (an ignored, unit
    -declared path) and never touches the real index or the work tree: the only
    git commands run inside it are ``init`` and ``check-ignore``.
    """
    resolved = copy.resolve()
    key = f"{resolved}:{hashlib.sha256(resolved.read_bytes()).hexdigest()}"
    cached = _STUB_ROOTS.get(key)
    if cached is not None:
        return cached
    if _STUB_STATE_DIR.exists():
        shutil.rmtree(_STUB_STATE_DIR)
    _STUB_STATE_DIR.mkdir(parents=True)
    _git_in(_STUB_STATE_DIR, "init", "--quiet", ".")
    # Copy it *as* ``.gitignore`` so git reads it as this work tree's rules.
    shutil.copyfile(resolved, _STUB_STATE_DIR / ".gitignore")
    _STUB_ROOTS[key] = _STUB_STATE_DIR
    return _STUB_STATE_DIR


@pytest.mark.parametrize("path", TMP_PATHS)
def test_tmp_paths_are_ignored_at_any_depth(path: str) -> None:
    # check-ignore is read-only and --no-index makes the probe independent of
    # what the index happens to contain; nothing is created on disk.
    assert is_ignored(path), (
        f"{path} is not ignored; the global '**/*.tmp' rule (U8.70, .gitignore:41) "
        "must cover a *.tmp scratch file at the repo root and inside the source "
        "tree, not only the spill files under state/ that /state/ already caught"
    )


def test_tmp_rule_is_not_inherited_from_an_ignored_parent() -> None:
    # If a parent directory were itself ignored the *.tmp probes would pass
    # transitively and say nothing about the rule.  The repo root has no parent
    # of its own, so it is excluded here.
    parents = [
        str(PurePosixPath(p).parent) for p in TMP_PATHS
    ]
    transitive = [
        f"{parent} (rule {ignored_by(parent)!r})"
        for parent in parents
        if parent != "." and is_ignored(parent)
    ]
    assert not transitive, (
        "these parent directories are themselves ignored: "
        + "; ".join(transitive)
        + " -- the *.tmp assertions would then pass without the **/*.tmp rule"
    )


def test_gitignore_declares_a_global_tmp_rule() -> None:
    # Structural half: parse the real .gitignore rather than snapshotting one
    # line, so the guard survives the exact matching mechanism changing.
    gitignore = _gitignore_under_test()
    lines = _effective_rule_lines(gitignore.read_text(encoding="utf-8"))
    matched = _tmp_rule_patterns(lines)
    assert matched, (
        f"{gitignore} declares no rule that would ignore a '*.tmp' file; the "
        "global '**/*.tmp' rule (U8.70, .gitignore:41) is what keeps scratch "
        "spill files out of the index, and deleting it made every "
        "test_tmp_paths_are_ignored_at_any_depth case fail"
    )
    global_rules = [rule for rule, pattern in matched if _pattern_is_global(pattern)]
    assert global_rules, (
        f"only directory-anchored rules {[r for r, _ in matched]!r}; a rule pinned "
        f"to one directory would not ignore note.tmp at the repository root"
    )


# --------------------------------------------------------------------------- #
# 6. U8.76: the SQLite sidecar rules are global by design (.gitignore:20-22)
# --------------------------------------------------------------------------- #
# A WAL/SHM/journal sidecar is created *next to its database*, so it appears at
# whatever depth the database lives.  Any rule pinned to one directory (root or
# state/) leaves a sidecar beside a database elsewhere in the tree showing up as
# untracked noise -- and, worse, stageable.  These three probe paths are chosen
# OUTSIDE state/** exactly like the *.tmp ones above, so they cannot be satisfied
# transitively by /state/.
SIDECAR_PROBE_PATHS = [
    "state.sqlite-wal",  # repo root: a sidecar beside a root-level database
    "orchestration/units/state.sqlite-shm",  # a hand-written dir with no rule of its own
    "src/resextract/state.sqlite-journal",  # inside the source tree
]

# The suffixes the rules at .gitignore:20-22 must each cover.
SIDECAR_SUFFIXES = ["-wal", "-shm", "-journal"]


def _sidecar_rule_patterns(lines: Iterable[str]) -> list[tuple[str, str]]:
    """``(rule, pattern)`` for rules whose last component globs a sidecar name.

    Deliberately suffix-agnostic: it asks which rules would ignore a
    ``state.sqlite-<suffix>`` *by name*, so it sees both the global form
    (``*.sqlite-wal``) and a root-anchored one (``/state.sqlite-wal``) -- the
    latter is matched here and then rejected by ``_pattern_is_global``.
    """
    found: list[tuple[str, str]] = []
    for rule in lines:
        pattern = rule[1:] if rule.startswith("!") else rule
        if not pattern:
            continue
        basename = pattern.rsplit("/", 1)[-1]
        if any(
            fnmatch.fnmatch(f"state.sqlite{suffix}", basename)
            for suffix in SIDECAR_SUFFIXES
        ):
            found.append((rule, pattern))
    return found


@pytest.mark.parametrize("path", SIDECAR_PROBE_PATHS)
def test_sidecar_paths_are_ignored_at_any_depth(path: str) -> None:
    # check-ignore is read-only and --no-index makes the probe independent of
    # the index; assert the sidecar is NOT on disk afterwards so a green here
    # can never be explained by the probe having created the thing it matched.
    parent = str(PurePosixPath(path).parent)
    assert parent == "." or not is_ignored(parent), (
        f"{parent} is itself ignored (by {ignored_by(parent)!r}); the sidecar "
        "assertions would then pass transitively and say nothing about the "
        "*.sqlite-wal/-shm/-journal rules"
    )
    assert not (REPO_ROOT / path).exists(), (
        f"{path} exists on disk; this module must only *name* sidecars, never "
        "create them"
    )
    rule = ignored_by(path)
    assert is_ignored(path), (
        f"{path} is not ignored; the global '*.sqlite-wal'/'-shm'/'-journal' "
        "rules (.gitignore:20-22) must cover a sidecar wherever its database "
        "lives -- at the repository root and inside the source tree, not only "
        "the spill files under state/ that /state/ already caught"
    )
    assert rule != "", f"{path} is ignored but no matching rule was reported"


@pytest.mark.parametrize("suffix", SIDECAR_SUFFIXES)
def test_gitignore_declares_a_global_sidecar_rule(suffix: str) -> None:
    # Structural half: parse the real .gitignore rather than snapshotting one
    # line, so the guard survives the exact matching mechanism changing.
    gitignore = _gitignore_under_test()
    lines = _effective_rule_lines(gitignore.read_text(encoding="utf-8"))
    matched = _sidecar_rule_patterns(lines)
    assert matched, (
        f"{gitignore} declares no rule that would ignore a "
        f"'state.sqlite{suffix}' file; the global '*.sqlite{suffix}' rule "
        "(.gitignore:20-22) is what keeps a runtime sidecar out of the index "
        "wherever its database lives"
    )
    global_rules = [rule for rule, pattern in matched if _pattern_is_global(pattern)]
    assert global_rules, (
        f"only directory-anchored rules {[r for r, _ in matched]!r}; a "
        f"root-anchored '/state.sqlite{suffix}' (or one pinned to state/) would "
        "not ignore a sidecar sitting next to a database elsewhere in the tree"
    )
