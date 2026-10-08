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

---

# U8.9 append — verified deviations and design decisions settled since the (a)–(ai) merge

Appended by **U8.9** (Occamy probe `000`, DOWN; zero LLM calls, no test suite run). Each entry was
re-checked against the code/artifacts on disk where that was possible in this unit; a clause resting
only on a unit's own report is labelled `reported-only` and names the unit. Nothing above this line
was rewritten. **Entries appended: 13 — `(aj)`–`(av)`. Entry count 35 → 48.**

---

## (aj) [verified] The store reached schema v4: producer provenance on `evidence` and `verdicts`, fail-closed to `unknown`

**Plan assumption** — §3.4 enumerates the columns of `evidence` (`id, claim_id, source_kind,
source_ref, sha256, quote, context, retrieved_at, copy_path`) and of `verdicts` (`id, claim_id,
verdict, rationale, evidence_ids_json, checked_at`) and defines **no producer column on either**, so
nothing in the plan prevented a verdict's provenance being unknowable.

**What is true** — the live store is schema **v4** (four `schema_version` rows). `evidence` gained
`producer TEXT NOT NULL DEFAULT 'unknown' CHECK (producer IN ('model','replay','fixture','unknown'))`;
`verdicts` gained `producer` (identical NOT NULL/DEFAULT/CHECK) **and** `model TEXT`. The backfill is
**fail-closed**: every pre-v4 row became `unknown` — `store.py`:520 records that "the schema-v4
backfill joins nothing, so it refuses to infer a `model`" — no old row was promoted on an inferred
signal. The migration is **purely additive with `rows_lost = 0` for every table**, and a second
`init_db` is a byte-identical no-op.

**Evidence** — my own read-only `sqlite_master` DDL for `evidence`/`verdicts` today (both CHECKs and
`verdicts.model` present, quoted above) · `orchestration/handoffs/U2.3.json` (`migration`: v3→v4,
`additive_only: true`, `rows_lost: 0`, `check_vocabulary: "model|replay|fixture|unknown"`, `added`,
`backfill.old_rows_became: "unknown"`, `no_row_became_model: true`) · `orchestration/handoffs/V2V.json`
(`done/PASS`; boundary re-derived from its own v3 copy, second migrate no-op) ·
`orchestration/handoffs/V2W.json` (`done/PASS`; live store, 13 tables, `schema_version` rows 1–4,
integrity ok, `candidates.producer=replay:10`, `evidence +producer`, `verdicts +producer,+model`) ·
`tests/test_store_v4.py`:187–188 (no row's producer is `model`). **Unit** — U2.3, verified by **V2V**
(logic, on copies) and **V2W** (the live store). *Clause not re-run here:* the second-`init_db` no-op —
re-running it would write the store, so it rests on the two done verifier handoffs.

---

## (ak) [verified] The migration had to be *executed*, and the backup semantics are non-obvious

**Plan assumption** — the plan treats the store as an artifact to be upgraded; it says nothing about
*which* in-place migration entry point is legitimate, nor about which of SQLite's two "backup" notions
is the rollback point.

**What is true** — the live store was migrated **in place with `store.init_db(path)`**;
`migrate_copy` **refuses in-place** by design. Backups: the **SQLite online-backup API copy is
page-normalized** (different sha256, logically identical), so the **rollback point is the byte-exact
pre-image** (`459e16cc…`), and the API copy is a **separate file** (`c0a56928…`). The rollback command
is recorded: `cp state/backups/U0.18-state-pre-v4/state.sqlite state/state.sqlite && rm -f
state/state.sqlite-wal state/state.sqlite-shm`.

**Evidence** — my own `sha256sum`/`stat` today: `state/backups/U0.18-state-pre-v4/state.sqlite` =
`459e16cc875654df…`, 167936 bytes, byte-identical to `state/U2.5_realmirror_before.sqlite`; live
`state/state.sqlite` = `40e8aa0cd1350275…` (v4) · `orchestration/handoffs/U0.18.json` (`backup`:
`byte_exact_source`, `api_backup_sha256: c0a56928…`, `companions`, `rollback_command`,
`migration.method`) · `orchestration/handoffs/V2W.json` (`done/PASS`; "c0a56928 is the separate
`.online-backup-api` sidecar, logically identical … 0 differing rows"). **Unit** — U0.18, verified by
**V2W**. *`reported-only` clause:* the `migrate_copy` in-place refusal (U0.18's method note) — I did
not re-locate that code text in this unit.

---

## (al) [verified; V6G corroboration `reported-only`] The dashboard's authorisation rule

**Plan assumption** — the dashboard is a local operator UI; the plan's §5/dashboard discussion does
not model a non-loopback bind as a distinct authorisation state, and assumes the read routes are the
whole surface.

**What is true** — a **non-loopback bind requires an operator-chosen token**, and that token is
required for **every route, reads included**; loopback keeps anonymous reads and `--token auto`;
**`auto` is refused on a remote bind** because it is usable but not an operator *choice*. The server
**serves 16 routes**: **14 project APIRoutes** (`/` + 11 GET `/api` reads + 2 POST `/api/control`),
**plus a framework route `/openapi.json`** (`openapi_url` defaults on even with `docs_url=None` /
`redoc_url=None`) **plus a `Mount` at `/static`**. The blanket remote middleware wraps the whole
router, so **framework routes and the static mount are gated identically** — the true read surface is
**14**, anonymous-reachable on a remote bind **14 before / 0 after**.

**Evidence** — my own read today: `dashboard/app.py` builds `FastAPI(title="resextract dashboard",
docs_url=None, redoc_url=None)` **without passing `openapi_url`**, mounts `app.mount("/static",
StaticFiles(...))`, and carries **14** `@app.get/post` route decorators ·
`orchestration/handoffs/U6.12.json` (`done`; before-fix `curl …/api/status → 200` with `--allow-remote`
and no token, after-fix `→ 401`, `-H 'x-dashboard-token: …' → 200`, POST control 401→200; 42 CLI + 9
new auth tests, 0 deletions) · `orchestration/handoffs/U6.13.json` (`done`; `routes_served: 16`,
`openapi_url` not passed → `'/openapi.json'` ENABLED, `/static` mount enabled, `/docs`+`/redoc`
disabled, each framework route `anon_remote_status: 401`; "/openapi.json discloses nothing
anonymously; 200 only with token") · `orchestration/handoffs/U6.9.json` (`done`). *`reported-only`:*
**V6G**'s independent arm-by-arm re-check is **not yet on disk** — its handoff is `status: "partial"`
with all three `checks` `verdict: "pending"` and empty `rule`/`tests_assert`/`red_green`.
**Unit** — U6.12 and U6.9.

---

## (am) [verified] The non-loopback bind refusal is a single decision

**Plan assumption** — the CLI's `--host` is the bind control; passing a non-loopback host is the
operator's opt-in.

**What is true** — `check_bind_host` is the **only** decider; an explicit `--host` is **not** an opt-in
(only `--allow-remote` authorises a remote bind); **four entry points agree** (console script,
`python -m resextract`, `-m resextract.cli`, `-m resextract.dashboard`). One of them previously
derived `allow_remote` from `--host` and **bound `0.0.0.0`**; a top-level `src/resextract/__main__.py`
was added so `-m resextract` reaches the same decision.

**Evidence** — `dashboard/app.py`:62 (`def check_bind_host`) and :106 (`bound_host =
check_bind_host(host, allow_remote)`) · `cli.py`:415–419 (imports and consults it, with
`allow_remote = bool(getattr(args, "allow_remote", False))` — no host inference) ·
`dashboard/__main__.py`:45–53 (the removed `… folded into allow_remote here, which bound 0.0.0.0`
comment and the `check_bind_host` call) · `src/resextract/__main__.py` exists and its docstring names
`dashboard.app.check_bind_host` · `tests/test_cli.py`:721–724 (`forbidden =
re.compile(r"allow_remote\s*=[^\n]*(is_loopback|explicit_host)")`, "no source infers `allow_remote`
from an explicit host") · `orchestration/handoffs/U6.9.json` (`done`; four entry points, pre-fix
`python -m resextract` exit 1 "No module named resextract.__main__"). **Unit** — U6.9.

---

## (an) [verified; the U5.15 fix `reported-only`] Claim standing at the docket layer

**Plan assumption** — §3.4's `verdicts`/`claims` vocabulary assumed a declared
`confirmed`/`confirms`/`verified` could be rendered as the docket verdict `CONFIRMS` without asking
*who* produced it.

**What is true** — (i) a declared `confirmed/confirms/verified` **maps to `CONFIRMS`**; (ii) it must be
**capped for a non-model producer**, and the cap must be judged on the **RAW** producer value;
(iii) a **coercing** `str(raw).strip().lower()` let `"Model"`/`"MODEL"`/`"  model  "` render
`CONFIRMS` while `store.producer_is_model(raw)` said `False` — **a fail-open**, reachable via the
unvalidated curated path `cli.py:346` (store rows are CHECK-constrained); (iv) standing should be keyed
off the **`verdicts`** row that assessed the claim, not `candidates.state` — and with **0 verdicts** in
the store, **every claim is bounded** (the honest state). Also, `materialize.PRODUCERS` **includes
`"mixed"`** while `store.PRODUCER_VOCAB` does not, so the two normalisations **disagreed**.

**Evidence** — (i)/(ii) `orchestration/handoffs/U5.13.json` (`done`; `_VERDICT_BY_STATE` at
`materialize.py`:210–218 consumed at `_claim_for` with no model check; the curated claim `C-curated`
renders `CONFIRMS` with no attribution in `dockets/duval/duval-replay-material/MANIFEST.json`;
`assess_cap` at `assess/verdicts.py`:401–406 caps a `CONFIRMS` to `EXTENDS` when not model-produced;
`assess.verdicts.may_back_model_claim IS store.producer_is_model`, corroborated by
`tests/test_store_v4.py`:469–471) · (iii) `orchestration/handoffs/V5D.json` (**`overall: "FAIL"`**,
C2: "raw 'Model'/'MODEL'/'  model  ' UNCAPPED → CONFIRMS with verdict_reason null while
store.producer_is_model(raw)=False", evidence `state/verify/V5D/cap_probe.out` rows 5a–5c; C1: 149
passed across the five docket suites) · (iv) my own read of `materialize.py`:1490–1500 — the standing
map is built from `SELECT v.id, v.claim_id, v.verdict, v.producer, c.candidate_id FROM verdicts v JOIN
claims c …`, and the docstring records "a candidate with no claim, or a claim with no verdict, is
simply absent from the map, which fail-closes it at materialisation" · the vocabulary disagreement, my
own read today: `docket/manifest.py`:81 `PRODUCERS: tuple[str, ...] = PRODUCER_VOCAB + ("mixed",)`
versus `store.py`:54 `PRODUCER_VOCAB: tuple[str, ...] = ("model", "replay", "fixture", "unknown")`.
*`reported-only`:* the **fix by U5.15** — its handoff is `status: "partial"`, `artifacts: []`,
`evidence: {}`. The tree today is *consistent with* a fix in flight (raw membership at
`materialize.py`:542 `if isinstance(raw, str) and raw in PRODUCERS`, the exact-membership refusal at
:1570–1572, and a raw-predicate gate at :1497 `if declared == "CONFIRMS" and not
_store.producer_is_model(producer)`), but a sibling is mid-write on these two files and no verifier's
verdict is on disk. **Unit** — U5.13; the fail-open found by **V5D**, fix by **U5.15** (in flight).

---

## (ao) [verified] The graph stage: provenance was stamped but never read, and a reuse candidate was not required to be usable

**Plan assumption** — a graph on disk at the expected path is a graph the run may reuse; nothing in the
plan distinguishes a graph built for the current HEAD from one built for an earlier one.

**What is true** — `graphify` **already stamps `built_at_commit` (the target HEAD) and
`graphify_version`** in the artifact; what was missing was that **`run.py` never read it**, so an
**already-stale** graph (`6deaed07` vs target HEAD `6c60da5a`) was reused **indistinguishably from
fresh**. The run now reports **`fresh | stale | unverified`** in the plan and the run — **report-only
by default** (the target's HEAD moves continuously, so "stale ⇒ rebuild" would rebuild every run),
with an opt-in to require freshness; missing provenance ⇒ **`unverified`**, never `fresh`. Separately,
a **reuse candidate must be a usable graph** (`regular file; one JSON object; non-empty nodes; links
array`) — a 0-byte/garbage/`{}`/`nodes: []` graph was previously reused as **`status="ok", nodes=0`**.

**Evidence** — my own read today: `run.py`:774 `def _graph_provenance(path, target_head)`, :803
`raw = doc.get("built_at_commit")`, the `no built_at_commit` (:809) and `records
built_at_commit=… but the target HEAD …` (:814) messages; the strings `"fresh"`/`"stale"`/
`"unverified"` and `graphify_version` are present; the decision is centralised at `_reuse_candidate`
(`run.py`:910) and consumed by both plan (:1020) and run ·
`orchestration/handoffs/U8.7.json` (`done`; 35→40 tests, red runs `KeyError: 'provenance'` and
`AssertionError: unrecorded provenance was reported 'fresh'`) · `orchestration/handoffs/U8.6.json`
(`done`; the four unusable-graph cases each `reused: true, mode: "reuse", nodes: 0, status: "ok",
reader_can_tell: false`, and each rejected after the fix) · `tests/test_run.py`:903, :1057–1069,
:1182–1186 (reuse-validity and staleness guards, including "the `unverified` branch … makes `state`
read …") · `orchestration/handoffs/V8B.json` (`done/PASS`). **Unit** — U8.7 and U8.6, verified by
**V8B**.

---

## (ap) [verified] `run`'s report fields: `ok` and `status` are derived, not stored

**Plan assumption** — a run report carries an outcome; the plan's §4 `run` stage reads `ok`/`status` as
report fields that could in principle be set independently of the exit code.

**What is true** — `RunReport.ok` and `RunReport.status` are **derived properties** of the single
stored `exit_code` and **cannot disagree** with it: they are absent from `dataclasses.fields`, and
`setattr`/constructor kwargs are refused.

**Evidence** — my own read today of `run.py`:176–218 — `@dataclass class RunReport` lists fields
ending at `finished_monotonic` (:198), then `@property def ok` (:210–213, "Derived from `exit_code`
(the single source of truth)") and `@property def status` (:215–218, "Derived from `exit_code` via
`status_for` — never a second verdict") · `orchestration/handoffs/U8.5.json` (`done`; the dry/real
divergence fix and the reuse-decision evidence) · `orchestration/handoffs/V8B.json` (`done/PASS`;
`status_fields` check; "25 passed after FULL pycache purge"). **Unit** — U8.5, verified by **V8B**.

---

## (aq) [verified] The assessment write path: a typed `SchemaTooOldError`, no longer swallowed

**Plan assumption** — §3.4 assumes a write path against a current-schema store; nothing in the plan
covers handing a **v3** database to a **write** path.

**What is true** — a v3 database handed to a **write** path raises a **typed `SchemaTooOldError`**
naming found-vs-required versions, and it is **re-raised out of** the per-claim isolation wrapper (an
earlier version was **swallowed by a blanket `except`**, producing a misleading `claims_assessed 0`).
Opt-in `migrate_store=True` migrates a **run-scoped copy**. `insert_verdict` **raises `ValueError`** if
a model id accompanies a non-model producer.

**Evidence** — my own read today: `store.py`:86 (`class SchemaTooOldError`), :625–634 (raises it on a
too-old version), :1281–1289 (`if model is not None and not producer_is_model(producer): … raise
ValueError("model id … may only accompany producer='model' …")`) · `assess/verdicts.py`:483/501/506
(`migrate_store` docstring: "opts in to a **run-scoped copy**"), :532–536 (`raise
SchemaTooOldError(store_path, found_version)`), **:687 `if isinstance(exc, SchemaTooOldError):`** (the
boundary re-raise) · `orchestration/handoffs/U2.6.json` (`done`; "typed error raised, but swallowed by
the per-claim except into `claims_assessed=0`" in the item-1 baseline, `schema_too_old_raised: true`,
147 tests) · `orchestration/handoffs/V2V.json` (`done/PASS`; "typed SchemaTooOldError found-v3/
required-v4 on my own v3 copy; source untouched; opt-in copy migrated v3→v4 rows_lost 0"; C2b "not
swallowed"). **Unit** — U2.6, verified by **V2V**.

---

## (ar) [verified] The lexicon of "who may claim model standing" is one predicate

**Plan assumption** — the plan does not name a producer predicate; it assumes the notion of a
"model-produced" result is expressed once.

**What is true** — `store.producer_is_model` is the single string-level comparison;
`assess.verdicts.may_back_model_claim` **is that same object**; **8 literal `== "model"`/`!= "model"`
comparisons remain** elsewhere (`run.py` 2, `docket/materialize.py` 2, `claims/decompose.py` 2,
`docket/manifest.py` 1, `docket/assemble.py` 1) and **must be judged individually** before any
codebase-wide uniqueness claim.

**Evidence** — my own count today over the source tree: `run.py` 2, `docket/materialize.py` 2,
`docket/manifest.py` 1, `docket/assemble.py` 1, `claims/decompose.py` 2 = **8**, with **0** in
`assess/verdicts.py` (which uses `producer_is_model` and re-exports `PRODUCER_VOCAB`) ·
`store.py`:60 (`def producer_is_model`), :71 ("`assess.verdicts.may_back_model_claim` *is* this
function object"), :1131 (`_producer_is_model` delegating to it) · `tests/test_store_v4.py`:469–471
(identity assertions) and `tests/test_assess_verdicts.py`:719 ("reuse the store vocabulary verbatim") ·
`orchestration/handoffs/U2.7.json` (`done`; 81→82 tests, 0 deletions) and `V2V.json` /
`V2W.json` (`done/PASS`; V2W re-checks the 9→8 literal delta, noting the pre-U2.7 count was not
observed live). **Unit** — U2.7, verified by **V2V**/**V2W**.

---

## (as) [verified] `serve` gained `--docket-root`: pure plumbing

**Plan assumption** — the docket root is a dashboard concern, so a CLI that never passes one is
exercising a dashboard default.

**What is true** — the dashboard's `create_app` **already accepted a directory**; the CLI simply never
passed it, so it fell back to `<cwd>/dockets`. Adding `--docket-root` was **pure plumbing** — no
dashboard edit was needed, and containment was already root-relative.

**Evidence** — my own read today: `cli.py`:437 `def _resolve_docket_root(raw)`, :463 resolution, :479
`dockets_dir=str(docket_root) if docket_root is not None else None` · `dashboard/app.py`:103
`create_app(..., dockets_dir=None, ...)` already in the signature ·
`orchestration/handoffs/U6.7.json` (`done`; `read_first.serve_default_root` "none: `_cmd_serve` called
`create_app(token=…, host=…, allow_remote=…)` only, so `DataLayer` fell back to `Path('dockets')"`;
the flag resolves relative paths against cwd, exits 2 on a missing/file root, and 7 new CLI tests,
16→23, 0 deletions). **Unit** — U6.7.

---

## (at) [verified] The doctor caches a DOWN verdict

**Plan assumption** — the plan treats the doctor as a live probe of the model leg's health; a DOWN
verdict is assumed to be re-derived on each call.

**What is true** — a negative TTL (default **30 s**, configurable, `0` disables) means a **DOWN**
verdict is reused within the window; **only DOWN is remembered**, `force=True` **never** reuses one,
and an explicit operator force **is now forwarded** from the dashboard. **Residual:** a **cold**
control call still pays the full probe cost.

**Evidence** — my own read today: `doctor.py` `DEFAULT_NEGATIVE_TTL_S = 30.0`, `NEGATIVE_TTL_ENV =
"RESEXTRACT_DOCTOR_NEGATIVE_TTL_S"`, `def negative_ttl_s()` with precedence "env var, then
`[doctor] negative_ttl_s` in `config/resextract.toml`, then `DEFAULT_NEGATIVE_TTL_S`. `0` disables
reuse", and "`force=True` always performs a fresh probe" · `dashboard/api.py`:1146
`def doctor_status(self, *, force: bool = False)` → :1155 `report = doctor_mod.run_doctor(force=force)`
· `orchestration/handoffs/U0.17.json` (`done`; 13→20 doctor tests, red-green script) ·
`orchestration/handoffs/V0.18.json` (`done/PASS`; 40/40 harness checks, "cached==fresh
byte-identical", and the correction that in the current *refusing* network state the cache removes
~0 s, 1.4538 s fresh vs 1.6131 s cached) · `orchestration/handoffs/U6.11.json` (`done`; the
force-swallowing repro `state/logs/U6.11_repro.py`, "recorded kwargs on `force=True`: `[{}]`", 63→66
dashboard tests, "ZERO assertions removed") · `orchestration/handoffs/V6C.json` (`done/PASS`;
`force=True→[{force:True}]`, `force=False→[{force:False}]`; residual "wall-clock cold-call ~5 s …
not measured"). **Unit** — U0.17, verified by **V0.18**; forwarding by **U6.11**, verified by **V6C**.

---

## (au) [verified] Method conventions now standing (these cost real cycles)

**Plan assumption** — the plan's unit cards and evidence expectations assume citations stay valid:
line numbers, tree/file hashes and "read-only" database reads are stable across siblings.

**What is true** — (1) **line-number citations drift** as siblings edit files (`run.py:1278→1384`,
`api.py:1052/1061→1155`, `app.py:184/196/216→225/237/257`, `manifest.py:255→309`,
`materialize.py:543→549`, `1602→1645`, `assemble.py:1601→1703`) — **locate by content**; (2) a
**tree/file hash is recipe-dependent** — state the recipe and never cross-compare hashes from
different recipes; (3) a **narrow `__pycache__` purge produced 5 spurious failures** — only a **full**
purge is trustworthy; (4) **opening a SQLite file `mode=ro` can still create `-wal`/`-shm` sidecars** —
use `immutable=1` or copy first.

**Evidence** — I independently re-observed (1) and (2) in this unit: the `app.py` read/rescan/control
doctor sites are at **225/237/257** today (V6C's own correction records "uniformly +41 lines … NOT a
U6.11 defect"), `assess/verdicts.py`'s cap is at 401–406 (U5.13's hint said :401), `api.py`
`doctor_status` is at **1146/1155** (not 1052/1061), and my own read-only store access returned
coherent DDL only because it was opened `mode=ro&immutable=1` — V0.18's `unverified` list still
flags its own read-only dashboard path as "not executed (dashboard/** is a sibling's write path)" ·
(3) `orchestration/handoffs/V5D.json` (C1) passed its 149-test five-file run only after a **FULL**
`__pycache__` purge, and `V2V.json` records the same discipline ("after FULL `__pycache__` purge +
`PYTHONDONTWRITEBYTECODE=1`") · (4) `orchestration/handoffs/U0.18.json` records the `-wal`/`-shm`
companions and the `rm -f` in the rollback command · `orchestration/handoffs/U6.11.json`
(`located_by_content: true`). **Unit** — the convention set is cross-unit; recorded here by U8.9 from
U0.18, U2.6, U2.7, U5.13, U6.11, V2V, V5D, V6C. *Per-clause status:* (1) and (2) I re-verified on
disk; (3) and (4) are taken from those units' `done` handoffs, not re-run here.

---

## (av) [verified] The fail-open family — a genuine plan gap

**Plan assumption** — the plan specified **no producer/provenance discipline** at the candidate,
verdict or claim layers (§3.4 constrains columns and CHECKs, not provenance).

**What is true** — the same class of defect appeared **four times**: a replay candidate stored
indistinguishably from a mined one (§3.4); an **undeclared client defaulting to `model`**; a **docket
claim asserting `CONFIRMS`** with no model check; and a **coercing comparison** that let `"Model"`
through. Each was found by an **independent verifier**, not by the author. **Recorded as a plan-level
correction: every fail-closed gate also needs something that declares the legitimate case**, or it
silently closes the real path too.

**Evidence** — the four instances are recorded above as (ai)/(af)/(an) and V5D: (ai) (replay row stored
indistinguishably, verifier V2's FAIL) · `orchestration/handoffs/U2.2.json` / `U2.3.json` (the
undeclared-client default; `ProducerDeclarationError` and `PRODUCER_VOCAB`) · `V5D.json`
(`overall: "FAIL"`, the coercing route to `CONFIRMS`) · `U5.13.json` (the docket `CONFIRMS` with no
model check). **Unit** — U8.9, recording a plan-level gap whose instances were each found and verified
by a different unit (U2.2/U2.3, U5.13, V5D, V2).

---

*End of the U8.9 append. Entries (a)–(ai) above are unchanged; 13 entries were appended (aj)–(av),
so the ledger now holds **48** entries and the next letter is `aw`.*


---

## (aw) [verified] The graph digest pin — an artifact cannot vouch for itself

**Plan assumption** — `docs/PLAN.md` treats the code-only graph under
`state/kg/<slug>/graphify-out/graph.json` as a reusable input whose provenance is *where* it was
built: `built_at_commit` was read as sufficient evidence that the bytes are the ones that commit
produced.

**What is true** — `built_at_commit` records the **target** HEAD at build time but says nothing about
the **bytes**. `graph.json` has **no `sha256` field** (top-level keys: `built_at_commit`, `directed`,
`graph`, `hyperedges`, `links`, `multigraph`, `nodes`), and the only digest ever computed for it was
computed **and written by the same writer that wrote the bytes** — so whoever can alter the bytes can
rewrite the digest, and an artifact could not vouch for itself. A copy with **5 nodes dropped**
(valid JSON, `built_at_commit` left untouched, bytes `7fca157f055e…` vs the real `4790bbb1111b…`)
was **reused and reported `fresh`**. The fix pins the **expected** digest **outside the artifact** at
`config/graph_pin.toml` (outside the artifact *and* outside gitignored `/state/`, so it survives a
state wipe), exposes `digest_state = match | mismatch | unpinned`, and makes **`mismatch` ⇒ UNUSABLE
by default**: not reused, reported loudly, and **kept on disk byte-for-byte**. An override
`allow_graph_digest_mismatch` reuses it anyway; **no pin ⇒ `unpinned`, still reused** (**no hard
failure** for setups that predate pinning).

**Addendum I verified myself (and it narrows the claim).** The pin's stated durability rests on its
being **committed**, and `config/graph_pin.toml` is **not committed today**: `git ls-files config/`
returns only `config/resextract.toml` and `config/targets.toml`, and `git status --porcelain`
reports **`?? config/graph_pin.toml`** (untracked, and `git check-ignore` says it is *not* ignored).
So the file is *in* the committed-config **directory** but is itself **not yet in git**; the
"survives a state wipe" property holds, while the "reviewable in a git diff" property does **not**
until it is added. The header's own comment ("the committed `config/` directory") describes the
intent, not the current tracked state.

**Residual (recorded, not fixed)** — the pin **detects change, not goodness**: a graph and pin
replaced *consistently*, a truncation **re-pinned to its own digest**, an **unpinned** path, the
**builder's own revision**, and rollback to an **old pinned digest** all stay undetectable.

**Evidence** — `orchestration/handoffs/U8.8.json` (`done`; tampered bytes reused as `fresh`,
`digest_source` "…`graph.json` has NO sha256 field…", pre-fix line "…fresh; graphify not re-run…");
`state/logs/U8.8-repro.txt`, `state/logs/U8.8-live.txt`; `config/graph_pin.toml` (present, 2331 B,
mode `-rw-------`); `src/resextract/run.py`:318,:326 (`allow_graph_digest_mismatch`),
:835–:836 (`GRAPH_PIN_FILE`), :848 `_graph_pin`, :956–:985 (`match`/`mismatch`/`unpinned`,
`require_fresh_graph`), :1042–:1045. **Addendum re-verified in this unit**: `git ls-files config/`,
`git status --porcelain config/graph_pin.toml`, `git check-ignore -v config/graph_pin.toml`.
**Unit** — U8.8; the untracked-pin addendum found and recorded by **U8.10**.
*Per-clause status:* mechanics `verified`; the residual is U8.8's own recorded limitation.

---

## (ax) [verified] The graph stage: provenance that nobody read, and a reuse gate that accepted anything

**Plan assumption** — reusing the existing code-only graph is safe because the artifact *records*
`built_at_commit` / `graphify_version`, and any JSON at the expected path is the graph.

**What is true** — the artifact **already** recorded `built_at_commit`/`graphify_version`; what was
missing is that **`run.py` never read it**, so an **already-stale** graph (`6deaed07` vs the target
HEAD `6c60da5a`) was reused **indistinguishably from a fresh one**. The run now reports
**`fresh | stale | unverified`** in the plan **and** in the run — **report-only by default** (the
target HEAD moves continuously under a foreign actor, so "stale ⇒ rebuild" would rebuild on *every*
run), with `require_fresh_graph` as the **opt-in** to refuse staleness; **missing provenance ⇒
`unverified`, never `fresh`**. Separately, a **reuse candidate must be a usable graph** — a regular
file, **one JSON object**, **non-empty `nodes`**, and `links` an **array**. A 0-byte, non-JSON
garbage, `{}`, or `nodes: []` graph was previously reused as **`status="ok", nodes=0`** with **no
way for the reader to tell**. Edge counts came from a `getattr(stats, "links", 0)` that **always
yielded 0** and now read **`stats.edges`** (**7102**).

**Evidence** — `orchestration/handoffs/U8.7.json` (`done`; `state/logs/U8.7/revert.py g` →
`KeyError: 'provenance'`, `h` → `AssertionError: unrecorded provenance was reported 'fresh'`);
`orchestration/handoffs/U8.6.json` (`done`; four rejected cases each `reused: true → after_fix
reused: false, rejected_reported: true`, `reader_can_tell: false` before);
`state/logs/U8.6_evidence.txt`:18 and `state/logs/U8.6_live_run.txt`:8 ("edges=7102, mode=reuse,
nodes=2685, sha256=4790bbb1111b"), `state/logs/U8.6_pytest_after_restore.txt`:379
(`assert stage.counts["edges"] == 7102`); `src/resextract/run.py`:313–:317 (`require_fresh_graph`,
"Absent (False) the default is report-only reuse"), :783–:822 (`stale`/`unverified` derivation),
:903–:904, :926–:938, :1028–:1029 (`stats.edges`). **Unit** — U8.7 and U8.6.
*Per-clause status:* I re-read the `run.py` provenance/usability/`stats.edges` code on disk and the
7102/2685 counts in U8.6's logs. The **behavioural** verification is **`reported-only`**: V8B
(`done`, verifying U8.5) is not this clause's verifier, and **V8C is `partial`** (its handoff records
only `"next_unit_hint":"starting C1"`), so the intended independent re-run of A/B has **not landed**.
**V8C in flight — treated as `reported-only`.**

---

## (ay) [verified] `RunReport.ok` / `.status` are derived from `exit_code`, not stored

**Plan assumption** — a run report carries its own verdict fields, so `ok`/`status` and `exit_code`
are independent values that could disagree.

**What is true** — `RunReport.ok` and `RunReport.status` are **`@property` values computed from the
single stored `exit_code`** and therefore **cannot disagree with it**. They are **absent from
`dataclasses.fields`**, and both `setattr` and constructor kwargs for them are **refused**. There is
exactly one source of truth for a run's outcome.

**Evidence** — `src/resextract/run.py`:183 (`exit_code: int = EXIT_OK`), :200 and :210–:217
(`@property` `ok` "Derived from `exit_code` (the single source of truth)", `status` "Derived from
`exit_code` via `status_for` — never a second verdict"); `orchestration/handoffs/U8.5.json`
(`done`; finding list F1/F2/F3). **Unit** — U8.5, verified by **V8B**.
*Per-clause status:* I re-read the two properties and the stored field on disk (`verified`); V8B's
red→green/release-sha verification is **taken on report** (`orchestration/handoffs/V8B.json`:
"U8.5's three fixes are verified (F1/F2/F3 PASS, red->green sha-proven, release sha 18d8bc32
matches)").

---

## (az) [verified] The dashboard's authorisation rule, and the census that was wrong

**Plan assumption** — the dashboard's read surface is `12` routes ("`/` + 11 GET `/api` reads"), and
gating the project's API reads is equivalent to gating what the server serves.

**What is true** — a **non-loopback bind requires an operator-chosen token**, required for **every
route, reads included**; loopback keeps anonymous reads and `--token auto`; and **`auto` is refused
on a remote bind** because it is usable but not an operator *choice*. The server **serves 16
routes**: **14 project APIRoutes** (`/` + 11 GET `/api` reads + 2 POST `/api/control`) **plus a
framework route `/openapi.json`** (it survives `docs_url=None`/`redoc_url=None`, because
`openapi_url` was never passed and defaults on) **plus a `Mount` at `/static`**. The **blanket remote
middleware wraps the whole router**, so framework routes and the static mount are gated
**identically** — a **blanket gate is what covers routes nobody enumerated**. The pre-fix count of
**12** was right for *project-authored* reads and **wrong as a census of what the server serves**:
true read surface **14**, anonymous-reachable on a remote bind **14 before / 0 after**.

**Evidence** — `orchestration/handoffs/U6.13.json` (`done`; `construction_call` at `app.py:114`
"`openapi_url` NOT passed", `docs_url: "None"`, `redoc_url: "None"`,
`openapi_url: "'/openapi.json' … ENABLED"`, `routes_served: 16`, `project_routes: 14`,
`framework_routes` with `/static` `Mounted app.py:388`, `/openapi.json` anon-remote **401** and
"200 only with token: 4975 B schema"), `state/logs/U6.13-evidence.txt`,
`state/verify/U6.13/report.md`; `orchestration/handoffs/U6.12.json` (`done`; LAN runs — **before**
`192.168.2.187:8941/api/status` **200**, **after** **401**, with `x-dashboard-token` **200**, POST
`/api/control/rescan` **401 → 200**); `orchestration/handoffs/U6.9.json` (`done`; the four
entry points, `-m resextract.dashboard` pre-fix `exit_code 124, bound true 0.0.0.0:8971`).
**Unit** — U6.12 and U6.9, checked by **U6.13**, verified by **V6G**.
*Per-clause status:* I **re-counted the census on disk in this unit** — `grep -cE
'@app\.(get|post|put|delete)' src/resextract/dashboard/app.py` = **14** (the 14 sites at
:173/:185/:189/:193/:198/:202/:206/:215/:219/:223/:227/:233/:253/:378), `FastAPI(title=…,
docs_url=None, redoc_url=None)` at **:114** with no `openapi_url`, and `app.mount("/static", …)` at
**:388** — so 14 + `/openapi.json` + `/static` = **16** is `verified`. V6G's live LAN arm is **taken
on report** (`orchestration/handoffs/V6G.json`: "U6.12's rule holds on every arm I could test and
both guards are sha-proven red->green").

---

## (ba) [verified — code only] The `auto`-token asymmetry: a weak literal secret on a remote bind

**Plan assumption** — `--token auto` has one meaning at every dashboard entry point, and `auto` is
never itself a secret.

**What is true** — `python -m resextract.dashboard --token auto` was **not refused**: that entry
point had **no `auto` keyword**, so it **bound a remote listener with the literal weak secret
`auto`** — anonymous requests **401**, but `x-dashboard-token: auto` **200**. **Not an anonymous
leak**, which is exactly why it was a subtle trap: the guard looked like it was working.
**The fix has landed on disk** (U6.14 → recovery U6.15): `dashboard/__main__.py` now refuses a
non-loopback bind when the raw token is **empty or `auto`** ("'auto' is not an operator-chosen
secret"), and resolves `auto` to a fresh **`secrets.token_urlsafe(32)`** that the caller prints, so
the **literal string `auto` is never the secret**; `cli.py` applies the same rule.

**Evidence** — found by `orchestration/handoffs/V6G.json` (`done`; "Two follow-ups … (1) align
entry-point semantics so `python -m resextract.dashboard` …"); fix at
`src/resextract/dashboard/__main__.py`:53–:92 (`raw.lower() == "auto"` → `secrets.token_urlsafe`,
`if not is_loopback(bound) and raw_token.lower() in ("", "auto")` → refuse, :122–:123 prints the
generated secret "V6G asked for this") and `src/resextract/cli.py`:421–:433 (`auto` refused on a
non-loopback bind, `token = secrets.token_urlsafe(32) if raw.lower() == "auto"`); recovery handoff
`orchestration/handoffs/U6.15.json` (**`partial`** — `fix: {}`, `red_green: {}`,
`live: {}` unfilled; its predecessor `U6.14.json` is `partial`, `blocker: "in flight"`).
**Unit** — V6G found it; U6.14 → **U6.15** (a **running sibling** of this unit) fixed it.
*Per-clause status:* the **guard text is `verified` on disk** as I read it above. The **behavioural
arm is `reported-only`**: I bound no listener and ran no test suite, and **U6.15's own handoff is
`partial` with empty `red_green`/`live`** — so "the literal `auto` no longer binds remotely" rests on
the code path, not on a re-run.

---

## (bb) [reported-only] Evidence strength: a green guard in a test is not proof of exposure

**Plan assumption** — a guard whose test goes red→green has demonstrated that the exposure is closed.

**What is true (method note)** — a guard can be **green for the right reason in a test and still
prove less about exposure**. In the auto-token test, **`uvicorn.run` is monkeypatched to a
sentinel**, so the **red case never actually binds** — that is a **logic red**, not an exposure red.
The **real** unguarded path **does** bind: reverting the read gate *as well* produced **anonymous
`GET /api/status` = 200 with the store payload on the LAN** — a genuine leak. **The rule: verify
exposure by binding a listener, not by argument alone**, and be explicit about which red a guard
demonstrates.

**Evidence** — `orchestration/handoffs/V6G.json` (`done`, recording the monkeypatched `uvicorn.run`
sentinel and the LAN 200-with-payload after reverting both gates).
**Unit** — V6G. *Per-clause status:* **`reported-only`** — this unit ran **zero network operations
and no test suite**, so I neither re-bound the listener nor re-reproduced the anonymous 200; the
finding is V6G's, recorded here as its method note.

---

## (bc) [verified] The claim-standing cap, and a live fail-open found after it "passed"

**Plan assumption** — a declared `confirmed`/`confirms`/`verified` maps to `CONFIRMS`, and that
mapping is safe as written.

**What is true** — the map is only safe **capped for a non-model producer**. A verifier then found
the cap **coerced the value** (`str(raw).strip().lower()`) **before judging it**, so a raw `"Model"`
or `"MODEL"` rendered **`CONFIRMS`** while the predicate said otherwise — reachable through the
**unvalidated curated path** (`cli.py` ~:346, the `--lane-file`/`LaneSpec.from_json` route); store
rows are **CHECK-constrained**, so the curated path is the way in. The fix judges the **raw** value
by **exact membership** and **caps fail-closed with a recorded reason** rather than raising, because
the docket layer must stay **total** for a rendering typo while **never conceding model standing**.
Standing is now keyed off the **`verdicts` row** (`verdicts.claim_id = claims.id` **and**
`claims.candidate_id = candidates.id`, latest wins; **there is no persisted `settled_by` column**),
and **no verdict ⇒ never `CONFIRMS`** — with **0 verdicts** in the store, **every** claim is bounded,
which is the honest state. Also `manifest.PRODUCERS = store.PRODUCER_VOCAB + ("mixed",)` — the
vocabulary is **imported, not restated**, and `mixed` is **aggregate-only**.

**Evidence** — `orchestration/handoffs/U5.13.json` (`done`; "`C-curated`" rendered `CONFIRMS` with
**no producer/assessor field** in `MANIFEST.json`, "status_map_has_model_check: false"),
`orchestration/handoffs/V5D.json` (`overall: "FAIL"`, the coercing route to `CONFIRMS`), and
`orchestration/handoffs/U5.15.json` (`done`; `item1_coercion` raw `"Model"` → `rendered_before:
"CONFIRMS"`, `predicate_raw: false`; fix "exact `in PRODUCERS` membership test; no `strip()`/`lower()`
anywhere on the decision path"), 154 tests / 0 deletions. Re-verified in this unit on disk:
`src/resextract/docket/materialize.py`:532–:545 (`_normalise_producer` — "No `strip()`, no `lower()`
… `"Model"`/`"MODEL"`/`"  model  "` are **not** `model`", returning `"unknown"`), :1485–:1500
(`_verdicts_by_candidate`, "There is **no `settled_by` column** in the store … the highest
`verdicts.id` wins"), :311–:318; `src/resextract/assess/verdicts.py`:401–:406 (the cap
"`[capped at EXTENDS: … not model-produced … cannot assert CONFIRMS]`"); `docket/manifest.py`:81
(`PRODUCERS: tuple[str, ...] = PRODUCER_VOCAB + ("mixed",)`); `cli.py`:343–:351 (the curated
`--lane-file` route; U5.13's hint said :346 — drift noted). **Store, opened
`file:state/state.sqlite?immutable=1` (sha **`40e8aa0c`**, v4, not written):** `verdicts` = **0**,
`claims` = **0**, `candidates` = 10, and `pragma table_info(claims)` returns **no `settled_by`**.
**Unit** — U5.13; the fail-open was found by **V5D** and fixed by **U5.15**.
*Per-clause status:* code, the `PRODUCERS` derivation and the store counts are `verified`; the
independent verification is **`reported-only`** — **V5F is `partial`** (`"next_unit_hint":"in
progress"`) and **`V5G.json` does not exist on disk**, so neither has landed.

---

## (bd) [verified] Method conventions added since the last merge

**Plan assumption** — the plan's evidence expectations assume that citations and hashes stay valid
and that reading state is side-effect-free.

**What is true** — four conventions have now cost real cycles and are standing:
(1) **quote a line number as a hint** — drift is routine, so **locate by content**; the recorded
drift set has grown (`run.py:1278→1384`, `api.py:1052/1061→1155`, `app.py:184/196/216→225/237/257`,
`manifest.py:255→309`, `materialize.py:543→549`, `1602→1645`, `assemble.py:1601→1703`);
(2) **a tree/file hash is recipe-dependent** — the same docket trees have been hashed **four**
different ways by four units, so **state the recipe and never cross-compare**;
(3) **open SQLite with `immutable=1`** — a plain `mode=ro` open **can create `-wal`/`-shm`
sidecars** in a directory you believed read-only;
(4) **backgrounded processes die with their shell** (`--die-with-parent`), so a server must be
**started, probed and killed inside one invocation**.

**Evidence** — `src/resextract/run.py`:313–:317 (provenance/opt-in), `_graph_pin` at :848,
`_verdicts_by_candidate` at `materialize.py:1485`, the cap at `assess/verdicts.py`:401–:406 and
`cli.py` `main` at :547 — all **content-anchored** this unit, not line-anchored;
`orchestration/handoffs/U5.13.json` (hint `assess/verdicts.py:401`), `U5.15.json` (cap verified at
"401-406"), `U6.13.json` (`app.py:114`, `/static` at `app.py:388`), `U8.6.json`/`U8.7.json` (the
`run.py` provenance sites); `orchestration/handoffs/U6.15.json` — `env_note`: "server started+probed
+killed inside one bash call (**die-with-parent**)" — and this unit's own store read used
`file:state/state.sqlite?immutable=1` on sha **`40e8aa0c`** and left it byte-identical.
**Unit** — cross-unit; recorded here by U8.10. *Per-clause status:* (1), (2) and (3) are
`verified` in this unit (I re-located each site by content and re-read the store `immutable=1`);
(4) is taken from **U6.15**'s `env_note` (`reported-only`). Clauses (1)–(3) partly restate (au);
what is **new** here is the expanded drift set and the die-with-parent rule.

---

*End of the U8.10 append. Entries (a)–(av) above are unchanged; 8 entries were appended (aw)–(bd),
so the ledger now holds **56** entries and the next letter is `be`. Section I (the fail-open family)
was **already recorded as (av)** by U8.9 and is deliberately **not** duplicated here.*

---

## (be) [verified] The uniqueness claim is qualified: one *scalar bare-literal comparison*, not one spelling

**Plan assumption** — §3.4/§4 leave the producer vocabulary to the store; the natural reading, and
the reading `(ar)` above recorded, is that "who may claim model standing" is expressed in exactly
one place, so the `"model"` literal cannot drift.

**What is true** — the quotable form is now, verbatim from U2.12: *"`store.producer_is_model` is the
only **scalar bare-literal model-standing comparison** in `src/resextract` — the only place that
decides model standing by testing a single producer value against the `"model"` literal. It is
**NOT** the only place `"model"` is spelled, and **NOT** the only producer comparison overall
(`docket/assemble.py:1690` compares against the second vocabulary `"mixed"`)."*

The **criterion** that makes it usable: a **declaration site** spells the literal because the
vocabulary **must be written somewhere** (`PRODUCER_VOCAB`, `MODEL_PRODUCER`, the SQL CHECKs, and
the five functions that `return` a producer). A declaration **establishes a value and duplicates no
rule**, so it is legitimate and **not** a counterexample. A **comparison** **re-derives** the
model-standing decision against the literal; **that** is the rule, and only its duplication risks
drift.

The **count correction**: *"`store.py` contains 0 `"model"` literals"* is **false**. Measured today:
**15** lines carry a double-quoted `"model"` (54, 57, 66, 453, 511, 525, 887, 914, 926, 1057, 1085,
1103, 1248, 1301, 1318) plus **4** single-quoted SQL CHECKs (489, 509, 536, 538) = **19 lines**
(union). The true statement is **"0 bare-literal producer *comparisons*."**

**Method lesson** — a **regex census undercounts**. U2.10's `== "model"` / `!= "model"` pattern gave
a clean 8→6 delta; verifier V2.11 then found **two real producer-literal comparisons the pattern
could not match** — `docket/materialize.py:562 if seen == {"model"}:` and
`docket/materialize.py:1549 value if value in ("model", "replay") else "unknown"` — so the honest
producer-literal count is **≥10 (12 with the two exclusions named in `(bf)`)**. **A census answers
"how many look like this", not "how many are there".**

**Evidence** — re-run by this unit: `grep -n '"model"' src/resextract/store.py` → 15 lines;
`grep -n "'model'" src/resextract/store.py` → 489, 509, 536, 538; union → 19;
`src/resextract/store.py:57` (`MODEL_PRODUCER = "model"`), `:60` (`def producer_is_model`);
`src/resextract/docket/materialize.py:562`, `:1549` (both read); `docket/assemble.py:1690`.
The false phrasing survives **only** in `orchestration/VERDICTS.md:1652` and
`orchestration/units/V2.11.md:27` — historical records, deliberately not edited. This entry
**supersedes** `(ar)` (`:967`), which is **not** edited. Sources: U2.10 (map + delegation), V2.11
(falsification), U2.12 (correction). **Unit** — U2.12; sources re-verified here by U8.12.

---

## (bf) [verified] Literal delegation: two of eight delegated, six remain, two near-misses correctly excluded

**Plan assumption** — `(be)`'s qualified claim still lists eight comparison sites; the plan assumes
the lexicon is centralised, so those eight are debt against `store.producer_is_model`.

**What is true** — **two** of the eight are now **delegated** (`claims/decompose.py`, at **496/661**);
**six remain**, all judged **safe to delegate**, in files owned by other units: `run.py:1247/1292`,
`docket/materialize.py:577/1787`, `docket/manifest.py:321`, `docket/assemble.py:1688`. Two
**near-misses were correctly EXCLUDED** and **must not be blind-replaced**: `materialize.py:566`
`"model" in seen` (set membership over *derived* values collapsing to `"mixed"` — no scalar to hand
the predicate) and `assemble.py:1690 producer == "mixed"` (the **second vocabulary**,
`PRODUCERS = store.PRODUCER_VOCAB + ("mixed",)`, imported at `assemble.py:48`). **The two
census-missed forms are open follow-ups** with recommended corrections, not yet applied:
`:562 → if seen == {store.MODEL_PRODUCER}:`; `:1549 → a PRODUCER_VOCAB-membership helper`.

**Evidence** — read this unit: `claims/decompose.py:496` ("Qualified: `store.producer_is_model` is
the only *scalar…") and `:661` ("Delegated (U2.10): `producer` is merely a declared string") —
i.e. the delegation is *documented at the site*, since comments were added above, the lines moved
**493→496** and **656→661**; `docket/materialize.py:562` (`if seen == {"model"}:`), `:566`
(`if "model" in seen:`), `:577` (`if producer != "model":`), `:1549`, `:1787`;
`docket/manifest.py:321` (`if producer == "model":`); `docket/assemble.py:1688`, `:1690`, and the
`PRODUCERS` import at `:48`; `orchestration/handoffs/U2.12.json` (`done`), `U2.10.json` (`done`),
`V2.11.json` (`partial`, with the `:562`/`:1549` follow-up in its `next_unit_hint`).
Sources: U2.10, verified by V2.11, corrected by U2.12. **Unit** — U2.12; sites re-verified here.

---

## (bg) [verified; the independent output verification is `reported-only` — V5G] The one-time re-render: what it repaired and its exact shape

**Plan assumption** — §re-assembly treats a manifest as sufficient input to reproduce a docket tree:
a bare `assemble` pass over an existing manifest should rebuild an equivalent docket.

**What is true** — a **bare** re-assembly of a **pre-`U5.14`** manifest **loses information**: the H1
collapses to the **lane slug** and the `EVIDENCE.md` prose is **destroyed**. So the two real dockets
were re-rendered **once**, supplying **both fields once** (`lane.title` from the backup tree's H1; an
evidence list rebuilt from the material rows), and **then** a **second BARE pass was proved stable**.

**Results** — *replay-material*: H1 → `Duval replay-sourced material`, `EVIDENCE.md` **120 → 151**
lines, contexts **0 → 8 each exactly once**; *u55-pinned*: H1 → `Duval — commit-pinned material
(U5.5)`, **23 → 86** lines, contexts **0 → 9 each once**. Material **byte-identical** (8/8, 9/9);
`blob_sha` **6/6** re-matched via `git rev-parse` for u55-pinned (0/0 for replay-material);
**banner 2 → 15** files. New manifests `9b6a577e1402fe41841e153a485e4b044a945a5f8bf05a59c2268df6086cd130`
and `445032f78851b8171c00dca3d95d7ed6660dbf36d903bc156027c11b44a33a07`.

The **banner enumeration is 15, not 14** — `repro/run.sh` was deliberately included (a `# PROVENANCE`
line after the shebang, in the target tree, not in this workspace); `BANNER_EXEMPT`
(`docket/assemble.py:1774`) states the reasons for `HISTORY.md` (append-only: a stamp would
accumulate) and `MANIFEST.json` (`generated_by.producer` already is the provenance field). **That is
a decision, not an anomaly.**

**`window_sealed` is `true` for u55-pinned but `null` for replay-material, and that is correct** —
the target's HEAD has moved past that docket's `target.head_sha` (`3982f261`), so sealing would be a
**false claim**. The code keeps the inheritance honest instead: `assemble.py:584–618` inherits a
previous `window_sealed` only as a **historical fact**, and refuses to inherit it when material bytes
changed (it emits "`window_sealed=… NOT inherited: material bytes …`").

**Evidence** — `state/verify/U5.18/result.json`, read this unit: `banner_count` 2 (before) → 15
(`banner_count_15: true`), `window_sealed` `null` (replay) / `true` (u55), `evidence_lines` 120/151
and 23/86, `material_identical_to_backup: true`, the two manifest sha256 values above; plus
`src/resextract/docket/assemble.py:1774` (`BANNER_EXEMPT`) and `:584–618` (`window_sealed`
inheritance, read here). Gated on `V5E` (`done`: "the one-time re-render is safe PROVIDED it supplies
BOTH fields once") and `U5.17` (`done`). **Unit** — U5.18. *Per-clause status:* the **result** is
verified from the on-disk harness output; the **independent verification of the output** is
`reported-only` — **V5G is `partial`** (its `next_unit_hint` still carries an F1 follow-up), so the
result is **not** independently credited here.

---

## (bh) [verified; the test-isolation fix is `reported-only`] Store resolution is now one boundary, and `mode=ro` leaked sidecars

**Plan assumption** — the plan assumes `RESEXTRACT_STATE_DB` isolates a run: set the env var and the
dashboard, the CLI and the tests all read that store.

**What is true** — **before U6.16 the precedence was incoherent**: `store.default_db_path()`
(`store.py:123`) and `default_layer()` (`dashboard/api.py:1411`) **honoured**
`RESEXTRACT_STATE_DB`, but `DataLayer.__init__` (`api.py:394/409`), and therefore `create_app`
(`app.py:110`), **ignored it** and resolved to the **real** `state/state.sqlite`. This was
**demonstrated, not inferred**: two units had already started servers believing the store was
isolated while the dashboard read the real one — an isolation mechanism that **half-works is worse
than none**, because it produces **confident containment claims that are false**.

**After** — **one boundary** `api.resolve_store(explicit) -> (Path, source)` (`api.py:359`), used by
**both** the app and the CLI; precedence **explicit `--store`/`store_path` > `RESEXTRACT_STATE_DB` >
cwd `state/state.sqlite`** (`api.py:346–371`); `DEFAULT_DB_PATH` imported from `store.py` (`api.py:39`,
**one** definition); and the resolved path is **observable** — `DataLayer.store_path` /
`.store_source` / `.resolution()` (`api.py:409/424–433`), published into `app.state.dashboard`
(`app.py:122`). Enforce at the boundary, not at instances.

**The sidecar leak** — plain `mode=ro` opens **created `state/state.sqlite-wal`/`-shm`**, and running
`tests/test_dashboard_auth.py` **alone reproduced it**: the test reads the **real** store, so it is
neither isolated nor side-effect-free (its result can depend on the store's contents). U6.16 removed
the two empty sidecars. *`reported-only`:* **a fix isolating that test file is in flight — U6.17**
(its handoff reports the residual, same bug class, now scoped to `tests/test_cli.py:343`/:419).

**Evidence** — read this unit: `src/resextract/dashboard/api.py:359–371` (`resolve_store`, the three
source constants and the documented precedence), `:394` (`class DataLayer`), `:409`
(`self.store_path, self.store_source = resolve_store(store_path)`), `:424–433` (`.resolution()`),
`:1411` (`default_layer`); `src/resextract/dashboard/app.py:110–122`; `src/resextract/store.py:122–125`
(`default_db_path`). Live check by **U6.16** (verified): with the env var set to a copy, `/api/status`
reported the copy and `candidates.total` **0** vs the real **10**. Sources: U6.16 (verified live),
U6.17 (residual, in flight). **Unit** — U6.16; boundary re-verified here by U8.12.

---

## (bi) [reported-only] The doctor can already report a live core dependency as DOWN — it is a classification bug

**Plan assumption** — §health/doctor assumes the per-leg bound is permissive enough that a live
dependency is reported UP, and that "contributing to a DOWN" is a cost issue.

**What is true** — verifier `V0.21` **tested** rather than accepted the argument that tightening the
doctor's per-leg bounds would manufacture a failure, and both **confirmed** and **falsified** parts
of it. **Confirmed:** SearXNG is alive **8/8** on a direct probe with min/median/max
**0.75 / 1.7584 / 8.232 s**; monkeypatching the bound to **2.0 s** flips **2/6** samples to DOWN
while the service works. **Falsified:** the **current 5.0 s bound already flips 1/6** (2/8 in one
sweep) — so **the doctor can already report a live core dependency as DOWN**, and *"all legs are
below the existing 5 s bound"* is **false**. The **exit code** is unchanged (`['Occamy']` vs
`['Occamy','SearXNG']` both exit 2), which is exactly why the wrong **cause** can hide behind a right
headline. **The verdict still stands:** **do not tighten** (it would make the false DOWN more
frequent) and **no cost change is safe inside `doctor.py`**; the real lever is **how often**
`run_doctor` is called, already bounded by a **20 s** doctor cache (`api.py:1148–1155` as reported).
**The defect is a CLASSIFICATION bug, not a threshold one:** a **timeout** conflates *slow* with
*absent*; the honest fix distinguishes them (a cheap liveness probe succeeding while the full read
times out ⇒ degraded, not down).

**Evidence-integrity find** — three tests cited `state/logs/U0.19-{searxng,measure}.json` /
`U0.19-redgreen.txt`, which **do not exist**, so that unit's constants (**1.747**, **3.50**) are
**unverifiable**, and one of its log rows is **self-inconsistent** (fresh **1.203** < share
**3.256**). **A test citing a file that is not there looks like provenance and proves nothing.**

**Evidence** — `orchestration/handoffs/V0.21.json` (`done`, with the explicit "no cost change is
justified inside `doctor.py`" hint). *`reported-only` for every number above:* this unit ran **zero
network operations, zero tests** — the probe timings, the 2.0 s monkeypatch and the 5.0 s flip are
**V0.21's measurements**, taken on report. *`reported-only`:* **a fix is in flight — U0.22**
(`doctor.py`, `tests/test_doctor.py`; no handoff on disk yet). Sources: V0.21. **Unit** — V0.21.

---

## (bj) [verified as code; re-verification `reported-only` — V8C′] Graph-chain hardening: three defects closed, and the control's boundary

**Plan assumption** — `(aw)`/`(ax)` establish the graph digest pin as the control; the plan assumes
"verify the graph" means the pin is checked and a mismatched or absent pin is refused.

**What is true** — an earlier verifier (`V8C`) returned **PARTIAL** on `U8.6`/`U8.7`/`U8.8` with three
defects, which `U8.11` then fixed:
(1) **the `ok`-with-zero-nodes hole** — `nodes:[100k ints]` yielded `status="ok", nodes=0` because
`nodes` was checked only for **non-emptiness**, never **element type**; fixed by requiring **every**
element to be a JSON object, checked for **all** elements — justified because the JSON parse is
already `O(len(nodes))`, so the walk is cheaper than the parse and **cannot be gamed by a valid
prefix**;
(2) **the digest was compared in 12 hex characters** — `_graph_digest` truncated, so a **wrong-tail**
pin reported *"matches the pinned digest"* at **48-bit effective strength**; fixed to full **64** hex
for comparison, a **display-only** 12-char form, comparison at `min(len,64)`; a short pin is
**accepted but reported loudly** (`PIN ABBREVIATED`, `REDUCED STRENGTH`). **`config/graph_pin.toml`
needed no rewrite** — it already carried the full digest;
(3) **the pin failed open, quietly** — missing/malformed/empty/wrong-key/unreadable all degraded to
`unpinned` ⇒ **reuse**, visible only as a clause. Now discriminated: **missing → reuse + LOUD note**
(*absence ≠ deletion*, and refusing would break every fresh setup); **malformed / unreadable / empty
→ refuse** (*present-and-broken ≠ never-set-up*); **keyed on another path → reuse + loud note**; and
**`require_fresh_graph` now also refuses `unverified`** (the opt-in means *"do not trust what I
cannot vouch for"*), while the default and the genuine **STALE** path are unchanged.
**The control's boundary, confirmed by experiment:** an attacker who can write **only** `graph.json`
is caught; one who can **also write/delete/re-key the pin** is **not** — a consistent replacement is
undetectable.

**Evidence** — read this unit: `src/resextract/run.py:852` ("sha256 is 64 hex characters. A pin
supplying fewer is an *abbreviation*"), `:869–872` (`min(len, 64)`, "U8.11 item 2"), `:881`
(`width = min(len(a), len(b), 64)`), `:1122` (the full 64-hex digest). *`reported-only`:* the
element-type walk (defect 1) and the pin-state discrimination (defect 3) are **U8.11's changes**,
taken from its `done` handoff and not re-run here (this unit runs **no test suite**). *`reported-only`:*
**the re-verification is in flight — V8C′** (`U8.11`'s `next_unit_hint` asks it to re-run
`tests/test_run.py` (50) and the 4 revert-restore checks). Sources: U8.6, U8.7, U8.8 (design), V8C
(defects), U8.11 (fixes). **Unit** — U8.11.

---

## (bk) [verified] The pin file is untracked — a checkpoint requirement (cross-reference, not a duplicate)

**Plan assumption** — `(aw)` establishes that the graph must not vouch for itself, so the pin must be
an artifact outside the graph.

**What is true** — `config/graph_pin.toml` is **untracked in git** (two verifiers confirmed; entry
`(aw)` already records this — **not duplicated here**). Re-verified today: `git ls-files config/`
lists only `config/resextract.toml` and `config/targets.toml`, and
`git ls-files --error-unmatch config/graph_pin.toml` fails with *"did not match any file(s) known to
git"*. Its content is **genuine** (a `# WHY THIS FILE EXISTS (unit U8.8)` header and the full
digest) and matches the real graph today, so no run refuses — but a `git clean -fd` or a fresh clone
**loses the pin**, after which the digest control silently degrades to `unpinned` ⇒ **reuse**.

**The checkpoint requirement** — the file **must appear in `git ls-files` after staging**; treat
"pin tracked" as a gate condition, not a cosmetic tidy-up.

**Evidence** — `git ls-files config/` → `config/resextract.toml`, `config/targets.toml` (read this
unit); `git ls-files --error-unmatch config/graph_pin.toml` → exit non-zero; `head -8
config/graph_pin.toml` (read). **Cross-reference:** `(aw)` — the untracked fact is **already
recorded there**; what is added here is only the checkpoint requirement. **Unit** — U8.12
(re-confirmed); original finding by the two verifiers cited in `(aw)`.

---

## (bl) [verified] One new method convention: inspect a file by reading it, not by `sed`; and the drift set is now nine

**Plan assumption** — the plan's evidence expectations assume that reading state is side-effect-free
and that citations stay valid.

**What is true** — one convention **not** recorded at `(bd)`: **inspect a file by reading it, not by
a `sed` peek** — a `sed` peek does not satisfy the read-before-edit policy and costs extra calls.
Everything else in this family is **already recorded at `(bd)`** and is **cross-referenced, not
duplicated**: quote a line number as a **hint** and locate by content; open SQLite with
**`immutable=1`** (a plain `mode=ro` open can create `-wal`/`-shm` sidecars — see `(bh)` for the
live instance); backgrounded processes die with their shell (`--die-with-parent`), so start, probe
and kill inside **one** invocation; and a tree/file hash is recipe-dependent.

**The drift set is now nine** — it grew again in this build: `claims/decompose.py` **493→496** and
**656→661**, because *comments were added above them* (see `(bf)`, where the two sites are located by
content, not by the numbers). Line numbers are hints; the **content** is the address.

**Evidence** — `(bd)` above (conventions 1–4, already recorded); this unit's own method: every one of
`store.py`, `materialize.py`, `manifest.py`, `assemble.py`, `dashboard/api.py`, `dashboard/app.py`
was located **by content** and read, and the two `decompose.py` sites were found by their comment
text, which is exactly how the 493→496 / 656→661 drift was measured. **Unit** — cross-unit; recorded
here by U8.12.

---

*End of the U8.12 append. Entries (a)–(bd) above are unchanged; 8 entries were appended (be)–(bl),
so the ledger now holds **64** entries and the next letter is `bm`. Sections A–H of the U8.12 card are
covered by (be)–(bl) respectively; the in-flight items named above (V5G's output verification,
U6.17's test isolation, U0.22's doctor fix, V8C′'s re-verification) are marked `reported-only` and
are **not** pre-credited. `(aw)` and `(bd)` were cross-referenced rather than duplicated. Entry
`:967` — and every other existing entry — is untouched.*

---

# U8.14 append — the containment-tool caveat, the health signal that lies, and the graph-chain close-out

Appended by **U8.14** (Occamy probe `000`, DOWN; **zero LLM calls, no test suite run**; the real store
touched by **no SQLite open** — only a 20-byte raw header read). Item A was **re-measured in this unit,
on a scratch fixture of this unit's own making**; every other site was located **by content** and read.
A clause resting only on a unit's own report is labelled `reported-only` and names the unit. Nothing
above this line was rewritten: the pre-existing prefix is **byte-identical** (prefix copy + `cmp` +
sha256 in the U8.14 handoff). **Entries appended: 5 — `(bm)`–`(bq)`. Entry count 64 → 69. Next letter `br`.**

---

## (bm) [verified] `immutable=1` is not a safe default for a live store: it never reads the WAL

**Plan assumption** — this ledger's own convention set says *open SQLite with `immutable=1`*:
`(au)` clause (4) and `(bd)` clause (3), on the sound ground that a plain `mode=ro` open **can create
`-wal`/`-shm` sidecars** in a directory you believed read-only. That is correct as far as
**containment** goes, and **wrong as a default for reading a live store**.

**What is true** — `immutable=1` asserts the file *cannot change*. If the store is in **WAL** mode with
**committed rows still in the `-wal`** (not yet checkpointed), `immutable=1` **never reads the WAL** and
answers from the main database file alone. **Measured in this unit** on a scratch fixture
(`state/logs/U8.14-wal-fixture.sqlite`, `journal_mode=wal`, **1000 committed rows**, `-wal` **28872**
bytes, no checkpoint):

| open | result |
|---|---|
| `file:…?mode=ro` | **1000** rows |
| `file:…?mode=ro&immutable=1` | **`OperationalError: no such table: t`** |
| `file:…?mode=ro&nolock=1` | `OperationalError: unable to open database file` |

So `immutable=1` is **silent data loss** — not an error about staleness, but a table that "does not
exist", or (**for a table created in an earlier checkpoint**) **stale or empty rows**. A reader that
concludes *"the store is unchanged"* from a view that **never saw the change** is exactly the shape of
a false negative no assertion catches. It also **disables change detection**: a checkpoint under the
reader yields a **torn view** — *`reported-only`* (U6.18 measured this on copies; this unit did not
checkpoint under a reader).

**The real store's journal mode is WAL** — established from the **file header**, bytes **18/19 = 2/2**,
read here by a **20-byte raw byte read** (no SQLite open, no sidecars, store byte-identical).
U6.18 confirms it on a copy via `PRAGMA journal_mode`, and records that `user_version=0` is **not**
evidence of anything. Real store: `state/state.sqlite`, sha **`40e8aa0c…`**, schema v4.

**The condition under which `immutable=1` is safe** — a **quiescent** store: writers not mid-write and
no un-checkpointed committed WAL frames. Several units used it **correctly** for containment reads
against exactly such a store (`(au)`, `(bd)`, `(bc)` re-read the store `immutable=1` and left it
byte-identical). The rule is therefore **conditional, not absolute**. Against a **live** store, prefer
a **copy** (or a plain read-only open, accepting the sidecars). A future unit that reaches for
`immutable=1` against a store with un-checkpointed WAL frames will read **stale or empty** rows and can
conclude *"the store is unchanged"* from a view that **never saw the change**.

**The read-WRITE fallback that is now read-only** — `dashboard/api.py`:438 `_connect` opens
`file:…?mode=ro` (`:474`). If that fails, the **fallback** used to be a plain read-**WRITE**
`sqlite3.connect(str(path))` — a layer whose whole contract is read-only silently regaining write
access. It now carries **`PRAGMA query_only=ON`** (`:487`; the comment at `:482–486` names U6.18).
Verified on disk.

**The recommendation, attributed and not applied** — the **writer-side** remedy is
**`journal_mode=DELETE`**, which needs no reader sidecars, **at the cost of the WAL's concurrent
read/write capability** (an exclusive lock per write, so a dashboard read can block a pipeline write).
`run.py`:502 already applies it — to **run-scoped copies** — and documents why (`:522` reads the mode
back). It is **not yet decided or implemented** for the real store: it needs a **concurrency test** and
a **dedicated unit**. **Explicitly: do not flip `dashboard/api.py::_connect` to `immutable=1`.** The
guard that fails if you do is
`tests/test_cli.py:228 test_immutable_uri_would_silently_lose_committed_wal_rows` — it asserts `mode=ro`
sees **1000** (`:277`) and that `immutable=1` is **not** 1000 (`:282`: `assert n_imm != 1000,
"immutable=1 must never be presented as a safe substitute"`).

**Evidence** — this unit's own measurement (table above; scratch fixture only; `state/state.sqlite`
never opened by SQLite); raw header read bytes 18/19 = 2/2 · `src/resextract/dashboard/api.py`:438,
:474, :482–487 · `src/resextract/run.py`:502, :522 · `tests/test_cli.py`:228, :277, :282–283.
Sources: **U6.18** (measured on copies; its handoff is `partial`, `decision: documented-non-fix`),
**U6.16** (the resolution boundary recorded at `(bh)`).

**Supersedes in part** — the **unconditional** phrasing of `(bd)` clause (3) and `(au)` clause (4).
Those entries are **not** edited. **Unit** — U6.18; re-measured by U8.14.

---

## (bn) [verified as code; the classification measurements are `reported-only` — V0.23] The doctor's `slow` is human-visible and invisible to an exit-code consumer

**Plan assumption** — the doctor's exit status is the health signal for the operator *and* for a code
consumer: `cli.EXIT_CORE_DOWN = 2` for a down core leg, 0 otherwise.

**What is true** — `V0.23` re-classified the cases against live stubs and its table (handoff
`overall: "PARTIAL"`) is: refused (nothing listening) → **down**, exit 2 · blackhole `192.0.2.1:80` →
**down**, exit 2 · **accept-never-reply (wedged, listening)** → **`slow`**, `in_core_slow: true`,
`in_core_down: false`, **`exit_code: 0`** · accept-then-RST → **down**, exit 2 · timeout whose cheap
check fails → **down**, exit 2 · listening-but-accept-queue-saturated → **down**, exit 2. **Only the
disclosed wedged acceptor is `slow`** — and it is exactly the case a machine cannot see: **`report.ok`
is `True` and the exit code is `0` while a core leg is `slow`**, so **an exit-code consumer reads a
wedge as healthy**. The signal is real but **human-only**: `cli.main(["doctor"])` prints the `slow` row
and `CORE SLOW: SearXNG (exit 0)`.

**The constraint that shaped the original design** — `tests/test_cli.py`:522 pins
`expected = 0 if not report["core_down"] else cli.EXIT_CORE_DOWN` and `:524` pins
`assert report["ok"] == (code == 0)`, so **a third exit code for `core_slow` would break a sibling
test**. (The card cited `:280–283`; those lines are the `immutable=1` guard today — line drift again,
content is the address.) **A decision on `core_slow`'s semantics is owed — `reported-only`, in flight.**

**The residual direction of the original bug** — a **listening** port with a **saturated accept queue**
classifies **DOWN** again (`6/8` filler connects timed out at `0.4 s` and the leg's own `0.5 s` cheap
check timed out), i.e. the *old* false-DOWN is **still reachable under saturation**; it is mitigated
only because the **full 5 s probe** also timed out. (*`reported-only`* — V0.23's measurement.)

**The overstatement to correct** — *"`1.747` / `3.50` are gone from the file"* is **too strong**. They
were removed from the **assertions** but survive in **4 prose mentions**: `tests/test_doctor.py`:21,
`:430`, `:590`, `:591` (all four read here). And the **two changed assertions** (`:628`, `:636`, read
here) are **self-referential pins that never read the cited handoff**: `:628` asserts
`max(LIVE_LATENCY_SAMPLES_S) > doctor.HTTP_TIMEOUT` and `:636` asserts
`doctor.HTTP_TIMEOUT == 5.0` — both compare **module constants**. The citation to
`orchestration/handoffs/V0.21.json` (`:630`, also `:24`, `:430`, `:596`) lives in **comment, docstring
and assertion-message prose**, never in a file read: the only `json.loads` in the file is `:139`, over
`capsys` (CLI stdout). The citation is **prose, not a programmatic link**. Their **before-text is
unquotable** — no pre-`U0.22` copy of the file exists on disk (U0.22's handoff records
`assertions_changed: 2`).

**Evidence** — `orchestration/handoffs/V0.23.json` (`overall: "PARTIAL"`, `classification_table`,
`ability_to_hide_a_broken_service`: *"the wedged acceptor is the genuine false negative … it never
enters core_down"*) · `src/resextract/doctor.py`:571 (`core_slow = [...]`), :580 (`"core_slow":
core_slow`), :615–620 (`verdict = f"CORE SLOW: …"`) · `tests/test_cli.py`:522, :524 ·
`tests/test_doctor.py`:21, :24, :139, :430, :590–591, :596, :628, :630, :636 ·
`orchestration/handoffs/U0.22.json` (`"status":"done"`, `assertions_changed: 2` — and see `(bq)`: the
file is **not valid JSON**). **Unit** — U0.22 (the fix), verified by **V0.23**.

---

## (bo) [verified as code; the behavioural arm is `reported-only` — V8E] The graph-chain close-out, and two overstatements in `U8.11`'s report

**Plan assumption** — a graph reused after a pin check is a graph whose **bytes** were vouched for;
`(aw)` closed the artifact and `(bj)` closed the pin mechanics.

**What is true** — **`U8.11` is PASS** (re-verified by **V8E**, `done`) and its **element-type fix
cannot be gamed by a valid prefix**: a **valid 10-object prefix followed by 100 000 ints** is
**rejected at element 10**, because **every** element is walked and **nothing is sampled**;
`nodes: []` / missing / scalar and a **missing `links`** are rejected; `[{}]*5000` is **accepted with
`graph_stats = 5000`**, so **`ok` with `nodes = 0` is unreachable**. The **cost claim holds**: the JSON
parse is **0.023 s** against the isinstance walk's **0.003 s** (~11 %). The genuine graph reuses at
**2685 nodes / 7102 edges**. *All of the behaviour and timings in this paragraph are `reported-only`
(V8E's run): this unit ran no test suite, and `state/graph.json` is **not on disk at that path**, so
the counts were not re-read here.*

Verified on disk: `run.py`:748–762 — `nodes = doc.get("nodes")` (`:750`), `if not isinstance(nodes,
list)` (`:751`), the **per-element** `if not isinstance(node, dict)` (`:756`, inside the loop),
`links` array required (`:762`) — with the justification in the docstring at `:727` ("`O(len(nodes))`,
so an `isinstance` walk is **strictly cheaper than the parse**", i.e. it cannot be gamed).

**Overstatement 1 — "3 existing assertions strengthened".** Only **ONE existing assertion changed
value**: `tests/test_run.py`:1020
`assert stage.counts["sha256"] == _GENUINE_SHA  # full 64 hex (U8.11 item 2)` — the 12-hex form became
the **full 64-hex** `_GENUINE_SHA` (declared at `:815`; `_GENUINE_SHA12 = _GENUINE_SHA[:12]` survives
at `:818` as the **display-only** abbreviation, `_graph_digest` being full). It is the **only**
comparison of a stage `sha256` to `_GENUINE_SHA` in the file; the other two full-digest pins are in
**newly appended tests**. The change is **meaningfully stronger and not brittle** — but *"3 existing"*
**overstates by two**. **Generalisable lesson: "an existing assertion was strengthened" and "a new test
with a stronger pin" are different claims about how much prior guard coverage improved.**

**Overstatement 2 — a reporting-shape lesson that cost a verifier a full cycle.** A report entry
**named a stage but not the implementation that backed it**. `V8D` read
`{"name":"graph","status":"ok","reason":"fake ok","counts":{}}` and concluded the report was **lossy** —
it was the **test harness's fake graph impl** (`_ALL_OK["graph"]`), a stage that genuinely **did
nothing**, so the **empty counts were accurate**. The real `_stage_graph` carries
`edges`/`mode`/`nodes`/`provenance`/`sha256`. **Recorded as a generalisable requirement:** when a
harness can substitute a stage implementation, the report must be able to say **which** implementation
produced an entry, or a reader **cannot distinguish a stub from the real thing**. (*`reported-only`* —
V8E/V8D; this unit did not re-locate `_ALL_OK`.)

**A pin boundary left open (named follow-up, not implemented)** — a **63-hex** pin **matches**, and a
pin **longer than 64** whose **first 64 hex are correct also matches** (the tail is unvalidated),
because comparison is at `min(len, 64)`. So the **abbreviated-pin warning may not fire for a
near-full-length pin** — the "accept and report" policy's ***reporting* half** may have a gap.
*`reported-only`* (V8E).

**Still holding, verified on disk** — the **fail-closed mismatch default** (`run.py`:1085
`if not ctx.allow_graph_digest_mismatch:`); the **override is CLI-unreachable**
(`allow_graph_digest_mismatch` has **7** references, **all in `run.py`** — `:326`, `:1085`, `:1745`,
`:1825` plus its docstrings — and **0** in any CLI or dashboard module; the only other hits are three
verifier harnesses under `state/verify/`); **`require_fresh_graph` refuses `unverified`**
(`run.py`:1097 `if ctx.require_fresh_graph and provenance.get("state") in ("stale", "unverified")`,
refusal text `:1100–1111`); and the **STALE path is unchanged**.

**Evidence** — `orchestration/handoffs/U8.11.json` (`done`), `V8E.json` (`done`), `V8C.json` (`done`),
`V8D.json` (`partial`) · `src/resextract/run.py`:727, :748–762, :1085, :1097–1111, :1745, :1825 ·
`tests/test_run.py`:815, :818, :1020, and the appended guard
`test_non_object_nodes_are_rejected_not_reused_as_ok_zero_nodes`. **Unit** — U8.11 (fixes), V8C
(defects), V8E (re-verification). This **closes `(bj)`'s in-flight `reported-only` (`V8C′`)** by
supersession; `(bj)` is **not** edited.

---

## (bp) [reported-only — V5.21 is verifying right now] The F2 provenance semantics: a claim's producer is a two-part statement

**Plan assumption** — §3.4 gives `verdicts`/`evidence` a single `producer`; the natural reading is
**one** provenance value per row.

**What is true (U5.19, `done`; not verified here)** — U5.19 unified a **third** normalisation site,
finding a **second instance of the same divergence** — `mixed`, not only the `fixture` case `V5G` had
named. Its recorded divergences are `["fixture","unknown","unknown","fixture"]` and
`["mixed","unknown","unknown","mixed"]`, and it **unified them on `unknown`**, justified as
**fail-closed**: `store.producer_is_model("fixture")` is `False` and the claim level renders only the
standing-bearing classes (`model`/`replay`), so **collapsing can only remove standing, never grant
it**. For the **mixed** case — a **model verdict on a replay-mined candidate** — it chose that claim
`producer` means the **assessing** (verdict) authority, while the **mining provenance is recorded in
`verdict_reason`**. Claim-level provenance is therefore a **two-part statement**, not one scalar.

**The decision was the point** — its own verifier was asked to **judge the decision, not the code**,
which is why this entry records the *choice* and its justification rather than a test result.
**Verification is in flight: `V5.21` is `partial`** (read here). Source: **U5.19**. **No clause of this
entry is credited as verified.**

---

## (bq) [verified] Hygiene and debris — measured, and left as open follow-ups

**What is true** — four small residuals, each **measured here today** (the `1.747`/`3.50` prose
residual is item `(bn)` and is listed only for completeness, not duplicated):

1. **A dead verifier's debris** — `state/verify/V8D/c2stage/` is a **recursively self-nesting tree**:
   **195 regular files** (the card's "61" is low), nested to **44 path components** (≈40 levels below
   `c2stage/`), longest nested file path **347 characters**. Nothing reads it; it should be removed or
   flattened.
2. **A stray untracked backup** — `src/resextract/dashboard/api.py.V6C-backup-B2`, **56700 bytes**, a
   backup living **inside the package directory**; `git ls-files --error-unmatch` fails ("did not match
   any file(s) known to git").
3. **Unfilled template placeholders** — `tests/test_run.py`:238 (`sha256 before/after: __SHA_A__`) and
   `:276` (`__SHA_B__`): a template committed with its substitution never performed. Prose only; no
   code reads them.
4. **4 residual prose mentions** of `1.747` / `3.50` — `tests/test_doctor.py`:21, `:430`, `:590`,
   `:591` (see `(bn)`).

**A clerical finding worth its own line** — `orchestration/handoffs/U0.22.json` is **not valid JSON**:
`json.load` fails with `Expecting ',' delimiter: line 6 column 32 (char 1165)`, because the
**`assertions_changed_detail` array is opened and never closed** (`:5` ends with `…"`, and `:6` starts
a new key object). The file **declares `"status":"done"`** in its first bytes, so U0.22 *did* report —
but **no consumer can machine-read it**. That is why `(bi)`'s supersession below rests on **V0.23's
verification** and on the prose `assertions_changed: 2`, not on the handoff being parseable. **A
handoff that does not parse is a claim with no address.**

**Evidence** — `find state/verify/V8D/c2stage -type f | wc -l` = **195**;
`find … -type d | awk -F/ '{print NF}' | sort -n | tail -1` = **44**; `ls -la
src/resextract/dashboard/api.py.V6C-backup-B2` (56700 B) + `git ls-files --error-unmatch …` (non-zero);
`grep -n "__SHA_A__\|__SHA_B__" tests/test_run.py` → **238, 276**;
`grep -n "1\.747\|3\.50" tests/test_doctor.py` → **21, 430, 590, 591**;
`python3 -c "import json; json.load(open('orchestration/handoffs/U0.22.json'))"` → the traceback above.
**Unit** — cross-unit; recorded by U8.14.

---

*End of the U8.14 append. Entries **(a)–(bl)** above are unchanged; **5** entries were appended
**(bm)–(bq)**, so the ledger now holds **69** entries and the next letter is **`br`**. Section **D** is
`reported-only` (V5.21 in flight); sections **A**, **B**, **C** and **E** are recorded with their
clause-level `reported-only` marks named above. **Supersessions — all made by adding new entries; none
by editing history:** `(bg)`'s `reported-only` mark for **V5G**'s output verification is upgraded
because **V5G has since reported** (`overall: "PASS"`); `(bh)`'s `reported-only` mark for **U6.17**'s
test-isolation fix is upgraded because **U6.17 has since reported** (`status: "done"`); `(bi)`'s
`reported-only` mark for **U0.22**'s doctor fix is upgraded because **U0.22 has since reported**
(`"status":"done"`, `assertions_changed: 2`) and **V0.23 verified it**; `(bj)`'s `reported-only` mark
for **V8C′**'s re-verification is upgraded because **V8E has since reported** (`status: "done"`); and
the **unconditional** `immutable=1` convention at `(au)` clause (4) / `(bd)` clause (3) is
**conditioned** by `(bm)`. The superseded entries themselves are **not edited** — they stand exactly as
written, with their original marks.*

---

# U8.17 append — the render-path bypass and the boundary that closes it, the drift convention, and the health signal in both directions

*Appended by **U8.17** on 2026-10-08. Entries **(a)–(bq)** above are **untouched**; **5** entries are
appended **(br)–(bv)**, so the ledger now holds **74** entries and the next letter is **`bw`**. Section
**F** produced **no additional settled item** and is recorded as a scope note in the closing note, not as
an entry. Every claim below is marked `verified` only where **U8.17 re-measured it on disk today**;
everything taken from another unit's handoff is `reported-only` and names that unit. **New convention
recorded at `(bs)`**: an entry citing **another unit's file** must name the **sha or mtime observed**.*

---

## (br) [verified as code; the carried test is `reported-only` — U5.22] The render-path bypass: a structural verifier certified a docket whose claim contradicted its own producer

**The corrected assumption.** The ledger's earlier entries (`(bc)`, and the `(bg)`-family) established
that the `CONFIRMS`→`EXTENDS` cap applies where claims are **made**. The implicit assumption was that this
was sufficient — that anything reaching a rendered docket's `CLAIMS.md` had passed through the cap, and
that `verify_docket` would catch a contradiction if one survived. **Both halves were false for the
re-render path.**

**Actually true.** A verifier (**V5.20**, handoff `orchestration/handoffs/V5.20.json`, sha
`5682b391b0959f6c…`, mtime `2026-10-08 09:02:12`) **FAILED** the delivered `duval-replay-material`
docket: its `CLAIMS.md` renders **`CONFIRMS`** at **`:9`** (`## C-curated — CONFIRMS`) and **`:15`**
(`**Verification state.** CONFIRMS`) while its producer is **`replay`/`unknown`** — the file's own banner
says *"PROVENANCE: replay-produced"*. The cap **never applied**, because the re-render **supplied
`claims` verbatim** (U5.18 re-rendered with `claims=[c.model_dump() …]`), so
`materialize._claim_standing` and the cap site in `assess/verdicts.py` **never ran**. It was
**inherited** from the pre-damage manifest, not introduced by the re-render. And **`verify_docket`
returned `ok`/`problems == []`** on it. So a **structural verifier certified a docket whose claim
contradicted its own producer**. This is the *"enforce at instances, not at the boundary"* shape, **one
layer above** the ones already recorded: the rule lived where claims are **made**, and nothing guarded
where they are **written** or **checked**.

**`U5.22` closed it** (handoff sha `caee75f75b1a509b…`, mtime `2026-10-08 09:13:19`; **status
`partial`** — the carried test is section `(bu)`):

1. **Cap on input** — a claim whose standing contradicts its producer is now **capped to `EXTENDS` with
   the reason recorded** at render time. The rule is **not duplicated**: it **reuses
   `store.producer_is_model`**, the same predicate `materialize._claim_standing` calls (verified:
   `materialize.py:1638`, sha `5dbf520e4822f681…`, mtime `2026-10-08 08:52:22`).
2. **The verifier condition** — appended as `_claim_standing_problems` (`assemble.py:2488`, sha
   `0c8f7386394b2e92…`, mtime `2026-10-08 09:12:21`), called by `verify_docket` (`:2528`). The condition
   is **exactly** `claim.verdict == "CONFIRMS" and not store.producer_is_model(claim.producer)`
   (verified at `:2493`). It is **deliberately NOT keyed on the docket-level `generated_by.producer`**,
   because a **model verdict may legitimately bless replay-mined material** — the `F2` semantics recorded
   at `(bp)`. The source comment states this and quotes the docket-level producer as context only.
3. **`file-fact` vocabulary question** — the cap is **right and fail-closed**; `CONFIRMS` **is**
   overloaded for mechanically-verified facts, but `resextract/docket/1` has **no standing** for that and
   **must not be bumped** → **handed up as a schema follow-up**.
4. **Refusal (option ii) was viable but rejected** — its sole in-repo caller is already capped, so a
   raise would not have broken a caller; rejected because *"a renderer that normalises repairs the
   artifact where a raise only refuses."*
5. **The `.rN` rotation is now bounded at `N = 5`** — `ITEM_SNAPSHOT_KEEP = 5` at **`assemble.py:1691`**
   (verified on disk). `5` is the **smallest bound that prunes nothing existing** (deepest real chain
   `r1–r4`; the comment at `:1685–1690` states the justification). Allocation is **`max(existing) + 1`**,
   deliberately **not** first-free — because once the bound prunes the oldest snapshot, first-free would
   hand the *newest* content a low index and the **newest snapshot would then be pruned as oldest**
   (`:1700–1703`). Oldest are pruned, the **live `ITEM.md` is never touched**, and **`HISTORY.md`
   remains the unbounded audit log** by design.

**Evidence (re-measured by U8.17, not taken from the handoff).** `sed -n '1,20p'
dockets/duval/duval-replay-material/CLAIMS.md` → `:9` `## C-curated — CONFIRMS`, `:15`
`**Verification state.** CONFIRMS`; file sha `d8751ad114e5d640…`, mtime `2026-10-08 08:36:35`, 1804 B ·
`grep -n 'def _claim_standing_problems\|def verify_docket' src/resextract/docket/assemble.py` → **2488,
2528** · `sed -n '2490,2515p'` → the condition verbatim · `sed -n '395,410p'
src/resextract/assess/verdicts.py` → the cap (`if verdict == "CONFIRMS" and not is_model: verdict =
"EXTENDS"`) · `grep -n 'ITEM_SNAPSHOT_KEEP' src/resextract/docket/assemble.py` → **1691** =
`5` · `grep -rn 'producer_is_model' src/resextract/` → the shared predicate at `store`, imported by
`verdicts.py:66`, `value.py:82`, `assemble.py:1134,:2493,:2516`, `materialize.py:1638`.
**`reporting-only`:** the red→green cycle and the docket-byte-identity measurements are U5.22's, not
re-run here. **Sources:** U5.18 (the re-render), V5.20 (the FAIL — `overall: "FAIL"`, `status: "done"`),
U5.22 (the fix). **Unit:** U8.17, recording U5.22's close.

---

## (bs) [verified: the baseline and the drift; `reported-only` — V8.16 for the `immutable=1` fixture] The ledger verified a third time — and the drift that defines a new convention

**The claim.** `U8.14`'s append (`bm`–`bq`) was independently checked by verifier **V8.16** (handoff sha
`4fe9d9c548d3db58…`, mtime `2026-10-08 09:12:23`, **`overall: "PASS"`**): **69 entries**, prefix
**byte-identical** by its own `cmp`, **263 added / 0 deleted**, all six superseded entries **inside the
byte-identical prefix** (so the upgrades are provably additive), the **6 original `reported-only`
markings** intact, **56 occurrences** confirmed. It also **reproduced `(bm)`'s `immutable=1` caveat
clause-by-clause** on its own WAL fixture (Python 3.14.4 / SQLite 3.46.1; `mode=ro` → 1000 rows;
`immutable=1` → `no such table: t`; `nolock=1` → cannot open) — a **third** independent measurement.

**Actually true, re-measured by U8.17.** `sha256sum docs/PLAN_CORRECTIONS.md` **before** this append =
**`55db3230493e86bd7b97d068abf328d2c8267c9a4a71a1274eb6acc7038fef22`**, **128295 bytes**, **1883 lines**,
`grep -c '^## ('` = **69**, last letter **`bq`**, `grep -o 'reported-only' | wc -l` = **56**. V8.16's
figures are **reproduced exactly**.

**And it found a drift.** `(bn)` claimed the literals `1.747`/`3.50` survive in `tests/test_doctor.py` —
**not reproducible today**: `grep -n '1\.747\|3\.50' tests/test_doctor.py` → **empty**. The cause is
**timing**: `tests/test_doctor.py` mtime is **`2026-10-08 09:04:25`** (sha `5ef954243e2baa85…`), which
is **71 seconds after** the ledger's own mtime **`2026-10-08 09:03:14`** — a sibling scrubbed them. **The
entry was true when written and falsified 71 s later by a concurrent unit.** This is the **second
drift-class** the build has measured; the first was **line-number drift**, recorded earlier.

**→ THE CONVENTION, NOW RECORDED (and followed throughout this append):** *an entry that cites **another
unit's file** must name the **sha256 prefix or mtime it observed**, not merely line numbers — so a later
reader can distinguish a claim that was **false** from one that is merely **stale**, and can re-check
against the exact revision the author saw.* Line numbers alone are insufficient because a sibling's edit
can make a true entry false within a minute.

**Evidence.** `sha256sum`/`wc -c`/`wc -l`/`grep -c '^## ('` on the pre-append file; `grep -n
'1\.747\|3\.50' tests/test_doctor.py` → rc=1, no output; `stat -c '%y %n' docs/PLAN_CORRECTIONS.md
tests/test_doctor.py` → `09:03:14` and `09:04:25` = **+71 s**. **`reported-only`:** the `immutable=1`
fixture (three clauses) and the red→green guard are V8.16's; U8.17 did **not** open the store. **Unit:**
U8.17, recording V8.16.

---

## (bt) [verified as code and in the report shape; the pre/post behavioural arms are `reported-only` — V0.26] The health signal, verified in both directions

**The claim being corrected.** `U0.25` fixed the doctor so that a live core dependency that is **slow**
is no longer reported as **DOWN**. Verifier **V0.26** (handoff sha `d754e503601e2674…`, mtime
`2026-10-08 09:13:09`, **`overall: "PASS"`**) loaded the **pre** and **post** revisions side by side and
called the real preflight: **slow SearXNG pre** → `degradable_core_down=['SearXNG']` + *"core leg
SearXNG is DOWN"*; **post** → `core_slow=['SearXNG']`, `degradable_core_down=[]` + *"SLOW (reachable but
slow, not down)"*; **refused** → `core_slow=[]`, `degradable_core_down=['SearXNG']`. **A DOWN leg can
never appear in `core_slow`** — the branch requires `state == 'slow'`. A **needed** slow leg (graphify)
still gates at **exit 2**.

**Verified on disk by U8.17.** The two report fields exist and are distinct: `core_slow` at
`src/resextract/run.py:257` and `degradable_core_down` at `:253` (sha `7f0b6a659102b9d5…`, mtime
`2026-10-08 09:04:47`), both serialised at `:279–280`. **`LEG_STAGE_NEEDS['searxng'] == frozenset()`** —
verified at `run.py:120`, and the line carries the comment *"no stage of this pipeline performs a web
search"*; `graphify` maps to `{"graph","staging","refresh"}` and `dashboard port` is also empty. So
**SearXNG gates no stage**, while a needed leg still gates — the **structural** half of the argument is
true as code.

**Two corrections to `U0.25`'s own write-up (both verified here).**
**(i)** `tests/test_cli.py` is **UNTRACKED** — `git ls-files --error-unmatch tests/test_cli.py` →
*"Did you forget to 'git add'?"* (sha `4395af6c582b3f0a…`, mtime `2026-10-08 08:56:00`). Therefore
U0.25's *"not edited — absent from `git status`"* was **false as evidence**: an untracked file **does**
appear in `git status` (as `??`). Untouchedness rests on **mtime alone**, with **no baseline to diff**.
**(ii)** The exit-code pin is at **`tests/test_cli.py:522`** — verified: `sed -n '518,525p'` →
`:522` `expected = 0 if not report["core_down"] else cli.EXIT_CORE_DOWN`. This is the **third correction
of that citation**: `:280-283` → `:520-523` → **`:522`**.

**And the honest weighting the ledger must carry.** The **empirical** spurious-block argument is
**thin**: `slow_fraction 0.0` from **8 samples**, and **1/16 ≈ 6.25 %** across all recorded samples
would be slow. The **structural** argument (SearXNG gates nothing; a needed slow leg still gates)
**stands independently** of those samples. **`reported-only`:** the pre/post/refused behavioural
measurements are V0.26's, not re-run here (this unit runs no suite). **Unit:** U8.17, recording V0.26 and
correcting U0.25.

---

## (bu) [reported-only — U5.22 raised it; the implementation is in flight, U5.24] The backward-compatibility witness, and the ruling

**What happened.** `U5.22`'s honesty check turned a **pre-existing test red by design**:
`test_pre_u5_7_smoke_manifest_still_validates_and_verifies` asserted that a **pre-U5.7 manifest with
`CONFIRMS` and no producer verifies ok** — the **exact contradiction now detected** by `(br)`'s
condition. `U5.22` **did not weaken it** — *"I stopped rather than invent a narrower condition to force
the last red test green."*

**The ruling (a plan-level point, not a code change).** *A backward-compatibility witness proves that old
artifacts still **LOAD**; it does not prove they **PASS every honesty check**.* The `_smoke` docket is
**frozen** and genuinely contains an uncapped `CONFIRMS`, so the **test's contract was wrong, not the
verifier**. The test is being **restated**: keep the **load** assertion, assert the **specific**
contradiction, assert the artifact is **byte-identical**, and **rename** it so the test list stops lying.

**The generalizable rule.** *When a new honesty check turns an old artifact's test red, the question is
which one encoded the wrong contract — and "the artifact is frozen" is decisive evidence that it is the
test.*

**Status — deliberately not credited.** The implementation is **in flight**: `orchestration/handoffs/
U5.24.json` reads `"status":"partial"` with `next_unit_hint: "in progress"`, and writes
`tests/test_docket_provenance.py` (present on disk, **untracked**, mtime `2026-10-08 08:51:48`). **No
clause of the restatement is verified.** `U5.22`'s own carried-test note is the source. **Unit:** U8.17,
recording a ruling; **implementation `reported-only`, naming U5.24.**

---

## (bv) [verified: the sidecars exist, and were observed by three independent units] The sidecar attribution practice

**The finding (from `(bm)`).** A read-only open of a **WAL** database **creates sidecars**
(`-wal`/`-shm`) — that is `(bm)`'s finding, already recorded.

**The practice now recorded.** Three units — **`U0.25`**, **`V8.16`**, **`U5.22`** — observed
`state/state.sqlite-wal`/`-shm` appearing **from another unit's plain `mode=ro` open** of the real store,
and each **reported them as "not mine" rather than deleting them**. **This is the correct behaviour**, and
it is now the practice: **a unit should report sidecars, attribute them honestly, and not delete what it
cannot prove is its own** — because deleting a sidecar out from under a **possibly-live sibling's handle**
is worse than leaving clutter.

**Verified on disk by U8.17 (this instance is not U8.17's either).** `ls -la state/state.sqlite-wal
state/state.sqlite-shm` → `-shm` **32768 B**, `-wal` **0 B**, both mtime **`2026-10-08 09:11`**, which is
**after** this unit started and **not** attributable to U8.17 (this unit has opened no database and
write nothing to `state/state.sqlite`). **U8.17 reports them and does not delete them.**

**Evidence.** the `ls -la` above; `stat -c '%y' state/state.sqlite` → `2026-10-08 07:47:56` (the store
itself was not written today). **`reported-only`:** the attachment of the sidecars to a *specific*
sibling is U0.25/V8.16/U5.22's report, not independently provable here; only their **existence, size and
mtime** are verified. **Unit:** U8.17, recording U0.25, V8.16 and U5.22.

---

*End of the U8.17 append. Entries **(a)–(bq)** above are unchanged; **5** entries were appended
**(br)–(bv)**, so the ledger now holds **74** entries and the next letter is **`bw`**. **Supersessions —
all made by adding new entries; none by editing history:** none of the five supersedes an earlier entry
by rewriting it; `(br)` **supersedes the scope of** the cap entries (`bc` and the `(bg)` family) by
extending the fix from the *making* boundary to the *writing* and *checking* boundaries, and `(bs)`
**supersedes `(bn)`'s** `1.747`/`3.50` prose-survival claim — which was true when written and was
falsified **71 seconds later** by a concurrent unit — while `(bn)` itself stands exactly as written, with
its original mark, as the motivating example of the drift class.*

**Section F — no additional settled item.** U8.17 read the handoffs for this wave and found **no further
settled** item beyond A–E. **Deliberately not pre-credited (in flight, named for the next unit):**
**`U8.15`** (`orchestration/handoffs/**` syntax repair — its own handoff reads `status: "partial"`,
`tool_calls: 2`, `parsed_ok: 133`, `parse_failed: 4` — **U0.14, U0.22, U8.9, U8.12** — against U8.14's
count of **1**; **U8.15's repair list is empty and its guard is `PENDING`, so the count discrepancy is
*not* settled**); **`U6.20`** (`dashboard/api.py`, `tests/test_dashboard.py`; handoff
`"status":"partial"`, *"in progress: step 0 inventory"*); **`U5.23`** (`docket/manifest.py`; handoff
`"status":"partial"`, *"consumer sweep pending"*); **`U5.24`** (`tests/test_docket_provenance.py`; see
`(bu)`); and **`V5.21`**, which is still verifying `(bp)`'s `U5.19` semantics — **`(bp)` therefore keeps
its `reported-only` mark here, and nothing in this append credits it.** **U8.17 made zero LLM calls and
ran no test suite.**

---

## (bw) [verified on disk: the gate, the two consumer sites and the four emitters; the sweep's *completeness* is V5.25's, `reported-only`] `verdict_reason`'s dual meaning is documentation-only — and the discriminator was attacked

**The overload (`U5.19`).** `Claim.verdict_reason` now carries **two unrelated things**: the **`CONFIRMS`-cap reason** (why a `CONFIRMS` verdict was demoted to `EXTENDS`) and a **provenance-divergence note** (the claim's `producer` is the *assessing* producer while the material was mined by another). `U5.23` swept the consumers and concluded **documentation-only**; verifier **`V5.25`** **re-derived the sweep and PASSED it**.

**Verified on disk by U8.20 — the load-bearing gate does NOT consult the reason.** `assemble.py:1134` reads exactly `if claim.verdict != "CONFIRMS" or _store.producer_is_model(claim.producer): continue` — the decision is **verdict + producer**; `reason` is read only **afterwards** (`:1136`), when the capped claim is append-recorded (**preserve-and-append**). `materialize._claim_standing` likewise decides from the **verdict row** (`materialize.py:1635–1644`). **Pins observed:** `assemble.py` sha `0c8f7386394b2e92…`, mtime `2026-10-08 09:22:20`; `materialize.py` sha `5dbf520e4822f681…`, mtime `2026-10-08 08:52:22`. ⚠️ **The `assemble.py` pin has a short half-life:** that mtime is **73 s** before this unit's clock reading `09:23:33` — `V5.26` was **mid-edit** on that file, and it reverts it for red→green.

**Two consumer sites `U5.23` missed — both reason-blind, neither a defect (verified here).** `dashboard/api.py:1143–1145` builds `dict(Counter(str(claim.verdict) for claim in manifest.claims))` — **verdict only**, the reason is never touched; and `api.py:42` `from resextract.docket import read_manifest, verify_docket`, where `verify_docket`'s `_claim_standing_problems` gates on **verdict + producer**. Pin: `api.py` sha `004d88fdbb61a2fc…`, mtime `2026-10-08 09:17:04`.

**HAZARD worth recording (verified).** `assemble.py:2495` contains the literal `is the *assessing* producer` **inside a docstring** (` ``claim.producer`` is the *assessing* producer `), **not an emitter** — so a **grep-based** consumer of the discriminator **false-positives** there.

**The discriminator's exclusivity, established by attack (V5.25; the four emit sites verified here).** **Four** sites emit **`capped at EXTENDS`**: `assess/verdicts.py:404` (→ `Verdict.rationale`; sha `754101b895f30545…`, mtime `2026-10-08 07:33:35`), `assemble.py:1138`, `materialize.py:1631`, `materialize.py:1641` — but only **three** reach `Claim.verdict_reason`, because **materialize never copies `rationale`** (V5.25's grep: **0**). The substring is **contiguous inside a single f-string literal** at each site — **not assembled from parts**, which is the failure a whole-phrase grep would hide. **`is the *assessing* producer` is emitted at `materialize.py:1686` alone.** `"; "`-joining is confirmed at `materialize.py:1690–1691`, and **non-clause-parseability** confirmed (the substring is not a sentence).

**Judgement — "a hint, not a contract".** Nothing pins either string, so a **reword breaks it silently**, and a **variant spelling already exists in-repo**: `tests/test_docket_reassembly.py:1385` carries `declared CONFIRMS capped to EXTENDS: producer replay is not a model` — note **`to`**, not **`at`** (sha `492872341ea37a8e…`, mtime `2026-10-08 08:19:31`). **The remedy is to land the handed-up guard**, judged **non-vacuous**: it pins **not-`None`**, **`verdict == "CONFIRMS"`**, and **both substrings present/absent** — so the discriminator can **fail loudly**.

**Corrections to `U5.23`'s write-up (verified here).** Its *"`is not None` is always corroborated by a content assert"* is **false** at `tests/test_docket_provenance.py:615`: the `is not None` at `:615` is corroborated by the **`EXTENDS` assert at `:613`**, not by any content assert on the reason (sha `3fbcb137c8fd283c…`, mtime `2026-10-08 09:17:03`) — **not a behaviour defect**. And `manifest.py:185` is a field **declaration** — `verdict_reason: str | None = None` (sha `0826f398add9f1c9…`, mtime `2026-10-08 09:14:48`) — so "writes" was loose. Its handoff says `tool_calls: 15` while the card says 16/18; that discrepancy is `U5.23`'s own and is **not** resolved here. **`reported-only`:** the **completeness** of the consumer sweep (that no *other* consumer reads the reason) is `V5.25`'s **re-derivation, not re-run here**, and the *materialize never copies `rationale`* grep result is likewise taken on report. **Units:** U5.19 (the overload), U5.23 (the sweep + the docstring), V5.25 (the verification); on-disk verification by U8.20.

---

## (bx) [verified on disk: the landed fix and its design; the reproduction and the store-row numbers are U6.20's, `reported-only`] The board published the **slug** in the title slot — **missing metadata**, not staleness

**A prior finding was partly wrong.** Verifier **`V5.20`** reported that the dashboard served **stale store-snapshot** metadata. A later unit (**`U6.20`**) **reproduced the surface defect live and corrected the diagnosis**: `GET /api/dockets` **published no title key at all** — its `lane` field carried the **slug** — and served **no evidence count**; and the store row's `evidence = 0` / `generated_by = None` **did NOT reproduce** (the row holds **8** evidence and a **non-null** `generated_by`). **What reproduced was `lane.title = None` plus a missing producer — and the board never read the row anyway.** So the defect was **missing metadata, not staleness**. **And for `_smoke` the slug is doubly wrong:** its recorded `lane.slug` is **`duval-trace-integrity`**, which **is not the directory name** (`_smoke`) — so a slug in the title slot misnames the artifact twice over.

**Verified on disk by U8.20 (api.py sha `004d88fdbb61a2fc…`, mtime `2026-10-08 09:17:04`).** The fix is landed and carries its own provenance comment naming the unit: `api.py:1146–1150` states that `lane` carries the manifest's `lane.slug` *"(normally the directory slug, but not always: `dockets/_smoke` records `duval-trace-integrity`)"* and that `lane_title`/`title` *"add the artifact's real title so no slug stands in for it"* while `evidence` counts the artifact's evidence entries; `:1151` sources `lane_title` from `getattr(manifest.lane, "title", None)`; `:1013` takes the same from the store metadata dict; `:1159` `entry["title"] = entry["lane_title"] or entry["lane"]`.

**The fix's design — the durable part (verified on disk).** The on-disk **`MANIFEST.json` is authoritative**; the store row is a **fallback only** (`:966`, `:1042`). A new **`source` field** makes the provenance of served metadata **explicit** — `"manifest"` at `:1156` and `:1308`, `"store"` at `:1109` and `:1218`, `null` at `:1066` — *"because a silent stale fallback is how this arose"*. A store-sourced entry reports **`verify.ok = None`** rather than implying a verification it did not run: **verified** at `api.py:1210–1213` → `{"ok": None, "problems": ["no MANIFEST.json on disk: not verified"]}`. **Store-only rows whose directory is gone are never resurrected** (`:1162–1167`; tests `test_u620_board_prefers_the_manifest_over_a_stale_store_row`, `..._falls_back_to_the_store_row_when_the_artifact_is_gone`, `..._never_resurrects_a_docket_outside_the_root` at `tests/test_dashboard.py:1408`, `:1446`, `:1476`). **Path safety reuses the existing containment helpers** (`:1241–1244` refuses a `MANIFEST.json` resolving outside the dockets root). **`reported-only`:** the live reproduction, the store row's `evidence = 8` / non-null `generated_by`, and **"no store write was made"** are `U6.20`'s report — not re-run here (this unit opens no database and starts no server). **Supersession:** this entry supersedes **only the diagnosis** of `V5.20`'s staleness finding; that observation stands **as written**, unedited. **Units:** V5.20 (the finding), U6.20 (the reproduction, the correction, the fix); on-disk verification by U8.20.

---

## (by) [reported-only — U6.20 observed it; the resolution is in flight, `U6.21`] The three red dashboard tests, and **why** they are red

**What was observed (`U6.20`).** `tests/test_dashboard.py` became the **only red suite** in the build (**71 collected / 68 passed / 3 failed**), and the same three failed **at the release sha**, so they are **pre-existing**. All three fail with **`verify.ok is False`** from the docket-verifier leg — i.e. **`U5.22`'s stricter check is correct**, and the tests assert that a **known-uncapped artifact verifies clean**.

**The ruling principle (it generalises the backward-compat ruling in `(bu)`).** *The **check** is right; an expectation that a **permanently**-invalid artifact verifies clean must be **restated**, and an expectation about a **transiently** invalid artifact must **NOT** be baked in as permanent.*

**The permanent/transient split.** `_smoke` is **frozen** and will **never** verify clean (see `(bu)`); `duval-replay-material` **will** verify clean once its claim is re-derived through the cap. **The resolution of that split is in flight (`U6.21`) and is `reported-only` here — no clause of it is credited by this append.** **Self-cleaning mechanism considered:** `xfail(..., strict=True)` **names the pending dependency** and **fails once the test starts passing**, so the marker **cannot rot silently**.

**Verified on disk by U8.20 — context only, not the counts.** `tests/test_dashboard.py` sha `4195099c9f8d4366…`, mtime **`2026-10-08 09:23:21`** — **12 s before** this unit observed it, i.e. `U6.21` is **mid-edit**; the file carries a docstring at `:74` about keeping *"`verify["ok"] is True` expectations intact, instead of restating them"*, `:311` `assert broken["verify"]["ok"] is False`, and `:1335` a helper describing *"the shape the real `duval-replay-material` row still holds"*. **Negative, verified:** as of that sha, **`xfail` appears nowhere** in `tests/test_dashboard.py` — the self-cleaning mechanism is **considered, not landed**. **`reported-only`:** the 71/68/3 counts, the release-sha comparison and the `verify.ok is False` failure cause are `U6.20`'s; **this unit ran no test suite** (hard bound). **Units:** U6.20 (the observation), U6.21 (in flight).

---

## (bz) [verified on disk: the contract of record in AGENTS.md; the measurement and the repairs are U8.15/U8.18's, `reported-only`] The orchestration **contract** was wrong, not its practitioners

**The measurement (`U8.15`).** **45 of 137 handoffs omitted ≥1 of the 7 contract keys**, almost all `V*` verifier handoffs, *"which use a verdict shape, not `unit`/`status`/`artifacts`/`evidence`"*. It **also** found and repaired **four unparseable handoffs** — `U0.14`, `U0.22`, `U8.9`, `U8.12` — **syntax only**, **field values changed = 0**, each carrying an in-file `_repaired_by`/`_repair` note, each the **unique** candidate yielding the contract shape with **string-literal multisets identical** before/after. And it **moved** (never deleted) the debris: `state/verify/V8D/` → `state/debris/V8D/tree/`, **243 files** with **73 distinct contents** — so **unique content was preserved** — of which the `c2stage` subtree is **195** files, plus the stray `src/.../api.py.V6C-backup-B2`.

**The reconciliation (`U8.18`).** **Two handoff shapes are now contracted:** the **unit handoff** (the seven keys) and the **verifier verdict**, whose core keys were **derived by measurement across the 43 `V*` handoffs** — carried by **≥90%**: `unit`, `overall`, `checks`, `blocker`, `next_unit_hint`, `write_paths`; commonly carried but **not** required: `not_reproduced` 37, `overstated` 37, `unverified` 37, `tool_calls` 36, `containment` 36, `bound` 35, `scope` 34, `red_green` 32, `corrections` 31. **Neither shape is wrong**; a verdict-shaped handoff is **not** to be rewritten into the unit shape — *"that would mean inventing values nobody wrote."* **Known gaps stay recorded gaps in frozen baselines** (U8.15's for the unit shape, U8.18's for the verifier shape); the guard fails on any **new** missing required key. **And the concurrency cap was updated `≤3 → ≤5`, attributed to the user's explicit instruction** — so a reader can tell an **operator decision** from a **build convenience**.

**Verified on disk by U8.20.** `AGENTS.md` (read-only for this wave, `V8.21`'s) now states **both shapes** with their keys, states that the verifier verdict is *"a **different** shape with a different job"*, **forbids** rewriting one into the other (*"that would mean inventing values nobody wrote"*), locates the **frozen baselines under `state/logs/`**, and carries the cap line **"Concurrency cap: ≤5 concurrent subagents.** Raised from ≤3 by explicit **user instruction** during this build" — with the user's quoted wording and a statement that it is **not a build convenience**. **`reported-only`:** the **45/137** figure, the four repairs, the **243/73/195** debris counts, the measured 43-handoff key frequencies, and the existence/content of the frozen baselines are `U8.15`'s and `U8.18`'s reports — **not re-measured here**. **Open:** `(bs)`/U8.17 recorded `U8.15` as `status: "partial"` with an **empty repair list** and a `PENDING` guard, and the parse-failure count **disputed** (U8.15's **4** vs U8.14's **1**); **U8.18's reconciliation does not by itself settle that count**, which stays open. **The generalisable rule:** *a contract that a third of its practitioners cannot follow without being wrong is a **defective contract** — reconcile the **contract**, and freeze the historical gaps rather than fabricating the missing values.* **Units:** U8.15 (measurement + repairs), U8.18 (reconciliation); on-disk verification by U8.20.

---

*End of the U8.20 append. Entries **(a)–(bv)** above are unchanged; **4** entries were appended **(bw)–(bz)**, so the ledger now holds **78** entries and the next letter is **`ca`**. **Supersessions — all made by adding new entries; none by editing history:** none of the four rewrites an earlier entry; `(bx)` supersedes **only the diagnosis** of `V5.20`'s stale-snapshot finding, whose observation stands exactly as written, and `(bw)` records the discriminator's judgement without altering any entry that cites it.*

**Section E — no additional settled item.** U8.20 found **no further settled** item beyond A–D and **did not pad the list to reach a letter**; this is a scope note, not an entry. **Deliberately not pre-credited (in flight, named for the next unit):** **`U8.19`** (`run.py`, `tests/test_run.py`); **`V5.26`** (`docket/assemble.py` — its mtime `2026-10-08 09:22:20` was **73 s** before this unit's clock reading `09:23:33`, so the shas pinned in `(bw)` are **observation pins with a short half-life** — and the five docket test files); **`U6.21`** (`tests/test_dashboard.py`; see `(by)`); and **`V8.21`** (`AGENTS.md` read-only, `tests/test_orchestration_handoffs.py`). **U8.20 made zero LLM calls and ran no test suite.**

---

## (ca) [verified on disk: the corrected rule, the emit branches and the renamed test node; the pin file's comment is `U8.24`'s report, `reported-only` except as pinned below] The pin's prose was false: the rule has three parts, and `< 12` is a **refusal**, not a reduction

**The claim that was wrong (`U8.19`).** `U8.19` wrote that a short pin is *"reported as reduced at **every** length below 64 hex"*. Verifier **`V8.23`** found that **false for lengths 1–11**: `_same_digest` requires `width >= 12`, so a 1–11-hex pin is **refused as a mismatch**. **The behaviour was correct and fail-closed; the *prose* was not.** `U8.24` corrected it.

**The rule, exactly as the code implements it (verified on disk).** `src/resextract/run.py` sha **`e778e9678cf1fdbc…`**, mtime **`2026-10-08 09:32:51`** — the function is at **`:939`**, its body at **`:957–958`**:

```python
width = min(len(a), len(b), 64)
return width >= 12 and a[:width] == b[:width]
```

- **`< 12`** ⇒ **refused as a mismatch** — and **no `PIN ABBREVIATED` note**;
- **12–63** ⇒ **match + `PIN ABBREVIATED` + `REDUCED STRENGTH`**;
- **`64`** ⇒ **match, silent**;
- **`> 64`** ⇒ **refused + `PIN OVERLONG`**, checked **before** the comparison.

**The `< 12` clause is verified by branch structure, not taken on report.** The chain is `if pin is not None and _pin_is_overlong(pin):` → `_add_note(...)` / `_note_unusable(...)` (**`run.py:1123`**, note at `:1131`), then `elif _same_digest(provenance["sha256"], pin):` (**`:1169`**) → `digest_state = "match"` and **only inside that branch** `if _pin_is_abbreviated(pin):` → `_add_note(... PIN ABBREVIATED ...)` (**`:1172`**, note at `:1175`), then `else:` (**`:1182`**) → `digest_state = "mismatch"` and **no note at all**. A `< 12` pin therefore falls to the `else`: **refused, and silent about abbreviation**. The docstring at **`run.py:920`** says the same in prose — *"(fail-closed, no `PIN ABBREVIATED` note)"*. **`> 64` is refused before the comparison** is likewise structural: the overlong test is the first arm of the chain, ahead of the `_same_digest` call.

**⚠️ Line-number drift — do not quote the card's addresses as pins.** The card cites the two body lines at `run.py:946–947` and the `PIN ABBREVIATED` note at `:1161`; **observed `:957–958` and `:1175`** — **+11** and **+14**. The card's four "live site" addresses (`run.py:888`, `:911`, `:937`, `:1245`) no longer land on the cited prose either (at this sha `:888` is a comment about the 12–63 range, `:911` is `def _pin_is_abbreviated`, `:937` is blank). **What is verified is the corrected *content*, at the sha and mtime above — not the card's line numbers.** By contrast `tests/test_run.py` (**sha `13078b3cc3bdcae6…`**, mtime **`2026-10-08 09:33:19`**) matches the card exactly at **`:1877`** (the `RULE (short pins, one sentence — corrected by U8.24)` comment), and the **renamed node** is at **`:1909`**, not `:1908`.

**The rename (verified).** `test_abbreviated_pin_warns_at_every_length_below_the_digest` → **`test_abbreviated_pin_warns_at_every_length_from_12_to_63`** — so the **test list itself stops making the false claim**, which is the half a prose-only fix would have left behind.

**The pin's comment (`U8.24`).** Its comment was corrected to match the enforced policy: pin sha **`52f491ed…` → `8420547f…`**, the **digest value byte-identical under `tomllib`** (`4790bbb1…`), the `path` and `[graphs]` keys unchanged, and a dry run still reporting *"matches the pinned digest"*. **A comment edit to a control's data file must be datable by the file's sha** — so the new sha is recorded: **Observed here:** `config/graph_pin.toml` sha **`8420547fe33da0b0…`** (full `8420547fe33da0b06d54632ae2f7785904cfb52e52e45cbfe57bf39e492d0785`), mtime **`2026-10-08 09:33:29`** — **matching `U8.24`'s reported new pin sha `8420547f…`**, so the comment edit is verified on disk and datable by this sha. **`reported-only`:** the `tomllib` byte-identity and the dry-run result are `U8.24`'s and were **not re-run here** (this unit runs no pipeline and no test suite); `V8.23`'s contemporaneous record still shows the **pre-correction** `52f491ed…` (`orchestration/VERDICTS.md:1736`), which dates the edit between them.

**Units:** `U8.19` (the change), `V8.23` (the overstatement), `U8.24` (the correction); on-disk verification by U8.26.

---

## (cb) [verified on disk: the guard's design change and the two hash-pinned baselines; the FAIL, the reproduction and the 157-file sweep are `V8.21`'s and `U8.22`'s, `reported-only`] The guard that could never go green — and the design flaw that produced it

**The FAIL (`V8.21`).** `V8.21` **failed `U8.18`**: the handoff guard was **red on unchanged data** (`1 failed, 7 passed`), because `U8.18`'s own **measurement** recorded `V6E.json ['blocker','next_unit_hint']` while **both** the shipped baseline **and** the guard's inline copy recorded only `['blocker']` — so the live corpus appeared to have gained a **new** missing key. `U8.22` reproduced it (with `V6E.json`'s sha **stable across two reads** ⇒ not a mid-write), fixed it by **declaring** the missing key in **both** copies, and proved **`8 passed / 0 failed`** — **without** inventing `next_unit_hint` into `V6E.json` (a historical record), excluding the file, or weakening the guard (required sets **byte-identical**: unit 7, verifier 6). Its **157-file sweep** found the condition **clean beyond `V6E`**, plus one **over-declaration** (`V5.25.json` declared `[next_unit_hint]`, measured `[]` — harmless, but it **hides a fixed file**), and that **`U8.15`'s `V*` entries are dead text** (`classify()` routes every `V*` to the verifier contract); it also **refuted `U8.18`'s card**, which blamed transient `V5.26.json`.

**The generalisable root cause — the point of this entry.** The guard asserted **`copy == copy`**, never **`copy == measurement`** — and **two copies of a wrong value agree perfectly**, so **a check that compares two derived artifacts cannot detect a derivation error.** The failure it could not see was a *transcription* error in the pair itself.

**Verified on disk by U8.26 — and the root cause has since been adopted as the fix.** `orchestration/handoffs/V6E.json` sha **`d65fa537cf02c862…`**, mtime **`2026-10-08 08:04:37`**; its top-level keys are `['checks','note','overall','scope','status','tool_calls','unit','write_paths']` — it carries **neither `blocker` nor `next_unit_hint`**, so a verifier-contract gap of **two** keys for that file is the *correct* measurement, and `['blocker']` alone was the defect. The frozen verifier baseline now records exactly that: `state/logs/U8.18/verifier_shape_baseline.json` sha **`ad97c9061e924dd4…`** (full `ad97c9061e924dd4929ff7ef74d2d76a9c60bfd02a4879a4383a8e8be6f5add4`), mtime `2026-10-08 09:35:15`, maps **`V6E.json: ["blocker","next_unit_hint"]`** — so `U8.22`'s repair is landed and `V5.25.json` no longer appears among the frozen verifier gaps, the over-declaration having been removed rather than the file edited.

**The copy==copy design has been dismantled (on disk; `U8.25` in flight).** `tests/test_orchestration_handoffs.py` sha **`9a6c7039b65658aa…`**, mtime **`2026-10-08 09:36:14`** — **33 s** before this unit's clock read of `09:36:47`, so `U8.25` was **mid-edit**. As of that sha the inline copies are **gone**: the two baselines are the **sole sources**, each hash-pinned, and the guard's own docstring states the reason in the root cause's own terms — *"There is deliberately no longer an inline copy of either record to compare the files against: that comparison was copy==copy and could never detect a transcription error in either copy."* The declared pins match the files **byte-for-byte** (verified independently here): `state/logs/U8.15/baseline_gaps.json` = `1a16e39d72f03d02…` (full `1a16e39d72f03d0272020f3b30c20b88d14a43ebc5650b33e69980d11316d716`, mtime `09:35:15`), and `state/logs/U8.18/verifier_shape_baseline.json` = `ad97c9061e924dd4…`. **Also verified as text on disk:** the docstring records that `U8.25` **removed the 13-file `BASELINE_NO_STATUSISH` exemption** (measured as protecting nothing, its keeper assertion a tautology), and that `test_no_baseline_entry_over_declares` exists precisely so the frozen baseline can only ever **tighten** against a re-measured corpus. **`reported-only` for every `U8.25` claim of outcome** — `U8.25` is **in flight**, its file changed under this unit's read, and **no test suite was run here** (hard bound), so the `8 passed / 0 failed` result is **not** re-verified.

**The contract change (`AGENTS.md`, read-only here).** sha **`201a0b9eb0bc5de7…`**, mtime **`2026-10-08 09:20:40`** — it documents **two** handoff shapes, derived **by measurement** from the 43 `V*` handoffs, and forbids rewriting one into the other. **`reported-only`:** `V8.21`'s confirmation of that derivation (core keys all **≥90%**, no "not required" key reaching 90%) and that the governance diff was **exactly the five claimed items** with **nothing outside scope**. **Its aside is worth keeping:** its **first handoff draft was invalid JSON and the guard caught it live** — the enforcement works.

**Supersession — by adding this entry, never by editing history.** `(bz)`'s account of `U8.18`'s reconciliation stands **exactly as written**; this entry supersedes only the **sufficiency** of the `copy == copy` design that account describes, and `(bz)`'s own `reported-only` mark on the guard's behaviour is **stale as of this wave** (the guard was in fact **red**). **Units:** `U8.18` (the change), `V8.21` (FAIL), `U8.22` (fix + sweep), `U8.25` (in flight); on-disk verification by U8.26.

---

## (cc) [verified on disk: the four cap emitters, the variant spelling, the docstring hazard and `assemble.py`'s corrected sha; the guard's non-vacuity demonstration and the consumer sweep are `U5.23`'s/`U5.28`'s, `reported-only`] The discriminator: one half is now a contract, the other is still a hint

**The overload (`U5.19`).** `Claim.verdict_reason` carries **two** unrelated meanings: the **`CONFIRMS`-cap reason** and a **provenance-divergence note** (the claim's `producer` is the *assessing* producer while the material was mined by another).

**What `V5.25` found.** The documented discriminator is **exactly right today** — **four** cap emitters of `capped at EXTENDS`, of which only **three** reach `Claim.verdict_reason` because `materialize` never copies `rationale`; the `F2` phrase emitted at `materialize.py:1686` **alone**; the substrings **contiguous in a single literal**, **not** assembled from parts (the failure a whole-phrase grep would hide). **But** it called the discriminator **"a hint, not a contract"**, because **nothing pinned it** and a **variant spelling already exists in-repo**: `capped to EXTENDS` at `tests/test_docket_reassembly.py:1385`.

**What `U5.23` established.** The overload is **documentation-only**: no consumer treats non-`None` as a downgrade, and the **actual cap gate** keys on **verdict + producer**, reading the reason only **after** deciding, to preserve-and-append.

**What `U5.28` landed — two judged patches.** The stale docstring in `assemble.py` (`0c8f7386…` → **`8cb9af52…`**) and a **non-vacuous guard**, demonstrating that the **`F2` side is now a contract** (renaming the `F2` emitter **fails** it).

**Verified on disk by U8.26.** `src/resextract/docket/assemble.py` sha **`8cb9af52fa8fc940…`**, mtime **`2026-10-08 09:27:06`** — **matching `U5.28`'s reported new sha**, so the docstring correction is **confirmed landed**. The cap phrase is present at **exactly four** sites, matching `V5.25`'s count of four, at these **observed** addresses: `assemble.py:1143`, `materialize.py:1631`, `materialize.py:1641`, `assess/verdicts.py:404`. ⚠️ **The card's `assemble.py:1138` has drifted to `:1143`**; `materialize.py:1631`/`:1641` and `verdicts.py:404` match exactly. The **variant spelling** is confirmed verbatim at `tests/test_docket_reassembly.py:1385` (`"declared CONFIRMS capped to EXTENDS: producer replay is not a model"`). The **grep false-positive hazard** is confirmed: `assemble.py:2500` carries the literal ``claim.producer`` is the *assessing* producer **inside a docstring** (card said `:2495`), **not an emitter**. **Not re-pinned here (budget):** `materialize.py` and `assess/verdicts.py` — `U8.20`'s last pins for them are `5dbf520e4822f681…` and `754101b895f30545…`, and `tests/test_docket_reassembly.py` was pinned by `U8.20` at `492872341ea37a8e…`. `reported-only`: `V5.25`'s "materialize never copies `rationale`" grep (0 hits) and `U5.23`'s consumer sweep were **not re-run**; the **cap gate at `assemble.py:1134`** is carried from `(bw)`'s on-disk verification, which this unit did not repeat.

**⚠️ THE GAP THAT REMAINS — record it, because a green guard is not coverage here.** Renaming the cap phrase at **all four** cap emitters leaves the guard **green** — *"the absence assertion cannot be falsified by renaming a cap site"* — so the **cap-side discriminator is unpinned in the presence direction**, and a **cap-detecting consumer can still break silently**. The named remedy is to pin the cap phrase's **presence** and its **emitter coverage (4)**, or to land the **typed standing**. **A guard that only asserts absence has no opinion about the thing it is meant to protect.**

**Supersession — adding this entry, never editing history.** `(bw)` recorded the discriminator's judgement and the remedy as *"to land the handed-up guard"*; that remedy is now **partly landed** (the `F2` side) and the **residual is the cap side**, as above. `(bw)` stands **unedited**. Note also that `(bw)`'s emitter address `assemble.py:1138` has drifted to `:1143` at this sha — **cite the sha, not the number**. **Units:** `U5.19`, `U5.23`, `V5.25`, `U5.28`; on-disk verification by U8.26.

---

## (cd) [verified on disk: the repaired claim, the manifest sha, `EVIDENCE.md`'s length and the `blob_sha` residual; the surgical diff, the non-idempotence repair and the ruling are `U5.27`'s and `U5.22`'s, `reported-only`] The deliverable was repaired — and a render is **not** byte-idempotent

**The FAIL and the repair.** Verifier **`V5.20`** had **failed** the delivered `duval-replay-material` docket for rendering **`CONFIRMS`** on a **non-model** producer, because the earlier re-render **supplied `claims` verbatim** so the cap never ran. **`U5.27`** repaired it by re-deriving through **`assemble_docket == assemble()`** (the **render-side cap** `_cap_uncapped_claims`), **rehearsed on a copy, applied once**, with **all inputs taken from the manifest's own recorded values** and the **standing not hand-edited**.

**The surgical evidence (`U5.27`).** File-level diff **= exactly `[MANIFEST.json, CLAIMS.md]`** with the file **set identical**; manifest **top-level key diff = `['claims']` only**; inside `claims` only **`C-curated.verdict`** (**`CONFIRMS` → `EXTENDS`**) and **`.verdict_reason`** (**null → a reason**) moved; title unchanged, `EVIDENCE.md` **151 lines**, **8 contexts each exactly once**, **8/8 material dest+sha**, **banner 15**, `window_sealed` **still `null`**, `replay`/`draft`/`promotion_eligible(False,…)` all unchanged; **`verify_docket` `ok=True, problems=[]`**. New manifest sha **`ce45766d…`**, tree **`158ae3d2…`**.

**Verified on disk by U8.26.** `dockets/duval/duval-replay-material/MANIFEST.json` sha **`ce45766d4ac845ed…`**, mtime **`2026-10-08 09:28:51`** — **matching the reported new sha**. `claims[0]` is `C-curated`, `kind` **`file-fact`**, `producer` **`unknown`**, `verdict` **`EXTENDS`**, and `verdict_reason` **non-null**: *"verdict CONFIRMS was passed to assemble() but the claim's producer is 'unknown', not 'model'; capped at EXTENDS by the same rule as materialize._claim_standing (a non-model run may not assert CONFIRMS)"* — i.e. the render-side cap **did** run, which is the repair's whole substance. `window_sealed` is `null`. `EVIDENCE.md` is **exactly 151 lines**. **`material` holds 8 items and 0 of 8 record a `blob_sha`** — the residual below, **verified** rather than taken on report. `ITEM.md.r1`–`.r4` exist and **no `.r5`** does, and `HISTORY.md`'s last lines read *"material provenance preserved for 8/8 entries"* and *"previous `ITEM.md` preserved as `ITEM.md.r4`"* — consistent with the `.r5` having been deleted after the render.

**⚠️ Three clauses of the surgical evidence are `reported-only`, and one count does not reproduce.** The card says the manifest key diff leaves *"17 other keys byte-identical"*; this unit observes **17 top-level keys in total** (`claims`, `evidence`, `freshness`, `generated_at`, `generated_by`, `lane`, `material`, `open_questions`, `prior_art`, `results`, `rework_open`, `schema`, `status`, `status_reason`, `target`, `web_sources`, `window_sealed`) — i.e. **16 besides `claims`**, not 17. The **claims-only substance is verified**; the **count is not**, and is left open rather than reconciled here. The card's *"8 contexts each exactly once"* is **not reproduced** by a `## `-heading count (**7**) — a different counting rule, so the clause stays `reported-only`. And *"banner 15"* could not be located: `banner` is **`null`** in the manifest, so that figure is `reported-only` too.

**The by-design non-idempotence — the durable rule.** The render **also appended a `HISTORY.md` line and created a new `ITEM.md.r5`** (its bounded `ITEM` rotation), which pushed the **banner-file count 15 → 16**; `U5.27` **restored `HISTORY.md` and deleted the `.r5`** to keep the diff claim-only. **So a re-render is NOT byte-identical by construction** — a verifier expecting byte-identity after one **will fail**, and the **`.rN` rotation** plus the **append-only `HISTORY.md`** are the reasons. *Byte-identity is the wrong success criterion for a renderer with an append-only history and a bounded rotation; the right one is the claim-level diff.*

**The ruling it implemented.** `_smoke` (**`41ec711a…`**) is the **frozen** witness and **stays reporting** its contradiction — *"a backward-compatibility witness proves old artifacts still **LOAD**, not that they **PASS** every honesty check"* — while the delivered docket is repaired.

**The four residuals, one of which makes the schema case concrete.** (1) **0 of 8 material items record a `blob_sha`** (all `working_tree` ⇒ hash-pinned to copied bytes, **not commit-pinned**) — **verified here**. (2) **`C-curated` is `kind='file-fact'` and can only render `EXTENDS` + a cap note — there is still no standing for mechanically-verified facts**, so a *proven* claim is **indistinguishable from an unverified one in the deliverable** (`kind='file-fact'` **verified**; the inference is `U5.27`'s). (3) The store's `dockets` row was **deliberately not updated** — `reported-only`. (4) **`HISTORY.md` carries no record of the repair** — `reported-only`.

**Supersession — adding this entry, never editing history.** `(bu)`'s `reported-only` mark said the ruling's **implementation was in flight**; that implementation is now **on disk in the delivered artifact**, so `(bu)`'s *in-flight* status is **stale and superseded here**. `(bu)` itself is **untouched**, and this entry does **not** re-adjudicate the ruling. **Units:** `V5.20` (FAIL), `U5.22` (boundary), `U5.27` (repair); on-disk verification by U8.26.

---

## (ce) [verified on disk: the `source` field, the `null` vs `false` distinction and the `api.py` sha; the live probes and the fixture repair are `V6.22`'s and `U6.21`'s, `reported-only`] The dashboard surface — verified, with four corrections

**What was built and verified.** `U6.20` made the on-disk `MANIFEST.json` **authoritative** with the store row as a **fallback** and added a **`source`** field; `U6.21` fixed **three red tests** by discovering they failed on a **fixture** named `ok-docket` whose `Claim C1` had `CONFIRMS` and **no producer** — **fixture-wrong**, not a real-docket issue — and made the fixture **genuinely valid** rather than excusing the assertion. `V6.22` verified both and found:

- **nothing escaped the dockets root**: five traversal attempts (`../etc`, `/etc`, `dockets/../../etc`, `..%2f..%2fetc%2fpasswd`, `%2e%2e%2f…`) all rejected, a **symlinked docket dir** 404 **and** excluded from the board, a **file symlink** excluded; a gone-directory row is **never resurrected**;
- **a prose claim we both made was wrong:** *"store-sourced ⇒ `verify.ok = null`"* holds **only for the store-only listing** — the **corrupt-manifest fallback reports `false`**, because **verification ran and failed**. **THE DISTINCTION TO RECORD: `null` = no verification was run; `false` = it ran and failed.** The **code is right**; the **prose conflated them**. (`U6.23` is correcting the live wording — `reported-only`.)
- **`U6.20`'s own correction of an earlier finding is author-attested, not independently reproduced** (no `api.py` pre-image exists).

**Verified on disk by U8.26.** `src/resextract/dashboard/api.py` sha **`4f5698cecee8ceb6…`**, mtime **`2026-10-08 09:36:17`** — ⚠️ **`U6.23` is editing this file live** (mtime **30 s** before this unit's clock read of `09:36:47`), and `U8.20`'s pin of the same file was `004d88fdbb61a2fc…`, so it has moved **twice** since that pin: **quote the sha, never the line number.** The `source` field is present at **`:1066`** (`None`), **`:1109`** and **`:1227`** (`"store"`), **`:1156`** and **`:1317`** (`"manifest"`) — the card's `:1218`/`:1308` have drifted to `:1227`/`:1317`. The **no-verification** case is exactly `"ok": None, "problems": ["no MANIFEST.json on disk: not verified"]` at **`:1220–1221`**, and **`"ok": False`** appears in the **ran-and-failed** paths at **`:616`**, **`:791`**, **`:1085`**, **`:1312`**, **`:1479`** — **so the `null` vs `false` distinction is verified in the code, not merely asserted by the verifier.** The traversal probes, the symlink exclusion and the fixture repair were **not re-run** (no test suite, hard bound): `reported-only`.

**Supersessions — adding this entry, never editing history.** (i) `(by)`'s `reported-only` mark said *"the resolution of that split is in flight (`U6.21`)"* — **`U6.21` has since reported and fixed it**, so that mark is **stale and superseded here**; `(by)` stands unedited. (ii) `(bx)`'s prose clause that a store-sourced entry *"reports `verify.ok = None` rather than implying a verification it did not run"* is **corrected** by the `null`/`false` distinction above — true of the **store-only listing**, false of the **corrupt-manifest fallback**. `(bx)`'s observation **stands exactly as written**; only its generality is narrowed. **Units:** `V5.20` (the original finding), `U6.20`, `U6.21`, `V6.22`; on-disk verification by U8.26.

---

## (cf) [verified on disk: the ignore rule, its anchoring and its stated reason; the observation itself is `U5.28`'s] Containment method: **`git status` cannot witness docket drift**

**The observation (`U5.28`).** `U5.28` saw `duval-replay-material` rewritten **under it** (`9b6a577e… → ce45766d…`, its sibling's repair) **while `git status --porcelain -- dockets` returned 0 lines** — because **`dockets/` is gitignored**.

**The rule.** **Many units have cited "porcelain clean" as containment evidence, and it cannot witness drift in an ignored tree.** For **docket containment, hash the artifacts — porcelain is silent by construction.** This also **explains why the sha-based checks were the ones that caught every drift**: they were the only instrument pointed at the bytes.

**Verified on disk by U8.26 — and the rule has a precise boundary.** `.gitignore:15` is **`/dockets/`**, and it is **deliberately anchored**: the comment at **`.gitignore:9–14`** records that the unanchored rule `dockets/` *"also matched a directory named 'dockets' at any depth - including the test fixture tree `tests/fixtures/dashboard-store/dockets/**`"*, so it was anchored to the root. **The refinement to record: porcelain is silent for the ROOT `dockets/` tree only** — a **nested** fixture docket tree **is** tracked, and a change there **would** show. That **sharpens** the rule rather than weakening it, since the artifacts this build reasons about are the root ones. **Units:** `U5.28` (the observation); on-disk verification by U8.26.

---

## (cg) [`reported-only` — the rule comes from `U8.24`'s report; the two miscited cards were not located here] Method correction: `ast.dump` equality proves a `#` comment edit — and is **FALSE** for a docstring edit

**The correction.** **`ast.dump` equality is the right proof for `#` comments but is FALSE for a docstring edit**, because a docstring **is** an AST `Constant` — so the dumps differ and the proof **fails even when behaviour is unchanged**. **Two cards instructed otherwise and cost a unit a call each.** The **correct proof for a docstring** is a **one-`Constant` AST diff plus bytecode-identical code objects** (`co_code` / `co_names` / `co_varnames` / `argcount` / `co_flags`).

**Why it is its own entry.** It is a **rule about proof method**, not a fact about the pin — its failure mode is **a false positive on a correct change**, which is the opposite direction from `(ca)`'s false claim. **`reported-only`:** the two miscited cards and the one-call cost were **not located in this unit's budget** and are taken from `U8.24`'s report; the bytecode-identity proof was **not executed here** (no pipeline run). **Recorded, not invented.** **Units:** `U8.19` (the change), `V8.23` (the overstatement), `U8.24` (the correction).

---

**Section G — scope note, not an entry.** U8.26 found **no further settled** item beyond A–F and the A-method line above, and **did not pad the list to reach a letter**. **Explicitly NOT recorded as corrections, because they were not verified on disk and were not settled by this wave:** the `banner 15` figure, the *"8 contexts each exactly once"* count, the *"17 other keys"* count (which **does not reproduce** and is left open, above), `V5.25`'s `materialize`-never-copies-`rationale` grep, `U5.28`'s guard non-vacuity demonstration, `U8.22`'s 157-file sweep, `V6.22`'s traversal probes, `U8.25`'s outcome, and the `ast.dump`/bytecode proof. **Deliberately not pre-credited (in flight, named):** **`U5.29`** (`tests/test_docket_provenance.py`); **`U8.25`** (`tests/test_orchestration_handoffs.py`, the baseline JSONs — see `(cb)`, whose file changed **33 s** before this unit's read); **`V5.30`** (read-only, the real dockets); **`U6.23`** (`src/resextract/dashboard/api.py` — **changed 30 s** before this unit's read — plus `tests/fixtures/dashboard-store/build.py` and `tests/test_dashboard.py`).

---

*End of the U8.26 append. Entries **(a)–(bz)** above are unchanged; **7** entries were appended **(ca)–(cg)**, so the ledger now holds **85** entries and the next letter is **`ch`**. **The additive proof:** before = sha256 `dac0cad6aea8c91ff4ff53d5d370dd87a8c392a76657870b3cc12aeb77e3d256`, **160134** bytes; as of the end of `(cg)` = sha256 `a6a0feaf06430d303a97357e54111d92504f058776124af2394c010186a040fc`, **186957** bytes; and the pre-existing **160134**-byte prefix is **byte-identical** (`cmp` clean) against the saved copy `state/logs/U8.26.prefix.backup.md`. The **6 original `reported-only` markings — (d), (e), (h), (i), (o), (p) — are preserved**, and **0** existing entries were modified.*

**Supersessions — all made by adding new entries; none by editing history.** **`(by)`**'s *"the resolution of that split is in flight (`U6.21`)"* is **stale** — `U6.21` has reported and fixed the three red tests — and is superseded by **`(ce)`**. **`(bz)`**'s *"reported-only"* mark on the guard's behaviour is **stale** — the guard was in fact **red on unchanged data** — and is superseded by **`(cb)`**. **`(bx)`**'s clause that a store-sourced entry *"reports `verify.ok = None`"* is **narrowed** by **`(ce)`**: true of the store-only listing, false of the corrupt-manifest fallback. **`(bw)`**'s forward-looking remedy *"to land the handed-up guard"* is **partly landed** (the `F2` side) with the **cap side still unpinned**, per **`(cc)`**. **`(bu)`**'s *in-flight implementation* status is **stale** — the ruling is now implemented in the delivered artifact — and is superseded by **`(cd)`**. **Not one of `(bu)`, `(bw)`, `(bx)`, `(by)`, `(bz)` was edited, reordered, strengthened or softened.** **U8.26 made zero LLM calls, ran no test suite and started nothing.**

---

## (ch) [verified on disk: the key sets and counts, the banner-file count on both sides, and `EVIDENCE.md`'s measured structure; the repairs themselves remain `U5.27`'s] The three inherited discrepancies are settled — one wrong count, two counting rules

**Why this entry exists.** `(cd)` left three clauses of `U5.27`'s surgical evidence `reported-only`, one of them explicitly **open** (*"17 other keys"*). This unit measured all three against the live docket and its backup. **A count without a recipe is not evidence**, so each number below is given with the exact command that produced it.

**(1) "the other 17 keys byte-identical" — a WRONG COUNT, with the substance correct.** The claim needs **18** top-level keys; the manifest has **17 in total**. Recipe: `.venv/bin/python -c "import json;a=json.load(open('dockets/duval/duval-replay-material/MANIFEST.json'));b=json.load(open('state/backups/U5.27-replay-material/duval-replay-material/MANIFEST.json'));print(len(a),len(b));print(sorted(set(a)^set(b)));print([k for k in a if k in b and a[k]!=b[k]])"` → `17 17`, symmetric key difference **empty** (the key sets are identical), and the **only key whose value differs is `claims`**. A strict canonical re-serialisation comparison — `json.dumps(a[k],sort_keys=True,separators=(',',':')) == json.dumps(b[k],…)` per top-level key — gives **16 identical / 1 differing (`claims`)**. So it is **16 other keys, not 17**: the **count is off by one** while the **substantive claim holds exactly** (*the only key whose value moved is `claims`*). Note also that "byte-identical" can only mean **value-identical after canonical JSON re-serialisation** — the keys of a parsed object have no byte identity of their own — and that is the reading the recipe implements. Shas/mtimes observed: live manifest **`ce45766d4ac845ed…`**, mtime **`2026-10-08 09:28:51`**; backup **`9b6a577e1402fe41…`**, mtime **`08:36:35`**.

**(2) "banner 15" — a METHOD DIFFERENCE, and not a manifest field at all.** `banner` is **not a key of the manifest**: `'banner' in m` → **`False`**, and `m.get('banner')` is `None` **because the key is absent** — so `(cd)`'s phrasing *"`banner` is `null` in the manifest"* is itself **slightly wrong** (absent, not present-and-null). **15 counts FILES CONTAINING THE BANNER STRING**, `PROVENANCE: replay-produced`. Recipes: `grep -rl 'PROVENANCE: replay-produced' dockets/duval/duval-replay-material | wc -l` → **15**; the same over the backup root → **15**; and `diff` of the two file lists **after normalising each to a path relative to its docket root** is **clean** (`SAME-RELATIVE-SET`). **The pre-repair side therefore also measures 15** — which independently corroborates `U5.27`'s account that the render's transient **15 → 16** bump was restored (`(cd)`). Not a wrong number; a number about **files**, not about a **field**.

**(3) "8 contexts" vs `grep -c '^## '` = 7 — two different countables, and BOTH methods are correct.** Measured on `EVIDENCE.md` (**151 lines, 8338 bytes**): headings by level **`h1=2, h2=7, h3=3`** (recipes: `grep -c '^## ' f`, `grep -c '^### ' f`), **11** list items (`grep -c '^[-*] ' f`), **10** table rows (`grep -c '^|' f`), and **8** `context:` lines (`grep -n 'context' f` → `:26, :55, :65, :75, :85, :135, :142, :149`). **8 = the number of evidence items; 7 = the number of `## ` headings.** They reconcile exactly: **5** of the `## ` headings are per-file excerpts (`:22 adapter.ts`, `:51 decisions.ts`, `:61 lease.ts`, `:71 performance.ts`, `:81 FINDINGS.md`) **plus** `## Copied material` (`:9`) and `## Other evidence entries` (`:130`) = **7**; and the item count adds the **three `###` entries** under *Other evidence entries* (`baseline.json` `:132`, `CITATION.cff` `:139`, `README.md` `:146`) → **5 + 3 = 8 evidence items**, matching the manifest's **8** material items. ⚠️ The second `# ` heading at **`:88` (`# FINDINGS — the whole picture in one place`) is INSIDE the excerpted `FINDINGS.md` text**, not a heading of `EVIDENCE.md` — which is why `h1=2` and why a naive heading count is the wrong instrument for "contexts". **Verdict: a method difference — `U5.27`'s "8" is not wrong and the appender's "7" is not wrong either.**

**Units:** `U5.27` (the surgical evidence), `V5.30` (the challenge), `U8.26` (the open flag); all three numbers measured here by **U8.28**.

---

## (ci) [verified in code on disk at `api.py` sha `4f5698ce…`: the `None` arm, the four docket `verify.ok` failed arms and the landed disambiguating comment; `U6.23`'s outcome is `reported-only`] The `verify.ok` two-state rule is now a contract — and the record's generalisation is corrected

**The rule, verbatim from `U6.23`** (supplied text, quoted as given and attributed): *"two distinct states, never one. `verify.ok` is `None` here because **no verification was run**: there is no `MANIFEST.json` to verify and this store-only listing path never calls `verify_docket`. That is **NOT** the same as the corrupt-but-present artifact handled above, where `verify_docket` **did** run and failed, so `verify.ok` is `False`. So: a store-sourced entry with no artifact reports `None` (did not run); a corrupt-but-present manifest reports `False` (ran and failed)."*

**It is now IN THE CODE, not merely in a report.** `src/resextract/dashboard/api.py` sha **`4f5698cecee8ceb61df6d95cf60522611cb7d71a643ac31cf88c15d7ede12f0f`**, mtime **`2026-10-08 09:36:17`** — **the same sha `U8.26` observed**, so the file has **not moved** since that read and `U6.23`'s edit is **landed and stable**. The comment sits at **`:1210–1218`**, immediately above the store-only arm at **`:1219–1222`**: `"verify": {"ok": None, "problems": ["no MANIFEST.json on disk: not verified"]}`.

**Re-located by content — the card's addresses were `U8.26`'s, and these are re-measured:**
- **`None` = did not run.** The load-bearing **store-only** site is **`:1220`** (`:1221` carries the reason string). Three further `None` sites are **initialisers that a run overwrites**: `:601` (journal listing, `{"ok": None, "first_bad_seq": None}`), `:1076` (manifest listing), `:1307` (the detail endpoint, `verify: dict[str, Any] = {"ok": None, "problems": []}`).
- **`False` = ran and failed.** `:616` (journal listing: `journal_mod.verify` raised, after the call at `:614`), `:791` (journal detail, same shape), and the two **`verify_docket` ran-and-raised** arms at **`:1085`** and **`:1312`**, whose calls are at **`:1081`** and **`:1310`**. **Those four are the docket/journal `verify.ok` failure arms, and they confirm the `null`/`false` distinction in the code, not merely in a verifier's report.**
- **One precision refinement to `U8.26`'s list.** `U8.26` named **five** `False` sites including **`:1479`**; measured, `:1479` is `report = {"ok": False, …}` — the **doctor report's own `ok`** (the never-500 probe path), a **different object and a different field**, not `verify.ok`. The artefact is accurate as a grep for `"ok": False`; it must not be read as five `verify.ok` sites.
- There is **no literal `"ok": True`** in the file at this sha: the success paths compute `bool(ok)` (`:614`, `:790`) or take `verify_docket(...).to_dict()` (`:1082`, `:1311`). The True arm is **computed, not spelled** — so a grep for `"ok": True` returns nothing and that absence is not evidence.

**The record-only correction.** The generalisation *"store-sourced ⇒ `verify.ok = null`"* — relayed by the orchestrating session and by `V6.22`, and written into the record at `(bx)` — is **narrowed**: it is true **only for the store-only listing**; the **corrupt-but-present** fallback reports **`False`**, because verification **ran and failed**. `U6.23` reports the conflated prose was **record-only** (the live code carried both states correctly but silently), citing `docs/PLAN_CORRECTIONS.md:2131` and `orchestration/VERDICTS.md:2135` — `:2131` sits inside `(bx)`, confirming the locus is the **record**, not live prose. **`VERDICTS.md` was NOT edited by this unit** (read-only here and outside this unit's write paths). `reported-only`: `U6.23`'s verdict that the prose was record-only and its `75 passed / 58 tests` run — **no test suite was run here** (hard bound).

**Why this is an entry and not a footnote.** A `None` meaning *"did not run"* and a `False` meaning *"ran and failed"* are **different operator facts**; conflating them in prose is the same class of failure `(cb)` records in the guard — **two derived artefacts agreeing with each other while disagreeing with the measurement**. **Units:** `U6.20` (authoritative-manifest change), `U6.21` (fixture repair), `V6.22` (the finding), `U6.23` (the wording correction); code verified here by **U8.28**.

---

## (cj) [verified on disk: the handoff `tool_calls` fields and the unit-card figures; the internal narratives are `U8.24`'s and `U6.23`'s, `reported-only`] The reporting contract is now the build's dominant overrun cause

**The measured counts.** `orchestration/handoffs/U8.24.json` (sha `9520d3579a4328ad…`, mtime `09:37:32`) carries **`"tool_calls": 33`**; `orchestration/handoffs/U6.23.json` (sha `b6865dac66505b09…`, mtime `09:39:42`) carries **`"tool_calls": 35`**. So **two consecutive units burned their bound recovering their own handoff JSON**.

- **`U8.24` (relayed: 33 vs 16 — see the count discrepancy below).** It first mistook the template's **contracted nesting** (the verdict keys **inside `evidence`**) for a **mis-nesting** and hoisted it, then a **repair script failed to assign its dict back and emptied `evidence`**. Recovery, not work. ⚠️ **And the count itself is reported three different ways, measured here:** `U8.24.md:3` declares **`Bound: 18 tool calls (used 26 — overage disclosed in the handoff)`**, while the handoff field is **`tool_calls: 33`**, and the relayed card says **33 vs 16**. So the **bound** differs (16 relayed vs **18** on the card), and the **used** count differs (**26** on the card vs **33** in the handoff) — a **7-call gap inside the same unit's own records**. Which number is "the count" is exactly the recipe question; **state which field, from which file.**
- **`U6.23` (relayed: 35 vs 18).** A **missing `}`**, then **+2 re-running its own faulty measurements**: a **`comm` on unsorted input** reported a **spurious "58 deleted"** tests, and a **tuple-vs-JSON-list** comparison reported a **spurious code-object mismatch** (both recorded verbatim in its handoff). `"tool_calls": 35` is measured; the relayed bound **18** is **not visible** on `U6.23.md` (`grep -niE 'bound|tool call' orchestration/units/U6.23.md` → **no match**), so it stays `reported-only`.

**The durable point — a count can be spuriously wrong because of the TOOLING, not the data.** The unsorted-`comm` case is a **measurement artefact that looked exactly like a real regression** (*"58 assertions deleted"*) — the kind of number a unit is most tempted to publish as a finding. **The mitigation is the one this build states everywhere: state the recipe, and re-run before believing a surprising number.** A surprise that survives a re-run *with the recipe written down* is evidence; one that does not is a bug in the instrument.

**The three standing mitigations to record (contract).** (1) **Validate the handoff JSON immediately after writing it, before anything else**, and again after every later edit to it. (2) **Cards must state the contracted nesting EXPLICITLY** — the verdict keys live **inside `evidence`**; say so rather than leaving a unit to infer it from a template. (3) **Bounds are stated as WORK CALLS, with the mandated final report-back excluded** — otherwise a unit's true work count is **inflated by one**, and `U8.24`'s count would read **32/16**.

**A fourth data point, measured here — the previous append's own additive proof was taken MID-APPEND, and that is structural.** `(cg)`'s closing note records this ledger's after-state as sha256 **`a6a0feaf06430d30…`, 186957 bytes**. On disk, before this append, the file is **188761 bytes** — and `head -c 186957 docs/PLAN_CORRECTIONS.md | sha256sum` returns **exactly `a6a0feaf06430d30…`**. So `U8.26` measured its "after" state **1804 bytes before it finished writing** (its footer and supersession paragraphs came afterwards). Its **prefix proof is sound** (the 160134-byte prefix it compared is *inside* the file and unchanged), but **its "after" sha is not the final ledger state**. **The generalisable rule: a file cannot contain its own final hash** — so the **after-state belongs in the handoff** (`sha256_after` / `bytes_after`), where it can be measured once and never re-derived, and **the ledger footer should carry the *before* state plus the `cmp` result**. This append follows that rule. **Measure the after-state last.**

**Units:** `U8.24` and `U6.23` (the data points, read here); `U8.26` (the fourth, measured here by **U8.28**).

---

## (ck) [the reproduction is `V5.30`'s, `reported-only`; the rule is a method limit established here] A tree hash is path-sensitive, so a destroyed pre-image's tree hash can never be re-derived

**What the verifier hit.** `V5.30` **could not reproduce** the pre-repair tree hash **`02fa18ec…`**: *"recipe is **path-string-sensitive** (same bytes elsewhere = `a1450929`) and that state is destroyed; backup at its own path = `1252e07b`, and its manifest sha `9b6a577e` confirms pre-repair content."* Its recipe, recorded verbatim from its handoff: **`find <root> -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum`** — the **path strings are hashed along with the bytes**, so the same content at a different path hashes differently (`a1450929` for copied bytes vs `158ae3d2` for the live tree at its own path).

**The rule.** A tree hash computed over **paths plus bytes** is **NOT path-independent**. Therefore a **destroyed pre-image's tree hash can never be re-derived** — the path-state *is* part of the pre-image, so `02fa18ec` is **UNVERIFIED, not contradicted**. Only **file-level content** survives a move, so only file-level content can be re-checked after the fact.

**How to record a tree identity so it stays checkable.** Either (a) **per-file shas**, or (b) a hash over a **path-normalised listing** — each file's sha paired with its path **relative to the tree root**, sorted, then hashed — so the same content at a new location reproduces the same value. **Record the recipe beside every tree hash:** a bare tree hash carries an implicit path convention that a later reader cannot recover, which is precisely how `02fa18ec` became unreproducible.

**Verified here (file-level content, which *is* path-independent).** The **backup manifest** sha **`9b6a577e1402fe41…`** at mtime `08:36:35` — the **pre-repair content** — confirms the backup *is* the comparandum for `(ch)`. `reported-only`: the `02fa18ec` / `1252e07b` / `a1450929` figures were **not re-derived here** (that would require re-copying the trees; not done, budget) and are taken from `V5.30`. **Units:** `V5.30` (the limit), `U5.27` (the pre-image).

---

## (cl) [verified on disk: the anchored rule, its comment and the observed shas; the original observation is `U5.28`'s] Containment refinement: `git status` is silent for the ROOT `dockets/` tree **only**

**The refinement.** `.gitignore:15` is **`/dockets/`** — **deliberately anchored** — and the reason is recorded at **`.gitignore:9–14`**: the unanchored rule *"also matched a directory named 'dockets' at any depth - including the test fixture tree `tests/fixtures/dashboard-store/dockets/**`, whose ok-docket/broken-docket fixtures were therefore untracked and absent on a fresh clone."* So **porcelain is silent for the ROOT `dockets/` tree only**: a **nested** fixture docket tree **is** tracked, and a change there **would** show. That **sharpens** the rule rather than weakening it, because the artefacts this build reasons about are the root ones.

**The rule and the observation that produced it.** A docket was **rewritten while `git status --porcelain -- dockets` returned 0 lines** (`U5.28`: `duval-replay-material` moved `9b6a577e… → ce45766d…` under it). **For docket containment, hash the artifacts — porcelain cannot witness an ignored tree.** Independently confirmed here: that exact sha pair is on disk now (`(ch)`), the live tree remains ignored at `.gitignore:15`, and the sha-based check is the only instrument that saw the move.

**Units:** `U5.28` (the observation), `U8.26` (the anchoring measurement, re-confirmed here at `.gitignore:15` by **U8.28**).

---

## (cm) [verified on disk: the handoffs, the shas, the two stability reads, the cache instrument and the ast-dump citations; the units' outcomes remain `reported-only`] Supersessions — which in-flight marks have reported, and which have not

**Superseded (the unit has reported and the evidence is on disk).**
1. **`(ce)`'s in-flight mark on `U6.23`.** `api.py` sha **`4f5698ce…`** is **unchanged** since `U8.26`'s read (same sha, mtime `09:36:17`), `U6.23`'s disambiguating comment is landed at **`:1210–1218`**, and `orchestration/handoffs/U6.23.json` now **exists** (sha `b6865dac66505b09…`, mtime **`09:39:42`**, 16077 bytes). So *"`U6.23` is editing this file live"* is **stale**, and `(ce)`'s `reported-only` mark on the wording correction is **closed in code** by `(ci)`. **Further narrowing:** `U6.23`'s fix is **comment-only** — the conflation was **record-only**, so the code's behaviour never changed, and `(ce)`'s phrasing *"the live wording"* is itself **one step too strong**.
2. **`(cb)`'s mark that `U8.25` was in flight.** `orchestration/handoffs/U8.25.json` now **exists** (sha **`77275f123f6a2326…`**, mtime **`09:42:44`**, 27862 bytes) — **but it is not readable.** `.venv/bin/python -c "import json;json.load(open('orchestration/handoffs/U8.25.json'))"` → **`json.decoder.JSONDecodeError: Expecting ',' delimiter: line 125 column 5 (char 23086)`**, and **two `sha256sum` reads 2 s apart returned identical bytes** (`77275f12…`) — so the mid-write exemption in `tests/test_orchestration_handoffs.py` **would not fire**, and on these bytes that guard **must fail**. **Not run here** (hard bound): that is an **inference from the guard's stated rule plus this measurement**, not a test result. **`U8.25` is therefore NOT credited**, and the item stays **open** — the build's dominant overrun cause, recurring in the artefact it damages. Its file also moved after `U8.26`'s pin: `tests/test_orchestration_handoffs.py` is now sha **`52fbceb74d09e59d…`**, mtime **`2026-10-08 09:37:45`** (vs `U8.26`'s `9a6c7039…` at `09:36:14`, **+91 s**).
3. **`.pytest_cache` "changed under `U8.26`" — settled, and the instrument was the wrong one.** ⚠️ The **top-level directory** mtime is **`09:04:48`**, *earlier* than `U8.26`'s read, which would suggest nothing changed; but a pytest run writes inside `v/cache/` and does **not** touch the parent directory's mtime. The correct recipe is the **newest file under the tree**: `find .pytest_cache -type f -printf '%T+ %p\n' | sort | tail` → **`.pytest_cache/v/cache/nodeids` and `.pytest_cache/v/cache/lastfailed`, both `2026-10-08 09:44:34`**. So a sibling **did** run pytest, at **`09:44:34`** — after `U8.26`'s read and after this unit began. **A directory mtime is not a change witness for a cache; the newest contained file is.**

**NOT superseded — `reported-only`, and deliberately not pre-credited.** The card names **`U5.31`**, **`V8.27`** and **`V6.24`** as still running. Their handoffs exist on disk but are **not credited here**. Observed, for the record, **without crediting**: `U5.31.json` (sha `93120ff606ac0938…`, mtime `09:41:17`) declares **`status done`**, **`tool_calls 17`**, **`bound 16`** — **+1 over its own declared bound**; `V8.27.json` is a **354-byte stub** with `overall PARTIAL`, `blocker: "in progress - stub"`; `V6.24.json` is an **1864-byte stub** with `overall PARTIAL`, `blocker: "in progress"`. **A stub is not a report**, and a `done` claim from a unit the card still lists as running is not a report this unit may credit.

**`(cg)`'s two miscited cards — LOCATED here.** `grep -rn 'ast\.dump\|ast_dump' orchestration/units/` returns **six** cards. Exactly **two** of them record the wrong mandate on a **docstring** edit: **`orchestration/units/U5.28.md:27`** (*"The card prescribes `ast.dump(ast.parse(before)) == ast.dump(ast.parse(after))`. **That proof does not apply here and is FALSE** (measured): a docstring is an AST node (a `str` `Constant`), unlike U5.23's `#:` comment change"*, with the correct proofs at `:30–:32` and the disclosure at `:82`), and **`orchestration/units/U8.24.md:53`** (*"**Raw `ast.dump` equality is FALSE by construction** — a docstring *is* an AST node. Stronger proofs, both TRUE: docstring-blanked AST dumps equal; all 129 code objects identical in `co_code`/`co_names`/`co_varnames`/`co_argcount`/`co_flags`"*). The other **four** hits are **comment-only** changes, where raw `ast.dump` equality is the **correct** method: `U2.12.md:26`, `U5.23.md:36`, `U5.31.md:34`, `U6.23.md:24`. **`(cg)` now has on-disk citations**; only its *cost* stanza (*"a call each"*) remains `U8.24`'s report. **`(cg)` is not edited.**

**Units:** `U8.24`, `U6.23`, `U5.28`, `U8.25` (observed, uncredited); on-disk measurements by **U8.28**.

---

**Section G — scope note, not an entry.** U8.28 found **no further settled** item beyond A–F, and **did not pad the list to reach a letter**. **Explicitly NOT recorded as corrections, because they were not verified on disk here and were not settled by this wave:** `V5.30`'s `02fa18ec`/`1252e07b`/`a1450929` reproductions (taken on report, `(ck)`); `U5.27`'s remaining surgical clauses (the `.r5` deletion, the `HISTORY.md` restore, `verify_docket ok=True`); `U8.25`'s outcome (**its handoff is stable-unparseable and its guard file moved**, `(cm)`); `U5.31`'s, `V8.27`'s and `V6.24`'s outcomes (**stubs or still-running — not credited**); `U6.23`'s `75 passed` run and `U8.24`'s handoff-repair narrative (**no test suite run here**); and any `VERDICTS.md` content (**not read for this append beyond the single `:2135` locus, and not edited**). **Deliberately not pre-credited (in flight, named):** `U5.31`, `V8.27`, `V6.24`.

---

*End of the U8.28 append. Entries **(a)–(cg)** above are unchanged; **6** entries were appended **(ch)–(cm)** plus this scope note, so the ledger holds **91** entries and the next letter is **`cn`**. **The additive proof:** before = sha256 **`7510d72ac42b2e35e073dcee9b4047fb4e09cfe52ae3d7a075cae2876d4cff4d`**, **188761** bytes; the pre-existing prefix is **byte-identical** (`cmp` clean) against the saved copy `state/logs/U8.28.prefix.backup.md`. **The after-state — sha256 and byte count — is deliberately NOT written into this file but recorded in `orchestration/handoffs/U8.28.json` (`sha256_after` / `bytes_after`)**: *a file cannot contain its own final hash*, which is exactly what made `U8.26`'s recorded "after" a mid-append artefact (see `(cj)`). The **6 original `reported-only` markings — (d), (e), (h), (i), (o), (p) — are preserved**, and **0** existing entries were modified; both follow directly from that byte-identical prefix, since an append at EOF cannot alter a byte before it.*

---

# U8.34 append — the retraction, the cannot-fail audit, and four method limits

*Appended by **U8.34** on 2026-10-08 (Occamy probe **`000`**, DOWN; **zero LLM calls, no network, no test suite run**; the real store was **not opened**). Entries **(a)–(cm)** above are **untouched**: the pre-existing **212122**-byte prefix is **byte-identical** (`cmp` clean against `state/logs/U8.34_prefix_backup.md`). **7** entries are appended **(cn)–(ct)**. Every count below carries the command that produced it; every citation of another unit's file carries the **sha or mtime observed here**.*

---

## (cn) [verified on disk: the emitter, both test sites and their pins — **read**, not executed; the refutation is `V5.32`'s] **RETRACTION:** `assess/verdicts.py:404` **is** observable — coverage is **4 of 4**, and the limit is **layer-specific**

**The claim being retracted.** That this emitter is *"unobservable"*, that *"no docket-level assertion can ever observe it"*, and therefore that the typed `/2` standing was *"the only instrument"*. The claim is carried **on disk** by two units and was relayed in the record. Recipe: `grep -rln 'unobservable' orchestration/handoffs/*.json` → **`U5.29.json`** (*"unobservable for 1."*), **`U5.31.json`** (*"unobservable (assess/verdicts.py:404 writes Verdict.rationale, never Claim.verdict_reason)"*), and **`V5.32.json`** (which **refutes** it); the other hits are different loci. Pins: `U5.29.json` sha **`7b9610de3ff9245f…`** mtime `09:36:03`; `U5.31.json` sha **`93120ff606ac0938…`** mtime `09:41:17`; `V5.32.json` sha **`d8edae17ac8336df…`** mtime `09:51:18`.

**What is actually true — 4 of 4, verified by reading here.**
- The emitter: `src/resextract/assess/verdicts.py`:401–406 (sha **`754101b895f30545…`**, mtime **`2026-10-08 07:33:35`**, 39719 B) — `if verdict == "CONFIRMS" and not is_model:` → `verdict = "EXTENDS"` and `rationale = rationale + " [capped at EXTENDS: this run was not model-produced …]"`. So `:404` writes the phrase into **`Verdict.rationale`**.
- `tests/test_assess_verdicts.py:311` — inside `test_a_replay_client_cannot_assert_confirms` (def `:304`, driving `CountingClient(…, verdict="CONFIRMS")  # producer == "replay"` at `:307`): **`assert "capped at EXTENDS" in verdict.rationale`**.
- `tests/test_assess_verdicts.py:651` — inside `test_undeclared_client_is_capped_and_recorded_unknown` (def `:633`): the **same assertion**, after the undeclared-client branch. Pin: sha **`8ded7f81c0fea9a6…`**, mtime `07:32:16`.
- **So the limit is layer-specific, not total.** The phrase is written to `Verdict.rationale` and read by **no** `src/resextract/docket` module (`grep -rn rationale src/resextract/docket` = **0**, as `V5.32` recorded) — **therefore no docket-level assertion can observe it, and that half of the claim is TRUE.** But the **assess** layer drives the branch and asserts the phrase, so **coverage is 4 of 4** (3 docket-level + 1 assess-level), and the typed `/2` standing is a **cleanup** (one shared constant), **not an observability requirement**.

**The evidence's LIMIT — stated, because it is the whole reason this entry grades the claim rather than the code.** `V5.32` **read-verified** `:311`/`:651` and **did not run a differential mutation of `verdicts.py:404`** — its own `unverified` list and `next_unit_hint` say execution was restricted to `tests/test_docket_provenance.py`. This unit **also ran no test suite** (hard bound). So the corrected coverage is **read-verified, not execution-verified**; an execution-grade proof (mutate `:404` against `test_assess_verdicts.py`) is the named follow-up, **not** a claim this entry makes.

**The CAUSE — the generalisable part.** The three units concluded "unobservable" from **`grep -rn rationale src/resextract/docket` = 0** — a search **scoped to the package where the answer was expected**. A statement true **of the docket layer** was silently promoted to a statement about **all layers**. **That is the same failure shape as two entries already in this ledger:**
- **`(cb)` — the copy==copy baseline check:** the guard compared **two derived artifacts** (`copy == copy`) instead of `copy == measurement`; two copies of a wrong value agree perfectly, so a check scoped to the pair **was read as if it covered the corpus**.
- **`(cf)`/`(cl)` — the gitignored `dockets/` containment claim:** `git status --porcelain -- dockets` returning 0 lines over the **ignored root** tree was read as containment, when porcelain is silent **for the root tree only** — a check scoped to one frame read as if it covered the whole.

All three: **a scope-limited instrument reported a clean result inside its own frame, and the frame was forgotten.** **Units:** `U5.29`/`U5.31` (the claim, on disk), `V5.32` (the refutation); re-verified here.

---

## (co) [verified on disk: the tautology, its line, the demonstration shas and the 4 bare broad raises; the sweep's completeness and the gate measurements are `U8.30`'s, `reported-only`] The cannot-fail audit — verdict **LOCAL**, and the systemic weakness is a **different class**

**The audit (`U8.30`, `status done`).** Pin: `orchestration/handoffs/U8.30.json` sha **`e5d36af511b43c3d…`**, mtime **`2026-10-08 09:51:08`**, 14692 B, `bound 18`, `tool_calls_work 17 / tool_calls_total 18`. It swept **all 56 `.py` files under `tests/`** — *"43 test modules, `tests/conftest.py`, 12 fixture modules"* — by **AST parse plus suite-wide regex**, **738 `def test_` functions counted statically**, 14 read at body level; its own recipe is `AST+regex sweep of all 56 tests/**/*.py`. **Recipe cross-check here:** `find tests -name '*.py' | wc -l` → **56** (matches); `grep -rh 'def test_' tests --include='*.py' | wc -l` → **770** — a **different recipe** (textual, not AST), so **770 and 738 are not comparable**. **Verdict: LOCAL** — *"a rare, localized defect, not a suite-wide pattern."*

**1 confirmed cannot-fail, demonstrated (not argued), at `tests/test_docket_reassembly.py:360–362`** — read here verbatim:
```
assert _block(read_manifest(dock / "MANIFEST.json")) == _block(
    read_manifest(dock / "MANIFEST.json")
)
```
**The same file is read twice.** `U8.30` imported the real test module and the real `read_manifest` and evaluated the predicate **as written** on a known-good manifest **and on a schema-valid lie**: **`True` for both**; the value-vs-measurement form returned `True`/`False`. **Perturbations verified on disk here:** `state/verify/U8.30/m_lie.json` sha **`1089ddc188015480…`**, 3557 B; `state/verify/U8.30/m_good.json` sha **`41ec711a4324eb98…`**, 4188 B — and that sha **is the frozen `_smoke` `MANIFEST.json` sha** (`41ec711a4324eb98…`), so the "good" comparandum is the **real frozen artifact**, not a synthetic one. **The repair is owned by `U8.32` — `reported-only`, and it has NOT landed:** `tests/test_docket_reassembly.py` is sha **`492872341ea37a8e…`**, mtime **`2026-10-08 08:19:31`** — the **same pin `U8.20` took**, i.e. unchanged through this wave.

**20 measured false positives — excluded, not assumed** (`false_positive_count: 20`): **6 always-skip candidates all measured OPEN** (one disproved by a **UDP route probe** — `socket(AF_INET,SOCK_DGRAM).connect(('192.168.2.1',9))` → `192.168.2.187`, non-loopback, so the skip never fires), **6 assert-free tests that delegate to assertion-bearing helpers**, and **8 `except-pass` sites of which 3 are the correct `else: raise AssertionError` idiom**. **1 unverified, deliberately left unaccused:** `tests/test_kg_graphify_flags.py:548`.

**THE REFRAMING — the actionable half.** **75 of 93 `pytest.raises` blocks carry neither `match=` nor any assertion on the caught exception** (**23** of them in assert-free tests). These **CAN fail** (absence, or the wrong type) — so they are **NOT the cannot-fail class**; they are **blind only to *which* diagnostic fired**. `U8.30`'s own judgement, quoted: *"the highest-value and lowest-risk target is the SYSTEMIC type-only class, not the single cannot-fail."* Worst sites, **verified here** by `grep -rn 'pytest.raises(Exception)' tests --include='*.py'` → exactly four, all bare: **`tests/test_docket_assemble.py:518`**, **`tests/test_docket_provenance.py:378`**, **`:651`**, **`:885`** — `pytest.raises(Exception)` with no `match=` accepts **any** exception as the right answer. **Recipe/limit:** my own grep counts **109** textual `pytest.raises` lines (**108** without `match=`), while **93 blocks / 75 type-only** is `U8.30`'s **AST** count after refinement (its scanner's own 18 false positives are disclosed in its handoff). Cite the AST recipe for 75/93.

**`fails-spuriously`: 0 confirmed — and it is a DIFFERENT class from cannot-fail.** Cannot-fail = the assertion **cannot observe** a perturbation. Fails-spuriously = the test **fails for a reason unrelated** to what it names. `U8.30` found **no `comm` use at all in the suite (0)** and **no set-vs-list comparison**. The distinction is not academic: an **unsorted `comm` produced a spurious "58 deleted"** earlier in this wave (`(cj)`).

**`reported-only`:** the 6 gate measurements, the 14 body-level reads and the demonstration harness are `U8.30`'s report (this unit ran no test file). **Verified here:** the tautology's file and line, the four bare `pytest.raises(Exception)` sites, the 56-file count, and the two demonstration shas. **Unit:** `U8.30`.

---

## (cp) [re-measured here; the rule is `U8.28`'s, already noted at `(cj)` — cross-reference, not a duplicate] The self-reference limit: **a file cannot contain its own final hash**, and a mid-append hash is detectable by prefix

**The rule.** A hash quoted **for a file** must **postdate that file's final write**. A hash taken **mid-append** is **reproducible by prefix**, and that is exactly how a reader can **detect** one: if `head -c <quoted_bytes> <file>` reproduces the quoted sha on a file that is now **larger**, the quoted hash was **mid-append**.

**Measured here (re-measured, not taken on report).** Recipe: `head -c 186957 docs/PLAN_CORRECTIONS.md | sha256sum` → **`a6a0feaf06430d30…`** — exactly the "after" sha `U8.26` recorded at `(cg)` — while the same file stood at **188761** bytes (`wc -c`). So `U8.26`'s recorded "after" state was taken **1804 bytes before it finished writing**. `U8.28` fixed this **for its own generation**: it wrote the after-state **only** into `orchestration/handoffs/U8.28.json` (`sha256_after`/`bytes_after`), which is the practice this append follows.

**Cross-reference.** `(cj)` already records this as its "fourth data point"; what this entry adds is the **detection recipe** (`head -c` prefix reproduction) and an independent re-measurement. **`(cj)` is not edited.** **Unit:** `U8.28`; re-measured by **U8.34**.

---

## (cq) [verified on disk: the guard's rule text, the repaired handoff and its window; the original stable-unparseable read is `(cm)`'s] The guard's mid-write heuristic is a **second-scale** test — a stable red can be transient at minute scale

**The rule as implemented** (read verbatim, `tests/test_orchestration_handoffs.py`:19–22; sha **`52fbceb74d09e59d…`**, mtime **`2026-10-08 09:37:45`**): *"1. read the file's bytes and try `json.loads`; 2. on failure, re-read **immediately**: if the bytes **DIFFER** from the first read the file is mid-write → 'skip' (recorded as `mid_write`, not a failure); 3. if the bytes are **IDENTICAL** and still unparseable, the defect is stable and [the guard fails]."* Implementation: `first = path.read_bytes()` (`:176`) / `second = path.read_bytes()` (`:180`) → `mid_write.append(path.name)` (`:182`). **The window between the two reads is therefore seconds, by construction.**

**Measured here.** `orchestration/handoffs/U8.25.json` was **stable-unparseable** earlier this wave (`77275f12…` @ `09:42:44`, byte-identical across reads 2 s apart, `JSONDecodeError` line 125 — `(cm)`'s measurement, **not** re-taken here), and has since been **rewritten**: current sha **`cf5167e488873858…`**, mtime **`2026-10-08 09:44:26`**, 28254 B, and `json.load` → **OK**. So the file was stable-unparseable for **~102 s** and then repaired. On the guard's rule those two immediate reads **would have called it stable and failed** — correctly by its own definition, and **wrongly** as a report of a defect that did not survive the minute. `U8.28.json` likewise: a verifier reported it as a **stable red**, and it was **transient**.

**The rule to record.** Second-scale re-reads distinguish *actively writing* from *settled* at **second** scale, **not minute** scale; **a verifier should re-read after a delay before declaring a stable red**, and should state the interval it used. **`reported-only`:** the start of the window (`77275f12…` @ `09:42:44`) is `(cm)`'s read; this unit measured only the **repaired end state**. **Sources:** `V8.27`'s report, `U8.28`'s drift measurement; repair re-measured by **U8.34**.

---

## (cr) [verified on disk: the tally's loci, the nested `tool_calls` path, and a citation that does not resolve; the costs themselves are `U8.28`'s, `reported-only`] Contract and records: five self-repairs, the stated mitigations, and a card citation that does not resolve

**The self-repair pattern — five instances.** `orchestration/handoffs/U8.28.json` (`wave_ranking`, quoted verbatim): *"this is the 4th self-inflicted handoff repair in this wave (**U8.24 +12 calls, U6.23 +3, U8.25 +11, U8.28 +4**). **V8.27** additionally reports reproducing the same mode in miniature at **+4 calls**."* → **costs `+12, +3, +11, +4, +4`.** Independently corroborated on disk: **`V8.27.json`:386** records its own +4 verbatim (*"the mandated write-validate-repair loop on this unit's own handoff cost +4 calls"*). **A sixth, measured here:** `orchestration/handoffs/V5.32.json` carries **`"tool_calls": 25`** against **`"bound": 22`** (`overage: 3`) with `overage_reason` naming *"three calls spent repairing and re-validating a structural JSON defect in my own handoff write"*. Pin: `V5.32.json` sha `d8edae17ac8336df…`, mtime `09:51:18`. **`reported-only` for the four non-`V8.27` costs** — `U8.28` labels its own tally *"parent-relayed and partially verified"*.

**The stated mitigations** (restated because they are the contract's answer): **(1)** validate the handoff JSON **immediately** after writing it and after **every** later edit; **(2)** cards state the contracted **nesting** explicitly — the verdict keys live **inside `evidence`**. Measured here: `U8.24.json` carries `tool_calls` at **`.evidence.tool_calls`** (= `33`), with **no top-level `tool_calls` key** (recipe: walk the object — `33 AT .evidence.tool_calls`); **(3)** bounds are stated as **WORK CALLS, with the mandated report-back excluded**.

**RECORDS FINDING — a `cm`-generation citation does not resolve (verified here).** `(cj)` states: *"`U8.24.md:3` declares **`Bound: 18 tool calls (used 26 — overage disclosed in the handoff)`**"*. Read directly, **`orchestration/units/U8.24.md:3` is**: *"**Status:** done. **Probe:** http 000 (Occamy DOWN, expected). **Zero LLM calls, no network, no graph build.**"* Recipes: `read` of `U8.24.md:1–10`; `grep -n 'Bound' orchestration/units/U8.24.md` → **0 matches**; `grep -n 'overage\|tool.call\|tool_calls\|Bound' orchestration/units/U8.24.md` → **0 matches**; `grep -n '26' …` → only **`:54`**. Pin: sha **`3e614e5f3e4c7097…`** (full `3e614e5f3e4c709701063df2f9a5773db77df81639d87c9b890ecf381112286d`), mtime **`2026-10-08 09:35:35`**, 5353 B — **earlier than `(cj)`'s own write**, so the file has not changed since that measurement. **The quoted text is not at that line and not anywhere in the card.** The **`33` half is real** (`U8.24.json` `.evidence.tool_calls = 33`). So the recorded "**33 vs 26 — a 7-call gap**" rests on a **mis-cited document**: what is verified is **33 (nested in the handoff)** versus **absent from the card**. **`(cj)` is not edited** — this is the superseding entry, in a **new** entry per the append-only rule. **Generalisable: a quoted line is not evidence until it is re-read at a stated sha — the recipe rule applies to card citations too.**

**The tooling-artefact rule.** An **unsorted `comm`** produced a spurious **"58 deleted"** (`U6.23`), and a **tuple-vs-JSON-list** compare produced a spurious code-object mismatch. **Sort inputs; re-run before believing a surprising number.** Positive example on disk: `V5.32` sorted `LC_ALL=C` on **both** sides and **discarded** its first failed diff rather than publishing it. (First recorded at `(cj)`; restated here with the `V5.32` instance.) **Units:** `U8.24`, `U6.23`, `U8.28`, `V5.32`.

---

## (cs) [verified on disk by grep here; already located by `(cm)` — recorded, and `(cg)` is NOT edited] The `(cg)` citations, located

`(cg)` left the two miscited cards `reported-only`. Recipe: `grep -rn 'ast\.dump|ast_dump' orchestration/units/` → **10 matches across 7 cards**. The two citations are **`orchestration/units/U5.28.md:27`** (*"The card prescribes `ast.dump(ast.parse(before)) == ast.dump(ast.parse(after))`… That proof does not apply here and is FALSE (measured)…"*) and **`orchestration/units/U8.24.md:53`** (*"**Raw `ast.dump` equality is FALSE by construction** — a docstring *is* an AST node…"*). The **other four** `ast.dump` hits are **comment-only** changes, where the method **is correct**: **`orchestration/units/U2.12.md:26`**, **`U5.23.md:36`**, **`U5.31.md:34`**, **`U6.23.md:24`**. **`(cm)` recorded these six first**; they are **re-verified here from the same grep**, and **`(cg)` is not edited**. **`reported-only`:** the *"cost a unit a call each"* clause remains `U8.24`'s report.

---

## (ct) [verified on disk: every pin and mtime below, re-taken in this unit] Supersessions — what is settled now, and what is running (**nothing running is credited**)

**Settled — the `cm`-generation `reported-only` marks are superseded by adding this entry (`(cm)` is not edited).**
- **`V5.32`** — sha **`d8edae17ac8336df…`**, mtime **`2026-10-08 09:51:18`**, 23000 B, `status partial` / `overall PARTIAL`. It carries **Section A's retraction** (`corrections[0]`; three `overstated` items). **Section A is the credit: PARTIAL, with the retraction recorded.**
- **`U8.30`** — sha **`e5d36af511b43c3d…`**, mtime **`09:51:08`**, 14692 B, `status done`, `bound 18`, `17 work / 18 total`. **Section B is the credit.**
- **`U8.28`** — sha **`e768e9a1be55aea2…`**, mtime **`09:51:37`**, 16313 B, `status done`. **Section C is the credit.**
- **`U5.29`** — sha **`7b9610de3ff9245f…`**, mtime **`09:36:03`**, 14228 B, `status done`, `tool_calls 18 / bound 18`.

**RUNNING — marked `reported-only`; observed, not credited; this append pre-credits no running unit.**
- **`V8.29`** — sha `33cdfb59b3729901…`, mtime **`09:52:38`**, 22877 B, `overall PASS` (8 checks). A full-looking PASS **from a unit the card still lists as running**: **not credited**.
- **`U8.31`** — sha `7efacf42841eef22…`, mtime `09:50:29`, 1557 B, `status partial` — and its status field **changed between two of my reads** (a mid-write signal on the very file that guards handoffs). **Not credited.**
- **`U5.33`** — sha `3175990665f4c902…`, mtime `09:52:37`, **364 B**, `status partial`, `blocker: "in progress"`.
- **`U8.32`** — sha `ad2450ba0358cf6e…`, mtime **`09:54:09`**, **208 B**, `status partial`. **It owns the `tests/test_docket_reassembly.py:360` repair and has not landed it** (see `(co)`).

**Re-pinned here — `U8.28`'s hint asked for exactly these, and all four moved during its run.**
- **`U8.25.json`** = sha **`cf5167e488873858…`**, mtime **`2026-10-08 09:44:26`**, 28254 B, **parses** (was `77275f12…` @ `09:42:44`, unparseable — `(cq)`).
- **`U5.31.json`** = sha **`93120ff606ac0938…`**, mtime **`09:41:17`**, 8971 B, `status done`, **`tool_calls 17 / bound 16`** — **+1 over its own declared bound**.
- **`V8.27.json`** = sha **`318e2c533953b4a1…`**, mtime **`09:49:09`**, **22778 B**, `overall PASS` (8 checks) — a **354-byte stub** when `(cm)` read it; it **has since reported**.
- **`V6.24.json`** = sha **`189d1c3ea4b7876e…`**, mtime **`09:45:38`**, **17102 B**, `overall PARTIAL` (8 checks) — an **1864-byte stub** when `(cm)` read it.
- Also re-pinned: `tests/test_orchestration_handoffs.py` sha **`52fbceb74d09e59d…`**, mtime **`09:37:45`** — **unchanged** from `(cm)`'s observation.

**The mtime ambiguity the card named — measured.** The replay docket's **`MANIFEST.json`** mtime is **`2026-10-08 09:28:51.302382844`** while its **directory** mtime is **`09:28:51.303536743`** — the two differ by **~1.1 ms**, so "the mtime of the replay docket" is ambiguous unless the **file** is named (recipe: `stat -c '%n mtime=%y' <file> <dir>`). Per-file shas (the path-sensitivity rule, `(ck)`): replay `MANIFEST.json` **`ce45766d4ac845ed…`**, `_smoke` **`41ec711a4324eb98…`**, `u55-pinned` **`445032f78851b817…`**. **No byte-identity is asserted for replay.**

---

**Section H — scope note, not an entry.** No further **settled** item was found beyond A–G, and the list was **not padded to reach a letter**. **Explicitly NOT recorded:** `V8.29`'s PASS content (running); `U8.32`'s fix (not landed); `U5.33`'s outcome (running); the full history of `U8.24.json`'s `.evidence.tool_calls` path (only its **current** path was pinned); and the **start** of `U8.25.json`'s stable-unparseable window (that read is `(cm)`'s; only the repaired end state was measured here).

---

*End of the U8.34 append. Entries **(a)–(cm)** above are unchanged; **7** entries were appended **(cn)–(ct)** plus this scope note, so the ledger holds **98** entries and the next letter is **`cu`**. **The additive proof:** before = sha256 **`b7559f62415edf65…`** (full `b7559f62415edf65283fdbd7ac67ba6f5abc9b7fbed21372da0d6620538b380b`), **212122** bytes; the pre-existing **212122**-byte prefix is **byte-identical** (`cmp` clean) against the saved copy `state/logs/U8.34_prefix_backup.md`. **The after-state — sha256 and byte count — is deliberately NOT written into this file but recorded in `orchestration/handoffs/U8.34.json` (`sha256_after` / `bytes_after`)**: *a file cannot contain its own final hash* (`(cp)`). The **6 original `reported-only` markings — (d), (e), (h), (i), (o), (p) — are preserved**, and **0** existing entries were modified; both follow from the byte-identical prefix, since an append at EOF cannot alter a byte before it. **U8.34 made zero LLM calls, ran no test suite and started nothing; the Occamy probe returned `000`.***

---

# U8.40 append — the landed repair, the count reconciliation, and the zeros

*Appended by **U8.40** on 2026-10-08 (Occamy probe **`000`**, DOWN — `curl -sS -m 5 -o /dev/null -w '%{http_code}\n' http://192.168.2.168:8012/v1/models` → `curl: (7) … port 8012: Could not connect to server` / `000`, probed once; **zero LLM calls, no network, no test suite run**; the real store was **not opened**, no `immutable=1` anywhere). Entries **(a)–(ct)** above are **untouched**: the pre-existing **234785**-byte prefix is **byte-identical** (`cmp` clean) against the saved copy `state/logs/U8.40_prefix_backup.md`. **7** entries are appended **(cu)–(da)** plus Section H. Every count below carries the exact command; every citation of another unit's file carries the **sha/mtime observed here**.*

---

## (cu) [verified on disk: the file, its sha, the repaired assertion read verbatim, and the demonstration artifacts; the demo was **not re-run** here] `U8.32`'s repair **HAS LANDED** — supersedes `(co)`'s "NOT landed"

**What `(co)` recorded, correctly at its read time.** That the cannot-fail assertion at `tests/test_docket_reassembly.py:360–362` was **owned by `U8.32` and had NOT landed**, with the file pinned at sha **`492872341ea37a8e…`**, mtime **`2026-10-08 08:19:31`** (the same pin `U8.20` took). **`(co)` is not edited** — this is the superseding entry, in a **new** entry per the append-only rule.

**What is actually true now — the repair landed.**
- Current sha256 of `tests/test_docket_reassembly.py` (recipe: `sha256sum tests/test_docket_reassembly.py`): **`dc09ea00be921ef1c17625479d9a6c7d85893a0f199ed9690d2b56d00b7b2966`** — the sha the card reported. Size/mtime (recipe: `stat -c '%n %s %y' …`): **70240 B**, mtime **`2026-10-08 09:56:08.324263170 -0500`**. So the file moved from `492872341ea3…`/`08:19:31` to `dc09ea00be92…`/`09:56:08`.
- **The tautology is gone, replaced by a pre-state capture.** Recipe: `grep -n '_block(read_manifest(dock / "MANIFEST.json")) == _block(' tests/test_docket_reassembly.py` → **one** hit, at **:364**, right-hand side `_block(before)` — the old doubled `_block(read_manifest(…)) == _block(read_manifest(…))` form matches **nothing**. `before` is captured **before** the re-assembly, not after: recipe `grep -n 'before = read_manifest' tests/test_docket_reassembly.py` → **:269, :343, :509** — inside this test it is **:343**.
- **The repaired assertion, quoted verbatim with real line numbers** (recipe: `awk 'NR>=360 && NR<=370 {printf "%d: %s\n", NR, $0}' tests/test_docket_reassembly.py`):

```
362:     # the WHOLE material block equals the pinned pre-image, not just the one row
363:     # we happened to look at: a measurement vs an independent value => it can fail
364:     assert _block(read_manifest(dock / "MANIFEST.json")) == _block(before), (
365:         "the repaired manifest's material block differs from the pinned pre-image"
366:     )
```

  Left side is a **measurement taken now**; right side is an **independent pre-image captured at :343** — the two are no longer the same read, so the assertion **can** fail. That is exactly the shape `(co)` required.

**`U8.32`'s demonstration — cited, not re-run here.** I ran **no test suite and no demo** (hard bound), so the *execution* is `U8.32`'s; what I verified here is that the **artifacts exist on disk** with these bytes (recipe: `sha256sum state/verify/U8.32/*`):
- `state/verify/U8.32/demo_predicate.py` sha **`3bfbcec720015a43…`** (1637 B); `demo_output.txt` sha **`67f2d9df5ab5a651…`** (505 B). Its output, read verbatim: **`OLD   form (:360 as written)  good=True  lie=True`** / **`FIXED form (vs pre-image)     good=True  lie=False`** / `DEMO_OK: old=True/True (cannot fail); fixed=True/False (can)` — i.e. the reported **`OLD good=True lie=True` / `FIXED good=True lie=False`**. The comparison target is the frozen **`_smoke`** pre-image: `PRE=_smoke 41ec711a4324eb9893b6f031c10a647f21e1cb3521ca73a8e8eb168522b283c6`, and `GOOD byte-identical to PRE (_smoke): True`.
- **The injected-downgrade pair — and one half is NOT on disk here.** The **new form** half is backed by a file: `state/verify/U8.32/red_fixed_output.txt` sha **`aacc8912df201db2…`**, ending **`1 failed, 69 deselected in 0.13s`** (its `FAILED …::test_would_be_downgrade_is_recorded_not_silent`). The **old form** half (`1 passed, 69 deselected`) is **`reported-only` — `U8.32`'s own handoff**, not an output file: the directory listing (recipe: `ls state/verify/U8.32/`) contains exactly **six** entries — `conftest.py`, `demo_output.txt`, `demo_predicate.py`, `red_fixed_output.txt`, `test_red_fixed_form_downgrade.py`, `test_red_old_form_downgrade.py` — and **no `red_old_form_output.txt`**. The old-form **test module** exists (`test_red_old_form_downgrade.py` sha `1cf4758141e0906b…`), and `U8.32.json` carries the command and the result string *(`-q -k would_be_downgrade -> 1 passed, 69 deselected (old form cannot fail)`)*; **the "1 passed" is therefore a report, the "1 failed" is an on-disk artifact.** Marked accordingly — a summary was not trusted in place of an artifact.
- **The counts it reported are `reported-only`:** **70 passed / 70 collected / 39 `def test_` / 0 deleted**. I did not run that suite, and a `grep -c 'def test_'` is a **different recipe** from pytest's collected count, so I record them as `U8.32`'s report without endorsing the number.

**Pin observed here:** `orchestration/handoffs/U8.32.json` sha **`76fe09fcabcaaf1e…`**, mtime **`2026-10-08 09:58:06.748822973 -0500`**, 11171 B, `status done` (was a 208-byte `partial` stub at `(ct)`'s read). **Unit:** `U8.32` (repair); superseded reading by **U8.40**; the "not landed" text remains at `(co)`.

---

## (cv) [verified on disk: the alias-taint sites, the current AST corpus count, the sibling zeros and every pin; the 102/68/93/75 stream counts are `U8.30`'s and `U8.36`'s AST sweeps] **THE COUNT RECONCILIATION: `U8.30`'s `75` was a conservative OVERCOUNT — the corrected figure is `68`**

**The number the record currently quotes** (`(co)`, from `U8.30`): *"**75 of 93 `pytest.raises` blocks carry neither `match=` nor any assertion on the caught exception**"* (**23** of them in assert-free tests). `U8.36` re-measured with a **refined detector** and got **`102` sites / `68` blind (69 before its one fix) / `23` in assert-free tests**. **This is not one audit being wrong — it is two deltas, both measured, and the third figure agreeing exactly.**

**Delta 1 — the corpus grew: `738 → 770` test functions.** `U8.30`'s `738` is its **AST** count; `U8.36`'s `770` is also an AST count. **Measured here** (recipe: `.venv/bin/python` walking `ast.parse` over `pathlib.Path('tests').rglob('*.py')`, counting `FunctionDef`/`AsyncFunctionDef` whose name starts with `test_`; printed `AST def test_ functions: 770 files: 56`) → **`770`** in **56** files. So on the **same recipe** the corpus is **738 (U8.30, reported) → 770 (measured here)**, **+32** functions, against **+9** `pytest.raises` sites (93→102). **I can measure only the current figure**; the `738` end is `U8.30`'s read and is recorded as such. **Recipe drift, disclosed:** the *textual* recipe `grep -rh 'def test_' tests --include='*.py' | wc -l` gives **`773`** here, where `(co)` recorded **`770`** by that same textual recipe — so the textual figure **drifted +3 during this wave**, and `738` vs `770` must never be compared across recipes (which is exactly what `(co)` warned).

**Delta 2 — the detector was refined: one level of alias-taint propagation.** `U8.36`'s detector treats the common form `message = str(excinfo.value); assert … in message` as **asserting on the caught exception**; `U8.30`'s coarser detector counted those **blind**. **10 such sites.** **Verified verbatim here** (recipe: `awk 'NR>=…' tests/test_docket_assemble.py`; file sha **`8b2a8685aab3b4d6…`** — full `8b2a8685aab3b4d6eea613545c18a9564e94449cdce211de73fe727eb772e3d7`, 25988 B, mtime `2026-10-08 10:01:00.943117388 -0500`):
```
282:     with pytest.raises(AssemblyRefused) as excinfo:
284:     message = str(excinfo.value)
285:     assert "C1" in message
331:     with pytest.raises(AssemblyRefused) as excinfo:
333:     message = str(excinfo.value)
334:     assert "sha256 mismatch" in message
349:     with pytest.raises(AssemblyRefused) as excinfo:
351:     message = str(excinfo.value)
352:     assert "§3.6 guard" in message
```
All three are `pytest.raises(AssemblyRefused)` — a **typed** refusal — *plus* an assertion on its message, so they are **not blind**; `U8.30`'s detector scored them blind.

**The control that proves the reconciliation is real and not a fudge: the assert-free figure agrees EXACTLY.** `U8.30` = **23**; `U8.36` = **23** (`blind_in_assert_free_tests`). Both audits, two detectors, two read times, **the same 23**. A detector artefact would not reproduce on an independent sub-population; a genuine refinement does.

**So, plainly: the corrected figure is `68`, and `U8.30`'s `75` was a conservative OVERCOUNT** — each of the 10 alias-taint sites was counted blind. `(co)`'s reframing sentence ("75 of 93 …") is **superseded by this entry and is not edited**; read it as **68 of 102**, with the 93→102 and 75→68 deltas explained above. `U8.30`'s other conclusion is unaffected: these sites **CAN** fail (absence / wrong type), so they are **not** the cannot-fail class.

**`U8.36`'s buckets (quoted from its `triage`, sha `338eb0084453c528…`):** total **102** sites → **fixable-by-narrowing-type `3`**; **needs-`match=` `59`** ("a builtin exception has no narrower class to name, or the same project refusal class fires at ≥2 sites in one file"); **keep-broad-with-reason `40`**, of which **`34` already assert on the caught exception** and **`6` are the sole site of a project-specific refusal class, where the type **is** the diagnostic". (Its own scalar field `already_asserts_on_caught_exception` reads **33**; the **34** is the figure in its `summary` and is the post-fix count implied by `102 − blind_total_after_fix 68` — the +1 being the one site it narrowed. Recorded, not harmonised.) Its summary verbatim: *"3 fixable by NARROWING THE TYPE (all 3 are U5.33's `pytest.raises(Exception)` sites; mine was the 4th and is fixed); 59 need `match=`: … 40 keep broad with a reason…"*

**Its quotable preference rule** (`preference_rule` field): *"narrow the exception type > match= > leave broad with a reason"* — expanded in its report as: **"Narrow the exception type first — an exception class is a stable contract and a message is not; use the shortest stable `match=` substring only when the class alone cannot discriminate, and leave the assertion broad with a stated reason when the code may legitimately raise several types."**

**Recipes/limits:** `93`/`75` is `U8.30`'s **AST** sweep (its 18 false positives disclosed in its handoff); `102`/`68`/`69`/`23` is `U8.36`'s **AST** sweep over the **41 `tests/test_*.py`** files (`counts_method`: per-file AST `ast.Assert` count + AST test-function count + `pytest --collect-only -q`, `LC_ALL=C sort` + `comm -3`, before-state reconstructed by reverse-applying the single edit into `state/verify/U8.36/before_recon.py`). My own independent `grep -rh 'pytest\.raises' tests --include='*.py' | wc -l` is a **textual** recipe and is **not** comparable to either AST figure. **I ran no suite; the 102/68/93/75 counts themselves are the two units' scans** — verified here only at the level of the alias-taint sites, the corpus count, and the sibling zeros. **Units:** `U8.30` (93/75), `U8.36` (102/68); reconciled by **U8.40**.

---

## (cw) [verified on disk: the landed edit and its sha, the contract line, the current line number and the sibling zeros; the mutant/control executions are `U8.36`'s] `U8.36`'s ONE FIX — and the "passes for the wrong reason" finding, now **PROVED**

**The fix landed, and the record's line number has drifted.** `U8.36`'s `files_changed`: `tests/test_docket_assemble.py` sha_before **`85f7b4d5fd0f6a2e…`** → sha_after **`8b2a8685aab3b4d6…`**; **27 → 27** test functions, **79 → 79** asserts, **0 deleted** (`LC_ALL=C sort` + `comm -3` over the test names and the assert lines: 0 diff both sides). **Re-measured here:** sha **`8b2a8685aab3b4d6eea613545c18a9564e94449cdce211de73fe727eb772e3d7`**, 25988 B, mtime **`2026-10-08 10:01:00.943117388 -0500`** — the `sha_after` is current. **The site the record cites as `:518` is now `:520`** (the edit inserted `from pydantic import ValidationError` + a blank line). Recipe: `awk 'NR>=512 && NR<=524 {printf "%d: %s\n", NR, $0}' tests/test_docket_assemble.py`:
```
515: def test_manifest_forbids_unknown_fields():
516:     from pydantic import ValidationError
517: 
518:     from resextract.docket.manifest import DocketManifest
519: 
520:     with pytest.raises(ValidationError):
```
**Any future citation of this site must use `:520`, and the same `:518` is simultaneously the line of an unrelated import** — a line number is a moving target unless a sha is named. **The class it narrows to, read here** (`src/resextract/docket/manifest.py`, sha **`0826f398add9f1c9…`**, 24747 B, mtime `09:14:48.643560206 -0500`): `:301 class DocketManifest(_Forbid):` / `:302 model_config = ConfigDict(extra="forbid", populate_by_name=True)` — `ValidationError` is the class the contract raises.

**The wrong-reason pass, PROVED — by a mutation that preserved the refusal and changed only the TYPE.** `U8.36` copied the tree, made the copy's `manifest.py:309` raise `RuntimeError("U8.36-MUTANT refused unknown field with the WRONG exception type")` from the **same refusal path**, asserted the copy was imported (`import_identity`), and ran:
- **old broad form (`pytest.raises(Exception)`) vs the mutant → `1 passed`** — a pass for the **wrong reason**, **demonstrated**, not argued;
- **narrow form (`pytest.raises(ValidationError)`) vs the mutant → `1 failed`**, failure verbatim:

```
>           DocketManifest.model_validate(
>           raise RuntimeError("U8.36-MUTANT refused unknown field with the WRONG exception type")
E           RuntimeError: U8.36-MUTANT refused unknown field with the WRONG exception type
state/verify/U8.36/copyroot/resextract/docket/manifest.py:309: RuntimeError
1 failed in 0.06s
```
- **control:** narrow form vs a **pristine** copy → **`1 passed`**, so the red came from the mutation and not from the copy mechanism.

**Marks:** the mutant runs and the control are **`U8.36`'s execution — `reported-only` here** (`red_green`, `control`, `import_identity` in `U8.36.json`); **I ran no test suite.** What I verified here: the landed sha, the `:520` narrow form, the `manifest.py:301–302` contract, and the sibling zeros.

**The structural class at the remaining sites — and the LIMIT.** `U8.36` did **not** individually mutate the rest; that is its stated limit and it is recorded as such:
- **3 remaining `pytest.raises(Exception)` sites** — `tests/test_docket_provenance.py:378/651/885` — "same class, NOT independently demonstrated by me (sibling-owned, read-only to this unit)"; the same `RuntimeError` mutant argument applies but was **not run** against those files. Verified here by `grep -n 'pytest.raises(Exception)' tests/test_docket_provenance.py` → exactly those three (the file's 4th `pytest.raises`, at `:239`, is typed `MAT.PromotionRefused`).
- **12 builtin-broad sites** (`passes_for_wrong_reason[2]`, `kind: structural`), quoted verbatim: *"sqlite3.IntegrityError/ValueError/OSError/OperationalError/KeyError sites cannot distinguish a foreign TypeError from the intended refusal; **not individually mutated here**"* — lines `[518, 524, 530, 537, 88, 101, 114, 127, 516, 522, 528, 534]` (the entry is a **class**, so those line numbers are not attributed to one file). **So: one site proved; three sites structurally identical but untested; twelve sites structural and untested.** **Unit:** `U8.36`; line-drift and contract read re-verified by **U8.40**.

---

## (cx) [verified on disk here: both zeros, all four sibling pins, and the line numbers] The sibling-owned sites — and the **two measured ZEROS**

**The zeros (`U8.36`'s measurement, re-measured here).** Recipe: `grep -c 'pytest\.raises' <file>` →
- **`tests/test_docket_reassembly.py` (`U8.32`'s file) → `0`**; sha **`dc09ea00be921ef1…`**, 70240 B, mtime **`2026-10-08 09:56:08.324263170 -0500`**.
- **`tests/test_orchestration_handoffs.py` (`U8.35`'s file) → `0`**; sha **`7d9c97ee95014c74…`** (full `7d9c97ee95014c74845ed3a5af20d652dc849dbf73d7d81edebf33933ed3d70e`), 32483 B, mtime **`2026-10-08 10:00:29.105697994 -0500`**.

Both are corroborated independently by `U8.36`'s AST sweep (`raises_sites: []` for both files) against the **same two shas** — so **no drift between `U8.36`'s read and mine** on either file. Note `U8.35`'s file **did** move since `(ct)` pinned it (`52fbceb74d09e59d…` @ `09:37:45` → `7d9c97ee95014c74…` @ `10:00:29`): **a zero is only a zero at a named sha.** A zero is evidence — these two sibling files contribute **no** blind sites, so the 102 is not diluted by them.

**The owed sites (`reported-only`).**
- **`tests/test_docket_provenance.py:378/651/885` — `pytest.raises(Exception)`, owner: `U5.33`'s file.** **Re-taken here** (the card warns `V5.37` was verifying that file while this was written): sha **`8eb9a623a01f2737…`** (full `8eb9a623a01f2737669b8d7f33eeefde5a9b8adbf3fafd1add89db467bfb626e`), 56937 B, mtime **`2026-10-08 09:55:12.356526002 -0500`**. That mtime is **identical** to the `mtime_ns 1791471312356526002` `U8.36` recorded — **the file did not drift between its read and mine**, so its lines `378/651/885` still hold. `V5.37`'s own handoff at this moment is sha **`84f36a854cb31822…`**, 1799 B, mtime `09:59:15`, `overall PARTIAL` — **observed, nothing credited** (it is running).
- **`tests/test_run.py:624`** — a blind `pytest.raises(ValueError)` with **no** `match=` and no assertion on the caught exception, in `test_stage_result_rejects_an_invented_status` (the preceding site `:618` **does** assert `"unknown stage" in str(excinfo.value)`). **Low priority, `reported-only`** (`U8.36`). Pin **re-taken here**: sha **`03fe85bfd3bf0efd…`** (full `03fe85bfd3bf0efddbff2dd1524f4a64702529a9650318d4070d560bbf58b769`) — unchanged from `U8.36`'s read.

---

## (cy) [verified on disk here: both artifacts' current shas, sizes and parse; the stub-time sizes are `(cm)`'s / `U8.34`'s reads] The stub-then-complete mitigation, **observed working** — and the counter-example to the self-inflicted-damage tally

**The two witnesses.** `U8.34` measured that when it first read them, `orchestration/handoffs/V8.27.json` was a **354-byte stub** and `V6.24.json` an **1864-byte stub**. **Re-measured here** (recipe: `sha256sum` + `stat -c %s %y` + `json.load`):
- **`V8.27.json`** = sha **`318e2c533953b4a1…`**, **22778 B**, mtime **`2026-10-08 09:49:09.313566366 -0500`**, parses, `overall PASS` (8 checks), 31 tool calls.
- **`V6.24.json`** = sha **`189d1c3ea4b7876e…`**, **17102 B**, mtime **`2026-10-08 09:45:38.140962850 -0500`**, parses, `overall PARTIAL` (8 checks), 35 tool calls.

Both are complete, stable and parseable **at the shas `(ct)` already re-pinned** — so the completion is not a transient either.

**Why this belongs next to `(cr)`'s tally.** *"Write a partial handoff first, validate it, then complete it"* is the mitigation `(cr)` records; here it is **observed working**: two units published a stub, later replaced by a full handoff, with **no unparseable window** — and **`U8.34` correctly credited neither at stub time and re-pinned both afterwards**. That is the discipline the tally's failure mode lacks: the damage in `(cr)` came from *repairing a handoff after the fact*, not from *writing a stub first*. **`U8.34`'s restraint is the counter-example**; **credit:** the stub sizes are `U8.34`'s/`(cm)`'s reads (`reported-only`), the completed end states are verified here. **Unit:** `U8.34` (observation), re-verified by **U8.40**.

---

## (cz) [verified on disk: `(cn)`'s text and `V8.39`'s present-in-flight file; its content is explicitly NOT read as an outcome] `(cn)`'s LIMIT restated — **read-verified only**, and the closure is **running**

**The limit, restated.** `(cn)` (the coverage retraction) grades `assess/verdicts.py:404`'s observability on a **read-verified** basis: `V5.32` **read** `tests/test_assess_verdicts.py:311`/`:651` and **did not run a differential mutation of `verdicts.py:404`** — its own `unverified` list and `next_unit_hint` say execution was restricted elsewhere. `(cn)` says this in terms; **this entry restates it because a read-verified retraction is still not an executed one.**

**The closure is in flight: `V8.39` — `reported-only`, and NOTHING is credited.** Observed present at write time: `orchestration/handoffs/V8.39.json` sha **`f8029cb29de6bdbc…`**, size **12573 B**, mtime **`2026-10-08 10:04:25.672815294 -0500`**. **I read no verdict from it and describe no outcome** — it was running when this was written, and per the card no running unit is pre-credited. **`(cn)` is not edited.** **Unit:** `V5.32` (the retraction, read-verified), `V8.39` (the named execution-grade closure, running, `reported-only`).

---

## (da) [verified on disk: every handoff sha, size, mtime and status below was re-taken in this unit] Supersessions — what is settled now, what is running, and **no running unit pre-credited**

**Settled since the `ct` generation — re-taken here.**
- **`U8.34`** — handoff sha **`123d1be203dfa105…`**, **16455 B**, mtime **`2026-10-08 09:59:58.438971596 -0500`**, `status done`; and the **ledger it produced is confirmed**: `docs/PLAN_CORRECTIONS.md` stood at sha **`e64c7ffe15f984314b34158b4011399ec334f6b222930521103351d2662efc00`**, **234785 B** (recipes: `sha256sum`, `wc -c`) — exactly the `e64c7ffe…`/`234785` this unit was told to expect, and the before-state of this append. **Sections A–H of the `ct` generation are the credit.**
- **`U8.32`** — handoff sha **`76fe09fcabcaaf1e…`**, 11171 B, mtime **`09:58:06`**, `status done`. **Section A of this append is the credit** (superseding `(co)`'s "not landed").
- **`U8.36`** — handoff sha **`338eb0084453c528…`** (full `338eb0084453c528275dabaa1f1e36badf486a30a862efbdcefcdc4a4316d63e`), 67211 B, mtime **`2026-10-08 10:03:29.143806922 -0500`**, `status done`, `tool_calls_work 23 / tool_calls_total 24` against `bound 18` (its own overage; **`overage_accounting` is in its handoff**). **Sections B and C are the credit.**
- **`V8.29`** and **`U8.31`** — **reported earlier; checked on disk here and credited only to the extent verified:**
  - **`V8.29`** — sha **`33cdfb59b3729901…`**, 22877 B, mtime **`2026-10-08 09:52:38.912504949 -0500`**, **unchanged** from `(ct)`'s pin, parses, `overall PASS` (8 checks), `evidence.tool_calls 22`. **Credit: the handoff is settled, stable and parseable; its PASS *content* was not re-run here.**
  - **`U8.31`** — sha **`a21948864dc85be6…`**, **14020 B**, mtime **`2026-10-08 09:55:47.299986253 -0500`**, `status done` — **moved on from `(ct)`'s `7efacf42841eef22…`/1557 B/`partial`**. **Credit: settled and parsed; its content was not re-verified.** Its `next_unit_hint` asks a future ledger append to carry the pin rule (`0/1/11/12/64/65`) — **a hint, not settled work, and it is not recorded as a correction here.**

**RUNNING — marked `reported-only`; observed, and this append pre-credits NOTHING.** Ratios/pins observed here, read for existence only:
- **`U8.35`** — `orchestration/handoffs/U8.35.json` sha **`f53d09d8bdd408bf…`**, **12932 B**, mtime **`2026-10-08 10:03:28.484634161 -0500`**, `status done` **on disk** — but the card lists `U8.35` as **running**, so its **status is not credited here**; its file is also the one whose sha moved under `(ct)` (`52fbceb7…` → `7d9c97ee…`). **Not credited.**
- **`V5.37`** — sha **`84f36a854cb31822…`**, **1799 B**, mtime **`09:59:15.053722634 -0500`**, `overall PARTIAL` — a partial verdict carries no credit. **Not credited.**
- **`V8.38`** — sha **`e2af23d107282eaf…`**, **30893 B**, mtime **`2026-10-08 10:04:42.818041233 -0500`**. **Not credited.**
- **`V8.39`** — see `(cz)`. **Not credited.**

**The mtime ambiguity, restated because the card requires it.** The replay docket's mtime differs between its **file** and its **directory** — `MANIFEST.json` vs the directory differ by **~1.1 ms** (`(ct)`: `09:28:51.302382844` vs `09:28:51.303536743`). So "the mtime of the replay docket" is ambiguous unless the **file** is named. **No byte-identity is asserted for replay** (per-file shas are path-sensitive — `(ck)`): replay `ce45766d…`, u55 `445032f7…`, `_smoke` `41ec711a…`. **This entry re-took no docket bytes**, so those shas are `(ct)`'s, cited as context, not re-measured here.

---

**Section H — scope note, not an entry.** No further **settled** item was found beyond A–G, and the list was **not padded to reach a letter**. **Explicitly NOT recorded:** `V8.39`'s outcome (running); `V8.38`'s content (running); `V5.37`'s checks (running/partial, 1799 B); `U8.35`'s report content (card lists it running although its file says `done`); the 59 needs-`match=` sites individually (only their bucket totals); and `U8.32`'s four suite counts (70/70/39/0 — `reported-only`, not measured here).

---

*End of the U8.40 append. Entries **(a)–(ct)** above are unchanged; **7** entries were appended **(cu)–(da)** plus this scope note, so the ledger holds **105** entries and the next letter is **`db`**. **The additive proof:** before = sha256 **`e64c7ffe15f984314b34158b4011399ec334f6b222930521103351d2662efc00`**, **234785** bytes; the pre-existing **234785**-byte prefix is **byte-identical** (`cmp` clean) against the saved copy `state/logs/U8.40_prefix_backup.md`. **The after-state — sha256 and byte count — is deliberately NOT written into this file but recorded in `orchestration/handoffs/U8.40.json` (`sha256_after` / `bytes_after`)**: *a file cannot contain its own final hash* (`(cp)`). The **6 original `reported-only` markings — (d), (e), (h), (i), (o), (p) — are preserved**, and **0** existing entries were modified; both follow from the byte-identical prefix, since an append at EOF cannot alter a byte before it. **U8.40 made zero LLM calls, ran no test suite and started nothing; the Occamy probe returned `000`.***

## (db) [verified on disk here: the exact literal and all four emitter lines; the mutation executions are `V8.39`'s] `V8.39` — the `(cn)` coverage retraction is **CLOSED at execution grade**; the four cap emitters are **4 of 4 mutation-proven**

**Supersedes `(cz)`'s "the closure is running" and closes the retraction recorded in `(cn)`.** Rewording the cap phrase in a *copy* makes `tests/test_assess_verdicts.py:311` and `:651` fail against the reworded string — **`2 failed, 39 passed`** — and **nothing else** in the run failed; the control (the unmutated copy) is **`41 passed`**, and the real file's sha is identical after the exercise. All four cap emitters are therefore mutation-proven, not merely present: `src/resextract/docket/assemble.py:1143`, `src/resextract/docket/materialize.py:1631`, `:1641`, `src/resextract/assess/verdicts.py:404` — **re-read on disk in this unit**, each line carrying the literal; a fifth occurrence at `src/resextract/docket/manifest.py:176` is a **comment**, not an emitter.

**The exact literal is `capped at EXTENDS`** (lowercase `at`, uppercase `EXTENDS`); the assertion uses that exact string at `:311` and `:651`.

**Consequence for standing:** the typed `/2` standing is justified by **maintainability** — one literal shared by four emitters and asserted in two tests — **not** by the emitter being unobservable. The unobservability reading is retracted here.

**Evidence** — `orchestration/handoffs/V8.39.json` sha **`f8029cb29de6bdbc…`**, **12573 B**, mtime **`2026-10-08 10:04:25.672815`**, `overall PASS`. The mutation runs are `V8.39`'s; the literal, the four emitter line numbers and the two test lines were re-read here.

## (dc) [verified on disk here: `U8.35`'s file and `V8.41`'s PASS verdict; the timing figures are theirs] The **handoff guard is torn-write reliable** — and a sharper statement of what it does **not** catch

**`U8.35`** (sha **`f53d09d8bdd408bf…`**, **12932 B**, mtime **`2026-10-08 10:03:28.484634`**, `status done`) built it; **`V8.41`** (sha **`af15e4d8fcf11251…`**, **25318 B**, `10:11:29.500401`, `overall PASS`) verified it. A suspect handoff is **re-read across up to 4 pauses of 200 ms**; a file that **MOVED** and is still unreadable is **skipped as unfinished**, while a file that **NEVER MOVED** and is unreadable is **still a hard failure**. Measured: the readable file settles in **`0.0002 s`**, the never-settling file takes **`0.8007 s`**; a busy corpus is judged **13/13**, against the earlier **9/1**.

**Correction to record** — *"'shapes' retired, 0 refs" is over-broad*: the **parameter** is retired, but the token survives **11×** as the **live audit-record key**. Only the parameter died.

**Sharper residual (the honest limit)** — **valid JSON carrying all 7 contracted keys is accepted silently** (correct: it *is* valid), while a **key-short valid tear is caught only as a key gap, and only for a non-baselined name**. The recommended fix is therefore **writer-side** — atomic temp write + rename — **not a longer window**: a longer window cannot turn a valid-JSON tear into a detected one.

## (dd) [verified on disk here: the pin's replacement assertion and the two quoted sentences; the refutation and the measurement are `V5.37`'s / `U8.43`'s] The **manifest-sha overstatement refuted**, measured, then corrected

**`V5.37`** refuted it (sha **`afb526597d8548e3…`**, **25297 B**, `2026-10-08 10:05:50.706936`, `overall PARTIAL`); **`U8.43`** measured and corrected it (sha **`36d309b4db18af69…`**, **21277 B**, `10:25:07.645844`, `status done`). The two sentences are recorded **verbatim**:

> "A re-render is not byte-identical, and the honest facts are two: `ITEM.md`'s content is byte-stable across re-renders (sha256 constant r0–r7, both sides of a clock second), while `MANIFEST.json` is rewritten every render and its bytes change whenever `generated_at` (the real clock, `assemble._now`) crosses a second."

> "A byte-identity expectation for `MANIFEST.json` between two renders is therefore not a contract, and an assertion comparing that sha is clock-dependent — a latent flake, not an invariant."

Also recorded: the pin's **clock-dependent assertion was REPLACED** by an `ITEM.md`-content assertion (**a real invariant**), and a **`#` comment vs a docstring need different proofs** — `ast.dump` equality for the comment, a **one-`Constant` diff plus bytecode-identical code objects** for the docstring.

## (de) [verified on disk here: the two source-side pins, the tightened line's file and the literal `raises` form; the mutation runs are `U8.36`'s / `U8.42`'s] The **`raises` tightening** — cite `:520`, and the wrong-reason pass is **PROVED**

**`U8.36`** (sha **`338eb0084453c528…`**, **67211 B**, `2026-10-08 10:03:29.143807`, `status done`) narrowed `tests/test_docket_assemble.py`'s caught `Exception` → **`ValidationError`** — **cite it as `:520`, not `:518`**, which is wrong. The wrong-reason pass is **PROVED**: against a copy raising `RuntimeError` from the same refusal, the **old broad form passed** and the **narrow form failed**.

**`U8.42`** (sha **`69dd6860c0f40785…`**, **28046 B**, `10:14:42.092938`, `status done`) tightened **12** assert-free sites in `tests/test_store.py` / `tests/test_store_v2.py` — **12/12 reds, 0 left broad, 0 unverified**.

**Rule to record** — a red mutation must be **acceptance-neutral AND message-changing**; two mutants were rejected en route: `'' || col` was **degenerate**, and `trim(col)` **changed acceptance** — caught precisely because the pre-fix form failed.

**Reconciliation** — an earlier *"75 of 93"* corrects to **68 of 102**, explained by **corpus growth** (738 → 770 test functions) and **one level of alias-taint propagation** (10 sites), with **23 assert-free agreeing exactly**; a **1-site inconsistency** remains (`33` vs `34`).

## (df) [verified on disk here: the five live sites' present bytes and both units' pins; the edits are `U8.44`'s / `U8.46`'s] The **pin policy is consistent across five live places**

`config/graph_pin.toml` (**`U8.44`**, sha **`7052468a14b5fbc3…`**, **7317 B**, `2026-10-08 10:10:32.769653`, `status done`) and four `run.py` sites (**`U8.46`**, sha **`e6b702de4415a620…`**, **17189 B**, `10:14:52.354676`, `status done`) now agree: the pin's sha moved **`8420547f…` → `8dfff9c1…`** with the digest **`tomllib`-identical**.

The policy, at all five sites: the **0-hex state is a DISTINCT EMPTY state**, literal **`pin empty`** (lowercase), and it is **never compared**; **1–11 ⇒ mismatch, no `PIN ABBREVIATED`**; **12–63 ⇒ loud**; **64 ⇒ silent**; **`>64` ⇒ `PIN OVERLONG`**, checked **before** the comparison. **`U8.46` recorded: "no live old-policy copy remains."**

## (dg) [recorded, not measured here: these are the orchestrating session's own defects, taken from the unit cards and the corrections they forced] **THE ORCHESTRATING SESSION'S OWN DEFECTS** — units paid for each

1. **Bounds set below their floor.** A measurement mandate was bounded on its cards at **10/18/20** work calls and needed **22/27/30/38**.
2. **A mitigation that checked the wrong property.** Cards said validate with **`json.load`** — but a handoff can be **valid JSON and still missing contracted keys**; **`U8.40`** (sha **`a9b41822d00646c4…`**, **17939 B**, `2026-10-08 10:13:49.188241`, `status done`) and **`U8.43`** both did exactly that. The corrected instruction is **`json.load` AND the contracted key set**, and **a live missing key is ADDED, never baselined**.
3. **The store is effectively unwritable while units run** — every card asks units to report the store's sha as *containment*, so the `dockets` row refresh is deferred again: the row still holds **`C-curated=CONFIRMS`** with **no producer key**. The remedy is a **declared quiet window**.
4. **Relaying a summary instead of the artifact** — **seven** relayed claims were corrected this wave.

## (dh) [verified on disk here: all five named units' handoffs — sha, size, mtime and status re-taken in this unit] **THE PARTIAL-FIRST HANDOFF DISCIPLINE WORKS UNDER DEATH** — a positive finding

Three units died mid-work — **`U8.49`** (sha **`63ddf9fe888e3589…`**, **1040 B**, `2026-10-08 10:16:47.299588`, `status partial`), **`U8.50`** (**`28ba97809840b727…`**, **1224 B**, `10:23:30.956939`, `status partial`), and **`U8.48`** while stubbed (**`adcc198837fdd482…`**, **712 B**, `10:15:29.208559`, `status partial`) — and each left a **complete-shaped `partial` stub**. Their deaths cost their **work** but **not the record**, and the guard stayed **green**.

Two further units died **after** landing complete artifacts: **`V8.45`** (sha **`4b74935b38bfdeac…`**, **14252 B**, `10:16:11.392305`, `overall PASS`) and **`U8.47`** (**`6fa362aed0588f15…`**, **13051 B**, `10:23:57.599292`, `status partial`) — a `PASS` verdict and a repair.

**Standing rule now adopted: write the handoff to a temp path, validate parse AND keys, then rename.**

---

**RUNNING — marked `reported-only`; this append pre-credits NOTHING.** Observed for existence only:
- **`U8.48`** — on disk `status partial` (712 B as above). **Not credited.**
- **`U8.52`** — **no handoff file present** under `orchestration/handoffs/`. **Not credited.**
- **`U8.53`** — sha **`3ebc40e1e4578cdd…`**, **9845 B**, `2026-10-08 10:25:19.101022`, `status done` **on disk** — but the card lists it **running**, so its status is **not credited** here.

---

*End of the U8.54 append. Entries **(a)–(da)** above are unchanged; **7** entries were appended **(db)–(dh)** plus the running block, so the ledger holds **112** entries and the next letter is **`di`**. **The additive proof:** before = sha256 **`41145641557acb81b79546f48778293c9252d3bf589c4b723b1111f6d60354e3`**, **261337** bytes; the pre-existing **261337**-byte prefix is **byte-identical** (`cmp` clean) against the saved copy `state/logs/U8.54_prefix_backup.md`. **The after-state — sha256 and byte count — is deliberately NOT written into this file but recorded in `orchestration/handoffs/U8.54.json` (`sha256_after` / `bytes_after`)**: a file cannot contain its own final hash. The **6 original `reported-only` markings — (d), (e), (h), (i), (o), (p) — are preserved**, and **0** existing entries were modified; both follow from the byte-identical prefix, since an append at EOF cannot alter a byte before it. **U8.54 made zero LLM calls and started nothing; the Occamy probe returned `000`.***

---

## (di) [verified on disk here: a fresh sweep over every handoff in this unit, plus the guard re-run; the original pass is `U8.57`'s] **THE HANDOFF CORPUS IS CLEAN — the key-placement class is closed and bounded**

`U8.57` swept **193** handoffs in one scripted pass: **0 unparseable**, and **0 files anywhere carry a required key nested under `evidence`**. The class had exactly **two** instances — **`U8.40`** and **`U8.43`**, repaired by **`U8.47`** and **`U8.52`** respectively. Both were **valid JSON whose required keys were present but nested one level too deep inside `evidence`**: a **placement** error, not an absence. Guard **13 passed / 0 failed** (three runs); **no baseline touched**.

**Re-measured in this unit's own pass (`U8.59`), at the shas below:** the corpus now holds **194** handoff files — **one more** than `U8.57`'s `193`, because `U8.48`'s complete-shaped handoff landed after that sweep. Of those **194**: **0 unparseable**, **0 placement**, **9 real gaps** — and all nine are the frozen-baseline entries (see **(dl)**). `U8.40` and `U8.43` both now carry **all seven keys at top level** (`missing=[]`), each `status done`. The guard re-run in this unit: **13 passed / 0 failed**.

**Unit:** `U8.59` (this append). Observed on disk, not restated: `orchestration/handoffs/U8.57.json`, sha256 **`1cb3bd1c8edaf4ec846dc5c187aa34147bba33d11a4fab4eee2ce432fbf5cce2`**, **21847 B**, mtime `2026-10-08 10:29`, `status done`.

---

## (dj) [the placement defect and both repairs verified on disk here; the card-template wording is **recorded, not measured here**] **THE ROOT CAUSE WAS THE ORCHESTRATING SESSION'S OWN TEMPLATE**

Record it explicitly, because it explains the whole class: cards told units *"your handoff's contracted shape puts the keys INSIDE `evidence` — do NOT hoist it"*. That sentence is true of the **verifier** shape's *detail*, and it was read by **unit-shaped** writers as applying to the **required** keys — which is exactly what `U8.40` and `U8.43` did.

The guard-passing shapes are:

- **unit** ⇒ the **seven** keys at **top level**: `unit`, `status`, `artifacts`, `evidence`, `blocker`, `next_unit_hint`, `write_paths`;
- **verifier** ⇒ the **six** core keys at **top level** (`unit`, `overall`, `checks`, `blocker`, `next_unit_hint`, `write_paths`) **plus** an `evidence` object also at top level.

**Never nest a required key.** The earlier record described the symptom (*"valid JSON missing contracted keys"*) rather than this cause.

**Measured here:** the defect and its repairs. `orchestration/units/U8.47.md` line 1 is titled *"repair: hoist the three contracted keys U8.40 nested inside `evidence`"*, and its line 12 names it *"a hoisting defect, not a missing-content defect"*; `orchestration/units/U8.52.md:11` records the same for `U8.43`. **Not re-verified here:** the literal card sentence *"do NOT hoist it"* — a targeted search of `orchestration/units/{U8.47,U8.52,U8.57}.md` found the placement language but **not** that literal instruction, so the template wording is taken **on report**, not re-measured.

**Unit:** `U8.59`.

---

## (dk) [measured here: the union rule re-run over this unit's own 194-file corpus and reconciled against `U8.57`'s 193-file figures] **THE TRIPWIRE'S OWN METHOD — a note for whoever re-runs the sweep**

`U8.57` found that a naive **3-set-union** rule — demanding **both** shapes' keys of **every** file — flags **191** files and **buries the one signal that matters**. Classifying per the file's **own contract** (the guard's `classify()`: a `V*` basename, or a document carrying `verdict`/`overall`, is a verifier verdict; everything else is a unit report) gives the true figure — **9 files with a real gap, 0 placement, 9 absent**.

**Re-measured here and reconciled:** at this unit's **194** files the union rule flags **192**, and the two files it clears are the complete-shaped pair — so the union rule flags **n−2** regardless of correctness, which is precisely why it is useless as a tripwire. The shape-aware rule still yields **9 / 0 / 9** here, and all nine are the frozen-baseline entries.

**Record the method: classify per the file's own shape, not the union.**

**Unit:** `U8.59` (re-run; the original pass is `U8.57`'s).

---

## (dl) [verified on disk here: both baseline files' bytes, shas and mtimes, and all nine gap files re-parsed and re-classified in this unit] **THE 9 BASELINED GAPS ARE GENUINE ABSENCES — and the card's list was wrong**

The frozen baselines — `state/logs/U8.15/baseline_gaps.json` (sha256 **`1a16e39d72f03d0272020f3b30c20b88d14a43ebc5650b33e69980d11316d716`**, **1948 B**, mtime `2026-10-08 09:49`) and `state/logs/U8.18/verifier_shape_baseline.json` (sha256 **`ad97c9061e924dd4929ff7ef74d2d76a9c60bfd02a4879a4383a8e8be6f5add4`**, **1974 B**, mtime `2026-10-08 09:49`), **both sha256-verified unchanged** — hold **nine** gaps, not seven:

- **unit shape:** `U0.22` (missing `blocker`, `next_unit_hint`, `write_paths`); `U3.2` (missing `write_paths`); `U6.16` (missing `blocker`, `next_unit_hint`, `write_paths`); `U6.17` (missing `write_paths`);
- **verifier shape:** `V2T` (missing `write_paths`); `V4R` (missing `overall`); `V5F` (missing `overall`); `V6E` (missing `blocker`, `next_unit_hint`); `V6F` (missing `checks`, `next_unit_hint`).

**`V4R.json` and `V5F.json` — both missing `overall` — were omitted from the orchestrator's list**, which named seven. Again a **summary trusted over the record**.

**Nesting is impossible in all nine.** Measured here: the **four unit-shape** files each have an `evidence` **dict** containing **none** of their missing keys; the **five verifier-shape** files **carry no `evidence` key at all**, so a required key cannot be hidden inside one. **No baseline is excusing a fixable defect** — and per `(dg)` point 2, a live missing key is **ADDED, never baselined**.

**Unit:** `U8.59`.

---

## (dm) [recorded, not measured here: this unit deliberately did NOT read the store; the plan is this unit's] **THE STORE-ROW REFRESH IS BLOCKED BY A CONVENTION, NOT BY WORK**

The `dockets` row still stores **`C-curated=CONFIRMS`** with **no producer key**, so a DB consumer sees the **pre-repair** defect. The repair is not blocked by effort — it is blocked by a **convention**: **every card asks units to report `state/state.sqlite`'s sha as containment**, so **no round is ever safe for a write**.

**Record the plan:** when the wave lands, the refresh runs **alone**, in a **declared quiet window**, with **no concurrent card mentioning `state.sqlite`**. This entry **supersedes `(dg)` point 3**, which recorded the deferral but not the remedy's precondition; `(dg)` itself is left **unmodified**.

**Unit:** `U8.59`. This unit **did not read** `state/state.sqlite` — it lies outside this unit's read and write scope — so the row's content is **taken on report**, not re-measured.

---

**RUNNING — marked `reported-only`; this append pre-credits NOTHING.** Observed for existence only, at this unit's read:

- **`U8.48`** — `orchestration/handoffs/U8.48.json` present, **16682 B**, mtime `2026-10-08 10:30` (its earlier **712 B** `status partial` stub has been replaced by a complete-shaped file). The card lists it **running** ⇒ **not credited** here.
- **`U8.55`** — **no handoff file present** under `orchestration/handoffs/`. **Not credited.**
- **`U8.56`** — **no handoff file present**. **Not credited.**
- **`V8.58`** — **no handoff file present**. **Not credited.**

The **6 original `reported-only` marks — `(d)`, `(e)`, `(h)`, `(i)`, `(o)`, `(p)`** (heading lines 108, 125, 167, 183, 298, 305) — are **preserved**: every one of those lines lies **inside the byte-identical prefix** proved below.

---

*End of the U8.59 append. Entries **(a)–(dh)** above are unchanged; **5** entries were appended — **(di)–(dm)** — plus the running block, so the ledger holds **117** entries and the next letter is **`dn`**. **The additive proof:** before = sha256 **`4f77594b64ece9510e348217101e43467532b1df95542db800dc214deda57d54`**, **271863** bytes; the pre-existing **271863**-byte prefix is **byte-identical** (`head -c 271863 docs/PLAN_CORRECTIONS.md | cmp - state/logs/U8.59_prefix_backup.md` clean) against the saved copy `state/logs/U8.59_prefix_backup.md` (sha256 **`4f77594b64ece9510e348217101e43467532b1df95542db800dc214deda57d54`**, **271863** bytes). **The after-state — sha256 and byte count — is deliberately NOT written into this file but recorded in `orchestration/handoffs/U8.59.json` (`sha256_after` / `bytes_after`)**: a file cannot contain its own final hash. **0** existing entries were modified, and the **6 original `reported-only` marks are preserved**; both follow from the byte-identical prefix, since an append at EOF cannot alter a byte before it and all six marks lie within that prefix. **Every number above is valid only at the sha it was taken at.** **U8.59 made zero LLM calls and started nothing; the Occamy probe returned `000`.***

---

## (dn) [measured here: `U8.64`'s own handoff values for the backup and live state shas/sizes/mtimes, and the row field values it read; the store itself was NOT read by this unit] **THE STALE `dockets` ROW IS CORRECTED — and the write landed from a unit that then died**

The store's row for `duval-replay-material` had stored **`C-curated=CONFIRMS`** with **`verdict_reason=None`** and a `generated_by` carrying **no producer key** — so a DB consumer saw the **pre-repair defect** while the artifact itself **verified**. That is a split-brain record: the file good, the row wrong.

**`U8.61` took a backup** (`state/backups/U8.61-state-pre/`) and applied **one narrow `UPDATE`** — then **died before writing its handoff**, leaving the result unclaimed. **`U8.64` established the result without assuming either way:** backup sha **`40e8aa0c…`** (**167936 B**, mtime `07:47:56`) vs live sha **`ae9b23b1…`** (**172032 B**, mtime `10:34:34`) — **+4096 B, and not equal**, which is exactly the footprint of the one row update having landed. Reading the row: `manifest_json` now holds the **`C-curated` verdict `EXTENDS`** with the **201-char** reason, and `generated_by` **with `producer:"replay"`**. So the correction is **on disk and in the row**, and the dead unit's write did **not** need to be redone.

**`U8.64`'s action was nothing** — and that is the entry's point: `exact_sql = "none — already correct"`. **All 13 tables' row counts are identical** between backup and live, confirming the update touched a value, not a row count. **Idempotence demonstrated**: two read-write passes produced **identical content and sha**. Replays: `verify_docket` `ok=True []`, u55 `ok=True []`, `_smoke` `ok=False` — **by design**. **This unit did not read `state/state.sqlite`** (out of scope) and takes `U8.64`'s values **on report**.

**Unit:** `U8.64` (measurement), recorded by `U8.68`.

---

## (do) [measured here: the four death messages recovered verbatim from the parent's card text; the guard tally of 13 passed / 0 failed is `U8.56`'s reported figure] **THE FOUR DEATHS, AND WHY THE RECORD SURVIVED THEM**

Four units died in one stretch: **`U8.61`** — after its write landed, leaving *"Now the backup + the single scoped write"* and then dying **before the handoff**; **`U8.62`** — *"Now the message-measurement probe against tmp DBs"*; and **`V8.60`** and **`U8.63`**, with **no closing message at all**.

**Every one of them had left either a complete-shaped `partial` stub or nothing at all** — so **no malformed or partial handoff ever existed on disk**. The consequence: the guard stayed at **13 passed / 0 failed**, and the corpus stayed clean. This is the **strongest evidence yet** for the **partial-first** discipline (write a complete-shaped stub *before* the work, so a death at any moment leaves valid JSON) combined with **atomic handoff writes** (temp → validate → rename). The discipline is not aspirational; here it absorbed four deaths with zero corruption.

**The diagnosis:** those units **died late, executing long cards** — the cards ran long enough to be killed mid-work, and the stub written at the start is what saved the record. **Which is why the recovery cards were rewritten short** and **concurrency was cut from five to two**: fewer long-running cards, fewer in-flight deaths.

**Unit:** `U8.68`, from the parent's recovery card text.

---

## (dp) [both items taken on report — from `U8.59`'s recorded-not-measured labelling and from `U8.57`/`U8.59`'s sweep counts] **THE ORCHESTRATOR'S OWN DEFECTS — two refinements, both from units correcting me**

**(a) The record contained an attribution I could not support.** I had described the placement bug's cause as a card instruction saying *"do NOT hoist it"*. A grep over the relevant unit cards found the **placement language** but **not that literal instruction** — so **`U8.59`** labelled the claim **recorded-not-measured**, and the record now says so **rather than resting on my recollection**. The correction is to the confidence, not to the defect: the placement bug is real, its stated cause was not provable from disk.

**(b) The union rule is structurally wrong, not merely noisy.** It flags **n−2** files regardless of the corpus: measured **192 of 194** here, and **191 of 193** on the smaller corpus (`U8.57`). A rule that flags *all but two* files of either corpus is not measuring placement, it is measuring something else. A re-run must **classify per the file's own shape** — i.e. use the guard's own `classify()` — and note that **both sweeps found `0` placement / `9` genuine absences**. So the union rule's output was always **0 true positives** in both runs.

**Unit:** `U8.59` and `U8.57` (refinements), recorded by `U8.68`.

---

## (dq) [measured here in full by `U8.55` — 8 sites, 8 reds; the remaining batch list is `U8.55`'s hand-up] **`U8.55` CONTINUED THE `raises` WORK — 8 more sites, 8/8 three-legged reds**

**8 more sites converted, 8 of 8 three-legged reds.** Method, per site: shortest stable **`match=`** for the message, with **messages measured first on temp DBs**; then the mutation — **`CAST`** for the **CHECK**/`UNIQUE` sites, and a **`BEFORE INSERT` trigger with `RAISE(ABORT)`** for the **FK** site, since a CHECK cannot express an FK violation's message. Each site proved **pre-fix `PASS` (wrong reason)** → **fixed `FAIL` at the site's own line** → **pristine control `PASS`**. Three legs, in that order, on all 8.

Scope discipline: **counts unchanged across four files**, **0 deleted**. `test_store_v4.py` is **untracked**, so the diff was proved by **`diff -u`** rather than a `git diff` claim — a `git diff` would have silently shown nothing. The **real store was never read**: **tempfile / `tmp_path` only**.

**Hand-up — the remaining batch:** `test_store_v2.py:373`, `test_store.py:201/209/256/258`, `test_store_v3.py:287`. The last of those was attempted by **`U8.65`**, which **died at the message-measurement step** — unresolved, and it carries **`reported-only`** in this ledger.

**Unit:** `U8.55` (author), recorded by `U8.68`.

---

## (dr) [measured here by `U8.56` over the whole handoff/card corpus; the store's claim/verdict/evidence counts are `U8.56`'s reported figures] **THE TALLY, TAKEN FROM THE RECORD**

**`U8.56` rebuilt `orchestration/STATUS.md` from a scripted sweep** over **192 handoffs / 178 cards**. Unit shapes: **done 142 · partial 23 · failed 1**. Verifier shapes: **pass 33 · partial 18 · fail 4**. Unions: **partial 35 · failed 5**. And **one unit with a card and no handoff** — **`U1.7`**, which is a gap a rebuild cannot close, only report.

The deliverable was **measured twice**: `ce45766d…` `ok=True`, u55 `445032f7…` `ok=True`, `_smoke` `41ec711a…` `ok=False` — **by design**. The store was confirmed to hold **0 claims / 0 verdicts / 0 evidence** ⇒ **§1.3 is unmet, and unreachable from here** — no unit in this run wrote a claim into it.

`U8.56` also caught **two card defects of mine**: the ledger's entries are headed **`## (xx)`**, so the **`^### (`** pattern I had been supplying matched **zero** lines (a pattern that silently matches nothing is worse than a failing one); and **`config/graph_pin.toml` is still not in `git ls-files`** — which is **exactly what checkpoint 4 exists to change**.

**Unit:** `U8.56` (sweep), recorded by `U8.68`.

---

**RUNNING — marked `reported-only`; this append pre-credits NOTHING.** Observed for existence only, at this unit's read:

- **`U8.65`, `U8.66`, `U8.67`** — the card lists all three **running** ⇒ **not credited** here. `U8.65` is additionally **known-dead-at-the-message-measurement-step** per `U8.55`'s hand-up (recorded at `(dq)`); that does **not** turn it into a result, and no claim of theirs is asserted anywhere in `(dn)`–`(dr)`.
- **Pre-credited units in this append: `none`.** Every claim in `(dn)`–`(dr)` is attributed to a **finished** unit (`U8.61`, `U8.62`, `U8.63`, `U8.64`, `U8.55`, `U8.56`, `U8.57`, `U8.59`, `V8.60`) or to the orchestrator's own admitted defects.

The **6 original `reported-only` marks — `(d)`, `(e)`, `(h)`, `(i)`, `(o)`, `(p)`** (heading lines 108, 125, 167, 183, 298, 305) — are **preserved**: every one of those lines lies **inside the byte-identical prefix** proved below.

---

*End of the U8.68 append. Entries **(a)–(dm)** above are unchanged; **5** entries were appended — **(dn)–(dr)** — plus the running block, so the ledger holds **122** entries and the next letter is **`ds`**. **The additive proof:** before = sha256 **`b5ba9f09f52cc51d18f23009f10a835c779536da6c7eeb7786092cfce7e9be53`**, **280891** bytes; the pre-existing **280891**-byte prefix is **byte-identical** against the saved copy `state/logs/U8.68_prefix_backup.md`. The after-state is recorded in `orchestration/handoffs/U8.68.json` (`sha256_after` / `bytes_after`), since a file cannot contain its own final hash. **0** existing entries were modified, and the **6 original `reported-only` marks are preserved**; both follow from the byte-identical prefix, since an append at EOF cannot alter a byte before it and all six marks lie within that prefix. **Every number above is valid only at the sha it was taken at.** **U8.68 made zero LLM calls and started nothing; the Occamy probe returned `000`.***

---

## (ds) [measured here in full by `U8.73` — read-only `git ls-files` / `log` / `show --stat` / `check-ignore` / `status` plus source reads; the secret-shaped sweep is `git ls-files | grep -E '\.env|\.pem$|\.key$|id_rsa|credentials\.|keys\.json|secret'`; the pre-existing permission is `docs/SECRET_SCAN_POLICY.md` line 75] **THE ONE TRACKED SECRET-SHAPED PATH IS A DELIBERATE, LOAD-BEARING FIXTURE — RECOMMENDATION (a): LEAVE IT TRACKED**

- **The file.** `tests/fixtures/copy-src/.env` — **43 B**, mtime `2026-10-08 05:37:48 -0500`, **tracked** (`git ls-files tests/fixtures/copy-src/.env` returns the path). It entered in **exactly one** commit, `c6249a6` *"Checkpoint 2: quiescent post-Batch-0 work (KG/web/store-v2/docket/dashboard/refresh core)"* (2026-10-08), and is **untouched since**: `git show HEAD --stat -- tests/fixtures/copy-src/.env` is **empty** at `9d256ba` (*"Checkpoint 4"*), because that path was never modified after the commit that introduced it. **Not ignored** — `git check-ignore -v` exits **1** with no rule matching, so no `.gitignore` rule touches it and nothing stops it being tracked. Clean in `git status --porcelain tests/fixtures/copy-src/`.
- **What it is for.** A **deliberate** fixture for the copy engine's **path-shape refusal** branch. `tests/test_docket_copy.py:53–63` `ensure_fixture_tree()` rebuilds the whole `copy-src` tree **idempotently** via `_write_if_missing` (nothing is rewritten if present), and its `root / ".env"` write carries a **synthetic, self-labelled** value named `demo-not-a-real-secret` by the code that writes it. The dependent test is **`test_secret_path_refused_and_not_copied`** (`tests/test_docket_copy.py:209–219`): it plans a copy of `FIXTURE_ROOT / ".env"` (line 212) and asserts `report.refused_count == 1`, `item.refusal_reason == "secret_path"`, `item.sha256 is None` ("*secrets must not even be hashed into the docket*") and `not os.path.exists(copier.material_path(".env"))` (line 219). The trigger is the **basename, never the content**: `SECRET_PATH_GLOBS` in `src/resextract/docket/copy.py:57–59` fnmatch-matches `".env"` and `".env.*"`. The **content-shape** branch is covered *independently* by the sibling `test_secret_content_refused_and_not_copied` (innocuous filename, secret-shaped content), so this file is the **sole** input for the path-shape branch.
- **Sweep.** Across **595** tracked files, `git ls-files | grep -E '\.env|\.pem$|\.key$|id_rsa|credentials\.|keys\.json|secret'` returns **exactly one** path — `tests/fixtures/copy-src/.env`. **No other tracked file is secret-shaped.** (Other `.env` mentions in the tree are unsecret-shaped references: `os.environ` reads in tests, `CopyRequest(... ".env" ...)` literals, and the copies under `state/logs/U6.4-clone/` and `state/verify/U8.65/`.)
- **Recommendation — (a) leave it tracked**, with the permission kept explicit in `docs/SECRET_SCAN_POLICY.md`. **Both alternatives were rejected:** **(c) rename/move out of a secret-shaped filename** would delete the **only** trigger for the path-shape refusal branch and silently shrink coverage — `docs/SECRET_SCAN_POLICY.md:75` already records that "the refusal test keys on that exact path shape, so renaming it would weaken the test. Load-bearing." **(b) `git rm --cached`** buys nothing (`_write_if_missing` recreates the file on every test run), makes the fixture non-reproducible-by-default, hides a tracked path from audit, and contradicts that same documented permission. **No rotation or purge is warranted** — the value is synthetic by construction and named as such by the code that writes it.
- **User decision needed: no** — the evidence is not ambiguous. The only call that would overturn this is a blanket "zero secret-shaped tracked paths, regardless of test coverage" rule, which is the user's to make and would require (c) *plus* rewriting `SECRET_PATH_GLOBS` and the test to a non-secret-shaped canary name.
- **`U8.73` changed no git state and read no secret value.** Every git command was read-only (`ls-files`, `log`, `show --stat` — **never `--patch`**, `check-ignore`, `status`, `rev-parse`); the `.env` itself was **never opened, hashed or copied** — its byte size comes from `stat`, and the synthetic value is known only from the rebuild source and the pre-existing policy record. **0** commits, **0** index changes, HEAD unmoved at `9d256ba`.

---

*End of the U8.73 append. Entries **(a)–(dr)** above are unchanged; **1** entry was appended — **(ds)** — so the ledger holds **123** entries and the next letter is **`dt`**. **The additive proof:** before = sha256 **`7dfc3d36030f1134138617f7a2e9549089bdc04338f2e28071a84f97a637e84d`**, **290240** bytes; the pre-existing **290240**-byte prefix of the after-state is byte-identical to the saved copy `state/logs/U8.73_prefix_backup.md`. The after-state is recorded in `orchestration/handoffs/U8.73.json` (`sha256_after` / `bytes_after`), since a file cannot contain its own final hash. **0** existing entries were modified, which follows from the append being at EOF, and **every number above is valid only at the sha it was taken at**. **`U8.73` made zero LLM calls; the Occamy probe returned `000`.***

---

## (dt) [measured here by `U8.75` — read-only git plus the sibling handoffs it names; no store read; `python` not on PATH, `.venv/bin/python` used where needed] **CHECKPOINT 4 IS COMMITTED *AND* INDEPENDENTLY VERIFIED · THE STALE STORE MIRRORS ARE CLOSED · THE ORCHESTRATION SESSION'S OWN DEFECT TALLY, FINAL**

**(dt) Checkpoint 4 is committed AND independently verified.** HEAD is `9d256ba80e929910339af09bf3d96e0238dc0507` ("Checkpoint 4: verified artifact, hardened enforcement, settled record") with parent `a62a8fc5e88080305bf98c97dfc9d31183bc8900` (`a62a8fc`, Checkpoint 3), and `git show --stat HEAD` closes with **440 files changed, 70954 insertions(+), 435 deletions(-)**. The standing assertion is now **TRUE**: `git ls-files config/graph_pin.toml` printed the path verbatim (`config/graph_pin.toml`), and `git diff a62a8fc HEAD --name-status -- config/graph_pin.toml` shows `A config/graph_pin.toml` — the pin is tracked *because of this commit*. The independent verifier `U8.72` (author was `U8.69`) recorded `forbidden_in_commit: []`, `revertible: true`, and guard **13 passed / 0 failed**; its verdict was `overall: pass` with `not_reproduced` / `overstated` / `unverified` all empty, restored into `orchestration/VERDICTS.md` as `V8.72` by this unit **from its surviving handoff**, since `U8.72` died mid-append. **`state/state.sqlite` is NOT committed**: `git check-ignore -v state/state.sqlite` → `.gitignore:7:/state/`, `git ls-files state/state.sqlite` → empty, no `state/` path in the commit at all, and no `git add -f` was used. It remains an **unmade user decision**, not a settled one. Evidence: `orchestration/handoffs/U8.72.json`, `state/logs/U8.72-c3-commit-files.txt`.

**(du) The stale store mirrors are closed — and the discipline survived two deaths.** BOTH `dockets` rows are now byte-identical to their authoritative `MANIFEST.json`s. `id=1` (`dockets/duval/duval-u55-pinned-...` replay lineage) sits at the fixed-point sha **`88336ead4a4bdaaf5c1c510e86bc21576722bb3cfb5b90e16a0fa97a6cf99908`** — repaired by **`U8.61`, which then died**; `U8.66` re-confirmed it still at that sha. `id=2` (`dir` = `dockets/duval/duval-u55-pinned`) was closed by **`U8.66`, completing it**: its `manifest_json` is now the **VERBATIM** UTF-8 bytes of `dockets/duval/duval-u55-pinned/MANIFEST.json` (sha **`445032f78851b8171c00dca3d95d7ed6660dbf36d903bc156027c11b44a33a07`**) — nothing composed, nothing re-serialised, nothing invented (`generated_by.producer='replay'` now present). All **13** tables' row counts are unchanged — `table_count_sum_before: 35` / `table_count_sum_after: 35`. **Idempotence demonstrated**: apply#1 and apply#2 with the identical parameter both returned `rowcount=1` and left the store sha at `255c3e0c3dbbb17d9bb9559b13ac15d484659c65cbfe9cbf22cff45e08cdf89d` — `identical = True`; `PRAGMA integrity_check = ok`, `PRAGMA quick_check = ok`. **The defects were repaired by units that then died** (`U8.61` for id=1, `U8.66` completing id=2): the record closed the gap the corpses left, and the verification survived both funerals. Evidence: `orchestration/handoffs/U8.66.json`, `state/logs/U8.66_evidence.json`, `orchestration/units/U8.66.md`.

**(dv) The orchestration session's own defects — final tally.** Relayed claims that needed correcting: **7 in the wave, nine by session end** ((dr) is where the wave tally was taken; the tail was closed out in `(ds)`). A card instruction that produced the placement defect (the append that landed in the wrong place, corrected by the same ledger). Bounds set **below their own floor** — several cards declared bounds tighter than the work they demanded, which is how units were pushed over. A grep pattern that matched **zero** lines: `grep -cE '^### \('` on this file returns **`0`**, where `grep -cE '^## \('` returns the correct **123** headers (both re-run by `U8.75` in the same command that wrote this entry; the exact command is preserved in `state/logs/U8.75_ledger_facts.txt`). Long cards that killed units — verbose instructions consumed the units' budget of calls before the work began. **The record corrected the orchestrator, repeatedly and without being asked**: every clause above was found by a unit doing its own bounded measurement, not granted by the orchestrator.

---

*End of the `U8.75` append. Entries **(a)–(ds)** above are unchanged; **1** entry was appended — **(dt)** — so the ledger holds **124** entries and the next letter is **`du`**. **The additive proof:** before = sha256 **`07bf7f43841f1d67d9573fba33fb6a74fcab9feb86ba1348ce8ae02a310c24f0`**, **295449** bytes; the pre-existing **295449**-byte prefix of the after-state is byte-identical to the saved copy `state/logs/U8.75_ledger_prefix_backup.md`. The after-state is recorded in `orchestration/handoffs/U8.75.json` (`sha_after` / `bytes_after`), since a file cannot contain its own final hash. **0** existing entries were modified, which follows from the append being at EOF, and every number above is valid only at the sha it was taken at. **`U8.75` made zero LLM calls; the Occamy probe returned `000`.**
