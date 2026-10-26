"""Warmpool isolation: the store root may not live inside the repository tree.

The warmpool is an isolated filespace, not a workspace subdirectory. A root under
the repo would be swept by `git clean`, copied by every archive, and would make "the
warmpool" mean two different things on two machines.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ptr_engine import BodyStore, assert_warmpool_root, find_repo_root
from ptr_engine.errors import (
    PtrExtensionError,
    PtrStoreMissError,
    PtrWarmpoolViolationError,
)
from ptr_engine.reference import ResourceRef


def test_the_engine_can_find_its_own_repository():
    repo = find_repo_root()
    assert repo is not None
    assert (repo / "pyproject.toml").is_file()
    assert (repo / "experiments").is_dir()
    assert Path(__file__).resolve().is_relative_to(repo)


def test_a_root_under_the_repo_is_refused_and_not_created():
    repo = find_repo_root()
    target = repo / "scratch" / "ptr-warmpool-must-not-exist"
    with pytest.raises(PtrWarmpoolViolationError) as excinfo:
        BodyStore(target)
    assert excinfo.value.code == "PTR_WARMPOOL_INSIDE_REPO"
    assert not target.exists(), "a refused root must not leave a directory behind"


def test_the_repo_root_itself_is_refused():
    with pytest.raises(PtrWarmpoolViolationError):
        BodyStore(find_repo_root())


def test_a_dot_dot_route_into_the_repo_is_refused():
    repo = find_repo_root()
    sneaky = repo / "experiments" / ".." / "warmpool"
    with pytest.raises(PtrWarmpoolViolationError):
        assert_warmpool_root(sneaky)


def test_a_root_outside_the_repo_is_accepted(tmp_path):
    root = assert_warmpool_root(tmp_path / "outside" / "warmpool")
    assert not root.is_relative_to(find_repo_root())
    assert BodyStore(root).root == root


def test_an_explicit_repo_root_is_honoured(tmp_path):
    with pytest.raises(PtrWarmpoolViolationError):
        BodyStore(tmp_path / "store", repo_root=tmp_path)
    assert BodyStore(tmp_path / "store", repo_root=tmp_path / "elsewhere").root


def test_the_layout_is_sharded_and_keeps_the_extension(warmpool):
    store = BodyStore(warmpool)
    ref = store.put(b"body bytes", ext=".json")
    parts = ref.locator.split("/")
    assert len(parts) == 2
    assert parts[0] == ref.digest[:2]
    assert parts[1] == ref.digest + ".json"
    assert store.path_of(ref).is_file()


def test_an_extension_cannot_carry_a_path(warmpool):
    store = BodyStore(warmpool)
    with pytest.raises(PtrExtensionError):
        store.put(b"x", ext=".json/../../escape")


def test_a_missing_body_is_a_named_miss(warmpool):
    store = BodyStore(warmpool)
    ghost = ResourceRef(
        scheme="artifact", locator="ab/" + "c" * 64 + ".txt", hash="sha256:" + "c" * 64
    )
    with pytest.raises(PtrStoreMissError) as excinfo:
        store.get(ghost)
    assert excinfo.value.code == "PTR_STORE_MISS"


def test_a_locator_cannot_escape_the_root(warmpool):
    store = BodyStore(warmpool)
    escape = ResourceRef(
        scheme="artifact",
        locator="../../etc/passwd",
        hash="sha256:" + "d" * 64,
    )
    with pytest.raises(PtrStoreMissError):
        store.get(escape)


def test_default_root_lives_outside_the_repo():
    from ptr_engine import default_root

    root = default_root()
    assert root.is_absolute()
    repo = find_repo_root()
    assert repo is None or repo not in root.parents
