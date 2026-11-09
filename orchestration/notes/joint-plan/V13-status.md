# V13 STATUS

1. Suite — `pytest ... 5 files`: 30 passed, 0 failed (0.62s). PASS.
2. Launch contract — `launch_contract_diff.py --check`: exit 0; 14 AGREES, 7 STALE-BY-DESIGN, 0 DISAGREES. PASS.
3. Gate 0.1 — composite verified_success=False on pos-full (control_kind=synthetic-abstention); no positive control exists. Reason: scorer exact-match vs fixture answer_marker contract are mutually exclusive; no recorded run has a complete working set. OPEN.
4. Gate 0.4 — identity check PASS (offline check(captured,captured)). argv/image=UNOBSERVABLE (tried GET /server_info 200 + GET /health 200); model_snapshot_digest=fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652. PASS.
5. Arms C/D — model-free run: C turn5 masked_rows=2 (mask_output called 2x, agreeing); D turn1 fetch_budget_tokens=1024, tokenizer_calls=0, tool_call_id=null, masked_rows=0, fetch_rows=1. PASS.
6. Fixtures — check_pointer_fixtures PT-01/02/03: all OK, 4 outcomes each, 4 checkpoints each. Walls: PT-01=4312, PT-02=4403, PT-03=4221, basis=DERIVED_FROM_PT_OWN_BYTES. PASS.
7. Hygiene — grep 'except Exception|/tmp' in arm_cd.py, pointer_table.py, fetch_tool.py, fetch_batch.py: empty; no experiments/ptr-engine/state/previews/ directory. PASS.
8. Cap — PROJECT_QUOTA=12094 (cell.py:141); spent=2591 (row-store count); headroom=9503; shortfall vs 12094.2 priced core=0.2. PASS (with 0.2 shortfall).

overall: ready for a funded control run: no (gate 0.1 open; cap 0.2 short of priced core).
