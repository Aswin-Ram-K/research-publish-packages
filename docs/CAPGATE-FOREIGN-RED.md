# CAPGATE-FOREIGN-RED — the stale assertion that charged other cards

**Verdict: done.** The test was wrong; the writer is right.

## Which side was wrong

`experiments/ptr-engine/longrun/tests/test_cap_gate.py:205` asserted `'tool-followup' in [r["kind"] for r in allowed["rows"]]`.
Since `TURN-ROW-ATTRIBUTION` the row model is **one row per send**:

- `run_longrun.py:2462-2468` — `attributed = bool(followup_rows) and attribute_initial_send()`;
  `row_extra["row_measurement_source"] = ("tool-followup" if followup_rows else "turn-initial")`.
  The turn row *is* the last follow-up's row.
- `run_longrun.py:2504-2517` — with attribution the turn's own request is written as its own
  `kind="turn-initial"` row (`send_index=0`, `initial_send=True`).
- `run_longrun.py:2518-2520` — `for frow in (followup_rows[:-1] if attributed else followup_rows)`:
  follow-ups `1..k-1` get their own `tool-followup` rows. With k=1 there are none, so the row
  kinds are exactly `['turn-initial', 'turn']`.

The contract is `experiments/ptr-engine/longrun/tests/test_row_attribution.py:222-231`: distinct `request_sha256` per turn ==
sends, distinct `ttft_ms` per send, and *no two rows may carry the same request identity*. The
old assertion expected the follow-up to be written **twice** (once as `tool-followup`, once
mirrored by the turn row) — the exact defect the attribution fix removed.

## Old assertion (verbatim)

```python
self.assertIn("tool-followup", [r["kind"] for r in allowed["rows"]])
```

## New assertion (verbatim)

```python
by_send = sorted(allowed["rows"], key=lambda r: int(r["send_index"]))
self.assertEqual([int(r["send_index"]) for r in by_send], [0, 1],
                 "each send owns exactly one row")
self.assertEqual([r["row_measurement_source"] for r in by_send],
                 ["turn-initial", "tool-followup"],
                 "row 0 measures the turn's own send, row 1 the follow-up's")
self.assertIs(by_send[1]["fetch_followup"], True,
              "the follow-up's row is marked as the follow-up it measures")
shas = [r["request_sha256"] for r in by_send]
self.assertEqual(len(set(shas)), 2, f"each send has its OWN request_sha256: {shas}")
self.assertTrue(all(s and s != R.client.REQUEST_SHA_UNKNOWN for s in shas), shas)
```

The original intent — *a follow-up counts as a second billed unit* — is preserved and made
stronger: two sends, two rows, two distinct request identities, no shared measurement. The
scenario's fake transport now stamps `request_sha256 = sha256("wire-body-<n>")` per send
(cf. `experiments/ptr-engine/longrun/tests/test_row_attribution.py:94-95`); before that it stamped nothing and every row
carried `REQUEST_SHA_UNKNOWN`, which is why the invariant could not be asserted.

## Measurements

| suite | before | after |
|---|---|---|
| cap gate | 9 tests, 1 failure (`'tool-followup' not found in ['turn-initial', 'turn']`) | **9 tests, OK** |
| row attribution | — | **5 passed** |
| longrun full (176) | 2 failures | 1 failure — `test_verdict_ritual`, unrelated |
| repo root (`pytest -q tests`) | — | 2 failed / 1375 passed / 1 skipped — both pre-existing, outside this unit |

## Can any card's acceptance command now fail for a reason outside its own write scope?

Not through this test: it was the only cap-gate red, and it now asserts the attribution
invariant instead of a pre-fix kind list.
