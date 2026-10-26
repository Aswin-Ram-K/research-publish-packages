# TOOLCHAIN — requirements, current state, and the plan

**Unit S7 (consolidation) · 2026-10-23 · repo `/home/zer0null/reserach extarctor`.** This is the document you act on. It merges `FINDINGS.md` (verdicts, ranked plan), `03-lsp-code-error-rate.md` (LSP/SCIP/code-quality), `01-inventory.md` (what the pipeline has and uses, G1–G15), `02-candidates.md` (every tool judged, web metadata) and `CORRECTIONS.md` (C1–C11, what was published wrongly); those five are its evidence and are not needed to use it. Verification record: `handoffs/V1.json`. Every version, licence and star count below is a **2026-10-23** snapshot (§10); `[T#]` markers resolve in §10, and `— (no URL captured in sources)` means the sources carry no URL for that tool, so none is invented.

## §0 Executive answer

- **The capability is installed and ~89% unused.** `graphifyy` 0.9.80 answers parse/traverse/rank over the target; the pipeline invokes 3 of its ~27 command families — `extract` (`src/resextract/run.py:1357`), `query` (`src/resextract/mine/candidates.py:920`), and `update` (`src/resextract/refresh/review.py:431`) — the last wired but disabled at its only caller (`run.py:1781`).
- **What the toolchain must be:** the nine capabilities of §1 — parse, symbol identity, type-resolved references, literal evidence at `file:line`, AST-shape search, budgeted ranked selection, a type/lint gate on our own Python, a test-strength number, and proof the target type-checks at the pinned commit.
- **What it is today:** R1 and R4 have the machinery but not the coverage or the binary; R6 is partial; **R2, R3, R5 and R9 are absent** (§3).
- **Move 1 — wire what exists:** rebuild + re-pin over Rust, enable `update` after bounding the copy, PageRank selection under the existing budget, `affected`/`check-update`.
- **Move 2 — add the one missing capability class cheaply:** `rg` + `ast-grep-py` for literal and shape evidence, an offline SCIP index per pinned commit for symbol identity.
- **Move 3 — gate our own Python and validate the target:** the target's own `tsc`/`cargo`, a `basedpyright` baseline ratchet, `mutmut`, `hypothesis`. **The trap:** stack graphs — archived 2025-09-09, still what older posts recommend.

## §1 Toolchain requirements

Capabilities the pipeline needs, independent of any product. State is derived from the call sites, not from what is installed.

| R# | capability | why the pipeline needs it (what breaks without it) | state | evidence |
|---|---|---|---|---|
| **R1** | Parse target source into a queryable graph | Without it every claim is a manual read; the miner has no adjacency to walk and no node to cite | **have** | `run.py:1357-1363` (`gf.extract(..., code_only=True, out=…, no_viz=True)`) |
| **R2** | Cross-file **symbol identity** — is this the definition the claim names, not merely a node that exists | A same-named definition elsewhere validates a wrong citation, so a docket can be confidently wrong | **absent** | `mine/provenance.py:154` (id present) only; `kg/graphify.py:28-30` records `main()` matching both `main` and `main_main` |
| **R3** | **Type-resolved** references — validity, not existence | Tree-sitter name matching guesses cross-file edges; wrong `calls` edges become "evidence" in a docket | **absent** | edge vocabulary is label-based (`graphify/extract.py:600-601`); no LSP/SCIP client in `src/` |
| **R4** | Literal text evidence at `file:line` | "does this line still say what the docket claims" has no primitive; every such check is a graph walk or a Python read | **partial** | span-fits check at `mine/provenance.py:168`; no search primitive in `src/` — the only regex scanners are `tools/package/scan_markers.py:1-3` |
| **R5** | AST-shape search ("every call of this shape") | The miner's questions are patterns across files; without shape matching it can only BFS over labels | **absent** | no pattern subcommand in `.venv/bin/graphify --help`; `calls` edges never traversed in reverse (`mine/candidates.py:894` rebuilds label indexes instead) |
| **R6** | Budgeted, ranked context selection | What the model ever sees is decided by insertion order, and the omission is invisible in the output | **partial** — fixed 60/40 menu | `candidates.py:125-126` (`MENU_NODE_LIMIT=60`), `QUERY_BUDGET=700` at `:105` |
| **R7** | Type/lint gate on our own Python | Undefined names, `None` flow and wrong arity reach the pipeline; a green test suite says nothing about them | **absent** | `pyproject.toml:20` — `pytest` is the only detector |
| **R8** | Test-strength measurement | A test can execute a line without asserting it; "passing" is not "strong" | **absent** | no mutation or strength config anywhere; `pyproject.toml:20` again is the whole detector list |
| **R9** | Proof the target even type-checks at the pinned commit | If the mined revision does not compile, every capability claim about it is unqualified | **absent** | no type-check stage in `src/resextract/run.py:85-94`; both compilers present, never run (§2) |

## §2 What is installed today (measured 2026-10-23)

| component | version | what it gives us |
|---|---|---|
| **graphifyy** `[T1]` | 0.9.80, Apache-2.0 | tree-sitter parse → `graph.json`; a CLI surface largely unwired (§0) + `graphify-mcp` |
| bundled with it `[T2]` | tree-sitter 0.25.2 + 24 grammars · networkx 3.7 · graspologic-native 1.3.1 · tiktoken · pypdf · python-docx · openpyxl · markdownify · lxml · openai 3.26.1 | parse, Leiden/Louvain, PageRank (one call), token counting, doc/PDF/office readers |
| Python venv `[T6]` | 3.14.4 | runs `src/`; a cp314 wheel exists for `ast-grep-py` |
| node / npm / npx `[T6]` | v22.22.1 / 9.2.0 | the SCIP TypeScript indexer path, no install |
| cargo `[T5]` | 1.98.1 (797e8a9bc, 2026-08-05) | the target's Rust toolchain — `cargo check` without an install |
| rust-analyzer `[T4]` | 1.98.1 (48a229c, 2026-09-01) | `diagnostics`, `unresolved-references`, `scip`, `symbols` for `rust/crates` |
| target's own tsc `[T5]` | 5.9.3 at `/home/zer0null/Duval/node_modules/.bin/tsc` | type-check the TypeScript half in place |
| graph artifact `[T1]` | 2,685 nodes / 7,102 links, `built_at_commit=6deaed0…`, digest == `config/graph_pin.toml:52` | the thing every claim is checked against |

**Absent — no binary, no package, no plugin:** `rg` · `ast-grep`/`sg` · `semgrep` · `ctags` · `difftastic` · `pyright` · `basedpyright` · `ty` · `pyrefly` · `mypy` · `ruff` · `pylint` · `vulture` · `bandit` · `scip-*` · `multilspy` · `pygls`, and **no MCP client plugin is installed** (0 `mcp` hits in the DSH profile), so `graphify-mcp`'s ten tools are unreachable from any session.

## §3 Gap matrix

**The worst defect is symbol identity.** `verify_provenance` checks that an id exists in the graph (`mine/provenance.py:154`) and that a span fits inside the file (`:168`); nothing asks whether the id *is* the definition the claim names. A deliberately wrong symbol citation is therefore rejected **0/20** times by construction — and the fixture that measures it does not exist yet either.

| R# | defect class it causes today | fix | effort |
|---|---|---|---|
| **R2** | wrong symbol cited / right symbol, wrong definition site → docket passes verification | SCIP index + definition-range containment (§4 item 5) | M |
| **R3** | guessed `calls`/`imports` edges presented as evidence; ambiguous `path`/`explain` answers | offline SCIP index per pinned commit (§4 item 4) | M |
| **R4** | "this constant is used in 4 places" is uncheckable; only span existence is verified | `rg` wrapper + `doctor` leg (§4 item 7) | S |
| **R5** | pattern-shaped findings cannot be retrieved at all, so they are not attempted | `ast-grep-py` (§4 item 7) | S |
| **R6** | ~2% of the graph reaches the model, silently | PageRank under a token budget (§4 item 3) | S |
| **R7/R8** | undefined names, dead branches, unasserted lines ship; suite strength is unmeasured | `basedpyright` ratchet + `ruff` + `mutmut` + `hypothesis` (§4 item 9) | S–M |
| **R9** | "type-checks at `96c7687`" is assumed, so a broken revision yields confident claims | target's own compilers as a gate (§4 item 2) | S |

## §4 The plan — one ranked list

| # | P | change | why (mechanism) | effort | risk | how you'd know it worked | delivery form |
|---|---|---|---|---|---|---|---|
| **1** | P0 | **Rebuild + re-pin the KG to cover Rust** | Pin `6deaed0` predates `rust/` entirely: 0 `.rs` admitted, while `rust/crates` now holds 20,353 LOC / 37 first-party `.rs` and the target's HEAD `96c7687` is 916 commits ahead — every kernel-half claim is unprovable from the graph | M | **a rebuild invalidates the digest**: `_reuse_candidate` treats a mismatch as unusable (`config/graph_pin.toml:17-53`, `run.py:884-990`), so re-pin the full 64-hex in the same change | manifest gains the `.rs` files; reuse reports `digest_state=match`; `check-update` says current | code in `src/` + `config/graph_pin.toml` |
| **2** | P0 | **Target's own type-check gate** `[T5]` — `tsc --noEmit --incremental false`, `cargo check --offline`, `CARGO_TARGET_DIR` outside the target (never the 1.5 GB `rust/target`) | Answers a question the pipeline never asks and turns "verified at `96c7687`" into a recorded fact instead of an assumption; **if the gate fails, that failure is itself the finding** — every capability claim about the revision gains a caveat; zero installs, both compilers already in the target | S | `.tsbuildinfo` is a write; a cold `CARGO_TARGET_DIR` rebuild is slow; the target's `tsconfig.json` may pull in tests | exit status stored per commit and cited in every docket; break one type deliberately and watch the gate fail | external invocation, no install |
| **3** | P0 | **PageRank selection under a token budget** (`networkx` `[T2]`), replacing the insertion-order menu at `candidates.py:125-126` | Seed with the query's matched nodes, run `networkx.pagerank` over `graph.json`, dedupe by `file`, spend `QUERY_BUDGET` by rank — the aider *algorithm*, not the agent | S | rank without dedup spends the budget on near-duplicates | mean prompt tokens flat while the reachable-node fraction rises | code in `src/` |
| **4** | P0 | **SCIP offline index per pinned commit** `[T10]` under `state/scip/<slug>/`, TS first, `npx --no-install`, `--no-global-caches` | Compiler-grade occurrences as data — definition/reference ranges without a daemon, which is the batch-shaped answer to R3 | M | **unverified write footprint** inside the target (`*.tsbuildinfo`, `node_modules/.cache`) — the first §8 row decides adoptability | ≥90% of admitted files covered; unresolved-reference count printed per run, never swallowed | external binary, optional per-target step |
| **5** | P0 | **provenance v2: symbol identity** `[T10]` — `graph:<id>` must land in the named definition's range; `file#Lx-y` must be contained by one definition | Converts the existence check into an identity check, using (4) as the oracle | M | index lag versus graph pin — pin both to one commit; false rejects on generated code | ≥18/20 rejections on the §3 fixture, zero regressions on existing dockets | code in `src/` |
| **6** | P1 | **Enable the existing `update` `[T1]` after bounding the copy**, and wire `affected` + `check-update` | `_stage_repo_copy` takes the whole 166,314-file tree to re-index 5.39 MB of admitted material; `run.py:1768-1771` states that cost as the reason it is off, so bound the copy to the admitted set first, then enable | S+M | the refreshed graph lives in the staged copy and must be adopted back into `state/kg/` | refresh after a target commit stamps the new commit without copying the tree; `affected <symbol>` lists the re-mined candidates | code in `src/` |
| **7** | P1 | **`rg` `[T8]` + `ast-grep-py` `[T7]` with a `doctor` leg** | `doctor.py` legs are services only (`:286-477`), so a missing search tool is invisible until a unit needs one; closing R4/R5 at one wheel + one binary | S | `sg -U` rewrites in place — wrap search-only, pass `--globs`, never `cd` into the target | a known `$CALL` pattern returns spans; a literal claim re-verifies from the CLI | pip dependency + external binary |
| **8** | P1 | **Let docs into the KG** `[T1]` — 209 `docs/*.md` are admissible prose and 0 are in the graph | `run.py:1359` sets `code_only=True`; flipping it is not sufficient because the repo has 18,624 `.md` files, so admission must stay bounded by `config/targets.toml:14-52` | S+M | vendor prose floods the graph if the bound slips | manifest gains `docs/**/*.md`; a docket cites a heading that resolves through `doc_section` | code in `src/` |
| **9** | P1 | **Quality stack on our own Python** — `basedpyright` `[T11]` baseline ratchet over 52 files / 32,810 lines, `ty` `[T13]` alpha as trial only, `ruff` `[T16]`, `hypothesis` `[T17]`, `mutmut` `[T18]`, `vulture` `[T19]`, `import-linter` `[T20]`, `bandit` `[T21]` | Nothing type-checks or lints `src/` today; the gate must be non-increasing first, then ratcheted per module (`mine/` first — it is the honesty layer) | S–M | 32.8k lines produce an error wall; 3.14 syntax support unverified (§8); false positives on fixtures | error count at a pinned commit is stored and non-increasing; killed/total rises at equal test count | pip dependencies + `src/` config |
| **10** | P2 | **Measurement and artifact** — wire `coverage_audit` and `benchmark` `[T1]`, emit a markdown view per subsystem into `state/views/` | `coverage_audit` (`kg/ingest.py:8-10`) is uncalled, so silent file-type loss is invisible; `benchmark` is uncalled, so the graph's economic case is a claim; the `community` field already sits in every node line | S | a narrow corpus flatters `benchmark`; a hand-edited view drifts | graph stage reports admitted/dropped by type; dashboard shows graph-vs-corpus tokens per run; `state/views/<slug>/` regenerates deterministically | code in `src/` + generated artifacts |

**Order note.** 1 is first because every other item asserts against the graph; 2 and 6 are the two zero-install wins and can run in parallel; 4 gates 5 (no index, no identity check); 9 is independent of all of it and can start immediately.

## §5 Not adopting

| candidate | one-line reason |
|---|---|
| Graphiti `[T42]` | Conversation memory with validity intervals — a graph server plus an LLM call per episode to store facts the SQLite store already holds. Different domain. |
| Graft `[T47]` | `graft init` writes `graft/`, an `AGENTS.md` block and editor hooks **into the analysed repo** — fatal under the read-only rule; only its markdown-per-subsystem artifact shape is borrowed (§4.10). |
| `@local/dsh-plugin-graphify` `[T52]` | **WITHDRAWN by user 2026-10-23 as redundant with the installed CLI.** Original blockers: five outputs lack `output.schema`/`render` so `register()` throws (`packages/core/tools/src/index.ts:1071,1077`), and a local 7-line `dsh-tools` shim wins the import. Moot now. |
| GraphRAG / LightRAG family `[T43][T44]` | LLM pays to rediscover call edges tree-sitter resolves deterministically; GraphRAG's README says "largely in maintenance mode". |
| code-graph-rag / potpie / blarify `[T39][T40][T41]` | Same parse→graph→cluster pipeline, plus a database service `graph.json` does not need. |
| semgrep / Joern / CodeQL `[T28][T29][T30]` | Taint depth no claim here needs; CodeQL's CLI is under proprietary terms and its DB build is minutes-to-hours per commit. |
| zoekt / Sourcegraph / Sourcebot `[T32][T33][T34]` | Many-repo search *servers* for one TypeScript-dominant admitted set (§7 C4); Sourcegraph needs a licence key. Its "API 404" was a rate-limit label, not an observation (`CORRECTIONS.md` C5). |
| repomix / gitingest / code2prompt `[T35][T36][T37]` | They move token cost and destroy node identity, so `file:line` provenance cannot survive the round trip. |
| aider repo-map as a dependency `[T38]` | Installing an editing agent to obtain PageRank is backwards; the **algorithm** is adopted, `networkx` is installed. |
| Understand / Sourcetrail `[T48][T49]` | Paid proprietary; and Sourcetrail was archived 2021-12-13. |
| stack graphs `[T50]` | **Archived 2025-09-09** — still the most-recommended answer in older material and unusable. |
| lsproxy `[T51]` | Stale (last push 2025-08-08) and it bridges to an MCP client that is not installed. |
| `radon` `[T23]` | Stale since 2023-03-26, no `requires_python`. |
| `pylint` as a runtime dep `[T22]` | GPL-2.0-or-later — fine locally, never vendored; `ruff` covers most of it. |
| MCP-based LSP bridges `[T46][T27]` | No MCP client mounted, so nothing can call them; Serena also carries GPL-3.0-or-later. |
| tree-sitter CLI `[T3]` | The library is already linked; the CLI adds query-authoring convenience and a second ABI to keep in step. |
| ugrep `[T31]` | `rg` already wins; extra flags buy nothing for claim verification. |
| difftastic `[T9]` | **EVALUATE, not adopted now:** `ast_hash` is a whole-file MD5 (`graphify/detect.py:2217,2880`), so formatting-only commits already re-extract — a real gate, but the saving is confined to the admitted set. |

## §6 Invariants the choices must respect

- **The target is read-only.** No writes, no hooks, no editor config inside it; any git command against it passes `--no-optional-locks` (a bare `git status` refreshes `.git/index`, which is a write).
- **No writable state inside a target.** Graphs, indexes, views and copies live under `state/`; the refresh path already does this by construction (`copy_root = root / "repo"`, `refresh/review.py:521`).
- **`docs/PLAN.md:86` "No Node dependency" governs the *runtime*.** It is satisfied by pip Rust wheels (`ruff`, `ty`, `pyrefly`, `basedpyright` — the pyright family carries a Node runtime inside the wheel, no system install) and broken only by the SCIP/TS indexer path, which is an **optional per-target index step**, not a runtime dependency.
- **Nothing is written outside the workspace** — profile mounts, `cordis.patch.yml` rows and DSH restarts are user-approval items, not unit work.
- **The graph pin is re-pinned atomically with any rebuild** (`config/graph_pin.toml:17-53`): a digest mismatch makes the artifact unusable, so a rebuild that does not re-pin breaks the pipeline.
- **This is a batch pipeline.** No daemons, no servers, no per-query language server — that is why SCIP beats LSP here, and why "LSP as a service" is rejected wholesale.

## §7 What was corrected, and why it matters

Two corrections change the plan (C1 — the incremental path exists and is disabled, so item 6 got cheaper; C6 — the plugin never registered, and is now moot), and one is methodological: **a method-call grep cannot see a literal CLI argv**, so an inventory built on `grep '\.update('` reports "absent" for anything invoked as a process — which is exactly how G5 was born.

| C# | claim as first published | truth | effect on the plan |
|---|---|---|---|
| **C1** | incremental re-index is **absent** ("no `graphify update`/`watch` call exists in `src/`") | wired and disabled: `refresh/review.py:416` defines `_run_graphify_update`, `:431` builds `argv = ["stdbuf", …, "update", copy_dir]`, `:628` calls it, `:861` defaults `run_graph_update=True`; only `run.py:1781` passes `False` | item 6 changes **kind**: enable and bound, not build; the read-only rule is satisfied by construction (the update runs on a staged copy) |
| **C6** | plugin registration "unverified either way — a fallback may carry it" | fails as shipped: `register()` requires `output.render` as a function (`packages/core/tools/src/index.ts:1077`), the five blocks are bare JSON schemas (`lib/index.js:173,256,339,417,491`), and the package's own `node_modules/@deepseek-ai/dsh-tools` — a 7-line `0.0.0-shim` — is what the import resolves to | promotion was a code change before it was a config change; **moot** after the user withdrew the plugin |
| **C2** | "2 of 28 subcommands", ≈93% dark | 3 command families, not 2; the denominator is a help-text count of 27, not a spec of 28 (§0) | headline only; no verdict changes |
| **C3** | `context/budget.py` is "imported only by tests" | **no `src/` importer**; importers are `tests/test_context_append_note.py:43`, `experiments/context-cache/cells/U5/u5_cells.py:57`, `…/U14/u14_append_note_probe.py:49` | none — the point stands: the module named `budget` does not govern the live prompt; the live limits are `QUERY_BUDGET` and the menu caps |
| **C4** | "436-file Python target", the sizing premise of five verdicts | 227 admitted files, TypeScript-dominant (`.ts` 135 / `.json` 59 / `.mjs` 13 / `.py` 9 / `.sh` 8); 436 is reproducible nowhere | every sizing sentence cites 227; the tree-sitter-adequacy argument gets stronger, no verdict flips |
| **C5** | Sourcegraph "API 404 on 2026-10-23", presented as an observed fact | a fallback label applied after the unauthenticated GitHub API was rate-limited (403 territory), recorded as an observation in S2's own handoff | none — the REJECT rests on the enterprise licence key, which is separately sourced; the prose may not present a rate limit as an API fact |
| **C7** | S1's recorded `evidence.commands` produced the findings | they are BRE alternations without `-E`, so they matched nothing; the findings are right, the commands cannot have produced them | record hygiene: a later unit copying the array reads 0 hits as "claim no longer holds" |
| **C8** | `graphify_version` listed as a top-level key | it is nested at `graph.graphify_version`; top-level is `None` | a script written against the artifact would read `None` and conclude the field predates 0.9.80 |
| **C9** | the plugin had "two promotion blockers" | there was a third, and it is the first one a promotion hits (the definitions are not registry-ready — same mechanism as C6) | moot with C6, but an incomplete blocker list is what produced the "unverified either way" hedge |
| **C10** | rework backlog "driven from `refresh_target` [inference]" | measured at `refresh/review.py:945` — `entries = rework_entries(manifest, change, docket_links, now=now_dt)` | closes an open item; a rework backlog already maps changes to entries, it just lacks a mapping to a re-extraction command |
| **C11** | "just flip `run_graph_update` to True" | the disabling is deliberate and stated at `run.py:1768-1771` — a graph update copies the target into the workspace; the engine defaults **on** (`review.py:861`) precisely so a caller that can afford the copy gets it | item 6 must first bound the copy (5.39 MB, not 166,314 files); flipping the flag trades a disabled feature for a full-tree copy |

## §8 Open questions, each with the test that settles it

| question | test that settles it |
|---|---|
| Does `scip-typescript` keep **every write out of a read-only target**? **This decides adoptability.** | Stage a copy, run, diff mtimes; then one run against the target with an audit of touched paths (`--no-global-caches` is documented, `*.tsbuildinfo` and `node_modules/.cache` are not excluded). |
| Does the target type-check clean at `96c7687`? | One run of `tsc --noEmit --incremental false` and `cargo check --offline` with `CARGO_TARGET_DIR` outside, mtime sweep before/after, exit status recorded. **If it fails, that is the finding** — every claim about the revision gains a caveat. |
| Does ≈71.5× reproduce at 2,685 nodes? | `graphify benchmark` on `state/kg/duval`, read the two token figures. The ratio was recorded on a 26,555-node repo and should fall as the graph shrinks relative to the corpus. |
| Does bounding the copy keep `graphify update` semantically correct? | Bound `_stage_repo_copy` to the admitted set, run `update`, diff the resulting graph against a full-copy run at the same commit. |
| Do `basedpyright` / `ty` handle 3.14 syntax? | `pip download --no-deps` and read `Requires-Dist`; run `--pythonversion 3.14` on a file using 3.14-only syntax; `ty` 0.0.91 is alpha — revisit at 0.1, its README names 3.10 only. |
| Does `scip-python` 0.6.8 parse 3.14 (`.py` and `.pyi`)? | Index ten representative files and count parse failures — it wraps pyright's parser, so the PyPI `>=3.8` is the launcher, not the language. |
| What fraction of references resolve over the admitted set? (imports point outside it) | unresolved occurrences / total occurrences, printed in every run header; never silently dropped. |
| Do `docs/` enter the same graph or a second one? | Build both, compare `benchmark` cost per query plus cross-type edge counts. |
| Would symbol-identity checking catch the failures already shipped? | Sample 20 existing docket citations and re-check them by hand against an index. |
| Do already-emitted dockets rest on the stale pin? | List dockets whose material cites a node or line absent at `96c7687`; a non-empty list makes them `needs_rework`, not silently current. |
| Does `resextract serve` expose a graph/search endpoint? | Read `cli.py:134-180` and the dashboard routes; if it does, item 10's view is duplicative. |
| Do `rust-analyzer` / `cargo` write when loading `rust/crates`? | `CARGO_TARGET_DIR` outside + mtime sweep + `GIT_OPTIONAL_LOCKS=0`; a `Cargo.lock` refresh inside the target is a violation. |

## §9 Provenance

All versions, licences, upload dates and star counts are a **2026-10-23 snapshot** (PyPI JSON, GitHub REST API, npm registry — fetched that day in units S2 and S6); they will drift, and re-fetching them is the first step of any re-check. All paths are repo-relative except `/home/zer0null/Duval` (the read-only acceptance target). The verification record is `handoffs/V1.json`: **18 checks, 12 reproduced, 6 contradicted**; the contradictions are `CORRECTIONS.md` C1–C6, and C7–C11 add four record-accuracy fixes and one correction to C1's own first pass. Where this document and `CORRECTIONS.md` differ, `CORRECTIONS.md` wins.

**Re-check recipe:** re-read `01-inventory.md`, `02-candidates.md`, `03-lsp-code-error-rate.md`; re-run the commands in their provenance tables (they are `path:line` + shell commands, mostly `sed`/`grep`/`python -c` over `state/kg/duval/`); re-fetch every §10 link. The graph artifact's constants (digest, node count, `built_at_commit`) change on every rebuild — a rebuild makes item 1 *done*, not this document wrong.

## §10 Links & sources

`[T#]` markers in §2, §4 and §5 resolve here. Every row is the 2026-10-23 snapshot; **links rot** — re-fetching them is the first step of any re-check, exactly as with the versions in §9. `— (no URL captured in sources)` is a deliberate non-link, not an omission to be filled by guessing; a bare `—` in the package cell means the tool has no package page (a binary or a language runtime), and the repo link is the whole reference.

### Tools

| # | tool | version @ 2026-10-23 | licence | repo | package |
|---|---|---|---|---|---|
| T1 | **graphify** (`graphifyy`, `graphify`, `graphify-mcp`) | 0.9.80 | Apache-2.0 | [docs.graphify.com](https://docs.graphify.com) (no repo published) | [PyPI graphifyy](https://pypi.org/project/graphifyy/) |
| T2 | graphify's bundled deps: tree-sitter · networkx · graspologic-native · tiktoken · pypdf · python-docx · openpyxl · markdownify · lxml · openai | 0.25.2 · 3.7 · 1.3.1 · — · — · — · — · — · — · 3.26.1 | per package | [tree-sitter](https://github.com/tree-sitter/tree-sitter) | [PyPI tree-sitter](https://pypi.org/project/tree-sitter/) |
| T3 | tree-sitter CLI | 0.27.1 | MIT | [tree-sitter](https://github.com/tree-sitter/tree-sitter) | [PyPI tree-sitter](https://pypi.org/project/tree-sitter/) |
| T4 | rust-analyzer | 1.98.1 (48a229c, 2026-09-01) | MIT / Apache-2.0 | [rust-lang/rust-analyzer](https://github.com/rust-lang/rust-analyzer) | — |
| T5 | target's own compilers: `tsc` / `cargo` | 5.9.3 / 1.98.1 | Apache-2.0 / MIT | [microsoft/TypeScript](https://github.com/microsoft/TypeScript) · [rust-lang/cargo](https://github.com/rust-lang/cargo) | — |
| T6 | Python · node · npm · npx | 3.14.4 · v22.22.1 · 9.2.0 | PSF-2.0 · MIT | [python.org](https://www.python.org) · [nodejs.org](https://nodejs.org) | — |
| T7 | ast-grep (`sg`) / **ast-grep-py** | 0.51.0 | MIT | [ast-grep](https://github.com/ast-grep/ast-grep) · [docs](https://ast-grep.github.io/) | [PyPI ast-grep-py](https://pypi.org/project/ast-grep-py/) |
| T8 | ripgrep | 15.2.0 | Unlicense | [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | — |
| T9 | difftastic | 0.71.0 | MIT | [Wilfred/difftastic](https://github.com/Wilfred/difftastic) | — |
| T10 | SCIP indexers: `scip-typescript` · `scip-python`; format | 0.5.2 · 0.6.8 · — | Apache-2.0 · MIT · Apache-2.0 | [sourcegraph/scip-typescript](https://github.com/sourcegraph/scip-typescript) · [sourcegraph/scip-python](https://github.com/sourcegraph/scip-python) · [scip-code/scip](https://github.com/scip-code/scip) | — |
| T11 | **basedpyright** | 1.40.2 | NOASSERTION (MIT-style) | [detachhead/basedpyright](https://github.com/detachhead/basedpyright) | [PyPI basedpyright](https://pypi.org/project/basedpyright/) |
| T12 | pyright (PyPI wrapper `pyright`) | 1.1.414 | MIT | [pyright-python wrapper](https://github.com/RobertCraigie/pyright-python) · [microsoft/pyright](https://github.com/microsoft/pyright) | [PyPI pyright](https://pypi.org/project/pyright/) |
| T13 | **ty** | 0.0.91 (alpha) | MIT | [astral-sh/ty](https://github.com/astral-sh/ty) | [PyPI ty](https://pypi.org/project/ty/) |
| T14 | pyrefly | 1.4.0 | MIT | [facebook/pyrefly](https://github.com/facebook/pyrefly) · [site](https://pyrefly.org) | [PyPI pyrefly](https://pypi.org/project/pyrefly/) |
| T15 | mypy | 2.4.0 | MIT | [mypy docs](https://mypy.readthedocs.io/en/stable/index.html) | [PyPI mypy](https://pypi.org/project/mypy/) |
| T16 | **ruff** | 0.17.2 | MIT | [docs.astral.sh/ruff](https://docs.astral.sh/ruff/) | [PyPI ruff](https://pypi.org/project/ruff/) |
| T17 | **hypothesis** | 6.170.8 | MPL-2.0 | [hypothesis docs](https://hypothesis.readthedocs.io) | [PyPI hypothesis](https://pypi.org/project/hypothesis/) |
| T18 | **mutmut** | 3.8.0 | BSD-3-Clause | [mutmut docs](https://mutmut.readthedocs.io/en/latest/) | [PyPI mutmut](https://pypi.org/project/mutmut/) |
| T19 | **vulture** | 2.16 | MIT | [jendrikseipp/vulture](https://github.com/jendrikseipp/vulture) | [PyPI vulture](https://pypi.org/project/vulture/) |
| T20 | **import-linter** | 2.15 | BSD-2-Clause | [import-linter docs](https://import-linter.readthedocs.io/) | [PyPI import-linter](https://pypi.org/project/import-linter/) |
| T21 | **bandit** | 1.9.4 | Apache-2.0 | [bandit docs](https://bandit.readthedocs.io/) | [PyPI bandit](https://pypi.org/project/bandit/) |
| T22 | pylint | 4.1.3 | GPL-2.0-or-later | [pylint-dev/pylint](https://github.com/pylint-dev/pylint) | [PyPI pylint](https://pypi.org/project/pylint/) |
| T23 | radon | 6.0.1 (2023-03-26, stale) | MIT | [radon docs](https://radon.readthedocs.org/) | [PyPI radon](https://pypi.org/project/radon/) |
| T24 | ctags (Universal Ctags) | not installed | GPL-2.0 | [universal-ctags/ctags](https://github.com/universal-ctags/ctags) | — |
| T25 | multilspy | 0.1.1 | MIT | [microsoft/multilspy](https://github.com/microsoft/multilspy) | [PyPI multilspy](https://pypi.org/project/multilspy/) |
| T26 | pygls · lsprotocol | 2.1.1 · 2025.0.0 | Apache-2.0 | [openlawlibrary/pygls](https://github.com/openlawlibrary/pygls) · [microsoft/lsprotocol](https://github.com/microsoft/lsprotocol) | [PyPI pygls](https://pypi.org/project/pygls/) |
| T27 | Serena | 2.1.0 | GPL-3.0-or-later app, MIT SolidLSP | [oraios/serena](https://github.com/oraios/serena) | — |
| T28 | semgrep | 1.182.0 | LGPL-2.1 engine; registry/platform separate | [semgrep/semgrep](https://github.com/semgrep/semgrep) | [licensing](https://semgrep.dev/docs/licensing) |
| T29 | Joern | 4.0.664 | Apache-2.0 | [joernio/joern](https://github.com/joernio/joern) | — |
| T30 | CodeQL | CLI releases | queries MIT; **CLI under GitHub CodeQL Terms** | [github/codeql](https://github.com/github/codeql) | [CLI licence](https://github.com/github/codeql-cli-binaries/blob/main/LICENSE.md) |
| T31 | ugrep | 7.8.5 | BSD-3-Clause | [Genivia/ugrep](https://github.com/Genivia/ugrep) | — |
| T32 | zoekt | no release object | Apache-2.0 | [sourcegraph/zoekt](https://github.com/sourcegraph/zoekt) | — |
| T33 | Sourcegraph | enterprise | proprietary licence key | [sourcegraph/sourcegraph](https://github.com/sourcegraph/sourcegraph) — unconfirmed, API rate-limited (C5) | [licensing](https://sourcegraph.com/docs/admin/licensing) |
| T34 | Sourcebot | v6.0.3 | MIT | [sourcebot-dev/sourcebot](https://github.com/sourcebot-dev/sourcebot) | — |
| T35 | repomix | v1.18.1 | MIT | [yamadashy/repomix](https://github.com/yamadashy/repomix) | — |
| T36 | gitingest | no release object | MIT | [coderamp-labs/gitingest](https://github.com/coderamp-labs/gitingest) | — |
| T37 | code2prompt | v4.2.0 (2025-12-11) | MIT | [mufeedvh/code2prompt](https://github.com/mufeedvh/code2prompt) | — |
| T38 | aider / repo-map | v0.86.0 | Apache-2.0 | [Aider-AI/aider](https://github.com/Aider-AI/aider) | [repo-map docs](https://aider.chat/docs/repomap.html) |
| T39 | code-graph-rag | v0.2.19 | MIT | [vitali87/code-graph-rag](https://github.com/vitali87/code-graph-rag) | — |
| T40 | potpie | v2.0.1 | Apache-2.0 | [potpie-ai/potpie](https://github.com/potpie-ai/potpie) | — |
| T41 | blarify | no releases | MIT | [blarApp/blarify](https://github.com/blarApp/blarify) | — |
| T42 | Graphiti | v0.31.2 | Apache-2.0 | [getzep/graphiti](https://github.com/getzep/graphiti) | — |
| T43 | GraphRAG | v3.3.0 | MIT | [microsoft/graphrag](https://github.com/microsoft/graphrag) | — |
| T44 | LightRAG · fast-graphrag · nano-graphrag | v1.5.7 · — · — | MIT | [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) · [circlemind-ai/fast-graphrag](https://github.com/circlemind-ai/fast-graphrag) · [gusye1234/nano-graphrag](https://github.com/gusye1234/nano-graphrag) | — |
| T45 | typescript-language-server | 6.0.2 | MIT | [typescript-language-server](https://github.com/typescript-language-server/typescript-language-server) | — |
| T46 | mcp-language-server | pushed 2026-03-01 | BSD-3-Clause | [isaacphi/mcp-language-server](https://github.com/isaacphi/mcp-language-server) | — |
| T47 | Graft (Trail-Code code map) | 0.24.1 | MIT | [trailhq/Trail-Code](https://github.com/trailhq/Trail-Code) | [npm @nanonets/graft](https://www.npmjs.com/package/@nanonets/graft) |
| T48 | Understand (SciTools) | commercial | proprietary | [scitools.com](https://scitools.com/) | — |
| T49 | Sourcetrail | archived 2021-12-13 | GPL-3.0 | [CoatiSoftware/Sourcetrail](https://github.com/CoatiSoftware/Sourcetrail) | — |
| T50 | stack graphs (`tree-sitter-stack-graphs`) | **archived 2025-09-09** | Apache-2.0 | [github/stack-graphs](https://github.com/github/stack-graphs) (archive banner) | — |
| T51 | lsproxy | last push 2025-08-08 | MIT | [agentic-labs/lsproxy](https://github.com/agentic-labs/lsproxy) | — |
| T52 | `@local/dsh-plugin-graphify` | 0.1.0, withdrawn 2026-10-23 | local package | `/home/zer0null/Desktop/deepseek agent harness testing/scratch-graphify/dsh-plugin-graphify/package/` | — |
| T53 | environment essentials named in §1/§6 (`pytest`, `git`, `stdbuf`) | — | — (no URL captured in sources) | — (no URL captured in sources) | — |

### Literature & specs

| item | why it matters here | link |
|---|---|---|
| LSP specification | the protocol a live-server design would implement; we consume indexes instead | [microsoft.github.io/language-server-protocol](https://microsoft.github.io/language-server-protocol/) |
| SCIP | the index format item 4 emits and item 5 checks against | [scip-code/scip](https://github.com/scip-code/scip) |
| MGD / `multilspy` (NeurIPS 2023) | the "absence of hallucinated symbol names" monitor — the technique behind R2/R3, measured on generation tasks, not batch pipelines | [arXiv:2306.10763](https://arxiv.org/abs/2306.10763) |
| LSPRAG | reported line-coverage gains **+174.55% Go, +213.31% Java, +31.57% Python** — the Python figure is the weakest, which weakens an "LSP will fix our claims" argument. ACM/IEEE entry: **— (unverified)**, only the arXiv record was captured | [arXiv:2510.22210](https://arxiv.org/abs/2510.22210) |
| tree-sitter | the parser under graphify and ast-grep; pins the ABI (`>=0.25,<0.26`) a second toolchain must match | [tree-sitter](https://github.com/tree-sitter/tree-sitter) |
| Aider's repo-map | the PageRank seeding idea adopted in item 3, not the dependency | [aider.chat/docs/repomap](https://aider.chat/docs/repomap.html) |
| graphify project page | the canonical doc host for the installed wheel | [docs.graphify.com](https://docs.graphify.com) |
