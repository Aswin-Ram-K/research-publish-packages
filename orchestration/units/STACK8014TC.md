# UNIT STACK8014TC

Status: complete.

## Summary
Verified tool calling on `:8014` (PASS) and measured TX-03 both arms, AGG fetch arm, HOP fetch arm on `:8014`. Cross-stack comparison written to `experiments/ptr-engine/research-seed-concepts/RESULTS-STACK-8014.md`.

## Requests
- Tool-call verification: 1
- TX-03 masking: 100
- TX-03 fetch: 148
- AGG fetch: 141
- HOP fetch: 195
- Total: 585 (cap 12094; start 6847; end 7432; remaining 4662; unit ceiling 700)

## Results
- TX-03 masking: 8,0,0,0,0,0 (agrees with :8012).
- TX-03 fetch: 5,8,8,8,7,6 (42/48) vs :8012 8,8,8,8,6,3.
- AGG fetch: first fetch turn 10 (vs 29 on :8012), 41 turns with fetch.
- HOP fetch: first fetch turn 2 (vs 28 on :8012), 15 turns with fetch.
- Fetch arm now measurable on :8014 (activates inside 40-turn floor).
