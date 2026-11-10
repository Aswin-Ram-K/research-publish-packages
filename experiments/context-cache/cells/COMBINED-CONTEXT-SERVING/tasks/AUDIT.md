# Audit of LR-01 / LR-04 and harnesses

## Harness seam
- `experiments/ptr-engine/longrun/run_longrun.py:52` defines `ARMS = ("transcript-grow", "transcript-compact", "pointer-stable", "lease-reopen")`; the runner is a turn driver, not a workspace executor. It records `_content`/answers per turn and never runs commands.
- `experiments/ptr-engine/longrun/score_longrun.py:168-186` (`match_answer`) grades by strict `text == want` after strip (or contains/regex), not by executing anything.
- `experiments/ptr-engine/longrun/score_longrun.py:584-638` (`eval_artifact`) only checks logged artifact text (`must_contain`, `must_not_contain`, sha256) from `run["artifacts"]`; it never writes or executes a file.
- `experiments/ptr-engine/longrun/score_longrun.py:760+` validates fixture digest / checkpoints / log completeness against the run log.

Conclusion: there is **no tool/execution seam**. The scorer cannot grade a completed workspace; it grades answer strings and logged artifacts.

## Impossible in a text-only replay
- LR-01 `acc.cp*` fact checks at turns 12/24/36 (`score_longrun.py:795-810`) require exact checkpoint answer values; a text-only model can emit them but nothing verifies a real edit.
- LR-01 `artifact` checks (`score_longrun.py:584-638`) require a logged write body with exact containment/digest; without a tool channel no workspace file is produced.
- LR-01 `neg.no_guard_weaken`, `neg.no_test_delete`, `neg.no_fixture_write` are regex scans over answer text (`score_longrun.py:818-825`), not executions.
- LR-04 `acc.cp*` fact checks require exact tuples/sets from checkpoint turns.
- LR-04 artifact/negative checks likewise scan text.

## Answerable
- Facts that fit in one answer string and are directly stated in pinned source ranges (e.g. algorithm name, counts, scope names) can be answered textually.
- Provenance can be checked by requiring the answer to reproduce a value from a specific pinned line range.

## Decision
Use **answer-as-artifact**: the model returns one self-contained Python module in a fenced block. The verifier extracts it, seeds pinned Duval files under `tasks/work/<task>/`, executes the module, and grades exit code/stdout plus seeded-digest integrity. Checks that cannot be executed are dropped (none retained here).

## Derivation vs recall
All four `der.*` checks are computed from the seeded source by the genuine `pass.py` programs (regex extraction/counting), not recalled literals. No check is marked `recall`.
