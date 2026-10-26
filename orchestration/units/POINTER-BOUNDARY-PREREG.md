# POINTER-BOUNDARY-PREREG

**Bound** 18 tool calls. **Used** 10. **Requests sent: 0.** DESIGN ONLY — no `curl`, no HTTP, no row file, no
server contact. Writes: `experiments/ptr-engine/BOUNDARY-PREREG.md`, this card, the handoff.

**Objective.** Pre-register where the pointer protocol actually wins, before any measurement, so the answer
cannot be chosen after the fact. The equal-information baseline left two claims unmeasured: (i) a set larger
than the window cannot be pasted at all; (ii) a cache-hostile history erases the transcript's edge.

**Delivered.** `BOUNDARY-PREREG.md`, 120 lines (cap 120): question + sub-questions; 4 arms with endpoints and
an exact eviction rule; a 4-rung size ladder; a 3-level hostile ladder; **7 predictions, each with direction,
mechanism and a refutation condition, written before the decision rule**; the decision rule (reused `AUD-4417`
question, 3 reps, `UNAVAILABLE` stop rule); cost table; 18-field row schema; what it cannot settle.

**Arms.** `C0-static` (byte-identical prefix), `C0-trunc` (fact-pinned FIFO eviction), `R-pointer` (index +
fetch), `R-pointer-prefetch` (one item early, so the break rides a request already breaking). occamy-1.0-NVFP4
on SGLang `:8012`; qwen3.5-9b on vLLM `:8014`, whose missing cache counters limit it to gross tokens.

**Ladder.** 12 / 40 / 120 / 400 items (108k / 360k / 1.08M / 3.6M B). `C0-static` first becomes impossible at
**rung 120 on occamy** (225,960 > 131,072) and **rung 40 on qwen** (75,320 > 32,768) — recorded `IMPOSSIBLE`
with the exact error, never as a cost.

**Cost.** 696 scheduled requests (stage 1 = 216, stage 2 = 300, stage 3 = 180), ceiling 810 with the retry
reserve. Three refusal points: a human can approve or refuse any stage.

**Strongest falsifiable prediction.** P2: the 1.84x inverts *below* the window — at occamy rung 40 the pointer
becomes cheaper (R/C0-static 0.50–0.65), because the transcript's whole advantage is one cold prime amortised
over four turns, and that prime scales with the set. A ratio ≥1.0 would make 1.84x a real law, not an artefact.

**Not settled.** One GPU, two models, synthetic corpus, exact-match scoring, no concurrency, no dollars.
