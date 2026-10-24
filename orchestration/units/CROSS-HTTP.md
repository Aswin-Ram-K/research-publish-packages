# CROSS-HTTP — first cross-engine, cross-architecture cache measurement (GAP G4)

**Status: partial (deliberate, and a result).** Live requests: **9 of 120**. Restarts: **0**. Writes
outside this unit's cell: `docs/serving-options/CROSS-HTTP.md` + `orchestration/{units,handoffs}/CROSS-HTTP.*`
only. Target repos untouched; no `git` run anywhere.

## Purpose

G4 is blocked on a maintenance window that restarts the production Occamy service. Two services already
listen on the same box and need no restart at all. `:8014` is vLLM 0.27.1 serving the **dense** model
`qwen3.5-9b` — a dense model has no Mamba state, so any grid measured there cannot be explained by the
hybrid state chunk. That is the clean anchor the paper lacks.

## What was done

1. Read `AGENTS.md`, `papers/context-cache/GAPS.md` §G4, `docs/serving-options/LAUNCH-VLLM.md`.
2. Probed read-only: `GET /v1/models`, `/version`, `/metrics` (no inference). `/metrics` yielded the full
   launch config without touching the service.
3. Ran the step-1 probe **three times** (the first ad-hoc, two archived): two identical ~2,500-token
   prompts with a fixed `seed`, plus a same-length from-scratch control; scraped
   `vllm:prompt_tokens_cached_total` before and after each run.
4. Recorded the finding and **stopped at the card's own step-1 branch**: no `cached_tokens` → say so,
   fall back to latency-only, and do not present a latency grid as a cache grid.
5. Wrote `analysis.json`, `rows.jsonl`, `runs/*.json`, `cross_http.py`, and the docs section.

## Findings

1. **`usage.prompt_tokens_details` is absent on 9/9 responses** — `null`, not `0`, on every probe row in
   all three runs. Consistent with `LAUNCH-VLLM.md`: the flag `--enable-prompt-tokens-details` is not set.
2. **The cache is nonetheless active.** `vllm:prompt_tokens_cached_total` moved by **exactly 1056** on
   each of two archived, independently-salted runs. The delta is identical across runs and across slightly
   different prompt lengths (2,504 and 2,509 tokens), which is what lets it be attributed to our three
   requests despite the counters being shared.
3. **Effective block = 1056 tokens**, read from `vllm:cache_config_info{block_size="1056",
   _block_size_resolved="True", user_specified_block_size="False"}`. Not 16 (the vLLM default), not 64
   (SGLang), not 128. The build **derived** it; the derivation mechanism is a hypothesis, not a finding.
4. **Latency-only fallback (labelled as such):** repeat/cold wall ratio **0.60** and **0.69** across the
   two runs; the from-scratch control lands at ~1.0× the cold send. Reported as latency, never as a
   cache-hit ratio.
5. **Steps 2–4 not run, deliberately:** the per-L sweep, the append chain and the fan-out all need a
   per-request `cached_tokens`. The fan-out additionally requires confirming prefix residency, which is
   unreadable here — so `fanout.verdict` is `unmeasurable`, **not** `1.0`.

## Hard constraints observed

- Read-only against the box: only `GET /models`, `GET /version`, `GET /metrics`, `POST /chat/completions`.
  No restart, no flag change, no `/flush_cache`, no systemd, no ssh.
- `:8010` never contacted; `:8000` (`ornith-1.5-35b`) read once with a plain `GET /v1/models` only
  (engine unidentified, so its stack stays `unknown` and it contributed no rows).
- `.occamy.lock` flock'ed for every live run, released in `finally`; every run shows `lock.wait_s = 0.0`.
- Bound 120; used **9** (3 + 3 + 3). A 5xx or a tripled TTFT aborts via `ServerUnhealthy`.

## Assumptions (automated session: no question was asked)

- **Requests 4–9 were confirmatory, not exploratory.** Runs 2 and 3 re-executed the same 3-request probe
  under a fresh salt after the engine counter was found to move. Rationale: a single observation of a
  shared, third-party counter is not attributable; the same delta recurring under independent salts is.
  This is the minimum evidence that makes finding 2 a finding rather than a coincidence.
- **`seed` is fixed at 1729** (the package's corpus seed) so both stacks share a seed. `temperature` is 0.
- The grid was **not** attempted despite the card allowing a fallback: a latency grid would answer a
  different question and the card forbids presenting it as cache data.
- Where the card contradicts itself (step 2 is conditioned on cached tokens being reported, which they
  are not), the conditioning branch won.

## Artifacts

| Path | What |
|---|---|
| `cells/CROSS-HTTP/cross_http.py` | the instrument: probe / run / analyse; lock, budget, health aborts |
| `cells/CROSS-HTTP/rows.jsonl` | 3 rows (final archived probe run), each with `row_digest` |
| `cells/CROSS-HTTP/history/rows-run{1,2}-*.jsonl` | the two earlier runs, frozen |
| `cells/CROSS-HTTP/runs/probe-*.json` | per-run summary **with counter before/after** |
| `cells/CROSS-HTTP/analysis.json` | machine-readable recovery (`engine_counters`, `latency_only`, `fanout`) |
| `cells/CROSS-HTTP/events.jsonl` | phase log |
| `docs/serving-options/CROSS-HTTP.md` | the measured vLLM grid versus SGLang's `64*floor((L-1)/64)` |
| `orchestration/handoffs/CROSS-HTTP.json` | unit handoff |

## Blocker / next hint

Not blocked on this unit's work — blocked on one flag on someone else's service.
**Next hint:** if `:8014` is ever relaunched, `--enable-prompt-tokens-details` alone unlocks steps 2–4;
`cross_http.py --run` already implements all three arms (grid 512…8192 = 32 req, append = 9 req,
fan-out K=8 = 9 req; total 53 incl. the probe) and will run them unchanged the moment the field appears.
