# SYS-OPT-RESULTS.md — the SYS-OPT round record

**Rule of record:** [`VERSIONS.md`](VERSIONS.md) — pre-registered `2026-10-24T08:40:15Z`, **before any
SYS-OPT cell existed**. §4 (CEILING), §5 (REGRESSION) and §6 (HEADROOM) are applied here as written; this
file records their consequence and does not renegotiate them.
**Round record:** [`SYS-OPT-R1B-RESULTS.md`](SYS-OPT-R1B-RESULTS.md) — the full round-1 measurement report,
including per-arm tables, quality components and the falsification detail.
**Machine-readable verdict:** [`state/sys-opt-verdict.json`](../../state/sys-opt-verdict.json).
**Published release:** [`RELEASE-v1.json`](RELEASE-v1.json).

> **No number in this file was measured by the unit that wrote it** (`SYS-OPT-CLOSE`). Every figure is a
> field of [`state/sys-opt-v1.json`](../../state/sys-opt-v1.json), transcribed from
> [`orchestration/handoffs/SYS-OPT-R1B.json`](../../orchestration/handoffs/SYS-OPT-R1B.json). This unit sent
> **0 live requests**.

---

## 1. CEILING LINE (VERSIONS.md §4)

**SYS-OPT CLOSED AT ITS CEILING AT ROUND 1.**

| field | value |
|---|---|
| verdict | **`no_signal`** — improved on **neither** model |
| `closed_at_ceiling` | **`true`** |
| `ceiling_round` | **`1`** |
| best version | **`V0`** (nothing was adopted; §4's "V0 if none was adopted") |
| rounds executed | 1 of a budget of 3 — **two rounds unspent, and not available** |
| headroom | **no headroom claimed** (§6 condition 1 fails: no version improved on either model) |
| quality guard (§5) | **not fired** (no rise > 1.0 pp on either model) |

§4 requires that a ceiling be read as **the rule working, not a failure**: the round budget's purpose is to
stop the search when the pre-registered conditions say stop, and round 1 said so. No spare round was spent
chasing noise. The two unspent rounds are **not** headroom — §6 grants headroom only to a version that
improved on both models, and none did.

## 2. Why `no_signal` — per model (§2 conditions, both required, never pooled)

Condition 1 is *Δunc/turn with a 95 % CI excluding zero*; condition 2 is *hit gain ≥ 2.0 pp*. The sign
convention (§2) makes a cost improvement a **negative** Δunc. On both models the CI excludes zero and the
mean is **positive**.

| model | setup | V0 unc/turn | V1 unc/turn (P1 headline) | Δunc/turn | CI95 | drift-corrected Δ | hit gain | cond. 1 (cost) | cond. 2 (hit) | improved? |
|---|---|---|---|---|---|---|---|---|---|---|
| MoE `occamy-1.0` | **O1** SGLang `:8012` | 522.718 | **652.831** | **+130.113** | [+121.718, +138.394] | +66.958 | **+6.72 pp** | **no** (CI excludes 0, mean positive) | yes | **no** |
| dense `qwen3.5-9b` | **O4** vLLM `:8014` | 1664.352 | **1893.169** | **+228.817** | [+140.310, +319.183] | +215.690 | **+22.20 pp** | **no** (CI excludes 0, mean positive) | yes | **no** |

**The hit gain is real and buys nothing.** The index grew, so a larger share of a larger prompt is cached
while the uncached tokens per turn also grew. §2 requires both conditions on each model; the cost condition
fails on both, so the combined status is `no_signal` and §4 fires.

**The drift correction does not rescue it.** The untouched reference arm P0 was re-run with identical bytes,
so its gap to the pinned P0 is instrument drift: MoE +63.155, dense +13.127. Subtracting drift leaves
**+66.958** and **+215.690** — still a cost rise, still positive, still above the +45 falsification ceiling
the round pre-registered. Reference arms P0 and P3 are reported beside the headline and are **never**
averaged into it (A2.1).

**Falsification (A2.2).** A2.2 predicted a ≥ 20 pp P1-form quality improvement and Δunc no worse than +45.
Measured: MoE **0 pp**, dense **−5 pp**; Δunc **+130.1** and **+228.8**. **Falsified on both models.** Under
A2.2's pre-registered falsification the change is **reverted** — `quote_tokens` returns to 0 — and lever 1
may not be retried without a new measured finding (§8). Recorded, not dropped.

## 3. Quality guard (§5) — did not fire

Read on the **P1 form**, the form the change acts on. The P0 form has no index and therefore no `sha8` to
state, so it is unanswerable by construction and scores 0/in every version (recorded limitation, A2.3).

| model | P1-form mismatches before | after | change | §5 verdict |
|---|---|---|---|---|
| MoE | 20/20 | 20/20 | **0.0 pp** | no regression |
| dense | 19/20 | 18/20 | **−5.0 pp** | no regression |

§5 fires at a rise **> 1.0 pp**. Neither model crosses it, so this round is a `no_signal`, not a
`discarded: quality_regression`. Had §5 fired it would have decided nothing about the ceiling (§5), so the
§4 outcome is stable either way.

The two component rates carry the useful finding: the **MoE ignored the new quote column** (`span_ok`
0/20 → 0/20; its V1 P1 answers are the V0 answers verbatim), while the **dense model started quoting**
(`span_ok` 0/20 → 20/20) and **stopped stating the hash** (`sha8_ok` 20/20 → 2/20). The change moved one
model's answer form toward the other's and cost it the quantity the question asks for.

## 4. HEADROOM (§6) — none claimed

§6 permits the claim only when **both** hold: the version improved on both models, **and** a named unused
lever remains with a measured basis for acting on both. Condition 1 fails, so condition 2 is never reached.
Reported as **"no headroom claimed"**.

The unmeasured levers of the effective menu (A1.5: 1 pointer index density, 2 tail placement — 1 vs 2
trailing blocks only, 3 scaffold order / anchor marker, 4 delta batching, 5 retrieval-hint wording, 6
serving-side levers proven in `R2-OPT-LOOP` only) are **unused, not promising**. Nothing in this round
measures that any of them would act on both models, and being unused is not a measured basis.

## 5. Reopening rule (§4, `FINAL-GOAL` reopening)

**No further SYS-OPT round may run on this lineage without a `DECISIONS` entry** that names (a) one lever
from the §8 menu and (b) a measured row-level basis, on the failing model, that the lever would act on. The
entry must come **before** the next round's changes are chosen. A better-looking arm or a preference for a
version does not qualify (§10's withdrawal clause).

## 6. What this ceiling does not say

- **It does not say the pointer layout is worthless.** It says the *tail-edit span-format change* (V1) did
  not improve cost on either model. What justifies the pointer layout is the fan-out / branch-sharing
  result, not a per-turn saving (A1.1, A1.3); that justification is unchanged and lives in V0's release.
- **It does not produce a V_n / C0 claim.** §1.3 requires C0 per model per round; the round harness never
  carried C0 (A1.4), so the release claim this lineage can make is **V0's own numbers against V0's
  pinned rows** — there is no C0 comparison on SYS-OPT rows.
- **It does not license a quality claim.** The quality guard's before/after is read on a frozen set whose P0
  form is unanswerable by construction, and the absolute rates are 100 % / 95 % mismatched. The guard is a
  regression detector that fired nowhere; it is not a quality measurement of the release.
- **It does not withdraw anything.** §10's amendment path requires an independent verifier to prove a
  measurement error in the scoring pipeline. None has. The decision structure and thresholds stand.

## 7. Round ledger

| round | version | change | per-model result | status | adopted? | record |
|---|---|---|---|---|---|---|
| 1 | **V1** | lever 1: `pointer_block.quote_tokens 0 → 40` (A2.2) | MoE cost +130.1, dense cost +228.8; CIs exclude zero, means positive | **`no_signal`** → **CEILING** | **no** | [`SYS-OPT-R1B-RESULTS.md`](SYS-OPT-R1B-RESULTS.md) |

Versions V2 and V3 **do not exist**. They were not skipped, failed or deferred — the search stopped before
them because §4 declares the ceiling at round 1.

## 8. Carried gaps (recorded, not corrected)

1. **C0 not carried** (A1.4) — §1.3's `V_n / C0` headline is unavailable on SYS-OPT rows.
2. **Frozen quality set has an unanswerable form** (A2.3) — the P0 form cannot state a `sha8`; the set stays
   frozen for this lineage.
3. **Round 1 exceeded its stated bounds** — **565** live requests against a **500** bound, **39** tool calls
   against **30** ([`SYS-OPT-R1B.json`](../../orchestration/handoffs/SYS-OPT-R1B.json)). The card's own
   mandated census (426 rows) plus the quality guard (80 probes) already totalled 506.
4. **Tool-call count differs between documents** — the round's results doc says 33, its handoff says 39. The
   handoff is the unit's own report; 39 is carried here. The discrepancy is recorded, not resolved.

## 9. Release

The paired release is **V0's**: one prompt artefact, identical bytes on both models, with a per-model serving
config — **MoE = O1** (SGLang `:8012`, `f2efaaac…`) and **dense = O4** (vLLM `:8014`, `163a5db6…`). Published
as [`RELEASE-v1.json`](RELEASE-v1.json); see §9's pairing rule — V0 has **no SYS-OPT measurement of its own**
and is cited with its R2-PROMPT provenance and row digests throughout.

**Closing line — SYS-OPT CLOSED AT CEILING, ROUND 1. Best version V0. No adoption, no headroom claimed, no
round 2 without a `DECISIONS` entry.**
