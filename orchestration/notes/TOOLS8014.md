# TOOLS8014 — vLLM tool-call enablement for `bounded-context-fetch` arm

## Current capability (observed, read-only)
- Endpoint: `http://192.168.2.168:8014`
- `GET /v1/models` → `id=qwen3.5-9b`, `owned_by=vllm`, `max_model_len=32768`, `root=/model`.
- `GET /version` → `{"version":"0.27.1"}`.
- `GET /health` → HTTP 200, empty body.
- No tool-call parser is active: vLLM requires explicit flags to accept/parse OpenAI-style `tools`/`tool_choice`; absent them, a request carrying `tools` is rejected or the model's `<tool_call>` output is not parsed into structured `tool_calls`.

## Missing configuration (cited)
vLLM Tool Calling docs (https://docs.vllm.ai/en/latest/features/tool_calling): start server with `--enable-auto-tool-choice` plus a `--tool-call-parser` matching the model's chat template. For Qwen models the docs recommend `hermes` for Qwen2.5 (tokenizer chat template already Hermes-style). For Qwen3.5 specifically, the vLLM Qwen3.5 recipe (https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen3.5.html) states: "To enable tool calling, add `--enable-auto-tool-choice --tool-call-parser qwen3_coder` to the serve command."

## Exact flags to add (operator)
Add to the vLLM launch command for `qwen3.5-9b`:
```
--enable-auto-tool-choice --tool-call-parser qwen3_coder
```
No custom `--chat-template` is required per the recipe; the model's own tokenizer chat template already supports tool use.

## One-command verification (operator, after restart)
```
curl -sS http://192.168.2.168:8014/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3.5-9b","messages":[{"role":"user","content":"What is 2+2? Use the add tool."}],"tools":[{"type":"function","function":{"name":"add","description":"Add two ints","parameters":{"type":"object","properties":{"a":{"type":"integer"},"b":{"type":"integer"}},"required":["a","b"]}}}],"tool_choice":"auto"}'
```
Expected: response `choices[0].message.tool_calls` non-empty with `function.name == "add"`.

## Harness-side gap
- `experiments/ptr-engine/longrun/run_longrun.py:466` `TOOL_NAMES = ("read_file",)` and `:3735` help text "supported: read_file" describe the read_file channel only; this is not a blocker for the fetch arm, which uses a separate `fetch` tool name and `arm_cd.parse_fetch_calls_from_response` (`experiments/ptr-engine/longrun/arm_cd.py:225`).
- `run_longrun.py:851` `parse_tool_calls` parses `read_file` calls only; fetch-arm round trips are handled by `arm_cd` path, so on a tool-capable endpoint the `bounded-context-fetch` arm would get a real tool-call round trip (structured `tool_calls` parsed by `arm_cd.parse_fetch_calls_from_response` at `:225`, then `service_fetches`).
- No harness code change required for the endpoint to become tool-capable; only the server flags above.

## Requests issued (read-only, no state change)
1. `GET http://192.168.2.168:8014/v1/models`
2. `GET http://192.168.2.168:8014/health`
3. `GET http://192.168.2.168:8014/version`
No `/flush_cache`, `/reset`, or other state-changing route was called; no route enumeration.