# TTFT definition — which row kind defines per-turn latency

**Unit:** `TTFT-KIND-DEFINITION` · **version:** `ttft-definition/1` · **offline:** zero inference requests.
**Selector:** `turn_latency_rows()` in [`experiments/ptr-engine/longrun/analyze_stats.py`](../experiments/ptr-engine/longrun/analyze_stats.py).
**Measured impact:** [`experiments/ptr-engine/measure/TTFT-DEFINITION-IMPACT.json`](../experiments/ptr-engine/measure/TTFT-DEFINITION-IMPACT.json).
**Rows model this is defined against:** [`docs/ROW-MODEL.md`](ROW-MODEL.md) (unit `TURN-ROW-ATTRIBUTION`, PASS `f17663d1`).

## 1. The definition (one line)

> **per-turn TTFT = the TTFT of the turn's own initial request**: the `kind="turn-initial"` row when present; otherwise the legacy `kind="turn"` row, recorded as `definition_fallback: true`. A `kind="tool-followup"` row is a request *inside* a turn and is never a turn's latency.

## 2. Why this row, and not the last follow-up

After `TURN-ROW-ATTRIBUTION` a turn with k follow-ups has **k+1 sends and k+1 rows**: one `kind="turn-initial"` (`send_index=0`), k `kind="tool-followup"` rows, and the **last follow-up** is written as `kind="turn"`. A tools-on cell therefore offers two candidate latency rows per turn, and they answer different questions:

| candidate | what it measures |
|---|---|
| `kind="turn-initial"` | how long the system took to start answering **this turn** — includes any pre-tool work |
| `kind="turn"` | the latency of the **last tool round-trip** inside the turn |

The operator's metric is **p95 TTFT over a long run**, i.e. "how long does the system take to start answering each turn". That is a statement about the turn's initial request. The alternatives are rejected for three concrete reasons:

1. **Wrong question.** The last follow-up measures a mid-turn re-query. Quoting it as the turn's TTFT reports the model's second thought as its first response.
2. **The metric would depend on tool policy.** An arm that calls the tool more often gets a different (and larger) sample, so a "latency" comparison across arms would partly measure how eager each arm was to fetch. TTFT must not move when only the fetch count moves.
3. **It double-counts sends.** In the legacy files the `kind="turn"` row *mirrors* the last follow-up's measurement, and the follow-up rows are in the same file. Counting every row as a turn gave G8 a published p95 at **n=70** and G9 one at **n=61** on cells that hold **48 turns** each — 46 % and 27 % of those denominators were sends, not turns.

The cost of the choice is stated plainly: for a *legacy* multi-send turn the initial request's TTFT was never written, so that fallback figure still quotes the last send. It is labelled `definition_fallback: true` with a `mirrored_turns` count, and no new cell may produce that label (`definition_violations()` reports a writer that omits the `turn-initial` row).

## 3. One selector, every path

`turn_latency_rows(rows) -> (selected_rows, meta)` is the only place the choice is made. It returns **one row per turn** plus a meta record (`mode`, `definition_fallback`, `n_selected`, `explicit_initial_rows`, `fallback_rows`, `mirrored_rows`, `dropped_followup`, `dropped_turn_followup`, `dropped_duplicate`, `turns_without_turn_row`).

Every caller:

| caller | how it uses the selector |
|---|---|
| `analyze()` — arm `p50`/`p95` block | selects once per arm; `ttft_values()` runs over the selected rows, so `n` is the turn count |
| `analyze()` — quantile comparison path | `compare()` is handed `report["arms"][arm]["ttft"]["values"]`, i.e. the same selected values — the definition cannot be half-applied |
| `paired_by_turn()` (McNemar + any paired path) | selects both sides before indexing, so pairs are turns, not sends; `dropped_followup_*` and `definition_fallback_*` are reported in its stats |
| CLI `analyze_stats.py --rows …` | prints one `definition:` line per arm (version, turns selected, follow-up rows dropped, mode, fallback, mirrored turns) before any figure |
| CLI `--check-definition` | runs `definition_violations()` per row file; exit **3** on a violation |

`analyze(selector=…)` and `paired_by_turn(select=…)` exist so a test can inject the identity selector and prove what the definition changes — the red side of §6 — without editing anything on disk.

## 4. Legacy and tools-off cells

- **Tools-off cells** (one send per turn) are value-identical before and after: for every non-tools grid (G1, G3, G4, G5, G6, G10) the selector's p50 equals the published p50 exactly — verified in the impact artefact, `tools_off_all_identical: true`.
- **Old rows with no `send_index` / `turn-initial`** still resolve: the `kind="turn"` row is selected and the figure carries `definition_fallback: true`. When such a turn also has follow-up rows the meta counts it in `mirrored_rows` — those are the rows where the fallback is not merely unproven but **known** to quote the last send (tools-off cells have `mirrored_rows: 0`).
- **No rows file on disk carries `kind="turn-initial"`** yet (`cells_with_turn_initial_on_disk: []`), so every published cell is a fallback cell. That is the state the definition has to survive, not a reason to postpone it.

## 5. What the decision changes in the published record

Recomputed offline from the row files; published values are read **verbatim** from `measure/LATENCY-REPORT.json` and are not restated by this unit. Every figure below states its definition and its n.

**G7 — V4-TOOLS** (68 rows, 48 turns; 31 single-send, 17 with follow-ups)

| definition | n | p50 | p95 |
|---|---|---|---|
| B — published record (all rows, deduped by measurement) | 51 | 198.72 ms [166.05, 206.66] | REFUSED (n=51 < 60) |
| **A — per-turn (`turn-initial` else fallback)** | **48** | **199.91 ms [165.33, 206.66]** | **REFUSED (n=48 < 60)** |
| A, definition-true subset (k=0 turns only) | 31 | 153.78 ms [145.73, 205.57] | REFUSED (n=31 < 60) |
| B, mirrored turns only (the rows B quoted a follow-up for) | 17 | REFUSED (n=17 < 20) | REFUSED |

**G8 — V5-TOOLS** (72 rows, 48 turns; 45 single-send, 3 with follow-ups) — *the only published tools-on p95*

| definition | n | p50 | p95 |
|---|---|---|---|
| B — published record (all rows, deduped) | 70 | 143.91 ms [140.23, 151.95] | 397.41 ms [273.84, 659.70] |
| **A — per-turn (`turn-initial` else fallback)** | **48** | **139.77 ms [134.60, 142.08]** | **REFUSED (n=48 < 60)** |
| A, definition-true subset (k=0 turns only) | 45 | 137.51 ms [133.46, 141.65] | REFUSED (n=45 < 60) |
| B, mirrored turns only | 3 | REFUSED (n=3 < 20) | REFUSED |

**G9 — V6-TOOLS** (72 rows, 48 turns; 35 single-send, 13 with follow-ups)

| definition | n | p50 | p95 |
|---|---|---|---|
| B — published record (all rows, deduped) | 61 | 147.59 ms [144.26, 168.07] | 429.70 ms [318.80, 477.06] |
| **A — per-turn (`turn-initial` else fallback)** | **48** | **144.81 ms [143.49, 149.52]** | **REFUSED (n=48 < 60)** |
| A, definition-true subset (k=0 turns only) | 35 | 143.53 ms [142.60, 144.66] | REFUSED (n=35 < 60) |
| B, mirrored turns only | 13 | REFUSED (n=13 < 20) | REFUSED |

**Consequence, one sentence:** every published tools-on per-turn figure quoted the last follow-up of the turn over a population that counted follow-up sends as turns; the p50 correction is small and its sign is not uniform (G7 +1.18 ms, G8 −4.15 ms, G9 −2.78 ms), but both published tools-on **p95** values (G8 397.41 ms at n=70, G9 429.70 ms at n=61) fall to **n=48** under one row per turn and must be **REFUSED**, not restated.

This unit does **not** edit `docs/LATENCY-REPORT.md` or `measure/LATENCY-REPORT.json`. The comparison is handed to the page's owner (`OPERATOR-BRIEF-3`) and to `LATENCY-UNDER-DISPUTE`.

## 6. Tests (`experiments/ptr-engine/longrun/tests/test_ttft_definition.py`)

Green — 8 cases: selector picks the initial request when it is slow *and* when it is fast (p50 differs from the last-follow-up figure by exactly 780 ms and 850 ms respectively); one sample per turn, never per send (72 rows → n=24); legacy cell resolves with `definition_fallback: true` and `mirrored_turns: 24`; tools-off cell value-identical with zero mirrors; both paths share the selector (pairing forms 24 pairs from a 72-row file, 48 follow-up rows dropped, every paired row is the turn row); the n≥60 p95 floor still refuses at n=48; `definition_violations()` reports a turn whose only turn row is a follow-up send, a follow-up carrying `send_index=0`, and two `turn` rows for one turn.

Red (injected, nothing on disk edited: `analyze(selector=identity)` / `paired_by_turn(select=identity)`):

```
RED selector reverted: 72 rows -> 72 samples, p50=120.0 ms (the 120 ms follow-up), not the 900 ms initial request
RED selector reverted: pairing drops 0 follow-up rows, so a turn's paired row can be a tool-followup (48 such rows in this 24-turn cell)
RED selector reverted: a 48-turn cell with k=1 offers 96 samples (follow-up rows promoted to turns), which is how a 48-turn cell published a p95 at n=70
```

Run: `python3 experiments/ptr-engine/longrun/tests/test_ttft_definition.py --red-green`

## 7. What this unit did not change

Floor policy (`min_n_for(0.95) = 60`, `MIN_N`, `TAIL_MIN`), the bootstrap (`RESAMPLES`, `SEED`), and the disputed dedupe rule are untouched — they belong to `LATENCY-UNDER-DISPUTE` and `PARM-1`. No rows file, fixture, writer, grader or published page was modified.
