# FOLD-FIX-2 — vLLM TTFT sentence-group repair (values only, automated)

## Objective
Correct the TTFT claim in `papers/context-cache/FOLD-PROPOSAL.md` from the verifier's findings
(`orchestration/handoffs/V-FOLD-RESIDUAL.json`). Values only: no re-analysis, no other claim touched,
classification unchanged.

## Bound
12 tool calls (used 12). Single pass, no retries beyond a grep-string wording fix.

## Sentences found (grep -n: `0.21`, `0.217`, `1.58`, `7.4`, `nine arm`, `nine-arm`, `TTFT`)
- `papers/context-cache/FOLD-PROPOSAL.md:31` — bucket (ii), cold-cache `1.585 s vs 0.217 s`, `2 rows`, limp `8.5x ... withdrawn (C2)`.
- `papers/context-cache/FOLD-PROPOSAL.md:44` — bucket (iii), `8.5x TTFT jump — withdrawn; recomputed 7.4x`.
- No `nine arms` / `nine-arm` string exists in the file; the nine-cells correction was folded into :31.

## Applied facts
- `experiments/miss-law/vllm2/rows.jsonl`: 133 rows (59 `prime`, 74 `measure`), nine cells CAL, CAL-T, G1–G7.
- Old pair mismatched: `1.585 s` = `prime` at `P1_target 6336`, `cached_tokens 0`; `0.216 s` = warm `measure` at `P1 7450`, `cached_tokens 6336`. `0.217` occurs 0 times in the artefact.
- Controlled: cell G6, `P1 7392` residue 0 → `cached_tokens [0,0]`, `ttft_server_s [1.790,1.792]`; neighbour `P1 7394` residue 2 → `[6336,6336]`, `[0.2108,0.2114]`. Ratio 8.5x, warm vs warm.
- Only one residue-0 measure pair exists (G6/7392); no residue-1 warm row exists.

## Edits (4 lines: :31, :44 replaced in place; :94 appended)
- `:31` now states the G6 residue-0 re-bill at full prefix (`cached_tokens 0`), 1.79 s vs 0.211 s, 8.5x warm-to-warm, one-pair limitation, nine cells, and withdraws the mismatched cold/warm pair.
- `:44` now records that any per-turn vLLM TTFT multiple is withdrawn; the measured quantity is a single-cell residue-0 boundary effect.
- `:94` one line added to `## Corrections (2026-10-26)`, naming `V-FOLD-RESIDUAL.json`.
- No claim id added; both sentences were unattached, both stay unattached. Classification line (95) untouched.

## Proof
`grep -c -E '1\.585|0\.216|7\.4x|nine-arm'` = 0; `grep -c '8\.5'` = 3; `grep -c 'G6'` = 3;
`grep -c '## Corrections (2026-10-26)'` = 1; `wc -l` 95 → 96; 4 lines changed (≤12).

## Blocker
None. Note: a residue-1 warm contrast cannot be written from this artefact — the row does not exist.
