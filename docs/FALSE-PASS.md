# False-pass register

Register of handoffs whose `status`/`overall` says **done** or **pass** while carrying none of
the six contracted substance keys (`evidence`, `checks`, `measurements`, `findings`, `commands`,
`command_or_count`). Source of the flag: `E_STATUS_WORD_CONTRADICTION` in
[`handoff_lint.py`](../experiments/ptr-engine/tools/handoff_lint.py), which
[`HANDOFF-PARTIAL-SUBSTANCE`](../orchestration/handoffs/HANDOFF-PARTIAL-SUBSTANCE.json) reported at
3 records and baselined as pre-existing.

Machine-readable copy: [`experiments/ptr-engine/measure/FALSE-PASS.json`](../experiments/ptr-engine/measure/FALSE-PASS.json).
Check it with `python3 experiments/ptr-engine/tools/false_pass_audit.py --check` (exit 0 = every
flagged record registered and every recorded `sha256` still matches the file on disk; exit 1 names
the record that drifted or the new flagged record not yet registered).

**This is a register, not a correction.** No handoff, ledger, or verdict row was edited to produce it.

## The three flagged records

| record | status word | missing substance keys | classification | substance that does the work |
|---|---|---|---|---|
| [`R2-A3`](../orchestration/handoffs/R2-A3.json) | done | all six | `substantive_elsewhere` | `max_mamba_cache_size_semantics.verdict` + three verbatim primary quotes; `eviction_policies.*.when_to_use_verbatim`; `corrections_downstream` refutes R2-A2's concurrency inference |
| [`R2-B2`](../orchestration/handoffs/R2-B2.json) | done | all six | `substantive_elsewhere` | `support_evidence`: 8 claims, each a verbatim quote with a URL and line anchor; `state_cache_sizing.answer` gives the slot/ratio mechanism with allocator quotes; `supported` scopes itself to upstream `main` |
| [`R2-C`](../orchestration/handoffs/R2-C.json) | done | all six | `substantive_elsewhere` | `method` pins tag `v0.27.1` and the reproduction route; `options[0].quote` is the `vllm/config/cache.py#L56-L67` text; `version_pins` records the opt-in-prefix-caching pitfall with its code anchor |

Totals: **3 flagged, 3 substantive_elsewhere, 0 false_pass, 0 stub, 0 superseded.**

All three are read-only web-research units. Their shape is a research dossier: keys name *what was
found* (`eviction_policies`, `flags`, `block_size_resolution`, `top3`) rather than the contract's
bookkeeping keys. Each carries re-fetchable verbatim quotes with URLs — a reader can check the claim
without trusting the unit. That is judgeable substance under another key, so the correct reading of
the lint hit is a **shape gap**, not a false claim. `HANDOFF-PARTIAL-SUBSTANCE` reached the same
conclusion for two of the four cards that prompted its rule.

**Offline limit, recorded:** this unit made zero network requests, so no quote was re-fetched from
its URL. The classification rests on the *presence of quotable, URL-addressable, mechanism-bearing
evidence* — which is what distinguishes these records from a bare status word — not on re-verifying
each quote. A quote level re-check is a separate unit's job.

## What a `false_pass` classification means for a count of "delivered" cards

A `false_pass` is a handoff that asserts a success word and has neither substance under any of the
six keys nor an artefact on disk that supports the claim. **Such a card was never delivered, so any
count of delivered cards must exclude it** — counting it counts an empty assertion as work, and
every downstream total (batch velocity, completion rate, "N cards done this week") inherits that
error silently, because the handoff parses as valid JSON and the board shows the card as `done`.
The register exists so that exclusion is measured rather than remembered: a card leaves the
delivered population only through an entry whose `sha256` was taken *after* the handoff stopped
changing, and a handoff edited afterwards fails `--check` rather than quietly re-entering the count.

For this batch the exclusion is empty — none of the three flagged records is a `false_pass` — but the
same rule applies forward: a `false_pass` stays excluded until a later card redoes the work and a
verdict row records it, at which point the register entry is annotated `superseded`, never deleted.
