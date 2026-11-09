# VERBOSITY-CONFOUND

**Purpose.** Measure whether the grow arm's ~9x longer answers (recorded by ARM-TREATMENTS-FIRE in grid G4)
explain the headline p95 TTFT gap, so H1's claim (pointer-stable beats transcript-grow on p95 TTFT at
equal-or-better verified quality) can be judged with completion length controlled.

**Bound.** 24 tool calls. OFFLINE: zero inference requests. Stub handoff within first 5 calls.

**Reads.** All `experiments/ptr-engine/measure/rows-*.jsonl` (14 files, enumerated + hashed by the unit).
Schema is NOT uniform: older files carry `answer_text`/`ttft_server_s`; newer longrun files carry
`content`/`content_tokens`/`ttft_ms`/`ttft_s`/`latency_s`/`kind`/`timing_usable`.

**Writes (only these).**
- `experiments/ptr-engine/measure/VERBOSITY.json`
- `docs/VERBOSITY.md`
- `experiments/ptr-engine/longrun/tests/test_verbosity.py`
- `orchestration/units/VERBOSITY-CONFOUND.md`, `orchestration/handoffs/VERBOSITY-CONFOUND.json`,
  `orchestration/journals/VERBOSITY-CONFOUND.log`, `/tmp/vconf/**`

**Never touches.** Any rows file, any grade file, `analyze_stats.py`, `measure/LATENCY-REPORT.json`,
`measure/TVS.json`, `docs/OPERATOR-BRIEF.md`.

**Floor.** p95 is refused for any cell with n<60 (project floor). Mean/median/p90 still reported with n.

**Deliverable verdict vocabulary.** `confound_material` | `confound_immaterial` | `not_measurable`.
