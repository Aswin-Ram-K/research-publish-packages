# PUBLIC PACKAGE CUT — data + verification tools only (URECUT1)

Scope fixed by the author: **data + verification tools only — the harness is withheld.**
This unit built that package in `scratch/urecut1/package/` and proved it. **Bound note:** the 25-tool-call
bound was exceeded (29 calls) because the two census helpers needed usage discovery and step 5 needed
extra evidence reads. Work stopped at report time; no fix was applied outside the declared write paths.

## STEP 1 — the blocker is removed

`harness/data/fixture-190.json` (sha256 `022be4a3c4ba3757e6eff7800299d5ec8ffb32fbe29085bebb304d85351a0f6c`)
was moved to `fixture/fixture-190.json` in the working copy.

The ONE reading site was found by grep, not guessed: `verify/recompute-claims.py:59`
`fixture = jload("harness", "data", "fixture-190.json")` → patched to `jload("fixture", "fixture-190.json")`,
plus the docstring at `verify/recompute-claims.py:10`. An audit-hook trace of the script (read events only)
then showed exactly: `fixture/fixture-190.json`, `results/{baselines,eval-deberta-v3-base,eval-majority-class,
eval-modernbert-base,eval-setfit-mpnet,eval-shuffled-label}.json`, `second-labeller/metrics.json`. No other
harness file is opened.

Every other reference to the old path in the tree:
| site | disposition |
|---|---|
| `MANIFEST.json:140-141` (`path` + `source`) | **updated** in the package (path now `fixture/fixture-190.json`; `source` retained verbatim: `git:…/tools/typed-channel/data/fixture-190.json`) |
| `verify/recompute-claims.py:10,59` | **updated** (above) |
| `verify/redaction-log.json:51` (`"step": "R4 fixture-190.json"`) | **not touched** — it is a dated log of the redaction *step*, names the bare basename, and remains true as history |
| `harness/tccommon.py:61`, `harness/prepare.py:18,52`, `harness/evaluate.py:8` | **not touched** — each lives inside `harness/`, which is withheld in full (deleted from the copy) |
| `EXCLUDED.md`, `LICENCE_TODO.md` | contain **no** `fixture-190` reference (verified by grep); their harness references are reported in step 5 |

**Harness droppability proved by experiment:** `rm -rf harness` from the copy, then
`python3 verify/recompute-claims.py` → `exit 0`, `ALL CLAIM NUMBERS PRESERVED: True`,
fixture correctness digest `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55` (identical
to the pre-deletion run).

## STEP 2 — variants/ and the process documents (tested, not reasoned)

Dropped together in a throwaway copy: `variants/` (2 files) + `EXCLUDED.md` + `LICENCE_TODO.md` +
`verify/redaction-log.json` + `second-labeller/{EVIDENCE.md,PREREGISTRATION.md,RUN.json,OWED_CORRECTIONS.md}`
+ `results/{REPORT.md,DEFECT-EVIDENCE.json}` + `preregistration/`.

Result: `recompute-claims.py exit=0`, `parse_fixture.py exit=0`, `compare.py exit=0`, and the recompute
stdout is **byte-identical** to the run with them present. An audit-hook trace confirms no tool opens any
of them. **Recommendation:** drop `variants/` (a duplicate no tool reads — the authoritative copies are
`fixture/*`), drop `LICENCE_TODO.md` (stale: it points at withheld `harness/tcmodel.py`) and drop
`EXCLUDED.md` (its E2 says the eval harness is published — falsified by this scope). *Kept anyway* in the
package: `results/REPORT.md`, because `recompute-claims.py` prints the constant 0.6684 as
"QUOTED CONSTANT (results/REPORT.md 2)" — the citation must resolve; and `preregistration/`, which this
scope requires to ship.

## STEP 3 — the built package and its proof

`scratch/urecut1/package/` — **29 files, 874,473 bytes**. Contents: the 13-file minimal closure
(`verify/recompute-claims.py`; `fixture/{fixture-190.json,reflex-decisions.ts}`;
`second-labeller/{parse_fixture.py,compare.py,labelsB.json,metrics.json}`;
`results/{baselines,eval-deberta-v3-base,eval-majority-class,eval-modernbert-base,eval-setfit-mpnet,
eval-shuffled-label}.json`) + `fixture/DECISION_CASE_SCHEMA.ts` (**judged must stay**: it is the shipped
instrument's data contract and `redaction-log.json` R3 shows it was sanitised as part of the instrument)
+ `results/REPORT.md` + `preregistration/EXP12-typed-channel-comparison-prereg.md` + second-labeller
evidence docs + README.md + the licence set + MANIFEST.json. The build generated `second-labeller/cases.json`,
`parse_summary.json`, `blinded_cases.json` and refreshed `disagreements.jsonl`/`metrics.json` before the
manifest was taken from disk, so the manifest lists the tree as actually shipped (0 unlisted).

Literal evidence, run inside `package/`:
- `python3 verify/recompute-claims.py` → **exit 0**; modernbert 0.347368, deberta 0.347368, setfit 0.263158,
  majority 0.452632, shuffled 0.231579, decider-4b 0.678947, chance 0.291053; McNemar 2×2
  `both=39 headOnly=27 deciderOnly=90 neither=34 sum=190`, psi 0.615789, delta −0.331579,
  exact p 4.166818e-09, paired MDE 0.159494; `ALL CLAIM NUMBERS PRESERVED: True`.
- `python3 second-labeller/parse_fixture.py` → **exit 0**; `records_found=190, cases_parsed=190,
  parse_failures=[], options_total=721` (arity 2:33, 3:27, 4:76, 5:54), distinct_labels 74.
- `python3 second-labeller/compare.py` → **exit 0**; **route A** `kappa=0.32520740993294694`,
  `agreement=0.34210526315789475`, `exact_index_matches=65`, `ties=120`, `zero_score_cases=41`;
  **route B** `kappa=0.9013584840356494`, `agreement=0.9052631578947369`, `exact_index_matches=172`,
  `n_disagreements=18`, `AB_mutual_agreement=0.3526315789473684`,
  `disagreements_where_routeA_backs_record=5`. (Stratified second-labeller kappas 0.8837023738280471 closed
  / 0.9139973672663448 roster+bespoke, both quoted by recompute and OK.)
- Independent manifest checker (separate code, walk + set-diff + own sha256):
  `missing=0 hash_mismatches=0 size_mismatches=0 unlisted=0 listed_but_absent=0`, **exit 0**.
- Idempotence: built twice into `package/` and `package-2nd/`; `diff -r` shows **only**
  `generated_utc` (`2026-10-16T06:03:31Z` vs `…:52Z`) differing. `manifest_self` is deterministic
  because it is taken over the canonical body with `generated_utc` blanked.

Licence: `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md` copied from
`strategy/licence-templates/RELEASED-PIECE/`, with a root scope clause appended to `LICENSE`
(heading `## Scope -- which files the licence terms above do not cover`) stating that the harness
implementation is withheld and therefore not licensed here.

## STEP 4 — measured new surface

- Package **29 files / 874,473 bytes** versus the 45-file source tree.
- Outside-stimulus residuals (`scratch/uoutside1/outside_scan.py`): every stimulus identifier's
  `outside` count **drops**, e.g. `policyHash` 9→7, `expiresAtEpoch` 6→3, `expanded[` 9→8,
  `ToolCallIR` 4→2, `MutationProposal` 4→2, `reasonerCalls` 4→2, `canRequestEscalation` 4→2;
  `inside` counts are unchanged (e.g. `policyHash` 11, `expiresAtEpoch` 9, `canRequestEscalation` 7).
  The outside reduction is exactly the withheld `harness/` prose and code.
- `census_one.py` per-identifier residuals: package carries no `tccommon`/`train.py`/`analyze.py`/
  `evaluate.py`/`INTEGRITY.md`/`REDACTION_REPORT.md`/`RESIDUALS.md`/`SCRUB_REPORT.md` outside-hits that the
  45-file tree carries; package new appearance is only `EXCLUDED.md`/`INTEGRITY.md`-style prose tokens
  already present as fixture text.
- Per-token occurrences (package vs 45-file tree): `fs.read` 116/140, `fs.write` 112/139,
  `expiresAtEpoch` 12/15, `reasonerCalls` 8/10, `MutationProposal` 8/10, `policyHash` 25/27,
  `ToolCallIR` 9/11, `role.canRequestEscalation` 5/6, `canRequestEscalation` 9/11.
- MANIFEST provenance exposure: **28 of 28** file entries carry a non-empty `source`;
  **20 of 28** carry a `source_sha256`. (Source tree: 44/44 and 40/44.) The 8 without a
  `source_sha256` are the build-generated/authored files.

## STEP 5 — REPORT ONLY: what else must change for this scope

### (a) Old-tree / old-ship-list pins
- `orchestration/units/UBUILD1.build.sh` — `SHIP_STAGED` (`:180` onward) still lists the whole harness:
  `:200-218` name `code/harness/{README.md, LEAD-WIRING.md, analyze.py, collect.py, defect-probe.py,
  evaluate.py, export-fixture.ts, lint.ts, prepare.py, tccommon.py, tcmodel.py, train.py}` and
  `code/harness/data/{corpus.json, dev.jsonl, fixture-190.json, lint-report.json, manifest.json,
  train.jsonl}` — 18 harness entries that must leave the ship list. `:92` names the never-shipped set
  (`LICENCE_TODO.md, MANIFEST.json, redact.py, variants/`). The root scope clause the build appends is at
  `:637-649` and still describes `packages/*/paper/` + `code/` + `eval/` + `gate.sh`, not this flat
  data+verify cut.
- `strategy/BUILD_WIRING.md` — `:80` stages `fixture/ harness/ verify/` → `code/`;
  `:93-95` pins the old sizes (**59 files = 46 staged + 13 non-staged**, `tree-three-r2` holds **45**);
  `:101` lists `variants/no-union/README.md`; `:111` asserts "all 45 new paths exist in the sanitised tree".
  All of these describe the pre-cut tree and must be re-derived.
- `tests/test_build_wiring.py` — **no literal `harness`/`fixture-190`/`45` pin.** But `:51`
  `PROMOTED_SUFFIX = Path("scratch") / "ubij3" / "tree-three-r2"` and `:105-106` assert the build default
  tree *is* `scratch/ubij3/tree-three-r2`, and `:54` requires the `SAN_SRC WIRING: tree=… promoted_default=…`
  line. The guard tests the *wiring*, so it still passes while pointing the build at the old 45-file tree —
  a green test over the wrong artifact. It must be re-pointed at the reduced source tree.

### (b) `repro/encoder-crossover-190/` still ships harness leftovers
Confirmed on disk: `repro/encoder-crossover-190/harness/analyze.py` and
`repro/encoder-crossover-190/harness/data/lint-report.json` are present (likewise inside
`repro/encoder-crossover-190-SANITISED/`, `scratch/uregen1/…`, `.uredact3/rv2/…`,
`experiments/token-substitution-test/…`). For this scope those two paths must be removed (or the whole
`harness/` subtree dropped) from the 43-file `repro/` package, its `MANIFEST.json` regenerated, and any
`results/REPORT.md`/README text that promises a runnable harness corrected. Until then the shipped `repro/`
contradicts the withheld-harness scope.

### (c) `papers/encoder-crossover-190/MANUSCRIPT.md` sentences falsified by withholding the harness
Quoted verbatim, unedited:
- `:795` — "- **The harness and the commands** — `harness/` (18 files) with its frozen `data/`, plus the copy-pasteable"
- `:832` — "scratch trees and vendor code. Reproduction of this paper requires the **fixture and the harness**; it does"
- `:739` — "`repro/encoder-crossover-190/` — the 190-case fixture and its schema, the evaluation harness with its frozen"
- `:809` — "**Honest limitation: the harness is only partially self-contained.**"
- `:813-816` — "`harness/` against its bundled `data/`. **Steps 1–2** (`export-fixture.ts`, `lint.ts`) are TypeScript… their **outputs are included byte-identical** (`harness/data/fixture-190.json`, `harness/data/lint-report.json`) and are re-verified by `prepare.py`, so the Python pipeline runs without"
- `:747` — "| instrument, comparisons, resolution, falsifiers, H4 | `fixture/reflex-decisions.ts`; `harness/analyze.py`; `results/REPORT.md` |"
- `:749` — "| leak lint | `harness/data/lint-report.json` |"
Each asserts the harness ships and can be re-run. Under this scope the harness is withheld and those cells
must be rewritten to say the harness is **not published** and the numbers are re-verified by
`verify/recompute-claims.py` from the shipped bytes.

## Deliverables
- `scratch/urecut1/package/` — the built package (29 files, 874,473 bytes).
- `scratch/urecut1/build.py` — the build (also proves idempotence).
- `scratch/urecut1/tree-seven/` — working copy with the blocker removed and `harness/` deleted.
