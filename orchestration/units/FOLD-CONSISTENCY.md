# FOLD-CONSISTENCY

Status: done. Unit card persisted per AGENTS.md §4.

## Purpose
Consistency pass on `papers/context-cache/FOLD-PROPOSAL.md` (97 lines): close exactly five CLOSABLE-OFFLINE
gaps from `orchestration/GAPS-INVENTORY.md` — #1 engine size, #2 suite tree, #7 index hash, #9 r = 67.1x,
#11 two claimless bucket-(i) items — and change nothing else.

## Bound
16 tool calls. Consumed 12 (read inventory + file, five measurement calls, one edit call, two proof/handoff calls).

## Write paths (declared, no others)
- `papers/context-cache/FOLD-PROPOSAL.md`
- `orchestration/handoffs/FOLD-CONSISTENCY.json`
- `orchestration/units/FOLD-CONSISTENCY.md`

## Method
1. Wrote the handoff stub before any read, per unit contract.
2. Backed the file up, recorded sha256 `c41644be…` / 97 lines / 15,369 bytes.
3. Measured rather than quoted: `wc -l`/file counts over `ptr_engine/` and `tests/`, `python3 -m pytest -q`,
   and re-derived the `index_text` sha256 out of `quality/rows.jsonl`.
4. Applied ten literal replacements, each asserted to occur exactly once.
5. Reconstructed the pre-image (the /tmp backup was gone between calls), proved it by sha256 match, diffed.

## Results
- #1: 9 modules / 1,896 + 1,222 / SPEC 260 -> 10 modules / 3,653 + 13 files / 2,248 / SPEC 499, dated 2026-10-26.
- #2: five branch counts (95/100/153/171/108) -> one tree, `190 passed` (0.24 s this run).
- #7: hash line states the artefact never left `/tmp` (gap #46, UNCLOSABLE) and the hash is over `index_text`
  in `quality/rows.jsonl`; `e81ba025…531d5`, 458 B, 12 `index_lines`, no `AUD-`/`lumen`.
- #9: option (b) — 67.1x marked one corpus scope, 78.3x marked single-unit; no sweep run.
- #11: C80 and C81 drafted from `V-ENGINE-P0.json` checks 6/7, marked drafted-not-ratified; claim table
  extended; `grep -rnoE 'C7[5-9]|C8[01]' papers/*/CLAIMS.md` = 0 hits.

## Not done (by scope)
Rows 20/60 keep `0.22 s`; the run measured `0.24 s`, stated inline in row 32 rather than editing rows outside
the five. Gap #40 (ratification) is an operator action, not a draft.
