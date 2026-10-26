# COPYRIGHT_DEADLINES — per-work first-publication dates and the § 412 clock

> **⛔ CLOSED — REGISTRATION DECLINED BY THE AUTHOR, 2026-10-16. DO NOT RE-OPEN.**
>
> **The author declined US copyright registration on 2026-10-16** in favour of licence-based
> protection. The § 412 deadline analysis below (grace expiries, the nearest date 2027-01-08) is
> retained **as analysis, not as a task list**: no filing is owed and no date here is an action item.
> Do not re-open this file as work.
>
> **Consequence, stated honestly:** without registration, **statutory damages and attorney's fees
> under 17 U.S.C. § 504 are unavailable** for these unpublished works, while **actual damages,
> the infringer's profits and the licence's own terms** remain. The analysis below is unaltered.


**Unit:** URIGHTS2 · **Date of all checks in this file:** **2026-10-16** (UTC; measured `date -u` = `2026-10-16T00:49:57Z`) · **Not legal advice.**
**Purpose (one):** replace unit UCOPY1's *estimated* first-publication date (2026-10-09/10 → ~2027-01-10) with dates grounded in this workspace's own records, and separate works whose § 412 clock is running from works whose clock has not started.
**Law is taken as given** from [`COPYRIGHT_REGISTRATION.md`](COPYRIGHT_REGISTRATION.md) § 2 (17 U.S.C. § 412, quoted there) and § 3 (fees). This unit re-derives no law; it dates facts.
**Ground:** `strategy/DISCLOSURE_INVENTORY.md`, `strategy/EXPOSURE_CLOSURE.md`, `strategy/ARCHIVE_WINDOW_CHECK.md`, `strategy/PAPER_CANDIDATES.md`, `strategy/O1_EVIDENCE_ASSESSMENT.md`, `strategy/PUBLICATION_STRATEGY.md`, `.ucurate1/pre/research-publish-packages/README.md` + that package's own git state, and a grep of `papers/**`. Every date below is tied to a quoted line.

---

## 0. Headline

**UCOPY1's ~2027-01-10 is one to two days late.** The earliest recorded first-publication event in the workspace's own records is the **profile README mechanism paragraph, public ≤ 2026-10-08** (grace expiry **2027-01-08**); the **public repository documentation surface and the AGPL code window both open at `2026-10-09T04:20:17Z`** (grace expiry **2027-01-09**). The nearest deadline is therefore **2027-01-08**, not 2027-01-10 — **84 days from today**.

**Nothing on UCOPY1's shortlist is in fact published.** Both manuscripts and `.ucurate1/pre/research-publish-packages/` are unpublished on their own records, so the **$150 / $215 recommendation does not change**. The correction runs the other way: **the works whose clock is actually running are not on UCOPY1's shortlist at all**, and the $150 buys no registration for any of them (§ 4).

---

## 1. The table of works

"Published as of today" = as of **2026-10-16**. Grace expiry = first publication + 3 months, per § 412(2) as stated in `COPYRIGHT_REGISTRATION.md:74–76`. The three-month period ends at the same time of day as publication, so **file at least one day before the date shown**; the column gives the computed last day.

| # | Work | Path / locus | Published as of 2026-10-16? | First publication | § 412 grace expiry | Evidence line that fixes it |
|---|---|---|---|---|---|---|
| 1 | **The 13 disclosed mechanisms (M1–M13)** as published descriptions, carried in `WHITEPAPER.md`, `findings/PAPER-DERIVATION.md`, `decisions/DECISION_LOG.md`, `experiments/` (15 files), `findings/` (15 files) | public repo `github.com/Aswin-Ram-K/publish-present-compete` — **no local copy in this workspace** (`findings/` does not exist here) | **Published** (had been public; repo is now private, but publication is not undone) | **2026-10-09** (`PublicEvent 2026-10-09T04:20:17Z`) | **2027-01-09** | `ARCHIVE_WINDOW_CHECK.md:159–160`: *"**Window boundary, measured from GitHub's own event feed rather than from commit messages:** `PublicEvent 2026-10-09T04:20:17Z` → `PushEvent 2026-10-10T07:52:54Z` (the force-push) = **~27.5 hours**."* `ARCHIVE_WINDOW_CHECK.md:147`: *"repo id `1411274590`, created `2026-10-09T04:20:17Z`"*. P1–P5 rows (`DISCLOSURE_INVENTORY.md:29–33`) each say *"public ≤ 2026-10-10"* — an upper bound consistent with the repo opening on 10-09. |
| 2 | **`findings/PAPER-DERIVATION.md`** — the M1–M9 spine, §5.5 five-layer rule, §7 artefact table, §8 command chain (sha256 `d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`) | same public repo, `findings/` | **Published** (same repo surface; now private) | **2026-10-09** (repo `PublicEvent 2026-10-09T04:20:17Z`; row says *"public ≤ 2026-10-10"*) | **2027-01-09** | `DISCLOSURE_INVENTORY.md:30` (P2): *"**`findings/PAPER-DERIVATION.md`** — 46,636 B, **byte-identical to the corpus's withheld `docs/research/PAPER_DERIVATION.md`**… \| *started 2026-10-01*; public ≤ 2026-10-10 \| **MIT**"*. Hash cited at `PUBLICATION_STRATEGY.md:4`: *"#1 is in any case already public — `findings/PAPER-DERIVATION.md`, MIT, ≤ 2026-10-10, byte-identical sha256 `d98c4359…`"*. **Not recomputed here** — no copy of `findings/` in this workspace (§ 5.2). |
| 3 | **Profile README mechanism paragraph** (*"Enforcement by absence, not refusal"*, the live A/B, the byte-identical digest) | `github.com/Aswin-Ram-K` · `Aswin-Ram-K/Aswin-Ram-K` README | **Published** (paragraph removed 2026-10-15T21:26:50Z; removal is prospective only) | **2026-10-08** (recorded as *"public ≤ 2026-10-08"*; EXPOSURE_CLOSURE R4 calls it *"roughly seven days"*, consistent with 10-08 as the actual start) | **2027-01-08** — **the nearest deadline** | `DISCLOSURE_INVENTORY.md:34` (P6): *"**Profile README** — Consonance in one paragraph… \| public ≤ **2026-10-08** \| **MIT**"*. Removal: `EXPOSURE_CLOSURE.md:81–84`: *"msg "Profile: remove capability-kernel mechanism description" / date 2026-10-15T21:26:50Z"*; `EXPOSURE_CLOSURE.md:132` (R4): *"hosted the mechanism paragraph for roughly **seven days** (public ≤ 2026-10-08 → removed 2026-10-15T21:26:50Z)"*. |
| 4 | **Consonance implementation source — `consonance/src/**`** (528 commits, 441 files, **16,704 LOC in `src/`**; AGPL-3.0) | public repo `…/publish-present-compete`, path `consonance/` (now unreachable anonymously; **not deleted**) | **Published in the window**; retrieval closed 2026-10-15, **deletion not done** | **2026-10-09T04:20:17Z** | **2027-01-09** | `ARCHIVE_WINDOW_CHECK.md:159–160` (window, event-measured). `DISCLOSURE_INVENTORY.md:19`: *"Between **2026-10-09 04:11** (`feat: fold Consonance in as a subdirectory`) and **2026-10-10 07:51** (`refactor: this repository is findings, not code`) the public repository carried the Consonance implementation — **528 commits, 441 files, 16,704 LOC in `src/`**, licensed **AGPL-3.0**"*. `DISCLOSURE_INVENTORY.md:38` (P10): *"… \| **2026-10-09 04:11 → 2026-10-10 07:51** \| **AGPL-3.0** \| **fetched by anyone in that window; not recalled by the rewrite**"*. `DISCLOSURE_INVENTORY.md:161`: *"**So the implementation was published under AGPL-3.0, not MIT.** … Anyone who fetched the tree during the P10 window obtained an irrevocable AGPL grant in it"*. `DISCLOSURE_INVENTORY.md:265`: *"Unit UARCH1 fetched the Consonance source **live, unauthenticated**… `…/89003e70…/consonance/src/journal.ts` → **HTTP 200, 46,450 bytes**"*. Closure (prospective only): `EXPOSURE_CLOSURE.md:11`, `:15`. |
| 5 | **`papers/encoder-crossover-190/MANUSCRIPT.md`** (9,678 words; paper #3) | workspace `papers/encoder-crossover-190/MANUSCRIPT.md` | **Unpublished** | `not published` | **n/a — no grace period for an unpublished work** (§ 412(1): the bar is the effective date of registration) | `O1_EVIDENCE_ASSESSMENT.md:215`: *"\| **4** \| **Paper #3 unpublished; zero peer-reviewed papers.** \| **Medium — one submission cycle** \| Submit #3; obtain a DOI and, if possible, peer review. \|"*. `PAPER_CANDIDATES.md:1023` records the verdict *"**publish**"* — i.e. an intended future publication, not a past one: *"\| **#3** A fine-tuned encoder head does not beat a fine-tuned 4B decider \| **pass** \| **exists** — `repro/encoder-crossover-190/`… \| **publish**"*. Plan to publish: `PUBLICATION_STRATEGY.md:20–21` (*"post **#3 to arXiv**"*, then TMLR). Independent check: `grep` over `papers/**` for `preprint\|arXiv\|arxiv\.org\|under review\|submitted to\|first published\|published in` returned **only third-party citations** — no arXiv/DOI record of this manuscript itself. |
| 6 | **`papers/gated-read-batching/MANUSCRIPT.md`** (5,213 words) | workspace `papers/gated-read-batching/MANUSCRIPT.md` | **Unpublished** | `not published` | **n/a** (§ 412(1)) | No publication record exists. `PAPER_CANDIDATES.md:1028` (candidate #7) gives the verdict *"**needs-author-decision**"*, not *publish*: *"…the **staged extractor** — whose routing/gating *is* the gate/absence machinery (M10) — is the part that must not ship"*. Its `MANUSCRIPT.md` references (lines 225–237) are all third-party arXiv IDs. UCOPY1 itself marks this one `UNVERIFIED` (*"no per-paper publication line was found for this one"*, `COPYRIGHT_REGISTRATION.md:288`); status here is established by **absence of any publication record**, not by a positive statement — carried as `UNVERIFIED` in § 5.4. |
| 7 | **`.ucurate1/pre/research-publish-packages/`** (154 files; 15 code files, 6,184 LOC; paper + sanitised code + eval evidence) | workspace `.ucurate1/pre/research-publish-packages/` | **Unpublished** | `not published` | **n/a** (§ 412(1)) | `README.md:6`: *"**Status: private for now.** Nothing here is announced or published yet; this is the repository being prepared"*. `README.md:49`: *"- **Any history, any remote, any push.** Fresh history; no remote is configured."* **Independently verified by this unit:** `git --no-optional-locks -C .ucurate1/pre/research-publish-packages log --oneline -1` → `67716cc Initial commit: exp12-encoder-crossover package (paper, sanitised code, eval evidence)`; `git … remote -v` → **no output** (no remote configured). |
| 8 | **`repro/encoder-crossover-190-SANITISED/`** (D) and **`repro/encoder-crossover-190/`** (E, the as-audited tree) | workspace `repro/…` | **Unpublished** (not part of the AGPL window) | `not published` | **n/a** (§ 412(1)) | The AGPL window exposed **only** `consonance/` + `app/`; `DISCLOSURE_INVENTORY.md:45` (V2): *"**`tools/**` — the experiment trees**… Path **names** are public (M13); the **code** is not in reachable history."*; `:46` (V3): *"**Private corpora** — the session traces, the 190-case decision fixture… deliberately omitted from the public mirror"*. UCOPY1's row E asserts the same (*"Never published… while the 27.5 h AGPL window exposed the Consonance implementation, this as-audited tree is the private record"*, `COPYRIGHT_REGISTRATION.md:291`). |

### 1.1 Works whose clock has not started (forthcoming)

| Work | Basis for "forthcoming" |
|---|---|
| `papers/encoder-crossover-190/MANUSCRIPT.md` (row 5) | `PUBLICATION_STRATEGY.md:20–21`: arXiv post, then TMLR submission |
| `papers/gated-read-batching/MANUSCRIPT.md` (row 6) | no publication record; no decision recorded |
| `.ucurate1/pre/research-publish-packages/` (row 7) | `README.md:6–7`: *"this is the repository being prepared as the public-facing one"* |
| `repro/encoder-crossover-190-SANITISED/`, `repro/encoder-crossover-190/` (row 8) | would become published only if shipped |
| **Papers #2, #4, #5, #9, #10, #11, #12 and NC1** — verdict **publish**, artifact *"not yet packaged"* / *"does not exist yet"* | `PAPER_CANDIDATES.md:1022` (#2), `:1024` (#4), `:1025` (#5), `:1030` (#9), `:1031` (#10), `:1032` (#11), `:1033` (#12), `:1027` (NC1) |

---

## 2. The nearest deadline

> **2027-01-08 — the profile README mechanism paragraph** (`github.com/Aswin-Ram-K/Aswin-Ram-K`, work row 3), first published **2026-10-08**.
> **File by 2027-01-07** to land clear of the boundary day.
>
> Next, one day later: **2027-01-09** for the public repository documentation surface (13 mechanisms + `findings/PAPER-DERIVATION.md`, rows 1–2) and for the **Consonance `consonance/src/**` AGPL window** (row 4), all of which open at `2026-10-09T04:20:17Z`.

UCOPY1's stated figure was *"on or about 2027-01-10"* (`COPYRIGHT_REGISTRATION.md:88`), computed from a 2026-10-10 publication date. The workspace's own earliest record is 2026-10-08 (profile README), so **UCOPY1's date is late by two days**, and late by one day even on the repo surface alone (2026-10-09, not 2026-10-10).

**Boundary caution.** Rows 1–2 and row 4 state first publication as a **date**; the record fixes the repo to the second (`2026-10-09T04:20:17Z`), and the three-month period ends at the matching time of day on 2027-01-09. Do not file on the boundary day.

**Publication is not undone by withdrawal.** Every "now private / removed" fact in the records is prospective: `EXPOSURE_CLOSURE.md:19`: *"`private` is a *door*, not an *eraser*."* The § 412 clock runs from the publication event, not from whether the material is still reachable. The AGPL window (row 4) therefore carries a live clock even though retrieval closed on 2026-10-15 — and the 34,523-byte AGPL grant in copies taken during the window cannot be revoked (`EXPOSURE_CLOSURE.md:119`: *"A copy lawfully obtained during the window carries that licence for that copy, and the author cannot revoke it"*).

---

## 3. The rule for works whose clock has not started

Per § 412 as stated in `COPYRIGHT_REGISTRATION.md:71–76`, **the grace period runs from the work's own first publication** — clause (1) gives an unpublished work *no* grace at all (the bar is the effective date of registration, so an unpublished work registered before any infringement is fully covered prospectively), and clause (2) gives a three-month grace measured from first publication.

**Posture for a work published in the future:** **register before publication, or within three months after it.** Registering *before* publication is the stronger of the two — it puts the effective date of registration ahead of any infringement, which satisfies clause (2) outright and needs no grace at all. Registering in the first three months after publication preserves remedies for infringements commenced after first publication and before registration; after those three months, that remedy is gone for anyone who started infringing before the registration date.

**In that class:** the two manuscripts (`papers/encoder-crossover-190/MANUSCRIPT.md`, `papers/gated-read-batching/MANUSCRIPT.md`), `.ucurate1/pre/research-publish-packages/`, the two `repro/…` trees if shipped, and the eight further `PAPER_CANDIDATES.md` § G.1 candidates with verdict **publish** (§ 1.1 above).

**Consequence for the existing $85 group route.** A *group of unpublished works* is available only while the works are unpublished. **The day either manuscript is posted (arXiv, TMLR, a journal, or a repo), that work leaves the group and acquires a clock** — and a group application that included it would then be registering a published work on a published-works route. The TMLR/arXiv plan in `PUBLICATION_STRATEGY.md:20–21` is what triggers this. This is the one place where a *future* act reshapes the route, and it argues for filing the group **before** the arXiv post, or accepting the switch to a published-works route afterwards.

---

## 4. Reconciliation with UCOPY1's $150 recommendation

UCOPY1 recommends (`COPYRIGHT_REGISTRATION.md:295–305`): **$85** — group of unpublished works (manuscripts A + B); **$65** — Standard Application for the sanitised publish package (C); **total $150**; **$215** with the optional as-audited private tree (E).

**Do my dates change it? No — the $150 / $215 figure is unchanged, and no work on the shortlist moves out of the unpaid-group route.**

| UCOPY1 shortlist item | UCOPY1 status | Verified status here | Moves route? |
|---|---|---|---|
| A — `papers/encoder-crossover-190/MANUSCRIPT.md` | unpublished | **unpublished** (row 5; `O1_EVIDENCE_ASSESSMENT.md:215`) | **No** — stays in the $85 group |
| B — `papers/gated-read-batching/MANUSCRIPT.md` | unpublished | **unpublished** (row 6; no publication record) | **No** — stays in the $85 group |
| C — `.ucurate1/pre/research-publish-packages/` | unpublished | **unpublished** (row 7; README `:6` + own git: single commit, no remote) | **No** — $65 Standard Application stands |
| E — `repro/encoder-crossover-190/` (as-audited) | never published | **never published** (row 8; the AGPL window exposed `consonance/` + `app/`, not this tree) | **No** — optional $65 stands |

**Two corrections to the reconciliation, both running the other way from "is anything secretly published":**

1. **The works with a running clock are not on the shortlist, so $150 does not buy any of them.** UCOPY1's § 6 table (A–G) and its recommended shortlist contain **no already-published work**. Rows 1–4 above (the repo documentation surface, `PAPER-DERIVATION.md`, the profile README, and the Consonance `src/**` AGPL window) each have a clock expiring **2027-01-08/09**, and **none of them is covered by the $85 group** — a group of *unpublished* works cannot include a published work (stated from UCOPY1's own reading of GRUW in `COPYRIGHT_REGISTRATION.md:250–255`). Protecting that surface costs an additional **Standard Application ($65)** at minimum, and it is the spend with a deadline attached. The true figure is therefore **$150 now + ≥$65 on a 2027-01-08/09 clock**, not $150 total.
2. **"Never published" for the *implementation* needs a qualifier.** UCOPY1's row E (`COPYRIGHT_REGISTRATION.md:291`) says *"Never published… while the 27.5 h AGPL window exposed the Consonance implementation, this as-audited tree is the private record"* — correct **for that tree**. But the **Consonance kernel `src/**` itself was published** (row 4; `DISCLOSURE_INVENTORY.md:19, :38, :161`) for 27.5 h under AGPL-3.0. If the author means to register the *kernel implementation* rather than the encoder-crossover tree, that is a **published** work on a **2027-01-09** clock and it cannot ride the unpublished-works group.

**Net answer:** dates do not change the $150; they add a deadline and a further fee that the recommendation omits.

---

## 5. What I could not establish (`UNVERIFIED`, listed explicitly)

1. **Per-document first-publication dates inside the public repo.** Records give P1–P5 as *"public ≤ 2026-10-10"* — upper bounds. The only second-precision anchor is the repo-level `PublicEvent 2026-10-09T04:20:17Z`. Whether an individual file (e.g. P7's README, commit-dated **2026-10-10 06:26**) became readable later than the repo event is `UNVERIFIED`; a later first publication moves that work's deadline later.
2. **The `sha256 d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802` for `findings/PAPER-DERIVATION.md`.** Quoted from `PUBLICATION_STRATEGY.md:4`; **not recomputed here** — this workspace has no `findings/` directory (`ls findings` → *"No such file or directory"*). The digest is therefore inherited, not re-verified.
3. **Whether 2026-10-08 is the profile README's true first-publication date or only an upper bound.** The record says *"public ≤ 2026-10-08"*; `EXPOSURE_CLOSURE.md:132`'s *"roughly seven days"* implies 10-08 is the real start, but that is inference from a rounding. **If the paragraph was public earlier, the 2027-01-08 deadline is earlier too.**
4. **Any publication record for `papers/gated-read-batching/MANUSCRIPT.md` outside this workspace.** Status is established by **absence of a record**, exactly as UCOPY1 flagged (`COPYRIGHT_REGISTRATION.md:288`). Not a positive finding.
5. **Whether the manuscripts are byte-identical to the package's copies** (`.ucurate1/pre/research-publish-packages/packages/exp12-encoder-crossover/paper/MANUSCRIPT.md`). Not diffed here; if identical, the "two works" framing of the $85 group and the "one work" framing of the $65 package overlap in expression (a cost question, not a rule — UCOPY1's own `UNVERIFIED` 13, `COPYRIGHT_REGISTRATION.md:414`).
6. **Whether `.ucurate1/pre/research-publish-packages/` was ever pushed anywhere not configured today.** No remote is configured and there is one commit; an earlier push to a since-removed remote would be undetectable from here.
7. **Whether `publish-present-compete` was ever public before 2026-10-09T04:20:17Z**, and whether it was ever private before that. `DISCLOSURE_INVENTORY.md:227` (§ 8.3) marks exactly this `UNVERIFIED`; `created_at` equals the `PublicEvent` timestamp, which is consistent with (but does not prove) "created public".
8. **Any dark-channel publication** (LinkedIn, X, Bluesky, Reddit, HN, YouTube, Discord/Slack, listservs, talks). `DISCLOSURE_INVENTORY.md:214` (§ 7.5): *"No credentials, no index access… a clean web-search result is not evidence of non-disclosure here."* A dark-channel first publication would predate every date in § 1 and shorten every deadline.
9. **Whether any third party cloned during the 27.5-hour window** (`DISCLOSURE_INVENTORY.md:209`, `EXPOSURE_CLOSURE.md:110`). Irrelevant to computing the date; relevant only to whether § 412(2) infringement "commenced" in the window.
10. **Pre-rewrite object retention.** `EXPOSURE_CLOSURE.md:142`: *"Whether GitHub keeps serving `89003e7069c9…` to the authenticated owner indefinitely… is not a documented guarantee"* — a deletion fact, not a dating fact, but it bears on the row-4 remediation posture.

---

## Appendix — evidence log for this unit

**Commands actually run (this unit):** `date -u` → `2026-10-16T00:49:57Z`; `ls -d findings papers` → `findings` absent, `papers` present; `stat -c '%y %n' strategy/…`; `sed -n` extractions of the exact lines quoted above; `git --no-optional-locks -C .ucurate1/pre/research-publish-packages log --oneline -1` → `67716cc Initial commit: exp12-encoder-crossover package (paper, sanitised code, eval evidence)`; `git --no-optional-locks -C .ucurate1/pre/research-publish-packages remote -v` → no output; `grep` over `papers/**` (`*.md`) for `preprint|arXiv|arxiv\.org|under review|submitted to|first published|published in` → 168 matches, **all third-party citations**.

**Files read (not edited):** `strategy/COPYRIGHT_REGISTRATION.md` (full), `strategy/DISCLOSURE_INVENTORY.md` (full), `strategy/EXPOSURE_CLOSURE.md` (full), `strategy/ARCHIVE_WINDOW_CHECK.md` (full), `strategy/PUBLICATION_STRATEGY.md:1–30`, `strategy/PAPER_CANDIDATES.md:1008–1035`, `strategy/O1_EVIDENCE_ASSESSMENT.md:200–225`, `.ucurate1/pre/research-publish-packages/README.md` (full).

**Write paths touched — exactly four:** `strategy/COPYRIGHT_DEADLINES.md` (this file), `orchestration/units/URIGHTS2.md`, `orchestration/handoffs/URIGHTS2.json`, `scratch/urights2/` (not used beyond the directory). No file under `papers/**`, `repro/**`, or `strategy/COPYRIGHT_REGISTRATION.md` was modified; `/home/zer0null/Duval` was not read, written, or `git`-touched.

*Nothing in this document is legal advice. It is a record of what this workspace's own files say about when each work was first published.*
