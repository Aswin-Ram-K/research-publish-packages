# R2-OPT-SETS — emit `state/config/best-config.json` for the four 2×2 setups, from measurements already on disk

**Successor to** `R2-OPT-LOOP` (exec `82a71fd0`, `cancelled`: it blocked itself on `ask_user_question` and
wrote nothing). Its question — *what does `R2-PROMPT` actually run?* — is already answered on the board:
the four setups are the literal **2 models × 2 engines**.

| id | model | engine |
|---|---|---|
| **O1** | occamy-1.0 (MoE, NVFP4) | SGLang |
| **O2** | qwen3.5-9b (dense, NVFP4) | SGLang |
| **O3** | occamy-1.0 (MoE, NVFP4) | vLLM |
| **O4** | qwen3.5-9b (dense, NVFP4) | vLLM |

The R / A / C / H arms are **not** setups — they are the four *prompt* arms `R2-PROMPT` runs *on* these
setups. Round-1 configs are banned as substrate for `R2-PROMPT`; nothing here copies one.

## Objective

Write `state/config/best-config.json` with one entry per 2×2 cell, every field taken from a measurement
already on disk (or marked `null` with a reason). At most **one** new measurement, and only if a required
field is absent.

## Evidence map — as assigned vs as found

The card's evidence paths and the paths that actually exist on this disk:

| setup | card says | on disk |
|---|---|---|
| O1 | `cells/WIN-SGL`, `cells/U15`, `state/config/occamy-restore-baseline.json` | ✅ all present; 32k-band figure re-derived from `cells/WIN-SGL/rows.jsonl` |
| O2 | `handoffs/W3-COLLECT.json`, **`cells/R2-SGL-9B/W3A/rows.jsonl`** | handoff ✅; **that cell path does not exist** — the rows are at `cells/W3-COLLECT/rows.jsonl` |
| O3 | `cells/R2-VLLM-FIX/OH1/rows.jsonl`, `state/config/r2-vllm-fix-oh1.json` | ✅ both present |
| O4 | `state/config/nvfp4-9b.json`, `cells/WIN-VLLM` | ✅ both present |

## Hard bound

20 tool calls / 1 new launch maximum / 1,200 live requests. Kill condition: if a required field cannot be
sourced, record `null` + `ci_source:"absent"` and stop that field — never invent a number.

## Deliverables (declared write paths)

- `state/config/best-config.json`
- `docs/serving-options/BEST-CONFIG.md`
- `orchestration/handoffs/R2-OPT-SETS.json`
- `orchestration/units/R2-OPT-SETS.md` (this card)

Nothing else. No `papers/**`, no `RUN.json`, no test edits, no cell edits. `gx10-occamy-nvfp4` is never
stopped, removed or restarted.

## Verification

- `python3 -c "import json;print(list(json.load(open('state/config/best-config.json'))['setups']))"` → `['O1','O2','O3','O4']`
- every `config_sha256` recomputed from its own `argv` in the same pass
- `:8012` 200 / `occamy-1.0` / 131072 and `:8014` 200 / `qwen3.5-9b` / 32768, `gx10-occamy-nvfp4` Up
