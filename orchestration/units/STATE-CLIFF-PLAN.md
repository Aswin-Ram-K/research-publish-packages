# STATE-CLIFF-PLAN — unit card

**Status:** done · permission workspace-write · bound 20 tool calls · offline only.
**Contract:** task-board card `ea91fa00-62cf-4295-a5a7-278f08846291`
"STATE-CLIFF-PLAN — prepare the max_mamba_cache_size 64/48/32/16 sweep
without touching the box". Automated session: never asks questions; GX10
contact forbidden (operator approved preparation only).

## Objective
Turn the state-cache cliff finding (1.50x pressure → resident 30–31 docs =
15.9–16.5% of capacity, bound `max_mamba_cache_size = 64`) into an executable
sweep ladder 64→48→32→16 — WITHOUT any live contact.

## Deliverables (declared write paths)
- `experiments/context-cache/cells/STATE-CLIFF/plan.md` — design: ladder,
  stop/never-remove mechanics, six-key restore proof, health gates, M4 reuse,
  failure-mode guards, assumptions A1–A5.
- `experiments/context-cache/cells/STATE-CLIFF/sweep.py` — dry-run-first,
  `--mamba-cache-size` + `--port`, pre-flight refusal (exit 2), execute only
  under `--execute`, restore proof on the way back (exit 3 on mismatch).
- `orchestration/units/STATE-CLIFF-PLAN.md` (this file),
  `orchestration/handoffs/STATE-CLIFF-PLAN.json`.

## Proofs (offline)
1. `python3 experiments/context-cache/cells/STATE-CLIFF/sweep.py --dry-run
   --mamba-cache-size 48 --port 8021` → exit 0, full 12-step command
   sequence, "DRY RUN complete — nothing executed."
2. `python3 -c "import json;print(json.load(open('state/config/
   ocamy-restore-baseline.json')).keys())"` → exit 0, all six restore keys
   present: `page_size=1`, `mamba_radix_cache_strategy="extra_buffer"`,
   `radix_eviction_policy="lru"`, `mem_fraction_static=0.45`,
   `kv_cache_dtype="fp8_e4m3"`, `max_mamba_cache_size=64`.

## Boundaries honoured
No ssh, no `docker stop/run/start`, no HTTP request to :8012 or any port,
no service restart, no writes outside the four declared paths (no
papers/**, no tests, no other cell). Nothing was executed against the box.

## Assumptions (conservative defaults, recorded)
- A1 flag spelling `--max-mamba-cache-size=<N>` is inferred (only proven
  convention: `page_size` ↔ `--page-size`); readback gate is authority.
- A2 `battery.py` CLI unverified offline; execute gates on `--help`.
- A3 variant binds/shm come from `docker inspect` at execute, forced
  absolute + `:ro`; A4 sweep waits for `.occamy.lock` free but does not hold
  it across the battery (flock deadlock); A5 `token_capacity` informational.
