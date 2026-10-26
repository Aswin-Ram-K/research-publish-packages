# P2-REPAD — re-measure the grid-aligned arm with the pad precomputed

Card: `425e3e7a-2ae6-45c9-ac5e-b7f0960f0d18` (board), execution `c6ed06c0`.
Unit session: this one. Started 2026-10-24T06:26 CDT.

## Objective

Replace the P2 measurement the previous run produced, because that P2 row was the
**second send** of a same-turn alignment correction: the recorded `cached_tokens`
belonged to the *first* send and the row's cost excluded a send. Re-measure P0, P1 and P2
on **production occamy `:8012`** (the O1 substrate), with the pad computed **before** the
one and only request of each turn.

## Substrate and constraints

- Production `gx10-occamy-nvfp4` on `:8012`; `setup=O1`, `config_sha256=f2efaaac…880c67`,
  grid unit 64. No container started, stopped or restarted; zero variant ports.
- Held `experiments/context-cache/.occamy.lock` for the run.
- Same task content **and same prefix digests** as `cells/R2-PROMPT/O3-REPEAT/` (same salt
  `o3-repeat-20261024T11:05Z-a1`, same frozen renderer `cells/VLLM-CELL/vllm_cell.py`):
  proven by matching `prefix_sha256` on P0/P1 at turns 1 and 71.

## Method (the part that makes the number honest)

1. Arms P0 (renderer `R`, whole-context), P1 (renderer `A`, pointer + newest delta), P2.
2. P2's base bytes are P1's own bytes. `base_tokens` is taken from the **P1 row measured in
   this same run** for the same turn, so the base length is measured, not estimated.
3. `pad_target = (-base_tokens) % 64`, raised to at least 64 (a sub-block tax would not be a
   real alignment test). The filler is `" PAD"` repeated `pad_target` times — the server's own
   `/tokenize` shows `" PAD"` is exactly **one token per repetition** (token 59671) and the
   bytes being padded always end in the same fixed canary, so the boundary is constant.
4. Before sending, a stratified sample of turns (1, 11, 21, …, 71) is tokenized with the
   server's chat-templated `/tokenize` and compared against `base_tokens + pad_target`.
   Any residue is applied to `pad_target` before the send.
5. **One** request per row: `requests_sent=1`, `corrections=0`, `had_correction=false`.
   No correction resend path exists in this script at all.
6. Post-run **self-hit guard**: fails if any row's `cached_tokens` equals a previously sent
   prompt's length without `had_correction`.

## Row schema

`setup stack model config_id config_sha256 arm turn prompt_tokens cached_tokens
uncached_tokens pad_tokens requests_sent corrections had_correction http_status
prefix_sha256` (plus `salt`, `cell`, `prompt_sha256`, `details_present`, `pad_aligned`,
`tokenize_count`, `base_tokens_from_P1`, `wall_ms`, `ts`). No nulls; an unobservable value
is `"unavailable"`.

## Writes (only these)

- `experiments/context-cache/cells/P2-REPAD/**`
- `state/r2-p2-repad.json`
- `state/logs/P2-REPAD-progress.log`
- `orchestration/handoffs/P2-REPAD.json`
- `orchestration/units/P2-REPAD.md`

## Bound and assumptions

- Bound: 30 tool calls / 300 live requests.
- Assumption 1: the `/tokenize` wrapper offset is constant (measured once at G0 on the warm
  text and recorded as `template_offset`); the per-row `pad_aligned` flag is the absolute
  check that does not depend on that assumption.
- Assumption 2: no warm-up repeats are spent per arm (the card does not ask for them); all
  three arms therefore start equally cold, and turn 1 of each arm is reported as measured.
- Assumption 3: production is shared. The run is sequential and salt-unique, so hits cannot
  come from another workload's prefix.

## Verification

- `wc -l cells/P2-REPAD/rows.jsonl` = 213 (71 × 3).
- `rows_multi_send == 0` and `corrections_total == 0` in `state/r2-p2-repad.json`.
- `self_hit_guard.verdict == "PASS"`.
- `pad_aligned` true on 71/71 P2 rows.
- `alignment_gain.mean_aligned_len_minus_cached` reported separately from cost.
