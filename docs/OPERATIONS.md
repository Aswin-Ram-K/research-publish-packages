# OPERATIONS — running Research Extractor

**Written by unit U8.1.** Companion to [`docs/ACCEPTANCE_PROTOCOL.md`](ACCEPTANCE_PROTOCOL.md) (the
end-to-end acceptance procedure) and [`AGENTS.md`](../AGENTS.md) (how work is done here).
**Spec of record:** [`docs/PLAN.md`](PLAN.md). **Live ledger:**
[`orchestration/STATUS.md`](../orchestration/STATUS.md).

Everything runs from the workspace root — `/home/zer0null/reserach extarctor` — with the venv at
`.venv/`. Nothing is installed globally; no systemd unit is enabled.

---

## 0. The one-paragraph version

```bash
.venv/bin/resextract doctor --json      # gate: exit 0, core legs green
.venv/bin/resextract status --json      # gate: schema v2, row counts match the ledger
# ... run the pipeline stages (below), each writing only into state/ or dockets/ ...
.venv/bin/resextract materialize --target duval --lane-file <lane.json> --json
```

Targets are **strictly read-only**. `/home/zer0null/Duval` is also being written by its own self-build
loop, so anything copied out of it must be **commit-pinned** or explicitly marked `unpinned`
([`docs/LIVE_TARGET_NOTES.md`](LIVE_TARGET_NOTES.md)).

---

## 1. How to run each stage

`resextract` is a single CLI. Today **four subcommands are real** — `doctor`, `status`, `materialize`,
`serve` — and the other nine names are **placeholders that exit 3** with the batch that owns them
(`src/resextract/cli.py:37–66`, `IMPLEMENTED = {doctor, status, materialize, serve}`; U0.3, U0.7, U5.3,
plus `serve` landed by a sibling unit mid-build). This workspace is written by several units at once, so
**re-read `cli.IMPLEMENTED` before relying on this list**. Where a stage has no CLI entry point, drive the
library API the same way the units did.

| Stage | Command | Notes |
|---|---|---|
| Doctor / dependency gate | `.venv/bin/resextract doctor [--json]` | core legs: Occamy, SearXNG, crawl bridge, graphify; optional: docling, renderers, dashboard port. Retry **once** on a SearXNG timeout before calling it down (U0.3). |
| Store summary | `.venv/bin/resextract status [--json]` | schema version, lanes, dockets, last run. Read-only. |
| Target registration | `config/targets.toml` (edit by hand) | `resextract target add` is a **placeholder** (batch 1). Registration + policy live in [`config/targets.toml`](../config/targets.toml) (U1.7R). |
| Knowledge graph (code-only) | `.venv/bin/graphify extract /home/zer0null/Duval --code-only --out state/kg/duval` | Writes `state/kg/duval/**graphify-out/**graph.json` — the extra `graphify-out/` level is graphify's, not a bug (correction (j)). **Do not pass `--no-viz`** to `extract` (correction (a)). |
| Knowledge graph (semantic) | see [`ACCEPTANCE_PROTOCOL.md`](ACCEPTANCE_PROTOCOL.md) §6 G2 | Requires a **live** Occamy probe (`HTTP 200`); `stdbuf -oL -eL`, `--token-budget 1500`, `--max-concurrency 1`, `--api-timeout 300`. |
| Coverage audit | `.venv/bin/python -c "from resextract.kg import ingest; print(ingest.coverage_audit('/home/zer0null/Duval'))"` | 533 files / 453 supported / 84.99% repo-native (U1.4). |
| Staging corpus | `resextract.kg.staging` (U1.5's exact argv is in [`orchestration/units/U1.5.md`](../orchestration/units/U1.5.md)) | 221 docs / 22,607,550 B; graph-reachable coverage 97.58% (U1.5). |
| Mining | `resextract.mine.Miner` (`verify_provenance`, `MineReport`) | `mine` CLI name is a placeholder (batch 2). **Model path is blocked while Occamy is down**; a replay run must be labelled as replay (V2). |
| Lanes + classifier | `resextract.lanes`: `from_store → build_lanes → classify_all → split_lane → persist_lanes` | `lanes` CLI name is a placeholder (batch 4). Deterministic under shuffle (U4.2). |
| Materialize | `.venv/bin/resextract materialize --target S [--lane ID\|--lane-file F] [--docket-root DIR] [--dry-run] [--json]` | The one implemented pipeline subcommand. `--dry-run` writes nothing (U5.3). |
| Docket verification | `resextract.docket.verify_docket(docket_dir)` | Orphan-claim + material-sha gates; `ok: true, problems: []` is the pass (U5.2, U5.5). |
| Refresh / staleness | `resextract.refresh.refresh_target(...)` | **No CLI entry point** today (placeholders `refresh`, `watch`) and `persist_store=False` by default (correction (w); V7 check 7). |
| Dashboard | `.venv/bin/python -m resextract.dashboard --port 8901` (U6.1-verified) or `.venv/bin/resextract serve [--host 127.0.0.1] [--port 8901] [--token auto]` (newly implemented; **not yet independently verified**) | Loopback-only; a non-loopback host is refused with exit **2** (a hard configuration failure, not a placeholder). Managed background job owned by the unit that runs it; the unit verifies and reports the exact URL, then stops it (U6.1). |
| Offline test suite | `.venv/bin/python -m pytest tests/ -q` | Fixtures only — no network, no GX10 (plan §1.8). |
| Red→green capture | run with `PYTHONDONTWRITEBYTECODE=1` and purge `__pycache__` | A same-length edit within the same wall-clock second can serve a stale `.pyc` and produce a **false failure on the restored file** (V3 gotcha; adopted by V7). |

**Idempotence and resumability.** Every stage is content-hash keyed and resumable (plan §3.2).
`materialize` rerun into the same docket reports the copies `unchanged` and leaves `verify_docket` `ok`
(U5.1, U5.3, U5.5). The miner resumes on an unchanged graph hash with `model_calls=0` and zero HTTP
(V2). Refresh's second pass is `noop=true` (U7.1, re-derived by V7 check 3).

---

## 2. Exit-code contract

The plan's declared contract (`docs/PLAN.md` §3.2):

| Code | Meaning |
|---|---|
| `0` | ok |
| `1` | completed **with recorded degradations** |
| `2` | **hard dependency down** |
| `3` | **budget exhausted with work remaining** (and, today, "not implemented") |

**What is actually implemented** at this reading (`src/resextract/cli.py:27–29`):

- `EXIT_OK = 0`, `EXIT_CORE_DOWN = 2`, `EXIT_NOT_IMPLEMENTED = 3`.
- **`1` has no constant in `cli.py`** — the plan declares it for "completed with recorded degradations",
  but no CLI code path returns it today. **UNVERIFIED**: do not treat exit 1 as a supported signal until a
  unit implements and tests it.
- `3` is doing double duty: it is the plan's "budget exhausted" code **and** the code every
  placeholder subcommand returns (`resextract mine` → `3`, message names the owning batch; U0.3, U0.7).
  Distinguish them by reading stderr, not by the number.
- `doctor` returns `0` only when **no core leg** is down; any core leg down → `2` (optional legs never
  fail the doctor — `src/resextract/doctor.py:314`).
- A stage that records degradations (unparseable model output, `fast_empty` search, truncated answer)
  **records them in the journal and the report** — that is where degradation is visible today, not in
  the exit code (U0.2, U0.3, V3).

---

## 3. Where state lives

Everything is under the workspace root; **nothing is written outside it** (AGENTS.md "Hard constraints").

| Path | Holds |
|---|---|
| `state/state.sqlite` | the store: `runs`, `candidates`, `claims`, `evidence`, `verdicts`, `lanes`, `lane_candidates`, `dockets`, `web_sources`, `search_health`, `rework`, `targets` + `schema_version` (12 application tables; schema **v2**, U0.10). WAL mode. |
| `state/journal/` | the append-only hash-chained journal: every model turn, tokens, `reasoning_content` when present, tool calls, degradations. Tamper-evident (`journal.verify()` → `(False, 2)` on tamper; U0.3, V0). |
| `state/logs/` | per-unit evidence logs, red→green captures, probes, migration reports. |
| `state/kg/` | graphify graphs (`state/kg/duval/graphify-out/graph.json`), semantic passes, fixtures. |
| `state/staging/` | normalised copies of unsupported-but-admitted files (`state/staging/duval/`). |
| `state/lanes/` | `state/lanes/duval/lanes.json` + `LANES.md` (U4.2). |
| `state/mine/` | the miner's resume index (`state/mine/index/<hash>.json`) — an unchanged hash means zero re-mining (U2.1, V2). |
| `state/webcache/` | fetched web content keyed by **URL** (the *content* hash is only what `refresh()` compares; correction (m)). |
| `state/verify/`, `state/refresh*/`, `state/verify-docket*/` | verifier and fixture scratch; safe to prune, not safe to cite as production state. |
| `dockets/<target>/<slug>/` | the deliverable: `MANIFEST.json`, `ITEM.md`, `CLAIMS.md`, `EVIDENCE.md`, `PRIOR_ART.md`, `REFERENCES.*`, `RESULTS.md`, `METHOD.md`, `CHECKLIST.md`, `OPEN_QUESTIONS.md`, `UPDATE_BACKLOG.md`, `HISTORY.md`, `material/`, `web/`, `repro/` (U5.2). |
| `orchestration/STATUS.md` | the **live ledger** — batch/unit table and evidence digest. |
| `orchestration/VERDICTS.md` | every verifier verdict (V0, V1, V3, V7, V2, …). |
| `orchestration/handoffs/<UNIT>.json` | each unit's forced report-back: status, artefacts, evidence, blocker, next hint. |
| `orchestration/units/<UNIT>.md` | each unit's persisted card. |
| `docs/` | the spec of record (`PLAN.md`), the verified corrections (`PLAN_CORRECTIONS*.md`), the target policy and secret-scan policy, and this pair of docs. |
| `config/` | `resextract.toml` (stage policy), `targets.toml` (registered targets + admission policy). |

**Auditing state:** `.venv/bin/resextract status --json` for the store; the `journal` table for what
happened; `orchestration/handoffs/*.json` for what each unit claimed. Absence of a handoff is **not**
evidence of success (`orchestration/STATUS.md`).

---

## 4. Secret-scan policy for commits

Full policy: [`docs/SECRET_SCAN_POLICY.md`](SECRET_SCAN_POLICY.md). The rules to operate by:

- **Scan the staged bytes** (`git diff --cached`) against six patterns: `sk-[A-Za-z0-9_-]{20,}`,
  `okr_[A-Za-z0-9]{16,}`, `AKIA[0-9A-Z]{16}`, `-----BEGIN [A-Z ]*PRIVATE KEY-----`,
  `ghp_[A-Za-z0-9]{20,}`, and the marker `Authorization: Bearer `.
- **The rule is value-based, never path-based.** No file and no directory is exempt. A recorded
  synthetic value passes wherever it appears (including inside a completed unit's evidence record); a
  real credential fails in every file, including the test files that define fixtures.
- **Never edit a completed unit's evidence to satisfy the scanner.** If a handoff contains a value that
  is not on the recorded set, investigate the value — do not rewrite the evidence
  (`docs/SECRET_SCAN_POLICY.md`).
- **Fixture secrets must be assembled at runtime** from non-secret-shaped pieces, so source bytes do not
  match the patterns while the runtime value keeps the shape the test exercises (U0.6).
- **Adding or removing a recorded value requires a handoff entry naming the value and the test that
  legitimises it**, plus an update to the policy file. "It is only a fixture" is not sufficient.
- A secret-shaped path is **refused from `material/`** and is not even hashed into a docket
  ([`docs/SECRET_SCAN_POLICY.md`](SECRET_SCAN_POLICY.md); U5.1, U5.4, U5.5).

---

## 5. Commit / checkpoint discipline

1. **Stage an explicit path list.** Never `git add -A`; never a glob into a tree a verifier is currently
   reverting (`orchestration/STATUS.md` "Standing constraints").
2. **A file under an active revert cycle is never staged.** Capturing a reverted guard bakes a **silent
   regression** into history and makes it look intentional. Both checkpoint commits in this build
   deliberately excluded trees owned by units that were mid-revert (U0.11; `orchestration/STATUS.md`
   "Checkpoint 2").
3. **A checkpoint is not a promotion.** Write in the commit message and the ledger what it captures and
   what it deliberately excludes.
4. **Run the secret scan on the staged bytes before committing** (§4). A refusal is a valid outcome —
   U0.5 staged its path list correctly, hit 10 pattern-matched diff lines, and **refused the commit**
   rather than self-exempt (U0.5 → U0.6).
5. **Record the commit sha in the handoff** (`artifacts` or `evidence`), and re-run the scan if further
   handoffs are staged in the same commit (U0.6's hint).
6. **Restore every guard file to its exact original sha256** after a red→green capture, and verify with
   `sha256sum -c` (V7 check 2). Run captures with `PYTHONDONTWRITEBYTECODE=1` + a `__pycache__` purge
   (V3's stale-`.pyc` gotcha).

---

## 6. Boundaries — what an operator must not do without explicit approval

- **No writes into a target repo.** `/home/zer0null/Duval` and every other registered target are
  strictly read-only: no writes, no `git` state changes, no hooks installed inside them (AGENTS.md;
  `docs/PLAN.md` §"Hard constraints").
- **No writes outside this workspace** (`/home/zer0null/reserach extarctor`).
- **No systemd unit is enabled.** The refresh timer and any `deploy/` unit files are to be **created but
  never enabled** without explicit user approval (plan §5, §10 batch 7). Note: `deploy/` **does not
  exist** at this reading — U7.2, the unit that owns the staged units, has persisted no card and no
  evidence.
- **No DSH plugin is mounted and no DSH service is restarted** without explicit approval.
- **Do not restart the shared model server.** Occamy `:8012` is down; D1 settled the cause and escalating
  the restart is a **user** decision (D1; `orchestration/STATUS.md` "External blocker").
- **Never read `.worktrees/`.** It belongs to another actor's in-flight worktrees, is a pruned directory,
  and is never enumerated (U1.7R; V7 check 8; `docs/LIVE_TARGET_NOTES.md`).
- **Long-lived processes** (the dashboard) are started as **managed background jobs by the owning unit**,
  which verifies and reports the exact URL and stops the server afterwards. The orchestrating session
  never starts a server (AGENTS.md).
- **Zero LLM calls on a dead endpoint.** Pre-flight the Occamy probe and stop on anything but `200`
  (U1.1's hint; `ACCEPTANCE_PROTOCOL.md` §6 G1).

---

## 7. When something fails

- **`doctor` core leg down** → read `core_down`. Occamy down is `blocked` (environmental, escalate to the
  user); SearXNG timeout is retried **once** before being called down (U0.3).
- **Exit 3** → read stderr: either the subcommand is a **placeholder** (names its batch) or a budget was
  exhausted with work remaining (`partial`, resumable by content hash).
- **A stage produced no artefact** → check `state/logs/` and the journal first; then the unit's handoff
  in `orchestration/handoffs/`. If the handoff is a skeleton or absent, the work is **not evidenced** —
  re-delegate to a **fresh** unit carrying the failure evidence; a unit is never extended
  (AGENTS.md "Unit contract").
- **A docket fails `verify_docket`** → `problems` names the broken invariant (orphan claim, sha256
  mismatch, span outside the file). Fix the input, not the manifest; a docket whose manifest was
  hand-edited after a material copy has no integrity claim left (U5.2).
- **The target moved mid-run** → the run is **not sealed**: record both heads, mark the docket
  `needs_rework`, and do not report a clean acceptance (`ACCEPTANCE_PROTOCOL.md` §3; U5.5).
