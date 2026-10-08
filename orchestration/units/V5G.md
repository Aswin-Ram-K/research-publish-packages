# V5G — independent verifier (replaces V5F)

**Scope:** U5.15 — the coercion fix + verdict-keyed claim standing. **Not the author of anything verified.**
**Bound:** ≤28 tool calls, one Occamy probe, zero live LLM calls, only the five docket test files. **Used: 27.**
**Write paths:** `orchestration/VERDICTS.md` (V5G section), `orchestration/units/V5G.md`, `orchestration/handoffs/V5G.json`, `state/verify/V5G/**`. No other file written.
**Reverts:** only `src/resextract/docket/materialize.py`, last, distinctly named backups, sha256 asserted on restore.

## Step 0
- Occamy `http://192.168.2.168:8012/v1/models`: `000`, curl exit 7, twice → **DOWN**. Zero live LLM calls.
- Handoff `orchestration/handoffs/V5G.json` created as `partial` immediately, finalized at the end (intermediate rewrites skipped to stay inside the 28-call bound — disclosed).

## Results
| check | verdict | key evidence |
|---|---|---|
| C1 suites | PASS | 166 passed / 6.30s; 70+24+30+25+17; assemble tracked-clean (no diff); 4 files untracked |
| C2 coercion | PASS | 24 raw values; only exact `model` renders CONFIRMS; no strip/lower in producer path; wrong-case capped with recorded reason |
| C3 verdict key | PASS | no `settled_by` in DDL; join `verdicts.claim_id=claims.id` + `claims.candidate_id=candidates.id`; a,b,c,d,e,f all as claimed; latest id wins |
| C4 vocabulary | PASS | `PRODUCERS = PRODUCER_VOCAB + ("mixed",)`, imported; CHECK refuses `mixed` on candidates **and** verdicts rows; 15-input table 0 divergences |
| C5 changed test | PASS | still pins outcome + reason; not vacuous; loading non-destructive (`extra="forbid"`, schema `resextract/docket/1`, `_smoke` validates) |
| C6 red→green | PASS | (a) and (b) both reproduced `assert 'CONFIRMS' == 'EXTENDS'`; restores sha-identical `51214b41…` |
| C7 honesty | PASS | `from_json` does not propagate verdict fields; only `_attach_verdicts` writes them ⇒ not data-reachable confirmed; 26/26 spend UNVERIFIED |
| C8 containment | PASS | Duval untouched; store v4 `40e8aa0c…` rows 10/0/0; dockets at U5.18 values; final sidecar delta 0; 0 worktrees reads; 0 stray processes |

## Findings
- **F1** `_claim_for`'s verdict branch renders the claim producer via `_normalise_producer(verdict_producer)` without the `("model","replay")` collapse ⇒ a `fixture` verdict yields `producer="fixture"` where `_claim_producer`/`derive_producer` yield `"unknown"`. Attribution inconsistency; no model standing conceded.
- **F2** A model-produced verdict on a **replay-mined candidate** renders `CONFIRMS` and the claim's producer becomes `"model"`, masking the candidate's replay provenance at claim level (docket-level `generated_by.producer` is still `replay`). Designed behaviour per ITEM 2 and consistent with `store.may_back_model_claim_verdict`, but it is the one route by which a non-model *claim* renders CONFIRMS.
- **F3** `(member.verification_state or "").lower()` at materialize.py:1594 is the one surviving normalisation in `_claim_standing`; it is on the declared state (not the producer) and caps rather than grants `CONFIRMS`.

## Release shas on disk (measured, unchanged through both reverts)
- `src/resextract/docket/materialize.py` `51214b415d2ffcd7a13790265c30794565b9def62c9a9c97a8b0606c25e04b88`
- `src/resextract/docket/manifest.py` `2099c15e39a3dae7c41815d0b2350265583a3331f12d83c13ce4412065964450`

## Files
- `state/verify/V5G/harness.py`, `harness.json` (full raw tables), `release-shas-before.txt`/`-after.txt`, `materialize.py.V5G-guard{A,B}.bak`, `scratch-store.sqlite` (fixture store), `curated.json`.
