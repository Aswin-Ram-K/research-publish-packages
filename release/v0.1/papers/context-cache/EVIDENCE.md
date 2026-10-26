# EVIDENCE.md — how each number was obtained, and how far it can be trusted

This is the audit trail behind `MANUSCRIPT.md`: the instrument, the derivation of each
quantity from the rows, what an independent verifier re-checked, and what remains unverified.
It is deliberately not a narrative of the units — the unit cards are
`orchestration/units/U*.md`, their self-reports are `orchestration/handoffs/U*.json`, and the
independent check of the source units is `orchestration/handoffs/CX-V2.json`.

## 1. The instrument

All live rows were produced against one SGLang endpoint at `http://serving-host`
serving `occamy-1.0`. The served configuration, captured once at
2026-10-20T23:03:42Z in `cells/U2/server_config.json`, records
`architectures: ["Qwen3_5MoeForConditionalGeneration"]`, `model_type: qwen3_5_moe`, NVFP4
weights (`models--Accio-Lab--occamy-1.0-NVFP4`), `served_model_name: occamy-1.0`,
`chunked_prefill_size: 8192`, `max_running_requests: 5`, `max_mamba_cache_size: 64`,
`linear_attn_backend: triton`, a KV pool of 1,306,681 tokens, and the radix cache enabled
(`radix_cache_disabled: false`).

Cache accounting uses the server's own report: `usage.prompt_tokens_details.cached_tokens`,
null on a cold request and coerced to 0 by the driver. `uncached = prompt_tokens -
cached_tokens` is computed from those two integers, so every uncached figure in the package
is a server statement, not a client estimate. Requests are serial. Prompts are assembled from
in-cell corpora, each cell carrying a per-cell salt so that a prompt cannot be reused across
cells by accident; the salt is also why two arms that should render identical text differ by a
2–3 token prefix, which matters in §4.

The units divide as follows. U2 measures the repeat grid. U4 tried to measure break cost of
three rewriting policies. U4b measures fan-out placement. U5 measures content retention and
accuracy under compaction. U9 measures hit/miss TTFT. U10 isolates the immediate-repeat miss
at 64-boundary lengths. U13 and U14 are offline library changes (fork marker, append-note
policy). U15 is the four-arm comparison that the title result rests on. G3-LIMIT-V2 drives the same
policies past a real context budget, which is the one thing U15 and G3 under different names
could not do.

## 2. Mechanisms, unit by unit

### 2.1 U2 — the grid for byte-identical repeats

`cells/U2/u2_cache_rows.jsonl` (88 rows) holds 44 warm repeats over 44 lengths from 314 to
1,550 tokens, plus the cold priming request for each. For every warm row the rows give
`prompt_tokens`, `cached_tokens` and `uncached`. The derivation is a comparison, not a fit:
`cached == 64 * ((L - 1) // 64)` holds on 44/44 rows and the uncached residual is 0 on 44/44
(C37). The `(L-1)` form is the corrected boundary form; the naive `64 * floor(L/64)` fails on
boundary lengths, and U10 exists because of it. The corpus contains no length that is a
multiple of 64, so U2 cannot by itself distinguish the two forms — the discrimination comes
from U10 (C40), and CX-V2 says so explicitly.

### 2.2 U4 — what the break-cost experiment actually did

`cells/U4/u4_rows.jsonl` (438 rows) is three sessions x 44 turns over three rewriting
policies plus a 42-row control; `u4_events.jsonl` (54 rows) schedules compaction at turns 12,
17, 22, ..., 42, seven events per session (C14). "Break cost" was defined as the uncached
tokens on the turn the compaction lands. The paired quantity in `c11()` is the fork-minus-
summarise difference at matched `(session, turn)` events; it is 0 on 18 of 21 pairs, with a
maximum absolute difference of 64 and a permutation median of exactly 0 (C11). The three
nonzero pairs are listed by C12: -64 (u4-s1 t17, prompt 6,174 vs 6,172), +64 (u4-s1 t32,
6,145 vs 6,143) and -64 (u4-s3 t17, 6,224 vs 6,221). Each disagreement is one 64-token chunk,
and the prompt lengths differ by 2–3 tokens — the size of a salt offset.

The reason is in the driver. `cells/U4/u4_cell.py` (sha256
`d69c8bc059f677237c59c59aa4befde61eb7134e4a10017957e54b1c18ed7022`) sets
`RENDER = RenderPolicy.NAIVE_APPEND` for every arm and never imports `POINTER_FORK` (C13).
The renderer serialises `node.text` and ignores `node.kind`, so the two policy objects produce
the same bytes. The offline replay `cells/CX-V2/u4_recon.py` rebuilt both arms and reported
body digests equal 44/44 in every session for the library as it stood; re-running it today
(C16) reports 11/44, because U13's marker now separates the arms from turn 12 (2,857 vs 2,857
body bytes at turn 1; 19,998 vs 20,173 at turn 12). The historical 44/44 and the current 11/44
are both correct measurements of different libraries, and the difference is the proof that the
old comparison was a comparison of one renderer against itself.

### 2.3 U4b — placement

`cells/U4b/rows.jsonl` (24 rows) is three arms x eight branches. The rows are read arm by arm;
there is no modelling. Prompt is 15,400 tokens in every arm; per-branch prompt is 1,925;
uncached per branch is 1,925 for the first two branches and 133 for the remaining six in arms
A and C, and 1,925 for all eight in arm B (C04). B/A = 3.3133 and C/A = 1.0000 (C05) — the **superseded pre-G5** single-fan-out values,
replaced as the paper's effect size by cell G5's race-free B/A = 6.744 [4.045, 9.443] (C53);
they survive here because the mechanism is read from these 24 rows. The
first-branch duplication in A and C is the insert race: the second request was issued before
the first request's cache insert completed, so it missed (branch 2 cached 0). The
counterfactual with seven warm branches gives 2,856 uncached and B/A = 5.3922 (C06) — a
race-corrected value for this cell, **also superseded** by G5's 6.744 and therefore not an upper
bound on the fan-out ratio.

### 2.4 U5 — content retention and accuracy

`cells/U5/u5_raw.jsonl` (760 rows) holds 190 cases x four conditions. Accuracy is the row's
`correct` flag; the retention measure is the row's gold-line retention computed by the
harness's checker and stored per row, so retention is re-counted rather than re-judged (C09).
Agreement is the fraction of cases in which two arms chose the same option letter
(`parsed_letter`), which is the strictest comparison the rows support; it is not a comparison
of confidences (C10). McNemar is exact on the discordant pairs (C08). The three compacted-arm
companions are 190 rows each; the shallow arm is a separate 190-row condition.

Two structural facts about these rows must be carried with any use of them. First, the deep
`fork` and `summarise` prompts are byte-identical (C03, 190/190), so the "fork" arm is a
second sample of the summarise policy and its 69.5 % accuracy is not evidence about forking.
Second, the identical-prompt arms agree only 174/190 (91.6 %), so 91.6 % is the noise floor
for this agreement measure with this sampling configuration; the 86.8–87.9 % agreement between
baseline and compacted arms is a small difference above that floor, not a large one. The
retention difference is not subject to this floor: 190/190 versus 0/190.

### 2.5 U13 and U14 — making the policies distinct

`cells/U13/u13_fork_marker.json` records the offline probe: the fork root text now begins
with `[fork] replaces head through <last folded head node_id>; forked_from <pre-compaction
chain_hash>`, a 171-character first line followed by a blank line and the same summary the
summarise policy writes. `c15()` re-derives the three digests from the probe: fork `b812c99d`,
summarise and the legacy fork `dc591b7e`; the fork prompt is 175 characters longer (7,966 vs
7,791), about 44 estimated tokens, and the text after the marker is byte-identical to the bare
summary (C15). `cells/U14/u14_append_note.json` records the append-note policy: the head
digest is unchanged by compaction (`2a38a86f` before and after) where summarise changes it
(`b424ae2e`), at +231 tokens per note against the summariser's reduction to 1,028.

These are library-level facts, not endpoint measurements, and they are verified by unit tests
rather than by request rows: U13's red→green was 5 failed / 1 passed against the mutation,
then 51 passed; U14's was 7 failed / 4 passed, then 11 new and 1,125 total passing with one
pre-existing unrelated failure. They are cited here because §5 and §6 of the manuscript depend
on the arms being genuinely distinct.

### 2.6 U15 — the four-arm comparison

`cells/U15/rows.jsonl` (160 rows) is four arms x 40 turns on `corpora/endtoend.json`
scenario E1 (turns 1–40), with compaction scheduled at turns 18 and 35, derived once from the
R arm so that all arms compact together. Compaction is signalled per row by
`scheduled_compaction` and the break schedule is re-derived per arm in C26. Totals are sums
of `prompt_tokens`, `cached_tokens` and `uncached` over the 40 rows (C17–C20); hit rate is
cached/prompt. The ratios (C21) are quotients of those totals. The decomposition (C22) takes
R's excess over C (20,649) and splits it into the two break turns' net cost (1,620, measured
as R minus C on the two break turns) and the remainder (19,029). The per-turn means (C23) are
over turns 19–34, i.e. between the first and second compaction; the counterfactual (C24) is
C's total plus R's net break cost, giving 32,143. The window quantities (C25) are the first
and last prompt of arm A and the prompt mass over 40 turns.

The stub summariser is deterministic and offline (750 characters, about 188 tokens), so the
compaction step is reproducible from the rows alone; nothing in this arm depends on a
generated summary. `max_tokens` was 4, thinking disabled, streaming on, requests serial.

### 2.6.1 G1 — decomposition of U15's 1.700x into break cost vs window truncation

`cells/G1/rows.jsonl` (264 rows) is two arms (E = summarise-in-place, F = fork) x 44 turns
over 3 sessions, with compaction scheduled at turns 18 and 35 in both arms, so that each arm
sees 6 matched break events. Rows carry `is_break_turn`, `uncached`, `prompt_tokens`,
`cached_tokens`, `est_chain_tokens_before/after` and `prefix_sha256` per turn. Totals and
per-break gross costs are in `cells/G1/analysis.json`. Results (C44):

- per-break gross mean `uncached`: E = 1,728.0, F = 1,664.0, ratio = 1.0384615;
- only 2 of the 6 break events fall within 10 % of each other (ratios 0.80, 0.875,
  0.9375, 0.9375, 1.4, 1.5);
- total uncached E/F = 0.9739 (E 127,824 vs F 131,248);
- post-compaction turns 19–44 show an E-F prompt imbalance (mean -165.1 tokens, est
  delta mean -43.0, 81 of 81 turns imbalanced).

Conclusion: U15's 1.700x (A vs R) does **not** survive decomposition as a break-cost effect.
Only 1,620 of R's 20,649-token excess (7.8 %) was net break cost; 19,029 (92.2 %) was
post-compaction steady-state window truncation (u15_decomposition_note, analysis.json).
The per-break fork/append cost (1.038) is within measurement noise of the edit cost, so the
fork marker does not change the break cost. Regeneration command:
`.venv/bin/python experiments/context-cache/cells/G1/g1_cell.py` (rows) and
`.venv/bin/python papers/context-cache/recompute.py C44` (claim check).

### 2.7 U9 — latency pairs

### 2.7 U9 — latency pairs

`cells/U9/u9_trials.jsonl` (139 rows) contains 45 hit, 43 miss, 20 prime, 20 noise-hit, 10
noise-cold and 1 calibration trial (C36). Each hit row is paired with the miss row of the
same `(length_target, rep)`; the pair length used in every fit is the measured
`prompt_tokens`, not the target, as CX-V2 requires — the measured values are 1,024, 2,028,
3,955, 7,863, 15,701 and 31,415 because prompts are built to hit token counts approximately.
Medians are taken within each length (7 pairs each, 10 at 1,024 including noise repeats);
ratios are hit median over miss median. Power-law exponents are least squares on log-log of
the six medians; the OLS slopes are least squares of time on measured tokens across the 42
paired rows (C33, C34). The sign test is exact binomial on 42 paired differences (C35).

### 2.8 U10 — the boundary

`cells/U10/u10_rows.jsonl` (65 rows) is phase 1; `u10_rows_p23.jsonl` (55 rows) is phases 2
and 3. A "miss on the immediate repeat" is a row whose role is `repeat1` and whose
`cached_tokens` is 0 while its prompt continues a prefix already sent. C40 counts these per
length directly. Fisher's exact test is two-sided on the 5x2 table (C41). C42 reads the delay
and interleaved phases; C43 reads the cold phase. The rows are 5 per boundary cell, which is
why C41 also reports the wider pool from the second phase: the pooled 35/35 versus 0/15 is the
stronger statement, and both are given.

### 2.6.2 G3-LIMIT-V2 — compaction forced by the context limit

`cells/G3-LIMIT-V2/rows.jsonl` (2,780 rows, sha256
`589662cef35cbdf6c54b3f75ff11dff9a86e618fc8c77fa3dbcc0d5a2d573382`) is eight arms at two
budgets — six compacting arms (`S`, `F`, `S-k800`, `F-k800`, `S-ptr`, `F-ptr`) against a
compaction-free baseline that renders the same bytes (`B` for `append_note`, `B-ptr` for the
pointer renderer) — 160 turns at 32k and 150–190 at 64k. Rows carry `prompt_tokens`,
`cached_tokens`, `uncached_tokens`, `est_chain_tokens_before/after`, `compacted_this_turn`,
`compactions_so_far`, `trigger_reason`, `keep_last` and the trigger's own bookkeeping.
`cells/G3-LIMIT-V2/events.jsonl` (18 events) records each fold: `tokens_before`, `tokens_after`,
`kept_tokens`, `edited_node_ids`, `forked`. Derivation (C62):

- a small number of compactions per arm, located from `compacted_this_turn`: turn 71 at 32k
  (and 137–140 for the second), turn 143 at 64k;
- the **control segment** is every turn before the arm's first compaction. Matched turn for
  turn against the baseline, the delta is −11.8 to +51.0 uncached tokens per turn over the
  twelve arm-instances and **0 of 12** bootstrap intervals excludes zero;
- the **post-boundary segment** is every turn after it. The same matched contrast gives
  +134.6 to +747.2 uncached tokens per turn **as an arm mean** (twelve means over 27–89 turns
  each), and 11 of 12 intervals exclude zero (pointer fork at 32k is the exception: +134.6,
  [−12.8, 285.9]); a mean is not a bound on a turn, and the per-turn figures in the same
  segment are **−927 to +5,473**, with **all 12 arms** carrying at least one turn below
  their baseline. Both extremes are turns around the baseline's own window drop, where the
  baseline still holds 30,656–31,616 cached tokens (32k arm turns 138–139/142; 64k arm turn
  151 is a separate `cached_tokens` 0 row with a larger prompt, not a window effect);
- the **resting-turn segment** (the post-boundary turns that do not follow one of the
  baseline's own window drops) changes no arm's range and no arm's significance, but it
  moves one mean: the pointer fork at 32k falls from +134.6 to **+112.5**, its interval
  [−33.7, 264.3] crossing zero — the one arm whose resting cost this cell cannot resolve;
- the **boundary turn itself** costs 1,826–3,033 uncached tokens across all 18 compaction
  rows (the 2,972 upper bound is `F-ptr`'s first compaction alone; the second-compaction
  rows reach 2,808–3,033), against the baseline's own window-drop turns at 1,236–1,321 —
  six drop rows, not one per budget, because the 32k baseline drops twice (1,236 at turn 71
  and 1,320 at turn 141, whose pointer-renderer twin is 1,237 / 1,321);
- the **resting window** after the boundary is visible in the last-turn prompts: baseline
  9,896 (32k) and 22,063 (64k) against the compacting arms' 11,009–13,546 and 14,197–23,765.
  The arms' mid-run boundary rows show the same thing directly: at 32k, arm `S`'s second
  boundary restarts it at 2,812 tokens on a turn where the baseline stands at 30,717.

The intervals are percentile bootstraps over turns (10,000 resamples, seed 20251023) of the
per-turn difference, the recipe the cell's own analyser used, re-implemented in
`papers/context-cache/recompute.py`'s `c62` and re-deriving the same numbers from the rows.
The trigger on all 18 events is `projected_prompt_exceeds_budget_headroom`, i.e. the cell
compacted when the projected prompt came within a headroom of the budget rather than after an
overrun — that is what makes the measured quantity "compaction at the limit's edge". Prompt
sizes were estimated from characters with a calibrated regression (slope 0.26893, intercept
−219.1) because no tokenizer was reachable from the driver; only the appended delta was ever
estimated (the server's own `prompt_tokens` gave the prefix), and at trigger turns the error
was a median of −7 tokens. Regeneration: `.venv/bin/python
experiments/context-cache/cells/G3-LIMIT-V2/g3v2_cell.py` (rows) and `.venv/bin/python
papers/context-cache/recompute.py C62` (claim check).

### 2.6.3 MATRIX-FOLD — the 2x2 that separates engine from model

Four row files measured the same 32k battery schedule — arms `R`/`A`/`C`/`H`, turns 1..71,
284 rows per cell, 1,136 paired rows in all:

| cell | model | engine | config | bytes | rows | sha256 |
|---|---|---|---|---:|---:|---|
| MOE-VLLM | occamy-1.0 (MoE) | vLLM 0.27.1 | V3 | 283,033 | 306 | `6658227689a35eeedbe3e2645a9093fb099771ca5b6793bb9bb17582758a07a1` |
| G3 | occamy-1.0 (MoE) | SGLang | S0 | 721,318 | 888 | `d6313f72c2eca0bc2192922bfcf1bad08c853c9dd11fbd67b0e65f85428759ee` |
| WIN-VLLM | qwen3.5-9b (dense) | vLLM 0.27.1 | V1 | 579,172 | 692 | `a606ca06a23145a52d2bb50f82baff1b6e8d0689164c80ce987c441ce83cf1d7` |
| DENSE-SGL | qwen3.5-9b (dense) | SGLang | P1 | 712,756 | 894 | `7a0beb4e7d67d0df97f7b4b5b7c0e9388dea94d0a74aa39a3c1a5d1ea07ef80d` |

All four digests are also in `CLAIMS.md` "Source rows and digests". The four
cells share one driver, so their prompt prefix digests and lengths match on all six cell
pairs (`prefix_sha256` 284/284, `chars` 284/284); the chat template moves `prompt_tokens` by at most 4 on 140 of the 284 rows in the
SGLang cells, which is why the pairing is on `(arm, turn_id)`, not on a prompt hash. No
compaction fires at 32k, so the four arms are salt-separated replicates of one schedule and
the **turn** is the resampling unit.

Derivation (C63): average `uncached` over the four arms in each cell to get four 71-turn
vectors; the **engine** effect is the mean of (MoE/vLLM − MoE/SGLang) and (dense/vLLM −
dense/SGLang); the **model** effect is the mean of (dense/vLLM − MoE/vLLM) and (dense/SGLang −
MoE/SGLang); the **interaction** is the difference of the two engine-within-model contrasts.
Intervals are percentile bootstraps over the 71 turns (10,000 resamples, seed 20251023) —
C62's recipe, applied to turns rather than rows because the arms are replicates. Result:
engine +549.33 [462.4, 631.9] (66/71 turns positive), model -400.02 [-474.2, -326.5]
(8/71), interaction -403.63 [-479.7, -328.5] (8/71); engine within MoE +952.96 [805.7,
1,099.8], within dense +145.70 [81.2, 210.5]; model within vLLM -803.65 [-953.6, -655.2]
(8/71), within SGLang +3.61 [0.0, 10.8] (1/71). Grand mean 1,006.2306; engine share 0.5459,
model share -0.3975; engine/model -1.3733.

MTP CORRECTION: the vLLM dense cell is the Round-2 re-measurement (`state/config/rows.jsonl`,
284 rows, `stack=vllm-0.27.1`, `config_id=O4`, hit 0.817432, 879.0669 uncached/turn, CI
[824.7806, 933.3532]). The Round-1 cell carried `--speculative-config mtp`; removing it moved
the cell 2,230.7782 -> 879.0669 (2.54x). The superseded derivation read engine +1,225.18
[1,132.2, 1,313.3] (70/71), model +275.83 [194.3, 357.6] (53/71), interaction +272.23 [190.1,
354.6] (52/71), model within vLLM +548.06, engine within dense +1,497.41, grand 1,344.1585,
engine share 0.9115, engine/model 4.4418 — all replaced by the figures above and retained in
`recompute.py:C63_SUPERSEDED`. Because the R2 cell writes no rendered-prompt `chars` and
digests the request rather than the prompt, the prompt-identity contrast covers the three
Round-1 cells (3 pairs, 284/284 rows) rather than all six.

The mechanism line is measured, not inferred: the hot-row unit each engine reports is 64 in
both SGLang cells and 2,096 (MoE) / 1,088 (dense) in the vLLM cells (`gcd` over hot rows with
count ≥ 3, `recompute.py C55`). The cell is its own confound inside the engine axis — the
vLLM cells resolved different blocks and the dense SGLang cell ran `--mem-fraction-static
0.22` on the shared GPU — so the engine effect is "these two engine configurations", and the
model axis carries size and architecture together. Regeneration: `.venv/bin/python
papers/context-cache/recompute.py C63`.

## 3. Provenance and independence

| Unit | Self-report (sha256 prefix) | Rows | Verified independently by |
|---|---|---|---|
| U2 | `handoffs/U2.json` `306401131be5d1d1` | `cells/U2/u2_cache_rows.jsonl` | CX-V2 (fit and law-form check) |
| U4 | `handoffs/U4.json` `cfde3153b71c0e6e` | `cells/U4/u4_rows.jsonl` | CX-V2 (confound confirmed) |
| U4b | `handoffs/U4b.json` `0cdca88982e23072` | `cells/U4b/rows.jsonl` | CX-V2 (arithmetic re-derived) |
| U5 | `handoffs/U5.json` `16640c1ba1e2c79e` | `cells/U5/u5_raw.jsonl` | CX-V2 (digest identity, agreement) |
| U9 | `handoffs/U9.json` `0a536672029f8b0c` | `cells/U9/u9_trials.jsonl` | CX-V2 (fits, one-sided label) |
| U10 | `handoffs/U10.json` `314b543167014995` | `cells/U10/u10_rows*.jsonl` | CX-V2 (pooled Fisher) |
| U13 | `handoffs/U13.json` `937a1eb6779d1f56` | `cells/U13/u13_fork_marker.json` | U14 tests (offline) |
| U14 | `handoffs/U14.json` `eb6d1160ae290509` | `cells/U14/u14_append_note.json` | U15 run (arm A) |
| U15 | `handoffs/U15.json` `e9dde675c3880623` | `cells/U15/rows.jsonl` | CX-V3 (PASS, 2026-10-21; see §5) |
| G1 | `handoffs/G1.json` | `cells/G1/rows.jsonl` | C44 (this document) |

**What CX-V2 verified.** The verifier re-ran the source units' evidence commands rather than
trusting their cards, and returned overall **fail**: it refuted the claim that `render.py` had
been rewritten mid-run (pins before and after the batch are identical,
`4184c9321b9a9406`; mtime 18:07:16, batch start 18:33:49; `source_changed_during_batch: []`),
confirmed the U4 confound more strongly than the author had, resolved two contradictions (the
U2–U4 "grid contradiction" by scope, and the B/A arithmetic), and reduced the U9 significance
claim to the one-sided sign test. Its replay scripts are the commands named for C01 and C16.

**What U7 recomputed.** Every value in `CLAIMS.md` was recomputed from raw rows by
`recompute.py` before the manuscript was written; none was copied from a card. Where the rows
and a card disagreed, the rows won and the correction is listed in `CLAIMS.md` and again
below. U15's self-report and its `analysis.json` (`2a828ba792eb5e995a86773c248256710a90287e4bd4ba1536ab9024a3b6a729`)
agree with the recomputation to the last token. Independent verification has since happened:
`orchestration/VERDICTS.md` records CX-V3 **PASS** on 2026-10-21 05:22 — `recompute.py all`
41/41, u5_recon 760/760, 13/13 digests match — with its red→green check on the decomposition
reproduced (1.7002→1.6002 ⇒ `FAIL 4/5`; restored ⇒ `PASS 5/5`).

**Digests of what is quoted.** `papers/context-cache/recompute.py`
`85917e480d1aea24d0d5b85ab75ab0464cd2b950ff6d7622ed093be09716abcc`;
`cells/CX-V2/u5_recon.py`
`6e821915821319b22ee79d7cb19ff092d38a88aa9192515c0e0deb92b7221238`;
`cells/CX-V2/u4_recon.py`
`b1f34efd26d3e3f6d90754987b859af85e8cbe32282e82f823f7392c1c9f815f`;
`cells/U4/u4_cell.py` `d69c8bc0…` (full digest in §2.2).

## 4. Corrections carried into the manuscript

| Source | Said | Rows say | Effect |
|---|---|---|---|
| `units/U4b.md` | 7/7 hits give 3,856 uncached and B/A 3.99 | 2,856 and 5.3922 (C06); superseded by G5's race-free 6.744 [4.045, 9.443] (C53) | the projection is corrected upward to 5.3922, and the single-fan-out 3.3133 with it is superseded as the reported figure; neither is a bound on the 8x8 result |
| `handoffs/U4.json` | warm-append residual 0.9–2.7k tokens | 832–7,936, median 1,792 (C38) | the append deviation is larger and its range is restated |
| `handoffs/U4.json` | edit-vs-fork "REFUTED" | the comparison measured renderer identity (C13, C16) | the hypothesis is untested, not refuted; §5 of the manuscript is built on this |
| `units/U4.md` | 454 live requests | 451 logged (438 batch + 13 probe); 3 smoke sends are card-only (C14) | RUN.json records the logged figure and the caveat |
| `handoffs/CX-V2.json` | replay bodies identical 44/44 | 11/44 under the current library (C16) | not a contradiction: U13 changed the library after the check |

None of these corrections changes the U15 result, the fan-out result, or the retention result.

## 5. Limits of this evidence

- **Independent verification of U15 is on record.** CX-V3 ruled **PASS** on 2026-10-21
  05:22 (`orchestration/VERDICTS.md`): `recompute.py all` 41/41 and its red→green check
  1/1 reproduced, so the 1.700x figure is verified by a different agent.
- **G1 closes the break-cost half.** G1 (C44) independently re-derives the break-cost
  decomposition (1.038) from 264 rows; it does not verify U15's total-uncached comparison or
  accuracy; CX-V3 has since ruled PASS on that check (2026-10-21 05:22).
- **No instrumentation.** The server exposes counters and configuration but the rows do not
  carry per-chunk provenance. The reason R re-prefills ~1,660 tokens per turn and the reason
  warm appends deviate from the grid are described, not demonstrated; both are named as
  hypotheses in `GAPS.md`.
- **Single endpoint, single model, single seed.** See `MANUSCRIPT.md` §11. In particular the
  hybrid mamba/linear-attention stack is where the grid and append results are most likely to
  be model-specific, and it is the only stack that was measured.
- **The stub summariser is not a model.** The compaction numbers are exact for a deterministic
  750-character stub; a model-written summary could change both the token cost and the
  retention. This applies to G3-LIMIT-V2 as well: its folds use the same deterministic stub,
  so the boundary band (+134.6 to +747.2 on the arm means, −927 to +5,473 per turn) is the
  cost of *that* fold text, not of a model's.
- **G3-LIMIT-V2 has no independent verifier yet.** C62 is an author-side recompute from the
  rows; the numbers in §6a are re-derived by one command but not yet re-checked by a different
  agent.
- **MATRIX-FOLD has no independent verifier yet either.** C63 is an author-side recompute from
  four row files (§2.6.3); the 2x2 is one band (32k, 71 turns), one seed, one GPU, and its
  model axis carries size and architecture as well as MoE-vs-dense.
- **U5's accuracy comparisons sit on a 91.6 % identical-prompt noise floor.** Retention does
  not; agreement figures must be read against that floor.
- **The U5 replay's prompt digests match on 570/760 rows, and the 190 misses are exactly the
  deep/fork rows.** They miss because the current library's fork renderer emits U13's marker
  and U5's rows predate it; the rows' fork digests equal the *summarise* digest, which is
  C03's finding arrived at from the other direction. C01's byte-identity is checked on
  rebuilt chains and covers all 760 cells; nothing in the manuscript depends on the 570/760
  match rate.
