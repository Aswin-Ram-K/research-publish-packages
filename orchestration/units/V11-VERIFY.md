# V11-VERIFY unit card
unit: V11-VERIFY
overall: fail
checks: 16 (1 fail-blocker, 2 pass, 3 pass-note, 4 pass, 5 pass, 6 pass, 7 pass, 8 pass, 9 pass, 10 pass, 11 pass, 12 pass, 13 partial-fail, 14 pass, 15 plumbing-only, 16 no)
blocker: bodies namespacing — _BODIES keyed by bare ref (pointer_table.py:102), _BODIES fallback leaks across fixtures (fetch returns BETA for ALPHA entry with body=None); reset_bodies() defined but has zero callers
next_unit_hint: fix bodies store to fixture-namespace + wire reset_bodies() per-fixture with red test (same ref, different bodies, body=None entries), then re-verify; also close hygiene (run_longrun except//tmp, scratch cleanup) and reconcile harness pin gen7/8
write_paths: orchestration/notes/joint-plan/V11-verdict.md, orchestration/units/V11-VERIFY.md (this file), orchestration/handoffs/V11-VERIFY.json
not_reproduced: (none claimed-reproduced-failed; all 14 items reproduced except #1 and hygiene subclaims)
overstated: (a) 'bodies namespaced per fixture' — bare-ref _BODIES still collides in fallback path; (b) 'reset_bodies called per fixture' — zero callers; (c) hygiene 'except//tmp → 0 in four changed modules' — run_longrun.py has 6/2, scratch not empty
unverified: gate 0.1 acc.2–4 closure, gate 0.4, launch contract / PIN_EXPECTED_GENERATION gen7→8 reconcile, cap headroom; no model/network runs done (per constraints)
tool_calls: ~40 probes (read, grep, python heredocs, pytest 29 passed)
bound: read-only except declared write_paths; pytest only via .venv/bin/python; no network/model/subagents
