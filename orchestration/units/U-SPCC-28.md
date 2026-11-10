# U-SPCC-28 — three result memos stop asserting the untested position claim

## Target
Only these three files:
`experiments/ptr-engine/research-seed-concepts/RESULTS-TX02-CELL1.md`,
`experiments/ptr-engine/research-seed-concepts/RESULTS-TX03-CELL1.md`,
`experiments/ptr-engine/research-seed-concepts/RESULTS-STACK-8014.md`.

## Change
1. Each superseded "presence, not position" wording replaced by: the failures are **content
   absence** — the mask deletes the fact at `intro+4`, before any probe deeper than `d2` is
   asked — so **position is untested on this arm**, plus the explicit clause that this run
   cannot test position because the value is absent from the prompt. Each memo now names
   `FINDINGS-LEDGER.md` `### The TX-03 cliff is content absence; position is untested here`
   as the record.
2. Both dead section citations retargeted to §The TX-03 cliff is content absence; position is
   untested here (the heading no longer exists in its old form; the ledger's own line 24 now
   reads `### The TX-03 cliff is content absence; position is untested here`).
3. Measured numbers untouched: TX-02 12/12 at `d=2` then 0/12 at `d=8/20/32`; TX-03 8/8 per
   rep, 16/16 pooled, 0/8 at every `d≥5`; STACK-8014 its own `:8014` numbers, not merged with
   `:8012`.

## Evidence
- `grep -n "presence, not position\|position is excluded" <the three files>` → no hits, exit 1.
- `grep -c "§The TX-03 cliff is content absence; position is untested here"` → 1 each for
  `RESULTS-TX03-CELL1.md` and `RESULTS-STACK-8014.md`.
- `git diff --stat` → only the three files.
- `python3 tools/doc_check.py` → `OK docs clean`, exit 0.

## Status
complete
