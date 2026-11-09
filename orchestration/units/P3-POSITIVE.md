# P3-POSITIVE

**Purpose.** Find an already recorded transcript whose working set was complete and grade it as the Gate 0.1 positive control.

**Result.** No qualifying transcript. All 48-turn complete-working-set runs fail (`cp.t24`, `cp.t46`, `acc.2`-`acc.4`, `repair.main`). Closest: `rows-longrun-v4-2026-10-26.jsonl [pointer-stable]` and `rows-longrun-v4-tools-2026-10-26.jsonl [pointer-stable]`.

**Minimal funded need.** 48 requests on `http://192.168.2.168:8012/v1` (`occamy-1.0`, SGLang) over `LR-01.v4.json`/`LR-01.v9.json`, 1 arm, 1 replicate, with a recorded verify turn (`exit 0`).

**Write paths.** `orchestration/notes/joint-plan/P3-positive-control.md`, `orchestration/units/P3-POSITIVE.md`, `orchestration/handoffs/P3-POSITIVE.json`. No `pos-complete.jsonl` created (none qualifies).
