# UCAND1 — re-triage the 15 paper candidates against the author's publication rule

**Unit:** UCAND1 · **Date:** 2026-10-15 · **Hard bound:** max 45 tool calls (used ≈16) ·
**Target:** `/home/zer0null/Duval` at HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` — **READ ONLY, never
written** (HEAD + `status --porcelain` recorded before and after; attribute: no change).

**One purpose.** Re-triage the 15 paper candidates against the author's rule of 2026-10-15 — *"dont publish
any blanket papers, only small extracted projects that go public and the papers associated with it"* — and
correct the two strategy documents that recommend the now-void plan.

**The defects being fixed.** `strategy/PUBLICATION_STRATEGY.md` §0 recommended *"ship #3 first, then #1 (the
umbrella), then #4"*. Candidate **#1 = `docs/research/PAPER_DERIVATION.md` is a blanket paper** describing the
kernel as a whole, now withheld — so the umbrella step is void. `strategy/PAPER_CANDIDATES.md` likewise
presented #1 as the programme anchor.

**The test applied to each candidate.** *Could this project be released on its own, without the rest of
Consonance, and still make sense — with its own fixture/harness/tooling that a reader could run?*
Yes → extracted project (publish; must name a releasable artifact). No → blanket (withhold). Surveys/position
pieces (#13, #14) are not extracted projects and were decided separately.

**Deliverables (all append-only where the file pre-existed).**

| # | Write path | What was done |
|---|---|---|
| A | [`strategy/PAPER_CANDIDATES.md`](../../strategy/PAPER_CANDIDATES.md) | **§G appended** — 15-row re-triage table (test · artifact · verdict · reasoning), G.1–G.5: #1 withheld in one line; the finding/mechanism split for #2, #5, #6, #7; five borderline `needs-author-decision` cases with their deciding questions; the citable-contribution mitigation. **Existing rankings §A–§F untouched.** |
| B | [`strategy/PUBLICATION_STRATEGY.md`](../../strategy/PUBLICATION_STRATEGY.md) | **§13 appended as dated errata** — §0 Step 2 void, #1 removed from the plan entirely, new sequence #3 first then the other extracted-project papers; "one citable body" void and replaced (per-paper standing, citations accrue per paper); the O-1 consequence stated plainly as an accepted cost; §13.4 lists what is unaffected and verified (venues, $0 route, JOSS mechanics, endorsement, TMLR conclusions, CC BY 4.0). **§0/§6/§9 not rewritten.** |
| C | [`strategy/WITHHELD.md`](../../strategy/WITHHELD.md) | **New register** — W1–W7 (blanket papers/docs, umbrella step, architectural claim, `src/**` + `kernel/**`, weights, patents) and M1–M13 (core mechanisms, by name, citing §4.1 of the trade-secret audit), what is *not* withheld, the O-1 cost, why the register is itself a reasonable measure, append-only change control. |

**Read for grounding (never written):** `AGENTS.md`; `strategy/PAPER_CANDIDATES.md` (all 982 lines);
`strategy/PUBLICATION_STRATEGY.md` (all 408 lines); `strategy/TRADE_SECRET_AUDIT.md` §0–§5.2;
`strategy/CODE_LICENSING_STRATEGY.md` §4–§5.3; `repro/encoder-crossover-190/README.md`;
`/home/zer0null/Duval/{tools,evals,package.json}` inventory.

**Evidence.**

- **15 candidates re-triaged: 9 `publish`** (#2, #3, #4, #5, NC1, #9, #10, #11, #12), **1 `withhold`** (#1),
  **5 `needs-author-decision`** (#6, #7, #8, #13, #14). Recipe: the §G.1 table has exactly one row per
  candidate in the §"Ranking at a glance" table (14 rows + the NC1 insertion at 6½ = 15).
- **#1 withheld:** `PAPER_CANDIDATES.md` §G.1 row 1, test `fail`, verdict `withhold`; `WITHHELD.md` W1.
- **Umbrella step removed:** `PUBLICATION_STRATEGY.md` §13.1 (`§0 Step 2 is VOID in both of its actions`).
- **O-1 cost stated:** `PUBLICATION_STRATEGY.md` §13.3 and `WITHHELD.md` §4.
- **Target read-only:** HEAD identical before/after (`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`);
  `git status --porcelain` identical before/after (4 pre-existing untracked entries:
  `.ci-trunk.txt`, `.relay/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `docs/migration/`) —
  **no entry attributable to UCAND1**. Commands: `git rev-parse HEAD`, `git status --porcelain`,
  `ls tools/`, `find tools -type f | wc -l` (=102), `ls repro/`, `head repro/encoder-crossover-190/README.md`.

**Blocker:** none.

**Next unit hint.** A verifier unit should (1) re-derive the 9/1/5 split from §G.1's rows against the §G
table, (2) confirm no candidate row is missing or duplicated and that §A–§F were not edited (append-only
check: byte-compare the first 982 lines against the pre-UCAND1 revision if a snapshot exists), and
(3) re-run the Duval containment check. The open author decisions to relay are §G.3 items 1–5 plus the
`DecisionKind`/fixture-rationale cut (M11) in `WITHHELD.md` §6.

**Write paths (declared, touched):** `strategy/PAPER_CANDIDATES.md`, `strategy/PUBLICATION_STRATEGY.md`,
`strategy/WITHHELD.md`, `orchestration/units/UCAND1.md`, `orchestration/handoffs/UCAND1.json`. **Nothing
else** — in particular `papers/`, `repro/`, `jobs/`, `journal/`, `experiments/` and
`strategy/CODE_LICENSING_STRATEGY.md` were read only (the audit and licensing files were not touched by this
unit).
