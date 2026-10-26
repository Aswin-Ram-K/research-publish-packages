# PROMPT-O1 — five prompt arms x 71 turns on production occamy-1.0 (SGLang)

**Objective.** Measure `uncached_tokens` per turn for five ways of laying out the same
71-turn workload, against the existing O1 setup in `state/config/best-config.json`
(occamy-1.0, SGLang, `http://192.168.2.168:8012/v1`). No restart, no container, no config edit.

**Arms.** `R` resend · `A` shared prefix (scaffold + pointer index + newest delta) ·
`C` tag at delta end · `H` hybrid/compaction (folds every 8) · `C0` plain chat transcript.
R/A/C/H are the Round-1 renderers imported **verbatim** from
`experiments/context-cache/cells/VLLM-CELL/vllm_cell.py`; `C0` is added in the cell script and
each arm gets a fresh salt head so no arm can warm on another's prefix.

**Hard bound.** 20 tool calls, 400 live requests (355 rows + 2 warm-up + retries). Non-200 aborts
the cell. `.occamy.lock` held for the whole run.

**Write paths.** `experiments/context-cache/cells/PROMPT-O1/**`,
`orchestration/handoffs/PROMPT-O1.json`, `orchestration/units/PROMPT-O1.md`. Nothing else.

**Guards.** warm-up must show `usage.prompt_tokens_details.cached_tokens > 0` on the second
identical call or the cell is `failed_blind_instrument`; `ARMS_IDENTICAL` over the turn-1 prompt
hashes makes the cell `invalid_arms_identical` rather than a winner.
