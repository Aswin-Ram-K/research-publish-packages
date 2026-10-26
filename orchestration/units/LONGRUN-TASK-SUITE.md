# LONGRUN-TASK-SUITE

**Status:** done · **Bound:** 24 tool calls (used 20) · **Requests:** 0 (offline fixture build)
**Write paths:** `experiments/ptr-engine/longrun/` (new tree), `orchestration/handoffs/LONGRUN-TASK-SUITE.json`, this card.
**Deliverables:** `SUITE.md` (119 lines) + 6 fixtures `fixtures/LR-01..LR-06.json` (`consonance.fixture/1`).
**Why:** every existing fixture is short (4 turns, 12 items); the long-run objective (p95 TTFT, tokens-to-verified-success) had no suite.

## Shape
| task | class | turns | cps | repair trap |
|---|---|---|---|---|
| LR-01 | repo-fix | 48 | 12/24/46 | 30 — refusals are not all funnelled through `_refuse` |
| LR-02 | multi-file-refactor | 64 | 16/32/62 | 38 — registry belongs in resolve.py (it does not) |
| LR-03 | bug-fix-with-test | 56 | 14/28/54 | 34 — 8-char compact hash (it is 6) |
| LR-04 | constraint-survival | 40 | 10/20/38 | 26 — bill is linear (avalanche at residue 0/1) |
| LR-05 | adversarial-debug | 72 | 18/36/70 | 44 — locator dirname proves containment (it does not) |
| LR-06 | doc-sync | 60 | 15/30/58 | 40 — "128 was agreed" (default is 64) |

**Totals:** 340 turns, 18 checkpoints, 6 repair traps, 9 pinned source files, 0 pin mismatches.

## Evidence
- `python3 -c "... [json.load(open(f)) for f in fs]"` → `6 fixtures parsed`, exit **0**.
- Audit: turn numbering 1..N, exactly 3 tagged checkpoints + plant/repair/verify, repair turn after its adoption turn, every pointer range inside its file, every sha256 re-checked → `TOTAL_TURNS 340 CHECKPOINTS 18 TRAPS 6 DISTINCT_PINS 9 PIN_MISMATCH []`.
- Live fact reproduction (offline import): `max_refs 64 | classes 31 | magic ptr-index/1c hashchars 6 B 64`, `(138,True) (46,False) 140`, `content_hash len 71`.

## Assumption (recorded, not hidden)
`LONGRUN-PREREG.md` is a 4-line stub and card `59965afa` is not on the board, so the four arms are defined
operationally in `SUITE.md` §5. Two checks are marked `MEASURE_UNVERIFIABLE` (taxonomy future-completeness,
docstring rationale) and are never scored.
