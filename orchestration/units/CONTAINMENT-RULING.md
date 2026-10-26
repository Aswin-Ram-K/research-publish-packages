# CONTAINMENT-RULING — the five undisclosed `quality/` artefacts of 01:07–01:10

Card `8acfcd9a-e655-4573-bbb7-095a33750ab0`. Bound 22 tool calls. Zero live requests; read-only on every file ruled on.

## Census (five artefacts + their producer)
| file | size | mtime | role / provenance clause |
|---|---|---|---|
| `probe_instrument.py` | 3,464 B / 59 ln | 01:07:20.53 | agent-authored probe (`/v1/tokenize` render vs chat vs `/generate` warmth); docstring "reports both before any measurement depends on it". Imports `runner.post_json`; **no output artefact, no log** → designed, not evidenced as run. |
| `runner.py` | 37,533 B / 853 ln | 01:10:16.67 | **edited in place**: `__pycache__/runner.cpython-314.pyc` written 01:10:16.86 (0.19 s later = import smoke test); mode 0600 vs 0664 on every run-produced sibling. **No committed or older copy exists** — `git status` = `?? experiments/ptr-engine/quality/` (whole dir untracked); other `runner.py` in tree belong to different experiments. Diff vs the 00:38 version **not reconstructable** — named gap. Carries the repair edits: `# BILL-REPAIR (defect 1)` at `runner.py:488`, `P1_previous` at `:508`/`:615`, `def _billed` at `:706`, `_assert_aligned` at `:782`. |
| `rerun_corrected.py` | 2,500 B / 55 ln | 01:10:25.45 | agent-authored driver, header `BILL-REPAIR: re-run the four QUALITY-ARM arms with the CORRECTED runner`; unlinks and rewrites **only** `rows-corrected.jsonl`, never `rows.jsonl` (`:4-6`). |
| `rows-corrected.jsonl` | 8,278 B / **9 rows** | 01:10:35.15 | **fresh live re-run output, NOT a derivation of `rows.jsonl`**: all 9 `observed_at` = 01:10, `run_root` = `/tmp/ptr-quality-A-r0-67kehwbm` (≠ the 00:38 root), identical `index_sha256 e81ba025…`, and **76 field diffs** against the matching A/rep0 rows, concentrated in billing (`L` 8/9, `predicted_uncached` 8/9, `residue` 8/9, `P1_previous` 8, `P1` 4, `P1_tokenizer` 4, `cached_tokens` 4). **Schema-drifted, not "same columns"**: union keys **47 vs 60** — adds `P1_previous`/`P1_tokenizer`/`cached_tokens`/`cached_reported`/`server_uncached`/`server_keys`/`law_note`, drops `billed_tokens`/`billed_tokens_measured`/`per_turn`/`turns`/`arm_policy`. Covers **arm A, rep 0 only (10 rows of 115)**. |
| `rerun-corrected.log` | 963 B / 16 ln | 01:10:35.17 | stderr of that run — it **aborted**: `AssertionError: per_turn['%d'] bills P1=18794 but the row's own tokenizer count was 10902` (`runner.py:815`, `_assert_aligned`). `results-corrected.json` **absent** → `main()` never reached its aggregate; **0 of 4 arms completed**. |

Producer, dated: `orchestration/handoffs/BILL-REPAIR.json` (561 B, **01:06:47**) holds only `{"stage":"start"}`, `status:"partial"`, `artifacts: []` — the unit then wrote this trail 01:07→01:10 and **died without updating its handoff**. **Sixth artefact outside the five:** `experiments/ptr-engine/tests/test_quality_billing.py` (13,506 B, 01:10:12) — same dead unit, 16 test defs, outside the verifier's list.

## Q1 — what wrote each
**A later repair attempt that crashed** — one agent session editing by tool, then executing its own driver. Not a successful re-run, not hand-editing of data. Evidence chain in 3 s: `test_quality_billing.py` 01:10:12.72 → `runner.py` 01:10:16.67 → its `.pyc` 01:10:16.86 → `rerun_corrected.py` 01:10:25.45 → `rows-corrected.jsonl` 01:10:35.15 → `rerun-corrected.log` 01:10:35.17 (writer timestamps, not editor timestamps, on the two data files). `rows.jsonl` is **untouched** (00:38:14, 101,103 B), exactly as `rerun_corrected.py:4-6` promises.

## Q2 — load-bearing for a published claim?
**None.** Workspace-wide grep (`rows-corrected|rerun_corrected|rerun-corrected|results-corrected|P1_previous`) hits **no** line in `experiments/ptr-engine/RECORD.md`, `ADOPTION.md`, `quality/RESULTS.md` or `papers/**`. Only sites:
- `orchestration/handoffs/V-QUALITY-ARM.json:10` and `:23` — flags the five as undisclosed (the containment record itself)
- `orchestration/units/V-QUALITY-ARM.md:69`, `:80-81`; `orchestration/VERDICTS.md:4010` (CONTAINMENT paragraph)
- self-references in the five files; `orchestration/units/CONTAINMENT-RULING.md` (this file)

Record defect exposed: `experiments/ptr-engine/RECORD.md:120` (C4) says the repair unit "never ran … is a stub". **It ran and crashed.** C4 stays **OPEN**, but its premise is wrong.

## Q3 — ruling: **(a) KEEP, as a disclosed repair trail**
Not (c) ADOPT: 9 rows of one rep of one arm, no aggregate, no `results-corrected.json`, and a **different schema** (47 vs 60 keys) — it cannot re-derive the 115 rows it would have to supersede; `rows.jsonl` is defective **only in its billing column** (V-QUALITY-ARM) while its corpus and discrimination rows stand. Adoption trades a measured defect for an unfinished one.
Not (b) QUARANTINE: nothing cites them, so no claim needs protecting; and the trail is the **only live evidence the defect and its guard are real** — `rerun-corrected.log:16` is the corrected alignment assertion biting on live data (`P1=18794` vs tokenizer `10902`), and `runner.py` is already load-bearing for green guards. The violation was **non-disclosure, not corruption**; (a) answers it where it occurred.

## Q4 — minimal action (one sentence; another unit edits, I do not)
Into `experiments/ptr-engine/quality/RESULTS.md`, in `## Corrections (2026-10-25)` (after `:257`, before item 4 at `:259`):

> **Repair trail, undisclosed at handoff (01:07–01:10).** Five files here post-date the 00:39 handoff — `probe_instrument.py`, the corrected `runner.py`, `rerun_corrected.py`, `rows-corrected.jsonl` (9 rows, arm A rep 0 only, 47-key schema) and `rerun-corrected.log` — and are the remains of the crashed `BILL-REPAIR` attempt: its own alignment guard stopped it (`AssertionError: per_turn['%d'] bills P1=18794 but the row's own tokenizer count was 10902`, `rerun-corrected.log:16`), no arm completed, and no aggregate was written, so C4 stays OPEN and nothing may cite these files as a measurement.

Owner: a **fresh** unit (`BILL-REPAIR-2`) — not the session that wrote them, and not `REPAIR-QP-A/B` (which edited `RESULTS.md` at 02:40 for the verifier's corrections), so authorship and certification stay separate. Its second job: finish the 12 rep cells, persist per-turn `cached_tokens`, write `results-corrected.json`, then re-open ADOPT.

## Assumptions recorded
- "Derivation" read as field correspondence to `rows.jsonl`; the 76 diffs, the new `observed_at`, the new `run_root` and the 47-vs-60 schema settle it as a re-run, not a copy.
- `mode 0600` read as agent-tool writes vs `0664` run output; corroborated by the `.pyc` timestamp, not relied on alone.
- `probe_instrument.py` judged "designed, not run" from the absence of any output/log; its result content is therefore **unverified** — it supports no claim either way.
- Earlier `runner.py` unreconstructable (untracked dir, no copy): statements about "what changed" are limited to the guard behaviour provable from `rerun-corrected.log`, the 16 test defs and the repair markers — **named gap**.
