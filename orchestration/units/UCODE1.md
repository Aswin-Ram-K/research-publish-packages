# UCODE1 — Code-licensing strategy memo

**Status:** done · **Date:** 2026-10-15 · **Bound:** 45 tool calls (`kill_condition`: stop at 45)

## One purpose
Produce a code-licensing strategy memo for a **source-available, free-for-personal-use, paid-for-
commercial** model, with the real options, their trade-offs, and the consequence for the author's O-1
goal.

## Declared write paths (touched nothing else)
- `strategy/CODE_LICENSING_STRATEGY.md`
- `orchestration/units/UCODE1.md`
- `orchestration/handoffs/UCODE1.json`

Target `/home/zer0null/Duval` was **read only**. `LICENSE` was read and deliberately **left untouched**.
No git state change in the target. `journal/`, `jobs/`, `experiments/`, `papers/`,
`strategy/PUBLICATION_STRATEGY.md` were not touched.

## The model, as finally specified
Four requirements: (1) **source-available only** — never called open source; (2) free for
personal/at-home/hobby/research use; (3) **commercial → paid, with no free commercial evaluation**;
(4) community modifications welcome and publishable, but the project integrates **ideas, not code**.

## Headline findings
1. **The contradiction.** `/home/zer0null/Duval/LICENSE` is AGPL-3.0 (lines 1–2, verified by reading).
   AGPL **permits free commercial use** — preamble *"charge for them if you wish"*, §4 *"You may charge
   any price or no price"*. It controls **source disclosure**, not **who may use**. It **fails
   requirement 3 outright** and must be **replaced, not amended**: AGPL §7 makes any non-commercial
   rider a *"further restriction"* and §10 forbids imposing further restrictions. "AGPL + no commercial
   use" is internally contradictory.
2. **NC ⇒ not open source.** OSD criterion 6 forbids field-of-use restriction; PolyForm NC, BUSL, SSPL,
   ELv2 and Commons Clause are **absent** from `opensource.org/licenses`. The project is
   **source-available**, which is the author's own correct term.
3. **PolyForm Noncommercial 1.0.0 fits; nothing else does.** It is the only established template that
   makes commercial use **paid** while keeping source public and permitting modification and
   redistribution. AGPL, SSPL, ELv2, MIT/Apache-2.0 and BUSL all permit free commercial use in some
   material form; CC BY-NC is the wrong instrument for code (CC's own advice); dual licensing lets
   commercial users in free.
4. **Prong (a) covers at-home use — confirmed.** *"personal study, private entertainment, **hobby
   projects, amateur pursuits** ... without any anticipated commercial application"*. And that qualifier
   is now the **feature**, not a defect: it delivers requirement 3. **No evaluation grant, no PolyForm
   Free Trial 1.0.0, no BUSL non-production allowance.**
5. **Contributions: no CLA, no DCO needed** — because no contributor code enters the project. One real
   risk remains: **verbatim copying imports the contributor's NC licence and that code then cannot be in
   a paid commercial licence.** Ideas/algorithms are fine (expression vs. ideas). Hygiene rule:
   re-implement, never copy-paste, never merge patches, state the policy.
6. **O-1 trade-off, stated not argued.** USCIS criterion 5 rewards *"contributions to repositories ...
   with evidence of significant ... impact"* and lists *"Evidence of commercial use of the beneficiary's
   work"* adjacently. Foreclosing commercial evaluation suppresses corporate adoption and therefore the
   impact evidence. **Mitigation that is real:** PolyForm NC's *Noncommercial Organizations* clause gives
   academia/research/government free use **regardless of funding source** — the users who cite and
   publish. For a scholarly-impact petition this materially reduces the cost.
7. **Private-repo relief.** Unauthenticated fetch of `github.com/Aswin-Ram-K/Consonance` → **404**
   (2026-10-15). No licence granted to anyone; the AGPL in the tree is an **intention, not a grant**;
   nothing is irrevocable; the choice is fully open — and because there is no contributor code, there is
   no third-party copyright to negotiate around.

## Recommendation
**PolyForm Noncommercial 1.0.0** as `LICENSE` + a **commercial licence sold directly by the author**
(`COMMERCIAL.md`) + a **contribution policy that accepts ideas only** (`CONTRIBUTING.md`) + a README
paragraph saying "source-available, not open source". No evaluation grant. No CLA. **Replace the AGPL
file before publishing.** Alternative on file: AGPL + paid commercial licence (dual licensing) if the
O-1 impact goal later outweighs requirement 3.

## Deliberately excluded (with reasons in the memo)
CC BY-NC 4.0 (CC advises against for software) · PolyForm Free Trial 1.0.0 (grants the eval the author
forbids) · BUSL 1.1 (grants free non-production use; later becomes open source; ASF Category X) · SSPL v1
and ELv2 (permit free commercial use) · MIT/Apache-2.0 (gives away the commercial rights) · no licence at
all (zero adoption, zero evidence) · any bespoke licence.

## Not verified
11 items in §7: private status inferred from a 404 (not authenticated); GitHub API 403 rate-limited;
BUSL parameter text not cleanly extracted; HashiCorp FAQ HTTP 429; ELv2 from rendered page (raw file
empty); "NC is not open source" is a *derivation* from OSD §6 + list absence; revenue is judgement; no
company page banning NC by name found; O-1 citations are policy guidance not regulation; the
expression/ideas principle is stated as general principle with no source fetched; and **the CLA
relicensing-grant specifics were NOT verified** (Apache ICLA now redirects to a PDF; extraction returned
nothing) — so if the author ever moves to accepting code, that must be researched first.

## Caveat
**Not legal advice.** The model is simple enough that dual-licensing complexity is gone, but a **short
(~20-minute) review of the commercial licence terms** is still worth buying — that is the one drafted
document that would actually be tested. Also raise: (a) any employment/funding encumbrance on the
copyright, and (b) consistency of the commercial terms with the immigration posture.
