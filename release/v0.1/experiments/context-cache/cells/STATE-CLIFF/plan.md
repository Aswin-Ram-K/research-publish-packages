# STATE-CLIFF — design for the `max_mamba_cache_size` sweep (64 → 48 → 32 → 16)

**Status: PREPARED, NOT APPROVED TO EXECUTE.** This plan and its companion
`sweep.py` were written offline by unit `STATE-CLIFF-PLAN`. **Nothing was
restarted, no container was created or stopped, no request was sent to the
GX10, and no live endpoint was called while producing these files.**
The operator has approved *preparation only*; execution of any rung requires a
separate approval.

## 1. Question the sweep answers

At `max_mamba_cache_size = 64` the server under 1.50× pressure held only
**30–31 resident documents** (258,035–266,636 tokens = 15.9–16.5 % of the
1,620,892-token declared capacity), i.e. the binding constraint is the mamba
state-slot budget, not the KV pool (M4-EVICT, `experiments/context-cache/cells/M4/`).
That number is a **single-point measurement**. Sweeping the slot budget
`64 → 48 → 32 → 16` turns it into the curve the paper needs:
`resident_docs / resident_tokens / resident_ratio` as a function of
`max_mamba_cache_size`, plus per-band (oldest/middle/newest) hit rates at each
point.

## 2. The ladder

| rung | `max_mamba_cache_size` | role |
|---|---|---|
| 0 | 64 | control — must reproduce the published single point (30–31 docs) |
| 1 | 48 | first curve point below control |
| 2 | 32 | mid curve |
| 3 | 16 | deep curve; expected to bind hardest |

**One point per restart cycle.** A rung is never changed without a full
stop → variant-run → measure → restore cycle (§4). Rungs are executed in
ladder order; the control rung (64) is executed first and its failure aborts
the sweep.

## 3. Box facts (production stop / restore)

- Production is the Docker container **`gx10-occamy-nvfp4`**, image
  `sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7`,
  published port `8012->30000`, `restart=no`.
- **Production is stopped, never removed.** `docker stop` / `docker start`
  only; `docker rm` is reserved for the *variant* container of the current
  rung, which is removed after measurement.
- Restore = `docker start gx10-occamy-nvfp4`, then the health gate, then the
  six-key restore proof (§5). The next rung does not start until the restore
  proof passes.
- `token_capacity` is **informational only**: the pool is re-profiled on every
  start (baseline 1,644,272; measured 1,620,892 at M4; WIN-SGL observed
  1,306,681 → 1,644,272, +25.8 %, on an *unchanged* configuration). A moved
  `token_capacity` after restore is not a restore failure.

## 4. Per-rung sequence (exactly what `sweep.py` emits)

All commands below are printed verbatim by
`python3 experiments/context-cache/cells/STATE-CLIFF/sweep.py --dry-run --mamba-cache-size <N> --port <P>`
and executed only when `--execute` is passed (never in this card).

0. **Offline pre-flight (no network, no docker):**
   - `state/config/occamy-restore-baseline.json` exists and carries all six
     restore keys with production values (§5); otherwise **refuse** (exit 2).
   - ladder membership: `<N> ∈ {64, 48, 32, 16}`; `<P>` a free high port
     (`<P> != 8012`).
   - `docker inspect gx10-occamy-nvfp4` gate: container exists,
     `AutoRemove=false`, `RestartPolicy.Name=no`. If the live container is not
     stop-safe, **abort with instructions** (rewrite stop-safe per the
     WIN-SGL `prepare_production` recipe under operator approval) — never
     improvise a production rewrite mid-sweep.
   - `python3 experiments/context-cache/cells/M4/battery.py --help` gate: the
     M4 battery must expose a base-URL argument (see §8, assumption A2);
     otherwise abort and record.
1. **Stop production (never removed):**
   `docker stop -t 60 gx10-occamy-nvfp4`
2. **Launch the rung variant** (binds/shm/env derived from step-0 inspect so
   the variant is spec-identical apart from the flag and the host port):
   `docker run -d --name gx10-occamy-sweep-<N> --restart no --gpus all -p <P>:30000 -e HF_HUB_OFFLINE=1 <ABSOLUTE_RO_BINDS_FROM_INSPECT> sha256:72457f09… --max-mamba-cache-size=<N>`
   Every bind is **absolute and `:ro`** (§7).
3. **Health gate:** poll `http://127.0.0.1:<P>/health` every 5 s, deadline
   **900 s**. Exited/dead/absent container or deadline → abort to step 6
   (restore) with `status=failed`.
4. **Per-config capture:** `curl -sf http://127.0.0.1:<P>/get_server_info -o experiments/context-cache/cells/STATE-CLIFF/rung-<N>/server_info.json`.
   **Readback gate:** `max_mamba_cache_size` in that document must equal `<N>`
   (and `page_size` must still be 1); a mismatch means the flag was rejected —
   abort, do not measure (assumption A1 is then falsified).
5. **Measure (M4 protocol reused):** wait ≤300 s for
   `experiments/context-cache/.occamy.lock` to be **free**, then hand it to
   the M4 battery (the battery holds it for the whole batch; the sweep must
   not hold it while the battery runs or the two flocks deadlock), read
   `capacity` from `internal_states[0].memory_usage.token_capacity`, then run the M4
   pressure generator at **1.50× the measured capacity** with the salted
   deterministic corpus (`cells/M4/corpus.py`, ≤300 docs), then the replay
   phases. Record per rung:
   - `capacity`
   - `resident_docs`, `resident_tokens`, `resident_ratio` (= resident_tokens /
     capacity) — derived exactly as M4-EVICT derived them (newest-first replay:
     consecutive newest hits define the resident window; cumulative estimated
     tokens of that window give `resident_tokens`)
   - **band hit rates**: oldest-10 / middle-10 / newest-10 replay hits
   - observed pressure total, doc count at onset, request counts, wall time
6. **Stop and remove the variant:**
   `docker stop -t 60 gx10-occamy-sweep-<N> && docker rm gx10-occamy-sweep-<N>`
7. **Restore production:** `docker start gx10-occamy-nvfp4`
8. **Health gate again** on `http://127.0.0.1:8012/health`, same 900 s bound.
9. **Restore proof (§5).** Pass → next rung. Fail → **loud failure**: write
   `restore-proof-FAILED.json` into the rung dir, stop the sweep, hand back to
   the operator. Never continue the ladder on a failed restore.

Output layout: `experiments/context-cache/cells/STATE-CLIFF/rung-<N>/`
holding `server_info.json` (step 4), `measure.json` + the M4 battery rows
(step 5), and the restore-proof record (step 9). The curve is assembled from
`measure.json` across rungs; no paper file is written by this cell.

## 5. Restore proof (six keys)

After step 8, `GET /get_server_info` must match
`state/config/occamy-restore-baseline.json` **exactly** on:

| key | required value |
|---|---|
| `page_size` | `1` |
| `mamba_radix_cache_strategy` | `"extra_buffer"` |
| `radix_eviction_policy` | `"lru"` |
| `mem_fraction_static` | `0.45` |
| `kv_cache_dtype` | `"fp8_e4m3"` |
| `max_mamba_cache_size` | `64` |

Anything else — key absent, value moved, document unreadable — is a failed
restore. `token_capacity` is deliberately **not** among them (§3).

## 6. Measurement details (reused, not reinvented)

- Protocol: M4-EVICT (`orchestration/units/M4-EVICT.md`) — Phase P pressure at
  1.50× capacity (M4 measured 2,434,133 tokens over 283 docs = 1.5017× at the
  64 rung), Phase R replay oldest/middle/newest 10, Phase D note-probe
  (informational).
- Hard bounds carried over: ≤600 battery requests, ≤300 docs, 90 min, three
  consecutive request failures → stop and report `partial`.
- The sweep adds **no new request type**; it only changes the server knob and
  re-runs the same generator, so rung-to-rung deltas are attributable to
  `max_mamba_cache_size` alone (all other knobs are held at baseline values by
  the restore proof between rungs).

## 7. Failure modes already seen (guards baked in)

1. **`disabling` a container is not removal** — the systemd `--user` unit
   (`gx10-occamy-nvfp4.service`, `Restart=on-failure`) recreates a container
   that carries `--rm`, and a container-level stop cannot hold the port free
   (measured by WIN-SGL). Guard: step-0 inspect gate requires
   `AutoRemove=false` + `RestartPolicy.Name=no` *before* any `docker stop`;
   if the unit is ever armed again during the sweep, abort.
2. **A literal `~` under `sudo` resolves to `/root`** — every path in every
   emitted command is absolute (workspace paths under
   `<workspace>…`), no `~`, no `$HOME` in binds.
3. **`HF_HUB_OFFLINE=1` kills a container that tries to download** — the
   variant always carries `-e HF_HUB_OFFLINE=1`, and every bind is absolute
   and `:ro`, so the rung container cannot reach for the network or mutate the
   cache. If the variant exits during health-poll, capture its `docker logs`
   tail and report; do not retry with network enabled.

## 8. Assumptions (recorded, conservative)

- **A1 — flag spelling.** No repository script ever passed this flag (grep
  `max-mamba` finds nothing), so `--max-mamba-cache-size=<N>` is *inferred*
  from the proven convention `page_size` ↔ `--page-size`
  (`cells/WIN-SGL/run_unit.py:79`). The step-4 readback gate is the authority:
  if the server does not report `<N>`, the sweep stops before measuring.
- **A2 — M4 battery CLI.** `battery.py`'s argument list was not read offline.
  The step-0 `--help` gate checks for a base-URL flag; if the battery hard-codes
  `127.0.0.1:8012`, the executor must point it at the variant port by editing
  `M4_MEASURE_ARGV` in `sweep.py` (one line, recorded in the handoff) before
  the first live rung.
- **A3 — variant spec.** Binds/shm/ulimits are copied from the production
  `docker inspect` at execute time (this card could not inspect the box), so
  the only intended deltas are `--max-mamba-cache-size=<N>` and the host port.

## 9. Boundaries of this card

Writes are confined to `experiments/context-cache/cells/STATE-CLIFF/**`,
`orchestration/handoffs/STATE-CLIFF-PLAN.json`, and
`orchestration/units/STATE-CLIFF-PLAN.md`. No `papers/**`, no tests, no other
cell is touched; no ssh, no `docker stop/start/run`, no HTTP request to the
GX10 was made to produce this plan. Execution happens only after an operator
approves the live sweep, rung by rung.
