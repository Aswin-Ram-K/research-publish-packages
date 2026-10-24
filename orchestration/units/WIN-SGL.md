# WIN-SGL — the SGLang pager/flag space (page_size 64 / 128, chunked-prefix-cache)

**Unit:** `WIN-SGL` · engine = the SGLang endpoint on `gx10-163b` (`192.168.2.168:8012`).
**One purpose:** characterise the pager/flag space of the live SGLang build by running three
configurations sequentially and measuring each identically.

## Bound

| Bound | Value |
|---|---|
| live model requests, all three configs | **1,800** (allocated `min(900, 1800 - spent)` per config) |
| wall clock per variant launch | health poll ≤ 900 s |
| variants | 3 (`S1`, `S2`, `S3`), strictly sequential |
| `S3` attempts | **1** (a rejection is a result) |

## Configurations

| id | flag | what it asks |
|---|---|---|
| `S0` | none (live: `--page-size 1`) | baseline, **not re-measured here** — the existing `cells/G3` 888 rows |
| `S1` | `--page-size 64` | does the cache grid move when the pager is aligned to the 64-token state chunk? |
| `S2` | `--page-size 128` | is 64 the granularity or a point on a curve? |
| `S3` | `--enable-chunked-prefix-cache` | documented DeepSeek/MLA-only; one attempt, verbatim error if rejected |

## Write paths

```
experiments/context-cache/cells/WIN-SGL/**      rows.jsonl, analysis.json, launch_variant.py,
                                                win_sgl_cell.py, win_sgl_analyze.py, run_unit.py, logs/
state/config/occamy-inspect-pre.json            pre-change capture of the live container
state/config/S0-server-info.json                pre-change /get_server_info
state/config/occamy-restore-baseline.json       production snapshot the restore is compared to
state/config/S1|S2|S3-server-info.json          per-configuration /get_server_info
experiments/context-cache/.occamy.lock          held for the whole battery
orchestration/units/WIN-SGL.md, orchestration/handoffs/WIN-SGL.json
```

## Method

1. **Pre-state** — `docker inspect` of the live container and `/get_server_info`, captured before
   anything moves (`state/config/occamy-inspect-pre.json`, `state/config/S0-server-info.json`).
2. **Variant build** — `launch_variant.py` re-issues the inspected spec (image digest,
   `Config.Cmd`, `Config.Env`, both binds, `ShmSize`, `IpcMode`, GPU request, `--memory`, port)
   with only the target flag added; no 50-flag command is hand-typed.
3. **Health** — bounded serial poll (`/health` 200, container not `exited/absent`), ≤900 s.
4. **Capture** — that configuration's `/get_server_info` → `state/config/<id>-server-info.json`
   (its sha256 is the row's `config_sha256`).
5. **Measure, identical to S0** — the G3 battery verbatim: `corpora/endtoend.json` scenario 0, the
   same preamble/turn texts, depths `32k`/`64k` (74/148 turns), arms `R`/`A`/`C`/`H`, the same
   fixed salts (`make_salt(3201..3204)`), `keep_last=2`, `max_tokens=4`, `temperature 0`, one
   request in flight, `.occamy.lock` held for the whole battery. Because the salts and the chain
   construction are identical, every prompt is **byte-identical to its S0 row** — the cross-config
   comparison is paired, not merely similar.
6. **Grid probe** — four targets spaced 64 tokens apart, three byte-identical sends each
   (`cold`/`rep1`/`rep2`); the spacing makes the quotient parity alternate, so two of the four
   separate a 64-token grid from a 128-token grid for any constant template offset.
7. **Restore** — in a `try/finally` for every configuration: remove the variant, start production,
   `/health` 200, `/get_server_info` compared to the snapshot on the restore keys, verdict written
   to `logs/<id>-restore-verify.json` **even on failure**.

## Measured facts that change the card's assumptions (evidence, not preference)

1. **The engine is owned by a systemd USER unit, not by a bare container.**
   `systemctl is-active gx10-occamy-nvfp4.service` (system scope) → `inactive` — that is the unit
   the card looked at. `systemctl --user is-active` → `active`; the unit's `ExecStart` is the
   `docker run --rm --init --name gx10-occamy-nvfp4 … --publish 192.168.2.168:8012:30000` whose
   process tree hangs off `systemd --user`, `Restart=on-failure`, `NRestarts=3`,
   `ActiveEnterTimestamp=Fri 2026-10-23 00:04:30 CDT`.
2. **`docker stop` cannot be used on production, and `docker start` cannot restore it.**
   `HostConfig.AutoRemove=true` (`--rm`), measured on a throwaway container from the same image:
   after `docker stop` the container id list was **empty** — the container is removed. And a
   container-level stop does not hold the port: the unit restarts `ExecStart` within ~1 s
   (observed: stop at 05:04:04Z, new container created 05:04:30Z).
   The control surface is therefore `systemctl --user stop|start gx10-occamy-nvfp4.service`.
   This is a deviation from the card's "do not touch systemd": the card's instruction was based on
   the inactive *system* unit, and following it literally makes the unit impossible.
3. **`token_capacity` is re-profiled at every start and is not a configuration key.**
   An unchanged configuration came back with `max_total_num_tokens` 1,306,681 → 1,644,272
   (+25.8 %) on the first restart. The restore gate therefore requires the *config* keys
   (`page_size`, `mamba_radix_cache_strategy`, `mem_fraction_static`,
   `disable_chunked_prefix_cache`) to match exactly and **reports** the capacity with its delta.

## Kill conditions

- variant unhealthy after 900 s → capture `docker logs --tail 40` verbatim, restore, mark `partial`;
- `S3` rejected by the arg parser → one attempt, verbatim error, no retry;
- 3 consecutive wire failures inside the cell → abort with the rows already written;
- request bound reached → stop, report `partial` naming what was skipped.

## Deliverables

`cells/WIN-SGL/{rows.jsonl, analysis.json, launch_variant.py, win_sgl_cell.py,
win_sgl_analyze.py, run_unit.py, logs/}`, `state/config/*` captures above,
`orchestration/handoffs/WIN-SGL.json`.
