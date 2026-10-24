# LICENCE_TODO.md — the code licence for this subset

**STATUS: DECIDED (recorded here by UREDACT1, 2026-10-15, on the parent unit's instruction).**

This file was written by UREPRO while the licence was **undecided**. The author has since decided, and the
as-audited copy's "NOT YET DECIDED" statement is now stale. It is corrected here rather than carried into a
release.

## The decision

- **Extracted pieces (this subset) ship under PolyForm Noncommercial 1.0.0.** Commercial use is not free; the
  terms are the template's, not a bespoke grant.
- **The main Consonance repository stays proprietary / unlicensed.** This subset's licence says nothing about it.
- **Papers remain public under CC BY 4.0** (author decision 2026-10-15). The fixture's *content* —
  `fixture/reflex-decisions.ts`, the hand-authored 190-case instrument — is covered by that paper decision.
- **Template of record:** `strategy/licence-templates/` — `PLACEMENT.md` (where the files go),
  `RELEASED-PIECE` (the licence text for a released piece), `README-PARAGRAPHS.md` (the README wording),
  `TRADE-SECRET-NOTICE.md` (the core-repo notice), `PROPRIETARY-LICENSE.txt` (the core repo).
  **This file records the decision; it does not restate the licence text** — take the text from the template so
  there is one copy of it.

## What the licence cannot do — unchanged, and still true

**A published licence is permanent for that version.** Once a version of this subset is obtainable by a third
party, that grant is irrevocable for that version. And publishing source under *any* terms **discloses it**:
PolyForm Noncommercial restricts commercial *use of the copyright*; it does not, and cannot, maintain **secrecy**
in published text (UTS1 §5.3). The residual disclosure this subset still carries is quantified in
[`REDACTION_REPORT.md`](REDACTION_REPORT.md) §7 — a licence does not address it.

- **Third-party licences are unaffected and already fixed.** The harness re-fetches three **public** checkpoints
  at run time (`answerdotai/ModernBERT-base` Apache-2.0, `microsoft/deberta-v3-base` MIT,
  `sentence-transformers/all-mpnet-base-v2` Apache-2.0, recorded in `harness/tcmodel.py`). **No weights ship**, so
  no model licence is redistributed and this subset's licence cannot narrow those terms.
- **The target's own `LICENSE` is still not copied in** (`EXCLUDED.md` E3) — copying it would decide this by
  accident, which was the reason for the exclusion and remains correct.

**Before publishing: place the licence text and the README paragraphs from the template, then re-check this
file.** That is the only step this file leaves open.
