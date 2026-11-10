# U-SPCC-12 — record the overwritten-fixture finding and the rule that prevents a repeat

**Unit:** U-SPCC-12 · **Status:** done · **Date:** 2026-11-10
**Inputs:** `orchestration/handoffs/U-SPCC-10.json` (provenance investigation, classification `unverifiable`), `measure/FIXTURE-MAP-MT36.note` (143 lines), `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md`

## 1. The finding, recorded where a reader will hit it

`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` — one new row in the existing
7-column table (`Finding | Number | Units | Source | Generation | Replicates on :8012 / :8014 | Status`),
plus `### What those 278 rows may and may not support` directly beneath the table (20 inserted lines, 0 removed).

Row status: **VERIFIED (pin absent, rewrite timestamped; provenance unverifiable)**. Replicates column:
**not comparable** — all 278 rows carry `claim: none`, `comparison_eligible: false`.

The subsection pins the timeline to the second rather than to "recently":

| fact | value |
|---|---|
| in-place rewrite | `2026-11-09T08:57:28Z` (mtime = ctime) |
| last consuming run | `longrun-2026-11-09T084942Z-bounded-context-fetch-r1` at `08:49:43Z` |
| manifests recording `2b416d82…` | 20, from `08:21:44Z` to `08:49:43Z` |
| preservation commit | `9fadcc9` — already carries the **rewritten** bytes, so no pre-rewrite blob exists in any ref |
| identifiers preserved | `gen-7`, `TX-AGG.v1`, N=100, `wall_tokens 4312` |
| ground truths changed | 26/26 embedded checkpoints agree on id/turn/question/source, 0 identical on `expected` (`g00.d2` 20786 → 156145; `g01.d2` 60786 → 210513; `g00.d6` 10131 → 51443; `g02.d2` 100786 → 269767; `g01.d6` 30131 → 84932; `g03.d2` 140786 → 268509) |

May support: per-row recorded measurements; that a run with the row's run id loaded bytes hashing
`2b416d82…`; grading against each row's own recorded `expected`.
May not support: reproducibility (prefix unrebuildable); substitution of current fixture values;
cross-arm comparability; any `ABSENT = 0` reading.

## 2. The rule, recorded where fixtures are generated

No script generates `tasks-v7/TX-AGG.v1.json` (`grep -rn "TX-AGG" experiments/ptr-engine/tools
experiments/ptr-engine/longrun --include=*.py` hits only `longrun/tests/test_tx_agg.py`); the fixtures there
are authored/adapted artifacts. The generator that governs runtime fixture bytes is
`experiments/ptr-engine/tools/build_fixture.py` ("the single generator"), and the doc that describes fixtures is
`docs/FIXTURE-GENERATIONS.md`. Both now carry the rule:

- `build_fixture.py` module docstring: `FIXTURE IDENTITY RULE -- a fixture is identified by its path *and* its
  digest … write a new versioned path (`TX-AGG.v2.json`, a fresh `--out`), and it must never overwrite the
  previous version in place, because rows pin the digest and identity-by-path silently becomes false.`
  It names the `TX-AGG` incident, the timestamp and the note, and states that nothing repairs a rewrite after the fact.
- `docs/FIXTURE-GENERATIONS.md` new `## 8. Fixture identity rule — path **and** digest`: the rule, the TX-AGG
  evidence, and the pointer to the generator's existing narrow guard (`--out` onto a frozen fixture exits `3`
  unless `--force-frozen`; its message already says "prefer writing to a new path").

## 3. Path note for the reader

The provenance note is at repository-root `measure/FIXTURE-MAP-MT36.note` (as `U-SPCC-10.json` records), **not**
under `experiments/ptr-engine/measure/` where the sibling `FIXTURE-MAP-ABS2.note` lives. The ledger row cites the
real path; the note was not moved or edited by this unit.

## 4. Not touched

Rows, `tasks-v7/TX-AGG.v1.json`, `tests/test_lost_fixture.py`, `measure/FIXTURE-MAP-MT36.note`,
`docs/STATE.md`, `orchestration/STATUS.md`, `orchestration/VERDICTS.md`, `run_longrun.py`, `score_longrun.py`.
