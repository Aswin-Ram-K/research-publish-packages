# UNIT P4-GATE04 — engine identity capture and pin (gate 0.4)

**Card:** P4-GATE04 · **Date:** 2026-11-08 · **Live requests:** 0 completion requests (metadata GETs only) · **Tool calls:** offline

## Objective
Make the engine's identity (container image, argv, versions) observable at grade time:
capture it at run start via metadata GETs, stamp it into run metadata, and wire gate 0.4
to compare the captured identity against the pinned expectation, failing on mismatch or
on UNOBSERVABLE for a required field.

## Write paths (exactly, as declared)
- `experiments/ptr-engine/longrun/engine_identity.py`
- `experiments/ptr-engine/measure/ENGINE-IDENTITY-PIN.json` (harness pin file for gate 0.4)
- `experiments/ptr-engine/longrun/PIN-UPDATES.md`
- `orchestration/units/P4-GATE04.md`
- `orchestration/handoffs/P4-GATE04.json`

## Captured identity
- model_id = occamy-1.0
- served_model_name = occamy-1.0
- engine_version = 0.0.0.dev1+g4ccff141d
- argv = UNOBSERVABLE (tried GET /server_info 200 and GET /health 200; no argv field)
- image_or_container = UNOBSERVABLE (tried GET /server_info 200 and GET /health 200; no image/container field)

## Red→green
Change one pinned required field (e.g. engine_version) → gate check fails. Restore → passes.
Verified in tests/test_engine_identity (offline, mocked urllib).

## Completion paths touched
None. All requests were GETs on metadata paths. No /v1/chat/completions, /generate, or
token-producing path was requested.

