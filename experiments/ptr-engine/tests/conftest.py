"""Shared fixtures. Every warmpool root here lives outside the repository tree.

If a fixture used a path under the repo, the engine would refuse it -- that is the
point of ``tests/test_warmpool.py``, and it would make every other test fail for the
wrong reason.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ENGINE_ROOT = Path(__file__).resolve().parents[1]
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from ptr_engine import BodyStore, Ledger, Scope, compile_turn  # noqa: E402
from ptr_engine.store import find_repo_root  # noqa: E402

SCOPE = "sess-01"
REVISION = 3
BLOCK_SIZE = 64


@pytest.fixture(scope="session", autouse=True)
def _warmpool_is_outside_repo(tmp_path_factory):
    """A guard, not a test: refuse to run if the temp root lands inside the repo."""
    root = tmp_path_factory.mktemp("ptrw")
    repo = find_repo_root()
    assert repo is not None, "the engine must be able to find its own repository"
    assert repo not in root.resolve().parents and root.resolve() != repo, (
        f"pytest tmp root {root} is inside the repository {repo}"
    )


@pytest.fixture
def warmpool(tmp_path: Path) -> Path:
    root = tmp_path / "warmpool"
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def store(warmpool: Path) -> BodyStore:
    return BodyStore(warmpool)


@pytest.fixture
def ledger(warmpool: Path) -> Ledger:
    return Ledger(warmpool / "ledger.jsonl", block_size=BLOCK_SIZE)


@pytest.fixture
def material() -> list[dict]:
    """Twelve items, one of them with a JSON pointer, one with a projection."""
    items: list[dict] = []
    for n in range(1, 10):
        items.append(
            {
                "kind": "knowledge",
                "id": f"k{n:02d}",
                "body": f"knowledge note {n}: " + ("filler " * (5 * n)).strip(),
            }
        )
    items.append(
        {
            "kind": "artifact",
            "id": "plan",
            "body": json.dumps(
                {"goal": "resolve lazily", "tools": ["fetch"], "rev": REVISION},
                sort_keys=True,
            ),
            "pointer": "/goal",
            "ext": ".json",
        }
    )
    items.append(
        {
            "kind": "memory",
            "id": "m01",
            "body": "a remembered preference: never prefetch",
            "projection": "brief",
        }
    )
    items.append({"kind": "decision", "id": "D-1", "body": "resolution is one-way"})
    return items


@pytest.fixture
def index(material, store):
    return compile_turn(
        material, revision=REVISION, scope=SCOPE, block_size=BLOCK_SIZE, store=store
    )


@pytest.fixture
def scope(index) -> Scope:
    return Scope(name=SCOPE, index=index)
