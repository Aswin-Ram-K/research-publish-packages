# Existing tooling inventory

**Date:** 2026-10-23 · **Repo:** `/home/zer0null/reserach extarctor` · **Python:** 3.14.4 (`.venv/bin/python -V`)
**Graph artifact on disk:** `state/kg/duval/graphify-out/graph.json` — 3,188,231 B, **2,685 nodes / 7,102 links**,
`directed=false`, `graphify_version=0.9.80`, `built_at_commit=6deaed07af0d998d1672fe3f1ab1579e6ba0cdc4`
(measured by loading the JSON this session); sha256 `4790bbb1111b76ea7cfb8024a98cfb3ec8c4b038beb23f6e5b6fa729fcdd897b`
= the pin at `config/graph_pin.toml:52`.

Every claim below carries a `path:line` or the command that produced it. **[inference]** marks reasoning, not measurement.

## §1 Capability table

| # | capability | provided by | where invoked (`path:line`) | status | gap it leaves |
|---|---|---|---|---|---|
| 1 | Target tree walk + admission (`.graphifyignore`/`.gitignore`/info-exclude) | graphify's own predicate, reused — `src/resextract/kg/policy.py:12-16`; walk at `src/resextract/kg/ingest.py:17-22` | `src/resextract/kg/staging.py` via `_walk`; config surface `config/targets.toml:14-52` | `runtime` | resextract owns **no** walker; a graphify ignore-rule change silently changes what the pipeline can ever find (§`policy.py:3-10`) |
| 2 | Ingestion-coverage audit (what was silently dropped) | `src/resextract/kg/ingest.py:8-10` `coverage_audit` | **not called from `run.py`** (grep of `run.py` for `coverage_audit` → 0 hits) | `vestigial` | the "file type dropped ⇒ material can never become a finding" blind spot is measured only when a unit calls it by hand |
| 3 | Normalisers for uncovered types (`.ipynb`, `.jsonl`, `.csv/.tsv` → markdown) | `src/resextract/kg/ingest.py:527,624,764` | reached from `build_staging_corpus` (`src/resextract/kg/staging.py:8-11`) | `runtime` | formats outside those three (`.xml` handled separately, `staging.py:10`) still fall through to `kind="unsupported"` (`ingest.py:871-876`) |
| 4 | Code graph build (tree-sitter AST, no LLM) | graphify `extract --code-only` | `src/resextract/run.py:1357-1363` (`gf.extract(..., code_only=True, token_budget=GRAPH_TOKEN_BUDGET, no_viz=True)`) | `runtime` | docs/PDF/office/image passes are **off** in this invocation; only code+doc-family files reach the graph |
| 5 | Graph reuse + external sha256 pin + commit provenance | `_graph_candidates` `run.py:735`, `_graph_digest`/pin `run.py:1283,884-990`, pin file `config/graph_pin.toml:17-53` | `src/resextract/run.py:1290-1326` (reuse branch) | `runtime` | reuse decision is digest-only; a graph built from an **older** tree with an untouched digest is reused silently **[inference]** |
| 6 | Graph traversal query (BFS, token-capped) | graphify `query` | `src/resextract/mine/candidates.py:920-922`, budget `QUERY_BUDGET = 700` at `:105` | `runtime` | one BFS per canned question; no result caching beyond the run-key index at `:906` |
| 7 | Symbol / structural / pattern search | **nothing** | — | `absent` | see G1–G3 |
| 8 | Provenance verification (`graph_node` / `file_lines` / `doc_section`) | `src/resextract/mine/provenance.py:1-19,41,49` | called from the miner's accept path (`src/resextract/mine/candidates.py`, `verify_provenance`) | `runtime` | verifies *existence* only (node id in graph, span inside file, heading present) — never that the line **supports** the claim |
| 9 | Context packing for the model | `_build_prompt` `src/resextract/mine/candidates.py:621-666`; caps `MENU_NODE_LIMIT=60`, `MENU_EDGE_LIMIT=40` at `:125-126` | `:951` `self._build_prompt(query, question, result, graph, ids, indexes)` | `runtime` | packing is a flat bullet menu of node ids/labels + ≤40 edges; no file-body text, no ranking, no dedup across queries |
| 10 | Chain compaction / cache-reuse policies (4 policies) | `src/resextract/context/budget.py:45,89` | **imported only by tests** (`tests/test_context_*.py`); `context/__init__.py:1` calls it "the context-cache experiment" | `vestigial` | the pipeline's prompt is built fresh per query (`candidates.py:621`); no compaction policy is applied to a live chain |
| 11 | Cache-metering rows | `src/resextract/context/meter.py:1-16` | tests only | `vestigial` | prompt-cache hits are not measured by the pipeline |
| 12 | Target staleness measurement | `src/resextract/refresh/staleness.py:119` (`git ls-files`), `:159` (mtime digest), `:196` (`read_target_state`) | `refresh_target` → `src/resextract/refresh/__init__.py:30`, called at `run.py:1775-1786` | `runtime` | measures **git state only**; it never asks whether the graph still covers the tree |
| 13 | Rework backlog from findings | `src/resextract/refresh/backlog.py:99,248` | re-exported `refresh/__init__.py:13-22`, driven from `refresh_target` **[inference: re-export implies use]** | `runtime` | entries are text; nothing maps a rework entry to a re-extraction command |
| 14 | Incremental graph re-index after commits | **nothing** | `run.py:1781` passes `run_graph_update=False`; no `graphify update`/`watch` call exists in `src/` (grep) | `absent` | see G5 |
| 15 | Material copy + sha256 + secret refusal | `src/resextract/docket/copy.py:112` (`sha256_file`), `:176,184` (secret path/content refusal), `:491` | `docket/materialize.py:1-20` | `runtime` | copy is containment-checked, not content-classified |
| 16 | Docket manifest sha256 gate | `src/resextract/docket/manifest.py:191` (`sha256: str` on `MaterialItem`), `:381` (`split_ref`) | `docket/assemble.py` verify path | `runtime` | manifest proves byte-agreement, not provenance of the claim |
| 17 | Dependency probing (core vs optional) | `src/resextract/doctor.py:286,352,379,415,444,464,477`; `CORE/OPTIONAL` at `:43-44` | `resextract doctor`, and preflight `run.py:552+` | `runtime` | legs are *services* (Occamy, SearXNG, crawl, graphify, docling, renderers, port); there is **no leg for a search/indexing tool** such as ast-grep/ripgrep |
| 18 | Pipeline stages | `src/resextract/run.py:85-94` | `STAGE_IMPLS` `:1803-1812` | `runtime` | `graph, staging, mine, claims, assess, lanes, materialize, refresh`; nothing between "graph" and "mine" refreshes the graph |

## §2 graphifyy 0.9.80 — real capability surface

Package: `.venv/lib/python3.14/site-packages/graphify/` (54 top-level modules + 35 extractor modules).
Deps that matter: `tree-sitter 0.25.2` + **24 language packs** (`tree-sitter-{c,cpp,c-sharp,elixir,fortran,go,groovy,java,javascript,json,julia,kotlin,lua,objc,php,powershell,python,ruby,rust,scala,swift,typescript,verilog,zig} 0.23–1.0.3`,
`networkx 3.7`, `graspologic-native 1.3.1`, `tiktoken`, `pypdf`, `python-docx`, `openpyxl`, `markdownify`, `lxml`, `openai 3.26.1`.

**Subcommands** (verbatim from `.venv/bin/graphify --help`): `install`, `uninstall`, `path`, `explain`, `diagnose multigraph`,
`clone`, `merge-driver`, `merge-graphs`, `add`, `watch`, `update`, `cluster-only`, `label`, `query`, `affected`, `god-nodes`, `prs`,
`save-result`, `reflect`, `check-update`, `tree`, `extract`, `provider`, `global {add,remove,list,path}`, `benchmark`, `export`, `hook {install,uninstall,status}`.

**Parsed formats** (`graphify/detect.py:47-52`): code — 100+ extensions incl. `.py,.ts,.tsx,.js,.go,.rs,.java,.c,.cpp,.h,.cs,.rb,.swift,.kt,.php,.lua,.zig,.sql,.sh,.ex,.ml,.jl,.vue,.svelte,.tf` and ~20 more;
docs — `.md,.mdx,.qmd,.skill,.txt,.rst,.html,.yaml,.yml`; papers — `.pdf`; office — `.docx,.xlsx`; images — `.png,.jpg,.jpeg,.gif,.webp,.svg`;
video/audio — `.mp4,.mov,.webm,.mkv,.avi,.m4v,.mp3,.wav,.m4a,.ogg`. AST edge vocabulary includes `calls, imports, imports_from, inherits, implements, references, contains, method, re_exports, indirect_call, dynamic_import` (`graphify/extract.py:600-601`; the on-disk graph really contains `calls` 2,216 / `contains` 2,093 / `imports` 1,254).

**Real, not marketing:** Leiden clustering is genuine with a Louvain fallback (`graphify/cluster.py:1,22,108`); `.graphifyignore` is parsed per gitignore spec and merged **after** `.gitignore` so it can only exclude more (`graphify/detect.py:1388-1414`); incremental re-extraction is real (`manifest.detect_incremental` + stat/sha256 cache, `graphify/manifest.py:2`, `graphify/cache.py:470`); `update` accepts only `--force`/`--no-cluster` (`src/resextract/kg/graphify.py:1256-1259`, verified against the CLI).

**MCP server** — `graphify-mcp` → `python -m graphify.serve` (stdio or Streamable HTTP, `--api-key`, `--stateless`).
Registers **10 tools** `query_graph, get_node, get_neighbors, get_community, god_nodes, graph_stats, shortest_path, list_prs, get_pr_impact, triage_prs`
(`graphify/serve.py:1991-2110`) and **6 resources** `graphify://{report,stats,god-nodes,surprises,audit,questions}` (`:2428-2433`).

**What graphify does NOT do** (checked against `--help` + module list):
1. No text/regex **code search** subcommand (no `search`, `grep`, `rg` equivalent).
2. No **AST-pattern query language** (no ast-grep-style `$META` matching); its AST output is a fixed node/edge schema.
3. No **LSP** server, no symbol rename/refactor, no type-hierarchy query.
4. No **taint/dataflow** analysis exposed as a command (a `security.py` module exists but no subcommand surfaces it — not verified, see §5).
5. `query` is **lexical/BFS over node labels**, not embedding retrieval; `explain` needs a node id or label, not `file:line` (recorded in `…/scratch-graphify/FINDINGS.md`: "explain takes node ids like `register()`, not file:line").
6. `update` rewrites `<path>/graphify-out/graph.json` **in place** and has no `--graph` (hence `UnsupportedGraphTarget`, `src/resextract/kg/graphify.py:1266-1276`) — unusable against a read-only target without a copy.

### §2b Installed-but-unused: subcommand → resextract reality

Grep of every `Graphify` method call in `src/` returns exactly **two** call sites: `gf.extract(...)` (`run.py:1357`) and `self._graphify.query(...)` (`mine/candidates.py:920`).

| graphify subcommand | resextract calls it? | evidence | verdict |
|---|---|---|---|
| `extract --code-only` | yes | `src/resextract/run.py:1357-1363` | **USED** |
| `query` | yes (700-token budget) | `src/resextract/mine/candidates.py:920-922` | **USED** |
| `update` (incremental re-extract) | no | `run.py:1781` `run_graph_update=False`; grep `\.update(` in `src/` → 0 graphify calls | **UNUSED** |
| `watch` | no | grep `\.watch(` → 0 | **UNUSED** |
| `affected` (reverse impact) | no | grep `\.affected(` → 0 | **UNUSED** — no impact analysis on the pipeline's own findings |
| `god-nodes` | no | grep `\.god_nodes(` → 0 | **UNUSED** — mining never ranks hubs; candidates.py builds its own adjacency indexes instead (`:894`) |
| `path` (shortest path) | no | grep `\.path(` → 0 | **UNUSED** |
| `explain` | no | grep `\.explain(` → 0 | **UNUSED** — the miner reformats query results itself (`:630-654`) |
| `cluster-only` | no | grep `\.cluster_only(` → 0 | **UNUSED** — communities are whatever `extract` produced |
| `label` (LLM community naming) | no | grep `\.label(` → 0 | **UNUSED** |
| `save-result` | no | grep `\.save_result(` → 0 | **UNUSED** |
| `reflect` (lessons loop) | no | grep `\.reflect(` → 0 | **UNUSED** — the memory/lessons feedback loop is entirely idle |
| `tree` (D3 HTML) | no | grep `\.tree(` → 0 | **UNUSED** |
| `benchmark` | no | grep `\.benchmark(` → 0 | **UNUSED** — no token-reduction measurement |
| `check-update` | no | grep `\.check_update(` → 0 | **UNUSED** — staleness is measured by resextract's own git probes (`refresh/staleness.py:196`) |
| `merge-graphs` / `global add` | wrapper exists, never called | `kg/graphify.py:1420,1556`; 0 call sites in `src/` | **UNUSED** — no cross-repo graph |
| `diagnose multigraph` | no | grep `\.diagnose` → 0 | **UNUSED** |
| `add <url>` | no | grep `\.add_url(` → 0 | **UNUSED** — the project has its own web client (`src/resextract/web/`) |
| `hook install` | no | `kg/graphify.py:1443`; 0 call sites | **UNUSED** — and installing a hook inside a read-only target is forbidden by `AGENTS.md` |
| `graph_stats` (MCP tool) | reimplemented in Python | `src/resextract/kg/graphify.py:598` reads `graph.json` directly | **REIMPLEMENTED** |
| `god_nodes`/`explain` data shaping | reimplemented in Python | `mine/candidates.py:894` `_build_indexes` (own `file → nodes`, `label → ids` maps) | **REIMPLEMENTED** |
| `graphify-mcp` (all 10 MCP tools) | no | no MCP client in the DSH profile (§3); no `serve`/`mcp` reference in `src/` | **UNUSED** |

No case met the "REIMPLEMENTED-**BADLY**" bar: the two reimplementations are direct file readers over a graph that is already on disk, and are cheaper than a subprocess. The cost is duplicate semantics that can drift from the CLI.

## §3 Agent-facing plugin / tool surface

The session's own tool inventory is the only place a *coding agent* can touch any of this. There is **no MCP client plugin installed** — grep for `mcp` in `~/.dsh/profiles/web/package.json` and `cordis.patch.yml` → 0 hits, so `graphify-mcp`'s 10 tools are unreachable from a session today.

| plugin (from `~/.dsh/profiles/web/package.json:5-17`) | what it gives an agent | MCP-based? |
|---|---|---|
| `@linxin666/dsh-client-ui-task-board` 0.4.8 | `task_board_{create,list,get,update,run,manage,set_parent,schedule}` — durable cards, scheduled runs | no |
| `@local/dsh-plugin-openui` (linked from `/home/zer0null/dsh-plugins/…`) | `openui_render` — declarative UI cards/tables/charts | no |
| `@memtensor/memos-local-plugin` 2.0.20 | `memos_{search,get,skill_list,skill_get,timeline,environment}` — long-term recall | no (local store) |
| `billion-context` ^0.1.204 | `compress`, `decompress`, `search_context`, `acp_status`, `acp_cache` | no |
| `dsh-email` 0.18.0 | `email_{folders,list,search,read,attachment,reply,draft,send,mark,watch,health}` | no (IMAP/SMTP/API) |
| `@michengai/dsh-skills-manager` 1.2.11 | skill install/enable/rollback surface | no |
| `cc-safety-net` 2.6.16 | guard/secret-audit tooling (`local_secret_audit`, `local_harness_guard_audit`) **[inference]** | no |
| `dshmarket`, `dsh-bottom-info-bar`, `dsh-task-progress`, `dsh-client-auto-continue`, `@michengai/dsh-pua`, `@local/dsh-plugin-opencode-keypool` | UI/behaviour/LLM routing; no repo-tooling capability | no |
| — (provider not found in the profile tree) | `local_web_{search,crawl,scrape}`, `local_doc_*`, `local_knowledge_*`, `local_memory_*`, `local_board_*` | no |
| **not promoted:** `@local/dsh-plugin-graphify` 0.1.0 | see below — 5 tools over a graphify graph | no |

**Unpromoted plugin** — `/home/zer0null/Desktop/deepseek agent harness testing/scratch-graphify/dsh-plugin-graphify/package/`
(`package.json`: name `@local/dsh-plugin-graphify`, v0.1.0, `exports: { ".": "./lib/index.js" }`). Registers **five** tools via
`ctx.tools.register(defineTool({...}))` — `graph_query` (`lib/index.js:146`), `graph_explain` (`:230`), `graph_path` (`:315`),
`graph_stats` (`:399`), `graph_ensure` (`:470`); `inject = ['tools']` only (`:40`). It auto-derives `<repo>/graphify-out/graph.json`
per call and auto-ensures freshness (init/update/skip, `cordis-row.yml` header comment). `docs/PLAN.md:55` records it as "9/9 tests,
never promoted"; `…/scratch-graphify/FINDINGS.md` says "9/9 PASS, ~2.6s" but describes only "two tools, graph_query + graph_explain" —
**that line is stale** against the five registered in `lib/index.js`.
Promotion blockers, both concrete: (a) the package lives **outside this workspace** (`/home/zer0null/Desktop/…`), so it cannot be linked by a
relative path; (b) promotion needs a `link:` dependency in `~/.dsh/profiles/web/package.json` plus the `insert:` row from
`dsh-plugin-graphify/cordis-row.yml` appended to `~/.dsh/profiles/web/cordis.patch.yml`, i.e. a write outside the workspace and a DSH restart —
both require explicit user approval per `AGENTS.md`.

**Repo-local CLIs** (not plugins): `.venv/bin/graphify`, `.venv/bin/graphify-mcp`, `.venv/bin/resextract`.

## §4 Gap list

**G1 — No text/regex search at runtime.** There is no grep-like primitive anywhere in `src/`; the only regex scanners are packaging tools (`tools/package/scan_markers.py:1-3`).
*Why it matters:* a claim like "this constant is used in 4 places" cannot be checked, so provenance verification (`mine/provenance.py`) can only confirm that a cited line **exists**, never that it is the only or the right one.

**G2 — No structural (AST-pattern) search.** Nothing in `src/` can ask "every call of this shape"; graphify emits `calls` edges but resextract never traverses them in the reverse direction (`affected` unused, §2b).
*Why it matters:* the miner's whole product is "novel primitive / invariant violation / capability boundary" — questions whose evidence is a *pattern across files*, and the pipeline can only retrieve via a BFS over labels.

**G3 — No cross-file symbol resolution the pipeline itself trusts.** Resolution lives inside graphify's per-language extractors (`graphify/extract.py:47-68,142-144`); resextract consumes the resulting ids as opaque strings and never resolves a symbol to a definition site independently.
*Why it matters:* if two files define `main`, `path`/`explain` are ambiguous (already observed: `kg/graphify.py:28-30` records `main()` matching both `main` and `main_main`), so a cited node id can point at the wrong definition and still verify.

**G4 — No LSP / no definition-or-reference query.** No language server is used or launched anywhere.
*Why it matters:* "where is X defined vs. where is X referenced" is the cheapest high-precision signal for the assess stage, and it is missing.

**G5 — Refresh does not re-index; it only re-measures.** `run.py:1781` passes `run_graph_update=False`, `refresh_target` copies the graph rather than updating it, and no `graphify update`/`watch` call exists.
*Why it matters:* after a target commit the graph is either reused from `state/kg/` or rebuilt whole — so "refresh on new commits" is git-staleness bookkeeping, not knowledge-graph currency.

**G6 — The graph is built `--code-only`, so docs/PDF/office never enter it.** `run.py:1359` sets `code_only=True`; the doc/paper path is only reachable through `kg/staging.py` + `semantic_ingest`, which `run.py` does not call (only `build_staging_corpus` at `:1429`).
*Why it matters:* the target's densest material is prose (`config/targets.toml:23-36` admits `.lane-j-scratch/*.md` and `.txt`), and the citation edge type that would link prose to code (`cites`, 4 edges in the whole graph) is effectively absent.

**G7 — `coverage_audit` is unwired.** `kg/ingest.py:8` exists and is not called from the pipeline.
*Why it matters:* silent file-type loss is exactly the failure mode `policy.py:3-10` says must never happen, and today nothing runs the check.

**G8 — Context packing is a fixed menu, not a budget.** `MENU_NODE_LIMIT=60` / `MENU_EDGE_LIMIT=40` (`mine/candidates.py:125-126`) truncate by insertion order; `context/budget.py`'s compaction is test-only.
*Why it matters:* on a 2,685-node graph a 60-node menu is ~2% of the graph and the 700-token query budget (`:105`) decides what the model ever sees — with no scoring, the omission is invisible in the output.

**G9 — The lessons/memory feedback loop is idle.** `save-result`/`reflect` are wrapped (`kg/graphify.py:1454,1481`) and never called; no equivalent store exists in resextract.
*Why it matters:* dead-end queries are re-run every batch; there is no mechanism by which a bad query stops being asked.

**G10 — No communities are used.** `cluster-only`/`label` are never called and the miner ignores any community field.
*Why it matters:* "which subsystem does this belong to" — the cheapest way to scope a claim — is unavailable, so candidates cannot be grouped by area before assessment.

**G11 — No impact/regression surface (`affected`, `diagnose`).** Both exist and are unused.
*Why it matters:* the assessment stage cannot ask "what breaks if this is true", which is the difference between a finding and an assertion.

**G12 — No token-reduction measurement (`benchmark` unused).** Nothing in the pipeline records graph-vs-corpus token cost.
*Why it matters:* the graph's entire economic justification is token reduction; it is currently a claim, not a metric.

**G13 — No MCP client in the harness.** The profile has no MCP plugin (`~/.dsh/profiles/web/package.json`, `cordis.patch.yml`: 0 `mcp` hits), so `graphify-mcp`'s ten tools and any future Graphiti/GraphRAG/Sourcegraph server are unreachable from a session.
*Why it matters:* every candidate tool judged later will be evaluated as "could an agent reach it", and today the answer is "only via CLI wrappers someone writes".

**G14 — Copy/material path is content-blind.** `docket/copy.py:176,184` refuses secret-shaped **paths and content**, but nothing classifies licence, binary type or language.
*Why it matters:* docket material is what a reader will re-verify; an unclassifiable blob is undifferentiated evidence.

**G15 — Two `graphify` reimplementations can drift.** `graph_stats` (`kg/graphify.py:598`) and the miner's adjacency indexes (`mine/candidates.py:894`) re-derive semantics the CLI/MCP already defines.
*Why it matters:* a graphify schema change (0.9.80 → next) breaks the readers silently while `doctor.py:415` still reports the leg green.

## §5 Not verified

- Whether `refresh_target` calls `backlog.rework_entries` (re-exported at `refresh/__init__.py:13-31`, but the call graph was not traced past `run.py:1775`).
- Which plugin provides the `local_doc_*` / `local_knowledge_*` / `local_board_*` tools: `grep -rl local_knowledge_index ~/.dsh/profiles/web/node_modules` → **0 hits**, so they come from outside the profile's declared dependency tree.
- `graphify/security.py` and `graphify/validate.py` purposes (no subcommand surfaced in `--help`); I did not read them.
- Whether `memos_*` is "MCP-based": the plugin is local-store, but its transport was not inspected.
- The `--help` text for `add`, `clone`, `prs`, `merge-driver` beyond the one-line descriptions in the main help.
- Whether `resextract serve` (the dashboard, `cli.py:134-180`) exposes any search endpoint over the graph — not inspected.
- I did not run any build, test, or the pipeline; the graph artifact's digest was read, not regenerated.

## §6 `tools/package/` (publication packaging — orthogonal to the pipeline)

`tools/package/README.md` documents seven parameterised commands, all `--package <slug>`, run from the workspace root:
`neutralise.py` (injective token→tag rename, map in memory only), `census.py` (identifier census over a tree),
`classify.py` (class the census/OOV identifiers), `scan_markers.py` (regex marker scan, exit 1 on hit),
`regen_manifest.py` (regenerate `MANIFEST.json` from disk), `check_manifest.py` (independent re-hash + omission walk),
`gate.sh` (positive-vocabulary acceptance gate; **not** a leak detector, `README.md:61-64`), `md2tex.py` (one Markdown→LaTeX converter).
None of these are reachable from `resextract run`; they operate on published package trees under `papers/`/`scratch/`.

## §7 Errata (2026-10-23, from verifier V1)

Appended by unit S5 after `handoffs/V1.json` (verdict `partial`: 12 reproduced / 6 contradicted). **The body above is not rewritten** — it is the record of what S1 believed, and these entries say what is true. Full statements, proofs and effects on the plan: [`CORRECTIONS.md`](CORRECTIONS.md).

1. **G5 and §1 row 14 are wrong (C1).** Incremental re-index is **wired and disabled**, not absent. `src/resextract/refresh/review.py:416` defines `_run_graphify_update(copy_dir, *, timeout)`, `:431` builds `argv = ["stdbuf", "-oL", "-eL", binary, "update", copy_dir]`, `:433` runs it, `:628` calls it, and `:861` defaults `run_graph_update: bool = True`; only `src/resextract/run.py:1781` passes `False`. The update runs on a **staged copy** (`_stage_repo_copy`, `:443`; `copy_root = root / "repo"`, `:521`), so the target is never written. §2b's `update` row therefore changes from **UNUSED** to **USED-BUT-DISABLED-BY-THE-CALLER**.
2. **The subcommand count is wrong (C2).** Not "2 of 28": `extract` (`run.py:1357`), `query` (`mine/candidates.py:920`) and `update` (`refresh/review.py:431`) are three families. `.venv/bin/graphify --help` presents **27 command families** / **46 distinct top-level names** counting the 19 per-platform install aliases — so **"3 of ~27 families, ≈89% unused"**, and the denominator is a **help-text family count, not a spec**. §2b's table enumerates 27 items, not 28.
3. **`context/budget.py` is not "imported only by tests" (C3).** It has **no `src/` importer**; importers are `tests/test_context_append_note.py:43` and `experiments/context-cache/cells/U5/u5_cells.py:57` and `.../U14/u14_append_note_probe.py:49`. (The one `src/` hit, `context/render.py:44`, is a docstring.) The substantive point stands: it does not govern the live prompt.
4. **`graphify_version` is nested (C8).** Header §lines 4-7: the value `0.9.80` lives at `json['graph']['graphify_version']`; top-level `json['graphify_version']` is `None`.
5. **§1 row 13 is measured, not inferred (C10).** `src/resextract/refresh/review.py:945` — `entries = rework_entries(manifest, change, docket_links, now=now_dt)` — so drop the `[inference: re-export implies use]` caveat and §5's first open bullet.
6. **§3's promotion blockers are incomplete (C9, C6).** There is a third, and it is the first one a promotion hits: the five tool definitions are not registry-ready — `register()` requires `output.render` to be a function and throws `TypeError: tool "<name>" must declare output { schema, render, presentationMeta? }` (`packages/core/tools/src/index.ts:1071,1077`), while `lib/index.js:173,256,339,417,491` carry JSON schemas with **no** `render`/`schema` key, and the package's own `node_modules/@deepseek-ai/dsh-tools` (7-line `0.0.0-shim`, "NOT used by the live harness") is what the import resolves to.

**Method lesson (this is the one to carry forward).** The G5 error was not a typo: the inventory's evidence was a grep for **`Graphify` method calls** (`\.update(`), which by construction cannot see a **literal CLI argv** — the subcommand name sat inside a list of strings one level below the wrapper, and `_run_graphify_update`'s own docstring ("this module never calls `Graphify.update` at all") is true while the binary is invoked on every refresh. **An inventory built on method-call greps reports "absent" for anything invoked as a process.** Grep for the argv strings too (`"update"`, `"check-update"`, `"affected"`, …) and for the helper that builds them.
