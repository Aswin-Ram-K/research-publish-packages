# Measured facts from Consonance — do not re-derive, extend or falsify

Consonance's own rule applies here: a **registered** experiment with passing instrument controls is
evidence; **unregistered reconnaissance** is a hypothesis generator; a **void** experiment produced no
result. The rows below carry that flag, because flattening them is how a recon sketch becomes a quoted
finding.

## Rows

| # | Claim, exactly as measured | Register | Source (Consonance path) |
|---|---|---|---|
| F1 | A re-rendered compact projection cut **payload** tokens **24.2 %** and **billed** tokens by only **2.4 %**, and was **more expensive than the full transcript from step 3 on**. | **registered, CLOSE** (a measured negative; instrument controls passed) | `docs/research/experiments/EXP#43-context-cost-under-cache.md` |
| F2 | The mechanism of F1: the projection's main call was served with **exactly 0 cached tokens at every step** — 0 of 134, 0 of 426, 0 of 499, 0 of 569, 0 of 663 — while the append-only transcript's cached share **climbed** 0 → 0.166 → 0.217 → 0.350 → 0.489. | registered (same experiment) | same |
| F3 | A depth change in the compiled context window moved **48 of 72 prefix bytes**, because the view rides inside the block the prefix is built from. | registered (instrument) | `tools/context/compiler.ts` header; D-086 |
| F4 | Structural paging saves bytes when **few** objects are used; the **all-needed control loses**. The fixture was 30 objects at a uniform 16:1 full-to-brief ratio and is **not** a general token result. | registered | `docs/research/experiments/EXP#5-context-engine-paging.md` |
| F5 | The prefix-reuse boundary experiment is **VOID**: its late-edit cache control failed. A later unregistered diagnostic showed a rewrite cliff but did **not** map the boundary. | **VOID** + unregistered | `docs/research/experiments/EXP#47-prefix-reuse-boundary.md` |
| F6 | The pointer-context live consumer ran its **required-set arm only**; pointer / full / brief-only controls are **untested**, and analyzer/control defects are known. | partial, with known instrument defects | `docs/research/experiments/EXP#48-pointer-context-live-consumer.md` |
| F7 | Prefix recon on Occamy/SGLang, seven requests: identical and append requests win; an 80/20 rewrite misses. | **unregistered reconnaissance — never a guarantee** | `docs/research/OCCAMY_PREFIX_REUSE_2026-10-19.md` |

**F2 + F3 are the load-bearing pair.** Together they say: *payload size is not the lever; prefix stability
is.* Any design that shortens the prompt by rewriting its prefix is expected to lose money, and we have
already watched it happen once.

## Windows on the live routes (probed 2026-10-25)

| Route | Engine | Model | `max_model_len` |
|---|---|---|---|
| `http://192.168.2.168:8012/v1` | sglang | `occamy-1.0` | **131072** |
| `http://192.168.2.168:8014/v1` | vLLM | `qwen3.5-9b` | **32768** |

Two consequences the design note had wrong before these were measured:

1. A **65,536-token** admission cap cannot be exercised on the dense route at all (its window is half that).
2. A "64K vs 128K raw history" arm **cannot exist**: 128K plus an 8K completion reserve is 136K > 131,072.
   The largest honest comparison on this hardware is **64K vs ~120K** on occamy, and a *separate* question
   on the 32K route (where paging is not an optimisation, it is the only way to hold a long task).

## What 65,536 means in Consonance (so it is not misquoted)

In our repository `65536` appears only as the **DSH workspace-instruction *byte* budget**
(`docs/BOARD.md:483`, `docs/VISIT_LOG.md:6`) and as one `maxTokens=65536` compaction record in a historical
inventory. **There is no 65,536-token ceiling anywhere in our code.** If a design lock says 65,536 tokens,
that number came from somewhere else and should be re-derived, not inherited.

## The telemetry rule we already enforce

In `src/model/contract.ts:84` a provider's cache count is `cachedTokens?: number` — **absent when the
provider did not report it, never `0`** — and `src/model/adapters/openai-chat.ts:98` exists specifically so
the field is not dropped on the way in. `src/model/contract.ts:309` gates a "reports usage" claim on that
field being present rather than truthy. This is contract, not convention: an unreported count is
**unknown**, and unknown must not be averaged as a zero.

## What our compiler does today (so you know what you are integrating with)

`tools/context/compiler.ts` (714 lines) composes EXP#4's resolver: a `ContextNeed` carries `budgetChars`
(**character-based**, not token-accurate), and the result names what it expanded, what it dropped and why,
with a typed refusal vocabulary — `resolver-budget-exceeded`, `resolver-refused`, `cumulative-budget` — and
an `unreachable` set. **It refuses rather than truncating, and it never reports an empty success.** The
`expanded[]` list is required in every committed step by D-026, which is why a step is auditable after the
fact.

That is the shape a token-accurate compiler must preserve: same refusals, same auditability, plus tokens.
