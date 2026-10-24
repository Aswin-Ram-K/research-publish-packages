# UARCH1 — Archive Window Check

**Purpose (one):** determine whether the Consonance implementation was captured by an archive during the
~27-hour public window in `github.com/Aswin-Ram-K/publish-present-compete` (2026-10-09 → 2026-10-10),
and report the archive identifiers or their absence.

**Deliverable:** `strategy/ARCHIVE_WINDOW_CHECK.md`

**Write paths (exactly three):** `strategy/ARCHIVE_WINDOW_CHECK.md`,
`orchestration/units/UARCH1.md`, `orchestration/handoffs/UARCH1.json`.
Nothing else was written. `/home/zer0null/Duval` was never written and no `git` command was run in it.
No `orchestration/VERDICTS.md`, no `strategy/DISCLOSURE_INVENTORY.md`, no `strategy/*.md` other than mine.

**Hard bound:** 50 tool calls. **Used: ~32.** No retry exceeded 3 attempts (Wayback CDX was attempted 3
times, all `HTTP 429`, then declared a partial).

## Method

Queried, unauthenticated: Software Heritage REST (origin lookup, origin search, validated against
controls), Internet Archive Wayback (availability API + CDX), archive.today, GH Archive hourly event
files, Bing, Google, Sourcegraph, plus attempted grep.app / searchcode.com / Memento / libraries.io /
OpenHub. Then read the repository's own GitHub event feed, commit/tree/blob API, `raw.githubusercontent.com`,
`codeload.github.com`, HTML routes, and `git ls-remote`.

## Result

**The archive question answers negative; the exposure question answers catastrophically.**

- **Archives: `not captured`.** SWH reports the **origin absent** (`HTTP 404 NotFoundExc`) and has
  archived **no repository of this author at all** (`origin/search/Aswin-Ram-K/` → `[]`, controls
  validated). Wayback has **0 captures** across 8 URLs including the author's profile. archive.today
  none. GH Archive recorded no event for the repo. Bing/Google have not indexed it. Sourcegraph: 0
  matches. Four secondary indexes could not be queried properly (grep.app bot-wall, searchcode 404,
  Memento `HTTP 000`, libraries.io 401 / OpenHub 403).
- **Source: the implementation is downloadable NOW.** The force-push at `2026-10-10T07:52:54Z` moved
  `refs/heads/main` off the code-bearing line, but GitHub still serves the pre-rewrite objects, and the
  repository's **own public events API prints the old head** as the `before` of that push:
  `89003e7069c9ad79c40d91982720751b1ddf0360`. That commit's tree `1aadb1ef5098` holds `consonance/`
  (428 entries, 388 blobs, 35 blobs / 708,575 B under `consonance/src/`) and `app/`.
  `raw.githubusercontent.com/…/89003e70…/consonance/src/journal.ts` → **HTTP 200, 46,450 bytes**
  (measured twice); `consonance/LICENSE` → 200, 34,523 B, AGPL-3.0 text;
  `codeload.github.com/…/tar.gz/89003e70…` → **HTTP/2 200** (whole tree, one unauthenticated download).
- **Two corrections to UDISC2.** (1) "No reachable commit contains the source" is **false** — it holds
  only for ref-referenced and current-history SHAs; the unreferenced pre-rewrite SHAs serve the source
  in full. (2) The current-history `ccdab112` ("fold Consonance in as a subdirectory") has a tree of
  **4 files with no `consonance/`**; the fold's content lives on the old line. Likewise `b81b35e`'s real
  diff is `README.md` + 33 added docs (`+14,819/−112`) with **zero** `consonance/`/`app/` deletions,
  despite its "Removed: consonance/ and app/" message. 28 of the 31 distinct trees in the current
  38-commit history were probed: all `consonance=False, app=False`.

**Window re-measured from GitHub's own feed:** `PublicEvent 2026-10-09T04:20:17Z` →
force-push `2026-10-10T07:52:54Z` = **~27.5 h**, independently confirming UDISC2's figure.

## UNVERIFIED

Full pre-rewrite ancestry depth/commit count (the "528 commits" figure is from a commit message);
Common Crawl and dark/commercial archives (never queried); whether GitHub will keep serving the
unreferenced objects after its next GC; whether any human cloned the repo in the window (**not
determinable from outside, ever**); 3 of 31 current-history trees (shell-quoting artifacts on messages
containing apostrophes — siblings show the identical docs-only pattern).

**Blocker:** none for this question. **The decisive constraint is not evidentiary but actionable:** no
licence, NOTICE or README change alters the exposure; only purging the objects (or deleting the repo)
ends *future* retrieval, and it still cannot recall copies already taken.

**Not legal advice.**
