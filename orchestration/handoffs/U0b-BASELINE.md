# U0b — Baseline Fairness: what production agent harnesses actually put in the prefix

**Unit:** U0b `baseline-fairness`
**Scope:** public sources only; no live model calls; writes limited to this unit's two handoff files.
**Sources verified: 8 / 9 attempted** (OpenHands not fetched — rows 8–9, §5).
**Tool calls used: 20** (bound 35).

---

## 1. Evidence table

| # | Harness | What is in the prefix | Changes per turn? | Source URL | Verified |
|---|---------|----------------------|-------------------|------------|----------|
| 1 | **Aider** (code) | Fixed chunk order, `all_messages()` = `system + examples + readonly_files + repo + done + chat_files + cur + reminder`. The *repository map* is a rendered chunk **ahead of** the editable-file chunks and ahead of the conversation. `add_cache_control_headers()` places `cache_control: {"type":"ephemeral"}` on the last message of `examples` (else `system`), on `repo` (else `readonly_files`), and on `chat_files`. | **No, by design.** The prefix is assembled to be cacheable; cache breakpoints are set explicitly. Volatility enters mid-prompt: a re-rendered `repo` chunk invalidates every breakpoint after it (`add_cache_control(self.repo)` marks *both* `readonly_files` and `repomap` as one cacheable span). | https://raw.githubusercontent.com/Aider-AI/aider/main/aider/coders/chat_chunks.py | yes |
| 2 | **Aider** (prompt text) | Prompt fragments live in `class CoderPrompts` (`system_reminder`, `files_content_prefix`, `read_only_files_prefix`, `repo_content_prefix`, `lazy_prompt`, …) — static string constants, no timestamps, no counters, no cwd. | No. Nothing in the file is turn-dependent. | https://raw.githubusercontent.com/Aider-AI/aider/main/aider/coders/base_prompts.py | yes |
| 3 | **Aider** (docs) | "Aider organizes the chat history to try and cache: The system prompt. Read only files added with `--read` or `/read-only`. The repository map. The editable files that have been added to the chat." Also: "By default, Anthropic keeps your cache for 5 minutes. Use `--cache-keepalive-pings N` to tell aider to ping every 5 minutes to keep the cache warm". | No — caching is an explicit product goal with a keepalive mechanism to defeat TTL expiry. | https://aider.chat/docs/usage/caching.html | yes |
| 4 | **SWE-agent** (code) | Full history of thought/action/observation per step; `_set_cache_control()` puts `cache_control: {"type":"ephemeral"}` on messages, and `_clear_cache_control()` strips them when the history is rewritten. `LastNObservations` is "our most classic history processor, used in the original paper to elide but the last 5 observations"; elided observations are replaced with `"Old environment output: (n lines omitted)"`. | **Yes, in the classic default.** Verbatim from the docstring: *"Note that using this history processor will break prompt caching (as the history of every query will change every time due to the elided observations)."* Mitigation is the `polling` parameter: *"This is useful for caching, as we want to remove more and more messages, but every time we change the history, we need to cache everything again."* So: append-only for `n` steps, then a **rewrite of earlier messages** ⇒ prefix churn. | https://raw.githubusercontent.com/SWE-agent/SWE-agent/main/sweagent/agent/history_processors.py | yes |
| 5 | **OpenAI Responses/Chat** (official docs) | "OpenAI caches the model's full rendered context including OpenAI-provided instructions, developer messages, tool definitions, and conversation history". Mechanism: "Prompt caching preserves that state for a reusable **prefix**: the unchanged tokens at the beginning of a prompt"; "Cache reuse requires the entire rendered prefix to match. If content or a relevant setting changes before a breakpoint, the prefix after that change cannot match the existing cache entry." | Cache **hit** is all-or-nothing on *rendered* prefix. Documented prefix-affecting settings: `model`; `tools` — "Changes tool names, descriptions, schemas, **ordering**, or tool-specific instructions"; `parallel_tool_calls`. | https://developers.openai.com/api/docs/guides/prompt-caching | yes |
| 6 | **LangGraph** (official docs) | Developer-authored system prompt + `MessagesState`; the documented call node is `model.invoke(state["messages"])`, with state persisted by a checkpointer (`InMemorySaver`, `PostgresSaver`) keyed on `thread_id`. | **No.** The framework does not rewrite earlier messages; the list grows by append. Compaction is not in the default loop — it is a node the developer adds. | https://docs.langchain.com/oss/python/langgraph/add-memory | yes |
| 7 | **Prompt Cache** (Gim et al., MLSys 2024) | Serving-side: "Many input prompts have overlapping text segments, such as system messages, prompt templates, and documents provided for context… precomputing and storing the attention states of these frequently occurring text segments". Requires "a schema to explicitly define such reusable text segments, called prompt modules… The schema ensures positional accuracy during attention state reuse". Reports 8× (GPU) to 60× (CPU) TTFT improvement. | n/a (engine-level, not harness-level) | https://arxiv.org/abs/2311.04934 | yes |
| 8 | **"Agents All the Way Down"** (Alier Forment et al., arXiv 2606.11869, 10 Jun 2026) | States as a *precondition* for building a custom agent: "(P1) Substrate, the LLM as a software component, framed as **tools, then system, then messages under prompt-caching**". | No — presented as a fixed construction order. | https://arxiv.org/abs/2606.11869 | yes |
| 9 | **OpenHands / OpenDevin** | **UNVERIFIED.** Not established. | UNVERIFIED | https://github.com/OpenHands/OpenHands (prompts path returned 404 on `main`; two searches and two raw fetches failed) | **no** |
| 10 | Cline / Roo Code | **UNVERIFIED.** Not established. Attempted `src/core/prompts/sections/environment.ts` → 404; search returned nothing. | UNVERIFIED | — | **no** |

### 1a. Per-pattern findings (the specific volatile elements asked about)

| Pattern | Finding | Evidence |
|---|---|---|
| **Timestamp / "today's date" / clock** | Found in **no** inspectable harness's prefix. Aider's prompt module contains no date. | Rows 2, 3 |
| **Session id / thread id** | Present in LangGraph, but as a **routing key in config** (`{"configurable": {"thread_id": "1"}}`), **not** injected into prompt text. | Row 6 |
| **Token / step counters** | Found in no inspectable harness's prefix. SWE-agent's step count exists only implicitly as history length. | Row 4 |
| **Current working directory / env snapshot** | Not found in the prefix of Aider or SWE-agent. Aider's repo map is derived from the working tree, but it is rendered as a *content chunk* (file summaries), not as a `cwd` string. | Rows 1, 2, 4 |
| **Tool-list changes** | **The one genuinely dangerous live variable.** OpenAI documents that changing tool names, descriptions, schemas, **ordering**, or tool-specific instructions invalidates the prefix, and `parallel_tool_calls` too. Any harness that enables/disables tools per turn (MCP servers connecting mid-session, mode switches) silently rewrites the front of the prompt. | Row 5 |
| **Dynamic tool results injected into the system prompt** | Found only in the **negative**: SWE-agent appends observations as history messages and can only shorten them by rewriting history (which it admits breaks caching); LangGraph appends. No harness inspected re-injects tool output into its system message. | Rows 4, 6 |
| **Model-name string in prompt** | Not found. Model identity is a request parameter, not prompt text — relevant because the *request* field alone (`model`) changes cache identity. | Row 5 |

### 1b. Do harnesses re-send full history or compact? (§Q3)

- **Aider:** no compaction of history; the *repo map* is the token-budget control (`--map-tokens`). History is append-only. (Row 3: caching doc lists exactly the four stable blocks it protects.)
- **LangGraph:** append-only `MessagesState` in a checkpointer; compaction is opt-in, not default. (Row 6)
- **SWE-agent:** ships **truncation/elision** as a first-class, paper-default history processor (`LastNObservations`, n=5), with a `polling` knob whose stated purpose is to reduce cache invalidation. (Row 4)
- **Summarisation-based compaction** ("condense history into a summary message") was **not verified** in this pass for any named harness — the closest verified artefact is SWE-agent's *elision*, which is truncation, not summarisation. Treat "the incumbent summarises" as **UNVERIFIED** until a doc is fetched.

**Consequence for our compaction arm:** elision-based compaction is real and is on by default in at least one research-lineage harness (SWE-agent). Summarisation-based compaction is plausible but unverified. Either way, the mechanism that matters is identical and is self-documented by SWE-agent: **any processor that rewrites earlier messages destroys the cacheable prefix.**

---

## 2. BASELINE SPEC WE RECOMMEND

> ### Recommended: **(a) static prefix + append-only history** — as the *single* headline baseline.
> Report **(b) static prefix + periodic compaction** as a mandatory second arm, and **(c) dynamic state in prefix** only as a clearly-labelled sensitivity bound, never as the comparator.

Rationale, in one line: **(a) is simultaneously the strongest case for the incumbent and the behaviour the majority of inspectable harnesses actually exhibit**, so a win against (a) is immune to the strawman objection, while (b)/(c) are *events* that can only reduce the incumbent's cache reuse, i.e. they are strictly weaker comparators.

### 2.1 The renderer the experiment must call `baseline`

Implement exactly this message-array construction, in this order:

| Segment | Content | Class | Mutability |
|---|---|---|---|
| `S1` | Invariant preamble: role, standing instructions, output-format contract, invariants list | **static** | frozen for the life of the session; rendered once into a byte buffer |
| `S2` | Tool definitions: names, descriptions, JSON schemas, **and their order** | **static** | frozen at session start. A tool-set change is a **session-boundary event**, never an in-session edit (OpenAI: tool names/descriptions/schemas/ordering all affect the prefix) |
| `S3` | Task charter / instance statement (the "what we are doing") | **static per-session** | written once at session start, never re-worded mid-session |
| `H` | History: the full list of prior `(role, content)` deltas | **append-only** | prior elements are **never rewritten, re-ordered, re-indented, or re-summarised** between compaction events |
| `D_t` | The new turn's delta: new user/tool content **plus all volatile state** (cwd, date/time, step index, token counters, session id, model name, env snapshot, last tool result, active mode) | **volatile — lives here** | values may change every turn; their *position* never does |

**Non-negotiables for the experiment (each is a fairness control):**

1. **No volatile value in `S1`–`S3`.** Dates, clocks, step counters, cwd, session ids and env snapshots go in `D_t`, after the last cache breakpoint. This is the *only* structural difference between `baseline` and the pointer renderer, and it is a placement rule, not an information rule.
2. **Byte-identical re-serialisation.** The baseline must re-emit `S1`–`S3` and all of `H` from a frozen byte buffer (or a deterministic serialiser proven byte-stable), not re-render them through a template on every turn. Whitespace, key order, and float formatting are part of the prefix.
3. **Explicit cache breakpoints** at (i) end of `S2`/`S3`, and (ii) end of the previous delta — the same pattern Aider and SWE-agent use (`cache_control: {"type":"ephemeral"}`). Compare like with like: give the baseline the breakpoints it already gives itself.
4. **Equal information.** `baseline` and the pointer renderer must carry the **same multiset of tokens** for a given turn; only *placement/ordering* differs. If the pointer design adds a pointer block, its tokens count against it.
5. **Identical TTL policy.** Same provider TTL, same keepalive policy (Aider pings every 5 min to defeat the default 5-minute expiry). A cache-reuse win that exists only because one arm kept its cache warm is an artefact.
6. **Compaction is an event, not a smoothing.** In arm (b), record every compaction as a forced cache-miss and report hit rate over the *whole* session including resets. Never average it away.
7. **Same session lengths** across arms (number of turns and total tokens), and report per-turn cache-hit tokens as well as the aggregate — an aggregate hides exactly the discontinuity under study.

### 2.2 Justification by ≥3 independently verified sources

1. **Aider, code + docs (rows 1–3):** a shipping harness already engineers `system → readonly_files → repo → chat_files` with explicit `cache_control` breakpoints and keepalive pings. ⇒ The static-prefix-plus-append design is not our invention; it is the incumbent's own best practice, so it must be the comparator.
2. **OpenAI official docs (row 5):** cache reuse "requires the entire rendered prefix to match", and tool definitions/ordering are part of that prefix. ⇒ `S2` must be frozen and ordered deterministically, and any harness that mutates tools mid-session loses the prefix — which is a *tool-lifecycle* cost, not a *renderer* cost, and must not be smuggled into the comparison.
3. **SWE-agent, code + docstring (row 4):** appending is cache-friendly; rewriting earlier messages is self-documented as breaking the cache, with a `polling` knob added purely to reduce it. ⇒ append-only is the incumbent's cache-optimal mode, and compaction is the mechanism that costs it the prefix. This is exactly the (a)→(b) axis, verified from the harness author's own words.
4. **LangGraph docs (row 6):** default state handling is an append-only message list; no automatic rewrite. ⇒ (a) is the *default* behaviour of a major framework, not a contrived arm.
5. **Prompt Cache, MLSys 2024 (row 7):** stable segments are worth precomputing, and reusing them *out of order* needs an explicit schema for "positional accuracy". ⇒ a pure prefix discipline needs no schema; that is the honest technical distinction our renderer claims.

---

## 3. STRAWMAN RISK

**Strongest form of the objection.**

> "No real agent rewrites its system prompt every turn, and you did not need to look far to know it — Aider's `chat_chunks.py` exists *specifically* to keep a cacheable front: fixed order `system → readonly_files → repo → chat_files`, `cache_control` breakpoints placed by hand, and `--cache-keepalive-pings` to stop the 5-minute TTL from eating the cache. OpenAI documents that the prefix must match exactly, so any harness author who read the docs has already frozen their prefix. Your 'typical agent renderer' with dynamic state in the prefix is therefore a **fiction you built to lose**, and the measured gain is the distance to a strawman, not a property of pointer-based context. Fix the comparator or withdraw the claim."

**The single sentence that answers it.**

> We do not compare against a rewritten system prompt: the comparator is the incumbent's own cache-optimal renderer — Aider's fixed order with explicit `cache_control` breakpoints and keepalive, i.e. a frozen prefix and an append-only tail (`aider/coders/chat_chunks.py`, `aider.chat/docs/usage/caching.html`) — so the incumbent is granted every prefix-stability trick it already ships, and the only variable we move is whether post-prefix state is re-rendered in place or appended as a delta.

Evidence backing that sentence: row 1 (chunk order + `add_cache_control_headers`), row 3 (docs: the four blocks it caches; 5-minute TTL; keepalive), row 5 (prefix must match exactly — which is *why* the comparator is fair when the prefix is frozen).

**Residual risk we must still disclose.** Even with a fair comparator, arm (c) would lose for a trivial reason (prefix mismatch), so a result reported *only* against (c) is unpublishable. State explicitly in the paper: (c) is a sensitivity bound demonstrating the *cost of state placement*, and the headline number is `pointer − (a)`.

---

## 4. NOVELTY CHECK

**Has anyone published a quantified prefix-churn measurement for named agent harnesses?** **No such work was found in this pass.** Nearest prior art, in decreasing order of threat:

| Work | What it already claims | Threat to us | How we must scope |
|---|---|---|---|
| **Prompt Cache**, Gim et al., MLSys 2024 — arXiv:2311.04934 | Stable segments ("prompt modules": system messages, prompt templates, documents) should be precomputed and reused across prompts; a schema is needed to keep positional accuracy when modules are placed out of order; 8×–60× TTFT gains. | **High for the idea, not for the measurement.** "Put the stable part first and reuse it" is published, dated, peer-reviewed. | We may **not** claim stable-prefix-first as novel. Our delta is *renderer-induced* placement at the harness layer with a controlled equal-information comparator and a measured cache-hit curve, not module reuse in the serving engine. |
| **"Agents All the Way Down"**, arXiv 2606.11869 (10 Jun 2026) | Lists as a build precondition: "the LLM as a software component, framed as **tools, then system, then messages under prompt-caching**". | **Medium.** The ordering discipline is already stated as practice in print. | Cite it as evidence the design principle is established practice; do not present the ordering rule as our finding. |
| **Aider / SWE-agent source comments** (rows 1, 4) | Practitioners already reason explicitly about cache invalidation (`polling` knob "useful for caching"; keepalive pings). | **Medium.** Shows the phenomenon is known to engineers. | Our contribution is to *quantify* it, not to discover it. |
| Quantified byte-stability / prefix-churn rate of real harnesses (e.g. "% of prompt bytes identical turn-over-turn for Claude Code vs Aider") | Not found. Searches for prefix-churn / byte-stable-prefix measurement returned only serving-side retention work (e.g. arXiv:2610.02766, prefix-retention timeouts over Mooncake traces) and unrelated hits. | — | **This gap is where our claim can live** — scoped to *renderer design*, with named baselines and released traces. |

**Scoping sentence we must adopt.** "Prior work establishes that stable prompt segments are cacheable and that ordering them first is good practice (Prompt Cache, MLSys 2024; arXiv:2606.11869). We do not claim that. We claim the first *controlled measurement* of how much cacheable prefix a **renderer** — not a serving engine — preserves across turns, against the incumbent's own cache-optimal layout, with equal information in both arms."

**Do not claim:** "we are first to notice prompt caching matters for agents"; "harnesses rewrite their system prompt every turn" (evidence points the other way); "compaction is universal" (verified only for SWE-agent's elision).

---

## 5. Gaps, and what is UNVERIFIED

- **OpenHands / OpenDevin:** attempted 2 searches + 2 raw fetches (`All-Hands-AI/OpenHands` and `OpenHands/OpenHands`, path `openhands/agenthub/codeact_agent/prompts/system_prompt.j2`) — all failed. Its prefix contents and volatility are **UNVERIFIED**. Do not put an OpenHands row in the paper without a fetched source.
- **Cline / Roo Code:** `src/core/prompts/sections/environment.ts` → 404; one search returned nothing. Their `environment_details` behaviour (widely believed to carry cwd/clock in the *appended* turn) is **UNVERIFIED**. If it verifies, it *helps* us: it is an incumbent that already puts volatile state in the delta.
- **OpenAI Agents SDK, AutoGen/AgentChat, CrewAI, Continue.dev:** not inspected (budget). No claims made.
- **Summarisation-based compaction:** not verified for any named harness. Only truncation/elision (SWE-agent) is verified.
- **Not measured here:** actual byte-stability percentages for any harness. This unit establishes *what is in the prefix and what mutates*, not *how much*. The churn number is the experiment's job — and per §4, that number is our novelty, so it must be measured, not asserted.

---

## 6. One-line answer for the parent

**Baseline = (a) static prefix + append-only history, justified by 5 independent verified sources; biggest risk is that Aider already ships a cache-optimal prefix, so the incumbent must be given its own `cache_control` layout and keepalive; novelty survives only if scoped against Prompt Cache (MLSys 2024) as a renderer-level *measurement*, since no published work quantifies harness prefix churn.**
