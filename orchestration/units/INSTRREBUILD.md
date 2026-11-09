# INSTRREBUILD

**Purpose.** Make `TX-01.v1.json` gradable and the mask-vs-fetch contrast measurable by closing 12 findings.

**Write paths.** `experiments/ptr-engine/longrun/tasks-v7/TX-01.v1.json`, `experiments/ptr-engine/ptr_engine/tx01_constants.py`, `experiments/ptr-engine/longrun/grade_v5.py`, `experiments/ptr-engine/longrun/score_longrun.py`, `experiments/ptr-engine/longrun/run_longrun.py`, `experiments/ptr-engine/longrun/arm_cd.py`, `experiments/ptr-engine/longrun/client.py`, `experiments/ptr-engine/longrun/tests/test_tx01_contrast.py`, this card, `handoffs/INSTRREBUILD.json`.

**Findings closed.** 12/12.

**Gradeable count.** 12/12 checkpoints reach a verdict through `grade_v5` normal entry point (12 pass on a correct transcript); one wrong answer fails (`num_mismatch`).

**Accounting proof.** D-arm fetch follow-up now gated via `gate.acquire()` and `sent >= budget` check before `send_chat`, with its own `tool-followup` row appended to `followup_rows`; verified by `test_arm_cd_wiring` (6 pass).

**Left open.** None.
