# LONGRUN-PREREG — scope, not confinement: p95 TTFT and tokens-to-verified-success over 60 turns
**Status:** REGISTERED 2026-10-26, before any request. **DESIGN ONLY — zero requests sent:** no `curl`, no row
file, no engine contact. Owned path: this file. Sibling design `experiments/ptr-engine/BOUNDARY-PREREG.md` belongs
to another unit and is not edited here. Bound: 20 tool calls.

## 0. The objective, and what it replaces
**Previous objective (now demoted):** uncached tokens per turn. It becomes a **diagnostic**, not the goal.
The 1.84× cost gap (`orchestration/handoffs/C0-EQUALINFO.json`: transcript **1,911** vs pointer **3,524**
uncached tokens/turn) is kept as a **secondary reading** — not thrown away, because *it predicted latency and
that latency was measured*: same file, `ttft_by_arm.occamy-1.0-NVFP4` reads transcript **0.182 s** and pointer
**0.602 s**, so at 12 items the pointer arm was **3.3× slower**, not cheaper. The operator's reframe
(2026-10-26): a real task is **scoped**; a session must not fill and lose focus; older steps are forgotten
*deliberately*; a naive system "wastes so much in doing and fixing the wrong things" that a per-turn premium
for the pointer engine is worth paying. **Cost is not the objective.** The engine is "not to confine the space
but to use the space better."

**Objective (one sentence, units).** Minimise **p95 TTFT (ms per turn)** and **tokens-to-verified-success
(tokens)**, over 60-turn runs at equal-or-better verification, on `occamy-1.0/SGLang` (`:8012`, B=64);
uncached tokens per turn are recorded as a diagnostic only.

**Why the long regime is the only place this can be true** — `papers/context-cache/CLAIMS.md`:
C27 "1,024 tokens: miss 208.7 ms, hit 86.4 ms"; C32 "31,415 tokens: 7,541.9 ms falls to 231.6 ms";
C33 "ratio exponent -0.7837 (r2 0.9962)". Warm and cold are close at short context and **differ ~32× at 31k**;
the design must therefore live where the context is long, not where it is small. C62 supplies the other half:
compaction at a real boundary costs the compacting arm "+134.6 to +747.2 uncached tokens per turn ON AVERAGE
after it" — a wall crossing is not free and must be paid in the fixture, not ignored.

## 1. The four arms (exact)
| arm | policy | requests / turn | prompt at turn 60 |
|---|---|---|---|
| **A `transcript-grow`** | naive: whole history replayed every turn; at the 64,000-token cap it truncates FIFO from the front; **fails at the window** (22,594 + 60×1,883 ≈ 135,600 > 131,072) | 1 | 64k, front-rewritten every turn after 23 |
| **B `transcript-compact`** | state update **at the wall**: at 64k, older turns are replaced by a ~700-token digest; recent 4 turns kept raw; appends between walls | 1 (+1 digest per wall) | 8–64k, sawtooth |
| **C `pointer-stable`** | **redesigned**: frozen index prefix (260–397 tok, byte-identical) + bodies **appended in the suffix** + next turn's body **prefetched** in the same request, so no rewrite lands in the reused prefix; 12 bodies saturate at ~22.6k, tail (state line + question) rewritten after the reused region | 1 | ~23.5k, stable |
| **D `lease-reopen`** | close at the wall and reopen a fresh session carrying only pointers plus a distilled state line (revealed size ≤400 tok); reopens at turns 23 and 56 | 1 | ~2.5k per lease |

**C is the redesign the 1.84× result demands.** The old `R` arm (C0-EQUALINFO) spent **2 requests per turn** and
appended the fetched body into the prefix it had just answered from, so every turn moved the prefix twice and paid
a break — hence 0.602 s against 0.182 s. C removes the second request and puts the delta *after* the reused bytes:
prefetch turn *t+1*'s body at turn *t*, answer from the extended prompt, and never rewrite the index or the bodies.
That is the only change from `R`, and it is the experiment.

## 2. The long-run fixture (`experiments/ptr-engine/longrun/`, host-side, no requests at design time)
- **Working set:** 12 items `k01..k12`, 9,000 B each = **22,594 served tokens** (the measured basis of
  C0-EQUALINFO, `prompt_tokens 22575` cold first turn). `k01` carries `lumen` → **`AUD-4417`**, the fact the
  quality arm already used; the index is `- @knowledge:kNN@1 <hash8> <len>`, 458 B, and leaks no `AUD-`/`lumen`.
- **Turn plan, N = 60.** Turn 1 primes the set. Turns 2–22 add one 9,000 B work note (≈1,883 tok) and one
  question each. **Turn 23 is the wall** (22,594 + 22×1,883 = 64,020 > 64,000) — the cap is a *design choice*
  (half of occamy's 131,072), applied to every arm, which is what makes the arms commensurable.
- **Turns 24–27, the wrong-thing band** (the operator's core claim, in the fixture, not assumed): turn 24
  injects a plausible **decoy** `AUD-0000` for `k01`; turn 25 asks the arm to file a record using it; the verifier
  fails the filed value; turns 25–27 are the arm's **3-attempt repair budget** to re-derive from the source of
  record; turn 28 restates the correction. A must recover from a front-truncated prefix, B from a digest, C by one
  pointer resolve, D from its state line.
- **Checkpoints** (asked as the turn itself, so no extra request): **t10** `lumen`'s audit code (`AUD-4417`) —
  pre-wall, every arm should pass, and any failure here voids the instrument rather than the arm; **t30** the
  retention code for `k04` stated once at turn 2 and never repeated, plus the repaired `k01` value; **t60** the
  final verified `k01` value and the item id that supplied it.

## 3. Pre-registered predictions (written before the decision rule)
| # | prediction | mechanism | falsified if |
|---|---|---|---|
| P1 | C's **p95 TTFT ≤ 0.5× A's** at N=60 | A truncates from turn 23 on *every* turn, so its reused prefix is rewritten at the front and it re-prefills 40–64k; C's index+bodies are frozen from turn 12 and each turn pays only the tail (~700 tok) | C/A ≥ 0.5, **or** C's cached share after turn 12 < 0.80 (its own tail rewrites dominate) |
| P2 | A's **tokens-to-verified-success ≥ 1.5× C's**, and the excess is **repair**, not per-turn cost | truncation destroys the turn-2 `k04` fact and the `k01` source, so A burns 3-attempt repairs at 64k scale; C repairs in one resolve | A's repair_turns ≤ C's, or A's non-repair per-turn uncached alone (within 1.2× of C's) explains the gap — then the win is cost after all and the demotion is wrong |
| P3 | D has the **lowest** p95 TTFT (small prompt; cold 1,024 tok = 208.7 ms) but **loses checkpoint accuracy at t30/t60** unless the ≤400-token state line carries both the turn-2 fact and the turn-24 correction | lease close discards anything not distilled; a short cold prefill is cheap but only what the state line names survives | D ties C's accuracy — then the distilled line *is* sufficient and the frozen prefix buys nothing |
| P4 | B lands within 2× of C on p95 (steady prompt 8–13k) but **fails t30** where its digest dropped the turn-2 code | a digest is lossy exactly where the fact is incidental; between walls B is cheap | B ties C's accuracy at lower total tokens — then compaction, not pointers, is sufficient |

## 4. Decision rule and falsifier
**PASS** iff all three: (i) C p95 TTFT ≤ 0.5 × A's; (ii) C tokens-to-verified-success ≤ A's; (iii) C's mean
checkpoint accuracy ≥ A's − 0.10. **If (i) or (ii) fails, the "use the space better" thesis fails on this
hardware** — recorded as FAIL with the measured ratio, and **not** re-run at a different N to find a passing one.
**Narrowing, not a pass:** if D beats C on p95 *and* ties its accuracy, the win belongs to **scoped reopening**,
not to the frozen prefix; if B ties C's accuracy at fewer total tokens, the digest is sufficient and the pointer
machinery is unjustified. Either outcome is reported as PARTIAL with the winner named.
**Falsifier, in one line:** if `pointer-stable` is not faster at p95 and does not solve with fewer total tokens
than `transcript-grow`, the thesis fails on this hardware and this file says so.

## 5. Metrics emitted per run (one row per turn; JSONL, never a prose table only)
| field | unit | definition |
|---|---|---|
| `ttft_ms` | ms | dispatch → first content token, streaming; `ttft_server_s` recorded beside it; p50/p95 per arm over pooled turns |
| `tokens_to_verified_success` | tokens | Σ(uncached prompt + completion) from turn 1 until the t60 checkpoint verifies; repairs included |
| `repair_turns` | count | turns after a failed verification, capped at 3 per checkpoint |
| `checkpoint_accuracy` | 0–1 | exact match on t10 / t30 / t60, reported per checkpoint and pooled |
| `cached_tokens` share | ratio | `cached / prompt_tokens` per request (null ⇒ 0 under `LIVE-CELLS-2` `usage_note`) |
| `items_in_context` | count | item bodies the prompt can actually resolve this turn |
| `evicted` | count | turns dropped from the prompt this turn (A truncation, B compaction, D close) |
| `context_age_of_surviving_facts` | turns | turn index where each surviving checkpoint fact was stated |

Unverifiable turns are coded `UNVERIFIED` and excluded from accuracy, never imputed as wrong or as right.

## 6. Budget (a human approves or refuses this number)
| arm | turns | extra | reps | requests |
|---|---:|---:|---:|---:|
| A `transcript-grow` | 60 | 0 | 2 | 120 |
| B `transcript-compact` | 60 | 2 digests (turns 23, 53) | 2 | 124 |
| C `pointer-stable` | 60 | 0 (prefetch rides the turn) | 2 | 120 |
| D `lease-reopen` | 60 | 0 (close is host-side; reopen is the turn) | 2 | 120 |
| controls (4, §7) | — | — | 1 | 4 |
| repair reserve | — | 3-attempt cap, band 24–27 | 2 | 12 |
| **total** | | | | **500** |

Derivation: 4 arms × 60 turns × 2 reps = 480; + 4 digests; + 4 controls; + 12 repair attempts = **500**.
Reps = 2 because 3 would be 720 and break the cap; 2 reps × 60 turns = 120 TTFT samples per arm, so p95 is the
6th worst — enough to sit in the post-wall regime. Any request beyond 500 **voids the run**; nothing is silently
extended, and no arm may borrow another arm's turns.

## 7. Controls that must be able to go red (the package's rule)
1. **Identical repeat must hit** — resend turn 12's exact prompt on the warm server: cached ≥ 0.95 × prompt.
   RED (voids the batch) if cached < 0.90: the counter is not measuring reuse.
2. **Never-sent must miss** — a 23k prompt never sent before: cached_tokens = 0. RED if cached > 64: the host's
   own hash is being mistaken for server reuse.
3. **Mismatched tokenizer must show no reuse** — the same body behind a different leading template (different
   leading token ids): cached ≤ 64. Run on `:8012` only; `:8014` reports no cache counters at all
   ("0/45 reported", `C0-EQUALINFO.json:vllm_cache_limit`). RED if cached ≥ 1,000: reuse is text-blind.
4. **No-op checkpoint must cost ≈0** — a checkpoint whose answer sits in the last 200 tokens: repair_turns 0 and
   that turn's uncached ≤ residue + 700. RED if it pays a re-prefill ≥ 5% of the prompt: wall accounting is wrong.

## 8. What this cannot settle
One GPU, one model (occamy-1.0-NVFP4, SGLang, B=64) — no vLLM cache claim is possible (`prompt_tokens_details`
null on every vLLM row); a synthetic fixture (12 items × 9,000 B, one work-note shape); exact-match scoring, which
is blind to a right answer reached for the wrong reason; no multi-agent contention, no human turn-taking; 2 reps,
so p95 is estimated from 120 samples; digests and state lines are the same model's own output (self-distillation
is not independent); and the 64,000-token cap is a design choice, not a measured wall — a different cap moves
turn 23 and re-parameterises every prediction above.
