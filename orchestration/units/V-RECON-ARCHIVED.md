# V-RECON-ARCHIVED — verifier card

Objective: independently re-run the RECON-ARCHIVED fix and its control case. Not the author
(`orchestration/units/RECON-ARCHIVED.md`); verdict only, no fix.

Hard bound: read-only over `~/.dsh`; no card created/moved/settled; ≤45 tool calls; kill condition = if the
red→green→control triple cannot be reproduced against the real ledger in 3 attempts, STOP and report
`partial`. Card permission: `workspace-write` (this handoff is a write).

Write paths: `orchestration/handoffs/V-RECON-ARCHIVED.json`, `orchestration/units/V-RECON-ARCHIVED.md`,
`orchestration/VERDICTS.md`, `state/logs/V-RECON-ARCHIVED-redgreen.txt`, `.scratch/v-recon-archived/`.

Automated session: no human present; no question asked. Missing values were resolved by the conservative
default in the never-ask rule (assumptions recorded in the handoff).

## What was checked

| Claim (author) | Re-run | Verdict |
|---|---|---|
| red: pre-fix `exit=1`, offenders=2, 4 offender lines | `exit=1`, offenders=2 lagging=2, 4 lines (raw + normalized keys) | reproduced |
| green: fixed `exit=0`, archived=2 | `exit=0`, offenders=0 lagging=0 archived=2, no OFFENDERS block | reproduced |
| control: +1 synthetic live lag → `exit=1`, 1 offender | `exit=1`, offenders=1, exactly 1 line, ARCHIVED block intact | reproduced |
| `tests/test_session_recon_archived.py`: 10 pass | 10 passed | reproduced |
| 3 tests fail against the pre-fix body | 3 failed, 7 passed (same three) | reproduced |
| handoff guard 13 passed | 13 passed | reproduced |

Beyond the author's evidence: every archived card in ledger revision 1052 was enumerated (16 archived, 10
archived+unsettled) to check no archived card escapes the exemption — the 8 scheduled ones are dropped by the
pre-existing schedule branch, the 2 non-scheduled ones are exactly the two reported. Adversarial edges
(`backlog`+archived, `running`+archived, `archivedAt=0`, `archivedAt=null`) behave conservatively.

## Verdict

**pass.** The fix does what it claims, the control proves the settled-lag check is still live, and no
regression escaped the author's evidence. Two recorded gaps that are *not* defects of this fix: an archived
card carrying a `schedule` is invisible in `archivedWithSettledExecution` (reporting only, 8 of 10 today), and
`archivedAt = 0/null` would be graded live (untriggered — archive writes epoch ms).
