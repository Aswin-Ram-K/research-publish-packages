# ACCEPTANCE_PROTOCOL — how the end-to-end acceptance run is executed and what evidence it must produce

**Status of this document:** written by unit **U8.1**. It is a **synthesis**, not an invention: every
gate, number and limitation below is derived from the handoffs, verifier verdicts and corrections already
on disk, and each is cited to the unit or verifier that produced it. Where the evidence for a step does
not exist, the step is marked **UNVERIFIED** rather than filled in.

**Spec of record:** [`docs/PLAN.md`](PLAN.md) §1 (success criteria 1–9), §4 (stages), §5 (continuity),
§6 (dashboard), §7 (failure modes), §8 (Phase-1 integration gate, line 256), §10 (unit batches).
**Live ledger:** [`orchestration/STATUS.md`](../orchestration/STATUS.md).
**Verdicts:** [`orchestration/VERDICTS.md`](../orchestration/VERDICTS.md).
**Deviations from the plan:** [`docs/PLAN_CORRECTIONS.md`](PLAN_CORRECTIONS.md) (a–p),
[`docs/PLAN_CORRECTIONS_PART2.md`](PLAN_CORRECTIONS_PART2.md) (q–y).
**Target environment:** [`docs/LIVE_TARGET_NOTES.md`](LIVE_TARGET_NOTES.md),
[`docs/TARGET_POLICY.md`](TARGET_POLICY.md).

---

## 1. Purpose and scope

### What an acceptance run proves

1. Every dependency the run needs is **green or named**: `resextract doctor` classifies each leg
   `core` / `optional`, and a core leg that is down stops the run rather than degrading it silently
   (`docs/PLAN.md` §7; U0.3, [`handoffs/U0.3.json`](../orchestration/handoffs/U0.3.json)).
2. The pipeline stages each produced their recorded artefact, at a **known commit of the target**, with
   counts that match what the stage itself recorded (U1.1, U1.5, U2.1, U4.2, U5.3, U5.5, U7.1).
3. **No tracked content in the target was modified by us**, proven by HEAD and tracked-file diff being
   unchanged across the run (§4 below; U0.10, U1.5, U5.4, U7.1, V7).
4. Material carried into a docket is **commit-pinned or explicitly marked `unpinned`**, and every copied
   byte's sha256 matches the manifest (U5.4, U5.5; corrections (r), (s); V7 check 8).
5. Docket validity is machine-checked (`verify_docket`), including the orphan-claim and material-sha
   gates (U5.2, U5.5).
6. The run is **sealed**: quiescence asserted before, HEAD and untracked anchor identities re-verified
   after (§3; corrections (q), (u); V7 check 6).

### What an acceptance run explicitly does **not** prove

- It does **not** prove the target repo "was unchanged". It is being written by a foreign actor
  (`tools/selfbuild/loop.ts`) the whole time (`docs/LIVE_TARGET_NOTES.md`). It proves only that **we**
  changed no tracked content.
- It does **not** prove the target will be quiescent for the *next* run. A quiescent verdict is evidence
  about the window it covered, and a burst can begin immediately after it closes
  (`src/resextract/refresh/writer.py` docstring; correction (q); V7 check 6).
- It does **not** prove the model/semantic path. That path has never been independently reproduced and
  is currently **blocked** on the Occamy endpoint (§6; V1, V2).
- It does **not** prove anything about `.worktrees/`: that directory is a **pruned directory entry**,
  never enumerated, never read (U1.7R; V7 check 8; `docs/TARGET_POLICY.md` rules 1–2).
- It does **not** make findings "model-derived" while candidates carry no producer field (§2 P5).

### Acceptance is a two-unit activity

`docs/PLAN.md` §10 assigns `U8.2` the run and `U8.3` the **independent adversarial verification**: the
operator of the run may not also be the verifier (AGENTS.md "Verification independence"). This document
is the protocol both follow.

---

## 2. Preconditions — the gate list

Run every gate. A gate that fails stops the run; record the failure and the gate id in the handoff.

### P1 — `doctor` exit 0 with all **core** legs green

```bash
.venv/bin/resextract doctor --json; echo "exit=$?"
```

- **Pass condition:** `exit=0`, `"ok": true`, `"core_down": []`.
- **The core legs are named:** **Occamy**, **SearXNG**, **crawl bridge**, **graphify**
  (`src/resextract/doctor.py` `CORE`; U0.3). *Optional* legs are `docling bridge`, `renderers`,
  `dashboard port` — an optional leg down is reported, never a failure (U0.3; V0 check 3).
- **SearXNG intermittency is real:** U0.3 measured two consecutive live `doctor` runs 16 s apart where
  the second returned `SearXNG ReadTimeout` and exit 2, and a third 3 s later was green. **Retry once**
  before declaring a core failure (U0.3).
- **Current state — Occamy is DOWN, and that is `blocked`, not `broken`.** The U8.1 probe at unit start:
  `curl -sS -m 5 -o /dev/null -w '%{http_code}' http://serving-host/v1/models` → **`000`**
  (connection refused). D1 settled the cause: TCP **CLOSED** on `:8012` while ICMP is alive and every
  other service on the box (`:8000`, `:8010`, `:8013`, `:8090`) answers — the shared model server is
  down, not a network fault, and **no unit may restart it** (`handoffs/D1.json`;
  `orchestration/STATUS.md` "External blocker"). Consequence: **a run cannot proceed to any
  model-dependent stage.** Gate A/offline stages can; Gate B/C and any mining that needs the model
  cannot. Report `blocked`, never `broken` (V1's Gate B wording; V2's model-path wording).
- **Optional, expected-red:** `docling bridge` DOWN and `renderers` missing `pdflatex`, `pandoc`,
  `tectonic` are the expected state (U0.3; correction (h)). Renderer-dependent export legs stay
  expected-red and must be named, not silently skipped (`docs/PLAN.md` §7).

### P2 — the store is at the current schema version and its rows match the ledger

```bash
.venv/bin/resextract status --json; echo "exit=$?"
```

- **Pass condition:** `exit=0`; `schema_version` = **2** (the current version — v1→v2 was additive,
  U0.10); `candidates.total`, `lanes.total`, `dockets.total` equal the ledger's recorded counts.
- **Measured state at the U8.1 reading** (read-only `sqlite3` against `state/state.sqlite`, plus
  `resextract status --json`): `schema_version 2`; `runs 4`, `candidates 10`, `claims 0`, `evidence 0`,
  `verdicts 0`, `lanes 5`, `dockets 2`, `web_sources 0`, `search_health 0`, `rework 0`, `targets 0`;
  12 application tables + `schema_version` = 13 `sqlite_master` tables.
  The ledger's older figure (`orchestration/STATUS.md` evidence digest, U0.10: `dockets 1`) is **stale**
  — U5.3/U5.5's live dockets ran after it. **A mismatch is a gate failure, not a cosmetic drift**: it
  means the store the run reads is not the store the ledger describes.
- Note `dockets.total` is **2** and `lanes.by_status` is `draft 5` / `by_type` `report 5`: there are
  **0 dockets at `status: ready`**, which is what `docs/PLAN.md` §1 criterion 3 requires. This gate
  checks consistency; criterion 3 is a *stage* acceptance condition (§5 A6), currently **not met**.

### P3 — the target is registered read-only and the target-policy assertions pass

```bash
.venv/bin/python -c "
from resextract.kg.policy import TargetPolicy, policy_audit
p = TargetPolicy.from_config('config/targets.toml', 'duval')
r = policy_audit('<workspace>', p)
print('admitted', r['totals']['admitted'], 'rejected', r['totals']['rejected'])
print('violations', r['violations'])
assert r['violations'] == [], r['violations']
"
```

- **Pass condition:** `violations == []` and every asserted path exists **and** is admitted.
- **The five asserted paths and their real byte sizes** (`handoffs/U1.7R.json`; `docs/TARGET_POLICY.md`):

  | path | bytes |
  |---|---|
  | `.lane-j-scratch/monograph.txt` | **83,832** |
  | `.lane-j-scratch/consonance-external-evidence-2026-10-07.md.txt` | **159,408** |
  | `README.md` | **19,578** |
  | `CITATION.cff` | **973** |
  | `docs/FINDINGS.md` | **27,401** |

  These are the **densest publishable material in the repo** and exist only as untracked scratch, which
  is why the policy asserts them explicitly (U1.7R; `docs/TARGET_POLICY.md`).
- Live audit baseline: **537 admitted / 8 rejected**, `rejected_by_reason = {ignored_dir: 4, noise_dir: 3,
  skip_file: 1}`, `violations: []`, `.ci-trunk.txt` admitted at **281,253 B** via
  `graphify_predicate` (U1.7R).
- **`.worktrees/` is one rejected *directory entry*** (`source=noise_dir`, "never walked") because
  graphify prunes the whole subtree. It is **not** a file count. `docs/LIVE_TARGET_NOTES.md` line 19
  records the "441 files under `.worktrees/run-1/`" figure as a sibling's name-count that the reporting
  unit deliberately did not recurse; correction (u) and V7 check 8 repeat the caution. **Do not repeat
  441 as a file count.**
- Widening is a hard error: an `include` naming `.worktrees/`, `node_modules/` or `.git/` raises
  `PolicyWideningError` (U1.7R; `docs/TARGET_POLICY.md` rule 2, red→green verified).

### P4 — the target is registered read-only, and that registration is honoured

- **Pass condition:** `config/targets.toml` registers `duval` → `<workspace>` with the policy of
  P3, and no command in the run has write intent against the target root (`docs/TARGET_POLICY.md`;
  AGENTS.md "Hard constraints").
- This is asserted behaviourally by §4 (the zero-write proof), not by trust.

### P5 — the producer-labelling prerequisite (a HARD gate)

> **No docket may claim model-derived findings while candidates carry no producer/mode/model field.**

- **This gate is currently FAILING.** Verifier **V2** returned **`FAIL`** on the miner for exactly this
  reason: `candidates` and `runs` carry **no producer/model/mode field**; all 10 replay rows are stored
  as `state='mined'`; `report.json` has no `model` / `mode` / `producer` key. The only signals are the
  `run_id` string `live-u21-replay` and the `REPLAY ` title prefix (10/10) — **naming conventions, not
  fields** (`orchestration/VERDICTS.md` V2, "Replay vs mined — FAIL";
  [`handoffs/V2.json`](../orchestration/handoffs/V2.json)).
- **The exact missing fields:** `candidates.producer` / `candidates.mode` (+ `candidates.model`),
  `runs.model` / `runs.mode`, `report.json.mode` (V2).
- **Consequence for the run:** until those fields exist *and* a verifier confirms them, any docket whose
  provenance is candidate-derived must be labelled **`replay`/unpinned-provenance** and **must not** be
  reported as containing model-derived findings. V2's own instruction, verbatim in effect: *"Do not let
  the 10 replay rows reach a docket as mined evidence until a producer/mode field exists."* The fix is
  **queued** (§8, FAIL-pending-fix).
- Related, and also gating for honesty in §5 A3: `model_calls` is **misleading** — `_Meter.absorb`
  (`src/resextract/mine/candidates.py:307`) increments on *every* `usage_sink` record, which is emitted
  on success, on 4xx, and on exhausted transport failure. A zero-I/O client reports
  `model_calls=2, total_tokens=240`; so `model_calls=5` reads as five real calls to an endpoint that was
  refusing connections (V2, "`model_calls` — FAIL"). Do **not** cite `model_calls` as a request count in
  the acceptance report; cite the endpoint probe and the journal instead.

### P6 — the run's own write paths are outside the target

- **Pass condition:** every output path is under the workspace (`--out state/...`, `--docket-root
  dockets/...`) and no command's argument list names a target path as a *destination* (U5.3 dry run
  "wrote nothing"; U5.1 `outside_target_root` refusal).

---

## 3. The moving-target protocol — the sealed window

**Requirement.** An acceptance run over `<workspace>` must open a **sealed window**: assert
quiescence *before* it acts, and **re-verify** the target's identity *after* it acts. A single pre-run
check cannot certify a run.

**Why — measured.** Two live windows (5 s `11:18:31Z–11:18:36Z` and 25 s `11:18:36Z–11:19:01Z`) both
returned `quiescent`, `files_touched_in_window = 0`, with 440/440 tracked files watched. The reflog for
the same repo shows **8 HEAD moves inside `11:01:38Z–11:04:38Z`** (10 inside `10:00Z–11:20Z`) and the
newest tracked mtime was `2026-10-08T11:04:38Z`: the burst ended ~14 minutes before the windows opened.
The actor is **bursty**, so individual quiet windows read quiescent while the repo is in fact moving
about once every few minutes (V7 check 6; correction (q); `handoffs/U5.4.json`). U5.4's live statement
of "9 HEAD moves" is a **one-high overstatement** of the same burst — **8** is the corrected count
(correction (y), V7 check 6).

### S1 — pre-window: record HEAD and the anchor identities

```bash
git -C <workspace> rev-parse HEAD
git -C <workspace> status --porcelain
for f in .lane-j-scratch/monograph.txt \
         .lane-j-scratch/consonance-external-evidence-2026-10-07.md.txt \
         .ci-trunk.txt; do
  printf '%s  ' "$f"
  stat -c '%s bytes' "<workspace>$f"
  sha256sum "<workspace>$f"
done
```

- **Record:** HEAD; the porcelain lines; and for each **untracked-but-admitted anchor file** the run
  depends on, its identity — **size + sha256**.
- **The anchors and their recorded identities** (U1.7R, U5.5; `docs/TARGET_POLICY.md`):

  | anchor | bytes | sha8 at the U5.5 live run | pinnable? |
  |---|---|---|---|
  | `.lane-j-scratch/monograph.txt` | 83,832 | `033b1547` | **no** — untracked |
  | `.lane-j-scratch/consonance-external-evidence-2026-10-07.md.txt` | 159,408 | `d141f139` | **no** — untracked |
  | `.ci-trunk.txt` | 281,253 | `590e007e` | **no** — untracked; porcelain `?? .ci-trunk.txt` |

  These three cannot be pinned at any commit: `GitObjectSource('.ci-trunk.txt')` raises
  `PathNotFoundAtCommit`, and the same holds for everything under `.lane-j-scratch/` (correction (s),
  U5.4/U5.5). A tracked comparator, `README.md`, pinned at `5cdc471a` **equals** the working tree
  (`1f6bbdf6`, blob `2c34d208`, 19,578 B) — clean between bursts, so it is **not** evidence of safety
  (U5.4; `docs/LIVE_TARGET_NOTES.md`).

- **This is why recording size+sha256 is mandatory for the untracked anchors:** they are exactly the
  bytes no commit describes, so the only seal available for them is the identity we measured.

### S2 — in-window: assert pinned quiescence

```bash
.venv/bin/python -c "
from resextract.refresh.writer import assert_pinned_quiescent
s = assert_pinned_quiescent(
    '<workspace>',
    pinned_paths=('.lane-j-scratch/monograph.txt',
                  '.lane-j-scratch/consonance-external-evidence-2026-10-07.md.txt',
                  '.ci-trunk.txt'),
    window_s=25.0, allow_active=False)
print(s.as_dict())
"
```

- **Pass condition:** `verdict == 'quiescent'` and no `TargetBusyError`. `allow_active=True` is available
  only by explicit opt-in and **disqualifies the run from "clean acceptance"** (writer.py docstring).
- **Describe the check as a *requirement*, not as a solved problem.** The requirement is: quiescence over
  **the tracked files *and* the identity of the untracked-but-admitted paths the run depends on**.
  `assert_pinned_quiescent` (`src/resextract/refresh/writer.py:854`) and the
  `detect_concurrent_writer(..., pinned=...)` path exist in the working tree at this reading, and the
  module docstring names the defect it closes as **"defect U7.2-1"** (git reported an existing untracked
  directory as one `?? dir/` entry, so a write *inside* `dir/` used to read quiescent — correction (u);
  V7 check 6's "new gap found"). Its mtime is `2026-10-08 06:26:31 -0500`.
- **Current state, honestly:** **`U7.2` has persisted no unit card and no evidence.**
  `orchestration/units/U7.2.md` does not exist and
  [`handoffs/U7.2.json`](../orchestration/handoffs/U7.2.json) is a **pending skeleton**
  (`"occamy_probe_http": "pending"`, all test and red→green fields `"pending"`, `tool_calls: 0`). No
  verifier has checked the fix. Therefore, **until U7.2 reports and a verifier reproduces its red→green,
  the untracked-path blindness must be treated as a KNOWN LIMITATION (§7)** and the sealed window must be
  accompanied by the manual anchor identity check of S1/S3 — which is done *outside* the detector and is
  therefore not subject to the blindness.

### S3 — post-window: re-verify HEAD **and** every anchor identity

```bash
git -C <workspace> rev-parse HEAD
git -C <workspace> status --porcelain
sha256sum "<workspace>" \
          "<workspace>" \
          "<workspace>"
```

- **Pass condition:** HEAD identical to S1 **and** each anchor's size+sha256 identical to S1.
- **If either moved, the run is NOT sealed.** Then:
  1. record **both** head values (`head_start`, `head_end`) in the acceptance report;
  2. mark the affected docket **`needs_rework`** — this is the designed behaviour, not an error: the
     offline-injected-HEAD test proves `window_sealed=False` ⇒ `needs_rework` even though the docket is
     still produced (U5.5 `red_green_detail.guard_2`);
  3. **do not report the run as a clean acceptance.** U5.5's live window shows the correct shape:
     `window_sealed: true`, `needs_rework_marked: false`, `head_start == head_end`.
- **Known unavoidable gap:** a writer that mutates a file and restores it byte-identically inside the
  window is undetectable by any before/after comparison, and a burst can begin immediately after the
  window closes (writer.py "Known limits"; U7.2 `limitations_documented`). State this in the report; do
  not claim the seal is absolute.

---

## 4. The zero-write proof, given a foreign writer

### The claim we can actually make

> **No tracked content in `<workspace>` was modified by this run.**

### How it is evidenced

1. **HEAD unchanged across the run** — `git rev-parse HEAD` before (S1) and after (S3). Every unit that
   ran read-only reproduced this: U0.10 (`5cdc471a…` unchanged), U1.5 (`b44e0e1…` at live run, identical
   before/after the run), U2.1 (`b44e0e1…`), U5.4 (HEAD stable across both windows), U7.1
   (`b2bade3e…`), V7 (`5cdc471a…`).
2. **`git diff --stat` for tracked files unchanged across the run.**
   ```bash
   git -C <workspace> diff --stat
   git -C <workspace> status --porcelain
   ```
   **Pass condition:** `diff --stat` empty (no tracked modifications) and porcelain identical to the
   baseline recorded in S1. The only porcelain entries any unit has ever seen are the foreign actor's
   **pre-existing** untracked paths — `?? .ci-trunk.txt`, `?? .lane-j-scratch/` — which were present
   *before* the units ran (U0.10's explicit note; U1.5; U2.1; U5.4; U7.1).
3. **Every copy path is a *read*.** Commit-pinned material is read from the object store with
   `git cat-file blob <commit>:<path>`, identity from `git ls-tree -z`; **there is no working-tree
   fallback** — a path absent at that commit raises `PathNotFoundAtCommit` (U5.4;
   `src/resextract/docket/git_source.py` docstring). U5.4 proved it with a spy on `builtins.open`
   recording **zero** opens under the repo root. URL material is read by `Fetcher` into
   `state/webcache/` (U3.2, U3.3): cache hits perform **0** HTTP calls (V3's independently counted
   transport). U5.1's copy engine only ever reads the source and writes the destination under
   `dockets/`.
4. **All tool output is written with `--out` outside the repo.** graphify's `--out DIR` lands at
   `DIR/graphify-out/` and the `--out` values used are all `state/...` paths (U1.1, U1.5; correction (j)).
   The materializer takes `--docket-root dockets/...` and its dry run wrote nothing (U5.3:
   `dry_run_wrote_nothing: true`).
5. **mtime sweeps are supportive, not conclusive.** U5.1 ran
   `find <workspace> -newer state/logs/U5.1-marker -not -path '*/.git/*' | wc -l` and saw
   `mtime_new: 0`; U4.2 characterised the foreign writer the same way.

### The confounder — untracked churn belongs to the foreign actor

- The target's own self-build loop (`tools/selfbuild/loop.ts`, `tools/selfbuild/run.ts`) writes in bursts
  (`docs/LIVE_TARGET_NOTES.md`). Its known entries — **`.ci-trunk.txt`** (281,253 B) and
  **`.lane-j-scratch/`** (13–20 top-level entries depending on when it was counted; U1.5 said 20 files,
  U5.4 said 13 top-level entries) — are the **pre-existing baseline**, already `??` before any unit
  started (U0.10; U1.5; `docs/TARGET_POLICY.md`).
- A 25-minute mtime sweep by V1 showed `src/`, `tests/` and `.worktrees/engine-a/` churn from the
  actor's external pull — **not** from V1. V1 recorded explicitly: "no pre-session mtime baseline;
  HEAD+porcelain+tree is the operative proof" (V1, "Containment").

### What we must NOT claim

- ~~"the repo was unchanged"~~ — **false**; a foreign actor writes it continuously.
- ~~"the mtime sweep was empty"~~ — **false**; the actor's churn populates it. V1's sweep was non-empty.
- ~~"`.worktrees/` contains 441 files that we ignored"~~ — the number is a name-count from a sibling
  unit and the directory is a **pruned entry**, not an enumerated file list (U1.7R; V7 check 8;
  `docs/LIVE_TARGET_NOTES.md` line 19). Count **1** pruned directory entry if a count is needed.
- ~~"material is verifiable at commit X"~~ for an untracked path. It is not; it carries an explicit
  `unpinned` marker instead (correction (s); U5.5 emits the warning **per file**).

---

## 5. Per-stage acceptance steps

Each step: **command · expected artefact · pass condition**. Where the CLI has no entry point yet, the
command is the library call the units themselves used, and the CLI gap is flagged — `cli.py`'s
`IMPLEMENTED` set is `{doctor, status, materialize, serve}` — a sibling unit landed `serve`
(`src/resextract/cli.py:364`) **while this document was being written** — and the remaining **9** names
are placeholders that exit **3** with their owning batch (`src/resextract/cli.py:37–66`; U0.3, U0.7,
U5.3). *Concurrency note: this workspace is written by several units at once, so any "N placeholders"
figure here is a snapshot; re-read `cli.IMPLEMENTED` before relying on it.*

### A1 — Knowledge graph (code-only, at the recorded head)

```bash
.venv/bin/graphify extract <workspace> --code-only --out state/kg/duval-acceptance
sha256sum state/kg/duval-acceptance/graphify-out/graph.json
```

- **Expected artefact:** `state/kg/duval-acceptance/graphify-out/graph.json` (note the extra
  `graphify-out/` level — correction (j)).
- **Reference counts:** U1.1 built **2685 nodes / 7102 edges / 128 communities** in **3 s** with
  `built_at_commit = 6deaed07af0d998d1672fe3f1ab1579e6ba0cdc4`; V1's independent rebuild at the moved
  head `b44e0e1` gave **2695 / 7151 / 119** in **2.75 s**. **The counts are head-dependent** — the
  +10 n / +49 e / −9 comm difference is the external `git pull --ff-only`, not drift (V1, Gate A). The
  acceptance run must therefore record the head it extracted **at** and compare against a rebuild at
  the *same* head.
- **Pass condition:** exit 0; the graph's `built_at_commit` equals the HEAD recorded in S1; pollution is
  zero — **0 nodes** from `.worktrees/`, `node_modules/`, `.tmp-consonance/`, `.consonance/`, and
  `node_modules_nodes = 0` (U1.1, reproduced by V1). `.lane-j-scratch/` contributes **23 nodes**
  (~0.86%) and that is expected and admitted, not pollution (U1.1; V1).
- **Shape checks:** top-level keys are `nodes, links, hyperedges, directed, graph, multigraph,
  built_at_commit` — edges live under **`links`**, not `edges` (corrections (c), (f); V1). Node kind is
  `file_type` ∈ {`code`, `concept`, `rationale`}, **not** `type` (correction (b)). `directed` was
  **false** for a pure-AST extraction, so direction must be read from the file, not assumed (U1.2).
- **`--no-viz` is NOT an `extract` flag** in graphify 0.9.80 — it sits under `cluster-only` and
  `export html`, and `extract` silently accepts it as a no-op (correction (a); V1). Do not pass it here.
- `resextract target add` is a **placeholder** today (batch 1) — registration is via
  `config/targets.toml` (U1.7R).

### A2 — Staging corpus + coverage (the 84.99% → 97.58% claim, and what it means)

```bash
.venv/bin/python -c "
from resextract.kg import ingest
r = ingest.coverage_audit('<workspace>')
print(r.to_dict() if hasattr(r,'to_dict') else r)
"
# then the staging run (U1.5's exact argv is persisted in orchestration/units/U1.5.md)
sha256sum state/kg/duval/graphify-out/graph.json
```

- **Expected artefacts:** `state/staging/duval/MANIFEST.json` + `state/staging/duval/docs/`;
  the merged graph.
- **The two numbers mean different things — say which one you are quoting:**
  - **84.99%** is **repo-native coverage**: of **533 files**, **453 supported** and **80 unsupported**;
    top gaps `jsonl ×38`, `xml ×29`, `rels ×4`, `cff ×1`, `patch ×1` (U1.4). It is the share graphify can
    see on its own.
  - **97.58%** is **graph-reachable coverage after staging**: **457 supported + 67 newly normalised of
    537 files**, measured **at the moved HEAD** (U1.5). `coverage_before_pct 84.99` →
    `coverage_after_note: "graph-reachable 97.58% …; repo-native coverage_pct unchanged at 85.1%"`.
    Staging does **not** fix graphify's own blindness; it adds copies the graph can reach.
- **Reference scale:** **221 docs copied**, **22,607,550 B staged**, normalised `jsonl 38 / xml 29`,
  skipped-by-reason `{covered-by-graphify: 236, ignored_dir: 4, noise_dir: 3, skip_file: 1,
  unsupported-no-normalizer: 13}`; merged graph **2706 nodes / 7129 edges / 133 communities**
  (U1.5).
- **Pass condition:** exit 0; `violations`-free staging; the merged graph's node count is
  `code_graph + semantic` and the **code graph file's sha256 is unchanged** by the merge
  (U1.5: `code_graph_unchanged: true`).
- **Remaining uncovered after staging:** `.rels 4`, `.cff 1`, `.patch 1` — no normaliser exists.
  Report them; do not round them away (U1.5).
- **Normalisation caveats:** 3 cache/vendor dirs pruned (`.git/`, `.worktrees/`, `node_modules/`),
  4 dirs excluded by `.gitignore`/`info-exclude` (`.consonance/`, `.tmp-consonance/`, `scratch/`,
  `tmp/`), no symlinks, no unreadable paths; `.bmp` is unsupported while `png/jpeg/gif/webp/svg` are
  supported (U1.4).
- **Scope note:** correction (k) records that the plan's Batch-1 row assigned `U1.2` to a notebook
  normalizer and **no such unit exists**; notebook handling was actually delivered inside `U1.4`'s
  `ingest` (its red→green guard reverts `_render_code_cell` and loses code-cell input). Cite U1.4, not a
  nonexistent normalizer unit.

### A3 — Mining (provenance verification; the producer gate; the model path is blocked)

- **Expected artefact:** a `ratextract` run's candidate rows in `state/state.sqlite` +
  `state/mine/index/<hash>.json` + journal entries.
- **Reference:** U2.1's live run gave `queries_run 5, unmatched 1, accepted 10, rejected 5, deduped 0`
  in `wall_s 1.527`, **in `mode: "replay"` because the endpoint was down** — "real graphify queries +
  real provenance verification against `<workspace>` + real store rows; candidate *selection*
  synthetic" (U2.1). The driver script was **not persisted**, so those live numbers are **not
  re-derivable** (V2, honesty audit).
- **Pass conditions:**
  1. **Provenance is verified.** V2's matrix is the standard: 20/20 stored refs re-verified
     `exists=True` against the real graph and the real tree; but
     `README.md#L99999-L100000` (real file, fabricated span, 275 real lines) → **False**, and as the only
     ref the candidate is **rejected**; `L0`, `L5-L2`, `../`, `/etc/passwd`, `nonsense`, `""`, `file#L`
     all handled **without raising**; one good + one bad ⇒ stored with only the good ref and score 0.5;
     **zero refs ⇒ rejected** (V2).
  2. **The producer gate (P5) holds.** If any candidate is replay-sourced, the report says so in words,
     because no field can say it today (V2 FAIL).
  3. **`model_calls` is not cited as a request count** (V2; P5 note above).
- **The model path is BLOCKED.** With Occamy down, a live mining run must be reported as `blocked`
  — V2's wording: *"the miner's model path is UNVERIFIED (blocked), not broken"*, endpoint refused at
  `2026-10-08T11:20:29Z` (V2). When the endpoint answers, re-run with `max_queries=6` (U2.1's hint):
  `state/mine/index/<hash>.json` holds no keys for the replay run, so it will re-mine.
- **API:** `resextract.mine` exports `Miner`, `verify_provenance`, `MineReport`, `Candidate`
  (`src/resextract/mine/__init__.py`). The `mine` CLI subcommand is a **placeholder** (exit 3).
- **Resume/dedupe/budget behaviour is verified** and must be spot-checked: budget ⇒ `partial=True`,
  `status=partial`, prior candidate persisted, journal `budget_exhausted`; same hash ⇒ `resumed=2,
  model_calls=0`, zero HTTP; duplicate normalised title ⇒ `found=2 accepted=1 deduped=1 stored=1`
  (V2).

### A4 — Lanes + classifier (the §3.6 guards; the honest refusal of `paper`)

```bash
.venv/bin/python -c "
import json
from resextract.lanes import from_store, build_lanes, classify_all, split_lane, persist_lanes, write_lanes_md
cands = from_store(10, graph_path='state/kg/duval/graphify-out/graph.json')
lanes = build_lanes(cands); classify_all(lanes)
for l in lanes: split_lane(l)
persist_lanes('duval')
print(json.dumps([l.to_dict() if hasattr(l,'to_dict') else l for l in lanes], indent=1, default=str))
"
```

- **Expected artefacts:** `state/lanes/duval/lanes.json`, `LANES.md`, 5 rows in the `lanes` table +
  10 `lane_candidates` rows (U0.10 backfill; U4.2 live persist).
- **Reference:** U4.2 live: **10 candidates input → 5 lanes, 5 paper refusals**, determinism proven
  byte-for-byte under shuffled input (identical `lanes.json` and `LANES.md`).
- **Pass condition — the §3.6 guards** (`docs/PLAN.md` §3.6; U4.2):
  - **no `paper`** without ≥1 `CONFIRMS`/`EXTENDS` anchor **and** ≥1 measured result;
  - **no `benchmark_card`** without recomputable numbers;
  - anything unverifiable defaults to **`memo`, never `paper`**.
  U4.2's rationale string is the model to check for:
  *"type=report: paper refused (external_anchor=false (no CONFIRMS/EXTENDS verdict);
  measured_result=false (no measured result)); downgrade report <- substantive_thesis=true"*.
  **This refusal is correct and must not be "fixed" by inventing verdicts**: `claims`/`verdicts` are
  both **0** in the store (P2), so there is nothing to anchor a paper to. The honest acceptance outcome
  for criterion 3 (`≥3 dockets at status: ready`, `≥2 distinct publication types`, `docs/PLAN.md` §1.3)
  is therefore **NOT MET today** — 5 lanes, all `type=report`, all `status=draft` (P2), and paper is
  honestly refused.
  - `split_lane` currently splits on ≥2 independent primary claims with different audiences/maturity;
    **no live split has been demonstrated** — U4.2's live run recorded `splits: 0` on every lane, and V4
    asked that a real split be exercised once claims/verdicts exist (V4 follow-up). Mark the split rule
    **UNVERIFIED live**; it is proven only by unit tests.
- **API:** `resextract.lanes` exports `build_lanes`, `classify_all`, `classify_lane`, `split_lane`,
  `persist_lanes`, `guards_passed`, `guards_failed` (`src/resextract/lanes/__init__.py`). The `lanes`
  CLI name is a **placeholder** (exit 3).
- **Verifier status (updated during this document's writing):** `V4` reported PARTIAL and was superseded
  by **`V4R`, which has now landed `done`** — its verdict is that the lane layer verifies clean: guards
  intact, 23 green, the membership join sound, determinism byte-identical on live rows, and the live
  `paper` refusal real (`handoffs/V4R.json`; `orchestration/VERDICTS.md` `#v4r`). V4R's own framing is the
  one to carry: *"the remaining batch-4 gap is a PLAN gap, not a code defect — a real lane cannot reach a
  2nd type or exercise the split rule until claims/verdicts/evidence rows exist."* An earlier ledger
  snapshot recorded V4R's handoff as an empty skeleton; that is now **stale** (`orchestration/STATUS.md`
  was written before V4R reported).

### A5 — Docket materialization (commit-pinned bytes, `verify_docket`, the gates, idempotent rerun)

```bash
.venv/bin/resextract materialize --target duval --lane-file <lane.json> \
    --docket-root dockets/duval-acceptance --json
.venv/bin/python -c "
from resextract.docket import verify_docket
print(verify_docket('dockets/duval-acceptance'))
"
```

- **Expected artefacts:** `dockets/duval-acceptance/{MANIFEST.json,ITEM.md,CLAIMS.md,EVIDENCE.md,
  PRIOR_ART.md,REFERENCES.md,REFERENCES.bib,RESULTS.md,METHOD.md,CHECKLIST.md,OPEN_QUESTIONS.md,
  UPDATE_BACKLOG.md,HISTORY.md,material/,web/,repro/}` (U5.2's live smoke listed all 17);
  `material/EXCERPTS.md` and, only when the cap binds, `material/LINKS.md` (U5.1, U5.2).
- **Pass conditions:**
  1. **Commit-pinned bytes.** `source.default = "commit"`; each material row records `resolved_from:
     git_object` + `blob_sha` + `sha256` + `unpinned: false`. U5.5's live docket
     (`dockets/duval/duval-u55-pinned`, 9 copied / 26 files written / `verify_ok: true`, 1 claim) shows
     the row shape: `traces/2026-09-28-duval-m0.jsonl` → `blob_sha 94495930…`,
     `sha256 431605e6…`, `unpinned: false` (U5.5).
  2. **`unpinned` marker for untracked material.** 3 of 6 entries in U5.5's run are unpinned
     (`.ci-trunk.txt` `590e007e`; `.lane-j-scratch/monograph.txt` `033b1547`;
     `.lane-j-scratch/consonance-external-evidence-2026-10-07.md.txt` `d141f139`), each reason
     `untracked_at_commit`, and the warning is emitted **per file** (`unpinned_warning_emitted_per_file:
     true`). Correction (r)/(s) is the authority: *"material must be resolved from the object store at a
     commit … An untracked path requires an explicit `unpinned` marker."*
  3. **The orphan-claim gate and the material-sha gate both hold.** U5.2 inverted both guard tests for
     the red→green capture: reverting the orphan-claim gate fails with `refusing to write an invalid
     MANIFEST.json: claims[C1]: no provenance`; reverting the sha256 gate fails with
     `sha256 mismatch for material/docs/FINDINGS.md (manifest 1ac9f4239172…, disk 6c0e099667eb…)`.
     Pass condition: `verify_docket(...).ok is True` with `problems == []`; and a fabricated ref
     (`graph:this_node_does_not_exist_u5_2`) or an out-of-range span (`lines 900-999` of a 379-line
     file) is **refused with no MANIFEST left behind** (U5.2).
  4. **Refusal parity between pinned and working-tree sources:** secret path (`.env`), secret content
     (`Bearer`), containment escape, `.worktrees/` ref, and a pinned-only secret all behave identically
     (U5.5, 5 parity tests). Pinned bytes do **not** bypass the predicates.
  5. **Idempotent rerun.** U5.3: rerun reported the copies `unchanged: 8`; U5.1: `rerun_unchanged: 6`;
     U5.5: `copied 9`. Pass condition: a second `materialize` into the same docket writes no changed
     material bytes and `verify_docket` stays `ok`.
  6. **Caps behave.** U5.1's live cap demo (30,000 B per-docket cap): `copied 2 / linked 4 / refused 0`,
     with `LINKS.md` rows carrying absolute source path + sha256 + byte size + a runnable quoted `cp`
     command. When no file exceeds the cap, `LINKS.md` is correctly **absent** (U5.1).
  7. **Refusals are reported, not dropped.** `docs/NOT_PRESENT.md` → `not_a_file_in_target`, recorded in
     `unresolved` (U5.3, U5.5: `unresolved: 1`). A symlink is refused as `symlink`, not
     `outside_target_root`; `.worktrees` → `is_directory`; `hostname.txt` → `outside_target_root`
     (U5.1).
- **`prepare`/dry-run first:** `.venv/bin/resextract materialize --dry-run` must write nothing
  (U5.3: `dry_run_wrote_nothing: true`, plan 8 files / 183,644 B).
- **`export`, `open` are placeholders** (exit 3, batch 5) — expected red, and the renderer legs are
  expected-red anyway (correction (h)); the `CHECKLIST.md` licence/PDF gates depend on renderers
  (U5.2's interface note).
- **Verifier gap:** `V5` (the independent verifier for batch 5) is **pending** in the ledger. A5's
  evidence today is the two authoring units' own red→green captures; **U8.3 must re-derive them**.

### A6 — Docket **status** criterion (plan §1.3) — currently NOT MET

```bash
.venv/bin/resextract status --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['dockets']); print(d['lanes'])"
```

- **Pass condition (plan §1.3):** `dockets/duval/` has **≥3 dockets at `status: ready`** and **≥2
  distinct publication types** chosen by the classifier.
- **Measured today:** `dockets.total 2`, all `by_freshness: current`; `lanes.by_type: {report: 5}` —
  i.e. **0 ready**, **1 type**. The gate is **NOT MET** and the honest report says so. Its blockers are
  upstream and named: no claims (A3, U2.2 pending), no verdicts (U4.1 pending), so the classifier
  correctly refuses `paper` (A4).

### A7 — Dashboard (loopback-only, no external origins, reasoning honesty)

```bash
.venv/bin/python -m resextract.dashboard --port 8911 &   # managed background job; owned by the unit
sleep 1
for p in / /api/status /api/runs /api/reasoning /api/findings /api/dockets /api/web-health /api/graph /api/doctor /api/refresh; do
  printf '%-24s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8911$p)"
done
curl -sN -m 3 http://127.0.0.1:8911/api/events
grep -RE 'https?://' src/resextract/dashboard/static/ || echo 'no external origins'
ss -ltn | grep 8911
```

- **Pass conditions** (U6.1: 48 passed; start command
  `.venv/bin/python -m resextract.dashboard --port 8901`):
  - every listed route returns **200**; `/api/dockets/..%2f..%2fetc%2fpasswd` returns **404** (U6.1's
    traversal guard; red→green: 2 failed when reverted);
  - `grep -E 'https?://' static/*` → **no matches** (`no_external_origins: true`);
  - non-loopback bind is **refused** (`ValueError`; red→green proven);
  - `/api/events` streams `text/event-stream`, ≥1 well-formed JSON heartbeat (U6.1: 3 events in 3 s
    carrying journals/dockets/doctor snapshots);
  - after the check the server is **stopped** and `ss -ltn` shows the port free (`server_stopped: true`).
- **Reasoning honesty — the field is not captured yet.** The reasoning screen is structurally complete
  but reports `reasoning_text_available: false` when the journal holds no `reasoning_content`
  (`src/resextract/dashboard/api.py:447,482,516`), and it refuses to paraphrase. See §7. Do **not**
  accept a reasoning screen whose rendered text is invented; the pass condition is that the API says
  `reasoning_text_available: false` rather than fabricating a summary (U6.1's hint; `api.py:20`).
- **Port discipline:** the optional `dashboard port` doctor leg reads *down* while the dashboard holds
  8901 — that is expected, not a failure (U6.1 `doctor_detail`).
- **`serve` became a real subcommand** during this document's writing (`src/resextract/cli.py:364`
  `_cmd_serve`; `IMPLEMENTED` now `{doctor, status, materialize, serve}`). It resolves the bind/port/token,
  refuses a non-loopback host with exit **2** ("a refused bind is a hard configuration failure, not a
  placeholder"), and starts the dashboard app. **Its acceptance is not yet independently verified** —
  `V6` is still pending and `U6.2` is in flight with a `partial` handoff. The **U6.1-verified** start
  command remains `.venv/bin/python -m resextract.dashboard --port 8901`; prefer whichever the run
  records, and state which one was used.
- **Verifier gap:** `V6` is **pending**. A7's evidence is U6.1's own run; **U8.3 must re-run it**.

### A8 — Refresh / staleness (no-op on an unchanged head)

```bash
.venv/bin/python -c "
from resextract.refresh import refresh_target
r1 = refresh_target('duval', docket=<slug>); print('pass1', r1)
r2 = refresh_target('duval', docket=<slug>); print('pass2 noop=', r2.noop)
"
git -C <workspace> status --porcelain
sha256sum state/kg/duval/graphify-out/graph.json   # before and after
```

- **Expected artefact:** docket `MANIFEST.json` + `HISTORY.md` + `PRIOR_ART.md` + `UPDATE_BACKLOG.md` +
  ledger + aggregate (`WORK_SUGGESTIONS.md`).
- **Pass conditions** (U7.1, re-derived by V7 check 3):
  - **second pass is `noop=true`** with `written=[]`, `planned=[]` and **zero** docket files changed;
    a third identical pass is also noop. V7 proved this from a **clean** docket (artifacts removed,
    `freshness.state` reset) — so the noop is genuine, not an artefact of pre-written state.
  - a changed cited file produces `needs_rework` with a **specific** reason. U7.1's live reason:
    *"`README.md` changed in `6deaed0..b2bade3` (commit b2bade3); claim C1 cites lines 1–30"*. V7
    check 4: with a changed file + expired TTL + gone/changed/suspect links all at once, **five**
    reasons are returned and `needs_rework` beats `stale` beats `current`; `superseded` is preserved.
  - the **original graph file's sha256 is unchanged** by refresh (U7.1:
    `4790bbb1…` before == after) — refresh works on a copy.
- **Change arithmetic:** `6deaed0..b2bade3` = **14 commits**, **25** `git diff --name-status -M` lines,
  and the reported **27** = 25 + the 2 dirty porcelain entries (`.ci-trunk.txt`, `.lane-j-scratch/`)
  because `detect_change` unions committed and dirty sets (correction (x), V7 check 8). Use the split
  form in the report; do not present 27 as a commit-diff count.
- **Known gaps that must be stated, not papered over:**
  - **Refresh has no CLI entry point:** `cli.py` carries only the placeholder `"refresh": "batch 7"`
    and `persist_store=False` by default, with **no caller** setting it True (correction (w); V7
    check 7).
  - **Refresh does not persist rework today.** Even with `persist_store=True`,
    `backlog.persist_rework` calls the legacy `open_rework` without `source_ref`/`model_suggested`
    (persisted row: `source_ref=None`, `model_suggested=0`). Schema v2 *does* unblock it
    (`add_rework` dedupes on `(docket_id, reason, source_ref)`; `list_rework`;
    `upsert_docket_by_dir`), but the wiring, the caller, the `dirs[0]`-only docket resolution and the
    double-counted row are all still open (correction (w); U0.10; V7 check 7).
  - **`target.head_sha` is never bumped** by refresh (stayed `6deaed0` while
    `freshness.state = "needs_rework"`) and `verify_docket` returns `ok=true` with no problems — no
    head↔freshness cross-check exists. No `src/` consumer reads `target.head_sha` as "current head",
    but a downstream consumer would be wrong (correction (v); V7 check 5).
  - **`graph_state.json` can label a stale copy with a newer head:** `state/kg-refresh/duval/repo` was
    staged at `b44e0e1` content while `graph_state.json` records `observed_head: b2bade3`, so the reuse
    guard can skip an update over a stale copy. For U7.1's file-cited fixture docket the invalidation
    verdict is identical either way (reasons byte-identical), so it is a **reproducibility** problem and
    a **latent correctness risk for graph-cited claims** (correction (t); V7 check 8).
- **Verifier record:** V7 gate call was **PASS — advance the Batch-7 staleness/refresh layer**, with the
  two limitations carried forward as corrections, not blockers (V7).

---

## 6. The Gate B / Gate C re-run procedure

**The plan's Phase-1 integration gate is STILL OPEN** (`docs/PLAN.md`:256). Status, precisely:

- **Gate B was observed exactly once** and **never independently reproduced.** U1.1's proven success run
  was against `state/kg/tiny/TINY.md`: exit 0, **54 s**, **1 LLM call**, **913 in / 1,938 out**,
  6 nodes / 6 edges / 2 communities, 6 semantic nodes, and a measured output rate of **≈36 output
  tok/s** (U1.1, "gate_b"). Its chosen real target was `<workspace>` —
  6 markdown files / 112 KB — because `constitution/` and `examples/` hold **0** markdown and
  `source-material/` is 2.5 MB / 53 files.
- **V1 could not re-derive it:** one probe, `HTTP 000`, connection refused at
  `2026-10-08T05:50:47-05:00`. V1's verdict was **UNVERIFIED (blocked), not failed** — none of U1.1's
  numbers is contradicted, and none is reproducible. V1 adds an honesty caveat: *"1 LLM call"* has **no
  local corroborating artifact** in U1.1's tree and would need **server-side accounting** (V1, Gate B).
- **Gate C — community labelling — was never run at all** by U1.1 (V1). `state/kg/semantic/` does not
  exist (U1.5's semantic half blocked).

### G1 — pre-flight liveness (mandatory; this is the step whose absence cost U1.1 ~20 minutes)

```bash
curl -sS -m 5 -o /dev/null -w '%{http_code}\n' http://serving-host/v1/models
```

- **Pass condition:** **`200`**. Anything else: **STOP.** U1.1's hint is explicit: *"pre-flight the curl
  liveness probe, abort if it is not HTTP 200 — that alone would have saved this unit 20 minutes."*
  Probe at most a couple of times; do not restart the server (D1; `orchestration/STATUS.md`).

### G2 — the semantic pass over the smallest corpus that exercises the docs path

```bash
stdbuf -oL -eL <workspace>/reserach\ extarctor/.venv/bin/graphify extract \
  '<workspace>' \
  --backend openai --model occamy-1.0 \
  --max-concurrency 1 --token-budget 1500 --api-timeout 300 \
  --out '<workspace>'
```

- This is U1.5's **exact persisted argv** (`handoffs/U1.5.json` `live.semantic.command`).
- **Flag contract — each element is load-bearing:**
  - `stdbuf -oL -eL` is **required**: graphify block-buffers stdout off-TTY, so a timeout discards all
    progress (correction (h)). U1.6 wired `stdbuf` into `Graphify.run()` via
    `spawn_argv_for()` and asserted `CommandResult.spawn_argv[:3] == ('stdbuf','-oL','-eL')` for all 35
    invocations, with `PYTHONUNBUFFERED=1` also set because `stdbuf` reaches only C stdio.
  - `--backend openai --model occamy-1.0` against `http://serving-host/v1` (dummy
    `OPENAI_API_KEY`) — the measured-working combination (U1.1 Gate B).
  - `--max-concurrency 1` — single GPU (`docs/PLAN.md` §3.3).
  - **`--token-budget 1500`, *not* the 60000 default.** Correction (i): at ≈36 output tok/s, a
    60000-token per-chunk cap means one chunk can run ~55 minutes and cannot return inside
    `--api-timeout 600`; the usable range is **1500–2000**. A stage left at the default "will look hung
    and then truncate" (correction (i), found by U1.1; the throughput half is `reported-only` because
    reproducing it needs a live Occamy).
  - `--api-timeout 300` (U1.5's argv; correction (i) discusses 600 as the ceiling that 60000 would blow).
  - `--out …/state/kg/semantic/duval` → writes `…/graphify-out/graph.json` (correction (j)).
  - `--no-viz`: **do not pass it** — it is not an `extract` flag (correction (a)); it is relevant only
    above 5k nodes for `cluster-only`, and the wrapper emits it only when explicitly requested (U1.2).
- **Expected artefact:** `state/kg/semantic/duval/graphify-out/graph.json`, then a merge into the code
  graph (U1.5's hint: `merge_with_code_graph(state/kg/duval/graphify-out/graph.json,
  state/kg/semantic/duval/graphify-out/graph.json, ...)`) → reference merged counts as in A2.
- **Pass condition:** exit 0; document and concept nodes present; semantic nodes carry
  `source_location` (U1.1's observed shape: `source_location_present 2655/2685` on the code graph; the
  semantic nodes matched `document|concept` with `source_location: null` — which V1 could not
  re-derive).

### G3 — Gate C: community labelling

- **Never run.** No observed command, no artefact, no counts exist on disk. The label pass
  (`docs/PLAN.md` §4 stage 1, "`label`") is **UNVERIFIED and unowned**. The first successful run of it
  is the one that must produce the Gate-C evidence; until then the Phase-1 gate **cannot** be cleared
  (V1). Record it as **not run**, never as passed.

### G4 — blocked-endpoint behaviour (what a failed G1 must produce)

- **`blocked_endpoint_down`, nothing executed, no partial graph.** U1.5's semantic block reads exactly:
  `"status": "blocked_endpoint_down"`, `"graph_produced": false`, and
  `state/kg/semantic/` was **not created** (`handoffs/U1.5.json`; U1.1's hint echoes it).
- Pass condition for the blocked path: the run exits naming the endpoint and produces **no** partial
  semantic graph and **no** claimed semantic nodes. A "partial graph" would be indistinguishable from a
  real one downstream.
- **Do not** substitute a fallback silently. `docs/PLAN.md` §8's fallback ("a ~150-line in-repo semantic
  pass over graphify's code-only graph, reusing its chunker") is the sanctioned substitute — it is
  **not built** (no such unit in `orchestration/units/`), so today the correct outcome is `blocked`
  (§8 status table).

### G5 — independent reproduction

- V1's Gate-B observation is the model: **one probe only**, per the probe budget, and the verdict word
  is **UNVERIFIED (blocked)** rather than PASS. The re-run's evidence must include the exact argv, the
  endpoint probe code, the wall time, and — if a call count is claimed — **server-side accounting**,
  because the miner's `model_calls` counter is misleading (P5; V2) and U1.1's "1 LLM call" has no local
  artifact (V1).

---

## 7. Known limitations

Each row names the unit or verifier that produced it. These are carried forward as **corrections, not
blockers** where the verdict said so (V7), but an acceptance report that omits them is not honest.

| # | Limitation | Consequence for the run | Source |
|---|---|---|---|
| L1 | A writer that mutates a file and **restores it byte-identically within the quiescence window** is undetectable by any before/after comparison. | The seal cannot be absolute; state it. | `writer.py` "Known limits"; U7.2 `limitations_documented` |
| L2 | A **burst can begin immediately after** the window closes. | A `quiescent` verdict is evidence about the window, never a promise. | `writer.py` "Known limits"; U7.2; correction (q); V7 check 6 |
| L3 | Detection is **blind to writes inside an existing untracked path** (`.lane-j-scratch/**`): modifying an existing untracked file changes neither the tracked digest nor the untracked **set**, so it reads `quiescent`. A *new* untracked entry does report `active_writer` (control). | For this target, even a sealed HEAD window is necessary but **not sufficient**. The fix is in the working tree (`assert_pinned_quiescent`, "defect U7.2-1") but **U7.2 has no card and no evidence and no verifier has checked it** — treat as a current limitation, and do the manual anchor identity check (§3 S1/S3) regardless. | correction (u), V7 check 6 "new gap found"; U5.4; `handoffs/U7.2.json` (pending skeleton) |
| L4 | `.worktrees/` is **never enumerated** — it is **one pruned directory entry** (`source=noise_dir`, "never walked") because graphify prunes the subtree. | Do **not** report it as a file count. The "441 files under `.worktrees/run-1/`" figure is a sibling's **name-count** that the reporting unit deliberately did not recurse; V7 did not re-count it either. | U1.7R; V7 check 8; `docs/LIVE_TARGET_NOTES.md` line 19; correction (u) |
| L5 | The miner's **`model_calls` counter is misleading** — `_Meter.absorb` increments on **every** `usage_sink` record (success, 4xx, exhausted transport failure), so a zero-I/O client reports `model_calls=2, total_tokens=240`. | Never cite `model_calls` as a request count. `model_calls=5, reasoning_tokens=0` reads as five real calls to an endpoint that was refusing connections. | V2 "`model_calls` — FAIL"; `src/resextract/mine/candidates.py:307` |
| L6 | **A replay-sourced candidate is indistinguishable from a mined one** — no producer/mode/model field on `candidates`/`runs`, no `mode` key in `report.json`; all 10 replay rows are `state='mined'`. The only signals are the `run_id` `live-u21-replay` and the `REPLAY ` title prefix. | Blocking prerequisite (P5) for any docket claiming model-derived findings. | V2 "Replay vs mined — FAIL" |
| L7 | **Refresh does not persist rework**: `persist_store=False` by default, no caller sets it True, `backlog.persist_rework` drops `source_ref`/`model_suggested`, `docket_id` uses only `dirs[0]`, and a deduplicated row is counted as written. Refresh also has **no CLI entry point**. | Rework exists only in `UPDATE_BACKLOG.md`; the `rework` table stays empty (`rework 0`, P2). | correction (w); V7 check 7; U0.10 |
| L8 | The dashboard's **reasoning text is not captured yet** — `reasoning_text_available: false` because the journal holds no `reasoning_content` field. The API reports the absence rather than paraphrasing. | Plan §1.7's "per-candidate Occamy reasoning (incl. `reasoning_content`)" is **not demonstrated**; it needs a miner that journals `reasoning_content` per model turn (U6.1's hint). | U6.1; `src/resextract/dashboard/api.py:20,447,482,516` |
| L9 | `graph_state.json` can label a **stale graph copy** with a **newer head** (`observed_head: b2bade3` over `b44e0e1` content), so the reuse guard can skip an update. | Reproducibility problem; **latent correctness risk for graph-cited claims** (identical for file-cited ones). | correction (t); V7 check 8 |
| L10 | Refresh never bumps `target.head_sha` and `verify_docket` has **no head↔freshness cross-check**. | `verify_docket` returning `ok=true` does not mean the freshness label and the head agree. | correction (v); V7 check 5 |
| L11 | A commit-pinned read and a working-tree read can **disagree**: `traces/2026-09-28-duval-m0.jsonl` working `431605e6` (866,816 B) vs pinned@`3982f26` `ba6128bf` (864,384 B); `.ci-trunk.txt` exists at **no** commit. | Any material claimed "verifiable at commit X" must be pinned, and an untracked path must carry `unpinned`. | correction (r)/(s); U5.4; `docs/LIVE_TARGET_NOTES.md` |
| L12 | SearXNG is **intermittent**: 2–7 ms dead responses vs 172–948 ms real ones; `unresponsive_engines` does **not** stay `[]` (V3 saw brave suspended, duckduckgo+qwant CAPTCHA). | A single `doctor` failure on SearXNG is retried once (U0.3); a zero-result search at ~1.5 ms is a degradation signal, not a real empty (V3; correction (l)). | U0.3; U3.1; V3 "Live search — PARTIAL"; correction (l) |
| L13 | A revert whose replacement is the **same byte length within the same wall-clock second** can leave Python serving a stale `.pyc` — a **false failure on the restored file**. | Any red→green capture must run with `PYTHONDONTWRITEBYTECODE=1` and a `__pycache__` purge (V3's gotcha, adopted by V7). | V3 "Red→green"; V7 check 2 |
| L14 | `.ipynb` normalisation is delivered inside `U1.4`'s `ingest`, but the plan's Batch-1 row named a **notebook-normalizer unit that does not exist**. | Cite U1.4 for notebook handling; the plan text is stale. | correction (k), V1 |
| L15 | The default `--token-budget 60000` is **unusable** at the measured ≈36 output tok/s; usable range 1500–2000. Its throughput half is `reported-only` (needs a live Occamy). | A semantic stage left at the default will look hung, then truncate. | correction (i), U1.1 |

---

## 8. The honest status table

Read this before believing any green run. Counts below are per **deliverable area**, not per unit.

| Batch / area | Verdict | Evidence (unit / verifier) |
|---|---|---|
| **0 — scaffold, client, store, journal, doctor, CLI skeleton, checkpoint** | **verified** | **V0 OVERALL PASS**, checks 1–10, red→green **2/2** sha-restored; `doctor --json` rc 0 core 4/4; 12 tables + WAL; commit `b4ea93c` (`VERDICTS.md` V0; `handoffs/V0.json`) |
| 0 — spec integrity | **verified** | `docs/PLAN.md` byte-identical (29,875 B / 308 lines / 12 `##`, md5 `7c4aac11…`) — V0 check 1 |
| 0 — store schema v2 | **verified** | U0.10: 13 v2 tests + 42 v1 regression; schema 1→2; rows preserved; live reading today: schema 2, 12 app tables (`handoffs/U0.10.json`) |
| 0 — "zero CLI drift" vs graphify 0.9.65 | **partial (UNVERIFIED half)** | V0: no local 0.9.65 artifact exists |
| **1 — knowledge graph (Gate A)** | **verified** | U1.1 2685/7102/128 @ `6deaed0`; **V1 rebuild** 2695/7151/119 @ `b44e0e1` rc 0 in 2.75 s, difference attributable to the HEAD move; pollution 0/0/0 (`VERDICTS.md` V1) |
| 1 — ingestion + coverage | **verified** | U1.4: 34 passed; live 533 files / 453 supported / **84.99%** |
| 1 — staging corpus + merged graph | **verified** | U1.5: 13 passed; 221 docs / 22,607,550 B; graph-reachable **97.58%**; merged 2706/7129/133; code graph sha unchanged |
| 1 — target policy | **verified** | U1.7R: 12 passed; two guards red→green with sha restore; `violations: []`; 537 admitted / 8 rejected |
| 1 — graphify flag-surface hardening | **verified** | U1.6: 25 passed; bound-flag guard has teeth; `update()` argv corrected; `stdbuf` wired for all 35 invocations |
| **1 — Gate B (semantic pass)** | **blocked — observed once, never reproduced** | U1.1's run (54 s / 1 LLM call / 913 in / 1,938 out / ≈36 tok/s); **V1 UNVERIFIED (blocked)**, endpoint HTTP 000 at `05:50:47-05:00`; "1 LLM call" has no local artifact |
| **1 — Gate C (community labelling)** | **not run** | V1: "Gate C was never run by U1.1"; no artefact on disk |
| **Phase-1 integration gate (`PLAN.md`:256)** | **OPEN** | V1's gate call: *"the plan's Phase-1 integration gate is not cleared"* |
| **2 — miner (provenance)** | **verified** | V2: 13 passed; provenance matrix adversarially re-derived (20/20 refs real; fabricated span → False; zero refs → rejected); 2/2 red→green sha-proven |
| **2 — miner (replay vs mined)** | **FAIL — pending fix** | V2: no producer/model/mode field anywhere; all 10 replay rows `state='mined'`; missing `candidates.producer/mode(+model)`, `runs.model/mode`, `report.json.mode` |
| **2 — `model_calls` semantics** | **FAIL — pending fix** | V2: counts `usage_sink` records, not requests; zero-I/O client reports `model_calls=2, total_tokens=240` |
| 2 — claims + provenance (U2.2) | **blocked** | `claims 0` in the store; U2.2 has no handoff as of this reading |
| **3 — web search / fetch / cache / SSRF** | **verified (code)** | **V3 PARTIAL — advance code**: 78 passed; **0 assertions deleted**; 4/4 guards red→green sha-proven; SSRF 4/4 `blocked_url`; cache hit 0 HTTP; arXiv refresh `changed=false` |
| 3 — live-search evidence half | **partial (environmental)** | V3: 3 paced genuine queries all returned **0** results today, so U3.1's "5/8 with results, 172–948 ms" is not reproduced; raw `unresponsive_engines` **non-empty**, contradicting U3.1's `[]` |
| **4 — lanes + classifier + split (code)** | **verified** | U4.2: 23 passed; deterministic byte-identical `lanes.json`; 10 candidates → 5 lanes, **5 paper refusals**; **V4R `done`** (landed during this document's writing): guards intact, membership join sound, determinism byte-identical, live refusal real (`handoffs/V4R.json`; `VERDICTS.md` `#v4r`) |
| 4 — split rule live | **UNVERIFIED live (a PLAN gap, not a code defect)** | U4.2 live: `splits: 0` on every lane; V4R: *"a real lane cannot reach a 2nd type or exercise the split rule until claims/verdicts/evidence rows exist"* |
| **4 — criterion §1.3 (≥3 ready dockets, ≥2 types)** | **NOT MET** | live store: 0 `ready`, 1 type (`report`); blocked on U2.2 (claims) + U4.1 (assessment) |
| **5 — copy engine / manifest / assembly gates** | **verified (author-side)** | U5.1: 15 passed, 6 copied / 2 refused / 6 sha matches / rerun unchanged, cap demo 2 copied + 4 linked; U5.2: 24 passed + full suite 250 passed + 1 skipped, **orphan-claim and sha256 gates red→green** |
| **5 — materialize (pinned) + idempotent rerun** | **verified (author-side)** | U5.3: 39 passed, refusal writes no docket, rerun `unchanged: 8`; **U5.5**: 50 passed, live `duval-u55-pinned` 9 copied / 26 files / `verify_ok: true`, 3 unpinned with per-file warning, refusal parity 5/5 |
| **5 — `V5` independent verification** | **partial — no evidence yet** | `handoffs/V5.json` landed with `status: partial` and an **empty evidence object** — not a verdict; A5 evidence remains author-side only |
| **6 — dashboard (API + SSE + UI)** | **verified (author-side); `serve` wiring in flight** | U6.1: 48 passed; 10 routes 200 + traversal 404; `no_external_origins: true`; loopback refusal red→green; server stopped; **`V6` pending**, `U6.2` in flight (`partial` handoff), and `serve` became a real subcommand during this document's writing (A7) |
| **7 — refresh / staleness / review / backlog** | **verified** | **V7 PASS**: 48 passed; 4/4 red→green sha-proven; noop proven genuine from a clean docket; `needs_rework` + 5 reasons beat `stale`/`current`; graph sha unchanged; containment PASS |
| **7 — rework persistence** | **not wired (gap)** | correction (w); V7 check 7; `rework 0` in the store |
| **7 — `U7.2` untracked-window fix + systemd units** | **partial / no evidence** | `handoffs/U7.2.json` is a **pending skeleton** (all fields `"pending"`, `tool_calls: 0`); **no** `orchestration/units/U7.2.md`; `deploy/` **does not exist** (no staged unit files); the fix code is present at `refresh/writer.py:854` but **unverified** |
| **8 — acceptance protocol + operations** | **this document (U8.1)** | `docs/ACCEPTANCE_PROTOCOL.md`, `docs/OPERATIONS.md` |
| 8 — full acceptance run (U8.2) | **pending** | `orchestration/STATUS.md` row `U8.2` = pending |
| 8 — independent adversarial verification (U8.3) | **pending** | `docs/PLAN.md` §10; AGENTS.md "Verification independence" |
| **Model path (all LLM legs)** | **BLOCKED** | Occamy `:8012` DOWN, probe HTTP **000** (U8.1, and D1/U1.1/U1.5/U2.1/V1/V2 all agree); `blocked`, not broken; restarting the shared server is the **user's** decision |

### The two current holes, named

1. **The model path is blocked on the GX10.** Every semantic/LLM leg is unproven: Gate B observed once
   and never reproduced, Gate C never run, U1.5's semantic half `blocked_endpoint_down`, U2.1 produced
   0 live candidates, V1's Phase-1 gate not cleared, V2's model path UNVERIFIED. D1 settled the cause
   (TCP closed; ICMP alive; all sibling services answer) — a shared model server, the **user's**
   decision to restart.
2. **The miner producer-labelling FAIL (fix queued).** A replay candidate is indistinguishable from a
   mined one by any field, and `model_calls` is a client-reported record count. This is a **hard gate**
   (P5) for any docket that claims model-derived findings.

**Nothing in this table should be upgraded by a later unit's assertion alone.** Every "verified" row was
produced by a unit that did not author the work (V0, V1, V3, V7) or by the author with its red→green
capture; the author-side rows that remain unverified (batches 5 and 6) are marked as such and are
explicitly assigned to `U8.3`.
