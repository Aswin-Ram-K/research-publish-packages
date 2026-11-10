# Context arms (COMBINED-CONTEXT-SERVING)

## Arms
- **A** verbatim append-only: system preamble, then one user/assistant pair per completed turn (instruction verbatim + produced answer verbatim), then current turn instruction.
- **B** dense typed append-only: preamble, then one canonical record per completed turn `{kind, turn, instruction, claim (<=240 chars), refs[{path,pointer,digest}], produced_artifact_digest, notes}`; source bodies are never inlined, only full-digest refs resolved via the store.
- **C** B plus append-only observation references: identical to B, but work turns older than K (default 12) have their observation body replaced in the outgoing view by a single reference record naming the digest; history/store keep every byte. Returns metadata `{arm, turn, masked_turns, replaced_bytes, divergence_turn}`.

## Record schema
Canonical serialization: UTF-8 JSON, `sort_keys=True`, `separators=(",",":")`, `ensure_ascii=False`, no trailing whitespace, LF only (`canonical.dumps`, `canonical.digest`).

## Render a turn
```python
import sys; sys.path.insert(0, "arms")
from render_arms import build_messages
msgs = build_messages("B", fixture, history, turn)  # list[{"role","content"}]
```

## Controls
```bash
python3 arms/controls.py
```

## Mutant (red) demonstration
A mutant must be a **directory shadow**, never a file: `ARMS_PATH` is consumed as a directory on `sys.path`. Create `arms/tests/mutant/` with copies of `canonical.py`, `store.py`, `fixtures/`, and a mutated `render_arms.py` that inlines source bodies into arm B. Then:
```bash
ARMS_PATH=arms/tests/mutant python3 -m pytest arms/tests/test_arms_contract.py -q
# 4 passed, 1 failed (test_b_no_source_body)
```
Real run: `5 passed` (arms). Mutant run: `4 passed, 1 failed`.
