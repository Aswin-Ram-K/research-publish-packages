# R2-P1-O2B

Cell 2 of the Round-2 prompt factorial: qwen3.5-9b NVFP4 on SGLang :8017.

- bound: 18 tool calls / 400 live requests (exceeded calls: harness restarted 4x mid-call)
- lock: experiments/context-cache/.occamy.lock (held whole run, released)
- writes: cell dir, this card, handoff
- outcome: 355 rows, 5 arms x 71 turns, G0 cached=5632, gcd 64, A-R=0.8838
- deviations: entrypoint needs explicit `sglang serve`; mem-fraction-static 0.22 unlaunchable -> 0.35
