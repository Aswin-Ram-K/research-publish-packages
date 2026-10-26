# 03 · LSP, SCIP and code-quality tooling against two error rates

**Unit:** S6 (web research) · **Date:** 2026-10-23 · **Repo:** `/home/zer0null/reserach extarctor`
**Scope:** research only — no product code, no installs, no target writes. Every version/licence below is a **2026-10-23 snapshot** (§8).
**Inputs:** `01-inventory.md` G3/G4 (no trusted cross-file resolution); `mine/provenance.py` (existence checks); `FINDINGS.md` §3/§4c (plugin now **withdrawn**); `CORRECTIONS.md`.

## §0 Answer in five lines

1. **LSP is the right technique; a live server is the wrong shape.** For a batch pipeline the cheap, deterministic form is an **offline index (SCIP)** built per pinned commit and queried as data — no daemon, no socket, no server lifecycle.
2. **(a) Errors in claims about the target** are *symbol-identity* errors: a citation verifies because its id exists, not because it is the intended definition. An index answers "what is declared at this line / referenced at this one" exactly; a language server answers it too, at seconds-per-query.
3. **(b) Errors in our own Python** are not a retrieval problem — better context cannot find an undefined name. Type checking (starting with the target's own `tsc`/`cargo`), mutation testing and property tests move this number; retrieval does not.
4. **Default gate for (b): `basedpyright`** 1.40.2 (mature, strict, Node-backed wheel) with a committed baseline ratchet; `ty` 0.0.91 is **alpha** — trial only; `pyrefly`/`mypy` are alternates.
5. **The trap to avoid is stack graphs** (`github/stack-graphs` **archived 2025-09-09**) — still the most-recommended answer in older posts and unusable.

## §1 Two different error rates

Conflating them is why this conversation circles: they have different detectors, different fixes, different metrics.

| | **(a) a claim about target code is wrong** | **(b) our Python is wrong** |
|---|---|---|
| failure shape | wrong symbol cited; right symbol, wrong definition site; inference stated that the code does not support | crash on an input shape; wrong dedup key; silent `None`; a branch no test asserts |
| today's detector | `verify_provenance` → `_check_graph_node` (`provenance.py:154`, id present in graph) + `_check_file_lines` (`:168`, span fits the file) | `pytest` only (`pyproject.toml:20`) — no type checker, no linter, no mutation score in the repo |
| blind spot | **identity** and **support**: a same-named definition elsewhere, or a line that exists but says something else, both pass | a test can execute a line without asserting it; the suite's *strength* is unmeasured |
| fix family | SCIP index; LSP definition/references/hover; `rust-analyzer` for the Rust half | type checker, mutation testing, property tests, lint, import contracts |
| metric | % of adversarial wrong-symbol citations rejected (today **0/20 by construction** — only existence is checked) | diagnostics at a pinned commit; mutmut killed/total; hypothesis falsifying examples |
| where | `mine/` → `context/` → docket | all of `src/resextract/` (**52 files / 32,810 lines**, measured) |

## §2 LSP and indexes for (a)

| option | version · licence · activity | mechanism | cost / precondition here | verdict |
|---|---|---|---|---|
| **SCIP indexers** — `@sourcegraph/scip-typescript`, `@sourcegraph/scip-python` | 0.5.2 Apache-2.0 (2026-10-22) · 0.6.8 MIT (2026-10-22); format repo `scip-code/scip` 835★, active 2026-10-22 | compiler-grade indexer emits **occurrences** (symbol, byte range, `definition`/`reference`/`implementation` role) + symbol monikers; one `index.scip` per commit; query offline | `npx` (node v22.22.1 ✓); TS indexer must run **from a project root that has `tsconfig.json` and installed deps** — Duval has both `tsconfig.json` and `node_modules/`, but that is a per-target precondition, not a universal one. README flags `--no-global-caches` because it maintains global caches | **P0** — the batch-shaped answer; adoptability hinges on §7.1 |
| **`multilspy`** | 0.1.1 MIT, 613★, active 2026-10-13/15 (`microsoft/multilspy`) | spawns real servers (pyright / rust-analyzer / `typescript-language-server` 6.0.2) over stdio; requests definition, references, hover, document symbols, **diagnostics** | one server process + project load per session (seconds, hundreds of MB); rust-analyzer wants a cargo project it can load | **P1** — right for "explain this symbol" in a session, wrong for a 227-file sweep |
| **`rust-analyzer` CLI** | **1.98.1 (48a229c, 2026-09-01)** — installed at `~/.local/bin/rust-analyzer` | subcommands `diagnostics`, `unresolved-references`, `scip`, `analysis-stats`, `symbols` (verified via `--help`) | none new; needs a loadable cargo project | **P0 for the Rust half** — usable today, no Python client |
| **`pygls` / `lsprotocol`** | 2.1.1 Apache-2.0 · 2025.0.0 | framework and types to *write* a server | weeks of work to re-implement what an indexer emits | **no** — we consume, we do not serve |
| **stack graphs** (`tree-sitter-stack-graphs`) | `github/stack-graphs` **ARCHIVED 2025-09-09**, 875★, Apache-2.0 | incremental name-resolution graphs over tree-sitter | dead upstream, no maintainer, no SCIP output | **reject — the trap** |
| **MCP bridges** — `mcp-language-server` 1,611★ BSD-3 (pushed 2026-03-01), `lsproxy` 108★ MIT (**pushed 2025-08-08, stale**), `serena` 30,637★ (GPL-3.0-or-later app + MIT SolidLSP) | agent-facing wrappers | require a mounted MCP client; **none is installed** | unreachable today; `lsproxy` also stale | **reject / defer** (`serena` already EVALUATE in `02-candidates.md`) |

**What it buys, concretely.** `graphify` matches *labels*, so `main()` resolves to both the file node `main` and the function `main_main` — recorded at `kg/graphify.py:29-30`. A claim carrying `graph:<id>` passes provenance because the id exists; nothing asks whether that id *is* the definition the claim names. With an index the check becomes mechanical:

- `graph:<id>` → read the node's `loc`, ask the index which symbol's definition range contains that line; reject when the symbol ≠ the one the claim names.
- `file#Lx-y` → require the span to contain (or be contained by) one definition, and record which symbol.
- asserted `calls` edge → require an index `reference` occurrence in the caller's body.

Two honest limits: the index only covers **admitted files** (227 of 166,314 — imports point outside the set), so unresolved references must be **counted and reported**, not silently dropped; and an index is only as fresh as its commit, so it must be pinned to the same commit as the graph (`config/graph_pin.toml:52`).

**The literature, as literature.** `multilspy` exists to run the monitor from *Guiding Language Models of Code with Global Context using Monitors* (NeurIPS 2023, [arXiv:2306.10763](https://arxiv.org/abs/2306.10763)) — static analysis that enforces "type-consistent object dereferences" and "absence of hallucinated symbol names". LSPRAG ([arXiv:2510.22210](https://arxiv.org/abs/2510.22210)) reports line-coverage gains over the best baseline of **+174.55% Go, +213.31% Java, +31.57% Python**. Both are external claims about *generation* tasks with their own threat models; neither measures a batch provenance pipeline. The Python number is the smallest, and it is the one closest to our work.

## §3 LSP and checkers for (b), and the Rust half

`rust-analyzer` 1.98.1 is **already installed** — for `/home/zer0null/Duval/rust/crates` it can answer diagnostics and unresolved references with no purchase, subject to §7.4 (a cargo load may want to write `Cargo.lock`/`target/`; point `CARGO_TARGET_DIR` outside the target and treat any write as a violation).

| checker | version · licence · upload | engine | 3.14 language support | verdict |
|---|---|---|---|---|
| **basedpyright** | 1.40.2 · NOASSERTION on PyPI (MIT-style fork of pyright — cite the repo, not an OSI label) · 2026-10-04 · `DetachHead/basedpyright` 3,632★ | TypeScript, Node-backed wheel | runs on 3.14; **language-level 3.14 checking not independently verified** (§7.6) | **default** — mature, strict-by-config, JSON diagnostics, per-file severity overrides |
| `pyright` | 1.1.414 · MIT · 2026-09-10 | same engine | same | fallback if basedpyright's fork lags |
| `ty` | 0.0.91 · MIT · 2026-10-22 · `astral-sh/ty` 19,913★ | Rust | **alpha 0.0.x**; README names 3.10, makes **no 3.14 claim** | **trial only** (watch mode); not a CI gate |
| `pyrefly` | 1.4.0 · MIT · 2026-10-15 · `facebook/pyrefly` 7,128★ | Rust | unverified | EVALUATE — young, fast |
| `mypy` | 2.4.0 · MIT · 2026-10-01 | Python | plugin ecosystem, slowest | fallback when a plugin is required |

**Recommendation.** Default `basedpyright` at `standard` severity with a **committed baseline** (`state/quality/…`): the first run over 32.8k lines will produce an error wall, so the gate is *non-increasing*, then a per-module budget ratcheted to zero (`mine/` first — it is the honesty layer). Keep `mypy` as the plugin fallback; trial `ty` in `--watch` for the fast loop; `pyrefly` stays EVALUATE.

**On `docs/PLAN.md:86` ("No Node dependency").** `ruff`, `ty`, `pyrefly` and `mypy` are Node-free (Rust or pure Python). `pyright`/`basedpyright` are TypeScript servers shipped as wheels that carry or bootstrap a Node runtime — no **system** Node is needed, and node v22.22.1 is present anyway. If line 86 is read strictly as "no JS runtime at all", it is false for these two; as "no system Node install", it holds. Reword rather than assume.

## §4 The non-LSP levers that actually move our defect rate

**Cheapest signal first: ask the target's own toolchain whether the code type-checks at the pinned commit.** `/home/zer0null/Duval` ships its own compilers — `cargo 1.98.1 (797e8a9bc 2026-08-05)` with a workspace manifest at `rust/Cargo.toml` (`crates/core-state`, `core-journal`, `core-protocol`, `substrate-core`, `substrated`) and a **1.5 GB prebuilt `rust/target`**, plus `node_modules/.bin/tsc` = **TypeScript 5.9.3**. Zero installs, zero daemon, no new dependency, and it answers a question the pipeline never asks: *does the code we mine even type-check at this revision?* If it fails, every capability claim about that commit carries a "does not type-check at this revision" caveat instead of silently becoming a finding. Read-only discipline is the whole precondition: `CARGO_TARGET_DIR` pointed **outside** the target (never `rust/target`) with `--offline`; `tsc --noEmit --incremental false` (`.tsbuildinfo` is a write); cwd at the target, every output redirected. Run it per commit as a gate — the Rust side may rebuild from the cargo registry cache, so it is periodic, not per-claim, and the result gives the docket a real "verified at `96c7687`" line.

| tool | version · licence · upload | catches | where | effort | caveat |
|---|---|---|---|---|---|
| **target's own compilers** (`tsc --noEmit`, `cargo check`) | TS **5.9.3** at `node_modules/.bin/tsc`; `cargo 1.98.1`; no install | the mined revision does not type-check — invalidates capability claims wholesale | `/home/zer0null/Duval` (read-only) | S | redirect every output; `--incremental false`; `CARGO_TARGET_DIR` outside + `--offline`; periodic gate, not per-claim |
| **ruff** | 0.17.2 · MIT · 2026-10-22 | `F` undefined/unused names, `E9` syntax, `B` bugbear, `I` import order; formatter | `src/` | S | select rules first; a whole-repo `format` is a large orthogonal diff |
| **type checker** (§3) | — | wrong arity, `None` flow, bad attribute, dead branches | `src/` | S–M | baseline first, or the gate is noise |
| **hypothesis** | 6.170.8 · MPL-2.0 · 2026-10-22 | falsifying inputs for `parse_ref`/`_SPAN_RE`, manifest and graph JSON shapes, dedup keys | `mine/`, `kg/` | M | `>=3.11` is the *interpreter* requirement, not a language-support claim |
| **mutmut** | 3.8.0 · BSD-3-Clause · 2026-09-12 | **test strength**: mutants that survive a green suite | `kg/`, `mine/` | M | slow; start with one module; score = killed / (killed+survived+timeout) |
| **vulture** | 2.16 · MIT · 2026-03-25 | dead functions, unused attributes | `src/` | S | false positives on pytest fixtures/dynamic dispatch — whitelist, never auto-delete |
| **import-linter** | 2.15 · BSD-2-Clause · 2026-09-04 | layering violations among `kg`/`mine`/`context`/`refresh`/`docket` | `pyproject.toml` contract | S | run once first: the true dependency direction, not the assumed one, goes in the contract |
| **bandit** | 1.9.4 · Apache-2.0 · 2026-02-25 | `subprocess` with `shell=True`, injection, hardcoded secrets — and this tool shells out a lot (`stdbuf`, `graphify`) | `src/` | S | noisy on tests; scan `src/` only |
| `pylint` | 4.1.3 · **GPL-2.0-or-later** · 2026-10-11 | overlap with ruff, slower | — | — | **copyleft**: fine as a local dev tool, never vendored into the product |
| `radon` | 6.0.1 · MIT · **2023-03-26 (stale)**, no `requires_python` | cyclomatic complexity | — | — | **skip** — three years unmaintained |

## §5 Ranked adoption

| # | P | change | effort | risk | how you would know it worked |
|---|---|---|---|---|---|
| 1 | **P0** | **Type-check gate at the pinned commit**, using the target's own `cargo check` / `tsc --noEmit` — no install | S | cargo `--offline` needs a warm registry cache; a cold `CARGO_TARGET_DIR` rebuild is slow; the target's `tsconfig.json` may include test files and inflate failures | exit status recorded per commit and cited in every docket; break one type deliberately and watch the gate fail (red→green) |
| 2 | **P0** | **SCIP index per pinned commit**, under `state/scip/<slug>/`, TS first then Python; `npx --no-install` or a pinned local install, `--no-global-caches`, output outside the target | M | TS indexer needs a buildable root (`tsconfig.json` + `node_modules` — present for Duval, not universal); caches may still land in `node_modules/.cache` or `tsconfig.tsbuildinfo` **inside** the target; verify by mtime sweep (§7.1) | index covers ≥90% of admitted files; unresolved-reference count reported per run, not swallowed |
| 3 | **P0** | **provenance v2: symbol identity**, using (2) for `graph:` refs and definition ranges for `file#Lx-y` | M | index lag vs graph pin → pin both to one commit; false rejects on generated/vendored code | **inject 20 deliberately wrong symbol citations** into a fixture docket and count rejections: today **0/20** (existence only); target **≥18/20**, with 0 regressions on the existing docket set |
| 4 | **P0** | **`basedpyright` baseline ratchet** on `src/` in CI | S–M | 32.8k-line first run is an error wall; 3.14 syntax support unverified | error count at a pinned commit is stored and **non-increasing**; `mine/` at zero within N runs |
| 5 | **P1** | **`ruff check` (F, E9, B, I)**, check-only, no reformat | S | rule noise in tests | zero findings on changed files; `F821` (undefined name) class reaches zero |
| 6 | **P1** | **hypothesis invariants** for `parse_ref`, span regex, manifest/graph loading, dedup keys | M | slow CI if the example budget is high | 10⁵ examples, zero falsifying; every historical bug shape has a named property |
| 7 | **P1** | **mutmut baseline** on `kg/`, then `mine/` | M | runtime; mutmut config friction | killed/total rises at equal test count — i.e. tests were added *or strengthened*, not merely more numerous |
| 8 | **P1** | **`rust-analyzer diagnostics` / `unresolved-references`** on `rust/crates` | S | cargo load may write into the target (§7.4) | diagnostics reproducible with target mtimes unchanged |
| 9 | **P2** | `multilspy` "explain symbol" tool for interactive sessions | M | server lifecycle per session | definition + hover answers on the 20-case fixture, no writes into the target |
| 10 | **P2** | import-linter contracts, vulture whitelist, bandit on `src/` | S each | false positives | contracts fail on a deliberate forbidden import (red→green) |

## §6 What NOT to adopt

- **Stack graphs** — `github/stack-graphs` archived 2025-09-09; `tree-sitter-stack-graphs` inherits the dead upstream. Every older blog post recommending it is stale.
- **`lsproxy`** — last push 2025-08-08, 108★; stale, and it is a bridge to an MCP client we do not have.
- **Writing our own LSP server** (`pygls`/`lsprotocol`) — months to reproduce what `scip-python` and `rust-analyzer scip` emit.
- **MCP-based LSP bridges** (`mcp-language-server`, `serena`) — no MCP client is mounted; `serena` also carries GPL-3.0-or-later.
- **`radon`** — stale since 2023-03-26.
- **`pylint` as a runtime dependency** — GPL-2.0-or-later; use it locally at most, and ruff covers most of it.
- **Any "LSP as a service"** — Sourcegraph-class index servers, a per-query daemon, or a container per language, for a 227-file read-only batch.
- **Running `scip-typescript` from inside the target** without proving every write is redirected — a cache file written under `/home/zer0null/Duval` is the Graft failure mode again.

## §7 Open questions (with the test that settles each)

1. **Does `scip-typescript` keep every write out of a read-only target?** README documents `--no-global-caches` and an index output path; TypeScript can still emit `*.tsbuildinfo`/`node_modules/.cache`. *Settles by:* stage a copy, run, diff mtimes; then one run against the target with an audit of touched paths. **This decides whether SCIP is adoptable at all.**
2. **Does `scip-python` 0.6.8 parse Python 3.14** (`.py` + `.pyi`)? It wraps pyright's parser; PyPI's `>=3.8` is the launcher, not the checked language. *Settles by:* index 10 representative files and count parse failures.
3. **What fraction of references resolve over the 227-file admitted set** (imports point outside)? *Settles by:* unresolved-reference count / total occurrences; report it in every run header.
4. **Does `rust-analyzer` write when loading `rust/crates`?** `cargo metadata` may create/refresh `Cargo.lock`, proc-macros may build. *Settles by:* `CARGO_TARGET_DIR` outside + mtime sweep + `GIT_OPTIONAL_LOCKS=0`.
5. **Is `ty` alpha acceptable for CI?** No — 0.0.91; *settles by:* revisit at 0.1 and re-check the 3.14 claim (README names 3.10 only).
6. **Does `basedpyright` check 3.14 *syntax*, and does its wheel vendor Node?** *Settles by:* `pip download --no-deps` and inspect `Requires-Dist`; run `--pythonversion 3.14` on a file using 3.14-only syntax.
7. **Would symbol-identity checking catch the failures we already shipped?** *Settles by:* sample 20 existing docket citations and re-check them by hand against an index.
8. **Does the target's own toolchain type-check cleanly at the pinned commit, read-only?** `cargo check --offline` needs a populated registry cache; `tsc --noEmit --incremental false` must emit no `.tsbuildinfo`; `CARGO_TARGET_DIR` may not point at `rust/target`. *Settles by:* one run at `96c7687` with an mtime sweep before/after and the exit status recorded. If it fails, that **is** the finding: every claim about that revision gains a caveat.

## §8 Provenance

**Snapshot date: 2026-10-23.** Versions, licences, upload dates and star counts are a one-day snapshot and will drift; re-fetch before citing.

| what | how it was obtained |
|---|---|
| PyPI metadata (version · licence · upload · `requires_python`) | `curl -s https://pypi.org/pypi/<pkg>/json` → `.info.{version,license,requires_python}` + `.releases[...]` upload times |
| GitHub metadata (stars · archived · `pushed_at` · licence) | `curl -s https://api.github.com/repos/<owner>/<repo>` |
| npm metadata | `curl -s https://registry.npmjs.org/<pkg>` → `dist-tags.latest`, `time` |
| local toolchain | `python -V` (3.14.4); `node -v` (v22.22.1); `npm -v` (9.2.0); `rust-analyzer --version` (**1.98.1, 48a229c, 2026-09-01**) and `--help` subcommands — run in this session |
| `src/` size | `find src/resextract -name '*.py' \| wc -l` → 52; `cat`-sum → 32,810 lines (this session) |
| target's own toolchain | `cargo --version` → **1.98.1 (797e8a9bc 2026-08-05)**; `/home/zer0null/Duval/node_modules/.bin/tsc --version` → **5.9.3**; `/home/zer0null/Duval/rust/Cargo.toml` workspace = `core-state`, `core-journal`, `core-protocol`, `substrate-core`, `substrated`; `rust/target` = **1.5 GB** — read in this session, nothing executed inside the target |
| `docs/PLAN.md:86` | read: "No Node dependency" |
| paper claims | [arXiv:2306.10763](https://arxiv.org/abs/2306.10763) abstract (fetched 2026-10-23); [arXiv:2510.22210](https://arxiv.org/abs/2510.22210) abstract (fetched 2026-10-23) |

**Correction to the brief I was given:** LSPRAG's reported gains are **Go +174.55%, Java +213.31%, Python +31.57%** — the 213.31% figure belongs to Java, not Python. Python is the weakest result, which weakens, not strengthens, an "LSP will fix our claims" argument.

**Not verified here:** the SCIP indexers were never run (installing them would have broken the no-install rule); `ty`/`basedpyright`/`pyrefly`/`mypy` were never run against `src/`; `rust-analyzer` was exercised only for `--version`/`--help`; the target's `cargo check`/`tsc --noEmit` were **not** run — only their `--version` — so "type-checks at `96c7687`" is open (§7.8); LSPRAG and MGD numbers are abstracts, not replications. The only new measurements are the toolchain versions, the 52-file/32,810-line count, and the workspace/target inventory.

**Version/licence block above is a 2026-10-23 snapshot supplied to and spot-checked by this unit; treat every row as dated.**
