# UNIT `PHANTOM-PATH-FIX` — a guard that fails on any cited path the tree does not have

**Purpose.** The batch's fourth phantom (`docs/BUDGET-SCHEDULE.md`, cited by four artefacts, real
path `experiments/ptr-engine/measure/BUDGET-SCHEDULE.md`) proved the record cannot police itself.
This unit ships the instrument, not just the patch.

**Deliverables**

| path | what |
|---|---|
| `experiments/ptr-engine/tools/path_refs.py` | scanner, classifier, forward-only `--check` |
| `experiments/ptr-engine/longrun/tests/test_path_refs.py` | 3 red + 3 green cases |
| `state/logs/path-refs-baseline.json` | frozen census of every `wrong_dir`/`missing` occurrence at arming time |
| `docs/PATH-REFS.md` | what the guard means, every allowlist entry justified, the first census |
| `docs/PRICE-REPLICATION.md`, `.../measure/price-replication.json`, `orchestration/handoffs/PRICE-REPLICATION.json` | the seven phantom `docs/BUDGET-SCHEDULE.md` citations, corrected token-only |

**Hard bound.** 26 tool calls. **Rules honoured:** no file was created to satisfy a citation; no
prose rewritten; no rows/grade/`cell.py`/`spawn_record.py`/`exit_codes.py`/`WITHDRAWN.json` touched;
zero requests; no questions asked.

**Write paths.** Exactly the ten listed in the card. No other file was written.

## What changed in the corpus

```diff
- docs/PRICE-REPLICATION.md:222   "docs/BUDGET-SCHEDULE.md §7"
+ docs/PRICE-REPLICATION.md:222   "experiments/ptr-engine/measure/BUDGET-SCHEDULE.md §7"
- measure/price-replication.json:35/39/115/119/393   "docs/BUDGET-SCHEDULE.md §1/§2/§3/§7"
+ measure/price-replication.json:35/39/115/119/393   "experiments/ptr-engine/measure/BUDGET-SCHEDULE.md §…"
- orchestration/handoffs/PRICE-REPLICATION.json:27   "docs/BUDGET-SCHEDULE.md §7"
+ orchestration/handoffs/PRICE-REPLICATION.json:27   "experiments/ptr-engine/measure/BUDGET-SCHEDULE.md §7"
```

## What the guard found in the corpus (2026-10-26)

Census at freeze: **ok 25,285 · wrong_dir 793 · missing 265 · ignored 203**. 752 distinct
`wrong_dir`/`missing` keys (1,058 occurrences) are frozen in the baseline. The dominant
`wrong_dir` family is the longrun-tests shorthand `tests/<name>.py` for
`experiments/ptr-engine/longrun/tests/<name>.py`; it is recorded, not rewritten.

Two live findings arrived from other cards *during* this unit — `orchestration/handoffs/COLD-START-SCORE.json:9`
citing `experiments/ptr-engine/tools/verdict_with_freeze.py` (missing: the fourth phantom, still
cited) and three shorthand references in `orchestration/units/CAPGATE-UNRECORDED-REFUSE.md` /
`docs/GATE-CHAIN.md:557`. They are outside this unit's write paths, so they are **baselined and
reported**, not repaired.

## Kill condition

If `--check` could not be made to exit 0 on the frozen corpus, or if a red case could not be made
to exit 1, STOP and report `partial`. Neither happened.
