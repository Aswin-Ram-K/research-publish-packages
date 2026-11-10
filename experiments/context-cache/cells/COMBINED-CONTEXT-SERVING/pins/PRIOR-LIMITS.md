# Prior-pilot limits the new experiment must not inherit (HL-PILOT)

- Loose input-only promotion gate printed `passes: true` for arm B in `notes/e5-analysis.json` and `notes/e5b-analysis.json` (`gate/*/B/passes=true`, `cost_10pct_lower=true`) while the plan's proxy (uncached input + output) leaves B at -5.4% / -8.6%, below the 10% bar — `REPORT.md` "Limitations" + `V-HL-PILOT.json` check 4b.
- No demonstrated watcher: `HL-PILOT/tools/` contains no watcher and no alert-delivery evidence; `REPORT.md` lists production interruption 0 min but no watcher identity/heartbeat — a new run must attach one before any >2 min job.
- Single restore-key snapshot only: `REPORT.md` "Serving configuration" has one before/after comparison and `V-HL-PILOT.json` flags "absence of a second restore-key snapshot" as an open item — new runs need paired before/after for all six keys.
- E1B has no row file: `V-HL-PILOT.json` check 5 records `E1B 14 (envelope only, no rows)` and `rows/` has no e1b.jsonl — aborted runs must still preserve rows or be explicitly excluded with counts.
- Envelope freeze-before-first-call not provable for E5: `V-HL-PILOT.json` check 6 shows `rows/e5.jsonl` mtime (23:52:10) postdates `envelopes/E5.json` (18:34:32) with no per-row timestamps — new runs must carry UTC start/end on every row.
- Null-to-zero hazard: engine omits `prompt_tokens_details` on a miss; `tests/test_hl_adapter_contract.py` guards null stays null; the mutant `cached = 0 if cached is None else cached` must fail the guard — never convert unknown cache counts to zero in economics.
