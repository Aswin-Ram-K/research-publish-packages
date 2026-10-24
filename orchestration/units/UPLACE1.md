# UPLACE1 — internal-record reference inventory (read-only review)

**Role:** bounded REVIEW unit. **Status:** running.

## Purpose
A verifier found paper #3's abstract cites an internal record by filename+line (`REPORT.md:189`).
Establish the full extent and severity of this class across all three papers, and write a precise
ready-to-apply recommendation. **Do not apply it.**

## Read-only constraint
`UAUTHOR1` is concurrently editing `papers/encoder-crossover-190/submission/main.tex` and
`tools/package/md2tex.py`. No writes to `papers/**` or `tools/**` at all. Scratch work, if any,
goes under `scratch/uplace1/**`.

## Targets
- `papers/encoder-crossover-190/` (MANUSCRIPT.md + submission/main.tex)
- `papers/gated-read-batching/`
- `papers/replay-record-not-decision/`
- shipped package for paper #3: `scratch/uneutral10/package/`

## Deliverables
1. Inventory of every internal-record reference (filename, `file:line`, `§`, dotted key path,
   record locator) with paper, file, line number, in-abstract flag, surrounding clause.
2. Shipping determination per referenced target (path + byte size if it ships; else plainly not).
3. Classification: (a) followable+fine / (b) followable but misplaced in abstract / (c) dangling /
   (d) identifying.
4. `strategy/INTERNAL_REFERENCE_PLACEMENT.md` with exact before/after edit pairs, replacement text
   written out in full; leave-alone items justified.

## Hard bound
15 tool calls. UNKNOWN rather than guessing if a target's shipping status cannot be established.

## Write paths
`scratch/uplace1/**`, `strategy/INTERNAL_REFERENCE_PLACEMENT.md`,
`orchestration/units/UPLACE1.md`, `orchestration/handoffs/UPLACE1.json`.
