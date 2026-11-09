# UNIT `LEDGER-AFTER-CANARY`

**Purpose.** The brake (`measure/REQUEST-LEDGER.json`) still published `spent 1128 · remaining 3192 · cap 4320`
from the 2026-10-26T18:56:31Z snapshot while live cells kept appending rows, so every reader of the artefact
overstates headroom. Rebuild the snapshot with the ledger's **own** builder, attribute the delta exactly, and
record whether the G1 cap gate reads the JSON's `spent` or re-counts the rows.

**Hard bound.** 25 tool calls (exceeded in practice: ~40 — the fourth-file discovery and a stale-pin repair in
the ledger tests cost the extra calls). Zero inference requests, zero network, no `ask_user_question`.

**Write paths.** `experiments/ptr-engine/measure/REQUEST-LEDGER.json` ·
`experiments/ptr-engine/measure/LEDGER-AFTER-CANARY.json` · `docs/LEDGER-AFTER-CANARY.md` ·
`experiments/ptr-engine/tests/test_request_ledger_sound.py` · `experiments/ptr-engine/tests/test_request_ledger_dedup.py`
(stale literal pins only) · this card · `orchestration/handoffs/LEDGER-AFTER-CANARY.json` ·
`orchestration/journals/LEDGER-AFTER-CANARY.jsonl`.

**Forbidden, and honoured.** row/grade/fixture files, `cell.py`, `run_longrun.py`, `run_a_star.py`,
`analyze_stats.py`, `grade_v5.py`, `measure/HARNESS-PIN.json`, `measure/GRID-PARAMS.json`, published pages other
than the one doc above, and `measure/LEDGER-GRID-BASELINE-2.json` (read only).

## Result

| item | measured |
|---|---|
| rebuild | `build_report(19 files, cap=4320, reserve=0, would_spend=0)` → `requests_raw` **1176**, `requests` 1176, `requests_deduplicated` 1146 (diagnostic, `deducted:false`), `duplicate_excess` 30, `remaining_raw`/`remaining` **3144**, files 19, rows 1176 |
| delta | **48**, not 36 — a fourth live cell was written 2m58s after the canary's own spend record |
| pre-existing files | 15/15 byte-identical (0 sha changed, 0 removed) |
| determinism | builder run twice → byte-identical, sha256 `eadc56f6…` |
| gate | `cell.py:1255` **re-counts** via `build_report` over the artefact's `files` list; it does not trust `budget.spent` |

**Verdict row.** `PASS f17663d1` — `bash -lc '/usr/bin/python3 -m pytest experiments/ptr-engine/longrun/tests/test_cell_gates.py -q'` exit 0.
**Finding for the next unit.** The two ledger test files hardcoded the pre-canary spend; their pins were
superseded with a dated comment (the project's own +27 precedent), not deleted.
