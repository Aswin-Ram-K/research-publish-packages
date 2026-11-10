# ENGINE-ATTEMPT-VLLM — vLLM on the SAME occamy weights (sequential, baseline restored)

**Status: done.** Verdict: `SAME_WEIGHT_VLLM_OK`. Baseline service verified healthy at finish.

## Summary
vLLM 0.27.1 (container image `2c211a1273b4`, the only vLLM image on gx10) successfully loaded the identical occamy-1.0 NVFP4 weights (`sha256:...fa865dc...`, 22.28 GiB) and served 2 chat completions on port 8013. Concurrent start was NOT attempted (memory arithmetic: SGLang's 110 GiB cap leaves 11 GiB = 9.1% < 15% headroom and < 22.28 GiB weights). Exclusive start succeeded; baseline restored and healthy.

## Key facts
- Weights: 22.28 GiB (5 shards). System RAM 121 GiB.
- vLLM load time: 158.44 s weights, 22.41 GiB memory. Startup incl. autotune ~4.5 min.
- Smoke 1: attempt `857904c1-da74-4537-92f6-ffcd03416165`, 50.79 s, 16/16 tokens, finish length.
- Smoke 2: attempt `2fbb611e-3567-4406-ad75-ed04f7fabb63`, 0.69 s, 17/16 tokens, finish length.
- CacheBlend/LMCache NOT exercised (prefix-only vLLM caching). FreeToken unverified/uninstalled. SGLang HiCache disabled on baseline.
- Restore: baseline container ID 6384dc02... matches frozen restore argv (770 chars). Weight load 131.49 s. /v1/models -> occamy-1.0. model_path matches pinned snapshot.

## Artifacts
- `$CAMPAIGN/pins/rollback-baseline.json`
- `$CAMPAIGN/notes/ENGINE-VLLM-ATTEMPT.md`
- `$CAMPAIGN/pins/logs/` (docker-ps-before/after, smoke1/2, baseline health before/after)
