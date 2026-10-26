# UNIT LAZY-LOAD-ARM  -  lazy instruction loading, first honest measurement

**Status:** done. Report: `orchestration/handoffs/LAZY-LOAD-ARM.json`; result: `experiments/agentic-lazy/RESULTS.md`
**Write paths:** `experiments/agentic-lazy/**`, `orchestration/units/LAZY-LOAD-ARM.md`, `orchestration/handoffs/LAZY-LOAD-ARM.json`
**Bound:** 60 tool calls. If either server unreachable -> stop at build step, ship corpus + harness + `--dry-run` proof, report `partial`.
**Automated:** no human present; no questions.

## Why this unit exists

The existing "pointer" arm in this repo is **not** token compression. `src/resextract/context/render.py:14-22`
states that the pointer rendering and the naive-append rendering send identical chain content, and claim C01
confirms 760/760 byte-identical cells. The hypothesis

> a large instruction body can be replaced by a short projection that the model resolves on demand

has therefore **never been measured here**. This unit measures it for the first time.

## Technique (naming rule)

The technique is called **lazy instruction loading**. The word "pointer" is NOT used for it, because three
prior meanings already exist in this repo: `src/resextract/pointers.py:1`, `src/resextract/context/render.py:82`,
`src/resextract/context/nodes.py:21`.

## Objective

Compare two renderings of the same instruction corpus under the same task:

- **C0 (plain chat)**  -  every item body inlined into the system prefix.
- **L1 (lazy)**  -  a compact projection per item (kind, id, one-line description, byte size) plus ONE fetch
  tool that returns an item body on demand.

## Corpus

12 original items, four kinds x 3 (tools, skills, memory, knowledge), target 20,000-40,000 characters.
Generated reproducibly by `experiments/agentic-lazy/build_corpus.py`; each item's sha256 is recorded in
`corpus/MANIFEST.json`. No third-party text is copied.

The one-line description in the L1 projection is **derived mechanically** from each body's hero line, so the
index cannot leak a fact the body does not contain.

## Task and ground truth

The task requires exactly 2 of the 12 items and never names them. Ground truth recorded in `harness.py`:

| fact | value | source item |
|---|---|---|
| billing log retention days | 400 | K-2 |
| nightly scheduler max retry attempts | 5 | M-1 |

Success = **both** facts present in the final answer.

Deliberate discriminator: the corpus carries near-miss neighbours so that a guess from the projection is not
free  -  K-2 sits beside K-1/K-3 and holds an in-item decoy (the backfill tier's 100 days vs compliance's 400),
and M-1 holds a decoy (5 attempts vs the 3->5 history). A model that answers from the description alone has a
real chance of being wrong.

## Measurement

- Models: `occamy-1.0` at `http://192.168.2.168:8012/v1`, `qwen3.5-9b` at `http://192.168.2.168:8014/v1`.
- Arms: C0, L1. Reps: 3 each. Temperature 0.
- Per request: `prompt_tokens`, `prompt_tokens_details.cached_tokens`, completion text, correctness, and for
  L1 the number and identity of fetch calls.

### Instrument findings from the pre-flight probes (design consequences)

1. **`:8014` has no tool parser.** `tools` + `tool_choice` returns
   `400: "auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set`.
   The server must not be restarted, so on `qwen3.5-9b` the L1 arm cannot use native function calling.
2. **Both models spend the completion budget on hidden reasoning** (occamy: 239 reasoning tokens before a
   239-token answer; qwen: 741-char reasoning block), so the completion budget is set to 2048 and held equal
   across arms.
3. **`:8014` never populates `prompt_tokens_details`**; cache overlap for qwen is therefore unmeasured, not 0.
4. `src/resextract/llm/occamy.py` always sends `chat_template_kwargs`, which `:8014` rejects, so both servers
   are driven through one minimal body builder in `runner.py`.
5. **`:8014` cannot use native tool calling**, so the two L1 arms differ in protocol: `occamy-1.0` uses
   native function calling (2 requests per run), `qwen3.5-9b` uses a text-emulated fetch protocol of
   `FETCH <id>` / `ANSWER` (3 requests per run). Each row records which via `protocol`. Cross-model
   comparison is indicative, not clean  -  the extra round is why qwen's overhead is higher.
6. A long call held open across a harness restart is treated as a lost measurement and re-run, never
   counted as a data point.

## Result (headline)

- L1 does **not** sweep the corpus: both models fetched **exactly the 2 required items (K-2, M-1) in 3/3
  runs**, with no wasted fetch and no wrong-id retry.
- Prompt tokens per run, whole run including tool rounds: `occamy-1.0` C0 **5359** vs L1 **2625**;
  `qwen3.5-9b` C0 **5359** vs L1 **3324**.
- Correctness: **3/3 both arms, both models** (both facts). Saturated  -  this task does not separate
  accuracy, which is recorded as a limitation.
- Realised saving (cold cache, charged for fetched bodies): **19.8%** occamy, **18.1%** qwen.
- **Caveat that reverses the verdict:** `occamy-1.0` served C0 at a **99.1% cache hit** in every rep, so
  under a warm prefix cache the 18-20% saving inverts into a loss. The cold-cache figure must not be
  quoted as "the" saving.

## Report (no massaging)

Tables required: tokens per arm per model; correctness per arm per model; L1 fetch-count distribution;
realised saving = `(C0 prompt - L1 prompt - fetched body tokens) / C0 prompt`.

**If L1 fetches nearly every item, state plainly that lazy loading does not pay for this workload.** A negative
result is the correct outcome if the data says so. The corpus and the task must NOT be tuned to make L1 win.
