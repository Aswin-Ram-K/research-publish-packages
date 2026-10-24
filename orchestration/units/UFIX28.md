# UFIX28 — Regenerate stale `disagreements.jsonl` + reconcile census totals

**Purpose (one):** mechanically regenerate the shipped stale `second-labeller/disagreements.jsonl` from the
shipped fixture using the shipped tools, decide/report on `metrics.json`'s four extra keys, and in one short
section reconcile the scanner-dependent census totals.

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Bound:** 20 tool calls. STOP and report if any cited figure in `papers/encoder-crossover-190/` moves.

**Reads allowed:** anything. **Writes (only):**
- `strategy/STALE_RECORD_FIX.md`
- `orchestration/units/UFIX28.md`
- `orchestration/handoffs/UFIX28.json`
- `scratch/ufix28/**`

**Never touch:** `scratch/uoutside1/tree-seven`, `scratch/utool1/tree-six`, `/home/zer0null/Duval` (read-only,
`--no-optional-locks` only), `/home/zer0null/research-publish-packages`.

## Steps
1. Copy `scratch/uoutside1/tree-seven` → `scratch/ufix28/tree-seven` (parse_fixture.py:172-177 writes in-place).
2. Read `second-labeller/compare.py` + `parse_fixture.py`; determine the exact pipeline.
3. Regenerate `disagreements.jsonl`; row count before/after; confirm 18 disagreements.
4. Compare before/after text (literal); scan `papers/encoder-crossover-190/` for moved figures.
5. Assess `metrics.json` extra keys (`_correction`, `limitation`, `passes.labelsB.json.limitation`,
   `routeB_primary.limitation`) — additive vs value-changing; recommend only.
6. If regenerated: rebuild `MANIFEST.json` from disk, independent checker (0 missing/0 hash/0 size/0 unlisted),
   sha256 + `counts.bytes_total`, build twice for idempotence.
7. Census: find file:line divergence between the 2,171-inside scanner and the 2,778-inside scanner; name which
   definition matches other published census figures; state the number to quote forward.

## Status
DONE (20-call bound, enclosed). Result in `strategy/STALE_RECORD_FIX.md`.

- Regenerated `disagreements.jsonl` mechanically on the copy with the shipped `parse_fixture.py`+`compare.py`:
  **18 rows → 18 rows, same 18 ids**, 18/18 rows differ (keys `F14/F55/F33/F31` → `F22/F40/F56/F30`,
  rationale non-empty → empty, line −40, 3/18 questions re-redacted). No field hand-edited.
- `metrics.json` shared values changed **0**; the four extra keys (`_correction`, `limitation`,
  `passes.labelsB.json.limitation`, `routeB_primary.limitation`) are **additive annotations** →
  recommend keep-and-annotate-as-hand-curated; **no action taken**.
- No figure in `papers/encoder-crossover-190/` moves; nothing to stop for.
- MANIFEST regenerated on the copy; independent checker 0 missing / 0 hash / 0 size / 0 unlisted / 0 absent;
  sha256 `f4f4b3741e9c82325096c598f5c18eebb7450f88f9d9d52d3ec2fed92317581c`, `counts.bytes_total=3162709`;
  two builds identical `files[]`. `disagreements.jsonl` idempotent
  (`d9d1f33bf3d12d74cba7160b8b981b593af8f5b09b8a6dd2b9e48f9c21f647b3`).
- JOB 2: **no scanner definition differs.** `census_one.py`, `census_uver13.py`, `outside_scan.py` all return
  **2,171 inside / 1,094 outside / 78 keys** on the 45-file shipped tree. `census7.txt`'s 2,778/1,101 came from
  a **48-file tree** carrying the `parse_fixture.py` intermediates (`cases.json` alone: +299 inside; all three:
  2,769). Quote forward **2,171 inside / 1,094 outside**, label "decoded-value walk, 45-file shipped tree".
