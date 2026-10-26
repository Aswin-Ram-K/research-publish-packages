# PTR-CORPUS-REPRO

**Purpose (one).** Make r = 30000/447 = 67.1141x reproducible by one command a reader can run — not only through a unit's handoff.

**Status: done.** All seven claimed values reproduce exactly; delta 0; nothing tuned.

## Where the corpus actually is

| what | artefact | note |
|---|---|---|
| the 12 bodies / 30,000 chars | `experiments/ptr-engine/examples/worked_example.py:45` (`corpus()`) | `TARGET_CHARS = 30_000` (:39), self-asserted 12 items (:82) and 30,000 chars (:83) |
| the index | `experiments/ptr-engine/ptr_engine/compile.py:222` (`compile_turn`) | scope `worked-example`, rev 1, block 64 |
| the prompt bytes | `experiments/ptr-engine/ptr_engine/adapter.py:74` (`build_prompt`) | empty resolve map = zero-resolution turn |

No corpus had to be invented or recovered from `/tmp`: the warmpool is a throwaway `mkdtemp` per run, so the bodies are **code**, regenerable — the kill condition does not apply.

## New artefact

`experiments/ptr-engine/tools/rebuild_corpus.py` (146 lines, stdlib only, 3.11+).
Imports `corpus()` from the worked example and the constants from that module (rev/scope/
block), then prints exactly eight lines and asserts none of them.

```
cd experiments/ptr-engine && python3 tools/rebuild_corpus.py
```

```
BODIES 12
BODY_BYTES 30000
INDEX_BYTES 447
INDEX_LINES 12
BYTES_PER_LINE 37.25
ZERO_RESOLUTION_PROMPT 472
INDEX_SHA256 e08700c9876162544ba0f6c73c47868f605d1ebfea2302d2b66eee866a099bd2
RATIO 67.1141
```

## Determinism (2 processes, 2 cwds, 2 warmpool roots)

run A from the repo → run B from `/tmp` with `PYTHONPATH=<repo>/experiments/ptr-engine` and `--warmpool-root /tmp/ptr-repro-root2`: `diff` empty, both captures sha256 `ddd2d143…488d`, same `INDEX_SHA256 e08700c9…9bd2`.
A third run from `/tmp` with no `PYTHONPATH` also matches (the script resolves the package from its own `__file__`), so the command needs no setup.

## Containment / bound

No existing file edited (`RECORD.md`, `ADOPTION.md`, `SPEC.md`, the package, the tests, rows, papers all untouched); writes only to the three declared paths plus removable `/tmp` roots.
`sys.dont_write_bytecode` + `PYTHONDONTWRITEBYTECODE=1`; sweep for new `*.pyc`: none. No network, no endpoint, no container, no git. Tool calls: 23 of 25.
