# KINDAGG — multi-fact aggregation fixture

Authors TX-AGG.v1.json: 100 turns, 48 checkpoints on 48 unique turns, 12 per distance {2,6,20,32}. Each of 12 groups introduces 4 numeric facts across nearby turns; each checkpoint asks for an aggregate (sum of all / first two / last two / first+third) of that group facts, computable only by combining >=2 facts. No single tool body contains any expected value; all 48 expected values distinct.

Write paths: fixture, test, this card, handoff.
Checker: pass with disabled={reachability} (reachability N/A for aggregates); 48 checkpoints; no duplicate turns.
Tests: 14 passed.
