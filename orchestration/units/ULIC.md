# ULIC — licence decision analysis, paper #3 (encoder crossover)

**Unit:** ULIC · **Status:** done · **Date:** 2026-10-15
**Hard bound:** max 45 tool calls · **used: ~43** (incl. report-back) · no retry exceeded 1 attempt
**Purpose (one):** write the licence decision analysis into the paper's own documents so the author can
decide with the facts in front of them — and document the conflict that made the choice consequential.

## Declared write paths (all honoured — nothing else touched)

- `papers/encoder-crossover-190/LICENSE_ANALYSIS.md` (created — deliverable)
- `papers/encoder-crossover-190/CHECKLIST.md` (append-only marked additions: §4.1, §8 items)
- `papers/encoder-crossover-190/OPEN_QUESTIONS.md` (append-only marked additions: Q2a, Q2b, closing note)
- `orchestration/units/ULIC.md`, `orchestration/handoffs/ULIC.json`

**Not touched:** `MANUSCRIPT.md`, `REFERENCES.bib`, `CLAIMS.md`, `REFS_VERIFIED.md`, `journal/`, `strategy/`,
`jobs/`, `experiments/`. **No writes to `/home/zer0null/Duval`** (reads only: `LICENSE`, `CITATION.cff`,
`package.json`, `git remote -v`, `.git/config`).

## What was verified (each with URL + date in `LICENSE_ANALYSIS.md`)

| # | fact | verdict |
|---|---|---|
| 1 | arXiv licence menu = 6 options; copyright retained for all but CC0; **"The license chosen is irrevocable and cannot be changed."**; escape hatch for unlisted licences | **CONFIRMED verbatim** — `info.arxiv.org/help/license/index.html`, 2026-10-15 |
| 2 | **"All articles on arXiv.org can be viewed and downloaded freely by anyone."** → the licence governs *reuse*, not *visibility* | **CONFIRMED verbatim** — same page |
| 3 | lab papers' actual licences: 5 checked, **2 open / 3 restrictive** | **MEASURED** — Anthropic 2212.08073 + 2501.18837 = CC BY 4.0 (icon `by-4.0.png`); Anthropic 2401.05566, OpenAI 2303.08774, OpenAI 2312.09390 = **arXiv perpetual non-exclusive 1.0** (no CC icon) |
| 4 | TMLR: **"All TMLR submissions, from the time of submission to final publication, are licensed under CC BY 4.0."** → the search snippet was **real** | **CONFIRMED verbatim** — `jmlr.org/tmlr/author-guide.html`, 2026-10-15 |
| 5 | workshop route: ICLR 2025 CFP states **no** licence requirement; OpenReview imposes **no** licence on Articles (only Comments/Config Records are CC BY 4.0) | **CONFIRMED**; per-workshop CFPs `UNVERIFIED` |
| 6 | AGPL-3.0 + repo reference | **CONFIRMED** (`LICENSE`, `package.json:122,125`, `CITATION.cff`) — **but the repo is NOT public**: `github.com/Aswin-Ram-K/Consonance` → 404, `api.github.com/repos/...` → 404, absent from the account's public repo list (all 2026-10-15) |

## The conflict, as documented

arXiv's licence is **irrevocable per posted version**; TMLR requires **CC BY 4.0 from the time of
submission**. Consequence: **a restrictive first posting cannot be undone, so the licence is effectively
chosen at first posting** — and a restrictive choice forecloses TMLR on that version. Mitigations recorded
verbatim: arXiv says *"different versions of the work can have different licenses"* and the copyright holder
retains ownership. The **enforcement** question (would TMLR reject a paper whose earlier version is
restrictive?) is `UNVERIFIED` — TMLR says nothing on arXiv interplay. **The author's decision (CC BY 4.0)
resolves it in favour of the TMLR-compatible option.**

## The decision (relayed by the author, not taken by this unit)

**CC BY 4.0 — open paper, withheld implementation.** Recorded in `LICENSE_ANALYSIS.md` §2, `CHECKLIST.md`
§4.1, `OPEN_QUESTIONS.md` Q2a. Reasons recorded: it is the only TMLR-compatible option, and it matches the
measured Anthropic practice.

**Withdrawn concern:** the first draft treated "code already public under AGPL" as a larger exposure. The
repository returns 404 and the author confirms it is private → **AGPL has triggered no obligation to the
public**. Recorded as withdrawn in `LICENSE_ANALYSIS.md` §1.6 so it is not re-"discovered".

## The open decision this unit escalated (D2)

**The disclosure scope.** `MANUSCRIPT.md` still promises everything is *"re-derivable from the target
repository `/home/zer0null/Duval`"* (§7 `:562–563`), names the eight load-bearing sources with in-repo paths
and a commit hash (`:565–576`), and states the AGPL-3.0 licence plus a now-**factually wrong** "licence must
still be made" sentence (Data and code availability `:605–608`). `LICENSE_ANALYSIS.md` §8 lists all eleven
disclosure items — **six conflict** with "implementation withheld", **five are method** — and recommends a
**minimal reproducibility subset** (fixture + schema, eval harness + exact commands, pre-registration) in a
**new small public repo**, *without* opening Consonance.

**O-1 consequence recorded:** criterion 5 names repositories *"with evidence of significant scientific,
scholarly, or business-related impact in the field"* (2 USCIS-PM M.4, fetched 2026-10-15, verbatim) — **a
private repository has zero impact evidence**; withholding forfeits it. Criterion 6 (authorship) is unaffected:
*"A petitioner need not provide evidence that the beneficiary's published work has been cited."*

## Blockers

None for this unit. One **inherited**, stated for the record: `MANUSCRIPT.md` cannot be corrected by ULIC
(other unit's file). `UNVERIFIED` count: 9 (`LICENSE_ANALYSIS.md` §9).
