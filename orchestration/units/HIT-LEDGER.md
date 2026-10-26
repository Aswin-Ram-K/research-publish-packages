# UNIT HIT-LEDGER — the append-cost law as an accounting layer

**Purpose.** Turn `experiments/miss-law/LAW.md` into a billing model the pointer engine
carries: `HitLedger` in `experiments/ptr-engine/ptr_engine/ledger.py`, with the law's
prediction, per-turn reconciliation and totals, and the avalanche as a first-class outcome.

**Bound.** 35 tool calls. Fully offline: no network, no server calls, no tokenizer at import.

**Write paths.** `experiments/ptr-engine/ptr_engine/ledger.py`, `.../ptr_engine/errors.py`,
`.../ptr_engine/__init__.py`, `.../tests/test_ledger.py`, `.../SPEC.md`,
`orchestration/units/HIT-LEDGER.md`, `orchestration/handoffs/HIT-LEDGER.json`.
`experiments/miss-law/**` was **read only** (`rows.jsonl`); nothing else was touched.

---

## 1. The law, as encoded

```
SGLang / occamy-1.0, B = 64:    uncached = (P1 mod B) + L
vLLM   / qwen3.5-9b, B = 1056:  uncached = (P1 mod B) + B + L
avalanche (SGLang measured, residues 0/1):  uncached = P1 + L
```

`L` is the measured appended length and **includes the 12 framing tokens**; the payload
count `n` is never it. Encoded once as `FRAMING_TOKENS = 12` + `law_L(n) = n + 12`.

The avalanche is **not** a footnote string. `HitEntry.avalanche` is a stored boolean,
`predicted_uncached` is the whole prefix at those residues, `tail_uncached` is what the
tail formula would have said, and `avalanche_tokens = predicted - tail` prices it. At
`P1 = 8000` that is **8,013 billed vs 13**, and `summarise()` reports the count, the
tokens billed and the tokens added.

## 2. One correction the replay forced (a finding, not a special case)

`boundary_blocks` is capped by the complete blocks the prefix holds:
`boundary term = min(boundary_blocks, P1 // B) * B`.

The single row the `+B` form could not explain is vLLM at `P1 = 453 < B`
(`cell Bprobe-400`), which billed `467 = P1 + L`. Verbatim from the first replay run,
before the cap:

```
E           AssertionError: vllm: ('turn 0 (vllm cell=Bprobe-400): could not explain --
            observed 467 vs predicted 1523 (delta -1056)',)
```

No cell is special-cased: a server that re-bills "one whole cached block" has no block
to re-bill when the prefix holds none. With `P1 >= B` the cap is inert, so the measured
formula is unchanged.

## 3. The accounting surface

| call | returns |
|---|---|
| `HitLedger(server, cell=...)` | pure in-memory ledger; unknown server → `PTR_LAW_UNKNOWN_SERVER` |
| `record(P1=, L=\|payload_tokens=, observed_uncached=, cell=)` | `HitEntry` with `P1, L, B, residue, avalanche, predicted_uncached, tail_uncached, observed_uncached, avalanche_extrapolated` |
| `predict(P1, L)` | the law's `(uncached, avalanche)` |
| `reconcile(observed=None)` | `Reconciliation`: per-turn `delta`, `mismatched` named with server+cell, `unknown` kept separate, `unexplained()` lines |
| `summarise()` | `billed_tokens`, `avalanche_count`, `avalanche_tokens`, `avalanche_extra_tokens`, `explained_fraction`, residue histogram |

`residue` and `avalanche` are **stored at record time**, never recomputed: a later
profile change cannot redraw a bill that was already issued.

## 4. Codes

Four new codes, in their own tuple `LEDGER_LAW_CODES` so the row contract's five stay
five (`tests/test_negative_controls.py` asserts `len(LEDGER_CODES) == 5`, so extending
that tuple would have been a regression): `PTR_LAW_UNKNOWN_SERVER`,
`PTR_LAW_BOUND_INVALID`, `PTR_LAW_SERIES_LENGTH`, `PTR_LAW_OBSERVED_INVALID`.
**New code total: 4. Package enumeration: 16 named codes (7 controls + 5 ledger + 4 law).**
Zero bare `ValueError` sites were added; every law failure is a `PtrError` subclass that
is also a `ValueError` (the existing ledger family), asserted by test.

## 5. Suite

`100 passed` before → **`108 passed`** after (`python3 -m pytest -q`, no regressions).
Eight new tests in `tests/test_ledger.py`: the law on both servers at residues 0/1/2/63
and a payload boundary; the profiles being the measured ones; `reconcile` naming a
mismatching turn; avalanche as its own outcome with its own cost; unknown-observed not
treated as zero; the four law codes; the 16-code enumeration; and the replay.

## 6. Red → green proofs (throwaway copies, verbatim tails)

Both sabotages were applied to a copy of `ptr_engine/` + `tests/` inside the workspace
(removed afterwards). Each produced **2 failed, 105 passed, 1 skipped** (the replay test
skips in a copy, because the rows it reads are two directories up from the real tests
directory, so it is not in `../..` of a copy).

**Sabotage A — `B = 32` for SGLang:**

```
tests/test_ledger.py:158: AssertionError
E       assert (63, (44, False)) == (63, (76, False))
E         At index 1 diff: (44, False) != (76, False)
tests/test_ledger.py:182: AssertionError
>       assert (sglang.block_size, sglang.boundary_blocks) == (64, 0)
E       assert (32, 0) == (64, 0)
FAILED tests/test_ledger.py::test_law_reproduces_both_servers_at_named_residues
FAILED tests/test_ledger.py::test_profiles_are_the_measured_ones
2 failed, 105 passed, 1 skipped in 0.22s
```

**Sabotage B — avalanche branch deleted:**

```
tests/test_ledger.py:155: AssertionError
tests/test_ledger.py:220: AssertionError
>       assert (avalanche.residue, avalanche.avalanche) == (0, True)
E       assert (0, False) == (0, True)
FAILED tests/test_ledger.py::test_law_reproduces_both_servers_at_named_residues
FAILED tests/test_ledger.py::test_avalanche_is_its_own_outcome_with_its_own_cost
2 failed, 105 passed, 1 skipped in 0.22s
```

Green: the unmodified suite is `108 passed`.

## 7. The observed series is real, not invented

`reconcile()` is exercised on `experiments/miss-law/rows.jsonl` —
**387 measure rows** (`sglang` 301, `vllm` 86: every row with `role == "measure"` and a
`prev_prompt_tokens`), read from disk in the test, never fabricated. `P1 =
prev_prompt_tokens`, `L` from `n_payload` via `law_L`, observed = `uncached_tokens`.
Result: **387/387 exact, 0 mismatches, 0 unknown**, `explained_fraction == 1.0`.
The replay also confirms on the raw rows that `L_app == n_payload + 12` in 387/387, that
the 83 null-cache rows are exactly the 83 avalanche turns and that their residues are
exactly `{0, 1}`. The brief's "85/86 on vLLM" is the sub-block row of §2, now explained.

## 8. Assumptions (autonomous: no human present)

1. **Latest moment of truth is the later material.** `predict` applies the avalanche
   branch *before* the tail formula, so an avalanche residue always bills `P1 + L`
   (conservative: never under-predict a bill).
2. **vLLM's avalanche is unmeasured** — 27 residues in the sweep, none 0 or 1. The
   profile keeps the rule (never under-predict) but marks `avalanche_measured = False`,
   so every such turn carries `avalanche_extrapolated = True` and is counted by
   `summarise()`. The honest alternative — refusing to predict — would leave a host
   with no number at all.
3. **`FRAMING_TOKENS = 12`** is the measured template's constant. A host with a
   different request shape must pass `L` directly; `record` refuses both `L` and
   `payload_tokens` at once so the two cannot quietly disagree.
4. **`LEDGER_CODES` was not extended.** The law codes live in `LEDGER_LAW_CODES`
   because `tests/test_negative_controls.py::test_ledger_codes_extend_the_enumeration_without_colliding`
   asserts `len(set(LEDGER_CODES)) == 5` and a 12-code total; extending it would have
   broken a passing guard. Both totals are now asserted instead (5 + 4, 16 named codes).
5. **The brief's "218/218 SGLang"** does not match any subset boundary I could
   reproduce (I get 301 SGLang measure rows); reported as replayed, not as quoted.

## 9. What this unit did NOT do

* No network, no server call, no tokenizer: every number is either a literal from the
  measured rows or arithmetic over them.
* The avalanche's **mechanism** remains unexplained (LAW.md §8); this unit encodes it
  as measured, and `SPEC.md` §13.3 says so.
* Multi-append runs are out of scope: the law is about one append onto a primed prefix.
