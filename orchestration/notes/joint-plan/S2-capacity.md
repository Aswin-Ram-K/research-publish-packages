# S2 Capacity — real remaining capacity for a funded run

## 1. Spend rebuilt from row store (read-only)
Command: `python3 /tmp/s2scan.py` over `experiments/ptr-engine/measure/rows-*.jsonl`.
- files: 41
- rows: 2591
- kinds: turn=1715, turn-initial=283, tool-followup=361, <none>=232
- arms: pointer-stable=1051, transcript-grow=649, lease-reopen=382, transcript-compact=277, R=106, C=24, C0=24, C0F=27, C0FT=24, <none>=27
- prompt_tokens sum: 14,517,784
- completion_tokens sum: 1,017,166
- first row ts: 2026-10-26T05:28:15Z
- last row ts: 2026-10-28T03:35:42.114Z

No repo tooling invoked for mutation; arithmetic replicated in throwaway /tmp/s2scan.py.

## 2. Cap
Authoritative cap = 4320. Defined in:
- `experiments/ptr-engine/measure/REQUEST-LEDGER.json` :: `budget.cap = 4320` (load-bearing)
- `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json` :: 4320
- `experiments/ptr-engine/longrun/cell.py:139` :: `PROJECT_QUOTA = 4320`
Per `measure/LAUNCH-CONTRACT-DIFF.json` id=ledger_cap, authoritative = REQUEST-LEDGER.json + cell.py PROJECT_QUOTA; status AGREES. It is a project-wide cumulative quota (hard cap against cumulative spent), not per-epoch. `operator_cap = 2000` appears only inside the reservation record (RESERVATIONS.json / RESERVATION-CCS-2026-11-05.json); it is an operator-chosen per-reservation ceiling, unrelated to the 4320 project quota. Reservation requested 1500 <= 2000, so it passed the operator gate; ledger remaining at reservation was 1729, so 1500 fit under 4320 at that time.

## 3. Reservation CCS-2026-11-05 (1500)
No consumer code marks any row as reservation-backed: grep for "CCS-2026" found only RESERVATIONS.json, RESERVATION-CCS-2026-11-05.json, and handoff JSONs; no rows-*.jsonl contains "CCS-2026" or "reservation". Therefore the 1500 is recorded-but-untracked: consumption cannot be established from the row store or code. Missing link = a row-level reservation_id / reservation consumer that debits against the 1500.

## 4. Capacity lines
- spent = 2591 (REQUEST-LEDGER.json requests_raw; row store count matches 2591)
- reserved-unverified = 1500 (recorded but no consumption evidence)
- cap = 4320
- available: UNKNOWN — missing link is reservation consumption evidence.
  Conditional bounds:
  - if reserved fully unspent: available = 4320 - 2591 - 1500 = 229
  - if reserved fully spent (or never real): available = 4320 - 2591 = 1729

## 5. Funded-run needs vs cap
Plan needs: core 12,094.2 requests; comparative 7,560 requests.
- spent-only reading (available 1729): cap 4320 < 7560 by 3,240; < 12,094.2 by 7,774.2. Available covers neither.
- spent+reserved reading (available 229): shortfall 7,331 vs 7,560; 11,865.2 vs 12,094.2.
Under both readings the cap falls far short of even the comparative alone; a funding/budget decision is required before any run.
