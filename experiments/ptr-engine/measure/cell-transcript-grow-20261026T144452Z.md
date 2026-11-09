# CELL transcript-grow — 20261026T144452Z

- fixture: `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json`
- arm: `transcript-grow`  turns: 48  reps: 1  mode: offline (../../../tmp/cell-demo-rows.jsonl)
- harness_sha256: `53fb8112f0912b7744d14b448d13ef8ff1ae6bf0032f5e57cf94c981074d8d5e`
- harness files: `analyze_stats.py`, `client.py`, `fixture`, `grade_v5.py`, `run_longrun.py`, `tools/det_verify.py`
- requests actually used: **0**

## stages

- `1/7 preflight ok checkpoints=3 turns=[12, 24, 46] kinds=['NUM', 'NUM', 'CALL'] fixture=v5-answer-contract`
- `2/7 harness ok harness_sha256=53fb8112f0912b7744d14b448d13ef8ff1ae6bf0032f5e57cf94c981074d8d5e files=6`
- `3/7 budget skipped offline mode: no request is sent`
- `4/7 run skipped offline mode: rows reused from ../../../tmp/cell-demo-rows.jsonl`
- `5/7 grade ok verdicts=transcript-grow      acc=3/3 decidable=3 text=0 verified=True reasons=-`
- `6/7 analyse ok checks=4 refusals=0 (a refusal is printed, never replaced by a number)`

## grade (verbatim)

```
transcript-grow      acc=3/3 decidable=3 text=0 verified=True reasons=-
  cp.0.t12     T12  pass   num_equal                asserted=64 expected=64  [experiments/ptr-engine/ptr_engine/resolve.py:39 ast.Assign DEFAULT_MAX_REFS = 64]
  cp.1.t24     T24  pass   num_equal                asserted=31 expected=31  [experiments/ptr-engine/ptr_engine/errors.py:15-247 ast.ClassDef count(^Ptr\w*$) = 31]
  cp.2.t46     T46  pass   call_equal               asserted={'callee': 'ledger.record_refusal', 'kwargs': {'code': 'error.code', 'scope': 'scope_name', 'serialized_ref': 'text'}, 'kwargs_as_written': ['code', 'scope', 'serialized_ref']} expected={'callee': 'ledger.record_refusal', 'kwargs': {'code': 'error.code', 'scope': 'scope_name', 'serialized_ref': 'text'}, 'kwargs_as_written': ['scope', 'serialized_ref', 'code']}  [experiments/ptr-engine/ptr_engine/resolve.py:69 ast.Call inside _refuse -> ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)]
```

## analysis (verbatim)

```
analyze_stats  rows=64  files=1
  cell-demo-rows.jsonl  rows=64

arm transcript-grow  (rows n=64)
  ttft_p50 n=64  531.55ms [415.10, 634.30]  (ttft dropped: 0 null, 0 unavailable)  order-stat span p39.1-p64.1
  ttft_p95 n=64  933.64ms [865.14, 963.10]  (ttft dropped: 0 null, 0 unavailable)  order-stat span p90.6-p100.0
  accuracy  55/64  wilson95 n=64  0.8594 [0.7538, 0.9242]  (undecidable: 0)
```
