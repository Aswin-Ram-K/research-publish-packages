# ENGINE-R1 — make the pointer engine exploit the append-cost law

**Status:** done · **Bound:** 45 tool calls (used 44) · **Server:** `:8012` (`occamy-1.0`, SGLang),
sole writer for the whole unit; `:8014` never touched; no restart, no `/flush_cache`.

## Purpose

The first unit where the engine's design is chosen by a *measured* law instead of intuition:
`uncached = (P1 mod 64) + L`, with an avalanche (`uncached = P1 + L`) when `P1 mod 64 ∈ {0, 1}`
(`experiments/miss-law/LAW.md`). The engine compiles its own prompt, so it can move `P1 mod 64`
with inert padding. Build the lever, then measure whether pulling it pays.

## Deliverables

| path | what it is |
|---|---|
| `experiments/ptr-engine/ptr_engine/quantise.py` | `token_len`, `choose_padding`, `predict_billed` (the contract) + `cycle_bill`, `compact_index` (what the measurement needed); `StubTokenizer` offline, `ServerTokenizer` opt-in |
| `experiments/ptr-engine/tests/test_quantise.py` | 45 tests: determinism (in-process **and** cross-process), padding visible, law at residues 0/1/2/63, offset accounting, compact index resolvability, no clock/randomness |
| `experiments/ptr-engine/measure/run_cells.py` | the 4-cell measurement, LAW §2 request shape, prediction row fsynced **before** each request |
| `experiments/ptr-engine/measure/rows.jsonl` | 49 rows (33 requests + 12 prediction rows + 4 calibrations), flush + fsync per row |
| `experiments/ptr-engine/measure/RESULTS.md` | cells, predicted vs observed, deltas, new `r`, the one-sentence answer |
| `experiments/ptr-engine/SPEC.md` §14 | usage, the three things a host must not skip, conditional-padding policy |

## Result (short)

* **Law reproduced on a live request: 12/12 measure rows exact**, avalanche included (residue 0 →
  `cached` null, `uncached = P1 + L = 397`, 3/3).
* **A** (index as compiled): residue **5**, `P1` 325, append bills **18**.
* **B** (padded to 2): residue 2, pad **60**, append bills **15** — but the cycle bills **+58** more.
* **C** (padded to 0, control): residue 0, pad 58, append bills **397** — avalanche confirmed.
* **D** (compact, padded to 2): index **447 → 383 B**, **37.25 → 31.92 B/line**, `r` **67.1× →
  78.3×**, `P1` 272 → 322 padded, append **15**.
* **Does quantisation pay?** Only as avalanche insurance (397 → 15 on an append) or at residue ≥ 35;
  at the residues the example actually lands on it *costs* 36–58 billed tokens per cycle and pays
  back after 4 (compact) / 21 (full) warm turns. Padding must be conditional.

## What went wrong first, and why it is in the record

The first pass aimed `target_residue` at the **text**, but the server bills the **whole prompt**
(user message + template framing), so cells B and C landed on residues 23 and 21 — the control never
tested the avalanche. Fixed by `offset_tokens` plus a per-rep wire check (read `prompt_tokens`,
re-aim), which also caught a **+1 token** shift from the padded tail meeting the template's trailing
marker. 12/12 reps needed exactly one re-aim. Lesson carried into SPEC: a residue the engine has not
read back from the server is a guess.

## Notes / limits

* `n = 1` payload only; single server; 3 reps are deterministic (they bound transcription error,
  not sampling variance).
* `breakeven_turns` is arithmetic on the law, not a measured warm session.
* A concurrent card was editing `ptr_engine/` throughout (`ledger.py`, `errors.py`, `__init__.py`);
  the `ptr_engine.quantise` re-export in `__init__.py` was **appended** at the end of the file rather
  than merged into the import block, so it cannot have clobbered that card's edits. If a later card
  rewrites `__init__.py` wholesale, the appended block needs re-applying (the module path
  `ptr_engine.quantise` is unaffected).
