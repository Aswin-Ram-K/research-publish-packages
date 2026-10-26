# REPAIR-QP-B — record the V-QUALITY-ARM verdict

**Purpose (one):** append exactly one row to `orchestration/VERDICTS.md` recording unit `V-QUALITY-ARM`'s
verifier verdict. Nothing else. No repair, no re-verification, no live requests.

**Bound:** 8 tool calls, autonomous (no `ask_user_question`), zero live requests.

**Write paths:** `orchestration/VERDICTS.md`, `orchestration/handoffs/REPAIR-QP-B.json`,
`orchestration/units/REPAIR-QP-B.md`.

**Method:**
1. Wrote the `status:"partial"` stub handoff first (contract-before-work).
2. Read the last 40 lines plus the heading list and the last `- **V-` bullet rows to match style.
   Finding: the two most recent verdicts (`V-PAPER-CLOSE`, and the `PAPER-FINAL-V2D` gate call before it)
   land as **trailing single-line bullets** `- **<UNIT> — <VERDICT> (verifier, <date>).** ...` at end of
   file, not as `##`-headed sections like the older `V-R2-VLLM-RERUN`/`V-FINAL3` entries.
3. Appended one newline-terminated bullet at EOF; the file already ended with `\n`, so no blank-line
   separator was introduced and no existing byte changed.

**Result:** 4009 → 4010 lines (+1). sha256 before `4c68aa0012f853d843893f03cf1f10f1b9e5dd6eacb361a32430ad6570383b53`,
after `d01359d2d127153b53b02d377af311e9ef03e98b0acac604b54be708e6a1cbde`. The previously-last row
(`V-PAPER-CLOSE`) is byte-identical at line 4009.

**Content of the row:** CONFIRMED (115-row reconciliation; discrimination control A 3/3 B 0/3 C 3/3 D 0/3;
index 458 B + full sha256; `k01`-only fact; PREREG match) · REFUTED (billing identity residuals per arm;
`RESULTS.md:176` 34,201 vs 32,401; `:150` "0 avalanches" vs `per_turn`; `:174` self-contradicting sentence)
· ROOT CAUSE (`runner.py:585-596` read, never persisted; `runner.py:688` recomputation) · GUARD (corpus.py
gate red→green in a /tmp copy, restore byte-identical) · CONTAINMENT (no attributable write outside
`quality/**`; five undisclosed artefacts 01:07–01:10 after the 00:39 handoff) · CONSEQUENCE (moat survives
on discrimination; no claim may rest on the billing identity until a live re-run persists per-turn
`cached_tokens`).
