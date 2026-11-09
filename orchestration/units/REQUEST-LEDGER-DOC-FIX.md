# UNIT `REQUEST-LEDGER-DOC-FIX`

**Purpose (one):** correct `docs/REQUEST-LEDGER.md` additively so no paragraph presents the non-deducted
de-duplicated figure as the budget. Offline, zero requests. Bound: 14 tool calls.

**Write paths:** `docs/REQUEST-LEDGER.md`, `orchestration/units/REQUEST-LEDGER-DOC-FIX.md`,
`orchestration/handoffs/REQUEST-LEDGER-DOC-FIX.json`,
`orchestration/journals/REQUEST-LEDGER-DOC-FIX.jsonl`.

**Source hit:** `orchestration/handoffs/WITHDRAWN-SCREEN.json` — WI-002 at `docs/REQUEST-LEDGER.md:145`.

**Scheme.** Old sentences and numbers stay visible; a dated correction block naming `WI-002` is appended
beneath each. The budget is stated as `1,101 of 4,320 raw, 3,219 remaining`; `1,071 / 3,249` is labelled a
diagnostic, **not deducted**, with the one-line reason (`V-DUPLICATE-RULE` fail: `content_sha256` is a
response hash, not request identity; deducting understates spend).

**Result.** Two correction blocks added: the flagged `:145` paragraph, and the intro paragraph at `:13`
which also presented 1,071 as the request count with no withheld status. Guard
`withdrawn_index.py --check docs/REQUEST-LEDGER.md` exits 0; a `/tmp` copy carrying the old line exits 1 (WI-002).
