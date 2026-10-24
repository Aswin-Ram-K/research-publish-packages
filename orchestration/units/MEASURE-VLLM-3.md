# MEASURE-VLLM-3 — relaunch occamy on vLLM at gpu-memory-utilization 0.34

- Shape: start-and-exit (launch + PID + health proof), card bound 12 calls.
- Why: attempt 2 (container `r2oh1`, sha 349a0ce0) died at engine init:
  `Available KV cache memory: -20.42 GiB` -> `ValueError: No available memory for the cache blocks.`
  vLLM's own hint: 0.2200 is effectively 0.2050 under CUDA-graph profiling.
- Fix applied exactly as the card specifies: `--gpu-memory-utilization 0.22 -> 0.34`, and stop
  `gx10-qwen9b` only. `gx10-occamy-nvfp4` (:8012 SGLang production) was not touched.
- Frozen memory: before stop available=51924 MB; after stop available=74374 MB (+22.4 GB).
- Launch: `GX10:/home/zer0null/r2/launch-oh2.sh` (reconstructed from attempt-2 inspect), container
  `r2oh1` = f72952ea6a23, host PID **3794205** (`vllm serve ... --gpu-memory-utilization 0.34`).
- Driver: `GX10:/home/zer0null/r2/run3.sh` (run.sh with `sudo -n docker` -> `docker`), PID **3794430**.
- Health: `GET :8020/v1/models` -> **200**, rows so far 0; status file last line:
  `STARTED 2026-10-24T03:35:22Z`.
- KV evidence: `(EngineCore pid=131) INFO 10-24 03:38:33 [gpu_worker.py:563] Available KV cache memory: 13.93 GiB;(EngineCore pid=131) INFO 10-24 03:38:33 [kv_cache_utils.py:2235] GPU KV cache size: 1,029,213 tokens;`

## Next

POLL-VLLM: read `OH1/rows.jsonl`, `OH1/startup.txt`, `OH1/status`, `/tmp/r2oh1.log`; expect
284 rows (4 arms x 71 turns). Restart `gx10-qwen9b` only after the cell completes.
