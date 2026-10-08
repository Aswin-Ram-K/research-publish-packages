# V4R — recovery verifier superseding V4 (lane builder · classifier · split rule)

**Batch** 4 · **Overall** PASS — recovery clean, U4.2's claims independently reproduced.
**Bound** ≤40 · **Spent** 35 tool calls · **LLM calls** 0 · **Occamy probes** 1 (`000`, crash-looping, restarted nothing)

## Recovery verdict

**No guard was left reverted.** V4's premise ("V4 died before finishing and left no report at all") is
**false**: `orchestration/handoffs/V4.json` (13833 B, mtime **06:20:40**) and `orchestration/units/V4.md`
exist and are current — its handoff was written *after* its revert cycles (code mtimes 06:16). Only the
`orchestration/VERDICTS.md` V4 section is missing (`grep V4` → no match).

Evidence for "clean tree":
- `state/verify/V4/*.bak` and `sha-before.txt` match the current file shas exactly (0 mismatches):
  `build.py 71da0d1e…`, `classify.py 783e75c1…`, `split.py 96a63ae1…`, `__init__.py 4add8c96…`.
- `classify.py:273` = `if guards["external_anchor"] and guards["measured_result"]:` and
  `split.py:91` = `return not (left_files & right_files)` — both intact.
- 0 revert tell-tales (`if False`, `assert False`, `assert 1 == 0`, `return None #`, `return True #`,
  `REVERT|TODO|XXX|FIXME`) across all four `lanes/*.py`.
- `23 passed in 0.05s` **before** my cycles (and again after).

`action_taken: none` — nothing needed restoring. I then ran my own revert/restore cycles to prove the
guards are live, and left the tree guard-intact (`sha` pinned, no `V4R-REVERT` marker remains).

## Checks

| id | check | verdict |
|----|-------|---------|
| C1 | `lanes.json#member_ids` vs `lane_candidates` — 5/5 equal, 0 in two lanes, 0 lost, 0 unlinked | **PASS** |
| C2 | red→green, independent, sha-proven: anchor guard + split rule | **PASS** |
| C3 | §3.6 truth table driven rule-by-rule (96-case sweep, 0 violations) | **PASS** |
| C4 | determinism: byte-identical under shuffle, no timestamp, persist-twice ids `[1..5]` | **PASS** |
| C5 | live refusal re-derived over the real store: `paper_refusals=5`, all `report` | **PASS** |
| C6 | honesty audit (`maturity`/`audience` computed, `thesis_source` derived, 0 splits) | **PASS** |
| T | containment: Duval `5cdc471a…` untouched, real store sha/rows unchanged | **PASS** |

### C1 — cross-unit membership (the check nobody had done)
All five lanes agree between the JSON and the store join; verified three ways
(`lane_candidate_ids`, `candidates_for_lane`, and the inverse `lanes_for_candidate`):

| slug | json_ids | store_ids | equal |
|---|---|---|---|
| claim-test-unreproduced | [9,10] | [9,10] | ✅ |
| decision-superseded | [7,8] | [7,8] | ✅ |
| delta-eval-measured | [5,6] | [5,6] | ✅ |
| invariant-stated | [3,4] | [3,4] | ✅ |
| inventory-novel | [1,2] | [1,2] | ✅ |

`in_two_lanes=0`, `lost=0`, `unlinked=0`, slug set and type/maturity/audience match the `lanes` table.
`materialize` can therefore trust the join — no docket can copy the wrong files.

### C2 — red→green (my own backups in `state/verify/V4R/`, pycache purged, `PYTHONDONTWRITEBYTECODE=1`)
- **(a) anchor guard** `classify.py:273` → `if guards["measured_result"]:` ⇒
  `test_paper_ineligible_lane_is_downgraded_to_report` **FAILS** with
  `IndexError: list index out of range` at `classify.py:277` ⇒ restore ⇒ sha `783e75c1…` equal
  (`SHA-A-OK`) ⇒ **1 passed**.
- **(b) split rule** `split.py:91` → `return True` ⇒
  `test_lane_with_non_independent_members_is_never_split` **FAILS** (`flint-spark` splits into
  `flint-spark-high` + `flint-spark-medium` on the maturity axis) ⇒ restore ⇒ sha `96a63ae1…` equal
  (`SHA-B-OK`) ⇒ **1 passed**. Full run after restoration: **23 passed**.
- Transcripts: `state/logs/V4R-redgreen.log`, `state/verify/V4R/logs/{A-red,A-green,B-red,B-green}.txt`.

### C3 — §3.6 truth table (driven through `guards_passed`/`guards_failed`, not by re-running fixtures)
- `paper` needs **both**: neither→`report`, anchor only→`report`, result only→`benchmark_card`,
  both→`paper`; an `EXTENDS` verdict anchors just like `CONFIRMS`.
- `benchmark_card`: value **with** command→`benchmark_card`; value with a **blank** command→`report`
  (`recomputable=false`); anchor + result-without-command→`paper` (paper does not require recomputability).
- Unknown/unverifiable ⇒ `memo`, never `paper`: the output vocabulary is closed at 5 labels
  (96-case sweep, 0 violations); an unrecognised *kind* yields `audience="technical readers"` and
  unrecognised material falls through to `memo`. A bogus guard name raises `KeyError` rather than passing.
- Downgrade order confirmed literally: `report` (substantive thesis) → `blog` (short thesis, kinds+title)
  → `memo` (no kinds/title); "nothing verifiable" → `memo`.

### C4 — determinism / stability
Unshuffled vs shuffled (seed 20261008) vs reversed candidate input → **byte-identical** `lanes.json`
and `LANES.md`; slugs stable across order; the JSON carries exactly the 10 documented keys with **no**
`generated_at`/timestamp leak; persisting twice against a **copy** (lanes + links cleared first) yields
ids `[1,2,3,4,5]` both passes, 5 rows, 10 links, 0 duplicate rows.

### C5 — live refusal, re-derived
Rebuilt from the 10 real replay-sourced candidates (store has **0** claims/evidence/verdicts — that is
*why* nothing qualifies): 5 lanes × 2 members, `paper_refusals=5`, every lane
`type=report / maturity=medium / audience=practitioners / thesis_source=derived`. Verbatim rationale,
identical on all five and matching the persisted run:

> `type=report: paper refused (external_anchor=false (no CONFIRMS/EXTENDS verdict); measured_result=false (no measured result)); downgrade report <- substantive_thesis=true.`

### C6 — honesty audit
- **`maturity` — computed, not constant.** `build.py:422-445`: member level `high` when
  `verified_refs>0` and a measured result or external verdict, `medium` when `verified_refs>0`, else
  `low`; lane level `high` if all high, `medium` if ≥half non-low, else `low`. The live store exercises
  **only** the `medium` branch (all 10 candidates have verified provenance and none has a
  result/verdict), so the live uniformity is a property of the data — the fixture test
  (201=high / 202=medium / 205=low) is the only proof the other branches work.
- **`audience` — computed, not fixed.** `build.py:457-464`: `_KIND_AUDIENCE` markers per member kind,
  plus `evaluators` when a member has a measured result, resolved by `AUDIENCE_PRIORITY`. Live input
  contains only two kinds (`novel_primitive`, `invariant_or_enforcement`), both mapping to
  `practitioners`, so live is uniform again — and V4's "5 distinct audiences" figure is **fixture-only**.
- **`thesis_source` — `"derived"` on every lane, no model path.** It is the literal `"derived"` at
  `build.py:581`, preserved by `split.py:168`; `derive_thesis` emits fixed text from kind counts. There
  is no `occamy`/`openai`/`llm`/`http` import anywhere in `lanes/**`, so no internal path can produce
  model-written text while the field says `derived` (a future unit must deliberately flip it, as
  `build.py:29-31` documents).
- **"0 splits live" — true.** Calling `split_lane` over all 5 real lanes yields 0 splits. The rule is
  **fixture-proven only** (`dune-drift` → `-evaluators` + `-practitioners`). Judged thin but fair: the
  fixture is a genuine 2-member lane with disjoint provenance files and an audience disagreement, plus
  `flint-spark` (non-independent members) and `ember-gate` (homogeneous) negative cases — but no
  realistic store-shaped multi-audience input exists, because every live candidate collapses to
  `practitioners`.

## Findings / corrections (also in the handoff's `corrections[]`)

1. **Recovery premise wrong** — V4 did leave a complete PARTIAL handoff + unit card; only the VERDICTS
   section is missing.
2. **Batch-4 gate gap (plan, not code)** — §4 asks for "≥3 lanes, ≥2 types, split on a real multi-claim
   lane"; live is 5 lanes but **1 type** and **0 live splits**.
3. **§3.6 deviation** — the split rule is specified over "≥2 independent primary *claims*" but
   `split.py` operates on candidate `provenance_refs` (store has 0 claims), so it is unmeasurable on
   claims today.
4. **Doc inaccuracy (V4's finding confirmed)** — `tests/test_lanes_classify.py:9-18` predicts
   `AssertionError: assert 'paper' == 'report'`; the real revert fails with `IndexError` at
   `classify.py:277`.
5. **WAL/SHM** — at inventory only `state/state.sqlite` existed; after read-only URI reads a 0-byte
   `-wal` and 32768-byte `-shm` exist. Content sha and all row counts are unchanged and
   `PRAGMA wal_checkpoint` reports `(0,0,0)` frames, i.e. no data written. I did **not** delete the
   sidecars (a concurrent sibling may hold the DB).

No guard was reverted; the tree is left guard-intact with shas
`build 71da0d1e… / classify 783e75c1… / split 96a63ae1… / __init__ 4add8c96…`.

Artifacts: `orchestration/handoffs/V4R.json`, `orchestration/VERDICTS.md` (V4R section),
`state/logs/V4R-redgreen.log`, `state/verify/V4R/**`.
