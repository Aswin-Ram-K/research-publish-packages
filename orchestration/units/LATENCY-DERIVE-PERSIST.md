# LATENCY-DERIVE-PERSIST — persist the measured latency verdict to state/latency-derive.json

*Card type:* executable, `automated`, `workspace-write`. No human present: **no `ask_user_question`**.
*Follows:* `LATENCY-DERIVE2` (status `partial`, handoff complete but its verdict never written to
`state/latency-derive.json`).

## 1. Objective

The previous unit measured and reported a latency verdict but never persisted it: `state/` existed with no
`latency-derive.json`, and no script, test or document referenced the path, so there was no schema to
inherit. This unit writes that file — the verdict as measured, with the numbers traced back to the rows.

One deliverable, one file. This unit does not re-run the measurement and does not re-run any request.

## 2. Hard bound and kill condition

- **Tool-call bound: 40.** Stop condition: if a figure cannot be traced to the row data in one independent
  re-read, record it as inherited-and-unverified rather than presenting it as re-derived.
- **0 live requests. No `.occamy.lock`. No server start or stop. No target-repo access.**
- **Do not edit `state/logs/LATENCY-DERIVE2/*`.** The prior unit's artefacts are evidence, not scratch space;
  where this unit disagrees with them, both values are recorded in the state file with the traced cause.

## 3. Declared write paths

```
state/latency-derive.json                       (the verdict — the deliverable)
orchestration/units/LATENCY-DERIVE-PERSIST.md   (this card)
orchestration/handoffs/LATENCY-DERIVE-PERSIST.json (handoff)
```

Nothing else is written. `experiments/`, `papers/`, `src/`, `state/logs/` and every target repo untouched.

## 4. What went in, and in what order

1. Read the two prior handoffs (`LATENCY-DERIVE`, `LATENCY-DERIVE2`) and the DERIVE2 report, summary and run log.
2. **Re-derived D1 and D5 independently** with a separate streaming reader before writing anything. This step
   was not in the card and is the reason the file is trustworthy: the independent totals disagreed with
   `summary.json` by 709,114.3 ms of wall time.
3. Traced the disagreement to `state/logs/LATENCY-DERIVE2/derive_latency.py:213-219`, which sums D1/D2 over
   `if c["spans_ms"]` — cells carrying a parseable `ts_utc` — while `rows_with_ttft_and_wall` counts every
   cell. U3 (192 rows), U6 (240 rows) and CROSS-HTTP (3 rows) were silently excluded.
4. Persisted **both** the corrected figures and the previously published ones side by side, with the cause,
   so the change is auditable rather than silently overwritten.
5. Re-confirmed containment after the write.

## 5. Deliverable shape

`state/latency-derive.json` carries: `verdict` (partial, 5 derivable / 6 refused, 0 requests), `source`
(field-by-field coverage), `derivable` D1–D5 (corrected values, published values, correction, caveat),
`refused` R1–R6 (each naming its missing field), `cross_checks_against_published_claims`, `containment`,
`reproduce`, `guard` (with its known gap), `open_items` and `not_claimed`.

## 6. What this unit is NOT allowed to claim

- No queue factor, no decode rate, no network latency, no harness queue delay — all six are refused with
  the missing field named.
- `wall_ms − ttft_ms` is never called "decode time".
- No live number is quoted as measured here: this unit made **0 requests**.
- The corrected D1/D2 values are arithmetic over existing rows, not a new measurement of the server.
- The T3 red→green is **inherited** from the prior handoff and labelled as such; it was not re-executed.

## 7. Gate

A verifier (`V-LATENCY-DERIVE2`, a different agent) must re-derive D1 and D5 independently against the
corrected figures in this file, force the T3 red, and confirm containment (lock mtime
`2026-10-21 16:18:54 -0500`, 10161 lines, md5-of-md5sums `6c988ecb87913e4f7c038fed6d5a49e2`). A second,
separate card should correct the derivation script itself — this unit deliberately left it untouched.
