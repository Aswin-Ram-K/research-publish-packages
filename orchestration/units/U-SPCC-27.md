# U-SPCC-27 — the TX-03 cliff is content absence; position is untested on this arm

**Status:** done (documentation only; zero live model requests).

**Inputs:** `orchestration/handoffs/U-SPCC-20.json`,
`experiments/ptr-engine/measure/answer-shape-diagnosis-TX03.md`,
`experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md`.

## Why

The landed wording said the cliff was **"presence, not position"** and that **"position is excluded"**. The
measurement does not support that. What it shows: the mask removes the fact's content at `intro+4`, so 40 of
48 checkpoints ask about a value absent from their prompt (0 occurrences, verified by re-materialising all
100 prompts); the 8 that pass are the `d2` probes at `intro+2`, i.e. **before** the mask. This run therefore
cannot test any position effect — the content is gone by the time the probe is asked. Until E3 runs
(`experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md`, body present, distance varied), the honest
claim is: **the cliff is content absence; position remains untested here.**

## What changed (claim only — no numeric fact altered)

1. **`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md`**
   - Row 22 title: `TX-03 masking cliff is presence, not position` → `TX-03 masking cliff is content
     absence; position untested on this arm` (7 cells preserved).
   - Row 22 status cell: `not depth, not attention` → `contract and fixture excluded; depth/attention
     untested here — no post-mask prompt carries the value`.
   - Section header: `### The TX-03 cliff is presence, not position` → `### The TX-03 cliff is content
     absence; position is untested here`.
   - Bucket arithmetic made explicit: five widths (`d5`/`d6`/`d8`/`d20`/`d32`) × 8 = **40**, consistent with
     `d2`'s 8 and the 48 total.
   - Exclusion bullet 2 rewritten: the `0.74` / `0.90` token-fraction retrievals are all pre-mask `d2`; no
     post-mask prompt holds the value, so no present-value distance contrast was run; E3 named.
   - Open-question bullet: marked **half closed** (content absence) with the position half left open and
     pointed at E3; the superseded "presence, not position / position is excluded" reading is labelled.
2. **`docs/STATE.md:535-545`** — "the cliff is presence, not position" → "content absence", with the
   position-untested sentence and E3 pointer; bucket arithmetic spelled out (`0/36` on the 12/48 arm,
   `0/40` = 5 × 8 on the 8/48 arm).
3. **`journal/2026-11-10.md` entry 8** — title corrected; paragraph added recording the 5 × 8 = 40 arithmetic
   and labelling the original "presence, not position" wording as the superseded overclaim.
4. **`orchestration/STATUS.md` U-SPCC-22 row** — shape `presence finding` → `content-absence finding`;
   claim restated as content absence with position untested and E3 named.
5. **`experiments/ptr-engine/measure/answer-shape-diagnosis-TX03.md`** — note under the classification table
   (bucket 2 is zero because nothing was present) and cause-2 bullet reframed from "excluded by data" to
   "not observed, not excluded as a mechanism".

Superseded-attribution notes were kept and relabelled, not deleted.

## Unchanged numbers (deliberate)

8/48; 8/8 at `d2`; mask turns `[5,12,21,28,49,56,65,72]` for facts at `[1,8,17,24,45,52,61,68]`; 40 `NONE`
on three `:8012` runs; `:8014` 39 `NONE` + 1 substitution (`cp.TX-03.f07.d8`, 3703 vs 3603); counters
`answered_correctly 8` / `abstained_after_mask 40` / `answered_wrong 0` / `unparsed 0`; billing `known
14,007` / `upper 14,303` / `coverage 0.99`.
