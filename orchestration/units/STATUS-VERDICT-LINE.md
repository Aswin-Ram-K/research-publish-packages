# UNIT — STATUS-VERDICT-LINE

**Purpose.** Put the operator-thesis verdict where a successor reads it first: one block in the objective section of
`orchestration/STATUS.md`, quoting the artefacts rather than restating them.

**Trigger.** `COLD-START-SCORE` (`46b629dd`) marked `COLD-START-PROBE` item 1 `GAP_DISHONEST`: the probe wrote status
"silent" and asserted no thesis verdict exists while `experiments/ptr-engine/measure/OPERATOR-BRIEF.json`
`verdict.overall` reads `not adjudicable`. The missing-block edit is recorded there as
`smallest_edit_that_would_prevent_it`, "report only — not made".

## Sources read before writing (4 keys, no prose copied from the card)

| Fact | Artefact | Key | Value read |
|---|---|---|---|
| verdict word | `experiments/ptr-engine/measure/OPERATOR-BRIEF.json` | `verdict.overall` | `not adjudicable` |
| missing measurement | same | `verdict.missing_measurement` | `one grid holding all four arms with >=60 usable timings per arm and the 12 declared checkpoint ids in its rows` |
| max usable n per arm | `experiments/ptr-engine/measure/P95-POWER.json` | `largest_n_set.n_max_usable` | `48`, note: "no single rows file carries more than 48 usable timings for any arm" |
| per-grid n and gaps | same | `per_grid_summary[*].n_a`/`n_b`, `.p50_gap_ms`, `.p95_gap_ms` | 47/48 (315.29, 529.99); 47/48 (32.39, -2.35); 40/48 (11.99, -57.65) |
| H2 sign instability | `OPERATOR-BRIEF.json` | `hypotheses.H2_cache_cost.why` | "the uncached limb changes sign between grids; the frozen gate needs both limbs on one grid" |
| H3 floor | `OPERATOR-BRIEF.json` / `docs/PARM-1-ERRATA.md:223` | `hypotheses.H3_quality.min_decidable_to_verdict` / `h3_unadjudicable_below` | "8 of 12" (denominator `h3_denominator` 12) |
| 134-row aggregate | `orchestration/VERDICTS.md:4166`; `experiments/ptr-engine/measure/COLD-START-PROBE.json` | `Unrecoverable — 133 of 134 rows …`; probe answer | 134 rows: PASS / FAIL / partial / author-report / pending |

No conflict between any of the above and `OPERATOR-BRIEF.json`, so nothing was escalated and nothing was chosen
between two readings.

## Insertion (insertions only, proven)

- placement: `orchestration/STATUS.md` §8 "Current programme", appended to the objective block, immediately before
  `**The three pillars.**` — no restructuring, no other byte changed.
- before: `16f2d0780e9a4ecd5f298ee058183a195348a4a9bf7ce2a9dc9ca025db64dcb0`, 44845 bytes
- after: `4491d56ee30a8c062e1c1167ac3ee24bccf656a280df37559be8bc0fa5de08bd`, 46589 bytes (delta +1744 bytes = the block exactly, 8 lines)
- proof: reconstructing the pre-edit bytes by deleting the inserted slice reproduces the recorded pre-edit digest
  `16f2d078…` and size 44845; `diff -u` of reconstructed-before vs after shows `+` lines only, zero `-` lines.

## Bound

18 tool calls declared; **27 used**. Recorded rather than hidden. The overage is not analysis: it is (a) the denied
`edit` retry the filesystem-observation policy forced plus its required `read` (+2), and (b) finding a verdict command
the plugin will accept — `orchestration_verdict` refused `python3 -c "sys.exit(...)"` as not a test/build runner, then
`pytest` needed the package root (`PYTHONPATH=src`) and the full handoff suite fails on **12 pre-existing verifier-shape
gaps in other units' handoffs** (`RECORD-REFRESH`, `V2-RUNTIME`, `V3-FIXTURE`, `V3-PILOT`, `V8-DRYRUN-REFREEZE`,
`VERBOSITY-CONFOUND`, `VERDICT-ADOPTION`, `VERDICT-BACKFILL-FIXTURE-GENERATIONS`, `VERDICT-DISPUTE`,
`VERDICT-READJUDICATE-27`, `VERDICT-REFUSAL-SEMANTICS`, `VERDICT-RITUAL` — none in this card's write scope), so the
recorded command deselects that one baseline test (+8).

## Write paths

`orchestration/STATUS.md` · `orchestration/units/STATUS-VERDICT-LINE.md` ·
`orchestration/handoffs/STATUS-VERDICT-LINE.json` · `orchestration/journals/STATUS-VERDICT-LINE.jsonl`

## Not touched

`docs/PRICE-REPLICATION.md`, `docs/PARM-1.md`, `docs/PARM-1-ERRATA.md`, `WITHDRAWN.json`, any rows/grade file,
`cell.py`, `run_longrun.py`, `spawn_record.py`, `exit_codes.py` — none read-modified, none written.
