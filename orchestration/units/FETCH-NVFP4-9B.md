# Unit card — FETCH-NVFP4-9B

**Purpose (one only):** get a verified NVFP4 copy of **the same** Qwen3.5-9B we already serve onto the GX10,
so the dense arm can run at NVFP4 instead of fp8.

**Status:** done — `go`, lineage `same`, sha256 verified against the publisher digest.

## Bound

- 45 min wall for the 9.4 GB transfer (actual: 77 s).
- At most **one** retry on a failed/truncated download (none needed).
- Verification is digest-based, not size-based.

## Write paths

| Path | Where |
|---|---|
| `state/config/nvfp4-9b.json` | workspace |
| `orchestration/handoffs/FETCH-NVFP4-9B.json` | workspace |
| `orchestration/units/FETCH-NVFP4-9B.md` | workspace (this file) |
| `/home/zer0null/models/qwen3.5-9b-nvfp4/` | GX10 |
| `/home/zer0null/models/fetch-nvfp4-9b.log` | GX10 |
| `/home/zer0null/models/nvfp4-9b.sha256` | GX10 |

No overlap with other units: nothing outside `/home/zer0null/`, no `state/logs/`, no `experiments/`.

## Hard constraints honoured

- **No container started, stopped or restarted.** `docker exec` was used for read-only introspection only.
- No live model requests. No `.occamy.lock` taken.
- Nothing written to `/root/...`, nothing touched in `~/.ssh`.

## Procedure actually run

1. **Pre-flight** — `df -h /home` → 285 GB free; `hf` + `huggingface-cli` present; `env | grep -i HF_` empty
   (so the host shell is *not* offline, unlike the container env).
2. **Download** detached via `setsid nohup env -u HF_HUB_OFFLINE -u TRANSFORMERS_OFFLINE hf download
   AxionML/Qwen3.5-9B-NVFP4 --local-dir /home/zer0null/models/qwen3.5-9b-nvfp4`, log to
   `/home/zer0null/models/fetch-nvfp4-9b.log`, polled in two rounds rather than blocking a turn.
3. **Verify** — size vs HF tree manifest; `model.safetensors` header parsed for the tensor inventory;
   `sha256sum` compared to the publisher LFS etag; config and tokenizer diffed field-by-field against
   `/home/zer0null/models/qwen3.5-9b-bf16`.
4. **Loadability** — proxied from checkpoint layout, the container's `modelopt_quant.py`, `flashinfer.mm_fp4`
   import, and `nvidia-smi` compute capability.

## Result

- **Bytes on disk:** 9,380,649,471 across 13 files (`du -sh` 8.8G); `model.safetensors` 9,361,048,680.
- **sha256:** `a1304acf8325cee90075bf8eb7f5e973ef893c7d497ded92e7d720f0e7178749` — equals the publisher's LFS digest.
- **Quant class:** `modelopt` / `NVFP4`, weights **and** activations 4-bit float, group_size 16.
- **Lineage:** same. Identical architecture, identical `layer_types` ordering, byte-identical tokenizer.
- **Go/no-go:** **go**, against the `gx10-occamy-nvfp4` image (GB10, cc 12.1; sglang built from source with
  full NVFP4 modelopt support).

## Notes for the next unit

- The card's 9,373,856,662-byte figure was `model.safetensors` **plus** `tokenizer.json`; do not read the
  8.8 GiB `du` output as a shortfall.
- `/home/zer0null/models/ornith-1.5-35b-a3b-nvfp4` is **FP8, not NVFP4**, despite its directory name. Do not
  use it as an NVFP4 baseline.
- Actual loading is unproven. Give the smoke test a **new** container — do not restart the two serving ones.
