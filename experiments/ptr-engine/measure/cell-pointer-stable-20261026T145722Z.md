# CELL pointer-stable — 20261026T145722Z

- fixture: `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json`
- arm: `pointer-stable`  turns: 48  reps: 1  mode: offline (experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl)
- harness_sha256: `231b0ae11477e85c9e27886d82ea0896138abde7891617584a5a04aee97342d8`
- harness files: `analyze_stats.py`, `client.py`, `fixture`, `grade_v5.py`, `run_longrun.py`, `tools/det_verify.py`
- requests actually used: **0**

## stages

- `1/7 preflight ok checkpoints=3 turns=[12, 24, 46] kinds=['NUM', 'NUM', 'CALL'] fixture=v5-answer-contract`
- `2/7 harness ok harness_sha256=231b0ae11477e85c9e27886d82ea0896138abde7891617584a5a04aee97342d8 files=6`
- `3/7 budget skipped offline mode: no request is sent`
- `4/7 run skipped offline mode: rows reused from experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl`
- `5/7 grade ok verdicts=pointer-stable       acc=1/3 decidable=3 text=0 verified=False reasons=answer_not_contract,answer_not_contract`
- `6/7 analyse ok checks=3 refusals=1 (a refusal is printed, never replaced by a number)`

## grade (verbatim)

```
pointer-stable       acc=1/3 decidable=3 text=0 verified=False reasons=answer_not_contract,answer_not_contract
  cp.0.t12     T12  pass   num_equal                asserted=64 expected=64  [experiments/ptr-engine/ptr_engine/resolve.py:39 ast.Assign DEFAULT_MAX_REFS = 64]
  cp.1.t24     T24  fail   answer_not_contract      asserted=None expected=31  [experiments/ptr-engine/ptr_engine/errors.py:15-247 ast.ClassDef count(^Ptr\w*$) = 31]
  cp.2.t46     T46  fail   answer_not_contract      asserted=None expected={'callee': 'ledger.record_refusal', 'kwargs': {'code': 'error.code', 'scope': 'scope_name', 'serialized_ref': 'text'}, 'kwargs_as_written': ['scope', 'serialized_ref', 'code']}  [experiments/ptr-engine/ptr_engine/resolve.py:69 ast.Call inside _refuse -> ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)]
```

## analysis (verbatim)

```
analyze_stats  rows=72  files=1
  rows-longrun-v6-tools.jsonl  rows=72

arm pointer-stable  (rows n=72)
  ttft_p50 n=72  158.19ms [146.19, 200.61]  (ttft dropped: 0 null, 0 unavailable)  order-stat span p40.3-p62.5
  ttft_p95 n=72  435.27ms [346.51, 529.89]  (ttft dropped: 0 null, 0 unavailable)  order-stat span p90.3-p100.0
  accuracy  UNDECIDABLE (n=0 decidable turns; 72 rows carry no decidable outcome)
```

## refusals (numbers withheld on purpose)

- arm pointer-stable accuracy: no decidable turns (n=0)
