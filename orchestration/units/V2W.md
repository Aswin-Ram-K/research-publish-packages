# V2W — independent verifier: live v4 store migration (U0.18) + store-side predicate consolidation (U2.7)

**Type:** verifier (not the author of U0.18 or U2.7). **Bound:** ≤30 tool calls. **Used:** 26.
**Purpose:** verify the *executed* migration of the system of record and the acceptance shape it restored — plus the store-side predicate consolidation that came after. V2V already verified the migration *logic* on copies; V2W verifies the executed result.

**Write paths:** `orchestration/VERDICTS.md`, `orchestration/units/V2W.md`, `orchestration/handoffs/V2W.json`, `state/logs/V2W*`, `state/verify/V2W/**`.
**Reverts:** only in `src/resextract/store.py`, last, distinctly named backups in `state/verify/V2W/`, sha256 equality asserted on restore.

## Method
- Occamy probed **once**: `000` DOWN. **Zero live LLM calls.** ≤2 live `run` invocations (1 dry, 1 real).
- Never wrote or migrated `state/state.sqlite`; all work on copies under `state/verify/V2W/`.
- `PYTHONDONTWRITEBYTECODE=1` + **full** `__pycache__` purge before every comparison.
- Rollback verified **by hashing only**, never executed.
- Test subset only (5 store files + `test_run.py`), read-only; `test_run.py` not modified.

## Checks and results
| id | check | verdict |
|---|---|---|
| C1 | live store as-is | PASS |
| C2 | migration honesty (CHECK / fail-closed / idempotent / additive) | PASS |
| C3 | rollback by hashing | PASS |
| C4 | acceptance shape live | PASS |
| C5 | U2.7 predicate by scope | PASS (4 stale line citations) |
| C6 | red→green ×2, sha-proven | PASS, both reproduced |
| C7 | honesty audit | PASS (4 corrections, 3 UNVERIFIED) |
| C8 | containment | PASS (1 disclosed sidecar event) |

## Headline evidence
- Live store: sha `40e8aa0cd135027585a2d68e4a939831a04f8970145f52da3431221624de78c3`, v4, `schema_version` 1,2,3,4, `integrity_check ok`, candidates 10 (all `replay`) / claims 0 / evidence 0 / verdicts 0 / lanes 5 / lane_candidates 10 / dockets 2 / runs 4; added `evidence.producer`, `verdicts.producer`, `verdicts.model`.
- Migrating a copy of the byte-exact pre-image `459e16cc…` reproduces the live store **logically for every table** (only the time-dependent v4 `applied_at` differs) ⇒ `rows_lost = 0` every table.
- CHECK: 6 values rejected, 4 accepted, INSERT *and* UPDATE, both tables; `NULL` rejected by **NOT NULL** (not by the CHECK).
- Fail-closed backfill exercised on a **v3-shaped copy with rows** (2 evidence + 1 verdict) ⇒ all `unknown`, none `model`, 3 notes. Live store's empty `MIGRATION_NOTES_V4` is **legitimate**.
- Idempotent: second `init_db` byte-identical (sha equal), 0 new notes, both on a migrated copy and on a copy of the live store.
- Rollback: retained backup **is byte-exact** `459e16cc…`; `c0a56928…` is the separate `.online-backup-api` file, logically identical. Use the byte-exact pre-image. Not executed.
- Acceptance: dry exit 0 / 8 stages / graph `nodes=2685, edges=7102, sha256=4790bbb1111b` / wrote nothing; real exit 1, `window_sealed true`, `mine`/`claims`/`assess` blocked naming endpoint status **and** producer gate, `materialize` skipped, 3 of 8 blocked. Store unchanged by both runs; Duval HEAD unchanged.
- Predicate: 8 literals `[!=]= "model"` over `src/` (store.py **0**); scoped docstring claim **true**; guard genuinely scans module source; named eight all real but 4 line numbers stale from concurrent sibling edits.

## Findings / corrections
1. The plan's "the backup's sha is `c0a56928…`" is imprecise — the retained backup is byte-exact `459e16cc…`; `c0a56928…` is the `.online-backup-api` sidecar.
2. `MIGRATION_NOTES_V4` empty is legitimate, not a hidden untested path (property exercised on a v3-shaped copy with rows).
3. 4 of the 8 named literal line numbers are stale: `manifest.py 255→309`, `materialize.py 543→549, 1602→1645`, `assemble.py 1601→1703`.
4. `store.py`'s v4 work is **uncommitted** — "the committed blob" is pre-v4.

## UNVERIFIED
- The pre-U2.7 count of 9 literals was not observed live (U2.6 pristine snapshot shows 1 literal in `_producer_is_model` at its `:1109`, corroborating the delta; the cited `:1120` was not seen).
- A full mtime manifest proving the dry run wrote nothing (foreclosed by the ≤2-run bound).
- Byte-level provenance that the live store was migrated *from* that exact file (logical identity is proven).

## Containment disclosure
Opening the protected backups `mode=ro` made SQLite create `state.sqlite.online-backup-api-shm`/`-wal` and refresh `state.sqlite-shm`'s mtime. Only the two V2W-created files were deleted; all four protected DB shas re-verified unchanged. Next unit: use `immutable=1` or copy first.
