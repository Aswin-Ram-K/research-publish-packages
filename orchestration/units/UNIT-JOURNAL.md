# UNIT-JOURNAL — append-only unit journal (tooling only)

**Card:** `6a513dac-fca5-4b19-96d8-0299448d0d3b` · execution `26066c3e-3583-4232-b695-16c2a9138218`
**Bound:** ≤26 tool calls, zero inference requests. **Status:** done.

## Purpose

Three cards in this project (`Q0-ANSWER-DEGENERACY`, `PROBE-CP3-V6`, `LIVE-SMOKE-CELL`) were killed at
their handoff step; because the handoff is written last, each kill destroyed the unit's evidence while
the work had succeeded. This unit builds an append-only per-unit work journal so evidence lands *as the
work happens* and a follow-up card can reconstruct a killed unit without re-running it.

## Deliverables

| Path | What |
|---|---|
| `experiments/ptr-engine/tools/unit_journal.py` | `init` / `log` / `status` / `resume`; one write path (`_append`, mode `"a"`, fsync) |
| `experiments/ptr-engine/longrun/tests/test_unit_journal.py` | kill test (a), torn line (b), missing-artifact exit (c), append-only (d) |
| `docs/UNIT-JOURNAL.md` | the protocol: when to log, why append-only, how `resume` is used, the never-edit rule |
| `orchestration/journals/UNIT-JOURNAL.jsonl` | this card's own journal, written as the work happened |
| `orchestration/handoffs/UNIT-JOURNAL.json` | handoff (written last, after the `next` record) |

## Evidence

- Killed-process test: unit logs header + 3 artifacts + evidence + `next`, child is `SIGKILL`ed
  (`returncode == -SIGKILL`) with no handoff on disk; `status` reconstructs `records: 6 / last_step: 5`,
  2 artifacts present with byte sizes, 1 missing named, last `next` recovered; `resume` prints the
  paste-ready paragraph including `PASS 12/12` and the next action.
- Red: reverting three guards (missing-artifact exit → 0, torn-line tolerance → `SystemExit`, append
  mode `"a"` → `"w"`) fails all 4 tests. Green: `OK (4 tests)` in 0.81 s.
- Zero inference requests: only local `python3` subprocesses.

## Constraints honoured

No harness code touched (`client.py`, `run_longrun.py`, `cell.py`, graders, fixtures untouched);
`orchestration/handoffs/` not modified except this unit's own handoff; no journal created for any other
unit; stdlib only; the tool never rewrites a journal.
