# V5B — independent verification: U5.6 (tree-first resolution) + U5.7 (producer gate)

- **Role:** verifier (not an author of either unit). Fresh context, no prior knowledge.
- **Bound:** ≤35 tool calls → used **33** (incl. writes + report-back). Zero LLM calls. One Occamy probe.
- **Probe (0a):** `http://192.168.2.168:8012/v1/models` → curl exit 7 / http 000 → **DOWN**. Model path = `UNVERIFIED (blocked)`.
- **Purpose:** test the claims that a docket's material is *verifiable at a commit* (U5.6) and that a docket **cannot claim model provenance it does not have** (U5.7) — from evidence generated here, not replayed from the unit cards.

## Order (as given) and results
| id | check | verdict |
|---|---|---|
| C1 | four suites (provenance/materialize/pinned/assemble) | PASS — 19/25/17/24 = 85 |
| C2 | live truth re-derived (real store read-only; materialize via store **copy**) | PASS |
| C2b | model case (fixture) | PASS, fixture-proven only |
| C3 | gate bites adversarially (-ready → PromotionRefused; vocab CHECK) | PASS |
| C4 | red→green ×3, sha-proven restore | PASS |
| C5 | backward compat (smoke, U5.5-shaped, schema string) | PASS |
| C6 | pinned-bytes regression on `duval-u55-pinned` | PASS — sha unchanged, 6/6 |
| C7 | honesty audit | PARTIAL (findings below) |
| C8 | containment | PASS |

**Overall: PARTIAL.**

## Key evidence
- **Live:** real store 10 replay / 0 model, `may_back_model_claim` false ×10. Scratch re-materialize of lane `claim-test-unreproduced` (store copy) → producer `replay`, model `null`, status `draft`, `status_reason` = `producer is replay: no model mined these candidates; not publication-eligible`, `promotion_eligible` recomputed independently = **False**. Warning verbatim in **README.md and CHECKLIST.md**: `> **PROVENANCE: replay-produced** — no model mined or assessed these candidates. Not eligible for publication until real mining runs.` Survives a bare re-assembly. `verify_docket` ok; copied 2 / pinned 2 / unpinned 0 / refused 0 / unresolved 0.
- **Model (fixture):** producer `model` + ready → no PROVENANCE line, `promotion_eligible` True, verify ok.
- **Gate:** explicit `status="ready"` on replay → `PromotionRefused`; bad producer rejected by store CHECK and manifest vocab.
- **Red→green (all restored bit-identical):** `materialize.py 6e768096…`, `assemble.py 95c3f717…`.
- **C6:** manifest sha `879e66b8…` unchanged; `blob_sha == git rev-parse <commit>:<path>` on 6/6 pinned entries.
- **C8:** Duval HEAD `55710509` + porcelain unchanged; real store rows identical before/after; verified docket sha unchanged; no stray processes.

## Findings / caveats
1. **Bare re-assembly drops pinned provenance.** On a *copy* of `duval-u55-pinned`, the documented bare re-assembly rewrote `resolved_from: git_object → working_tree`, dropped all 6 `blob_sha`, and changed the manifest sha `879e66b8… → 526b869d…`. U5.7's warning survives; U5.6's commit-verifiability does **not**. Real docket untouched.
2. **"the docket is still built, labelled"** holds only for the default draft path; with explicit `status="ready"` nothing is written.
3. `dc25c257` sha **not reproducible** anywhere in docket sources/tests (`6e768096`/`95c3f717` confirmed).
4. Model path is fixture-only; live model path unverified (endpoint down).
5. Precedence `model+replay ⇒ replay` judged **conservative-correct**, not a defect (asymmetric error; one producer field cannot attest a mined share).

## Write paths (only)
`orchestration/VERDICTS.md`, `orchestration/units/V5B.md`, `orchestration/handoffs/V5B.json`, `state/logs/V5B*`, `state/verify/V5B/**`. Nothing outside the workspace. Real store never mutated (writes against copies). `docs/PLAN_CORRECTIONS*` not written.
