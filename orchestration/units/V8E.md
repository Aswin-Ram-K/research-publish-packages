# V8E — recovery verifier: re-verify U8.11's graph-chain fixes (supersedes V8D)

**Purpose.** Independently complete the re-verification of U8.6/U8.7/U8.8 (defects V8C, fixed by U8.11) and settle the
observation V8D died holding: *"Stage shows `ok` with empty counts."* **V8E fixes nothing.**

**Bounds.** ≤28 tool calls (used 26); one Occamy probe (DOWN, `000`); zero live LLM calls; ≤2 live `run` invocations;
no graph build; only `tests/test_run.py`; full `__pycache__` purge + `PYTHONDONTWRITEBYTECODE=1` for every revert/restore.

**Recovery.** V8D left no unit card, no `state/logs/V8D*`, a stub handoff (`checks:[]`, `"blocker":"in flight"`), and
only harness fragments. `run.py` sha256 **`78ae6101…`** == U8.11's release sha ⇒ `action_taken: none`; revert markers 0.

**Finding.** The empty-counts stage was the harness's **fake** graph impl (`_ALL_OK["graph"]` → `reason:"fake ok"`,
`counts:{}`) — **(A) honest**, not lossy. The real `_stage_graph` carries `mode/nodes/edges/sha256/provenance`.

**Result.** PASS on the substance: element check ungameable, full-64 digest boundary correct, all six pin states behave
as claimed and loudly, default fail-closed, override CLI-unreachable, two red→green guards reproduced with bit-identical
restores. One overstatement: **1** existing assertion strengthened, not 3.

**Evidence.** `state/logs/V8E-live.txt`, `state/logs/V8E-red-green.txt`, `state/verify/V8E/{probe,harness,live}.py`,
`state/verify/V8E/{probe,harness}.out`, `orchestration/VERDICTS.md` (V8E section), `orchestration/handoffs/V8E.json`.

**Write paths.** `orchestration/{VERDICTS.md,units/V8E.md,handoffs/V8E.json}`, `state/logs/V8E*`, `state/verify/V8E/**`.
