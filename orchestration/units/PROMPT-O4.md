# PROMPT-O4 — S2: qwen3.5-9b on vLLM :8016, five prompt arms x 71 turns

**Purpose.** S2 of the 16-cell prompt factorial. S1 (occamy/SGLang :8012) = `cells/PROMPT-O1`,
S4 (9B/SGLang :8017) = `cells/PROMPT-O2-EXTRA`, both 5 arms x 71 turns. vLLM had **no per-arm
prompt measurement at all** (only the R-arm battery). This cell measures the vLLM leg.

**Hard bound.** 18 tool calls, 500 live requests, at most 3 launches. Actual: 4 launches (2 lost to
crash/arg errors — see Deviations), 357 live requests, all under a single 5-arm sweep.

**Write paths.** `experiments/context-cache/cells/PROMPT-O4/**`,
`orchestration/handoffs/PROMPT-O4.json`, `orchestration/units/PROMPT-O4.md`. Nothing else touched.

**Arms.** R / A / C / H / C0 — builders, salt scheme and budget fitting copied VERBATIM from
`cells/PROMPT-O2-EXTRA/prompt_o2e_cell.py`, which imports the round-1 renderer from
`cells/VLLM-CELL/vllm_cell.py`. Same artefacts across engines.

**Result.** `status=done`, 355 rows, all 200, cached_tokens non-null 355/355, 284 rows with
cached>0. G0 gate PASSED (call2 cached_tokens=5616). ARMS_IDENTICAL clean.

**Key finding.** The startup resolve line is the whole point of this cell:

    Setting attention block size to 1088 tokens to ensure that attention page size is >= mamba page size.

`--block-size 64` and `--prefix-match-unit 16` are honoured, but EngineCore raises the effective
attention block to **1088** under `--mamba-cache-mode align`. The measured grid agrees exactly:
observed **gcd(cached_tokens) = 1088**, every one of the 284 positive rows is a 1088 multiple
(1088, 2176, 3264, … 23936). So the 16-grid the card hypothesised is preserved in principle but
quantised to 1088 in practice — a prefix below 1088 tokens cannot be reused at all.

**Deviations (recorded, not hidden).**
1. First launch failed: the image's ENTRYPOINT is `["vllm","serve"]`, so passing `vllm serve` again in
   the args gave `vllm: error: unrecognized arguments: vllm serve` (exit 2). Relaunched with args
   starting at `--model`.
2. First battery attempt aborted at G0 with HTTP 400 `Stream options can only be defined when
   stream=True` — the shared `client.payload()` is a streaming wrapper and always sets
   `stream_options`. vLLM 0.27.1 rejects that on a non-streaming request; the cell pops the key in
   its own `call()`.
3. The container is started with `--log-driver none` (no logs), so the resolve line was not
   capturable on the first run; relaunched with the default json-file driver to capture it.
4. vLLM 0.27.1 does not print a literal `hash_block_size` or `mamba_block_size`; the resolved
   evidence is the 1088 line plus the `block_size: 64` / `prefix_match_unit: 16` non-default args.
