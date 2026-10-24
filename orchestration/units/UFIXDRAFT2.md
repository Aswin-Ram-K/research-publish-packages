# UFIXDRAFT2 — repair the six defects the independent verifier found in DRAFT2

- **Workspace:** `/home/zer0null/reserach extarctor` (write only declared paths). No `git`, no network, `/home/zer0null/Duval` read-only.
- **Hard bound:** 20 tool calls.
- **Purpose:** fix *exactly* the six findings in `strategy/VERIFICATION_REPORT_DRAFT2.md` (checks 1–11 otherwise CONTROL: the headline arithmetic reproduces and must not change).
- **Must not change:** V0 476/1,140 = 41.7544 %, per-variant figures, 244/244 controls, pooled 245/760 = 32.2368 %, stability 60/190 = 31.5789 %, claims numbering C01–C62, gaps G-01–G-09, document structure.
- **Write paths:** `papers/replay-record-not-decision/**`, `orchestration/units/UFIXDRAFT2.md`, `orchestration/handoffs/UFIXDRAFT2.json`, `scratch/ufixdraft2/**`.

## Findings to repair (from the verifier report)
1. `conf` claimed identical on 380/380 in MANUSCRIPT.md:216, :227-229 and CLAIMS.md C54 — L1 has **no `conf` key** (8 keys: correct, error, id, kind, model, ms, p_chosen, picked_index). Only `p_chosen` identical 380/380; `ms` differs 380/380.
2. MANUSCRIPT.md:183 "69.4 %"; measured 130/190 = 68.4211 %. CLAIMS C42 records 68.4 %, so they disagree.
3. CLAIMS.md:147 "explicit file/field source: all 62" — 12 rows are arithmetic/derived (C05, C19, C20, C21, C31, C37, C42, C47, C58–C61).
4. MANUSCRIPT.md:88 "202/190 on the second record file" — whole-file L1 sum is 404/380; 202/190 is the per-model line.
5. AVAILABILITY.md:65 claims a `decision` key — no such key in either file (decision axis is `picked_index`).
6. CLAIMS.md:8 discloses `/home/zer0null/reserach extarctor` (username). Replace with relative root.

## Method
Edit with exact before-strings, assert each occurs exactly once before writing, re-derive any replacement figure from the two raw `.jsonl` records, then re-scan the four paper files for consistency (percentages agree, no nonexistent fields, no `/home/` or `zer0null`).
