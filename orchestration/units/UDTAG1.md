# UDTAG1 - neutralise five internal decision-document numbers in a release-tree copy

**Status: done** (2026-10-16). Hard bound: 30 tool calls; used 29.

## Purpose
The 184-identifier census never listed five project-specific strings in the chosen release tree, and
`strategy/NONCENSUS_CLASSIFICATION.md` (UNONCENSUS2) ruled that 16 of the 19 such strings must survive
because the CC BY 4.0 manuscript already names them. Exactly five - `D35`, `D44`, `D09`, `D15`, `D25` - are
internal decision-document numbers that index the withheld research record (`D35`/`D44` also leak internal
paths). This unit replaces those five, in a **copy**, with NEUTRAL-TAG/v1 tokens and proves nothing else moved.

## Write paths (checked against concurrently running units)
`scratch/udtag1/**`, `strategy/DTAG_NEUTRALISATION.md`, `orchestration/units/UDTAG1.md`,
`orchestration/handoffs/UDTAG1.json`. No overlap with the always-forbidden set (`scratch/ubij1|ubij2|ubij3`,
`scratch/upack1`, `scratch/unoncensus1|2`, `scratch/uver20|21|22`, `scratch/ufix25|26`, `scratch/uwire1|2`,
`repro/**`, `orchestration/units/UBUILD1.build.sh`, `/home/zer0null/research-publish-packages`).

## Method
Copy `scratch/ubij3/tree-three-r2` -> `scratch/udtag1/tree-five` (verified `diff -rq`), then run
`scratch/udtag1/dtag_one.py`: house style copied from `scratch/ubij3/bij_three.py` (structural mask for
prose-valued JSON string literals, word-boundary regex `(?<![A-Za-z0-9_.\\])` + `(?![A-Za-z0-9_$])`,
fail-closed inside-stimulus census guard, map printed as counts only). Map: D09->P02, D15->P03, D25->P05,
D35->P04, D44->P01. 17 of 45 files rewritten; 0 residual occurrences.

## Result
* Inside-stimulus census delta **+0** (2171 occurrences / 30 distinct keys, before and after).
* `verify/recompute-claims.py` exit 0 in the emitted tree; output byte-identical to the base copy; **no
  published claim number moved**.
* compileall 0; train.jsonl 800/0 bad; dev.jsonl 200/0 bad; disagreements.jsonl 18/0 bad.
* parse_fixture.py 1 and compare.py 1 **in both trees** - pre-existing: `reflex-decisions.sandbox.ts` is
  not shipped, so `cases.json` is never produced. No diagnostic value could move (metrics.json byte-identical).
* Manifest regenerated from disk (22,325 bytes, sha256 `8527a83be8c7259d230a1eb90452ad818287747dc6646e5b9d21f820cd03c8c1`), independent checker PASS (0 missing / 0 hash /
  0 size / 0 unlisted / 0 duplicate), not hand-edited.
* Idempotent: two builds `diff -r` 0 lines; 44 payload files byte-identical; manifests identical modulo
  `generated_utc`; two in-place regenerations give the same sha256.
* No path rename was needed; the shipped tools contain no D-number, so nothing was rewired (the conflict
  rule in the card was never triggered).
* `LEAD` and `no-union` left untouched (no denotation found anywhere - not renamed on a hunch).

## Conflict rule
"If renaming a path breaks a shipped docstring or a `verify/` script that hardcodes it, stop and report the
conflict rather than editing the tooling." No filename contained any of the five strings, so no path broke
and no tooling was edited. `verify/recompute-claims.py`, `second-labeller/compare.py` and
`second-labeller/parse_fixture.py` contain no D-number.

## Blocker
None for this unit. Two things are reported rather than fixed: the pre-existing `reflex-decisions.sandbox.ts`
packaging gap (parse_fixture/compare cannot run as shipped) and the manifest's `source`/`source_sha256`
exposure, which is an open author decision.

## Next unit hint
Verify this unit: re-run `dtag_one.py` into a fresh directory, re-run the census with `PYTHONHASHSEED=0`, and
re-run `check_emitted.py`. Then decide (a) whether the shipped package is supposed to carry
`second-labeller/reflex-decisions.sandbox.ts` so parse_fixture/compare can run at all, and (b) the `source`
exposure policy.
