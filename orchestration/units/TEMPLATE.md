# TEMPLATE — the unit card

Copy this and fill it in. A card is a contract: the `prompt` (not the `description`) is what the board
sends to the worker. Two sections are load-bearing for the gate: **`verify:`** and **§CLOSING**.

---

# <UNIT> — <one line of purpose>

**Card:** <task board id> · execution <execution id> (filled in when the run starts)
**Bound:** ≤N tool calls, 0 inference requests. OFFLINE: <what is forbidden>.

## Why
<the measured defect, with paths and numbers>

## Objective
1. <what changes>
2. <what must not change>

## TESTS
- <the new tests, file, and the red→green demonstration>

## CLOSING — three steps; the handoff write is LAST (a card is not done before all three)

0. **Read this line first:** the verdict row is recorded **before** the handoff file exists. A handoff that
   is already written when the row is missing is the exact shape of all seven post-ritual `no-verdict`
   closures (`orchestration/VERDICT-RITUAL.md` §0: **0/7**).

1. **Run the acceptance command** (the `verify:` line) once, as one frozen string, and keep its real exit
   code.
2. **Record the verdict** with `orchestration_verdict action:"record"`, passing `taskId`, `executionId`,
   the **exact** command as one frozen string, its **real** exit code, the **40-hex head sha** the command
   ran against, and a short `output` tail. Paste it from
   `python3 experiments/ptr-engine/tools/verdict_payload.py --task <taskId> --execution <executionId> --command '<the exact command>'`.
   Then run `python3 experiments/ptr-engine/longrun/tests/test_verdict_ritual.py` — it fails if a settled
   card has a done handoff and no row.
3. **Only now write the handoff** `orchestration/handoffs/<UNIT>.json` — the seven-key unit shape, plus the
   measured evidence lines, plus `"verdict_recorded_before_handoff": true`.
   Full procedure: `orchestration/VERDICT-RITUAL.md`.

A card that skips step 2 settles **FAIL `no-verdict`** however good its diff is — and `operational` prose in
the handoff is not the gate. A card that cannot name an acceptance command **must declare that** in its
handoff and its board end line (`"acceptance": {"command": null, "reason": "..."}`) instead of leaving the
gate to fail it silently.

## verify
```
verify: <one command>        # exit 0 = the card succeeded
```
Its own line, inside the prompt, at the start of the line. One command, no `&&` chains that hide which part
failed, and it must **fail when the work is wrong**. It is the gate's fallback: when a worker records no
verdict row, the sweeper runs this line against the base tree in a scratch copy and settles the card on the
**measured** exit code. It must start with an allow-listed runner (`python3`, `pytest`, `node`, `npm`,
`bash`, …) — `curl`, `rm`, `sudo`, `eval` and pipelines into them are refused.

## WRITE PATHS — exactly (nothing else)
`<path 1>`
`<path 2>`

## HARD RULES
- Never weaken a guard or edit a test to earn a PASS.
- Never fabricate a sha, an exit code, or a command. `unstamped` is honest; `no-verdict` is the gate's rule.
- Handoff `partial` within 5 calls; journal first. Bound ≤N calls.

## REPORT
Board: one line at start, one at end. The end line carries the measured evidence and **the verdict row as
recorded** (command, exit code, sha) or, for a card with no acceptance command, the declaration from §CLOSING.

## Research

A card that uses a network/API contract we did not write, proposes a mechanism instead of measuring one, fixes
an instrument whose semantics we are guessing at, or spends requests on a hypothesis with a published answer
**must run the research step first** — [`docs/RESEARCH-PROTOCOL.md`](../../docs/RESEARCH-PROTOCOL.md) §1
(two-line test) and §2 (where it lands): `docs/research/<SLUG>.md` + `measure/research/<SLUG>.json` carrying
`sources[].url`, `sources[].retrieved_at`, `claims[].status ∈ {verified, inferred, contradicted}` and
`open_questions`. A `verified` claim is a fact **about the source**, never a measurement of our stack; anything
about our rows, our config or our version is a measurement, and a workaround (e.g. a text-protocol shim) is
labelled `workaround: true`.

The handoff carries two extra keys, without which the card's handoff is incomplete:

```json
"research_note": "docs/research/<SLUG>.md",
"claims_status": {"<claim id or text>": "verified|inferred|contradicted"}
```

`research_note` is the note path, or `null` **with** `"research_note_reason"` naming why the card is a pure
measurement of our own rows. `claims_status` maps **every** external-contract claim the card relied on to its
status, so a documentation fact can never wear a measurement's clothes in the handoff.

**Adoption (append-only addition, [`docs/RESEARCH-PROTOCOL.md`](../../docs/RESEARCH-PROTOCOL.md) §8).** When the
card meets a **hairy** problem — mechanism unclear, more than one component must change, we are about to write
infrastructure rather than a measurement, or the same-shaped problem was solved outside this repo — a research
card landing an adoption memo `docs/research/ADOPT-<SLUG>.md` (+ `measure/research/ADOPT-<SLUG>.json`) comes
**first**, before the build card, exactly as coordination comes first. The memo's table carries one row per
candidate with **name, licence, maturity, last release, what it would replace, adopt cost, build cost avoided,
decision ∈ {adopt, adapt, borrow-idea, build, not-applicable}**, and **a source URL + retrieval date on every
row**; an option nobody read stays `unassessed` and is not named. When `adopt cost < build cost` and the option
is maintained, adopt. The handoff then carries two more keys:

```json
"adoption_considered": true,
"adoption_memo": "docs/research/ADOPT-<SLUG>.md"
```

`adoption_considered` is `false` only when no §8.1 test holds, with the failing test named; `adoption_memo` is
`null` with `adoption_memo_reason` when no memo exists. The running record is
[`docs/research/ADOPTION-LEDGER.md`](../../docs/research/ADOPTION-LEDGER.md).
