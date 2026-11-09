# UNIT CANARY-GATE-DRYRUN — rehearse the canary's own argv against cell.py's three gates, offline

**Bound:** 18 tool calls; read-only rehearsal. **Autonomous:** no questions, zero requests.
**Write paths:** `orchestration/units/CANARY-GATE-DRYRUN.md` · `orchestration/handoffs/CANARY-GATE-DRYRUN.json` · `orchestration/journals/CANARY-GATE-DRYRUN.jsonl` · `experiments/ptr-engine/measure/CANARY-DRYRUN.json`.
**Not edited:** cell.py, run_longrun.py, run_a_star.py, analyze_stats.py, fixtures, rows/grades, thresholds, pages.

## Question
Does the canary argv from `orchestration/handoffs/CANARY-ARGV-WIRING.json` (`evidence.canary_argv`) pass G1/G2/G3 offline? The unpriced risk: G3 built to refuse *silence* might also refuse `smoke` (= claim none), exiting 12 before request 1.

## 1. Command rehearsed (exact wiring argv, `--dry-run` appended, nothing else changed)
```
/usr/bin/python3 experiments/ptr-engine/longrun/cell.py --arm pointer-stable \
  --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json \
  --turns 12 --reps 1 --thinking off --max-wall 600 --turn-wall-cap 180 \
  --runaway-turns 2 --budget 108 --hypothesis smoke --no-cell-handoff \
  --out-dir experiments/ptr-engine/measure \
  --endpoint http://192.168.2.168:8012/v1 --dry-run
```
`RC=0`. Launcher form:
```
python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --canary --budget 108 --cell 1 --dry-run
```
`RC=0`, line `RUN-A DRY cell 1 pointer-stable r1 rc=0 …`, `RUN-A DRY END cells=1 refused=0 requests=0 claim=smoke turns=12 max_wall=600`.

## 2. Gate verdicts (verbatim)
- **G1 allow** — `computed=1,142 requests limit=4,320 requests (cap 4,320 - reserve 0 - spent 1,128)` (launcher form with `--fetch-followup-allowance 2`: `computed=1,188`).
- **G2 WOULD-REFUSE** — `computed=720 s limit=600 s (--max-wall)`; operands `turns=12 projected_requests=12 projected_wall~=720s (cap-per-turn 180s -> worst case 2160s) cap=600s projected-turn-wall=60.0s source=artefact-mode thinking=off`.
- **G3 allow** — `computed=claim=none declared (smoke/plumbing) limit=no claim is made, so no PARM-1 n threshold applies`; `hypothesis=none (flag:--hypothesis (smoke)) thresholds={"basis": "a cell that declares claim=none makes no PARM-1 claim, so no n threshold applies; claim_mode.resolve_claim is the only resolver of that decision", "min_n": 0}`; short `G3 n=12 (smoke, non-comparable)`.
- Final line: `cell: EXIT 0 — dry run: 1 of 3 gate(s) would refuse; …nothing was sent`.

## 3. g3_allows_smoke = **true**
G3's allow-list is not `{H1,H2,H3}`: `validate_g3(..., smoke=claim.is_smoke)` (cell.py:1030,1408-1411) has a `smoke` branch setting `min_n=0`, and `claim_mode.smoke_prereg_verdict` supplies the verdict. No refusal text exists to quote. The `{H1,H2,H3}` worry was already closed by WIRE-CLAIM-MODE.

## 4. Offline proof (`sys.addaudithook`, wrapper recorded counts)
cell.py under audit: `{"socket_socket": 0, "socket_connect": 0, "getaddrinfo": 0, "spawn": 0, "fork": 0, "writes": [], "_rc": 0}` → **requests_sent 0, sockets 0, runner_launch 0**, and the dry run wrote **no** manifest (`writes: []`).
Launcher under audit: `{"socket_socket": 0, "socket_connect": 0, "getaddrinfo": 0, "spawn": 1, "_rc": 0}` — the single spawn is the `cell.py --dry-run` child itself; `run_longrun.py` (the runner) was never launched. Launcher side effects are in tempdir only (`/tmp/run-a-star-logs/cell01-pointer-stable-r1.log`, `/tmp/grid-shape-shim/runner_read_file.py`), not in the workspace.

## 5. Claim landing (where the analyser reads it)
Dry run writes no manifest, so the stamp was proved at the resolver and the row writer:
`resolve_claim("smoke") -> {'claim': 'none', 'comparison_eligible': False, 'mode': 'smoke', 'is_smoke': True}`; `resolve_claim("H2") -> {'claim': 'H2', 'comparison_eligible': True, 'mode': 'hypothesis'}`; `resolve_claim(None) -> ClaimRefusal code 12` (silence still refused — the original G3 purpose is intact).
Row stamp site: `run_longrun.py:1834-1836` writes `claim_mode.CLAIM_NONE` / `comparison_eligible: False` when no `cfg.claim`. Corroborated by the wiring handoff's stamped-row counts: canary `{('none', False)}` over 12 rows, grid `{('H2', True)}` over 12 rows.
Dry-run claim line verbatim: `claim=none comparison_eligible=False mode=smoke resolver=claim_mode.resolve_claim (one resolution per invocation)`.

## 6. Wall arithmetic at N=12
G2 bills `projected_requests × projected_turn_wall(thinking mode)`, **not** `× --turn-wall-cap`: `12 requests × 60.0 s/turn = 720 s`, against `--max-wall 600` → over by **120 s**. The live path uses the runner's `would_send_total` (12 for 1 arm × 1 rep × 12 turns), so the live cell would hit the identical number at `3b/7 projection` and exit **8**. **`--max-wall 600` is NOT enough for 12 turns at the calibrated 60 s/turn; the minimum is 720 s** (the wiring's `cell_argv` grid value of 2880 is ample). G1 and G3 both admit at N=12; only G2 refuses.

## FINDING
**The launch is BLOCKED — by G2 (projection), exit 8, not G3.** `--hypothesis smoke` passes G3 (`g3_allows_smoke: true`, claim=none, comparison_eligible=false); `--max-wall 600` cannot price 12 turns × 60 s = 720 s. Also: every recovery surface is green while G2 refuses — dry-run `RC=0`, launcher `refused=0`, `ready_to_launch: true` — because `cell.py`'s dry run returns 0 even when a gate would refuse, and callers must parse the `WOULD-REFUSE` line. Fix by passing `--max-wall >= 720` in `evidence.canary_argv` (do not shrink the projection).
