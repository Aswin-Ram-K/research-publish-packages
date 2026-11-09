# The failed column is 60 pieces of unfinished work, 9 rows re-recordable for free, and one real red

**Classification of the 104 failed cards, by artefact and by a fresh run today** (2026-10-26).
Read-only; zero network requests; no board mutation. Machine-readable record:
[`measure/FAILED-COLUMN-RECLAIM.json`](../experiments/ptr-engine/measure/FAILED-COLUMN-RECLAIM.json);
gate: `python3 experiments/ptr-engine/tools/failed_column.py --check` (exit 0).

This extends `UNSTAMPED-104` ([`docs/UNSTAMPED.md`](UNSTAMPED.md)): that census proved **nobody** had
measured these cards from their verdict rows. This file asks the next question — *the unit may have
finished; did it?* — from the handoff artefacts and the card’s own acceptance command, re-run today.

## The arithmetic, reconciled

| | |
|---|---|
| failed cards in the census | **104** |
| — `never_had_a_row` | 96 |
| — `superseded_or_duplicate` (answered by a later card) | 5 |
| — `verified_fail` with a measuring row that exits **0** (sha drift, not a failed artefact) | 2 |
| — `unstamped_refusal`, exit **124** (outside `EXIT_TABLE`) | 1 |
| **in scope of this card** (96 + 2 + 1) | **99** |

The card text says 94 and derives it as “96 never-had-a-row minus the 5 superseded, plus the 2 drift
rows and the 1 exit-124 row”. That subtracts the five twice: the census’s 96 never-had-a-row **already**
excludes the 5 superseded (96 + 5 + 2 + 1 = 104). The reconciled in-scope count is **99**, and the
totals below sum to 99 + 5 superseded = 104. `--check` enforces exactly this.

## Classes

| class | cards | meaning |
|---|---|---|
| `finished_once_and_still_green` | **9** | declared artefacts exist and the card’s own acceptance command exits 0 today |
| `finished_once_but_red_today` | **1** | artefacts exist, the command now exits non-zero |
| `not_runnable` | 29 | no handoff/command, or a command that cannot run offline read-only today (reason named per row) |
| `no_artifacts` | 60 | nothing on disk carries this unit: genuinely unfinished |
| `superseded` | 5 | answered by a later card; out of scope |
| **total** | **104** | |

**How a command was chosen.** Handoff `evidence.commands` is narrative: strings with a `-> output`
tail, `{cmd, output}` dicts, and prose (`ssh ... free -m`). Each entry is normalised to its base
command; entries that cannot be re-run **offline and read-only** are dropped and the refusal reason is
recorded (`network/container`, `mutating`, `writes a measurement record`, `inspection only`,
`placeholder/prose`, `referenced path absent`). Of what survives, `pytest`/`test_` outranks
`--check`/`verify`/`audit`, which outranks anything else. The chosen string is stored verbatim, so every
green below can be re-run and disputed.

## Ranked: offline-passing first — rows that cost nothing to record

### 1. `finished_once_and_still_green` — 9 cards, a row each is free

| # | card | artefacts present | command re-run today | exit | next action |
|---|---|---|---|---|---|
| 1 | `R2-OPT-SIM` | 18 | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q` | 0 | re-record the row from this command |
| 2 | `R2-VLLM` | 18 | `.venv/bin/python experiments/context-cache/cells/R2-VLLM/selftest_off…` | 0 | re-record the row from this command |
| 3 | `RUN-INSTRUMENT-FIX` | 14 | `.venv/bin/python experiments/ptr-engine/longrun/run_longrun.py --self…` | 0 | re-record the row from this command |
| 4 | `SIM-PROMOTE` | 12 | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q -p no:cachepro…` | 0 | re-record the row from this command |
| 5 | `R2.1-TIGHTEN` | 10 | `python3 experiments/ptr-engine/tools/tests/test_anchor_classify.py` | 0 | re-record the row from this command |
| 6 | `C63-CELL` | 8 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_claim…` | 0 | re-record the row from this command |
| 7 | `Q0-ANSWER-DEGENERACY` | 7 | `python3 experiments/ptr-engine/tools/answer_degeneracy_check.py` | 0 | re-record the row from this command |
| 8 | `ACCOUNT-INVENTORY` | 3 | `node -e "const fs=require('fs');const j=JSON.parse(fs.readFileSync('/…` | 0 | re-record the row from this command |
| 9 | `PROFILE-PACK` | 1 | `node -e "const fs=require('fs');const d='/home/zer0null/TRUTH/presenc…` | 0 | re-record the row from this command |

Two of these are the `verified_fail`-by-drift rows `UNSTAMPED-104` flagged (`ACCOUNT-INVENTORY`,
`PROFILE-PACK`): their existing rows exit 0 against artefacts that exist **outside** this workspace
(`/home/zer0null/TRUTH/presence/`), so the sha mismatch that settled them `failed` was a record
defect. Re-running their own acceptance command re-records them without touching the artefact.

### 2. `finished_once_but_red_today` — 1 card

| card | command re-run today | exit | first failure line | next action |
|---|---|---|---|---|
| `PROBE-CP3-V6` | `python3 experiments/ptr-engine/longrun/tests/test_tool_chan…` | 1 | AssertionError: ({'before': '9624cb3e8b80ae6caf828d26e289831bdacfc9d31302dbca5cd11d5be39ff493'… | repair, then one row |

`PROBE-CP3-V6` is the only card in the whole column whose artefact is **proven red today**: its own
`test_tool_channel2.py` now fails `assertion_e_tools_off_identical` — “tools-off output drifted” — i.e.
the tools-off path is not deterministic. That is a measurement of the work, not of the record.

### 3. `not_runnable` — 29 cards, each with its named reason

| card | artefacts present | reason it cannot be judged today | next action |
|---|---|---|---|
| `RECORD-C8-APPEND` | 2 | handoff records no runnable command (inspection only (wc/grep/host/nvidia-smi), not an accepta… | bound or re-run |
| `PROMPT-O4` | 6 | handoff records no runnable command (inspection only (wc/grep/host/nvidia-smi), not an accepta… | bound or re-run |
| `PROMPT-O2C` | 6 | handoff records no runnable command (inspection only (wc/grep/host/nvidia-smi), not an accepta… | bound or re-run |
| `R2-P1-O1` | 11 | handoff records no runnable command (inspection only (wc/grep/host/nvidia-smi), not an accepta… | bound or re-run |
| `R2-P1-O2` | 2 | handoff records no runnable command (inspection only (wc/grep/host/nvidia-smi), not an accepta… | bound or re-run |
| `LATENCY-DERIVE` | 6 | handoff records no runnable command (mutating command (redirect/--out/git write); not re-run o… | bound or re-run |
| `PROBE-CP3-V5` | 8 | handoff records no runnable command (mutating command (redirect/--out/git write); not re-run o… | bound or re-run |
| `PROMPT-O2` | 4 | handoff records no runnable command (network or container command; offline session cannot re-r… | bound or re-run |
| `REASONING-PILOT-OFF` | 6 | handoff records no runnable command (network or container command; offline session cannot re-r… | bound or re-run |
| `AVALANCHE-2` | 1 | handoff records no runnable command (no commands at all) | bound or re-run |
| `C8-ADDENDUM2` | 2 | handoff records no runnable command (no commands at all) | bound or re-run |
| `C8-CENSUS-FIX` | 2 | handoff records no runnable command (no commands at all) | bound or re-run |
| `C8-SENTENCE-FIX` | 1 | handoff records no runnable command (no commands at all) | bound or re-run |
| `CONTAINMENT-RULING` | 2 | handoff records no runnable command (no commands at all) | bound or re-run |
| `PAPER-FINAL-V2C` | 5 | handoff records no runnable command (no commands at all) | bound or re-run |
| `PROMPT-O2B` | 6 | handoff records no runnable command (no commands at all) | bound or re-run |
| `R2-OPT-SIM2` | 10 | handoff records no runnable command (no commands at all) | bound or re-run |
| `RECORD-C8-PARAGRAPH` | 2 | handoff records no runnable command (no commands at all) | bound or re-run |
| `VERIFY-CLASSIFIER-FIX` | 2 | handoff records no runnable command (no commands at all) | bound or re-run |
| `GRADE-FIT-CONTROL` | 8 | handoff records no runnable command (placeholder/prose, not an executable command; the tool wr… | bound or re-run |
| `LAZY-LOAD-CROSSOVER` | 9 | handoff records no runnable command (referenced path absent today: run2/analyze2.py; reference… | bound or re-run |
| `LAZY-LOAD-CROSSOVER-2` | 9 | handoff records no runnable command (referenced path absent today: run2/analyze2.py; reference… | bound or re-run |
| `AVALANCHE-INSERT` | 5 | handoff records no runnable command (the tool writes on its own run path; re-running would edi… | bound or re-run |
| `DET-VERIFY-FIX` | 8 | handoff records no runnable command (the tool writes on its own run path; re-running would edi… | bound or re-run |
| `RUN-REASONING-POLICY` | 6 | handoff records no runnable command (the tool writes on its own run path; re-running would edi… | bound or re-run |
| `STRAND-MERGE-2` | 0 | measuring row exists but its command exits 1 today; no handoff declares artefacts | write the missing handoff |
| `GAP-LEDGER` | 3 | no handoff, so no recorded acceptance command | write the missing handoff |
| `MEASURE-VLLM` | 2 | no handoff, so no recorded acceptance command | write the missing handoff |
| `R2-VLLM-FIX` | 1 | no handoff, so no recorded acceptance command | write the missing handoff |

Three sub-reasons dominate, and none of them is a verdict: **24** cards have a handoff whose only
commands are network/container, mutating, inspection-only or unordered prose; **3** have no handoff at
all; **1** (`STRAND-MERGE-2`) has a row whose command is a suite run — its recorded exit is **124** and
a bounded re-run today returns exit 1 quickly (`node scripts/run-suite.mjs`), so the 124 was a timeout
of an unbounded suite, not a measurement.

### 4. `no_artifacts` — 60 cards, genuinely unfinished

Nothing on disk carries these units: no handoff artefact, no `write_paths` target, no file whose name
carries the unit. Most never wrote a handoff at all; the few that did declare artefacts that do not
exist on this tree. Absent means absent.

`APPLY-EVIDENCE`, `CB-TMPDIR`, `DIRECTION-1`, `E11-7`, `E16-1`, `E3-1`, `ENV-GREEN`, `ENV-PIN`, `ENVELOPE-PORT`, `ENVELOPE-RESCUE`, `ENVELOPE-RESCUE-2`, `Enforcement eval`, `FIX-ADV`, `FIX-DENIALS`, `FIX-FRAME-PROGRESS`, `FIX-INSTRUMENT`, `FLAKE-RSI-SURFACES`, `FLAKE-RSI-SURFACES-2`, `FLAKE-RSI-SURFACES-3`, `FORK-CHECKPOINT`, `FULL MOCK`, `FUZZ-BUDGET`, `FUZZ-BUDGET-2`, `FUZZ-BUDGET-4`, `FUZZ-BUDGET-5`, `GATE-RUN at fa01962`, `GATE-RUN envelope-port at a37bde6`, `HOUSEKEEPING-WT`, `Landing queue`, `M2-REVIEW-WIRE`, `M3-INST-3`, `M3-INSTRUMENTS`, `MOCK 04 SIGNAL`, `PROJ-ADOPT-1`, `QA + BUILD`, `R2-SGL-9B`, `RSI-ATTR-1`, `RSI-ATTR-VERIFY`, `RSI-SURFACES-1`, `SCOPE-GUARD-MARKERS`, `SEAM-1`, `SEED-PROMOTION`, `SEED-PROMOTION-2`, `SEED-PROMOTION-RED`, `SEED-PROMOTION-RED-2`, `SEED-RED3`, `SEED-RED4`, `SEED-RED6`, `STATE-GRAPH-VIEW`, `STUDIO`, `STUDIO FIX`, `T4-1`, `UX 01 HORIZON`, `V-MECH-RECORD offline diff-verifier of wording repairs`, `V-PAPER-CLOSE independent verifier of experiment close`, `V-RELEASE-BATCH`, `V-XSTACK2`, `Vision audit: orchestration board screenshots via the keyless OVH route`, `WIRE-FIXTURES`, `dogfood-bl1`

### 5. `superseded` — 5 cards, out of scope

- `GUARD-U4` — answered by a later card: GUARD-U4-R2
- `V-PKG-CORR` — answered by a later card: PACKAGE-C63-FOLD
- `ARMS-PARITY-WITHDRAW` — answered by a later card: ARMS-PARITY-WITHDRAW2
- `PAPER-FINAL-V` — answered by a later card: PAPER-FINAL-V2A + PAPER-FINAL-V2B (3b96d627)
- `C8-CENSUS` — answered by a later card: C8-CENSUS-FIX-V2

## What this column is not

It is **not a measure of unit quality**, and it must not be cited as one. 96 of the 104 cards never
wrote a verdict row; 60 have no artefact on disk at all. A card that appears here failed to **report**,
which is a different property from failing to **work** — and the 9 green cards prove the difference:
their artefacts exist and their own commands pass, yet the board shows them as failures because nobody
recorded the run. Read the column as an inventory of missing records and missing work, never as a count
of broken units. The one card whose artefact is measurably red (`PROBE-CP3-V6`) is the exception that
makes the point: it is red because it was re-run, not because it was called failed.

## Priority: eight cards whose single row closes the most open questions

Ranked by what one recorded row would settle for the arm work (`RUN-A*`), `docs/OPERATOR-BRIEF.md`, or
the withdraw register — not by ease of recording (all nine greens are equally cheap).

| # | card | why this row matters | what the row must say |
|---|---|---|---|
| 1 | `RUN-INSTRUMENT-FIX` | the instrument harness every `RUN-A*` arm run depends on; a green self-test today means arm rows stop being unattributable | `run_longrun.py --self-test` exit 0, plus the smoke-run limitation the card hit |
| 2 | `PROBE-CP3-V6` | the only **measured red** in the column: tools-off output drifts, which contaminates any arm comparison it feeds | the failing assertion, the reproduced hash pair, and whether the drift is in the artefact or the harness |
| 3 | `R2-OPT-SIM` | the arm-cost simulator the `R2` arm numbers and the withdraw register’s cost entries rest on; its test suite passes today | pytest exit 0 plus which constants were regenerated, if any |
| 4 | `R2-VLLM` | the vLLM cell whose rows feed the cross-stack and cost claims; offline selftest passes while the cell itself is unbounded | selftest exit 0, and an explicit statement that no live row was produced |
| 5 | `Q0-ANSWER-DEGENERACY` | OPERATOR-BRIEF §3 keeps “whether prose asserting a value counts” open; this check is the instrument for it | `answer_degeneracy_check.py` exit 0 and what it does not decide |
| 6 | `C63-CELL` | guards the claims/attribution surface the withdraw register cites (WI-003/005/014); both guard tests pass today | pytest exit 0 against the current `papers/context-cache/` tree |
| 7 | `ACCOUNT-INVENTORY` | the operator’s channel inventory lives in `/home/zer0null/TRUTH`; its drift row is re-recordable for free | the existing command’s exit 0, recorded against today’s sha |
| 8 | `STRAND-MERGE-2` | the only exit **124** in the column; whether 124 is a verdict decides if the suite bound is a measurement or a bookkeeping gap | a bounded run with its real exit, or the 124 recorded as a refusal code |

## Recommendation on exit 124

`124` should join `EXIT_TABLE` as a **refusing** code (`REFUSING` in `verdict_semantics.py`), not a
measuring one: it is the timeout sentinel and says the suite was killed before any gate wrote a
verdict, so classifying it as a refusal records the row without letting a kill pose as evidence about
the artefact. One-line justification for the table: *124 = command timed out, nothing measured.*
`exit_codes.py` is **not** edited here (out of scope); this is a recommendation, and until it lands
`STRAND-MERGE-2` stays `not_runnable` with the code recorded, never guessed.
