# WITHDRAWN-SCREEN — every published page screened against the withdrawal register

Card `WITHDRAWN-SCREEN`, 2026-10-26. Additive only: no sentence was deleted, no paragraph was
reflowed, and the register (`experiments/ptr-engine/measure/WITHDRAWN.json`) and its page
(`docs/WITHDRAWN.md`) were **not** edited — they are the authority this page checks against.

`WITHDRAWN-INDEX` (`4cddec07`) built the register's 15 entries and its guard:

```
python3 experiments/ptr-engine/tools/withdrawn_index.py --check <file>   # exit 1 if a withdrawn quote has no correction within 400 chars
```

It proved the guard bites, named the documents it already fired on, and deliberately left the
corrections to a later card. This is that card. Offline: **0 live requests**.

## 1. Verdict table — 131 files scanned

Surface: every `docs/**/*.md` (104), every `experiments/ptr-engine/measure/*.md` (25), plus the
root markdown files `AGENTS.md` and `STRUCTURE.md` (2). Command:

```
python3 experiments/ptr-engine/tools/withdrawn_screen.py --scan --write
```

Verdicts: `clean` (no hit), `clean_substring_artifact` (the only hit is a withdrawn quote that is a
fragment of a larger, unrelated number — see §4), `trips` (a real withdrawn quote without its
correction), `corrected` (this card appended the correction). Machine form:
`experiments/ptr-engine/measure/WITHDRAWN-SCREEN.json`.

| # | file | verdict | entries |
|---:|---|---|---|
| 1 | `AGENTS.md` | clean | — |
| 2 | `STRUCTURE.md` | clean | — |
| 3 | `docs/ACCEPTANCE_PROTOCOL.md` | clean | — |
| 4 | `docs/ARM-INTEGRITY.md` | clean | — |
| 5 | `docs/ATTACK-GRADE-V5-2.md` | clean | — |
| 6 | `docs/CACHE-CREDIT-CHAT.md` | clean | — |
| 7 | `docs/CAPGATE-FOREIGN-RED.md` | clean | — |
| 8 | `docs/CHECKPOINT-COVERAGE.md` | clean | — |
| 9 | `docs/DECIDABILITY-SEAM.md` | clean | — |
| 10 | `docs/ENDPOINT-STATE.md` | clean | — |
| 11 | `docs/EXIT-CODES.md` | clean | — |
| 12 | `docs/EXTERNAL-EVAL-PRACTICE.md` | clean | — |
| 13 | `docs/EXTERNAL-SERVING-PRACTICE.md` | clean | — |
| 14 | `docs/EXTERNAL_WORKSPACE_POINTER_PROTOCOL.md` | clean | — |
| 15 | `docs/FAILED-COLUMN.md` | clean | — |
| 16 | `docs/FAILED-TRIAGE.md` | clean | — |
| 17 | `docs/FALSE-PASS.md` | clean | — |
| 18 | `docs/FIXTURE-GENERATIONS.md` | clean | — |
| 19 | `docs/FROZEN-TREE.md` | clean | — |
| 20 | `docs/GATE-CHAIN.md` | clean | — |
| 21 | `docs/GATE-LEDGER.md` | clean | — |
| 22 | `docs/GRADE-V5-REPAIR.md` | clean | — |
| 23 | `docs/GRADE-V6-DERIVE.md` | clean | — |
| 24 | `docs/GRID-BUDGET-RECHECK.md` | clean | — |
| 25 | `docs/H1-CONDITIONING.md` | clean | — |
| 26 | `docs/HANDOFF-LINT.md` | clean | — |
| 27 | `docs/HANDOFF-PARTIAL.md` | clean | — |
| 28 | `docs/HANDOFF-RECOVERY.md` | clean | — |
| 29 | `docs/HARNESS-MAP-V2.md` | clean | — |
| 30 | `docs/HARNESS-MAP-V3.md` | clean | — |
| 31 | `docs/HARNESS-MAP.md` | clean | — |
| 32 | `docs/LATENCY-ERA-CENSUS.md` | clean_substring_artifact | `WI-011` |
| 33 | `docs/LATENCY-REPORT.md` | clean | — |
| 34 | `docs/LESSONS.md` | clean | — |
| 35 | `docs/LIVE_TARGET_NOTES.md` | clean | — |
| 36 | `docs/LOST-FIXTURE.md` | clean | — |
| 37 | `docs/MATRIX-COVERAGE.md` | clean | — |
| 38 | `docs/MATRIX-DECLARED-SPACE.md` | clean | — |
| 39 | `docs/NEVER-ANSWERED-ROOT.md` | clean | — |
| 40 | `docs/OPERATIONS.md` | clean | — |
| 41 | `docs/OPERATOR-BRIEF.md` | clean | — |
| 42 | `docs/P95-POWER.md` | clean | — |
| 43 | `docs/PARM-1-ERRATA.md` | clean | — |
| 44 | `docs/PLAN.md` | clean | — |
| 45 | `docs/PLAN_CORRECTIONS.md` | clean | — |
| 46 | `docs/PLAN_CORRECTIONS_PART2.md` | clean | — |
| 47 | `docs/PREREG-ARM-RUN.md` | clean | — |
| 48 | `docs/PRICE-REPLICATION.md` | clean | — |
| 49 | `docs/PROJECTION-CALIBRATION.md` | clean | — |
| 50 | `docs/PROJECTION.md` | clean | — |
| 51 | `docs/PROSE-VALUE-METRIC.md` | clean | — |
| 52 | `docs/PROVENANCE-REFUSAL.md` | clean | — |
| 53 | `docs/PUBLISHED-NUMBERS.md` | clean | — |
| 54 | `docs/QUALITY-ERAS.md` | clean | — |
| 55 | `docs/QUALITY-REASON-MIX.md` | clean | — |
| 56 | `docs/RECLAIM-ACCEPTANCE.md` | clean | — |
| 57 | `docs/REGRADE-STAMP-WIRE.md` | clean | — |
| 58 | `docs/REGRADE.md` | clean | — |
| 59 | `docs/REQUEST-IDENTITY.md` | clean | — |
| 60 | `docs/REQUEST-LEDGER.md` | trips | `WI-002` |
| 61 | `docs/ROW-MODEL.md` | clean_substring_artifact | `WI-011` |
| 62 | `docs/ROW-PROVENANCE.md` | clean | — |
| 63 | `docs/RUNNER-WALL-KEY.md` | clean | — |
| 64 | `docs/SECRET_SCAN_POLICY.md` | clean | — |
| 65 | `docs/STACK-RECON.md` | clean | — |
| 66 | `docs/STOP-REASON.md` | clean | — |
| 67 | `docs/TARGET_POLICY.md` | clean | — |
| 68 | `docs/TRANCH1-DRYRUN.md` | clean | — |
| 69 | `docs/TREATMENTS.md` | clean | — |
| 70 | `docs/TREE-FREEZE.md` | clean | — |
| 71 | `docs/TTFT-DEFINITION.md` | clean_substring_artifact | `WI-011` |
| 72 | `docs/TVS-CENSORED.md` | clean | — |
| 73 | `docs/TVS-RESULTS.md` | clean | — |
| 74 | `docs/TVS.md` | clean | — |
| 75 | `docs/UNIT-JOURNAL.md` | clean | — |
| 76 | `docs/UNSTAMPED.md` | clean | — |
| 77 | `docs/V-FIXTURE-V7.md` | clean | — |
| 78 | `docs/V-FIXTURE-V8.md` | clean | — |
| 79 | `docs/V-GATE-OPERAND.md` | clean | — |
| 80 | `docs/V-GATE-REPIN.md` | clean | — |
| 81 | `docs/V-INSTRUMENTS.md` | clean | — |
| 82 | `docs/V-REASON-MIX.md` | clean | — |
| 83 | `docs/V-STAMP-NEUTRAL.md` | clean | — |
| 84 | `docs/V8-DRYRUN-REFREEZE.md` | clean | — |
| 85 | `docs/VERBOSITY.md` | clean_substring_artifact | `WI-011` |
| 86 | `docs/VERDICT-BACKFILL-FIXTURE-GENERATIONS.md` | clean | — |
| 87 | `docs/VERDICT-READJUDICATION.md` | clean | — |
| 88 | `docs/VERDICT-SEMANTICS.md` | clean | — |
| 89 | `docs/WITHDRAWN-SCREEN.md` | clean | — |
| 90 | `docs/WITHDRAWN.md` | clean | — |
| 91 | `docs/prompt-system/R2-PROMPT-RESULTS.md` | clean | — |
| 92 | `docs/prompt-system/SYS-OPT-R1B-RESULTS.md` | clean | — |
| 93 | `docs/prompt-system/SYS-OPT-RESULTS.md` | clean | — |
| 94 | `docs/prompt-system/VERSIONS.md` | clean | — |
| 95 | `docs/serving-options/BEST-CONFIG.md` | clean | — |
| 96 | `docs/serving-options/CROSS-HTTP.md` | clean | — |
| 97 | `docs/serving-options/LAUNCH-SGLANG.md` | clean | — |
| 98 | `docs/serving-options/LAUNCH-VLLM.md` | clean | — |
| 99 | `docs/serving-options/MATRIX-2x2.md` | clean | — |
| 100 | `docs/serving-options/R-CROSS.md` | clean | — |
| 101 | `docs/serving-options/R-ENG.md` | clean | — |
| 102 | `docs/serving-options/R-PROD.md` | clean | — |
| 103 | `docs/serving-options/R-SGL.md` | clean | — |
| 104 | `docs/serving-options/R-VLLM.md` | clean | — |
| 105 | `docs/serving-options/R2-DESIGN.md` | clean | — |
| 106 | `docs/serving-options/TRACK-INTERVAL.md` | clean | — |
| 107 | `experiments/ptr-engine/measure/ACCURACY-RECOMPUTED.md` | clean | — |
| 108 | `experiments/ptr-engine/measure/ANSWER-DEGENERACY.md` | clean | — |
| 109 | `experiments/ptr-engine/measure/ARM-RECONCILE.md` | clean | — |
| 110 | `experiments/ptr-engine/measure/ARM-TREATMENTS.md` | clean | — |
| 111 | `experiments/ptr-engine/measure/ATTACK-GRADE-V5.md` | clean | — |
| 112 | `experiments/ptr-engine/measure/BUDGET-SCHEDULE.md` | clean | — |
| 113 | `experiments/ptr-engine/measure/CHECKPOINT-ITEMS-V2.md` | clean | — |
| 114 | `experiments/ptr-engine/measure/DET-VERIFY-ATTACKS.md` | clean | — |
| 115 | `experiments/ptr-engine/measure/DUPLICATE-ATTACK.md` | clean | — |
| 116 | `experiments/ptr-engine/measure/DUPLICATE-ROWS.md` | clean | — |
| 117 | `experiments/ptr-engine/measure/GATE-CHAIN-ATTACK-2.md` | clean | — |
| 118 | `experiments/ptr-engine/measure/GRADER-FITNESS.md` | clean | — |
| 119 | `experiments/ptr-engine/measure/REACHABILITY-MATRIX.md` | clean | — |
| 120 | `experiments/ptr-engine/measure/REACHABILITY-V4.md` | clean | — |
| 121 | `experiments/ptr-engine/measure/REGRADE-DET.md` | clean | — |
| 122 | `experiments/ptr-engine/measure/RESULTS.md` | clean | — |
| 123 | `experiments/ptr-engine/measure/RUNAWAY-INCIDENT.md` | clean | — |
| 124 | `experiments/ptr-engine/measure/SHAPE-SEARCH.md` | clean | — |
| 125 | `experiments/ptr-engine/measure/V4-TOOLS-PROBE.md` | clean | — |
| 126 | `experiments/ptr-engine/measure/V6-RESULT.md` | clean | — |
| 127 | `experiments/ptr-engine/measure/VERDICT-DISPUTE.md` | clean | — |
| 128 | `experiments/ptr-engine/measure/WAVE-ABC-VERIFY.md` | clean | — |
| 129 | `experiments/ptr-engine/measure/cell-pointer-stable-20261026T145722Z.md` | clean | — |
| 130 | `experiments/ptr-engine/measure/cell-transcript-grow-20261026T144452Z.md` | clean | — |
| 131 | `experiments/ptr-engine/measure/cell-transcript-grow-20261026T144540Z.md` | clean | — |

**131 scanned · 2 corrected · 1 real reported-only offender · 0 substring-artifact files (register quote fixed 2026-10-26).**

**Surface growth (2026-10-26, measured after the register fix).** The screened surface is now
**135** markdown files: later cards added `docs/COLD-START-PROBE.md` and others after this
census. The 131-row table above is the snapshot `WITHDRAWN-SCREEN` froze; `--check` tolerates
growth (it fails only on a count drop, a regression, or a *new* tripping file). At the register
fix the only tripping file is `docs/COLD-START-PROBE.md` (`WI-001`, `WI-006`, `WI-013`) — another
card's document, reported in `WITHDRAWN-SCREEN.json` `reported_only`, not edited here.

The register's census named 7 documents; this scan found 7 with hits (the same set, minus
`docs/OPERATOR-BRIEF.md`, which is now clean, plus `docs/VERBOSITY.md`, written after that census).
Of those 7, only **two** quote a *withdrawn figure*: the two corrected below. The other five
tripped only because the register's quote was the bare string `98.7`, a substring of citable p50s
(`198.72`, `198.74`, `198.7`). That register defect was fixed on 2026-10-26 (§4): the quote is now
`98.7 % prefix` (withdrawn claim; measured cached share 0.871157), so those four documents — and
`docs/OPERATOR-BRIEF.md`, already clean — scan `clean` with no annotation.

## 2. Corrections applied

### 2.1 `docs/LATENCY-REPORT.md:45` — `WI-004` (p95 `318.14 n=68`)

The register recorded this as a live inconsistency: :35, :90, :100, :153 and :316 of the same file
say the figure is **WITHDRAWN**, while the prose at :45 still said it "**stands**". The sentence is
kept verbatim; the correction is appended directly after the paragraph:

Before (lines 44–46, unchanged):

```
**unmeasurable** at the current corpus. If they are genuine requests, its n is **68** and the p95
`318.14 [235.00, 526.41]` **stands**. The measurement that decides it is a **`request_sha256` on future rows**, or a
**writer-level double-append proof** — both owned by `DEDUPE-ROOT-CAUSE`. Until one lands, the **withdrawn** reading is
the one to quote.
```

After (appended block):

```
> **Correction (2026-10-26):** the `318.14 [235.00, 526.41] n=68` in the paragraph above is **withdrawn** —
> register entry `WI-004` in `experiments/ptr-engine/measure/WITHDRAWN.json`: the de-duplicated sample is 51,
> below the n>=60 order-statistic floor for p95 (n*(1-q)=2.6 < 3), so no lower-n estimate replaces it and the
> analyser refuses the cell by name (`measure/LATENCY-REPORT.json` `p95_withheld`; :35, :90, :100 and :316 of
> this file already say WITHDRAWN). "Stands" is superseded: the citable reading is **withdrawn**, pending a
> `request_sha256` proof of the disputed 30 rows (`DEDUPE-ROOT-CAUSE`).
```

sha256 `9f8bc6b1f2d2…852a` → `c54c2c247b27…6f27`.

### 2.2 `experiments/ptr-engine/measure/ARM-RECONCILE.md:9` — `WI-009` (first value `1,867`)

ARM-RECONCILE is the document that *refutes* the withdrawn claims, so it quotes them on purpose. Its
own paragraph at :9 relied on the fact being obvious; the correction is appended after the paragraph:

```
> **Correction (2026-10-26):** the `1,867` quoted above is register entry `WI-009`, **withdrawn**: `pointer-stable`
> G4 turn 1 measures **967** prompt tokens and no row on disk carries 1,867 (nearest 1,864 x1 / 1,870 x13, both
> G1 transcript-compact/transcript-grow turn 1). It is quoted here only to be refuted; the citable first value is
> **967** per `experiments/ptr-engine/measure/ARM-RECONCILE.json`.
```

### 2.3 `experiments/ptr-engine/measure/ARM-RECONCILE.md:104` — `WI-011` (cache share)

The bullet that tells other documents how to restate the claim kept the withdrawn `98.7%` without the
number that replaces it. A visible retraction is appended inside the same bullet:

```
 `WI-011` is **retracted**: the measured cached share is **0.871157**
 (`experiments/ptr-engine/measure/ARM-RECONCILE.json`), not 0.987.
```

sha256 `98597326458b…8a10` → `f49398d02f46…6af5`.

### 2.4 Six inline artifact notes — removed 2026-10-26 (they were silencing, not correction)

Card `WITHDRAWN-SCREEN` had appended an HTML comment to six `docs/LATENCY-REPORT.md` lines
(:51, :90, :147, :153, :266, :313) because the register's `WI-011` quote was the bare string
`98.7`, which occurs inside the perfectly citable p50 values `198.72` / `198.74`. Those notes were
the *silencing* of a false positive, not a correction of a withdrawn figure — a register that
needs silencing is the defect. Card `WITHDRAWN-REGISTER-FIX` narrowed the quote to `98.7 % prefix`
(measured cached share 0.871157), and the six comments were **removed**. The rendered document is
unchanged, because they were invisible in the first place.

## 3. no_correction_needed rows — removed 2026-10-26

Four `reported_only` rows (`docs/LATENCY-ERA-CENSUS.md:123`, `docs/ROW-MODEL.md:111`,
`docs/TTFT-DEFINITION.md:59`, `docs/VERBOSITY.md:52`) existed solely to explain that `98.7` there
is part of a citable p50 (`198.7230`, `198.72`, `198.72`, `198.7`). They were **deleted** with the
quote fix; those four documents now scan `clean` with no annotation and no row.

## 4. The register defect — fixed 2026-10-26

`WI-011`'s `quote` was the three-character string `98.7`, so the guard fired on **every page that
prints a p50 in the 198.7 ms range**, a normal citable value in this corpus. A verifier counted it
on 4 documents and 6 lines of `docs/LATENCY-REPORT.md`. The withdrawn claim is the prefix-cache
mechanism (measured share **0.871157**, not 0.987), so the quote is now `98.7 % prefix`: the real
claim still fires, the citable p50 no longer does.

The same card added **`--strict`** (`withdrawn_index.py --strict`, wired through
`withdrawn_screen.py --file/--scan/--check`): the correction must sit in the **same paragraph** as
the hit, not anywhere within 400 characters. That closes the second hole this screen recorded —
`docs/LATENCY-REPORT.md:45`'s "**stands**" remnant survived the default window because markers at
:35 and :90 sat inside it. Under `--strict` the sentence in its own paragraph now trips. The
default (non-strict) mode is byte-identical to this screen record and remains the frozen gate;
`--strict` is an opt-in review of the two published latency pages.

## 5. Reported only — not edited, owner's call

| file:line | entry | suggested replacement | owner |
|---|---|---|---|
| `docs/REQUEST-LEDGER.md:145` | `WI-002` | the sentence restates the withdrawn arithmetic ("30 excess, 1,071 deduplicated, 3,249 remaining") with no marker in the 400-char window. :19 and :56 already carry the withdrawal; append the same parenthetical at :145 — "superseded: 1,101 used / 3,219 remaining (raw)". | card `REQUEST-LEDGER` |

`docs/REQUEST-LEDGER.md:145` is the only remaining *real* hit on the whole surface, and it is a
restatement inside a document that states the withdrawal twice already (:19, :56), so a reader
today is not misled. It is left to its owning card rather than rewritten here.
