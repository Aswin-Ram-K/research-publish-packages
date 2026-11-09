# V-GATE-CHAIN-2 — second attack on the repaired gate chain

**Verdict: `fail`** — the four original breaks are all closed, but one new bypass survives and
it is the same failure mode the repair was built to end.

## Pinned

| file | sha256 | lines |
|---|---|---|
| `cell.py` | `60cdf98b048377327d75384c831644cc4f34d3e08315f9bc783ddcd148d79bfb` | 1487 |
| `exit_codes.py` | `97cdfc1e63471aecff83fc212346a56b719d44ecde13ae58c0f9bd4f8a3a86c8` | 236 |
| `run_longrun.py` | `dc5f3742…` → `0bc3b824…` (**changed under me**) | 2450 → 2496 |

`cell.py` and `exit_codes.py` were byte-stable before and after every probe.

## Closed (each run twice, `LIVE` = recording-stub subprocess proof)

| break | exit ×2 | LIVE ×2 |
|---|---|---|
| `--max-wall 0` | 8, 8 | 0, 0 |
| `--max-wall -1` | 8, 8 | 0, 0 |
| `--max-wall -3600` | 8, 8 | 0, 0 |
| absent `--hypothesis` | 12, 12 | 0, 0 |
| `--hypothesis none` | 12, 12 | 0, 0 |
| gate test from repo root | 15 tests OK | — |

G3's code `12` is in `EXIT_TABLE`, the docstring, `docs/EXIT-CODES.md` and the source-scan test.

## New bypass (`fail`)

```
cell.py --arm transcript-grow --fixture …/LR-01.v5.json --hypothesis H2 --turns 12 \
        --max-wall 1 --projected-turn-wall -1 --budget 600
```
`G2 … projected_wall~=-12s … cap=1s` → `ok` → `invoking:` → LIVE spawn (`0` does the same).
`projected_turn_wall()` validates nothing about the sign of the override; the repaired check
only guards the ceiling. Same class as break 1, one operand over.

## Other probes

boundary 720 s allows (no spawn in dry-run, spawn live), 719 s refuses 8; `--projected-from p90`
preempted by budget (3, documented ordering); `H9` refuses 12; missing/corrupt gate artefact
refuses 2 with a reason and no traceback; `--dry-run` + refusing gate prints WOULD-REFUSE with
its numbers, attempts no socket, and exits **0** (contract divergence R2).

## Exit table

raised-but-undeclared **none**; declared-but-never-raised `{5,6}` — both provisioned by
`RUNNER_CODES` propagation at `cell.py:945`, so not drift; `run_longrun.py` raises `9` and `1`,
both declared in `RUNNER_MAPPED_TO_CRASH`; docs rows `0..12` == table keys. Set equality true.

## Suites

`test_cell.py` 7/7 · `test_cell_gates.py` 15/15 · `test_guards.py` 6/6 GREEN (direct script) ·
`test_projection_calibration.py` 4/4 (direct script) · `test_exit_codes.py` 16/16.
Red half: G3 neutered in a `/tmp` driver → live runner spawn, so the gates are load-bearing.

## Rules

No file under `experiments/ptr-engine/longrun/` edited; all mutation in `/tmp`; zero inference
requests; zero network; no git. Probe debris (7 gate manifests written by the first batch into
the repo's `measure/` because that is `cell.py`'s default out-dir) was moved to
`/tmp/vgc2-debris/` and the batch re-run isolated and deterministic.
