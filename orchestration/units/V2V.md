# V2V — independent verification of U2.6

**Verdict: PASS** (3 non-blocking corrections; disclosure overstatements recorded).
Scope: U2.6 — boundary (item 1), hint (item 2), one predicate (item 3), `verdicts.model`
enforcement, and the three repaired false disclosures. I authored none of it.

Bound: 34 tool calls. **Used 29.** Occamy endpoint DOWN (curl exit 7 / HTTP 000); **0 live LLM
calls**, **0 real web searches** — every client was a local stub. Full `__pycache__` purge +
`PYTHONDONTWRITEBYTECODE=1` before every comparison.

## C1 — the eight suites: 147, exact
`store 42 · store_v2 13 · store_v3 8 · store_v4 9 · assess_verdicts 41 · assess_evidence 14 ·
assess_value 11 · store_boundary 9 = 147`. Claim matches exactly.

## C2 — boundary re-derived from my own setup (highest value): PASS
Built my own copy of the v3 claims DB (`state/claims/store-copy.sqlite`, v3, 9 claims) under
`state/verify/V2V/`.

* **Typed error, run start.** `assess_claims(..., migrate_store=False)` raised
  `resextract.store.SchemaTooOldError`, `found=3 required=4`, message:
  `schema too old: <path> is schema v3 but this write needs v4; run store.init_db('<path>') to
  migrate it in place, or store.migrate_copy('<path>', dst) to migrate a run-scoped copy (backs
  the source up first)`. Not a `sqlite3.OperationalError`; source sha unchanged, still v3.
* **Not swallowed.** Injecting a `SchemaTooOldError` mid-loop (patched `store.insert_verdict`) was
  **re-raised out of the per-claim isolation wrapper**. For contrast I injected the *old* obscure
  error instead: `sqlite3.OperationalError: table verdicts has no column named producer` **is**
  swallowed → `claims_assessed 0` with 9 degradations. That is exactly U2.5's failure mode, and it
  is now special-cased. **Caller sees the error.**
* **Migration of a copy.** With `migrate_store=True`: `version_before 3 → version_after 4`,
  `rows_lost 0`, `claims_assessed 9`, **9 verdict rows**, `producer = fixture ×9`, `model` all
  NULL, **source sha unchanged and still v3**, `report.migration` populated (not silent).
* **Idempotency.** A second `migrate_copy` from the already-v4 copy: `4 → 4`, `migrated False`,
  `rows_lost 0`, counts identical, **no new notes**.

## C3 — one predicate by IDENTITY: PASS, one false comment
* `assess.verdicts.may_back_model_claim **is** store.producer_is_model` (module
  `resextract.store`); `PRODUCER_VOCAB` and `MODEL_PRODUCER` are the store objects in **both**
  `verdicts.py` and `value.py`. `store.may_back_model_claim` is deliberately a *different*,
  row-taking predicate.
* Duplicate constants: **0 remain** (2 removed from `verdicts.py` — reproduced).
* Literals: **3 removed** (all in `assess/value.py`), **not 5 as claimed**; `assess/**` now has 0.
  **1 literal remains in `store.py:1120`** (`_producer_is_model`: `row.get("producer") == "model"`).
* Therefore `producer_is_model`'s docstring *"the **single** string-level comparison"* is **FALSE**
  — a second exists. This is the same drift class U2.6 set out to remove. The other comments
  (single vocabulary definition; `may_back_model_claim IS producer_is_model`) are **true**.

## C4 — the hint, adversarially: PASS, no upgrade possible
| client | hint | result |
|---|---|---|
| replay | `model` | **EXTENDS** (capped), model_calls 0, client_producer replay |
| undeclared | `model` | **EXTENDS** (capped), client_producer `unknown` |
| model | `model` | **CONFIRMS** |
| model | `replay` | `replay` (deny/downgrade allowed) |
| any | `MODEL`/`Model`/`gpt`/`""`/`"model "` | `ProducerDeclarationError` (typed, case-exact) |

Brute force over **25** (declaration, hint) pairs plus nested/bool-declaration clients: **zero
upgrades found**. `value._client_producer` **delegates** (wrapper at `value.py:832-844`) — but it
is **not the same object**, contrary to the handoff's "same function object".

## C5 — `verdicts.model` + enforcement: PASS, one nuance
Model row records `model`; non-model row records `producer` and `model NULL`; `insert_verdict`
raises `ValueError: model id 'occamy-1' may only accompany producer='model', not 'replay'`.
The assess writer derives `producer` (`_verdict_db_producer`) and passes `model` only when
`producer_is_model`; the publish gate consults the single predicate. **Nuance:** the *store-level*
default is `producer="unknown"` when omitted — fail-closed, but not "required/derived" as claimed;
derivation lives in the assess writer.

**Accessor judgement:** the four v4 accessors (`evidence_by_producer`, `verdicts_by_producer`,
`may_back_model_claim_verdict`, `model_produced_verdicts`) have **0 production callers** —
confirmed. Acceptable as public query API, but they are currently exercised only by tests; wire
them when a consumer exists, else they are unused surface.

## C6 — the regeneration: coherent, matches the good backups byte-for-byte
`store.py`/`verdicts.py`/`value.py` are **sha256-identical** to `state/backups/U2.6-good-*.py` and
match the handoff's final shas. No duplicate top-level definitions/assignments, no vanished helper
still referenced, no orphaned constants. Accident traces found: the `store.py:61` docstring
overstatement and the value-delegate wording. **Passing tests plus this coherent read is enough**
for me to conclude the files are what U2.6 claims.

## C7 — red→green, three guards, sha-proven (LAST)
| guard | revert | red | restore | green |
|---|---|---|---|---|
| (a) boundary typed error | drop `_require_writable_schema` from `insert_verdict` | `sqlite3.OperationalError: table verdicts has no column named producer` → 1 failed | sha `f79ba0ab→cb96d4d0→f79ba0ab` equal | 1 passed |
| (b) hint cannot upgrade | `_client_producer` hint-first | hint upgraded the declaration → 1 failed | sha `754101b8→49aa684b→754101b8` equal | 1 passed |
| (c) `verdicts.model` enforcement | drop the `model`+non-model guard | `Failed: DID NOT RAISE ValueError` → 1 failed | sha `f79ba0ab→9499cba8→f79ba0ab` equal | 1 passed |

Distinctly named backups under `state/verify/V2V/c7/backups/`; restore asserted by sha256 equality
and re-run. No restore would have overwritten newer content (checked before writing back).

## C8 — the three repairs: PASS
* `tests/test_store_v3.py` vs HEAD `a62a8fc`: **4 deleted assert lines / 7 added assert lines**
  (16 added non-context total) — exact match. The 4 deletions are all version literals; each is
  replaced by a looser `>=` pin **plus** a stricter `== store.SCHEMA_VERSION` / cross-check, so the
  net contract is **stricter**. **0 substantive; I agree nothing needed restoring.**
* Migration-4 note now reads *"the schema-v4 backfill joins nothing, so it refuses to infer a
  producer; 'unknown' is the conservative, fail-closed result"*. Live spot-check on a fresh v3 copy:
  2 notes (evidence, verdicts), both `unknown`, old *"no producer evidence exists"* text gone,
  source sha unchanged.
* Caller picture correct: `may_back_model_claim` **is** called in production — at
  **`run.py:1384`** (the unit's `1278` is stale; `run.py` is concurrently edited by U8.5). Four v4
  accessors: 0 production callers.

## C9 — honesty audit
Reproduced: 147; 9 claims / 9 verdicts / `fixture ×9` / `rows_lost 0`; red→green.
**Overstated:** "5 literals removed" (measured 3); `value._client_producer` "same function object"
(delegating wrapper); `insert_verdict` "requires" producer (store default `unknown`);
`producer_is_model` "single string-level comparison" (a second at `store.py:1120`).
**Not reproduced:** the 5-literal figure; whether `U2.6-good-*` are pre-accident-good rather than
regenerated artifacts (self-consistent only); U2.6's own 34/34 spend. **No behavioural trace of the
accident** that the 147 tests would miss — the gaps are wording-level.

**`fixture` judgement: correct.** `fixture` is the codebase's existing value for the deterministic
non-model pass (`assess/value.py:589,613,634`); `replay` would be actively wrong (no model response
was replayed) and `unknown` would discard the true fact that the deterministic pass produced it.
Recommend documenting it, or adding an explicit `deterministic` at the next vocabulary migration —
not now, since a vocabulary change needs a CHECK migration on the real store.

## C10 — containment: PASS
Real `state/state.sqlite` **unchanged**: sha `459e16cc875654df0fa0b5a4dc5480de3c861de75a53eaceea54fafde3f2faf5`,
**v3**, verdicts columns still `id, claim_id, verdict, rationale, evidence_ids_json, checked_at`,
rows candidates 10 (all `replay`), claims 0, evidence 0, verdicts 0, lanes 5, lane_candidates 10,
dockets 2, runs 4. `/home/zer0null/Duval` HEAD `6c60da5a…` unchanged with only the foreign actor's
`?? .ci-trunk.txt` / `?? .lane-j-scratch/`; 0 `.worktrees/` reads; 0 writes outside the workspace;
0 stray processes. Temporary reverts touched only `src/resextract/store.py` and
`src/resextract/assess/verdicts.py`, last, sha-restored.
