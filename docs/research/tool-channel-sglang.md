# tool-channel-sglang — what the SGLang docs actually say about the tool channel

**Research note, first application of [`docs/RESEARCH-PROTOCOL.md`](../RESEARCH-PROTOCOL.md).**
Machine record: [`measure/research/tool-channel-sglang.json`](../../measure/research/tool-channel-sglang.json).

- **Question:** on an SGLang OpenAI-compatible server, what makes the server emit **structured**
  `message.tool_calls`, which parser names exist for the Qwen family and others, and what does `tool_choice`
  do?
- **Retrieved:** 2026-10-26. **Sources:** 1 primary page. **Fetches used:** 2 (the same page, second read
  longer to reach §Tool Choice Mode). **Budget:** ≤6 fetches / ≤10 min — stopped when each question below was
  answered by the page or shown to be a local check.
- **Scope:** documentation only. **0 live model requests were made.** Nothing here is a measurement of the
  server at `:8012`.

## Source

| id | URL | retrieved_at | kind | claim taken from it |
|---|---|---|---|---|
| `sglang-tool-parser` | <https://docs.sglang.io/docs/advanced_features/tool_parser> | 2026-10-26 | primary (vendor docs, **current-main / unversioned**) | The launch flag that selects the tool parser, the supported parser names, and the `tool_choice` support matrix |

## Verified — read in the primary source

**V1. The flag exists and is a launch flag on `sglang.launch_server`.** The page's launch example is

```
python3 -m sglang.launch_server --model-path Qwen/Qwen2.5-7B-Instruct --tool-call-parser qwen25 --host 0.0.0.0 --log-level warning   # qwen25
```

so the flag is `--tool-call-parser <parser>`, passed at server launch.

**V2. The page's own statement of what the flag does** — verbatim:

> Note that `--tool-call-parser` defines the parser used to interpret responses.

**V3. The supported parser names** (the "Currently supported parsers" table, verbatim rows relevant here):

| Parser | Supported Models (page text) |
|---|---|
| `qwen` | Qwen series (e.g. `Qwen/Qwen3-Next-80B-A3B-Instruct`, `Qwen/Qwen3-VL-30B-A3B-Thinking`) **except Qwen3-Coder** |
| `qwen3_coder` | Qwen3-Coder (e.g. `Qwen/Qwen3-Coder-30B-A3B-Instruct`) |
| `deepseekv3`, `deepseekv31`, `deepseekv32` | DeepSeek-v3 / V3.1 / V3.2-Exp / V3.2 (the v3 and v31 rows recommend a matching `--chat-template`) |
| `glm` | GLM series (e.g. `zai-org/GLM-4.6`) |
| `gpt-oss` | GPT-OSS (e.g. `openai/gpt-oss-120b`, `lmsys/gpt-oss-20b-bf16`) |
| `kimi_k2` | `moonshotai/Kimi-K2-Instruct` |
| `llama3`, `llama4` | Llama 3.1/3.2/3.3, Llama 4 |
| `mistral` | Mistral (e.g. `mistralai/Mistral-7B-Instruct-v0.3`) |
| `pythonic` | Llama-3.2/3.3/4; "Requires `--tool-call-parser pythonic`" |
| `step3` | Step-3 |
| `apertus2509` | Apertus 2509; calls emitted as `<|tools_prefix|>[{"tool": {...}}]<|tools_suffix|>` |

**V4. `qwen25` is a real parser token, but it is in the examples, not the table.** The token `qwen25` appears
in the launch example (V1), in the native-API `/parse_function_call` example
(`"tool_call_parser": "qwen25"` in the request body), and in the offline-engine example
(`FunctionCallParser(tools=tools, tool_call_parser="qwen25")`). It does **not** appear as a row of the table
in V3, whose Qwen rows are `qwen` and `qwen3_coder`. Whether `qwen25` and `qwen` are the same implementation
is **not stated on the page**.

**V5. `tool_choice` is supported, and is implemented as a grammar constraint.** Verbatim:

> SGLang supports OpenAI's `tool_choice` parameter to control when and which tools the model should call. This
> feature is implemented using EBNF (Extended Backus-Naur Form) grammar to ensure reliable tool calling
> behavior.

**V6. The supported `tool_choice` values** — verbatim:

- `tool_choice="required"`: "Forces the model to call at least one tool"
- `tool_choice={"type": "function", "function": {"name": "specific_function"}}`: "Forces the model to call a
  specific function"

**V7. `tool_choice` depends on the grammar backend, not (as written) on the tool-call parser.** Verbatim:

> Tool choice is fully supported with the **Xgrammar backend**, which is the default grammar backend
> (`--grammar-backend xgrammar`). However, it may not be fully supported with other backends such as
> `outlines`.

**V8. The page also exposes a parser selection per request** on the native endpoint
`POST /parse_function_call`, whose body carried `"tool_call_parser": "qwen25"` and returned
`normal_text` + `calls[]`. This is the native SGLang API, not the OpenAI-compatible `/v1/chat/completions`
path.

## Inferred — reasoned, not stated

**I1. Without a tool parser configured, the OpenAI-compatible response carries no structured
`message.tool_calls`.** The page ties the flag to "the parser used to interpret responses" (V2) and every
tool-call example sets it (V1, V4). It never states the negative case. Treating "no flag ⇒ no structured
calls" as documented would be exactly the error the protocol forbids; it is a hypothesis that owns a local
check (launch argv) and, if needed, one measurement.

**I2. `tool_choice` is only meaningful where a tool parser is active.** The page documents `tool_choice` on
the tool-parser page and describes it as forcing tool calls, but it names the **grammar** backend as the
dependency (V7), not the tool-call parser. So "`tool_choice` requires `--tool-call-parser`" is an inference
about the implementation's plumbing, not a documented requirement. Both the `--grammar-backend` default and
the presence of `--tool-call-parser` are **local** facts to read from our launch, not web facts.

**I3. Parser choice is model-family-specific, so the wrong name degrades silently rather than erroring.**
The table pairs each parser with model families (V3), and `qwen` explicitly excludes Qwen3-Coder. A
mismatched name therefore plausibly produces *unparsed* text rather than a startup failure. The page does not
describe error behaviour for a mismatched parser; this inference is what makes the local family check matter.

## Contradicted — recorded, not resolved

**X1. "An SGLang server returns structured `tool_calls` when asked with `tools`."** The page's examples
(V1, V4) show exactly that, and our stack returned **0 structured calls in 36 live requests**
(batch record; not re-measured by this card). This is a real disagreement between a primary source and a
measurement on our stack, and per protocol §5 it is **kept as `contradicted`**. It does not make the page
wrong. It makes two premises visible and both are local, not web:

- **premise A** — the server at `:8012` was launched **with** `--tool-call-parser` at all (read the process
  argv);
- **premise B** — the parser name matches the model family actually served (read `/v1/models` and compare
  with V3).

Until one of those is read, "the flag is missing" and "the parser name is wrong" are equally unfalsified, and
anything said about them is speculation.

## What this changes in our plan

1. **The root-cause card becomes two local reads, not a live battery.** Order: (i) launch argv of `:8012` for
   `--tool-call-parser` and `--grammar-backend`; (ii) the served model id/family. Only if both look correct
   does a live tool-call request carry new information.
2. **No further live measurement is justified to establish the documented behaviour.** V1–V7 settle it. A
   live request is justified only to test premise A or B on this stack.
3. **`tool_choice` is not a free variable.** Any experiment that varies `tool_choice` must also record
   `--grammar-backend`, because V7 makes the grammar backend the documented dependency.
4. **A text-protocol shim, if adopted, is a workaround** (`workaround: true`), not a tool channel: it produces
   no structured `tool_calls` and no server-side `tool_choice` enforcement (protocol §6.3).

## What this note does NOT settle

- **Open Q1.** Whether the server at `:8012` was launched with `--tool-call-parser` (and with which name).
  A local check on the process argv; **owned by the root-cause card**, not by this note.
- **Open Q2.** Which model family `occamy-1.0` belongs to, i.e. which row of V3 would apply.
  A local check on `/v1/models` and the served weights; **owned by the root-cause card**. Not speculated here.
- **Open Q3.** Which SGLang build `:8012` runs. The cited page is **unversioned current-main** docs; version
  drift is possible until the running package version is read (protocol §6.2). A claim about our build taken
  from this page stays `inferred` until then.
- **Open Q4.** Whether `qwen25` (examples) and `qwen` (table) are the same parser, and whether a mismatched
  parser fails loudly. The page is silent; the library source would answer it (next fetch if ever needed).
- **Caveat on the source itself.** The page carries a site-wide banner saying responses are AI-generated and
  "may contain mistakes". It is still the vendor's documentation and outranks any blog, but it is a
  documentation page, not a test result — which is why X1 is recorded as a disagreement rather than settled
  by citation.
