# Unit R2-VLLM-PREFLIGHT2 — read-only host preflight before the R2-VLLM cell re-run

**Status:** done (host state observed; one conclusion revised in-flight, see Findings)
**Hard bound:** 15 tool calls (used 11). Read-only host verbs only.
**Write paths (declared):**
- `experiments/context-cache/cells/R2-VLLM/logs/preflight2.json`
- `orchestration/units/R2-VLLM-PREFLIGHT2.md`
- `orchestration/handoffs/R2-VLLM-PREFLIGHT2.json`

## Purpose
The cell `experiments/context-cache/cells/R2-VLLM/` is being re-run after an instrument repair
(`logs/repair-offline.json`). The previous preflight unit died at its bound; the recorded facts were
inconclusive about the production engine `gx10-qwen9b` ("mid-cold-start, weights ~25%") and the
02:32Z reading `{"prod": 0, "occamy": 200, "var": 0}`. This unit establishes the live host state
without mutating anything, so the next unit can decide safely.

## Method
One batching policy: every ssh call carried many probes (see handoff `evidence.ssh_calls`).
Host: `zer0null@192.168.2.168` (`gx10-163b`).

Probes: `docker ps -a`, `docker inspect -f`, `docker logs --tail`, `docker events --since`,
`ss -ltn` / `ss -ltnp`, `curl -m 5` GET on `/health` and `/v1/models` only, `nvidia-smi --query-*`,
`ps -o pid,etime,args`.

## Findings
1. **`gx10-occamy-nvfp4` is UP and was never touched**: `running`, started `2026-10-23T07:58:48.66Z`,
   `Up 19 hours`, exit 0, not OOM-killed, restart count 0, `/health` **200** on `192.168.2.168:8012`.
   *(Probe note: `127.0.0.1:8012/health` returns `000` because the binding is `192.168.2.168:8012`,
   not loopback. The up-path is `http://192.168.2.168:8012`. Same applies to 8010.)*
2. **`gx10-qwen9b` (prod) is NOT up — it was cleanly stopped and replaced.** Sequence over
   ~02:29–02:46Z: prod start 02:32:51 (health 200 by 02:35:04, proven), prod killed 02:43:13,
   prod `die` 02:43:20 (`ExitCode 0`, `OOMKilled false`, `RestartCount 0`), and `r2v-a1` created and
   started at 02:43:21 on the same host port. Prod's `HostConfig.PortBindings` is now `{}` and nothing
   listens on 8014 for it.
   **Correction to the dead unit's report:** prod was not "mid-cold-start"; it had already reached
   `200` on `/health` and `/v1/models`, then was shut down by an explicit `kill`+`stop`
   (shutdown log 02:43:13 `API server: shutdown triggered`). The 02:32Z `prod:0` reading was a
   stop/start boundary, and the "25% weights" line came from a run that completed at 02:34:30
   (`Loading weights took 14.83 seconds`).
3. **Third container `r2v-a1` is the A1 cell variant, not a foreign process.** Image
   `sha256:2c211a1273b4` (same as prod), Cmd = the prod command + `--enable-prompt-tokens-details`,
   binds are the two A1 binds, served model `qwen3.5-9b`, host port 8014 — identical to
   `logs/A1-launch.json` `spec.cmd`/`binds`. In the window it progressed loading → weights 100% →
   `init engine ... took 64.47 s` at 02:46:19 → API server up; `/health` had not returned 200 by
   02:46:26 (curl `000`).
4. **Port 8014 is used mutually exclusively, never concurrently.** Events in the last 13 minutes show
   three clean cycles: prod stop → r2v-a1 destroy → prod start → prod kill/stop → r2v-a1 start.
   So the cell's stop-prod/start-variant/teardown/restore-prod sequence is working as designed and the
   `var:0` readings are launch-phase, not conflicts.
5. **GPU:** single `NVIDIA GB10`, `utilization.gpu 0 %`; `nvidia-smi` reports `memory.used/total` as
   `[N/A]` (unified memory), so the observable is `--query-compute-apps`:
   `3254084 /usr/bin/python3 218 MiB` (sglang wrapper, occamy), `3255041 sglang::scheduler 44954 MiB`
   (occamy), `3655291 VLLM::EngineCore 14384 MiB` (r2v-a1, was 14975 MiB at 02:45:46). Only two model
   engines are resident; there is no third tenant.
6. **Other containers:** none besides the three above.
7. **Lock:** `experiments/context-cache/.occamy.lock` exists and is stale — it records
   `{"unit":"U6-R","pid":11,"released_utc":"2026-10-21T21:18:54+00:00"}` (released). Recorded as an
   observation only; this unit did not touch it.

## Verdict / blocker
No hard blocker for occamy. **Prod is not up**, and `r2v-a1` (cell variant) is the process on 8014.
Safest recovery — prose only, NOT applied by this unit: let the in-flight `r2v-a1` finish its own
startup (its launch script already waits `health_wait_s`); if it must be abandoned, tear down
`r2v-a1` with the cell's own teardown (`docker rm -f r2v-a1` — named r2v-a1 only, never
`gx10-occamy-nvfp4`), then start `gx10-qwen9b` exactly as `logs/prod-restore.json` did
(`docker start gx10-qwen9b`, wait ~133 s for `/health` 200) and re-prove with
`health:200 / models qwen3.5-9b`. Never run two containers against port 8014.

## Handoff
`orchestration/handoffs/R2-VLLM-PREFLIGHT2.json`.
