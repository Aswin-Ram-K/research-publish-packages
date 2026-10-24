# CX-V2 — independent verifier, Occamy context-cache batch

**Status:** done (fail — one claim refuted, two contradictions resolved) · **Bound:** 40 tool calls, 30 used
**Write paths:** `orchestration/handoffs/CX-V2.json`, `orchestration/units/CX-V2.md`,
`experiments/context-cache/cells/CX-V2/**` · **Nothing else touched**: no unit rows, no unit scripts,
no `src/`, no live request, no lock, no git, no target repo.

## What it did

Re-derived every headline number of U9, U4b, U5, U10 and U2 from the units' own row files with
independent code (`repro.py`), replayed U5's and U4's prompts offline from their corpora
(`u5_recon.py`, `u4_recon.py`), re-derived U4's tables (`u4_numbers.py`), and ran a red→green on the
null→0 cache coercion (`guard_tax.py` + `null_coerce.py`).

```
.venv/bin/python experiments/context-cache/cells/CX-V2/repro.py
.venv/bin/python experiments/context-cache/cells/CX-V2/u4_numbers.py
.venv/bin/python experiments/context-cache/cells/CX-V2/u4_recon.py
.venv/bin/python experiments/context-cache/cells/CX-V2/u5_recon.py
.venv/bin/python experiments/context-cache/cells/CX-V2/guard_tax.py     # exit 0 green
```

## Per-unit verdict

| unit | verdict | the figure that decided it |
|---|---|---|
| U9 | reproduced | ratios .414/.250/.156/.080/.046/.031; miss L^1.0520 r²=.9934, hit L^.2683, ratio L^−.7837 r²=.9962; slopes .240736 vs .004659 ms/tok — all to the digit, but only when x = measured prompt_tokens |
| U4b | reproduced | B/A 3.3133, C/A 1.000000, 6/7 warm branches at cached=1792, branch 2 = 0 |
| U5 | reproduced | 126/137/134/132 of 190; gold 190/0; POINTER==NAIVE_APPEND 760/760 rebuilt byte-identical |
| U10 | reproduced | 10/10 vs 0/15, Fisher two-sided 3.0593e−07 (= 1/C(25,10), genuinely two-sided); wider pool 35/35 vs 0/15 → 4.44e−13 |
| U2 | figure reproduced, law refuted | 44/44 residual 0 — but under *both* laws, because all 44 lengths have L%64 ≠ 0 |
| U4 | **confounded** | fork and summarise bodies byte-identical 44/44; only the salt differs |

## Contradiction A — `u4_confounded: true`, but not for the stated reason

The brief's mechanism is false: `u4_runlog.json` shows `source_pins_before == source_pins_after ==
4184c932…` for `render.py` with `source_changed_during_batch: []`, and the rewrite's mtime (18:07:16)
precedes U4's live start (18:33:49) by 26 minutes. U4 ran one pinned renderer consistently.

The real confound is in the arm, not the clock. `u4_cell.RENDER = NAIVE_APPEND` for every arm,
`POINTER_FORK` is never imported, and `render._bodies` emits `node.text` only — never `node.kind`.
`budget.compact(FORK)` and `budget.compact(SUMMARISE_IN_PLACE)` emit the same texts in the same
order. Offline replay confirms it turn by turn: body digests identical 44/44 in each of the three
sessions (identical byte counts too); the full prompt differs only because the per-cell salt differs.
So "fork ≡ summarise, median Δ 0, 18/21 zero, p=1.0" is a construction, and its three nonzero deltas
(−64, +64, −64) are 64-grid rounding of a 2–3 token salt offset.

**Must be re-run:** a fork arm with a renderer that actually emits a pointer, the *same* salt in both
arms, and `break_cost` measured against the append residual rather than `L % 64`.

## Contradiction B — both claims stand, but only scoped

Disjoint request shapes, zero overlapping rows. U2's 44 warm rows are byte-identical repeats
(314–1550 tokens); U4's 372 warm rows are appends (934–12,393 tokens, `rep=1`, no identical repeat
anywhere in 438 rows). Prompt size and the hybrid model are the same on both, so the regime
difference is the access pattern, not scale.

Anchoring the law at the previous prompt does not rescue it either: `cached == 64*floor((L_prev−1)/64)`
holds on only 18/39 control rows and 62/216 pre-event rows (none/u4-s1 turn 3: L=2642, prev 1803 →
law 1792, measured 896). So there is a genuine lag beyond the anchor, but U4's mamba-checkpoint
attribution is untested — no probe varies the checkpoint interval or cache size.

**Neither sentence may print unqualified.** U4's "the 64-grid does not hold on this server" is
refuted as a general statement by U2's 44/44 and by U4's own post-compaction hits on exact grid
values (4352, 6144, 7936). U2's `64*floor(L/64)` is refuted at L%64==0 by U9 (1024→960, 3/3) and
U10 (rep1 0/10, rep2 960/1024).

## Red → green

Guard: the null→0 coercion (72 null-details records: U2 49, U4 23) and the cold-start contract.

* green: `GUARD PASSED: 3/3`, exit 0
* break: null details treated as "fully cached" → exit 1 — `A1 72/72 null-details records derived cached>0`,
  `A2 12/12 U4 cells' first record derived as a cache hit`
* restore (sha256 `d05e7765…`): `GUARD PASSED: 3/3`, exit 0

## Corrections handed back

1. U2's law → `64*floor((L−1)/64)`, repeat-only, with the multiple-of-64 first-repeat miss.
2. U4's residual histogram is 6 buckets short (364 of 372 listed); true range 832–7936, median 1792 —
   not 6976, and not "0.9–2.7k".
3. U9's p=0.0078 is one-sided; two-sided is 0.0156.
4. U5's "fork" arm shares its prompt digest with "summarise" in 190/190 cases — one condition
   sampled twice, not two.
5. `break_cost` (median 1792 per policy) is the same magnitude as the ordinary warm-append residual
   on the same cells, so it is not separable from the ambient penalty.

## Blocker

U4's fork claim cannot be settled offline: no arm in the batch ever rendered a pointer, and
re-measuring it needs live requests, which this unit may not make.
