# Remote writes — BLOCKED by default

The only writable location is `/home/zer0null/research extractor`. Anything on
the remote host `gx10-163b` (model downloads, HuggingFace cache, build trees)
requires an explicit operator authorisation pasted verbatim into this file.
Without that text, remote writes remain blocked.

## Current status

BLOCKED. No authorisation recorded. The programme therefore reads only the
models already resident on the host and writes no new bytes to it:

- `occamy-1.0-NVFP4` on `:8012` (SGLang)
- `qwen3.5-9b` on `:8014` (vLLM)

Reading an existing path is not writing; Nemotron adoption and local post-training
are deferred, not dropped, until an authorisation is recorded.

## Proposed root (proposal only — not authorised)

`/home/zer0null/gx10-serving-programme/`

If authorised, weights land there with `HF_HOME`, `HF_HUB_CACHE`,
`TRANSFORMERS_CACHE`, `VLLM_CACHE_ROOT` and any build tree inside it
(`models/`, `cache/hf/`, `cache/vllm/`, `build/`). Nothing is written to
`/home/zer0null/models` or `~/.cache/huggingface`. Every path on that host must
be enumerated here. The authorisation text must be pasted verbatim below before
any remote write occurs.

## Authorisation (verbatim)

(none recorded)
