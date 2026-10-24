# R2-VLLM-REPAIR — repair the two proven instrument defects in the vLLM cell (offline)

**Session:** automated (never asks the user) · **Bound:** 30 tool calls, red→green within 3 attempts
**Scope:** offline only — 0 model requests, no lock, no container action, `gx10-occamy-nvfp4` and
`gx10-qwen9b` untouched.

## Why
`orchestration/handoffs/V-R2VLLM-TRIAGE.json` and `state/logs/R2-VLLM-triage.json` proved two defects in
`experiments/context-cache/cells/R2-VLLM/pmu16_cell.py`:

1. **Blind usage accounting.** OH1/OH1L launched without `--enable-prompt-tokens-details`, and the reader
   `int(... or 0)` (line 295-297) turned absence into a fabricated `0`. OH1 recorded `cached_tokens>0` on
   0/219 rows while A1 (which had the flag) recorded it on 108/201.
2. **Collapsed arm identity.** `phase_battery` hardcoded `render(RenderPolicy.NAIVE_APPEND, …)`; `ARMS[i]`
   `["compaction"]` was dead data, so A/C/H/R differed only by salt.

## Repairs (all in the declared write paths)
- **A** flag in OH1/OH1L `extra` + `OCCAMY_FLAGS`; `parse_usage`/`Client.chat_full` return `cached=None` when
  `prompt_tokens_details` is absent; `usage_has_details` on every row; `uncached=None` when cached is None;
  gate/grid/baseline/`_battery_pass`/analyser all treat `None` as unobserved.
- **B** rows carry `http_status` (== `status`) and `prefix_sha256` + `prefix_sha256_basis`
  (`canonical_json(messages, sort_keys=True, separators=(',',':'))|utf-8`).
- **C** pass 1 renders every turn under its own per-turn salt (`battery_salt(seed, turn)`), pass 2 repeats
  the pass-1 salts; `blocks_available = prompt_tokens // resolved_block_size` (None without a block size);
  the falsified "cold by construction" claim is replaced by a documented correction.
- **D** `build_arm_messages` selects `CompactionPolicy` from `ARMS[i]["compaction"]` and the matching
  `RenderPolicy` (A/H `APPEND_NOTE`→`POINTER`, C `SUMMARISE_IN_PLACE`→`NAIVE_APPEND`, R `FORK`→`POINTER_FORK`)
  with a deterministic offline summariser; `arm_identity_report` refuses to spend requests when an arm is
  indistinguishable; each row records `arm_compaction`, `arm_render`, `prompt_nodes`.
- **E** `run_analyse` refuses to overwrite an analysis whose rows digest no longer matches (legacy
  no-digest analysis refused on row-count mismatch; `--force` keeps a backup and writes separately);
  `usage_coverage` counts `usage_has_details` False/absent separately.

## Verification
`selftest_offline.py` — 14 checks + red→green on both headline fixes, 0 network calls
(`httpx` is aliased to a stand-in; no ssh/docker/HTTP call site is executed).

## Result
See `orchestration/handoffs/R2-VLLM-REPAIR.json`.
