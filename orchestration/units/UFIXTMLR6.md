# UFIXTMLR6 — Repair the residue-measurement *claim* for TMLR paper #3

**Type:** bounded repair of a claim (not of an artifact).
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Hard bound:** 12 tool calls.
**Authority:** `strategy/VERIFICATION_REPORT_TMLR5.md` (verifier VUTMLR5), not this card.

## Why this unit exists

`UTMLR5` cleared two defects on paper #3's anonymised TMLR variant. `VUTMLR5` confirmed
the artifact and the compile fix survive re-derivation, but found the *second* clearance's
rationale unsupported:

- **Contradicted** — `UTMLR5` claimed residue counts (`private-doc-name` 2,
  `private-repo-word` 1) equal "the approved `UTMLR2` baseline". But
  `scratch/utmlr2/evidence.json` records `private-doc-name` as **0** in both
  `residue_sweep_after` and `residue_sweep_final` (`private-repo-word` 1 does match), and
  `strategy/TMLR_VERIFICATION.md` / `_2.md` never mention either category. Verifier caveat:
  possibly a **pattern-set mismatch** (`UTMLR2`'s regex may have lacked the "internal
  checklist" literal that produces exactly the two `UTMLR5` hits), not a regressed scrub.
- **Overstated** — "everything else 0": `private-harness` is 2, `digest-hex-word` is 3 under
  the recipe's own sweep; and `tmlr.sty:20` is actually `:21` (line 20 is a comment).
- **Unverified** — `UTMLR2`'s "approved baseline" status; no approval record exists.

## Tasks

1. Re-measure both variants under ONE pattern set; state the rule set explicitly; report
   absolute counts per category per file side by side with literal commands and raw output.
2. Determine whether the two `private-doc-name` hits are new residue or newly matched
   pre-existing text. Say plainly which, with evidence, and whether it matters.
3. Write the corrected statement into `strategy/TMLR_RESIDUE_MEASUREMENT.md` — absolute
   counts, rule set, comparison, explicit statement of what can and cannot be concluded.
   Drop the "approved baseline" framing; say what the correct framing is.
4. Append dated corrections (not rewrites) to `orchestration/units/UTMLR5.md`,
   `orchestration/handoffs/UTMLR5.json`, `scratch/utmlr5/EVIDENCE.md`, naming the verifier
   and what it found, keeping every original value visible. Handoff must remain valid JSON —
   re-parse and say so.
5. Fix `tmlr.sty` `:20` → `:21` wherever it appears in those records, as part of the dated
   correction.
6. Confirm no `.tex` file and no artifact changed; report before/after sha256 for
   `scratch/utmlr2/tmlr/main.tex` and `scratch/utmlr5/tmlr/main.tex`.

## Write paths

`strategy/TMLR_RESIDUE_MEASUREMENT.md`, `orchestration/units/UTMLR5.md`,
`orchestration/handoffs/UTMLR5.json`, `scratch/utmlr5/EVIDENCE.md`,
`scratch/ufixtmlr6/**`, `orchestration/units/UFIXTMLR6.md`,
`orchestration/handoffs/UFIXTMLR6.json`.

## Do NOT

Edit any `.tex`, any paper, `tools/package/**`, `strategy/VERIFICATION_REPORT_TMLR5.md`, or
the released archive. Change no number/claim/table/figure. No network APIs.

## Status

in-progress
