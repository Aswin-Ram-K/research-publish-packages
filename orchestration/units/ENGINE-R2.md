# ENGINE-R2 — remove the insurance premium

**Status:** partial (delivered, with the live cell deferred) · **Bound:** 35 tool calls · **Used:** ~34
**Offline:** every run in this unit was offline. **No request was sent** — `:8012` belongs to another
unit and `:8014` is taken. Every number this unit reports is **PREDICTED**.

## 1. Objective as given

ENGINE-R1 proved that residue quantisation works on a live request but charges for it: at a benign
residue, padding to residue 2 costs 58 billed tokens per cycle (full index) and 36 (compact), and pays
back only as avalanche insurance (397 → 15, 26×) or at residue ≥ 35. Its next hint named the fix: the
compact index is 53 prompt tokens smaller, so a compile can reach a cheap residue by **cutting**
instead of by **adding** filler.

Deliver: `choose_shape()` + `cycle_bill()` in `quantise.py`, a candidate table for the 12-item corpus
(full / compact / projection variants, all PREDICTED), tests (prefer a free variant; never return
residue 0 or 1; a planted corpus where no free variant reaches a cheap residue → pad and say so),
`SPEC.md` section, `measure/SHAPE-SEARCH.md`, this card, and the handoff.

## 2. What was built

| file | change |
|---|---|
| `ptr_engine/quantise.py` | `PAD_FOR_FREE_RESIDUE`, `ShapeVariant`, `ShapeCandidate`, `ShapeChoice`, `choose_shape`, `quick_bill`, `projection_variant`, `calibration_limits` (+ `cycle_bill` unchanged and reused) |
| `ptr_engine/__init__.py` | re-exports appended to the ENGINE-R1 block (not merged into the import block, so a concurrent card's edits cannot be clobbered) |
| `tests/test_quantise.py` | 45 → 63 tests: 18 for the search |
| `SPEC.md` | new section 15 (shape search) |
| `measure/shape_search.py` | offline generator; imports the shipped `choose_shape`, so the table cannot drift from the code |
| `measure/shape-search.json`, `measure/SHAPE-SEARCH.md` | the candidate tables (PREDICTED), the calibration residual, and the live-measurement plan |

## 3. Findings

1. **The padding line is `r ≥ 34` at B = 64, and it follows from the law alone.** Padding pays iff the
   filler is smaller than the tail it saves, `k + 2 < r`. ENGINE-R1's "≥ 35" was the same line computed
   from the other side. `PAD_FOR_FREE_RESIDUE = 33` is that boundary in code.
2. **The search must compare, not aim.** An earlier draft of `choose_shape` always tried the target
   first, so it padded unconditionally — exactly the behaviour this unit exists to remove. The shipped
   version emits the unpadded row beside every padded row and lets the law pick. At residue 5 it now
   pads nothing; at residue 58 it pads 8; at residue 63 it pads 1.
3. **The free-residue idea does not reach a cheap residue for this corpus, and the search does not
   invent one.** Under the byte-aware stub every variant sits at residue 12–38 (the band where filler
   costs more than it saves), so the search returns the compact index **unpadded** and reports
   *"no shape reached a cheap residue at an acceptable bill"*. It still wins by 12 per cycle — the cut,
   not the padding.
4. **The two ENGINE-R1 main-text anchors and its cell-D anchor cannot all be met by any stub of this
   corpus's text.** The main-text pair implies 53 tokens saved across 11 fewer words; cell D requires
   each `" the"` filler token to be one token. Three calibrations are reported, each with the anchors it
   breaks; none is claimed to be the server's tokenizer. This is the unit's honest negative result and it
   is what makes the corpus recommendation a candidate, not a conclusion.
5. **The projection cut is catalogued, not recommended.** It saves 12 index bytes and the byte-aware
   stub predicts it *costs* 44 per cycle. That is a warning, not evidence; the sign is settled by one
   `/v1/tokenize` call in the live unit.

## 4. Evidence

| claim | command | output |
|---|---|---|
| the search's tests pass | `TMPDIR=/var/tmp python3 -m pytest experiments/ptr-engine/tests/test_quantise.py -q` | **63 passed** (was 45) |
| no regression | `TMPDIR=/var/tmp python3 -m pytest experiments/ptr-engine/tests -q` | **171 passed** (baseline 153) |
| the table is generated, not typed | `python3 experiments/ptr-engine/measure/shape_search.py` | deterministic; `measure/shape-search.json` |
| the law's four measured cells reproduce | `quick_bill(325,13)=343`, `(386,13)=401`, `(384,13)=781`, `(322,13)=337` | asserted in `test_quick_bill_is_the_law_restated_*` |
| the handoff is valid JSON | `PYTHONPATH=src:. python3 -m pytest tests/test_orchestration_handoffs.py -q` | 13 passed |

The root `tests/` suite is **not** runnable in this environment (`fastapi`, `graphify` not installed; 16
collection errors), so the engine suite under `experiments/ptr-engine/tests` is the one run here — the
same suite the 153 baseline was counted on.

## 5. What is not done

The **live** measurement (cells E and F, §5 of `measure/SHAPE-SEARCH.md`) is deferred: this unit had no
measurement budget. Until it runs, the corpus residue, the `L` for a 400–600-token prompt, and the sign
of the projection cut are **unmeasured**.
