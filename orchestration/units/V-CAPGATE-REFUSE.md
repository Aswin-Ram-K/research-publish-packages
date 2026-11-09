# UNIT V-CAPGATE-REFUSE

- **Purpose:** independently attack the `delta < 0` refusal added by `CAPGATE-UNRECORDED-REFUSE`. The
  author is not me; nothing here was repaired, only measured and reported.
- **Bound:** 26 tool calls (used 24). Offline, zero inference requests.
- **Write paths:** `docs/V-CAPGATE-REFUSE.md`, `experiments/ptr-engine/measure/V-CAPGATE-REFUSE.json`,
  `orchestration/units/V-CAPGATE-REFUSE.md`, `orchestration/handoffs/V-CAPGATE-REFUSE.json`,
  `orchestration/journals/V-CAPGATE-REFUSE.jsonl`, `/tmp/**` only.
- **Forbidden and respected:** no edit to `cell.py`, `run_longrun.py`, `spawn_record.py`, `exit_codes.py`,
  the author's tests, or any rows/grade file. All mutation in `/tmp/vcap`.
- **Attacks:** (1) re-derive the path from source; (2) `delta < 0` by three shapes of my own; (3) message
  quality; (4) safe direction (0 / positive / pre-send); (5) exit-code coherence; (6) survival through
  `cell.py`.
- **Result:** `overall: partial`. Every `delta < 0` shape that reaches the reconciliation exits 9, the safe
  direction holds (0 / 9 / 4 with zero rows and zero transport for the refused request), and the message is
  actionable. But (a) a truncated rows file exits **5**, not 9; the text is on **stderr**; and the handoff's
  claim that `cell.py` propagates exit 9 unmodified is **false** — `cell.py:1568` maps 9 to 5.
- **Own red→green:** disabling `elif rec["delta"] < 0:` in a `/tmp` copy makes every `delta < 0` shape exit 0
  under a false "reconciled" line; restoring the pristine source returns 9.
