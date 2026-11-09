# V-GATE-REPIN — the gate precondition, decided on the tree as it stands

**Verdict: `partial`.** All four breaks refuse with the right codes and no live runner is spawned;
one item of the stated PASS rule does not hold — `popen_calls == 0` is false, because a *pre-gate*
dry-run self-check spawns on every invocation (finding F-1).

## Pins (before any probe / after every probe)

| file | sha256 (before = after) | size | mtime_ns before | mtime_ns after |
|---|---|---|---|---|
| `experiments/ptr-engine/longrun/cell.py` | `24627d7b648262f901825e87459b41a3ce7185539e46ccd3dda01c3002233253` | 104869 | 1793035628100164323 | 1793035883681770898 |
| `experiments/ptr-engine/longrun/run_longrun.py` | `9e8c30df9355e7bee243a15bf9ea67b23a20dd4c3d6ced6c9af1e53a6d76add1` | 151435 | 1793035588600689132 | 1793035588600689132 |
| `experiments/ptr-engine/longrun/exit_codes.py` | `97cdfc1e63471aecff83fc212346a56b719d44ecde13ae58c0f9bd4f8a3a86c8` | 12623 | 1793030850109447518 | 1793030850109447518 |
| `experiments/ptr-engine/longrun/grade_v5.py` | `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772` | 44739 | 1793034776180268337 | 1793034776180268337 |

`cell.py` **moved mid-card**: its mtime advanced by ~255 s while its bytes stayed identical (same
sha256, same size). No result is unstamped by sha — every probe ran against `24627d7b` — but the move
is reported rather than smoothed over. The pin `GATE-OPERAND-VALIDATION` claimed (`cell.py=6b0ca83a`)
does not name this file.

## The oracle

`subprocess.Popen` is the counted spawn site (`os.posix_spawn` is its py3.14 mechanism, deduped only
while inside our own delegated Popen call; a *direct* `os.posix_spawn`, `os.fork` or `os.execv` is
counted and tripwired on its own). Every live spawn attempt is counted and then **raised**, so no child
process is ever created and no socket can open. `cell._run` is counted for contrast and is **not** the
oracle — that was the defect this card exists to fix.

Two spawn sites exist in `cell.py`: stage 2/7 `harness` (`run_longrun.py --dry-run`, via `cell.py:169`)
and stage 3+ `stage_run` (`cell.py:1506`). The first fires **before any gate is evaluated**.

## Step 2 — the four breaks, each twice

| break | exit | popen | preflight | live runner spawns | cell._run |
|---|---|---|---|---|---|
| `--max-wall 0` (x2) | **8** | 1 | 1 | 0 | 1 |
| `--max-wall -1` (x2) | **8** | 1 | 1 | 0 | 1 |
| no `--hypothesis` (x2) | **12** | 1 | 1 | 0 | 1 |
| `--hypothesis none` (x2) | **12** | 1 | 1 | 0 | 1 |

Messages (verbatim, abridged at the artefact/parenthetical where marked `...`):

- `--max-wall 0` → `cell: 3b/7 projection REFUSED(8) G2 projection REFUSED: computed --max-wall=0 s | limit a positive ceiling (> 0 s) | ... | --max-wall 0 is not a wall: a ceiling of zero or less is not 'unlimited' and does not disable the gate.`
- `--max-wall -1` → same shape, `computed --max-wall=-1 s`, `--max-wall -1 is not a wall ...`
- no `--hypothesis` → `cell: 3c/7 G3 prereg gate REFUSED(12) G3 prereg REFUSED: computed hypothesis=none declared | limit a declared claim (smoke|plumbing, or one of H1, H2, H3) | ... claim REFUSED: --hypothesis=None is not a declaration this run may make.`
- `--hypothesis none` → same, `claim REFUSED: --hypothesis='none' is not a declaration this run may make.`

**Break 4** — repo-root unittest, `PYTHONPATH` unset:

```
env -u PYTHONPATH python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_cell_gates.py'
Ran 15 tests in 1.957s
OK            (exit 0)
```

## Step 3 — the six F-cases

| case | exit | popen | live spawns | expected | verdict |
|---|---|---|---|---|---|
| F1 `--max-wall 1e308` | 8 | 1 | 0 | 8 | ok |
| F2 `--projected-turn-wall 1e-9` | 8 | 1 | 0 | 8 | ok |
| F3 zero-per-turn artefact | 8 | 1 | 0 | 8 | ok (fixture-scoped) |
| F4 `--turns 0` (H3) | 4 | 1 | 0 | 4 | ok |
| F5 `--turns -1` (H3) | 4 | 1 | 0 | 4 | ok |
| F8 `--turn-wall-cap 0` | 8 | 1 | 0 | 8 | ok |

No F-case encodes a bypass as its pass condition. One scope caveat (F-3): F3 passes only because the
harness swaps `PROJECTION_ARTEFACT` for an artefact whose per-turn figure is `0`; on the deployed
artefact that figure is positive, so F3 pins the gate's zero handling, not the tree's state.

## Liveness — the oracle can see a spawn

A non-refusing invocation (`--max-wall 3600 --hypothesis H2`) reached `stage_run` and the primitive
counter recorded **`popen_calls=2`, `live_runner_spawns=1`** (one preflight + one live runner attempt),
which the tripwire stopped before any child existed. An oracle that never fires would have reported 0.

## What "partial" names

`popen_calls == 0` is not satisfied: it is **1** for every invocation, refusals included, and that one
call is the pre-gate `run_longrun.py --dry-run` harness self-check at stage 2/7. It is offline
(`offline: zero requests`) and it is not the runner, so the substantive claim — a refusal spawns no
runner — holds. The rule as written does not, and this card does not average it away.

## May the 800-request grid launch on this tree?

Yes, on sha `24627d7b` — and it would be trusting that the gate chain is the only door to a live runner
and that the single pre-gate spawn is an offline dry-run self-check; it would **not** be trusting that
zero processes are created before a refusal, because one is.
