# V4-TOOLS-PROBE — does a working fetch channel let `pointer-stable` answer CP3?

Date: 2026-10-26. Fixture: `longrun/tasks-v4/runtime-v4/LR-01.v4.tools.json` (v4 + one tool-channel sentence).
Arm: pointer-stable, `--tools read_file`, `--thinking off`, max_tokens 4096, 1 rep, N=48.
Rows: `measure/rows-longrun-v4-tools-2026-10-26.jsonl` (68 rows). Grade: `measure/rows-longrun-v4-tools-2026-10-26.grade-v3.json`.

## The exchange at t46 (checkpoint 3)

Emitted text (whole content, 32 completion tokens):

```
<tool_call>read_file {"path": "ptr_engine/resolve.py", "start_line": 66, "end_line": 71}
</tool_call>
```

tool_calls array:

```json
[{"path": "ptr_engine/resolve.py", "start_line": 66, "end_line": 71, "executed": false, "truncated": false, "error": "fetch_budget_exhausted"}]
```

`<tool_result>` injected: **none**. `error` = `fetch_budget_exhausted`. No `kind='tool-followup'` row exists for turn 46 (`T46 followup rows: []`), because the runner refused to execute the call: the per-arm round cap was already spent (`fetch_rounds_used=8/8` at t46). The turn answered nothing — the content is the call alone, with no `ANSWER:` line — so `cp.2.t46` fails with `marker_missing`.

## Fetch census

| item | value |
|---|---|
| rounds the runner reported | 8 / 8 (exhausted before t46) |
| calls **executed** (tool-followup rows) | 20 |
| calls **refused** | 194 — {'path_not_found': 54, 'fetch_budget_exhausted': 136, 'turn_call_cap': 4} |
| requests actually spent | 48 turn rows + 20 follow-up rows = **68** |

The 20-vs-8 gap is a real accounting anomaly and part of the finding: the run was launched three times in one job slot (two harness kills at turn 4 and turn 23, each resumed with `--resume`), and the in-memory `fetch_rounds` counter resets on every relaunch, so the arm consumed 20 real fetches while the counter believed 8. Row count and `requests_sent` stayed consistent with `48 + follow-ups` (68 requests), so the per-request accounting is real; only the round cap is not durable across a resume.

## Grade

`verified_success = None` · `checkpoint_accuracy = 1/3` (33.3%) · `tokens_to_verified_success = None`.

- `cp.0.t12` pass — but the answer was reached after inventing `find`/`run_shell` tool calls the channel does not offer.
- `cp.1.t24` fail — `marker_missing`; asked for a shell `grep`.
- `cp.2.t46` fail — `marker_missing`; the fetch it correctly requested was refused (`fetch_budget_exhausted`).
- `repair.t30` fail — `repair_not_acknowledged`; at t30 the arm said "I'm out of fetch rounds, so I'll work from the pinned bodies."

## Tools-off control (`rows-longrun-v4-2026-10-26.jsonl`, same arm, same checkpoint)

| | tools OFF | tools ON |
|---|---|---|
| cp.2.t46 | False — marker_missing | False — marker_missing |
| checkpoint_accuracy | 1/3 | 1/3 |
| verified_success | None | None |
| requests spent | 48 | 68 (+20) |

Enabling the channel changed CP3's *shape* — the arm now emits a well-formed `read_file` call with a correct path and a correct line window instead of a mangled `2629 read_file` blob — but **not its outcome**: CP3 still fails, now because the round budget was spent before the checkpoint turn. Cost: +20 requests (48 → 68).

## Verdict

**FETCH-BROKEN** — at the checkpoint turn a well-formed call was asked for and the harness did not execute it; the quoted error is `fetch_budget_exhausted`, recorded on the t46 `tool_calls` entry with no matching `tool-followup` row. Contributing defect: the `8` round cap is not durable across `--resume`, so the arm spent 20 fetches while the counter reported 8/8 and the checkpoint landed behind an exhausted budget.
