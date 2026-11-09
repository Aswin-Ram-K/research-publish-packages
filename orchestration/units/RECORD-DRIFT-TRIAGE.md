# UNIT `RECORD-DRIFT-TRIAGE`

**Purpose.** Decide by measurement whether two drifting artefacts are the record's fault or their readers'.
**Bound:** 22 tool calls. **Offline:** zero requests. **Verdict:** `record_stale` (A), stale label (B).

## A — the red accuracy test
Test: `experiments/ptr-engine/measure/test_accuracy_recomputed.py:30`

    AssertionError: regenerated record differs from the published one
    At index 26937 diff: b'3' != b'a'    (1 failed, 1 passed in 0.04s)

Regeneration (generator embedded in the record, run into /tmp) differs in **exactly two data paths**, both
derived from one source:

| path | published | regenerated |
|---|---|---|
| `aggregate_records_checked[2].source_sha256` (source `measure/OPERATOR-BRIEF.json`) | `aa887d0a…c6e91b` | `3d2da7bb…104f9c` |
| `aggregate_records_checked[2].mentions_3/25` | `false` | `true` |

The record (mtime 11:54) predates the brief's rewrite (mtime 12:47) by card **`OPERATOR-BRIEF-4`**
(`orchestration/handoffs/OPERATOR-BRIEF-4.json`, `generated_utc 2026-10-26T18:10Z`), which introduced the
literal `3/25` at `experiments/ptr-engine/measure/OPERATOR-BRIEF.json:65` (`quality.grade_v5.value`).
No volatile field exists in the record (no `computed_at` / `generated_at` / `paths`); the byte comparison
is therefore legitimate and the **record is the stale side**.

Proof (`/tmp` copy of the measure dir): published record → **1 failed, 1 passed**; record replaced by a
fresh regeneration → **2 passed**; flipping one data field (`mentions_5/43` `true→false`) in that
regenerated copy → **1 failed, 1 passed**. Two generator runs are byte-identical, so the failure is not
nondeterminism. **No edit made** — regeneration is a card (command in the handoff).

## B — the misleading label
`experiments/ptr-engine/tools/latency_report.py:672-674` writes `p95_inventory.cells_with_p95_raw` as a
count over `prior["cells"]` — the **previous** artefact's p95-bearing cells, also consumed as `p95_before`
at `:711`. In `measure/LATENCY-REPORT.json` a reader sees `cells_with_p95 = 0` beside
`cells_with_p95_raw = 0` and reads the second as "0 refusals"; it actually means "the prior artefact
published no p95 point". **Fix chosen: documentation, not rename** — renaming the key in the tool without
regenerating the published artefact would leave code and JSON disagreeing, and the report is outside this
unit's surface. One sentence on `docs/LATENCY-REPORT.md` (owning page) + the same note as a comment at the
write site.

Numbers unchanged: `cells_with_p95=0`, `cells_with_p95_raw=0`, `cells_with_p50=11` before and after;
`measure/LATENCY-REPORT.json` sha256 `d48aff2f…` identical; `withdrawn_index --check docs/LATENCY-REPORT.md`
rc=0 before/after; `path_refs --check` rc=1 before/after with 41 new entries, **0** in the edited page.

## Which side was stale
A: the record. B: the label (the number was right).
