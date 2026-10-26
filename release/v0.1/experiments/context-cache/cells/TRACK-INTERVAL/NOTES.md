# TRACK-INTERVAL — what differs from `cells/PROMPT-O1/prompt_o1_cell.py`

Each `t<N>/cell.py` is a byte copy of `cells/PROMPT-O1/prompt_o1_cell.py` with
**only** these changes (the prompt renderers, salts, arms, budgets, request
loop and analysis are untouched, so the arms stay comparable with PROMPT-O1):

| line | PROMPT-O1 | here |
|---|---|---|
| `REPO` | `HERE.parents[3]` | `HERE.parents[4]` (one extra dir level) |
| `CELL` | `"PROMPT-O1"` | `"TRACK-T{N}"` |
| `HANDOFF_PATH` | `orchestration/handoffs/<CELL>.json` | `HERE/handoff.json` (write-path rule) |
| `UNIT_PATH` | `orchestration/units/<CELL>.md` | `HERE/unit.md` |
| `load_setup` | `setups.O1` | same dict, but `config_id`/`config_sha256` from `TRACK_CONFIG_*` env (per-arm `/get_server_info`) |
| `acquire_lock`/`release_lock` | flock the occamy lock | no-op when `TRACK_LOCK_HELD=1`: the driver holds it for the whole card |

`run_track.py` is the driver (lock, launch, G0 warm-up, 5×71, capacity probe,
restore).  `capacity_only.py` is the corrected capacity pass (the first pass's
probe built a 343k-token document and got HTTP 400).
