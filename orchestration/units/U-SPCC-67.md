# U-SPCC-67 — the 6/48 attribution gap is a transcript-replay artefact

**Status:** DONE. Read-only analysis. Zero requests spent, no code or prompt changed.

## Why

U-SPCC-64 measured a 6/48 (12.5 pp) gap between `spcc` (48/48) and `masking-no-fetch`
(42/48) in `measure/rows-e3-retain-2026-11-10.jsonl`, with **no distance gradient** —
failures at d2, d8, d20, d32 and d64 perfect in both arms. That cell masks nothing
(`masked_rows = 0` on all 200 rows) and compacts nothing (`compactions = 0`), so both arms
carry every body. The gap therefore cannot be a retention effect. This unit asks what in
the two prompt formats makes the masking arm misattribute a value it has been given.

## Method — reconstruction verified against the rows

Both arms' prompts were rebuilt through the runner's own `Planner`
(`experiments/ptr-engine/longrun/run_longrun.py:1562`) with `send_chat` replaced by a
recorder, replaying each row's `content` through `Planner.record` and applying
`checkpoint_prompt` on the 48 checkpoint turns exactly as the run loop does
(`run_longrun.py:3555-3567`).

**`prompt_sha256` matched on 200/200 rows** — 100 turns × 2 arms, 0 mismatches. The
reconstruction is the prompt the model actually saw, not an approximation.

## Structural diff

### `masking-no-fetch` — flat transcript replay (T30: 158 lines, 1,611 prompt_tokens)

```
WORKING SET
INDEX
- doc-config@r1 e89a5778 85
- doc-errors@r1 9ff3224c 170
- doc-constants@r1 4ae7df40 95
- doc-revoked@r1 70c18e5f 26
- doc-versioned@r1 6437d0a9 27

BODY item-1 (33 B)
unrelated working set placeholder

QUESTION (T1): Work turn 1.
ANSWER (T1): ANSWER: NONE
...
QUESTION (Tt): <question>
TOOL OUTPUTS:
TOOL_OUTPUT (doc-fact-XX@1): # doc-fact-XX
VAL_A = ...
VAL_B = ...
VAL_C = ...
VAL_D = ...

ANSWER (Tt): <answer>
...
QUESTION (T30): What is VAL_A of doc-fact-09?
TOOL OUTPUTS:
TOOL_OUTPUT (doc-fact-01@1): # doc-fact-01
VAL_A = 4011
...

CHECKPOINT TURN.
Retrieval is unavailable; answer from context or ANSWER: NONE.
```

Blocks: one pinned working set, then **29 turn blocks**, then the current turn block, then
the contract. Every turn block is `QUESTION → TOOL OUTPUTS: → TOOL_OUTPUT (doc@rev): body
→ ANSWER (Tt): <value>`. No layer structure; the system prompt is a separate system
message and is not repeated in the user content.

### `spcc` — layered compiler (T30: 69 lines, 1,465 prompt_tokens)

`layer_tokens` from the row: `L0=80 L1=20 L2=215 L3=21 L4=2`.

```
L0  system prompt + answer contract + "RUN model=offline-model fixture=TX-04 generation=gen-7"
L1  5 world-index refs (ref, hash8, byte length — no fact values)
L2  journal, ONE line per prior turn:
      T2|user|QUESTION (T2): Work turn 2.⏎# doc-fact-02⏎VAL_A = 4021⏎VAL_B = 4022⏎...
L3  QUESTION (T30): What is VAL_A of doc-fact-09?
    # doc-fact-01
    VAL_A = 4011
    ...
L4  ANSWER: NONE
```

The journal line carries the question and the delivered body and **no answer**. The body's
own `# doc-fact-XX` header is the only document anchor.

### The one structural difference that matters

The masking arm replays an `ANSWER (Tt):` line after every turn's tool-output block. The
spcc journal replays no answers at all. Everything else — the pinned index, the current
turn's delivery appended after the question, the checkpoint contract — is shared.

## Where the two values sit, per failure

Line numbers are 1-based in the reconstructed prompt; token distances use the fixture's
`bytes_per_token = 4.0914`.

| checkpoint | turn | expected | answered | masking: expected | masking: answered | spcc: expected | spcc: answered |
|---|---:|---|---|---|---|---|---|
| `cp.TX-04.f09.d2` | 30 | 4091 | 4011 | L132, 32 tok before | L145, 27 tok after | L49, 21 before | L54, 17 after |
| `cp.TX-04.f02.d8` | 10 | 4021 | 4061 | L19, 112 before | L50, 27 after | L23, 73 before | L34, 17 after |
| `cp.TX-04.f07.d8` | 39 | 4072 | 4102 | L156, 171 before | L194, 30 after | L52, 115 before | L64, 20 after |
| `cp.TX-04.f08.d20` | 31 | 4083 | 4073 | L62, 428 before | L157, 33 after | L32, 283 before | L57, 23 after |
| `cp.TX-04.f12.d20` | 73 | 4123 | 4124 | L251, 336 before | L252, adjacent | L74, same line | L74 |
| `cp.TX-04.f02.d32` | 34 | 4023 | 4022 | L21, 693 before | L20, adjacent | L23, same line | L23 |

The expected value is present in **both** prompts at all six turns. The masking arm has
strictly more information than the spcc arm — it also carries every prior answer.

## Mechanism

### Proximity alone is refuted

At T30 the masking arm has the expected value 32 tokens before the question and the
answered value 27 tokens after; the spcc arm has 21 before and 17 after. **Both arms have
the answered value closer to the question than the expected one, and spcc answers
correctly.** So "the answered value is nearer" (option a) is not the mechanism.

### The answer slot binds to the adjacent tool-output block

Five checkpoint turns have a current-turn delivery, and in **all five the delivered
document differs from the asked document**:

| turn | checkpoint | asked | delivered | masking | spcc |
|---:|---|---|---|---|---|
| 10 | `f02.d8` | doc-fact-02 | doc-fact-06 | **4061 (wrong)** | 4021 |
| 12 | `f06.d2` | doc-fact-06 | doc-fact-04 | 4061 (right) | 4061 |
| 30 | `f09.d2` | doc-fact-09 | doc-fact-01 | **4011 (wrong)** | 4091 |
| 31 | `f08.d20` | doc-fact-08 | doc-fact-07 | **4073 (wrong)** | 4083 |
| 39 | `f07.d8` | doc-fact-07 | doc-fact-10 | **4102 (wrong)** | 4072 |

The masking arm answers with the delivered body's value on 4 of 5; the spcc arm on 0 of 5.
The transcript teaches a positional rule — *the `ANSWER` line takes its value from the
tool-output block immediately above it* — because that is the shape of all 29 prior turn
blocks it replays. On a checkpoint turn the fixture delivers a body for a different
document, and that body is the block immediately above the answer slot.

Quoted, masking T31 (lines 152-158):

```
QUESTION (T31): What is VAL_C of doc-fact-08?
TOOL OUTPUTS:
TOOL_OUTPUT (doc-fact-07@1): # doc-fact-07
VAL_A = 4071
VAL_B = 4072
VAL_C = 4073
VAL_D = 4074
```

Answered `4073`. The expected `4083` is at line 62, inside `TOOL_OUTPUT (doc-fact-08@1)`
delivered at T11 — 90 lines and 428 tokens above the question, and it is the only
occurrence of that value in the prompt.

### The single masking pass among the five is answer replay, not resolution

T12 is the one delivery turn the masking arm gets right, and it is the one where the
expected value had already been echoed as a prior answer. Masking T12, line 55:

```
ANSWER (T10): ANSWER: NUM 4061
```

T10's *wrong* answer (4061, taken from doc-fact-06's body) is T12's *correct* answer
(doc-fact-06's `VAL_A`). The value appears twice — once in the T10 body at line 50, once in
the T10 answer line at line 55 — and the model reproduces it. At T31 the expected `4083`
appears once. So the masking arm's only correct delivery-turn answer is supplied by the
replay, not by resolving the document name.

### The two within-document failures are a different, smaller error

Neither T34 nor T73 has a current-turn delivery, so there is no adjacent block to bind to.

- **T34** answered `4022`, which is exactly `ANSWER (T22): ANSWER: NUM 4022` — the replayed
  answer for the *same* document (doc-fact-02) but a different symbol (`VAL_B` for a
  `VAL_C` question). The replayed answers act as a stale same-document value cache.
- **T73** answered `4124`, the line immediately below the expected `VAL_C = 4123` in the
  same body (`VAL_D = 4124`, masking L252 vs L251). A within-body symbol slip.

## Verdict — intrinsic to a transcript replay that replays answers

The gap is **not** fixable without changing what the arm measures.

The answer replay is load-bearing for the masking treatment: the masking branch masks prior
answers on masked turns precisely so an earlier checkpoint's value cannot be copied without
recovering the fact (`run_longrun.py`, masking branch: *"Mask prior answers on masked turns
so an earlier checkpoint's value cannot be copied without recovering the fact"*). The
`ANSWER (Tt):` lines are the thing masking acts on. Delete them and the arm is no longer a
transcript replay — it is the spcc journal, i.e. the other arm.

The binding is a consequence of that replay, not of any tunable formatting choice: in a
transcript the answer necessarily follows the turn's tool output, and the current turn's
delivery necessarily follows the question. Both arms already share that ordering; only the
masking arm attaches an answer slot to it.

## Consequence for the comparison

**The 6/48 gap is a format artefact and must be excluded from any retention comparison.**

At this cell neither arm loses information: `masked_rows = 0`, `compactions = 0`,
`evicted = 0` on all 200 rows, and `expected_present` is `True` on 96/96 checkpoint rows
with `expected_present_source = prompt-digit-boundary`. The cell is a **format control**,
not a retention measurement. Its correct reading is: both arms retain everything; the
masking arm's transcript format costs 6/48 on checkpoint accuracy through answer-slot
binding, independent of distance.

Any retention claim must come from cells where the treatment actually fires — masking
window below 100 turns, or compaction interval below 100 turns. Pooling this 12.5 pp with
the distance cliff would attribute a prompt-format artefact to memory.

## Artifacts

- `experiments/ptr-engine/measure/rows-e3-retain-2026-11-10.jsonl` — read only, unchanged
- `orchestration/units/U-SPCC-67.md`
- `orchestration/handoffs/U-SPCC-67.json`

No rows, fixtures, manifests, `ptr_engine/layers.py`, `longrun/arm_cd.py`,
`longrun/claim_mode.py`, `longrun/cell.py`, prereg, ledger, `docs/STATE.md`, journal or
`orchestration/STATUS.md` was written.
