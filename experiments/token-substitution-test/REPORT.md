# UTOK1 — Token-substitution test on `repro/encoder-crossover-190-SANITISED`

**Question this unit exists to answer:** can the kernel vocabulary the sanitised fixture re-discloses
(`StateClass`, `grantPolicy`, `expanded[`, `admit(`, `src/*.ts`) be replaced with neutral tokens
**without moving the published numbers**?

**Answers, up front:**

1. **YES — released scripts DO read `question`.** It is not display text. The single consumption point is
   `harness/tccommon.py:155`, and `second-labeller/compare.py:55` recomputes a CLAIMS value from it.
   So substitution is an *experiment change*, not a cosmetic one — and the numbers therefore had to be
   measured, not assumed.
2. **Every number this subset can recompute held: 10/10** (ten `run-verification.sh` values), plus the
   5 `recompute-claims.py` CLAIMS constants and the fixture-correctness digest — byte-identical output.
3. **The scoring-projection digest necessarily moved** (`57a29b4e…` → `75d4b0a2…`) because that digest
   *hashes `question`*. `train/dev` digests did **not** move.
4. **The exclusion gate is NOT cleared: 434 → 295 hard-fail lines.** Mechanism-token lines drop
   222 → 76, but option labels, frozen `results/*.json`, the verifier's own log, and the instrumentation
   keep the patterns alive.

**Verdict:** the substitution is **viable for every reported number** and **not free** — one digest is a
declared casualty, and the gate fails for reasons the substitution cannot reach. Details below.

---

## 1. The critical sub-question: does any script read `question`? — YES

| file:line | what it reads | consequence |
|---|---|---|
| `harness/tccommon.py:155` | `"situation": case["question"]` in `fixture_case_to_example()` | **the consumption point.** `situation` is what `render()`/`render_context()` put into the model input for the fixture path (`tccommon.py:106,116`), used by `harness/prepare.py` and the scored path in `harness/evaluate.py`, `harness/train.py`, `harness/defect-probe.py` |
| `harness/prepare.py:150` | declares `"fixtureSituation": "question"` (provenance metadata) | confirms the binding is deliberate and named |
| `second-labeller/compare.py:55` | `route_a(c["question"], c["options"])` | **route A's kappa is one of the ten CLAIMS values** — recomputed from question text on every run |
| `second-labeller/parse_fixture.py:94` | `question = field(body, "question", STR)` | carries the text into `cases.json` / `blinded_cases.json` |
| `verify/run-verification.sh:55` | `proj = [{k: c[k] for k in ('id','kind','question','options','correct')} …]` | the scoring-projection **digest hashes the question**, so that digest cannot survive any substitution |
| `verify/run-verification.sh:157-163` | reports residual hits per field class (`question`, `options`, …) | the instrument already distinguishes these fields |

`rationale` and `namespaces` are **not** read for scoring (`tccommon.py:19`), and `correct` is read only as
an index. Option labels **are** read (scoring, and A/B label comparison), which is why they were not touched.

**No released script is indifferent to `question`.** The substitution is an instrument change.

---

## 2. Before state — the ten values and the digests (verbatim, `logs/before.txt`)

Command: `bash work/verify/run-verification.sh "$PWD/scratch-before"` → exit 0.

| # | value (`run-verification.sh` §5) | before |
|---|---|---|
| 1 | `comparison cases` | 190 |
| 2 | `options_total` | 721 |
| 3 | `routeA kappa` (CLAIMS 0.3252) | 0.32520740993294694 |
| 4 | `routeB agreement` | 0.9052631578947369 |
| 5 | `routeB kappa` | 0.9013584840356494 |
| 6 | `n_disagreements` | 18 |
| 7 | `AB mutual agreement` (CLAIMS 0.3526) | 0.3526315789473684 |
| 8 | `closed-subset kappa` (CLAIMS 0.8837) | 0.8837023738280471 |
| 9 | `roster/bespoke kappa` (CLAIMS 0.9140) | 0.9139973672663448 |
| 10 | `disagreements_count_routeB` | 18 |

Digests before:

| digest | before |
|---|---|
| scoring projection (`id,kind,question,options,correct`) | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` |
| `harness/data/train.jsonl` | `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` |
| `harness/data/dev.jsonl` | `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` |
| fixture-correctness digest (`recompute-claims.py`) | `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a` |

`recompute-claims.py` before: all 5 CLAIMS constants `OK`, **ALL CLAIM NUMBERS PRESERVED: True**, exit 0.

---

## 3. Substitution applied

Tree: `experiments/token-substitution-test/work/` (a copy — the source `repro/encoder-crossover-190-SANITISED/` was never written to).
Mapping file: `mapping.json`; engine: `substitute.py`.

| kernel token | neutral token |
|---|---|
| `StateClass` | `TYPE_A` |
| `grantPolicy` | `POLICY_A` |
| `expanded[]` / `expanded[` | `EXPANDED_A` |
| `admit()` / `admit(` | `ADMIT_A` |
| `materialiseGrants` | `MATERIALISE_A` |
| `src/broker.ts` / `src/broker-test.ts` | `MODULE_1` / `MODULE_7` |
| `src/scope.ts`, `src/layer.ts`, `src/loop.ts`, `src/policy.ts`, `src/state.ts` | `MODULE_2` … `MODULE_6` |

**Scope rules (documented, enforced):**
* `.md` / `.txt` / `.ts` → global literal replacement, **except** `fixture/reflex-decisions.ts`, where
  replacement is confined to `question:` value spans (the same span rule the verifier uses).
* `.json` / `.jsonl` → string values reached **only** under keys `question`, `situation`, `instructions`,
  `rationale`, `recorded_rationale`. A file is rewritten only if a value actually changed.
* `.py` / `.sh` → **never touched.** They are instrumentation; their pattern lists and parsers must stay
  byte-faithful or the before/after comparison measures nothing.
* **Never changed:** case `id`, `options` arrays / option labels, `correct` / `recorded_index` / `gold` /
  `predLabel` / any label field, `_line` provenance. Verified: `0` changed lines in the fixture begin
  `options:`/`correct:`/`id:`.

Commands (exact):

```bash
cd experiments/token-substitution-test
cp -r ../../repro/encoder-crossover-190-SANITISED work            # experiment copy
cp -r ../../repro/encoder-crossover-190 .                          # transient as-audited control (deleted after)
PATH="$PWD/bin:$PATH" bash work/verify/run-verification.sh "$PWD/scratch-before" > logs/before.txt 2>&1
python3 substitute.py "$PWD/work"                                  # -> logs/substitution-fixed.txt
PATH="$PWD/bin:$PATH" bash work/verify/run-verification.sh "$PWD/scratch-after"  > logs/after.txt  2>&1
bash gate-scan.sh "$PWD/work"                                      # -> logs/gate-after.txt
python3 work/verify/recompute-claims.py                            # -> logs/recompute-after.txt
```

`bin/git` is a shim that refuses any `git` invocation naming `/home/zer0null/Duval`, because that target is
read-only for this unit (the script's own `git -C … rev-parse HEAD` / `git status --porcelain` lines were
therefore not executed; their output is replaced by a one-line notice in `logs/before.txt:13-16`).

---

## 4. After state — ten values, digests, and the VERDICT per value

| # | value | before | after | verdict |
|---|---|---|---|---|
| 1 | `comparison cases` | 190 | 190 | **unchanged** |
| 2 | `options_total` | 721 | 721 | **unchanged** |
| 3 | `routeA kappa` | 0.32520740993294694 | 0.32520740993294694 | **unchanged** |
| 4 | `routeB agreement` | 0.9052631578947369 | 0.9052631578947369 | **unchanged** |
| 5 | `routeB kappa` | 0.9013584840356494 | 0.9013584840356494 | **unchanged** |
| 6 | `n_disagreements` | 18 | 18 | **unchanged** |
| 7 | `AB mutual agreement` | 0.3526315789473684 | 0.3526315789473684 | **unchanged** |
| 8 | `closed-subset kappa` | 0.8837023738280471 | 0.8837023738280471 | **unchanged** |
| 9 | `roster/bespoke kappa` | 0.9139973672663448 | 0.9139973672663448 | **unchanged** |
| 10 | `disagreements_count_routeB` | 18 | 18 | **unchanged** |

**10/10 unchanged.** The one value that *is* recomputed from question text at verify time — route A kappa —
did not move: the substituted tokens (`TYPE_A`, `POLICY_A`, `EXPANDED_A`, `ADMIT_A`, `MODULE_n`) never occur
in any option label, and route A scores by **distinct-token overlap between question and option**, so its
per-case argmax is untouched. (Measured fact; the mechanism is the explanation, not an assumption.)

| digest | before | after | verdict |
|---|---|---|---|
| scoring projection | `57a29b4e…ecbf300` | `75d4b0a22c50eb7fe80ccdee5ffaecdb647f4373a90fae34e3dd0468cbb91a69` | **MOVED** (by construction: it hashes `question`) |
| `harness/data/train.jsonl` | `24c39afa…020c09` | `24c39afa…020c09` | **identical** |
| `harness/data/dev.jsonl` | `d311a99f…4eaa976` | `d311a99f…4eaa976` | **identical** |

`recompute-claims.py` after: **`diff` against the before output is empty — byte-identical**, including
`0.3474`, `0.4526`, `0.2911`, `0.6684`, `0.6789`, all four second-labeller numbers, the McNemar 2×2
`39+27+90+34`, and the fixture-correctness digest `8dd05ce6…`. Exit 0 both times.

### Verdict

* **Substitution is viable for the numbers.** Every recomputable claim value is preserved, and the
  verification scripts were run unmodified against a substituted tree.
* **It is not free.** `verify/run-verification.sh`'s scoring-projection digest **is** the hash of
  `(id,kind,question,options,correct)`; any question edit *must* change it. A released package therefore
  cannot carry `57a29b4e…`; it must carry `75d4b0a2…` and declare the substitution. Whether a *documented
  substitution* is acceptable where a byte-faithful copy of what the model saw is not, is a **publication
  judgement for the author, not a number** — but it is the real residual cost, and it is one the ten-value
  table does not show.
* **The numbers that remain unproven are the model arms** (§7): `0.3474` / `deberta` accuracies come from
  transformer heads that read the rendered question, and this subset cannot re-run them (EXCLUDED.md E12).
  For those, this test establishes nothing.

---

## 5. Exclusion gate before/after

Scanner `gate-scan.sh` transcribes the HARD-FAIL and REVIEW pattern lists **verbatim** from the location
they then occupied — the `PATTERNS_HARD`/`PATTERNS_REVIEW` heredocs of `orchestration/units/UBUILD1.build.sh`, since deleted by ULICENCE3 and replaced with the positive vocabulary checker written by `cat > "$DEST/gate.sh" <<'GATE_EOF'` (`:771`–`:896`, `chmod +x` at `:897`) —
matching with the `grep -rn -I -i -F -f` invocation.

| | before (sanitised tree) | after (substituted tree) |
|---|---|---|
| **HARD-FAIL hit lines** | **434** | **295** (−139, −32%) |
| REVIEW hit lines (report only) | 2294 | 2278 |

Per pattern (gate's own counting — lines of the hit listing containing the pattern, case-insensitive):

| pattern | before | after | | pattern | before | after |
|---|---|---|---|---|---|---|
| `/home/zer0null` | 83 | 83 | | `StateClass` | 108 | **5** |
| `duval` | 62 | 62 | | `grantPolicy` | 83 | **15** |
| `publish-present-compete` | 1 | 1 | | `src/broker` | 7 | **0** |
| `consonance` | 3 | 3 | | `src/scope` | 4 | **0** |
| `EXCLUDED.md` | 22 | 22 | | `src/layer` | 3 | **0** |
| `REDACTION_REPORT` | 120 | 100 | | `CommitRecord` | 0 | 0 |
| `RESIDUALS.md` | 31 | 35 | | `admit(` | 28 | 29 |
| `LICENCE_TODO` | 12 | 12 | | `expanded[` | 35 | 37 |
| `TRADE_SECRET` | 3 | 3 | | | | |
| `VERIFICATION_REPORT` | 13 | 13 | | | | |

**Mechanism-pattern subtotal (`StateClass`,`grantPolicy`,`src/broker`,`src/scope`,`src/layer`,`CommitRecord`,`admit(`,`expanded[`): 268 → 86.** A raw recursive line count over the tree gives **222 → 76**.

**The mechanism patterns are NOT cleared.** `admit(` and `expanded[` even *rise* by 1–2, because the
regenerated `verify/VERIFICATION.txt` — the verifier's own report — quotes the tokens it scans for
(21 → 37 hard-fail lines in that one file). The residual mechanism hits live in:

* `fixture/reflex-decisions.ts` (2) and `harness/data/fixture-190.json` (2) — the **protected `expanded[]`
  option label** (`"the expanded[] ref list"`), which the rule forbids changing;
* `results/*.json` (33) — frozen per-case records that embed option-label strings;
* `verify/VERIFICATION.txt` (20) and `verify/redaction-log.json` (3) — the verifier's own artifacts;
* `redact.py` (5) and `verify/run-verification.sh` (2) — instrumentation pattern lists, deliberately untouched;
* `second-labeller/parse_fixture.py` (1) and `RUN.json` (1).

So: substitution removes the mechanism vocabulary **from the instrument** (fixture question text 47 → 2
cases; strict-scan lines 416 → 84) but **cannot** clear the gate, because the gate's failing hits are
dominated by labels it may not change, records it may not re-derive, and the verifier's own log.

---

## 6. What this does NOT fix

1. **Path disclosures and paper apparatus — untouched by this test.** `/home/zer0null` (83 hits) and `duval`
   (62) live in `REDACTION_REPORT.md`, `INTEGRITY.md`, `MANIFEST.json`, `OWED_CORRECTIONS.md`, `README.md`,
   `LICENCE_TODO.md` and the `results/*.json` provenance. `publish-present-compete` (1) and `consonance` (3)
   likewise. Token substitution says nothing about them.
2. **Process artifacts.** `EXCLUDED.md` (22), `REDACTION_REPORT` (100), `RESIDUALS.md` (35),
   `LICENCE_TODO` (12), `TRADE_SECRET` (3), `VERIFICATION_REPORT` (13) — mostly filename-and-citation
   patterns (`TRADE_SECRET`, `VERIFICATION_REPORT` are names of workspace documents this release *cites*).
   `verify/VERIFICATION.txt`, `second-labeller/OWED_CORRECTIONS.md`, `second-labeller/EVIDENCE.md` are the
   same family and remain.
3. **`harness/data/{train,dev}.jsonl`** are **not** affected either way — they derive from `corpus.json`,
   not from the 190-case fixture (their digests are unchanged, which is exactly why the substitution cannot
   influence the trained heads' inputs).
4. **The transformer-model arms** (`modernbert-base` 0.3474, `deberta-v3-base`, `setfit-mpnet`) cannot be
   re-scored here: `evaluate.py`/`analyze.py` need `harness/out/manifest-eval.json`, excluded by
   `EXCLUDED.md` E12. Since those heads read the rendered question text, **substitution is not proven
   score-neutral for them** — only for the recomputable claims.
5. **UFIX10's instrument-version objection is not refuted, only narrowed.** The claim "the numbers survive"
   is now measured; the claim "this is the same instrument" is not, and cannot be, established by numbers.

---

## 7. Correction recorded during the test (honesty note)

The first scripted pass had a span-scanning bug: the field terminator test never fired, so substitution ran
to end-of-file in the `.ts` fixture and changed **4 option-label lines** (including `"the expanded[] ref
list"` → `"the EXPANDED_A ref list"`), which is outside the declared scope. That pass is **discarded** and
kept for audit as `logs/after-SPANBUG-discarded.txt` / `logs/gate-after-SPANBUG-discarded.txt`; in it the ten
values *also* held (projection digest `d52893f4…`, strict-scan 416 → 68, gate 434 → 293). The reported
figures are the re-run after fixing the span rule, from the untouched pre-substitution copy.

---

## 7b. Concurrent-writer note (found in the final write-scope sweep)

`repro/encoder-crossover-190-SANITISED/` **changed underneath this test while it ran.** I copied it at
18:17 CDT; by 18:22 CDT the source differed in `README.md`, `REDACTION_REPORT.md`, `INTEGRITY.md`,
`EXCLUDED.md`, `LICENCE_TODO.md`, `MANIFEST.json`, `verify/run-verification.sh`,
`verify/redaction-log.json`, `verify/VERIFICATION.txt`, `harness/collect.py`,
`second-labeller/{EVIDENCE.md,OWED_CORRECTIONS.md,PREREGISTRATION.md,RUN.json}` and
`preregistration/EXP12-typed-channel-comparison-prereg.md`, and two entries appeared that are not in my
copy: `verify/scrub-uscrub1.py` and `verify/__pycache__/`. That is **another unit's work — this unit wrote
only under `experiments/token-substitution-test/**`** (verified: no write outside the declared paths).

Consequence: `work-origcopy/` is the **18:17 snapshot**, and the before/after comparison is entirely
internal to my own copy, so it is a controlled comparison — but **re-running this test against today's
source will not reproduce these numbers**, because the verifier script itself has since changed. The
mapping and the result stand; the baseline bytes do not.

## 8. UNVERIFIED

* **Model-arm score neutrality** for `modernbert-base` / `deberta-v3-base` / `setfit-mpnet` under
  substitution — not testable in this subset (E12 excluded; no torch, no weights, no network).
* That `gate-scan.sh` reproduces the *published* `packages/exp12-encoder-crossover` gate exactly — no
  package tree exists in this workspace to diff against; the pattern lists and the `grep` invocation are
  transcribed from `UBUILD1.build.sh:423-461`, but the published `gun.sh`'s `--exclude="$SELF"` behaviour
  was not exercised (my scanner lives outside the scanned tree).
* Whether the residual `/home/zer0null` / `duval` hits *inside* `results/*.json` provenance are
  re-disclosures or already-public paper apparatus — not assessed here.
* Whether a re-declared projection digest is an acceptable substitute for byte-fidelity in the package's
  own `INTEGRITY.md` claims — an author/reviewer judgement, not a measurement.
* `src/x.ts`, `src/a.ts`, `src/b.ts`, `src/y.ts`, `src/store.ts`, `src/dag.ts` were **not** mapped: they are
  pre-existing neutral placeholder names, not kernel vocabulary. The REVIEW patterns `src/`, `dag.ts`,
  `store.ts` therefore persist (report-only; they never hard-fail).
* `variants/no-union/files/fixture/reflex-decisions.ts` was substituted **globally** (it is a `.ts` file
  that is not the canonical fixture path), so it is not scope-identical to the canonical fixture's
  question-only treatment. No script in the verification path reads it, so no measured value depends on it.

## Artifacts

`REPORT.md` (this file) · `mapping.json` · `substitute.py` · `gate-scan.sh` · `bin/git` (shim) ·
`logs/{before,after,after-SPANBUG-discarded,substitution-fixed,gate-before,gate-after,recompute-before,recompute-after}.txt` ·
`work/` (substituted tree) · `work-origcopy/` (pre-substitution control).
