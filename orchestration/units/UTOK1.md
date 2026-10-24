# UTOK1 — token-substitution test (does neutralising kernel vocabulary move the numbers?)

**Spec of record:** `docs/PLAN.md`; unit prompt issued by the main session.
**Status:** done. Deliverable `experiments/token-substitution-test/REPORT.md`.

## One purpose

Test whether the kernel vocabulary the sanitised encoder-crossover fixture re-discloses
(`StateClass`, `grantPolicy`, `expanded[`, `admit(`, `src/*.ts`) can be replaced with neutral tokens
**without moving the ten CLAIMS values** — the third path UFIX10 refused. A clear negative would have been
an acceptable result; it was not the result.

## Hard bound

**Maximum 40 tool calls.** Used 28 by the time the report was written; STOP and report `partial` beyond that.

## Declared write paths (nothing else touched)

* `experiments/token-substitution-test/**` — report, mapping, substitution engine, gate scanner, logs, `work/`
* `orchestration/units/UTOK1.md`
* `orchestration/handoffs/UTOK1.json`

Never written: `repro/encoder-crossover-190-SANITISED/`, `repro/encoder-crossover-190/`, `/home/zer0null/Duval`,
`strategy/`, `papers/`. The as-audited control copy made under `experiments/token-substitution-test/` was
deleted after use; the source of truth remains `repro/encoder-crossover-190/`.

## Method

1. Copied the sanitised tree to `work/`; captured the before state with the shipped
   `verify/run-verification.sh` and `verify/recompute-claims.py` (exit 0, output logged verbatim).
2. Applied a documented mapping (`mapping.json`, engine `substitute.py`) with an enforced scope:
   question/prose only; **never** option labels, `correct`/`recorded_index`, case ids, or `_line`; `.py`/`.sh`
   instrumentation untouched.
3. Re-ran both verifications unmodified on the substituted copy and diffed.
4. Re-ran the exclusion gate using the HARD-FAIL list then published at
   the `PATTERNS_HARD`/`PATTERNS_REVIEW` heredocs of `orchestration/units/UBUILD1.build.sh` — a range that is now dead. ULICENCE3 has since deleted that list and replaced it with the positive vocabulary checker written by the heredoc beginning `cat > "$DEST/gate.sh" <<'GATE_EOF'`, currently `:771`–`:896` (`chmod +x` at `:897`).
5. A `bin/git` shim refused every `git` call naming the read-only target, so `run-verification.sh`'s
   `git -C /home/zer0null/Duval` lines never executed.

## Result

* **A released script DOES read `question`** — `harness/tccommon.py:155` (the model input), and
  `second-labeller/compare.py:55` recomputes a CLAIMS value from it. Not display text.
* **10/10** `run-verification.sh` values unchanged; `recompute-claims.py` output **byte-identical**
  (5 CLAIMS constants + 4 kappas + fixture-correctness digest). `train/dev` digests identical.
* **The scoring-projection digest moved** `57a29b4e…` → `75d4b0a2…` — it hashes `question`, so it must.
* **Gate NOT cleared: 434 → 295** hard-fail lines (mechanism tokens 222 → 76); residual hits are protected
  option labels, frozen `results/*.json`, the verifier's own log, and instrumentation.
* Model-arm accuracies (`0.3474` etc.) are **not** re-testable in this subset (E12) → listed as UNVERIFIED.

## Recorded correction

First scripted pass had a span-scanning bug that leaked substitution into 4 option-label lines (out of
scope); that pass was discarded and the experiment re-run from the clean copy. Both passes are logged.

## Concurrent-writer note

`repro/encoder-crossover-190-SANITISED/` was modified by **another unit** during this test (new
`verify/scrub-uscrub1.py`, `verify/run-verification.sh` itself changed after my 18:17 copy). UTOK1 wrote
only under its declared paths; the before/after comparison is internal to `experiments/token-substitution-test/`
(`work/` vs `work-origcopy/`, the 18:17 snapshot), so it is controlled — but the baseline bytes are not
reproducible against the current source.

## Report-back

`orchestration/handoffs/UTOK1.json`. Next hint: the numbers survive, but a re-declared projection digest is
an author judgement, and the process-artifact / paper-apparatus gate hits are a separate, untouched problem.
