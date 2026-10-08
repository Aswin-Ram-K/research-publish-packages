# Orchestration status — Research Extractor

**Spec of record:** [`docs/PLAN.md`](../docs/PLAN.md) (308 lines, §0–§11; md5 `7c4aac1199d530a3172cfa55c9a042d1`, 29875 bytes — byte-identical to the approved plan, V0 check 1).
**Merged corrections ledger:** [`docs/PLAN_CORRECTIONS.md`](../docs/PLAN_CORRECTIONS.md) — entries **(a)–(ai)**, **35 entries**, merged by `U8.2` (a–y) and extended by `U8.4` (z–ai). Next letter: **`aj`**. Fragment [`docs/PLAN_CORRECTIONS_PART2.md`](../docs/PLAN_CORRECTIONS_PART2.md) is retained.
**Process lessons:** [`docs/LESSONS.md`](../docs/LESSONS.md) — nine findings, each with the incident it came from.
**Legend — the three main-session rules:** (1) **delegation only** — the main session composes prompts, launches units, collects handoffs and reports; it never writes a file, runs a command, or reads source; (2) **units persist their own cards** to `orchestration/units/<UNIT>.md` and their verdict to `orchestration/handoffs/<UNIT>.json`; (3) **every batch needs an independent verifier** — never the unit that authored the work.

Status vocabulary: `pending` · `in_progress` · `done` · `failed` · `partial` · `superseded`.

**This table is rebuilt from the 61 handoffs actually on disk, as of `2026-10-08T12:0xZ` by `U0.15` (the
recovery/checkpoint unit), not from the plan's intent.**
**Totals at this rebuild:** **45 `done`** · **8 `partial`** (`U0.14`, `U0.15`, `U1.1`, `U2.1`, `U2.2`,
`U5.8`, `U6.5`, `V8` — 6 in flight, `U0.14` dead) · **1 `failed`** (superseded, `U0.5`) · **7 verifier
handoffs** whose verdict lives in `overall` (`V0` PASS · `V1` PARTIAL · `V2` FAIL → **closed by `V2S`** ·
`V3` PARTIAL · `V4` PARTIAL, superseded · `V4R` PASS · `V5` PASS · `V7` PASS). `running` means "launched,
no usable handoff on disk yet" — a statement about evidence, not about health.

> Retired: the previous ledger carried its own `(a)–(j)` "verified corrections" index whose numbering
> **conflicted** with the corrections ledger (its (c) was SGLang, the ledger's (c) is the `links` key).
> It is replaced by the single merged `(a)–(ai)` ledger, which is authoritative.

## Corrections that matter (superseding earlier claims in this ledger)

A recurring failure mode of this build is **inferring "no artifacts" from "no closing message."** Three
premises recorded here were wrong and each cost a recovery cycle. Corrected:

- **`V4` *did* leave a handoff.** `orchestration/handoffs/V4.json` is on disk, `overall: "PARTIAL"`. The
  "died silently" premise was **wrong**; `V4R` (done, `PASS`) supersedes it.
- **`V2R` *did* leave a complete report.** It was recorded as "no verdict yet" while its checks were on
  disk all along (`C1 = store_v2 failures are version pins only`). Recovery re-established what already
  existed.
- **`U2.2` → `V2S` closed the build's only outright FAIL.** `V2`'s FAIL (replay rows indistinguishable
  from model-mined rows; `model_calls` misleading) is **genuinely closed**, independently reproducible
  (`V2S` done). The earlier "FAIL stands open" text below is retained as history only.
- **`U5.6` / `U5.7` / `U0.12` / `U8.3` / `U8.4` are done** (tree-first deletion-gap fix; manifest
  provenance fields + materialize gate; store follow-through; the adversarial acceptance verifier;
  ledger extension to 35).
- **`V5B` found a genuine defect** — bare re-assembly in `assemble` silently **downgrades
  `generated_by.producer` provenance**; `U5.8` is fixing it.
- **`V6` dashboard six screens PASS**, but **nested dockets 404** on `route_slug` (needs a 2-segment
  route or detail-by-path); `U6.5` is fixing it.
- **`U0.14` died mid-checkpoint** (no closing message). Its artifacts *are* present: a `partial` handoff
  and `state/logs/U0.14_staged.diff`. **`U0.15` is the recovery/checkpoint unit** and does not assume
  U0.14's claims; it re-verified them.

## Coupling & licensing note (read before the table)

Since the Batch-0 checkpoint, units were launched concurrently inside shared write surfaces. One unit
**died mid-flight leaving neither card nor handoff** (`U1.7`). Three further "silent deaths" were
**false premises** (above). In-flight write surfaces at this rebuild: **`U5.8`**
(`src/resextract/docket/{assemble,manifest,materialize}.py`), **`U6.5`**
(`src/resextract/dashboard/{api,app}.py`, `tests/test_dashboard.py`), **`V4A`**
(`src/resextract/assess/{evidence,verdicts}.py`, last), **`V8`** (`src/resextract/run.py`, last).
Nothing in this ledger is claimed on their behalf. Because `cli.py` imports docket, dashboard and run,
**no checkpoint can include `cli.py` while excluding any of them** — see the checkpoint-3 note.

## Batches (plan §10)

| Batch | Unit | Purpose (one line) | Status | Verdict / note |
|---|---|---|---|---|
| 0 | `U0.1` | Persist the approved plan verbatim; lay down `orchestration/`, `AGENTS.md`, `.gitignore`, `git init` | done | plan byte-identical (`7c4aac11…`) |
| 0 | `U0.1b` | Package scaffold + venv install | done | py3.14.4 · graphify 0.9.80 · 9/9 imports |
| 0 | `U0.2` | Occamy client + tests | done | 33 passed + 1 skipped |
| 0 | `U0.3` | Store + journal + `doctor` | done | 64 passed · doctor rc 0 core 4/4 |
| 0 | `D1` | Occamy outage diagnosis | done | `:8012` TCP CLOSED, ICMP alive |
| 0 | `U0.5` | Ledger update + Batch-0 checkpoint commit | **failed** → superseded by `U0.6` | commit withheld on secret-scan hits |
| 0 | `U0.6` | Re-stage identical path list; remediate fixture literals; commit | done | commit **`b4ea93c`**, 31 files |
| 0 | `U0.7` | CLI skeleton: placeholders mapped to owning batches + tests | done | 14 passed |
| 0 | `V0` | **Verifier** Batch 0 | **PASS** | red→green 2/2 sha-restored; containment PASS |
| — | `U0.10` | Store schema **v1 → v2** migration (additive) | done | 13 + 42 passed · rows preserved |
| 0 | `U0.11` | **Checkpoint 2** commit of quiescent work | done | commit **`c6249a6`**, 115 files |
| 0 | `U0.12` | Store follow-through after v2 | done | four evidence commands re-runnable |
| 1 | `U1.1` | graphify integration gate on `/home/zer0null/Duval` | **partial** | Gate A 2685/7102/128; Gate C blocked (Occamy) |
| 1 | `U1.2` | graphify wrapper + query battery | done | 22 passed |
| 1 | `U1.4` | Notebook/data-format ingestion + coverage audit | done | 34 passed · 84.99 % supported |
| 1 | `U1.5` | Staging: normalized copies + combined graph | done (LLM half externally blocked) | 13 passed · 221 docs / 22.6 MB |
| 1 | `U1.6` | graphify flag-surface hardening (fail-closed bound-flag guard) | done | 25 passed; bogus flag → `1 failed` |
| 1 | `U1.7` | Target policy / exclusion enforcement | **failed — no handoff, no card** → recovered by `U1.7R` | evidence lost/reconstructed |
| 1 | `U1.7R` | Fresh re-delegation of U1.7 carrying its failure evidence | done | 12 passed · 2 guards red→green · `worktrees_rejected: 1` |
| 1 | `V1` | **Verifier** Gate A/node-shape/provenance | **PARTIAL** | rebuild 2695/7151/119 @`b44e0e1`; Phase-1 gate NOT cleared |
| 2 | `U2.1` | Miner — graph query battery + bounded Occamy tool loop | **partial** | 13 passed; live run 0 candidates (Occamy 000) |
| 2 | `U2.2` | Claims + provenance (producer labelling) | **partial** | mine 15 passed · store_v3 8 passed · version pins in store_v2 |
| 2 | `V2` | **Verifier** of the miner | **FAIL → closed by `V2S`** | replay rows indistinguishable · `model_calls` misleading |
| 2 | `V2R` | Recovery re-check of the miner verification | verifier (verdict in `overall`) | **report WAS on disk**; C1 = store_v2 failures are version pins only |
| 2 | `V2S` | Superseding fix/verification of `V2`'s FAIL A + FAIL B | done | **both FAILs genuinely closed**, independently reproducible |
| 3 | `U3.1` | SearXNG client + search-health recording | done | 12 passed · 3-consecutive-empty latch red→green |
| 3 | `U3.2` | Fetch/cache — crawl → scrape fallback, URL-keyed cache | done | 52 passed · SSRF guard red→green |
| 3 | `U3.3` | Web package hardening pass | done | 78 passed (search 17 + fetch 61) |
| 3 | `U3.4` | Search-health signal follow-through | done | 30 passed · tool calls 25/35 |
| 3 | `V3` | **Verifier** web suite, deleted-assertion audit | **PARTIAL** | 78 passed in 15.37 s · 0 assertions deleted |
| 4 | `U4.0` | Assessment — decompose | done | store rows before: candidates 10, claims 0, verdicts 0 |
| 4 | `U4.1` | Evidence/verdicts | done | filled only when the search backend works |
| 4 | `U4.2` | Lanes + classifier + split rule | done | 23 passed · live 5 lanes, 5 `paper` refusals, 0 splits |
| 4 | `V4` | **Verifier** of the lane code | **PARTIAL** → superseded by `V4R` | 23 passed · 2 guards red→green · **handoff IS on disk** |
| 4 | `V4R` | Recovery of `V4` | done | `PASS` — no guard left reverted |
| 4 | `V4A` | **Verifier** — degraded search never yields a publication | done | `PASS` on the safety property |
| 5 | `U5.1` | Copy engine — sha256 byte-copies, caps, symlink refusal | done | 15 passed · 6 copied / 0 linked / 2 refused |
| 5 | `U5.2` | Manifest + assembly/verification engine + refusal gates | done | 24 passed · suite 250 passed + 1 skipped |
| 5 | `U5.3` | Materialize + CLI `materialize` wiring | done | 39 passed · refusal writes no docket |
| 5 | `U5.4` | Git-object source + refresh writer-detection | done | 33 passed · pinned-vs-working divergence live |
| 5 | `U5.5` | Materialize/manifest follow-through (supersedes `U5.3` in part) | done | 50 passed · `duval-u55-pinned` 9 copied / verify_ok |
| 5 | `U5.6` | Deletion-gap fix (tree-first resolution) | done | tree-first in and guard-proven |
| 5 | `U5.7` | Manifest provenance fields + materialize gate | done | gate enforced and labelled |
| 5 | `U5.8` | Fix `assemble`'s **provenance downgrade** on bare re-assembly (found by `V5B`) | **partial (in flight)** | mid-edit in `docket/{assemble,manifest,materialize}.py` |
| 5 | `V5` | **Verifier** docket tree, manifest, sha256, repo untouched | **PASS** | tracked drift real · sealed-window live attempt NOT proof |
| 5 | `V5B` | **Verifier** re-assembly / provenance | done | found assemble dropping `git_object`/`blob_sha` |
| 6 | `U6.1` | Dashboard API + static UI (six screens) | done | 48 passed · traversal + loopback guards red→green |
| 6 | `U6.2` | Static UI polish + `serve` CLI wiring | done | 15 passed · 9 routes 200 on `127.0.0.1:8901` |
| 6 | `U6.3` | Dashboard fixture/test-strategy pass | done | fresh-checkout reproduction evidenced |
| 6 | `U6.4` | Repo hygiene: anchor `.gitignore`, untrack fixture sqlite | done | root-only `/dockets/`; three sqlite files untracked |
| 6 | `U6.5` | Fix nested-docket 404 (masked traversal condition) | **partial (in flight)** | `dashboard/{api,app}.py`, `tests/test_dashboard.py` |
| 6 | `V6` | **Verifier** six screens live, loopback-only | done | `PASS`; nested dockets 404 → `U6.5` |
| 7 | `U7.1` | Refresh/staleness/review/backlog core | done | 15 passed · live 14 commits between / 27 changed files |
| 7 | `U7.2` | Rework backlog + **staged** systemd units (never enabled) | done | 38 passed · bytecode discipline |
| 7 | `V7` | **Verifier** of the refresh layer | **PASS** | 8 HEAD moves in the reflog window (not 9) |
| 8 | `U8.1` | Docs — `ACCEPTANCE_PROTOCOL.md`, `OPERATIONS.md` | done | 41 handoffs read · 22 gates defined |
| 8 | `U8.2` | Merge corrections (a)–(y); write `LESSONS.md`; rebuild status | done | merged 25 entries, no entry rewritten |
| 8 | `U8.3` | **Independent adversarial verifier** — §1 criteria 1–9 | done | re-runnable evidence commands |
| 8 | `U8.4` | Corrections ledger extension | done | closed through **(ai)**; next letter `aj` |
| 8 | `V8` | **Verifier** of the acceptance run | **partial (in flight)** | verification in progress; mid-edit in `src/resextract/run.py` |
| — | `U0.14` | **Checkpoint 3** (first attempt) | **partial — died mid-checkpoint** | no closing message; handoff + `state/logs/U0.14_staged.diff` present; index left half-staged |
| — | `U0.15` | **Recovery/checkpoint 3 (stable core)** | **partial → done (this unit)** | classification `index_half_staged`; see checkpoints below |

**Batch boundary is sequential.** Concurrency inside a batch is allowed only with disjoint write paths (declared in the unit card), capped at 3.

### Deaths and "silent deaths" — corrected

- `U1.7` — **truly died** mid-flight leaving **no handoff** (a card exists). Re-delegated as `U1.7R`.
- `V4` — premise "left no report" was **wrong**; `V4.json` is on disk with `overall: "PARTIAL"`.
- `V2R` — premise "no verdict" was **wrong**; its complete report was on disk all along.
- `U0.14` — died with no closing message; **artifacts present** (handoff `partial`, staged-diff log,
  68-path index). Its handoff is **not machine-parseable** (`JSONDecodeError: Extra data: line 11
  column 167`), so its fields are read by inspection and treated as **unverified**. `U0.15` re-ran the
  coherence proof rather than inheriting the claim.
- In flight with partial handoffs (not dead): `U2.2`, `U5.8`, `U6.5`, `V8`.

## Checkpoints (three)

| Commit | Subject | By | Files | Evidence |
|---|---|---|---|---|
| `b4ea93c` | Batch-0 checkpoint: verified resextract core (V0 PASS) | `U0.6` | 31 | value-based scan after 8 literal remediations · scoped re-run 43 passed + 1 skipped |
| `c6249a6` | Checkpoint 2: quiescent post-Batch-0 work | `U0.11` | 115 | 19319 insertions / 76 deletions · scan 2 matches, 1 distinct value, **by value** |
| *(checkpoint 3)* | **Checkpoint 3: stable core only** (docket/dashboard/assess/run/cli deferred to checkpoint 4) | `U0.15` | see handoff | imports 14/14 · scoped **423 passed, 1 skipped, 0 failed** · scan by value · parent `c6249a6` |

Checkpoint 3's sha is recorded in [`orchestration/handoffs/U0.15.json`](../orchestration/handoffs/U0.15.json)
(committed content cannot contain its own hash).

**Why checkpoint 3 is narrower than checkpoint 2.** Four siblings are mid-edit and `cli.py` imports
three of their packages, so no commit containing `cli.py` can exclude them coherently. The coherent set
is therefore the **stable core**; `docket/**`, `dashboard/**`, `assess/**`, `run.py`, `cli.py` and their
test files are **excluded and await checkpoint 4**. Consequence unchanged from checkpoint 2: most of the
evidence this ledger cites is **on disk but not in git history** — "it is in the repo" and "it is
committed" are different claims. Checkpoint 3 also commits **only `orchestration/STATUS.md`** from
`orchestration/` — handoffs, unit cards and `VERDICTS.md` are excluded.

## Open items

1. **Both existing dockets lack `generated_by.producer`.** The provenance gap `V5B` found in assembly is
   being fixed by `U5.8`; until it lands, no produced docket carries a producer label.
2. **Nested dockets 404** on the dashboard (`V6` `PASS` otherwise) — `U6.5` fixing (2-segment
   `route_slug` or detail-by-path).
3. **Deferred batch-4 gate** — *"≥2 publication types + a split on a real lane"* is **unmet live**: the
   store holds **0 claims / 0 verdicts / 0 evidence** (candidates 10, lanes 5), so `U4.2`'s live run
   produced **1 publication type (`report`)** and **0 splits**, with **5/5 lanes correctly refusing
   `paper`** because no lane has an external anchor or a measured result. **That refusal is the guard
   working as designed.** The gate **stays deferred until real claims/verdicts/evidence exist** and must
   not be marked satisfied from canned or replay data.
4. **Two external blockers for the acceptance criteria:** **Occamy is DOWN** and **SearXNG is denying
   access**. Every model-dependent *and* search-dependent leg stays unproven (`U1.1` Gate C, `U1.5`
   semantic half, `U2.1` live mining, `V1` Phase-1 gate, `U4.1` evidence/verdicts, `U8.x` acceptance
   Gates B/C).
5. **Excluded packages await checkpoint 4** — docket, dashboard, assess, `run.py`, `cli.py` and their
   tests, plus the four in-flight units that own them.

## External blocker (environment-level, user decision)

Occamy `http://192.168.2.168:8012/v1` is **DOWN** — `U0.15`'s probe returned HTTP **`000`**
(`curl (7) refused`, `2026-10-08T12:0xZ`), matching D1's diagnosis (TCP closed, ICMP alive). The owning
unit is **`gx10-occamy-nvfp4.service`**, which is **crash-looping** on an SGLang
`--mem-fraction-static=0.5` KV-cache sizing guard (minimum viable = **0.4993**, drifting toward the
configured **0.500**). The durable fix is raising it to **~0.60**; a bare restart is a coin flip.
**No unit may touch the GX10 or restart the service — this is the user's decision.**
Separately, **SearXNG is denying access** to this host, which blocks the web legs independently of Occamy.

## Canonical unit-id registry

`U0.1` · `U0.1b` · `U0.2` · `U0.3` · `D1` · `U0.5` → `U0.6` · `U0.7` · `U0.10` · `U0.11` · `U0.12` ·
`U1.1` · `U1.2` · `U1.4` · `U1.5` · `U1.6` · `U1.7` → `U1.7R` · `U2.1` · `U2.2` · `U3.1` · `U3.2` ·
`U3.3` · `U3.4` · `U4.0` · `U4.1` · `U4.2` · `U5.1` · `U5.2` · `U5.3` ← `U5.5` · `U5.4` · `U5.6` ·
`U5.7` · `U5.8` · `U6.1` · `U6.2` · `U6.3` · `U6.4` · `U6.5` · `U7.1` · `U7.2` · `U8.1` · `U8.2` ·
`U8.3` · `U8.4` · checkpoint units `U0.11`, `U0.14`, `U0.15` · verifiers `V0`–`V8` (`V0.1` does not
exist — superseded by `V0`) · `V2R`/`V2S` (recovery of `V2`) · `V4A`/`V4R` · `V5B`.

**Supersessions:** `U0.6` > `U0.5` · `U1.7R` > `U1.7` · `V4R` > `V4` · `U5.5` > `U5.3` (in part) ·
**`V2S` closes `V2`** · **`U0.15` > `U0.14`** (recovery of the dead checkpoint). `V2R` is a *recovery
re-check* of `V2`, not a supersession.

**Rule: placeholder owners are named by batch, never by a live unit id.** A batch name
(`batch 2 (mining)`) is stable; a live unit id (`U2.1`) is not.

### CLI placeholder → target batch

| Placeholder | Target batch |
|---|---|
| `target` | batch 1 (KG) |
| `run`, `mine` | batch 2 (mining) |
| `assess` | batch 4 (assessment) |
| `lanes` | batch 4 (lanes/classifier) |
| `open`, `export` | batch 5 (docket) |
| `refresh`, `watch` | batch 7 (continuity) |

Implemented: `doctor`, `status`, `materialize` (`U5.3`), `serve` (`U6.2`). `U8.3` reports the `run` CLI
still placeholder; `U3.4` notes the `[stages.*].thinking` / `max_thinking_tokens` policy is still
unwired — an open follow-up, not a placeholder.

## Standing constraints (apply to every unit)

- Target repos are **strictly read-only**: `/home/zer0null/Duval` and every other target. No writes, no `git` state changes, no hooks installed inside them.
- Nothing is written outside `/home/zer0null/reserach extarctor`.
- No systemd unit is enabled, no DSH plugin mounted, no DSH restart — without explicit user approval.
- No unit is ever extended; a failure is re-delegated to a **fresh** unit carrying the failure evidence. `partial` is a valid result.
- **A file under an active revert cycle is never staged.** Checkpoint units stage an explicit path list; never `git add -A` unqualified.
- Persist a `status: partial` handoff **immediately** after your step-0 probe, then update it after each
  step — three units died mid-flight and two of them left no *usable* handoff
  (`docs/LESSONS.md` §2, `U0.14`).
- **A missing closing message is not missing artifacts.** Check the disk before re-doing a recovery.
