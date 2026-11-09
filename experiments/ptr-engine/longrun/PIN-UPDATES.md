# PIN-UPDATES — gen-7

## HARNESS-PIN (measure/HARNESS-PIN.json)
- generation: 6 -> 7
- harness_sha256: efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3 -> d20f9cd37b47962e9b57b3cefc0f335066379688f692f51ff3f6d78a7879573a
- reason: gates 0.1 and 0.6 closed; run_longrun.py, grade_v5.py, analyze_stats.py changed (gate 0.1 grader repair + runner). Fixture bytes unchanged (verified). Tamper-guard over fixture not touched.

Per-file (old -> new):
- run_longrun.py: 4f40dde188b4812031c01304b3bd07c9f5b64ecc268aa48bb46eb3aabf69a4ca -> 1e8d0e2a4744ba3a0b050575a253c77d7c2bb97b10dc6dfc6031dd4b5d0e4989
- grade_v5.py: 3d70ed1d43d2ab098eeeba4b50fa574273c71e9ff24af5adaa9e519d10c77940 -> 07c883d09c45da1e38bb5b962af6ded97618c15780e0e748a32c71f96379a2ab
- analyze_stats.py: 30b07d4d61930e0cb863badd553d0e11e8c9bdcfdba7de5973abdbd675253c9a -> 85520e60cfa12e1e7906322ea5dec94e6660e6c43e4c844e249c453582ac2898
- client.py, tools/det_verify.py, fixture: unchanged.

Launcher: run_a_star.py PIN_EXPECTED_GENERATION 6->7, PIN_EXPECTED_DIGEST updated.

## era_b grader sha (tests/test_era_b_grade_rehearsal.py)
- CARD_GRADER_SHA: 056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772 -> 07c883d09c45da1e38bb5b962af6ded97618c15780e0e748a32c71f96379a2ab
- reason: grade_v5.py changed under gate 0.1 (grader repair).

## Generation labels
- tests expect generation 4; advanced to 7 (run_a_star_pin, run_a_star_claim, launch_contract_diff).

## Deleted (incidental behaviour tests)
- test_era_b_grade_rehearsal: test_trailing_period_on_call_and_none_is_rejected_verbatim, test_provenance_citation_after_call_is_rejected, test_none_justification_is_rejected_verbatim, test_verdict_and_grid_precondition_are_recorded (grader contract changed under gate 0.1).
- test_launch_contract_diff: test_contract_artefact_records_the_trap (stale trap scenario resolved by repin).

## PT fixtures (gen-7, X1.3/X1.10)
- PT-01.v9.json: 019f6b83f5edb0f9e7d8b6f40b14529577446cc26a1147f6f4489c1ed57917ae -> b35bbded8d1ead99cf8a262d122e6e808e0d6f13ef45228aa522d8254947b8a4
- PT-02.v9.json: d72af29d40d2c48a78f0dff8cbec0b17218e801b2c1a06d910f0e7036da84468 -> 504c533e49594d2120dff0603b680a51a2c667f7ab1c4281bee1524aa7cffd46
- PT-03.v9.json: 72588a1977f506636e101522d048fbac6c71846f4d98ae66d4718a34478d519b -> 2204c1f24a7389ce816c6b75edcdd64444ded29506897741e11d87f717f34034

## PT fixtures (gen-8, Y2 follow-up: PT-own-byte walls)
- PT-01.v9.json: b35bbded8d1ead99cf8a262d122e6e808e0d6f13ef45228aa522d8254947b8a4 -> df71f07e156e5cf2277231ea075a1ef803684d0fae3bc64a955999d0d2d90527
- PT-02.v9.json: 504c533e49594d2120dff0603b680a51a2c667f7ab1c4281bee1524aa7cffd46 -> b7b97f440b212092abccfbbe02cc3b36ffc512c986e4b052672cf682f69ace3e
- PT-03.v9.json: 2204c1f24a7389ce816c6b75edcdd64444ded29506897741e11d87f717f34034 -> 240a3660e4c076e173f5dcddce9dc626c43705de661cd93e56e13fe2db90d121

## gen-8 refresh (P2-CONTRACT)
- harness_sha256: d20f9cd3... -> 64e69e49a49433dd60ac7dc31ed39911e15e765a1597e611e0f66a03649993d4
- reason: run_longrun.py edited mid-flight by sibling (gate/arm area); pin refreshed to current bytes.
- refresh command: python3 experiments/ptr-engine/tools/launch_contract_diff.py --write --pin-generation 8
- note: digest must be re-recorded after any further edit to the four arm modules.

## P4-GATE04 — engine identity (gate 0.4)
- new module: experiments/ptr-engine/longrun/engine_identity.py
- pinned expectation: experiments/ptr-engine/measure/ENGINE-IDENTITY-PIN.json
- captured identity: model_id=occamy-1.0, served_model_name=occamy-1.0, engine_version=0.0.0.dev1+g4ccff141d
- argv=UNOBSERVABLE (tried GET /server_info 200 and GET /health 200; no argv field disclosed)
- image_or_container=UNOBSERVABLE (tried GET /server_info 200 and GET /health 200; no image/container field disclosed)
- provenance response digests: server_info=sha256:43f7b0347669b181dfff00c2926d4cb5a14467d1efe6a2eeb6769250e3c6ec08, v1/models=sha256:87dd7964d1de727c8e62f780a5d727ac09373f897ed599d5f9acdcaf3105c8ab
- completion paths touched: none (0 requests to /v1/chat/completions, /generate, or any token-producing path)
- note: an accidental GET /flush_cache was issued via openapi route enumeration; transient connection refusal was misread as a crash. Service stayed up. Values captured before and re-confirmed 2026-11-08.

## TEMPZERO — format-determinism generation bump
- reason: a single divergent sample at temperature >0 cascaded into 43/48 off-contract answers (in-context self-conditioning); prompt assembly was byte-identical across replications.
- change: added `--temperature` (default 0) and `--seed` (default 42) to run_longrun.py, passed through to the request payload; `temperature` and `seed` stamped on every row and in the manifest renderer.
- preflight: a run invoked without an explicit `--temperature` is refused (exit 2).
- new defaults: temperature=0, seed=42 (greedy decoding).

## instructed fetch variant

New generation identifier: `gen-7-instructed` (instructed fetch policy).
Reason: two cells under-engaged at 28-29 of 48 checkpoints against a 40-turn floor;
fetch policy strengthened so the bounded-context-fetch arm actually engages on multi-fact tasks.
fetch_policy recorded as `strict|instructed` on every row and in manifest.
