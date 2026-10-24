# UBIJ2 — extend the coherent bijection to the harness's own vocabulary

**Status: `partial`** (deliverable complete and measured; **≤40 tool-call bound exceeded**).
**Write paths:** `scratch/ubij2/**`, `strategy/COHERENT_BIJECTION_EXTENSION.md`,
`orchestration/units/UBIJ2.md`, `orchestration/handoffs/UBIJ2.json`. Nothing else touched; no target repo
written; map M never written or logged.

## Purpose
Extend UBIJ1's proven one-pass lockstep rename (`scratch/ubij1/bij_one.py`, which swept only the 10 `kind`
values and `<kind>-NNN` case ids) to the harness's own vocabulary — record fields, roles, tools/actions,
states and the compound-name leftovers — and measure the result honestly.

## Method
`scratch/ubij2/bij_two.py`, base `scratch/uneutral3/tree-stripped` → mask pinned prose → substitute every
name at definition and use in one pass → unmask → re-mask and abort if the masked count moved.
Rename set: 91 tokens (10 kinds → N01…N10, 3 dotted leftovers → X, 60 fields → F, 11 roles → R, 7 tools → T).
Pristine twin `tree-two-r2` (nothing run inside it) carries the headline numbers; diagnostics ran in
`tree-two`; `tree-two-r3` proves idempotence.

## Headline (pristine `scratch/ubij2/tree-two-r2`)
- 44 files, **3,038,324 bytes**; frozen census **3,118** = inside **1,617** + outside **1,381** + keys **120**
  (base stripped 9,247; UBIJ1 5,364). Complete decode (frozen + 3,676 K-codes) = **6,794**.
- Idempotent: `diff -r tree-two-r2 tree-two-r3` identical; aggregate manifest hash
  `d9b15118decba1902cf22f597ce8b3d7625abb4e8953a409123916fb7262be13`.
- All re-measured metrics bit-intact: routeA 0.34210526315789475 / kappa 0.32520740993294694 / 65 / 120 / 41;
  routeB 0.9052631578947369 / 0.9013584840356494 / 172 / 18; AB 0.3526315789473684; tooling exit 0.

## Blocker / defect (why NOT shippable as built)
Inside-stimulus fell 2,171 → **1,617**: 554 in-stimulus occurrences rewritten because the composed,
rendered `situation` strings in `train.jsonl`/`dev.jsonl` are not fully covered by the masker's needles.
Also `harness/tccommon.py:118` reads `\F19 option:` — the field token `nCandidate` matched `\nCandidate`.
Named fixes in `strategy/COHERENT_BIJECTION_EXTENSION.md` §6. Ship UBIJ1's `tree-one-r2` unchanged.

## Evidence
`strategy/COHERENT_BIJECTION_EXTENSION.md` — exact commands, residual tables, metric table, exit codes,
leftover list, and the unverified list. `scratch/ubij2/logs/` holds the build and tooling transcripts.
