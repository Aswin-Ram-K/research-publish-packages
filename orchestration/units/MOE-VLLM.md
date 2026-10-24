# MOE-VLLM — full four-arm battery for occamy-1.0 (NVFP4 MoE) on vLLM 0.27.1

**Card prompt (as received):** "MOE-VLLM — full four-arm battery for occamy-1.0 on vLLM, not
the 22-row probe." Automated session, no human present.

## Objective

Turn WIN-VLLM's 22-row gate+grid **pilot** on `occamy-1.0` (:8020, vLLM 0.27.1) into the
measurement it was a pilot for: the four-arm **R/A/C/H** battery on G3's 32k turn schedule
(74 turns, budget 32768), prompts byte-identical to G3's 32k rows so the MoE rows compare
row-for-row with the same weights under SGLang.

## Contract

| item | value |
|---|---|
| Hard bound | 1 launch, 1 live phase, **420-request cap** (used **306**), lock timeout 900 s |
| Live window | launch 271.9 s + cell 172.6 s + restore; total run ≈ 12 min |
| Write paths | `experiments/context-cache/cells/MOE-VLLM/**`, `.occamy.lock` (held for the live phase), this card, its handoff |
| Forbidden | touching `gx10-occamy-nvfp4` / :8012, removing production, enabling systemd, writing outside the workspace |
| Stop condition | any `REFUSE:` from the cell (wrong model, no launch record), or launch health failure → restore and report `partial` |

## What ran

```
.venv/bin/python experiments/context-cache/cells/MOE-VLLM/run_moe_live.py --fresh
```

`run_moe_live.py` holds `.occamy.lock` across the whole live phase and calls:

1. `launch_moe_vllm.py --launch` — stops production `gx10-qwen9b` (never removes it), starts
   `wv-v3` on :8020 from the measured V3 spec (no `--speculative-config`: attempt 1 in the
   pilot died with `RuntimeError: No Qwen3Next layer found in the model.layers.`), waits for
   `/health` 200. **271.9 s**, `launched=True`, `config_sha256 302ebd82…` (identical to the
   pilot's spec).
2. `moe_vllm_cell.py --config V3 --phase all --port 8020 --no-lock` — gate → probe → battery,
   one request in flight, fsync per row. **306 requests, 172.6 s, 0 non-200.**
3. `launch_moe_vllm.py --restore` — removes `wv-v3`, `docker start gx10-qwen9b`, proves
   `qwen3.5-9b / 32768 / block_size="1056"`, re-checks occamy :8012. **`config_ok=True`.**

## Results (all derived from `rows.jsonl`, no re-measurement)

- **Rows 306 / 306 HTTP 200**: gate 2 + probe 20 + battery **284** (= 4 arms × 71 servable
  turns). `rows.jsonl` sha256 `6658227689a35eeedbe3e2645a9093fb099771ca5b6793bb9bb17582758a07a1`.
- **Resolved block 2096**, `max_model_len 32768`, served `occamy-1.0`.
- **Gate**: `/tokenize` 3129 vs served 3131 → offset 2; rep-1 `cached=0`, rep-2 `cached=2096`.
- **Boundary law 15/15**: `cached = 0 if L<g; L-(L mod g) if L mod g != 0`; at exact multiples
  rep-1 is 0 and rep≥2 is `L-g` (`L=2096` → 0/0/0, `L=4192` → 0/2096/2096). Same `L-g`
  ceiling `E4` measured on SGLang's 64-grid, here at 2096.
- **Battery**: hit **0.9012**, uncached **1682.7**/turn overall; arms 0.9011–0.9013 and
  1681.0–1685.0 (spread 4.0 tokens/turn = noise floor; no compaction fires at 32k, so the
  arms are salt-separated replicates). Final prompt 32,466–32,470; gcd of cached = **2096**.
- **Mechanism**: `cached(t) == 2096*floor(prompt(t-1)/2096)` holds **252/280** transitions;
  **28/280** sit exactly one block low, clustered at **7** block completions
  (turns 9, 23, 27, 37, 41, 51, 55). Each arm's excess over the rule is **14,672 = 7×2096**
  exactly. Mean growth 446.9 tokens/turn.
- **Cross-cell vs G3 (same model, SGLang, turns 1–71)**: 284 paired rows, **chars equal
  284/284** (prompt_tokens differ only by the chat template: 144×0, 140×+4). Paired uncached
  delta **+952.96 tokens/turn**, boot95 **[875.54, 1028.11]** (`seed 20251023`, 10 k
  resamples), median 1024 **[772.0, 1124.0]**, **265/284 positive**, ratio **2.306×**.
- **2×2 matrix, 32k band (n=284 each)**:

  | model | engine | block | hit | uncached/turn |
  |---|---|---|---|---|
  | occamy-1.0 (MoE) | vLLM 0.27.1 | 2096 | 0.9012 | 1682.7 |
  | occamy-1.0 (MoE) | SGLang | 64 | 0.9572 | 729.8 |
  | qwen3.5-9b (dense) | vLLM 0.27.1 | 1088 | 0.8690 | 2230.8 |
  | qwen3.5-9b (dense) | SGLang | 64 | 0.9569 | 733.4 |

- **Pilot correction**: the 22-row V3 grid's nominal targets overshot by **1.307–1.318×**
  (e.g. target 2095 → L 2759) because its `/tokenize` call named `qwen3.5-9b` on an occamy
  server; `make_grid_messages` fell back to its word guess. Its five-target law is still
  correct at the measured L (15/15 under the rule above), but its lengths were **nominal, not
  exact**. This cell names the served model and hits 2095/2096/2097/4191/4192 exactly.
- **Restore**: `config_ok=True`, :8014 `qwen3.5-9b` 32768 block 1056, occamy :8012 200,
  `wv-v3` gone, lock released at `00:03:38Z` with the `MOE-VLLM` record.

## Verification (for the independent verifier — 0 requests, no lock)

Re-run offline: `.venv/bin/python experiments/context-cache/cells/MOE-VLLM/moe_vllm_analyze.py`
(reads `rows.jsonl` + frozen comparison rows only). Red→green checks that fail when the claim
is mutated:

1. Swap the mechanism rule from the **previous** prompt to the **current** prompt:
   `cached(t) == g*floor(L_t/g)` matches **192/280**, not 252/280.
2. Use a plain floor boundary law (`g*floor(L/g)` at exact multiples too): probe drops
   **15/15 → 9/15** (the six exact-multiple rows fail).
3. Drop the one-block lag term: expected uncached per arm **104,961** vs observed **119,633**
   — short by exactly **14,672 = 7×2096**.

## Limits / open items (state, do not paper over)

- **No compaction at 32k / 74 turns** (`schedule []`), so the four arms are replicates, not
  policy contrasts — identical to G3/WIN-VLLM/DENSE-SGL at this band. A policy contrast needs a
  depth where a fold fires (G3-LIMIT-V2 used 160 turns at 32k) or a larger `max_model_len`.
- **64k is not runnable on this launch**: `--max-model-len 32768` is the launch invariant
  (MTP removed; `gpu-memory-utilization 0.32` shares the GB10 with production occamy 0.45).
- **The lag condition is unidentified**: 7 of 14 block completions lag one block; prompt
  length, growth and wall time do not separate them from the 7 that do not.
- The dense-vLLM one-block-forever deficit (V1 230/280, V2 220/280 under `floor-1`) is a
  measured contrast here, **not** a mechanism claim.

## Artifacts

| path | role | sha256 |
|---|---|---|
| `cells/MOE-VLLM/rows.jsonl` | 306 measured rows | `66582276…758a07a1` |
| `cells/MOE-VLLM/analysis.json` | every derived number | `3b46b908…bed485c9` |
| `cells/MOE-VLLM/analysis.md` | human report | `1789f1d1…79cc81e7` |
| `cells/MOE-VLLM/moe_vllm_cell.py` | gate/probe/battery, lock discipline | — |
| `cells/MOE-VLLM/launch_moe_vllm.py` | V3 launch/restore wrapper | — |
| `cells/MOE-VLLM/run_moe_live.py` | lock-spanning driver | — |
| `cells/MOE-VLLM/moe_vllm_analyze.py` | offline analyser | — |
| `cells/MOE-VLLM/logs/V3-launch.json` | launch proof, spec, metrics | `23623ffe…fa4198eb` |
| `cells/MOE-VLLM/logs/V3-all.json` | gate + plan + counts | — |
| `cells/MOE-VLLM/logs/battery-plan.json` | servable turns, schedule | `b0ab6594…aea38afb` |
| `cells/MOE-VLLM/logs/live-run.json` | driver timeline + restore proof | `592b287b…42d99954` |
