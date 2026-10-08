# V8C — independent verifier: U8.6 validity + U8.7 provenance + U8.8 digest pin
Scope: three stacked changes in `src/resextract/run.py`; verify, never fix. Hard bound 28 tool calls (used 27).
Constraints honoured: 1 Occamy probe (DOWN, 000, zero live LLM calls), 2 live `run` invocations (1 dry, 1 real),
no graph build, only `tests/test_run.py`, full `__pycache__` purge + `PYTHONDONTWRITEBYTECODE=1` for every
comparison, `/home/zer0null/Duval` read-only, store read via `immutable=1` (no sidecars created).
Reverts confined to `run.py`, last, each with a distinctly named backup + sha256 asserted on restore (both OK).
Verdict: PARTIAL (see `orchestration/VERDICTS.md` §V8C; handoff `orchestration/handoffs/V8C.json`).
