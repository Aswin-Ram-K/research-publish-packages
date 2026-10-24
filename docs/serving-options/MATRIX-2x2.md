# MATRIX-2x2.md — the measured 2x2: the engine sets the bill, the model sets it only under vLLM

**Status:** CURRENT — this is the pointer for the serving question "which knob moves the per-turn
cache bill: the engine or the model?" **Measured, not projected.** Every number on this page is
copied from the machine-checked ledger, not recomputed here.

**Canonical source (of record):**

| What | Where |
|---|---|
| Claim, with its full figures | `papers/context-cache/CLAIMS.md` row **C63** |
| Checked numeric expectations | `papers/context-cache/recompute.py` → `EXPECTED["C63"]` (tolerance `1e-6`) |
| Prose + table | `papers/context-cache/MANUSCRIPT.md` **§9b** (the matrix), abstract lines 68–78 |
| Reproduce | `.venv/bin/python papers/context-cache/recompute.py C63` → `PASS  43/43 values match` |
| Guard | `tests/test_paper_matrix_fold.py` (8 tests; red->green recorded in `state/logs/MATRIX-FOLD-redgreen.txt`) |
| Per-cell serving figures | `papers/context-cache/SERVING-BRIEF.md` (S-items, 13 cells pinned) |
| Rows | `MOE-VLLM`, `G3`, `WIN-VLLM`, `DENSE-SGL` (4 x 284 rows) |

**Read the ledger, not this page, before quoting.** This page is a signpost; `CLAIMS.md` C63 is where
the claim lives and `MANUSCRIPT.md` §9b is where it is argued.

---

## 1. The answer

On **one shared 32k / 71-turn schedule** (4 arms x 71 turns = **284 rows per cell**, **1,136 rows** in
all; same prompt prefix digest and length on all six cell pairs — `prefix_sha256` 284/284,
`chars` 284/284), the four cells are:

| model | engine | hit | uncached/turn | cache unit (hot gcd) |
|---|---|---:|---:|---:|
| occamy-1.0 (MoE) | vLLM 0.27.1 | 0.901212 | 1,682.72 | 2,096 |
| occamy-1.0 (MoE) | SGLang | 0.957153 | 729.76 | 64 |
| qwen3.5-9b (dense) | vLLM 0.27.1 | 0.869037 | 2,230.78 | 1,088 |
| qwen3.5-9b (dense) | SGLang | 0.956941 | 733.37 | 64 |

- **The engine is the lever.** vLLM spends **+1,225.18** more uncached tokens per turn than SGLang
  [1,132.2, 1,313.3], positive on **70 of 71** turns — a **2.6738x** ratio (2.3058x on the MoE,
  3.0418x on the dense). That is **0.9115** of the 1,344.16-token grand mean.
- **The model main effect is small:** **+275.83** [194.3, 357.6], **53 of 71** turns positive.
  The engine effect is **4.4418x** larger.
- **And it is engine-conditional (the interaction):** within vLLM the dense pays **+548.06**
  [384.7, 711.9] more than the MoE (1.3257x); within SGLang the two models differ by **+3.61**
  [0.0, 10.8] (1.0049x), positive on **1 of 71** paired turns. Interaction **+272.23**
  [190.1, 354.6]; the model effect is **152.00x** larger under vLLM (the ratio of the
  raw per-level means, rounded to 4 dp; dividing the two rounded operands 548.06/3.61 is an
  artefact of rounding, not this figure).
- **Why:** SGLang delivers the 64-token grid to both checkpoints; under vLLM the resolved block is a
  property of the checkpoint (2,096 MoE / 1,088 dense). The engine that pages at 64 also hides the
  model's per-turn cost.
- **Arm check:** recomputed per salt-separated arm, engine effect 1,216.2–1,229.7 and model effect
  274.0–281.2 across R/A/C/H — the result is not an artefact of one replicate.

**Design takeaway:** a per-turn bill cannot be read off the model alone. Pick the engine first; under
vLLM the checkpoint's block geometry then matters, under SGLang (at this band) it does not.

## 2. Where it stops (read before extrapolating)

- ONE schedule at ONE band (**32k**, 71 turns), one seed, one GPU.
- The two checkpoints differ in **size and architecture** as well as MoE-vs-dense, and the engine axis
  also carries each cell's launch flags (vLLM resolved blocks 1,088 / 2,096; SGLang
  `--mem-fraction-static` 0.22 on the dense cell). **This is not a claim that the model effect is an
  architecture effect.**
- The 64k band was run on **SGLang only**. No extrapolation to other bands is made.
- It is a **measured 2x2, not a law over models or engines** — `papers/context-cache/GAPS.md` **G4**.
- No compaction fires at 32k, so the four arms are salt-separated replicates, not four policies.

## 3. How this relates to the older notes in this directory

`R-*.md` and `CROSS-HTTP.md` are dated research notes, now carrying a **STALE** banner;
`LAUNCH-*.md` remain current and carry a **cost pointer** here instead. Two figures in them must not
be carried forward into the matrix answer:

- `CROSS-HTTP.md` measures `qwen3.5-9b` on vLLM with effective block **1056** and no per-request
  `cached_tokens`. The matrix's dense vLLM cell (`WIN-VLLM`, config `V1`) resolves to **1,088**; 1056
  is a different configuration (`V2`, CLAIMS C56), not a contradiction.
- Statements that the thick end of the gap is "a different model as well as a different engine"
  (GAPS G4, first/second pass) are the state **before** the 2x2. After C63 the engine effect is
  identified at this band; what C63 still cannot claim is any *architecture* attribution.

`LAUNCH-VLLM.md` and `LAUNCH-SGLANG.md` remain the correct launch guides — the flags matter more,
not less, now that the engine is shown to be the dominant lever. Only a 4-line cost pointer was
prepended to each; no body text changed. That shifted the two line-range citations `GAPS.md` makes
into them, and both were repointed by the same +4:
`LAUNCH-SGLANG.md:103-146` → **`:107-150`** and `LAUNCH-VLLM.md:83-89` → **`:87-93`**.
