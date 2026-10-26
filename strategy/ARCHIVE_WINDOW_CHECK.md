# ARCHIVE_WINDOW_CHECK — was the Consonance implementation captured during the public window?

> ## ⚠️ CORRECTION — unit UCLOSE2, 2026-10-15: the live exposure is CLOSED
>
> **This block is appended and the rows it names are marked `⚠️ STALE` in place. Nothing below is deleted
> or silently rewritten; the withdrawn wording is quoted and retained.** Where it conflicts with §1, §2, §4
> or §5, **this block governs.** Companions: [`EXPOSURE_CLOSURE.md`](EXPOSURE_CLOSURE.md) (unit UCLOSE1) and the
> §10 correction block in [`DISCLOSURE_INVENTORY.md`](DISCLOSURE_INVENTORY.md). **Not legal advice.**
>
> **UARCH1's finding was correct when written (~20:45–20:54 UTC, 2026-10-15) and is now stale.** The
> repository `Aswin-Ram-K/publish-present-compete` was made **private** later that day, and every
> unauthenticated retrieval route UARCH1 measured has closed. UCLOSE2 re-ran the fetches itself:
>
> | URL — unauthenticated, `curl -s -o /dev/null -w '%{http_code}'`, 2026-10-15 | UARCH1 | UCLOSE2 now |
> |---|---|---|
> | `raw.githubusercontent.com/…/89003e7069c9ad79c40d91982720751b1ddf0360/consonance/src/journal.ts` | 200, 46,450 B | **404** |
> | `…/89003e70…/consonance/src/dag.ts` | 200, 44,468 B | **404** |
> | `…/89003e70…/consonance/LICENSE` | 200, 34,523 B (AGPL-3.0) | **404** |
> | `…/main/findings/PAPER-DERIVATION.md` | 200 | **404** |
> | `codeload.github.com/…/tar.gz/89003e7069c9ad79c40d91982720751b1ddf0360` | HTTP/2 200, 481 entries | **404** |
> | `github.com/…/commit/89003e70…` · `…/tree/89003e70…/consonance/src` · `…/blob/…/journal.ts` | 200 | **404** |
> | **control:** `raw.githubusercontent.com/Aswin-Ram-K/ai-pe-deck/main/README.md` | 200 | **200** |
>
> `gh repo view Aswin-Ram-K/publish-present-compete --json visibility,isPrivate,forkCount` →
> `{"forkCount":0,"isPrivate":true,"visibility":"PRIVATE"}`. **The control's 200 proves the fetcher works,
> so a 404 is visibility, not breakage.** (Anonymous `api.github.com` returned **403 rate-limit** — a
> different code for a different reason — so UCLOSE2 did not re-measure the API rows; UCLOSE1 measured the
> repo API → 404 earlier the same day. No code here is guessed.)
>
> ### The precise post-closure truth — three distinctions that must travel together
>
> 1. **Retrieval is closed.** Unauthenticated 404s at the full object id, against a **200** control. The
>    paper route and the whole-tree tarball are closed with it.
> 2. **Deletion is NOT done.** With the **owner token**, the *same unreferenced object* still resolves:
>    `gh api "repos/Aswin-Ram-K/publish-present-compete/contents/consonance/src/journal.ts?ref=89003e7069c9ad79c40d91982720751b1ddf0360"`
>    → `{"name":"journal.ts","size":46450}` — **the same 46,450 bytes** UARCH1 measured live, i.e. the
>    object is intact in GitHub's storage. **"Door shut, room untouched."** What removes it is a
>    **GitHub Support purge** of the unreferenced objects, or **deleting the repository** — and **the
>    author has said he will do this himself.** UCLOSE2 changed no setting and filed nothing.
> 3. **Copies already taken are not recalled.** Privacy is prospective. **`forkCount = 0`** — no fork
>    preserves a copy, which is genuine good news — but undetectable human clones from the **~27.5-hour**
>    window (2026-10-09T04:20:17Z → 2026-10-10T07:52:54Z) **cannot be ruled out by anyone.**
>
> ### Two things this correction must not be read as saying
>
> - **The archive-channel finding is archive-only, and it is NOT reassurance about the direct channel.**
>   §3's negatives stand exactly as written and remain correct — Software Heritage holds **no repository of
>   this author at all**, Wayback returned **0 captures**, GH Archive carried **0 mentions** — but they are
>   statements about *third-party archives*. They say nothing about the **direct channel**, which was open
>   and serving 200s **until today**, and the direct channel is the one that matters.
> - **A copy fetched during the window carries an AGPL-3.0 grant for that copy, which the author cannot
>   revoke.** `consonance/LICENSE` was read live as 34,523 B opening *"GNU AFFERO GENERAL PUBLIC LICENSE /
>   Version 3"*. Closing the door does not retract a licence already granted for a copy already taken.
>
> **Nothing in §3 (per-archive table), §4 (what was not checked) or §6 (UNVERIFIED) is withdrawn** — the
> SWH-absent, Wayback-0, GH-Archive-0, `cannot determine` and unqueryable-archive findings were correct
> and remain correct. **Only the live-exposure rows are stale**, and each is marked below.

**Unit:** UARCH1 · **Date of all checks:** 2026-10-15 (~20:45–20:54 UTC) · **Target repo:** strictly read-only, never written · **Not legal advice.** **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.**

**Scope:** the ~27-hour window in which the Consonance implementation sat in the **public** repo
`github.com/Aswin-Ram-K/publish-present-compete` (discovered by UDISC2). Question: did any archive
capture it?

---

## 1. Direct verdict

Two verdicts, and they must not be confused:

| Question as posed | Verdict |
|---|---|
| **Was the implementation captured by any archive during the window?** | **`not captured`** — 7 archives/indexes gave definitive negatives, including both primary targets (SWH, Wayback). 4 secondary indexes could not be queried (§3, §4). |
| **Is the implementation obtainable by a third party *today*?** | **YES — `captured` in substance.** It is downloadable from GitHub right now, unauthenticated, at an unreferenced pre-rewrite SHA that the repository's own public event feed publishes. **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2 measured `journal.ts` → **404**. |

> ### The archive negative is real and nearly irrelevant: **the exposure is not historical, it is live.**
>
> **The Consonance implementation is downloadable from GitHub at this moment, unauthenticated, via an
> unreferenced commit SHA that the repository's own public event feed hands out.**
>
> No archive I could query holds it (Software Heritage has never archived this origin — nor *any* repo
> of this author; the Wayback Machine holds no snapshot of any URL of the repo or even the author's
> profile; archive.today holds none; GH Archive recorded no event for the repo; Bing/Google have not
> indexed it; Sourcegraph has no match). **That negative is almost irrelevant**, because the asset was
> never lost to a rewrite in the first place: GitHub still serves the pre-rewrite objects, and the
> `.tar.gz` of the entire 481-entry tree — including all 388 `consonance/` blobs — returns **HTTP 200**.
>
> **⚠️ STALE — unit UCLOSE2, 2026-10-15: the exposure this blockquote calls *live* is CLOSED.** The
> whole-tree tarball now returns **404** unauthenticated (control **200**). The archive half of this page
> was already correct; the *live* half is what changed. See the CORRECTION block at the top.

**Two corrections to the record:**

1. **UDISC2's conclusion "no reachable commit contains the source" is FALSE.** It is true of every
   *branch/tag-referenced* commit and of every SHA in the current history. It is false of the
   **unreferenced pre-rewrite commits**, which GitHub still serves in full. UDISC2 tested only `main`
   and history SHAs (`06d618ca`, `d7072672`); it never tested the old heads that the force-push left
   behind. The 404s it measured were real but were *path-absent* 404s on the wrong commits.
2. **The current-history commit `ccdab112` ("fold Consonance in as a subdirectory") contains no
   `consonance/` directory.** Its tree is `.gitignore CLAIMS.tsv README.md SOURCES.tsv`. The
   `consonance/` tree lives on the **old (unreferenced) line**, whose messages and dates are the same
   but whose SHAs and contents are different. The window UDISC2 measured from commit *messages* is
   real — the *content* it attributed to `ccdab112` belongs to a different, still-served object.

### The reproduction, in four commands

```bash
# 1. The repository's own public event feed hands out the old head SHA (no auth):
curl -s https://api.github.com/repos/Aswin-Ram-K/publish-present-compete/events
#    -> PushEvent 2026-10-10T07:52:54Z  before=89003e7069c9ad79c40d91982720751b1ddf0360
#                                          head=1d2e0bf235530cebd38269ffcf548e245ae839cf

# 2. That pre-rewrite head is still served:
curl -s https://api.github.com/repos/Aswin-Ram-K/publish-present-compete/commits/89003e7069c9ad79c40d91982720751b1ddf0360
#    -> HTTP 200, tree 1aadb1ef5098  ("docs: state that source-material/ is deliberately omitted…")

# 3. The tree contains consonance/ and app/ (the current history's trees do not):
curl -s "https://api.github.com/repos/Aswin-Ram-K/publish-present-compete/git/trees/1aadb1ef5098"
#    -> .gitignore ARCHITECTURE.md CLAIMS.tsv LICENSE NOTICE PRODUCT.md README.md SOURCES.tsv
#       STATUS.md  app/  consonance/  package.json  pnpm-workspace.yaml  resume/  validate-ledgers.py

# 4. The source is downloadable, and so is the whole tree:
curl -sI https://raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/89003e7069c9ad79c40d91982720751b1ddf0360/consonance/src/journal.ts
#    -> HTTP 200, 46,450 bytes
curl -sI https://codeload.github.com/Aswin-Ram-K/publish-present-compete/tar.gz/89003e7069c9ad79c40d91982720751b1ddf0360
#    -> HTTP/2 200, content-disposition: attachment;
#       filename=publish-present-compete-89003e7069c9ad79c40d91982720751b1ddf0360.tar.gz
```

**⚠️ STALE (UCLOSE2, 2026-10-15):** these four commands are retained as the *historical* demonstration.
Re-run today, the `raw.githubusercontent.com` and `codeload.github.com` fetches return **404**
unauthenticated (control **200**), and the `api.github.com` routes return **403** rate-limit from this IP
— which is why UCLOSE2 relied on the `raw`/web routes and on owner-token `gh api` calls instead.

Every one of those requests was made **unauthenticated** (no GitHub token).

---

## 2. The live-exposure evidence (source, not archive)

**⚠️ STALE (unit UCLOSE2, 2026-10-15):** every **HTTP 200** recorded in this section was measured while
the repository was **public**. After the closure the same unauthenticated fetches return **404**
(control **200**). Each stale row is marked in place; **the original wording is retained, not rewritten.**

| Check | Result | Identifier / detail |
|---|---|---|
| Repo visibility | `public`, `fork:false`, `archived:false`, `default_branch:main` | repo id `1411274590`, created `2026-10-09T04:20:17Z`, `pushed_at 2026-10-10T07:52:53Z`, 0 stars, 0 forks **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** |
| Refs (`git ls-remote`) | **only** `HEAD` + `refs/heads/main` → `1d2e0bf235530cebd38269ffcf548e245ae839cf` | no `refs/pull/*` — so no PR-branch route; the exposure route is SHA-addressability |
| Public event feed | `GET /repos/…/events` → **HTTP 200**, 7 events | `PushEvent 2026-10-10T07:52:54Z`, `before=89003e7069c9ad79c40d91982720751b1ddf0360`, `head=1d2e0bf2…`, `ref=refs/heads/main` ← **this is the force-push, and it publishes the old head** **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2 measured the web route `github.com/…/commit/89003e70…` → **404**; `api.github.com` → **403** rate-limited, so that API code was not re-measured. |
| Old head reachable | `GET /commits/89003e7069c9ad79c40d91982720751b1ddf0360` → **HTTP 200** | tree `1aadb1ef5098`; date `2026-10-10T06:26:07Z` **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2: `api.github.com` → **403** rate-limited. |
| Old tree contents | 15 top-level entries incl. **`app/`** and **`consonance/`** | recursive: **481 entries, 428 under `consonance/`, 388 `consonance/` blobs, 35 blobs under `consonance/src/` (708,575 bytes)** **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2: `api.github.com` → **403** rate-limited. |
| Source file | `raw.githubusercontent.com/…/89003e70…/consonance/src/journal.ts` → **HTTP 200**, **46,450 bytes** | verified twice; body begins `/** journal.ts — the event journal: typed, append-only, hash-chained, pure-projected.` **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2 measured journal.ts → **404**. |
| More source files | `consonance/src/dag.ts` 44,468 B · `consonance/src/store.ts` 3,316 B · `consonance/package.json` 6,349 B — all **HTTP 200** | **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2 measured dag.ts, store.ts, package.json → all **404**. |
| Licence file | `consonance/LICENSE` → **HTTP 200**, 34,523 B, `GNU AFFERO GENERAL PUBLIC LICENSE / Version 3, 19 November 2007` | confirms UDISC2's AGPL-3.0 reading from the licence text itself (previously only inferable from README + a commit message) **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2 measured `consonance/LICENSE` → **404**. |
| Whole-tree download | `codeload.github.com/…/tar.gz/89003e70…` → **HTTP/2 200** | a single unauthenticated tarball of the entire window state **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2 measured the tarball → **404**. |
| Web UI route | `github.com/…/commit/89003e70…` **200** · `…/tree/89003e70…/consonance/src` **200** · `…/blob/89003e70…/consonance/src/journal.ts` **200** | not just raw/API — ordinary browser URLs resolve **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2 measured commit/tree/blob web routes → all **404**. |
| Old history line | `fd590ce54d1d → ddbd1d157e1b → 563aa5b0f31a → 207b2177f6f5 → 89003e7069c9` — **all five HTTP 200**, all with `consonance/`+`app/` trees | `fd590ce5`'s parent is `7c37181f7396` → the pre-rewrite line runs deeper still **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2: those API codes now **403** rate-limited; the equivalent web routes → **404**. |

**Window boundary, measured from GitHub's own event feed rather than from commit messages:**
`PublicEvent 2026-10-09T04:20:17Z` → `PushEvent 2026-10-10T07:52:54Z` (the force-push) = **~27.5 hours**.
This independently confirms UDISC2's ~27-hour window, and shows the code-bearing line was the public
`main` for its whole duration (pushes at `04:20:46Z`, `04:21:26Z`, `06:23:10Z`, `06:26:08Z` all moved
the *old* line, whose trees carry `consonance/`).

**Retention is the whole story.** A force-push moves the ref; it does not delete objects. GitHub has not
garbage-collected the pre-rewrite objects, and it serves unreferenced commits by SHA. Nothing needs to
be guessed: the SHA is printed by the repository's own public events API.

**⚠️ STALE (UCLOSE2, 2026-10-15):** the retention mechanism described here was real, and the object
was indeed **not** deleted — UCLOSE2 confirms the same bytes (`size 46450`) still resolve for the
**owner**. But the anonymous route is now closed: the repository is **PRIVATE** and these URLs return
**404** unauthenticated. **Door shut, room untouched.**

---

## 3. Per-archive table

| Archive | Searched how | Result | Identifier / URL | If present, what it would mean |
|---|---|---|---|---|
| **Software Heritage** (primary target) | REST: `GET /api/1/origin/https://github.com/Aswin-Ram-K/publish-present-compete/get/` → **HTTP 404** `{"exception":"NotFoundExc","reason":"Origin with url … not found!"}`; `origin/search/publish-present-compete/` → **200 `[]`**; `origin/search/Aswin-Ram-K/` → **200 `[]`**; `origin/search/consonance/` → 200, 20 results, **none this project** (all unrelated: `willwangg/consonance`, `Consonance/consonance`, `Efaistos/ida-consonance`, …) | **ORIGIN ABSENT — not archived.** No snapshot SWHID, no revision SWHID, no origin SWHID exists to report | n/a (control: `origin/https://github.com/git/git/get/` → **200**; `origin/search/torvalds/` → **200** with 5 origins, so the API and my query form work) | If present with a snapshot: the full tree would have been permanently preserved and re-servable. **Absent**, so SWH contributes nothing — and, decisively, `origin/search/Aswin-Ram-K/` returning `[]` means SWH has archived **no repository of this author at all**, not merely not this one |
| **Internet Archive Wayback Machine** | Availability API (`archive.org/wayback/available`) on **8 URLs** incl. the repo root, `raw…/main/LICENSE`, `blob/main/WHITEPAPER.md`, `raw…/<old-sha>/consonance/src/journal.ts`, `tree/<old-sha>/consonance`, `commit/<old-sha>`, `commits/main`, and `github.com/Aswin-Ram-K` → **every one returned `{"archived_snapshots": {}}` (HTTP 200)**. CDX enumeration (`web.archive.org/cdx/search/cdx?…&matchType=prefix`) → **HTTP 429** on 3 attempts (see §4) | **No captures — 0.** `wayback_captures = 0` | n/a | If a capture existed in 2026-10-09→10-10, the implementation would be preserved in an independent, third-party, perpetual archive. None exists |
| **archive.today / archive.ph** | `archive.ph/newest/<repo-url>` → **HTTP 404**; `archive.today/newest/<repo-url>` → **HTTP 404** | **No capture** | n/a | Same as Wayback: an independent copy would exist. It does not |
| **GH Archive** (public GitHub event record) | Hourly files: `data.gharchive.org/2026-10-10-7.json.gz` → **HTTP 200**, 12,741,978 B, **38,794 event lines**, event types well-formed (28,398 PushEvent, …). Grepped: **0 lines mention `publish-present-compete`** (2 lines contain "Aswin", unrelated). Also `2026-10-09-4.json.gz` (11,586,825 B) and `2026-10-09-5.json.gz` (12,025,054 B) → **HTTP 200** | **Not recorded** | n/a | GH Archive stores push **metadata**, not file contents — so it could never have held the source. It *would* have preserved the old SHAs for third parties. It did not capture this repo's pushes at all |
| **Search-engine caches** (Google / Bing) | `bing.com/search?q="publish-present-compete"` → **HTTP 200**, but result titles are all generic "publish" dictionary/SEO pages and the page contains **0** `github.com` links; `google.com/search?q="publish-present-compete"` → **HTTP 200**, **0** `github.com` links, 1 echo of the query string | **Not indexed by either** | n/a | Google's *cache* feature was retired in 2024, so even an indexed page would not yield a 2026-10 snapshot. No indexed copy exists to begin with |
| **Sourcegraph** (public code search) | `sourcegraph.com/.api/search/stream?q=context:global+publish-present-compete&v=V3&t=literal` → **HTTP 200**, stream reports `matchCount: 0` (69264 archived / 282 forked repos in scope) | **No match** | n/a | A code-search index would have made the source discoverable by content. It has not indexed it |
| **grep.app** | `grep.app/api/search?q=publish-present-compete` (and 2 other distinctive strings) → **HTTP 200 but a Vercel "Security Checkpoint" challenge page**, not results | **Cannot determine** | n/a | A code-search index holding `consonance/src/*.ts` would make the source content-addressable. Unresolved from here |
| **searchcode.com** | `searchcode.com/api/codesearch_I/?q=publish-present-compete` → **HTTP 404** (`404 page not found`) — endpoint no longer serves this form | **Cannot determine** | n/a | as above |
| **Memento TimeTravel** (aggregates GWC, archive.today, Bibliotheca Alexandrina, Icelandic, Portuguese, … archives) | `timetravel.mementoweb.org/timemap/link/<repo-url>` → **HTTP 000** (connection failed, twice) | **Cannot determine** | n/a | This is the single best tool for "did *any* of the ~15 smaller web archives capture it". Its failure is the largest remaining hole in the archive negative |
| **libraries.io / OpenHub** | `libraries.io/api/search?q=…` → **HTTP 401** (key required); `openhub.net/p?query=…` → **HTTP 403** | **Cannot determine** | n/a | Both index *published packages/projects*, not arbitrary repos; low prior, unverified |

**Archives queried with a definitive answer: 7** (SWH, Wayback, archive.today, GH Archive, Bing, Google,
Sourcegraph) — **all negative**. **Archives that could not be queried properly: 4** (grep.app,
searchcode.com, Memento, libraries.io/OpenHub) — **these are why the archive verdict is not
`not captured` with full confidence**.

---

## 4. What was NOT checked, and the residual risk it leaves

| Not checked | Why | Residual risk |
|---|---|---|
| **Wayback CDX full prefix enumeration** | `web.archive.org/cdx/search/cdx` returned **HTTP 429** on 3 attempts (25 s and 20 s backoff). The *availability* API — a different, unthrottled endpoint — answered cleanly for 8 URLs and found nothing | Low. The availability API is authoritative per-URL; a capture under a URL form I did not name (e.g. a `?tab=` variant) would be missed |
| **Memento / ~15 smaller web archives** | Endpoint unreachable (`HTTP 000`) | **Real but small.** A small archive could hold a capture not visible anywhere else |
| **grep.app, searchcode.com** | Bot-challenge / dead endpoint | Small. Both are code indexes with partial coverage |
| **Common Crawl** | Not queried (index crawl would need S3/`index.commoncrawl.org` work beyond this unit's bound) | **Real.** A Common Crawl segment covering 2026-10-09/10 could contain a raw-file fetch |
| **Commercial/dark archives** (LexisNexis, Bloomberg, Meltwater, Bright Data, intelligence crawlers) | Not publicly queryable | **Irreducible.** If any of these hold it, no external check can show it |
| **Any human's local `git clone` from 2026-10-09/10** | Undetectable by construction | **Irreducible and decisive.** At least the author's own machines hold it; anyone who ran `git clone` in that 27.5 h holds it |
| **The pre-rewrite line's root and total commit count** | Unreferenced commits cannot be enumerated; would require walking parents one API call at a time (≈500 calls) | Immaterial to the verdict. UDISC2's "528 commits" figure derives from a commit message and was not independently counted |
| **Whether the objects are still served after a further GitHub GC cycle** | Point-in-time measurement | **The exposure could end without notice.** This analysis describes 2026-10-15; retention of unreferenced objects is not a documented GitHub guarantee **⚠️ STALE — unit UCLOSE2, 2026-10-15: this recorded the exposure as LIVE; retrieval is now CLOSED (unauthenticated 404s, 200 control). See the CORRECTION block at the top of this file.** UCLOSE2 measured it: the object still resolves to the AUTHENTICATED OWNER at **46,450 B** — not deleted, only unreachable anonymously. |

**The irreducible floor.** Even a fully negative archive sweep proves only that *no archive I can see*
copied it. It cannot prove nobody cloned it, and it cannot undo a 27.5-hour window. In this case the
floor is not even reached, because the source is retrievable at the origin today.

**⚠️ STALE (UCLOSE2, 2026-10-15):** as of the closure the source is **no longer retrievable at the
origin** by third parties — unauthenticated 404s against a 200 control. The irreducible-floor critique
still stands unchanged: it cannot prove nobody cloned it during the ~27.5-hour window.

---

## 5. What each outcome implies, stated plainly

**A. If an archive had captured it (the branch that would have been alarming):** the implementation
would be permanently preserved by a third party and re-servable forever, independent of GitHub. Trade-secret
status in the disclosed *expression* would be destroyed beyond any possible remediation.

**B. What I actually found — no archive capture, but the source is live at the origin:** this is
**materially worse than A for remediation purposes, and better only in one narrow sense.** Worse: no
archiver needs to have acted for the implementation to be obtainable — the retrieval is one `curl`
away, and the pointer is published by the repository's own event feed. Better: because the exposure is
still under GitHub's control, it is the *only* variant that can be **stopped** — a DMCA/support request
to purge unreferenced objects, or deletion of the repository, would end *future* retrieval (it would
still not recall anyone who already fetched).

**⚠️ STALE (UCLOSE2, 2026-10-15):** branch B's premise — *"the source is live at the origin"* — no
longer holds. **Retrieval is closed; deletion is NOT done; copies are not recalled.** B's remedy half is
now the live to-do and remains exactly right: a **GitHub Support purge** of the unreferenced objects, or
**deleting the repository**, is what removes them — and **the author has said he will do this himself.**

**Protectability implications, plainly:**

1. **The implementation's expression is disclosed.** It was published on a public repository under a
   real licence file (`consonance/LICENSE` = AGPL-3.0, read directly, not inferred) and it is still
   publicly retrievable. Whatever "withhold / trade secret" register the project keeps, the
   implementation expression is on the wrong side of it.
   **⚠️ STALE (UCLOSE2, 2026-10-15):** *"still publicly retrievable"* is no longer true — the
   repository is **PRIVATE** and the object URL returns **404** unauthenticated. The rest of this item
   stands: the expression **was** disclosed under AGPL-3.0 during the window.
2. **Anyone who obtained a copy holds a licence to that copy.** Publishing under AGPL-3.0 is a grant;
   the later force-push removed *availability*, not the licence already granted for copies taken. A
   force-push is not a retraction.
3. **Trade secrecy in the disclosed expression is gone, and "we rewrote the history" does not restore
   it.** The remaining protectable assets are the ones UDISC2 found genuinely undisclosed
   (e.g. the W4 five-layer SPEC) — not the implementation.
4. **The repository is the problem, not the licence.** Because the old objects are still served and the
   SHA is published by the events API, no licence choice, NOTICE file, or README wording changes the
   position. If the author wants retrieval to stop, the action is a purge request to GitHub — and it is
   urgent precisely because object retention is not guaranteed and could be reclaimed at any time.
   **⚠️ STALE (UCLOSE2, 2026-10-15):** *"still served"* now means **served to the authenticated
   owner only**; the anonymous route returns **404**. So the action named here is **outstanding, not
   performed** — the object is intact in GitHub's storage at the same **46,450 bytes**. The urgency
   argument is unchanged.
5. **A "not captured by archives" finding must not be relayed as reassurance.** It is a negative on one
   channel (third-party archival) while the direct channel is wide open. Relaying it as "no evidence of
   exposure" would be the single worst misreading of this document.
   **⚠️ STALE (UCLOSE2, 2026-10-15):** *"the direct channel is wide open"* was true when written and
   is **no longer true** — the direct channel closed on 2026-10-15. The warning survives in corrected
   form: the archive negatives (SWH none / Wayback 0 / GH Archive 0) are **archive-channel only** and are
   **NOT reassurance about the direct channel**, which was open and serving 200s until today.

---

## 6. UNVERIFIED

- `UNVERIFIED` — whether GitHub will continue serving `89003e7069c9…` (or any unreferenced object)
  after its next garbage-collection cycle. Measured **200 today**; not a guarantee.
- `UNVERIFIED` → **partly resolved, UCLOSE2, 2026-10-15.** The anonymous route is now **404**, but the
  object still resolves to the **authenticated owner** at the same **46,450 bytes**, so it is **not
  deleted**. Whether a further GC cycle ends owner-side resolution remains unverified.
- `UNVERIFIED` — the full pre-rewrite ancestry depth and commit count ("528 commits" is from a commit
  message, not from a count).
- `UNVERIFIED` — Common Crawl, Memento's ~15 member archives, and all commercial/dark archives
  (never queried; see §4).
- `UNVERIFIED` — grep.app and searchcode.com coverage (bot-challenged / dead endpoint).
- `UNVERIFIED` — whether any third party cloned the repo during the 2026-10-09T04:20:17Z →
  2026-10-10T07:52:54Z window. **Not determinable from outside, by anyone, ever.**
- `UNVERIFIED` — whether the *current*-history commit `ccdab112` ever had a `consonance/` tree. All
  evidence says no (its tree is 4 files and it is content-addressed), but I did not survey every one of
  the 31 distinct trees in the current history: 28 were probed (all `consonance=False, app=False`); the
  3 unprobed are merge commits of 2026-10-05/07/08 whose sibling trees show the identical docs-only
  pattern, and the omissions were shell-quoting artifacts on commit messages containing apostrophes.
- `UNVERIFIED` — the author's intent at any point; only observable effects are reported here.

**Not legal advice.** This document records HTTP statuses, timestamps, identifiers and responses. It
states no conclusion about ownership, contract, licence compatibility (note: the published root is MIT
while `consonance/` was AGPL-3.0), or liability. Take the mechanism-level facts in §1–§2 to a lawyer.
