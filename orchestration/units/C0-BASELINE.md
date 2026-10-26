# C0-BASELINE — plain-chat comparator on both live models

**Bound** 30 tool calls, 2 retries/turn. **Writes** rows file, this card, `orchestration/handoffs/C0-BASELINE.json`. No edit to RECORD/CLAIMS/MANUSCRIPT or any existing row file.
**Question** (`quality/PREREG.json`, unchanged): audit code of `lumen` = `AUD-4417`, exact match. **Turn plan** T1 body k12, T2 k10, T3 k08, T4 question; corpus `quality/corpus.py`, 12 x 9000 B.
**Endpoints** SGLang `http://192.168.2.168:8012` `occamy-1.0-NVFP4` ctx 131072; vLLM `http://192.168.2.168:8014` served id `qwen3.5-9b` ctx 32768. Both probed first, HTTP 200 / curl exit 0; no loopback.

## What ran — 105 rows (3 reps x 4 turns x 3 arms x 2 models)

| model | arm | reqs | correct | uncached tok/turn |
|---|---|---|---|---|
| occamy | C0 plain transcript | 12 | **0/3** (`k08`) | 1546.1 |
| occamy | R pointer, tool-call fetch | 24 | **3/3** (`AUD-4417`) | 2318.8 |
| occamy | C compaction, keep newest + 200 B digest | 12 | **0/3** (`k08`) | 1407.7 |
| qwen3.5-9b | C0 plain transcript | 12 | **0/3** ("Cannot be determined") | 4676.8 |
| qwen3.5-9b | R pointer, text `FETCH` protocol | 33 (12 = HTTP 400) | **0/3** | 6362.5 |
| qwen3.5-9b | C compaction | 12 | **0/3** (`k08`) | 1991.2 |

`pointer / C0` uncached per turn = **1.50x** SGLang, **1.36x** vLLM: a resolve costs an extra request over the same growing prefix, so the pointer arm is dearer here.

## Findings
1. **Plain transcript cannot answer**: C0 never sees k01 (turns carry k12/k10/k08 only). It is a floor, not a rival.
2. **Pointer is the only arm that finished** (SGLang 3/3). Compaction of the same transcript fails 0/3 both models.
3. **Cost direction is against pointer** at 3 bodies; the index's r = 236x win does not appear in a 3-body session.
4. **vLLM refuses tool calling** (HTTP 400: needs `--enable-auto-tool-choice --tool-call-parser`), so R there ran a text `FETCH` protocol and scored 0/3 — qwen never fetches k01 at T4. Protocol parity is missing.
5. **Accounting**: vLLM returns `prompt_tokens_details: null` on every row, so its uncached column is gross prompt tokens (upper bound); SGLang reports cached tokens.

## Traps
Both models are reasoning models: with thinking on, all `max_tokens` went to `reasoning_content` (first run, 8 rows, `max_tokens=800`, empty content — discarded before analysis, row file reset). Rerun used `chat_template_kwargs.enable_thinking=false`, `max_tokens=300`, temp 0.0. Corpus bodies are deterministic, so rows replay byte-for-byte.

**Handoff** `orchestration/handoffs/C0-BASELINE.json` (status `partial`: vLLM pointer protocol parity missing). **Rows** `experiments/ptr-engine/measure/rows-baseline-2026-10-26.jsonl`.
