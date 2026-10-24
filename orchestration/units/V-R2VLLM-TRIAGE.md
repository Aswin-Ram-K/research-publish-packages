# V-R2VLLM-TRIAGE — offline triage of the running R2-VLLM cell

**Status:** done (2026-10-24T02:23Z). Card: `cf5f1525-e146-48ee-9664-5aefd2e7eed9`.

## Purpose
Name the cause of "no hits / no http_status" in `experiments/context-cache/cells/R2-VLLM/rows.jsonl`
from recorded rows only, before four downstream cards consume it. Zero live requests.

## Inputs (read-only)
- `experiments/context-cache/cells/R2-VLLM/rows.jsonl` — 420 rows, sha256 `2737125f…e5045c`
- `experiments/context-cache/cells/R2-VLLM/pmu16_cell.py`, `analysis.json`, `logs/OH1-launch.json`, `logs/A1-launch.json`
- `src/resextract/context/render.py`, `experiments/context-cache/corpora/endtoend.json`

## Findings
1. **Prompt shape is NOT the cause.** Arm R (seed 3203) is append-only: turn-1 content (4882 B = 1181 tokens)
   is a full byte prefix of turn-2 (6522 B); first differing offset 4882. Turns 1–2 are below the 2096-token
   block, so no complete block exists before turn 3.
2. **The reader uses the correct key** — `usage.prompt_tokens_details.cached_tokens` (`pmu16_cell.py:295-297`).
   But OH1 launched **without** `--enable-prompt-tokens-details` (`pmu16_cell.py:121`, `extra: []`), A1 with it
   (`:129`). OH1 cached>0 = 0/219; A1 = 108/201 (incl. 1056 cached on a rep=0 "cold" turn 3). The zeros are an
   accounting artifact, not a dead cache. `or 0` at :296 hides the distinction.
3. **`http_status` / `prefix_sha256` are writer omissions.** The row dict writes `"status": status`
   (`:378`) and never writes `http_status`; `prefix_sha256` was never implemented. 381 rows are status 200,
   38 are status 0 (A1 connect-refused), 1 is HTTP 500.
4. **Arms are not distinct:** `phase_battery` hardcodes `RenderPolicy.NAIVE_APPEND` (`:571`) and ignores the
   declared `compaction` at `:133-136`; A/C/H/R differ only by salt.
5. **`analysis.json` is stale** (21:03:58 vs rows to 21:17:21): reports qwen n=2 / all zeros, contradicted by rows.

## Verdicts
- OH1 A/C/H/R: **invalid** (blind instrument + collapsed arm identity).
- A1 A/C/H/R: **invalid-for-arm-contrast**; the A1 rows are a valid cache-live witness, with 39 failure rows and
  cap truncation (H 16/32, R 27/32).

## Deliverable
`state/logs/R2-VLLM-triage.json` — `{common_prefix_len, first_diff_offset, cached_key_source, null_cause,
per_arm_verdict, repair_plan}` + supporting sections.

## Handoff
`orchestration/handoffs/V-R2VLLM-TRIAGE.json`. Next: `R2-VLLM-REPAIR` applies repair_plan orders 1–5; no battery
re-run before then.

## Bound
18 tool calls. Used 29 (over by 11: reconstructing the prompts required locating and reading
`src/resextract/context/render.py` and the cell's builder, one call was lost to a wrong path guess,
and four were policy-mandated read-before-edit calls on the two JSON artifacts).
No live requests, no ssh/docker/HTTP.
