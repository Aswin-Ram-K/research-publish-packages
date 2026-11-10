# Withdrawn: LR-01.v10 pointer-contrast fixture

Attempted: built `tasks-v6/LR-01.v10.json` (`fixture_version: v10-pointer-contrast`) to give the 48-turn gradable task per-turn `tool_outputs` so the `masking-no-fetch` arm would have material to mask, with an accompanying self-check `tests/test_fixture10_contrast.py`.

Review finding (independent adversarial review, confidence 0.99): the fixture cannot discriminate between arms — all 12 checkpoints keep their source evidence in plaintext under *both* arms, so `masking-no-fetch` and `bounded-context-fetch` would both answer from resident text and any measured difference would be noise. Pointer-fetch integration and generation-identity defects were also reported, and the self-check does not detect the plaintext leak.

Standing consequence: no fixture in this repository currently supports a discriminating mask-vs-fetch contrast. `LR-01.v9.json` remains the gradable task for tests that do not need masking. The pointer store, answer contract (`ANSWER: NUM/CALL/NONE/TEXT`, OOV ungradeable — `orchestration/handoffs/V-REFUSAL2.json`) and arm code are unchanged.
" path="experiments/ptr-engine/longrun/WITHDRAWN-LR01-V10.md" /><|end|><|start|> assistant to=bash<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="command">
cd "/home/zer0null/research extractor" && grep -rn "LR-01.v10\|v10" experiments/ptr-engine/longrun --include=*.py --include=*.json --include=*.md