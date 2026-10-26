# RUNNER-THINKING-FLAG

Objective: add `--thinking {auto,on,off}` (default `auto`) to `run_longrun.py` so a later card can
test the chat-template thinking switch, WITHOUT changing what the instrument does today.

## Change
- `thinking_setting(cfg)` / `thinking_kwargs(thinking)` + `request_body` seam (the only new key).
  `auto` -> key omitted entirely (byte-identical body); `on`/`off` -> `chat_template_kwargs.enable_thinking`.
- `--thinking` CLI; `thinking` frozen in the manifest (top level + `renderer`), stamped on every row.

## Bound and result
16 tool calls max; zero requests; `--dry-run` + pytest only. Status: done.
Evidence: see `orchestration/handoffs/RUNNER-THINKING-FLAG.json`.
