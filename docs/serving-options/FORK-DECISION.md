# Fork decision — SGLang

Current verdict: **no fork.** No failing run has yet been produced for any of the
three fork-gate criteria, so no patch to `/sgl-workspace/sglang` is justified.

## Fork gate (all three must hold, each demonstrated by a failing run)

A fork is permitted only when every one of the following is demonstrated by a
failing run on the captured fixture:

(a) **Per-range eviction protection** — pin a prefix range so LRU cannot drop it.
    Must be shown to fail on the stock image before a fork may add it.
(b) **Non-prefix reuse** — suffix or substring reuse of cached KV.
    Must be shown to fail on the stock image before a fork may add it.
(c) **Per-range attribution in the cache report** — the cache report must expose
    per-range attribution; absence must be demonstrated, not assumed.

## Environment

- Image tag: `lmsysorg/sglang:dev-qwen38-next-local`
- `sglang.__version__`: `0.0.0.dev1+g4ccff141d`
- Baseline server: `192.168.2.168:8012` (host-mapped from container port 30000),
  model `occamy-1.0` (occamy-1.0-NVFP4), `--mem-fraction-static 0.45`.

## Rule if a gap is demonstrated

If and only if a gap is demonstrated, patch `/sgl-workspace/sglang` inside the
image, rebuild under a **new tag**, and A/B against `:8012` on the **same
fixture**. Record here which gap justified the fork and the measured delta.

Until then this file states "no fork" and cites the flags that made it
unnecessary: `--enable-hierarchical-cache`, `--page-size 1`,
`--kv-cache-dtype fp8_e4m3`, `--enable-cache-report`,
`--mamba-radix-cache-strategy extra_buffer`.
