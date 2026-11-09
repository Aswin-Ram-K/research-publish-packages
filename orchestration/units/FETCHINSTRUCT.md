# FETCHINSTRUCT

- unit: FETCHINSTRUCT
- status: done
- artifacts: experiments/ptr-engine/longrun/run_longrun.py, arm_cd.py (unchanged), tests/test_fetch_policy.py, measure/rows-fetchinstruct-probe.jsonl
- evidence: strict vs instructed instructions differ; answer contract identical; fetch_policy stamped on all 5 rows as 'instructed'; T5 checkpoint issued fetch(ref="doc-key-1@r1"); 5 requests spent, cap 12094.
- blocker: none
- next_unit_hint: none