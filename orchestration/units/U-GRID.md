# U-GRID — live server config inspection (state-checkpoint grid)

**Purpose (one only).** Settle from the *live* server whether the mamba/GDN state-checkpoint
grid explains the measured `cached = 64*floor((L-1)/64)` law.

**Bound.** 12 tool calls, **3 HTTP requests** (used: 2), no lock, no test battery, read-only.
Kill condition: server unreachable twice -> report `failed`.

**Write paths (mine alone).** `orchestration/units/U-GRID.md`,
`state/config/live-server-config.json`, `orchestration/handoffs/U-GRID.json`.

## Method
1. Client contract read from `experiments/context-cache/client.py`: base
   `http://192.168.2.168:8012/v1` (env `RESEXTRACT_OCCAMY_BASE_URL`), model `occamy-1.0`,
   `Authorization: Bearer <RESEXTRACT_OCCAMY_API_KEY>` (unset in env -> `EMPTY`). Admin endpoints
   live at the origin root, i.e. drop the `/v1` suffix -> `http://192.168.2.168:8012/get_server_info`.
2. `GET /get_server_info` answered **HTTP 200** on the first try (request 1); re-fetched once into
   the workspace (request 2). No 404 fallback needed; `/metrics` never touched. No auth required
   (server reports `api_key = null`, `admin_api_key = null`).
3. Parsed `internal_states[0]` — the scheduler's **effective runtime config**, authoritative where
   it differs from the top-level echo.

## Answer
`--mamba-track-interval` is **present and equal to 256** on this deployment (the SGLang default, so
the flag was never passed). The single published recipe that sets it to 64 is therefore *not* what
is serving: the CLI-flag version of the mamba-grid explanation is **refuted**.

**But the payload also carries `_mamba_cache_chunk_size = 64`** in `internal_states[0]` — a 64-token
mamba cache chunk granularity that is not the CLI flag and is not in `_resolved_overrides`. So the
empirical 64-token grid is *not* left unexplained: the live runtime does hold a 64 constant for
mamba cache chunking, and that (or `max_mamba_cache_size = 64`, a slot count, not a token grid) is
where a 64 boundary can come from. The tax law and this field were not re-correlated here (read-only
unit, no requests to the chat endpoint).

## Extracted flags (see `state/config/live-server-config.json` for the full sanitized payload)
mamba_track_interval 256 (explicit) | _mamba_cache_chunk_size 64 | page_size 1 | c128_page_size 16 |
mamba_radix_cache_strategy extra_buffer | max_mamba_cache_size 64 | mamba_max_states_per_path -1 |
chunked_prefill_size 8192 | mem_fraction_static 0.45 | attention_backend triton |
speculative_algorithm null (absent) | uses_mamba_radix_cache true | disable_radix_cache false |
enable_int8_mamba_checkpoint false | served_model_name occamy-1.0 |
model_path /root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652 |
version 0.0.0.dev1+g4ccff141d | status ready.

`FLA_CHUNK_SIZE`: not reported anywhere in the payload (no `fla_*` key at all);
`linear_attn_backend = triton`, `mamba_backend = triton`.

**Echo discrepancy:** top-level `disable_chunked_prefix_cache = false` but
`internal_states[0].disable_chunked_prefix_cache = true` (runtime effective). Same for
`page_size`/`mamba_track_interval` (agree). Cite the internal_states value.

## Lock
None taken. Pure GET metadata reads; `.occamy.lock` never opened or created.
