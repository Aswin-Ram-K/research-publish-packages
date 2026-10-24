"""Guard: the release build must promote the chosen DATA + VERIFICATION package.

Rewired by unit UWIRE3 (was UWIRE2).  The scope of the release changed: the
package ships **data and verification tools only, the harness withheld**.  The
build (`orchestration/units/UBUILD1.build.sh`) used to stage a 45-file
``code/``/``eval/`` tree and ship 18 ``code/harness/*`` entries.  It now stages
the proven package ``scratch/uneutral10/package/`` (29 files) verbatim, and the
promoted path lives in exactly **one named constant**:

    PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"

This test DERIVES that path — and the frozen path, and the ship list — from the
script itself.  It never repeats their values, which is what made the previous
version of this guard pass green over a stale tree (it asserted the same
constant the script hard-coded).  It FAILS if:

  * the default tree is silently changed away from the chosen release artifact
    (the promoted path must exist in this workspace, and the wiring line must
    name it);
  * `SAN_SRC_FROZEN_OVERRIDE=1` stops selecting the frozen original tree;
  * `SAN_SRC_OVERRIDE=<path>` stops selecting exactly that path;
  * either default is guessed from disk instead of being a literal path;
  * the wiring line stops being emitted, stops naming the tree, or stops being
    emitted before the first destructive step;
  * **the ship list stops matching the files actually present in the promoted
    tree** — so re-pinning the constant at a wrong/older tree without
    re-deriving the list makes this RED;
  * a `code/harness/*` entry ever comes back into the ship list;
  * any fail-closed guard is deleted from the script.

Several build invocations run against a throwaway fake `SRC`, so they are
cheap: they print the wiring line and stop at the first missing source
directory or the fail-closed ship-list check.  Set `UWIRE3_BUILD_SCRIPT` (or the
older `UWIRE2_BUILD_SCRIPT`) to point the guard at a copy of the script — that
is how the red->green was produced.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = Path(
    os.environ.get("UWIRE3_BUILD_SCRIPT")
    or os.environ.get("UWIRE2_BUILD_SCRIPT")
    or (ROOT / "orchestration" / "units" / "UBUILD1.build.sh")
)
WIRING_DOC = ROOT / "strategy" / "BUILD_WIRING.md"

WIRING_LINE = re.compile(
    r"^SAN_SRC WIRING: tree=(?P<tree>.*) promoted_default=(?P<promoted>yes|no)$", re.M
)
PROMOTED_LINE = re.compile(r'^PROMOTED_SAN_SRC="\$SRC/(?P<rel>[^"]+)"$', re.M)
FROZEN_LINE = re.compile(r'^FROZEN_SAN_SRC="\$SRC/(?P<rel>[^"]+)"$', re.M)
SHIP_BLOCK = re.compile(r"^SHIP_STAGED=\(\n(?P<body>.*?)^\)$", re.M | re.S)


# --------------------------------------------------------------------------- #
# The script is the single source of truth: parse it, never repeat its values. #
# --------------------------------------------------------------------------- #
def _script_text() -> str:
    return BUILD_SCRIPT.read_text(encoding="utf-8")


def _literal_rel(pattern: re.Pattern[str], name: str) -> Path:
    match = pattern.search(_script_text())
    assert match, f"{name} is not a literal $SRC-relative path in {BUILD_SCRIPT}"
    rel = match.group("rel")
    assert "$(" not in rel and "`" not in rel, f"{name} is guessed from disk: {rel}"
    return Path(rel)


def promoted_rel() -> Path:
    return _literal_rel(PROMOTED_LINE, "PROMOTED_SAN_SRC")


def frozen_rel() -> Path:
    return _literal_rel(FROZEN_LINE, "FROZEN_SAN_SRC")


def ship_list() -> list[str]:
    match = SHIP_BLOCK.search(_script_text())
    assert match, "SHIP_STAGED=( ... ) not found in the build script"
    entries = [
        line.strip()
        for line in match.group("body").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert entries, "SHIP_STAGED parsed as empty"
    return entries


def _clean_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in ("SRC", "DEST", "SAN_SRC_OVERRIDE", "SAN_SRC_FROZEN_OVERRIDE"):
        env.pop(key, None)
    return env


def _fake_src(tmp_path: Path) -> Path:
    """A SRC tree with just enough shape for the build to reach its own checks."""
    src = tmp_path / "srctree"
    for rel in (promoted_rel(), frozen_rel()):
        (src / rel).mkdir(parents=True, exist_ok=True)
    return src


def _run_build(src: Path, tmp_path: Path, tag: str, **overrides: str) -> tuple[int, str]:
    env = _clean_env()
    env["SRC"] = str(src)
    # DEST must end in /research-publish-packages; keep it in the throwaway tree.
    env["DEST"] = str(tmp_path / f"dest-{tag}" / "research-publish-packages")
    env.update(overrides)
    proc = subprocess.run(
        ["bash", str(BUILD_SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
        timeout=300,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _wiring(log: str) -> re.Match[str]:
    hits = list(WIRING_LINE.finditer(log))
    assert hits, "no 'SAN_SRC WIRING: tree=... promoted_default=...' line:\n" + log[-2000:]
    assert len(hits) == 1, "expected exactly one wiring line, got %d:\n%s" % (len(hits), log[-2000:])
    return hits[0]


def _workspace_files(rel: Path) -> list[str]:
    root = ROOT / rel
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    )


# --------------------------------------------------------------------------- #
# Wiring (derived from the script, never hard-coded).                          #
# --------------------------------------------------------------------------- #
def test_the_script_under_test_exists() -> None:
    assert BUILD_SCRIPT.is_file(), f"build script not found: {BUILD_SCRIPT}"


def test_default_is_the_chosen_release_artifact(tmp_path: Path) -> None:
    """Unset overrides must select the promoted package, not the frozen tree."""
    src = _fake_src(tmp_path)
    rc, log = _run_build(src, tmp_path, "default")
    hit = _wiring(log)
    assert hit.group("promoted") == "yes", "the default is NOT the promoted default:\n" + log[-2000:]
    assert Path(hit.group("tree")) == src / promoted_rel(), (
        "the default tree is not the chosen release artifact:\n  got  %s\n  want %s\n%s"
        % (hit.group("tree"), src / promoted_rel(), log[-2000:])
    )
    assert rc != 0, "the empty fake SRC should have stopped the build non-zero"


def test_frozen_override_still_selects_the_frozen_tree(tmp_path: Path) -> None:
    """SAN_SRC_FROZEN_OVERRIDE=1 must select the original sanitised tree, loudly."""
    src = _fake_src(tmp_path)
    rc, log = _run_build(src, tmp_path, "frozen", SAN_SRC_FROZEN_OVERRIDE="1")
    hit = _wiring(log)
    assert Path(hit.group("tree")) == src / frozen_rel(), (
        "the frozen override stopped selecting the frozen tree:\n  got  %s\n  want %s\n%s"
        % (hit.group("tree"), src / frozen_rel(), log[-2000:])
    )
    assert hit.group("promoted") == "no", "the frozen tree must not be reported as promoted"
    assert "WARNING" in log and "FROZEN" in log, "selecting the frozen tree did not warn:\n" + log[-2000:]
    assert rc != 0


def test_generic_override_is_honoured_verbatim(tmp_path: Path) -> None:
    """SAN_SRC_OVERRIDE=<path> must win and select exactly that path."""
    src = _fake_src(tmp_path)
    other = tmp_path / "some-other-tree"
    other.mkdir()
    rc, log = _run_build(src, tmp_path, "override", SAN_SRC_OVERRIDE=str(other))
    hit = _wiring(log)
    assert Path(hit.group("tree")) == other, (
        "SAN_SRC_OVERRIDE is not honoured verbatim:\n  got  %s\n  want %s\n%s"
        % (hit.group("tree"), other, log[-2000:])
    )
    assert hit.group("promoted") == "no"
    assert rc != 0


def test_wiring_line_is_emitted_before_anything_destructive(tmp_path: Path) -> None:
    """The warning must exist even when the build stops immediately after it."""
    src = _fake_src(tmp_path)
    _rc, log = _run_build(src, tmp_path, "early")
    assert "SAN_SRC WIRING:" in log
    assert log.index("SAN_SRC WIRING:") < log.index("removing any previous target"), (
        "the wiring line is emitted after the build starts removing the target"
    )


def test_defaults_are_literal_never_guessed_from_disk() -> None:
    """A disk guess would make the tree depend on ambient state; both are literal."""
    assert PROMOTED_LINE.search(_script_text()), "PROMOTED_SAN_SRC is no longer a literal path"
    assert FROZEN_LINE.search(_script_text()), "FROZEN_SAN_SRC is no longer a literal path"
    for line in _script_text().splitlines():
        if line.startswith(("PROMOTED_SAN_SRC=", "FROZEN_SAN_SRC=")):
            assert "$(" not in line and "`" not in line, f"default guessed from disk: {line}"


def test_the_chosen_artifact_and_the_frozen_tree_exist_in_this_workspace() -> None:
    assert (ROOT / promoted_rel()).is_dir(), f"promoted artifact missing: {ROOT / promoted_rel()}"
    assert (ROOT / frozen_rel()).is_dir(), f"frozen tree missing: {ROOT / frozen_rel()}"


# --------------------------------------------------------------------------- #
# The property that makes a stale pin RED.                                     #
# --------------------------------------------------------------------------- #
def test_ship_list_is_exactly_the_promoted_tree_as_it_is() -> None:
    """The ship list must equal the files actually present in the promoted tree.

    Re-pin the constant at a different (older) tree without re-deriving the list
    and this fails: that is the whole point.
    """
    present = _workspace_files(promoted_rel())
    listed = sorted(ship_list())
    assert listed == present, (
        "SHIP_STAGED does not match the promoted tree %s:\n"
        "  only in SHIP_STAGED: %s\n  only on disk: %s"
        % (promoted_rel(), sorted(set(listed) - set(present)), sorted(set(present) - set(listed)))
    )


def test_the_harness_is_not_shipped() -> None:
    """Scope: data + verification tools only, the harness withheld."""
    harnessed = [entry for entry in ship_list() if entry.startswith("code/harness/")]
    assert not harnessed, f"code/harness/* entries are back in the ship list: {harnessed}"
    assert not any(entry.startswith("code/") for entry in ship_list()), (
        "the old code/ tree is back in the ship list"
    )


def test_the_fail_closed_guards_are_still_present() -> None:
    """Every fail-closed guard the build documents must survive a rewire."""
    text = _script_text()
    for needle, why in (
        ('*/research-publish-packages)', "DEST suffix guard"),
        ("FATAL: refusing to rm -rf", "DEST rm -rf guard"),
        ("exit 2", "guard exit code 2"),
        ('echo "FATAL: ship-list names a file the package does not have: $rel" >&2', "ship-list FATAL"),
        ("NEVER_SHIP=(", "NEVER_SHIP list"),
        ("FATAL: NEVER_SHIP entry is present in the package", "NEVER_SHIP absence FATAL"),
        ("sha256sum \"$DEST/LICENSE\"", "licence sha guard"),
        ('3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900', "licence sha"),
        ('exit "$GATE_RC"', "gate exit propagation"),
    ):
        assert needle in text, f"fail-closed guard missing ({why}): {needle!r}"


def test_build_wiring_doc_names_both_overrides() -> None:
    doc = WIRING_DOC.read_text(encoding="utf-8")
    assert "SAN_SRC_FROZEN_OVERRIDE" in doc, "BUILD_WIRING.md does not document the frozen override"
    assert "SAN_SRC_OVERRIDE" in doc, "BUILD_WIRING.md does not document the general override"
    assert "promoted_default" in doc, "BUILD_WIRING.md does not document the wiring line"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
