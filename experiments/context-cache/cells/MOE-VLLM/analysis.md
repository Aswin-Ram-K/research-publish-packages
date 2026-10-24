# MOE-VLLM — occamy-1.0 (NVFP4 MoE) on vLLM 0.27.1: full four-arm battery

Rows: **306** {'gate': 2, 'probe': 20, 'battery': 284}; non-200: **0**. Resolved block **2096**, `max_model_len 32768`, served `occamy-1.0`.
Battery: **284** rows (4 arms x 71 servable turns); compaction schedule **0** (none fires at 32k / 74 turns).
Gate: {"gate_pass": true, "tokenize_count": 3129, "served_prompt_tokens": 3131, "offset": 2, "rep0_cached": 0, "rep1_cached": 2096}

## 1. Boundary law (measured in THIS launch)

- Repeat law at the five targets: **15/15** rows satisfy `cached = 0 if L<g; L-(L mod g) if L mod g != 0; 0 on rep1 / L-g on rep2+ if L mod g == 0`; cold rows all zero: **True** (n=5).
- Exact multiples are special: `L=2096` repeats give **0, 0, 0**; `L=4192` gives **0, 2096, 2096** — the `L-g` ceiling from repeat 2, measured on SGLang's 64-grid as `E4`'s 64-token tax, now at `g=2096` on vLLM.
- The 22-row V3 pilot is **consistent but not exact**: its /tokenize call named `qwen3.5-9b`, so `make_grid_messages` fell back to its word guess and every nominal target overshot by [1.3169, 1.3158, 1.3176, 1.309, 1.3077] — its five-target law holds on all 15/15 repeat rows at the measured L, but the lengths were nominal. This run names the served model and hits 2095/2096/2097/4191/4192 exactly.

## 2. Battery (four arms, G3 32k schedule, 71 servable turns)

| arm | n | hit | uncached/turn | final prompt | mean TTFT ms |
|---|---|---|---|---|---|
| A | 71 | 0.9012 | 1683.0 | 32468 | 465 |
| C | 71 | 0.9013 | 1681.0 | 32466 | 483 |
| H | 71 | 0.9013 | 1682.0 | 32467 | 480 |
| R | 71 | 0.9011 | 1685.0 | 32470 | 473 |
| all | 284 | 0.9012 | 1682.7 | 32467 | 475 |

Arm spread is **4.0 tokens/turn** — the noise floor of identical chains under different salts. At 32k the policy arms do not differ because no compaction event fires (same as G3 and WIN-VLLM).

## 3. Why: per-turn cost is the previous prompt's block remainder

- `cached(t) == 2096*floor(prompt(t-1)/2096)` holds **252/280** transitions (**0.900**).
- **28** transitions (**0.100**) sit exactly one block low (`cached = pred - 2096`), clustered at **7** block completions (turns [9, 23, 27, 37, 41, 51, 55]); each arm's excess over the rule is **14672** tokens = **7 x 2096** exactly.
- Mean prompt growth is **446.9** tokens/turn, so the rule's per-turn floor is `growth + mean remainder (~1048)`; the measured 1683 includes the lag rows.
- gcd of all nonzero battery `cached_tokens`: **2096** = the resolved block.

## 4. Same weights, two engines — and the full 2x2 matrix (32k battery band)

Paired rows with G3: **284**; chars equal **284**; served `prompt_tokens` delta histogram {'0': 144, '4': 140} (chat-template tokens only).

| model | engine | block | n | hit | uncached/turn |
|---|---|---|---|---|---|
| occamy-1.0 (MoE) | vLLM 0.27.1 | 2096 | 284 | 0.9012 | 1682.7 |
| occamy-1.0 (MoE) | SGLang | 64 | 284 | 0.9572 | 729.8 |
| qwen3.5-9b (dense) | vLLM 0.27.1 | 1088 | 284 | 0.8690 | 2230.8 |
| qwen3.5-9b (dense) | SGLang | 64 | 284 | 0.9569 | 733.4 |

Paired uncached delta (occamy vLLM - occamy SGLang): mean **952.958** tokens/turn, boot95 **[875.5352, 1028.1127]**; median 1024, boot95 **[772.0, 1124.0]**; **265/284** positive. Ratio **2.306x**.

## 5. Interpretation

For occamy the engine's resolved block is the whole story: vLLM reuses only full 2096-token blocks of the *previous* prompt, so a turn costs its growth plus the previous prompt's remainder (mean ~1048). SGLang pages at 64 tokens on the same weights and pays ~64/2 instead. That is the ~2.306x per-turn gap.

The dense-model rows under the same engine show a **different** rule, so block size alone does not transfer: V1 (block 1088) matches `floor` **0/280** times and `floor - 1` **230/280** times; V2 (block 1056) is 220/280 under `floor - 1`. The dense hybrid permanently forfeits one whole block per turn (~2,230 uncached/turn), while occamy forfeits it only in the transient lag rows. That is why the MoE cell is *cheaper* per turn than the dense one on the same engine despite its larger block.

One vLLM-specific finding on occamy: a newly completed block lags one request at 7 of the block completions here, costing exactly one block each; the condition that separates lagging from non-lagging completions is **not identified** by prompt length, growth or wall time. It is not the permanent one-block deficit the dense model shows.

## 6. Guardrails and restore

- Prompts are byte-identical to G3's 32k rows (chars equal on every pair).
- 71/74 turns served; turns 72-74 dropped offline from /tokenize, no request spent.
- Launch: production `gx10-qwen9b` stopped (never removed); variant `wv-v3` on :8020; restore by `docker start` -> `qwen3.5-9b`, max_model_len 32768, `config_ok=True`; occamy :8012 health 200 before and after; lock held for the whole live phase.
- Every request is one-in-flight under `.occamy.lock`; 306 requests total, 0 non-200.
