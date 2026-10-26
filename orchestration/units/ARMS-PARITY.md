# ARMS-PARITY — **WITHDRAWN** (2026-10-24, by ARMS-PARITY-WITHDRAW)

> **Status: WITHDRAWN. Do not act on this card's verdict or its prescription.**
> The finding below that PROMPT-O1's arm-R `cached_tokens` is a "bookkeeping artifact" is **falsified**: a
> fresh-salt re-measurement of the same cell (`GROUND-TRUTH-PROMPT`) gives **589.2029** uncached/turn vs the
> restored 583.14 (+1.0 %) and the repaired 391.48 (+50.5 %); `CACHED-AUDIT` showed the duplicate-value
> signature is not discriminating (37/69 on that fresh ground truth); and the only impossible corpus is the
> repair itself (40 of 71 cached values off the 64-token grid).
> **The prescription was inverted.** The standing figure is **A − R = −53.8451 [−96.6197, −10.4085]**
> (*A cheaper*), and it is **not** withdrawn. `+133.3` / `+138.5` are **not publishable**.
> Record: `state/logs/arms-parity-withdraw.json` · guard: `tools/audit/arms_parity_status.py`.
> What survives is the renderer parity observation (same renderer, same two arms, salt-only difference).

## (original card, kept as history)

**Objective.** Resolve the sign contradiction between `cells/PROMPT-O1` (A-R = -53.8) and
`cells/R2-P1-O1` (A-R = +133.3) on the same O1 setup, offline, zero live requests.

**Finding.** Neither R is mis-rendered. Both cells import the same renderer
(`experiments/context-cache/cells/VLLM-CELL/vllm_cell.py`) and their `render("R", turn)` /
`arm_messages` bodies are byte-identical apart from a salt digest, so these are the **same two arms**.
`prompt_tokens` agree to within 1 token at every turn, and both produce the full-state shape 71/71.
`A` produces pointer+delta in both (growth 51.8 tok/turn vs R's 339).
The split is in `cached_tokens`: 40 of PROMPT-O1's 71 R rows carry a value that duplicates a neighbour's,
inflating `uncached_tokens` by +321/+385. R2-P1-O1's R rows show the correct smooth sawtooth.

**Verdict.** PROMPT-O1's `-53.8` is a `cached_tokens` bookkeeping artifact and must be withdrawn.
The publishable number is **A-R = +133.3 [123.7, 143.0] (A costlier, pointer layout helps)**.

**Caveat recorded.** R2-P1-O1 reports `cached_tokens="unavailable"` on 2 rows, so its R mean is over 69
turns; PROMPT-O1 has 71 numeric rows. The corrected PROMPT-O1 R mean (390.80) matches R2's 390.80 exactly.

**Bound.** 15 tool calls. **Writes.** `state/logs/arms-parity.json`, this file, the handoff.
**Live requests: 0.**
