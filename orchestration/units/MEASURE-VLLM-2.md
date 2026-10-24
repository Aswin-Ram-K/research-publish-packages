# MEASURE-VLLM-2 — detached launch (start-and-exit)

- Shape: launch only, no waiting. Card bound 12 calls; used 12.
- GX10 (192.168.2.168): `available=52211 MB`, `gx10-occamy-nvfp4` Up 19 h, `r2v-a1` Up (left alone).
- Container `r2oh1` (349a0ce0…) Up on `:8020->30000`, loading 22.28 GiB occamy-1.0 NVFP4.
- Driver: PID **3778667** (`bash run.sh`, setsid/nohup), started 2026-10-24T03:24:31Z.
- Driver flow: poll `/v1/models` ≤900 s → dump `docker logs` to `/tmp/r2oh1.log` → grep block/hash/mamba/num_gpu_blocks into `OH1/startup.txt` → `vllm_cell.py --arm all --turns 71 --budget 32768 --warmup` → `DONE rc=$?` in `OH1/status`.
- Logs: `/home/zer0null/r2/run.out.log`, `/home/zer0null/r2/OH1/status`, `/tmp/r2oh1.log`; rows `/home/zer0null/r2/OH1/rows.jsonl`.
- Production untouched: `:8012` never contacted, `gx10-occamy-nvfp4` never stopped; `gx10-qwen9b` not stopped per card.
- Next: `POLL-VLLM` collects rows + startup + `DONE rc=`; expected 284 rows (4 arms × 71 turns).
- Note: the launching ssh client kept its channel open (backgrounded subshell inherited the pipe); it does not affect the detached remote job and ends when `run.sh` ends.
