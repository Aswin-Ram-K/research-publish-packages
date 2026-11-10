# COMBINED-CONTEXT-SERVING — measured result

Date: 2026-11-05. Cell: `experiments/context-cache/cells/COMBINED-CONTEXT-SERVING`.
Plan of record: `local://combined-context-serving-plan.md` (10 steps; gate = quality first, then ≥10 % lower cost per verified success).

## Question

Does folding the context into dense typed records — and masking old work turns behind references — make a long agentic run cheaper per verified success than appending the transcript verbatim, on the same tasks under one engine fingerprint?

## Configuration actually executed

| Item | Value |
|---|---|
| Envelope | `run/envelopes/CCS.json` **rev 5** — 144 calls, arms A/B/C × tasks T1/T2/T3/T4 × 12 turns |
| Output budget | 2,400 tokens, thinking **off** (driver default) |
| Engine | occamy-1.0, container `gx10-occamy-nvfp4`, image `72457f09d20e`, 131,072 context |
| Fingerprints at send time | model `4d01ef81`, tokenizer/template `bd733fb8`, renderer `86c8adeb`, engine `e641bf9c` |
| Calls | 144 sent, 144 rows, 0 errors, 0 empty texts |
| Budget used | 208 of 1,500 reserved (ledger `SPENT-CCS.json`) |
| Production | 0 restarts, 0 flushes, six restore keys unchanged |

`envelopes/CCS.json` rev 6 (3,200 tokens) was written to a path the driver does not read and was **never used**; it is marked void in its own revision list, and `envelopes/ENVELOPE-RECONCILIATION.md` names which file governs which run id.

Arms: **A** verbatim append-only transcript; **B** dense typed records (answer ≤240 chars, full-digest references, no bodies inlined); **C** = B plus masking of work turns older than turn 6.

## Result

| Arm | Calls | Verified | Rate | Prompt tok | Cached tok | Cache share | Uncached tok | Completion tok | Combined proxy | Cost / verified |
|---|---|---|---|---|---|---|---|---|---|---|
| A verbatim | 48 | 12 | 0.250 | 145,216 | 113,600 | **0.785** | 31,616 | 10,266 | **41,882** | **3,490** |
| B typed records | 48 | 14 | 0.292 | 144,985 | 92,352 | 0.637 | 52,633 | 11,389 | 64,022 | 4,573 |
| C B + masking | 48 | 15 | 0.313 | 116,341 | 30,272 | **0.260** | 86,069 | 23,994 | 110,063 | 7,338 |

Cache share is computed over rows that reported `cached_tokens` at all: arm A has one row with no cache report (T2, turn 1) and that row is excluded from the share, counted as full prefill in the cost — never as a zero. That makes A's cost an upper bound (41,322–41,882 depending on the unknown reuse in that one call); B and C are unaffected.

Gate (`run/analyse.py`, margin 0.10, baseline A): **no promotion**. B is 31 % more expensive per verified success, C is 110 % more expensive. Both pass the quality bar (verified rate ≥ A); neither passes the cost bar.

Paired quality, per (task, turn) cell:

| Pair | both | only first | only second | neither |
|---|---|---|---|---|
| A vs B | 12 | 0 | 2 | 34 |
| A vs C | 11 | 1 | 4 | 32 |
| B vs C | 11 | 3 | 4 | 30 |

## Why the byte-saving designs lose

The designs do exactly what they were built to do to length — and it costs them the cache.

| Turn | A prompt / share | B prompt / share | C prompt / share |
|---|---|---|---|
| 1 | 565 / 0.116 | 565 / 0.921 | 565 / 0.921 |
| 2 | 1,262 / 0.423 | 1,006 / 0.065 | 998 / 0.321 |
| 6 | 2,989 / 0.847 | 2,807 / 0.590 | 2,787 / 0.582 |
| 9 | 4,220 / 0.796 | 4,165 / 0.730 | 3,088 / **0.124** |
| 12 | 5,452 / 0.841 | 5,526 / 0.786 | 3,361 / **0.191** |

Source: `notes/CACHE-MECHANISM.json` (per-turn medians from `rows/ccs.jsonl`).

- **B does not shrink the prompt at all** (144,985 vs 145,216 tokens) yet loses 21 % of the cached prefix, because every turn rewrites the record tail: the shared prefix survives only up to the last stable record. Uncached prefill rises 66 % (31,616 → 52,633).
- **C does shrink it** — 20 % fewer prompt tokens, and by turn 12 the prompt is 38 % shorter — but masking rewrites the tail at turn 7 and the cached share collapses from 0.582 to 0.111 and never recovers. Uncached prefill is 2.7× A's, and completion tokens more than double (10,266 → 23,994), consistent with the model re-deriving facts that masking removed.
- **A wins on cache, not on size.** Its prefix grows monotonically and stays reusable; by turn 12 it reuses 84 % of a 5,452-token prompt.

At turn 12 the measured median uncached prefill per call is 844 (A), 1,173 (B) and 2,721 (C) tokens: a shorter prompt is not a cheaper prompt.

## What this falsifies

The pilot's working hypothesis — that typed records and masking buy cost efficiency at a long context — does not hold on a prefix-cache-serving engine. Token-count reduction is the wrong objective when serving is prefix-cached; **prefix stability per turn is the objective**, and both "improvements" trade it away. A policy that only appends (or rewrites a suffix that the next turn keeps) is the shape the serving layer rewards.

## Limitations — read before citing

1. **Held-out status.** T3/T4 were held out from arm selection, but their question text was revised after observing calibration failures (supported phrasing (b) in `notes/INTEGRITY-HELDOUT.md`). They are not pristine held-out.
2. **The suite has a ceiling.** Per task, verified: T1 12/12 (A), 12/12 (B), 11/12 (C); T2 0, 2, 1; T3 0, 0, 3; T4 0, 0, 0. Failures are value-extraction ambiguities in the fixtures (e.g. `ref_kinds=16` vs the model's 20; `state_fields=16`/`derived_regions=12` vs 8/4), not context loss. Quality differences are therefore within noise at n=48 and must not be read as arm effects; cost per verified success is dominated by T1, the only task the model reliably solves.
3. **Instrument defects found after the run** (`orchestration/handoffs/AUDIT-INSTRUMENT.json`, `notes/INSTRUMENT-AUDIT.md`): `neg.no_outside_write` could not see writes outside `work_parent`; `neg.no_network` matched literal imports only, so `__import__('socket')` passed; arm C emitted digests without persisting bodies, so its references were not resolvable and C is not yet a genuine recoverable-context arm; the renderer fingerprint omitted `run/driver.py:make_history` until `WATCHER-REPAIR` added it (all rows above carry the pre-fix digest `86c8adeb`).
   The two grading holes are now closed — artifacts run under `bwrap`, and a runtime import hook catches dynamic imports; `escape_write.py` fails `neg.no_outside_write` and `dynamic_import.py` fails `neg.no_network`. **All 144 stored artifacts were re-graded with the hardened grader and 0 verdicts flipped** (`notes/REGRADE.md`), so the table above survives the hardening. None of these defects changes the cost measurements, which are read from the API's own usage block; the unresolved one bounds what may be claimed about arm C's recovery property.
4. **Supervision gap.** The watcher crashed at startup (`TypeError` on a missing rows file), so the run had no independent monitor, and the driver had no path by which an alert could stop a send. Repaired afterwards: the watcher handles a missing rows file and a pre-row stall, the driver aborts before the next send on any alert, the launcher supervises on a 120 s cadence and exits non-zero if the watcher dies. Three offline proofs (killed watcher mid-run, pre-row stall, healthy run) pass; none of the 144 calls above benefited from them.
   The batch's 1,500-call reservation was also not exclusive across worktrees: `ledger/reserve.py` read shared state but wrote locally, so two runs could each reserve against the same remainder. Now one exclusive lock on the authoritative ledger covers read-and-write; two concurrent reservations from the same tree and one across trees each grant exactly one (`orchestration/handoffs/RESERVE-GUARD.json`), with the authoritative ledger's sha256 unchanged.
5. **Accounting.** 208 ledger calls against 189 row-bearing sends: **19 sends produced no row** (during killed calibration attempts), and the intents logs hold 209 distinct entries, a count that has not been reconciled with the 189 sends. The gap is named rather than netted away.
6. **The held-out gate is undefined, not passed.** Split by task set, held-out (T3/T4) verified 0/24 (A), 0/24 (B) and 3/24 (C) — arm A verifies nothing there, so cost per verified success has no denominator. The pooled `no-promotion` verdict therefore rests on discovery tasks plus one task the model solves; no held-out claim is made either way.

## Reproduce

```
cd experiments/context-cache/cells/COMBINED-CONTEXT-SERVING
python3 run/analyse.py --rows rows/ccs.jsonl --out notes/ANALYSIS.json
python3 -c "import json;print(json.load(open('notes/ANALYSIS.json'))['gate']['verdict'])"   # -> no-promotion
```

## Verdict

**Do not adopt typed records or masking as a cost optimisation on this engine.** On 144 paired calls the verbatim transcript was the cheapest per verified success; the typed-record arm cost 31 % more and the masked arm 110 % more, both driven by measurable cache-prefix loss rather than by token count. The next experiment worth running is the opposite direction: measure how much prefix stability a record format can keep (append-only record log with a stable header) before it costs more than it saves.
