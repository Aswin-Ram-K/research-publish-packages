# Unit KG-POLICY (2026-10-23) — resolve the pre-existing kg_policy failure

- **Card**: cb3a1e51-5e27-4038-8a35-b56d37fefc25, execution e99859d4, session-71d46747.
- **Objective**: diagnose `pytest tests/test_kg_policy.py::test_real_target_config_declares_the_decision`
  (PolicyWideningError on `.lane-j-scratch/*.md`) and resolve or explicitly waive it.
- **Bound**: 20 tool calls (used ~15), reply ≤8 lines.
- **Write paths**: `config/targets.toml` (sanctioned by card step 3(b) "fix the config"; see
  handoff assumptions), `tests/test_kg_policy.py`, `state/logs/kg-policy-analysis.md`,
  `orchestration/units/KG-POLICY.md`, `orchestration/handoffs/KG-POLICY.json`.
  `/home/zer0null/Duval` inspected read-only only (`--no-optional-locks`, `GIT_OPTIONAL_LOCKS=0`).
- **Result**: **done**. Root cause = target drift: Duval owner commit `90ba6d3` (2026-10-14)
  gitignored `.lane-j-scratch/` (`.gitignore:93`), so graphify's predicate now excludes it and the
  U1.7-era include entries became widening attempts. Fixed the config (dropped the two include +
  two assert_present entries, dated comment with restore path) and inverted test 12's pins;
  policy module untouched. Before: 1 failed, 11 passed. After: **12 passed**; full suite
  **1202 passed, 1 skipped** (0 failures). Guard B red→green proven live (re-adding the entry
  re-raises PolicyWideningError). Live audit: violations [], `.lane-j-scratch/` rejected ignored_dir.
- **Full analysis**: `state/logs/kg-policy-analysis.md`.
- **Known gaps flagged for follow-up**: `docs/PLAN.md:198` + `docs/TARGET_POLICY.md` §5 observation
  block are now dated w.r.t. the Oct-14 gitignore (doc-sync card); a fresh verifier card should
  red→green independently (rule (b) forbids this unit spawning one).
