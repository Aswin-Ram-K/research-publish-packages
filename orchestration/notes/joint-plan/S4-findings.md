# S4 — What the prior work actually established (with numbers)

**Unit:** `S4-FINDINGS`. **Written:** 2026-11-07. **Scope:** synthesis only — no inference, no new claim. Every figure cites source `file:line`. Labels: **MEASURED** (from rows), **HISTORICAL** (past config, not current live state), **DERIVED** (arithmetic on measured/historical inputs), **PROSPECTIVE** (planned, unrun).

---

## 1. Was the full context×serving experiment ever run? — No.

**Direct answer: no run ever crossed a context arm against a serving configuration factorially.** Three distinct bodies of work exist, and none of them is that experiment:

- **Gen-6 16-cell grid** (`docs/GRID-2-FINAL.md:13-36`; `docs/STATE.md:14-16`) — measured 2026-10-28. It is **context-only**: four transcript arms (A `transcript-grow`, B `transcript-compact`, C `pointer-stable`, D `lease-reopen`) on **one** model/engine/endpoint (occamy-1.0 on SGLang `:8012`), one fixture, one horizon. Verdict `not_adjudicable`. It never varied serving configuration. See §2.
- **Consonance bounded-context comparative** (`research/next-candidates/consonance-bounded-context-evaluation.md`; `docs/STATE.md:124-131`) — **PROSPECTIVE, UNFUNDED, unrun**: 7,560 requests vs 1,729 remaining (4.37×). No model call made, no run exists (`docs/STATE.md:130`).
- **R2-PROMPT matrix** (`docs/prompt-system/R2-PROMPT-RESULTS.md:13-21`) — **MEASURED, but serving×prompt-policy, not context-arm**: 4 setups × 4 prompt arms (P0/P1/P2/P3), 16/16 cells measured, 71 turns each. It varies serving configuration and prompt policy; it does not run the five context arms A–E.

So the answer to "was the full context×serving experiment ever run" is: **no; gen-6 is context-only on one serving config and is not_adjudicable; the comparative is unfunded; R2-PROMPT is a different (serving×prompt) matrix.** `docs/STATE.md:14-16`, `docs/STATE.md:124-131`, `R2-PROMPT-RESULTS.md:13-21`.

---

## 2. Gen-6 in detail

**Census** (`docs/GRID-2-FINAL.md:13-36`): 16 cells, **6 usable**, 10 excluded.

| cell | arm | turns | `usable_for` | requests billed |
|---:|---|---:|---|---:|
| 1 | lease-reopen | 48 | `["h1","h2","h3"]` | 91 |
| 2 | lease-reopen | 48 | `["h1","h2","h3"]` | 96 |
| 3 | pointer-stable | 48 | `["h1","h2","h3"]` | 96 |
| 4 | pointer-stable | 48 | `["h1","h2","h3"]` | 93 |
| 5 | pointer-stable | 47 | **ABSENT** (no manifest) | 94 |
| 6 | pointer-stable | 46 | **ABSENT** (no manifest) | 93 |
| 7 | pointer-stable | 48 | `["h1","h2","h3"]` | 94 |
| 8 | pointer-stable | 48 | `["h1","h2","h3"]` | 89 |
| 9–10 | transcript-compact | 48 | `[]` | 66, 81 |
| 11–16 | transcript-grow | 48 | `[]` | 77, 53, 56, 56, 82, 53 |

"Usable: 6 of 16 … Excluded: 10 — 8 stamped `[]` … and 2 with no manifest at all, whose `usable_for` is therefore `ABSENT`." `docs/GRID-2-FINAL.md:32-36`. Request rows sum to **1,270** across the 16 cells = the ledger delta exactly (`docs/GRID-2-FINAL.md:34`).

**Four instrument defects** (`docs/STATE.md:47-60`; `docs/GRID-GAP-DIAGNOSIS.md:19-25`):

1. **Treatments never fired** (fixture layer): 8 transcript cells carry `usable_for: []`; `evicted_turns=0`, `digest_rows=0` over 48 turns. `tasks-v6/LR-01.v8.json` prices its wall from *declared* padding (10,616) while live base is 5,628–6,139 tokens and growth 41–98 tok/turn ⇒ turns-to-wall 73–113 > 48. `docs/STATE.md:49-51`; `docs/GRID-GAP-DIAGNOSIS.md:34-76`.
2. **Replicate collapse** (selector layer): `tools/run_grid_report.py:235` dedupes on `(arm, rep, turn_index)` and every gen-6 cell wrote `rep=1`; **288 turn rows → 96 analysed** (`dropped_duplicate=192`). `docs/STATE.md:52-54`; `docs/GRID-2-FINAL.md:54`.
3. **Absent stamp admitted**: `longrun/analyze_stats.py:749` keeps a manifest-less cell (prints it `unstamped`); the two `exit-4` cells are excluded **by name** in the census instead. `docs/STATE.md:55-56`; `docs/GRID-2-FINAL.md:36`.
4. **Cap-gate projection under-counts** (pinned runner): `projected_requests` prices 96, but a tools-on turn bills k+1 requests; the gate refused the 97th → 2 cells `exit 4` at T47/T48 with no manifest. `docs/STATE.md:57-60`; `docs/GRID-GAP-DIAGNOSIS.md:106-135`.

**Why `not_adjudicable`, not a null result** (`docs/STATE.md:37-43`; `docs/GRID-2-FINAL.md:144-148`): a null result would require the comparison to have run and returned no effect. Here the instrument failed before any comparison could be made:
- H1 tail latency: `not_adjudicable_floor` — binding arm pointer-stable p50 156.151 ms [146.306, 291.926], n=48, lag-1 r=+0.2949 ⇒ n_eff 26.14 < 60; p95 refused at n=48; arm A has 0 usable cells. `docs/STATE.md:39`; `docs/GRID-2-FINAL.md:44-47,76`.
- H2 prompt work: `not_adjudicable` — frozen rule is C-vs-A; A has 0 usable cells. (Within-arm only: C cached 5,395.09 vs uncached 355.62 tok/turn n=364; D 1,497.85 vs 332.28 n=184.) `docs/STATE.md:40`; `docs/GRID-2-FINAL.md:82-91`.
- H3 checkpoint quality: `not_adjudicable` — grid's `x/12`, `x/9`, `answered_ratio` are **placeholder zeros**, not measurements; no admissible emitter. `docs/STATE.md:41`; `docs/GRID-2-FINAL.md:93-106`.
- TVS: `UNDEFINED` — `n_verified_success = 0` arm-level and 0 at first checkpoint; denominator undefined, no token count substituted. `docs/STATE.md:42`; `docs/GRID-2-FINAL.md:108-114`.

Overall: **`not_adjudicable`** (`docs/STATE.md:44`; `docs/GRID-2-FINAL.md:146`). The card's claim that "this cycle's binding constraint is the request budget, not the instrument" is **declined**: recomputed, this grid billed 1,270 requests (79.375/cell), and 16 cells at the highest bill any cell produced cost 1,536 — inside the 1,729 remaining. `docs/GRID-2-FINAL.md:148`.

---

## 3. What IS established (quantified)

### 3a. Historical serving configurations O1–O4 (all HISTORICAL, not current live state)

Source: `docs/serving-options/BEST-CONFIG.md` §1 table (`:16-21`) and §2 (`:42-78`). None is running today (`R2-serving.md:18,46-53`).

| setup | model × engine | hit | uncached / turn | naive-history arm | grid_unit | rows | CI on unc/turn |
|---|---|---:|---:|---:|---:|---:|---|
| **O1** | occamy-1.0 (MoE, NVFP4) × SGLang | **0.958789** | **729.20** | 723.39 (A) | **64** | 296 | **[659.16, 787.62]** |
| **O2** | qwen3.5-9b (dense, NVFP4) × SGLang | **0.958079** | **713.99** | 714.69 (A) | **64** | 284 | **[651.31, 778.07]** |
| **O3** | occamy-1.0 (MoE, NVFP4) × vLLM | **0.887475** | **1384.96** | — (no A arm) | 48 (gcd; no page law) | 71 | **[1235.25, 1532.17]** |
| **O4** | qwen3.5-9b (dense, NVFP4) × vLLM | **0.869037** | **2230.78** | 2231.03 (A) | **1088** (resolved block) | 284 | **[2131.79, 2330.27]** |

`unc/turn` = mean over rows selected in each setup's `evidence.selector`, computed as `prompt_tokens − cached_tokens` per row; hit = Σcached / Σprompt. `BEST-CONFIG.md:23-24`.

Flags (HISTORICAL, from `BEST-CONFIG.md:44-78`):
- **O1**: `page_size 1`, `mamba_radix_cache_strategy extra_buffer`, `radix_eviction_policy lru`, `mem_fraction_static 0.45`, `kv_cache_dtype fp8_e4m3`, `max_mamba_cache_size 64`, `max_running_requests 5`, context 131072, sglang `0.0.0.dev1+g4ccff141d`. `:44-46`.
- **O2**: container `gx10-w3-dense9b` at `192.168.2.168:8017`: `--page-size 64 --mamba-radix-cache-strategy no_buffer --max-mamba-cache-size 40 --mem-fraction-static 0.08 --context-length 32768`, NVFP4 `modelopt_fp4`. `:54-56`.
- **O3**: `--block-size 64 --prefix-match-unit 16 --mamba-cache-mode align --enable-prefix-caching --enable-prompt-tokens-details --kv-cache-dtype fp8 --gpu-memory-utilization 0.34 --max-model-len 32768`, no `--speculative-config mtp`. `:63-65`.
- **O4**: `--block-size 64 --quantization modelopt_fp4 --kv-cache-dtype fp8 --enable-prefix-caching --enable-prompt-tokens-details --gpu-memory-utilization 0.15 --max-num-seqs 6 --max-num-batched-tokens 8192 --max-model-len 32768`, image `sha256:2c211a1273b4…`, **with** MTP speculative-config. `:72-75`.

Engine-vs-model reading (`BEST-CONFIG.md:93-111`, HISTORICAL): same engine, two models (SGLang): O1 729.20 vs O2 713.99 — a 15.21-token gap (2.1%). Same weights, two engines: occamy-1.0 costs 1384.96 − 729.20 = 655.76 more tokens/turn on vLLM than SGLang (1.899×); qwen3.5-9b costs 2230.78 − 713.99 = 1516.79 more (3.125×). Inside vLLM the dense model pays 845.82 more than the MoE (1.611×). Sizing caveat: the two vLLM numbers are measured at different memory fractions on the same GB10 (O3 at 0.34 with 13.93 GiB KV cache; O4 at 0.15 with 64,736-token KV cache), so the interaction mixes engine, available KV cache and checkpoint; the engine main effect (O1 vs O3 on identical weights and context) is clean, the interaction is not. `BEST-CONFIG.md:106-111`.

### 3b. C0F equal-information control (MEASURED, one equal-information data point)

Source: `research/next-candidates/consonance-bounded-context-evaluation.md:56` (P2 row): `C0-EQUALINFO` handoff `orchestration/handoffs/C0-EQUALINFO.json`: C0F **1,911.2** uncached/turn vs R **3,524.0**, ratio **1.8441**. `docs/STATE.md:145-146` repeats: "the one equal-information measurement points the other way — C0-EQUALINFO C0F mean 1,911 vs R mean 3,524 uncached, ratio 1.8441."

What it **does** license: the pointer arm can be **more** expensive at equal information than the full-transcript arm. `consonance-bounded-context-evaluation.md:56`.

What it **does not** license: that the pointer case is dead — it survives only above the window or on cache-hostile history (`ADOPTION.md`). `consonance-bounded-context-evaluation.md:56`. Arm D must be compared against Arm A at equal information, not against a truncated strawman. `docs/STATE.md:145-146` (README.md §"What cannot be claimed today": "A pointer/bounded context design is cheaper than a full transcript" is unavailable; "the design changes which appends happen; whether that is cheaper at equal information is the paper's open question"). `experiments/ptr-engine/research-seed-concepts/README.md:104`.

### 3c. R2-PROMPT matrix (MEASURED, serving×prompt-policy; 16/16 cells)

Source: `docs/prompt-system/R2-PROMPT-RESULTS.md`. Mean uncached (prefill) tokens per turn, 71 turns each, 4 setups × 4 arms (P0 whole-context, P1 pointer+tail, P2 = P1 + grid pad, P3 = P1 + mid-context edit). Full table: `R2-PROMPT-RESULTS.md:34-52`. Headline contrasts (`R2-PROMPT-RESULTS.md:64-69`): P1/P0 null on O1/O2/O3, non-null saving −11.7% only on O4; P2/P0 non-null saving on O2 (−14.0%) and O3 (−51.5%), non-null *worse* on O4 (+20.6%); P3/P1 null on all four. Quality guard (`R2-PROMPT-RESULTS.md:105-117`): pointer form changes the answer surface in 20/20 (O1), 14/20 (O2), 20/20 (O3), 19/20 (O4) first-32-token mismatches. (Reported as context for what serving-side evidence exists; it is not the context-arm comparative.)

### 3d. Other established ptr-engine facts (MEASURED/HISTORICAL)

- Append-cost law: `uncached = (P1 mod 64) + L` on SGLang (residual 0 in 186/186 rows); `uncached = (P1 mod 1056) + 1056 + L` on vLLM. `experiments/ptr-engine/RECORD.md:36-37`; `experiments/miss-law/LAW.md`.
- 67.1141× is **body bytes over index bytes** (30,000/447), not a token/cost/latency saving. `docs/STATE.md:145`; `experiments/ptr-engine/RECORD.md` §1.
- C54: server-wide resident working set 30–31 docs = 258,035–266,636 tokens = 0.1592–0.1645 of 1,620,892 declared, at 1.501724× pressure, binding constraint the state cache (`max_mamba_cache_size` 64), verdict `consistent_with_lru`. `consonance-bounded-context-evaluation.md:62`.
- C53: B/A 6.744331504 [4.04542649, 9.44323652], C/A 1.105174403; A 123,240 prompt / 102,912 cached / 20,328 uncached, B 123,256 / 0 / 123,256, C 123,216 / 103,424 / 19,792; 8 fan-outs × 8 branches, single seed. **The estimator is the unweighted mean of 8 per-fan-out ratios** (5.379888, 5.667647, 6.034483, 5.389356, **14.70229**, 6.015625, 5.385475, 5.379888; stdev 3.227761582); the ratio of aggregated totals is **6.063360882** and fan-out 5 drives the mean. `consonance-bounded-context-evaluation.md:61`.
- QUALITY-POSITIVE-CONTROL: verdict `PATH-CANNOT-SAY-YES`; a valid `pos-full` log fails 7 checks (`cp.t12`, `cp.t24`, `cp.t46`, `acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.1`); only the bare-value diagnostic `pos-exact-only` passes (`verified_success` true, 3/3, TVS 22,396); `grade_v2.py` incompatible. `consonance-bounded-context-evaluation.md:66`.
- Ledger: 2,591 spent / 1,729 remaining of 4,320, rebuilt 2026-10-28 (`docs/STATE.md:64-72`); gen-6 marginal cost 1,270 / 16 = 79.375 requests/cell; highest single cell 96; 16 cells at max = 1,536 < 1,729. `docs/STATE.md:68-71`.

---

## 4. The law package (residual tables)

Source: `experiments/ptr-engine/research-seed-concepts/README.md:137-164` (Verifying block); `experiments/ptr-engine/RECORD.md:138`; `VALIDATION-ROADMAP.md:59` (gate 0.11).

Recompute command (`README.md:139-149`): filter rows with `L_app is not None` and `role=='measure'` and `prev_prompt_tokens is not None`; residual = `uncached_tokens − ((prev_prompt_tokens % B) + extra + L_app)` with B=64 extra=0 for sglang, B=1056 extra=1056 for vllm.

Expected output (`README.md:161-162`):
- **sglang: 301 rows** — `{0: 218, 2048: 2, 4096: 2, 6144: 2, 7680: 1, 7936: 2, 8000: 8, 8064: 66}`.
- **vllm: 86 rows** — `{-1056: 1, 0: 85}`.

What was measured: the per-append law on the miss-law rows (`experiments/miss-law/rows.jsonl`, 774 lines: 387 measure / 383 prime / 4 controls; `RECORD.md:40`). The law states that appending L tokens to a primed prefix of P1 tokens re-bills `(P1 mod B) + L` (sglang, B=64) or `(P1 mod B) + B + L` (vllm, B=1056). The residual is the difference between measured `uncached_tokens` and that prediction.

Reading of the tables (`RECORD.md:138`; `README.md:161-164`): residual **zero on every row that is not an avalanche**, and the avalanche rows bill `P1 + L` exactly (the whole prefix is re-billed when `P1 mod B ∈ {0,1}`). The 66 sglang rows at 8064 are avalanches (P1 mod 64 ∈ {0,1}); the single vllm row at −1056 is the one off-by-block case. `RECORD.md:138` corrects an earlier claim ("303 exact at residual 0; 1 is off") — strictly-zero is 160 on the combined 304, with 60 sglang rows at −64/−128/−192 and 69 vllm rows at −1056 etc.; the 301/86 split is the *measure-role* subset.

What this does **not** license (`README.md:109`; `RECORD.md` C7 at `:140`): the law is declared for **one append onto an already-primed prefix**; multi-append was never swept end to end (§6.3 extrapolates). The magnitude is instrument-dependent (counter-derived cached vs null, `RECORD.md:114` "UNDECIDABLE"). The law is not generalized to conversations or to other engines.

---

## 5. What is NOT known

- **No adjudicable context-arm comparison across serving settings.** Gen-6 is `not_adjudicable` on one serving config; the Consonance comparative (A/B/C/D/E + C0F) is unfunded and unrun. `docs/STATE.md:14-16,124-131`.
- **No memory-sweep data.** No measured memory-utilization sweep exists; higher cache memory is a variable to test, not a presumed win. `plan §2`.
- **No verified restore.** No documented restore procedure for O1–O4 (no launch scripts/unit files in repo); all restore paths UNVERIFIED. `R2-serving.md:55-57`.
- **No dollar/energy cost.** USD 0.20/1M uncached input tokens is a *declared* price, not measured (on-prem box); energy cost unknown. `R2-PROMPT-RESULTS.md:121`; `plan §4`.
- **No real-workflow validation.** Task selection and ground truth for representative workflows are unspecified; request counts are estimates until bounded from an actual task envelope. `plan §5`.
- **No multi-hop fixture.** Every authored checkpoint is single-source; multi-hop retrieval and unavailable/stale/revoked source classes are MISSING. `consonance-bounded-context-evaluation.md:157-161`; `VALIDATION-ROADMAP.md:61-63`.
- **No multi-hop / stale-source measurements.** Reported `UNAVAILABLE`/`NOT_OBSERVED`, never scored as success, no fixture fabricated.
- **No qwen3.5-9b-on-vLLM-without-MTP measurement.** O4 ran *with* MTP; stripping it is a new measurement, not an edit. `BEST-CONFIG.md:81-88`.
- **No verified quality arm.** Quality path cannot say yes (`PATH-CANNOT-SAY-YES`); every quality arm's `verified_success` limb is void before its first call. `consonance-bounded-context-evaluation.md:66`.
- **No current live SGLang/vLLM.** None running on this machine today (`R2-serving.md:18`); O1–O4 all UNAVAILABLE.
- **No independent replication of the append law beyond one append.** Multi-append never swept end to end. `README.md:109`.

---

## 6. Ceiling on what the current evidence can support

One short paragraph a technical reader can quote:

> The current evidence supports three things and no more: (i) an exact per-append cache-billing law on two engines (`uncached = (P1 mod B)+L` on SGLang B=64, `…+B+L` on vLLM B=1056), measured on 301+86 measure-role rows with residual zero on non-avalanche rows, declared for one append onto a primed prefix only; (ii) a serving-side matrix showing aligned padding pays on fine cache units (O2 −14.0%, O3 −51.5%) and loses on coarse ones (O4 +20.6%), with the pointer form itself never showing a cost saving on three of four setups and never quality-equivalent (14–20 of 20 answer mismatches); and (iii) a gen-6 context grid that spent 1,270 requests and returned `not_adjudicable` because its treatments never fired, its replicates collapsed, its absent stamps were admitted, and its cap gate under-counted — not because the budget bound it (16 cells at the observed max bill cost 1,536 against 1,729 remaining). Everything else — whether a bounded/recoverable context design is cheaper or quality-neutral than a full transcript at equal information, whether any memory sweep helps, what a restore costs, dollar/energy cost, and multi-hop or real-workflow behaviour — is unmeasured, unfunded, or UNAVAILABLE, and must not be stated as a result.

---

## Sources

- `docs/STATE.md` (esp. §§1, 2a, 6) — current state, gen-6 verdict, ledger.
- `docs/GRID-2-FINAL.md` — census, H1/H2/H3/TVS, price arithmetic.
- `docs/GRID-GAP-DIAGNOSIS.md` — four defects, wall arithmetic, gate.
- `docs/LEDGER-RECONCILE.md` — ledger semantics, kind rule, reconcile arithmetic.
- `docs/serving-options/BEST-CONFIG.md` — O1–O4 historical configs.
- `research/next-candidates/consonance-bounded-context-evaluation.md` — arms, C0F, gates, unavailable classes.
- `docs/prompt-system/R2-PROMPT-RESULTS.md` — serving×prompt matrix.
- `experiments/ptr-engine/research-seed-concepts/README.md` — residual tables, corrections.
- `experiments/ptr-engine/RECORD.md` — engine record, residual correction.
- `experiments/ptr-engine/research-seed-concepts/VALIDATION-ROADMAP.md` — gates 0.1–0.11.
- `orchestration/notes/joint-plan/R1-design.md` — arm arithmetic, 7,560 derivation.
- `orchestration/notes/joint-plan/R2-serving.md` — live serving inventory (current machine).
- `orchestration/notes/joint-plan/R3-ledger.md` (if present) — ledger detail.