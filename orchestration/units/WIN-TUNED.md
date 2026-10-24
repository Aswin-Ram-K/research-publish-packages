# WIN-TUNED — eviction policy under pressure: `slru` vs the production `lru`

**Unit:** `WIN-TUNED` · engine = the SGLang endpoint on `gx10-163b` (`192.168.2.168:8012`).
**One purpose:** answer one question on one protocol — *does `--radix-eviction-policy slru` beat
the production `lru` under KV pressure?* Production is not switched to anything.

## Bound

| Bound | Value |
|---|---|
| live model requests | **600** hard cap (variant battery + replay only; no calibration run) |
| wall clock | 120 minutes |
| launches | **2** (variant `wt-slru` + production restore); one extra config only if budget clearly allowed |
| health poll per launch | ≤ 900 s |
| `gx10-qwen9b` (`:8014`) | untouched; `/health` verified 200 at the end |

## What is already measured (not re-litigated)

| Dead end | Evidence |
|---|---|
| `page_size 64` | grid unchanged (gcd 64, 351/880 odd multiples of 64, 887/888 rows byte-identical), cost slightly worse (740.4 vs 725.75 unc/turn @32k) |
| `page_size 128` | grid moves to 128, cost worse (752.6) |
| `--enable-chunked-prefix-cache` | cannot start (`cells/WIN-SGL/logs/S3-startup-failure.log`) |
| vLLM on the same weights | ~3.1× SGLang's per-turn uncached cost |

Production config therefore stays as-is. The only untested lever with a mechanism is **eviction
policy**, and it only matters past capacity — which `M4-EVICT` made measurable.

## Write paths

```
experiments/context-cache/cells/TUNED/**        rows.jsonl, analysis.json, run.json, run_tuned.py,
                                                win_tuned_analyze.py, variant_server_info.json,
                                                step0-pre-diff.json, logs/
state/config/tuned-pre.json                     production /get_server_info, before the variant
state/config/tuned-restored.json                production /get_server_info, after restore
state/config/tuned-restore-diff.json            key-by-key restore gate
experiments/context-cache/.occamy.lock          held for the whole measurement
orchestration/units/WIN-TUNED.md, orchestration/handoffs/WIN-TUNED.json
```

## Method

1. **Step 0 — production intact.** `GET :8012/get_server_info` → `state/config/tuned-pre.json`,
   diffed against `state/config/occamy-restore-baseline.json` on `page_size`,
   `mamba_radix_cache_strategy`, `radix_eviction_policy`, `mem_fraction_static`,
   `kv_cache_dtype`, `max_mamba_cache_size` (plus capacity, reported not gated). If inconsistent,
   STOP and report a P0 — never "fix" it.
2. **Stop surface.** The live container is the `ExecStart` of the systemd **user** unit
   `gx10-occamy-nvfp4.service` and carries `HostConfig.AutoRemove=true`, so a container-level
   `docker stop` *deletes* it and `docker start` would have nothing to start (measured by
   `WIN-SGL`, `assumptions.stop_surface`). The unit is therefore stopped and started through its
   owning unit: `systemctl --user stop|start gx10-occamy-nvfp4.service`. The container is never
   `rm`-ed by this unit.
3. **Variant build.** `cells/WIN-SGL/launch_variant.py` is imported, not re-written: it rebuilds
   the spec from `state/config/occamy-inspect-pre.json` (image digest, `Config.Cmd`,
   `Config.Env`, both binds, `ShmSize`, `IpcMode`, GPU request, `--memory`, published port) and
   applies exactly one argv change — `--radix-eviction-policy slru` (2 tokens added, 51 → 53).
   Variant container name `wt-slru`, `AutoRemove=false` so a startup failure keeps its logs.
4. **Health** — bounded poll (`/health` 200, container not `exited/absent`), ≤900 s. On failure:
   `docker logs wt-slru | tail -40` verbatim, restore, report — a refused flag is a result.
5. **Measure (M4's protocol).** Reuse `cells/M4/corpus.jsonl` (same 300 salted ~8.6k-token
   documents, identical `prompt_sha256`), push one document per request until cumulative
   **measured** `prompt_tokens` ≥ `1.5 ×` this variant's own `token_capacity` (read from the
   variant's `/get_server_info`, never M4's 1,620,892), then replay oldest 10 / middle 10 /
   newest 10 in M4's order (newest→middle→oldest). `temperature 0`, `max_tokens 4`, one request
   in flight, `.occamy.lock` held.
6. **Compare band by band** against `cells/M4/analysis.json` `phase_r.bands` mean cached
   fraction; better/worse at a 0.05 absolute margin, otherwise *indistinguishable*. Capacity and
   pressure-ratio normalisation reported with the numbers.
7. **Restore (mandatory, failure path included).** `docker rm -f wt-slru` →
   `systemctl --user start gx10-occamy-nvfp4.service` → `/health` 200 → `/v1/models` returns
   `occamy-1.0` with `max_model_len 131072` → re-capture `/get_server_info` and diff against
   `tuned-pre.json`. Every config key must match except uptime, counters and timestamps.
   Two attempts, then a loud P0 and stop.

## Result — null

The flag is accepted (`ServerArgs.radix_eviction_policy='slru'`, `/get_server_info` reports `slru`),
the battery ran on 1,480,094 of the variant's own tokens (2,227,665 pressure = 1.5051×, 259 documents),
and the replay profile is **indistinguishable from lru in every band**:

| band (positions of 259) | slru mean cached fraction | lru (M4, 283 docs) | delta | verdict |
|---|---|---|---|---|
| oldest (1–10) | 0.000 | 0.000 | 0.000 | indistinguishable |
| middle (125–134) | 0.000 | 0.000 | 0.000 | indistinguishable |
| newest (250–259) | 0.9961 | 0.9970 | −0.0009 | indistinguishable |

289 requests, 0 failures; restore 9/9 config keys equal, `/health` 200, `occamy-1.0`
`max_model_len 131072`. The null is the mechanistically expected one: the protocol submits each
document exactly **once** before replaying it, so a segmented policy has no re-access to promote
anything on, and a scan degenerates slru to lru. Answer: **the production policy is already the right
one for this workload** — not a proof that slru can never win, but that it does not win here.

See `orchestration/handoffs/WIN-TUNED.json` and `experiments/context-cache/cells/TUNED/analysis.json`.

## Correction note (FIX-VXSTACK)

- TUNED's delivered replay rows follow the G3 64-token law (10/30 exact, 19 rows at cached=0); `page_size=1` in `variant_server_info.json` is reconciled with that grid through SGLang FLA `cache_chunk_size=64`. TUNED is not a no-grid baseline.
- All 289 TUNED rows now carry `"stack": "tuned"` and `"config_id": "TUNED"`; `win_tuned_analyze.py` rejects rows lacking either field.
- TUNED has no in-cell G0; its result is downgraded accordingly. S1/S2 likewise have no in-cell G0 (only the predating U2 gate exists).
