# STATUS-E — `status-refresh`

**Batch:** context-cache mechanism batch (2026-10-21). **Automated session — no questions asked.**
**Mode:** `status-refresh`, offline, **0 live requests**, **no `.occamy.lock`**.

## OBJECTIVE (one)
Rebuild `orchestration/STATUS.md` from the record so it reflects the mechanism batch that just settled
(E1–E4, LIVE-MEAS, the rep-3 probe, and every verifier/repair unit that touched them) **while keeping
the docket/deliverable program (§§1–6) intact**, with the sweep recounted from disk.

## INPUT STATE
- `orchestration/handoffs/*.json` (623 entries, 617 parseable), `orchestration/units/*.md` (599).
- `orchestration/STATUS.md` at 128 lines: two batches stale — "192 handoffs", "178 unit cards",
  the U8.56 sweep, and `running` = launched-without-handoff.
- `orchestration/VERDICTS.md` (3,700 lines).

## HARD BOUND
≤ 20 tool calls, ≤ 20 min, 0 live requests, no lock, no `git`, no `VERDICTS.md` write.
Nothing written outside the three declared paths.

## METHOD
1. Scripted sweep of every handoff: `json.load` per file, counts by shape (`status` vs `overall`) and by
   value, handoffs that fail to parse, cards without a handoff, handoffs without a card, and missing
   contracted keys per shape.
2. Dumped the 18 card-listed units plus `E2C` (a correcting handoff) — `status`/`overall`, `evidence`,
   `next_unit_hint`, `not_reproduced`/`overstated`/`corrections`/`checks`.
3. Read the `VERDICTS.md` tail (~6 entries) for the gate text.
4. Rewrote `STATUS.md` atomically: temp file → `json`-shaped sanity (`wc -l`) → `mv` into place;
   §§1–6 preserved with dated scoping notes, new §7 added, old §7 renumbered §8.

## RESULT
- `STATUS.md`: **128 → 250 lines**; attribution now `STATUS-E`; one-line state names both
  programs. §§1–6 preserved with dated scoping notes; old §7 renumbered §8; §7 added.
- §7 carries the 19-unit table, gate outcomes, the manuscript-safe facts block, and 6 open items with
  their exact numbers.
- No claim re-measured live; every experiment number is quoted from a handoff or a verifier's ruling,
  and every corrected claim is cited to its **correcting** unit (E3C, E2C, E4C/E4C3, LMC, E4RC).

## WRITE PATHS
`orchestration/STATUS.md`, `orchestration/units/STATUS-E.md`, `orchestration/handoffs/STATUS-E.json`.
