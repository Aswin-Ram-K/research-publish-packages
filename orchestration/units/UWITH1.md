# UWITH1 — re-issue `WITHHELD.md` on the corrected disclosure facts

**Unit:** UWITH1 · **Date:** 2026-10-15 · **Parent:** `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`
**Target of record:** `/home/zer0null/Duval` at HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` — **read-only,
never written; no git command run there.**

## Purpose (one)

Re-issue `strategy/WITHHELD.md` on the corrected facts — **12 of 13 mechanisms already public; only M11
undetermined** — narrow its protective claim to the implementation, and propagate the correction into the two
documents that repeat it (`PUBLICATION_STRATEGY.md`, `PAPER_CANDIDATES.md`), using each document's own
append-only change control.

## Work order read first

- `strategy/VERIFICATION_REPORT_6.md` (UVER6, verdict `WITHHELD.md` = **fail as issued**)
- `strategy/PRIOR_DISCLOSURE_AUDIT.md` (UDISC1)
- `strategy/VERIFICATION_REPORT_5.md` (UVER5)
- `strategy/TRADE_SECRET_AUDIT.md` §4.1/§4.3/§5.1/§5.2 (read-only source, **not edited**)

## Required changes and disposition

| # | Change | Disposition |
|---|---|---|
| A1 | M1–M10, M12, M13 → `ALREADY PUBLIC` with location, date, **MIT**, byte-identical evidence; trade secret not available; MIT already grants free commercial use | `WITHHELD.md` §8.1 |
| A2 | M11 stays `undetermined` — not guessed either way | `WITHHELD.md` §8.2 |
| A3 | Protective claim narrowed to the **implementation** (`src/**`, concrete types, code-level state-class catalogue, private corpora, `tools/**`, unpublished prose) | `WITHHELD.md` §8.3 |
| A4 | Corrected strategy stated in one place: **publish the design, keep the code** | `WITHHELD.md` §8.4 |
| A5 | C6 fixed — M12 (and via rationales M10/M7) are also in the release set | `WITHHELD.md` §6 + §8.5 |
| A6 | Licensing consequence for already-public material; prose-under-a-software-licence flagged `UNVERIFIED` | `WITHHELD.md` §8.6 |
| B | O-1 inversion propagated to **3** live instances | `WITHHELD.md` §4/§8.7; `PUBLICATION_STRATEGY.md` §13.3+§13.6(b); `PAPER_CANDIDATES.md` §G.4 |
| C1 | `PUBLICATION_STRATEGY.md:47` "Published artifacts: none" corrected (true as to arXiv/DOI only) | corrected in place |
| C2 | Five residual live `#1` refs (`:4`, `:67`, `:274–275`, `:292`, `:296`) fixed/marked | 5/5 marked in place |
| C3 | §13.4 (venue / $0 / endorsement / TMLR / CC BY 4.0) left intact | untouched |
| D1 | C5 — #14 "no Consonance content" corrected (33 `Consonance` mentions; §8 at `:679`); #13 left alone | `PAPER_CANDIDATES.md` §G.1 #14 |
| D2 | Drop #1's "by its own §6.4 admission"; verdict unchanged (limb (a) fails via contribution 2 `:72–76`; limb (b) via private M13) | `PAPER_CANDIDATES.md` §G.1 #1 |

**Not re-triaged:** the 9 `publish` / 1 `withhold` / 5 `needs-author-decision` split — UVER6 re-derived it.

## Evidence re-verified by this unit (not taken on trust)

```
sha256sum /home/zer0null/Duval/docs/research/PAPER_DERIVATION.md
  d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802  46636 B   (matches UVER6's both-sides hash)
grep -c "Consonance" docs/research/AGENT_HARNESSES_2026.md              -> 33
grep -n "^## 8" docs/research/AGENT_HARNESSES_2026.md                   -> 679:## 8. Implications for Consonance
grep -c StateClass / SandboxSpec / "gate chain" (same file)             -> 2 / 5 / 1
LONG_HORIZON_EVALS_2026.md: Consonance 0, "observation stream" 0, "enforcement by absence" 0,
  DecisionKind 0, "derived state" 0                                     (#13's claim reproduces clean)
PAPER_DERIVATION.md:669–672 §6.4 middle sentence present: "Every artefact lives in `tools/`, which is the
  operator's rule: experiments land outside the kernel and are promoted only when a measurement justifies it."
PAPER_DERIVATION.md:72–76 contribution 2: "The loop itself: observation stream → derived state → projection"
```

## Hard bound

**45 tool calls.** Reported honestly in the handoff.

## Write paths (declared — nothing else touched)

`strategy/WITHHELD.md`, `strategy/PUBLICATION_STRATEGY.md`, `strategy/PAPER_CANDIDATES.md`,
`orchestration/units/UWITH1.md`, `orchestration/handoffs/UWITH1.json`.

**Not touched:** `strategy/TRADE_SECRET_AUDIT.md`, `strategy/licence-templates/**`, `strategy/VERIFICATION_REPORT_*.md`,
`repro/**`, `papers/**`, `jobs/`, `journal/`, `experiments/`, and never `/home/zer0null/Duval`.
