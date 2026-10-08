# Verifier verdicts

Every batch ends with a verifier unit that is **not** the author of the work it checks. It re-runs the
evidence commands, checks the plan's clause in [`docs/PLAN.md`](../docs/PLAN.md), and includes a
red→green check on at least one guard. The main session makes the phase-gate call from this table.

| Date (UTC) | Verifier | Batch | Verdict | Plan clause checked | Evidence (commands run) | Red→green | Gate call |
|---|---|---|---|---|---|---|---|
| 2026-10-08 05:40 | **V0** | 0 | **PASS** | `docs/PLAN.md` §0–§11 (spec of record) | plan byte-identical (29875 B / 308 lines / 12 h2); doctor 3/3 rc 0 core 4/4, docling DOWN; U0.2 33p+1s, U0.3 64p exact; sqlite 12 tables + WAL; journal tamper→`(False,2)`, redaction safe; live off 152 ms/0 rt, on 7.44 s/256 rt | **2/2 reproduced** (`if not thinking:` and journal hash recompute), both sha-restored | **advance** |

## V0 — Batch 0 independent verification (U0.1, U0.1b, U0.2, U0.3) → PASS

Verified adversarially from self-generated evidence; author of none of the units. 20/40 tool calls, 2/2
permitted Occamy calls. Full report: [`orchestration/units/V0.md`](units/V0.md).

- **Spec integrity — PASS.** Session-log recovery (record 258) is **byte-identical** to `docs/PLAN.md`
  (29875 B, 308 lines, 12 `##`); §0/§11 present; all normative probe strings present (the two verbatim
  misses in the task are the plan's own wording: "Main session does only three things:" and
  `keyring/deepseek-v4.1-flash`). The log also holds an earlier 27770 B / 11-section revision, corroborating
  U0.1's recovery claim.
- **Env — PASS.** py3.14.4, graphify 0.9.80, openai 3.26.1, graspologic-native 1.3.1 (leiden), all 9 imports
  OK, all sampled graphify flags present. *UNVERIFIED:* the 0.9.65 side of "zero CLI drift" (no local artifact).
- **Doctor — PASS.** 3/3 `--json` rc 0 (core 4/4 green, docling DOWN); plain doctor rc 0. SearXNG did not
  time out in any run (retry rule untriggered). sqlite RO: WAL, 12 tables (11 + `schema_version`), 15 indices,
  declared column order matches DDL, 4 CHECK vocabularies.
- **Tests — PASS in scope.** U0.2 33+1 and U0.3 64 reproduced exactly (=97+1). Whole tree grew under us from
  siblings; their 6 `tests/test_web_fetch.py` failures are `src/resextract/web/**`, **out of scope / sibling-owned**.
- **Red→green — 2/2.** occamy `if not thinking:` (`7a44b4e8…`) and journal hash recompute (`3f82e6c6…`) each
  failed when reverted and passed when restored; sha before == after for both. `doctor.py` untouched.
- **Journal — PASS.** clean `(True,None)`; tamper→`(False,2)`; secret 0 chunks survive redaction;
  `tokens_used`/`reasoning_tokens`/`max_tokens` intact.
- **Live — PASS.** off 151.8 ms / 0 rt / "OK"; on 7438.7 ms / 256 rt / empty content, `finish_reason=length`
  — truncation trap reproduced.
- **Containment — PASS.** Duval HEAD `6deaed0…` unchanged; only the workspace is newer than 05:20 under
  `/home/zer0null`; `.gitignore` covers `state/`, `.venv/`, `dockets/`.
- **Follow-up (non-blocking):** CLI placeholder owner labels (`target→U1.1`, `run/mine→U2.1`, `assess→U4.1`,
  `lanes→U4.2`, `materialize/open/export→U5.2`, `serve→U6.1`, `refresh/watch→U7.1`) collide with live unit
  ids — rename or map them. Also surface the unwired `[stages.*].thinking` policy table.
