# UNSTAMPED-104 — census the failed column

**Purpose.** Partition all 104 currently-failed cards from their verdict rows alone, and say
how many are actually unfinished work. **Offline**: zero inference requests, no test/cell/pipeline
command run, no card or row edited.

**Bound.** 28 tool calls. **Writes.** `experiments/ptr-engine/measure/UNSTAMPED-CENSUS.json`,
`docs/UNSTAMPED.md`, `experiments/ptr-engine/tools/unstamped_audit.py`,
`experiments/ptr-engine/longrun/tests/test_unstamped_audit.py`, this card, its handoff and journal.

**Result.** Of the 104 failed cards, 97 are unfinished work: 96 never had a verdict row at all and 1 has a row that refused before measuring. 5 were redone and settled by a later card. 2 carry a measuring row — and both of those rows exit 0, so the column holds no measured failure of anyone's artefact.

| class | n |
|---|---|
| `never_had_a_row` | 96 |
| `superseded_or_duplicate` | 5 |
| `unstamped_refusal` | 1 |
| `verified_fail` | 2 |

**Method.** Rows read from the Host closure store (`taskId:executionId` -> `verdictRow`); classification
from `verdict_semantics.is_refusal`, never a copied table. Journals cross-checked for a verdict event
on every one of the 101 row-less cards: none exists, so absence is real and not a lost write. The five
`superseded_or_duplicate` rows each name a successor verified `done` in the ledger.

**Known limit.** Exit 124 is not in `exit_codes.EXIT_TABLE`; it is recorded as a refusal with
`gate: "unclassified-exit-124"` and named as a gap rather than classified by guess.
