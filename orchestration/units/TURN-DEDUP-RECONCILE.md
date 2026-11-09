# UNIT TURN-DEDUP-RECONCILE

**Purpose.** Reconcile the three turn counts the analyser and the rows can produce (48 / 46 / 43), name
the true per-cell n, and say whether the de-duplication is data loss.

**Hard bound.** 26 tool calls; journal first; handoff within 6 calls of the end; verdict row before the
handoff write. Offline: zero requests. `ask_user_question` never called.

**Declared write paths (exactly these).**
`tests/test_turn_dedup.py` (new) · `docs/TURN-DEDUP.md` (new) · `orchestration/units/TURN-DEDUP-RECONCILE.md` ·
`orchestration/handoffs/TURN-DEDUP-RECONCILE.json` · `orchestration/journals/TURN-DEDUP-RECONCILE.jsonl`

**Forbidden, and not touched.** `analyze_stats.py`, `analyze.py`, `cell.py`, `run_longrun.py`, rows,
grades, thresholds, `PARM-1`, any published page.

## Findings

1. **The three counts are three different questions.** Selector = `turn_latency_rows`
   (`experiments/ptr-engine/longrun/analyze_stats.py:805-908`, `TURN_ROW_KINDS` at `:608`), whose own
   de-dup key is `(arm, rep, turn)` (`_turn_key`, `:797-802`) and is **0** on these files. The 48→46 step
   is rule R in the report tool: `latency_report.dedupe` (`experiments/ptr-engine/tools/latency_report.py:202-214`)
   with key `(ts, content_sha256, prompt_tokens, completion_tokens)`, first occurrence kept, applied before
   the analyser (`:310`, `:324`). 43 is distinct `content_sha256` = distinct assistant **response text**,
   documented as a response hash at `latency_report.py:17`.
2. **The quoted triple is G8 (`rows-longrun-v5-tools.jsonl`): 48 / 46 / 43.** v6 (`rows-longrun-v6-tools.jsonl`)
   is 48 / **37** / 43 — the same defect twice as badly. The `c` grid has 48 turns and as few as 9 distinct
   response bodies (`transcript-compact`), which is what disqualifies the content hash as a turn count.
3. **R drops true duplicate measurements — but the wrong copy of each pair.** Every dropped `turn` row shares
   `ts`, `content_sha256`, `prompt_tokens`, `completion_tokens`, `ttft_ms`, `latency_s`, `run_id`, `turn` and
   `rep` with a kept `tool-followup` row; only `kind` and `prompt_sha256` differ. That is the pre-ROW-ATTRIBUTION
   mirror of the last send (`analyze_stats.py:583-601`). Because the frozen definition never selects a
   `tool-followup` (`:848-852`, `:867`), deleting the turn row deletes the **turn**: 48 → 46 (G8) / 37 (G9).
   Correct diagnosis, wrong survivor — data loss relative to the turn metric.
4. **True per-cell n = 48** (48 distinct turn identities, 48 distinct `prompt_sha256`, selector duplicates 0).
   Pooled at 3 reps: **n = 144** per arm. Floor: `min_n_for(0.95) = ceil(3/0.05) = 60`
   (`analyze_stats.py:111`, `:330-335`); `144×0.05 = 7.2 ≥ 3` ✓ (`138 → 6.9`, `129 → 6.45`, all pass).
   p95 rank span via `h=(n-1)q` (`_quantile_sorted`, `:279-288`): n=144 → h=135.85, between order stats
   136–137, 7.2 above; n=138 → 130.15 (131–132); n=129 → 121.60 (122–123).
5. **Plan.** The grid's 144/arm is reachable under the frozen definition and is what the current
   one-row-per-send writer produces (no mirrored pair, so R has nothing to drop). On legacy mirrored tools
   files the tooling prints 3×46=138 and 3×37=111 instead. Smallest fix (not applied — separate card): in
   `dedupe`, on a key collision prefer the row whose kind is in `TURN_ROW_KINDS` over a `tool-followup` row.

## Test

`tests/test_turn_dedup.py` — 8 cases, `PYTHONPATH=src python3 -m pytest tests/test_turn_dedup.py -q`
→ **4 failed, 4 passed**. The 4 red are `test_rule_r_keeps_every_turn_the_definition_selects` and
`test_dedupe_keeps_a_selectable_row_for_every_turn`, × 2 files; message: "rule R deleted 2 of 48 turns …
Data loss, not de-duplication." The 4 green are the a/b/c/d census and the mirrored-twin evidence.

Status: **done**. The analyser is not fixed here.
