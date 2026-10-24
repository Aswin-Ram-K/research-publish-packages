# UFIXAD6 — apply the AD6 archive-window corrections

**Unit:** UFIXAD6 · **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a · **Workspace:** `/home/zer0null/reserach extarctor`

## Purpose
Apply the corrections decided by `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md` (handoff `orchestration/handoffs/UAD6.json`).
Decision: **YES — the AGPL window DID expose the target's `src/**`**, and `strategy/WITHHELD.md:443-445`'s
"404 at every historical ref" is FALSE as written.

## Corrections
1. `strategy/WITHHELD.md:443-445` — dated note fixing the retrieval premise in place; keep the protective
   conclusion (do not republish). Record: `89003e7069c9ad79c40d91982720751b1ddf0360` served
   `consonance/src/journal.ts` 200/46,450 B; window 481 entries / 428 under `consonance/` / 35 blobs under
   `consonance/src/` = 708,575 B; mapping corroborated by three exact byte matches against `/home/zer0null/Duval`
   (`src/journal.ts` 46,450 B; `src/dag.ts` 44,468 B; `src/store.ts` 3,316 B). Keep original text visible.
2. `strategy/GATED_READ_DISCLOSURE.md` — move §1 item 4, §1 item 5, X-08, and X-07's `src/` component only into
   `already-disclosed` with window evidence + dated notes; mark U-1 decided, AD-6 resolved. Caveat: fact is
   public, paper still must not republish, no filing may assert non-publication.
3. Never state `ccdab112` carried `consonance/` — it did not (tree `.gitignore CLAIMS.tsv README.md SOURCES.tsv`).
   Boundary: `ccdab112` (2026-10-09 04:11) → `b81b35e` (2026-10-10 07:51); event-measured
   2026-10-09T04:20:17Z → 2026-10-10T07:52:54Z.

## Hard bound
15 tool calls. Stop condition: if an edit's before-string does not match exactly once, STOP that edit, leave the
file unchanged, report it — never force a fuzzy match.

## Write paths
`strategy/WITHHELD.md`, `strategy/GATED_READ_DISCLOSURE.md`, `orchestration/units/UFIXAD6.md`,
`orchestration/handoffs/UFIXAD6.json`, `scratch/ufixad6/**`

## Constraints
`/home/zer0null/Duval` strictly read-only, no `git` against it. Do not re-derive the window. Do not edit papers,
`ARCHIVE_WINDOW_CHECK.md`, `DISCLOSURE_INVENTORY.md`, `PRIOR_DISCLOSURE_AUDIT.md`. Dated notes only; preserve
every original value; do not renumber/restructure.

## Result
See `orchestration/handoffs/UFIXAD6.json`.
