# URIGHTS2 — per-work first-publication dates and the § 412 clock

**Status:** done · **Unit:** URIGHTS2 (fresh unit; supersedes the failed URIGHTS1, which died writing nothing)
**Date of checks:** 2026-10-16 (`date -u` = `2026-10-16T00:49:57Z`)
**Bound:** ≤20 tool calls. **Remainder:** none.

## One purpose
Replace unit UCOPY1's *estimated* first-publication date (~2026-10-09/10 → ~2027-01-10) in `strategy/COPYRIGHT_REGISTRATION.md` with first-publication dates grounded in this workspace's own records, and separate works whose § 412 clock is running from works whose clock has not started. **Do not re-derive the law** — UCOPY1's legal statements are taken as given.

## Deliverable
`strategy/COPYRIGHT_DEADLINES.md` — table of 8 works with path · published/unpublished as of 2026-10-16 · first-publication date · § 412 expiry · the quoted line that fixes it; the nearest deadline; the not-yet-started rule; the $150 reconciliation; a 10-item `UNVERIFIED` list; an evidence appendix.

## Write paths (exactly these, checked against concurrent units)
- `strategy/COPYRIGHT_DEADLINES.md` (created)
- `orchestration/units/URIGHTS2.md` (this card)
- `orchestration/handoffs/URIGHTS2.json`
- `scratch/urights2/**` (declared; not needed)

No file under `papers/**`, `repro/**` or `strategy/COPYRIGHT_REGISTRATION.md` was modified. `/home/zer0null/Duval` was never read, written, or `git`-touched. Nothing was written outside the workspace. `strategy/` and `papers/` are UNTRACKED in this repo, so the verbatim evidence lines are carried in the handoff.

## Findings (see the deliverable for the full evidence lines)
1. **Nearest deadline = 2027-01-08** — the profile README mechanism paragraph (`github.com/Aswin-Ram-K/Aswin-Ram-K`), first published **2026-10-08**; removed 2026-10-15T21:26:50Z, which is prospective only. File by 2027-01-07.
2. **Next = 2027-01-09** — the public repo documentation surface (13 mechanisms + `findings/PAPER-DERIVATION.md`) and the **Consonance `consonance/src/**` AGPL window**, both opening `2026-10-09T04:20:17Z` (GitHub's own event feed, `ARCHIVE_WINDOW_CHECK.md:159–160`). UCOPY1's 2027-01-10 is therefore **late by 1–2 days**.
3. **Nothing on UCOPY1's shortlist is in fact published.** Both manuscripts and `.ucurate1/pre/research-publish-packages/` are unpublished on their own records → **$150 / $215 unchanged**; no shortlist work moves out of the unpaid-group route.
4. **The correction runs the other way:** no already-published work is on the shortlist, and a *group of unpublished works* cannot include a published work — so the running-clock surface costs an **extra ≥$65 Standard Application** that UCOPY1's figure omits: "$150 now + ≥$65 on a 2027-01-08/09 clock".
5. UCOPY1's "*Never published*" is right for `repro/encoder-crossover-190/`; the **Consonance kernel `src/**` itself was published** 2026-10-09→10-10 under AGPL-3.0 (528 commits, 441 files, 16,704 LOC in `src/`) and cannot ride the unpublished-works group.
6. Forthcoming works (both manuscripts, the publish package, the two `repro/…` trees, and the eight further `PAPER_CANDIDATES.md` § G.1 candidates with verdict *publish*): clock not started → **register before publication, or within 3 months after it**. The arXiv/TMLR plan (`PUBLICATION_STRATEGY.md:20–21`) is what would break the $85 group.

## Blocker
None. 10 items could not be pinned to a record and are listed explicitly as `UNVERIFIED` in the deliverable § 5 — most materially: per-document dates inside the public repo (only the repo-level `PublicEvent` is second-precise), the `d98c4359…` digest (quoted from `PUBLICATION_STRATEGY.md:4`, **not recomputed** — no `findings/` in this workspace), and whether 2026-10-08 is the profile README's true first publication or only an upper bound (earlier ⇒ earlier deadline).

## Next unit hint
A verifier unit should re-run the dating commands and check the two-day correction against `COPYRIGHT_REGISTRATION.md:88`; the one open remediation path is a **filed-before-deadline decision for the already-published surface (rows 1–4)**, which UCOPY1's shortlist does not cover.
