# FIXTURE-GENERATIONS — one spec, one generator

**Unit:** `FIXTURE-GENERATIONS` · **Task:** LR-01 (`consonance.longrun-fixture/1`) · **Date:** 2026-10-26
**Spec of record:** [`LR-01.spec.json`](../experiments/ptr-engine/longrun/fixtures-spec/LR-01.spec.json)
**Generator:** [`build_fixture.py`](../experiments/ptr-engine/tools/build_fixture.py) · **Guard:** [`test_build_fixture.py`](../experiments/ptr-engine/longrun/tests/test_build_fixture.py)

Nothing in this document was deleted. Every fixture named *deletable* is a **recommendation**, to be
executed by a later card with the operator's word — this card wrote only the spec, the generator, the
tests and this ledger, and modified **zero** existing runtime fixtures.

## 1. Inventory, from disk

21 files carry `schema: consonance.longrun-fixture/1` and `task_id: LR-01`; they are **20 unique byte
documents** (`LR-01.v4.tools.json` and `manifests/v4tools2-baseline-tools.json` are the same digest,
`a592a48f…`) **plus one digest that survives with no file behind it**.

| path | generation label | gen | bytes | sha256 | class | frozen | refs | key referents |
|---|---|---|---|---|---|---|---|---|
| `experiments/ptr-engine/longrun/runtime/LR-01.json` | *(v1, unlabelled)* | 1 | 27111 | `b7e303a65f20…` | historical-frozen | frozen | 4 rows/grades · 25 manifests | `ROW-PROVENANCE.json`, `rows-longrun-2026-10-26-fix.jsonl` |
| `experiments/ptr-engine/longrun/tasks-v2/runtime-v2/LR-01.v2.json` | v2-bounded | 2 | 31301 | `0a07db1b14f3…` | historical-frozen | frozen | 2 rows/grades · 4 manifests | `ROW-PROVENANCE.json`, `rows-longrun-c-2026-10-26.jsonl` |
| `experiments/ptr-engine/longrun/tasks-v3/runtime-v3/LR-01.v3.json` | v3-answer-marker | 3 | 31780 | `07abab0bd902…` | historical-frozen | frozen | 4 rows/grades · 2 manifests | `ROW-PROVENANCE.json`, `rows-longrun-v3-2026-10-26.grade-v2.json` |
| `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json` | v4-slice-widened | 4 | 40295 | `5a5f8c4be202…` | historical-frozen | frozen | 3 rows/grades · 9 manifests | `ROW-PROVENANCE.json`, `rows-longrun-v4-2026-10-26.jsonl` |
| `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools.json` | v4-slice-widened | 5 | 40954 | `a592a48ff3e5…` | historical-frozen | frozen | 2 rows/grades · 2 manifests | `ROW-PROVENANCE.json`, `rows-longrun-v4-tools-2026-10-26.jsonl` |
| `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json` | v4-slice-widened | 6 | 41268 | `5bf5f6393946…` | historical-frozen | frozen | 3 rows/grades · 12 manifests | `ROW-PROVENANCE.json`, `rows-longrun-v5-tools.jsonl` |
| `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json` | v5-answer-contract | 7 | 42183 | `967cef03c362…` | live | frozen | 6 rows/grades · 1 manifests | `ARM-TREATMENTS.json`, `ROW-PROVENANCE.json` |
| `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json` | v6-coverage | 8 | 50254 | `ff89625df95d…` | live | frozen | 0 rows/grades · 0 manifests | derived: `LR-01.v7.json`, `LR-01.v8.json` |
| `experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json` | v7-answer-forms | 9 | 52004 | `42b4df007352…` | live | frozen | 3 rows/grades · 0 manifests | `FIXTURE-TREATMENTS.json`, `OPERATOR-BRIEF.json` |
| `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` | v8-treatments-reachable | 10 | 57242 | `0804b51575cc…` | live | frozen | 2 rows/grades · 3 manifests | `FIXTURE-TREATMENTS.json`, `H1-CONDITIONING.json` |

**The lost digest.** `72c3832d95f9c7966b4358eda10fa2882775a416ee8a663d57b1c871ed19c44d` is pinned by
`rows-longrun-2026-10-26.jsonl` (192 rows), `rows-longrun-2026-10-26-fix.jsonl` (29) and
`rows-longrun-2026-10-26-policy.jsonl` (40) — **261 rows** — and by no file on disk. That is a
hand-edited v1-lineage variant of `runtime/LR-01.json` (`b7e303a6…`) that was overwritten in place.
What those cells ran under survives only as a digest. It is recorded in the spec under `lost_fixtures`
and cannot be a variant: there are no bytes to reproduce.

**LR-02 … LR-06** are *siblings*, not generations: `runtime/LR-0[2-6].json` (v1) and
`tasks-v2/runtime-v2/LR-0[2-6].v2.json` (v2). No row file pins either set by sha256, so they are listed
as deletable in §5. Their digests appear in `orchestration/handoffs/ACCEPTANCE-AS-CHECKS.json` and
`orchestration/handoffs/V2-RUNTIME.json`.

## 2. How many generations, actually

The map said **4 generations / 16 runtime files**. Disk says:

| counted | value |
|---|---|
| distinct `fixture_version` labels | **8** — *(v1 unlabelled)*, `v2-bounded`, `v3-answer-marker`, `v4-slice-widened`, `v5-answer-contract`, `v6-coverage`, `v7-answer-forms`, `v8-treatments-reachable` |
| named variant documents (v4 exists in 3 byte forms) | **10** |
| files on disk carrying the fixture schema | **21** (20 unique digests + 1 duplicate) |
| digests pinned by row files with no file behind them | **1** (`72c3832d…`) |
| serialization dialects in use | **3** — v1-v4: `indent=2, ensure_ascii=False, trailing NL`; v5-v8: `indent=1, ensure_ascii=True`; v6 alone has **no** trailing newline |

So the map undercounted: it is **8 generations across 10 variant documents in 21 files**, and one of
them is gone. The v4 → v4.tools → v4.tools2 split is not a generation change but a **tool-policy**
change on the same document, which is exactly why a variant model — not a file convention — is needed.

## 3. The variant model

A variant is a **named merge over its predecessor**, never a copy:

```
v1 ── v2 ── v3 ── v4 ── v4.tools ── v4.tools2 ── v5 ── v6 ── v7 ── v8
```

- `base` is the v1 document. Every other variant carries a **deep merge-patch** of its parent:
  `null` deletes a key, an object recurses, any other value (including every list) replaces, and the
  reserved key `@order` sets that level's key order.
- `@order` exists because **dict insertion order is part of the bytes** and the original files were
  authored with keys appended at different levels — without it, regeneration reproduces the same JSON
  in a different order and the sha256 changes.
- Each variant records its own `emit` block (`indent`, `ensure_ascii`, `sort_keys`, `trailing_newline`),
  because the serialization dialects above are not cosmetic: rows pin sha256.
- The spec's `carried` block indexes where each required piece of content first appears:
  `system_prompt` and `turns` (the 48-turn plan) at v1, `objective` and `answer_budget` at v2,
  `answer_marker` at v3, `tools_channel` (per-turn tool policy) at v4.tools, `checkpoints` with
  `id`/`answer_spec`/pinned source range/expected answer form at v5, `sources` with pointer+revision at
  v5, and 12-coverage checkpoints at v6. `engine_root` (`/home/zer0null/Duval`, read-only) is declared
  once at the top.
- The generator refuses to overwrite frozen bytes (by recorded path **or** by digest) unless
  `--force-frozen`, and prints the rows that reference the fixture when it refuses. A variant is chosen
  by name: `--variant v6`. There is no other write path to a runtime fixture.

## 4. Live · historical-frozen · deletable

- **Live — 4** (`v5`, `v6`, `v7`, `v8`): pinned by a current arm, a treatment matrix, a current row file, or a test;
  `v6`/`v7` are also the `derived_from` parents of `v8`.
- **Historical-frozen — 6** (`v1`, `v2`, `v3`, `v4`, `v4.tools`, `v4.tools2`): no longer run, but at least one row/grade file on disk pins its
  sha256. Different bytes would silently detach those rows from the fixture they claim to have run
  under — which is why every variant is `frozen: true` in the spec.
- **Superseded and deletable — 11**, named in §5, **none deleted**.

## 5. Deletion recommendations (not executed)

| file(s) | why deletable | what to check first |
|---|---|---|
| `experiments/ptr-engine/longrun/runtime/LR-0{2,3,4,5,6}.json` (5) | v1 siblings; no row, grade or manifest pins their sha256 | the two handoffs that named them are historical |
| `experiments/ptr-engine/longrun/tasks-v2/runtime-v2/LR-0{2,3,4,5,6}.v2.json` (5) | v2 siblings; same | `orchestration/handoffs/V2-RUNTIME.json` is the only referent |
| `experiments/ptr-engine/longrun/manifests/v4tools2-baseline-tools.json` | byte-for-byte duplicate of `LR-01.v4.tools.json` (`a592a48f…`), stored under a *manifest* name | any manifest that opens it by that path |

Deleting those 11 files removes ~259 KB and no unique digest: every digest above stays represented by a
live variant, a frozen variant, or a row file's pin. The 261-row lost digest is unaffected either way.

## 6. The cost this would have saved

The map prices this at **10 rounds / 96 wasted requests / 16 runtime files across 4 generations**.
Against the inventory the file count is understated (21, not 16) and the generation count is understated
(8, not 4). The request figure is credible, but for a different reason than the map gives:
`rows-longrun-v3-2026-10-26.jsonl` and `rows-longrun-v4-2026-10-26.jsonl` are **exactly 96 rows each**,
so 96 requests is the price of **one** wasted re-authored round — the ten rounds the map counts would be
~960 requests, which makes 96 a conservative floor rather than the total.

## 7. Reproduction

```bash
# regenerate, never hand-edit
python3 experiments/ptr-engine/tools/build_fixture.py --variant v5 --out /tmp/LR-01.v5.json
# byte-identity, both frozen generations (sha256sum of the live files is unchanged)
sha256sum /tmp/LR-01.v5.json   # 967cef03c362446a3187c9a8517bb6867b03e680f9a673ab53e42bb9f06ab567
sha256sum /tmp/LR-01.v6.json   # ff89625df95dca6ae47dd24db72f43d83c24f9cd371e16938258ec03b7e946db
# drift gate: non-zero if any on-disk fixture has left the spec
python3 experiments/ptr-engine/tools/build_fixture.py --check
# guard (5 tests: (a) v5 sha, (b) v6 bytes, (c) drift named, (d) frozen refusal + rows, (e) spec/variants)
python3 -m pytest experiments/ptr-engine/longrun/tests/test_build_fixture.py -q   # 5 passed
```
