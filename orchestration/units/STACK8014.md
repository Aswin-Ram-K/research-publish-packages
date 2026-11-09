# STACK8014

Cross-stack check on `http://192.168.2.168:8014` (vLLM, qwen3.5-9b, context 32768).

## Preflight
- Model confirmed: `GET /v1/models` -> `qwen3.5-9b`, `max_model_len=32768`.
- Offline prompt build for all 48 turns, both arms: max prompt ~758 tokens (est) / 3101 bytes at turn 48, far below the 32768 window. Fixture fits. No shrinkage applied.

## Runs
1. masking-no-fetch, masking on: 48 requests, 0 truncated. Score 0/12 (all 12 checkpoints NONE).
2. masking-no-fetch, masking off (WINDOW_TURNS=100 sitecustomize): 48 requests, 0 truncated. Score 8/12 (t30,t32,t34,t40 failed on format, not fact).
3. bounded-context-fetch, masking on, --tools read_file: 1 request, HTTP 400 (vLLM lacks --enable-auto-tool-choice/--tool-call-parser). Cell stopped. Score 0/12 (no records past T1).

## Compare to 8012 (occamy-1.0)
- 8012 masking-on: 0/12; 8014 masking-on: 0/12. Masking destroys the fact on both stacks.
- 8012 masking-off: 12/12; 8014 masking-off: 8/12. Compliance differs (qwen3.5-9b emits codes as NUM and adds quotes).
- 8012 bounded fetch: 12/12; 8014 bounded fetch: blocked (tool calls unsupported). Pattern cannot be tested on this stack.

## Accounting
48 + 48 + 1 = 97 requests. All rows task_id=TX-01, sha 44a1b4356536a0a55757ed2a4c90f5ef7f9d0541836007dc195a50ab3db2ec21. No disagreements.

## Blocker
bounded-context-fetch cannot run on 8014: vLLM 0.27.1 rejects tool schemas with HTTP 400 ("auto tool choice requires --enable-auto-tool-choice and --tool-call-parser"). No service change made. Fetch-recovery claim for this stack is untested.