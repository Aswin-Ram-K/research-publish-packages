# V6-RESULT — PROBE-CP3-V6 (record completed offline by V6-COMPLETE)

**Verdict.** The fetch channel was un-starved: at T46 the arm had **4 of 24 rounds left** and its pinned-
range read was served from the prompt for **zero rounds** — yet the checkpoint failed because the ^ANSWER:
line dropped a required anchor. Accuracy is **1/3, the v4 tools-OFF control's 1/3**. Channel capacity is no
longer the constraint; the grader's anchor set is.

## Six numbers (file + key)
- **rows/requests**: 72 = 48 turn + 24 tool-followup; requests_spent 72 — rows jsonl `kind` census; grade `row_count: 72`.
- **rounds left at T46**: fetch_rounds_used 20 of 24 → **4**; cap_per_turn 3 — rows jsonl `turn=46.fetch_rounds_used`.
- **T46 pinned serve**: served_from=prompt, base=prompt, pinned_lines=36-110, lines_returned=6, billed=false, executed=false — rows jsonl `turn=46.tool_calls[0]`.
- **tool_calls census**: prompt 37; executed 79; turn_call_cap 236; per_turn_round_cap 7; range_out_of_bounds 2; path_not_found 10; followup_suppressed 31; 371 entries — rows jsonl per-entry keys.
- **truncated/tokens/markers**: 0; 356,740 prompt / 12,615 completion; marker_lines 13/72 — rows jsonl + grade `marker_census`.
- **grade**: 1/3 — cp.0.t12 PASS · cp.1.t24 marker_missing · cp.2.t46 refused_while_knowable ("marker dropped anchors; missing raising") · repair.t30 repair_not_acknowledged · acc.n2b PASS · acc.n3b–n3e unverifiable — grade json `arms.pointer-stable.checks`.

**Correction (rows win)**: the driver's census (prompt 32 / executed 50 / turn_call_cap 220 / oob 1 /
path_not_found 6) does not reproduce; recomputed 37 / 79 / 236 / 2 / 10. Only per_turn_round_cap 7 agrees.

## V6 vs V5
V5: fetch_budget_exhausted at T46, 0 rounds left, no <tool_result>, no follow-up row, 1/3, 72 requests,
1 truncated turn. V6: no refusal, 4 rounds left, prompt-served read billed=false, 1/3, 72 requests, 0
truncated turns. Half the prediction held (rounds_left>0); the other half was falsified, for a new reason.

## V6 vs v4 tools-OFF control
`rows-longrun-v4-2026-10-26.grade-v3.json` → `arms.pointer-stable.checkpoint_accuracy` 1/3 (that batch's
68-turn tools arm also 1/3). V6 tools-ON is also 1/3: indistinguishable on quality. The channel was never
the binding constraint here.

## Conclusion
Giving the arm back its rounds removed the T46 starvation but not the failure — it retrieved and restated
the fact, then dropped the "before re-raising" anchor — so the constraint is answer/marker discipline
against the grader's anchors, not fetch capacity.

## test2 edit: NEUTRAL-BUT-UNAUTHORISED
`tests/test_tool_channel2.py`, mtime 08:18:22, sha256 `021a7be4…`, **untracked** (`git ls-files
--error-unmatch` → exit 1; no log, no diff) → classified by inspection. No assertion deleted or loosened;
the one change is the range fed to (d):
- `:54-55` `UNPINNED_TURN` → resolve.py L1-30 (outside the pinned L36-110); rationale in-file `:49-53`.
- Guards intact: `:261` sent==1 · `:264` one T2 row · `:265` fetch_rounds_used==24 · `:267` errs==["fetch_budget_exhausted"] · `:268` no fetch_followup.

Neutral, not weakening: a pinned range is now served at zero rounds (test_tool_channel3 case (a) GREEN),
so a pinned assertion would test obsolete behaviour; the guard still fails on a broken channel.
Unauthorised: the file is not in V6's declared write paths.

## Acceptance, re-run offline (0 requests)
1. test_tool_channel2.py → exit 0, PASS 5/5, 0 real sends.
2. test_tool_channel3.py → exit 0, PASS 5 checks (2 green held, 2 red failed as required).
3. run_longrun.py --dry-run --tools read_file → exit 0, would_send_total=48.
4. grade_v3.py → /tmp/v6-regrade.json exit 0; dict-identical to the recorded grade minus `generated_at` →
**grade reproducible**. No non-reproducible-grade finding.
