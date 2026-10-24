# UCLOSE2 — bring `strategy/ARCHIVE_WINDOW_CHECK.md` in line with the closed exposure

**Unit:** UCLOSE2 · **Date:** 2026-10-15 · **Bound:** max 25 tool calls (used 21) ·
**Target repo:** `/home/zer0null/Duval` untouched, no `git` run there; GitHub access read-only (`curl`, `gh` GET) ·
**No GitHub setting changed, nothing written to any repository.**

## Purpose (one)

Append-only correction of `strategy/ARCHIVE_WINDOW_CHECK.md` (owned by this unit, written by UARCH1), whose
live-exposure rows still asserted that the Consonance implementation was downloadable. UCLOSE1 could not touch
that file; `DISCLOSURE_INVENTORY.md` §10 recorded the discrepancy and named it as needing "its own dated
correction by a unit that owns it". This is that correction.

## What was verified first-hand (unauthenticated `curl -s -o /dev/null -w '%{http_code}'`, 2026-10-15)

| URL | Code |
|---|---|
| `raw…/89003e7069c9ad79c40d91982720751b1ddf0360/consonance/src/journal.ts` | **404** |
| `…/89003e70…/consonance/src/dag.ts` · `…/store.ts` · `…/package.json` | **404**, **404**, **404** |
| `…/89003e70…/consonance/LICENSE` | **404** |
| `…/main/findings/PAPER-DERIVATION.md` | **404** |
| `codeload.github.com/…/tar.gz/89003e7069c9ad79c40d91982720751b1ddf0360` | **404** |
| `github.com/…/commit\|tree\|blob/89003e70…` (web routes) | **404** |
| **control** `raw…/Aswin-Ram-K/ai-pe-deck/main/README.md` | **200** |
| `api.github.com/…` (repo, commits, events, tree) | **403 — rate limit** (control repo also 403) |

`gh repo view Aswin-Ram-K/publish-present-compete --json visibility,isPrivate,forkCount` →
`{"forkCount":0,"isPrivate":true,"visibility":"PRIVATE"}`.

Owner-authenticated resolution still works — **deletion is NOT done**:
`gh api "repos/…/contents/consonance/src/journal.ts?ref=89003e70…"` → `{"name":"journal.ts","size":46450}`,
i.e. the same bytes UARCH1 measured live; and `…/commits/89003e70…` → tree `1aadb1ef5098`.

**Honest limit recorded, not papered over:** the anonymous `api.github.com` rows returned **403 rate-limit**
(a different code for a different reason — verified by the same 403 on a known-public control repo), so
UCLOSE2 did **not** re-measure those API codes; UCLOSE1 measured the repo API → 404 earlier the same day. No
code in the artifact is inherited on trust or guessed.

## Edit made — append-only

- A dated `CORRECTION — unit UCLOSE2, 2026-10-15` blockquote inserted directly under the H1.
- **23 stale locations annotated in place** (22 `⚠️ STALE` markers + the §6 "still served" `UNVERIFIED`
  bullet marked "partly resolved"). Table rows keep their original wording, with the marker appended inside
  the final cell (pipe counts unchanged: 3- or 4-pipe rows stay well-formed).
- **Nothing deleted.** §3 (per-archive table), §4 (not checked) and §6's other `UNVERIFIED` items — SWH
  absent, Wayback 0 captures, GH Archive 0 mentions, the `cannot determine` items and the unqueryable
  archives — are **untouched**; they were correct and remain correct.
- Truth carried exactly: **retrieval closed; deletion not done** ("door shut, room untouched"); **copies not
  recalled** (`forkCount = 0` is genuine good news, but undetectable clones from the ~27.5 h window cannot be
  ruled out); the archive finding is **archive-only and NOT reassurance about the direct channel**; a copy
  fetched during the window carries an **unrevocable AGPL-3.0 grant**.
- Cross-referenced `EXPOSURE_CLOSURE.md` (UCLOSE1) and the `DISCLOSURE_INVENTORY.md` §10 correction.

## Write paths touched (exactly three)

`strategy/ARCHIVE_WINDOW_CHECK.md`, `orchestration/units/UCLOSE2.md`, `orchestration/handoffs/UCLOSE2.json`.
No other file edited; no concurrent unit was running; nothing written outside the workspace.

**Not legal advice.**
