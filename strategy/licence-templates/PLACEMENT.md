# PLACEMENT — where each drafted file goes, and in what order

> **These are DRAFTS in the Research Extractor workspace (`/home/zer0null/reserach extarctor`).**
> Nothing has been copied into any repository, and **nothing will be**: replacing or adding a
> licence is a legal act the author performs. The target repository `/home/zer0null/Duval` was
> read only and was **never modified** by this unit.
>
> Sources implemented: `strategy/CODE_LICENSING_STRATEGY.md` §5 (recommendation), with the two-tier
> structure fixed by the author's IP position of 2026-10-15 (quoted in the unit card): the main
> Consonance repository stays **proprietary and trade secret**; each **extracted piece** released
> publicly gets **PolyForm Noncommercial 1.0.0**.

## 1. Which file goes where

| Drafted file (in this workspace) | Destination | Notes |
|---|---|---|
| `PROPRIETARY-LICENSE.txt` | the main Consonance repo, as **`LICENSE`** | **Replaces** the existing `LICENSE` file. Do not keep both. |
| `TRADE-SECRET-NOTICE.md` | the main Consonance repo, as `TRADE-SECRET-NOTICE.md` (root) | Interior file. Referenced by the README paragraph and by `LICENSE`. |
| `README-PARAGRAPHS.md` → **Case A** paragraph | the main Consonance repo `README` | Copy the paragraph verbatim. |
| `RELEASED-PIECE/LICENSE` | the root of **each** extracted, publicly released piece, as **`LICENSE`** | Contains the PolyForm NC 1.0.0 text verbatim **plus** the `Required Notice:` line. |
| `RELEASED-PIECE/COMMERCIAL.md` | the root of **each** released piece, as `COMMERCIAL.md` | Contact is the published repository's own issue tracker (<https://github.com/Aswin-Ram-K/research-publish-packages>) — no personal address is published. |
| `RELEASED-PIECE/CONTRIBUTING.md` | the root of **each** released piece, as `CONTRIBUTING.md` | |
| `README-PARAGRAPHS.md` → **Case B** paragraph | the `README` of **each** released piece | Copy the paragraph verbatim. |

## 2. What to delete

- **Delete the existing `LICENSE` file in the main repository and put `PROPRIETARY-LICENSE.txt` in
  its place as `LICENSE`.** It currently contains **AGPL-3.0** (verified by reading the target's
  `LICENSE`: it opens *"GNU AFFERO GENERAL PUBLIC LICENSE / Version 3, 19 November 2007"*).
- **Replace it, never amend it.** A non-commercial rider cannot lawfully be bolted onto AGPL-3.0
  (`CODE_LICENSING_STRATEGY.md` §5.4). "AGPL + no commercial use" is internally contradictory.
- **Do the same in every released piece:** no AGPL file may remain in any repository that is made
  public, and no released piece may contain two licence files.
- **Do not leave the old file in git history as the current statement of terms** — the file in the
  tree at release is what a reader sees. (History rewriting is **not** required and is **not**
  recommended here; the strategy does not ask for it.)

## 3. Order of operations

1. **Placeholders are filled** (2026-10-16), and none remains: the year is `2026`, the copyright
   holder is `Aswin-Ram-K`, and the commercial contact is the published repository's own issue
   tracker (`https://github.com/Aswin-Ram-K/research-publish-packages`) — no personal address is
   published. The project-name placeholder was **not** filled: the author does not reserve the name
   (and does not mind it being shared), so the name/logo reservation it belonged to was **removed**
   instead — see § 4. Nothing ships with an angle-bracket placeholder visible.
2. **Replace the licence in the private main repository first** — delete the old `LICENSE`, add
   `PROPRIETARY-LICENSE.txt` as `LICENSE`, add `TRADE-SECRET-NOTICE.md`, and add the Case A README
   paragraph. Do this **while the repository is still private**, so the tree is already correct
   the moment it is looked at.
3. **Put the released-piece files in place in the piece's own repository before that repository
   goes public** — `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`, and the Case B README paragraph.
   §6 (rule 3) requires `COMMERCIAL.md` and `CONTRIBUTING.md` to exist *before* the repo goes
   public: no window of ambiguity.
4. **Only then make the repository public.** One repository per released piece — separate
   repositories, not one repository with mixed licences (§6, rule 1).
5. **Date the release and keep a copy of the exact licence text used for that version** (§6,
   rule 7). The audit trail is itself evidence of a deliberate programme.

> ### ⚠️ The one irreversible step
> **Replace the licence BEFORE the repository is ever made public.** Once a version is published
> under a licence, that grant is **permanent for that version** and cannot be withdrawn
> (`CODE_LICENSING_STRATEGY.md` §1, §5.4, §5.5, §6). Publishing first and fixing the licence
> afterwards does not undo the grant that publication made. This notice also cannot withdraw a
> grant already made for a version that was published earlier.

## 4. Recorded gaps## 5. Recorded gaps (left for the author — not decided here)

1. **The commercial contact address — RESOLVED (2026-10-16).** `CODE_LICENSING_STRATEGY.md` §5.1
   supplies no address: it says only that the paid licence is "offered directly by the author …
   arranged by contact". By author decision the contact is the published repository's own issue
   tracker, `https://github.com/Aswin-Ram-K/research-publish-packages`. No personal address is
   published.
2. **The paid commercial agreement itself** is not drafted here. It is out of this unit's declared
   scope and its write paths. §8 recommends a short legal review of it and of `COMMERCIAL.md`.
3. **`strategy/TRADE_SECRET_AUDIT.md` now exists on disk** at
   `strategy/TRADE_SECRET_AUDIT.md` (unit UTS1; **507 lines / 48,851 bytes**, written **2026-10-15
   15:31:34**; presence checked by UFIX5 on 2026-10-15). `TRADE-SECRET-NOTICE.md` points to it as the
   intended legal-basis citation and says so explicitly; no legal proposition has been invented in its
   place. *Corrected by UFIX5, 2026-10-15 — this item previously read "is not present on disk", which
   was true when written and false once the audit landed. Its findings are not imported here.*
4. **Reconciliation of §5.1/§6 with the author's 2026-10-15 position — RESOLVED.** §5.1 and §6 (Stage 0)
   describe replacing AGPL with PolyForm NC in the main repository. The author's position of
   2026-10-15 makes the main Consonance repository **proprietary (no licence)**, with PolyForm NC
   attaching to the **extracted released pieces** (§6 Stage 2 onwards). That divergence is now
   **resolved** by the dated **ERRATA** at the top of `strategy/CODE_LICENSING_STRATEGY.md` (unit
   UMEMO1, 2026-10-15), which fixes the **two-tier structure** in force: **main repository =
   proprietary notice; each released piece = PolyForm Noncommercial 1.0.0**. §5.1 and §6 Stage 0 of
   that memo are marked **SUPERSEDED** in place (`:433`, `:600`; re-verified 2026-10-15 by UFIX7 —
   the citation previously read `:423`, `:590`, stale by 10 after the ERRATA block was added). These drafts implement the author's
   position. *Corrected by UFIX5, 2026-10-15 — this item previously ended "The divergence is recorded
   here rather than resolved by this unit", which was true when written and false once UMEMO1's errata
   landed.*
5. **The academic carve-out sentence** (naming the *Noncommercial Organizations* clause in the
   README, §6 rule 6) **is now drafted** — see `README-PARAGRAPHS.md` (it is inside the Case B
   paragraph, and repeated as a standalone line). It is **required in every released piece's
   README**: the licence grants these institutions free use *silently*, so a released piece whose
   README leads with "commercial use requires a paid licence" makes them self-exclude. The wording
   quotes the licence itself. *Drafted 2026-10-15 by UFIX7; this item previously read "recommended
   but not worded by the strategy; no wording has been invented."*
6. **Not legal advice.** `CODE_LICENSING_STRATEGY.md` §8: the memo is a research synthesis by a
   non-lawyer and is not legal advice.
7. **Name/logo reservation — REMOVED (2026-10-16).** The former § 4 (name and logo reservation,
   trademark) was **deleted** by unit ULICENCE5 on the author's instruction: he does not reserve the
   project name or logo, does not mind the name being shared, and is not seeking a trademark. The
   removed text is carried verbatim in `orchestration/handoffs/ULICENCE5.json`. Sections "Recorded
   gaps" and "What this unit did and did not do" were renumbered 5→4 and 6→5.
8. **US copyright registration — DECLINED (2026-10-16).** The author declined registration and chose
   **licence-based protection alone**. `strategy/COPYRIGHT_REGISTRATION.md` and
   `strategy/COPYRIGHT_DEADLINES.md` are retained as analysis, not as a task list, and carry a dated
   closure note at the top. **Consequence, stated honestly:** without registration, statutory damages
   and attorney's fees under 17 U.S.C. § 504 are unavailable for these unpublished works, while
   actual damages, the infringer's profits and the licence's own terms remain.

## 5. What this unit did and did not do

- **Did:** read `AGENTS.md`, `strategy/CODE_LICENSING_STRATEGY.md` (§3.3, §5, §6, §7, §8), and the
  target's `LICENSE` (read-only, to confirm it is AGPL-3.0); fetched the PolyForm text from the
  canonical source; drafted the seven template files listed above.
- **Did not:** write anything in `/home/zer0null/Duval`; run `git` in the target or change any git
  state; decide any licence question; invent licence terms; touch the papers, `repro/`, `jobs/`,
  `journal/`, `experiments/`, or `strategy/CODE_LICENSING_STRATEGY.md`.
