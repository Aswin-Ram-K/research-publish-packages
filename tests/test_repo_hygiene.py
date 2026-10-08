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
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

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


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
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
    """True if git considers ``path`` ignored (index status ignored)."""
    return _git("check-ignore", "--quiet", "--no-index", "--", path).returncode == 0


def ignored_by(path: str) -> str:
    """The rule that ignores ``path`` (``.gitignore:LINE:pattern``), or ``""``."""
    result = _git("check-ignore", "-v", "--no-index", "--", path)
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
def test_root_dockets_is_still_ignored() -> None:
    path = "dockets/example-docket/MANIFEST.json"
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
