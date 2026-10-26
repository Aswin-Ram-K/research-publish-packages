# C5-ADJUDICATE

**Bound:** 12 tool calls (used 10) · **Offline:** zero requests; read-only on all pre-existing files.
**Question:** does any on-disk artefact pin what padding does, or does every apparent pin depend on a
live endpoint?

## Verdict
C5 as written ("no measured padded cycle exists in any unit") is FALSE — nine measured padded
requests exist — but the C5 *objection* survives on a different fact: the model that would let you
compare padded against unpadded is the ~4x-off stub. **OPEN.**

## Evidence
- `experiments/ptr-engine/measure/rows.jsonl` — 49 rows; recomputed padding counts:
  `{(applied=False,0):3, (True,60):3, (True,58):3, (True,50):3}` ⇒ **9 of 12 `measure` request rows
  are padded requests**, 3 reps each, all with `token_source='http://192.168.2.168:8012/v1'`, all
  `error: null`. C5's "no measured padded cycle exists in any unit" contradicts this file.
- `experiments/ptr-engine/measure/rows.jsonl` cell B rep0-2 — `pad 60, P1 386, residue_after 2,
  cached_tokens 384, cached_reported true, uncached 15`; cell D rep0-2 — `pad 50, P1 322,
  residue_after 2, cached_tokens 320, uncached 15`. These are measured padded cells that satisfy the
  law `uncached = residue + L`; they are **not** predictions.
- Cell D is a **byte-identical control**: ENGINE-R2's own offline byte counts give compact index
  383 B / 42 words vs full 447 B / 53 words (`experiments/ptr-engine/measure/SHAPE-SEARCH.md:83-88`),
  and ENGINE-R1 measured the compact+50-filler prompt live at `P1 322, residue 16`
  (`experiments/ptr-engine/measure/SHAPE-SEARCH.md:80`). Cell D is that prompt.
- `experiments/ptr-engine/measure/shape-search.json:2` — `"predicted": true`, `"L_measured": 13`,
  3 tokenizers. Every candidate table in that file feeds on tokenizers built to satisfy or to break
  ENGINE-R1's anchors: `PYTHONPATH=… quick_bill(325,13),quick_bill(386,13),quick_bill(384,13),
  quick_bill(322,13)` → `343 401 781 337`.
- `experiments/ptr-engine/measure/SHAPE-SEARCH.md:241-244` — the unit itself names the live
  measurement it did not run: one prime, two shapes, 3 reps, `L` read from `prompt_tokens`.
- `orchestration/handoffs/ENGINE-R2.json:evidence.command_or_count` — "OFFLINE ONLY — not one request
  was sent … Every number below is PREDICTED"; calibrated-anchor stub base P1 550/588 vs the measured
  325, i.e. ~1.7-1.8x off, not 4x. C5's "~4x (66 vs 325)" is the **words-only** stub's prediction,
  also in that same handoff. The stub is uncalibrated; the factor quoted in C5 overstates it.

## Proposed sentence for C5
> **C5 — OPEN, on the stub and not on the cells.** Nine measured padded requests exist — 3 reps each at
> pads 60/58/50 (`measure/rows.jsonl`, cells B/C/D) — so "no measured padded cycle exists" is false;
> but no artefact pins a compact-UNPADDED cell, and the tables predicting it rest on stubs
> ~1.7-4x off (`SHAPE-SEARCH.md:241`).

## Missing measurement
MISSING: SGLang the compact index UNPADDED on `:8012` (cell E, P1_E and residue R_E=P1_E mod 64) —
it would live in `experiments/ptr-engine/measure/rows.jsonl` as a cell E row.
