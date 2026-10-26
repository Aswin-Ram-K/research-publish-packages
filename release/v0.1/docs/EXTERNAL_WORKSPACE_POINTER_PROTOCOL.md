# External-workspace pointer protocol

**Status:** normative specification. **Owner:** `R2-OPT-SIM`. **Schema id:** `resextract/r2-opt-sim/pointers/1`.
**Reference implementation:** `scratch/r2-opt-sim/cost_model.py` (`Pointer`, `load_pointers`, `check_pointers`).
**Gates:** `tests/test_r2_opt_sim.py` (21 tests).

This document specifies how a value that lives in *another* workspace is referenced from this one
without merging them. It is written to be **implementable**: every rule states an observable
outcome, the reference implementation is named, and every number in it is attributed in §8.

## 1. Problem

A cost model needs constants of two kinds:

1. **Derivable here** — calibratable from row files already on disk in this workspace.
2. **Not derivable here** — GPU-side throughput, kernel timing, server configuration, which were
   measured on *another machine's state* and cannot be re-measured from a workspace that holds no
   such machine.

Copying kind 2 into this workspace is the failure this protocol exists to prevent: the copy
detaches from the machine that produced it, so a later reader cannot tell whether the number is
still true, and the two workspaces acquire two drifting copies of one fact. The protocol therefore
makes kind 2 **referenceable and citable, but never copied**, and makes its absence a *status*
rather than an error.

## 2. Vocabulary

- **Pointer** — a triple `(source_id, path, role)` plus the **manifest** that declares it. A path
  alone is not a pointer: it does not say who declared it, who may write it, or whether it is
  absent by design.
- **Manifest** — the single document that declares pointers. For `R2-OPT-SIM` this is
  `orchestration/units/R2-OPT-SIM.md`, §"POINTER PROTOCOL", one fenced `json` block.
- **Root** — a named directory a pointer resolves under. Resolution goes through roots, so the same
  manifest yields a different absolute path on another host.
- **`source_id`** — the stable, human-readable name a constant cites. Never a path: the id survives
  the file moving.
- **Role** — one of the three below. Role decides writability and what absence means.

## 3. Roles

| role | lives where | may be written by | absence is |
|---|---|---|---|
| `external` | outside this workspace (another machine's checkout) | **nobody here** — declared read-only | a status (`MISSING`), not an error |
| `cursor` | this workspace | this workspace (the boundary artifact an external reader consumes) | a status, not an error |
| `cell-source` | this workspace | **nobody** (evidence) | a status, not an error |

The external root is declared `read-only` with `declared: false` when no such workspace is
reachable. That is a truthful declaration, not a configuration error: `R2-OPT-SIM` sets
`roots.external.declared == false` and gives the reason inline (`"no such workspace is reachable
from this host; every constant used below is derivable from own-root cells"`).

## 4. Resolution

A pointer resolves in this order, and the order is normative:

1. **`cell-source` → the own root.** `ROOT / path`, where `ROOT` is the reference implementation's
   own workspace root (`cost_model.py:50`, `ROOT = Path(__file__).resolve().parents[2]`). A
   cell-source is evidence *inside* this workspace, so it is never resolved elsewhere.
2. **`cursor` and `external` → `roots["own"] / path`** when an own root is supplied.
3. If no own root is supplied, or that candidate does not exist, a `cursor`/`external` pointer
   resolves **relative to the declaring manifest's directory** — `manifest_path.parent / path`.

**Correction of record.** The first implementation's `resolve()` reached `manifest_path.parent /
path` for `cursor` and `external` whenever no own root was passed, producing
`orchestration/units/orchestration/cursors/r2-opt-sim.json`; and `report.json` was generated
without an own root, so the cursor was reported `MISSING` even though
`orchestration/cursors/r2-opt-sim.json` exists. The file's existence was never in doubt — only
the resolution order. Rule 2 is both the fix and the specification: an own-rooted workspace path
is tried first, and any caller that wants a truthful cursor status must pass the own root.

Absence under every rule is the status `MISSING`, produced without exception.

## 5. Statuses

Exactly three, no others:

| status | meaning |
|---|---|
| `OK` | resolved, and (if a `sha256` was declared) the digest matches |
| `MISSING` | resolved to no existing file under any applicable rule |
| `DIGEST_MISMATCH` | resolved, but the bytes do not hash to the declared `sha256` |

Absence is a status, never an exception. `DIGEST_MISMATCH` exists so that a silently changed source
cannot be mistaken for the one the model was fitted on. A pointer with no declared `sha256` can
only reach `OK`, and `path_has_sha256: false` records that, so an unpinned pointer is never
mistaken for a verified one.

## 6. Rules

1. **A constant must cite its source.** Every number in `constants.json` carries the `source_id` it
   came from. `validate_constants` refuses a constant without a pinned `source_id` or without a
   rerun command, and `cost_model.py` then exits non-zero.
2. **External constants are normalised, never copied.** An external number enters the model only as
   a *ratio* against a same-unit in-workspace constant (throughput ratio, relative kernel time). A
   raw external latency never enters the model, because it was measured on another machine's state.
3. **Absence degrades, it never blocks.** A missing root or file downgrades the affected constant
   to `degraded`; the model still produces a ranking and reports what was degraded.
4. **Digest, not path.** A pointer may carry `sha256`; mismatch is `DIGEST_MISMATCH` (§5).
5. **One writer per pointer.** Only the role table (§3) decides who may write. Nothing in
   `R2-OPT-SIM` writes an `external` or `cell-source` pointer.
6. **The manifest is data.** Pointers are read out of the manifest's fenced `json` block
   (`load_pointers`, located by the `## POINTER PROTOCOL` heading). Adding a pointer is a manifest
   edit plus a digest, never a code change.

## 7. Manifest shape

```json
{
  "schema": "resextract/r2-opt-sim/pointers/1",
  "unit": "<unit>",
  "roots": {
    "own": {"path": "<absolute or empty>", "mode": "workspace-write", "declared": true},
    "external": {"path": "", "mode": "read-only", "declared": false, "reason": "<why absent>"}
  },
  "pointers": [
    {"source_id": "<stable name>", "path": "<workspace-relative or external-relative>",
     "role": "external|cursor|cell-source", "manifest": "<this document>",
     "sha256": null, "bytes_expected": null, "note": "<what it is>"}
  ]
}
```

Current declared pointers, with the status **measured under both invocations** — because §4
rule 2 makes the own root load-bearing for `cursor`:

| `source_id` | role | with own root | without own root | `sha256` (first 12) |
|---|---|---|---|---|
| `experiments/context-cache/cells/LIVE-MEAS/rows.jsonl` | `cell-source` | `OK` | `OK` | `6150e534c4f5` |
| `experiments/context-cache/cells/U9/u9_trials.jsonl` | `cell-source` | `OK` | `OK` | `863df39ec2c8` |
| `experiments/context-cache/cells/LIVE-MEAS/plan.json` | `cell-source` | `OK` | `OK` | `8b787e94f23a` |
| `cross-feed-cursor` | `cursor` | **`OK`** | `MISSING` | file `d461f3d76e76…`, unpinned |
| `external:gpu-prefill-throughput` | `external` | `MISSING` | `MISSING` | — |

Read that table as the protocol's own warning: a caller that forgets the own root gets a *false*
`MISSING` on the cursor, indistinguishable in shape from the true one on the external pointer.
`cell-source` is immune (rule 1 ignores roots); `external` is correctly `MISSING` either way.
`scratch/r2-opt-sim/report.json` records the **without-own-root** run (`degraded` =
`[cross-feed-cursor, external:gpu-prefill-throughput]`), so its cursor entry is that false
`MISSING`, not a missing file.

## 8. Attribution of every number

Each figure this document or its manifest states, with the file and field it is read from. Counts
are the files' own row counts; digests are sha256 of the file bytes.

| Claim | Value | Source of record |
|---|---:|---|
| LIVE-MEAS rows | 960 | `experiments/context-cache/cells/LIVE-MEAS/rows.jsonl`, JSONL line count |
| LIVE-MEAS design | 4 arms × 3 epochs × 80 turns | same file: `arm` ∈ {A, C, F, R}; `epoch` ∈ {1, 2, 3}; `turn` 1–80; every (arm, epoch) pair holds exactly 80 rows |
| LIVE-MEAS planned requests | 960 | `.../LIVE-MEAS/plan.json` → `planned_requests` (also `chains_checked: 960`) |
| LIVE-MEAS epochs | 3 | `.../LIVE-MEAS/plan.json` → `epochs` |
| LIVE-MEAS turns | 80 | `.../LIVE-MEAS/plan.json` → `turns` |
| Request cap | 990 | `.../LIVE-MEAS/plan.json` → `request_cap` |
| Budget tokens | 8192 | `.../LIVE-MEAS/plan.json` → `budget_tokens` |
| Keep-last | 2 | `.../LIVE-MEAS/plan.json` → `keep_last` |
| Fold schedule | `[18, 35, 53, 71]`, 4 folds | `.../LIVE-MEAS/plan.json` → `fold_schedule`, `folds` |
| U9 rows | 139 | `experiments/context-cache/cells/U9/u9_trials.jsonl`, JSONL line count |
| U9 pure-prefill rows | 139 of 139 with `completion_tokens == 1` | same file → `completion_tokens` |
| `rows.jsonl` digest | `6150e534c4f52553771172fe988a70a49d65917f85d0c9e1b5a336cf1d119b65` | `sha256sum`, agreeing with `constants.json` → `sources.files` |
| `u9_trials.jsonl` digest | `863df39ec2c8c9236ab413dc5365fbd763ff5d37671e5ade1236b653f580663f` | `sha256sum`, agreeing with `constants.json` and `papers/context-cache/CLAIMS.md` (U9-rows) |
| `plan.json` digest | `8b787e94f23a4f3428f5a37d92e37ba7da477ed69b95bcca93101d10a002469f` | `sha256sum`, agreeing with `constants.json` → `sources.files` |
| `u9_trials.jsonl` size | 50,417 bytes | `stat`, agreeing with `CLAIMS.md` (U9-rows) |
| Pointer statuses, own root supplied | 4 `OK`, 1 `MISSING` | `cost_model.check_pointers(MANIFEST, {"own": ROOT})` |
| Pointer statuses, no own root | 3 `OK`, 2 `MISSING` | `cost_model.check_pointers(MANIFEST)` — matches `report.json` |
| Cursor file digest | `d461f3d76e76b30b50262a188c4fe58102569376ee137519d492bd8d707e3f01` | `check_pointers` → `sha256`, own-root run |
| Gate count | 21 tests | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q` |

**Correction of record.** The `R2-OPT-SIM` card previously described LIVE-MEAS as
"960 measured rows, arms C/A/R/F × **2 epochs** × 80 turns". 4 × 2 × 80 = 640 ≠ 960; the file and
its plan both say **3** epochs, and 4 × 3 × 80 = 960. The figure was internally inconsistent with
its own row count and is corrected here; the row count is what the model reads.

## 9. Verification

```bash
cd "<workspace>"

# pointer statuses for the manifest (3 OK / 2 MISSING expected)
.venv/bin/python -c "import sys,json;sys.path.insert(0,'scratch/r2-opt-sim');import cost_model as cm;from pathlib import Path;r=cm.check_pointers(Path('orchestration/units/R2-OPT-SIM.md'),{'own':str(cm.ROOT)});print(json.dumps(r.to_json(),indent=1))"

# the gates
.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q

# the pinned digests behind §8
sha256sum experiments/context-cache/cells/LIVE-MEAS/rows.jsonl \
          experiments/context-cache/cells/LIVE-MEAS/plan.json \
          experiments/context-cache/cells/U9/u9_trials.jsonl
```

A reader who runs these gets the values §8 states. Nothing here contacts a network endpoint or
takes `.occamy.lock`; every figure is derived from disk.
