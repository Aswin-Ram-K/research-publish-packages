# PLAN corrections ledger — merged (a)–(y)

Additive record of **verified deviations** between the approved spec ([`docs/PLAN.md`](PLAN.md) — **not edited**)
and observed reality. `docs/PLAN.md` stays the spec of record; this file is the correction channel.

Each entry: the plan's assumption (quoted) · what is actually true · the evidence · the unit that found it.
A correction V1 could **not** independently reproduce is marked `reported-only` rather than deleted — it stays
in the ledger with its confidence labelled.

Opened by **V1** (Batch 1 independent verifier), 2026-10-08. Append-only.

## Merge record

This file is the **merged corrections ledger** — the single additive record of verified
deviations between the approved spec ([`docs/PLAN.md`](PLAN.md) — **not edited**) and observed
reality. `docs/PLAN.md` remains the approved spec; this file is its additive correction channel.

- Entries **(a)–(p)** were merged from `docs/PLAN_CORRECTIONS.md`, written by verifier **V1**
  (a–k) and appended by verifier **V3** (l–p).
- Entries **(q)–(y)** were merged from `docs/PLAN_CORRECTIONS_PART2.md`, written by verifier
  **V7** because the first file was contended at the time.
- Every entry's plan assumption, what is actually true, its **evidence** and the **unit that
  found it** were carried over **verbatim** from the two sources. No entry was rewritten,
  summarised, strengthened or softened.
- Every `reported-only` and every verified marking is preserved exactly as written. Where a
  source's marking is mixed or ambiguous (e.g. "(h)", "(i)"), the source's own wording is kept
  as-is; this merge does **not** decide the ambiguity.
- **Count of entries merged: 25** — (a)–(p) = **16**, (q)–(y) = **9**.
- `docs/PLAN_CORRECTIONS_PART2.md` is now a **superseded pointer** to this file; its text is
  preserved here.

The V1 summary table below indexes **(a)–(k) only** (V1's Batch-1 scope). Entries (l)–(y) are
recorded in full in the sections that follow and are deliberately not summarised in that table.

---

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

---

# V7 corrections — Batch 7 (refresh / invalidation evidence, U5.4–U7.1)

Merged verbatim from `docs/PLAN_CORRECTIONS_PART2.md` (now a superseded pointer). Independent
verifier **V7** wrote there: "Every entry below was verified by **V7** from evidence V7 generated
itself; nothing here is copied from a unit's report." Entries carried over unchanged.

## (q) The target repo is concurrently modified by a foreign actor, and quiescence is bursty/windowed

**Plan assumption** — `docs/PLAN.md` §"Hard constraints": *"Nothing is promoted outside this
workspace: no writes into `~/Duval`, no systemd unit enabled…"* and batch-7 gate: *"V7: simulated
commit marks exactly the right dockets stale with correct rework entries"* — both assume the target
is a stable thing to measure.

**What is true** — `/home/zer0null/Duval` is written by its own self-build loop in **bursts**.
Two live observation windows on 2026-10-08 (`11:18:31Z–11:18:36Z`, 5 s, and
`11:18:36Z–11:19:01Z`, 25 s) both returned `quiescent` with `files_touched_in_window = 0`. The
reflog for the same repo shows **8 HEAD moves inside `11:01:38Z–11:04:38Z`** (10 moves inside
`10:00Z–11:20Z`), and the newest tracked-file mtime was `2026-10-08T11:04:38Z` — i.e. the burst had
ended ~14 minutes before the windows opened.

**Consequence for the plan** — an acceptance run needs a **sealed window**: assert quiescence
before, *and* re-verify HEAD/porcelain after, and report both. A single pre-run check cannot certify
a run; it certifies only the seconds it covered.

**Evidence** — `state/verify/V7/check6-writer.txt` (both signals, with UTC window stamps),
`state/verify/V7/check6b-reflog-gap.txt` (reflog parse honouring the `-0500` offset).
**Unit** — U5.4 (`refresh/writer.py`); verified by V7.

---

## (r) A tracked file's bytes at a commit can differ from the working tree

**Plan assumption** — `docs/PLAN.md` line 39: *"`resextract refresh` after a new commit marks the
right dockets stale and appends specific rework to `UPDATE_BACKLOG.md`; cited URLs are re-fetched
and content-diffed"*, with the manifest recording `target{slug,head_sha,graph_hash}` and
`material[{src,dest,sha256,…}]` (line 186) — an implicit assumption that `head_sha` + the bytes on
disk describe one state.

**What is true** — they can describe two. `traces/2026-09-28-duval-m0.jsonl`:
working-tree sha256 `431605e6…`, pinned at `3982f26` `ba6128bf…` — different bytes under one head.
(`README.md` happened to match: `1f6bbdf6…` both pinned at `3982f26` and on disk, so it is not a
counter-example but also not evidence of safety.)

**Consequence for the plan** — material must be resolved from the **object store at a commit**
(`GitObjectSource`), never from the working tree, or a docket's "verifiable at commit X" claim is
false without anything noticing.

**Evidence** — `state/verify/V7/check8-u54-live.txt`. **Unit** — U5.4.

---

## (s) Untracked files cannot be pinned at all — and `.lane-j-scratch/**` is untracked

**Plan assumption** — `docs/PLAN.md` line 198 admits Duval's `.lane-j-scratch/*.md` to the corpus
*"where the monograph and evidence review live"*, and line 212 routes change detection through
`graphify update → changed files → graph nodes`.

**What is true** — `.ci-trunk.txt` is working-tree-only: `GitObjectSource('.ci-trunk.txt')` raises
`PathNotFoundAtCommit` at `3982f26` (and at any commit — it is untracked, porcelain `??`). The same
holds for everything under `.lane-j-scratch/` (porcelain `?? .lane-j-scratch/`). No commit can pin
those bytes.

**Consequence for the plan** — admitting an untracked path to a docket requires an explicit
`unpinned` marker (and the plan must say what verification means for it). A silent fallback to the
working tree would defeat the pinning entirely; the current code correctly refuses instead.

**Evidence** — `state/verify/V7/check8-u54-live.txt`, `git -C /home/zer0null/Duval status --porcelain`.
**Unit** — U5.4.

---

## (t) The refresh's staged graph copy can be stale while `graph_state.json` claims a newer head

**Plan assumption** — `docs/PLAN.md` line 212: *"On repo change: `graphify update` → changed files
→ graph nodes → re-mine only affected candidates"* — the graph is assumed to reflect the head the
run observed.

**What is true** — `state/kg-refresh/duval/repo` was staged from the working tree when HEAD was
`b44e0e1` (files added in `b44e0e1..b2bade3` are **absent** from the copy: `tools/selfbuild/backlog.ts`,
`tools/selfbuild/loop.ts`), while `state/kg-refresh/duval/graph_state.json` records
`observed_head: b2bade3` and `updated_at 11:01:51Z`. The reuse guard compares that recorded head with
the next observed head, so a future run at `b2bade3` would reuse a `b44e0e1`-content graph and skip
the update. For the U7.1 fixture docket — whose claims cite files, not graph nodes — the invalidation
verdict is **identical** with the copy and with `graph=None` (reasons byte-identical), so the
demonstrated verdict is unaffected; for graph-cited claims it is a latent correctness risk, and the
state file's `observed_head` is not a truthful provenance label.

**Evidence** — `state/verify/V7/check3-recompute.txt` (identical reasons both ways; absent-file
probe). **Unit** — U7.1.

---

## (u) Detection gap: a writer churning inside an EXISTING untracked path reads `quiescent`

**Plan assumption** — `refresh/writer.py` docstring / batch-7 intent: the presence of a writer is
*"a measured, reported fact, so a run must either find the target quiescent or explicitly opt in"*.

**What is true** — `detect_concurrent_writer` watches tracked `(size, mtime_ns)` and the **set** of
untracked entries. Modifying an existing untracked file (or content under `.lane-j-scratch/**`,
which porcelain already reports as one `??` entry) changes neither, so it reports `quiescent`
with `files_touched_in_window = 0`. Control: creating a *new* untracked entry does report
`active_writer`. The target's foreign actor writes into exactly such paths.

**Consequence for the plan** — for this target, even a sealed HEAD window is not sufficient
evidence of quiescence; the plan should require an explicit statement that untracked-path content
is outside the detector's field of view, or extend the detector.

**Evidence** — `state/verify/V7/check6b-reflog-gap.txt` (both the gap and the control).
**Unit** — U5.4.

---

## (v) Refresh never bumps `target.head_sha`, and `verify_docket` accepts the result

**Plan assumption** — `docs/PLAN.md` line 215: *"Nothing silently overwritten: `HISTORY.md` +
`MANIFEST.json` hold the timeline"*, and the freshness vocabulary is *"`current` · `stale (age N d)`
· `needs_rework (source moved)` · `superseded`"*.

**What is true** — refresh rewrites only `freshness{state, age_days}` and leaves
`target.head_sha = 6deaed0` while setting `freshness.state = "needs_rework"`. `verify_docket` on the
result returns `ok = true` with **no problems** (the manifest validator has no head↔freshness
cross-check). Rendering pairs `target @ 6deaed0` with the freshness label, so the state is not
misrepresented; a downstream consumer that reads `target.head_sha` as "current head" would be
wrong, but no such consumer was found in `src/` (renderers print it beside the freshness state).

**Evidence** — `state/verify/V7/check3-noop.txt` (manifest head before/after, `verify_docket_ok`).
**Unit** — U7.1.

---

## (w) Refresh does not persist rework today; schema v2 now unblocks it (gap, not a defect)

**Plan assumption** — `docs/PLAN.md` line 39 describes the *file* side only
(*"appends specific rework to `UPDATE_BACKLOG.md`"*); the store schema (line 151+) has a `rework`
table.

**What is true** — `refresh_target(persist_store=False)` by default, and **no caller** (CLI or
tests) sets it `True`; `src/resextract/cli.py` has only a placeholder `"refresh": "batch 7"` entry,
so refresh has no CLI entry point at all. Even with `persist_store=True`, `backlog.persist_rework`
still calls the legacy `store.open_rework` **without** `source_ref`/`model_suggested`, so provenance
is dropped (proved: persisted row has `source_ref=None`, `model_suggested=0`) and its note still
claims the columns do not exist. Schema v2 (`add_rework` deduping on
`(docket_id, reason, source_ref)`, `list_rework`, `upsert_docket_by_dir`) **does** unblock the
persistence path. Remaining unwired: (1) `persist_rework` → `add_rework` carrying provenance;
(2) any caller enabling persistence; (3) `docket_id` resolution uses only `dirs[0]`, so a
multi-docket target would attach every entry to the first docket; (4) `persist_rework` counts a
deduplicated row as written.

**Evidence** — `state/verify/V7/check7-persistence.txt`. **Unit** — U7.1 (documented gap) with
U0.10 (schema).

---

## (x) The "27 changed files" figure = diff entries + untracked porcelain entries

**Plan assumption** — batch-7 gate: *"simulated commit marks exactly the right dockets stale with
correct rework entries"*; the changed-file count is used as the invalidation surface.

**What is true** — `6deaed0..b2bade3` has **14** commits and **25** `git diff --name-status -M`
lines. The reported **27** is `25 + 2`: `detect_change` unions the committed changed set with the
dirty porcelain set, and at run time the working tree had two untracked entries
(`.ci-trunk.txt`, `.lane-j-scratch/`). Recomputed live: `kind "both"`, `commits_between 14`,
`changed_files 27` — the figure reproduces exactly.

**Evidence** — `state/verify/V7/check3-recompute.txt`. **Unit** — U7.1.

---

## (y) Overstatement: the reflog window contains 8 HEAD moves, not 9

**Plan assumption** — U5.4's live evidence states *"9 HEAD moves 11:01:38Z–11:04:38Z"*.

**What is true** — parsing `git reflog --date=iso` with the recorded `-0500` offset honoured gives
**8** entries inside `2026-10-08T11:01:38Z–11:04:38Z` (10 inside `10:00Z–11:20Z`). The burstiness
conclusion is unaffected; the count is one high.

**Evidence** — `state/verify/V7/check6b-reflog-gap.txt`. **Unit** — U5.4.

---

# U8.4 append — deferred entries carried by units settled since the (a)–(y) merge

Appended by **U8.4** on 2026-10-08 from the handoffs named in each entry. Nothing above this
line was modified: the pre-existing prefix is byte-identical, and every `reported-only` marking
stands. These ten entries close the "deferred to a later unit" queue left by U5.7, U5.6, U6.3,
U6.4, U8.3, U2.2, U0.12 and U4.0. The next letter after this block is **`aj`**.

---

## (z) The docket manifest is a superset of the plan's §3.5 contract, with the schema string deliberately un-bumped

**Plan assumption** — `docs/PLAN.md`:186 defines the manifest as
`… generated_by{app,version,model} …`, i.e. `generated_by` carries exactly those three keys and no
producer or reason field.

**What is true** — `src/resextract/docket/manifest.py` gained, **additively**:
`generated_by.producer` (validated against the closed set `model|replay|mixed|fixture|unknown`;
`PRODUCERS` at :58, `DProducer` at :66), `generated_by.model`, `status_reason` (:161), and a
**derived** `promotion_eligible()` (:193) rather than a stored flag — its docstring says it is
computed from `generated_by.producer` and `status` "so it cannot drift out of sync with" them. The
schema string is **not** bumped (`resextract/docket/1` still), and an old manifest with no
`producer` key loads as `unknown` (:147). **Code now leads the document**: `docs/PLAN.md`:186 does
not list these keys — that is the point of this ledger.

**Evidence** — `orchestration/handoffs/U5.7.json` (`gate`, `backward_compat`:
`old_manifest_model_field_still_loads`, `smoke_manifest_validates`; artifact sha `manifest.py` =
`f358822977f656bc`) · `src/resextract/docket/manifest.py`:23–26, :58, :66, :147, :161, :193–205 ·
`docs/PLAN.md`:186. **Unit** — U5.7.

---

## (aa) Producer precedence is deliberately conservative: any replay wins

**Plan assumption** — the plan defines no provenance-collapse rule; with mixed member provenance
the natural expectation would be a `mixed` label.

**What is true** — `derive_producer()` (`src/resextract/docket/materialize.py`:512–534) is literal
and conservative: all `model` ⇒ `model`; **`model` + `replay` ⇒ `replay`** (the more damning label
wins, so a docket holding *any* replay-derived candidate cannot claim model provenance);
`model` + `fixture` ⇒ `mixed`; `replay` + `fixture` ⇒ `replay`; `fixture`-only (or no rows, or
unrecognised values) ⇒ `unknown`. There is no fifth outcome, because every non-`model` value blocks
promotion anyway — `producer_gate_reason()` refuses each of them, and `assemble()` independently
downgrades `ready` → `draft` for a non-model producer.

**Evidence** — `src/resextract/docket/materialize.py`:512–534 (docstring + branch order) ·
`orchestration/handoffs/U5.7.json` (`next_unit_hint` precedence statement, `gate.vocab`,
`promotion_eligible` = {replay:false, mixed:false, unknown:false, model_ready:true}, and the live
docket with `producer:"replay"`, `status:"draft"`, `promotion_eligible:false`). **Unit** — U5.7.

---

## (ab) `.gitignore` rules must be root-anchored or they silently untrack a fixture tree

**Plan assumption** — the plan is silent on ignore semantics; the workspace assumed an ignore rule
names a path in the repository.

**What is true** — the unanchored rule `dockets/` matched
`tests/fixtures/dashboard-store/dockets/` **at any depth**, so the ok-docket/broken-docket fixture
trees were gitignored, untracked, and therefore **absent on a fresh clone**. U6.3 diagnosed it
(fresh-checkout emulation with the gitignored tree removed: **5 failed / 43 passed**; additionally
removing the committed DB: 12 failed / 36 passed). U6.4 measured a `git archive HEAD` clone at
**6 failed / 42 passed** and fixed it. The rules are now `/state/`, `/dockets/`, `/.venv/`,
`/.pytest_cache/` (root-anchored), with `*.sqlite-wal`, `*.sqlite-shm`, `*.sqlite-journal` added
globally and `/tests/fixtures/dashboard-store/state.sqlite` ignored because that DB is generated on
demand into a pytest tmp_path. `tests/test_repo_hygiene.py` (**11 passed**) guards the semantics via
`git check-ignore` (rule reverted ⇒ 10 failed / 1 passed).

**Evidence** — `orchestration/handoffs/U6.3.json` (`diagnosis`, `before`, `red_green`) ·
`orchestration/handoffs/U6.4.json` (`defect.clone_emulation`, `ignore_audit`, `red_green`,
`after`, `deferred_question`) · `.gitignore` (verbatim) · `tests/test_repo_hygiene.py`.
**Unit** — U6.3 (diagnosis), U6.4 (fix).

---

## (ac) Commit pinning resolves tree-first; deletion from the working tree no longer loses pinned bytes

**Plan assumption** — pinning obtains the bytes at the recorded commit.

**What is true** — before U5.6, a path tracked at the commit but deleted from disk was reported
`not_a_file_in_target` and its committed bytes were never read: verifier **V5** reproduced exactly
that (`C7`, judgement "REPRODUCED → DEFECT" — the bytes were present in the object store and were
never consulted). The fix resolves **tree-first**: the recorded commit is asked before the working
tree, and `not_a_file_in_target` now applies **only** when the path is absent from **both** the
commit and the working tree. The content/secret scan still runs over the **pinned** bytes through
the same `Copier`, so a secret present **only** in committed content is **refused by the commit
path** while a working-tree-only secret is copied — an **intended asymmetry** (the refusal follows
the bytes being copied), not a parity bug. No cited live `duval` ref is currently deleted, so the
deleted case is fixture-proven only.

**Evidence** — `orchestration/handoffs/U5.6.json` (`fix.tree_first`,
`fix.not_a_file_in_target_only_when_absent_from_both`, `fix.secret_check_on_pinned_bytes`,
`fix.asymmetry_preserved`, `tree_only_real_case`, red→green A/B with sha-identical restores) ·
`orchestration/handoffs/V5.json` (`checks` C7, `deleted_file_verdict`, `next_unit_hint`) ·
`src/resextract/docket/materialize.py`:50–58, :83–85 · `tests/test_docket_materialize_pinned.py`
(17 passed). **Unit** — U5.6, on a defect judged by verifier V5.

---

## (ad) The model endpoint is a DEGRADABLE core leg, not a fatal one

**Plan assumption** — `docs/PLAN.md` §1.2 treats the model endpoint as a core leg, and a fatal
preflight on any core-leg probe would abort the run.

**What is true** — a fatal preflight would make plan §1.2 unreachable: U8.3 reports that **a live
run exited 2** because the `doctor` **SearXNG** probe (a core leg) `ReadTimed` out, before the
needs-based gate landed. The endpoint is now a **blocked** stage with exit **1**
(`exit_code_for`: ok 0, degraded 1, hard_down 2, nothing_runnable 3), and other core legs are fatal
only if a selected stage actually invokes them. Live `run --target duval --json` → **exit 1**, with
`mine`/`claims`/`assess` **blocked**, `graph`/`staging`/`lanes`/`refresh` **ok**, `materialize`
**skipped** by the producer gate. SearXNG flakiness is independently corroborated: U0.3's first
`doctor --json` returned `SearXNG ReadTimeout` and exited 2 (a third run 3 s later was green), and
V3 observed 3/3 genuine queries returning zero with `unresponsive_engines` non-empty (this ledger,
entry (l)).

**Evidence** — `orchestration/handoffs/U8.3.json` (`exit_codes`, `live.real_run`,
`next_unit_hint` — "one live run exited 2 on a core SearXNG ReadTimeout before the needs-based gate
landed", red→green for `mine` blocked-vs-skipped) · `state/logs/U8.3-realrun.json` ·
`orchestration/handoffs/U0.3.json` (`live_intermittency`, `doctor_json`) · entry (l) of this file.
**Unit** — U8.3.

---

## (ae) `run` keeps the real store read-only — stage writes go to a run-scoped copy

**Plan assumption** — the plan's safety rule keeps the target read-only and forbids writes outside
the workspace; it did not specify what a run does to the authoritative store.

**What is true** — a run does not mutate `state/state.sqlite`. The run workspace is
`state/run/<slug>/`, graphify's `--out` lives inside it, and stage writes go to a **run-scoped
SQLite copy made with the backup API** (`_copy_store` opens the source read-only and calls
`source.backup(target)`). Live proof: the store sha256 `459e16cc875654df` was unchanged by both the
dry run and the real run, and `state/run/duval` was not created by the dry run.

**Evidence** — `orchestration/handoffs/U8.3.json` (`live.dry_run.note` — "state/state.sqlite sha256
459e16cc875654df unchanged", `live.real_run` sealed window, `duval_untouched`) ·
`src/resextract/run.py`:38–40, :430–442, :1256 · `state/logs/U8.3-realrun.json`. **Unit** — U8.3.

---

## (af) The store reached schema v3: producer identity and honest metering, backfilled on two signals with `rows_lost = 0`

**Plan assumption** — §3.4's DDL has no producer/provenance column and one undifferentiated call
counter.

**What is true** — schema v3 adds `candidates.producer` (CHECK over
`model|replay|fixture|unknown`), `candidates.model`, `runs.model`, `runs.mode`, and separates
**`model_calls`** (real outbound model requests) from **`usage_records`** (every usage-sink record —
what the old counter counted), after a verifier proved the old counter misleading (it incremented on
4xx and on exhausted transport failures). The backfill required **two independent signals** — the
`live-u21-replay` run tag **and** the `REPLAY ` title prefix; **half-evidence ⇒ `unknown`**, never a
guess. Migration: `schema_before 2 → after 3`, `rows_lost = 0` across 12 tables, backup at
`state/logs/U2.2-state-backup.sqlite` (sha256 `d11c86f6…`). V2S independently re-derived the
migration on its own v2-shaped DB and confirmed the new CHECK rejects a bogus producer on both
UPDATE and INSERT, and that a zero-I/O replay client reports `model_calls=0` / `usage_records=2`.

**Evidence** — `orchestration/handoffs/U2.2.json` (`migration`, `metering`, `live_report`) ·
`orchestration/handoffs/V2S.json` (C1, C2, C4 — red→green sha-proven) ·
`orchestration/handoffs/V2.json` checks 4–5 (the FAILs that motivated it) ·
`src/resextract/mine/candidates.py`:231–232, :1078–1079, :799–800. Live read-only DDL:
`schema_version` rows `[(1,),(2,),(3,)]`; `candidates` carries
`producer TEXT DEFAULT 'unknown' CHECK (producer IN ('model','replay','fixture','unknown')), model TEXT`;
`runs` carries `model TEXT, mode TEXT`. **Unit** — U2.2, verified by V2/V2S.

---

## (ag) `tests/test_store_v2.py`'s version pins now assert the migration's contract, not the current schema number

**Plan assumption** — the mandated v3 bump assumed the v2 suite's `== 2` version pins were
compatible with it.

**What is true** — the bump broke **four** pins (`:169`, `:221`, `:252`, `:537`) **plus a fifth
masked behind the first** (`:170`; pytest stops at the first failing assert in a test). U0.12
relaxed them to `assert schema_version >= 2`, membership/ordering for the migration list, and a
fresh DB equal to `store.SCHEMA_VERSION` — every relaxed site carrying the comment "the schema
advances; this pins the migration's contract, not the current number. Do NOT re-tighten to == 2."
**0 assertions deleted** (the 6 pinned sites became 10 assertions; no row, CHECK or dedupe
assertion was touched). A migration-contract guard monkeypatches `store.MIGRATIONS=[]` (the source
file is never edited; plugin at `state/logs/U0.12_guard/migrations_off.py`) and proves the relaxed
assertions still fail when the migration list is emptied (`E assert 0 >= 2`, 2 failed).

**Reported-only within this entry** — the source's "82 → 87 lines, +5" line-count figure is **not
reproduced**: U0.12's handoff states only the assertion accounting (6 pinned sites → 10 assertions,
0 deleted), and `tests/test_store_v2.py` measures **566** lines on disk versus **539** at `HEAD`
(+27 for the file as a whole, which does not corroborate a +5 delta). The substance of the entry
(relaxed pins, the latent fifth, 0 assertions deleted, the contract guard) is verified; the +5
figure is carried as `reported-only`.

**Evidence** — `orchestration/handoffs/U0.12.json` (`classification`, `migration_contract_guard`
with its `2 failed, 11 deselected` transcript, `red_green`) · `tests/test_store_v2.py`:175–176,
:220–221, :252, :537, :564 (`wc -l` 566 vs `git show HEAD:tests/test_store_v2.py | wc -l` 539) ·
`state/logs/U0.12_guard/migrations_off.py`. **Unit** — U0.12.

---

## (ah) `claims` carries no CHECK on `kind`/`verification_state`, so the claims unit defined its own vocabulary

**Plan assumption** — §3.4 constrains the enumerated columns of `verdicts`, `lanes` and `evidence`,
so `claims.kind` and `claims.verification_state` were assumed constrained too.

**What is true** — the live DDL for `claims` is `id INTEGER PRIMARY KEY, candidate_id INTEGER
REFERENCES candidates(id), kind TEXT, "text" TEXT, provenance_json TEXT, verification_state TEXT,
confidence REAL` — **no CHECK on either column**, unlike the tables the plan does constrain
(`verdicts.verdict` and `evidence.source_kind` each carry one, `lanes` carries two). The store
therefore cannot reject an unknown claim kind or verification state, so U4.0 defined a **closed
vocabulary itself** and documented it: kind ∈
`measured|behavioural|architectural|comparative|negative|definitional`, with verification_state
starting at `unverified` (which `docket/materialize` already defaults to). The same handoff records
an adjacent gap: `store.py` exposes `get_claim(id)` but no all-claims reader, so `decompose.py` runs
its own SELECTs against the same DB path; `store.py` was not edited (sibling-owned).

**Evidence** — live read-only `sqlite_master` DDL for `claims` (quoted above; `CHECK` absent) versus
`verdicts`/`lanes`/`evidence` (1/2/1 CHECKs) · `orchestration/handoffs/U4.0.json` (`vocabularies`,
`store_gap`, `duval_untouched`) · `docs/PLAN.md` §3.4 (`claims(…)` column list). **Unit** — U4.0.

---

## (ai) Plan gap: nothing in §3.4 would have prevented a replay row being stored indistinguishably from a mined one

**Plan assumption** — §3.4's DDL defines no producer/provenance column for `candidates` or `runs`,
so a stored candidate records *what* was found but not *how* it was produced.

**What is true** — this was the build's only **outright FAIL** (verifier **V2**, checks 4 and 5,
`overall: FAIL`): `candidates` was `[id, run_id, kind, title, summary, provenance_json,
graph_nodes_json, score, state]` and `runs` was `[id, target, started_at, finished_at, status,
budget, tokens_used, notes]` — **no producer/model/mode field anywhere**, all **10/10** replay rows
sitting at `state='mined'`, and `report.json` with no producer key; the only distinguishing signals
were the `live-u21-replay` run-id string and the `REPLAY ` title prefix — a naming convention, not a
field any consumer could rely on. In the same FAIL, `model_calls` counted every usage-sink record,
so a replay run with no HTTP transport at all reported `model_calls=2`. Both FAILs were fixed by
U2.2 (see (af)) and closed by V2S; the columns are present in the live DDL today. **Recorded as a
plan gap**: because §3.4 defined no producer column, nothing in the plan would have prevented it —
the defect was found by a verifier, not by the spec.

**Evidence** — `orchestration/handoffs/V2.json` (`overall: FAIL`, checks 4/5,
`replay_distinguishable`, `model_calls_semantics`, `corrections`) ·
`orchestration/handoffs/U2.2.json` (`fixes`: "FAIL A producer identity", "FAIL B metering
semantics") · `orchestration/handoffs/V2S.json` (`fail_a_closed`, C1/C2) · live read-only DDL
showing `candidates.producer` + `model` and `runs.model` + `mode`. **Unit** — U2.2, after V2's FAIL.

---

*End of the U8.4 append. Entries (a)–(y) above are unchanged; the next letter is `aj`.*
