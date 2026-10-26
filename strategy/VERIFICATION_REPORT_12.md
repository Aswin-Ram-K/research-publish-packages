# VERIFICATION_REPORT_12 — UVER12 verdict on `strategy/REGEN_ASSESSMENT.md` (UREGEN1)

**Verdict: `partial`.** UREGEN1's measured science reproduces; the orchestrator's central allegation
against it was the orchestrator's own error; UREGEN1's "62 is a floor" is **overstated for its stated
scope**. Bound: 40 tool calls (used ~31). Targets `/home/zer0null/Duval` and
`/home/zer0null/research-publish-packages` were never written; no plain `git -C … status` was run.

## Q1 — Is 62 a FLOOR? (the decisive experiment)

**No, not at 62 — the reachable floor is 22, and 0 costs exactly one published number.**

I copied the regenerated tree to `scratch/uver12/` and ran two substitutions.

- **Display-only** (`scratch/uver12/tree-disp`): applied the instrument-token rules to the 40 hits in
  the six `results/*.json` archives only. Then `python3 verify/recompute-claims.py` → **exit 0**,
  `ALL CLAIM NUMBERS PRESERVED: True`, fixture-correctness digest unchanged
  `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a`. The 40 hits are clearable with
  **zero** number movement → **floor = 22**.
- **Consistent file-wide instrument substitution** (`scratch/uver12/tree-sub`, 22 files):
  `routeA/ties` **120 → 119**; agreement `0.34210526315789475`, kappa `0.32520740993294694`,
  `exact_index_matches` 65 all unchanged. So substituting the option-label vocabulary itself is **not
  free** — UTOK2's ONE-LABEL measurement (REPORT2 §5) generalises: even a consistent bijection moves
  `ties`, because `route_a` is a tokeniser-overlap scorer and `admit(`→`ADMIT_A` adds the token `a`.

**Verdict:** UREGEN1's constraint is real but it applies it to the wrong 40 lines. It lumped the
`results/*.json` label echoes in with the instrument at report line 121–127 ("62 is a floor given that
constraint"). The parent's hypothesis is correct: those 40 are display archives that nothing reads for a
number (`recompute-claims.py` reads them but still passes). **Reachable floor = 22**, namely the 10 +
2 + 3 + 1 + 1 + 2 + 1 + 1 + 1 residual lines in `reflex-decisions.ts`, `harness/data/fixture-190.json`,
`second-labeller/disagreements.jsonl`, `recompute-claims.py`, `parse_fixture.py`, `LEAD-WIRING.md`,
`export-fixture.ts`, `RUN.json`, `metrics.json`. Of those 22, only ~7 are number-bearing instrument lines
(2 option lines in `reflex-decisions.ts`, 2 in `harness/data/fixture-190.json`, 3 in
`disagreements.jsonl`); the rest are filename pointers/docstrings/correction notes and can be reworded
without touching a number. Reaching **0** requires accepting `routeA.ties` 120→119.

## Q1 (cont.) — reproducible floor command
```
cp -r scratch/uregen1/tree scratch/uver12/tree-disp
python3 scratch/uver12/subst_results_only.py          # or the inline heredoc in the unit card
cd scratch/uver12/tree-disp && python3 verify/recompute-claims.py   # ALL CLAIM NUMBERS PRESERVED: True
```

## Q2 — Stage-D reversal: UREGEN1 is RIGHT

`redact.py:855-895` re-derives the identity flag from actual bytes:
`sh = _sha(sp)`, `flag = (sh == h) if sh else e.get(key)`, then writes `e[key] = flag`. It therefore
*repairs* stale `identical_to_source: true` rows rather than preserving them.

| MANIFEST | entries | flag-True | contradictions (`sha256 != source_sha256` while flag True) |
|---|---|---|---|
| `repro/encoder-crossover-190/MANIFEST.json` (pristine source) | 42 | 42 | 2 |
| `repro/encoder-crossover-190-SANITISED/MANIFEST.json` (shipped) | 42 | 39 | **8** |
| `scratch/uregen1/tree/MANIFEST.json` (regenerated) | 42 | 25 | **0** |

- UREGEN1's "25 flag-True rows, 0 contradictions" on the regenerated tree: **confirmed exactly**.
- UREGEN1 named 6 contradictions; I find those 6 **plus 2 pre-existing source-level ones**
  (`fixture/DECISION_CASE_SCHEMA.ts`, `preregistration/EXP12-typed-channel-comparison-prereg.md`) that
  are already contradictory in the pristine source MANIFEST, so UREGEN1's 6 is the correct count of
  *redaction-introduced* defects (mild undercount of total contradictory rows: 8).
- **UFIX12's `strategy/PUBLISH_PACKAGE_MANIFEST.md` §12.5 is contradicted.** Its "6 stale rows, 4 fixed
  by stage D, 2 still open (`README.md`, `INTEGRITY.md`)" is wrong on the outcome: regeneration clears
  **all six** (regenerated MANIFEST has 0 contradictions). UREDACT3's stage-D "defect" claim should be
  withdrawn, as UREGEN1 recommends.

## Q3 — UREDACT3's 98 vs UREGEN1's 360/494: scope mismatch, and partly not reproduced

The nine process/audit files are, verbatim from `strategy/REGEN_ASSESSMENT.md:140-142`:
`REDACT3_REPORT.md  REDACTION_REPORT.md  redact.py  README.md  RESIDUALS.md  INTEGRITY.md
SCRUB_REPORT.md  verify/VERIFICATION.txt  verify/redaction-log.json`.

Independent whole-tree scan (24 HARD patterns, `--exclude-dir=.git`):

| tree | UREGEN1 | UVER12 |
|---|---|---|
| live `repro/encoder-crossover-190-SANITISED/` | 494 | **494 ✓** |
| regenerated `scratch/uregen1/tree/` | 360 | **382 ✗** |
| regenerated minus 9 process files | 98 | **83 ✗** |
| live minus same 9 | 237 | **207 ✗** |

The discrepancy is a **scope mismatch**, not a clean contradiction (`redact.py` was never run against
this workspace's live tree; `394`/`98`/`360` come from different file sets), but UREGEN1's *own*
whole-tree numbers do **not** reproduce under a uniform scan whose method reproduces its live-tree 494
exactly. Recorded as `not_reproduced`, not falsified. Pattern file
`scratch/uregen1/patterns/hard.txt` is byte-identical to the build script's 24 HARD patterns.

## Q4 — Digest re-declaration

- `57a29b4e…`: my workspace grep (excluding my own `scratch/uver12` and `.git`) finds **91** files,
  not 89 — a 2-file drift, immaterial to the conclusion.
- **"0 ship" confirmed**: `grep -rl` for the old digest inside the built package
  `scratch/uregen1/pkg/research-publish-packages` returns **0**, and no file listed in
  `scratch/uregen1/ship_staged.txt` records it.
- `repro/encoder-crossover-190-SANITISED/INTEGRITY.md:93` confirmed: it prints
  `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` in **both** the as-audited and
  sanitised columns, i.e. asserts the projection digest unchanged. After regeneration the projection
  digest is `b85e4585d8c7f0beec02620356b8fcb2b53bb27b0c9e5544bf51e8368bec7a26`, so that row is now
  **false** and must be re-declared. (Same stale 'unchanged' text also at
  `SCRUB_REPORT.md:237-238`, `verify/VERIFICATION.txt:25,30`, `README.md:62`, `REDACT3_REPORT.md:192-193`,
  `REDACTION_REPORT.md:151`, `variants/no-union/README.md:32`.)

## Q5 — `routeA.ties`

**Confirmed 120 in BOTH files**: `repro/encoder-crossover-190-SANITISED/second-labeller/metrics.json`
and `scratch/uregen1/tree/second-labeller/metrics.json`. Also 120 in
`scratch/uregen1/livecheck/second-labeller/metrics.json` and `scratch/uregen1/encoder-crossover-190/…`.
So the label vocabulary was never substituted, and UTOK2's 120→119 does not describe the shipped state —
it describes the *counterfactual* that my Q1 instrument experiment re-confirmed (120→119).

## Reproduced / not

- **Reproduced:** 62/63 counting and the one double-match line; the 15-file distribution; §2's named
  file:line residue; 0 HARD hits in `ROBUSTNESS.md`; all six digests; recompute-claims exit 0 with all
  numbers preserved; `CASE_FIELDS=("question",)`; regenerated MANIFEST 0 contradictions; old-digest
  "0 ship"; `ties` 120 both.
- **Contradicted:** the brief's "60 of 62 in 3 files" (it is 3+1+0 across those three files, and the
  claim is absent from the report — it was the orchestrator's error); UFIX12 §12.5's "2 open".
- **Overstated:** UREGEN1's "62 is a floor" — reachable floor is 22 (display-only) with zero number
  movement; ~7 if prose pointers are reworded; 0 only by accepting `routeA.ties` 120→119.
- **Not reproduced:** whole-tree `360`, `98`, `237` (I get `382`, `83`, `207`); old-digest file count
  89 (I get 91).
- **Unverified:** UREGEN1's returned status-message wording (not on disk); the 4 `README.md`/`INTEGRITY.md`
  rows UFIX12 called "fixed by stage D" were not individually traced (regeneration's net effect, however,
  is confirmed).

## Containment

Wrote only to `strategy/VERIFICATION_REPORT_12.md`, `orchestration/units/UVER12.md`,
`orchestration/handoffs/UVER12.json`, `scratch/uver12/**`. No writes to `/home/zer0null/Duval`,
`/home/zer0null/research-publish-packages`, `strategy/REGEN_ASSESSMENT.md`, `redact.py`, or `repro/`.
