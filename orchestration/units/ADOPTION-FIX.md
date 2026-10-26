# ADOPTION-FIX — repair eight audited items in the adopter guide

**Unit.** `ADOPTION-FIX` · automated session, no human present, offline.
**Objective.** Fix exactly the eight items the independent audit
(`orchestration/handoffs/ADOPTION-AUDIT.json`) left non-CONFIRMED in
`experiments/ptr-engine/ADOPTION.md`: item 20 WRONG, item 17 STALE, items 6/7/10/15/25/27 OVERSTATED.
Nothing else in the page changed.
**Hard bound.** 16 tool calls (used 13), single pass, no re-delegation.
**Write paths.** `experiments/ptr-engine/ADOPTION.md`,
`orchestration/handoffs/ADOPTION-FIX.json`, `orchestration/units/ADOPTION-FIX.md`.

## Procedure

1. Snapshotted the page (39 lines, sha256 `76ea7e054e00425cb8c91a041f8addd8d07160e88e9fa530605cfcef7299569e`).
2. Re-derived the padded cells myself from `experiments/ptr-engine/measure/rows.jsonl` before writing
   item 20 — predicate `row=request ∧ pad_tokens>0 ∧ cached_reported=true`: cell B pad 60, P1 386 →
   `cached 384 / uncached 15`; cell D pad 50, P1 322 → `cached 320 / uncached 15`; 3 reps each.
   Cell C pad 58 (P1 384, residue 0) reports `cached_tokens: null` — it does **not** settle residue 0.
3. Checked each cited source before relying on it: `RECORD.md:114` (C1 UNDECIDABLE),
   `RECORD.md:145` (C2 8.5× warm-vs-warm), `RECORD.md:153` (residue-0 decided at 397/320, cell A, unpadded),
   `measure/run_cells.py:109` (`/chat/completions`), `papers/context-cache/EVIDENCE.md:16`
   (`max_mamba_cache_size: 64`), `experiments/miss-law/avalanche/HARVEST.md:30` (270 = 141 + 129),
   `experiments/miss-law/LAW.md:222-224` (5.2× withdrawn, do not cite).
4. Applied seven exact-string replacements with `assert count==1` per anchor, then appended one
   corrections line naming the audit.

## Verification

- before sha256 `76ea7e05…9569e`, 39 lines; after sha256 `0580fa8f87fabe2b41f628ad9ec715f821c6ab5bee9cbd7ee871868e73f28b81`, 41 lines.
- `diff` of a byte-exact reconstruction of the before-file (its sha256 reproduces `76ea7e05…`) against the
  after-file: 3 hunks, 3 lines removed, 8 added, 16 changed lines total. The page was not tracked by git,
  so the diff base is the pre-edit read, hash-verified rather than assumed.
- `grep -c 'no measured padded cycle'` = 0; `grep -c '5.2x'` = 0 (the surviving mention is `5.2×` inside a
  sentence that marks it WITHDRAWN); `'nothing was measured'` = 0; `'LAW.md:§1'` = 0; `'never consumed by a unit'` = 0.

## Assumptions (recorded, not escalated)

- No human present: the item-15 wording the card requested ("C1 calls the magnitude UNDECIDABLE") was
  re-checked against `RECORD.md`, which had since added `:153` (C1 DECIDED for residue 0 on an unpadded
  384-token prefix). Both facts are stated in the page rather than the card's single reading, so the
  adopter is not told a decided point is open nor an open one decided.
- `/tmp` does not persist between bash calls in this session, so the `cp` snapshot vanished; the diff base
  was rebuilt from the pre-edit read and proved byte-identical by sha256.
