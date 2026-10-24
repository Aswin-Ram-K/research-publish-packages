# UVER12 — Independent verifier: REGEN_ASSESSMENT.md (UREGEN1)

**Status:** COMPLETE
**Bound:** 40 tool calls (used ~31).
**Declared write paths:** `strategy/VERIFICATION_REPORT_12.md`, `orchestration/units/UVER12.md`,
`orchestration/handoffs/UVER12.json`, `scratch/uver12/**`.
**Read-only respected:** target `/home/zer0null/Duval` and `/home/zer0null/research-publish-packages`
were never written; no plain `git -C /home/zer0null/Duval status` was run.

## Verdict: PARTIAL — UREGEN1's science holds; the brief's central allegation was the orchestrator's error

The orchestrator's accusation ("60 of 62 sit in exactly 3 files — disagreements.jsonl, RUN.json,
second-labeller-190/ROBUSTNESS.md") does **not appear anywhere in `strategy/REGEN_ASSESSMENT.md`**.
The report's §2 actually names *all 62 lines by file:line across 15 files*, and that map **matches my
independent scan exactly**. The bad wording was in UREGEN1's first *status message* (not on disk), not
its artifact. UREGEN1's substantive claims survive; its "62 is a floor" is **overstated for its stated
scope**.

## Evidence (all commands re-run against the tree myself)

- `scratch/uregen1/build-run.log:2270` = `GATE RESULT: FAIL — 62 HARD-FAIL hit(s) and 2124 REVIEW hit(s).`
- 24 HARD patterns confirmed at `orchestration/units/UBUILD1.build.sh` heredoc (613–636). Re-scan of
  `scratch/uregen1/pkg/research-publish-packages` (`--exclude-dir=.git`, exclude `gate.sh`):
  **62 distinct matched lines**; per-pattern sum **63** because `eval/second-labeller/disagreements.jsonl:2`
  carries both `StateClass` and `grantPolicy`. Per-pattern: `expanded[` 26, `admit(` 20,
  `REDACTION_REPORT` 10, `StateClass` 2, `grantPolicy` 2, `EXCLUDED.md` 2, `VERIFICATION_REPORT` 1.
- File distribution (distinct lines): reflex-decisions.ts 10; eval-shuffled-label.json 8;
  eval-majority-class.json 7; eval-deberta-v3-base.json 7; eval-setfit-mpnet.json 6;
  eval-modernbert-base.json 6; baselines.json 6; disagreements.jsonl 3; fixture-190.json 2;
  LEAD-WIRING.md 2; parse_fixture.py 1; metrics.json 1; RUN.json 1; recompute-claims.py 1;
  export-fixture.ts 1 → **15 files**.
- `second-labeller-190/ROBUSTNESS.md`: **ZERO HARD hits**; its `memory.admission`/`capability.family`
  lines are REVIEW-only patterns.
- **Q1 floor experiment** (`scratch/uver12/tree-sub`, `scratch/uver12/tree-disp`):
  * Display-only substitution of the 40 `results/*.json` label echoes → `verify/recompute-claims.py`
    exit 0, `ALL CLAIM NUMBERS PRESERVED: True`, fixture-correctness digest unchanged
    `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a`. **Reachable floor = 22.**
  * Consistent file-wide instrument substitution (22 files) → `routeA/ties` **120 → 119**; agreement
    0.34210526315789475, kappa 0.32520740993294694, exact_index 65 all unchanged. So option labels are
    genuinely not free — UREGEN1/UTOK2's constraint is REAL, but it binds only ~7 lines.
- Digests verified byte-for-byte: reflex-decisions.ts source `076164ac…` (145,031 B at
  `repro/encoder-crossover-190/fixture/reflex-decisions.ts`), sanitised `751dc007…` (90,738 B at
  `repro/encoder-crossover-190-SANITISED/fixture/reflex-decisions.ts`), regenerated `23515654…`
  (pkg tree). fixture-190.json source `a6536c04…` (145,628 B), sanitised `3c64af01…` (84,550 B),
  regenerated `3f6e41d2…`. Report §2's `code/` prefixes are ship-set-relative; underlying paths are as above.
- `redact.py:204-206` `CASE_FIELDS = ("question",)` + comment; `DISCLOSURE_SKIP` includes `results/`,
  `harness/data/`, `fixture/`, `second-labeller/disagreements.jsonl` — confirms no label substitution.
- Stage D (`redact.py:855-895`): recomputes `flag = (sh == h)`; regenerated MANIFEST has flagTrue 25,
  **0 contradictions**; sanitised MANIFEST has flagTrue 39, **8 contradictions** (the 6 UREGEN1 named
  plus 2 pre-existing source-level: `fixture/DECISION_CASE_SCHEMA.ts`,
  `preregistration/EXP12-typed-channel-comparison-prereg.md`, both also contradictory in the pristine
  source MANIFEST). `redact.py:873-883` (recount) closes the `identical_to_source` rewrite.
- Whole tree: `repro/encoder-crossover-190-SANITISED` = **494** (reproduces exactly); `scratch/uregen1/tree`
  = **382**, NOT the reported 360. minus the 9 process files = 83 (report 98) and 207 (report 237).
- Old digest `57a29b4e…` recorded in **91** workspace files (report 89); **0** inside the built ship
  package `scratch/uregen1/pkg/research-publish-packages` and none in `ship_staged.txt`.
  `repro/encoder-crossover-190-SANITISED/INTEGRITY.md:93` still prints `57a29b4e…` in the sanitised
  column as "unchanged" — now false after regeneration (new digest `b85e4585…`).
- `routeA.ties` = **120** in both `repro/encoder-crossover-190-SANITISED/second-labeller/metrics.json`
  and `scratch/uregen1/tree/second-labeller/metrics.json` (Q5 confirmed).

## Reachable floor (Q1)
62 hard-fail lines. The 40 in `eval/results/*.json` are display archives no published number depends on
(verified) → clearable. Of the remaining 22: ~7 are number-bearing instrument lines
(`reflex-decisions.ts:146,:572`; `harness/data/fixture-190.json:72,:573`;
`second-labeller/disagreements.jsonl` 3), the other ~15 are filename pointers/docstrings/correction
notes clearable by prose rewrite. **Floor = 22** with display-only substitution; only touching the
option-label vocabulary reaches 0, at the cost of `routeA.ties` 120→119.

## Containment
Wrote only to declared paths. Targets untouched.
