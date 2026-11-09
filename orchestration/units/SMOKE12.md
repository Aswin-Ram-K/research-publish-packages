# SMOKE12

- dry-run: offline, 12 requests projected (6 per arm), no socket opened.
- arm C (masking-no-fetch): 6 turns, stop=stop x6, masked_rows fired at T5 (3), no fetch.
- arm D (bounded-context-fetch): 10 requests (6 turn + 4 fetch follow-ups), fetches returned body with fact.
- accounting: rows written 16 = requests sent 16; cap 2642 -> 2658 (+16). Balanced.
- answers: short 10-token content replies; D turns 1-4 were tool_calls (fetch) with no final answer on first pass.
