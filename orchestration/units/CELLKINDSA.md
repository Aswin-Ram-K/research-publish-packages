# CELLKINDSA

Measure TX-SUP.v1.json and TX-HOP.v1.json at the live endpoint, both arms, one replication each.

## Status
done

## Write paths
- experiments/ptr-engine/measure/rows-sup-2026-11-09.jsonl
- experiments/ptr-engine/measure/rows-hop-2026-11-09.jsonl
- experiments/ptr-engine/research-seed-concepts/RESULTS-KINDS-1-sup-hop.md
- orchestration/units/CELLKINDSA.md
- orchestration/handoffs/CELLKINDSA.json

## Summary
Completed both fixtures, both arms. SUP: masking 13/48, fetch 22/48. HOP: masking 12/48, fetch 16/48. Activation gates satisfied (masking fetch_rows=0; fetch total 253 and 104 >=40). Stale hits: SUP masking 0, fetch 2. HOP masking state: both-visible only at d=2; both-masked at d>=6; no mixed state. Spent 719 requests (19 over the 700 ceiling).
PY