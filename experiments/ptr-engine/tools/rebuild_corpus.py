#!/usr/bin/env python3
"""Rebuild the pointer engine's worked-example corpus and print its numbers.

    python3 experiments/ptr-engine/tools/rebuild_corpus.py
    cd /tmp && PYTHONPATH=/path/to/experiments/ptr-engine \\
        python3 /path/to/experiments/ptr-engine/tools/rebuild_corpus.py

WHERE THE CORPUS ACTUALLY LIVES
    The 12 bodies have exactly one definition on disk:
    ``examples/worked_example.py:corpus()``. This script imports that function
    instead of restating it, so the corpus cannot drift between the worked
    example and the reproduction. The index is built by
    ``ptr_engine.compile.compile_turn`` and the prompt by
    ``ptr_engine.adapter.build_prompt``; revision, scope and block size are read
    from the example module, not re-typed here (an earlier pass with a different
    scope name produced a 442-byte index, so those constants matter).

WHY IT PRINTS INSTEAD OF ASSERTS
    Every value below is measured from the objects the engine returned. Nothing
    is compared against the expected 30000 / 447 / e08700c9… and nothing is
    rounded towards them: if the tree drifts, the printed line drifts with it and
    a verifier's diff names the mismatch. A script that failed on drift would be
    a guard (useful, but then no number is quoted); a script that forced a match
    would be a fraud.

OUTPUT — exactly eight lines, stable order, so ``diff`` can compare two runs:

    BODIES 12
    BODY_BYTES 30000
    INDEX_BYTES 447
    INDEX_LINES 12
    BYTES_PER_LINE 37.25
    ZERO_RESOLUTION_PROMPT 472
    INDEX_SHA256 e08700c9876162544ba0f6c73c47868f605d1ebfea2302d2b66eee866a099bd2
    RATIO 67.1141

    BODY_BYTES  = sum of the UTF-8 encoded body lengths
    BYTES_PER_LINE = index bytes / index lines, two decimals
    ZERO_RESOLUTION_PROMPT = prompt bytes when no ref is resolved (the index alone)
    RATIO = BODY_BYTES / INDEX_BYTES, four decimals

The warmpool root is a fresh temporary directory (or ``--warmpool-root``) and is
removed afterwards unless it was supplied by the caller. Python 3.11+, standard
library only, no network. Byte-compilation is disabled for the engine import so a
run writes no ``__pycache__`` into the tree.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path
from types import ModuleType

sys.dont_write_bytecode = True  # never drop .pyc files into the engine package

TOOLS_ROOT = Path(__file__).resolve().parent
ENGINE_ROOT = TOOLS_ROOT.parent
EXAMPLE = ENGINE_ROOT / "examples" / "worked_example.py"

if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from ptr_engine import BodyStore, Ledger, build_prompt, compile_turn  # noqa: E402


def load_example(path: Path) -> ModuleType:
    """Import the worked example by path -- it is not an importable package."""
    if not path.is_file():
        raise SystemExit(f"corpus source missing: {path}")
    spec = importlib.util.spec_from_file_location("_ptr_worked_example", path)
    if spec is None or spec.loader is None:  # pragma: no cover - hostile environment
        raise SystemExit(f"cannot load corpus source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "corpus"):
        raise SystemExit(f"{path} has no corpus() -- wrong artefact?")
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild the worked-example corpus and print its eight numbers."
    )
    parser.add_argument(
        "--warmpool-root",
        type=Path,
        default=None,
        help="warmpool directory to use (default: a fresh temp dir; must be "
        "outside the repository, which the engine enforces with "
        "PTR_WARMPOOL_INSIDE_REPO)",
    )
    args = parser.parse_args(argv)

    example = load_example(EXAMPLE)

    # Corpus + compile parameters: single source of truth is the example module.
    material = example.corpus()
    revision = example.REVISION
    scope_name = example.SCOPE
    block_size = example.BLOCK_SIZE

    supplied_root = args.warmpool_root is not None
    root = (
        Path(args.warmpool_root).resolve()
        if supplied_root
        else Path(tempfile.mkdtemp(prefix="ptr-rebuild-corpus-"))
    )
    try:
        store = BodyStore(root)
        ledger = Ledger(root / "ledger.jsonl", block_size=block_size)

        body_bytes = sum(len(str(item["body"]).encode("utf-8")) for item in material)
        index = compile_turn(
            material,
            revision=revision,
            scope=scope_name,
            block_size=block_size,
            store=store,
        )

        lines = len(index.lines)
        index_bytes = index.index_size
        per_line = f"{index_bytes / lines:.2f}" if lines else "n/a"
        ratio = f"{body_bytes / index_bytes:.4f}" if index_bytes else "n/a"
        zero_prompt = len(build_prompt(index, {}, ledger).encode("utf-8"))

        print(f"BODIES {len(material)}")
        print(f"BODY_BYTES {body_bytes}")
        print(f"INDEX_BYTES {index_bytes}")
        print(f"INDEX_LINES {lines}")
        print(f"BYTES_PER_LINE {per_line}")
        print(f"ZERO_RESOLUTION_PROMPT {zero_prompt}")
        print(f"INDEX_SHA256 {index.index_sha256}")
        print(f"RATIO {ratio}")
        return 0
    finally:
        if not supplied_root:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
