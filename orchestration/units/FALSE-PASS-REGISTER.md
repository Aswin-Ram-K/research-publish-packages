# FALSE-PASS-REGISTER

**Purpose.** Adjudicate the 3 records flagged `E_STATUS_WORD_CONTRADICTION` by
`HANDOFF-PARTIAL-SUBSTANCE` (reported as `R2-A3`, `R2-B2`, `R2-C`) and register the verdict.
Additive only: never edit a handoff, a ledger, or a verdict row.

**Resolved ids** (aliases → files): `R2-A3` → `orchestration/handoffs/R2-A3.json`,
`R2-B2` → `orchestration/handoffs/R2-B2.json`, `R2-C` → `orchestration/handoffs/R2-C.json`.

**Classifications.** All three: `substantive_elsewhere`. Each lacks all six contracted substance
keys (`evidence`, `checks`, `measurements`, `findings`, `commands`, `command_or_count`) — hence the
flag — but each carries re-fetchable verbatim quotes with URLs and a mechanism, so the claim is
judgeable under another key. Zero `false_pass`.

**Mechanical check.** `python3 experiments/ptr-engine/tools/false_pass_audit.py --check` → exit 0
when the register covers every currently flagged record and every recorded `sha256` still matches
the handoff on disk; exit 1 naming the drifted record or the new unregistered one.

**Hard bound.** 24 tool calls. Offline: zero network requests, no URL re-fetch.

**Write paths.** `experiments/ptr-engine/measure/FALSE-PASS.json`, `docs/FALSE-PASS.md`,
`experiments/ptr-engine/tools/false_pass_audit.py`,
`experiments/ptr-engine/longrun/tests/test_false_pass.py`,
`orchestration/units/FALSE-PASS-REGISTER.md`, `orchestration/handoffs/FALSE-PASS-REGISTER.json`,
`orchestration/journals/FALSE-PASS-REGISTER.jsonl` (+ `.log` mirror per card wording).
