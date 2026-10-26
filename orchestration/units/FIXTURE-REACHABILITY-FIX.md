# Unit card — FIXTURE-REACHABILITY-FIX

**Bound:** max 24 tool calls, zero inference requests, no live run. **Result:** done, 20 calls,
`requests_sent: 0`, verdict `RESOLVABLE-NOT-PRELOADED`.

## Purpose

PLANT-REACHABILITY measured LR-01's CP1 and CP2 **unanswerable in both arms** and CP3 truncated:
`resolve.py#L66-L110` carried no `DEFAULT_MAX_REFS` (L39) and `errors.py#L114-L126` ended
mid-declaration with 3 of 31 `Ptr*` classes. Repair the fixture (not the arms), then prove the
repair with the same materialiser, without a single request.

## What was established

| CP | requires | v3 defect |
|---|---|---|
| 1 (`64`) | `resolve.py:39` `DEFAULT_MAX_REFS = 64` | slice starts at L66 |
| 2 (`31`) | all 31 `^class Ptr` in `errors.py` L15–L250 | slice L114–L126 = 3 declarations (20 classes exist only up to L142) |
| 3 (phrase) | `_refuse` body + "before re-raising" at L66–L71 | present, but the surrounding slice reads as truncated |

## Delivered

* `longrun/tasks-v4/LR-01.v4.json` — authored v4 (`v4-slice-widened`): `resolve.py` `#L36-L110`,
  `errors.py` `#L15-L250`, CP2 question re-cited to the range that actually holds the count.
  Everything else byte-identical: answer marker, 150/400 budgets, turn plan, repair trap,
  negative constraints, 3 expected values, 12 `checks_structured` ids.
* `longrun/adapt_v4.py` — imports `adapt_v3.adapt_v2`, refuses a non-v4 `fixture_version`,
  stamps v4 provenance + the slice delta, writes `tasks-v4/runtime-v4/`.
* `longrun/tasks-v4/runtime-v4/LR-01.v4.json` — `sha256:5a5f8c4be2027c53…`.
* `longrun/controls/v4/pos-full.v4.jsonl` + `.grade-v4.json` — control rows byte-identical to
  v3 (no check moved); `grade_v3.py` exit 0, `verified=True acc=3/3`.
* `measure/REACHABILITY-V4.md` — before/after matrix, grep counts, commands.

## Why not ALL-SIX-REACHABLE

`31` is a **count**; the numeral appears nowhere in `errors.py`. After the widening every one of
the 31 declarations is in the materialised body (set-equal to the file), so the count is
derivable in both arms — but a digit-bound literal test cannot go green without editing the
pinned corpus (forbidden) or inlining the answer (`RECALL-NOT-RETRIEVAL`). Recorded as
`resolvable-not-preloaded`, not claimed as preloaded.

## Verification performed

1. `adapt_v4.py --all` — 4 sources digest-verified, 12 checks, 3 checkpoints, exit 0.
2. `prompt_at_turn.py` on `runtime-v4`, both arms × T12/T24/T46 — exit 0, `no_http_proof ok`,
   `network_attempts=[]`, `requests_sent=0`.
3. Probe: every v4 prompt contains the `errors.py` body with 31 `^class Ptr`, literal `64` ×1,
   `ledger.record_refusal(` and `before re-raising`.
4. `grade_v3.py` untouched, re-run on the v4 fixture — `verified=True acc=3/3`.

## Constraints respected

Wrote only `tasks-v4/**`, `adapt_v4.py`, `controls/v4/**`, `measure/REACHABILITY-V4.md`,
`/tmp/**`, this card and the handoff. Did not edit `run_longrun.py`, `score_longrun.py`,
`grade_v2.py`, `grade_v3.py`, `adapt_v3.py`, `tasks-v3/**`, `fixtures/` or `runtime/`; no corpus
file touched; no plan/row file touched; no request and no live run.
