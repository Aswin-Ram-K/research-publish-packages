# UFIXPKG12 — correct stale shipped-instrument digest in two process records

**Status:** in progress
**Hard bound:** 10 tool calls; STOP and report `partial` if the two files cannot be read and judged within it.

## Purpose
Two process records still describe the shipped instrument's digest as it was BEFORE a later
clean-up, and one states it in the present tense as still true.

- Shipped instrument path: `scratch/uneutral10/package/fixture/reflex-decisions.ts`
- Old digest (pre-clean-up): `369159b03aa67f1571517ea2a9c3c460d218ee832d00e8ddd4928e5e6da0f78d`, 81,284 B
- New digest (current): `89e77a8e24a907f06345a45485c013799e08c806cc9d8f075db7709fbfd8e169`, 81,439 B
  (corrected by UFIXPKG10, 2026-10-16; published at `papers/encoder-crossover-190/CLAIMS.md:46-47`,
  `MANUSCRIPT.md:802`, `submission/main.tex:408`)

Instance sites named by the verifier:
- `strategy/RELEASE_BUILD_3.md:315` — describes shipped instrument as `369159b0…`, 81,284 B
- `strategy/RELEASE_BUILD_3.md:321` — present-tense claim that `MANUSCRIPT.md:800-802` "now pairs the
  shipped path with the shipped digest `369159b0…`" (now FALSE)
- `strategy/RESIDUAL_TRIAGE_3.md:231`, `:240` — each to be judged dated-record vs live-assertion

## Decision rule
- **Live assertion** (text reads as current) → correct in place; keep the old value visible in a dated note.
- **Dated record** (explicitly historical/at-that-time) → keep value; add a short dated note naming the
  current value and the unit that established it.
Never silently rewrite history. Do not touch frozen records (`orchestration/units/*.md` other than this
one, `orchestration/handoffs/*.json` other than mine, `strategy/VERIFICATION_REPORT*.md`, `papers/**`).

## Write paths
`strategy/RELEASE_BUILD_3.md`, `strategy/RESIDUAL_TRIAGE_3.md`, `orchestration/units/UFIXPKG12.md`,
`orchestration/handoffs/UFIXPKG12.json`, `scratch/ufixpkg12/**`

## Plan
1. Measure true digest/size from disk (MANIFEST.json + own sha256sum/stat). [done, call 1]
2. Read each site in full surrounding section; classify each occurrence.
3. Correct live assertions / annotate dated records; sweep both files for other falsified present-tense claims.
4. Verify: before/after, exactly-once before-strings, workspace-wide literal listing labelled, JSON re-parse.
5. Handoff JSON + ≤12-line report; no artifact/paper/guard changed.
