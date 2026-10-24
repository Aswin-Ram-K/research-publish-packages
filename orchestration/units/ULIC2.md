# ULIC2 — Draft the two-tier licence templates

**Purpose (one):** draft seven copy-ready licence/policy templates in the workspace for the author
to place himself. **No file in the target repo is written.**

**Status:** done.

## Bound
Max 40 tool calls. **Actual: 23.** No retries needed; no blocker encountered.

## Write paths (declared)
`strategy/licence-templates/**`, `orchestration/units/ULIC2.md`, `orchestration/handoffs/ULIC2.json`.
Nothing else was written.

## Inputs read
- `AGENTS.md`
- `strategy/CODE_LICENSING_STRATEGY.md` §3.3, §5 (5.1–5.7), §6, §7, §8 — the implemented analysis
- `/home/zer0null/Duval/LICENSE` — **read only**, first 5 lines, to confirm it is AGPL-3.0
- Canonical PolyForm source: `https://polyformproject.org/licenses/noncommercial/1.0.0` and
  `.../1.0.0.txt` (both HTTP 200, fetched 2026-10-15)

## Structure implemented (two-tier)
| | Main Consonance repo | Each extracted released piece |
|---|---|---|
| Status | proprietary, private, trade secret | source-available |
| Licence | `PROPRIETARY-LICENSE.txt` → `LICENSE`, "All rights reserved" | PolyForm NC 1.0.0 verbatim + `Required Notice:` |
| Commercial | none — nothing licensed | `COMMERCIAL.md`, paid licence by contact |
| Contributions | not accepted | forks welcome; ideas only, no code merged |
| README | "Confidential and proprietary" | "source-available, not open source" |

## Deliverables
1. `strategy/licence-templates/PROPRIETARY-LICENSE.txt`
2. `strategy/licence-templates/TRADE-SECRET-NOTICE.md`
3. `strategy/licence-templates/RELEASED-PIECE/LICENSE`
4. `strategy/licence-templates/RELEASED-PIECE/COMMERCIAL.md`
5. `strategy/licence-templates/RELEASED-PIECE/CONTRIBUTING.md`
6. `strategy/licence-templates/README-PARAGRAPHS.md`
7. `strategy/licence-templates/PLACEMENT.md`

## Evidence
- PolyForm body diffed against the canonical plain text: **4563 bytes vs 4563 bytes, `diff` empty —
  identical**. Not paraphrased.
- `grep -rn "AGPL\|Affero"` over `strategy/licence-templates/` matches **only prose in
  `PLACEMENT.md`** that instructs deletion of AGPL. **No AGPL text in any drafted licence file.**
- `grep -rn "^Required Notice:"` → `RELEASED-PIECE/LICENSE:1`.
- Name/logo reservation present in all four released-piece templates.
- Target untouched: `/home/zer0null/Duval/LICENSE` mtime `2026-09-28 12:30:24.333955905 -0500`,
  size 34523, md5 `eb1e647870add0502f8f010b19de32af` — unchanged; no `git` command run in the
  target; only `head`, `stat`, `find`, `md5sum` reads.

## Recorded gaps (not filled — §5 is silent)
1. `<CONTACT>` commercial address not supplied by the strategy.
2. The paid commercial agreement itself is out of scope (and §8 recommends legal review of it).
3. `strategy/TRADE_SECRET_AUDIT.md` **was not on disk**; `TRADE-SECRET-NOTICE.md` points to it as
   the intended citation and says so explicitly. No legal proposition invented in its place.
4. §5.1/§6 Stage 0 say "replace AGPL with PolyForm NC in the main repo"; the author's 2026-10-15
   position makes the main repo proprietary and PolyForm NC attach to extracted pieces. The
   author's position was implemented; the divergence is recorded in `PLACEMENT.md` §5.4.
5. The academic-carve-out README sentence (§6 rule 6) is recommended but not worded by the
   strategy — no wording invented.

## Not done
No file written to `/home/zer0null/Duval`. No `LICENSE` in the target was replaced or amended.
Papers, `repro/`, `jobs/`, `journal/`, `experiments/` and `strategy/CODE_LICENSING_STRATEGY.md`
untouched. No decision taken that `CODE_LICENSING_STRATEGY.md` does not already contain.
