# Unit LONGRUN-PREREG — design + pre-registration only

**Purpose.** Replace the cost thesis with the operator's objective and pre-register the long-run experiment:
minimise **p95 TTFT (ms/turn)** and **tokens-to-verified-success (tokens)** over 60-turn runs at equal-or-better
verification, on occamy-1.0/SGLang `:8012`. Uncached tokens/turn is demoted to a **diagnostic**.

**Why now.** The operator (2026-10-26) reframed: a task is *scoped*; older steps are forgotten deliberately; a naive
system wastes turns "doing and fixing the wrong things"; **cost is not the objective**. The measured 1.84× cost gap
(`C0-EQUALINFO`: 1,911 vs 3,524 uncached tokens/turn) is kept as a secondary reading because it predicted latency —
and that latency was measured: 0.182 s (transcript) vs 0.602 s (pointer), 3.3× slower.

**Arms (exact).** A `transcript-grow` (naive, fails at the window) · B `transcript-compact` (state update at the
wall) · C `pointer-stable` (frozen index prefix, body appended in the suffix, next body prefetched — the redesign
the 1.84× result demands) · D `lease-reopen` (close at the wall, reopen with pointers + distilled state).

**Design.** N=60; wall at turn 23 (64,000-token cap = half of 131,072); checkpoints t10/t30/t60; wrong-thing band
turns 24–27 with a decoy `AUD-0000` and a 3-attempt repair budget. Predictions P1–P4 and the decision rule are
written **before** the rule: C must beat A by 2× at p95 and by 1.5× on tokens, and the token excess must be
*repair*, not per-turn cost.

**Budget.** 4 arms × 60 turns × 2 reps = 480, + 4 digests, + 4 controls, + 12 repair attempts = **500 requests.**

**Bound.** 20 tool calls. **Zero requests sent** — no curl, no row file, no engine contact. This unit designs; it
does not measure.

**Artefacts.** `experiments/ptr-engine/LONGRUN-PREREG.md` · `orchestration/handoffs/LONGRUN-PREREG.json` · this card.

**Next.** `LONGRUN-RUN` executes the 500 requests, controls first; any RED control voids the batch.
