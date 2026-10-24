# ROW-SCHEMA — one writer that refuses null rows, plus an audit of every cell

**Tag:** `automated` — no human present. No `ask_user_question`, no waiting, no confirmation.
**Mode:** `workspace-write`. **Live requests: 0** (no Occamy, no SearXNG, no lock taken).
**Persisted:** 2026-10-23 (America/Chicago).

## 1. Objective

Close the null-field defect class at its source and make it visible if it ever recurs:

1. **One writer.** Every row written through `resextract.store` passes a *single* gate
   (`store._insert`) which validates the row against a **declared per-table profile**: which
   columns are **hard-required** (a NULL there means the row is defective and is refused,
   `NullRowError`), which are **optional-nullable** (NULL is a legitimate recorded state), and
   which `_json` columns must parse. A refusal never happens half-way: the INSERT is never issued.
2. **The profiles are declared, not inherited.** They encode the rule the rest of this workspace
   already states in two places — `AGENTS.md` ("validate parse AND the contracted key set; add a
   live missing key, never baseline it") and `docket/manifest.py` ("`None` means *never
   recorded*, never *a value called None*") — as ONE object per table, so a new writer cannot
   pick a weaker rule.
3. **An audit of every cell.** `python -m resextract.audit_store` walks the live DB
   (`state/state.sqlite`) and reports, per table and per column, the NULL count and — for every
   `_json` column — parse failures, with an explicit **conformant / defect / undeclared** verdict
   per cell. The pre-existing NULLs found in the live store are classified rather than laundered:
   they are real (see §3), not noise.

## 2. What the live store actually holds (measured before any code change)

`state/state.sqlite`, 13 tables, 12,004-byte `claims`/`evidence`/`verdicts` = **0 rows**:

| table | rows | NULL cells |
|---|---|---|
| `candidates` | 10 | `model` ×10 |
| `lanes` | 5 | `parent_lane_id` ×5 |
| `dockets` | 2 | `lane_id` ×2 |
| `runs` | 4 | `finished_at` ×1 (`run 3`, failed), `model` ×4 |
| other 9 | 0 | — |

Every one of those NULLs has a *reason* on the row (replay-sourced producer ⇒ no model id; roots
have no parent lane; run 3 never finished; dockets written by the replay assembler have no lane
row). So the profile must class them **optional-nullable**, not refuse them — the defect class is
about *missing required* values (the `U8.40`/`U8.43`-family key gaps and the `C-curated` producer
gap), not about honest "never recorded".

## 3. Hard bound

**30 work tool calls** (edits + test runs counted; the handoff write excluded). If the suite is
not green in 3 attempts, STOP, write the card + handoff as `partial` naming the failing tests.

## 4. Write paths (for clash detection)

`src/resextract/row_schema.py` · `src/resextract/audit_store.py` · `src/resextract/store.py`
(additive: import + `_insert` gate + `NullRowError` re-export) · `tests/test_row_schema.py` ·
`state/logs/ROW-SCHEMA-null-audit.{json,txt}` · `state/logs/ROW-SCHEMA-redgreen.txt` ·
this card · `orchestration/handoffs/ROW-SCHEMA.json`.

**No writes** to `/home/zer0null/Duval`, no `git`, no systemd, no DSH change, no `state/state.sqlite`
mutation (the audit opens the DB **read-only** via `file:...?mode=ro`).

## 5. DO NOT TOUCH

- Do not repair or rewrite the four R2-* handoffs whose key gaps currently fail
  `tests/test_orchestration_handoffs.py::test_no_new_contract_key_gaps` (that guard is red at HEAD,
  pre-existing, recorded as a known gap; the guard is not baselined here).
- Do not change migration count / `SCHEMA_VERSION` (stays 4) — the profiles describe the schema at
  v4 and are asserted to cover every column of every table.
- Do not touch `docket/manifest.py`, `assess/**`, `lanes/**`, `claims/**`.

## 6. Verdict format

`orchestration/handoffs/ROW-SCHEMA.json` — unit shape (`unit, status, artifacts, evidence,
blocker, next_unit_hint, write_paths`) plus `assumptions`, `red_green`, `tool_calls`, `bound`.

## 7. Outcome (appended at close — see orchestration/handoffs/ROW-SCHEMA.json)

**Status: done.** The three tiers landed, the single writer refuses, and the audit is clean.

| guard | what it forbids | red when reverted |
|---|---|---|
| `_gate` in `store._insert` / `store._arrow_execute` | a row missing a tier-1 column | `DID NOT RAISE NullRowError` |
| `test_no_insert_bypasses_the_single_writer` | an INSERT issued straight to `con.execute` | `bypassing INSERT sites: ['store.py:1584 …INSERT INTO dockets…']` |
| same test, gated-site count | a writer that keeps its `ON CONFLICT`/`OR IGNORE` but drops its gate | `expected the two gate-then-execute writer sites, saw […lane_candidates…]` |
| `audit_store.audit` classification | a tier-1 NULL planted behind the writer's back | `the audit missed a planted tier-1 NULL` |

Evidence: `state/logs/ROW-SCHEMA-redgreen.txt`, `state/logs/ROW-SCHEMA-null-audit.{json,txt}`.
Suite: `1 failed, 1315 passed, 1 skipped` — the single failure is the pre-existing
`test_orchestration_handoffs.py::test_no_new_contract_key_gaps` (R2-* and `V-R2VLLM-TRIAGE`
handoffs; not this unit's files, not baselined here).

### Two things this unit learned the hard way (worth repeating in the next card)

1. **A guard that cannot fail is not a guard.** The first bypass scan matched per *line*, so it
   reported "no bypass sites" against a store that had two — including `upsert_lane`'s
   explicit-id upsert, the very path a NULL `lanes.target` could have entered through. It now
   scans whole files and carries a control assertion that it matches the multi-line shape.
2. **A red→green harness can lie.** The first version ran the copied tree's tests against the
   *parent* `src/` (import resolution), so every reverted run printed green. It now pins
   `PYTHONPATH` to the copy, clears `__pycache__`, and asserts that the revert changed bytes.

Also removed: `insert_evidence`/`insert_verdict` silently substituted `utcnow()` for a missing
`retrieved_at`/`checked_at` — the writer invented a value the caller never supplied, which is the
same defect one layer up.
