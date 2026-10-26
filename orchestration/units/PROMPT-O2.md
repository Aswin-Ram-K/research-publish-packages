# PROMPT-O2 — five-arm prompt cell on qwen3.5-9b dense NVFP4 under SGLang

**Status: failed (blocked at launch, arg validation).** 0 rows written.

## Purpose
Second of four prompt cells: reproduce `setups.O2` (hit 0.958079, 713.9894 uncached/turn,
grid 64, 284 rows) as a 5-arm x 71-turn cell (355 rows) on a variant container.

## What was done
1. Pre-flight: `available` 57105 MB (gate 20000) — pass. Both production containers Up.
2. Wrote `prompt_o2_cell.py` as `prompt_o1_cell.py` with ONLY CELL / BASE_URL / setups-key /
   salt changed (code diff verified: identity + endpoint lines, nothing else).
3. Launched `gx10-p-o2` from image `72457f09d20e` on `192.168.2.168:8017` with
   `setups.O2.argv` verbatim (only `--model-path` rewritten to `/model`).
4. Container exited code 1 in ~7 s, before binding the port.

## Failure
```
sglang/srt/server_args.py:5835  _validate_mamba_no_buffer
    assert view.page_size in (1, None), "no_buffer only supports page_size=1."
AssertionError: no_buffer only supports page_size=1.
```
`setups.O2.argv` pairs `--mamba-radix-cache-strategy no_buffer` with `--page-size 64`.
This build rejects that pair. This is **not** the expected hybrid-state slot-budget failure
(that string never appears) and **not** an OOM.

## Why it was not worked around
The card requires argv verbatim and forbids inventing flags. Changing `--page-size` to 1 or
dropping `no_buffer` would measure a different config whose rows cannot be compared to the
recorded 713.9894 baseline.

## Follow-up required
A config decision on `state/config/best-config.json` → `setups.O2` (out of this unit's write
scope), plus a check of which container/argv actually produced hit 0.958079.

## Writes
`experiments/context-cache/cells/PROMPT-O2/**`, `orchestration/handoffs/PROMPT-O2.json`,
`orchestration/units/PROMPT-O2.md`, `/home/zer0null/p-o2/**`.
