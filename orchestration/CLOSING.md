# CLOSING — Research Extractor · unit **U8.77**

_Closing measurement taken 2026-10-08 11:14. Every number below was measured in this unit unless marked
**(prior unit)** — those are cited from the unit handoffs in [`orchestration/handoffs/`](orchestration/handoffs/)
and the logs under [`state/logs/`](state/logs/). No new work was started; nothing was fixed._

## 1. What was asked, and what was delivered

| | |
|---|---|
| **Asked** | A research extractor that runs against the acceptance target, with a pipeline, a dashboard, and a publication-grade docket/folder structure with all material copied in. |
| **Pipeline** | [`src/resextract/`](src/resextract/) — `run`, `assess`, `refresh`, `docket` (assemble/materialize), `dashboard`, `cli`, `doctor`. |
| **Dashboard** | Shipped in [`src/resextract/dashboard/`](src/resextract/dashboard/); exact URL verified and reported by its owning unit (not re-measured here). |
| **Dockets** | [`dockets/duval/duval-replay-material/`](dockets/duval/duval-replay-material/) (deliverable), [`dockets/duval/duval-u55-pinned/`](dockets/duval/duval-u55-pinned/), [`dockets/_smoke/`](dockets/_smoke/) — material copied in, manifests present. |
| **Acceptance target** | `duval` / Consonance, **AGPL-3.0**. `/home/zer0null/Duval` is strictly read-only. |

## 2. What is verified

| # | Claim | Evidence (measured 2026-10-08 11:14 unless marked) |
|---|---|---|
| 1 | Deliverable docket verifies | `verify_docket("dockets/duval/duval-replay-material")` → **`ok=True`, `problems=[]`** |
| 2 | Pinned sibling docket verifies | `verify_docket("dockets/duval/duval-u55-pinned")` → **`ok=True`, `problems=[]`** |
| 3 | Smoke docket fails **by design** | `verify_docket("dockets/_smoke")` → **`ok=False`**, 1 problem: *a standing `CONFIRMS` contradicts its backing producer `unknown` — a non-model run may not assert `CONFIRMS`* — i.e. the **claim cap** firing correctly at the verify boundary |
| 4 | Manifest shas | `ce45766d…` (replay), `445032f7…` (u55-pinned), `41ec711a…` (`_smoke`) — all three re-hashed and unchanged |
| 5 | Store mirrors byte-identical & idempotent | **(prior unit)** re-materialisation from a **copy** of the store → 0 changed / 0 added |
| 6 | Claim cap at **both** boundaries | render boundary via `materialize` **(prior unit)**; verify boundary = row 3 above (measured now) |
| 7 | Read path manifest-authoritative | manifest sha256 gates every read; `source` provenance carried through **(prior unit)** |
| 8 | Pin policy | pinned docket admits pinned sources only, `target.head_sha` + freshness honoured **(prior unit)** |
| 9 | Guard, torn-write detection | **13 torn writes reliably caught / 0 false positives** **(prior unit)** |
| 10 | 33 `raises` closed | each closed with a three-legged red (red → fix → green) **(prior unit)** |
| 11 | Ledger, self-correcting | [`docs/PLAN_CORRECTIONS.md`](docs/PLAN_CORRECTIONS.md) — **125 headings / 2,907 lines**; each entry is a statement replaced by its measurement. *Contents deliberately not restated here.* |
| 12 | Checkpoint 4 committed | `git log -1` → **`9d256ba`** "Checkpoint 4: verified artifact, hardened enforcement, settled record" — **440 files, +70,954 / −435**; revertible via `git revert 9d256ba`; `state/state.sqlite` **untracked** and gitignored (`.gitignore:7` → `/state/`) |

## 3. The verification record

**4 FAIL · 7 PARTIAL · rest PASS.** A **PARTIAL was never a broken artifact** — it was a *statement*
that did not survive re-measurement and was rewritten to match what was actually measured, with the
correction recorded in the ledger. A FAIL was re-delegated to a fresh unit carrying the failure
evidence, per the unit contract; none of the 33 `raises` was closed by weakening the assertion.

## 4. What is NOT done, and why

**§1.3 is not met and cannot be met from inside this workspace.**

Store contents, read **via a copy** at [`state/verify/U8.77/state.copy.sqlite`](state/verify/U8.77/state.copy.sqlite)
(never `immutable=1`; the copy exists precisely so the live store is never opened):

| table | rows |
|---|---|
| `claims` | **0** |
| `verdicts` | **0** |
| `evidence` | **0** |
| `candidates` | 10 |

With 0 claims and 0 verdicts there is nothing to confirm. **Every verdict is `UNVERIFIED`.**

Two external blockers, both user-owned, both measured this unit, **neither attempted**:

| Blocker | Measured | Durable fix (held for the user, **not executed**) |
|---|---|---|
| **Occamy** `192.168.2.168:8012/v1/models` | **HTTP `000`** — connection refused after **0.002 s** | gx10-host `--mem-fraction-static` **0.50 → ~0.60** |
| **SearXNG** `127.0.0.1:8080` | root **`200` in 0.002 s**, but search path degraded: `/search?q=…&format=json` → **`000` after the 5.00 s timeout**, HTML search `200` in **4.86 s** | repair the search backend so queries return inside the timeout |

**No evidence row can exist until both change** — `evidence` will stay at 0 regardless of how many
`run`s are attempted, because there is no model to produce it and no search to feed it.

## 5. Decisions held for the user

1. **Occamy `--mem-fraction-static` 0.50 → ~0.60** on the gx10 host — the single durable fix for
   blocker A. **Not executed.**
2. **SearXNG repair** (search path timing out). **Not executed.**
3. **Should `state/state.sqlite` be committed?** — *my recommendation: **no**.* It is derived state,
   currently `untracked` and gitignored via `.gitignore:7`. Committing it would put a mutable
   176 KB binary into history and fight every future mirror check.
4. **`tests/state/backups/v3.sqlite.v3.bak`** — committed by checkpoint 4's `tests` sweep and, in this
   unit's scan, the **only** never-commit-shaped path inside `9d256ba` (1 of 440). It should be moved
   out of the test tree and the reference dropped.
5. **Any systemd timer, watch daemon, or DSH-facing change** — **none executed**; each needs explicit
   user approval under the hard constraints.
6. **Nothing else** — no `AGENTS.md`, `docs/**`, `src/**`, `tests/**`, `config/**`, `dockets/**`,
   baselines, or other handoff was touched by this unit. Read-only `git` only; no state change.

## 6. What I would do next, if the switches are flipped

1. Re-run `run` against **`duval`** with Occamy answering `200` on `/v1/models`.
2. Expect the **first real `evidence` rows** and the first claims that are capable of `CONFIRMS`
   rather than `EXTENDS`/`UNVERIFIED`.
3. Re-derive the docket (`materialize`), re-run `verify_docket` on all three, and re-check the three
   manifest shas above — replay and u55 must stay `ok=True []`, `_smoke` must stay `ok=False`.
4. Land the **deferred schema item**: typed `assessed_by` / `mined_by` under `resextract/docket/2`, so
   a mechanically verified `file_fact` can be told apart from an unverified one. This is the same
   defect the `_smoke` red names, and it is the one item that keeps a correct docket from being
   *distinguishable* rather than merely *valid*.
