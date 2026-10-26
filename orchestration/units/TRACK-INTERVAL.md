# TRACK-INTERVAL — unit card and result

**Objective.** Measure whether `--mamba-track-interval` (256 default / 128 / 64) moves the
64-token cache grid, the per-prompt-arm uncached cost, or the capacity of production occamy.

**Hard bound.** 45 tool calls, 1,300 live requests. Used: 45 calls, 1109 requests.

**Write paths.** `experiments/context-cache/cells/TRACK-INTERVAL/**`, `state/config/track-*.json`,
`docs/serving-options/TRACK-INTERVAL.md`, `orchestration/handoffs/TRACK-INTERVAL.json`,
`orchestration/units/TRACK-INTERVAL.md`.

**Procedure.** Hold `experiments/context-cache/.occamy.lock`; per interval: stop the systemd user
unit (the container is `--rm`, so a stop removes it) -> `docker create/start` a variant built from
`state/config/occamy-inspect-pre.json` with only `--mamba-track-interval` changed -> health ->
`/get_server_info` -> the PROMPT-O1 cell (5 arms x 71 turns) -> 1.54x capacity pressure ->
drop the variant -> `systemctl --user start` production -> verify the six baseline keys + 256.

**Result.** Grid 64 at all three intervals (0 off-grid of 1,065 rows); no cross-interval delta
excludes zero (A -4.51 [-12.33, 3.31] at 64); capacity flat (1,514,033 / 1,512,903 / 1,512,950)
with the pressure window at 2 / 6 / 7 resident 100k documents. Recommendation: keep 256.

**Deviations.** Two harness restarts killed the first capacity pass (its probe overran the 131072
context: hex filler is ~1.15 chars/token, so the 4-chars/token estimate built a 343k-token
document -> HTTP 400) and one `save()` was truncated by a kill; the probe was rebuilt as an
atomic, resumable step driver (`cap_step.py`) and the capacity passes were re-run. Production was
restored and verified after every arm and at the end.
