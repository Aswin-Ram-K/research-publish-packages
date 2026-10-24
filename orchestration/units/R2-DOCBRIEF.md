# R2-DOCBRIEF — the design rationale for Round 2, written before the numbers land

**Status:** done (partial by construction — see `assumptions`)
**Persisted:** 2026-10-23T20:33-05:00 America/Chicago
**Predecessors read:** `orchestration/handoffs/R2-A2.json`, `R2-A3.json`, `R2-B2.json`, `R2-C.json`,
`R2-D.json`, `R2-E.json`; `papers/context-cache/GAPS.md` §G16; `papers/context-cache/CLAIMS.md` C62/C63.

## Objective

Write the Round-2 design rationale **before** the Round-2 numbers exist: a document that states what
Round 2 will measure, why each arm is in the design, and pre-commits to how a result will be read —
so the arms cannot be chosen after seeing the data. This is a **pre-registration**, not a report.

## Why R2-DOCBRIEF exists at all

Every negative result in the package is a statement about the options that were *tried*, and G16
records that the tried set is narrow: SGLang got `--page-size` (S1=64, S2=128) and one eviction policy
(`slru` at default); vLLM got `--block-size`, `--max-model-len`, `--gpu-memory-utilization`,
`--kv-cache-dtype`. Five research lanes (R2-A..R2-E) then found the documented option space is much
larger than the tried set — and, in two cases, that a *rejection* in the package cites a source that
does not carry the claim. Round 2 is the answered response to G16. Writing the rationale first is what
makes it a pre-registration rather than a narrative fitted to whatever the arms produced.

## Hard bound

- **No live request.** No GX10 access, no lock, no server start. This unit reads disk plus the six R2
  handoffs' already-pinned URLs; it re-derives no measurement.
- **No edits to `papers/**`.** The deliverable is a new design document; it does not amend the
  manuscript, `CLAIMS.md`, or `GAPS.md`.
- Attempt bound: if a figure could not be traced to a named row/cell/handoff in ≤2 lookups, it is
  cited as "design input, unpinned" rather than chased further.

## Writability (AGENTS.md, automated-session rules)

This card's job is **to report**, so it must be writable — `workspace-write`, never `read-only`
(cf. `V-G3FOLD2`, whose verdict could not be persisted at all). The handoff stub was written **first**,
before any other artefact, so that a mid-turn death still leaves a parseable record.

## Write paths (declared)

- `orchestration/handoffs/R2-DOCBRIEF.json` — written first (stub), completed last.
- `orchestration/units/R2-DOCBRIEF.md` — this card.
- `docs/serving-options/R2-DESIGN.md` — the deliverable.

No clash: no other unit is running in this session; the R2-A..R2-E lanes wrote only their own
handoffs and are closed.

## Kill condition

Stop and report `partial` if: (a) a Round-2 arm cannot be given a falsifiable predicted direction, or
(b) a cited figure cannot be traced to a pinned row/cell/claim — the arm is then recorded as
`prediction: unpinned` rather than given an invented number.

## Assumptions (automated session, no answerer)

The card prompt is the whole contract, and it named only the deliverable. Two values were genuinely
missing and were resolved conservatively rather than asked:

1. **Deliverable path.** Not stated. Chosen: `docs/serving-options/R2-DESIGN.md`, beside `MATRIX-2x2.md`
   (which is the Round-1 answer) and the five `R-*.md` lane notes. Rationale: the design is a serving
   document, not a manuscript section; landing it under `docs/serving-options/` keeps it out of
   `papers/**`, which this unit is not licensed to edit.
2. **Scope of "Round 2".** Not stated. Chosen: the served-option space that closes/substantially
   narrows **G16**, scoped to the R2-A..R2-E findings. Rationale: G16 is the only open gap whose
   named closure is "run the documented options", and the R2 lanes were commissioned against it.
   Round 2 is **not** a rerun of the 2x2 (that is C63, already measured) and **not** the binary-gate
   harness's Round 2 named in `strategy/SYSTEM_ITEM_INVENTORY.md:539` (a different program, whose
   `docs/research/EXPERIMENT_PROGRAMME_2.md` does not exist on this disk).

Recorded as assumptions, not decisions: a reviewer may reassign the path or widen the scope without
invalidating anything below, because every claim in the document names its own source.
