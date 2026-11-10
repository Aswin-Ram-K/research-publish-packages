# U-SPCC-71 — record the 6/48 gap as answer-slot binding in the ledger

**Status:** DONE. Documentation only. Zero requests spent; no rows, fixture, manifest, code,
prompt or prereg file touched.

## Why

`U-SPCC-67` (commit `dcc9b65`) explained the 6/48 masking-vs-spcc gap in the E3 cell but
wrote only its card and handoff — no ledger row. The finding is a real result and belongs in
`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md`, with the exclusion rule
that keeps it out of any retention comparison.

## What was written

- **Ledger row** (7 columns, matching the main findings table): the gap is answer-slot
  binding, a transcript-replay artefact, not a retention difference; `prompt_sha256` matched
  200/200; masking T30 158 lines / 1,611 prompt tokens vs spcc 69 lines / 1,465
  (`layer_tokens` L0=80 L1=20 L2=215 L3=21 L4=2); 5 delivery turns, delivered document ≠
  asked document in 5/5, masking answers with the delivered body's value on 4/5, spcc 0/5;
  control `masked_rows` 0, `compactions` 0, `evicted` 0 on all 200 rows, `expected_present`
  96/96 true. Status `RECORDED`, carrying the exclusion rule.
- **Subsection** `### The 6/48 gap is answer-slot binding` under the E3 material: the
  reconstruction method, the structural diff, the mechanism, the quoted masking T31 block
  (lines 152-158), the 4-of-5 / 0-of-5 delivery table, the two refuted rivals (proximity,
  document anchoring), the T12 answer-replay pass, the two within-document failures, the
  verdict (intrinsic to a transcript replay that replays answers) and the consequence.
- **`docs/STATE.md`** — the finding and the exclusion rule in the E3 section; header
  attribution moved to U-SPCC-71.
- **`journal/2026-11-10.md`** — the same finding and exclusion rule in the E3 entry.
- **`orchestration/STATUS.md`** — the same finding and exclusion rule in the E3 section.

## The finding, in one paragraph

The masking arm replays an `ANSWER (Tt):` line after every turn's tool-output block; the
spcc journal replays no answers at all. The transcript therefore teaches a positional rule —
the answer slot takes its value from the block immediately above it — because that is the
shape of all 29 prior turn blocks. On a checkpoint turn the fixture delivers a body for a
*different* document, and that body is the block immediately above the answer slot. Five
checkpoint turns deliver a body; in all five the delivered document differs from the asked
one; the masking arm answers with the delivered body's value on 4 of 5, spcc on 0 of 5.
Proximity is refuted (at T30 both arms have the answered value closer to the question than
the expected one, and spcc answers correctly) and document anchoring is refuted (the masking
arm prints `TOOL_OUTPUT (doc-fact-07@1): # doc-fact-07` and the model ignores it).

## Exclusion rule

**The 6/48 gap is a format artefact and must be excluded from any retention comparison.**
At this cell neither arm loses information (`masked_rows` 0, `compactions` 0, `evicted` 0 on
all 200 rows; `expected_present` true on 96/96 with `expected_present_source =
prompt-digit-boundary`). The cell is a format control, not a retention measurement. Pooling
this 12.5 pp with the distance cliff would attribute a prompt-format artefact to memory.

## Artifacts

- `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md`
- `docs/STATE.md`
- `journal/2026-11-10.md`
- `orchestration/STATUS.md`
- `orchestration/units/U-SPCC-71.md`
- `orchestration/handoffs/U-SPCC-71.json`

`python3 tools/doc_check.py` exits 0.
