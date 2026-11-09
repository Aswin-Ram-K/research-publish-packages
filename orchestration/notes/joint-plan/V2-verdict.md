# V2 Independent Verification Verdict

**Unit:** V2-VERIFY · **Date:** 2026-11-07 · **Target:** `experiments/ptr-engine/research-seed-concepts/JOINT-SERVING-CONTEXT-PLAN.md` · **Overall:** `partial`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | L14 formula × reps = `2,520`; table and JSON agree; bounds consistent | **FAIL** | JSON L14: `840*3 (D arm only)`, requests `2520`, bounds `2520/2520` (consistent). Markdown table has **two** L14 rows: line 198 (`840 × 3`, requests `2,520`) and line 206 (`1 × 7,560 (D arm only: 840×3 = 2,520)`, requests `2,520`). The line-206 formula evaluates to `7,560`, not `2,520`, and the table/JSON ID sets differ (table lacks `L6`, which JSON has). |
| 2 | Priced sum recomputed from `status == priced` | PASS (with note) | Recomputed JSON sum: `0 + 7,560 + 1,260 + 225 + 378 + 151.2 + 2,520 + 696 = 12,790.2`. This matches the document's stated sum `12,790.2`. Pre-relabel figure `13,020.2` is correctly retained as historical context only. L1–L3 are `unpriced-unavailable` and do not contribute. Duplicate L14 row means a naive double count would yield `15,310.2`; the document's stated sum uses one L14. |
| 3 | L1–L3 status | PASS | Lines 193–195: all `unpriced-unavailable`; reasons name the historical SGLang stack as unlaunchable today (no SGLang/vLLM process, containers absent). Candidate-only framing retained (`candidate=true` in JSON). |
| 4 | VRAM figures | PASS | Total `17,095,983,104`, used `10,965,823,488`, free `6,130,159,616 B ≈ 5.71 GiB`; `7,674,114,048 B` appears only as an upper bound conditional on releasing PID 9738. No stale `6.13 GiB`. |
| 5 | Global arithmetic regression | **FAIL** (one row) | `420 = 6×10 + 6×30 + 3×60` (line 178), `3 × (4×420 + 2×420) = 7,560` (line 182), `4 × 7,560 = 30,240` (line 184/199), and `3 × 420 = 1,260` (line 185/197) all recompute. Every JSON row's formula vs count agrees except the duplicate markdown L14 row at line 206 (`1 × 7,560` vs requests `2,520`). L10 fractional `151.2` is consistent with `0.02 × 7,560`. |
| 6 | Stale-token sweep | PASS (with one hit) | No hits for `12,820`, `1×7,560` (no spaces), or `6.13 GiB`. The spaced variant `1 × 7,560` appears at line 206 (stale formula, see defect 1). Legitimate historical references to `13,020.2` remain at lines 242 and 299. |
| 7 | No collateral damage | PASS | All ten required sections present (§1–§10). §7.4 states the sum is a lower bound over priced lines plus named unpriced-unavailable and unpriced-unbounded lines. Every unpriced line carries a reason. §9.1 retains the illustrative row schema with all three dimensions, per-run/per-task identifiers, a quality outcome, and null-capable cache fields; §9.2 retains invalid/missing rows with exclusion reasons. |
| 8 | Red→green guard | PASS | Copied the document to `/tmp/JOINT-PLAN-PERTURBED.md`, changed L14 requests from `2,520` to `2,100`. Independent check recomputed the priced sum as `12,370.2` vs expected `12,790.2` and reported `L14 requests=2100, expected 2520`; exit code 1. Perturbed copy removed; original left unchanged. |

## Defects (exact locations and corrected values)

1. **Duplicate/stale L14 row in the markdown table.** Line 198 is the corrected row (`840 × 3`, requests `2,520`). Line 206 still contains the pre-fix formula `1 × 7,560 (D arm only: 840×3 = 2,520)` with requests `2,520`; the formula evaluates to `7,560`, not `2,520`. Corrected row: remove line 206 or replace its formula with `840 × 3` (requests `2,520`, bounds `2,520/2,520`).
2. **Table/JSON ID parity.** The markdown table omits `L6` (present in the fenced JSON at line 223, `1*7560`, `unpriced-unavailable`) and instead has two `L14` rows. Corrected table should have exactly one row per JSON id `L0`–`L19`.
3. **No other arithmetic defect found.** L1–L3 remain correctly excluded from the priced sum; their candidate-only status is intact.

## Red→green guard detail

- Perturbed file: `/tmp/JOINT-PLAN-PERTURBED.md`
- Change: L14 `requests` `2,520` → `2,100`
- Recomputed priced sum: `12,370.2` vs expected `12,790.2` (delta `420.0`)
- Detected mismatch: `L14 requests=2100, expected 2520`
- Original restored: perturbed copy removed; `/tmp/verify_joint_plan.py` remains as the check.

## Conclusion

`partial`: checks 2, 3, 4, 6, 7, 8 pass; checks 1 and 5 fail on the duplicate/stale L14 row (line 206) and the resulting table/JSON ID mismatch. No precise total over unknowns and no historical-as-current claim were found. The document is not yet `pass`-eligible until the duplicate L14 row is removed and table/JSON parity is restored.
PY
echo written