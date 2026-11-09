# ADOPT-BEFORE-BUILD — make adoption research a step, and open the ledger

**Card:** 0c90d64e-38fc-485d-87da-b4a1ac946745 · execution 85dd9051-3d95-49eb-88f8-7ad58cf91a99
**Bound:** ≤25 tool calls, 0 inference requests. OFFLINE for the model: no model requests, no experiments, no
live endpoint calls.

## Why

The operator's instruction — *"for every new problem we have, always learn about what's already available out
there to easily adopt and increase our throughput and reduce our workload too — so make researching, when
things seem hairy, a common step alongside coordination."* — is not yet a rule. `docs/RESEARCH-PROTOCOL.md`
(as of the previous head) covers §1–§7: *"has someone published the fact?"* It has no section on *"has someone
already built the thing?"*. The batch's own record shows the cost: roughly 200 rounds hand-building a gate /
budget / verdict / provenance stack, and a tool channel that spent 36 live requests before the client was
found never to send `tools` at all.

## Objective

1. **Append** a new section **§8 "Adopt before build"** to `docs/RESEARCH-PROTOCOL.md` — extending, not
   rewriting: the hairy test (§8.1), the adoption memo format `docs/research/ADOPT-<SLUG>.md` +
   `measure/research/ADOPT-<SLUG>.json` with source URL + retrieval date on every row (§8.2), the
   adopt-by-default rule with the batch's counter-example (§8.3), four added anti-patterns (§8.4), and the
   handoff fields `adoption_considered` / `adoption_memo` (§8.5). Two new bullets in the §7 checklist.
2. **Create** `docs/research/ADOPTION-LEDGER.md` (+ `measure/research/ADOPTION-LEDGER.json`) — one table of
   every hairy problem this batch met, two rows answered from landed evidence (tool calls on SGLang →
   `borrow-idea`; retry/backoff → `unassessed`, no invented name) and two further `unassessed` rows for the
   gate/verdict stack and the note validator.
3. **Append** the adoption paragraph and the two handoff keys to `orchestration/units/TEMPLATE.md`'s
   `## Research` section — append only, no restructuring.
4. **What must not change:** §1–§7 of the protocol (headings pinned by `tools/check_research_notes.py`),
   `docs/TOOL-CHANNEL-ROOT-CAUSE.md`, and the frozen instrument files.

## CLOSING — three steps; the handoff write is LAST

0. Read this line first: the verdict row is recorded **before** the handoff file exists.
1. Run the acceptance command exactly once, as one frozen string, and keep its real exit code.
2. Record the verdict with `orchestration_verdict action:"record"` (taskId, executionId, exact command, real
   exit code, 40-hex head sha, short output tail).
3. Only now write `orchestration/handoffs/ADOPT-BEFORE-BUILD.json`, with `"verdict_recorded_before_handoff": true`.

## verify
```
verify: bash -lc '/usr/bin/python3 tools/check_research_notes.py --protocol docs/RESEARCH-PROTOCOL.md --template orchestration/units/TEMPLATE.md --note measure/research/ADOPTION-LEDGER.json --doc docs/research/ADOPTION-LEDGER.md'
```
Exit 0 = the protocol still carries §1–§7 headings and the two new handoff keys, the ledger JSON parses with
sources/claims/open_questions/changes_plan, and the ledger doc carries its question and evidence sections.

## WRITE PATHS — exactly (nothing else)
`docs/RESEARCH-PROTOCOL.md` (append only)
`docs/research/ADOPTION-LEDGER.md`
`measure/research/ADOPTION-LEDGER.json`
`orchestration/units/TEMPLATE.md` (append only)
`orchestration/units/ADOPT-BEFORE-BUILD.md`
`orchestration/handoffs/ADOPT-BEFORE-BUILD.json`
`orchestration/journals/ADOPT-BEFORE-BUILD.jsonl`

## HARD RULES
- Never rewrite a §1–§7 section; append the two checklist bullets and §8 only.
- Never invent a project name, licence, release or URL for an unread option — `unassessed` is the honest value.
- Never weaken a guard or edit a test to earn a PASS.
- Never fabricate a sha, an exit code, or a command.
- Journal first, step-numbered. Bound 25 calls.

## Research

The adoption memo this card appends is itself the research step; its evidence base is
[`docs/research/tool-channel-sglang.md`](../../docs/research/tool-channel-sglang.md) (source
<https://docs.sglang.io/docs/advanced_features/tool_parser>, retrieved 2026-10-26) plus the local probe record
`orchestration/handoffs/TOOL-CHANNEL-ROOT-CAUSE.json`. Everything the ledger cannot evidence (retry/backoff
candidates, gate-stack tooling, note-lint tooling) is recorded `unassessed` with the owner named in
`open_questions` — never invented.
