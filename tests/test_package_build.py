"""Guard: the release package is described by its MANIFEST, and the manifest is
checked against the tree it claims to ship.

`tests/test_build_wiring.py` derives the wiring from the DRIVER's built-in
default block.  This file derives the same facts from
``orchestration/packages/<slug>.toml`` -- the manifest that the driver actually
reads with ``--package <slug>`` -- and it is the file that makes a STALE MANIFEST
ENTRY RED.  The two files are deliberately independent:

    test_build_wiring.py   script literals  ->  tree on disk
    test_package_build.py  manifest         ->  tree on disk
    ...and this file also cross-checks manifest -> script literals, so the two
    sources of truth cannot drift apart silently.

Run it the way the workspace documents (a bare ``pytest`` fails at collection in
``tests/conftest.py``):

    PYTHONPATH=src:. python3 -m pytest tests/test_package_build.py -q

WHAT THIS FILE PROVES
  * every manifest declares the full schema and names fragments that exist;
  * ``ship_staged`` is EXACTLY the file set of the promoted tree -- add, remove
    or rename one file on either side and this is RED;
  * ``never_ship`` is disjoint from ``ship_staged``;
  * no package digest is pinned anywhere -- the only 64-hex value in any manifest
    or in the driver is the named LICENCE-template guard;
  * the default package's manifest agrees with the driver's built-in default
    block (the two-way tripwire);
  * an unknown package slug fails closed (exit 2) before anything is touched;
  * the GATE governs the exit code: a failing gate is never reported as a pass.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "orchestration" / "packages"
BUILD_SCRIPT = ROOT / "orchestration" / "units" / "UBUILD1.build.sh"
DEFAULT_SLUG = "gated-read-batching"

REQUIRED_KEYS = (
    "schema", "slug", "name", "dest_default", "promoted_san_src",
    "frozen_san_src", "licence_src", "licence_files", "licence_sha256",
    "commit_subject", "anchors", "index_row", "vocabulary_code",
    "vocabulary_public", "neutralise_rules", "neutralise_forbidden",
    "ship_staged", "never_ship",
)
FRAGMENT_KEYS = ("vocabulary_code", "vocabulary_public")
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
# Literal forms parsed out of the DRIVER (the same shapes test_build_wiring.py uses).
PROMOTED_LINE = re.compile(r'^PROMOTED_SAN_SRC="\$SRC/(?P<rel>[^"]+)"$', re.M)
FROZEN_LINE = re.compile(r'^FROZEN_SAN_SRC="\$SRC/(?P<rel>[^"]+)"$', re.M)
SHIP_BLOCK = re.compile(r"^SHIP_STAGED=\(\n(?P<body>.*?)^\)$", re.M | re.S)
NEVER_BLOCK = re.compile(r"^NEVER_SHIP=\(\n(?P<body>.*?)^\)$", re.M | re.S)


# --------------------------------------------------------------------------- #
# Manifest inventory and shape.                                               #
# --------------------------------------------------------------------------- #
def manifest_paths() -> list[Path]:
    return sorted(MANIFEST_DIR.glob("*.toml"))


def load(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def all_manifests() -> list[tuple[Path, dict]]:
    paths = manifest_paths()
    assert paths, f"no manifests under {MANIFEST_DIR}"
    return [(p, load(p)) for p in paths]


def resolve(value: str, src: Path = ROOT) -> Path:
    """A manifest path is $SRC-relative unless it is absolute."""
    return Path(value) if os.path.isabs(value) else src / value


def test_at_least_one_manifest_exists() -> None:
    assert manifest_paths(), f"no *.toml manifests under {MANIFEST_DIR}"


def test_every_manifest_declares_the_full_schema() -> None:
    for path, man in all_manifests():
        missing = [key for key in REQUIRED_KEYS if key not in man]
        assert not missing, f"{path.name}: missing manifest key(s): {missing}"
        assert man["schema"] == 1, f"{path.name}: unsupported schema {man['schema']!r}"


def test_every_manifest_slug_matches_its_file_name() -> None:
    for path, man in all_manifests():
        assert man["slug"] == path.stem, (
            f"{path.name}: slug {man['slug']!r} does not match the file name")


def test_every_manifest_name_is_a_bare_directory_name() -> None:
    for path, man in all_manifests():
        name = man["name"]
        assert name and "/" not in name and name not in (".", ".."), (
            f"{path.name}: name must be a bare directory name, got {name!r}")


def test_every_manifest_fragment_exists() -> None:
    for path, man in all_manifests():
        for key in FRAGMENT_KEYS:
            frag = MANIFEST_DIR / man[key]
            assert frag.is_file(), f"{path.name}: {key} fragment missing: {frag}"


def test_every_manifest_licence_template_exists() -> None:
    for path, man in all_manifests():
        lic = resolve(man["licence_src"])
        assert lic.is_dir(), f"{path.name}: licence template dir missing: {lic}"
        for name in man["licence_files"]:
            assert (lic / name).is_file(), f"{path.name}: licence file missing: {lic / name}"


def test_every_manifest_promoted_and_frozen_tree_exists_in_this_workspace() -> None:
    for path, man in all_manifests():
        for key in ("promoted_san_src", "frozen_san_src"):
            tree = resolve(man[key])
            assert tree.is_dir(), f"{path.name}: {key} missing: {tree}"


# --------------------------------------------------------------------------- #
# THE PROPERTY THAT MAKES A STALE MANIFEST ENTRY RED.                         #
# --------------------------------------------------------------------------- #
def test_ship_list_is_exactly_the_promoted_tree_as_it_is() -> None:
    """`ship_staged` must equal the files actually present in the promoted tree.

    Add a file to the tree without listing it, list a file the tree does not
    have, or rename either side, and this is RED.  That is the whole point: the
    failure mode this refactor exists to remove is a manifest that no longer
    describes the tree it pins.
    """
    for path, man in all_manifests():
        promoted = resolve(man["promoted_san_src"])
        present = sorted(
            p.relative_to(promoted).as_posix()
            for p in promoted.rglob("*")
            if p.is_file() and ".git" not in p.parts
        )
        listed = sorted(man["ship_staged"])
        assert listed == present, (
            "%s: ship_staged does not match the promoted tree %s\n"
            "  only in ship_staged: %s\n  only on disk:        %s"
            % (path.name, man["promoted_san_src"],
               sorted(set(listed) - set(present)), sorted(set(present) - set(listed)))
        )


def test_never_ship_is_disjoint_from_the_ship_list() -> None:
    for path, man in all_manifests():
        both = sorted(set(man["never_ship"]) & set(man["ship_staged"]))
        assert not both, f"{path.name}: entry both shipped and never-shipped: {both}"


def test_never_ship_is_checked_by_the_driver() -> None:
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "FATAL: NEVER_SHIP entry is present in the package" in text


def test_ship_list_is_fail_closed_in_the_driver() -> None:
    """A listed file that is missing must stop the build, not be skipped."""
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert 'echo "FATAL: ship-list names a file the package does not have: $rel" >&2' in text


def test_no_package_digest_is_pinned_anywhere() -> None:
    """The only pinned digest is the NAMED licence-template guard.

    A digest of the package (or of the staged tree) would turn every honest
    re-pin into a hard failure; this workspace forbids that.  So: every 64-hex
    value in every manifest, and in the driver, must be the licence hash.
    """
    for path, man in all_manifests():
        raw = path.read_text(encoding="utf-8")
        found = set(HEX64.findall(raw))
        assert found == {man["licence_sha256"]}, (
            f"{path.name}: pinned digest(s) other than licence_sha256: "
            f"{sorted(found - {man['licence_sha256']})}")
        assert "licence_sha256" in raw

    driver_hexes = set(HEX64.findall(BUILD_SCRIPT.read_text(encoding="utf-8")))
    assert len(driver_hexes) == 1, f"driver pins more than the licence hash: {driver_hexes}"
    default = load(MANIFEST_DIR / (DEFAULT_SLUG + ".toml"))
    assert driver_hexes == {default["licence_sha256"]}


# --------------------------------------------------------------------------- #
# The manifest and the driver's built-in default block must agree.            #
# --------------------------------------------------------------------------- #
def _block(pattern: re.Pattern[str], text: str) -> list[str]:
    match = pattern.search(text)
    assert match, f"driver literal block not found for {pattern.pattern!r}"
    return [
        line.strip() for line in match.group("body").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_default_manifest_agrees_with_the_drivers_built_in_default_block() -> None:
    """Two sources of truth, one tripwire: editing either alone stops the build."""
    man = load(MANIFEST_DIR / (DEFAULT_SLUG + ".toml"))
    text = BUILD_SCRIPT.read_text(encoding="utf-8")

    promoted = PROMOTED_LINE.search(text)
    frozen = FROZEN_LINE.search(text)
    assert promoted and frozen, "the driver lost its literal default tree block"
    assert man["promoted_san_src"] == promoted.group("rel")
    assert man["frozen_san_src"] == frozen.group("rel")
    assert sorted(man["ship_staged"]) == sorted(_block(SHIP_BLOCK, text))
    assert sorted(man["never_ship"]) == sorted(_block(NEVER_BLOCK, text))

    # the driver carries the same assignment shape test_build_wiring.py asserts
    assert 'LIC_SHA_EXPECTED="%s"' % man["licence_sha256"] in text


def test_the_driver_accepts_package_and_fails_closed_on_an_unknown_slug(tmp_path: Path) -> None:
    env = dict(os.environ)
    for key in ("SRC", "DEST", "SAN_SRC_OVERRIDE", "SAN_SRC_FROZEN_OVERRIDE"):
        env.pop(key, None)
    env["DEST"] = str(tmp_path / "dest" / "research-publish-packages")
    proc = subprocess.run(
        ["bash", str(BUILD_SCRIPT), "--package", "no-such-package-xyz"],
        capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=120,
    )
    assert proc.returncode == 2, (
        "an unknown package slug must fail closed with exit 2, got %d:\n%s"
        % (proc.returncode, proc.stdout + proc.stderr))
    assert "FATAL: no manifest for package" in proc.stdout + proc.stderr
    assert not (tmp_path / "dest").exists(), "the build touched DEST before validating the slug"


# --------------------------------------------------------------------------- #
# Fail-closed gate: a failing gate is never reported as a pass.               #
# --------------------------------------------------------------------------- #
def test_the_gate_result_governs_the_exit_code(tmp_path: Path) -> None:
    """Run the real driver and assert the exit code TRACKS the gate result.

    The gate is fail-closed: a hard-fail must exit non-zero and must never be
    printed as a pass.  Today this workspace's tree still carries flagged tokens,
    so the assertion that fires is the FAIL one; if the vocabulary is ever
    cleaned the PASS branch fires instead, and neither branch can be satisfied by
    a build that swallows the gate's status.
    """
    dest = tmp_path / "dest" / "research-publish-packages"
    env = dict(os.environ)
    for key in ("SRC", "DEST", "SAN_SRC_OVERRIDE", "SAN_SRC_FROZEN_OVERRIDE"):
        env.pop(key, None)
    env["DEST"] = str(dest)
    proc = subprocess.run(
        ["bash", str(BUILD_SCRIPT), "--package", DEFAULT_SLUG],
        capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=900,
    )
    log = proc.stdout + proc.stderr
    assert "BUILD COMPLETE" in log, "the build did not reach its done step:\n" + log[-3000:]

    passed = "GATE RESULT: PASS" in log
    failed = "GATE RESULT: FAIL" in log
    assert passed != failed, "the gate printed neither (or both) results:\n" + log[-3000:]

    if failed:
        assert proc.returncode != 0, (
            "a FAILING gate was reported as a success (exit 0):\n" + log[-3000:])
        assert "the exclusion gate FAILED" in log
        assert "the exclusion gate PASSED" not in log
    else:
        assert proc.returncode == 0, (
            "a PASSING gate did not exit 0 (exit %d):\n" % proc.returncode + log[-3000:])
    # the tree is complete either way: the gate runs AFTER the commit
    assert (dest / "packages" / load(MANIFEST_DIR / (DEFAULT_SLUG + ".toml"))["name"]).is_dir()


# --------------------------------------------------------------------------- #
# GAP 1: the ship-list/tree check is manifest-derived and fails closed for     #
# EVERY package, not only the built-in default one.                            #
# --------------------------------------------------------------------------- #
SHIPLIST_FATAL = "FATAL: SHIP-LIST/TREE MISMATCH"


def _clean_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in ("SRC", "DEST", "SAN_SRC_OVERRIDE", "SAN_SRC_FROZEN_OVERRIDE"):
        env.pop(key, None)
    return env


def test_the_driver_checks_the_ship_list_against_the_pinned_tree() -> None:
    """The check exists, is derived from the manifest, and is not default-only."""
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert SHIPLIST_FATAL in text, "the manifest-derived ship-list/tree check is missing"
    assert "SHIPLIST_TREE_CHECK_PY" in text, "the ship-list/tree check body is missing"
    assert 'man["promoted_san_src"]' in text and 'man["ship_staged"]' in text
    guard = text.index('if [ "$PKG_SLUG" = "$DEFAULT_SLUG" ]; then')
    assert text.index(SHIPLIST_FATAL) > guard, (
        "the ship-list/tree check sits inside the default-package-only block")


def _copy_driver_root(tmp_path: Path, slug: str, mutate) -> Path:
    """A throwaway repo root holding the driver, a manifest copy and fragments.

    `promoted_san_src` is $SRC-relative and SRC stays the real workspace, so the
    copy pins the REAL 29-file tree -- only the manifest is the copy under test.
    """
    root = tmp_path / "root"
    (root / "orchestration" / "units").mkdir(parents=True)
    (root / "orchestration" / "packages").mkdir(parents=True)
    shutil.copy2(BUILD_SCRIPT, root / "orchestration" / "units" / BUILD_SCRIPT.name)
    text = (MANIFEST_DIR / "encoder-crossover-190.toml").read_text(encoding="utf-8")
    text = text.replace('slug = "encoder-crossover-190"', 'slug = "%s"' % slug, 1)
    (root / "orchestration" / "packages" / (slug + ".toml")).write_text(
        mutate(text), encoding="utf-8")
    shutil.copytree(MANIFEST_DIR / "encoder-crossover-190",
                    root / "orchestration" / "packages" / "encoder-crossover-190")
    return root


def _run_copy(tmp_path: Path, root: Path, slug: str) -> tuple[int, str, Path]:
    dest = tmp_path / "dest" / "research-publish-packages"
    env = _clean_env()
    env["DEST"] = str(dest)
    proc = subprocess.run(
        ["bash", str(root / "orchestration" / "units" / BUILD_SCRIPT.name),
         "--package", slug],
        capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=600)
    return proc.returncode, proc.stdout + proc.stderr, dest


def test_ship_list_check_fails_closed_on_a_perturbed_manifest_copy(tmp_path: Path) -> None:
    """Perturb ship_staged in a COPY: the new check fires, before DEST is touched."""
    root = _copy_driver_root(
        tmp_path, "perturbed-pkg",
        lambda text: text.replace(
            '  "verify/recompute-claims.py",\n',
            '  "verify/recompute-claims.py",\n  "results/STALE-ENTRY.json",\n', 1))
    rc, log, dest = _run_copy(tmp_path, root, "perturbed-pkg")
    assert rc != 0, "a perturbed ship list did not stop the build:\n" + log[-3000:]
    assert SHIPLIST_FATAL in log, "the manifest-derived check did not fire:\n" + log[-3000:]
    assert "results/STALE-ENTRY.json" in log
    pkg = dest / "packages" / "encoder-crossover-190"
    assert not pkg.is_dir() or not list(pkg.iterdir()), (
        "files were staged despite the ship-list mismatch")
    assert "staging" not in log or SHIPLIST_FATAL in log


def test_ship_list_check_passes_green_on_an_unperturbed_manifest_copy(tmp_path: Path) -> None:
    root = _copy_driver_root(tmp_path, "green-pkg", lambda text: text)
    _rc, log, _dest = _run_copy(tmp_path, root, "green-pkg")
    assert "ship-list/tree check: 29 declared file(s) == 29 present" in log, log[-3000:]
    assert SHIPLIST_FATAL not in log


# --------------------------------------------------------------------------- #
# GAP 2: the archive README index is manifest-driven and ACCUMULATES.          #
# --------------------------------------------------------------------------- #
def test_root_readme_index_accumulates_two_packages(tmp_path: Path) -> None:
    dest = tmp_path / "dest" / "research-publish-packages"
    env = _clean_env()
    env["DEST"] = str(dest)
    for slug in ("gated-read-batching", "encoder-crossover-190"):
        subprocess.run(
            ["bash", str(BUILD_SCRIPT), "--package", slug],
            capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=900)
    readme = (dest / "README.md").read_text(encoding="utf-8")
    first = readme.index("packages/exp12-encoder-crossover/")
    second = readme.index("packages/encoder-crossover-190/")
    assert first != second
    assert second < first, "rows are not in deterministic slug order:\n" + readme
    assert (dest / "packages" / "exp12-encoder-crossover").is_dir(), (
        "the first package's tree was wiped by the second build")
    assert (dest / "packages" / "encoder-crossover-190").is_dir()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
