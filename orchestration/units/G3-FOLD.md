# G3-FOLD — put the measured compaction cost into the paper and close G3

**Status: done.** One claim added (`C62`), one manuscript section added (`§6a`), the abstract,
§1 table, §10 rule 5, §11 limitations, `CLAIMS.md`, `EVIDENCE.md`, `PACKAGE.md`, `READER-MAP.md`,
`RUN.json` and the G3 gap entry updated, and one new red→green guard
(`tests/test_paper_boundary_attribution.py`) written and proven.

## Why this unit exists

G3-LIMIT-V2 measured the thing the paper had never measured — compaction forced by a context
limit rather than scheduled at a turn — and reported it only in a handoff whose
`next_unit_hint` said to publish it. The paper's §6 comparison was bounded by its own rows
(cell G3: `scheduled_compaction` false on 888/888), and `GAPS.md` G3 still carried the
pre-measurement verdict `STATUS: NOT SETTLED`. A measured result that lives only in a handoff
is a result the package cannot defend, so this unit folded it in and closed the gap chain.

## What was decided, and why

- **Counted from rows, not copied from the cell's `analysis.json`.** The cell's analyser
  reports an all-turn delta (e.g. +390.2 tokens/turn for 32k S), which mixes the pre-boundary
  turns with the post-boundary ones and therefore answers "what does compaction cost?" with a
  number diluted by turns on which the arms were identical by construction. `C62` splits each
  arm at its own first compaction: the **control segment** (turns before it, where a nonzero
  delta would mean the cell failed its own pre-registration) and the **post-boundary segment**
  (turns after it, the result). The pre-segment deltas (-11.8 to +51.0, 0/12 CIs excluding
  zero) are what licenses reading the post-segment deltas (+134.6 to +747.2, 11/12 CIs
  excluding zero) as compaction cost rather than as arm drift.
- **Matched on the same turn, baseline by renderer.** `B` for `append_note` arms, `B-ptr` for
  pointer arms, restricted to turns both arms have. The 32k `B-ptr` baseline carries a phase
  artefact (noted in the G3-LIMIT-V2 handoff); matching by renderer keeps it out of the
  append-note contrast and matching turn-for-turn keeps the baseline's own phase drift out of
  both.
- **The mechanism sentence is the rows' own.** An earlier draft said the compacting arms "rest
  shorter, so a later note lands on a longer prompt drive". The last-turn prompts
  (13,325 / 13,542 at 32k and 23,632 / 23,762 at 64k against 9,896 / 22,063) refute that: the
  arms carry *more* prompt at the end, not less. The corrected sentence is what the boundary
  row shows directly — `cached_tokens` 0 on the compaction row against 31,552 on the
  baseline's preceding turn — so the cost is a destroyed prefix and a worse hit rate on a
  shorter prompt, not prompt volume.
- **Two limits stated, not smoothed.** The trigger was headroom-based, not an overrun, and the
  post-boundary segment is 27–89 turns on one seed; both are in §6a and in `GAPS.md` G3's
  "what is still not settled". It is also stated plainly that the rewrite policies do not
  separate at 64k (all four append-note intervals overlap), rather than reporting the one
  ordering that looks clean at 32k as a policy finding.
- **C62 is pinned row by row.** The expected value is a tuple per arm (delta, CI, pre-delta,
  compaction turns, boundary cost, baseline drop cost) so a rewrite that keeps the range and
  drops an arm fails `recompute.py C62`. Measured: removing the 32k `F-ptr` row gives
  `FAIL 16/17 values match`.
- **The new guard is anchored on result sentences.** The first attempt checked "does §6a
  contain +134.6" in the whole section, and a revert that rewrote the result sentence stayed
  green at `8 passed` because the per-arm table still carried the figure. The assertions now
  run on the sentence that states the band and on the sentence that states the control.

## Gate (self-check before handoff)

| command | result |
|---|---|
| `.venv/bin/python papers/context-cache/recompute.py C62` | `PASS 17/17 values match` |
| `.venv/bin/python papers/context-cache/recompute.py all` | `59 claims checked, all match` |
| `.venv/bin/python papers/context-cache/verify_package.py` | `PASS — 62 claims, 62 mapped` |
| `pytest tests/test_paper_boundary_attribution.py tests/test_paper_attribution_guard.py -q` | `19 passed` |
| red: drop 32k `F-ptr` from `C62`'s expected rows | `FAIL 16/17`, guard test fails |
| red: G3 status reverted to `NOT SETTLED` | `1 failed, 7 passed` |
| red: §6a band/control sentences reverted | `2 failed, 6 passed` |
| green: restored | `19 passed` |

Offline: no live request was made, the endpoint was not contacted, `/flush_cache` was not
called, and the `.occamy.lock` was not touched.

## Assumptions

- Read "put the measured compaction cost into the paper" as: one new claim with one recompute
  command, one new manuscript section, and the gap's status updated — the package's existing
  conventions — rather than a new paper section that restates §6.
- Read "close G3" as **narrowed, not closed**: the measurement exists and is in the paper, but
  the trigger-headroom, post-boundary-length, separation and second-engine limits are
  genuinely open. Calling the gap closed would assert more than the rows carry.
- The cell's existing `analysis.json` was left untouched (it is another unit's artefact);
  C62 re-derives what it needs from `rows.jsonl` alone, using the same bootstrap recipe
  (10,000 resamples, seed 20251023) so the numbers agree with the cell where they overlap.
