# LONGRUN — long-run task suite

Fixture unit for the long-run objective (p95 TTFT, tokens-to-verified-success, quality of work produced).
Shipped by unit `LONGRUN-TASK-SUITE`, 2026-10-26, offline, zero model requests.
Fixtures: `fixtures/LR-0N.json`, schema `consonance.fixture/1` (`handoff from consonance/INTERFACE_CONTRACT.md` §4).
`experiments/ptr-engine/LONGRUN-PREREG.md` was a 4-line stub when read and card `59965afa` is not on the
board, so the four arm definitions in §5 are stated here as an explicit assumption (also in the handoff
`assumptions`). Nothing in this suite runs a model; every check is a file/grep/arithmetic check.

## 1. The six tasks

### LR-01 · repo-fix · 48 turns · checkpoints 12/24/46 · repair 30
Objective: every `resolve()` refusal writes its ledger row **before** it raises, including the argument
guards that currently raise outside the recorded block (`ptr_engine/resolve.py#L66-L110`).
Long-run: 48 read→edit→pytest cycles; the transcript grows by one test log and one refusal case per cycle.
Verifiable: one ledger row per refusal, `code` per path, `tests/test_scope.py` (9 tests) still green.
Repair trap (§3): the funnel assumption — not every refusal reaches `_refuse` (`ptr_engine/resolve.py#L66-L95`).

### LR-02 · multi-file-refactor · 64 turns · checkpoints 16/32/62 · repair 38
Objective: give every `PtrError` subclass a distinct machine-readable `code` and one deterministic registry
built from the class tree (`ptr_engine/errors.py#L15-L142`), with no code string edited.
Long-run: 64 turns across two files plus the negative-control suite; each code collision found late must be
reconciled with all earlier edits, so the working set grows monotonically.
Verifiable: `len({code}) == len(subclasses)` computed from the module; the seven refusal codes distinct.
Repair trap: the registry was built in `resolve.py` on an assumed enumeration (see §3), but codes are per class.

### LR-03 · bug-fix-with-test · 56 turns · checkpoints 14/28/54 · repair 34
Objective: `compact_index` must keep the `@N` revision of a ref that carries one and strip it only from the
hashed form (`ptr_engine/quantise.py#L422-L469`, `_strip_revision` at `#L455`).
Long-run: 56 turns; the compact form is re-derived for every index fixture turn, and each re-derivation
carries the previous turns' assumptions about hash width.
Verifiable: `COMPACT_MAGIC == "ptr-index/1c"`, `COMPACT_HASH_CHARS == 6`, revision survives a round trip.
Repair trap: 8-char hash width assumed from `compile.py#L39` (`HASH_PREFIX_LEN = 8`); the compact form uses 6.

### LR-04 · constraint-survival · 40 turns · checkpoints 10/20/38 · repair 26
Objective: speed up the billing path while preserving the measured avalanche discontinuity
(`ptr_engine/quantise.py#L336-L366`).
Long-run: 40 turns of narrowing a hot path; each refactor re-evaluates earlier turns' arithmetic against the
same law, and the correctness of every prior number depends on the residue branch not being dropped.
Verifiable: `predict_billed(128,10,64) == (138, True)`, `predict_billed(100,10,64) == (46, False)`,
`quick_bill(65,10,64) == 140`, `PtrAnnotationError` on negative `P1`.
Repair trap: "the bill is linear in the appended tokens" — false exactly when `P1 % B in {0,1}`.

### LR-05 · adversarial-debug · 72 turns · checkpoints 18/36/70 · repair 44
Objective: `BodyStore.path_of` must refuse any locator that escapes the warmpool root without weakening
content addressing (`ptr_engine/store.py#L88-L140`).
Long-run: 72 turns of adversarial cases; the case list grows, and each new escape attempt is judged against
the hashing contract fixed at turn 3, so early context must survive the whole run.
Verifiable: `content_hash(b"abc")` is `sha256:` + 64 hex, `../x.txt` locator → `PtrStoreMissError`,
`tests/test_roundtrip.py::test_store_refuses_a_tampered_body` green.
Repair trap: "a locator is safe because its dirname is a hash prefix" — the locator comes from the `ResourceRef`.

### LR-06 · doc-sync · 60 turns · checkpoints 15/30/58 · repair 40
Objective: the scope budget is documented and enforced at its real default, 64 refs per turn, with
`Scope.block()` falling back to the index block size (`ptr_engine/resolve.py#L39-L64`).
Long-run: 60 turns; the doc text, the code and two tests are edited in alternating turns, each edit citing
earlier ones, so an early wrong default propagates into prose, code and test.
Verifiable: `DEFAULT_MAX_REFS == 64`; the 65th ref in a turn raises `PtrBudgetExceededError`;
`test_the_budget_is_per_turn_and_configurable` and `test_a_bigger_budget_admits_more` green.
Repair trap: a turn-6 instruction asserts "128 was agreed"; the true default is 64 and the earlier edits go.

## 2. Turn counts and checkpoint schedule

| task | class | turns | plant | checkpoints (¼ / ½ / end) | repair | verify |
|---|---|---|---|---|---|---|
| LR-01 | repo-fix | 48 | 2 | 12 / 24 / 46 | 30 | 48 |
| LR-02 | multi-file-refactor | 64 | 3 | 16 / 32 / 62 | 38 | 64 |
| LR-03 | bug-fix-with-test | 56 | 2 | 14 / 28 / 54 | 34 | 56 |
| LR-04 | constraint-survival | 40 | 1 | 10 / 20 / 38 | 26 | 40 |
| LR-05 | adversarial-debug | 72 | 3 | 18 / 36 / 70 | 44 | 72 |
| LR-06 | doc-sync | 60 | 2 | 15 / 30 / 58 | 40 | 60 |

Total turns **340** (mean 56.7, min 40, max 72). 18 checkpoints, 6 repair traps.
Each checkpoint re-asks a fact planted in the first three turns; the fixture's `checkpoints[].source` names
the file and line that carries it, and every pointer is range-checked against the pinned file at build time.

## 3. Repair trap

A repair trap is a turn at which the correct action is to *undo* an earlier, locally reasonable assumption.
The run's own log makes it countable: `repair_turns` counts turns whose instruction is classified `repair`
plus turns that reverse an earlier edit (the fixtures mark them `kind: "repair"`).
All six tasks carry one; LR-01/LR-03/LR-06 are the sharpest because the wrong assumption is cheap and the
repair is expensive (it invalidates several earlier turns of work).

## 4. Scoring contract

Deterministic (no judge): exit status of each `python3 -c` assertion in `acceptance.checks`; pytest exit
status on the named test files; grep counts for "no occurrence of …"; presence of the named symbol/constant;
arithmetic on the documented law.
`MEASURE_UNVERIFIABLE` (marked in the fixtures, never scored): whether the error taxonomy is "complete for
future errors" (LR-02) and whether the new docstring "explains the reason for 64" (LR-06). No proxy score is
invented for these two; a run is not credited either way.
Negative constraints are checked by diff inspection (`git diff` on the run's copy, not the fixture): a
forbidden edit is a failure, not a deduction.

## 5. What each arm should do differently

Arms are now taken from `experiments/ptr-engine/LONGRUN-PREREG.md#L28-L34` — that file was a 4-line stub when
this unit first read it and another unit completed it mid-build (recorded in the handoff, not hidden).
- `transcript-grow` (A) — whole history replayed verbatim, FIFO truncation from the front at the window;
  should pass the ¼ and ½ checkpoints, then lose the turn-3 fact late (LR-05 turn 70).
- `transcript-compact` (B) — state updated at the wall, older turns replaced by a ~700-token digest, recent 4
  turns kept raw; should pass the ½ checkpoint and miss a constant compacted away (LR-03 turn 54).
- `pointer-stable` (C) — frozen index prefix + bodies appended in the suffix + next body prefetched; flat
  prompt; should hold every checkpoint and pay read latency (prereg: 0.182 s passive vs 0.602 s pointer).
- `lease-reopen` (D) — close at the wall, reopen from pointers plus a <=400-token state line at the prereg's
  turns 23 and 56; should fail a checkpoint whose fact never entered that line (LR-06 turn 58).
A repaired assumption (LR-01/LR-03/LR-06) is exactly what the digest and the state line tend to drop, so the
suite separates flat-context arms from the grow arm on long runs *and* makes the repair cost countable.

## 6. Freshness — which source carries each checkpoint fact

| fact | source |
|---|---|
| default per-turn budget 64; `Scope.block()` fallback | `experiments/ptr-engine/ptr_engine/resolve.py#L39-L64` |
| 31 `Ptr*` classes, `PTR_ERROR`, `PTR_PROJECTION_UNENUMERATED` | `experiments/ptr-engine/ptr_engine/errors.py#L15-L57` |
| `COMPACT_MAGIC`, `COMPACT_HASH_CHARS=6`, `_strip_revision` | `experiments/ptr-engine/ptr_engine/quantise.py#L63-L68`, `#L455` |
| avalanche on residue {0,1}; `predict_billed`; `quick_bill` | `experiments/ptr-engine/ptr_engine/quantise.py#L336-L366` |
| `content_hash` prefix, `{digest[:2]}/{digest}{ext}` locator, escape refusal | `experiments/ptr-engine/ptr_engine/store.py#L88-L140` |
| 9 scope tests, budget tests, tampered-body test | `experiments/ptr-engine/tests/test_scope.py#L16-L80`, `test_roundtrip.py#L51` |
