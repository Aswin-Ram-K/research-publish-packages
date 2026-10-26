# COMPILATION-LEDGER — the living index of findings and its rebuild machinery

**Unit.** COMPILATION-LEDGER (automated session, task-board card, tag `compilation`). 2026-10-26.
**Operator decision it implements.** Decision 3: compile findings, relations and compilable material
as we go, indexed and ready, so a later "compile everything into publishable material" pass is
assembly rather than re-reading. No live request was sent; `:8012/:8014/:8016/:8017/:8020` untouched.
**Rules owned elsewhere, not restated here.** `AGENTS.md` (board ancestry, write paths, handoff shape,
no-questions-in-automated-sessions, trace-pinning); `docs/PLAN.md` (what is built).

## Deliverables

| artefact | what it is |
|---|---|
| `papers/context-cache/COMPILATION.md` | the living index: 87 rows, one per finding, grouped in 14 themes (A–N) plus a 4-line 48-gap ledger |
| `papers/context-cache/COMPILATION-RELATIONS.md` | the relation map: `A -> B`, `A contradicts B`, `A == B`, one line each, each naming its source |
| `experiments/ptr-engine/tools/build_compilation.py` | dependency-free rebuild of the claim + status columns (stdlib only, no network) |
| `orchestration/handoffs/COMPILATION-LEDGER.json` | this unit's handoff |

## The refresh command (run this every compilation pass)

```bash
cd "/home/zer0null/reserach extarctor" && python3 experiments/ptr-engine/tools/build_compilation.py
```

It takes no arguments and needs no virtualenv. It prints, on one line:
`ROWS n | CLAIMS n | READY n | WITHDRAWN n` (READY counts `READY` + `READY-WITH-LIMITATION`;
WITHDRAWN counts rows whose strength is `WITHDRAWN`, not the `NOT-PUBLISHABLE` status).
Two further lines report row-file counts (`ROW-FILES checked … mismatch … not-parsed …`) and unresolved
claim ids / bad strengths. `--dry-run` computes and writes nothing. It exits 1 only if
`COMPILATION.md` itself is unreadable; every parse problem prints `NOT-PARSED` instead of a guess.

When a new finding lands: add one 7-column row to `COMPILATION.md` with its strength and claim cell
(`—` when there is no claim), prefix `[lim]` / `[live]` / `[op]` to the last column when one applies,
then run the command. **Never hand-edit a status cell** — the next pass overwrites it.

## Status rules (derived, in this order)

1. `[live]` -> `BLOCKED-LIVE`; `[op]` -> `BLOCKED-OPERATOR`.
2. strength `WITHDRAWN` or `UNSUPPORTED` -> `NOT-PUBLISHABLE`.
3. strength `DRAFTED` -> `BLOCKED-OPERATOR` (written, not ratified).
4. any claim id in the row absent from `CLAIMS.md` (or no claim id at all) -> `BLOCKED-OPERATOR`:
   measured but not citable, the gap-#11 precedent.
5. `[lim]` -> `READY-WITH-LIMITATION`; otherwise `READY`.

## Evidence

- first run: `ROWS 87 | CLAIMS 69 | READY 60 | WITHDRAWN 7`; second run: identical, `index unchanged`.
- idempotence: `cp` after run 1, run 2, `diff /tmp/comp-run1.md /tmp/comp-run2.md` -> no output.
- row files: 30 of 30 declared rows-counts in `CLAIMS.md` matched on disk; 7 JSON artefacts whose
  row count is not a line count (`U13`, `U14`, `M4-analysis`, `G1-analysis`, `E1-corpus`, `C1-corpus`,
  `V1-corpus`) print `NOT-PARSED` rather than a guess.
- unresolved claim ids: `C75 C76 C77 C78 C79 C80 C81` — drafted in `FOLD-PROPOSAL.md`, absent from
  `CLAIMS.md` by design (gap #40); they are the index's `BLOCKED-OPERATOR` fold block.
- `COMPILATION.md` is 190 lines, under the 220 bound.

## Assumptions recorded (automated session: no answerer)

1. **Status is derived, strength is authored.** Strength is a judgement about evidence (six values,
   unchangeable by the script); status is arithmetic over strength + claim resolution + marker, so the
   script can own it. A row whose strength is left off prints `BAD-STRENGTH` and is not rewritten.
2. **Marker placement.** `[lim]`/`[live]`/`[op]` live at the head of the last column rather than in the
   strength column, which the contract fixes to six values. The script strips nothing; it only reads them.
3. **`RECORD.md`'s C1–C10 labels are not claim ids.** They collide with `CLAIMS.md`'s C01/C03/C10, so the
   contradiction labels appear in finding prose only, never in the claim column (the script parses the
   claim column alone). This is the reason `W03`/`W04`/`W05` carry `—` and cite `RECORD.md:134`/`:118`.
4. **The 48 gaps are a ledger, not findings.** They live in a 4-column table by class so they cannot be
   mistaken for evidence rows; per-gap detail stays in `orchestration/GAPS-INVENTORY.md`.

## Blocker

None for this unit. The index's own `BLOCKED-OPERATOR` block is the operator's: ratifying the fold
(`GAPS-INVENTORY.md:48`, gaps #39/#40) is what turns 11 rows into publishable material; the 3
`BLOCKED-LIVE` rows need three live cells (gaps #14/#15/#17).
