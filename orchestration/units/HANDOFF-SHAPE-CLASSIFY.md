# Unit HANDOFF-SHAPE-CLASSIFY

Card: fix the classifier that makes `tests/test_orchestration_handoffs.py::test_no_new_contract_key_gaps`
permanently red, without weakening the guard. Offline, zero inference requests. Bound: 24 tool calls.

## Why it was red (measured, at HEAD `f17663d1`)

`1 failed, 12 passed`, failure naming **13** handoffs as "new verifier-shape gaps". Measured per file:
**all 13 carry the complete 7-key unit contract and declare `status`** — this was never a missing-key
defect. 12 are `V`-named; the 13th (`RECORD-REFRESH.json`) was judged a verdict only because it
self-reports `overall: PASS`. The defect was `classify()`'s ORDER: `name.startswith("V") or "overall" in doc`
ran before any measurement of the unit key set, so a name overrode the document's own keys. The
`HANDOFF-BASELINE-REGEN` hint's proposed rule (V-prefix + unit key set + no verdict key → unit) explains
**8 of 13**, not all: it leaves `RECORD-REFRESH.json`, `VERDICT-DISPUTE.json`,
`VERDICT-REFUSAL-SEMANTICS.json` (unit key set **and** `overall`) plus `V3-PILOT.json` /
`VERDICT-ADOPTION.json` (unit key set **and** `verdict`) still mis-shaped. The rule that explains all 13 is
precedence by **document completeness**, not by name:

```
unit      iff  all 7 CONTRACT keys are present
verifier  iff  otherwise and (name starts with "V" or "overall" in doc)
unit      otherwise                                        # the loud fallback
```

## Why that is not a weakening

The rescue to the unit shape only happens when every key the unit shape requires is already present, so it
can forgive nothing. Drop one unit key and the document falls through to the verdict test and is reported.

## Deliverables

- `classify()` rewritten with the rule and the reasoning in its docstring (module docstring's shape section
  updated to match).
- `test_no_baseline_entry_over_declares` now measures each exemption against the **document** and the
  exemption's own contract, not against `{gaps of that shape}`; a document that changed SHAPE used to look
  "repaired" and now is not reported as one.
- `tests/test_handoff_shape_classify.py` — 8 tests: V-prefixed unit shape → unit; verdict shape → verifier;
  ambiguous → unit *and* cannot smuggle a missing key; empty/unrecognised → unit (loud, 7 gaps); the
  no-forgiveness invariant measured on the live corpus.
- `docs/HANDOFF-SHAPE.md` — rule, the 13-row table, the residual (`checks` not required of an ambiguous
  document), and the sentinel sentence.
- **No baseline entry added.** Both frozen baselines are byte-identical to HEAD
  (`verifier_shape_baseline.json` sha256 `5f8bbd35…`, `baseline_gaps.json` sha256 `d25e5bcc…` — the same
  values pinned in the test).

## Proofs (scratch copy; the live tree was never used for the red cases)

| case | result |
|---|---|
| corpus as-is + fix, no baseline edit | `13 passed`, exit 0 |
| 14th handoff, complete unit shape, `V`-named | `13 passed`, exit 0 |
| 14th handoff, one unit key short | `1 failed`, exit 1, names `V-NEW-GAP.json` |
| verdict-shaped, missing `next_unit_hint` | `1 failed`, exit 1, names `V-RED-VERDICT.json` |
| classifier reverted to prefix-first | `1 failed`, exit 1 |

## Assumption recorded

The card asked for the `/tmp` copy. `/tmp` here is a per-invocation private mount (a directory created in
one call is gone in the next), so a leaked fixture briefly landed in the real corpus and was removed in the
following call. Red proofs were therefore run in one self-contained call inside
`scratch/handoff-shape-red/`, removed at the end of that call; nothing outside the declared write paths
persists.

## Test-file shas

before `9071255ea29e071c3e6cc454430e8ad9b2989f7dc4f1d8b6d72c082d37adb065`
after  `918f4af9e9b71b2acf9d24aa64e81375775abe29c2620683f1cff2b9c8072752`
