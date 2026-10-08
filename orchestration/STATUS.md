# Orchestration status — Research Extractor

**Spec of record:** [`docs/PLAN.md`](../docs/PLAN.md) (308 lines, §0–§11; md5 `7c4aac1199d530a3172cfa55c9a042d1`, 29875 bytes, 12 `##` headings — byte-identical to the approved plan, V0 check 1).
**Legend — the three main-session rules:** (1) **delegation only** — the main session composes prompts, launches units, collects handoffs and reports; it never writes a file, runs a command, or reads source; (2) **units persist their own cards** to `orchestration/units/<UNIT>.md` and their verdict to `orchestration/handoffs/<UNIT>.json`; (3) **every batch needs an independent verifier** — never the unit that authored the work.

Status vocabulary: `pending` · `in_progress` · `done` · `failed` · `partial` · `superseded`.
**The status column below is rebuilt from what `orchestration/handoffs/*.json` actually say, not from the
plan's intent.** Where a unit failed and a fresh unit recovered or superseded it, both rows are kept.
`running` means "launched, no handoff on disk yet" — that is a statement about evidence, not about health.

## Coupling & licensing note (read before the table)

Since the Batch-0 checkpoint, four units were launched concurrently inside one
write-surface. Three units **died mid-flight leaving no handoff at all** (`U1.7`, and the verifiers
`U4`'s predecessor evidence and `U5.5`/`V2`/`V7` are still open at the time of writing) — see
"Deaths without a report" below. That is a process fact the ledger must carry.

## Batches (plan §10)

| Batch | Unit | Purpose (one line) | Write paths | Status |
|---|---|---|---|---|
| 0 | `U0.1` | Persist the approved plan verbatim; lay down `orchestration/`, `AGENTS.md`, `.gitignore`, `git init` | `docs/PLAN.md`, `orchestration/**`, `AGENTS.md`, `.gitignore`, `.git/**` | done |
| 0 | `U0.1b` | Package scaffold + venv install (`pyproject.toml`, config, `src/`, `.venv/`) | `pyproject.toml`, `src/`, `config/`, `.venv/`, `state/logs/` | done |
| 0 | `U0.2` | Occamy client + tests (thinking flag per call, tool calls, retries, budgets, metering) | `src/resextract/llm/` | done |
| 0 | `U0.3` | Store + journal + `doctor` | `src/resextract/store.py`, `journal.py`, `doctor.py` | done |
| 0 | `D1` | Occamy outage diagnosis (why `:8012` refuses; settled cause handed to the user) | `state/logs/D1-occamy-diagnosis.log`, own card + handoff | done |
| 0 | `U0.5` | Ledger update + Batch-0 checkpoint commit | `orchestration/STATUS.md`, `.git/**` | **failed — commit withheld (secret scan)** → **superseded by `U0.6`** |
| 0 | `U0.6` | Re-stage the identical path list; remediate fixture literals; value-based scan; **commit** | `docs/SECRET_SCAN_POLICY.md`, `.git/**`, `tests/test_journal.py`, `tests/test_occamy_client.py` | done — commit `b4ea93c` |
| 0 | `U0.7` | CLI skeleton: 11 placeholders mapped to owning batches + tests | `src/resextract/cli.py`, `tests/test_cli.py` | done |
| 0 | `V0` | **Verifier** (not an author): spec/env/doctor/tests/red→green/journal/live/containment | `orchestration/VERDICTS.md`, `orchestration/handoffs/V0.json` | **OVERALL PASS** |
| — | `U0.10` | Store schema **v1 → v2** migration (additive; hand-rolled dir-dedupe retired downstream) | `src/resextract/store.py`, `tests/test_store_v2.py`, `state/logs/` | done |
| 1 | `U1.1` | graphify integration gate on `/home/zer0null/Duval` | `state/kg/`, `state/logs/` | **partial** — Gate C blocked (Occamy down) |
| 1 | `U1.2` | graphify wrapper + query battery (delivered `kg/graphify.py`, `kg/queries.py`; §10 row said "notebook normalizer" — stale) | `src/resextract/kg/` | done |
| 1 | `U1.4` | Notebook/data-format ingestion + coverage audit | `src/resextract/kg/ingest.py`, `tests/fixtures/ingest-repo/` | done |
| 1 | `U1.5` | Staging: normalized copies + combined graph | `src/resextract/kg/staging.py`, `kg/__init__.py` | done (LLM half externally blocked) |
| 1 | `U1.6` | graphify flag-surface hardening (bound-flag guard; `update()` arg fix) | `src/resextract/kg/graphify.py` | done |
| 1 | `U1.7` | Target policy / exclusion enforcement | `src/resextract/kg/policy.py` | **failed — no handoff persisted** → **recovered by `U1.7R`** |
| 1 | `U1.7R` | Fresh re-delegation of U1.7 carrying its failure evidence | `src/resextract/kg/policy.py`, `config/targets.toml`, `docs/TARGET_POLICY.md` | done |
| 1 | `V1` | **Verifier**: Gate A re-run, pollution/node-shape, provenance; Gate B/C semantic pass | `orchestration/VERDICTS.md`, `handoffs/V1.json` | **PARTIAL** — Occamy HTTP 000, Phase-1 gate NOT cleared |
| 2 | `U2.1` | Miner — canned graph query battery + bounded Occamy tool loop → candidates | `src/resextract/mine/` | **partial** — 0 live candidates (Occamy down) |
| 2 | `U2.2` | Claims + provenance | `src/resextract/mine/claims.py`, `provenance.py` | pending |
| 2 | `V2` | **Verifier** of the miner (mid-revert cycle at this checkpoint) | `orchestration/VERDICTS.md`, `handoffs/V2.json` | **running** — no handoff yet |
| 3 | `U3.1` | SearXNG client + search-health recording (pacing, engine rotation, backoff, negative cache) | `src/resextract/web/search.py` | done |
| 3 | `U3.2` | Fetch/cache — crawl → scrape fallback, content-hash cache, HTML→text | `src/resextract/web/fetch.py` | done |
| 3 | `U3.3` | Web package hardening pass over search + fetch | `src/resextract/web/` | done |
| 3 | `U3.4` | Search-health signal follow-through (per-attempt engine telemetry) | `src/resextract/web/search.py` | done |
| 3 | `V3` | **Verifier**: web suite, deleted-assertion audit, cache/SSRF/refresh live | `handoffs/V3.json` | **PARTIAL** — ≥1 follow-up open (raw `unresponsive_engines`) |
| 4 | `U4.1` | Assessment — novelty verdicts + real-world value axes | `src/resextract/assess/` | pending |
| 4 | `U4.2` | Lanes + classifier + split rule | `src/resextract/lanes/` | done |
| 4 | `V4` | **Verifier** of the lane code | `handoffs/V4.json` | **failed/partial — superseded by `V4R`** |
| 4 | `V4R` | Recovery of the failed V4 verifier; rounded re-check | `src/resextract/lanes/**` (reverts) | **partial** — handoff on disk is an empty skeleton **as of this checkpoint** |
| 5 | `U5.1` | Copy engine — byte-copies with sha256, caps, symlink refusal, `LINKS.md` fallback | `src/resextract/docket/copy.py` | done |
| 5 | `U5.2` | Manifest + assembly/verification engine + refusal gates | `src/resextract/docket/manifest.py`, `assemble.py` | done |
| 5 | `U5.3` | Materialize + CLI `materialize` wiring | `src/resextract/docket/materialize.py`, `cli.py` | done — **superseded in part by `U5.5`** |
| 5 | `U5.4` | Git-object source + refresh writer-detection | `src/resextract/docket/git_source.py`, `refresh/writer.py` | done |
| 5 | `U5.5` | Materialize/manifest follow-through (mid-write at this checkpoint) | `docket/materialize.py`, `manifest.py`, `cli.py`, `dockets/duval/**` | **running** — no handoff yet |
| 5 | `V5` | **Verifier**: full docket tree, manifest valid, every sha256 matches, repo untouched | `orchestration/VERDICTS.md` | pending |
| 6 | `U6.1` | Dashboard API + static UI (six screens) | `src/resextract/dashboard/**` | done |
| 6 | `U6.2` | Static UI polish beyond U6.1 | `dashboard/static/` | pending |
| 6 | `V6` | **Verifier**: six screens live on `127.0.0.1:8901`; loopback-only enforced | `orchestration/VERDICTS.md` | pending |
| 7 | `U7.1` | Refresh/staleness/review/backlog core | `src/resextract/refresh/` | done |
| 7 | `U7.2` | Rework backlog + **staged** systemd units (created, not enabled) | `refresh/backlog.py`, `deploy/` | pending |
| 7 | `V7` | **Verifier** of the refresh layer (mid-revert cycle at this checkpoint) | `refresh/**`, `docket/git_source.py` | **running** — no handoff yet |
| 8 | `U8.1` | Docs — `DESIGN.md`, `OPERATIONS.md`, `DOCKET_FORMAT.md`, `AGENTS.md` visit-log entry | `docs/`, `AGENTS.md` | pending |
| 8 | `U8.2` | Full acceptance run against `/home/zer0null/Duval` | `dockets/`, `state/` | pending |
| 8 | `U8.3` | **Independent adversarial verifier** — §1 criteria 1–9 each backed by a command output | `orchestration/VERDICTS.md`, `handoffs/V8.json` | pending |

**Batch boundary is sequential.** Concurrency inside a batch is allowed only with disjoint write paths (declared in the unit card), capped at 3.

### Deaths without a report

- `U1.7` — died mid-flight leaving **no handoff and no card**; its work was re-delegated as `U1.7R`,
  which persisted a full card, a handoff, and a red→green capture. `U1.7`'s own evidence is therefore
  **lost/reconstructed**, not verified.
- `V4` — left a `PARTIAL` handoff; `V4R` was launched to recover it. At this checkpoint `V4R`'s handoff
  is still an **empty skeleton** (`recovery.action_taken: "none"`, all checks empty), so V4's work is
  **not** re-verified yet.
- `U5.5`, `V2`, `V7` — running with no handoff on disk. Nothing about them is claimed here.

## Checkpoints

### Checkpoint 1 — `b4ea93c` (Batch-0)

U0.5 staged the 30 batch-0 paths correctly and the path-level checks passed (30 files; 0 paths under
`.venv/`, `state/`, `dockets/`; 0 secret-shaped filenames), but the **content** secret scan matched:
`sk-[A-Za-z0-9_-]{20,}` in 8 lines and `okr_[A-Za-z0-9]{16,}` in 2 lines, confined to
`tests/test_journal.py`, `tests/test_occamy_client.py`, `orchestration/units/V0.md`,
`orchestration/handoffs/V0.json`. U0.5's hard bound forbade committing on any hit and it had no
authority to self-exempt, so it **refused** and reported `failed` (honest: 30 files, 0 bad dir paths,
0 bad names, 10 pattern-matched diff lines).
`U0.6` then re-staged the identical list, converted the two test files' fixture literals to
runtime-assembled values, recorded every remaining synthetic value **by value** in
[`docs/SECRET_SCAN_POLICY.md`](../docs/SECRET_SCAN_POLICY.md), and committed **31 files** as
`b4ea93c457b39a1affa3e9efc63ab90abb234fc7`.

### Checkpoint 2 — this commit (Batch-0 + quiescent additions)

**This commit is a checkpoint, not a promotion.** It captures the work that is *quiescent* as of this
unit: the KG wrapper + ingestion + staging + policy, the web layer, the store v2 migration, the copy +
assembly engine, dashboard, and the refresh core — plus this ledger.
It **deliberately excludes** `src/resextract/{mine,lanes,refresh}/**`,
`docket/{materialize,manifest,git_source}.py`, `cli.py`, `dockets/**`, `state/**`, `.venv/**`, all
`orchestration/{handoffs,units}/**` and `orchestration/VERDICTS.md`, and the tests/fixtures those
trees own — because **four sibling units were running while it was staged, two of them mid-revert**
(`V2` in `mine/**`, `V4R` in `lanes/**`, `V7` in `refresh/**` + `docket/git_source.py`, `U5.5` in
`docket/materialize.py` + `manifest.py` + `cli.py` + `dockets/duval/**`).
A file under an active revert cycle must never be snapshotted: capturing a reverted guard would bake a
**silent regression** into history and make it look intentional.
`orchestration/` is limited to **this file** — the live ledger `AGENTS.md` points at — for the same
reason. Evidence: `orchestration/handoffs/U0.11.json`.

## Evidence digest — units with a persisted handoff

| Unit | Status | One-line evidence (test count + one key measured number, as the handoff reports) |
|---|---|---|
| `U0.1` | done | `docs/PLAN.md` 308 lines / 29875 B / md5 `7c4aac1199d530a3172cfa55c9a042d1` / 12 `##`; recovered byte-identical from the session log; `git init` only. |
| `U0.1b` | done | Python 3.14.4; graphify 0.9.80; graspologic-native 1.3.1 (leiden); 9/9 imports OK; `resextract --version` → 0.1.0 rc 0. |
| `U0.2` | done | **33 passed + 1 skipped** offline; live Occamy thinking-off ≈122.4 ms / 0 reasoning tokens / content `OK`; thinking-on ≈7214 ms / 256 rt / **empty content, `finish_reason=length`**. |
| `U0.3` | done | **64 passed**; `doctor --json` rc 0, core 4/4 green (docling DOWN); journal tamper → `(False, 2)`; 12 sqlite tables + WAL. |
| `D1` | done | Occamy `:8012` TCP **CLOSED** (connection refused), ICMP still alive → shared model server down, not a network fault; nothing restarted. |
| `U0.5` | failed | Path checks passed (**30 files**, 0 bad dir paths, 0 bad filenames) but **10 pattern-matched diff lines**; commit withheld. Superseded by `U0.6`. |
| `U0.6` | done | Commit `b4ea93c`, **31 files**; scoped re-run **43 passed + 1 skipped**; **8 literals remediated** across the 2 test files. |
| `U0.7` | done | **14 passed**; **11 placeholders** mapped to owning batches; no placeholder owner matches a live unit id. |
| `U0.10` | done | **13 passed (v2) + 42 passed (v1 regression)**; schema **1 → 2**; rows preserved (`runs` 4, `candidates` 10, `lanes` 5, `dockets` 1). |
| `U1.1` | partial | Gate A live on Duval: **2685 nodes / 7102 edges / 128 communities** in 3 s; Gate C (semantic) **not run** — Occamy refused. |
| `U1.2` | done | **22 passed**; fixture graph 21 nodes / 27 edges / 5 communities; node kinds `code` 12 / `rationale` 9. |
| `U1.4` | done | **34 passed**; live Duval audit **533 files, 453 supported, 84.99 %** coverage; top gap `jsonl` ×38. |
| `U1.5` | done | **13 passed**; **221 docs copied**, **22 607 550 B** staged; graph-reachable coverage **97.58 %** (moved HEAD); skipped-by-reason 236 covered-by-graphify. |
| `U1.6` | done | **25 passed**; bound-flag guard has teeth (bogus flag → `1 failed`); `update()` argv surface corrected. |
| `U1.7R` | done | **12 passed**; two guards red→green with sha before/after (`policy.py` `f8f1f7db…` restored); silent-loss path and widening refusal both proven. |
| `V0` | PASS | **OVERALL PASS** on Batch 0 (checks 1–10); red→green **2/2** sha-restored; containment PASS (Duval HEAD unchanged, no writes outside workspace). Honest gap: graphify **0.9.65** side of "zero CLI drift" UNVERIFIED. |
| `V1` | PARTIAL | Gate A re-run rc 0 in 2.75 s → **2695 nodes / 7151 edges / 119 communities** at the moved HEAD (U1.1's artifact: 2685/7102/128, difference attributable to the HEAD move). Phase-1 gate **not cleared**. |
| `U2.1` | partial | **13 passed**; live run produced **0 candidates** (Occamy `http=000` across 5 probes) — the reported live numbers come from a replay of U1.1's graph, not the model. |
| `U3.1` | done | **12 passed**; live probe 8 queries → 5 answered / 3 empty / 0 errors; degradation latch (3rd consecutive distinct empty) red→green. |
| `U3.2` | done | **52 passed**; 5 live cache entries; SSRF guard red→green (**18 failed** when reverted); refresh guard 3 failed; workspace-wide 183 passed + 1 skipped at that moment. |
| `U3.3` | done | Web package **78 passed** (search 17 + fetch 61); whole suite at 05:47 **237 passed, 1 skipped, 13 failed** — every failure in sibling-owned files, 0 in `test_web*`. |
| `U3.4` | done | **30 passed**; `search.py` sha256 `b79ff107…` captured before/after both guards; tool calls **25 / bound 35**. |
| `U4.2` | done | **23 passed**; live `from_store` → `build_lanes` → `classify_all` → `split_lane` → `persist_lanes('duval')`; determinism proven on shuffled input. |
| `V3` | PARTIAL | **78 passed** in 15.37 s; deleted-assertion audit → **0 assertions deleted**; ≥1 follow-up open (`unresponsive_engines` not yet surfaced). |
| `V4` | failed→`V4R` | Lane tests **23 passed in 0.05 s**; two red→green guards PASS with sha restored (`classify.py` `783e75c1…`); reported PARTIAL, superseded by `V4R`. |
| `V4R` | partial | Handoff is an **empty skeleton** at this checkpoint (`action_taken: "none"`, no checks captured) — recovery not yet evidenced. |
| `U5.1` | done | **15 passed**; live copy **6 copied / 0 linked / 2 refused / 134 236 B**, 6/6 sha spot-checks match, rerun unchanged. |
| `U5.2` | done | **24 passed**; full suite **250 passed + 1 skipped**; orphan-claim and sha256 tamper gates both red→green. |
| `U5.3` | done | **39 passed** (materialize 25 + cli 14); refusal writes no docket; containment guard red→green. |
| `U5.4` | done | **33 passed** (git_source 21 + writer_detection 12); pinned-vs-working divergence demonstrated live via a working-tree-only file. |
| `U6.1` | done | **48 passed**; traversal guard (2 failed) and loopback-bind refusal both red→green. |
| `U7.1` | done | **15 passed** (staleness 8 + review 7); live Duval refresh saw **14 commits between / 27 changed files**; second pass `noop=true`. |

Units with no handoff on disk (`U1.7`, `U2.2`, `U4.1`, `U5.5`, `V2`, `V7`, and every `pending` row above)
contribute **no evidence line** — absence of a handoff is not evidence of success.

## Canonical unit-id registry

Authoritative list of the unit ids in use in this build. Where the plan §10 table and a delivered card
diverge, **this registry wins**.

| Id | Kind | Owns |
|---|---|---|
| `U0.1` | builder | `docs/PLAN.md`, `orchestration/**` scaffolding, `AGENTS.md`, `.gitignore`, `git init` |
| `U0.1b` | builder | `pyproject.toml`, `src/resextract/__init__.py`, `src/resextract/py.typed`, `src/resextract/cli.py`, `config/`, `.venv/` |
| `U0.2` | builder | `src/resextract/llm/` (Occamy client), `tests/conftest.py`, `tests/test_occamy_client.py` |
| `U0.3` | builder | `src/resextract/store.py`, `journal.py`, `doctor.py`, `tests/test_store.py`, `tests/test_journal.py`, `tests/test_doctor.py` |
| `D1` | diagnosis | Occamy outage triage → `state/logs/D1-occamy-diagnosis.log` |
| `U0.5` | builder | Batch-0 checkpoint commit attempt (failed) |
| `U0.6` | builder | Batch-0 checkpoint commit (succeeded) + `docs/SECRET_SCAN_POLICY.md` |
| `U0.7` | builder | `src/resextract/cli.py` skeleton + `tests/test_cli.py` |
| `U0.10` | builder | `src/resextract/store.py` v2 schema + `tests/test_store_v2.py` |
| `U0.11` | builder | **this** checkpoint commit; `orchestration/STATUS.md` only under `orchestration/` |
| `U1.1` | builder | graphify integration gate (partial) |
| `U1.2` | builder | `src/resextract/kg/graphify.py`, `kg/queries.py`, `kg/__init__.py` + kg fixtures/tests (*not* "notebook normalizer" — stale §10 row) |
| `U1.4` | builder | `src/resextract/kg/ingest.py` + ingest fixtures |
| `U1.5` | builder | `src/resextract/kg/staging.py`, `kg/__init__.py` exports |
| `U1.6` | builder | `src/resextract/kg/graphify.py` flag-surface hardening |
| `U1.7` | builder | `src/resextract/kg/policy.py` (died, no handoff) |
| `U1.7R` | builder | `src/resextract/kg/policy.py`, `config/targets.toml`, `docs/TARGET_POLICY.md` (recovery of U1.7) |
| `U2.1` | builder | `src/resextract/mine/candidates.py`, `provenance.py`, `mine/__init__.py` |
| `U2.2` | builder | `src/resextract/mine/claims.py` |
| `U3.1` | builder | `src/resextract/web/search.py` |
| `U3.2` | builder | `src/resextract/web/fetch.py` |
| `U3.3` | builder | web package hardening pass (`search.py`, `fetch.py`, `web/__init__.py`) |
| `U3.4` | builder | `src/resextract/web/search.py` engine telemetry |
| `U4.1` | builder | `src/resextract/assess/` |
| `U4.2` | builder | `src/resextract/lanes/` |
| `U5.1` | builder | `src/resextract/docket/copy.py` |
| `U5.2` | builder | `src/resextract/docket/manifest.py`, `assemble.py` |
| `U5.3` | builder | `src/resextract/docket/materialize.py`, `cli.py` |
| `U5.4` | builder | `docket/git_source.py`, `refresh/writer.py`, `docs/LIVE_TARGET_NOTES.md` |
| `U5.5` | builder | `docket/materialize.py`, `manifest.py`, `cli.py`, `dockets/duval/**` (follow-through) |
| `U6.1` | builder | `src/resextract/dashboard/**` |
| `U6.2` | builder | dashboard static-UI polish |
| `U7.1` | builder | `src/resextract/refresh/review.py`, `staleness.py`, `backlog.py`, `refresh/__init__.py` |
| `U7.2` | builder | `deploy/` **staged** systemd units (created, never enabled) |
| `U8.1` | builder | `docs/DESIGN.md`, `docs/OPERATIONS.md`, `docs/DOCKET_FORMAT.md` |
| `U8.2` | builder | full acceptance run (`dockets/`, `state/`) |
| `V0` | verifier | Batch-0 verification (**no `V0.1` exists** — the §10 `V0.1` placeholder is superseded by `V0`) |
| `V1`–`V8` | verifier | per-batch verification; each is a *different* agent from the batch authors |
| `V4R` | verifier | recovery of the failed `V4`; **supersedes `V4`** |
| `U1.7R` | builder | **supersedes `U1.7`** |
| `U5.5` | builder | **supersedes `U5.3` in part** (materialize/manifest follow-through) |
| `U0.6` | builder | **supersedes `U0.5`** |

**Rule: placeholder owners are named by batch, never by a live unit id.** A batch name (`batch 1 (KG)`,
`batch 5 (docket)`) is stable; a live unit id (`U1.1`) is not — it names a specific agent that will finish
and be superseded.

### CLI placeholder → target batch (11 placeholders)

| Placeholder | Target batch |
|---|---|
| `target` | batch 1 (KG) |
| `run`, `mine` | batch 2 (mining) |
| `assess` | batch 4 (assessment) |
| `lanes` | batch 4 (lanes/classifier) |
| `materialize`, `open`, `export` | batch 5 (docket) |
| `serve` | batch 6 (dashboard) |
| `refresh`, `watch` | batch 7 (continuity) |

The placeholder strings **predate this rule and collided with live unit ids** in the Batch-0 tree;
`U0.7` re-authored `cli.py` against the batch-name table and added the regression test asserting no
placeholder owner matches `U\d+\.\d+[a-z]?` (14 passed). `cli.PLACEHOLDERS` is now conformant.

## Verified corrections (recorded across handoffs; `docs/PLAN_CORRECTIONS.md` carries the long form)

Observed on graphify 0.9.80 / this stack; each was measured, not assumed.

- **(a) `--no-viz` is not an `extract` flag.** In graphify 0.9.80 `--no-viz` belongs to `cluster-only`;
  `extract` does not accept it.
- **(b) graphify AST nodes have no `type` field.** The node kind is `file_type`, with values
  `code` / `rationale`; rationale/docstring nodes are first-class (fixture graph: 12 code + 9 rationale).
- **(c) SGLang counts reasoning *inside* `max_tokens`.** `finish_reason == "length"` with empty content
  means **truncation**, not an empty answer (measured: 256/256 tokens consumed by reasoning).
- **(d) SearXNG dead responses return in 2–7 ms while real ones take 172–948 ms**, and
  `unresponsive_engines` stays `[]` — so latency, not that field, is the tell.
- **(e) graphify appends a `graphify-out/` level under `--out`.** `--out state/kg/duval` writes
  `state/kg/duval/graphify-out/graph.json` (U1.1) — plan off-by-one-level, not a wrapper bug.
- **(f) The node-link JSON stores edges under the key `links`**, not `edges` (U1.1); readers must not
  assume `edges`.
- **(g) A graphify per-subcommand flag surface must be validated before use.** The wrapper emitted an
  argument `graphify update` rejects; U1.6 added a fail-closed bound-flag guard so a bogus flag is caught
  by the test suite rather than at runtime.
- **(h) The local environment has docling DOWN and no `pdflatex`/`pandoc`/`tectonic`** (U0.3 `doctor`
  core 4/4 green with docling as an optional leg). Renderer-dependent legs stay expected-red.
- **(i) The store v2 schema migration is additive.** v1 → v2 preserved every v1 row (`runs` 4,
  `candidates` 10, `lanes` 5, `dockets` 1) and v1's 42 tests still pass (U0.10); downstream code should
  call `upsert_docket_by_dir` / lane helpers instead of hand-rolling dir dedupe.
- **(j) A degraded search must latch on 3 consecutive distinct empties**, not on a single empty result
  (U3.1); the latch is the guard that failed when reverted.

## Standing constraints (apply to every unit)

- Target repos are **strictly read-only**: `/home/zer0null/Duval` and every other target. No writes, no `git` state changes, no hooks installed inside them.
- Nothing is written outside `/home/zer0null/reserach extarctor`.
- No systemd unit is enabled, no DSH plugin mounted, no DSH restart — without explicit user approval.
- No unit is ever extended; a failure is re-delegated to a **fresh** unit carrying the failure evidence. `partial` is a valid result.
- **A file under an active revert cycle is never staged.** Checkpoint units stage an explicit path list;
  never `git add -A`, never a glob into a tree a verifier is currently reverting.

## External blocker (unchanged, environment-level)

Occamy `http://192.168.2.168:8012/v1` is **down** (probe HTTP `000`, `curl (7) refused`; D1: TCP closed,
ICMP alive). Consequence: every semantic/LLM leg is unproven — `U1.1` Gate C not run, `U1.5` semantic
half not run, `U2.1` produced 0 live candidates, `V1` Phase-1 gate **not cleared**. Restarting a shared
model server is the **user's** decision; no unit may restart it.
