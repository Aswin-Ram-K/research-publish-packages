# BOUNDARY-PREREG — where the pointer protocol actually wins
**Status:** REGISTERED 2026-10-26T01:22-0500, before any request. DESIGN ONLY — no `curl`, no row file, no
server contact (a sent request would void the registration). Bound: 18 tool calls.
**Question.** Does the pointer protocol beat a pasted working set at the two places the equal-information
baseline left open — when the set cannot be pasted at all, and when the history is cache-hostile?
**Sub-questions.** **(i) Window overflow:** is a pasted whole set *impossible* above the window rather than
merely expensive, and what does the best legal paste cost per turn against the pointer? **(ii) Cache
hostility:** does a history that rewrites its recent turns (Round 1: 0% hit on per-branch rewrites) erase the
transcript's advantage, making the pointer cheaper by construction?
**Artefacts.** `orchestration/handoffs/C0-EQUALINFO.json` — `uncached_per_turn_by_arm` (C0F occamy 5,676/28/28
mean **1,911**; R 9,476/1,044/52 mean **3,524**; `headline_ratio` 1.84), `truncation` (occamy est 22,524 tok
of 131,072; qwen served 22,594 of 32,768), `vllm_cache_limit` (0/45 vLLM rows report cached tokens).
`experiments/ptr-engine/RECORD.md` §2 append-cost law + C2 layer ("an append re-bills regardless of how warm
the prefix was", 8.40x/8.41x) and §3 hit-ledger reconciliation. `papers/context-cache/CLAIMS.md` **C53**
(branching arm B 123,256 prompt / **0 cached**, B/A 6.744), **C55** (SGLang grid 64), **C63** (engine, not
model, sets the bill: engine +549.33/turn vs model −400.02, interaction −403.63).
**Item basis.** 22,594 served tokens / 12 items = **1,883 tok/item** (9,000 B each): 12 = 22.6k, 40 = 75.3k,
120 = 226.0k, 400 = 753.2k tok = 108k, 360k, 1.08M, 3.6M B.

## 1. Arms (exact)
| arm | definition | endpoint |
|---|---|---|
| `C0-static` | every item's body pasted in the system message each turn; **byte-identical prefix** on turns 2–4; one request per turn | occamy-1.0-NVFP4 SGLang `http://192.168.2.168:8012`; qwen3.5-9b vLLM `:8014` |
| `C0-trunc` | whole set pasted but **fact-pinned FIFO** eviction: `k01` (fact item) never evicted, newest non-fact items fill `window − 1,024` tokens, oldest non-fact out first; `evicted` per row | same two |
| `R-pointer` | 458-B index only (`- @knowledge:kNN@1 <hash8> <len>`, no `AUD-`/`lumen`), fetch per turn, 2 requests/turn (fetch + answer) | SGLang native tool-call fetch; vLLM text `FETCH` (image refuses `tool_choice`) |
| `R-pointer-prefetch` | as `R-pointer`, but the **next scheduled item's** body is appended to the current resolve request, one turn early, so the answering turn adds no new bytes | same two |

**Engine caveat:** vLLM reports no cache counters (0/45 rows, `cached_reported:false`), so `:8014` carries
only accuracy and **gross** tokens; every qwen "uncached" is an upper bound on the net bill. Counter-based
predictions (P5, P6) run on `:8012` only. **Reps:** 3 sequential on a warm server — rep 1 pays the cold
prime, reps 2–3 measure steady state; the prime is reported as its own number, never averaged away silently.

## 2. Working-set ladder
| rung | items | bytes | tokens | occamy 131,072 | qwen 32,768 |
|---|---|---|---|---|---|
| 12 | 12 | 108k | 22.6k | `C0-static` possible (measured) | possible (22,594 served, 10,174 headroom) |
| 40 | 40 | 360k | 75.3k | possible (75,320 ≤ 131,072) | **IMPOSSIBLE** — first crossing |
| 120 | 120 | 1.08M | 226.0k | **IMPOSSIBLE** — first crossing | impossible |
| 400 | 400 | 3.6M | 753.2k | impossible | impossible |

Occamy fits 69 items (129,927); `C0-trunc` keeps 69 there and **16** on qwen (30,128 ≤ 31,744). Claim (i) is
answered at **rung 120 on occamy** and **rung 40 on qwen** — three rungs earlier on the dense model. An
impossible arm is recorded `IMPOSSIBLE` with the exact 4xx/error string, never rendered as a cost.

## 3. Cache-hostile ladder (occamy only, rung 12, so (ii) is isolated from (i))
`branches` ∈ {1, 4, 16}: b divergent histories, each turn rewriting the last min(N, b) turns of its own,
interleaved so that between two requests of the observed branch, b−1 other prefixes are served. Requests per
rep per arm = 4 observed + (b−1) pollution sends = 4 / 7 / 19. Pollution sends carry `cached_tokens` too, so
"the prefix was polluted" is measured, not assumed.

## 4. Pre-registered predictions (written before the decision rule and before any run)
**P1 — Replication gate.** Occamy rung 12: `C0-static` mean **1,911** (±15%: 1,624–2,198), `R-pointer`
**3,524** (±20%), ratio **1.84** in [1.4, 2.4], all arms 3/3. *Mechanism:* turns 2–4 are a byte-identical
prefix (22,528 cached after the prime) while each resolve appends a body, and an append re-bills regardless
of warmth. **If P1 fails the run is invalidated, not reinterpreted.**
**P2 — The 1.84x inverts *below* the window.** Occamy rung 40, `R/C0-static` on the rep-mean falls **below
1.0**, expected **0.50–0.65** (C0-static ≈ (75,320/4 + 28 + 28)/3 = **6,292**/turn; R ≈ **3,524–3,850**, its
fetched set not growing with the rung). *Mechanism:* the transcript's only advantage is one cold prime
amortised over four turns, and that prime scales with the set. **Refuted if the ratio ≥ 1.0** — then 1.84x is
a window-independent property, not an artefact of rung 12.
**P3 — Window-bound plateau.** Occamy rungs 120 and 400: `C0-trunc` mean uncached/turn the **same within
±5%** ((129,927/4 + 56)/3 = **10,846**, both bound to 69 items), `R/C0-trunc` **0.30–0.45** at 120 and
**0.35–0.50** at 400. **Refuted if** the rungs differ >5% (eviction not binding) or `C0-trunc` exceeds 11,500
(the rule did not cap the context).
**P4 — The dense model crosses first.** qwen rung 40: `C0-static` `IMPOSSIBLE` (75,320 vs 32,768) while
occamy still serves it; `C0-trunc` flat at **30,128 gross tokens every turn**; `R/C0-trunc` ≈ **0.22**, which
*overstates* the pointer's saving because the gross count hides every hit. **Refuted if qwen serves
`C0-static` at rung 40** — the 1,883 tok/item basis would be wrong by ~2.3x and the crossing moves to rung ~17.
**P5 — Hostile history kills the transcript's edge.** Occamy rung 12, `C0-static` hit rate ≈0.97 at b=1,
**<0.25** at b=4, **<0.10** at b=16; at b=16 `R/C0-static` ≥ **0.8**. *Mechanism:* interleaved rewrites leave
no byte-identical prefix — C53's arm B already shows the shape at fan-out scale (123,256 prompt, **0 cached**).
**Refuted if b=16 holds hit >0.50**; claim (ii) would be false and the pointer case would rest on (i) alone.
**P6 — Prefetch moves the break, it does not remove it.** `R-pointer-prefetch` per-rep uncached total within
**±20%** of `R-pointer`; its answering turn carries **≤5%** of R's T4 uncached and its resolve turns **≥1.8x**
R's. *Mechanism:* the bytes are identical, only their arrival moves, so the break rides a request that was
already going to break. **Refuted if the per-rep total drops >20%** — the append-cost law would not be binding.
**P7 — Accuracy is not the variable.** Every *served* arm is **3/3** on occamy at every rung; on qwen
`R-pointer` must fetch `k01` at T4 (the repair run's 0/1 failed exactly there). **Refuted if any occamy arm
scores <3/3 at rung 12** — a quality regression stops the cost comparison rather than sitting beside it.

## 5. Decision rule (fixed now, after the predictions)
Question, verbatim from `experiments/ptr-engine/quality/PREREG.json`: *"Each knowledge item records one
calibration constant's audit code. Naming one constant is meaningful only if its own audit code is known.
Which audit code belongs to the constant named 'lumen'?"* — **`AUD-4417`**, exact case-sensitive match,
"Reply with the audit code only." Minimum **3 reps**; one rep is descriptive, never a verdict.
- **Claim (i) supported** iff at occamy rung 120 **and** qwen rung 40: (a) `C0-static` is `IMPOSSIBLE` with
  the exact error recorded and (b) `C0-trunc` mean uncached/turn ≥ **2x** `R-pointer`'s on the same cell, over
  3/3 reps. If `C0-trunc/R < 1.5`, claim (i) is **not** supported: above-window pasting is expensive, not
  impossible, and the recommendation becomes "truncate-and-paste before you switch".
- **Claim (ii) supported** iff b=16 hit < 0.10 **and** `R/C0-static` ≥ 0.8. Hit > 0.50 at b=16 **refutes** it.
- **Both refuted** → recorded: the pointer is never cheaper here; the transcript wins below the window and
  loses above it. Written down, not negotiated.
- **Instrument gates.** P1 replication; C55 grid 64 (a hit rate from <64 cached tokens is noise); a null
  `cached_tokens` is **0** with `cached_reported:false` (RECORD tail, settled 2026-10-26), never "unknown".
- **Stop rule.** A rung that cannot be served (overflow, OOM, timeout, 5xx, empty content) is recorded
  **`UNAVAILABLE`** with the exact error and null — never 0 — in its cost fields; the ladder continues. Two
  or more `UNAVAILABLE` arms in a cell make the cell `UNAVAILABLE`. ≤2 retries per request (same `unit`,
  `attempt+1`); a repaired request (thinking off) carries `instrument:"repair: …"` so it stays separable.

## 6. Cost (requests, so a human can approve or refuse it)
Per rep per arm: `C0-static` **4** (one per turn, no resolver), `C0-trunc` **4** (same), `R-pointer` **8**
(fetch + answer per turn; T4 may add one resolve), `R-pointer-prefetch` **8** (same count, the prefetch
riding the resolve request) = **24 per rung-model-rep**. Ladder A = 24 × 3 reps × 8 cells = 576, minus **60**
for the five impossible `C0-static` cells (occamy 120/400 = 24; qwen 40/120/400 = 36) = **516**. Ladder B =
(4+7+19) × 2 arms × 3 reps = **180**. **Total 696 scheduled requests** — stage 1 = 216 (under-window cells),
stage 2 = 300 (above-window cells), stage 3 = 180 (hostile) — ceiling **810** with the resolve/retry reserve.
Three refusal points, one per stage.

## 7. Row schema (per request, one file per stage)
`unit, ts_utc, endpoint, model, arm, rung_items, branches, turn, rep, items_in_context, evicted,
prompt_tokens, cached_tokens, cached_reported, completion_tokens, ttft_server_s, answer_correct, error`

## 8. What this cannot settle
One GPU, one host, sequential single client: no concurrency, no radix-tree eviction under memory pressure.
C63 shows the **engine** sets the bill (engine +549.33 vs model −400.02), so the two engines confound any
model claim with their launch flags. The corpus is synthetic and i.i.d. — 9,000-B items, one fact item, no
semantic redundancy, no distractor pressure in T1–T3. Scoring is exact-match on one string: 3/3 is a floor,
not a quality curve. vLLM reports no counters, so the pointer looks cheaper on `:8014` than can be shown.
`R-pointer` on vLLM is text `FETCH`, not `tool_choice`, so the two R arms are not protocol-identical.
Nothing here speaks to dollars, power, or any wall-clock SLA beyond `ttft_server_s`.
