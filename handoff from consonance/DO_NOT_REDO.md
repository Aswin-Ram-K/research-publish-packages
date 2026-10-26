# Do not redo — ten traps, each paid for once

These are written as prohibitions because each one has already cost a run, a day, or a claim.

## 1. Do not infer savings from prompt length

EXP#43 measured **payload −24.2 % / billed −2.4 %** on the same change. Any arm you design must report
**uncached work or time-to-verified-success**, not tokens saved. A shorter prompt that rewrites the prefix is
expected to cost more, and we have watched it happen.

## 2. Do not promote unregistered reconnaissance into a guarantee

The Occamy prefix recon (seven requests) and every "it looked like a cliff" observation are hypothesis
generators. If a number is going to be quoted, it needs a registered run with a pre-frozen `run.json`.

## 3. Do not mix hosted and local cache metrics

A hosted provider's cache accounting and an engine's KV accounting are different quantities even when the
field name matches. A provider that reports nothing can still contribute quality and latency; it cannot
contribute a hit-rate claim.

## 4. Do not compare arms across builds

Engine image digest and every serving flag go in `run.json` **before** the first call. A cache number
measured at one build is not evidence at another. If the rig swaps containers between arms, the arms are
different experiments.

## 5. Do not touch the production container

`gx10-occamy-nvfp4` stays up. Variant containers take `:8012` and the production model is then **not
running**; restore is mandatory and is verified by `:8012/v1/models` returning `occamy-1.0` — **not** by a
`/health` probe, which returns 000 on a perfectly healthy server on this box.

## 6. Do not treat `cached_tokens` granularity as a defect

Counts come back in multiples of 64, and `--prefix-match-unit` does not finer the grid on this build.
Repeated values are server behaviour, not a bug to repair; a "repair" was already attempted twice and
reverted both times.

## 7. Do not claim KV portability

KV state does not transfer across models, quantizations, serving engines or adapters, and alignment to
block/page boundaries changes accounting, never attention validity. A semantic block with identical content
but different preceding tokens is not the same cached state.

## 8. Do not let a control be unfireable

Consonance lost a gate entry to exactly this: a control whose predicate graded host speed and fired 3 times
in 12 runs on fixtures that were always serialised. Before a run, show the control **red** on an input where
the property is absent. If it cannot go red, it is decoration.

## 9. Do not run heavy jobs concurrently on one host

Two `npm run ci` on one machine red each other here through a published lock, and on the GPU box a
concurrent job moves TTFT enough to invert an arm. Serialise measurement runs; record concurrency in
`run.json`.

## 10. Do not quote Consonance's 65,536 as a token ceiling

In our repository `65536` is the **DSH workspace-instruction *byte* budget** and one historical
`maxTokens=65536` record. There is no 65,536-token ceiling in our code. The live windows are **131,072**
(occamy) and **32,768** (qwen3.5-9b), and they were measured on 2026-10-25.

---

**One more, not a trap but a habit:** when a measurement contradicts the design note, the note changes and
the measurement stays. Consonance's whole method is that history is evidence; the same applies to whichever
of us writes first.
