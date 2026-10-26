# Inference-side experiments — pre-registration skeletons

Write each one into your own `docs/` as a registered experiment **before** the first call, freeze
`run.json` (§3 of the contract), then append results. A falsifier is mandatory: if nothing could show the
claim false, it is not an experiment. Instrument controls come before primary runs, and each control must be
shown able to report the **opposite**.

Ordering is deliberate: **E1 then E2 decide whether our design has a premise.** If E1 or E2 fires its
falsifier, the rest of the programme changes shape and Consonance must be told before we build further.

---

## E1 — CACHE-BOUNDARY-SWEEP (replaces the VOID EXP#47)

**Question.** How does cache reuse depend on *where* a rewrite lands, on this engine and this model?

**Hypothesis.** With a frozen system+project prefix `P` of ~8–12K tokens, reuse falls monotonically as the
first rewritten byte-offset moves earlier, and there is a measurable boundary below which the request is
served effectively cold.

**Method.** One prompt skeleton; one **identical** control; one **append** control; one **never-sent**
control; then a sweep at ≥8 rewrite offsets from the tail to the head (offsets expressed in tokenizer units,
reported in tokens and bytes). 3 repetitions each, alternating order, one frozen build. Record
`prompt_tokens`, `cached_tokens` (or absent), `uncached_prefill_tokens` where exposed, `ttft_ms`.

**Falsifier.** Reuse does **not** fall monotonically with earlier rewrite offset (e.g. depends on block
alignment only, or is all-or-nothing at every offset). Then "rewrite depth" is not a usable predictor, our
checkpoint cost model is wrong, and it must be replaced by whatever the data does show.

**Controls.** identical → hit ≥ 0.9 of `P`; never-sent → 0; append → reuse ≥ `P − k` where `k` is the
appended tokens; a control arm at deliberately mismatched tokenizer must show **no** reuse.

**Budget.** ≤ 60 calls; no GPU memory beyond one container.

**Decides for Consonance.** The `rewrite_depth` term in `tools/context/economics.ts`, and whether a
checkpoint is priced per-token or per-boundary.

---

## E2 — CHECKPOINT-COST (the premise test)

**Question.** What does one compaction checkpoint cost, and over how many steps can it repay that cost?

**Hypothesis.** A checkpoint that rewrites `D` tokens costs ≈ `D × prefill_cost` and saves
`ΔD × (1 − reuse)` per subsequent step, so it repays inside 20 steps for task lengths above ~40 steps and
never repays for short tasks.

**Method.** Three arms on one fixture: **A** append-only; **B** one checkpoint at ~70 % of budget;
**C** checkpoints every ~20 steps. Same model, same outputs (fixed seed / temperature 0 where possible),
same verifier. Measure uncached prefill tokens, TTFT, and time-to-verified-success per task.

**Falsifier.** The checkpoint arm does not repay its rebuild within 20 steps, or repays only by making the
prompt shorter (i.e. the gain vanishes when measured as uncached work rather than payload). Then "bounded
working memory" is not an economic win at our task lengths and the BCF premise must be restated.

**Controls.** Append arm must show climbing cached share on the same fixture (F2's curve); a no-op
checkpoint (rewrite nothing) must cost ≈ 0.

**Budget.** ≤ 120 calls.

**Decides for Consonance.** Whether M2 (immutable branches + checkpoint/fork) is worth building at all, and
what the default checkpoint trigger should be. **This is the single most valuable number in the programme.**

---

## E3 — ORDERING (does placement of volatile material matter?)

**Question.** For the **same module set**, does ordering change uncached prefill work?

**Hypothesis.** Placing volatile material late (suffix) and stable material early reduces uncached work
versus relevance-only ordering, at equal token count and equal content.

**Method.** Two permutations of one module set — `stable…volatile` vs `volatile…stable` — plus a third
"relevance-interleaved" ordering; 3 repetitions; measure the cached/uncached split and TTFT at step 1 and
step 5 of a short trajectory.

**Falsifier.** No measurable difference in the cached/uncached split (within the noise band you report).
Then ordering is not a lever, Consonance's admission objective keeps relevance-only ordering, and we save
the complexity.

**Controls.** Both permutations must have **identical** token counts (assert it, don't assume); a
byte-identical repeat of each must hit fully.

**Budget.** ≤ 40 calls.

**Decides for Consonance.** Whether the admission objective gains a positional term at all.

---

## E4 — 32K DENSE TIER

**Question.** Is `qwen3.5-9b` (`max_model_len: 32768`) a usable cheap tier for long tasks, or does the
small window cost more than the model saves?

**Hypothesis.** On tasks whose full context fits 32K, the dense route matches the large model's verified
success at lower cost; on tasks that need paging to fit 32K, it does not.

**Method.** One fixture set split by "fits raw" / "needs paging"; run the dense route and the occamy route
on both subsets; measure verified success and time-to-verified-success, with cost per verified success.

**Falsifier.** Verified success collapses on the "needs paging" subset (a tier that only works when paging
is unnecessary is not a tier), or the dense route loses quality even when everything fits.

**Controls.** Same fixtures, same verifier, same acceptance checks; a trivially easy task subset both
routes must pass (otherwise the verifier is broken, not the tier).

**Budget.** ≤ 80 calls.

**Decides for Consonance.** Whether the harness should have a tier-selection policy at all, and what its
floor is.

---

## E5 — HYBRID REUSE ELIGIBILITY (occamy / SGLang)

**Question.** On a hybrid model with full-attention + sliding-window + recurrent components, what is the
deepest **safe** prefix boundary, and does the engine's accounting reflect it?

**Hypothesis.** Reuse is bounded by the intersection of all component states, so the effective boundary is
shorter than the attention-only boundary and is not predictable from token count alone.

**Method.** Prefix ladder (8 lengths) × 3 repetitions on the frozen build; compare `cached_tokens` against
the token offset; repeat with a component that changes (e.g. window size) if flags allow.

**Falsifier.** The boundary is all-or-nothing, or the engine reports reuse at offsets where the repeating
prefix is provably shorter than claimed. Either way "intersection of component states" is not usable as a
predictor and Consonance must not model it.

**Controls.** Identical repeat at each length must hit; a request whose prefix differs in its **first** token
must miss.

**Budget.** ≤ 60 calls.

**Decides for Consonance.** Whether our branch-reuse model can be stated in tokens at all, or must be
"engine says so" only.

---

## E6 — FIX EXP#48'S CONTROLS, THEN RERUN

**Question.** Does the pointer-context consumer actually help, once its controls can report the opposite?

**Hypothesis.** Unknown until the analyzer and the missing pointer / full / brief-only controls are repaired.

**Method.** Repair the analyzer first, add the three missing arms, show each control red before green, then
run the four arms on one fixture.

**Falsifier.** Any control that cannot be made to report the opposite invalidates the arm, and the result is
reported as **void** rather than as a null result.

**Budget.** ≤ 80 calls.

**Decides for Consonance.** Whether demand paging (`EXPAND(ref)`) is a real mechanism or a plausible story.

---

## Reporting format (all six)

Return to us: `run.json`, the NDJSON rows, the control table, and one page naming (a) what fired,
(b) what did not, (c) the falsifier verdict, (d) every cost you paid, itemised. A negative result in this
format is worth more than a positive one without it.
