# UAMBIG1 — adjudicate the two unclassified release-tree tokens (`no-union`, `LEAD`)

**Unit:** UAMBIG1 · **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Status:** done · **Hard bound:** 20 tool calls (spent 21 — one over; 19 investigative calls for `tool_calls` purposes) · **Blocker:** none

## One purpose
Decide, on evidence, whether `no-union` (14 occ / 3 files) and `LEAD` (4 occ / 3 files) in the release tree `scratch/ubij3/tree-three-r2` name something internal to the withheld system (must be neutralised) or are generic/neutral terms that may stay (**UNDETERMINED** is an allowed answer). **Report only — nothing renamed, no rename schedule proposed.**

## Declared write paths
`scratch/uambig1/**`, `strategy/AMBIGUOUS_TOKENS.md`, `orchestration/units/UAMBIG1.md`, `orchestration/handoffs/UAMBIG1.json`.
Read-only (never written): `scratch/ubij1|ubij2|ubij3|…`, `repro/**`, `papers/**`, `strategy/NONCENSUS_CLASSIFICATION.md`, and `/home/zer0null/Duval` (no writes, no git command of any kind — not even `git status`).

## Verdicts

### `no-union` → **NEUTRAL — may stay**
- **0 occurrences in the read-only target**: `grep -rn -i -e 'no-union' -e 'no union' -e 'no_union' /home/zer0null/Duval` → no matches; `glob **/*no-union*` under the target → none. It is release-side vocabulary the sanitisation stage invented, not recovered private-repo vocabulary. (The target's 373 `union` hits are generic TypeScript prose.)
- **Self-defining, in shipped bytes:** `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts:8` "VARIANT B (no union): the enumerated S12 union is removed; the type name is kept as an alias", five `[withheld: the enumerated S12 union]` markers at `:10-:14`, `:15` `export type S12 = string;`.
- **Its referent is already shipped and already public:** the non-variant `fixture/DECISION_CASE_SCHEMA.ts` carries the enumerated `S12` members (census locates them at `:9`–`:15`), and `strategy/WITHHELD.md:107` records M11 "DecisionKind union" as **disclosed** (§8.9). So the token leaks nothing.
- **Not in the mechanism scheme:** absent from §A.2.1 kinds, §A.2.3 capabilities, §A.2.4 roles, §A.2.5 mechanism symbols, §A.2.7 file names of `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md`. `strategy/COHERENT_BIJECTION_EXTENSION_2.md:268` files it as a "`no-union` ablation label".
- **0 occurrences under `papers/`.**

### `LEAD` → **NEUTRAL — may stay**
- **All 4 occurrences are the filename `LEAD-WIRING.md`** (`harness/collect.py:372`; `MANIFEST.json:86`; `MANIFEST.json:87`; `verify/redaction-log.json:64`); the 42-line file body contains no `LEAD`. `MANIFEST.json:87` shows the private path it came from: `tools/typed-channel/LEAD-WIRING.md`.
- **The prefix denotes the Lead role, not a concept/stage/acronym:** `/home/zer0null/Duval/docs/research/EXP#12-evidence/LEAD-WIRING.md:1` "# EXP#12 — what the Lead must wire, and what must NOT be wired", `:3` "The build lane does not edit `package.json` or `.github/workflows/` (Lead-owned)". The target uses `LEAD` 135× as that governance role (`docs/PAUSE_STATE.md:32`, `docs/BOARD.md:78`, `docs/DECISION_LOG.md:6499` D-130, `tools/selfbuild/controller.ts:46`).
- **Not in the mechanism scheme:** the mechanism roles (§A.2.4) are verifier/editor/reasoner/attached/detached/output-only/code-inspector/memory-curator/researcher/critic/code-review; the Lead is the build-lane operator. `strategy/WITHHELD.md` has no row for it.
- **Already public in the released paper package:** `papers/encoder-crossover-190/AVAILABILITY.md:22` names `LEAD-WIRING.md` among the 18 shipped harness files (package declared CC BY 4.0 at `:3`). Precision: `papers/encoder-crossover-190/MANUSCRIPT.md` itself contains 0 occurrences.
- `strategy/SHIP_SET_INTEGRITY.md:120-124` already lists it as an un-renameable visible shipped name.

## Evidence (commands)
- `grep -rn 'LEAD' scratch/ubij3/tree-three-r2` → 4 hits / 3 files, all the filename.
- `grep -rn -i -e 'no-union' -e 'no union' -e 'no_union' -e 'union' /home/zer0null/Duval` → 0 for `no-union`; 250 of 373 `union` hits generic TypeScript prose.
- `glob **/*no-union*`, `glob **/LEAD-WIRING.md` under `/home/zer0null/Duval`.
- `grep -rn -i -e 'no-union' -e 'no union' -e 'no_union' -e 'LEAD' papers` → 4 hits (`AVAILABILITY.md:22`; `gated-read-batching/GAPS.md:105,:134,:181` = `ULEAD1`).
- `grep -n -i -e LEAD -e 'no-union' papers/encoder-crossover-190/MANUSCRIPT.md` → no matches.

## FileName warning
If a later owner neutralised either name it would be a path change: `harness/LEAD-WIRING.md` is cited by `harness/collect.py:372`, `MANIFEST.json:86-87`, `verify/redaction-log.json:64` and published by `papers/encoder-crossover-190/AVAILABILITY.md:22`; `variants/no-union/` is cited by `MANIFEST.json:34,:411,:412,:419,:420`, `verify/redaction-log.json:12,:116,:134` and the five comment lines `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts:10-14`. No package manifest change is warranted on the present evidence.

## Next unit hint
Nothing to neutralise for these two tokens. If the disclosure-policy owner wants the variant gone, the lever is the shipped sentence at `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts:8` and the five `[withheld: …]` markers at `:10-:14` (and the variant directory), not the token name — and that is a recorded M11-disclosure decision, not a token question.
