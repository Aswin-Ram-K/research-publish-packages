# GAP-LEDGER2 — gap status derived from resolvable evidence

**Status:** done. **Bound:** 18 tool calls (19 used; the extra call is the unit card required by AGENTS.md).
**Writes:** `state/gap-ledger.json`, `tests/test_gap_closure_ledger.py`, this card, the handoff JSON.

## Objective

Stop trusting `papers/context-cache/GAPS.md` prose for gap status. Build a machine-checkable ledger whose
`derived_status` comes from evidence that exists on disk, and a test that re-derives it.

## Method

1. Parse the 15 `## G<n>.` sections plus the `## Downgrade note` section (16 entries).
2. Record each entry's exact stated status words, every `file:line` / claim id / cell path / handoff it cites,
   whether it still lists a remainder, and a derived status:
   `unverifiable` (any cited ref does not resolve) > `closed` (a resolving checker ref: claim in `CLAIMS.md`,
   cell with `rows.jsonl`, handoff `done`) > `narrowed` (closed but remainder present) > `open`.
3. Streamed to disk in two halves (G1–G8, then G9–G15 + downgrade) so no single turn carries the table.
4. `tests/test_gap_closure_ledger.py` re-derives everything: id-set equality, ref resolvability, stated-vs-derived,
   recomputed derived status, stored resolution flags, stale-citation audit, and honest `known_missing` entries.

## Result

16 entries: **closed 2** (G1, G5), **narrowed 3** (G3, G4, G11), **open 10** (G2, G6–G10, G12–G15),
**unverifiable 1** (downgrade note). No stated status disagrees with its derived status.

Red→green: moving `experiments/context-cache/cells/G1/rows.jsonl` aside fails with
`G1: `cells/G1` (cell) does not resolve` and `stated 'CLOSED by G1 (C44)' claims closed but derived 'unverifiable'`;
restored with `cmp` byte-identical → `8 passed`.

## Findings left to the prose owner

- Six stale line citations: MANUSCRIPT `:14`, `:100`, `:439`, `:424` (G5) and `:424` (G7) do not carry the quoted
  figures (actual sites `:16`/`:163`, `:131`, `:625`, `:581`); EVIDENCE `:240` is empty.
- The downgrade note cites `experiments/context-cache/cells/SGLang/u2_gate.py`, absent from disk
  (the only gate is `cells/U2/u2_gate.py`) — recorded as the single `known_missing` entry, not silently skipped.
