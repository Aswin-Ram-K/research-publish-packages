# UFIXGR9 — retire stale metadata-sheet warnings after UFIXGR8

- **Purpose:** correct statements in `papers/gated-read-batching/submission/METADATA.md` and
  `BUILD_NOTES.md` that UFIXGR8's 2026-10-16 body-prose edits made false, without touching the
  shipped payload.
- **Bound:** 8 tool calls.
- **Write paths:** `papers/gated-read-batching/submission/METADATA.md`,
  `papers/gated-read-batching/submission/BUILD_NOTES.md`, `orchestration/units/UFIXGR9.md`,
  `orchestration/handoffs/UFIXGR9.json`, `scratch/ufixgr9/**`.
- **Context:** UFIXGR8 removed five references to three internal documents (`CLAIMS.md`,
  `GAPS.md G-25`, `REFS.md`) from `MANUSCRIPT.md`, neutralised the `**Status:**` banner
  (now `**Scope:**`) and deliberately kept the two `UFIXGR7` §3.2 markers; UVERGR8 confirmed
  0 residual pointers in `MANUSCRIPT.md`/`main.tex` and 497 numeric tokens unchanged.
- **Plan:** (1) read both metadata documents in full; (2) measure current `MANUSCRIPT.md`
  size/lines/words and `main.tex` counts; (3) supersede item 7 (fully resolved) and item 10
  (banner resolved, `UFIXGR7` marks deliberately kept) in `METADATA.md`, preserving the original
  wording; (4) correct the two false count claims in `BUILD_NOTES.md`; (5) leave provenance
  mentions of `CLAIMS.md`/`GAPS.md`/`REFS.md` intact; (6) confirm the shipped payload is
  byte-unchanged.

## Outcome (recorded after the edits)

- `papers/gated-read-batching/submission/METADATA.md:63` (item 7): fully-resolved note written;
  original wording preserved as a superseded quote. Reason: 0 internal-document pointers remain
  (UVERGR8), so the item's premise is false.
- `papers/gated-read-batching/submission/METADATA.md:93` (item 10, renumbered by the insert):
  marked partly resolved — `**Status:**` banner replaced by `**Scope:**` (resolved by UFIXGR8),
  two `UFIXGR7` marks deliberately kept (superseded decision). Original wording preserved.
- `papers/gated-read-batching/submission/BUILD_NOTES.md:8`: `MANUSCRIPT.md` 33,032 bytes / 238
  lines / 5,377 words -> 33,165 / 237 / 5,399 (measured). False before.
- `papers/gated-read-batching/submission/BUILD_NOTES.md:82`: braces 403/403 -> 402/402 (measured on
  the current `main.tex`). False before; all other counts in that list re-measured and unchanged.
- Left alone (not false): `METADATA.md:3` sourcing note, `METADATA.md:75` `REFS.md` Tier C
  provenance pointer, and the `BUILD_NOTES.md:9-11` sentence recording that `CLAIMS.md`/`GAPS.md`/
  `REFS.md` were consulted while building the reference list.
- Shipped payload byte-unchanged: `main.tex` sha256
  `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4`; tarball sha256
  `0899f5b6252f68ac076e67eea1e9b325a5fcd8b9959c0515b861882106969c18`; `MANUSCRIPT.md` sha256
  `2a4cc287e8509b2cf2492cf1edff989ff57f352d8d0d2d2bf7666de023b8a2a7`.
