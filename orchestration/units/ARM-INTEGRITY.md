# UNIT ARM-INTEGRITY — arm-label integrity audit

**Objective.** Prove the four arm labels (`pointer-stable`, `transcript-grow`, `transcript-compact`,
`lease-reopen`) name four genuinely different behaviours, and that `pointer-stable` rows were produced by
the pointer engine rather than a transcript. **Bound:** 26 tool calls. **Offline:** zero inference requests.
**Auditor:** read-only — the runner, arms, rows, fixtures, analyzer and reports were not edited.

**Write paths (exactly):** `docs/ARM-INTEGRITY.md` · `experiments/ptr-engine/measure/arm-integrity.json` ·
`orchestration/units/ARM-INTEGRITY.md` · `orchestration/handoffs/ARM-INTEGRITY.json` ·
`orchestration/journals/ARM-INTEGRITY.jsonl` · `/tmp/**`.

**Method.** (1) read `Planner.build` dispatch (`run_longrun.py:1052`) and pin source shas; (2) name the
difference per pair; (3) per-arm signature from row fields (`prompt_tokens`, `prompt_sha256`, `evicted`,
`lease`, `fetch_rounds_used`, `tool_calls[].pinned_lines`, `kind`); (4) OLS prompt-token slope
on turn index per arm; (5) cross-grid consistency (fixture sha, manifest keys, T1 prompt bytes).

**Result.** Four distinct code paths (`run_longrun.py:1057/1076/1094/1112`). Five of six pairs `distinct`;
`grow × compact` is **`distinct-in-code-only`** because the cap is never reached: `wall_tokens=65536` and the
largest prompt in any grid is 34,279 tok (52.3 %), so `evicted>0` appears in 0/192 grow rows and a
`kind:"digest"` row in 0/788 rows — below the wall the two arms emit byte-identical prompts (6 shared
`prompt_sha256` at T1–T6, stage1). `lease-reopen` never reopened either: `lease_reopen_turns` is absent from
all 7 fixtures, `lease == 1` on 96/96 rows. `pointer-stable` never grows like a transcript (slope 2.72–4.85
tok/turn vs 38.79–676.96; 0 shared prompt bytes) — no mislabel. No row or manifest carries a code/harness
sha, so cross-grid implementation identity is not provable from the record, and v5-vs-v6 pointer T1 differs
on the same fixture (3,515 vs 3,520 tok).

**Deliverables:** `docs/ARM-INTEGRITY.md`, `experiments/ptr-engine/measure/arm-integrity.json`,
`orchestration/handoffs/ARM-INTEGRITY.json`.
