# AD6_ARCHIVE_WINDOW_RESOLUTION — did the AGPL window expose the target's `src/**`?

**Unit:** UAD6 · **Status:** resolved · **Target repo:** `/home/zer0null/Duval` — strictly read-only, never written, no `git` command run against it · **Not legal advice.**

**Question adjudicated:** does the public AGPL window's `consonance/src/**` correspond to the target's `src/**`, making `strategy/WITHHELD.md`'s 404 claim wrong and moving withhold items 4–5 and X-08 into `already-disclosed`?

**One-sentence decision:** **YES — the window did expose the target's `src/**` implementation**, and `WITHHELD.md:443–445`'s *"404 at every historical ref"* is false as written (true only of branch/tag-reachable refs and of path-absent refs; the pre-rewrite unreferenced head `89003e70…` served `consonance/src/journal.ts` at HTTP 200, 46,450 B).

---

## 1. The contradicting claims, side by side

| # | Claim (verbatim) | `file:line` | What it asserts |
|---|---|---|---|
| W-1 | *"UDISC2 verified that `consonance/src/journal.ts` and `src/journal.ts` return **404 at every historical ref** while a control README returns **200**."* | `strategy/WITHHELD.md:444-445` | The implementation was **never** retrievable at any ref. |
| W-2 | *"the public repo carries the design prose and explicitly does not carry the implementation (`README.md`: *"The implementation is not published here."*)"* | `strategy/WITHHELD.md:443-444` | The implementation is not public. |
| A-1 | *"raw.githubusercontent.com/…/**89003e7069c9ad79c40d91982720751b1ddf0360**/consonance/src/journal.ts → **HTTP 200**, **46,450 bytes**"* — *"verified twice; body begins `/** journal.ts — the event journal: typed, append-only, hash-chained, pure-projected.`"* | `strategy/ARCHIVE_WINDOW_CHECK.md:152` (also `:123-124`, `:86`) | The implementation **was** publicly retrievable — at an unreferenced pre-rewrite SHA. |
| A-2 | *"consonance/src/dag.ts 44,468 B · consonance/src/store.ts 3,316 B · consonance/package.json 6,349 B — all **HTTP 200**"* | `strategy/ARCHIVE_WINDOW_CHECK.md:153` | Same, three more files. |
| A-3 | *"recursive: **481 entries, 428 under `consonance/`, 388 `consonance/` blobs, 35 blobs under `consonance/src/` (708,575 bytes)**"* | `strategy/ARCHIVE_WINDOW_CHECK.md:151` | The window tree carried a full `consonance/src/` (35 blobs). |
| A-4 | *"2. **The current-history commit `ccdab112` ("fold Consonance in as a subdirectory") contains no `consonance/` directory.** Its tree is `.gitignore CLAIMS.tsv README.md SOURCES.tsv`."* | `strategy/ARCHIVE_WINDOW_CHECK.md:99-103` | **Reframes W-1's refs:** a 404 at `ccdab112` is *path-absent*, not content-withdrawn. |
| T-1 | *"Between **2026-10-09 04:11** … and **2026-10-10 07:51** … the public repository carried the Consonance implementation — **528 commits, 441 files, 16,704 LOC in `src/`**, licensed **AGPL-3.0**"* | `strategy/DISCLOSURE_INVENTORY.md:19` | Third statement, **agrees with A-1/A-3**, disagrees with W-1. |
| T-2 | P10: *"the Consonance source under `consonance/` at **AGPL-3.0** … folded in at `ccdab112` and removed at `b81b35e`"* | `strategy/DISCLOSURE_INVENTORY.md:38` | The mapping `consonance/` → the Consonance source is recorded. |
| T-3 | V1 (`src/**` — the kernel implementation): *"Not in any **reachable** commit (§5, verified by 404). **Published only in the P10 window.**"* | `strategy/DISCLOSURE_INVENTORY.md:44` | The record already classifies the window as having published `src/**`. |
| T-4 | P8 names `src/journal.ts`, `src/replay.ts`, `src/lease.ts`, `src/invariants.ts`, `src/policy.ts`, `src/commit.ts`, `src/observation.ts`, `src/reference.ts`, `src/constitution.ts`, `src/index.ts`, `src/adapters/stub-agent.ts`, `src/worker-sandboxed.ts` as **public commit-message** content | `strategy/DISCLOSURE_INVENTORY.md:36` | The target's `src/**` names were in the public history. |
| G-1 | *"AD-6 \| **AGPL window — CONFLICTED, must be reconciled.** The target's `src/**` is recorded as public under AGPL-3.0 for ~27.5 h … vs `strategy/WITHHELD.md:444–445`"* | `strategy/GATED_READ_DISCLOSURE.md:173` | The workspace names this exact conflict. |
| G-2 | U-1: *"Whether the AGPL window actually exposed the implementation (`consonance/` = target `src/**`), i.e. whether §1 item 5 and X-08 are `withhold` or `already-disclosed`"* | `strategy/GATED_READ_DISCLOSURE.md:216` | The undecided element this report settles. |

**Where they disagree.** W-1 (universal 404) contradicts A-1/A-2 (HTTP 200 at `89003e70…`) and T-1/T-3 (the window published `src/**`). **Where the apparent disagreement is not real:** W-1's 404s were measured only on *branch/tag-reachable* refs (`main`, `06d618ca`, `d7072672` — `ARCHIVE_WINDOW_CHECK.md:97-98`) and, for `ccdab112`, on a commit that has no `consonance/` directory at all (A-4). UDISC2 *"never tested the old heads that the force-push left behind"* (`ARCHIVE_WINDOW_CHECK.md:97-98`). So W-1's 404 is real per-URL and false as a universal; **A-4 does not rescue W-1, it explains it.**

---

## 2. File-set facts from the record

| Fact | Value | Source |
|---|---|---|
| Repository | `github.com/Aswin-Ram-K/publish-present-compete` (repo id `1411274590`, created `2026-10-09T04:20:17Z`) | `ARCHIVE_WINDOW_CHECK.md:61-62`, `:147` |
| Boundary refs (as recorded) | `ccdab112` (2026-10-09 04:11, *"feat: fold Consonance in as a subdirectory"*) → `b81b35e` (2026-10-10 07:51, *"refactor: this repository is findings, not code"*) | `DISCLOSURE_INVENTORY.md:19`, `:38`; `VISA_US_ROUTES.md:65` |
| Boundary, event-measured | `PublicEvent 2026-10-09T04:20:17Z` → `PushEvent 2026-10-10T07:52:54Z` (the force-push) = **~27.5 h** | `ARCHIVE_WINDOW_CHECK.md:159-160` |
| **Ref caveat** | `ccdab112` is current-history and carries **no** `consonance/` (tree = `.gitignore CLAIMS.tsv README.md SOURCES.tsv`). The code-bearing object is the **unreferenced old head** `89003e7069c9ad79c40d91982720751b1ddf0360`, tree `1aadb1ef509824bd9219e6a917fdf059afcd2f03` | `ARCHIVE_WINDOW_CHECK.md:99-103`, `:114-115`, `:143` |
| Window tree size | **481 entries** total; **428 under `consonance/`**; 388 `consonance/` blobs; **35 blobs under `consonance/src/` = 708,575 bytes** | `ARCHIVE_WINDOW_CHECK.md:151`, `:86` |
| Window top-level dirs (15 entries) | `.gitignore ARCHITECTURE.md CLAIMS.tsv LICENSE NOTICE PRODUCT.md README.md SOURCES.tsv STATUS.md app/ consonance/ package.json pnpm-workspace.yaml resume/ validate-ledgers.py` | `ARCHIVE_WINDOW_CHECK.md:119-120` |
| AGPL licence in window | `consonance/LICENSE` 34,523 B, *"GNU AFFERO GENERAL PUBLIC LICENSE / Version 3"* | `ARCHIVE_WINDOW_CHECK.md:154` |
| **Is a `consonance/` → target `src/**` mapping recorded?** | **YES, explicitly.** `consonance/` = the Consonance source (T-2); the window carried *"16,704 LOC in `src/`"* (T-1); `src/**` is *"Published only in the P10 window"* (T-3); the target's `src/*.ts` names appear as public commit-message content (T-4). | `DISCLOSURE_INVENTORY.md:19`, `:36`, `:38`, `:44` |
| **Byte-size corroboration (this unit, read-only)** | target `/home/zer0null/Duval/src/journal.ts` = **46,450 B** = A-1's `consonance/src/journal.ts`; `src/dag.ts` = **44,468 B** = A-2's `consonance/src/dag.ts`; `src/store.ts` = **3,316 B** = A-2's `consonance/src/store.ts` — **three exact matches** | `wc -c /home/zer0null/Duval/src/{journal,dag,store}.ts` |
| Version drift (expected) | window: 35 `consonance/src/` blobs / 708,575 B, README claim 16,704 LOC; today's target `src/`: **39 files / 754,461 B / 17,640 LOC** | `ARCHIVE_WINDOW_CHECK.md:151`; `glob /home/zer0null/Duval/src/**/*`; `cat src/*.ts src/adapters/*.ts \| wc -c -l` |

**So the mapping is not assumed — it is recorded, and independently corroborated by three exact byte counts.**

---

## 3. Retrieval table (this unit, unauthenticated `curl -sS -L --max-time 25`, 2026-10-15)

Body of every 404 is the literal 14-byte string `404: Not Found`, sha256 first-16 = `d5558cd419c8d46b`.

| # | URL | ref | status | bytes | sha256¹⁶ | verdict |
|---|---|---|---|---|---|---|
| C1 | `raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/ccdab112/consonance/src/journal.ts` | `ccdab112` (in-window boundary) | **404** | 14 | `d5558cd419c8d46b` | unavailable — repo PRIVATE; also path-absent at this current-history ref (A-4) |
| C2 | `…/ccdab112/src/journal.ts` | `ccdab112` | **404** | 14 | `d5558cd419c8d46b` | same |
| C3 | `…/b81b35e/consonance/src/journal.ts` | `b81b35e` (removal boundary) | **404** | 14 | `d5558cd419c8d46b` | unavailable — repo PRIVATE |
| C4 | `…/b81b35e/src/journal.ts` | `b81b35e` | **404** | 14 | `d5558cd419c8d46b` | same |
| C5 | `…/main/consonance/src/journal.ts` | `main` (post-removal) | **404** | 14 | `d5558cd419c8d46b` | same |
| C6 | `…/main/src/journal.ts` | `main` | **404** | 14 | `d5558cd419c8d46b` | same |
| C7 | `…/89003e7069c9ad79c40d91982720751b1ddf0360/consonance/src/journal.ts` | `89003e70…` (the recorded 200 ref) | **404** | 14 | `d5558cd419c8d46b` | **was 200/46,450 B (A-1); now closed by visibility** |
| C8 | `…/06d618ca4caac9bb967eaa742eaef9a6371e4017/consonance/src/journal.ts` | `06d618ca` (Consonance-era) | **404** | 14 | `d5558cd419c8d46b` | path-absent at this ref |
| C9 | `…/ccdab112/README.md` | `ccdab112` | **404** | 14 | `d5558cd419c8d46b` | expected — whole repo private |
| API-1 | `api.github.com/repos/Aswin-Ram-K/publish-present-compete` | — | **404** | `{"message":"Not Found",…}` | — | repo PRIVATE |
| API-2 | `api.github.com/…/git/trees/1aadb1ef5098` | tree `1aadb1ef5098` | **404** | 99 | — | unreferenced tree not anonymously served |
| **CTRL** | `raw.githubusercontent.com/Aswin-Ram-K/**ai-pe-deck**/main/README.md` | `main`, different repo | **200** | **4445** | — | **fetcher works — the 404s are visibility, not breakage** |

Result: today's direct test **cannot** re-confirm the window content (the repository is private; `ARCHIVE_WINDOW_CHECK.md:3-28` records the closure). The positive case therefore rests on **the recorded 200s (A-1/A-2) plus this unit's three exact byte-size matches (row "Byte-size corroboration" above)** — not on a live 200 obtained now. The closure distinction is recorded and not overread: *"Retrieval is closed; deletion is NOT done; copies already taken are not recalled"* (`ARCHIVE_WINDOW_CHECK.md:30-42`, `DISCLOSURE_INVENTORY.md:299-303`).

## 4. Elements that change class

Keyed to `strategy/GATED_READ_DISCLOSURE.md` (candidate #7). **"Change" means the window's version is public** — the paper must still not *republish* those names/construction, and no filing may assert non-publication (`GATED_READ_DISCLOSURE.md:175-179`).

**Move to `already-disclosed` (for the window's version):**

1. **§1 item 4** — *"Any `src/**` or `kernel/**` path name"*, incl. the 19 grep hits listed there (`src/loop.ts`, `src/lease.ts`, `src/dag.ts`, …). `GATED_READ_DISCLOSURE.md:27`.
2. **§1 item 5** — *"The concrete shape of the product's gate/absence machinery … (M10), as construction"*. `GATED_READ_DISCLOSURE.md:28`.
3. **X-08** — *"`src/**` file names (19 grep hits, listed in §1 item 4)"*, was `withhold`. `GATED_READ_DISCLOSURE.md:138`.
4. **X-07, the `src/` component only** — corpus root `src/` (the other roots `docs/ tests/ evals/ examples/ tools/ scripts/` were **not** in the window; unchanged). `GATED_READ_DISCLOSURE.md:137`.
5. **U-1 itself** — decided, no longer undecided. `GATED_READ_DISCLOSURE.md:216`.
6. **AD-6** — no longer *"CONFLICTED"*; resolved. `GATED_READ_DISCLOSURE.md:173`.
7. **`DISCLOSURE_INVENTORY.md` V1 (`src/**`)** — already said *"Published only in the P10 window"* (`:44`); **corroborated, not changed**.

**Do NOT change** (were not in the window — it carried `consonance/` + `app/` only: `ARCHIVE_WINDOW_CHECK.md:119-120`, `COPYRIGHT_DEADLINES.md:43`):

- §1 items **1, 2, 3** (`tools/gated-read/bench.py`, `tasks.json`, rows/summary) — `tools/**` and corpora were never in the window (`DISCLOSURE_INVENTORY.md:45` V2, `:46` V3).
- §1 items **6, 7, 8, 11, 12** (KeyRing credential surface, fixture answers, branch label `measure/gated-read`, payload identifiers, model ids) — harness internals/private corpora, not `consonance/`.
- **X-01 … X-06, X-09** — tools/corpora/docs/functions of the private harness.
- §1 items **9, 10** — unchanged and now more load-bearing: *item 9* (no first-disclosure claim for M1–M13) and *item 10* (**any assertion or filing line that the work was never published**) already forbidden (`GATED_READ_DISCLOSURE.md:32-33`); this finding reinforces item 10 and adds `src/**` to the class it protects.
- **`WITHHELD.md`'s protective conclusion** — the register still protects the *implementation expression* in the released tree (do-not-republish), even though it was public in the window. What is falsified is its **retrieval** premise (*"404 at every historical ref"*), not its protective intent.

---

## 5. Residual uncertainty

- **Cannot re-fetch the 200 now.** All 11 unauthenticated routes to the target repo return 404 while the control returns 200 (`§3`), so the positive case is historical evidence + byte-size correspondence, not a live fetch. No owner token is available to this unit.
- **Correspondence is at module identity + three exact byte counts, not a whole-tree hash.** 35 `consonance/src/` blobs / 708,575 B in the window vs 39 files / 754,461 B today (16,704 vs 17,640 LOC) is version drift; I did **not** hash the window tree (undownloadable) so I cannot claim byte-identity of the whole tree. The three simultaneous exact size matches (`journal.ts` 46,450; `dag.ts` 44,468; `store.ts` 3,316) are strong but are counts, not digests.
- **Whether any third party fetched during the ~27.5 h window is not determinable from outside, by anyone, ever** (`ARCHIVE_WINDOW_CHECK.md:285-286`, `:207`).
- **The archive channel stays negative** (SWH none / Wayback 0 / GH Archive 0) and must not be relayed as reassurance (`ARCHIVE_WINDOW_CHECK.md:46-50`, `:263-269`).
- **Not settled here:** whether the object survives a future GitHub GC for the owner (`ARCHIVE_WINDOW_CHECK.md:275-279`); `worker.class` / `context.package` residue (`DISCLOSURE_INVENTORY.md:215`) — untouched by this finding.

**Non-negotiable:** **whichever way this resolves, no filing, declaration or exhibit may assert the work was never published.** It was published: the Consonance source sat in a public AGPL-3.0 repository for ~27.5 h on 2026-10-09/10, `consonance/src/**` was retrievable (200, 46,450 B measured), and the closure of 2026-10-15 is prospective only.

## 6. Limits of this check

- **Unauthenticated only**; the repository is private, so no tree/blob/API read was possible (`§3` API-1/API-2 404). No owner token exists in this unit's scope.
- **One batched network attempt** (9 raw URLs + 2 API routes) — within the declared stop condition of 5 network attempts; the question was settled on the disk record plus the size correspondence, not on a live 200.
- **No `git` command was run against `/home/zer0null/Duval`**; target reads were `ls`/`wc`/`sha256sum`/`sed` only, and `glob`/`read` for the workspace records.
- **No existing record was edited** — `strategy/WITHHELD.md`, `ARCHIVE_WINDOW_CHECK.md`, `DISCLOSURE_INVENTORY.md` and `GATED_READ_DISCLOSURE.md` are quoted, not amended. A separate fixing unit applies dated corrections.
- Byte-size comparison used the target's working tree **as read today**; if the target changed between the window and now, the three matches would still be a lower bound on correspondence, not an upper bound.

**Not legal advice.**
