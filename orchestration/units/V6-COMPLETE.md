# V6-COMPLETE — complete the PROBE-CP3-V6 record from on-disk artifacts

**Status:** done · **Bound:** ≤18 tool calls (used 17) · **Live requests:** 0 · **Deliverables:** 3

## Why

`PROBE-CP3-V6` (card `4e559586`, execution `44e83c19`) completed its live cell, then its session was
interrupted by a harness restart at the handoff step (third such restart that day). The card read `failed`
and the record was believed absent. This unit re-derived the record from the artifacts — no live run.

## Disk state as found (vs the card's description)

| Artifact | Card said | Found |
|---|---|---|
| `orchestration/handoffs/PROBE-CP3-V6.json` | 1,175 B pre-run stub | **6,400 B, already in the seven-key unit shape, `status: done`** — a later writer had landed the body but left `pre_run`/`live` unsplit and inherited the driver's unreproduced census |
| `orchestration/units/PROBE-CP3-V6.md` | 4,599 B | **6,379 B** |
| `rows-longrun-v6-tools.jsonl` | 225,648 B / 72 rows | confirmed, 225,648 B / 72 rows |
| `rows-longrun-v6-tools.grade-v3.json` | 3,394 B | confirmed, 3,394 B |

The stub→live rewrite therefore became a **correction** pass: same data, contracted shape, every number
recomputed from the rows.

## What this unit did

1. Recomputed the whole census from the 72 rows. Confirmed rows 72 (48 turn + 24 follow-up),
   `requests_spent = 72`, T46 `fetch_rounds_used = 20` of 24 (rounds left 4), the T46 pinned serve
   (`served_from=prompt`, `base=prompt`, `pinned_lines=36-110`, `lines_returned=6`, `billed=false`),
   truncated 0, tokens 356,740/12,615, `marker_lines` 13/72, grade 1/3 with the three recorded reasons.
   **Corrected** the driver's turn-`tool_calls` census: prompt-served 37 (not 32), executed 79 (not 50),
   `turn_call_cap` 236 (not 220), `range_out_of_bounds` 2 (not 1), `path_not_found` 10 (not 6).
2. Rewrote `orchestration/handoffs/PROBE-CP3-V6.json` in the seven-key unit shape with `evidence.pre_run`
   (stub evidence: test exits, dry-run `would_send_total=48`, `--tools off` identity) and `evidence.live`
   (the numbers plus V6-vs-V5 and V6-vs-tools-OFF baselines). `status: done`.
3. Re-ran all four acceptance commands offline — all exit 0; the regrade **reproduced byte-for-byte**
   (identical with `generated_at` stripped).
4. Audited the unaudited `tests/test_tool_channel2.py` edit (mtime 08:18, sha256 `021a7be46fc5a7a8…`,
   untracked in git). Classification: **neutral-but-unauthorised** — the single change (`:54-55`, a pinned
   range → unpinned `resolve.py L1-30`, rationale at `:49-53`) is forced by V6's per-call serve rule, and
   every guard assertion survives (`:261`, `:264`, `:265`, `:267`, `:268`). No assertion was weakened.

## Result

`experiments/ptr-engine/measure/V6-RESULT.md` — verdict, six numbers with `file`+`key`, both comparisons,
the one-sentence conclusion, and the test2 classification.

**Verdict:** the channel was un-starved (4 rounds left at T46, pinned read served free) and accuracy stayed
at 1/3 — identical to the v4 tools-OFF control. The binding constraint is the grader's anchor set and the
arm's answer discipline, not fetch capacity.

**Blocker:** none.
