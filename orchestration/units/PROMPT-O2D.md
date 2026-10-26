# PROMPT-O2D — finish the PROMPT-O2 cell, restore production, correct O2's config

**Context.** `PROMPT-O2` was interrupted mid-run. Disk at session start: `rows.jsonl` = **199 rows**
(R=71, A=71, C=57), all `stack=sglang`, `config_id=O2`, 0 null cached_tokens, 0 non-200.
The variant `gx10-p-o2` was Up on `:8017`; `gx10-qwen9b` was Exited (0).

**Purpose.** Complete the missing arm×turn pairs by appending only, rebuild the analysis from all rows,
restore both production containers, and record O2's launchable argv with the measurement behind it.

**Hard bound.** 14 tool calls, 200 live requests, no new container launches, no truncation of rows.

**Write paths.** `experiments/context-cache/cells/PROMPT-O2/**`,
`state/config/best-config.json` (setups.O2 only), this card, `orchestration/handoffs/PROMPT-O2D.json`.

**Method.** The cell script is resumable: it skips every `(arm, turn)` already present in `rows.jsonl`.
An earlier turn's detached runner was already appending when this unit resumed, so it was monitored
rather than duplicated; C reached 71, H ran 71 turns, and the runner's C0 tail was resumed to 71.

**Result.** 355 rows = 5 arms × 71 turns at budget 32768. `analysis.json` rebuilt: ARMS_IDENTICAL
collisions = none. Restore done (`gx10-p-o2` removed, `gx10-qwen9b` Up on `:8014`, `:8012` still Up).
`state/config/best-config.json` `setups.O2` carries `--page-size 1 --mamba-radix-cache-strategy no_buffer
--disable-overlap-schedule --mem-fraction-static 0.22`, `config_sha256 27f5a145…`, `resolved_page_size: 1`,
`grid_unit 8192`, `n_rows 355`, and `tools/best_config_build.py --check` prints True.

**Traps recorded.** (1) The chat endpoint returns `usage.prompt_tokens_details: null` on repeated
identical calls — a blind instrument; the rows' `cached_tokens` come from the client's `/generate`
meta_info path. (2) The card's inherited-row count was stale (152 vs 199); re-running "complete" arms
would have destroyed rows, so counts were re-probed first.
