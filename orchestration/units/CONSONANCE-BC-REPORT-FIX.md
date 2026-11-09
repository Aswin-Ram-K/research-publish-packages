# CONSONANCE-BC-REPORT-FIX

**Status:** done. Surgical repair of `research/next-candidates/consonance-bounded-context-report.md` against `orchestration/handoffs/V-CONSONANCE-BC-REPORT.json` (overall partial, check A10 FAILS, 4 corrections). No evidence value changed; no experiment run; no live request.

## Material defect fixed (A10)
The report presented `E2-CHECKPOINT-COST` at ≤120 calls as deciding the premise / firing the falsifier. The sibling protocol §5.1 arithmetic (3 arms × 40 turns = 120 turn requests + 3 checkpoint requests = 123 for one rep; one rep is descriptive; 3 reps = 369; 450 with the 12-checkpoint fixture) shows ≤120 buys only a descriptive one-rep probe — and even that is 123, over the cap. The report was qualified to match; the protocol was not weakened.

## Edits applied (8 locations, each `edit`, no whole-file rewrite)
1. §1 bold recommendation (line 21): E2 now runs "at a budget the owner approves"; ≤120 = one-rep descriptive probe (123 requests incl. 3 checkpoint requests), not a verdict; adjudicable 3-rep E2 = 369 (450 with 12-checkpoint fixture), explicit owner approval against 1,729 remaining (2026-10-28). `and nothing else on this evidence` kept verbatim.
2. §1 item 3 (line 25): E2 decides only at an adjudicable budget; at ≤120 (123 actual) it is a one-rep descriptive cost probe that can neither fire nor clear the falsifier; 369–450 needs owner approval.
3. §1 item 4 no-go (line 26): "E2's checkpoint does not repay within 20 steps — measured as uncached work — in an adjudicable E2 run (a 120-call descriptive probe cannot trigger this no-go)".
4. §8.1 item 2 (line 283): "E2's falsifier fires in an adjudicable E2 run (never in the ≤120-call, 123-request descriptive probe)".
5. §8.3 table (line 300): calls = `≤120 descriptive (123 actual) / 369–450 adjudicable with owner approval`; decides = `at 123: a descriptive cost estimate only, no verdict; at 369–450: the premise …`; falsifier kept with `only an adjudicable run can fire it`.
6. §8.3 hard-stop row (line 301): `180 for the ≤120 probe; an adjudicable E2 supersedes it and needs its own cap`.
7. §8.3 budget paragraph (line 305): `E1+E2 at their ceilings is 180 for the ≤120 probe; an adjudicable E2 is 369–450.`
8. §5.1 component 2 (line 178): `C54 forbids deriving one` → `C54 supplies no basis for deriving one`.
9. §7 manifest bullet (line 263): "when our M1 lane lands" attributed to `handoff from consonance/README.md:27`; `INTERFACE_CONTRACT.md` §6 wording `when our manifest and replay fixture land` noted.
10. E-13 row (line 64): after `1.8441x` added `(the source's rounded figure; exact 3,524.0/1,911.2 = 1.843868)`; no other occurrence touched.
11. §0 status table (line 13): `| revision | 2026-11-03, post-VReport: E2 budget qualification and two citation fixes; no evidence changed |`.

## Invariants checked
- 26 evidence ledger rows (`^| E-` count) unchanged; all 10 corrections, BRCV design, 26-row ledger and the zero-live-traffic claim intact.
- `grep -n '120'` leaves no unqualified `≤120 … decides the premise`; the only E2-as-verdict text is now conditioned on an adjudicable run.
- Arithmetic: 3*40+3=123, 3*123=369, 369+81=450, 3524.0/1911.2=1.8438677.
- Report 356 lines (355 + 1 revision row); no protocol, source, frozen record, or evaluation file touched.

## Files
- `research/next-candidates/consonance-bounded-context-report.md` (edited)
- `orchestration/units/CONSONANCE-BC-REPORT-FIX.md` (this card)
- `orchestration/handoffs/CONSONANCE-BC-REPORT-FIX.json`
