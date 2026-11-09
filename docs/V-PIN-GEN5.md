# V-PIN-GEN5 — independent attribution of harness pin generation 5

**Verdict: `pin_attributable`.** Digest recomputed independently, both moved inputs
attributed to settled cards, stale expectation refused at stage 2/7 with exit **2**,
current expectation accepted with exit **0**, and the launcher refuses to spawn at all
against this generation (fail-closed, not open). Requests sent: **0**.

## 1. Digest, recomputed (not imported from `cell.py`)

Implemented the recipe from `experiments/ptr-engine/longrun/cell.py:334-349` in my own
code — `sha256` over `"name:sha256\n"` for `sorted(names)`, names =
`cell.py:128-135` `HARNESS_FILES` (`run_longrun.py`, `client.py`, `grade_v5.py`,
`analyze_stats.py`, `tools/det_verify.py`) plus `fixture`
(`longrun/tasks-v6/LR-01.v8.json`).

| field | value |
|---|---|
| recomputed | `35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb` |
| pinned | `35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb` |
| files_counted | 6 |
| match | **true** |

All six per-file shas on disk equal the pin's `files[*].sha256`.

## 2. Attribution — every move has an owning card

Generation 4 (preserved at `measure/HARNESS-PIN.json` → `supersedes_pin_generation_4`,
`harness_sha256 = fa6fd8cc…`) versus now: **two** of six inputs moved, four byte-identical.

| file | gen4 sha | current sha | moved_by card | evidence |
|---|---|---|---|---|
| `grade_v5.py` | `056eb605…f26772` | `3d70ed1d…c77940` | `8beed953-cb46-4982-8307-7d442dc27ca9` GRADE-V5-T4-DECORATION | `task_board_list` → status **done**, latestExecution `c0e65298-6ec2-4310-886f-d1599e95aa0a` **succeeded**; handoff `evidence.grader_sha256_before/after` = exactly these two digests |
| `run_longrun.py` | `b2003038…42965e` | `30dfa9e9…a16576b` | `9d7b9aac-6ca8-4b88-9a36-99c3bc15314b` RUN-DRY-TURN-SCOPE | `task_board_list` → status **done**, latestExecution `a8085c15-2e50-4217-8cd5-5b5adf44d1e0` **succeeded**; handoff quotes **both** digests and lists `run_longrun.py` in `artifacts` and `write_paths` |

Unchanged since generation 4 (byte-for-byte): `analyze_stats.py` (`30b07d4d…`),
`client.py` (`5aa23bb5…`), `fixture` (`0804b515…`), `tools/det_verify.py` (`12ccc74e…`).

**Unattributed rows: none.**

Non-member move, recorded but not digest-relevant: `experiments/ptr-engine/longrun/cell.py`
sha256 `cf512f5f3bd075c46a2c7c508ce9b803a32d9ba1ceb44edf3c729ded6ce3ce18`, 114 184 bytes,
moved by `BUDGET-STAGE-MAX-TURNS` — a card whose own handoff settles **`partial`** because
it falsified its premise (the dry run ignored `--max-turns`; repaired later by
RUN-DRY-TURN-SCOPE). `cell.py` is outside `HARNESS_FILES` by construction, so it cannot
move the digest. The pin records **no** `cell.py` sha at all (`"cf512f5f"` does not occur
in `measure/HARNESS-PIN.json`).

## 3. Enforcement, measured — not merely recorded

Both runs used the same argv: `--arm pointer-stable --fixture
experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 12 --reps 1 --thinking off
--max-wall 900 --turn-wall-cap 180 --runaway-turns 2 --budget 108 --hypothesis smoke
--no-cell-handoff --dry-run --fetch-followup-allowance 48`.

**Stale expectation (`--expect-harness fa6fd8cc…`, generation 4) → exit 2**, quoted:

```
cell: 2/7 harness REFUSED(2) harness changed mid-cell: --expect-harness fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac but the current digest is 35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb (files: analyze_stats.py, client.py, fixture, grade_v5.py, run_longrun.py, tools/det_verify.py)
```

**Current expectation (`--expect-harness 35ff41b7…`) → exit 0**, quoted:

```
cell: EXIT 0 - dry run: 0 of 3 gate(s) would refuse; exit 0 means the PREVIEW ran, not that the gates allow: callers MUST parse this line or the WOULD-REFUSE verdict lines, never the exit code; nothing was sent
```

The refusal names the flag and the current digest, and happens at **stage 2/7 — before
any spawn** (`cell: spawns runner_launch=0 preflight_self_check=0 declared=0 …`), so it is
not a post-spawn abort.

**Is the flag only passed by hand?** No — and the launcher is currently *stricter* than
the pin. `tools/run_a_star.py:357` `cell_argv` always appends
`"--expect-harness", pinned_digest()`; `pinned_digest()` (`run_a_star.py:72-88`, constant
at `:51`) raises `SystemExit` when `rec["generation"] != 4` or the digest disagrees.
Probed by importing the module (its `__main__` is guarded at `:656`) and calling it:

```
SystemExit: HARNESS-PIN record disagrees with the launcher: record generation=5 digest='35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb', launcher gen 4 digest='fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac'
```

So no launcher cell — grid or canary — can start against generation 5 until the constant
and the `generation != 4` check are advanced. The pin's own `wiring` block says exactly
this and names the owner of the advance. **Fail-closed, not `pin_unenforced`.**

## 4. `cell.py` itself

| object | sha256 | bytes |
|---|---|---|
| `experiments/ptr-engine/longrun/cell.py` | `cf512f5f3bd075c46a2c7c508ce9b803a32d9ba1ceb44edf3c729ded6ce3ce18` | 114 184 |
| pin `harness_sha256` | `35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb` | measured over 6 files |

`cell.py` is deliberately **not** in `HARNESS_FILES` (`PIN-COVERS-CELL-PY`, queued;
`measure/HARNESS-MAP-PREGRID.json:82`).

**Answer:** this pin certifies the six files *around* the conductor, **not the
conductor** — `cell.py` both builds the `--expect-harness` flag and would be the file
doing the hashing; a change to it moves neither the digest nor the record (demonstrated:
`cell.py` did move, to `cf512f5f…`, and the digest stayed at generation 5 unchanged).

## 5. Residual — named, not fixed

| unbound | what it means | owner |
|---|---|---|
| `longrun/cell.py` | conductor unhashed; "pin covers cell.py" is false today | `PIN-COVERS-CELL-PY` (queued, `measure/HARNESS-MAP-PREGRID.json:82`) |
| `tools/run_a_star.py:51,64` | launcher constant and `generation != 4` gate still on gen 4; every launcher cell refuses before spawn | advance owner named in the pin's `wiring.advance_owner`: a fresh `HARNESS-PIN-WIRING` successor card; HARNESS-PIN-GEN5 may not edit it |
| `analyze_stats.py` runtime behaviour | the digest binds *bytes*; the analyser's semantics (inclusion of unstamped cells, `analyze_stats.py:749`) are not a hash property | the arm-analysis cards behind `measure/ARM-RECONCILE.json` |
| `grade_v5.py` grader semantics | bytes `3d70ed1d…` pinned; whether that grader accepts correct era-B answers is a *behavioural* claim | `ERA-B-GRADE-REHEARSAL-2` (`8e4b7d40-0426-4f21-81fa-7f3e4534d57d`, done, 64/64 + 0/9 controls) |
| thresholds / grid shape | `GRID-PARAMS.json`, `GRID-SHAPE.json` are pinned by *their own* cards, not by this digest | `GRID-PARAMS-DIGEST-SUPERSEDE` (`b51f4988-2983-49e1-b5e2-cd88f312abad`, done) |

None of these was touched. Requests sent: **0**; no network; `--dry-run` only.
