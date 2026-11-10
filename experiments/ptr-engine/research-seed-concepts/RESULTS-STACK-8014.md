# RESULTS-STACK-8014 — Cross-stack record (occamy-1.0 :8012 vs qwen3.5-9b :8014)

## Purpose and stacks

This record compares the ptr-engine research-seed concept runs across two serving stacks. It was restored from
the row files listed under *Files and provenance* after the original 3,103-byte write was truncated to 822
bytes by the following unit.

- `:8012` — `occamy-1.0`, SGLang, 131,072-token window, `--mem-fraction-static 0.45`, `--enable-cache-report`.
- `:8014` — `qwen3.5-9b`, vLLM 0.27.1, 32,768-token window, `--gpu-memory-utilization 0.15`. Tool calling was
  absent until the container was restarted with `--enable-auto-tool-choice --tool-call-parser qwen3_coder`
  (`qwen3_coder` confirmed in that build's lazy parser registry); everything else unchanged.

## Tool-call enablement and verification

Before the restart the fetch arm scored 0/12 and was blocked at the first turn because the endpoint executed no
tool calls; prompt usage was ~1,392 tokens against 32,768, so context was never binding. After the restart a
probe returned a `tool_calls` array with `function.name` and parseable arguments — PASS.

## Runs on :8014

|Run|contract|value|abstained|ungradeable|fetch turns|
|---|---|---|---|---|---|
|`TX-03` masking r1|8/48|8/48|39|0|—|
|`TX-03` fetch r1|42/48|42/48|0|0|48 (61 calls)|
|`TX-AGG` fetch|0/48|0/48|19|2|41 (243 calls)|
|`TX-HOP` fetch r1|0/48|0/48|10|37|15 (21 calls)|
|`TX-HOP` fetch r2|3/48|3/48|8|32|11 (17 calls)|
|`TX-HOP` fetch r3|9/48|9/48|32|3|20|

## Distance axis side by side

Distance axis `{2,5,6,8,20,32}`, 8 checkpoints each.

`TX-03` masking: `:8014` `8,0,0,0,0,0`; `:8012` `8,0,0,0,0,0` — identical, the eviction boundary at 5 turns
reproduces exactly on a different model, engine and window size. *(Corrected wording: the mask fires at `intro+4`, so `d=5` is the first checkpoint past it rather than the boundary value itself. Cause is content evicted, not depth. The presence finding in FINDINGS-LEDGER.md §The TX-03 cliff is presence, not position was measured on `:8012` (SGLang, `occamy-1.0`); this file's own `:8014` (vLLM, `qwen3.5-9b`) numbers above remain `:8014` and are not merged with it.)*

`TX-03` fetch: `:8014` `5,8,8,8,7,6` (42/48); `:8012` `8,8,8,8,6,3` (41/48) — full through distance 8 on
both, decaying after; the stacks differ only at distance 2 (5 vs 8) and 32 (6 vs 3).

`:8012` reference for the other tasks. `TX-AGG` fetch 4/48 with 29 fetch turns; `TX-HOP` fetch 9/48 with 28 fetch
turns; `TX-SUP` 18/48 with 42 turns; `TX-ABS` 15/48 with 42 turns.

## Two instrument repairs made after the first HOP attempts

(1) The `:8014` model emits `ANSWER: CALL(fetch(ref="doc-key-1@1"))` — a tool call wrapped in an answer line,
with a bare-integer revision. Because the parser treats `ANSWER: CALL` as an answer whose content is a call, the
fetch never executed and 41 of 48 checkpoint answers were ungradeable. Text-form fetch requests are now executed
as fetches, stamped `protocol_variant=text_call` with `ref_as_emitted` and `ref_revision_normalised`; unparseable
text-form calls stay ungradeable; at most one per turn. Result: OOV fell to 0 on turn rows and HOP moved
3/48 → 9/48.

(2) Each fetch follow-up re-asked the same checkpoint and wrote a second checkpoint-bearing row — 80 checkpoint
rows for 48 ids, 17 ids duplicated — which produced a bogus `9/59` score. Interim rows are now marked
`interim=true`, exactly one answer per checkpoint id is graded, more than one non-interim answer fails loudly,
and a graded count that differs from the fixture's checkpoint count reports `denominator_mismatch` instead of a
score. Re-scored: 9/48. The two unaffected `:8014` runs re-scored unchanged at 42/48 and 8/48.

## What transfers across stacks and what does not

Single-fact recall transfers almost exactly (41/48 vs 42/48) and the masking eviction boundary transfers exactly.
Multi-fact tasks fail on both stacks — AGG 4/48 vs 0/48, HOP 9/48 vs 9/48 — so the multi-fact limitation is not
a property of one model. Format compliance does NOT transfer: the `:8014` model needs text-form call normalisation
and still leaves 14 `no_answer_line` turns, while the `:8012` model emits native tool calls. Anything read off
`:8014` before the parser and normalisation were in place measured format, not retrieval.

## Limitations

One replication per cell on `:8014`; different model families, context windows and GPU memory fractions, so no
cross-stack claim is causal; `TX-AGG` on `:8014` made 243 fetch calls for 0 correct answers, which is a behavioural
observation without an established mechanism; the text-call normalisation is an instrument change made
mid-programme and is recorded here rather than retrofitted to earlier cells.

## Files and provenance

Row files under `experiments/ptr-engine/measure/`:

- `rows-tx03-8014-masking-r1.jsonl`
- `rows-tx03-8014-fetch-r1.jsonl`
- `rows-agg-8014.jsonl`
- `rows-hop-8014.jsonl`
- `rows-hop-8014-r2.jsonl`
- `rows-hop-8014-r3.jsonl`

Restored 2026-11-09 after the original 3,103-byte record was overwritten and truncated to 822 bytes.
