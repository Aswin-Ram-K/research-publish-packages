# DIAG1 — compliance diagnosis (occamy-1.0, 3 completions)

Rows: `experiments/ptr-engine/measure/rows-compliance-diag-2026-11-08.jsonl` (3 rows).

## Sampling (from posctrl row + harness default)
- model `occamy-1.0`, endpoint `http://192.168.2.168:8012/v1`
- temperature 0, max_tokens 4096, thinking off (`enable_thinking=false`), stream false here (posctrl used stream true; content identical)
- temperature not recorded in posctrl rows → harness default 0 used.

## Exact instruction appended by harness (system_prompt, v4 fixture)
"End every answer with a final line: ANSWER: <the value, or NOT-AN-ANSWER>. The value must appear in that line, never only inside a pasted code block."

## Prompt construction
- Working set identical for R1/R2 (LR-01.v4 fixture, turn-12 checkpoint question).
- R1 control: current instruction + working set + question.
- R2 explicit: same + worked example `ANSWER: NUM 64` + "anything else invalid".
- R3 minimal: checkpoint question only, no scaffolding/system prompt.

## Results (raw answer ≤120 chars, parsed under score_longrun.answer_of)

R1 control:
"The default per-turn resolve budget is defined by `DEFAULT_MAX_REFS = 64` in resolve.py. / ANSWER: 64"
→ parsed NUM 64 (answer_of = "64").

R2 explicit:
"I'm checking the default per-turn resolve budget... DEFAULT_MAX_REFS = 64 ... ANSWER: NUM 64"
→ parsed NUM 64 (answer_of = "64").

R3 minimal:
"Based on the reference to ... PTR ... default resolve budget is 1000 refs."
→ prose_only; answer_of returns full prose; no ANSWER line.

## Verdict
Instruction-wording defect. The instruction's refusal token `NOT-AN-ANSWER` is not a valid contract kind: `grade_v5.parse_answer_contract` accepts only `NUM/CALL/NONE/TEXT`, so the 45 non-checkpoint turns that emit `ANSWER: NOT-AN-ANSWER` grade `unparseable` (43 of 45; 2 `multiple_answer_lines`). Harness bug excluded: R1 with the identical instruction produced a parseable `ANSWER: 64` under `score_longrun.answer_of`, proving the instruction reaches the model. Capacity limitation excluded as the primary cause: capacity failure looks like R3 (prose hallucination, no contract line, wrong value 1000), not like the observed `ANSWER: NOT-AN-ANSWER` token, which is the instruction's own vocabulary echoed verbatim.

Discriminating observations:
- R1 parsed → instruction reaches model (excludes harness bug).
- 45/48 posctrl turns echo the instruction's exact refusal token `ANSWER: NOT-AN-ANSWER` → wording mismatch, not capacity.
- R3 (no instruction) → prose_only + hallucinated 1000 → capacity/absence looks different.

## Cap accounting
- Before: cap 12094, spent 2639, remaining 9455.
- After 3 completions: spent 2642, remaining 9452.

## Cheapest next step if non-compliance persists
Change the refusal token in the instruction from `NOT-AN-ANSWER` to `NONE` (the contract kind), so non-checkpoint turns emit `ANSWER: NONE` and parse cleanly; equivalently teach the parser to map `NOT-AN-ANSWER` → `NONE`. One-line instruction edit, no model change.
