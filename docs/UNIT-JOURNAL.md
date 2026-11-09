# UNIT-JOURNAL — the append-only unit journal

**Tool:** [`experiments/ptr-engine/tools/unit_journal.py`](../experiments/ptr-engine/tools/unit_journal.py) ·
**Tests:** [`experiments/ptr-engine/longrun/tests/test_unit_journal.py`](../experiments/ptr-engine/longrun/tests/test_unit_journal.py) ·
**Live example:** [`orchestration/journals/UNIT-JOURNAL.jsonl`](../orchestration/journals/UNIT-JOURNAL.jsonl)

## Why this exists

Three cards in this project were killed by harness restarts **at their handoff step**. Because the
handoff was written *last*, each kill destroyed the unit's evidence while the work itself had
succeeded:

- `Q0-ANSWER-DEGENERACY` (`17a76d24`) — artifacts landed, handoff did not; a second card (`Q0-COMPLETE`) had to rewrite it.
- `PROBE-CP3-V6` (`4e559586`) — the cell completed and rows were written, but `orchestration/handoffs/PROBE-CP3-V6.json` stayed a 1,175-byte pre-run stub; `V6-COMPLETE` had to reconstruct from the rows.
- `LIVE-SMOKE-CELL` (`dbed0e9d`) — settled by hand after 6 requests; the handoff was written only by luck on the way out.

Each time the cost was a fresh card plus its tool calls, and each time the loss was invisible: the card
read `failed`/`cancelled` while the work had in fact succeeded.

A journal moves the evidence **off the end of the run** and spreads it across the run.

## Record shape

One JSON object per line at `orchestration/journals/<UNIT>.jsonl`:

```json
{"t":"2026-10-26T15:04:11Z","step":7,"kind":"artifact","path":"docs/X.md","bytes":4021,"note":"section 3 written"}
{"t":"2026-10-26T15:04:19Z","step":8,"kind":"evidence","command":"python3 tools/x.py","exit":0,"out":"PASS 12/12"}
{"t":"2026-10-26T15:04:25Z","step":9,"kind":"next","text":"run corpus audit, then handoff"}
```

The first line is a `header` record (`unit`, `card`, `bound`, `paths`). `--kind` is one of
`artifact`, `evidence`, `next`, `assumption`, `blocker`. `step` is assigned by the tool as
`last step + 1`, so steps are monotone without the caller tracking state.

## When a unit logs

| Moment | Record |
|---|---|
| at start, before any work | `init` — header with unit, card id, bound, declared write paths |
| **after every artifact write** | `log --kind artifact --path … --bytes … --note …` |
| **after every evidence command** | `log --kind evidence --command … --exit … --out "<tail of the actual output>"` |
| when a non-obvious default is chosen | `log --kind assumption --text …` |
| when progress stops | `log --kind blocker --text …` |
| **before the handoff** | `log --kind next --text "<what the follow-up card should do>"` |

Log **as the work happens**, not at the end. A record written at step 3 survives a kill at step 9; a
record written "when done" survives nothing. The `next` record is what makes a kill survivable: it is
the handoff's intent, logged while the unit still knows it.

## Why append-only

The failure this protocol repairs is *the last write destroying the record*. A journal that is
rewritten — even to "tidy" it, even to correct a step number — has a window in which the whole file is
new and empty: a kill inside that window loses every record, exactly the handoff failure again, only
with more records at stake. Appending one line means a kill can destroy **at most the line being
written**, and a torn half-line is expected rather than fatal: `status` and `resume` skip unparseable
lines and count them (`torn_lines`).

The tool therefore has exactly one write path, `_append()`: open in `"a"`, write one line, `flush`,
`fsync`. There is no `rewrite`, no truncate, no `os.replace`, and `init` **refuses** (exit 2) if the
journal already has bytes. A test asserts that two successive `log` calls leave the earlier bytes
byte-identical.

## How a follow-up card uses `resume`

```bash
python3 experiments/ptr-engine/tools/unit_journal.py resume --unit PROBE-CP3-V6
```

It prints one paragraph a fresh unit can paste as its starting context: records and last step, the
artifacts that **exist** with byte sizes, the artifacts that are logged but **missing** (re-create them
or log a blocker), the last evidence line, any open blocker, and the last stated next action. It never
writes, so it is safe on a journal owned by a dead or live session.

`status` is the same inspection without the paragraph, and it exits non-zero **only** when a logged
artifact is missing — naming it on a `MISSING-ARTIFACT:` line — so it can be used as a checker without
turning a torn line into a failure.

## Hard rules

1. **`orchestration/journals/` is never edited and never cleaned.** No corrections, no compaction, no
   deletion. A journal for a superseded unit **stays**: it is the only record of what that unit actually
   did before it was replaced. Wrong steps are corrected by appending, never by rewriting.
2. **Journals are per unit.** One file per unit card; never fold two units into one file, never
   continue a previous unit's journal from a new card.
3. **The handoff is still the last thing written** — but by then the evidence is already on disk.
4. `status` and `resume` are read-only, always.

## Verifying the protocol holds

```bash
python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_unit_journal.py' -v
```

Four cases, all in temp dirs: (a) a unit logs header + 3 artifacts + 1 evidence + a `next`, the process
is `SIGKILL`ed before any handoff, and `status`/`resume` reconstruct the run — distinguishing the two
artifacts that exist from the one deliberately missing; (b) a torn final line still yields a usable
`resume` and exit 0; (c) `status` exits non-zero only for a missing artifact and names it; (d)
append-only — a second `log` leaves the first line byte-identical, `init` refuses to rewrite, and the
source contains no rewrite path.
