# UPKGX1 — analysis.json releasability for the Paper #3 release boundary

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Purpose (one):** establish whether `analysis.json` is releasable, so the release-boundary decision
(add it to the package vs rewrite eight citations) can be made from facts.
**Bound:** 20 tool calls. If `analysis.json` cannot be located → STOP and report as blocker.
**Write paths (only these):** `scratch/upkgx1/**`, `strategy/ANALYSIS_JSON_RELEASABILITY.md`,
`orchestration/units/UPKGX1.md`, `orchestration/handoffs/UPKGX1.json`.

## Question
Paper #3 (`papers/encoder-crossover-190/submission/main.tex`) cites `analysis.json` 8× at lines
134,148,149,153,251,268,273,395 with precise key paths (e.g. `.comparisons["modernbert-base"].b`).
`analysis.json` does not ship in `scratch/uneutral10/package/` (29 files, MANIFEST.json sha256
d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02). Also missing:
`docs/DECIDER_STACK_DECISION.md`, `harness/data/lint-report.json`. Proposed fix: add the file, if releasable.

## Constraints
Target repo `/home/zer0null/Duval` strictly read-only; no mutating git; no bare `git status`.
Measure, do not sanitise. No network. No credentials/tokens/ORCID in any file.

## Tasks
1. Locate every copy of `analysis.json`: path, bytes, sha256; say which copy citations resolve against.
2. Structure: top-level keys, cited-object shape, how many of the 8 cited key paths exist; report any
   cited path that does NOT exist (paper defect, not release gap).
3. Releasability: run `tools/package/` census/classify over it; count project identifiers, paths,
   digests, hostnames, private repo names, neutralised system vocabulary.
4. Cost the fix: identifiers to neutralise, mechanical vs judgement, downstream changes
   (manifest, data zip, tarball, paper's description of what ships).
5. Alternative: cost to rewrite 8 citations to `results/REPORT.md`; is key→section mapping
   determinable from disk? If not, say so — do not guess.
6. Recommendation with reason + what must be re-verified if the package changes.

## Report back
`orchestration/handoffs/UPKGX1.json` with exactly `unit,status,artifacts,evidence,blocker,
next_unit_hint,write_paths`; ≤15-line summary to parent starting with the recommendation.
