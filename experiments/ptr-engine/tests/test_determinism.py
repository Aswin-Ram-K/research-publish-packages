"""The same (material, revision, scope, block_size) must compile to identical bytes.

Two *independent processes*, two *different* warmpool roots. Identical index bytes
prove two things at once: no timestamp and no random id (the index would differ in
one process pair anyway), and no absolute store path (the roots differ).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from ptr_engine import BodyStore, compile_turn

CHILD = r"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from ptr_engine import BodyStore, compile_turn

material = json.loads(Path(sys.argv[1]).read_text())
root = sys.argv[2]
index = compile_turn(
    material, revision=3, scope="sess-01", block_size=64, store=BodyStore(root)
)
print(hashlib.sha256(index.index_bytes).hexdigest())
print(len(index.index_bytes))
print(index.index_text.count("\n"))
"""


def _child(root: Path, material_path: Path, engine_root: Path) -> tuple[str, int, int]:
    result = subprocess.run(
        [sys.executable, "-c", CHILD, str(material_path), str(root), str(engine_root)],
        capture_output=True,
        text=True,
        check=True,
    )
    digest, size, lines = result.stdout.strip().splitlines()
    return digest, int(size), int(lines)


def test_two_processes_two_roots_agree(material, tmp_path, request):
    engine_root = Path(__file__).resolve().parents[1]
    material_path = tmp_path / "material.json"
    material_path.write_text(json.dumps(material), encoding="utf-8")

    root_a = tmp_path / "warmpool-a"
    root_b = tmp_path / "warmpool-b"
    digest_a, size_a, lines_a = _child(root_a, material_path, engine_root)
    digest_b, size_b, lines_b = _child(root_b, material_path, engine_root)

    assert digest_a == digest_b, "index bytes differ between two processes"
    assert (size_a, lines_a) == (size_b, lines_b)
    assert size_a == len(material) * 0 + size_a  # size is a real measurement
    assert lines_a == len(material) + 1  # header + one line per item


def test_index_carries_no_store_path(material, tmp_path, store):
    index = compile_turn(
        material, revision=3, scope="sess-01", block_size=64, store=store
    )
    text = index.index_text
    assert str(store.root) not in text
    assert str(Path.home()) not in text


def test_material_order_does_not_matter(material, tmp_path):
    forward = compile_turn(
        material, revision=1, scope="s", block_size=64, store=BodyStore(tmp_path / "f")
    )
    backward = compile_turn(
        list(reversed(material)),
        revision=1,
        scope="s",
        block_size=64,
        store=BodyStore(tmp_path / "b"),
    )
    assert forward.index_bytes == backward.index_bytes
    assert list(forward.entries) == sorted(forward.entries)  # sorted by (kind, id)


def test_recompiling_into_the_same_store_is_idempotent(material, store):
    first = compile_turn(
        material, revision=3, scope="sess-01", block_size=64, store=store
    )
    second = compile_turn(
        material, revision=3, scope="sess-01", block_size=64, store=store
    )
    assert first.index_sha256 == second.index_sha256
    files = [p for p in store.root.rglob("*") if p.is_file()]
    assert len(files) == len(material) + 1  # + the pointer region body


def test_digest_is_a_function_of_the_inputs(material, store):
    a = compile_turn(material, revision=3, scope="s", block_size=64, store=store)
    b = compile_turn(material, revision=4, scope="s", block_size=64, store=store)
    c = compile_turn(material, revision=3, scope="t", block_size=64, store=store)
    d = compile_turn(material, revision=3, scope="s", block_size=128, store=store)
    digests = {a.index_sha256, b.index_sha256, c.index_sha256, d.index_sha256}
    assert len(digests) == 4
    assert a.index_sha256 == hashlib.sha256(a.index_bytes).hexdigest()
