# UNIT ENGINE-RECORD — consolidate the pointer-engine evidence into one reconciled record

**Purpose.** Reporting unit only: fold MISS-LAW, HIT-LEDGER, PTR-ENGINE-P0/P0.1/R1/R2, QUALITY-ARM,
V-QUALITY-ARM, BILL-AUDIT and the avalanche handoffs into one reconciled record plus an adoption pack. Not
the author of any number; no live measurement; no request to `:8012/:8014/:8016/:8017/:8020`; no container,
no GX10, no `.occamy.lock`, no `git` against `/home/zer0null/Duval`.

**Write paths (only these).** `experiments/ptr-engine/RECORD.md`,
`experiments/ptr-engine/ADOPTION.md`, `orchestration/handoffs/ENGINE-RECORD.json`,
`orchestration/units/ENGINE-RECORD.md`.

**Bound.** 30 tool calls; a number untraceable in 3 attempts becomes UNVERIFIED and is left out. Used: 26.

**Deliverables.** RECORD.md ≤180 lines (engine/ratio → law → hit ledger → quality arm → CONTRADICTIONS);
every table row carries a `source` column (`path:field` / `handoff.key`). ADOPTION.md ≤60 lines, fully
derivable from RECORD.md.

**Result.** `experiments/ptr-engine/RECORD.md` **138 lines**, 44 data rows, 94 distinct carried figures in
non-source cells, 0 unsourced numbers, 0 UNVERIFIED. `experiments/ptr-engine/ADOPTION.md` **39 lines** — three
decisions, measured preconditions (including mamba cache: **not measured**), measured failure modes, do-not list.

**Verified by this session, not inherited.** `wc -l rows.jsonl` = 774 and its composition (387 `measure` +
383 `prime` + 4 `warm1/warm2/cold1/cold2`); ENGINE-R2 = 171 passed / 63 in `test_quantise.py`, offline;
V-ENGINE-P0 checks[0]/[2]/[3]/[4]/[6]/[7] (95 passed, narrow one-way guard, sha256 `e08700c9…`, r =
67.1141, seven codes, warmpool refusal); `ledger.py` anchors (ServerProfile:323, SGLANG_PROFILE:362,
VLLM_PROFILE:371, law_L:414, HitEntry:420, reconcile:749, summarise:797); the `Bprobe-400` rows read directly
(sglang 467/448/19; vllm 467/0/467 = P1+L); `CLAIMS.md` grep → no hit, C34's 51.67× at `:135` is unrelated.
A prior run at 02:27 had written RECORD/ADOPTION/card but never a handoff; this session created the stub,
re-derived the numbers, and corrected five defects (checks[2] citation, profile line anchors, R2 labelled
offline, the CLAIMS grep sentence, C8 row composition) plus the missing mamba-cache precondition.

**Contradictions recorded, not tidied away.** C1 SGLang avalanche magnitude (whole prefix vs one block;
believed BILL-AUDIT, ENGINE-R1's 397-token cell overstated 5.2×) · C2 vLLM avalanche (whole prefix, believed
MISS-LAW-2; engine-specific, not a conflict with C1; ledger flag stale) · C3 QUALITY-ARM's billed column
57.6× low (root cause `quality/runner.py:467`, believed BILL-AUDIT) · C4 `BILL-REPAIR` never ran (OPEN) · C5
ENGINE-R2's padding is an uncalibrated offline model (OPEN) · C6 "full suite" = 95/100/108/153/171 on
divergent branches · C7 the law applied outside `LAW.md` §8's scope · C8 `law_fit.json` covers 753 of 774
rows, unspecified which (OPEN) · C9 378 harvested avalanche rows abandoned, never consumed as a result (OPEN) ·
C10 QUALITY-ARM's telescoping claim refuted by V-QUALITY-ARM (+17,193 residual on C rep2; "0 avalanches"
contradicted by its own `rep.per_turn`), not resolved in the author's favour (OPEN). `papers/context-cache/
CLAIMS.md` checked: no engine/law/ledger claim to correct; not edited.

**Handoff.** `orchestration/handoffs/ENGINE-RECORD.json` — `status: done`.
