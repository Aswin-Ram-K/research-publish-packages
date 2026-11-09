# UNIT CELL-STAMP-WIRING

**Purpose.** Settle what happens to a fresh grid cell whose manifest carries **no**
`usable_for` stamp, and name the exact command the grid must run after each cell.

**Bound.** 24 tool calls; journal-first; handoff within 6 calls; verdict row before handoff.
**Mode.** Offline — zero requests, no sockets, no live cell.

## Findings (offline, on a real 48-turn era-B corpus)
1. Absent key ⇒ `usable_for_for_path` falls through `USABLE_FOR_FIELD in man`
   (`analyze_stats.py:722`) to `usable_for: None, source: "unstamped"`
   (`analyze_stats.py:733-734`). `select_usable_cells` excludes only on the empty list
   (`analyze_stats.py:749`), so the cell is **kept**; the CLI prints
   `usable_for unstamped ... not a certification` (`analyze_stats.py:1753`) and exits 0.
   ⇒ **absent == silently included**, never refused, never certified.
2. Three cases on `measure/rows-longrun-v6-tools.jsonl` (72 rows / 48 turns):
   absent → exit 0, `ttft_p50 n=48 144.81ms [143.58, 147.68]`;
   `["h1","h2","h3"]` → exit 0, same interval;
   `[]` → exit 1, `no usable cells`.
3. Stamp command: `python3 analyze_stats.py --stamp-rows <ROWS> --manifest-out <MAN>
   --usable-for "h1,h2,h3" --usable-for-reason "<why>"` (writer
   `write_cell_manifest_usable_for`, `analyze_stats.py:777`; CLI `:1647`).
   Stamping a good cell changes the reporting line and the record, not the numbers.
4. Guard `tests/test_stamp_wiring.py` (9 tests) pins the absent-key branch; its last
   test mutates a COPY to "treat absent as usable" and goes red. Branch unchanged.

**Deliverables.** `tests/test_stamp_wiring.py`, `docs/CELL-STAMP-WIRING.md`,
this card, `orchestration/handoffs/CELL-STAMP-WIRING.json`, journal.

**Kill condition.** If the absent-key branch could not be quoted with `file:line` or the
48-turn fixture could not be run offline, STOP and report `partial`.
