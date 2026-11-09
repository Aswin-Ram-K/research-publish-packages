# UNIT LATENCY-DEDUPE-FIX

**Status:** done · **Bound:** 26 tool calls (used 24) · **Offline:** zero requests · **Base sha:** f17663d1fed0162a7dc3c5a0a58d372c710974c3

Make the turn metric immune to the response-hash de-duplication (rule R), flip the two red tests, re-issue `LATENCY-REPORT.json`.

## 1. The rule as it stood

`experiments/ptr-engine/tools/latency_report.py:202-214` (before this unit):

```python
def dedupe(rows):
    """Rule R. Returns (kept_rows, groups, excess). First occurrence kept."""
    seen, kept, groups = set(), [], {}
    for r in rows:
        key = (r.get("ts"), r.get("content_sha256"),
               r.get("prompt_tokens"), r.get("completion_tokens"))
        if key in seen:
            groups[key] = groups.get(key, 1) + 1
            continue
        seen.add(key)
        kept.append(r)
```

- **Collision key:** `(ts, content_sha256, prompt_tokens, completion_tokens)` — `content_sha256` is `sha256(assistant content)`, a *response* hash, not a request identity.
- **Ordering that decides the survivor:** `seen.add(key)` / `kept.append(r)` — **first occurrence in wire order wins**; every later occurrence is counted in `groups` and `continue`d.
- **`TURN_ROW_KINDS` today:** consulted **nowhere** in `latency_report.py`. Its one owner is `experiments/ptr-engine/longrun/analyze_stats.py:608` (`('turn-initial', 'turn')`), consumed by `turn_latency_rows` at `analyze_stats.py:805-908`. The caller is `dedupe_rows` at `latency_report.py:230-245`, applied to a grid file at `:310-311` before the analyser is invoked at `:324`.
- **What a turn-kind row loses:** on collision it loses the whole turn — the earlier-written `tool-followup` mirror of the last send survives, and the frozen per-turn definition never selects a `tool-followup` row, so 48 turns measured as 46 (G8) / 37 (G9) even though the *measurement* was still present.

## 2. New precedence (one sentence)

On a collision a row whose `kind ∈ TURN_ROW_KINDS` always beats a non-turn row (same measurement, and it is the only copy the frozen definition can select); between two turn-kind rows the **later** write survives — later `row_seq`, else later `send_index`, else later position in the file — while every non-turn collision keeps the old first-occurrence rule, and the survivor stays in its original wire position so the kept-row count does not move.

`turn_row_kinds()` reads the set from `analyze_stats`, never restates it:

```python
if new_turn and not prev_turn:
    kept[pos], ords[pos] = r, ordinal      # 1: turn-kind wins
elif new_turn and prev_turn and \
        _row_seq(r, ordinal) > _row_seq(prev, ords[pos]):
    kept[pos], ords[pos] = r, ordinal      # 2: later turn-kind wins
continue                                   # 3: else first kept
```

`_row_seq` prefers `row_seq`, then `send_index`; the row schema of the measured cells persists neither (`arm, kind, rep, turn` are the only identity fields), so the file position is the fallback — and `run_longrun.py` already writes the attributed turn row as the *last* send of the turn (`send_index=len(followup_rows)`).

## 3. Proof: `a == b == 48` for every cell

a = turn-kind rows, b = turn rows surviving R, c = distinct `content_sha256`, d = distinct `prompt_sha256`.

| cell | rows | a | b before | b after | c | d | kept rows |
|---|---|---|---|---|---|---|---|
| G4 pointer-stable | 48 | 48 | 48 | **48** | 48 | 48 | 48 |
| G4 lease-reopen | 48 | 48 | 48 | **48** | 46 | 48 | 48 |
| G4 transcript-compact | 48 | 48 | 48 | **48** | 9 | 48 | 48 |
| G4 transcript-grow | 48 | 48 | 48 | **48** | 33 | 48 | 48 |
| G8 rows-longrun-v5-tools | 72 | 48 | **46** | **48** | 43 | 48 | 70 |
| G9 rows-longrun-v6-tools | 72 | 48 | **37** | **48** | 43 | 48 | 61 |

The four G4 arms were already 48/48 (excess 0 — R is a no-op there); the drop was on the two legacy mirrored tools files. "Before" numbers are the red tests' own: `test_rule_r_keeps_every_turn_the_definition_selects` failed with `rule R deleted 2 of 48 turns` (G8) and `11 of 48` (G9).

## 4. Red → green, and the mutation

- Fix in, whole file: `PYTHONPATH=src python3 -m pytest tests/test_turn_dedup.py -q` → **8 passed**, exit 0.
- Precedence mutated back (`if False and new_turn and not prev_turn:`): **8 failed**, exactly naming **G8 `rows-longrun-v5-tools.jsonl` (b=46)** and **G9 `rows-longrun-v6-tools.jsonl` (b=37)** — the two cells that carry the mirrored pairs.
- Restored: `cmp` byte-identical to the fixed file, 8 passed again.
- The two former red tests are now plain asserts (`assert len(dedup_turns) == len(raw_turns)`, `assert not missing`); `test_counts_are_three_different_questions` gained `assert got["b"] == 48`, so strictness lives in the assertion, not in a marker.
- One evidence test had to be mirrored: `test_dropped_rows_are_the_mirrored_copy_of_a_surviving_tool_call` now asserts the dropped copies are the `tool-followup` rows and each kept twin is a `TURN_ROW_KINDS` row (same measurement, same turn). Its claim is unchanged; only which side of the mirror is dropped changed.

## 5. Re-issued report (`experiments/ptr-engine/measure/LATENCY-REPORT.json`)

Regenerated **by its own generator**: `python3 experiments/ptr-engine/tools/latency_report.py --report …/LATENCY-REPORT.json --out …/LATENCY-REPORT.json --summary …`. Never edited by hand.

- `cells_moved`: **8 cells before, 8 cells after — identical set** (G2 transcript-grow, G4 lease-reopen, G4 pointer-stable, G5 pointer-stable, G6 pointer-stable, G7 pointer-stable, G8 pointer-stable, G9 pointer-stable). What moved inside them:
  - G8: `n_turn_dedup` 46 → **48**, `ttft_used` 45 → **47**, `n_followup_dedup` 24 → 22.
  - G9: `n_turn_dedup` 37 → **48**, `ttft_used` 37 → **48**, `n_followup_dedup` 24 → 13.
  - G7: `n_turn_dedup` 31 → **48**, `ttft_used` 30 → **47**, `n_followup_dedup` 20 → 3 (the same defect in the V4-TOOLS cell).
- Expected pins met: **G8 48/48, G9 48/48, `ttft_used` 47 for G8**.

## 6. Every p95 is still refused

`analyze_stats.min_n_for(0.95)` = 60; the largest cell that could carry a p95 here has n_dedup 70 but no analyser interval at that n. Measured on the regenerated file:

- `p95_inventory.cells_with_p95_raw = 0`, `cells_with_p95 = 0`, `cells = []` — **before and after**.
- `floor_policy`: `cells_with_p95_published = 0`, `cells_with_p95_withheld = 3`, `floor = 60`; 3 entries in `withdrawn` (G7 n_raw 68/n_dedup 51, G8 72/70, G9 72/61).
- Every cell's `p95` object has `point` null (refused by name): G8 "refusing p95 at n=47 … minimum n for p95 is 60", G9 "… n=48 …", G7 "… n=30". A 48-turn cell never produced a p95; the generator did not try.

## 7. Guards

- `experiments/ptr-engine/tools/withdrawn_index.py --self-test`: 15 entries, 0 problems.
- `withdrawn_index.py --check experiments/ptr-engine/measure/LATENCY-REPORT.json`: **pre-existing WI-004** — quote `318.14` at lines 1541 and 3865 (the G7 `supersedes.p95 = 318.143` withdrawal record), no correction within the 400-char window. Verified pre-existing: the identical two hits fire on the pre-fix report. **Not fixed here** (out of scope; `WITHDRAWN.json` is frozen for this unit).
- `path_refs.py --check`: 902 known (baselined), **35 NEW — all in other units' documents** (`RUNAWAY-POLICY`, `TVS-ROWS-IDENTITY`, `ANALYSIS-CONSUMER-FIX`, `GATE-ATTACK-STUB-FIX`, `RUNNER-ROUNDS-48`). **Pre-existing, not fixed here.** No finding points at a file this unit wrote.
- Untouched, as required: `analyze_stats.py` (thresholds), `analyze.py`, `cell.py`, `run_longrun.py`, rows, grades, `PARM-1`, `WITHDRAWN.json`.

## 8. Which published numbers change

The turn-level and TTFT cells for **G8, G9 and G7** change: `n_turn_dedup` climbs to 48 in all three (46/37/31 → 48/48/48), `ttft_used` rises to 47/48/47 (45/37/30), and the corresponding `n_followup_dedup` falls (24→22, 24→13, 20→3) — the same 70/61/51 rows, re-attributed from follow-up copies to the turn rows they mirrored. **Unaffected:** every p50 (11 cells), every p95 (all still refused/withdrawn, zero published), the kept-row and duplicate counts (`n_dedup` 70/61/51, `dedup_excess` 2/11/17 unchanged), the whole G4 four-arm table (48/48/0 excess, bit-identical), G1/G2/G3/G5/G6/G10, and the quality/comparison blocks (owned elsewhere). Separately, `transcript-compact`'s **9 distinct answers out of 48 turns** is a *quality* fact — the same refusal text repeated — not a latency fact and not a turn count; it belongs in the quality record (`measure/QUALITY-*` / the answer-degeneracy analysis feeding `TVS.json`), where the response-diversity count is the unit. It is **not** recorded here, and `c=9` was not allowed to move any latency number.
