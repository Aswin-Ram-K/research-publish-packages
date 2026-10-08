# Orchestration status — Research Extractor

**Spec of record:** [`docs/PLAN.md`](../docs/PLAN.md) (308 lines, §0–§11; md5 `7c4aac1199d530a3172cfa55c9a042d1`, 29875 bytes, 12 `##` headings — byte-identical to the approved plan, V0 check 1).
**Legend — the three main-session rules:** (1) **delegation only** — the main session composes prompts, launches units, collects handoffs and reports; it never writes a file, runs a command, or reads source; (2) **units persist their own cards** to `orchestration/units/<UNIT>.md` and their verdict to `orchestration/handoffs/<UNIT>.json`; (3) **every batch needs an independent verifier** — never the unit that authored the work.

Status vocabulary: `pending` · `in_progress` · `done` · `failed` · `partial` · `superseded`.

## Batches (plan §10)

| Batch | Unit | Purpose (one line) | Write paths | Status |
|---|---|---|---|---|
| 0 | `U0.1` | Persist the approved plan verbatim; lay down `orchestration/`, `AGENTS.md`, `.gitignore`, `git init` | `docs/PLAN.md`, `orchestration/**`, `AGENTS.md`, `.gitignore`, `.git/**` | done |
| 0 | `U0.1b` | Package scaffold + venv install (`pyproject.toml`, config, `src/`, `.venv/`) | `pyproject.toml`, `src/`, `config/`, `.venv/`, `state/logs/` | done |
| 0 | `U0.2` | Occamy client + tests (thinking flag per call, tool calls, retries, budgets, metering) | `src/resextract/llm/` | done |
| 0 | `U0.3` | Store + journal + `doctor` | `src/resextract/store.py`, `journal.py`, `doctor.py` | done |
| 0 | `U0.5` | Ledger update + **verified Batch-0 checkpoint commit** (this unit) | `orchestration/STATUS.md`, `.git/**`, `orchestration/units/U0.5.md`, `orchestration/handoffs/U0.5.json` | **failed — commit withheld** |
| 0 | `V0` | **Verifier** (not an author): re-ran evidence; spec/env/doctor/tests/red→green/journal/live/containment | `orchestration/VERDICTS.md`, `orchestration/handoffs/V0.json` | **PASS** |
| 1 | `U1.1` | graphify integration gate (in flight at checkpoint; card not yet persisted) | `src/resextract/kg/` | running |
| 1 | `U1.2` | graphify wrapper + query battery (delivered `kg/graphify.py`, `kg/queries.py`; §10 row said "notebook normalizer" — stale) | `src/resextract/kg/` | done |
| 1 | `V1.1` | **Verifier**: real graph built from `/home/zer0null/Duval` with paths/hashes recorded; `query` returns real provenance; semantic pass proven or the fallback activated | `orchestration/VERDICTS.md`, `orchestration/handoffs/V1.1.json` | pending |
| 2 | `U2.1` | Miner — canned graph query battery + bounded Occamy tool loop → candidates | `src/resextract/mine/candidates.py` | running |
| 2 | `U2.2` | Claims + provenance | `src/resextract/mine/claims.py`, `provenance.py` | pending |
| 2 | `V2.1` | **Verifier**: ≥20 candidates with reproducible provenance; every candidate traceable in the journal | `orchestration/VERDICTS.md`, `orchestration/handoffs/V2.1.json` | pending |
| 3 | `U3.1` | SearXNG client + search-health recording (pacing, engine rotation, backoff, negative cache) | `src/resextract/web/search.py` | done |
| 3 | `U3.2` | Fetch/cache — crawl → scrape fallback, content-hash cache, HTML→text | `src/resextract/web/fetch.py` | done |
| 3 | `U3.3` | Sibling in flight at checkpoint (card not yet persisted) | (not recorded here) | running |
| 3 | `V3.1` | **Verifier**: ≥1 real lane's `PRIOR_ART.md` meets the existing review's standard; search-health table honest about ≥1 induced failure | `orchestration/VERDICTS.md`, `orchestration/handoffs/V3.1.json` | pending |
| 4 | `U4.1` | Assessment — novelty verdicts + real-world value axes | `src/resextract/assess/` | pending |
| 4 | `U4.2` | Lanes + classifier + split rule | `src/resextract/lanes/` | pending |
| 4 | `V4.1` | **Verifier**: ≥3 lanes, ≥2 types, split rule demonstrated on a real multi-claim lane, guards red→green | `orchestration/VERDICTS.md`, `orchestration/handoffs/V4.1.json` | pending |
| 5 | `U5.1` | Copy engine — byte-copies with sha256, caps, symlink refusal, `LINKS.md` fallback | `src/resextract/docket/copy.py` | running |
| 5 | `U5.2` | Manifest + templates + draft + export | `src/resextract/docket/`, `templates/` | pending |
| 5 | `V5.1` | **Verifier**: full docket tree for Duval, manifest valid, every copied sha256 matches, repo untouched | `orchestration/VERDICTS.md`, `orchestration/handoffs/V5.1.json` | pending |
| 6 | `U6.1` | Dashboard API + SSE | `src/resextract/web/app.py` | pending |
| 6 | `U6.2` | Static UI (six screens) | `src/resextract/web/static/` | pending |
| 6 | `V6.1` | **Verifier**: six screens live on `127.0.0.1:8901` rendering batch-2/3 data; loopback-only enforced | `orchestration/VERDICTS.md`, `orchestration/handoffs/V6.1.json` | pending |
| 7 | `U7.1` | Watch / refresh / staleness state machine | `src/resextract/refresh/review.py`, `staleness.py` | pending |
| 7 | `U7.2` | Rework backlog + **staged** systemd units (created, not enabled) | `src/resextract/refresh/backlog.py`, `deploy/` | pending |
| 7 | `V7.1` | **Verifier**: a simulated commit marks exactly the right dockets stale with correct rework entries; unit files created but not enabled | `orchestration/VERDICTS.md`, `orchestration/handoffs/V7.1.json` | pending |
| 8 | `U8.1` | Docs — `DESIGN.md`, `OPERATIONS.md`, `DOCKET_FORMAT.md`, `AGENTS.md` visit-log entry | `docs/`, `AGENTS.md` | pending |
| 8 | `U8.2` | Full acceptance run against `/home/zer0null/Duval` | `dockets/`, `state/` | pending |
| 8 | `U8.3` | **Independent adversarial verifier** — §1 criteria 1–9 each backed by a command output | `orchestration/VERDICTS.md`, `orchestration/handoffs/V8.1.json` | pending |

**Batch boundary is sequential.** Concurrency inside a batch is allowed only with disjoint write paths (declared in the unit card), capped at 3.

**In flight at the U0.5 checkpoint (deliberately NOT snapshotted): `U1.1`, `U2.1`, `U3.3`, `U5.1`.**
They were mid-write when the checkpoint was **attempted**; their files stay untracked (or their tracked
paths untouched) until a later, verified checkpoint covers them.

**Checkpoint status — U0.6 committed the verified Batch-0 tree.** (U0.5 staged the 30 paths correctly but refused to commit on secret-shaped fixtures; U0.6 remediated the fixture sources and applied the value-based scan of `docs/SECRET_SCAN_POLICY.md`.) Staging of the 30 batch-0 paths succeeded and
the path-level checks passed (30 files; 0 paths under `.venv/`, `state/`, `dockets/`; 0 secret-shaped
filenames), but the content secret scan matched: `sk-[A-Za-z0-9_-]{20,}` in 8 lines across
`tests/test_journal.py`, `tests/test_occamy_client.py`, `orchestration/units/V0.md`,
`orchestration/handoffs/V0.json`; and `okr_[A-Za-z0-9]{16,}` in 2 lines of `tests/test_journal.py`.
No `AKIA…`, private-key, `ghp_…` or `Authorization: Bearer` hits and **no hits under `src/`**. These are
the secret-shaped **fixtures that the journal-redaction tests require** plus the verifier's evidence
quoting them — i.e. almost certainly benign — but the unit's hard bound forbids committing on any hit and
the unit has no authority to self-exempt. `master` still has **no commits**; the index is left staged.
U0.6 did both: the two test files assemble their fixtures at runtime, and every remaining synthetic value is recorded **by value** in `docs/SECRET_SCAN_POLICY.md`.

## Evidence digest — completed units

| Unit | One-line evidence (as verified) |
|---|---|
| `U0.1` | `docs/PLAN.md` 308 lines / 29875 B / md5 `7c4aac1199d530a3172cfa55c9a042d1` / 12 `##`; recovered byte-identical from the session log; `git init` only (no commit). |
| `U0.1b` | Python 3.14.4; graphify 0.9.80; graspologic-native 1.3.1 (leiden); openai 3.26.1; 9/9 imports OK; `resextract --version` → 0.1.0 rc 0; all sampled graphify flags present. |
| `U0.2` | **33 passed + 1 skipped** offline; live Occamy: thinking off ≈122 ms / 0 reasoning tokens / content `OK`; thinking on ≈7214 ms / 256 reasoning tokens, **content empty, `finish_reason=length`**; red→green guard sha `7a44b4e8…` restored. |
| `U0.3` | **64 passed**; `doctor --json` rc 0, core 4/4 green (docling DOWN); journal tamper → `(False, 2)`; 12 sqlite tables + WAL; red→green 2 guards (`3f82e6c6…`), sha-restored. |
| `U1.2` | **22 passed** (kg graphify + queries); fixture graph 21 nodes / 27 edges / 5 communities; node kinds `code` 12 / `rationale` 9; those 0.9.80 runs are the source of corrections (a) and (b). |
| `U3.1` | **12 passed**; live probe 8 queries, 5 answered, 3 empty, 0 errors; dead responses **2–2.6 ms** vs real **172–948 ms**, `unresponsive_engines` stayed `[]`. |
| `U3.2` | **52 passed**; 5 live cache entries; SSRF guard red→green (18 failed when reverted), refresh guard (3 failed); workspace-wide 183 passed + 1 skipped at that moment. |
| `V0` | **OVERALL PASS** on Batch 0 (checks 1–10); red→green **2/2** sha-restored; live re-check off 151.8 ms / 0 rt, on 7438.7 ms / 256 rt; containment PASS (Duval HEAD unchanged, no writes outside the workspace). Honest gaps: graphify **0.9.65** side of "zero CLI drift" UNVERIFIED (no local artifact); U0.2 standalone 33+1 and U0.3 64 are the batch-0 test truth. |

## Canonical unit-id registry

Authoritative list of the unit ids in use in this build. Where the plan §10 table and a delivered card
diverge, **this registry wins**.

| Id | Kind | Owns |
|---|---|---|
| `U0.1` | builder | `docs/PLAN.md`, `orchestration/**` scaffolding, `AGENTS.md`, `.gitignore`, `git init` |
| `U0.1b` | builder | `pyproject.toml`, `src/resextract/__init__.py`, `src/resextract/py.typed`, `src/resextract/cli.py`, `config/`, `.venv/` |
| `U0.2` | builder | `src/resextract/llm/` (Occamy client), `tests/conftest.py`, `tests/test_occamy_client.py` |
| `U0.3` | builder | `src/resextract/store.py`, `journal.py`, `doctor.py`, `tests/test_store.py`, `tests/test_journal.py`, `tests/test_doctor.py` |
| `U0.5` | builder | `orchestration/STATUS.md`, `.git/**` (this checkpoint), own card + handoff only |
| `U1.1` | builder | graphify **integration gate** (in flight at checkpoint; card not yet persisted) |
| `U1.2` | builder | `src/resextract/kg/graphify.py`, `kg/queries.py`, `kg/__init__.py` + kg fixtures/tests (*not* "notebook normalizer" — §10 row is stale) |
| `U2.1` | builder | `src/resextract/mine/candidates.py` (in flight at checkpoint) |
| `U2.2` | builder | `src/resextract/mine/claims.py`, `provenance.py` |
| `U3.1` | builder | `src/resextract/web/search.py` |
| `U3.2` | builder | `src/resextract/web/fetch.py` |
| `U3.3` | builder | sibling in flight at checkpoint (card not yet persisted) |
| `U4.1` | builder | `src/resextract/assess/` |
| `U4.2` | builder | `src/resextract/lanes/` |
| `U5.1` | builder | `src/resextract/docket/copy.py` (in flight at checkpoint) |
| `U5.2` | builder | `src/resextract/docket/` (rest), `templates/` |
| `U6.1` | builder | `src/resextract/web/app.py` |
| `U6.2` | builder | `src/resextract/web/static/` |
| `U7.1` | builder | `src/resextract/refresh/review.py`, `staleness.py` |
| `U7.2` | builder | `src/resextract/refresh/backlog.py`, `deploy/` |
| `U8.1` | builder | `docs/DESIGN.md`, `docs/OPERATIONS.md`, `docs/DOCKET_FORMAT.md`, `AGENTS.md` |
| `U8.2` | builder | full acceptance run (`dockets/`, `state/`) |
| `V0` | verifier | Batch-0 verification → `orchestration/VERDICTS.md`, `handoffs/V0.json`. (**No `V0.1` exists** — the §10 placeholder `V0.1` row is superseded by `V0`.) |
| `V1.1`–`V8.1` | verifier | per-batch verification; each is a *different* agent from the batch authors |

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

The **current `cli.py` placeholder strings predate this rule and collide with live unit ids** — e.g.
`target` claims owner `U1.1`, which was the graphify integration gate, and `materialize/open/export`
claim `U5.2` while `U5.1` is the copy engine. A follow-up unit will conform `cli.py` to the table above
and add a regression test asserting that no placeholder owner string matches a live unit id.

## Verified corrections (pending the formal `docs/PLAN_CORRECTIONS.md`)

Observed on 0.9.80 / this stack; each was measured, not assumed.

- **(a) `--no-viz` is not an `extract` flag.** In graphify 0.9.80 `--no-viz` belongs to `cluster-only`;
  `extract` does not accept it.
- **(b) graphify AST nodes have no `type` field.** The node kind is `file_type`, with values
  `code` / `rationale`; rationale/docstring nodes are first-class (fixture graph: 12 code + 9 rationale).
- **(c) SGLang counts reasoning *inside* `max_tokens`.** `finish_reason == "length"` with empty content
  means **truncation**, not an empty answer (measured: 256/256 tokens consumed by reasoning).
- **(d) SearXNG dead responses return in 2–7 ms while real ones take 172–948 ms**, and
  `unresponsive_engines` stays `[]` — so latency, not that field, is the tell.

## Standing constraints (apply to every unit)

- Target repos are **strictly read-only**: `/home/zer0null/Duval` and every other target. No writes, no `git` state changes, no hooks installed inside them.
- Nothing is written outside `/home/zer0null/reserach extarctor`.
- No systemd unit is enabled, no DSH plugin mounted, no DSH restart — without explicit user approval.
- No unit is ever extended; a failure is re-delegated to a **fresh** unit carrying the failure evidence. `partial` is a valid result.

### U0.6 — Batch-0 checkpoint committed

The verified Batch-0 tree is committed (value-based secret scan, `docs/SECRET_SCAN_POLICY.md`); `tests/test_journal.py` and `tests/test_occamy_client.py` carry their synthetic fixtures as runtime-assembled values and no longer match the scanner. Evidence: `orchestration/handoffs/U0.6.json`.
