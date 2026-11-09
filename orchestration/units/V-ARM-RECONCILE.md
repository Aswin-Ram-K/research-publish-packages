# UNIT V-ARM-RECONCILE - reconcile two impossible claims about `pointer-stable`

**Objective.** Adjudicate, from pinned rows only, between board #891 (Claim A: `pointer-stable` starts at 1,867
prompt tokens, reaches 217k, grows 1.21x/turn, r=0.9799, p50 advantage = 98.7 % prefix cache) and
`LATENCY-REPORT.json` G4/RUN-C-V2 (Claim B: 104,468 prompt tokens over 48 turns = 2,176.4/turn).

**Bound:** 30 tool calls. **Offline:** 0 inference requests. **No existing document edited.**

**Verdict:** `CLAIM_A_DEAD__CLAIM_B_SURVIVES`. `prompt_tokens` is per-request (cumulative prefix); the sum over
turn rows IS 104,468. `216,951` is G7 V4-TOOLS `pointer-stable`'s 68-row column total, not a prompt size;
`1,867` matches no row on disk. Grid max prompt 34,279; corpus max 51,216. Cached share 0.871157, not 0.987.

**Deliverables:** `experiments/ptr-engine/measure/ARM-RECONCILE.json`, `ARM-RECONCILE.md`.
