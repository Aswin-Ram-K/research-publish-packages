# R2-P1-O2 — cell lock / status stub

Unit: CELL 2 of 4, Round-2 prompt factorial, setup O2 (qwen3.5-9b dense, SGLang).
Lock file held: experiments/context-cache/.occamy.lock

STATUS: ABORTED AT PRE-FLIGHT. No container launched, no rows measured.
Reason (real output, 2026-10-24T02:07-05:00):
  MemAvailable = 21,914,344 kB  ->  BELOW the 35,000,000 kB abort threshold
  docker inspect gx10-occamy-nvfp4 -> "error: no such object: gx10-occamy-nvfp4"
  No sglang/gx10 image present in `docker images` (only non-GPU app images)
