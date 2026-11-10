# V-SPCC-23 — verify stable-prefix compiler (layers.py) and run_longrun stamping

Independent re-check of `experiments/ptr-engine/ptr_engine/layers.py` and the claimed stamping in `experiments/ptr-engine/longrun/run_longrun.py`.

## Author tests
`.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_layers_compiler.py -q` → `5 passed in 0.03s`. The five tests cover exactly the five invariants named in the file (determinism, drift, prefix stability, compaction, fetch isolation). They do NOT cover: journal/index line format rules, `mask_output` absence from the new path, `cached_tokens` null semantics, or the run_longrun wiring. Those are checked below.

## Checks performed
1. Author tests: `5 passed in 0.03s` (see above).
2. Determinism (own scratch, fresh RunStates): `str(a)==str(b) True`, `prefix_sha256 equal True`. Byte-identical on two renders.
3. Drift: mutating `run.model` ("m1"→"m2") for the same run_id raises `PtrPrefixDrift('PTR_PREFIX_DRIFT: L0 bytes changed within run')`; mutating `run.system` (+ "X") also raises. Public injection exists via run attributes.
4. Prefix stability under fetch: 24 turns, fetches at turns 5/12/19 → `unique prefixes 1`, `L3 grows 3`. Pass.
5. Compaction: 24-line journal → `compactions 1`, `epoch 1`, `journal []`, all index lines present, exactly one summary block. Pass.
6. Fetch isolation: body at turn 13 does not change `prefix_sha256` (equal True). Pass.
7. Format rules: journal line `T3|assistant|T⏎second line` (pipe-delimited, `\n`→`⏎`, no trailing space); index lines sorted lexicographically (`@artifact...`, `@doc...`, `@knowledge...`); `mask_output` not present in layers.py source. Pass. Note: `_sort_index_lines` sorts the full line (including ` scope=...`), not strictly the reference token; not demonstrated to differ.
8. Wiring: `grep -n "prefix_sha256\|layer_tokens\|cached_tokens" run_longrun.py` shows stamping at lines 2677/2680 (extras) and 3193/3196 (info), plus 2578 (row). BUT `compile_prompt`/`CompactionState`/`layers` are imported nowhere in run_longrun.py (repo-wide grep: only layers.py, __init__.py, tests, docs). `layer_tokens` is never populated (`info["layer_tokens"]` never set → always None). `prefix_sha256` is set only by the `pointer-stable` arm via `sha256_text(prefix)`, not via `layers.compile_prompt`. The claimed "stamping near line 3058" does not call the compiler; the new path is aspirational, not wired.
   `cached_tokens` null semantics: row field = `resp.get("cached_tokens")` (resolved usage or metrics delta); None when unreported with no metrics delta → null, not 0. `cached_tokens_normalized` applies engine null semantics (sglang: None→0, vllm: None→None). Pass for null-not-zero.
9. Surrounding suite: `test_layers_compiler.py` + `test_cell.py` + `test_cell_gates.py` → `27 passed, 13 subtests passed`. `test_verdict_semantics.py` fails to collect due to a pre-existing exit-code partition drift (exit code 14 unclassified in `EXIT_TABLE`); unrelated to this unit.

## Defects
- `layers.compile_prompt` is never imported or called in `run_longrun.py` (or anywhere outside tests/docs); `layer_tokens` is always None in rows; the compiler is un-wired. The stable-prefix path exists as a library but is not on the measurement path.
- `_L0_HASHES` is module-global and never cleared/reset, keyed by run_id; no public reset, so reuse of a run_id across distinct L0s in one process yields a false `PtrPrefixDrift`. Minor.
- Compaction fires on `len(st.journal) >= COMPACT_EVERY` but `st.journal` is overwritten from the `journal` param each call; callers must read `state.journal` after the call to observe the reset, otherwise compaction re-fires every turn. Latent footgun, not exercised by tests.
- `__init__.py` re-exports only `compile_prompt, CompactionState, PtrPrefixDrift, COMPACT_EVERY` from layers, not `escape_journal_content`, `format_journal_line`, `RETURN_SYMBOL`, `_sort_index_lines` (all in layers `__all__`). Consumers wanting format helpers must import `ptr_engine.layers` directly.
