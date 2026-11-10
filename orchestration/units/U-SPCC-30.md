# U-SPCC-30 — Corpus-wide fixture provenance loss, and an honest forward-only guard

## 1. Reproduction

Independent script, not the parent's numbers. Hash every on-disk document under
`experiments/ptr-engine/longrun` whose `schema` starts `consonance.longrun-fixture`
(**53 distinct digests**), then compare against every `fixture_sha256` pinned in
`experiments/ptr-engine/measure/rows-*.jsonl` (**7,734 pinned rows across 93 files**;
7,969 rows total, 235 carry no pin).

| rows file | rows | distinct pins | missing |
|---|---:|---:|---:|
| `rows-agg-fetch-mt36.jsonl` | 41 | 1 | 41 of 41 |
| `rows-agg-fetch-mt50.jsonl` | 54 | 1 | 54 of 54 |
| `rows-agg-fetch-r1.jsonl` | 10 | 1 | 10 of 10 |
| `rows-agg-fetch-test.jsonl` | 36 | 1 | 36 of 36 |
| `rows-agg-fetch-test2.jsonl` | 37 | 1 | 37 of 37 |
| `rows-agg-masking-r1.jsonl` | 100 | 1 | 100 of 100 |
| `rows-hop-2026-11-09.jsonl` | 450 | 1 | 450 of 450 |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | 2 | 27 of 29 |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | 1 | 40 of 40 |
| `rows-longrun-2026-10-26.jsonl` | 192 | 1 | 192 of 192 |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | 1 | 96 of 96 |
| `rows-smoke-tx01-20261109.jsonl` | 16 | 1 | 16 of 16 |
| `rows-sup-2026-11-09.jsonl` | 269 | 1 | 269 of 269 |
| **total** | | | **1,368 of 7,734 (17.7%)** |

Six distinct missing digests: `2b416d82…` (278), `09157d80…` (450), `12f46fcd…` (269),
`72c3832d…` (259), `5a5f8c4b…` (96), `db497435…` (16). The parent's table reproduces exactly.

## 2. Per-file cause, with evidence

Fixture path comes from the run manifest (`fixture.path` / `provenance.fixture_sha256`),
matched by the row's `run_manifest_sha256`. Two of the six manifests live only under the
nested duplicate tree `experiments/ptr-engine/longrun/experiments/ptr-engine/longrun/manifests/`
(`dryrun-TX-HOP-*`, `dryrun-TX-SUP-*`, `longrun-2026-11-09T082853Z-*`, `longrun-2026-11-09T082138Z-*`),
which is why a `manifests/**` glob from the top level misses them.

| fixture | pin | path exists | current sha256 | mtime (UTC) | last consumer (UTC) | git ref with pin | class |
|---|---|---|---|---|---|---|---|
| `tasks-v7/TX-AGG.v1.json` | `2b416d82…` | yes | `178042c2…` | 2026-11-09T08:57:28Z | 08:49:43Z | none | overwritten in place |
| `tasks-v7/TX-HOP.v1.json` | `09157d80…` | yes | `860aad56…` | 2026-11-09T09:04:41Z | 08:31:49Z | none | overwritten in place |
| `tasks-v7/TX-SUP.v1.json` | `12f46fcd…` | yes | `75ab558b…` | 2026-11-09T08:51:33Z | 08:22:21Z | none | overwritten in place |
| `tasks-v7/TX-01.v1.json` | `db497435…` | yes | `44a1b435…` | 2026-11-09T06:13:23Z | 06:10:40Z | none | overwritten in place |
| `runtime/LR-01.json` | `72c3832d…` | yes | `b7e303a6…` | 2026-10-26T09:00:46Z | 08:39:28Z | none | overwritten in place |
| `tasks-v4/runtime-v4/LR-01.v4.json` | `5a5f8c4b…` | yes | `8bdb58ae…` | 2026-11-09T03:51:12Z | 2026-10-26T19:05:21Z | **`f17663d1fed0`** | overwritten in place, **recoverable** |

**Three-way classification: 13 of 13 files `overwritten in place`; 0 `never committed`; 0 `unexplained`.**
Every path exists, every current digest differs, and every `mtime` is later than the last run that
consumed the pinned bytes. `git log --all --format=%H -- <path>` returns at least one commit for all six
paths (`9fadcc9` for the four `tasks-v7` fixtures and `LR-01.v4`; `f17663d1` for `LR-01` and `LR-01.v4`),
so no path is absent from history — what is absent is the pinned *bytes*.

Blob check, because it decides the class: `git show 9fadcc9:experiments/ptr-engine/longrun/tasks-v7/TX-HOP.v1.json`
exits 0 with **95,742 bytes, sha256 `860aad56…`** (`git ls-tree 9fadcc9 -- <path>` → `100644 blob 30f75ee0…`).
The path *was* committed and the pin is not in it. `TX-SUP` is identical: 55,018 bytes, `75ab558b…`,
`100644 blob 94b7ffc3…`. An empty `git show` (`e3b0c442…`) would mean the path was absent from that commit;
that is not the case for any of the six.

**Recoverability split.** 12 files / 1,272 rows: pinned bytes never committed, no ref can restore them.
1 file / 96 rows (`rows-longrun-v4-2026-10-26.jsonl`): the pin **does** survive as
`f17663d1fed0:experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json`, sha256
`5a5f8c4be2027c53038ae31b4db60ebbae03996a5a650d8fb4fe6d872df5e235` — verified by hashing the blob.
That is the only recoverable fixture; nothing else is claimed recoverable.

**Recorded defect, separate from the loss.** The 20 manifests that consumed `LR-01` record the absolute
path `/home/zer0null/reserach extarctor/experiments/ptr-engine/longrun/runtime/LR-01.json` — a misspelling
of the repo root. That path never existed; a naive path-existence check therefore reports those 259 rows as
"path missing" rather than "digest differs".

## 3. Scope — the loss does not touch any live claim

Of the 93 `rows-*.jsonl` files, **80 have zero missing pins**. Every affected file is a first-generation
AGG/HOP/SUP run dated `2026-11-09` (plus the three `2026-10-26` `LR-01` files and `rows-smoke-tx01-20261109`),
and each was superseded by a later generation that pins a digest still on disk: `agg-8014`/`agg2`/`agg3`,
`hop-8014`/`hop2`/`hop3`, `sup2-fetch`/`sup2-masking`, `tx01-real`/`smoke2`/`contrast24`/`control-nomask`,
`longrun-c`/`v3`/`v4-tools`/`v5-tools`/`v6-tools`. The headline rows this ledger rests on —
`rows-tx02-*` (12/48), all eight `rows-tx03-*` including `:8014` (8/48, 41/48, 42/48, 4/48, 0/48, 9/48),
`rows-spcc-billedproof-2026-11-10` — are **0 missing** and fully reproducible.

## 4. Ledger

`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md`:
one new table row (`Corpus-wide fixture provenance loss`, 7 cells, table now 12 lines at 7 cells) and a new
`### Corpus-wide fixture provenance` subsection carrying the per-file table (15 lines at 10 cells), the
scoping table (7 lines at 3 cells), the three-way classification, the blob check, the recoverability split,
the `LR-01` path typo, and what the rows may and may not support.

## 5. Guard decision

`experiments/ptr-engine/longrun/tests/test_lost_fixture.py` froze 259 rows for the single digest `72c3832d…`.
The 1,368 are already lost and cannot be recovered, so freezing them is the baseline doing its job — but it
had to be a dated, documented freeze, not a silent widening.

- `state/logs/lost-fixture-baseline.json` (the path every existing doc names) rewritten to schema
  `consonance.lost-fixture-baseline/2` and **force-added** (`git add -f`), because `.gitignore:7` ignores
  `/state/` root-only on purpose. Without the force-add the guard would ship without its baseline and a
  fresh clone would fail on a missing file rather than on a lost fixture. A re-freeze must be force-added
  again; the test docstring says so. Contents:
  `frozen_at` `2026-11-10T00:00:00Z`, `audit` `U-SPCC-30`, a `note` naming this audit and the
  recoverable/unrecoverable split, a `digests` map (6 entries with fixture name, path, current sha256,
  current mtime, row count, recoverability), and all 1,368 `{file, line, digest}` rows.
- The test keeps set equality on `(file, line)` — **not** a count — so a new miss fails and so does swapping
  one frozen lost row for another. It also fails if a frozen row stops missing (stale baseline) and if a
  frozen row's digest is not a recorded lost digest or is on disk.
- The failure message now reads: *"A new miss means a fixture was destroyed after 2026-11-10T00:00:00Z (the
  dated freeze in state/logs/lost-fixture-baseline.json). Restore the fixture, or re-freeze deliberately with
  a new dated note naming the audit — never widen the baseline silently."*
- Pre-existing performance defect fixed: `misses()` called `fixture_digests()` once **per pin** (8,310 walks
  of the tree, ~5.5 min). The digest set is now hoisted and computed once. Assertions unchanged.

## 6. Proof

- Green: `.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_lost_fixture.py -q` →
  `1 passed in 0.18s`.
- Red on a synthetic new pin: a temporary `experiments/ptr-engine/measure/zzz-synthetic-probe.jsonl` with
  `fixture_sha256` `0000…0000` → `1 failed`, message
  `NEW row(s) pin a fixture_sha256 with no file on disk: experiments/ptr-engine/measure/zzz-synthetic-probe.jsonl:1.
  A new miss means a fixture was destroyed after 2026-11-10T00:00:00Z …`. Probe file removed; green re-confirmed.
- `python3 tools/doc_check.py` → `OK docs clean`, `exit=0`.

## 7. Not touched

`measure/rows-*.jsonl` (append-only, no edit), `measure/FIXTURE-MAP-MT36.note` (left as written),
`run_longrun.py`, `score_longrun.py`, every fixture document.
