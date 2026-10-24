# UPAPER1a — extract and independently verify every quantitative claim for paper candidate A3

**Status:** done (within bound; 31 of 45 tool calls used).
**Write paths:** `papers/encoder-crossover-190/**`, `orchestration/units/UPAPER1a.md`,
`orchestration/handoffs/UPAPER1a.json` — nothing else touched.
**Target:** `/home/zer0null/Duval`, STRICTLY READ-ONLY. HEAD before = after =
`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`. `status --porcelain` before = after = 4 untracked paths
(`.ci-trunk.txt`, `.relay/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `docs/migration/`),
all pre-existing and unrelated to this unit; **no change attributable to UPAPER1a**.

## Purpose (one)

Extract and verify every quantitative claim for paper candidate **A3** and write them down as a verified
table. NOT writing the paper.

## Sources read

1. `strategy/PAPER_CANDIDATES.md` §A3 (lines 247–285) — the specification.
2. `docs/research/experiments/EXP#12-typed-channel-comparison.md` §10–§11 + §11.2 head.
3. `docs/research/EXP#12-evidence/` — `analysis.json` (the aggregator), the five `eval-*.json` arms,
   `DEFECT-EVIDENCE.json`, `lint-report.json`, `REPORT.md`, and `NOTES-defects.md`/`METHOD-README.md` for
   citation search. Machine-readable JSON preferred over prose throughout.
4. `docs/research/experiments/LEARNINGS.md` M12 (+ M11 errata).
5. `experiments/second-labeller-190/` (workspace copy) — `RUN.json`, `metrics.json`, `EVIDENCE.md`.
6. `docs/DECIDER_STACK_DECISION.md` §11.2/§11.6 — the only place the thesis's literature claim is sourced.

## Work done

- Verified all five arm accuracies, the chance floor, the majority-class control, both decider baselines,
  the paired McNemar (b/c/ψ/Δ/p), both MDEs, the SetFit correction chain, the F4 lint figures, H4, and the
  second-labeller reliability figures — each against the machine-readable source, then cross-checked the
  prose tables in `REPORT.md` and `EXP#12` §10.
- Independently **derived**: the chance floor from `options_per_case`; Δ from b=27, c=90, n=190; ψ from
  117/190; harm/MDE = 2.079×; the McNemar row identity (39+27+90+34 = 190).
- Confirmed the U+2212 search trap and located both the typographic-minus and ASCII forms in different files.
- Found and recorded one `DISAGREES` row, and answered the latency question (`no`).

## Deliverables

| file | contents |
|---|---|
| `papers/encoder-crossover-190/CLAIMS.md` | 76 claim rows — 72 `yes`, 3 `derived`, 1 `DISAGREES`, 1 `UNVERIFIED` |
| `papers/encoder-crossover-190/EVIDENCE_NOTES.md` | copy-pasteable command + verbatim output per number; `REPORT.md` table row per arm |
| `papers/encoder-crossover-190/GAPS.md` | the 4 named gaps with status + 6 discovered gaps |
| `papers/encoder-crossover-190/REFS.md` | 4 sourced references, 4 `UNSOURCED`, 1 uncited load-bearing claim |

## Headline findings for the writer

1. **Every number in §A3 checks out against the evidence tree.** No numeric disagreement.
2. **One `DISAGREES`:** "every correction moved the affected arm DOWN" is false as a universal —
   `modernbert-base` moved **up** 0.342105 → 0.347368 when the order-probe bug was fixed. True for SetFit only.
3. **Latency is NOT supportable (`no`)** — different stacks, different units of work, unstable 2× spread,
   and F6's threshold is a pre-registered constant, not a co-measurement. Writer must re-measure or drop it.
4. **The 0.6684 baseline cannot be re-scored** (no per-case rows; `REPORT.md:189`). The 0.6789 can, exactly.
   A human must declare the primary baseline; this unit did not.
5. **The thesis's literature claim has no citation inside the EXP#12 corpus** — it is asserted, and sourced
   only in `DECIDER_STACK_DECISION.md §11.6` + commit `ad301ae`, with GLiNER/GLiClass left `UNSOURCED`.

## Bound / stop condition

Max 45 tool calls. Stopped at 31. No blockers.
