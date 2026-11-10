# U-SPCC-69 — Commit completed-run manifests, delete dry-run scratch

## Situation
`experiments/ptr-engine/longrun/manifests/` held 229 tracked manifests plus untracked
files from today's cells and dry-run scratch. The tracked set is the convention: every
completed run's manifest is committed as evidence.

**Discrepancy vs assignment:** the ticket said 39 untracked; actual count was **23**
(6 dry-run scratch + 17 completed-run manifests). No other untracked files existed
under `manifests/`.

## Classification

Rows files live at `experiments/ptr-engine/measure/` (not `longrun/measure/`).
Every non-dry manifest's `rows_path` resolved and its `run_id` appeared in that file.

| Manifest | Kind | rows file | run_id hits | Action |
|---|---|---|---|---|
| dryrun-TX-03-spcc-r1-c12.json | scratch (dry_run=true) | rows-e2-compact-2026-11-10.jsonl | 0 | deleted |
| dryrun-TX-03-spcc-r1-c48.json | scratch (dry_run=true) | rows-e2-turnover-2026-11-10.jsonl | 0 | deleted |
| dryrun-TX-03-spcc-r1.json | scratch (dry_run=true) | rows-e2-compact-2026-11-10.jsonl | 0 | deleted |
| dryrun-TX-03-spcc-r2.json | scratch (dry_run=true) | rows-longrun-2026-11-10.jsonl (absent) | 0 | deleted |
| dryrun-TX-04-masking-no-fetch-r1-c200-w200.json | scratch (dry_run=true) | rows-e3-retain-2026-11-10.jsonl | 0 | deleted |
| dryrun-TX-04-spcc-r1-c200-w200.json | scratch (dry_run=true) | rows-e3-retain-2026-11-10.jsonl | 0 | deleted |
| e1-indexfix-2026-11-10-bounded-context-fetch-r1.json | run | rows-e1-indexfix-2026-11-10.jsonl (343) | 143 | committed |
| e1-indexfix-2026-11-10-masking-no-fetch-r1.json | run | rows-e1-indexfix-2026-11-10.jsonl (343) | 100 | committed |
| e1-indexfix-2026-11-10-spcc-r1.json | run | rows-e1-indexfix-2026-11-10.jsonl (343) | 100 | committed |
| e1-parserfix-2026-11-10-bounded-context-fetch-r1.json | run | rows-e1-parserfix-2026-11-10.jsonl (325) | 125 | committed |
| e1-parserfix-2026-11-10-masking-no-fetch-r1.json | run | rows-e1-parserfix-2026-11-10.jsonl (325) | 100 | committed |
| e1-parserfix-2026-11-10-spcc-r1.json | run | rows-e1-parserfix-2026-11-10.jsonl (325) | 100 | committed |
| e1-tools-2026-11-10-bounded-context-fetch-r1.json | run | rows-e1-tools-2026-11-10.jsonl (318) | 118 | committed |
| e1-tools-2026-11-10-masking-no-fetch-r1.json | run | rows-e1-tools-2026-11-10.jsonl (318) | 100 | committed |
| e1-tools-2026-11-10-spcc-r1.json | run | rows-e1-tools-2026-11-10.jsonl (318) | 100 | committed |
| e2-compact-2026-11-10-spcc-r1-c12.json | run | rows-e2-compact-2026-11-10.jsonl (300) | 100 | committed |
| e2-compact-2026-11-10-spcc-r1-c48.json | run | rows-e2-compact-2026-11-10.jsonl (300) | 100 | committed |
| e2-compact-2026-11-10-spcc-r1.json | run | rows-e2-compact-2026-11-10.jsonl (300) | 300 | committed |
| e2-turnover-2026-11-10-spcc-r1-c48.json | run | rows-e2-turnover-2026-11-10.jsonl (300) | 100 | committed |
| e2-turnover-2026-11-10-spcc-r1-c64.json | run | rows-e2-turnover-2026-11-10.jsonl (300) | 100 | committed |
| e2-turnover-2026-11-10-spcc-r1-c96.json | run | rows-e2-turnover-2026-11-10.jsonl (300) | 100 | committed |
| smoke-spcc-2026-11-10-spcc-r1.json | run | rows-smoke-spcc-2026-11-10.jsonl (6) | 6 | committed |
| smoke-spcc2-2026-11-10-spcc-r1.json | run | rows-smoke-spcc2-2026-11-10.jsonl (6) | 6 | committed |

No run manifest lacked a matching rows file. The only absent `rows_path` belonged to
`dryrun-TX-03-spcc-r2.json`, which is scratch and was deleted.

## Result
- Commit `286e2df3142b29b63846dbbff41ce579f7748599` — 17 manifests, explicit paths.
- 6 dry-run scratch files deleted.
- `git --no-optional-locks status --porcelain experiments/ptr-engine/longrun/manifests/` → empty.
- No tracked file modified.
- Pushed: `dcc9b65..286e2df HEAD -> research/next-candidates-2026-10-24`.
