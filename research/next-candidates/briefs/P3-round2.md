# P3 — The engine effect is not a knob: a pre-registered search of the documented cache space

> **Prospective and unapproved.** Derived only from `research/next-candidates/2026-10-24-sweep.md`;
> it authorises no request, restart or operator approval. Every number is quoted from that memo.
## Objective
Run the pre-registered Round 2 subset — A3 (lfu), A6 (HiCache), A7 (session radix), B3 (KV offload) —
to test whether only block/page geometry moves the per-turn bill and whether the documented eviction,
host-tier and offload options are nulls at 32k. The subset either moves C63's engine-effect result or
delivers a strong pre-registered null.
## Why now
- `docs/serving-options/R2-DESIGN.md` fixes **12 arms** (SGLang A1–A7, vLLM B1–B5), predictions
  **P1–P9**, **32k/71 turns**, paired bootstrap seed **20251023**; the instrument is repaired and the
  SGLang prep is offline-verified (**23 checks, 0 host actions**).
- C63 (1,136 rows, 2×2 at 32k/71 turns): engine **+1,225.18** [1,132.2, 1,313.3] uncached/turn =
  **2.6738×**; model **+275.83**; engine effect **4.4418×** the model's; model effect
  engine-conditional (**+548.06** vLLM vs **+3.61** SGLang; interaction **+272.23**).
- C57: page 64 vs production page 1 leaves **887/888** prompts identical; page 128 moves the grid one
  block (WIN-SGL, 1,800 rows). C60: **5 units / 7 stacks**; WIN-VLLM 692 rows gives 1,088 / 1,056 /
  2,096-token blocks by model.
- TUNED ran only **1 of 5** documented policies (newest band 0.996109 vs 0.997033; oldest and middle
  0.0, 289 rows); M4 holds **30–31** resident documents = **15.9–16.5 %** of 1,620,892 tokens at
  1.5017× pressure (327 rows).
## Design / arms
| Arm | Engine | Change | Pre-registered question |
|---|---|---|---|
| A3 | SGLang | lfu eviction | does a frequency policy move the bill? |
| A6 | SGLang | HiCache host tier | does the host tier change the per-turn cost? |
| A7 | SGLang | session radix | does session reuse beat block reuse? |
| B3 | vLLM | KV offload | does offload move the vLLM side? |

No arm is added, dropped or renamed: the 12-arm design and P1–P9 stay as written. A6's startup attempt
costs **0 model requests** and is the cheapest first move.

**Budget: first subset ≈280–750 requests, 3–8 restarts**; full 12 arms ≈852 requests.
## Gates / controls
- **Pre-registration is read-only:** `R2-DESIGN.md` is not edited; a deviation is a new addendum file
  (`docs/serving-options/R2-DESIGN-AMEND-01.md`) written before the affected arm runs.
- **Restart discipline:** each restart needs operator approval and the six-key restore proof written
  before the next arm; a restart without the proof halts the batch.
- **Build pin (G13):** publish the `config_sha256 → server_version` table first; an arm whose build
  cannot be pinned is dropped, not guessed.
- **Pressure protocol:** A3 lfu is meaningful only under the M4/TUNED pressure protocol — at 32k
  nothing evicts and TUNED submits each document once, so a frequency policy has no signal.
- **Forbidden claim:** no `--prefix-match-unit` result is printed (2096 % 16 == 0, 1056 % 16 == 0;
  `orchestration/STATUS.md` §8.2 lists it do-not-print).
- **One lock and one restore proof per restart cycle**, and every row carries `usage_has_details`.
## Kill condition
Operational: halt if a restart cannot be followed by the six-key restore proof, or if an arm's build
cannot be pinned. Scientific: all-nulls is not a failure — it is the pre-registered null paper; only a
missing control (no pinned build, no cold pass) kills the result.
## Deliverable
- A verdict table for P1–P9 from the subset, with per-arm statistics and every restore proof.
- A paper draft that either narrows "engine-level" to "configuration-conditional" or publishes the
  null across the documented option space; a contracted-shape handoff naming artefacts and commands.
## Proposed write paths (future unit)
- `experiments/context-cache/cells/R2-SUBSET/plan.md` — subset order; `rows*.jsonl` — new rows only
  (R2-VLLM rows stay frozen); `analysis.json` — per-arm and P1–P9 verdicts.
- `orchestration/units/R2S1.md` — the unit card; `orchestration/handoffs/R2S1.json` — the handoff.
- `docs/serving-options/R2-DESIGN-AMEND-01.md` — only if a deviation is needed.
## Open risks
- All nulls is likely and is still publishable, but the paper must be framed as a null from the start.
- A positive forces "engine-level" → "configuration-conditional", a claim the current paper lacks.
- Restart cycles need operator approval; 3–8 restarts make the box window the binding constraint.
- A3's lfu may be uninformative even under pressure: TUNED's frequency has no signal at 32k.
- No GX10 access in the sweep: restart costs are inferred, not observed; the full 12 arms may not fit.
