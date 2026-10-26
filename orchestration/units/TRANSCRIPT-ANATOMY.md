# UNIT CARD — TRANSCRIPT-ANATOMY

**Status:** done · **Parent:** `session-7c91986e-3de7-4b15-90c3-a5feb729db96` · **Mode:** read-only analysis
(no network, no live model requests), writes confined to the three declared paths.

## Purpose

Quantify, from real DSH session transcripts, how much of the token-turn bill is tool-result body mass,
and how much a "pointer + warmpool" context design would remove under an explicit pointer-floor model.

## Hard bound

≤35 tool calls (used **18**); ≤8 sessions and ≤120 MB decompressed (used **6 sessions / 86,526,484 B**);
skip any file that fails to parse twice (none did). Never ask the user; choose the conservative default
and record it.

## Write paths (exclusive)

- `orchestration/units/TRANSCRIPT-ANATOMY.md` (this card)
- `scratch/transcript-anatomy/` — `analyze.py`, `results.jsonl`, `scan.tsv`, `sizes.tsv`, `REPORT.md`
- `orchestration/handoffs/TRANSCRIPT-ANATOMY.json`

Nothing outside these was written; `experiments/`, `dockets/`, `release/`, `papers/` and every target
repo were not touched.

## Method

1. Corpus enumerated at `~/.dsh/sessions/<slug>/<session-id>/session.jsonl.zstd` — 2880 files, 753
   workspace dirs, 3.9 GB. All multi-frame zstd, so no header size; sizes streamed and counted.
2. Six sessions selected for shape diversity under the byte cap (two long/result-heavy, the
   58-compaction maximum, one 0-compaction baseline, one DSH-testing session; **no session exists under
   this workspace's slug**, so that slot was filled by a sixth >50-step session).
3. `analyze.py` streams `zstd -dc` line by line (never materialising a file) and accumulates global step
   ordinals, `tool/call` lengths, `tool/result` body lengths, `usage` triples and compaction ordinals.
4. Attribution computed twice — the brief's closed form `Σ body_i × (N − i)` and a compaction-aware
   `Σ_steps Σ_resident body_tokens` — so the persistence assumption is testable.
5. Counterfactuals re-derive the per-step bill (`inputTokens + cacheReadTokens`), removing resident body
   tokens and adding the replacement pointer lines; a body smaller than a pointer is never replaced.

## Key results

| quantity | value |
|---|---|
| sessions / decompressed bytes | 6 / 86,526,484 |
| Σ `inputTokens` (contract bill) | 243,857,351 |
| Σ `inputTokens + cacheReadTokens` (prompt bill) | 516,808,519 |
| body stock | 1,566,248 tok @4.0 c/t = **0.64 %** of the input bill |
| body **token-turns** | **134,114,144 = 25.95 %** of the prompt bill (55.0 % of the input bill) |
| naive ÷ live overcount | 1.02× (no compactions) … 13.02× (14 compactions) |
| pointer floor | p 240–1,061 chars median, r 1.3–12.2, t̄ 112–428, N_live 11.9–265.7; **flat wins 6/6**; floor 1.17–12.92 % of mean prompt (weighted 10.28 %) |
| depth-2 floor | 1.09–1.91 %; reduction 1.77–7.18× (degenerate 0.99× where N_live ≤ 10) |
| CF1 dedupe / CF2 flat / CF3 depth-2+set / CF3b index-only / CF4 newest-3 | 99.55 / 79.46 / 82.08 / **76.85** / 80.42 % of bill |
| compaction | only S1 drops (−37 %); S2 132 %, S3 129 % of session mean after |

## Schema corrections the brief did not have

- `data.step` is **turn-local**; ordinals must come from counting `step/start` (S6: 45 turns, 304 steps).
- `usage` carries **`cacheReadTokens`** alongside `inputTokens`; total prompt ≈ input + cacheRead. S5
  differs 47× between the two. Four of six sessions report 0, so the corpus cannot be priced uniformly.
- A tool-result body is at `data.message.content[*].content` on a `{"type":"tool-result",…}` part, not
  at a `text` field. A `text`-based extractor returns empty bodies and makes all results look identical.

## Assumptions (full list in the handoff `assumptions`)

`p` = full `tool/call` record length (overstates a real pointer → conservative); body resident from the
step after insertion until the next compaction; 4.0 chars/token primary, 2.11 secondary, `inputTokens`
ground truth; bodies smaller than a pointer are never pointer-ised; CF3 assumes a 10-body working set,
CF3b is index-only; a marker-only pre-scan over 15 files chose the sample; privacy — lengths, counts,
ordinals and hashes only, no message text, commands, code or in-session paths.

## Deliverables

`orchestration/handoffs/TRANSCRIPT-ANATOMY.json` (valid JSON, unit shape) ·
`scratch/transcript-anatomy/REPORT.md` (full narrative and tables) ·
`scratch/transcript-anatomy/{analyze.py,results.jsonl,scan.tsv,sizes.tsv}`.
