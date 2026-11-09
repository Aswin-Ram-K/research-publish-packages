# RECLAIM-GREEN-ROWS — can finished work be un-filed as failed?

Offline. Ten stored acceptance commands re-run from the repo root at HEAD `f17663d1fed0162a7dc3c5a0a58d372c710974c3`
(zero inference requests). Each green card was then offered to the board as a verdict row, verbatim command,
measured exit, measured sha. Full detail: `experiments/ptr-engine/measure/RECLAIM-GREEN-ROWS.json`.

| card | command (as stored) | exit today | row recorded | refusal (short) |
|---|---|---|---|---|
| R2-OPT-SIM | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q` | 0 | no | `command-not-allowed: ".venv/bin/python"` |
| SIM-PROMOTE | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q -p no:cacheprovider` | 0 | no | `command-not-allowed: ".venv/bin/python"` |
| R2-VLLM | `.venv/bin/python experiments/context-cache/cells/R2-VLLM/selftest_offline.py` | 0 | no | `command-not-allowed: ".venv/bin/python"` |
| C63-CELL | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest … -q` | 0 | no | `command-not-allowed: ".venv/bin/python"` |
| RUN-INSTRUMENT-FIX | `.venv/bin/python experiments/ptr-engine/longrun/run_longrun.py --self-test` | 0 | no | `command-not-allowed: ".venv/bin/python"` |
| Q0-ANSWER-DEGENERACY | `python3 experiments/ptr-engine/tools/answer_degeneracy_check.py` | 0 | **yes** | — |
| ACCOUNT-INVENTORY | `node -e "…accounts.json…"` | 0 | no | `command-not-allowed: "const"` |
| PROFILE-PACK | `node -e "…profile-pack…"` | 0 | no | `command-not-allowed: "const"` |
| R2.1-TIGHTEN | `python3 experiments/ptr-engine/tools/tests/test_anchor_classify.py` | 0 | **yes** | — |
| PROBE-CP3-V6 *(red, untouched)* | `python3 experiments/ptr-engine/longrun/tests/test_tool_channel2.py` | 1 | no | `AssertionError: … 'tools-off output drifted'` |

Both recorded rows were accepted verbatim:

- `recorded verdict for 17a76d24-e915-4e51-ae6f-584718002eb7 [da4ba836-93ac-4ec4-a77f-6ac5bfca9444]: PASS f17663d1 python3 experiments/ptr-engine/tools/answer_degeneracy_check.py`
- `recorded verdict for 3d65a93c-04db-496e-8b00-8d37f9a4d399 [3bed4bf4-b054-4b76-a68f-68814c6d5f16]: PASS f17663d1 python3 experiments/ptr-engine/tools/tests/test_anchor_classify.py`

Both refusals are lexical and identical in kind:

- `refused (command-not-allowed): verdict command ".venv/bin/python" is not allowed: only test/build runners may be recorded (see checkVerdictCommand)`
- `refused (command-not-allowed): verdict command "const" is not allowed: only test/build runners may be recorded (see checkVerdictCommand)`

No row was recorded for `PROBE-CP3-V6`; its exit 1 is unchanged and its cell did complete — the drifted
`tools-off` assertion is the finding, not a broken card.

## The objective's question

**A verdict row can be recorded retroactively for a card whose execution has settled — settlement is not what
refuses reclaim.** `R2.1-TIGHTEN` (`3d65a93c`) had `status: failed` with `latestExecution.endedAt` set, and its
row was accepted after the fact; the card stayed in the failed column because recording a row is not a closure.
What actually refuses reclaim here is the **evidence allow-list** in `checkVerdictCommand`: 5 of the 9 green cards
ran `.venv/bin/python`, which is not a recognised runner token, and the 2 `node -e` cards were split at the `;`
inside their quoted program, so the checker judged the segment `const`. The refusals never reached ownership,
settlement, or sha checks. A second, quieter gap follows the ones that were accepted: each row cites today's
HEAD `f17663d1`, which is not the execution head sha, so a closure derived from it would still be
`FAIL sha-mismatch` — recording proves the work is green today, it does not retroactively pass the card.

**Smallest mechanism: a `reclaim` execution per card — a fresh, normally-settled run whose own settlement
carries the row and whose head sha is the tree the command actually ran against — instead of an attempt to write
a row into an already-closed execution.** It needs one operator decision, because the alternative fix (adding
`.venv/bin/python` to the runner allow-list and making the segment splitter quote-aware) widens what may be
recorded as evidence, and that is the gate's own policy, not this card's to change. The `reclaim` route needs no
policy change at all, only a card whose prompt is the stored command and whose write scope is empty.
