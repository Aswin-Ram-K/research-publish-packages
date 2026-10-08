# V8B — independent verifier for U8.5

**Purpose:** verify U8.5 (three honesty/cleanliness fixes to `resextract run`). Fixes nothing.
**Bound:** ≤30 tool calls, ≤2 live `run` invocations, 0 LLM calls, 1 Occamy probe.
**Write paths:** `orchestration/VERDICTS.md`, `orchestration/units/V8B.md`, `orchestration/handoffs/V8B.json`, `state/logs/V8B*`, `state/verify/V8B/**`.
**Reverts:** only `src/resextract/run.py`, last, sha-proven backup.
**Checks:** C1 suite · C2 plan/run coupling adversarial · C3 sidecar unit-level · C4 status fields · C5 v4/v3 blocker · C6 red->green · C7 honesty · C8 containment.

## Result (V8B, independent verifier) — overall PASS

- **C1** 25 passed (full purge; re-run post-revert 25). `run.py`/`test_run.py` untracked ⇒ 0 deletions
  enumerated, not diff-proven.
- **C2** PASS — `_reuse_candidate` is the single decision function (run.py:686/709) fed to both the dry plan
  (1444) and the real run (1447); 10 adversarial scenarios all matched on mode/nodes/edges/sha256. Minor:
  `planned_out` names the wrong build artifact path; a 0-byte/corrupt graph is reused as `ok, nodes=0`. Only
  divergence is an fs change between invocations (inherent). Dry-writes-nothing: unit-level only.
- **C3** PASS — fresh copy `journal_mode=delete`, 13/13 rows (claim said 12), integrity ok, glob
  `["state.sqlite"]`; sidecars deleted only after `con.close()`; WAL copy checkpointed+kept with note.
- **C4** PASS — `ok`/`status` are properties, not stored fields; follow `exit_code` for 0/1/2/3; setattr and
  constructor kwargs both refused ⇒ cannot disagree.
- **C5** live run **exit 2**, 8/8 stages skipped, `window_sealed=false`; store sha unchanged v3.
  Judgement: **correct fail-fast**. Exit-1 shape pinned by `test_run.py:230`. Not reproduced live.
- **C6** both guards sha-proven red→green; release sha `18d8bc32…` matches.
- **C7** caveats named (unauditable tool/run overage, reasoned-not-demonstrated safety, Duval sweep bound).
- **C8** containment clean; store unmigrated v3 `459e16cc…`; Duval HEAD unchanged.
