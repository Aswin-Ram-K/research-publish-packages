# CONTRACT3 — answer contract, marker grammar, fetch gating

- Fix 1: `tasks-v7/TX-01.v1.json` system_prompt now lists four explicit forms (NUM/CALL/NONE/TEXT), one per line; slash enumeration removed everywhere. `grade_v5.parse_answer_contract` treats `ANSWER: 1/1/NONE` as OOV (ungradeable).
- Fix 2: masked marker renders exact fetch ref `[MASKED doc-<name>@r<revision>]`; `mask_output` aligned. Round-trip: 3 markers (doc-config@r1, doc-constants@r1, doc-errors@r1) all parse via fetch_tool and resolve bodies under D.
- Fix 3: checkpoint_prompt arm-aware: D states marker grammar + example fetch(ref="doc-constants@r1") + fetch-only-when-marker-blocks; C states retrieval unavailable → context or ANSWER: NONE. Removed "bounded retrieval may be used before answering" wording.
- Tests: `tests/test_contract3.py` (5 passed).
