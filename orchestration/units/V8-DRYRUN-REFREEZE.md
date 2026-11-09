# V8-DRYRUN-REFREEZE

**Purpose:** re-freeze the v8 dry-run manifests so grid provenance matches the runner
(`design_cap_tokens=10616` from `wall_tokens_by_arm`, not the dead top-level 3838).
**Bound:** ≤16 tool calls, 0 requests. **Status:** done (16 calls, 0 requests).

**Write paths:** `longrun/manifests/` (+`archive/pre-wallkey/`), `measure/V8-DRYRUN-REFREEZE.json`,
`longrun/experiments/ptr-engine/longrun/tests/test_manifest_cap_consistency.py`, `docs/V8-DRYRUN-REFREEZE.md`,
`orchestration/units|handoffs|journals/V8-DRYRUN-REFREEZE.*`.

**Result:** four manifests re-frozen at 10616; four stale ones archived (3×3838, 1×65536
mislabeled); dry run exits 0 with all three gates allow; guard red→green proven.
