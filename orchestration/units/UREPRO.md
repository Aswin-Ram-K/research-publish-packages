# UREPRO — minimal reproducibility subset for paper #3 (EXP#12)

**Status:** done · **Bound:** 45 tool calls (used 32) · **Purpose:** one thing — assemble the minimal
reproducibility subset for EXP#12 as a file tree the author can publish later, implementing *open paper,
withheld implementation*.

## Declared write paths
`repro/encoder-crossover-190/**`, `orchestration/units/UREPRO.md`, `orchestration/handoffs/UREPRO.json`.

## Inputs
- Target `/home/zer0null/Duval` (READ ONLY, HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`).
- Workspace `experiments/second-labeller-190/` (unit UEXP).
- Policy: author decision 2026-10-15 — papers public (CC BY 4.0); every paper ships a minimal
  reproducibility subset; withhold the agent-state kernel/runtime and all model weights.

## What was done
1. Copied the fixture verbatim (145,031 B, sha256 `076164ac…b4796`) and extracted the schema
   (`DecisionKind` + `DecisionCase`, target lines 53–75).
2. **Found the harness is not on trunk**: EXP#12 closed unmerged; its method is at branch `a5ef1b2`,
   `tools/typed-channel/`. Recovered 18 files read-only via `git cat-file blob` (no checkout).
3. Copied the eight measured-result files from `docs/research/EXP#12-evidence/`, and proved each is
   byte-identical to the closed branch's `results/` blob (harvest integrity).
4. Cut the pre-registration §§1–9 at `## 10. Results` (protocol only), and copied the second-labeller
   pre-registration.
5. Copied the second-labeller evidence, **plus `labelsB.json`** (without it `compare.py` cannot re-run)
   and **`OWED_CORRECTIONS.md`** (the experiment's own corrections ledger) — both flagged in the README.
6. Wrote the five deliverables and generated `INTEGRITY.md` + `MANIFEST.json` from live source-vs-copy
   hashing; verified independently from the written manifest (0 mismatches, 0 unlisted, 0 missing).

## Result — evidence
- 42 files, 5,393,492 bytes; 40 copy/source pairs byte-identical; 2 derived excerpts equal to their
  source regions; 8/8 result files equal to the branch blobs.
- Target HEAD before = after; `status --porcelain` = the same four untracked paths before and after
  (unrelated concurrent session, attributed); mtime sweep over the two directories read: empty.
- Harness self-containment: **partial** — the six Python steps run from `harness/` with its bundled
  `data/`; steps 1–2 need the repo's `scripts/run.sh` + tsx runner and a repo-shaped layout, but their
  outputs are included byte-identical; the three encoder checkpoints are **public** and fetched at run
  time — **no weights are shipped**.
- Secrets: credential-shaped scan over the three source directories → **0 hits**; nothing excluded for
  secrecy and nothing credential-shaped opened.
- 15 exclusion classes recorded in `EXCLUDED.md` (kernel/runtime, weights, traces/runs/tmp/scratch/
  archive/node_modules, target `LICENSE`, minimality cuts).

## Boundary notes for the next unit
- Publication is gated on `LICENCE_TODO.md`: the code licence is **undecided** (UCODE1 analysing; author
  intends non-free commercial use, disclosed in pieces) and a published licence is permanent for that
  version.
- Nothing was pushed, committed, or published; the target was never written.
