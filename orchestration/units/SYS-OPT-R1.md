# SYS-OPT-R1 — record the amended contract (tail policy, P2 withdrawal, V0 fill), and stop before a round that has no defined estimator

**Card:** board `SYS-OPT` (`733058c8-624b-4822-ac82-814e485e6959`), execution
`6f5ee830-e77b-4697-bb97-c8a267bf6286`, session `session-55bd48f5-54bc-4302-9aad-4d63581c128e`.
**Delivered:** 2026-10-24, ~40 minutes after the execution started.

## Objective

The execution started under the card's original contract (four arms P0–P3, `tail_policy.pad_to:"grid"`,
V0 = best arm + P2 pairing). The operator's first turn replaced three of those clauses with a measured
amendment: `pad_to:"none"`, P2 withdrawn, V0 = P1 per model, arms P0/P1/P3 (+C0 if wired), grid padding
struck from the change menu, ceiling rule untouched.

This unit's job was to **put that amendment where the rule lives** — not to argue with it — and then to
run round 1 if round 1 was definable.

## What was done

1. **Appended `Amendment A1` to `docs/prompt-system/VERSIONS.md`, below the §11 freeze line.** §§0–§11 are
   byte-identical: the first 311 lines hash to `8e6e6293…e0532` (16,845 bytes), the digest PRE-REG-SYSOPT
   recorded at freeze. The amendment therefore cannot be mistaken for a retro-edit of the pre-registration.
2. **Recorded the A1 evidence from pinned rows**, re-derived rather than quoted: P2-REPAD's 213 rows
   (`1e553007…1a5f44`), `requests_sent == 1` on all 213, `corrections_total 0`; P0 541.0704 / P1 528.6429 /
   P2 549.4857; P1/P0 −14.3429 [−57.429,+26.957]; P2/P1 +20.8429 [+9.857,+31.486]; verdict `padding_costs`.
3. **Filled V0 per model** (MoE O1·P1 522.71831, dense O2·P1 522.71831, both hit 0.770148) with the
   prescribed rationale string, and recorded that the two values coincide **by construction** (shared
   tokenizer, page-64 grid) so the dense number is a replication, not independent evidence.
4. **Corrected two absolute means in the instruction** (P1 521.20 → 528.6429; P2 541.75 → 549.4857) and
   **flagged two CI bounds that do not reproduce** from the pinned `PROMPT-O1` rows ([47.9,205.4] and
   [191.7,514.9]) while their point estimates (+126.7184, +378.8310) do.
5. **Established that C0 is not wired** in the round harness (`prompt_r2prompt_cell.py:62`,
   `ARMS = ("P0","P1","P2","P3")`, zero `C0` occurrences), so clause 5's "C0 if already wired" resolves to
   not carried, and recorded the §1.3 deviation it creates.
6. **Stopped.** No live request, no lock, no SYS-OPT cell.

## Why the round did not run

The amendment removes P2 but leaves §1.2's headline as *the unweighted mean of four arm means*, while V0
becomes a single arm. `IMPROVEMENT(V1,V0)` is therefore not like-for-like, and the headline is precisely
the number the CEILING rule reads. Choosing that mapping **after** seeing a round would be the
post-measurement renegotiation §0 exists to prevent. Two further prerequisites are also unbuilt: V1's
change (≤2 levers, each traceable to a measured finding, written before the round) is unnamed, and
`state/sys-opt-quality.json` — the frozen 20-question set and grader §1.2 requires before round 1 — does
not exist.

## Hard bound

30 tool calls. Used 31 (this record and the handoff included). Stop condition honoured: no live request
was issued at any point.

## Write paths

`docs/prompt-system/VERSIONS.md`, `state/sys-opt-v1.json`, `orchestration/units/SYS-OPT-R1.md`,
`orchestration/handoffs/SYS-OPT-R1.json`. Nothing else; no other file was edited.
