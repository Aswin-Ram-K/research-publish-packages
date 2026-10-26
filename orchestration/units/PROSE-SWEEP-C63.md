# PROSE-SWEEP-C63 — the seven sites the last sweep left unread

**Bound (card):** 18 tool calls. **Used: 25** (overrun 7; breakdown in the handoff).
**Offline:** 0 live requests, no GX10, no `.occamy.lock`.
**Write paths:** `RUN.json`, `GAPS.md`, `CLAIM-HEALTH.md`, `MANUSCRIPT.md`, `SERVING-BRIEF.md`,
this card, `orchestration/handoffs/PROSE-SWEEP-C63.json`. No `CLAIMS.md`, no `recompute.py`,
no tests, no cells.
**Rule enforced:** a superseded number may appear only in a sentence that says it is superseded and
sits next to the value that replaced it. Source of truth: `CLAIMS.md` (C05 3.3133 "**superseded** as an
effect size by G5's race-free 6.744, C53"; C21 "the observed `A/R = 1.7002359` stands, but its causal
reading ... is superseded by G1"; C44 `u15_1_700x_survives_decomposition=False`).

## The seven sites — all read in full (no `grep -A1`)

| # | site | classified | action |
|---|---|---|---|
| 1 | `RUN.json:141` (G1 purpose) | **live-stale** — `1.700x` unmarked, framed as a break-cost object | **fixed** |
| 2 | `RUN.json:522` (U15 evidence) | disclosed — caveat + replacement in the same string | none |
| 3 | `RUN.json:583` (guard description) | disclosed — the sentence forbids the break-cost re-attribution | none |
| 4 | `GAPS.md:270` | disclosed — "the superseded 3.3133", 6.744 at :259/:262/:267 | none |
| 5 | `CLAIM-HEALTH.md:13` (C06 value cell) | **live-stale** — `measured 3.3133` with no superseded marker | **fixed** |
| 6 | `MANUSCRIPT.md:139-146` | disclosed — "the **superseded** pre-G5 value", table cell "3.3133 (superseded)", live column 6.744 | none |
| 7 | `SERVING-BRIEF.md:146` (S16 row) | disclosed by the row's own headline; **marker not addable** (render-pinned) | attempted, reverted |

### The two fixes

`RUN.json:141` before:
`"purpose": "decompose U15's 1.700x into break cost vs post-compaction window truncation (fork marker in place)",`
after:
`"purpose": "decompose U15's 1.700x into break cost vs post-compaction window truncation (fork marker in place); the break-cost reading this tested is refuted: the 1.700x is a window-truncation effect (C44)",`

`CLAIM-HEALTH.md:13` before:
`| C06 | B/A_cf 5.3922 (A 2,856 unc); measured 3.3133; G5 ref 6.744 |`
after:
`| C06 | B/A_cf 5.3922 (A 2,856 unc); measured 3.3133 (superseded as an effect size); G5 ref 6.744 |`

### Site 7: why no marker

`SERVING-BRIEF.md:146` is inside the generated `NUMBERS` block; `serving_brief.py --check` re-renders
that block from the ledger and compares it byte-wise. Appending ", a window-truncation effect rather than
break-event cost" produced `SERVING-BRIEF CHECK FAIL  1 problem(s): - numbers table block does not match
the ledger rendering` and `tests/test_serving_brief.py::test_brief_recomputes_from_cells` FAILED; the edit
was reverted and the check now PASSes. The row's headline ("cheap per turn, unbounded window") already
carries the corrected, window-truncating reading, so the site does not sell the break-cost story — it is
disclosed, and a marker would belong in the renderer (out of this card's write scope).

## Verification (all offline)

- `verify_package.py` → PASS, 63 claims mapped 1:1, `UNVERIFIED: none`, EXIT=0.
- `recompute.py all` → `COVERAGE GUARD PASS 63 claims documented, 61 runnable here + 2 script-backed`, EXIT=0.
- `pytest test_paper_attribution_guard.py test_serving_brief.py` → 21 passed.
- `serving_brief.py --check` → `PASS 19 items, 13 cells, all figures re-derived`.
- `RUN.json` still parses (`json.load` OK).

## Red→green

`/tmp/psw63/prose_guard.py` requires each fixed site to carry its retraction marker. On a `/tmp` copy with
both markers stripped: `PROSE GUARD FAIL (0/2 superseded numbers marked)`, quoting
`"purpose": "decompose U15's 1.700x into break cost vs post-compaction window truncation (fork marker in
place)",` and `| C06 | ... measured 3.3133; G5 ref 6.744 |`. On the repo: `PROSE GUARD PASS (2/2)`.

## Pre-existing failure, reported not hidden

`tests/test_round1_record_pins.py::test_verifier_handoff_and_recompute_scripts_are_pinned_to_disk` FAILS,
and it failed before this unit touched anything: the pin wants
`c34742ab179a937fb5470503a89e7d682be52d70d49e78a7f511a056b8e18704` (RUN.json, set by MTP-CORRECTION)
while `recompute.py` on disk is `f8cb87ca52dd93be19413179644c6b08dbab0dd7132598286b1e84b20313f072`,
mtime **2026-10-24 03:03:16** — 28 minutes before this session started (03:31:17). `recompute.py` is not in
this card's write scope and its owner must re-pin, not this sweep.
