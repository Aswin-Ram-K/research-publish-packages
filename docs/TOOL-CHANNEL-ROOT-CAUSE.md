# TOOL-CHANNEL-ROOT-CAUSE — where a tool call stops being a request and becomes prose

**Unit:** `TOOL-CHANNEL-ROOT-CAUSE` · **Date:** 2026-10-26 · **Bound:** 30 tool calls, ≤6 model requests
**Verdict:** `client_never_sends_tools` — the harness client never puts a `tools` member on the wire, so the
model is never handed a schema to call, and the runner's whole "tool channel" is a text protocol the model
was never told about.
**Fix owner:** client-side, inside this workspace (`experiments/ptr-engine/longrun/client.py`, plus the one
consumer in `run_longrun.py`). **Needs operator approval:** no — no server change is required.

**Evidence artefacts:** `experiments/ptr-engine/measure/probe-tool-channel-raw.json` (2 billed requests),
`measure/TOOL-CHANNEL-ROOT-CAUSE.json`, `tools/tool_channel_root_cause_check.py` (offline replay, 17 assertions, exit 0).

---

## 0. The claim under test

`LIVE-CANARY-4ARM-3` ran 36 live requests with `--tools read_file` on the runner argv and the
`CELL_RUNNER_PATH` shim in place, and produced `tool_calls=[]` on **every row of all three arms**.
`transcript-grow` turn 1 wrote the call as fenced text:

```text
``` read_file @knowledge:resolve.py@1 ```
```

`pointer-stable` turn 4 degenerated into "Let me run the tests." repeated to the 4,096-token ceiling.
The channel is *declared* in argv and *absent* in the wire.

## 1. The chain, in order

| # | Step | Where | What actually happens |
|---|------|-------|-----------------------|
| 1 | argv declares the channel | `CELL_RUNNER_PATH` shim (recorded at `measure/DRYRUN-TOOLS-SHAPE.json`, recorded shim body) → `run_longrun.py:2884` (`--tools`), `run_longrun.py:262-263` (`tools_enabled`) | `--tools read_file` becomes a **boolean in this process**. Nothing leaves the process. |
| 2 | the runner builds the prompt | `run_longrun.py:1071-1073` `Planner.messages` → `{"role":"system","content":fixture["system_prompt"]}` + one user turn; working set rendered by `run_longrun.py:190-192` `index_lines` as `- @knowledge:<id>@1 <hash8> <len>` | The prompt **invites a read** ("Read ptr_engine/resolve.py#L66-L110") and shows ptr-engine ref notation, but never names an invocation protocol. `<tool_call>` occurs **0** times in the fixture; `read_file` occurs **exactly once**, negatively: *"On those turns the tools are unavailable - no read_file, no fetch, no follow-up request is served"*. |
| 3 | **the request body is built — this is where the channel dies** | `client.py:317-346` `request_body()`; called at `client.py:658`, serialised at `client.py:659`, posted to `/chat/completions` at `client.py:661` | The body is `{"model", "messages", "temperature": 0, "max_tokens": cap, "stream"}` plus optional `stream_options` (`client.py:340`) and `chat_template_kwargs` (`client.py:343`). **No `tools`. No `tool_choice`.** These are the only two body mutations in the whole file. |
| 4 | the response is parsed for prose | `client.py:579` (stream delta), `client.py:685` (non-stream), `client.py:766` (`tool_calls_present`) vs `run_longrun.py:605-645` `parse_tool_calls`, gated at `run_longrun.py:2480-2504` | The client can *see* a structured call but records only a boolean `tool_calls_present` (a token-kind / stop-reason signal). The **runner** reads calls by scanning `resp["content"]` for `<tool_call>` and then decoding a JSON object that carries a `path` key (`run_longrun.py:614-632`). |
| 5 | the endpoint | `http://192.168.2.168:8012/v1` (SGLang, `occamy-1.0`) | Supports structured tool calls — see the probe below. `/v1/models` advertises `{"id":"occamy-1.0","owned_by":"sglang","max_model_len":131072}` and no tool metadata (SGLang does not advertise it there). |

**Step 3 is the divergence.** Everything upstream of `request_body()` is an internal convention; everything
downstream of it — the model's response, the runner's parser, the fetch executor — depends on a schema the
wire never carried. The harness's expectation ("tools are on") and the model's information ("no tool
definitions, no call syntax") separate exactly at `client.py:333-339`.

A telling detail: `request_digest`'s own docstring (`client.py:305-315`) says the request identity is
*"model, messages, temperature, max_tokens, stream, stream_options, chat_template_kwargs/thinking — and
`tools` where an engine takes them as a body member"*. The docstring anticipates the member; the body
builder never adds it. That is not a bug in the parser — it is an unimplemented assumption one function
above the wire.

## 2. Why the model answered in prose specifically

`index_lines` (`run_longrun.py:190-192`) renders the working set as `- @knowledge:resolve.py@1 <hash8> <len>`,
and turn 1 says *"Read ptr_engine/resolve.py#L66-L110"*. With no schema, the only invocation grammar in
context is the ref notation, so transcript-grow t1 emitted `` ``` read_file @knowledge:resolve.py@1 ``` `` —
a plausible call in the notation it was shown, wrapped in a code fence. `parse_tool_calls` requires
`"read_file" in text` (satisfied) and then a JSON object with a string `path` (`run_longrun.py:616-617`,
`:629-632`); a ref string has none, so the call yields `[]`. The model did **not** ignore a tool; there was
no tool to call.

`pointer-stable` t4 is a different failure on the same root: with no call available and a wall of pinned
corpus, the turn emits "Let me run the tests." repeatedly to `finish_reason=length` at 4,096 tokens.

## 3. The probe (2 billed requests, `thinking off`, `max_tokens 512`, no cell, no fixture)

One prompt — *"Read ptr_engine/resolve.py lines 66 through 110 and list every raise site…"* — sent twice to
`POST /v1/chat/completions`, `temperature 0`, `stream false`, `chat_template_kwargs {"enable_thinking": false}`.

| request | body adds | HTTP | `finish_reason` | `tool_calls` | content |
|---|---|---|---|---|---|
| A | `tools=[read_file schema]`, `tool_choice="auto"` | 200 | **`tool_calls`** | **present** — `function.name="read_file"`, `arguments={"path":"ptr_engine/resolve.py","start_line":66,"end_line":110}`, `id="call_0ffd2bc459de42e790223702"` | empty (len 0), 56 completion tokens |
| B | — (nothing) | 200 | `stop` | `null` | 237 chars: *"I cannot read specific lines of a file without its content being provided in the context. Please paste the text of `ptr_engine/resolve.py` lines 66–110…"* |

Both went to the endpoint the runner uses. The endpoint is **not** the bottleneck: given a schema it returns
a structurally valid call with the exact arguments the executor consumes, and given no schema it declines in
prose rather than inventing a fenced call (unlike the fixture prompt, which supplies ref notation for it to
imitate).

The call shape the endpoint emits is also directly executable by the existing runner: `find_pinned_view`
(`run_longrun.py:813-836`) matches a path on equality **or a `/`-anchored suffix** and calls the arm's
`ptr_engine/resolve.py` against the fixture's `experiments/ptr-engine/ptr_engine/resolve.py` "intentionally
lenient", and `execute_tool_call` (`run_longrun.py:704-746`) serves `{"path","start_line","end_line"}`.

## 4. Classification

**`client_never_sends_tools`.** The endpoint honours `tools`; the client never sends one. The fix is
client-side and needs no endpoint change, no flag, and no operator approval.

Rejected alternatives, with the evidence that rejects them:

- **`endpoint_ignores_tools`** — rejected by probe A: HTTP 200, `finish_reason="tool_calls"`, structured
  `arguments`. No SGLang `--tool-call-parser` flag is missing; the served process already parses.
- **`prompt_never_requests_a_call`** — *also true*, but not sufficient and not the primary cause: it is a
  consequence of having no schema to describe. With `tools` on the wire a prompt that says nothing about
  invocation is *correct* (the schema is the protocol); the probe's own prompt never names `read_file` and
  still produced a call. Fixing the prompt first would only change which prose the model writes — the
  parser at `run_longrun.py:605` would still be matching a text format the engine never emits.
- **`model_emits_prose_by_preference`** — rejected by probe A: the model calls when given a schema, and
  declines in a *different* register when it is not. No coercion (`tool_choice="required"`, stricter
  schema) is needed to obtain a call.

## 5. Consequence for the fix card (read this before writing it)

A one-line addition of `tools` to `request_body()` is **not** a fix by itself, and will make the arms look
worse, not better:

1. With `tools` sent, SGLang returns the call in `message.tool_calls` and **`content` is empty** (probe A:
   `content_len 0`). `run_longrun.py:2426` passes `resp["content"]` to `parse_tool_calls`, which would then
   find nothing — and `client.py:766` already flattens the call to `tool_calls_present: true`, so the
   information exists and is discarded one layer below the consumer.
2. So the fix is two coupled changes: (a) `request_body()` carries `tools` (and, if the protocol wants
   determinism, `tool_choice`), driven by `tools_enabled(cfg)` so a tools-off run keeps its exact body; and
   (b) `client.send_chat` returns the structured `tool_calls` (or the runner reads them off the response
   object) and `parse_tool_calls`' text scan is retired or kept only as a fallback.
3. Two contract details the fix must not break: `request_digest` covers the exact bytes (`client.py:305`), so
   a tools-on body changes every request sha — that is correct, but any frozen ledger/row identity that
   assumed the old body must be told; and `tools_mode` (`client.py:862`) already labels a run `on:read_file`
   even though the wire said otherwise, so **existing rows misreport their tool mode** — that is a
   provenance defect that predates the fix.
4. `--tools` is currently opt-in and `tools_enabled()` is false on every tools-off run (`run_longrun.py:262`);
   the body change must be gated on it, or every historical arm's request identity moves.

**Diagnose only — no fix applied.** `client.py`, `run_longrun.py`, `cell.py`, `run_a_star.py`,
`analyze_stats.py`, `grade_v5.py`, and every fixture/pin/params/ledger/rows/grade artefact were read only,
never written.
