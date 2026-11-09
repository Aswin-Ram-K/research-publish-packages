
## LAUNCH-CONTRACT-ABSENT (card 962c8fcb) — 2026-10-26
1. Journal first (this entry).
2. Read launch_contract_diff.py — locate the crashing access at :653 and the row/table structure.
3. Introduce one accessor returning (present, value, path) for every row; ABSENT rows non-zero exit, no raise.
4. Price arithmetic in the REPORT only: when price.components absent, print turns x factor + provenance beside total, flag price_unjustified.
5. Keep strict --check exit 1 on disagreement; --pin-generation still exits 13 MOVED; numeric disagreement still exit 1 naming both values.
6. Write tests/test_launch_contract_diff_absent.py covering (a)-(d) with red->green.
7. docs/CONTRACT-DIFF-ABSENCE.md.
8. Verdict row with ABSOLUTE interpreter path, then handoff.
9. launch_contract_diff.py: the crash was in checks() building the table (computed probe indexed params["price"]["components"]["tranche"]); run_probe already caught exceptions.
10. Added resolve_field(obj, keys) -> (present, value, path) + _absent(); JSON/jsonpick rows now resolve through it; computed rows may carry absent_path via CA().
11. classify(): absent probes split out; DISAGREES tested BEFORE ABSENT so absence cannot mask two competing values (this ordering is what test (c) guards).
12. build(): row["absent"], summary["absent"], strict exit now includes ABSENT; --pin-generation MOVED=13 still wins.
13. price_derivation(): turns x factor + factor provenance beside the bare total, flag price_unjustified. Params file NOT edited.
14. Tests: 4 passed green; red-1 (crash restored) 4 failed with KeyError; red-2 (precedence reverted) 1 failed ASSERT 'ABSENT' == 'DISAGREES'.
15. Pre-existing external red in tests/test_launch_contract_diff.py (run_a_star.py line drift :241->:517 by the owning card; components-less params crashed the pre-fix tool too).
16. Docs + unit card + handoff written; verdict row recorded with absolute /usr/bin/python3.
17. VERDICT ROW DEFECT (mine, recorded): first orchestration_verdict record carried a placeholder sha b0a4de0b...; the plugin bound execution f6360381 to it and refused a corrected re-record (sha-mismatch). Real HEAD f17663d1. PASS verdict itself is measured (4 passed, exit 0). Needs board-side sha correction.
18. orchestration_verdict refuses an ABSOLUTE interpreter as a runner ("/usr/bin/python3 is not allowed: only test/build runners"), so the ledger command is bare `python3 -m pytest`; absolute path only appears in the local runs.
19. Bound 24 exceeded (27 calls) — verdict-row mechanics only.
