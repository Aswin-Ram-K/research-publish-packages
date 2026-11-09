# ADOPTION-LEDGER — every hairy problem this batch met, and whether adoption was considered

**Question:** for each hairy problem this batch met, did we look for something that already exists before
building, what did we find, what did it cost to adopt, what build did it save, and what did we decide?

Machine record: [`measure/research/ADOPTION-LEDGER.json`](../../measure/research/ADOPTION-LEDGER.json).
Rule of record: [`docs/RESEARCH-PROTOCOL.md`](../RESEARCH-PROTOCOL.md) §8 (**Adopt before build**).

**Hairy** (§8.1) = mechanism unclear, or more than one component must change, or we are about to write
infrastructure rather than a measurement, or the same-shaped problem has been solved outside this repo
(serving, batching, caching, tool calls, benchmarking, provenance, CI gating). **Hairy ⇒ the research card
comes first, before the build card.**

**Reading the `decision` column.** `adopt` · `adapt` · `borrow-idea` · `build` · `not-applicable` are
decisions. `unassessed` is **not** a decision: it means no candidate was named or read, so there is nothing to
decide yet — those rows are the backlog this ledger exists to surface. An unread option is never given a
project name and never given a URL here; inventing either would be worse than the gap.

## The table

| # | problem (hairy because) | existing option (name · licence · maturity · last release) | what it would replace here | adopt cost (calls/files/risk) | build cost avoided | decision | source (URL · retrieved) |
|---|---|---|---|---|---|---|---|
| R1 | **tool calls on SGLang** — mechanism unclear (0 structured calls in 36 live requests), two components must change (request body + response consumer), same shape solved outside this repo | **SGLang's own server-side tool parser**: `--tool-call-parser <parser>` at launch; the adoptable part proved to be the OpenAI-compatible **wire contract** (`tools` in, `tool_calls` out), not a client library. Name: SGLang. Licence/maturity/last release: **not read** (docs page carries none of the three) | our hand-written text-protocol scan (`run_longrun.py:605-645`, `<tool_call>` notation in `content`) and a planned client-side shim | 0 new dependencies; 2 files (`client.py` request body gains `tools`; `run_longrun.py` consumes `message.tool_calls`); risk: every tools-on request's exact bytes change, so `request_digest`/row sha moves | a client-side tool-call parser plus its ambiguity handling (arguments as free text) | **borrow-idea** — send `tools`, consume `tool_calls`; no library | <https://docs.sglang.io/docs/advanced_features/tool_parser> · 2026-10-26; probe: `orchestration/handoffs/TOOL-CHANNEL-ROOT-CAUSE.json` · 2026-10-26 |
| R2 | **retry / backoff & HTTP client** — we wrote infrastructure (a retry loop) rather than measuring, and the shape is solved outside this repo | **unassessed** — candidate class only: a maintained HTTP client/transport library offering retry + backoff (no project named, no page read) | our hand-rolled retry/backoff and HTTP request path in `experiments/ptr-engine/longrun/client.py` | unassessed — no candidate read, so no cost measured | unknown — cannot be claimed before a candidate is read | **unassessed** | none (recorded gap; no URL, no name) |
| R3 | **gate / budget / verdict / provenance stack** — about 200 rounds of infrastructure, multi-component, same shape solved outside this repo | **unassessed** — no candidate framework was named or read in this batch; this row is the operator's own counter-example (protocol §8.3), not a survey | our hand-built gate, budget, verdict and provenance layers (`orchestration/verdicts/`, `orchestration/VERDICTS.md`, verdict-ritual tests) | unassessed | unassessed | **unassessed** (status quo is hand-built; the counter-arguments — custom semantics, frozen thresholds, one-writer discipline — must be written case by case, not assumed) | none (recorded gap) |
| R4 | **research-note / handoff shape validation** — we wrote a validator rather than measuring, and JSON-shape checking is solved outside this repo | **unassessed** — candidate class only: a JSON-Schema validator or note linter (no project named, no page read) | [`tools/check_research_notes.py`](../../tools/check_research_notes.py) and the handoff parsers under `tests/` | unassessed | unknown | **unassessed** | none (recorded gap) |

## Verified — read in a primary source, or measured on our stack

**V1 (source fact).** `--tool-call-parser <parser>` is a **launch flag** on `sglang.launch_server`, and the
vendor page states verbatim "`--tool-call-parser` defines the parser used to interpret responses." Source
<https://docs.sglang.io/docs/advanced_features/tool_parser>, retrieved 2026-10-26; quoted and dated in
[`docs/research/tool-channel-sglang.md`](tool-channel-sglang.md) §"Verified" V1–V2 (this ledger did not re-fetch;
it reads the landed note's verbatim quote).

**V2 (measurement on our stack).** With `tools` in the request, the server answered `finish_reason='tool_calls'`
and a structured `tool_calls[0].function = {"name":"read_file","arguments":"{\"path\": \"ptr_engine/resolve.py\", \"start_line\": 66, \"end_line\": 110}"}`,
`content_len=0`, 56 completion tokens; the same prompt **without** `tools` returned `finish_reason='stop'`,
`tool_calls=null`, 237 chars of prose. Evidence:
`orchestration/handoffs/TOOL-CHANNEL-ROOT-CAUSE.json` (`probe_with_tools`, `probe_without_tools`), 2026-10-26.

**V3 (measurement on our stack).** The root cause was client-side: the request body is
`{model, messages, temperature, max_tokens, stream[, stream_options][, chat_template_kwargs]}` — no `tools` key
exists in `client.py:317-346` — so the earlier 36-request batch sent no schema and could not have received a
structured call. Evidence: same handoff, `cause=client_never_sends_tools`.

## Inferred — reasoned, not documented

**I1.** The adoptable part of the tool channel was the **wire contract**, not a library or a server flag change.
V1 says a parser exists server-side; V2 shows our build already honours `tools`; V3 shows the missing piece was
one absent client key. Adopting any tool-call library on the client would not have supplied it.

**I2.** The batch's "0 structured calls in 36 requests" was not a server limitation and not a counter-example to
the vendor docs; it was a client omission. The docs were right about the mechanism; our request was not
speaking it.

## Contradicted — recorded, not resolved by convenience

**X1.** "An SGLang server returns structured `tool_calls` when asked with `tools`" vs **0 structured calls in 36
live requests** (batch record). Per protocol §5 this stays recorded. The root-cause probe (V2) shows the
disagreement was **ours**: the client never sent `tools`. Both facts survive — the batch record is true, and
the docs claim is true — because they describe different request bodies.

## Open questions

- **Q1 — R2.** Which maintained HTTP client/transport actually covers retry + backoff for our call shape, and at
  what licence/maturity? Owner: a future adoption research card (`ADOPT-HTTP-RETRY`).
- **Q2 — R3.** Which, if any, existing gate/verdict/provenance tooling covers the parts of that stack that are
  not custom (e.g. verdict recording, artefact provenance)? Owner: a future adoption research card
  (`ADOPT-VERDICT-STACK`), which must write the counter-arguments per layer rather than for the whole stack.
- **Q3 — R4.** Whether a JSON-Schema validator would replace `tools/check_research_notes.py` without losing its
  protocol-specific headings check. Owner: same class of card (`ADOPT-NOTE-LINT`).
- **Q4 — R1.** SGLang's licence, maturity and last release were not read on this pass; a later memo that proposes
  *changing* the served build (rather than its wire contract) must read all three.

## Adding a row

Append a row when a card meets a §8.1 test. Fill `name · licence · maturity · last release` **only from a
source you read**, with its URL and retrieval date; otherwise write `unassessed` and put the question in the
JSON's `open_questions`. A frozen measurement path may be proposed here but not changed: mark
`blocked_by: frozen-path` and leave execution to a card that owns the freeze.
