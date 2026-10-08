# PLAN corrections ledger

Additive record of **verified deviations** between the approved spec ([`docs/PLAN.md`](PLAN.md) — **not edited**)
and observed reality. `docs/PLAN.md` stays the spec of record; this file is the correction channel.

Each entry: the plan's assumption (quoted) · what is actually true · the evidence · the unit that found it.
A correction V1 could **not** independently reproduce is marked `reported-only` rather than deleted — it stays
in the ledger with its confidence labelled.

Opened by **V1** (Batch 1 independent verifier), 2026-10-08. Append-only.

| # | Correction | Found by | V1 status |
|---|---|---|---|
| a | `--no-viz` is not an `extract` flag | U1.1 | **reproduced** |
| b | node kind is `file_type`, not `type` | U1.2 | **reproduced** (26-node exception) |
| c | `confidence`/`confidence_score` are on links, edges live under `links` | U1.1 | **reproduced** (4-node exception) |
| d | SGLang counts reasoning inside `max_tokens` → `length`+empty = truncation | V0 (×2) | `reported-only` (Occamy down) |
| e | SearXNG zero-result latency 1–7 ms vs 500–950 ms is the degradation signal | U3.1 / U3.3 | `reported-only` (outside Batch 1) |
| f | `graphify query` prints labels, never real node ids | U2.1 | **reproduced** |
| g | a relative `--graph` from another cwd makes every query exit 1 | U2.1 | **reproduced** |
| h | graphify block-buffers stdout off-TTY; a timeout discards progress | U1.1 | **remedy reproduced**; failure mode `reported-only` |
| i | the default `--token-budget 60000` is unusable at ~36 output tok/s | U1.1 | **default reproduced**; throughput `reported-only` |
| j | `graphify extract --out DIR` writes to `DIR/graphify-out/` | U1.1 | **reproduced** |
| k | the plan's Batch-1 unit mapping differs from the delivered unit set | V1 | **reproduced** (scope note) |

---

## (a) `--no-viz` is not an `extract` flag

**Plan assumption** — §4 stage 1, `docs/PLAN.md`:198: "graphify `extract --code-only` (free AST) → docs/semantic
pass on Occamy (`OPENAI_BASE_URL=…`, `--max-concurrency 1`, **`--no-viz` above 5k nodes**) → `label`." Repeated at
`docs/PLAN.md`:240: "excludes, **`--no-viz` >5k nodes**, per-stage budgets".

**Actually true** — `--no-viz` is documented only for **`cluster-only`** (`state/logs/graphify-0.9.80-help.txt`:40,
"skip graph.html generation (useful for >5000 node graphs / CI)") and for **`export html`** (line 124). The
`extract` block is lines 91–116 and does not list it. `graphify extract` has no per-command help at all
(`graphify extract --help` → `Run 'graphify --help' for full usage.`, exit 0). Passing it anyway is **silently
accepted** — it reaches the same path check with the same exit as without the flag, i.e. it is a no-op for
`extract`, not a hard error.

**Evidence** — `state/logs/graphify-0.9.80-help.txt`:40,:91–116,:124 · `state/logs/V1-extract-help.txt` ·
probe `graphify extract /nonexistent-v1-probe --code-only --no-viz` → `error: path not found: …`, exit 1 —
byte-identical to the same probe without `--no-viz`.

**Found by** U1.1. Independently reproduced by V1.

## (b) graphify nodes have no `type` — the kind is `file_type`

**Plan assumption** — the plan does not name graphify's node-kind discriminator (it uses `kind` only for the
*claims* table, `docs/PLAN.md`:153: "`claims(id, candidate_id, text, kind, provenance_json, …)`"); the natural
reading of a graph node was a `type` field. U1.2 reported: "nodes have **no `type`** field — kind is `file_type`
(`code`/`rationale`, 12+9); rationale/docstring nodes are first-class".

**Actually true** — real file nodes carry **`file_type`** ∈ {`code`, `rationale`, `concept`} (and `document` only
after the semantic pass) and carry no `type`. **Exception:** the 26 synthetic external-reference nodes *do* carry
`type: "external"` (all have `external: true`, `source_file: ""`). So the absolute claim holds for 2659 of 2685
nodes, not for all.

**Evidence** — V1 counts over `state/kg/duval/graphify-out/graph.json`: `file_type` = {`code`: 2636, `concept`: 32,
`rationale`: 17}; a `type` key on exactly 26 nodes, value `external` on all 26. kg-mini fixture:
`file_type` = {`code`: 12, `rationale`: 9} over 21 nodes.

**Found by** U1.2; exception quantified by V1.

## (c) `confidence` / `confidence_score` live on links; edges are under the `links` key

**Plan assumption** — typed results were assumed to be documented as declared (`docs/PLAN.md`:99, "subprocess
wrapper + typed results"). U1.1 reported: "`confidence: EXTRACTED` lives on **edges** (with `confidence_score`),
not nodes; edges live under the `links` JSON key".

**Actually true** — top-level JSON keys are `nodes`, `links`, `hyperedges`, `directed` (+ `graph`, `multigraph`,
`built_at_commit`); there is **no `edges` key**. All 7102 links carry **both** `confidence` and
`confidence_score`; the vocabulary is `EXTRACTED | INFERRED`. **Exception:** 4 placeholder nodes also carry
`confidence: "EXTRACTED"` (with **no** `confidence_score`) — `./evals/drift.ts`, `node:fs/promises`,
`node:child_process`, `node:net`. No node carries `confidence_score`.

**Evidence** — V1 script over `state/kg/duval/graphify-out/graph.json`: `edges` key present = **False**;
links with `confidence` = 7102/7102; with `confidence_score` = 7102/7102; nodes with `confidence_score` = 0;
the 4 nodes above.

**Found by** U1.1; exception quantified by V1.

## (d) SGLang counts reasoning inside `max_tokens` — `finish_reason == "length"` with empty content is truncation

**Plan assumption** — `docs/PLAN.md`:52–53 reads an Occamy reply as content-bearing: "`POST /v1/chat/completions`
(`:8012`) returned `finish_reason: tool_calls` with valid JSON args" and "⭐ Thinking can be turned off …
`enable_thinking=false` → **0.25 s / 2 tokens**".

**Actually true** — SGLang counts **reasoning tokens inside `max_tokens`**. A response with
`finish_reason == "length"` and **empty `content`** means the whole budget was spent on reasoning — **truncation,
not an empty answer**. A client that treats empty content as a valid (or failed-but-retryable) answer will
silently lose the answer and mis-bill the call.

**Evidence** — `orchestration/VERDICTS.md` V0 §"Live — PASS": "on 7438.7 ms / 256 rt / empty content,
`finish_reason=length` — truncation trap reproduced" (verified twice, once earlier in the session).
V1 could **not** re-run it: Occamy is down (HTTP 000, connection refused).

**Found by** V0. **V1 status: `reported-only`.**

## (e) SearXNG: zero-result latency (1–7 ms) vs genuine answers (500–950 ms), with `unresponsive_engines == []`

**Plan assumption** — `docs/PLAN.md`:237 ("SearXNG intermittency … every failure in `search_health`") and
`:201` assume failures surface through the response's error field, so pacing/rotation reacts to them.

**Actually true** — a **zero-result** SearXNG response can return in **1–7 ms** while a genuine answer takes
**500–950 ms**, and `unresponsive_engines` stays `[]` throughout. **Latency, not the error field, is the
degradation signal**; a health check that inspects only `unresponsive_engines` will report a degraded instance
healthy. `search_health` must record latency, not just status.

**Evidence** — reported by U3.1 / U3.3 from their own runs. Out of Batch 1's scope; V1 ran no SearXNG experiment.
**V1 status: `reported-only`.**

## (f) `graphify query` prints node **labels**, never real ids

**Plan assumption** — `docs/PLAN.md`:199 wires the mining loop to "`graph_query`/`graph_explain`/`graph_path`",
and `:288` requires "`query` returns real provenance" — i.e. query output is assumed usable as a node reference.

**Actually true** — `query` prints human **labels**, never the graph's real node ids. On the kg-mini fixture the
query printed `main()`, `Job`, `run_job()`, while `read_graph(...).by_id()` keys are `main_main`,
`pkg_core_job`, `pkg_core_run_job`. A tool loop that pipes query output back in as an id gets an ambiguous
**label**; `graphify path "A" "B"` matches labels and exits 1 on ambiguity.

**Evidence** — V1 transcript: `graphify query "how does main call run_job" --graph <abs> --budget 200` →
`NODE main() [src=main.py …]`, `NODE Job`, `NODE run_job()`; wrapper `by_id()` keys listed above.

**Found by** U2.1; reproduced by V1.

## (g) A relative `--graph` path with a different cwd makes every query exit 1

**Plan assumption** — the plan's CLI examples pass `--graph <path>` without requiring an absolute path
(`docs/PLAN.md`:188–199); `--out`/`--graph` were assumed to resolve against the invocation context.

**Actually true** — `--graph` is resolved against the **process cwd**, not the wrapper's `cwd`. From `/tmp`,
`--graph state/kg-mini/graphify-out/graph.json` → `error: graph file not found: /tmp/state/kg-mini/graphify-out/graph.json`,
**exit 1**; the same relative path from the workspace root exits **0**; the **absolute** path from `/tmp` exits **0**.
A wrapper that keeps a relative graph path while changing cwd fails every traversal.

**Evidence** — V1 transcripts (workspace-root relative: exit 0 · `/tmp` relative: exit 1 · `/tmp` absolute: exit 0).

**Found by** U2.1; reproduced by V1.

## (h) graphify block-buffers stdout off-TTY — a timeout discards all progress

**Plan assumption** — `docs/PLAN.md`:256 makes the semantic pass the "one real unknown" of Phase 1; a subprocess
timeout was assumed to be a usable progress/cost guard.

**Actually true** — when stdout is a pipe (not a TTY), graphify **block-buffers**: nothing appears until the
buffer flushes, so a `subprocess` timeout kills the run with an **empty stdout** and all progress lost.
`stdbuf -oL -eL` restores line buffering. The wrapper captures via pipes, so it is always in the buffered case.

**Evidence** — V1's Gate A rebuild ran under `stdbuf -oL -eL` and its log holds 227/227 AST progress lines plus
the final `wrote …: 2695 nodes, 7151 edges, 119 communities` line (`state/logs/V1-gate-a.log`).
**V1 status: the `stdbuf` remedy is reproduced; the buffered-vs-unbuffered byte-count measurement behind
"silently discards progress" was not run — that half is `reported-only`.**

**Found by** U1.1; remedy reproduced by V1.

## (i) The default `--token-budget 60000` is unusable at the measured throughput

**Plan assumption** — `docs/PLAN.md`:144 sets the semantic stage's only lever as "`--max-concurrency 1`
(single GPU)" and is silent on the token budget; graphify's help default is
"`--token-budget N  per-chunk token cap for semantic extraction (default: 60000)`".

**Actually true** — at **~36 output tok/s** (U1.1's measurement; output ≈ 2× input) a 60000-token per-chunk cap
means one chunk can run ~55 minutes and cannot return inside `--api-timeout 600`. The usable range is
**1500–2000**. A stage that leaves the flag at its default will look hung and then truncate.

**Evidence** — `state/logs/graphify-0.9.80-help.txt`:103 (default 60000) — reproduced. The ~36 tok/s figure
requires a live Occamy and is **not** reproduced. **V1 status: `reported-only` for the throughput half.**

**Found by** U1.1.

## (j) `graphify extract --out DIR` writes to `DIR/graphify-out/`

**Plan assumption** — `docs/PLAN.md`:188: "never write inside the target repo (graphify `--out` + `.graphifyignore`
keep **`graphify-out/`** outside it too)" — naturally read as "`--out DIR` writes into `DIR`".

**Actually true** — `--out DIR` writes to **`DIR/graphify-out/`**, one level deeper. Help text, verbatim:
"`--out DIR, --output DIR   output dir (default: <path>); writes <DIR>/graphify-out/`". Any consumer that looks
for `DIR/graph.json` finds nothing.

**Evidence** — `state/logs/graphify-0.9.80-help.txt`:106 · both V1 and U1.1 landed at
`<out>/graphify-out/graph.json` (`state/verify/V1/kg/graphify-out/graph.json`) · the wrapper encodes this
(`resolve_graph_path`, asserted at `tests/test_kg_graphify.py`:60).

**Found by** U1.1; reproduced by V1.

## (k) Scope note — the plan's Batch-1 unit mapping differs from the delivered units

**Plan assumption** — `docs/PLAN.md`:288: "`U1.1` graphify wrapper + query battery (`src/resextract/kg/`) —
**the integration gate, run alone** · `U1.2` **notebook normalizer**".

**Actually true** — U1.1 was delivered as the **viability gate** (prompt-side, no code) and U1.2 as the
**typed wrapper + query battery** (`src/resextract/kg/{__init__,graphify,queries}.py`). **No notebook-normalizer
unit exists** in `orchestration/units/` (`D1, U0.1–U0.7, U1.1, U1.2, U2.1, U3.1–U3.3, U5.1, U5.2, V0`).
Consequence: §4 stage 2's "Notebooks (`.ipynb`, unsupported by graphify) are normalized to markdown into
`state/notebooks/`" currently has **no owning unit**.

**Evidence** — `docs/PLAN.md`:288 vs the delivered `src/resextract/kg/` files and the unit-card listing.
Recorded as an open scope deviation, not a defect in the delivered work (the gate itself was correctly run alone).

**Found by** V1.

---

# V3 corrections — Batch 3 (web-research layer, U3.1–U3.3)

Independent verifier V3; author of none of the units it checks. Suite re-run: **78 passed** (17
`test_web_search.py` + 61 `test_web_fetch.py`). Four guards red→green reproduced with sha256 proof
(`state/verify/V3/redgreen.log`). **[V3-verified]** = re-observed by this unit from its own probes;
**[reported-only]** = taken from another unit's handoff and not reproduced by V3.

## (l) [V3-verified] Latency is a *lower bound* on SearXNG deadness, not a classifier — and `unresponsive_engines` does **not** stay `[]`

**Plan assumption** — `docs/PLAN.md`:201: "**Web research** — query generation → SearXNG with pacing
+ jitter, engine rotation, backoff, negative cache TTL, index-page fallback". `docs/PLAN.md`:61
records only the symptom: `local_web_search` "worked for the first ~6 queries, then returned **no
results**". The plan encodes no way to distinguish a dead SearXNG from a genuine "nothing found".

**Actually true** —

1. The sub-50 ms `fast_empty` escalation (U3.1/U3.3) **is real and reproduced**: 2 rapid identical
   forced queries returned `ok=True, results=0` at **1.617 ms** and **1.315 ms**, and the client
   latched `degraded` with `reason="fast_empty"` on the **first** one (`live_probe.json`). U3.3's
   1.635/1.124 ms pair is confirmed in kind.
2. But **dead responses are not all fast, and `unresponsive_engines` was not `[]`.** In the same run
   the same dead service returned empties at **59.7 ms, 126.2 ms and 340.0 ms** — all ≥
   `fast_empty_ms=50` — so none fast-latched; degradation only latched after three consecutive slow
   empties (`reason="consecutive_empty"`). A separate raw JSON `GET /search` returned
   `unresponsive_engines` = `[["brave","Suspended: too many requests"],["duckduckgo","CAPTCHA"],
   ["qwant","CAPTCHA"]]` — **not** `[]`. U3.1's "with `unresponsive_engines: []`" is therefore **not
   reproducible at the time of this check**; SearXNG can name its own unresponsive engines, which if
   anything strengthens the honesty argument but means `[]` is not a property to rely on. Likewise
   U3.1's "8 distinct queries → 5 with results (172–948 ms)" was **not reproducible**: all 3 genuine
   paced queries returned zero results on both `google` and `duckduckgo` (latencies 2.1–340.0 ms).

**Consequence** — the 50 ms rule catches the *fastest* dead answers only; empties between ~50 ms and
~350 ms are indistinguishable from a genuine empty by latency and depend on the 3-in-a-row rule.
`unresponsive_engines`, when non-empty, is a strictly better signal and is currently **discarded** by
`src/resextract/web/search.py` (the parsed payload's field is never read).

**Evidence** — `state/verify/V3/live_probe.json` (`genuine`, `rapid_identical_forced`, `raw_probe`);
`state/verify/V3/redgreen.log` guard (c). **Found by** U3.1/U3.3; reproduced and corrected by V3.

## (m) [V3-verified] The fetch cache is keyed by **URL**, not by content; the *content* hash is only what `refresh()` compares

**Plan assumption** — `docs/PLAN.md`:201: "fetch via crawl bridge, scrape on failure, **content-hash
cached**" — naturally read as "the cache is keyed by content hash".

**Actually true** — the cache path is `sha256(url)` (`fetch.py::_cache_key`), i.e. keyed by URL
identity (`state/webcache/<sha256(url)>.json` + `.txt`); the **content** digest is stored *inside*
the record (`FetchMeta.sha256`) and is what makes `refresh()` honest: `old == new ⇒ changed=False,
note="unchanged"`; `old is None ⇒ changed=True, note="no_previous_copy"`. It is not a content-
addressed store — two distinct URLs with identical bytes make two entries. Live: `refresh()` on
arXiv `/abs/2505.22954` returned `changed=False` with `old_sha256 == new_sha256 == 0dde6e26…`; a
non-forced re-fetch returned `from_cache=True` with **0** bridge HTTP calls (independently counted by
wrapping `httpx.HTTPTransport`).

**Evidence** — `state/verify/V3/live_probe.json` (`fetch.arxiv_refresh`, `fetch.cache_hit_refetch`);
`_cache_key`/`_read_cache` in `src/resextract/web/fetch.py`. **Found by** U3.2; clarified by V3.

## (n) [V3-verified] A transport failure is never cached as a negative result — but no test asserts it

**Actually true** — a zero-result `ok=True` outcome *is* cached (as a **success-shaped** empty: the
second call returns `ok=True` plus a "negative-cache hit" note), while `ok=False` paths (transport
error, HTTP 4xx/5xx, malformed/empty body) never touch `_negative_cache` and are retried every call.
V3's probe confirms `_negative_cache == {}` and 2 HTTP calls after 2 transport failures, and `ok=False`
for HTTP 500, empty body and malformed JSON. **But** `tests/test_web_search.py` asserts none of the
`ok=False`-not-cached, 4xx/5xx, or malformed-body paths; the same holds for "the latch survives a
later successful search" (true in code — `_degraded` is never reset — and reproduced, but unasserted).
The gap is test coverage, not behaviour. **Evidence** — `state/verify/V3/invariants_probe.json`.

## (o) [reported-only] graphify 0.9.80 has no `FileType.OFFICE`; Office files classify as `DOCUMENT`

**Reported by U1.4** (`orchestration/handoffs/U1.4.json`: `docx_supported: true`), **not reproduced by
V3.** `graphify`'s `FileType` enum has no `OFFICE` member, so `.docx`/`.xlsx` fall through to the
generic `DOCUMENT` type. Any ingestion code keying on `FileType.OFFICE` cannot exist against 0.9.80;
an Office-specific path must key on the file extension instead.

## (p) [reported-only] graphify cannot see **15.01%** of `Duval` (80 of 533 files); the largest block is `.jsonl` (38)

**Reported by U1.4, not reproduced by V3.** U1.4's audit reports 533 walked files, 453 supported
(84.99%), 80 unsupported (15.01%), top gaps `jsonl 38`, `xml 29`, `rels 4`, `cff 1`, `patch 1`.
Consequence: a graph built by graphify alone silently omits ~1 file in 7 in the acceptance target, so
"the graph is the codebase" is false until the normalizer covers those types.
