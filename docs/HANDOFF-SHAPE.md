# Handoff shape: how `classify()` decides, and why

Owner of the rule: `classify()` in [`tests/test_orchestration_handoffs.py`](../tests/test_orchestration_handoffs.py)
(`#L193`), decided by unit `HANDOFF-SHAPE-CLASSIFY` on 2026-10-26 at HEAD `f17663d1`.

## The rule

1. **A document that carries the complete 7-key unit contract is a UNIT handoff** — whatever its
   filename, and whatever extra keys it carries. Those seven keys (`unit`, `status`, `artifacts`,
   `evidence`, `blocker`, `next_unit_hint`, `write_paths`) are the *specification* of the unit report
   (AGENTS.md unit-contract rule 5), not a measurement of one. A document carrying all of them has no
   unit-shape gap for a classifier to forgive, which is the whole reason this precedence is safe.
2. **Otherwise**, a `V` filename prefix **or** an `overall` key makes it a **VERIFIER verdict**, judged
   against the verifier contract recorded in `state/logs/U8.18/verifier_shape_baseline.json`.
3. **Otherwise** it is a unit handoff. There is no third "other" bucket: an unrecognisable document owes
   all 7 unit keys, so it is reported with 7 gaps rather than waved through.

The `V` prefix is a **naming convention** — a name a human chose — and **not** a shape measurement.
`verdict` is deliberately *not* a trigger: it appears as an incidental field in real unit reports
(`V3-PILOT.json`, `VERDICT-ADOPTION.json` carry it beside `status`).

## Ambiguity: unit key set **and** `overall` → **unit**

The code goes to **unit**, deliberately, and the reason is not convenience: the rescue can forgive
nothing, because it only happens when all 7 unit keys are already present. Drop one unit key and the
document falls through to the verdict test and is reported (proved by
`test_ambiguous_shape_cannot_smuggle_a_missing_key`).

**Recorded residual, not hidden:** such a document is not asked for `checks`, a verifier-contract key.
That is correct for a unit report that also self-reports a verdict (`RECORD-REFRESH.json` is literally
`{"status":"done","overall":"PASS", ...all 7 unit keys...}`), and it is stated here so a later reader can
disagree with reasons.

## The 13 documents the old classifier mis-shaped

At HEAD `f17663d1` the guard reported `1 failed, 12 passed` and named 13 handoffs as *new verifier-shape
gaps*. The prefix test ran first, so a `V`-named document was judged a verdict even when it carried the
full unit contract. Measured state of each, before and after the fix:

| # | file | `V` prefix | unit keys | `overall` | `verdict` | old shape | old gaps | new shape | new gaps |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `RECORD-REFRESH.json` | no | 7/7 | yes | — | verifier | `checks` | unit | — |
| 2 | `V2-RUNTIME.json` | yes | 7/7 | — | — | verifier | `overall`,`checks` | unit | — |
| 3 | `V3-FIXTURE.json` | yes | 7/7 | — | — | verifier | `overall`,`checks` | unit | — |
| 4 | `V3-PILOT.json` | yes | 7/7 | — | yes | verifier | `overall`,`checks` | unit | — |
| 5 | `V8-DRYRUN-REFREEZE.json` | yes | 7/7 | — | — | verifier | `overall`,`checks` | unit | — |
| 6 | `VERBOSITY-CONFOUND.json` | yes | 7/7 | — | — | verifier | `overall`,`checks` | unit | — |
| 7 | `VERDICT-ADOPTION.json` | yes | 7/7 | — | yes | verifier | `overall`,`checks` | unit | — |
| 8 | `VERDICT-ALLOWLIST-WRAP.json` | yes | 7/7 | — | — | verifier | `overall`,`checks` | unit | — |
| 9 | `VERDICT-BACKFILL-FIXTURE-GENERATIONS.json` | yes | 7/7 | — | — | verifier | `overall`,`checks` | unit | — |
| 10 | `VERDICT-DISPUTE.json` | yes | 7/7 | yes | — | verifier | `checks` | unit | — |
| 11 | `VERDICT-READJUDICATE-27.json` | yes | 7/7 | — | — | verifier | `overall`,`checks` | unit | — |
| 12 | `VERDICT-REFUSAL-SEMANTICS.json` | yes | 7/7 | yes | — | verifier | `checks` | unit | — |
| 13 | `VERDICT-RITUAL.json` | yes | 7/7 | — | — | verifier | `overall`,`checks` | unit | — |

Every one carries all 7 unit keys and declares `status`: this was never a missing-key defect, it was a
mis-shaped document. 12 of 13 were `V`-named; #1 was read as a verdict only because it self-reports
`overall`.

**A baseline entry records a defect as expected; a classifier that mis-shapes a document invents one.**

So the fix is in the classifier, and **no baseline entry was added** — `state/logs/U8.18/verifier_shape_baseline.json`
and `state/logs/U8.15/baseline_gaps.json` are byte-identical to HEAD, and their sha256 pins are unchanged.

## Companion change: what "over-declares" now measures

`test_no_baseline_entry_over_declares` used to compare each exemption against `{gaps of that shape}`, so a
document that changed **shape** fell out of the live set and its exemption looked "repaired" although
nothing was repaired. It now measures the **document** against the exemption's own contract: "how many of
the keys this exemption forgives does the document *still* lack?" Identical verdict for a same-shape repair
(so it still bites), and no longer a false positive for a shape move. Only two entries are affected:
`V-R2VLLM-TRIAGE.json` and `VLLM-CELL.json`, both of which still lack `overall`+`checks` — their verifier
exemptions are unreachable, not satisfied, and if either regains the verdict shape *and* those keys the
check fires.

## What is still guarded

The purpose survives and is measured, not asserted:

| case | result |
|---|---|
| corpus as-is, classifier fix, **no baseline edit** | `13 passed`, exit 0 |
| + a 14th handoff, complete unit shape, `V`-named | `13 passed`, exit 0 (shape, not a name blacklist) |
| + a 14th handoff, same shape, one unit key short | `1 failed`, exit 1, names `V-NEW-GAP.json` |
| + a genuinely verdict-shaped handoff missing `next_unit_hint` | `1 failed`, exit 1, names `V-RED-VERDICT.json` |
| classifier reverted to prefix-first | `1 failed`, exit 1 (the 13 return) |

Proofs run in a scratch copy of `tests/`, `state/logs/U8.15`, `state/logs/U8.18` and
`orchestration/handoffs`; the live tree and both frozen baselines were never written.

---

# The shape DECISION for the three ambiguous documents (2026-10-26)

Appended by unit `HANDOFF-SHAPE-DECISION`, on the evidence of verifier `V-HANDOFF-SHAPE`
(`orchestration/handoffs/V-HANDOFF-SHAPE.json`, `overall: fail`). **This section records a decision; it
does not re-classify and it does not loosen anything.** The classifier above is unchanged: `if all(k in
doc for k in CONTRACT): return "unit"` still runs before the `V`-prefix / `overall` test, because the 11
of 13 false positives that narrowing removed were real and reverting would re-red the guard for documents
that are genuinely unit handoffs.

## Why a `fail` was owed on a green guard

The verifier's sentence that produced the verdict, quoted:

> with that rule a document that is **verifier-shaped by role** but carries the 7 unit keys is judged as a
> unit handoff, so a genuinely missing `checks` is **silently forgiven** — proven with a fresh fixture that
> passes.

A green suite that cannot see a missing required key is the defect, not a reassurance. Its per-document
findings, quoted: `RECORD-REFRESH.json` = *"unit handoff, false positive, no material gap"*;
`VERDICT-DISPUTE.json` = *"ambiguous — verdict by role (`overall: fail`, adjudicates `V-GATE-CHAIN-3`),
unit by shape"*; `VERDICT-REFUSAL-SEMANTICS.json` = *"ambiguous — verdict by role (`overall: PASS`,
triage/reopen), unit by shape"*.

## The decision table

| file | role decided | reason | recorded gap | baseline entry |
|---|---|---|---|---|
| `VERDICT-DISPUTE.json` | **verdict** | its job was to adjudicate another card's PASS; `overall: fail` is a judgement, not a self-report | **yes** — `['checks']` | `state/logs/U8.18/verifier_shape_baseline.json` |
| `VERDICT-REFUSAL-SEMANTICS.json` | **verdict** | triage and reopening of two cards; `overall: PASS` is a judgement | **yes** — `['checks']` | same file |
| `RECORD-REFRESH.json` | **unit** | its `overall: PASS` is a self-report of its own insertion work; `checks` was never its key | no — no gap exists | **none**, deliberately |

Both verdict-role documents carry the substance `checks` would hold under `evidence.commands`. Role is
decided by the document's **job**, never by its key set — that is exactly what the classifier cannot see.

## The recorded gap is a visible second edit

The two entries were added to `state/logs/U8.18/verifier_shape_baseline.json` (no other entry changed, no
handoff edited) and the pin in `tests/test_orchestration_handoffs.py` was updated in **exactly one place**:

- baseline before `5f8bbd35…`, after `c692935180293684401dd40ec19801eaebcd33435ea29973fa5fdf952343b780`
- baseline diff: two new `gaps` entries, each `["checks"]`, plus a `decided_by` note; nothing removed
- `tests/test_orchestration_handoffs.py` after the whole unit:
  sha256 `ff1b22f189bb79f990f128e2d0bf436231905e6b84a3c4fe67bd43858fb26bc4`

The baseline schema can express this exactly: `gaps` is `{handoff name: [missing keys]}`, so no per-document
missing-key list had to be approximated and no unrelated pin needed re-freezing.

`test_no_baseline_entry_over_declares` measures each entry against the document itself, so these two entries
are reachable: they fire the moment either document gains `checks` (a repaired gap must not stay exempt).

## The ambiguity is now visible on every run

`_ambiguity_report()` in the guard prints — and warns, which is what makes it visible under `-q` — every
handoff carrying **both** `overall` and the full 7-key unit contract, with its missing verifier keys and its
recorded role. A document with no recorded decision prints `role=UNDECIDED`. It is a **REPORT, not an
assertion**: a new both-shape document is a decision to be recorded, and failing the suite for it would be
the pressure that produces a looser classifier. Measured on this corpus (2026-10-26): **10** documents carry
both shapes — the three above, plus `U10.json`, `V-INSTRUMENTS.json`, `V-SPAWN-ATTACK-2.json`,
`V-XSTACK.json`, `V2W.json`, `V5.32.json`, `VERIFY-CLASSIFIER-FIX.json`, each of which carries the *complete*
verifier contract too (`missing=none`), so the ambiguity costs them nothing.

## The rule, as it now stands, in one sentence

A document carrying all 7 unit keys is a unit handoff whatever its name and whatever it also carries;
a document without them is a verifier verdict if it is `V`-named or carries `overall`; and any verdict-ROLE
document that the shape test therefore never asks for `checks` is named as a recorded gap in the pinned
baseline and printed in every run.

**A recorded gap is a defect that is expected and visible; a loosened classifier is a defect that is none of
those.**
