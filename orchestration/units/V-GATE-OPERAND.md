# UNIT V-GATE-OPERAND

**Status:** partial · **Requests:** 0 · **Bound:** 30 tool calls · **Final pin:**
`experiments/ptr-engine/longrun/cell.py` sha256
`24627d7b648262f901825e87459b41a3ce7185539e46ccd3dda01c3002233253` (104,869 B,
mtime 12:23:43) · **HEAD:** `f17663d1fed0162a7dc3c5a0a58d372c710974c3`

## Objective
Independent, offline attack on `GATE-OPERAND-VALIDATION` with my own hostile table and
my own spawn oracle; verify or refute each claim line by line; record a verdict.

## What was attacked
1. **Pin** — claimed `6b0ca83a…`; observed `0136052e…` (12:16:20) then `24627d7b…`
   (12:23:43). Re-pinned twice; all mutation in `/tmp` copies; sha identical before and
   after the final probe.
2. **Fresh hostile set** — 246 rows (132 argv, 36 artefact, 114 unit), including
   `0`, `-0.0`, `-1`, `-48`, `1e-9`, `1e308`, `inf`, `-inf`, `nan`, `"0"`, `""`, `"abc"`,
   `None`, `True`/`False`, a 10⁶-digit integer string, `" 5 "`, `"5_0"`, `5.0000001`,
   plus permissive siblings (`--max-wall 100000`) so only the probed operand can refuse.
3. **Spawn oracle** — `subprocess.Popen` patched before `cell` import; runner stub;
   positive control reached the runner once. 100/100 hostile end-to-end rows refused
   with 0 live spawns; 0 admitted (two table rows of mine, `budget.reserve 0/-0.0`, are
   legal and were reclassified after measurement).
4. **Assertion integrity** — author's F-cases assert the refusal (exit code compared,
   `self.assertEqual(want, actual)`, `live_spawns == 0`, refusal text non-empty). Their
   spawn counter is a surrogate (`cell._run`), not the live primitive
   (`subprocess.run`, `cell.py:1501`) — recorded as overstated, not as a bypass.
5. **Revert-one-validator** — `/tmp` copy `--turn-wall-cap lo=1` → `lo=0`: 9/9 OK
   becomes FAILED (4), including `F8: expected exit 8, got 1`. The suite bites.
6. **The silent seam** — `test_guards` 1 passed and `test_projection_calibration`
   1 passed, fixed by a declared `--hypothesis H2` in those files at 11:07 (before this
   card) and by `run_longrun.py`'s concurrent edit settling; no validation weakened.
7. **No regression** — `test_gate_operand_validation` 9/9, `test_cell_gates` 15/15,
   `test_gate_override` 7/7, `test_exit_codes` 16/16, `test_cell` 7/7,
   `test_claim_mode` 21/21, `test_row_attribution` 5 passed,
   `test_projection_modes` 8 passed.
8. **Nothing relaxed** — bounds, thresholds, G3 anchors and exit codes unchanged.

## Verdict
`partial`: the gate holds on the current file and every hostile value is refused with
zero spawns, but the pinned digest is stale (the file moved twice) and the "0 live
spawns" claim rests on an oracle that cannot observe the live spawn primitive. The
"before" column is an unexecutable reconstruction.

## Artifacts
`experiments/ptr-engine/measure/V-GATE-OPERAND.json` · `docs/V-GATE-OPERAND.md` ·
`orchestration/handoffs/V-GATE-OPERAND.json` ·
`orchestration/journals/V-GATE-OPERAND.jsonl`
