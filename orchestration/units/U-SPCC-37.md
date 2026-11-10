# U-SPCC-37 — the runner enforces G3 before it spends anything

## 0. The gap

`experiments/ptr-engine/longrun/cell.py` implements the G3 preregistration gate —
`eval_gate_prereg(args, fixture)` at `cell.py:1638`, `validate_g3(...)` at
`cell.py:1220`, `GATE_PREREG = "G3"` at `cell.py:170`, enforced inside the conductor at
`cell.py:2274` via `_enforce(..., "3c/7 G3 prereg gate", 12)`. It refuses a cell whose
`n` cannot support the claim it declares: an `E1` cell outside PREREG-SPCC's 200–500
request ceiling, an `H1` cell below `n = 60`, a fixture carrying fewer than 48
checkpoints for an `E*` claim.

`experiments/ptr-engine/longrun/run_longrun.py` — the runner every live cell actually
uses — had **zero** references to `eval_gate_prereg`, `validate_g3` or `GATE_PREREG`.
Its only contact with `cell` was `import cell as _cell` at `run_longrun.py:2369`, for a
file list. The gate was implemented, tested, and never enforced on a live run.

Measured consequence: the E1 cell of 2026-11-10 (`rows-e1-spcc-2026-11-10.jsonl`) spent
100 requests, below the prereg's 200–500 floor, and nothing refused it. Its rows are
stamped `claim=E1` but were never checked for admissibility.

## 1. The change

Two functions added at `run_longrun.py:4020` and `run_longrun.py:4042`, and one call at
`run_longrun.py:4185` — after `claim_mode.resolve_claim` (`run_longrun.py:4169`) and
before the first `run_cell`:

- `prereg_gate_args(cfg, fixture)` — the adapter. `cell.eval_gate_prereg` reads
  `args.hypothesis`, `args.turns`, `args.reps`; the runner spells those `--claim-mode`,
  `--max-turns` (0 = the fixture's N, resolved by the existing `cell_turns`) and
  `--reps`. `hypothesis` is the **already-resolved** `cfg.claim`, so the gate adjudicates
  the same decision the rows are stamped with — never a second parse of the flag.
- `enforce_prereg_gate(cfg, fixture)` — calls `cell.eval_gate_prereg`, prints
  `cell._gate_message(verdict)` (the gate's own refusal format, verbatim) plus
  `PREREG REFUSED (exit N): no row was written and no request was sent`, and returns the
  gate's own code. `cell.Abort` (an unreadable artefact, a stale SPCC companion pin) is
  caught and its code returned the same way.

`cell.py` and `claim_mode.py` are untouched. No bypass flag was added.

## 2. Red → green

Red (the call site neutered — the pre-change runner):

```
RED: exit=0 sends=100 rows=100 | GREEN: exit=12 sends=0 rows=0
```

Green, below-floor E1 (`TX-03.v1.json`, N=100, 48 checkpoints, `--claim-mode E1
--reps 1` → n=100):

```
EXIT 12
G3 prereg REFUSED: computed n=100 over 48 checkpoint(s) | limit n in [200, 500] and >= 48 checkpoint(s) | artefact experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.json (sha256 3a01b3e4130dd6d4d2e9db2bbb0e16558847ebd65e46c1991a1696cd2eda7af8) | to change this decision pass --hypothesis / --turns / --reps | PREREG-SPCC's E1 is budgeted at 200-500 requests over 48 checkpoints; this cell would spend n=100 over 48 checkpoint(s), so its own allocation cannot support the claim it would state
PREREG REFUSED (exit 12): no row was written and no request was sent
```

## 3. Cases

| case | operands | exit | sends | rows |
|---|---|---|---|---|
| (a) E1 below floor | `E1`, reps=1, N=100 → n=100 | 12 | 0 | 0 |
| (b) E1 at floor | `E1`, reps=2, N=100 → n=200 | 0 | 200 | 200 |
| (c) H1 below 60 | `H1`, reps=1, max-turns=10 → n=10 | 12 | 0 | 0 |
| (d) smoke | `smoke`, reps=1, max-turns=3 | 0 | 3 | 3 (`claim=none`, `comparison_eligible=false`) |

## 4. Gates

```
TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
  experiments/ptr-engine/longrun/tests/test_runner_prereg_gate.py \
  experiments/ptr-engine/longrun/tests/test_spcc_claim.py \
  experiments/ptr-engine/longrun/tests/test_claim_rows.py \
  experiments/ptr-engine/longrun/tests/test_cap_gate.py -q
-> 35 passed in 4.85s
```

`python3 tools/doc_check.py` → `OK docs clean under /home/zer0null/research extractor`,
exit 0.

Full `experiments/ptr-engine/longrun/tests` sweep: 855 passed, 7 failed. All 7 are
on-disk corpus/artefact state, none touches the gate: `test_journal_lint` (handoff JSONs
missing journal entries), `test_layers_compiler::test_compaction`, `test_request_ledger`
(`spent=8081 > cap=4320`), `test_stop_reason` (stale `STOP-REASON.json`), and three
`test_verbosity` cases (rows files missing from the report corpus).

## 5. Checkout note

The session cwd `/home/zer0null/.omp/wt/wt-20261109-055629-bd8df5c` is a stale worktree
at `f17663d` with no `cell.py`/`claim_mode.py` in `longrun/`. All work was done in
`/home/zer0null/research extractor` on `research/next-candidates-2026-10-24`.
