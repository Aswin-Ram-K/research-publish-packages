# UNIT `VERDICT-DISPUTE`

**One purpose:** three closure records disagree with the cards they settle. Re-run the frozen commands
independently, decide which record is true for each claim, and publish the adjudication. **Offline: 0
inference requests. No existing document edited.** Bound: 26 tool calls.

Card tag: `automated` / `verdict` — no `ask_user_question`, no network, no inference.

## Question

At 16:46:24Z the sweep settled three closures. Two contradict their own cards:

1. `V-GATE-CHAIN-3` (`4e7e8017`, exec `0884f187`) closed **PASS** while its handoff says `overall: fail`
   with six surviving bypasses.
2. `P95-POWER-FROM-ROWS` (`3ef6e0e3`, exec `b03377d6`) closed **FAIL exit-1** while its board post
   claims PASS on `p95-power-verify.sh`.
3. `V-FIXTURE-V7` (`c87b53ae`) closed PASS — no dispute, confirm.

Both disputes decide money: `RUN-A*` (792 requests) has `V-GATE-CHAIN = pass` as a hard precondition, and
`A* sufficient` is the only reason 144 raw turns per arm is worth paying for.

## Method (as executed)

1. Pinned the tree before any judgement: `git rev-parse HEAD`, `git status --porcelain | wc -l`
   (count only), plus `sha256sum` of `cell.py`, `analyze_stats.py`, `fixture_v7_audit.py`,
   `p95-power-verify.sh`, `orchestration/units/V-GATE-CHAIN-3.md` — re-checked at the end, unchanged.
2. Extracted the embedded attack script from the V-GATE card between its markers and read it, then ran
   the frozen command verbatim.
3. Ran `p95-power-verify.sh` **twice** and, separately, the generator plus a JSON-level comparison, to
   separate "flaky" from "tree-state dependent" and to isolate the failing byte.
4. Re-ran `fixture_v7_audit.py`.
5. Cross-referenced the downstream artefacts that lean on each verdict.

## Result

**Claim 1 — `PASS` is supportable only as "the attack script ran green", not as "the gate chain has no
surviving hole".** The script does fail closed (`sys.exit(1 if bad else 0)`; exit 0 = 26 assertions true),
but six of its assertions *require the bypasses to be admitted* (`B2_max_wall_1e308_allows` → `exit == 6`,
and siblings for F2‑F5, F8), G2's decision expression is only a description string never compared to a
computed expectation, and G3 is untouched. A green run is compatible with the holes surviving because it
demands them. **Winner: the handoff.**

**Claim 2 — `A* sufficient` is `supported`; the closure FAIL is provenance drift.** Both runs exit 1,
stably; the only differing byte is `method.analyze_stats_sha256_atimport` (`0a9a7861…` vs committed
`2c9756f3…`); every computed number regenerates identically; `p95_power_gen.py:271-272` hashes the file
and sets `analyze_stats_imported: False`, so the digest never enters the computation. `analyze_stats.py`
is untracked at HEAD, which is why it could drift uncommitted. **Winner on substance: the card's PASS.**
The command is nonetheless red today, so the PASS cannot presently be re-earned from it.

**Claim 3 — no dispute:** `fixture_v7_audit.py` exits 0.

## Deliverables

| path | content |
|---|---|
| `experiments/ptr-engine/measure/VERDICT-DISPUTE.json` | three records side by side, recomputed exit codes with tree shas, per-claim adjudication, consequences |
| `experiments/ptr-engine/measure/VERDICT-DISPUTE.md` | the same, readable, incl. "what the verdict row can and cannot prove" |
| `orchestration/units/VERDICT-DISPUTE.md` | this card |
| `orchestration/handoffs/VERDICT-DISPUTE.json` | handoff |
| `orchestration/journals/VERDICT-DISPUTE.jsonl` | journal |

## What this unit did NOT do

It edited no script, fixture, threshold, test, or existing document — the two failing commands were run
verbatim, and their defects are reported, not repaired. It spent zero inference requests and made no
network call.
