# S1 — Generative model endpoints reachable from this machine

Observation date: 2026-11-07. Real checkout: `/home/zer0null/research extractor` @ f17663d. No service started/stopped/restarted/reconfigured; no completion/inference request sent. TCP probes used `timeout 2 bash -c '</dev/tcp/HOST/PORT'`; metadata GETs (labelled) only on open ports.

## 1. Configured endpoint declarations (live source; logs/scratch excluded)

| File:line | Declared endpoint | Model it names |
|---|---|---|
| `src/resextract/llm/occamy.py:76` | `DEFAULT_BASE_URL = "http://192.168.2.168:8012/v1"` | occamy-1.0 (SGLang) |
| `src/resextract/kg/staging.py:874` | `base_url = "http://192.168.2.168:8012/v1"` | occamy-1.0 |
| `src/resextract/doctor.py:77` | `"occamy_base_url": "http://192.168.2.168:8012/v1"` | occamy-1.0 |
| `src/resextract/doctor.py:81` | `"docling_bridge_base_url": "http://127.0.0.1:8893"` | docling bridge (not generative; port closed) |
| `src/resextract/web/search.py:202` (via `state/logs`) | `http://127.0.0.1:8080` | SearXNG (not generative) |
| `src/resextract/dashboard/app.py:21` | `127.0.0.1:8901` | dashboard (not model; port closed) |
| `config/resextract.toml:7` | `occamy_base_url = "http://192.168.2.168:8012/v1"` | occamy-1.0 |
| `config/resextract.toml:14` | `docling_bridge_base_url = "http://127.0.0.1:8893"` | docling (port closed) |
| `experiments/context-cache/client.py:30` | `RESEXTRACT_OCCAMY_BASE_URL` default `http://192.168.2.168:8012/v1` | occamy-1.0 |
| `experiments/context-cache/cells/WIN-SGL/*` | `BASE_URL = "http://192.168.2.168:8012"` | occamy-1.0 (SGLang) |
| `experiments/context-cache/cells/WIN-VLLM/*` | `API_BASE = "http://192.168.2.168:8014/v1"` | qwen3.5-9b (vLLM) |
| `experiments/context-cache/cells/W3-COLLECT/*` | `BASE_URL = "http://192.168.2.168:8017"` | qwen3.5-9b (SGLang, historical) |
| `experiments/context-cache/cells/PROMPT-O2-EXTRA/*` | `http://192.168.2.168:8017/v1` | qwen3.5-9b (SGLang, historical) |
| `docs/PLAN.md:24,62` | `keyring` @ `127.0.0.1:8790/v1`, default model `deepseek-v4.1-flash` | KeyRing (27 models; see §3) |
| `~/.dsh/profiles/web/cordis.yml` (external, per docs/PLAN.md:62) | `keyring` @ `127.0.0.1:8790/v1` | deepseek-v4.1-flash |

Historical-only O1–O4 endpoints (`:8012`/`:8014`/`:8017`) are comparison candidates, not evidence of current config; only `:8012` and `:8014` are live today (§5).

## 2. TCP reachability (measured)

Command: `timeout 2 bash -c '</dev/tcp/HOST/PORT'`.

| host:port | result |
|---|---|
| 127.0.0.1:80 | OPEN |
| 127.0.0.1:8000 | CLOSED |
| 127.0.0.1:8010 | CLOSED |
| 127.0.0.1:8012 | CLOSED |
| 127.0.0.1:8013 | CLOSED |
| 127.0.0.1:8014 | CLOSED |
| 127.0.0.1:8017 | CLOSED |
| 127.0.0.1:8080 | OPEN |
| 127.0.0.1:8088 | OPEN |
| 127.0.0.1:8090 | OPEN |
| 127.0.0.1:8787 | OPEN |
| 127.0.0.1:8790 | OPEN |
| 127.0.0.1:8791 | OPEN |
| 127.0.0.1:8792 | OPEN (TCP only; direct HTTP empty reply — nono sandbox blocks direct access) |
| 127.0.0.1:8801 | OPEN |
| 127.0.0.1:8891 | OPEN |
| 127.0.0.1:8893 | CLOSED |
| 127.0.0.1:8901 | CLOSED |
| 127.0.0.1:3080 | OPEN |
| 127.0.0.1:3090 | OPEN |
| 127.0.0.1:3091 | OPEN |
| 127.0.0.1:3220 | OPEN |
| 192.168.2.168:8000 | OPEN |
| 192.168.2.168:8010 | OPEN |
| 192.168.2.168:8012 | OPEN |
| 192.168.2.168:8014 | OPEN |
| 192.168.2.168:8017 | CLOSED |
| 192.168.2.168:8090 | OPEN |
| 192.168.2.168:80 | CLOSED |
| 192.168.2.168:8080 | CLOSED |
| 192.168.2.168:8088 | CLOSED |

## 3. Model identity per reachable endpoint (metadata GETs only)

- **192.168.2.168:8012** — SGLang `0.0.0.dev1+g4ccff141d` (container `gx10-occamy-nvfp4`, image sha256:72457f09…). `GET /v1/models` → `occamy-1.0`, `max_model_len=131072`. Full argv (via SSH, read-only): `--quantization modelopt_fp4 --context-length 131072 --mem-fraction-static 0.45 --kv-cache-dtype fp8_e4m3 --max-running-requests 5 --mamba-radix-cache-strategy extra_buffer --max-mamba-cache-size 64 --reasoning-parser qwen3 --tool-call-parser qwen3_coder --enable-metrics --enable-cache-report`. `/model_info` → `is_generation=true`. **Generative.** Cached tokens reported (`--enable-cache-report`).
- **192.168.2.168:8014** — vLLM `0.27.1` (container, image sha256:2c211a12…). `GET /v1/models` → `qwen3.5-9b`, `max_model_len=32768`. Full argv: `--quantization fp8 --kv-cache-dtype fp8 --max-model-len 32768 --gpu-memory-utilization 0.15 --max-num-seqs 6 --max-num-batched-tokens 8192 --enable-chunked-prefill --enable-prefix-caching --speculative-config {"method":"mtp","num_speculative_tokens":1} --reasoning-parser qwen3`. **Generative.** `--enable-prompt-tokens-details` is NOT in argv → `cached_tokens`/`prompt_tokens_details` UNAVAILABLE from this instance (prompt_tokens still present).
- **192.168.2.168:8000** - Qwen3.8 effort adapter (Node, gx10-qwen38-effort-adapter.mjs, mode=ingress), proxy to LiteLLM 127.0.0.1:8005 -> effort adapter 127.0.0.1:8001 -> SGLang 127.0.0.1:8002 (down). GET /v1/models (via adapter/LiteLLM) -> ornith-1.5-35b; GET /health -> healthy_endpoints: [] (0 healthy), error connect ECONNREFUSED 127.0.0.1:8002. Configured but backend down - not usable for inference today. Not a standalone stack.
- **192.168.2.168:8010** - specialist-models gateway (Node, gx10-specialist-models/gateway/gateway.mjs), auth-gated (Bearer token). GET /health -> {"status":"ready","models":["laya-decision","needle3-tool-calling"]}. GET /v1/models -> 401 without token. Surface is /v1/decisions and /v1/tool-calls (Laya + Needle), not /v1/chat/completions. Specialized, not a general generative stack.
- **192.168.2.168:8090** - GX10 SGLang dashboard (Node), HTML; not a model API.
- **127.0.0.1:8005 (remote loopback)** - LiteLLM router, model ornith-1.5-35b; 0 healthy upstreams (backend chain broken). 127.0.0.1:8002 (SGLang target) down; 127.0.0.1:8011 (Needle) serves /complete only, not OpenAI chat.
- **127.0.0.1:8790** — KeyRing broker (nono proxy → node `server.js`), `GET /health` → `{"ok":true,"keyCount":7,...}`. `GET /v1/models` → `401 {"error":{"message":"missing or unknown client key"}}` (auth required; not bypassed). Generative proxy: `POST /v1/chat/completions` SSE passthrough to 7 upstream accounts. Model catalog (from `data/state.json`, 27 models, none removed): deepseek-v4.1-flash, deepseek-v4-pro, kimi-k2.7-code, kimi-k3, qwen3.7-plus, qwen3.8-flash, qwen3.8-max, glm-5.2, glm-5.3, glm-5.3-flash, hy3, hy4-preview, muse-spark-1.2/1.3-contributor, gpt-6-luna, mimo-v2.6-flash/pro, minimax-m3, longcat-2.0, step-5-preview, beam-free, minimax-m3.1-flash, kimi-k3.1-pro, iceman-contributor-free, gemini-4-argon, hy4, crouton-alpha-free (context windows 131072–1050000). Usage accounting (server.js) reports `prompt_tokens` and `prompt_tokens_details.cached_tokens`. Auth required → model list above is from local state file, not a live GET.
- **127.0.0.1:8088** — openjev (Docker, PyTorch 2.9.1+rocm7.1.1, Transformers 5.15.0, FastAPI). `GET /health` → reranker `Qwen3_5ForSequenceClassification` (labels contradiction/entailment/neutral, batch 16, max_len 128). `GET /v1/models` → 404. **NOT generative** (sequence classifier). Not a stack for chat comparison.
- **127.0.0.1:8080** — SearXNG (metasearch), not generative.
- **127.0.0.1:8090** — pi-agent (HTML), not generative.
- **127.0.0.1:8787** — Swarm console (UI), not generative.
- **127.0.0.1:8791** — web (UI), not generative.
- **127.0.0.1:8792** — nono internal target (TCP open, direct HTTP empty reply); not directly usable; external surface is :8790.
- **127.0.0.1:8801** — dsh-board-hub, not generative.
- **127.0.0.1:8891** — crawl/scrape bridge (`GET /health` → `{"ok":true}`), not generative.
- **127.0.0.1:3080** — DSH web (auth-gated), not generative.
- **127.0.0.1:3090** — Cerebro, not generative.
- **127.0.0.1:3091** — cordis, not generative.
- **127.0.0.1:3220** — Vegtam, not generative.
- **127.0.0.1:80** — Caddy reverse proxy (process 8175), not a model endpoint.

## 4. Verdict table

| endpoint | generative? | reachable today | model | five-arm stack? (chat completions + per-request token accounting) |
|---|---|---|---|---|
| 192.168.2.168:8012 | yes | yes | occamy-1.0 (SGLang) | yes — `prompt_tokens` + `prompt_tokens_details.cached_tokens` (`--enable-cache-report`) |
| 192.168.2.168:8014 | yes | yes | qwen3.5-9b (vLLM 0.27.1) | partial — `prompt_tokens` yes; `cached_tokens` unavailable (no `--enable-prompt-tokens-details`) |
| 127.0.0.1:8790 (KeyRing) | yes | yes (auth-gated) | 27 models (deepseek/kimi/qwen/glm/…), ctx up to 1,050,000 | yes if client key supplied — `prompt_tokens` + `cached_tokens` reported |
| 192.168.2.168:8000 | yes (configured) | yes (API only; backend down) | ornith-1.5-35b (LiteLLM->adapter chain broken) | no - 0 healthy upstreams |
| 192.168.2.168:8010 | specialized | yes | laya-decision, needle3-tool-calling | no - no /v1/chat/completions surface |
| 127.0.0.1:8088 | no (reranker) | yes | Qwen3.5-4B NLI | no |
| 127.0.0.1:80/8080/8090/8787/8791/8792/8801/8891/3080/3090/3091/3220 | no | yes | n/a | no |
| 127.0.0.1:8012/8014/8017/8000/8010/8013/8893/8901 | n/a | no | n/a | no |

## 5. LAN/remote candidates named in docs

- `192.168.2.168:8012` — **reachable** (TCP OPEN; SGLang occamy-1.0 live). Evidence: `curl /v1/models` → 200 `occamy-1.0`, `max_model_len 131072`; full argv via SSH.
- `192.168.2.168:8014` — **reachable** (TCP OPEN; vLLM qwen3.5-9b live). Evidence: `curl /v1/models` → 200 `qwen3.5-9b`, `max_model_len 32768`; full argv via SSH.
- `192.168.2.168:8017` — **not reachable** (TCP CLOSED). Historical SGLang qwen3.5-9b endpoint torn down. UNAVAILABLE.
- `192.168.2.168:8000` — **reachable at API surface** (TCP OPEN) but backend down: adapter->LiteLLM->effort adapter->SGLang :8002 (connection refused); 0 healthy endpoints. Not usable.
- `192.168.2.168:8010` — **reachable** (TCP OPEN; specialist gateway, auth-gated, specialized surface).
- `192.168.2.168:8090` — **reachable** (TCP OPEN; GX10 SGLang dashboard, HTML).
- `192.168.2.168:80/8080/8088` — **not reachable** (TCP CLOSED).
- `127.0.0.1:8012/8014/8017` (local) — CLOSED; the generative servers are on the remote gx10 host, not this machine (this machine's LAN IP is 192.168.2.187).

## 6. HTTP call accounting

Metadata calls made: 107 HTTP requests total (100 direct + 7 via SSH) (GET/HEAD only), all labelled `metadata GET, not inference`. Breakdown: 42 local-port probes (14 ports × 3 paths), 27 remote-port probes (8012/8014/8017 × 9 paths), 9 remote-port probes (8000/8010/8090 × 3 paths), 8 KeyRing probes, 4 Caddy probes, 5 identity probes on 8012/8014, 3 repeat identity probes, 2 cached-token schema probes, plus 7 remote-loopback probes via SSH (8002/8005/8011). Completion/inference POSTs: **0**. TCP connect probes (not HTTP): 28. No service started/stopped/restarted/reconfigured.
