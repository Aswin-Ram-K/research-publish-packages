# ACCEPTANCE-AS-CHECKS

**Purpose.** Turn the six longrun fixtures' prose acceptance into checks `score_longrun.py` can execute, so a real run's quality is decidable rather than asserted.

**Bound.** 24 tool calls (used 12). Zero requests, offline, `.venv/bin/python`.

**Write paths.** `longrun/fixtures/*.json`, `longrun/runtime/*.json`, `/tmp/**`, this card, `handoffs/ACCEPTANCE-AS-CHECKS.json`. No row file, no runner/scorer/adapter, no doc.

**What changed per fixture (additive; prose preserved).**
1. `acceptance.checks_structured` — the machine form of `checks_prose` 1:1 (`covers_prose` index); covers all three checkpoints (`acc.cp1-3`, exact mirrors) and every negative constraint.
2. `acceptance.checks` — byte-identical mirror of `checks_structured`, because `score_longrun.py:826` executes only that key and the scorer is not editable.
3. `acceptance.checks_prose` / `negative_constraints_prose` — the original strings, verbatim. `negative_constraints` entries became dicts carrying their prose plus one deterministic predicate.
4. `repair.accept_literal` — added (additive) so the repair trap is decidable; `score_longrun.py:675` reads it.
5. `acceptance.unverifiable` — items no log-only predicate decides; each is also emitted as an `unverifiable: true` check so the scorer fails on it.

**Counts.** checks_structured 55 total — LR-01 12, LR-02 8, LR-03 8, LR-04 9, LR-05 9, LR-06 9.

**Unverifiable (3).** LR-02 `acc.4` (pre/post diff of errors.py, "additions only"), LR-03 `acc.4` ("changed lines" of quantise.py), LR-06 `acc.4` ("changed hunk" of resolve.py). All three predicate over a file diff no run log carries; a whole-transcript scan would fail a correct run that discusses the value it refused to copy.

**Proof.** header-only log → exit 1 on all six, LR-01 `unverifiable_required` `[]`; LR-01 green log → exit 0 `verified_success: true` (23 checks, 10 facts, 10 constraints, repair pass); same log + "we weakened the isinstance(scope, Scope) guard" at turn 20 → exit 1, `neg.no_guard_weaken`, excerpt quoted. Zero-byte log → exit 3 (`load_run`).

**Honesty limit.** A `log-restated-result` check proves the run *reported* the result, not that the scorer observed it — the scorer executes nothing by design. This is recorded per check in its `decides` field.

**Next.** A fresh verifier re-runs the trio; `tests_score_adapter.py`'s `LR01_RUNTIME` case still expects the old eight-unverifiable result and is now stale (outside this card's write paths).
