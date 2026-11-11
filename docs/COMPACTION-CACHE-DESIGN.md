# Compaction and cache design — pin the small set, drop the bulk, never summarise

**Status:** design + pre-registration. **No live run has been made under this design.** Every number
below is either measured in this workspace (with the command that produced it) or marked
`[INFERENCE]`. The pre-registered A/B is `experiments/ptr-engine/research-seed-concepts/PREREG-COMPACTION.md`
(E7).

**Supersedes nothing.** It extends the SPCC programme (`PREREG-SPCC.md`) with a compaction-specific
design; E1–E6 keep their predictions unedited.

---

## 1. The question

The operator's framing, which this document tests rather than assumes:

> We lose to compaction no matter what. Make compaction cheaper. A lesser reduction that works 100 %
> is better than a much harder reduction that spends more tokens re-injecting what it already had.

Three sub-questions:

1. **What does a fold actually cost?** Prefix re-prefill, lost information, or the re-fetch that lost
   information causes?
2. **What should survive a fold, and at what price?** Pinned memory/knowledge, agent-authored notes
   (warnings, blockers), or a summary of the journal?
3. **How should the prompt be structured** so that a fold is cheap and a pin is cheap?

---

## 2. What was measured before designing

All commands run in `/home/zer0null/research extractor` on 2026-11-11, offline, 0 requests.

**Unit caveat, stated once and binding on every number in §2.1–§2.3.** The compiler's own
`_layer_tokens` (`experiments/ptr-engine/ptr_engine/layers.py:144-145`) is `len(text.split())` — a
**whitespace word count, not tokenizer tokens**. Every figure in §2.1–§2.3 is therefore in *layer
units*, and a real tokenizer would put them ~1.3× higher. The **ratios** (0.05 %, 6.38 %, 187.6 %) are
unaffected, because numerator and denominator are the same measure. §2.4's figures are different: they
are `prompt_tokens`/`completion_tokens` read from the API's own response, so those are real tokens.

### 2.1 The current fold rewrites the cached prefix

`experiments/ptr-engine/ptr_engine/layers.py:247-257` drops the journal and appends the marker to
`state.index_lines`, which is **L1 — inside the hashed prefix** (`prefix_text = "\n\n".join([l0, l1])`,
`:282-283`). Driving the real compiler for 50 turns at `COMPACT_EVERY = 24`:

```
prefix breaks at turns: [24, 48]
compactions: 2   final epoch: 2
turn 23: L1=0  L2=92  prompt=2971 chars  prefix_sha=79020676
turn 24: L1=7  L2=0   prompt=1052 chars  prefix_sha=bfb2e6ef
```

So every fold changes `prefix_sha256`. **But the re-prefill it forces is tiny**, because the post-fold
prompt is small: over 100 turns with a 1,515-token L0, the four folds re-prefill **86 tokens in total —
0.05 % of the 156,390 prompt tokens sent**. The design does **not** try to reduce that 86: it keeps the
fold record in the prefix (in PINS) because the record must persist on every later turn, and an
append-only record extends the cached prefix instead of rewriting it.

**Conclusion 1: the prefix rewrite is not the cost of compaction.** Any design that optimises only the
prefix break is optimising 0.05 %.

### 2.2 The token saving of dropping the journal shrinks as the fixed prefix grows

Same compiler, 100 turns, `COMPACT_EVERY = 24`, ~50-token journal lines, comparing no-compaction
against drop-only:

| L0 (system + tool schema) | no-compact | drop-only | drop saving | drop saving % |
|---:|---:|---:|---:|---:|
| 1,515 tok | 167,050 | 156,390 | 10,660 | **6.38 %** |
| 6,060 tok | 617,050 | 606,390 | 10,660 | **1.73 %** |
| 12,120 tok | 1,217,050 | 1,206,390 | 10,660 | **0.88 %** |

The absolute saving is constant (it is the journal), so its *share* collapses as the fixed prefix
grows. A real coding agent's system prompt plus tool schema is 5–20 k tokens.

**Conclusion 2: compaction is a window-management tool, not a cost tool.** Its token saving is
1–6 % of the bill and falls toward zero as the agent gets more capable.

### 2.3 Pinning costs more tokens than compaction saves — at a billed cache price

Adding a 200-token pinned block for 100 turns costs **20,000 token-turns**, which is **187.6 %** of the
10,660-token saving from dropping the journal — at every L0 scale.

**But that figure assumes a cache-read price of 0.1×, and this endpoint's cache read is free.** The
repo's own billing model says so: `billed_of` at `experiments/ptr-engine/longrun/score_longrun.py:144-190`
computes `billed_tokens = prompt_tokens − cached_tokens`, i.e. **a cached token is billed at zero**.
Measured over the 300 rows of `rows-e2-turnover-2026-11-10.jsonl`:

| Quantity | Sum over 300 rows |
|---|---:|
| `prompt_tokens` | 476,697 |
| `cached_tokens` | 431,680 (**90.6 %**) |
| `billed_tokens` | **44,426** (9.3 % of prompt) |
| `completion_tokens` | 2,142 |

So at `c = 0` a pin that lives in the cached prefix costs **zero marginal billed tokens**; its only cost
is the one-time prefill when it is first appended, plus the re-prefill of the suffix behind it at that
moment. §2.1 measured that re-prefill at 86 units over 100 turns.

**Conclusion 3 (corrected): pinning is free on this endpoint and cheap on a billed one.** At `c = 0` it
costs 0 units against a re-fetch's 1,627. At `c = 0.1` it costs 480 against the same 1,627. The
conclusion is **invariant across the whole plausible `c` range** — which is a stronger claim than the
one this section originally made, and it is the one the evidence supports.

### 2.4 What a re-fetch costs

From `experiments/ptr-engine/measure/rows-longrun-v5-tools.jsonl` (72 rows, 68 with tool calls, 24
`tool-followup` rows):

| Field | Value |
|---|---|
| mean `prompt_tokens` on tool rows | **5,448** |
| mean `completion_tokens` on tool rows | **179** |
| tool-followup rows | 24 of 72 |

From `rows-e2-turnover-2026-11-10.jsonl` (300 rows, tool-free): mean prompt **1,589** tokens, cached
fraction **0.9056**.

So one re-fetch is **one extra request** at ~5.4 k prompt tokens (≈90 % cached) plus ~180 output
tokens. In full-price token-equivalents at `c = 0.1`, `o = 3`:

```
re-fetch ≈ 0.1 × 4,900 + 1.0 × 550 + 3 × 179 ≈ 1,627 units
pin 200 tok for 24 turns ≈ 0.1 × 200 × 24 = 480 units
```

**Conclusion 4: pinning pays if it prevents one re-fetch per fold interval, with ~3.4× margin.**
That is the break-even rule, and it is the only justification for a pin.

### 2.5 How much of the tool traffic is already redundant

The same file, counted by `(path, start_line, end_line)` over all 290 tool calls in its 68 tool-call
rows:

| Quantity | Value |
|---|---:|
| tool calls | **290** |
| distinct `(path, start, end)` ranges | **88** |
| **re-fetches** (a range already fetched earlier in the cell) | **202 (69.7 %)** |

The five most-repeated ranges:

| Range | Fetches |
|---|---:|
| `ptr_engine/errors.py:114-126` | **22** |
| `ptr_engine/resolve.py:200-2785` | **20** |
| `ptr_engine/resolve.py:66-110` | **18** |
| `ptr_engine/resolve.py:66-130` | **17** |
| `ptr_engine/errors.py:126-200` | **10** |

**Conclusion 5: 70 % of this cell's tool calls re-read a range it had already read.** At ~1,627 units
per re-fetch, 202 re-fetches is ~328,000 units — against a pin set that costs **0 units at `c = 0`**.
A pin holding `errors.py:114-126` (13 lines) would have had 21 of those 22 fetches to prevent.

**What this does not prove.** It does not prove a pin *would* have prevented them: the agent may have
re-read for a reason a pin cannot serve (a changed file, a different question about the same lines).
It establishes the **magnitude of the opportunity**, which is what makes E7 worth 1,000 requests. The
`refetch_count` metric in E7 is what turns this into a causal claim.

**And the arm that produced this data cannot yet run the design.** All 72 rows of
`rows-longrun-v5-tools.jsonl` are `arm: pointer-stable`. `run_longrun.py:3919` services tool calls only
for arms **not in** `(arm_cd.ARM_C, arm_cd.ARM_D, arm_cd.ARM_SPCC)`, so **`spcc` — the only arm that
renders through `compile_prompt` — does not service tool calls today**. Arms B and C are `spcc`
variants, so E7 cannot measure `refetch_count` until `spcc` gains the tool channel. That is
`PREREG-COMPACTION.md` instrument requirement 9, and it is the one that would have wasted stage 1.

---

## 3. The reframing

| | What it is | What it costs | What it is for |
|---|---|---|---|
| **Compaction** | dropping the journal | the re-fetch of anything still needed | staying under the window |
| **Pinning** | keeping a small set verbatim | cache-read tokens every turn | avoiding the re-fetch |
| **Summarising** | an LLM call that rewrites the journal into the prefix | a full prompt read + output + a prefix rewrite + lossy | nothing this design can justify |

The operator's intuition is correct and now has a mechanism: a *harder* reduction (summarise) adds an
LLM call and a prefix rewrite, and still loses detail that must be re-fetched. A *lesser* reduction
(drop the journal, keep the pins) costs almost nothing and loses nothing that matters.

---

## 3.5 Prior art, and what it changes here

Researched 2026-11-11 from primary sources. Each row states what it changes in this design, not just
what it says.

### Cache mechanics that constrain any design

| Source | Fact | Consequence here |
|---|---|---|
| [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) | write 1.25× (5 m) / 2× (1 h), read **0.1×** (0.025–0.05× on newest models); minimum cacheable prefix 512/1024/2048/4096 tokens; hash order **tools → system → messages**; 20-block lookback window | A pin must sit **after** tools+system and **before** messages, or it is not cacheable at all. A prefix shorter than the model's minimum is never cached — a 1.5 k-token prompt on a 4 k-minimum model gets no cache benefit, which is another reason §2.2's saving is illusory. |
| [Anthropic context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing) | tool-result clearing with `clear_at_least`; **clearing invalidates cached prefixes**, and the minimum-clear threshold exists precisely because of that | Confirms the design's rule: never clear from the middle. Clear only the tail (the journal), and only at a fold. |
| [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) | automatic; 1,024-token minimum; 128-token rounding for reporting; 1.25×/2.5× write, 0.1× read; 2,048-token breakpoint spacing pre-5.6; **explicitly states compaction may reduce cache reuse yet still save money** | The vendor itself concedes the tradeoff this design measures. It is a reason to measure both sides, not to assume either. |
| [SGLang HiCache](https://docs.sglang.io/docs/advanced_features/hicache_design.md) | L1/L2/L3 tiers; HiRadixTree splits a node on a mid-node match; page-granular matching when `page_size > 1`; L2 is node-local, never shared | On this endpoint the radix cache is the reason `c = 0` (§2.3). A mid-node match still costs a split, so an append is cheaper than an insert. |
| [SGLang server args](https://docs.sglang.io/docs/advanced_features/server_arguments.md) | `--enable-cache-report` **default False**; it is what populates `usage.prompt_tokens_details` | **Verified live**: 298 of 300 rows in `rows-e2-turnover-2026-11-10.jsonl` carry `cached_reported=True` with `cached_source='prompt_tokens_details'`, so the flag is on for the current server. The instrument requirement is satisfied, not pending. |
| [vLLM prefix caching](https://docs.vllm.ai/en/latest/design/prefix_caching.html) | hash-chained block cache; **only full blocks are cached**; 16-token blocks; LRU free-queue eviction; `cache_salt` | A pin smaller than one block may not be cached at all. Pins should be batched to at least a block, which the design's "batch at fold boundaries" rule already does. |

### Designs that already do this

| Source | Design | What this design takes |
|---|---|---|
| [Manus: context engineering](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) | KV-cache hit rate as the **top production metric**; 100:1 input:output ratio; append-only + deterministic serialization; **mask, don't remove**; restorable compression; keep-the-wrong-stuff-in; recitation | The append-only rule and the "mask, don't remove" rule are the same rule as §5.1's tombstone. Recitation is a pin the agent re-reads — the design's `fact` kind. |
| [opencode-cache-compact](https://github.com/lennartschoch/opencode-cache-compact) | **append-then-cut**: summarise by appending a user turn, rewrite only the outgoing view, resume; threshold 68 %; `summaryMaxTokens` 1200; never touches the on-disk session | The "rewrite only the outgoing view" rule is exactly §5.3's "the fold only changes the outgoing view". The 68 % threshold is the design's 70–80 % window-pressure trigger, independently arrived at. |
| [Anthropic: effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Claude Code's compaction field list: **architectural decisions, unresolved bugs, implementation details, the five most recently accessed files**; warns aggressive compaction loses subtle context; tool-result clearing is the safest, lightest touch | This is a **published pin set**. The design's kinds map onto it: `decision` ← architectural decisions, `blocker` ← unresolved bugs, `fact` ← implementation details, and a `ref` pin for the recently-accessed files. Adopt it as the default seed pin set. |

### The breakeven formula

The report derives, for a billed provider:

```
n ≈ (write_multiplier × retained_prefix_tokens) / (0.1 × cleared_tokens)  ≈  12.5 × S / X
```

Clearing 30 k tokens while retaining a 40 k prefix needs **~17 turns** to pay back. This is a better
formula than §6's ad-hoc arithmetic because it accounts for the **write** multiplier, which §6 ignores.
It is adopted into §6 below, and it makes the same point more sharply: a fold that clears little while
retaining a lot **never** pays back.

### Counter-evidence, recorded because it constrains the claim

| Finding | Why it matters |
|---|---|
| Observation masking has an **inverted-U** regime map — it collapses on saturated models | The design must not claim masking is universally safe. E7's arms do not include masking; that is a deliberate omission, and it is a limitation. |
| Frontier selectors hit 96/96 on retrieval, but **structured writers do not** | A "structured brief" is not automatically better than free text. The design's pin format is deliberately flat (`P7|kind|text`), not a schema. |
| **Tombstone removal gives 16/16 replay failures** | Direct support for §5.1's append-only + tombstone rule. Removing a line from the prefix is not a neutral edit. |
| **27 compaction summaries contained self-injected instructions** | The strongest argument for "never summarise" — and it is a **safety** argument, not a cost one. A summary is an LLM writing into the trusted prefix; a pin is the agent writing a line it can be held to. |

---

## 4. The cost model

The endpoint is local (`http://192.168.2.168:8012/v1`, `occamy-1.0`, `max_model_len` 131,072, SGLang),
so dollars are not the measure. Cost is reported in **normalised units** with the multipliers stated,
and every ranking is re-checked at the sensitivity bounds:

```
cost_units = billed_in × 1.0 + cached_in × c + out × o
c ∈ {0.00, 0.10, 0.25}      # cache-read price; 0.00 is THIS endpoint (measured, §2.3)
o ∈ {1, 3, 5}               # output multiplier
```

`c = 0.00` is not a modelling choice — it is what `billed_of`
(`experiments/ptr-engine/longrun/score_longrun.py:144-190`) already computes, and what the 300-row
measurement in §2.3 confirms. `c = 0.10` is the Anthropic/OpenAI cache-read multiplier, used as the
portability case; `c = 0.25` is a pessimistic bound.

**The ranking is invariant across that grid** (§2.3): pinning beats a re-fetch at every `c` from 0 to
0.25. A result that flips inside the grid is reported as **not robust**, not as a win.

Per cell, report: `prompt_tokens`, `cached_tokens`, `billed_tokens`, `uncached_tokens`,
`completion_tokens`, `cost_units` at each `(c, o)`, `compactions`, `prefix_breaks`, `reprefill_tokens`,
`refetch_count`, `checkpoint_accuracy`, and `cost_units_per_verified_success`.

Use the repo's own field names, not invented ones: `cached_fraction_of_prompt` and
`cached_fraction_of_accounted` from `billing_block` (`score_longrun.py:192-315`). There is **no** field
named `cached_fraction`; a test asserts its absence.

`ABSENT ≠ 0`: an unreported `cached_tokens` is `null` and makes the cost an **upper bound**, never a
zero. `billed_of` already enforces this — a null cache counter past turn 1 yields
`(None, "unknown")`, and 1 of the 300 rows is in exactly that state.

---

## 5. The design

### 5.1 Layer order by volatility

Cache hits are prefix matches: the first byte that changes ends the hit. So layers are ordered
**most stable first**, and the only layer a fold may touch is the last one before the tail.

The names below are the **code's** names (`experiments/ptr-engine/ptr_engine/layers.py:270-284`), with
one new layer inserted. The current compiler renders `layers = [l0, l1, l2, l3, l4]` and hashes
`prefix_text = "\n\n".join([l0, l1])`.

| Layer | Code name | Content | Mutability | In the cached prefix? |
|---|---|---|---|---|
| **L0** | `_l0_text(run)` | system prompt, tool schema, answer grammar | **immutable within a run** (`PtrPrefixDrift` guards it) | yes |
| **PINS** *(new)* | `st.pins` | memory/knowledge injections, agent notes, retired-pin tombstones, **the fold record** | **append-only** | yes |
| **L1** | `st.index_lines` | world-index refs, one line per addressable ref | **append-only** (a dead ref is tombstoned, never removed) | yes |
| **L2** | `st.journal` | one line per prior turn | **droppable** — the only layer a fold removes | no (tail) |
| **L3** | `work` | this turn's question, deliveries, fetches | per-turn | no |
| **L4** | `contract_line` | the answer contract for this turn | per-turn | no |

Three changes from the current compiler:

1. **A `PINS` layer is inserted between L0 and L1**, rendered as its own block, and `prefix_text`
   becomes `"\n\n".join([l0, pins, l1])`. It is a new key in `layer_tokens`, so
   `experiments/ptr-engine/longrun/tests/test_spcc_arm.py:118` — which asserts
   `set(lt) == {"L0","L1","L2","L3","L4"}` — must be updated to
   `{"L0","PINS","L1","L2","L3","L4"}`. That is a deliberate contract change, not a test weakening:
   the test pins the layer set, and the layer set is what is changing.
2. **The fold record moves from L1 to PINS, as a pin.** It is a durable fact about the conversation
   ("24 turns were dropped at epoch 1"), so it belongs with the other durable facts — and it must
   **persist on every turn after the fold**, not only on the fold turn. Writing it to L3 (`work`) would
   make fold-awareness vanish on turn 25, which is worse than today's behaviour. Writing it to PINS
   keeps it visible every turn *and* keeps it append-only, so it extends the cached prefix instead of
   rewriting it. The line is `P<n>|fold|T24: 24 turns dropped at epoch 1`.
3. **PINS and L1 are append-only.** A pin is appended; a retired pin gets a tombstone line
   (`P7|retired|T31 superseded by P9`), never a rewrite. An index ref that dies is tombstoned the same
   way. This is what makes the prefix *extend* rather than *change* — an extension is a cache hit up to
   the old length; a change is a re-prefill of everything after it. (`_sort_index_lines` at
   `layers.py:148-157` already puts non-`@` lines last, so today's marker append also extends L1 rather
   than rewriting it; the change is about **persistence and semantics**, not about the sort.)

`prefix_sha256` is computed over `L0+PINS+L1` and must be **stable within an epoch**; the only
permitted change is a fold, and a fold no longer touches it. `PtrPrefixDrift` keeps guarding L0.

**Note on the size of this change.** §2.1 measured the re-prefill it saves at 70 of 86 tokens over 100
turns. The change is worth making because it is nearly free and it removes a class of bug (a fold that
silently invalidates the prefix), **not** because it saves tokens. The token argument for this design
is §2.4, the re-fetch.

**The edit surface, verified by reading the code (four touch points):**

1. `CompactionState` (`experiments/ptr-engine/ptr_engine/layers.py:36`) gains `pins: List[str] = []`.
2. `compile_prompt` (`layers.py:169-330`) renders `pins` as its own block between `l0` and `l1`, and
   `prefix_text` becomes `"\n\n".join([l0, pins, l1])`; `layer_tokens` gains a `"PINS"` key.
3. The fold block (`layers.py:247-257`) appends `P<n>|fold|T<t>: <n> turns dropped at epoch <e>` to
   `st.pins` instead of appending the marker to `st.index_lines`.
4. `SpccArmState` (`experiments/ptr-engine/longrun/arm_cd.py:481-565`) gains `pin(kind, text)`,
   `retire(id, reason)` and `pins()`, each appending to `self.state.pins`. Its `__init__` already
   constructs `CompactionState(index_lines=..., compact_every=...)`, so the new field needs no
   constructor change beyond the default.

No other call site reads `index_lines` for the marker, and `spcc_world_index` builds L1 independently,
so the change does not disturb the world index.

**Render the `PINS` block only when it is non-empty.** `"\n\n".join([l0, "", l1])` would insert a
double separator and change the prefix bytes for every arm, including arm A, which has no pins. That
would mint a new prefix generation and make E7's arm A incomparable with the existing `spcc` rows.
Omitting an empty block keeps arm A **byte-identical to today**, so the control is a true control and
`test_prefix_stability` (`tests/test_layers_compiler.py:59-77`, which asserts
`len(set(prefixes)) == 1` across turns 1–24) passes unchanged.

### 5.2 The pin model

A pin is a line in the **PINS** layer with a stable id, a kind, and text that is **never summarised and
never rewritten**:

```
P7|blocker|the ledger tool exits 4 over the 4,320 default cap; do not regenerate REQUEST-LEDGER.json
P8|decision|the fold record is a pin in PINS, not a line in L1, so a fold extends the prefix
P9|fact|TX-03 distances are 2/5/6/8/20/32; d32 is the fixture ceiling
```

| Kind | Written by | Example |
|---|---|---|
| `goal` | operator / harness | the task's acceptance check |
| `decision` | agent | a choice and its reason |
| `constraint` | operator / harness | "never run `git add -A`" |
| `blocker` | agent | "cap gate refuses; awaiting operator" |
| `warning` | agent | "this test rewrites tracked previews" |
| `fact` | agent | a measured value the task depends on |

**API (one call, append-only):**

```
pin(kind, text) -> id          # appends P<n>|kind|text to PINS
retire(id, reason) -> None     # appends a tombstone line; never removes the pin
pins() -> list                 # read back, for the summary and for the handoff
```

**Rules:**

- A pin is **never summarised**. If PINS grows past its budget, pins are **retired explicitly**, with a
  reason, and the retirement is itself a line.
- A pin is **never re-injected per turn** as a separate message. It lives in PINS, which is in the
  cached prefix, so it is read at cache price — which on this endpoint is **zero** (§2.3).
- A pin is **never edited**. A correction is a new pin that names the old one.
- Pins are **batched at fold boundaries** where possible: appending a pin extends the prefix, which is
  cheap, but appending one every turn turns the prefix into a per-turn rewrite.

### 5.3 The fold policy

- **Trigger on window pressure, not on a fixed interval.** Fold when the prompt reaches 70–80 % of the
  model's window, or when the journal exceeds a token budget — whichever comes first. A fixed
  `COMPACT_EVERY = 24` folds a 1,500-token prompt that had no need to fold (measured: 6.38 % saving at
  best, 0.88 % at a realistic prefix).
- **Fold only L2.** L0, PINS and L1 are untouched. The fold record is appended to **PINS** as a pin.
- **Never summarise.** The fold drops the journal and appends `P<n>|fold|T24: 24 turns dropped at
  epoch 1` to PINS. No LLM call, no prefix rewrite, no lossy artefact that later has to be trusted.
  The record persists on every later turn, so the agent always knows history was truncated and how
  much — which is the one thing a fold must never hide.
- **Keep a recovery route.** The full journal stays on disk (the rows file); the fold only changes the
  outgoing view. A pin can reference a journal range (`P10|fact|see T12-T18`) so the agent can re-read
  it deliberately rather than re-fetch it blindly.

### 5.4 What the agent may pin, and when

The agent pins when it learns something it would otherwise have to re-derive:

- a **blocker** it cannot resolve (so it does not retry the same failing command),
- a **decision** and its reason (so it does not relitigate),
- a **warning** about a hazard it discovered (so it does not step on it twice),
- a **fact** the task depends on and that lives outside the window.

The harness pins the **goal** and the **constraints** at turn 1. Memory/knowledge injection is a pin
of kind `fact` written once, not a per-turn message.

**Default seed pin set.** Claude Code's published compaction field list is a pin set that already
exists in production: *architectural decisions, unresolved bugs, implementation details, and the five
most recently accessed files*. Adopt it as the default, mapped onto the kinds above:

```
P1|goal|<the task's acceptance check>
P2|constraint|<the hard constraints that must not be violated>
P3|decision|<architectural decision> — because <reason>
P4|blocker|<unresolved bug or refusal>
P5|fact|<implementation detail the task depends on>
P6|ref|<the five most recently accessed files, as paths>
```

`ref` is a new kind: a pointer, not content. It costs a few tokens and lets the agent re-read
deliberately instead of re-fetching blindly — which is the whole point of §2.4.

---

## 6. Break-even rules (the arithmetic an operator can check)

| Rule | Arithmetic | Source |
|---|---|---|
| **Pin if it prevents ≥ 1 re-fetch per fold interval** | re-fetch ≈ 1,627 units; pin 200 tok × 24 turns = **0 units at `c=0`** (this endpoint), 480 at `c=0.1` | §2.3, §2.4 |
| **The opportunity is large, not marginal** | **202 of 290 tool calls (69.7 %) re-read a range already read**; one range was fetched 22 times | §2.5 |
| **Pinning is free here, cheap on a billed provider** | at `c=0` a cached pin costs nothing; at `c=0.1` it costs 187.6 % of the drop saving but still beats one re-fetch | §2.3 |
| **A fold that clears little while retaining a lot never pays back** | `n ≈ 12.5 × S / X` turns; clearing 30 k while retaining 40 k needs ~17 turns | §3.5 |
| **Do not summarise** | a summary is a full prompt read + output + a prefix rewrite, is lossy, and 27 measured summaries carried self-injected instructions | §3, §3.5 |
| **Fold on window pressure, not on a count** | drop saving is 6.38 % at 1.5 k L0, 0.88 % at 12 k L0 | §2.2 |
| **Keep the fold record append-only and persistent** | a record in PINS extends the prefix; a record in L3 vanishes after the fold turn | §5.1, §5.3 |
| **Batch pins to at least one cache block** | vLLM caches only full 16-token blocks; a sub-block pin may not be cached at all | §3.5 |

---

## 7. The A/B design (summary; full pre-registration in `PREREG-COMPACTION.md`)

Four arms on one tool-enabled fixture, one model, temperature 0, seed 42:

| Arm | Fold | Pins | Summary call |
|---|---|---|---|
| **A `spcc`** (control) | drop journal, record in L1 | none | no |
| **B `pinned-compact`** | drop journal, record in PINS | PINS append-only | no |
| **C `pinned-summary`** | drop journal, record in PINS | PINS append-only | **yes** — journal summarised into PINS |
| **D `no-compact`** | grow until the window forces a FIFO truncation from the front | none | no |

Arm A is the existing `spcc` arm unchanged. Arm D is the existing `transcript-grow` arm, which
"replay[s] the whole history every turn; FIFO-truncate[s] from the [front]" (`run_longrun.py:10`) — so
it is not literally never-compacting: it is the **cost ceiling**, and it truncates only when the window
forces it. Arms B and C are new and must be added to `ARMS` in
`experiments/ptr-engine/longrun/run_longrun.py:74`.

**Primary metric:** `cost_units_per_verified_success` at `(c=0.00, o=3)`, with the sensitivity grid.
**Secondary:** `refetch_count` (tool calls that read material already present in the journal),
`checkpoint_accuracy`, `prefix_breaks`, `reprefill_tokens`, `compactions`.

**Predictions, written before the run:**

1. **B ≤ A on cost** at equal accuracy, because the pins prevent re-fetches and the fold record is
   append-only. The margin is small in tokens (§2.1) and large in re-fetches (§2.4).
2. **C > B on cost** — the summary call plus the prefix rewrite costs more than the pins it replaces.
3. **C ≤ B on accuracy** — a summary is lossy; a pin is not. If C beats B on accuracy, the design's
   "never summarise" rule is wrong and must be revised.
4. **D has the highest prompt tokens and the lowest re-fetch count** — it never loses anything, and it
   is the cost ceiling.
5. **A has the highest re-fetch count** — it loses the journal and keeps nothing.

**Falsifiers:**

- B's `cost_units_per_verified_success` ≥ A's → the pinning design does not pay.
- B's accuracy < A's beyond the measured noise band (±4.2 pp, `PREREG-SPCC.md` §noise floor) → pinning
  costs quality.
- C's accuracy > B's beyond the band → summarising is worth it, and rule 5.3 ("never summarise") is
  falsified.
- `refetch_count` does not differ between A and B → the mechanism is not the one claimed, and the
  result is a token-only comparison that §2.2 already says is 1–6 %.

**Power and budget.** The noise floor is ±2/48 = ±4.2 pp per checkpoint set, so an accuracy claim needs
≥ 4 reps (1,200 requests for 3 arms × 100 turns). A **cost-only** claim needs 1 rep per arm. The
pre-registered run is therefore **two stages**: stage 1, 4 arms × 1 rep = 400 requests, decides the
cost ranking; stage 2, +3 reps on the two surviving arms = 600 requests, decides accuracy. Total
**1,000 requests**, inside the 1,927 headroom but **gated on the 4,320 default-cap decision**
(`docs/STATE.md` §6 item 10).

---

## 8. What this design does not claim

- It does not claim compaction is unnecessary. It claims compaction is **window management**, and that
  its cost is the re-fetch, not the prefill.
- It does not claim pinning is free. It costs 187.6 % of the drop saving in tokens and is justified
  only by re-fetch avoidance.
- It does not claim the numbers in §2 transfer to another engine. They are measured on this compiler
  and this corpus; the cache multipliers are parameters, and the ranking is re-checked at the
  sensitivity bounds.
- It does not claim a summary is never useful. It claims a summary is not justified **as a cost
  measure**, and the A/B is designed to falsify that if it is wrong.
