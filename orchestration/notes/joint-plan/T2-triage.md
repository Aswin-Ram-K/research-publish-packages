# T2 triage — wave attribution

Wave write set (union of G1–G5): experiments/ptr-engine/longrun/tasks-v6/LR-*.v9.json; check_wall_reachability.py; score_longrun.py; grade_v5.py; run_longrun.py; analyze_stats.py; tools/run_a_star.py; ptr_engine/{outcomes,fetch_batch,resume}.py; tests/test_batch_resume_vocab.py; orchestration/handoffs/G1-FIXTURE.json, G3-RUNNER.json (G4 has no write_paths).

Suites run: ptr-engine 41F/369P; longrun 51F (50 repeat-identity + 1 thinking-flag) + 1 collection ERROR; root 44F/1505P + 10E.

Buckets: wave-caused ~117 (41 ptr + 50 longrun repeat-identity + ~26 root); not wave-caused ~31 (env graphify/venv path, stale report2.json, harness-map citations, ledger-delta format, thinking-flag, launcher stale vector); undetermined 2 (g5_fanout_attribution, r2_opt_sim2).

verdict_semantics collection error: RuntimeError exit-code partition drift — exit code 14 (EXIT_CAPGATE_UNRECORDED) in exit_codes.EXIT_TABLE but unclassified in verdict_semantics (MEASURING/REFUSING). Not caused by G5 modules; pre-existing partition gap.

Blocks gen-7: repeat-identity guard failures (ptr+longrun), run_a_star pin/harness gen mismatch, era_b grade_v5 hash, orchestration handoff G4-CAP schema. Unrelated plumbing: graphify binary/venv path, stale report2.json, harness-map citations, ledger delta format, thinking-flag, launcher stale budget vector.

Secondary reference not run (HEAD already dirty; labelled unreliable per constraints).
Scratch dir deleted.
