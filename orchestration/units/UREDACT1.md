# UREDACT1 — sanitise the paper-#3 release package and prove reproduction still holds

**Unit:** UREDACT1 · **Status:** done · **Date:** 2026-10-15 (UTC)
**One purpose:** produce a sanitised copy of `repro/encoder-crossover-190/` that (a) removes mechanism
disclosure and (b) provably still reproduces every headline number in `papers/encoder-crossover-190/CLAIMS.md`.

## Fixed
UTS1 `strategy/TRADE_SECRET_AUDIT.md` §4.3/§5.2: the reproducibility subset for paper #3 ships the complete
`DecisionKind` union, the six kernel namespaces, and 335 mechanism-narrating fixture lines, while `EXCLUDED.md` E1
bounds only *implementation code*.

## Carded premise, and its correction
The card proposed redacting the fixture's `rationale` + `namespaces` ("used in review, not fed to the model").
**Tested, not assumed: free for every number, and INSUFFICIENT.** Measured independently here and confirmed by
UVER5 C1/O1: the `question` text carries more kernel vocabulary (56 occurrences / 47 cases) than the rationales
(31 / 25), and `question`/`options` **are** the model input, so they cannot be edited without moving every number.
See `REDACTION_REPORT.md` §7 and §10.2-10.3.

## Hard bound
50 tool calls. Used ~47. No attempt abandoned; every failing tool call retried until green (4 red builds in
`redact.py`, each refused loudly rather than redacting blind).

## Write paths (declared, honoured)
`repro/encoder-crossover-190-SANITISED/**`, `orchestration/units/UREDACT1.md`,
`orchestration/handoffs/UREDACT1.json`. `strategy/`, `papers/`, `jobs/`, `journal/`, `experiments/` and the
as-audited `repro/encoder-crossover-190/` untouched.

## Deliverables
- `repro/encoder-crossover-190-SANITISED/` — VARIANT A (union kept; rationale/namespaces values emptied)
- `…/REDACTION_REPORT.md` (leak inventory, redaction, acceptance test, cost, union trade, residual scan, §10 amendment)
- `…/README.md` (incl. the fresh-export rule), `…/INTEGRITY.md` (41 file hashes + digests + provenance)
- `…/variants/no-union/` — VARIANT B (labelled), `…/redact.py`, `…/verify/**` (acceptance test + verbatim logs)

## Evidence (verbatim logs in `…/verify/`)
- strict mechanism lines: as-audited **210** → sanitised **154** (56 removed); `LEAD-WIRING.md` 142→43
- reproduction on the shipped fix: `prepare.py` exit 0, stdout identical, `train.jsonl`/`dev.jsonl` byte-identical
- scoring projection `57a29b4e…` identical; chance floor 0.29105263157894734 both
- all CLAIMS numbers recomputed from inside the sanitised tree; 2×2 `39+27+90+34 = 190`; p=4.166818e-09; MDE 0.159494
- `metrics.json`: orig-regenerated == san-regenerated == shipped (4 hand-added keys stripped)
- `disagreements.jsonl`: only `recorded_rationale` differs, now empty (18 rows)
- residual: 154 lines, all classified (instrument `question` 47 cases / option labels 2 / `DecisionKind` type name 4)
- target HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; as-audited subset 42/42 manifest entries unchanged
