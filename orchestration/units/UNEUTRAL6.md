# UNEUTRAL6 — neutralise the ten system-specific tokens in the released stimulus

**Status:** DONE (skeleton written before work, per unit contract)

**Author decision (option B, given in the unit card):** the ten system-specific tokens that sit
inside the released stimulus must be neutralised; the second-labeller's route A diagnostic may move
as a result (the paper is unpublished and will be updated).

## Declared write paths (nothing else)
- `strategy/STIMULUS_NEUTRALISATION.md`
- `orchestration/units/UNEUTRAL6.md`
- `orchestration/handoffs/UNEUTRAL6.json`
- `scratch/uneutral6/**`

## Source
`scratch/urecut1/package/` (29 files, 874,473 bytes) -> working copy `scratch/uneutral6/package/`.

## The ten tokens (definitive list from the gate's own classification)
`fs.read`, `fs.write`, `expiresAtEpoch`, `reasonerCalls`, `MutationProposal`, `policyHash`,
`ToolCallIR`, `ToolCallIR.`, `role.canRequestEscalation`, `canRequestEscalation`.

## Hard bound
25 tool calls. Small increments; never `cat` a large file.

## Method
1. Census + classify every occurrence: (i) inside stimulus (`question`, `options`, `situation`),
   (ii) released schema / data outside stimulus, (iii) prose or a script.
2. Apply the maximal safe variant (NEUTRAL-TAG/v1: single-token, injective, longest-first, case-sensitive).
   Mapping never written to disk.
3. Prove by running `verify/recompute-claims.py`, `second-labeller/parse_fixture.py`,
   `second-labeller/compare.py` — before and after, literal output.
4. Regenerate `MANIFEST.json` with the package procedure, independent checker, idempotence diff.
5. Report (do not edit) affected `papers/encoder-crossover-190/MANUSCRIPT.md` and `CLAIMS.md` lines.

## Log

- Census: 299 physical occurrences of the ten tokens — 221 inside stimulus values, 64 in the stimulus
  TS source, 5 in released data outside the stimulus, 9 JSON keys; 0 prose, 0 script, 0 filename.
- Four same-class tokens are MISSING from the definitive ten: `test.run` (48), `memory.write` (30),
  `web.fetch` (13), `role.model` (4). Left untouched; reported for the author to decide.
- Neutralised all 299 with tag family `NC01`…`NC10` (NEUTRAL-TAG/v1; matches the gate's released id
  grammar `^[NKFS][A-Z]?[0-9]{2,4}$` from `scratch/ugate1/gate_scoped.sh:72-76`; one token under the
  scorer's `[a-z0-9]+`). Map in memory only, never written/logged/shipped. Longest-first, case-sensitive.
- Residual ten tokens in neutralised tree: NONE. Regenerated generated artefacts with the package's own
  tools (not hand-edited).
- Diagnostics unchanged: recompute exit 0 / `ALL CLAIM NUMBERS PRESERVED: True`; fixture-correctness
  digest `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` before = after; parse
  190 records / 190 cases / 0 failures / 721 options; route A κ 0.32520740993294694, route B κ
  0.9013584840356494, AB mutual 0.3526315789473684, closed 0.8837023738280471, roster 0.9139973672663448
  — every value byte-identical before and after.
- `MANIFEST.json` regenerated: `counts.files=29`, `bytes_total=861248`, `manifest_self=a7eeb522…`;
  independent checker 0 missing / 0 hash / 0 size / 0 unlisted / 0 listed-but-absent; idempotent
  (two builds differ only in `generated_utc`).
- Report: `strategy/STIMULUS_NEUTRALISATION.md`. Paper lines affected: **none** (`MANUSCRIPT.md` and
  `CLAIMS.md` quote none of the ten tokens; all quoted κ values unchanged).

