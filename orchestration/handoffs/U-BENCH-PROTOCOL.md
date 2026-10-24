# U-BENCH-PROTOCOL — Prefix-Cache Taxation in a Hybrid-Attention Serving Stack

**Status:** PROPOSED — pre-registration text, **not yet frozen**. Freezes on the G0 verdict of
§2 (instrument validity). Nothing in this document is a measurement; every number in §5 is
either a *prior observation* (labelled as such, with no protocol attached) or a *prediction*
that has not been run.
**Author:** experimental-design unit `U-BENCH-PROTOCOL`.
**Written:** 2026-10-20, before any Arm A / Arm B run.
**Supersedes:** nothing. On freeze this file is copied verbatim to
`experiments/cache-tax-bench/PREREGISTRATION.md` and **never edited after the first run**;
revisions are dated addenda appended below, original text kept (house convention,
`experiments/second-labeller-190/PREREGISTRATION.md` §preamble).

---

## 0. What this protocol is, and what it is NOT

This protocol measures **one thing**: whether the *partitioning* of an identical token
subsequence — rendered as an invariant prefix plus an appended delta, versus re-rendered whole
every turn — changes the number of **billable (uncached) prompt tokens** the serving stack
charges for, and by how much.

**It is NOT** a claim that state rendering produces better answers. No quality, accuracy or
task-success metric appears in this protocol. Arm A holds the token subsequence fixed by
construction, so any *subsequence*-level quality difference is zero by definition; a
*rendering*-level quality difference is outside this protocol and must be measured separately
if anyone wants it.

**It is NOT** a causal claim about recorded production traffic (Arm B). Arm B is observational
and is reported with its own section-level disclaimer (§4), which travels with every number
it produces.

**It is NOT** a benchmark of SGLang. The stack is an *instrument*, not a subject. Where the
stack's behaviour is used as a prior (§5, P1), the prior is tested by the stack against itself.

### 0.1 Established facts carried in (not re-derived here)

These were measured before this protocol was written. They are **inputs, not results of this
protocol**, and no claim row may cite them as a protocol outcome.

| Fact | Source |
|---|---|
| Serving stack: SGLang on a local hybrid-attention model, 30 of 40 layers linear attention, recurrent state checkpointed every 64 tokens | operator briefing (prior measurement) |
| Only 64-token-aligned boundaries are reusable; the radix tree is prefix-only | operator briefing (prior measurement) |
| Single-request probe, page/chunk 64: an 807-token prompt repeated → 768 cached (95.2 %) | prior probe |
| A 6-token marker inserted at char 2000 → 0/813 cached; the original prompt then reuses 768 again | prior probe |
| PREFIX (451 tok) → PREFIX+INSERT+SUFFIX (827) → 384 cached; same inserted form again → 768; different INSERT value → back to 384 | prior probe |
| Fixed preamble + appended history: 96.2 / 95.0 / 97.4 / 96.2 % across 5 turns. Sliding newest-first window: 98.6 / 95.0 / 95.0 / 95.0 %, never recovers | prior probe |

**The five prior-probe rows above are single-request observations.** They are consistent with
the laws in §5, which is exactly why they must not be used as *evidence for* them. A law
fitted to the observation that motivated it is not a test of that observation. §5 states each
prediction with a numeric point I do not get to choose after seeing the data.

---

## 1. The hypothesis under test

> **H1 (partitioning law).** For a fixed token subsequence rendered at turn *n*, the billable
> (uncached) prompt-token count equals the number of tokens beyond the last reusable 64-aligned
> prefix boundary. Rendering the same subsequence as an *invariant prefix + appended delta*
> therefore costs, per turn, **only the delta rounded up to a 64-boundary** — a quantity that is
> **flat in n** — whereas re-rendering the whole transcript costs a quantity that **grows
> linearly in n**.

H1 is the conjunction of three sub-laws (P1–P3, §5). Each is separately falsifiable and each
has its own kill condition. Killing one does **not** kill the protocol; it kills that
sub-law and is reported as a partial result (house rule: *partial is a result*).

### 1.1 Why this isolates partitioning as the causal variable

This is the load-bearing methodological argument, so it is made explicit rather than asserted.

Let `S_n` be the exact token subsequence (model-input tokens, after chat template) that turn
*n* of a prototype replay must consume. Define two renderings of the **same** `S_n`:

- **(a) state-renderer** — `render_a(n) = P ⊕ δ_n`, where `P` is an invariant prefix (system
  prompt, tool schemas, fixed rubric) and `δ_n` is the appended turn-*n* delta;
- **(b) full re-render** — `render_b(n) = P ⊕ δ_1 ⊕ δ_2 ⊕ … ⊕ δ_n`, the whole transcript,
  re-emitted from scratch.

Both arms transmit a byte stream that tokenises to `S_n` **plus** the same `P` and the same
`δ_1…δ_n` in the same order. The arms differ in exactly one respect: whether the server sees a
request whose *longest reusable prefix* is `P` (arm a) or `P ⊕ δ_1 ⊕ … ⊕ δ_{n−1}` (arm b).

Three design choices make that the **only** differing respect, and each is a control in §6:

1. **Same subsequence, asserted, not assumed.** Every pair (a, b) at turn *n* is checked by
   tokenising both bodies and asserting `tokens(a) == tokens(b)` (Control C5). A pair that
   fails the assertion is a **protocol bug**, not a result, and is excluded and counted.
2. **Same request envelope.** Temperature 0, same `max_tokens`, same `chat_template_kwargs`
   (thinking **off** — see `src/resextract/llm/occamy.py:456-495`; `build_request_body` emits
   the body in a fixed key order), same `tools` **absent** in Arm A (the tool array hashes
   before the system prompt — see Control C4, which is where the tool array is studied).
3. **Between-run isolation.** The prefix cache is flushed between every (arm, depth) cell
   (Control C0), so turn *n* of arm (a) and turn *n* of arm (b) each start from a cold cache and
   the measurement at depth *n* is not contaminated by the depth-*n−1* request of the *other*
   arm.

Given 1–3, the differing quantity is a function of rendering *alone*. That is what licenses the
causal sentence — and it is **only** the causal sentence about the *instrument* (cached token
count), never about output quality.

**What this design cannot settle, stated up front.** Because the arms differ in cache state,
and cache state can change latency, a *timing* difference between arms is confounded with
whatever the stack does differently on a cache hit. TTFT is therefore reported as a **sanity
and magnitude check** (§3.4), never as a mechanism. Any sentence of the form "state rendering
is faster because of caching" is out of scope for this protocol.

---

## 2. Prerequisite gate G0 — instrument validity

**Nothing downstream of G0 may be reported as a result until G0 passes.** This is the first
thing that runs and the only thing that can block the whole protocol.

### 2.1 The uncertainty being gated

The server's per-request cache-hit field may be a **server-reported count** or a **client-side
estimate**. Prior work in the workspace already had to extract this conclusion from a larger
measurement into its own handoff. The distinction matters because the entire protocol measures
billable tokens, and an estimate would be measuring the *estimator*:

- the client's typed `Usage` model (`src/resextract/llm/occamy.py:314-322`) carries
  **`prompt_tokens`, `completion_tokens`, `reasoning_tokens`, `total_tokens` and nothing else** —
  **there is no cached-token field in the typed model at all**;
- `parse_usage` (`src/resextract/llm/occamy.py:524-556`) reads only those shapes;
- so any cached-token number taken through `resextract`'s client would be arriving via
  `raw_usage` (recorded verbatim in `ChatResult.raw_usage`, `:363`) but is **not** modelled, not
  validated, and not metered. A consumer that reads it is reading an unvalidated field.

That is a concrete reason the gate exists and is not paranoia.

### 2.2 G0 probes (all read-only against the server; nothing is written to the repo)

| Probe | What it does | Passes when |
|---|---|---|
| **G0-a** | Flush the prefix cache server-side; send the *same* 807-token prompt twice unchanged, single request each, via a raw HTTP call (not the client). Capture the **raw JSON response bytes**. | The response carries a cached-token field on both calls. |
| **G0-b** | On the second call, check whether the cached field equals a value the server could have computed (768 under page 64) **and** whether a `cached_tokens`-shaped key appears in `usage`, `usage.prompt_tokens_details`, or a SGLang extension path. Record the exact key path. | A key path is identified and reproducible on a second independent day. |
| **G0-c** | Cached value is **monotone in exact prefix**: 300, 700, 900 token prompts, each repeated. | Cached grows in 64-aligned steps matching each prompt's own length (control C2 shape). |
| **G0-d** | Cached value is **sensitive to depth** in the direction law P1 predicts: a 1000-token prompt gives ≤ 1000 − (1000 mod 64 target) cached on first use and ≈ prompt-length cached on second use. | The field moves; it is not a constant or a pass-through of prompt length. |
| **G0-e** | Declare which server version / CLI flags the box runs, and whether the field lives in a server log line, a response header, or the usage object. | Recorded verbatim, with the exact command that produced it. |

### 2.3 G0 verdicts and what each one permits

| Verdict | Condition | What the protocol may then claim |
|---|---|---|
| **V-SERVER** | G0-a…G0-d all pass; field is present, key-path-stable, monotone, depth-sensitive | Full protocol. All three predictions (§5) may be tested and the word *billable* may be used. |
| **V-DERIVED** | Field absent or fails mononoticity, **but** the server emits utilisation/cache counters (e.g. a `/metrics` or `/stats` endpoint, or a log line per request) that reconstruct cached count | Full protocol, with cached count **reconstructed** from the counter, and every claim labelled `RECONSTRUCTED`, with the reconstruction formula and its own test (G0-c repeated against the reconstruction). The response-usage field may not be used. |
| **V-TIMING** | No usable count at all | **Time-only mode**: the protocol runs with the *inference latency* as the quantity, and P1/P2 (which are statements about token counts) are **withdrawn, not tested**. Only P3 (flat vs linear scaling) survives, restated in latency terms, and the manuscript's claim class degrades from "taxation is measurable" to "the shape of per-turn cost differs by rendering". Every figure carries a banner: *cache-hit field unavailable; cost inferred from latency*. |
| **V-FAIL** | Neither count nor latency signal separates the arms | Report as **blocked**, with the exact command output. The protocol does not proceed to Arm A. This is a legitimate terminal outcome and must be recorded as such rather than worked around. |

**G0 is a gate, not a warm-up.** If G0 lands on V-TIMING or V-FAIL, the run stops and the
parent decides; it does not get improvised around.

---

## 3. Arm A — controlled replay

### 3.1 Corpus inventory (what actually exists on disk and can be replayed)

Searched `dockets/`, `experiments/`, `state/`, `repro/`, `docs/`, `templates/`. Pinned by digest
at the time of writing; a re-run must re-pin and record drift.

| id | Path | Bytes / lines | sha256 (16) | Replayable as | Verdict |
|---|---|---|---|---|---|
| **CORP-MAIN** | `experiments/second-labeller-190/cases.json` | 141,703 B / 3,382 lines / **190 cases** | `e8e3e9819c22808e` | Structured multiple-choice cases, **7 kinds**, fields `id, kind, question, options, rationale, namespaces, correct, _line`. ~132.7 k chars ≈ **33 k tokens** total. | **PRIMARY.** Natural per-turn re-render: each turn is one case appended. `correct` is **withheld from the prompt** (the model must not see the label); it is used only for the (out-of-scope) quality check that this protocol does not run. |
| **CORP-LONG** | `dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl` | 866,816 B / **573 lines** | `431605e624ca9059` | 573 structured records, fields `detail, discoveredBy, hash, kind, refs, seq, session, subject, ts`. Sequential `seq`, so a replay prefix is well-defined. | **SECONDARY** — long-context replication (depth sweep beyond 190 turns without repeating cases; 573 turns available). **Not** the primary, because the bytes are a JSONL ledger and are not a natural-language prototype. |
| **CORP-CAND** | `state/mine/live-u21-replay/candidates.jsonl` | 7,190 B / **10 lines** | `973194a166199d2a` | 10 mined candidates, keys `title, summary, evidence_quote, verified_provenance, confidence, kind, query, rationale, graph_nodes, provenance_refs` | **SMOKE ONLY** (10 turns is not a sweep). Also note `state/mine/live-u21-r1/` and `live-u21-r2/candidates.jsonl` are **0 lines** — empty, not replayable. |
| — | `templates/` | — | — | **DIRECTORY ABSENT at the workspace root.** `docs/PLAN.md` §3.1 lists `templates/` (Jinja2: paper, report, …, benchmark_card, memo). No prompt template for the *state renderer* exists on disk to reuse. | **BLOCKER for the renderer as specified** — see §3.2. |

**Corpus selection inside CORP-MAIN.** The 190 cases span 7 kinds, all cases shipped (no
exclusion). Turns are drawn as a **fixed permutation seeded at 20261020** over all 190 ids,
so depth *n* always uses the same first *n* cases in both arms and across repetitions. The
permutation seed and the resulting ordered id list are written to the run record before the
first request.

### 3.2 The two renderers — exact specification

**The state-renderer must be specified as text, not as "whatever the app does", because the
app's emitter does not exist on disk.** (This mirrors B6's recorded failure in
`strategy/PAPER_CANDIDATES.md`:355-360 — "the *emitter* … and no neutral emitter exists on
disk".) This protocol does not repeat that error: it defines the renderer byte-exactly here.

Let `P` be the invariant prefix, fixed for the whole run:

```
[system] You are a research extractor. For each item appended below, answer the question
using exactly one of the listed options. Reply with the option letter only.
[user  ] <item 1 …>
```

- `render_b(n)`: one `system` turn carrying `P`'s system text, then **one `user` turn** carrying
  the concatenation of items `1…n`; the assistant answer for item *n* is requested now.
- `render_a(n)`: the **same** `system` turn, then `user(item 1)`, `assistant(answer 1)`,
  `user(item 2)`, … `user(item n)`. `P` is thus the invariant prefix in both arms; the
  difference is whether items `1…n−1` sit inside a *single* user turn (b) or in *already
  submitted* turns (a).

**Why this is the right operationalisation of "the identical token subsequence".** In both
renderers the concatenated model-input tokens are `P ⊕ item_1 ⊕ … ⊕ item_n` with the same
separators; the only difference is that (b) re-sends the earlier items as one block while (a)
has them as prior turns. The assertion in Control C5 is against the **tokenised concatenation
of item text with a fixed separator**, so a chat-template difference that would silently change
the subsequence is caught rather than assumed away.

> **Honest limitation, recorded before the run.** Chat templates insert role markers, and
> whether `P ⊕ item_1` in arm (a) tokenises identically to the first 1-item block of arm (b)
> depends on the template. If C5 fails on a majority of pairs, **the arms are not
> subsequence-identical** and the protocol must report that as the finding — namely that
> rendering cannot be varied while holding tokens fixed on this template — rather than
> silently proceeding on a weakened claim. This is the single most likely way Arm A dies, and
> it is stated here, not discovered later.

### 3.3 Design grid — what a single "run" is

| Factor | Levels | Fixed by |
|---|---|---|
| Arm | (a) state / (b) full re-render | §3.2 |
| Depth *n* | 1, 2, 4, 8, 16, 32, 64, 128, 190 | corpus permutation §3.1 |
| Repetition *r* | 1, 2, 3 (three repeats per cell) | to expose run-to-run jitter |
| Corpus | CORP-MAIN primary; CORP-LONG for depth > 190 | §3.1 |
| Cache state at cell start | **cold** (flush) | Control C0 |

- A **cell** = (arm, depth *n*, repetition *r*). A cell issues **n requests** (turn 1 … turn n).
- A **run** = one cell, executed end to end, with its own cold cache flush at the start and its
  own run record. Runs are the unit of repetition; cells are the unit of reporting.
- The full primary grid is 2 arms × 9 depths × 3 reps = **54 runs**, **≤ 2 × 3 × 445 = 2,670
  requests** (Σ n over the 9 depths = 445). Every request is temperature 0, thinking off,
  `max_tokens` fixed at 8 (letters only). **No wall-clock dependency is assumed**: if a run is
  interrupted, the cell restarts from its own cold flush and the abandoned partial is recorded,
  not stitched.
- **Bounded cost estimate** is a protocol *input* to be filled by the operator before running;
  it is deliberately not asserted here.

### 3.4 Metrics — exact definitions

Throughout: `c_i` = the server-reported (or reconstructed, per G0 verdict) cached-token count for
request *i*; `p_i` = `prompt_tokens` for request *i*; `u_i = p_i − c_i` = billable tokens.
`B` = 64 (the checkpoint boundary).

| Metric | Definition | Why this denominator |
|---|---|---|
| **BM (billable fraction)** | `BM(cell) = Σ_{i=1..n} u_i / Σ_{i=1..n} p_i` — **token-weighted**, pooled over all *n* requests of the cell | Token-weighted, not request-weighted: the claim is about the *token bill*, and a request-weighted mean would let a short 40-token turn count as loud as a 400-token one. Both are reported; BM is the headline. |
| **BM_tail(n)** | `u_n / p_n` at the **final** turn only | The per-turn tax at depth n; the quantity P1 and P3 are stated on. |
| **Waste W(cell)** | `Σ_i (c_i mod B)` and `Σ_i (u_i mod B)` reported separately | Alignment waste, the physical quantity behind the 64-token tax. |
| **Recovery R(cell)** | `u_n` for arm (a) ÷ `u_n` for arm (b) at the same *n* | The headline causal ratio. **< 1 favours state rendering.** |
| **TTFT** | time from request send to first streamed byte, at **fixed prefix length** — reported only at depths where `p_n` differs from the other arm by < 5 %, else omitted (see §1.1) | Confound-bounded by construction. |
| **Throughput sanity** | completion tokens ÷ generation wall time, and requests ÷ second, per cell | Sanity only: a cell whose throughput collapses signals a stack problem (contention, eviction), and the cell is flagged rather than reported. |

Statistics: every headline number is reported as `mean [min, max]` over the 3 repetitions,
**plus the pooled figure**. With 3 reps no confidence interval is claimed; the spread is the
honest object (house convention: report the variation, cf. `CLAIMS.md` C41–C47 pattern).

---

## 4. Arm B — real-use telemetry (observational; no causality)

Arm B reports **what the production sessions already did**. It has one job: give the reader a
distribution to compare Arm A's controlled result against. It does **not** test H1 and cannot
support the words "causes", "because of", or "as a result of".

### 4.1 Exact stat fields to record

Per session (one session = one prototype/agent conversation), one row:

| Field | Meaning |
|---|---|
| `session_id` | stable id |
| `turn_index` | 1-based |
| `prompt_tokens` | `usage.prompt_tokens`, as recorded |
| `cached_tokens` | cached count, **plus the G0 key path it came from** |
| `cache_field_origin` | `SERVER` \| `RECONSTRUCTED` \| `ABSENT` — the G0 verdict per row |
| `rendering` | `APPEND` \| `WINDOW` \| `OTHER` — what the session's renderer did, inferred from the recorded request bodies, **not** from intent |
| `prefix_drift` | `0` if this turn's prompt is a byte-prefix-extension of the previous turn's prompt, else `1` (computable from the recorded bodies) |
| `cache_event` | none \| server restart \| model reload \| config change, taken from server logs |
| `prompt_token_band` | bucket: `0–1k`, `1k–4k`, `4k–16k`, `16k–64k`, `64k+` |

### 4.2 The two reported statistics, and what each may be called

1. **Band distribution** — count and **token-weighted share** of turns per `prompt_token_band`,
   at the observed cached fraction. Reported as: *"in band X, Y % of prompt tokens were cached
   across Z turns"* — a description, nothing more.
2. **Request-weighted rate** — `Σ cached_i / Σ prompt_i` pooled over sessions, and separately
   the **median per-session** rate. Both are reported because the pooled figure is dominated by
   the largest sessions; showing only the pooled number would repeat the GX10 §6 error
   recorded in `strategy/PAPER_CANDIDATES.md:391` ("the pooled 83.7 % is dominated by one
   synthetic corpus … the honest headline is the per-corpus column").

### 4.3 Mandatory disclaimer text, verbatim, wherever Arm B numbers appear

> These are descriptive statistics from recorded production traffic. Turns are not
> randomised, renderer choice correlates with prompt length and with the task itself, and
> sessions are not independent. No causal claim is made from this table.

**Equivalence to Arm A is never asserted.** If Arm B's numbers happen to match Arm A's
predictions, the correct sentence is "consistent with", not "confirms".

---

## 5. Pre-registered predictions (stated BEFORE the run)

Each prediction names its **numeric point** (a value fixed now, not after looking), its
**kill condition** (what makes it wrong), and its **scope** (what it does not say).

### P1 — The tax law

> For a prompt of length `L` submitted against a **cold** cache with an exact-prefix match
> available, the billable count is `u = L − 64·⌊(L_prev)/64⌋` where `L_prev` is the length of
> the longest available exact prefix; **for a repeat of an identical prompt, `u = L mod 64`.**

- **Numeric point:** on a full repeat, `u = L mod 64` **exactly**, for every `L` in
  {300, 700, 900, 1000} (±0). Falsified if any repeat's `u` is not `L mod 64`.
- **Kill condition (K1):** if ≥ 2 of 4 tested lengths miss `L mod 64` by more than `B/2`, the
  law is **killed** and the observed relationship is reported as fitted, not derived.
- **Scope:** says nothing about *first* use of a prompt, only about reuse; and nothing about
  whether reuse would have happened in a real conversation.

### P2 — The collapse law

> An insertion **before** an already-cached boundary invalidates **every** token after the
> insertion point; an insertion **after** the boundary invalidates only what follows it.

- **Numeric point:** inserting a k-token marker at token offset `o` into a cached `L`-token
  prompt yields `cached ≈ 64·⌊(o−1)/64⌋`; at `o` past `L` it yields `cached ≈ L`.
- **Kill condition (K2):** if a post-prompt insertion (offset > L) ever drops cached below
  `L − B/2`, the "prefix-only" model of the instrument is refuted and the protocol's
  mechanism claims are void.
- **Pre-declared known tension:** the prior probe recorded **0/813 cached** for a marker
  inserted at char 2000 into an 807-token prompt — i.e. a *total* collapse, not a
  neighbourhood collapse. Under P2 this is a **40-token-offset** insertion and should have
  left ~608 cached (64·⌊1999/...⌋ boundary). **P2 as stated would kill itself against that
  prior observation.** The protocol therefore pre-registers the disambiguating probe
  (**C3**, §6) as the *first* thing that runs after G0, and states now that if C3 reproduces
  total collapse, P2 is replaced by the stronger, simpler law *"any earlier mutation collapses
  the request entirely on this stack"* — recorded as a **revision with a date**, not silently.

### P3 — The depth law

> Per-turn billable cost is **flat in n** for the state renderer and **grows ~linearly in n**
> for the full re-render.

- **Numeric point:** `BM_tail(n)` for arm (a) is constant to within `±B` tokens across all nine
  depths (its spread is bounded by one 64-boundary), while `BM_tail(n)` for arm (b) grows and
  `BM(cell)` for arm (b) exceeds arm (a)'s by **≥ 5× at n = 190** (a ratio, not a percentage).
- **Kill condition (K3):** if `BM_tail(n)` for arm (a) has a slope whose fitted growth over
  n = 8→190 exceeds **B/2 tokens per 10 turns**, the "flat" half is killed. If `BM_tail(n)` for
  arm (b) fails to grow monotonically over the same range, the "linear" half is killed.
- **Scope:** the linear half is a prediction about *this corpus's delta sizes*; it is stated as
  a ratio against the state arm, not as an absolute token count.

### Ordering rule (anti-HARKing)

Predictions are frozen **before** C3 and before any Arm A cell. If C3 forces the P2 revision,
the revision is appended as a dated addendum and the manuscript carries both the original P2
and the revision with the C3 result that forced it — the reader sees a law that was changed
by evidence, not a law written after it.

---

## 6. Controls

Every control names its **zero** — the value it must return if the instrument and the protocol
are working. The house convention it follows is the 244/244 control in
`papers/replay-record-not-decision/CLAIMS.md` §E (C38–C40): a control arm that must return
*identical* on every comparison, whose failure would have caught an inverted predicate
("would have published '51 % replication divergence'; control caught it", C40). A control that
could plausibly pass under a broken protocol is not a control.

| id | Control | Zero / expected | If it fails |
|---|---|---|---|
| **C0** | **Cache flush before every cell.** Flush, then send a throwaway probe; the probe must report ~0 cached. | probe cached < B | Nothing runs. A cell that starts warm measures the previous cell. |
| **C1** | **Repeat-run identical requests (the zero).** The same prompt issued twice, unchanged, cold start each time. | turn-2 cached = turn-1 prompt length − (L mod B), **identical in all 3 reps** | The instrument has no zero and no ratio in this protocol is interpretable. **This is the 244/244 analogue** and is reported as `N/N identical`. |
| **C2** | **64-aligned vs unaligned.** Prompts of length 640, 641, 703, 704, each repeated. | `u` = 0, 1, 63, 0 respectively | P1's mechanism is mis-specified. |
| **C3** | **Single-token early mutation → collapse.** Insert one token at offset 1, at offset 40, and at offset 600 of a 900-token cached prompt; then re-issue the original. | offset 1 → collapse to ~0; offset 40 → **per P2**, ~0; offset 600 → ~576; original → 900 cached | **The in-hand prior says 0/813 for a ~40-token offset.** C3 decides whether P2 or the total-collapse law holds. The "then re-issue the original" half is the recovery check — prior probe says 768 returns, so failure to recover means the server evicted rather than the prefix being absent. |
| **C4** | **Tool-array change.** The tool array hashes **before** the system prompt, so a tool-array change may invalidate everything. Send the same 1,000-token prompt with (i) no tools, (ii) tool set A, (iii) tool set A again, (iv) tool set A with one tool's **description** altered, (v) tool set A again. | (i) cold; (ii) ~0; (iii) ~full; (iv) **~0** (the whole prefix, including the system prompt, dies); (v) ~full again | If (iv) does **not** collapse, the tool array hashes *after* the system prompt and the recorded claim "tool array hashes before the system prompt" is refuted — itself a publishable negative. If (v) does not recover, the cache is evicting on size, not invalidating on prefix, and Arm A's between-run isolation needs re-derivation. |
| **C5** | **Subsequence identity assertion.** Both arms' bodies tokenised; `tokens(a) == tokens(b)` per pair. | 100 % of pairs identical | Cells failing C5 are excluded **and counted**; if > 10 % fail, Arm A's central claim is not measurable on this chat template (§3.2) and the protocol reports that as its result. |
| **C6** | **Negative control — rendering that should NOT help.** Sliding newest-first window (prior probe: 98.6/95.0/95.0/95.0, never recovers). | never returns to arm-(a) parity | If the window *does* reach parity, the measurement is not distinguishing renderings and C1 should be re-read. |

**C4 is the control the naive design forgets.** A tool-array experiment that changes both the
tools and the system prompt in one step cannot tell a tool-array invalidation from a
system-prompt invalidation. Step (iv) changes **only a tool description** and keeps the
system prompt byte-identical, which is the minimum move that isolates "the tool array hashes
early" from "some other prefix component changed".

---

## 7. Paper readiness

The paper this serves is the live-cache arm that B6 (`strategy/PAPER_CANDIDATES.md` §B6,
"live cache claim NOT MEASURED") is missing. It must ship in the `replay-record-not-decision`
shape: a `CLAIMS.md` where **every** number maps to a file, a field, or a named arithmetic
derivation, with **RE-DERIVED** rows naming their command.

### 7.1 Pinning (at run time, before the first request)

| Artifact | Pin |
|---|---|
| Corpus | `sha256` + byte count + line count, per §3.1, **re-taken on the run day** |
| Server | model id, server version string, launch flags, page size, checkpoint interval — recorded verbatim |
| Client | `build_request_body` and `parse_usage` source digests (`src/resextract/llm/occamy.py:456`, `:524`) — a client change silently changes every prompt |
| Hardware | host, GPU, load state (anything else running on the box) |
| Date | both the model-serving date and the analysis date |

### 7.2 Commands — every number recomputable

| Number class | Command |
|---|---|
| BM, BM_tail, R, W | `python3 experiments/cache-tax-bench/recompute.py --runs <run-dir> --metric bm` |
| Arm B band table | `python3 experiments/cache-tax-bench/recompute.py --telemetry <session-dir> --metric bands` |
| C1–C6 zeros | `python3 experiments/cache-tax-bench/recompute.py --controls <run-dir>` |
| Digest pins | `sha256sum <corpus>` (also in the run record, so a drift shows as a diff) |

The re-run is **expected** to produce the same numbers; a non-reproducing cell is reported as
a failed cell, kept in the table, and counted — not dropped (house rule: the failed run is the
interesting one, `experiments/README.md`).

### 7.3 CLAIMS.md skeleton — every future number pre-mapped

Rows are numbered `CB-` (cache benchmark) to avoid collision with the note's `C` rows.

| # | Claim in the future manuscript | Value | Source | Note |
|---|---|---|---|---|
| CB-01 | Pinned corpus size/digest | *(run day)* | **CORP-MAIN** `stat`, `sha256sum` | drift check |
| CB-02 | G0 verdict | *(V-SERVER / V-DERIVED / V-TIMING / V-FAIL)* | G0 probe output | gates everything below |
| CB-03 | C1 zero | *N/N identical* | **CONTROLS** `--controls` | the 244/244 analogue |
| CB-04 | C2 alignment zeros | *0, 1, 63, 0* | **CONTROLS** | P1's mechanism |
| CB-05 | C3 collapse offsets | *(three cached values)* | **CONTROLS** | decides P2 vs total-collapse |
| CB-06 | C4 tool-array collapse | *(true/false per step)* | **CONTROLS** | the early-hash claim |
| CB-07 | C5 subsequence identity | *k of m pairs* | **CONTROLS** | if < 90 %, Arm A is unmeasurable |
| CB-08 | Arm A BM at each depth, per arm | *2 × 9 values* | **RUNS** `--metric bm` | RE-DERIVED |
| CB-09 | Arm A ratio R at n = 190 | *(a/b)* | arithmetic on CB-08 | the headline |
| CB-10 | P3 flatness spread, arm (a) | *(tokens)* | arithmetic on CB-08 | must be ≤ B |
| CB-11 | Arm B band table | *(per band)* | **TELEMETRY** | descriptive only |
| CB-12 | Arm B pooled vs median per-session | *(two rates)* | **TELEMETRY** | both required (§4.2) |

### 7.4 What the manuscript may not contain

- Any Arm B number in a causal sentence (§4.3 disclaimer must travel with the table).
- Any timing claim at a prefix length where the arms' `p_n` differ by ≥ 5 % (§3.4 TTFT).
- Any number whose row in the CLAIMS table is missing a command.
- The word *benchmark* for Arm A: it is a controlled replay, not a benchmark. (The workspace's
  own `docs/PLAN.md:73` classification guard would put an unrecomputable item in `memo`, never
  `paper`.)

---

## 8. Blockers and open questions (recorded now, at design time)

1. **No emitter on disk.** `templates/` is absent at the workspace root though `docs/PLAN.md`
   §3.1 lists it. §3.2 supplies a byte-exact renderer specification as the mitigation; if the
   operator runs the app's real emitter instead, that emitter must be pinned by digest and its
   output diffed against §3.2's before any comparison.
2. **No cached-token field in the typed client.** `Usage` (`src/resextract/llm/occamy.py:314`)
   carries four fields, none of them cached. Every cached number must come from `raw_usage` or a
   raw HTTP call, and G0 must establish the key path. A consumer reading a cached field through
   the typed client is reading an unvalidated path.
3. **Instrument validity is unresolved at write time.** Another unit is checking whether the
   field is server-reported or estimated. §2 is written so that either outcome produces a
   defined run; it does not assume the favourable one.
4. **The in-hand prior is in tension with P2** (§5, P2 known tension). C3 resolves it and is
   the first post-G0 probe. This tension is disclosed rather than smoothed.
5. **The hybrid model's 64-token checkpoint interval is an input, not a finding.** If the run
   day's model or server configuration differs, P1's `B` changes and every prediction in §5 must
   be re-stated before the run, not after.
