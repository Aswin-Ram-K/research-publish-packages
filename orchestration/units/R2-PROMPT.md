# R2-PROMPT — pointer index × whole-context resend, four arms on the optimised setups

**Status:** done (8 of 16 cells measured; 8 named `unavailable` with evidence)
**Card:** `fcb4b36b-ea77-4517-9bb0-23214dc04396`, execution `79d71e48`
**Contract (what this unit owed):** LIVE factorial P0/P1/P2/P3 × O1/O2/O3/O4 on the optimised setups from
`state/config/best-config.json`; 71 turns per arm at budget 32768; warm-up per arm; no nulls in rows (an
unobservable value is the string `unavailable`); matrix + results doc; quality guard; cost column.

## Arms

| arm | what it is | implementation |
|---|---|---|
| P0 | whole-context resend — the full evolving state as one appended message | `render("R", t)` of the frozen round-1 renderer |
| P1 | immutable scaffold + pointer index (`id \| byte-span \| sha8 \| one-line summary`) + one trailing volatile delta; nothing earlier rewritten | `render("A", t)` |
| P2 | P1 with the trailing block padded so the request length is a multiple of the setup's cache unit | `FILLER = " PAD"`, pad computed from P1's measured length for the same turn, ≤3 corrective resends until the server's `prompt_tokens % grid == 0` |
| P3 | P1 with one earlier index line (`t020`) rewritten once at turn 40 | P1 + `[rev2]` line and a `MODE[edit-policy; revised=…]` marker from turn 1, so P3 is distinct from P1 before the edit |

Renderer reused unchanged: `experiments/context-cache/cells/VLLM-CELL/vllm_cell.py` (249 lines, frozen).

## What ran

- **O1** occamy-1.0 × SGLang `:8012`, grid 64 → 284 rows, `observed_cached_gcd 64`.
- **O4** qwen3.5-9b × vLLM `:8014`, grid 1088 → 284 rows, `observed_cached_gcd 1056`, `cached_tokens` derived
  from `vllm:prefix_cache_hits_total` deltas (the endpoint reports `prompt_tokens_details: null`).
- **O2** (9B SGLang) and **O3** (occamy vLLM) → `unavailable`: no listener on 8015–8019, no `gx10-*` container
  on this host, and ssh to the GX10 is refused by policy (`BLOCKED by CC Safety Net / Rule: secret.home.ssh`).

## Findings in one screen

- **P1/P0:** O1 **null** (−7.68 unc/turn, CI [−51.84, +36.49]); O4 **non-null −219.51** [−355.36, −83.65],
  i.e. **−11.7 %** prefill work per turn.
- **P2/P0:** O1 null (+11.35); O4 **non-null +387.24** [+223.06, +551.42] — padding to the cache unit is a
  **20.6 % loss** on O4, partly because the declared grid (1088) is not the observed unit (1056).
- **P3/P1:** null on cost in both setups (O1 −2.17, O4 +23.52). **P3 survival on O1 is proven:** 48.4 % of the
  pre-edit cached prefix is lost at the edit turn (1984 → 1024, P1 stays 1984) and rebuilds to within 1.3 %.
  On O4 the collapse is **unmeasurable** (cached is 0 at the edit turn in both arms).
- **Quality:** the pointer form is **not output-equivalent** — first-32-token mismatch on 20/20 (O1) and
  19/20 (O4) fixed questions.

## Files

- `experiments/context-cache/cells/R2-PROMPT/prompt_r2prompt_cell.py` — the harness (four arms, gates,
  measured pads, counter-derived instrument, quality pass, analysis)
- `experiments/context-cache/cells/R2-PROMPT/build_matrix.py` — assembles the 16-cell matrix from disk
- `experiments/context-cache/cells/R2-PROMPT/{O1,O4}/{rows.jsonl,g0.json,analysis.json,quality.json}`
- `state/r2-prompt-matrix.json`, `state/config/r2-prompt-cost.json`
- `docs/prompt-system/R2-PROMPT-RESULTS.md`
- `state/logs/R2-PROMPT-progress.log`

## Bound

75 tool calls / 1,600 live requests. Used ≈62 tool calls and ≈900 live requests (568 row-bearing plus
warm-ups, gates, calibration probes, one aborted O4 P2 attempt and 40 quality posts).

## Traps recorded (do not repeat)

1. A whitespace pad is stripped by the chat template — pad with content.
2. A generic chars→tokens ratio does not align a pad; measure tokens/char and correct against the server's
   own `prompt_tokens`.
3. Do not sleep on an endpoint's self-report: O4's cache works while its per-request accounting is off.
4. In a loop where a resend can replace the response, the counter sampling must wrap **every** POST, or the
   derived value is silently lost (this bit the first O4 P2 pass).
