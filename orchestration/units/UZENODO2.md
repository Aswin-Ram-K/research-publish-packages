# Unit UZENODO2 — Zenodo deposit payload + form metadata

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Hard bound:** 20 tool calls.
**Status:** in progress

## Purpose
Build the one upload file for the Zenodo deposit of the released data/tooling package,
plus the exact form metadata to paste. The earlier orchestrator path
`papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` was a
**mistake** — nothing existed there. This unit creates the directory and the tarball.

## Authoritative source
`scratch/uneutral10/package` — 29 files, ~842,810 B. Promoted tree: sealed fixture,
verification tooling, result records, pre-registered protocol, licence pieces.
**No harness** (model/training/eval code withheld by author decision). Must not be
described as reproducing the measurement.

## Constraints
- `/home/zer0null/Duval` STRICTLY READ-ONLY. Never run `git` against it.
- Do not modify package contents. Report defects, do not fix.
- Do not change any measured number or paper claim.
- Licence: released package = **PolyForm Noncommercial 1.0.0** + author-offered paid
  commercial licence; paper text = CC BY 4.0; main repo proprietary/closed.
  Do not substitute a different licence. If no matching Zenodo option, report it and
  mark the closest-option choice as an author decision.
- Persist card first. End with `orchestration/handoffs/UZENODO2.json` (7 keys, valid JSON).

## Declared write paths
- `papers/encoder-crossover-190/released/**`
- `strategy/ZENODO_DEPOSIT.md`
- `orchestration/units/UZENODO2.md`, `orchestration/handoffs/UZENODO2.json`
- `scratch/uzenodo2/**`

## Jobs
1. Assemble payload: 29 package files unchanged (sha256-verified) + README.md, LICENSE,
   COMMERCIAL.md, CONTRIBUTING.md, CITATION.cff.
2. Build deterministic `encoder-crossover-190-released.tar.gz`, single top-level dir;
   report bytes, sha256, member list.
3. `strategy/ZENODO_DEPOSIT.md` — form values; verify PolyForm NC 1.0.0 availability
   against Zenodo's own licence vocabulary.
4. Report on other papers' released artifacts (`scratch/urelease7/cut3`).
5. Prove: hashes, tarball shape, extract-and-compare, residual identifier count.

## Result
(see `orchestration/handoffs/UZENODO2.json`)
