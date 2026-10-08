# V5E — independent verification of U5.14 (render neutrality + banner coverage)

**Role:** verifier, not author. **Purpose:** gate the one-time re-render of the two real dockets.
**Probe:** occamy `192.168.2.168:8012/v1/models` **DOWN** (curl exit 7, `000`), one probe, **zero live LLM calls**.
**Bound:** ≤32 tool calls. **Writable:** `orchestration/VERDICTS.md`, `orchestration/units/V5E.md`,
`orchestration/handoffs/V5E.json`, `state/logs/V5E*`, `state/verify/V5E/**`.

## Method
Re-derived on my **own** copies of `state/backups/U5.12-*/tree/` (never their fixtures, never writing the real
dockets or the backups). Full `__pycache__` purge + `PYTHONDONTWRITEBYTECODE=1` for every comparison.
Scripts: `state/verify/V5E/{c2_render,attacks,c3c4,revert}.py`, outputs `*.out`.

## Verdict: PASS (minor findings only)
