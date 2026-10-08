# Orchestration status — Research Extractor

Rebuilt from the record by **`U8.56`** (scripted sweep over `orchestration/handoffs/*.json` +
`orchestration/units/*.md`, plus the bounded ledger tail). Spec of record:
[`docs/PLAN.md`](../docs/PLAN.md) · ledger: [`docs/PLAN_CORRECTIONS.md`](../docs/PLAN_CORRECTIONS.md) ·
lessons: [`docs/LESSONS.md`](../docs/LESSONS.md) · handoff contract: [`AGENTS.md`](../AGENTS.md).

> **One-line state:** the *deliverable* is verified and reproducible on disk; the *acceptance
> criteria* are **not met** and cannot be met from here — the two external dependencies are down and
> the store holds **0 claims / 0 verdicts / 0 evidence**, so every verdict is **`UNVERIFIED`**.

## 1. Goal, and the two external blockers

**Goal:** mine a target repo into claims, verify them against evidence, and emit a self-verifying
docket. **§1.3 of the plan is NOT met and cannot be met from here** — with 0 claims, 0 verdicts and 0
evidence, no verdict can be anything but `UNVERIFIED`.

| Blocker | Observed | Durable fix | Status |
|---|---|---|---|
| **Occamy** `192.168.2.168:8012` | `curl` → **`000`** in **~1 ms** (`connection refused`), re-probed `U8.56` | `gpus`-host `--mem-fraction-static` **0.50 → ~0.60** | **HELD FOR THE USER — not executed** |
| **SearXNG** `127.0.0.1:8080` | degraded / denying access | — | **HELD FOR THE USER** |

`gx10-occamy-nvfp4.service` is crash-looping on an SGLang KV-cache sizing guard (min viable
`0.4993`, drifting toward the configured `0.500`); a bare restart is a coin flip. **No unit may touch
the GX10 or restart the service.** Every model-dependent *and* search-dependent leg stays unproven.

## 2. Deliverable — verified state (measured on disk, `U8.56`)

| Docket | `MANIFEST.json` sha256 | files | `verify_docket` |
|---|---|---|---|
| [`dockets/duval/duval-replay-material`](../dockets/duval/duval-replay-material) | `ce45766d4ac845ed83432e876b0e424c038f5453bf66570d52ec6df599f99da4` | 30 | **`ok=True`, `problems=[]`** |
| [`dockets/duval/duval-u55-pinned`](../dockets/duval/duval-u55-pinned) | `445032f78851b8171c00dca3d95d7ed6660dbf36d903bc156027c11b44a33a07` | 29 | **`ok=True`, `problems=[]`** |
| [`dockets/_smoke`](../dockets/_smoke) | `41ec711a4324eb9893b6f031c10a647f21e1cb3521ca73a8e8eb168522b283c6` | 31 | **`ok=False` — by design** |

- The replay docket **exists**, is self-contained, and **`verify_docket` returns `ok=True` with
  `problems=[]`**.
- **`_smoke` is the frozen backward-compatibility witness** — `ok=False` on its known CONFIRMS
  problem (`claim C1: standing CONFIRMS contradicts its backing producer 'unknown'`). That is the
  point: *"a compatibility guarantee is about readability, not approval."* The failure is a
  **compatibility contract**, not a regression.
- **Measured twice.** A sibling unit independently recovered `ok=False` for `_smoke` with the same
  known CONFIRMS problem; `U8.56` re-ran all three and got the same three verdicts.
- **A docket-hash contradiction between two reports was resolved as a recipe difference** —
  parent-dir roll-up vs per-file bytes. One anomalous value was **falsified**: the two dockets hold
  **30 vs 29 files**, so any recipe claiming they hash identically is measuring the wrong thing.

## 3. Unit table — where the build stands

Sweep over the **192 handoffs** and **178 unit cards** on disk (`U8.56`).

| Shape | Counts |
|---|---|
| **status** (unit shape, 166 handoffs carry it) | **done 142** · **partial 23** · **failed 1** |
| **overall** (verdict shape, 55 handoffs carry it) | **pass 33** · **partial 18** · **fail 4** |
| **partial, either shape** (union) | **35 units** |
| **failed, either shape** (union) | **5** — `U0.5`, `V2`, `V5.20`, `V5D`, `V8.21` |
| **missing handoff for an existing card** | **1** — `U1.7` |
| **died without report** | **1** — `U1.7` (card on disk, no handoff; recovered by `U1.7R`) |

- **Verification record: 4 FAIL · 7 PARTIAL · rest PASS** (the last verifier sweep). A **PARTIAL has
  consistently meant *"a statement corrected against its measurement"***, **not** a broken artifact.
- `V2`'s FAIL (replay rows indistinguishable from mined rows) was **genuinely closed by `V2S`**; the
  remaining `fail` values are historical or in-family, not open defects.
- **`running` means "launched, no usable handoff on disk yet"** — a statement about evidence, not
  about health. *(No unit is pre-credited from a card's own claim of its status.)*

## 4. The record's state

- **`docs/PLAN_CORRECTIONS.md`**: **105 entries**, last letter **`(da)`**, next letter **`db`**
  (confirmed from the tail only — see §6c).
- **`AGENTS.md` contracts two handoff shapes**, both valid JSON: the **unit handoff**
  (`unit`, `status`, `artifacts`, `evidence`, `blocker`, `next_unit_hint`, `write_paths`) and the
  **verifier verdict** (`unit`, `overall`, `checks`, `blocker`, `next_unit_hint`, `write_paths`, …).
  A verdict-shaped handoff is **not** a defective unit report and is never rewritten into the unit
  shape.
- **The guard is the enforcement**: `tests/test_orchestration_handoffs.py` parses every handoff and
  fails on a *new* missing required key. Known shape gaps stay recorded in the frozen baselines under
  `state/logs/`.

## 5. The two known record defects and their repairs

| Defect | Shape | Repair |
|---|---|---|
| `U8.40.json` | valid JSON, **missing `blocker` / `next_unit_hint` / `write_paths`** | repaired by **`U8.47`** |
| `U8.43.json` | valid JSON, **missing the same three keys** | repair unit **`U8.52`** (now `done`; key set re-swept complete) |

**Cause:** an instruction that validated **`json.load` only**. **Corrected rule — validate parse AND
the contracted key set; add a live missing key, never baseline it.** (A baseline freezes a gap; it
must not be used to launder a new one.)

## 6. Mitigations now standing

- **(a) Write handoffs atomically:** temp file → validate **parse + keys** → `mv` into place. Every
  edit is re-validated.
- **(b) Partial-first is a result, and it is *proven* to work:** units that died mid-work left a
  **complete-shaped `partial` stub** on disk (7 complete-shaped stubs observed this sweep; `U5.16` is
  documented as dying before it could write its guards). Their deaths cost **work — not the record**.
- **(c) State the recipe with every count.** Four assert-count recipes were reported for one file;
  two docket-hash recipes for one docket. A count without its recipe is not evidence.
- **(d) A measurement is only valid at the sha it was taken at.** Handoff shas are re-taken, not
  inherited.
- **(e) Bounds are stated as work calls with the report-back excluded**, and measurement mandates
  need **~26–30**.
- **(f) HELD FOR THE USER — nothing executed:** the Occamy memory fraction; any systemd timer/watch
  daemon; anything touching DSH; whether `dockets/` should be versioned (currently gitignored via an
  **anchored `/dockets/`**, so root dockets stay ignored); and whether a unit's **own** handoff should
  be exempt from read-before-write.

## 7. Next structural steps

1. **Store-row refresh.** The `dockets` row for the replay docket still stores
   **`C-curated = CONFIRMS`** with **no producer key**, so a DB consumer sees the pre-repair defect
   even though the on-disk manifest verifies. It needs a **declared quiet window** because every card
   asks units to report the store's sha.
2. **Checkpoint 4.** Standing assertion: **`config/graph_pin.toml` appears in `git ls-files` after
   staging.** *(Currently on disk (3235 B) but **not** tracked — `git ls-files config/` lists only
   `resextract.toml` and `targets.toml`.)* It follows checkpoint 3's deferred set:
   `docket/**`, `dashboard/**`, `assess/**`, `run.py`, `cli.py` and their tests.

## Standing constraints (apply to every unit)

- Target repos are **strictly read-only** (`/home/zer0null/Duval` included). Nothing is written
  outside this workspace.
- **No systemd unit enabled, no DSH plugin mounted, no DSH restart** — without explicit user approval.
- No unit is ever extended; a failure is re-delegated to a **fresh** unit carrying the failure
  evidence. **`partial` is a valid result.**
- A file under an active revert cycle is never staged; checkpoint units stage an explicit path list.
- **A missing closing message is not missing artifacts** — check the disk before re-doing a recovery.
