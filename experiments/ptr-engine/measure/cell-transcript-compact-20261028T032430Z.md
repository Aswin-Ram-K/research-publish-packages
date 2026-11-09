# CELL transcript-compact — 20261028T032430Z

- fixture: `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json`
- arm: `transcript-compact`  turns: 48  reps: 1  mode: live
- harness_sha256: `efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3`
- harness files: `analyze_stats.py`, `client.py`, `fixture`, `grade_v5.py`, `run_longrun.py`, `tools/det_verify.py`
- requests actually used: **81**

## stages

- `1/7 preflight ok checkpoints=12 turns=[6, 8, 12, 14, 18, 20, 24, 26, 32, 36, 42, 46] kinds=['CALL', 'CALL', 'NUM', 'NONE', 'NUM', 'NONE', 'NUM', 'NUM', 'NUM', 'CALL', 'NONE', 'CALL'] fixture=v8-treatments-reachable`
- `2/7 harness ok harness_sha256=efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3 files=6`
- `3/7 budget ok would_send_total=48 +10%=53 <= budget=108 (quota_remaining=1997 best-effort)`
- `3a/7 G1 ledger gate ok G1 1,417/4,320 requests · cap 4,320 - reserve 0 - spent 1,321 (counted by request_ledger.py)`
- `3b/7 projection ok turns=48 projected_requests=48 projected_wall~=2880s (cap-per-turn 180s -> worst case 8640s) cap=2880s projected-turn-wall=60.0s source=artefact-mode thinking=off`
- `3c/7 G3 prereg gate ok G3 n=48 ≥ 1 · claim H2 (PARM-1 21cb85511b78dc4046f0f8f1449b68a7de2fd8bd8f659985efd63c9651398ec8) under {"basis": "a per-turn ratio needs at least one completed turn per arm", "claim": "within the same grid, pointer-stable carries fewer total prompt tokens per completed turn than transcript-grow", "materiality_margin": "C per-turn total <= 0.95 x A (5% reduction) on prompt_tokens AND < 1.00 x on uncached", "min_n": 1, "unit_of_account": "prompt_tokens summed over non-excluded completed turns, divided by that same count; not wall time, not request count (identical by construction), not completion tokens as primary"}`
- `gates recorded experiments/ptr-engine/measure/cell-transcript-compact-20261028T032430Z-p227-001.gates.json (3 verdicts, 3 artefact digest(s))`
- `4/7 run ok rows=81 path=experiments/ptr-engine/measure/rows-cell-transcript-compact-20261028T032430Z.jsonl`
- `5/7 grade ok verdicts=transcript-compact   acc=5/10 decidable=10(pass 5, fail 5) undecidable=2 missing=0 text=0 verified=False reasons=kind_mismatch:NONE_expected,num_mismatch,num_mismatch,num_mismatch,kwarg_value_mismatch:scope`
- `6/7 analyse ok checks=3 refusals=1 (a refusal is printed, never replaced by a number)`
- `6b/7 consistency ok grader decidable=10 (grade_v5.py:653) vs analyser graded_n=12 (analyze_stats.py:457)`

## budget

would_send_total=48  budget=108  required_with_headroom=53  quota_remaining=1997 (best-effort: project cap 4320 minus rows on disk in experiments/ptr-engine/measure (38 files); the runner reports no quota)

## gate chain (verdicts taken before the runner was invoked)

- `G1 allow` computed=1,417 requests limit=4,320 requests (cap 4,320 - reserve 0 - spent 1,321) artefact=`experiments/ptr-engine/measure/REQUEST-LEDGER.json` sha256=`3f879fa424105319cf87b6f571ac88424ccad9d394e052ac65a00c359fe2968a`
- `G2 allow` computed=2880 s limit=2880 s (--max-wall) artefact=`experiments/ptr-engine/measure/PROJECTION.json` sha256=`75d02c735da66156f6d7b13554d9cdd2da8b2d99df5d7032ea2e761feca3925c`
- `G3 allow` computed=n=48 limit=n >= 1 artefact=`experiments/ptr-engine/measure/PREREG-ARM-RUN.json` sha256=`696de5100315889172d4424de1c60a9699c17bc5d3a736226cc3171987bf56d6`
- hypothesis: `H2` (flag:--hypothesis (hypothesis)), n=48, rule_sha256=`21cb85511b78dc4046f0f8f1449b68a7de2fd8bd8f659985efd63c9651398ec8`
- manifest: `experiments/ptr-engine/measure/cell-transcript-compact-20261028T032430Z-p227-001.gates.json`

## grade (verbatim)

```
transcript-compact   acc=5/10 decidable=10(pass 5, fail 5) undecidable=2 missing=0 text=0 verified=False reasons=kind_mismatch:NONE_expected,num_mismatch,num_mismatch,num_mismatch,kwarg_value_mismatch:scope
  cp.0.t06     T6   undecidable no_answer_line           asserted=None expected={'callee': 'ledger.record_resolution', 'kwargs': {'block_size': 'scope.block()', 'bytes_appended': "len(presented.encode('utf-8'))", 'entry_text': 'entry.text', 'scope': 'scope.name', 'serialized_ref': 'presented'}, 'kwargs_as_written': ['scope', 'serialized_ref', 'bytes_appended', 'block_size', 'entry_text']}  [experiments/ptr-engine/ptr_engine/resolve.py:159 ast.Call inside resolve -> ledger.record_resolution(scope=scope.name, serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), block_size=scope.block(), entry_text=entry.text)]
  cp.1.t08     T8   undecidable no_answer_line           asserted=None expected={'callee': 'scope.block', 'kwargs': {}, 'kwargs_as_written': []}  [experiments/ptr-engine/ptr_engine/resolve.py:163 ast.Call inside resolve -> scope.block()]
  cp.2.t12     T12  pass   num_equal                asserted=64 expected=64  [experiments/ptr-engine/ptr_engine/resolve.py:39 ast.Assign DEFAULT_MAX_REFS = 64]
  cp.3.t14     T14  fail   kind_mismatch:NONE_expected asserted={'callee': 'ledger.record_refusal', 'kwargs': {'code': 'error.code', 'scope': 'scope.name', 'serialized_ref': 'presented'}, 'kwargs_as_written': ['scope', 'serialized_ref', 'code']} expected='NONE'  [experiments/ptr-engine/ptr_engine/resolve.py ast.Call *.record_refusal inside resolve -> absent]
  cp.4.t18     T18  fail   num_mismatch             asserted=5 expected=6  [experiments/ptr-engine/ptr_engine/errors.py:176-211 ast.ClassDef count(^PtrLedger\w*$) = 6]
  cp.5.t20     T20  pass   none_confirmed_absent_in_source asserted=None expected='NONE'  [experiments/ptr-engine/ptr_engine/resolve.py ast.Call *.resolved_count inside _refuse -> absent]
  cp.6.t24     T24  fail   num_mismatch             asserted=20 expected=31  [experiments/ptr-engine/ptr_engine/errors.py:15-247 ast.ClassDef count(^Ptr\w*$) = 31]
  cp.7.t26     T26  fail   num_mismatch             asserted=4 expected=5  [experiments/ptr-engine/ptr_engine/errors.py:217-247 ast.ClassDef count(^PtrLaw\w*$) = 5]
  cp.8.t32     T32  pass   num_equal                asserted=2 expected=2  [experiments/ptr-engine/ptr_engine/errors.py:36-42 ast.ClassDef count(^PtrUnknown\w*$) = 2]
  cp.9.t36     T36  pass   call_equal               asserted={'callee': 'ledger.resolved_count', 'kwargs': {}, 'kwargs_as_written': []} expected={'callee': 'ledger.resolved_count', 'kwargs': {}, 'kwargs_as_written': []}  [experiments/ptr-engine/ptr_engine/resolve.py:141 ast.Call (line-pinned) -> ledger.resolved_count()]
  cp.10.t42    T42  pass   none_confirmed_absent_in_source asserted=None expected='NONE'  [experiments/ptr-engine/ptr_engine/resolve.py ast.Call *.block inside _refuse -> absent]
  cp.11.t46    T46  fail   kwarg_value_mismatch:scope asserted={'callee': 'ledger.record_refusal', 'kwargs': {'code': 'error.code', 'scope': 'scope.name', 'serialized_ref': 'presented'}, 'kwargs_as_written': ['scope', 'serialized_ref', 'code']} expected={'callee': 'ledger.record_refusal', 'kwargs': {'code': 'error.code', 'scope': 'scope_name', 'serialized_ref': 'text'}, 'kwargs_as_written': ['scope', 'serialized_ref', 'code']}  [experiments/ptr-engine/ptr_engine/resolve.py:69 ast.Call inside _refuse -> ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)]
```

## analysis (verbatim)

```
analyze_stats  rows=81  files=1
  definition[ttft-definition/1]: per-turn TTFT = the TTFT of the turn's own initial request: kind='turn-initial' when present, else the legacy kind='turn' row with definition_fallback=true; a kind='tool-followup' row is a request inside a turn and is never a turn's latency
  rows-cell-transcript-compact-20261028T032430Z.jsonl  rows=81
  usable_for unstamped  rows-cell-transcript-compact-20261028T032430Z.jsonl  (included: no usability stamp on disk -- not a certification)

arm transcript-compact  (rows n=81)
  definition: per-turn TTFT = the turn's own initial request (kind=turn-initial, else legacy kind=turn)  version=ttft-definition/1  turns selected=48 of 81 rows  follow-up rows dropped=17  mode=mixed  definition_fallback=true
  provenance transcript-compact: fixture_sha256=0804b51575cc model=occamy-1.0-NVFP4 thinking=off tools_mode=on:read_file
  ttft_p50 n=48  172.66ms [163.40, 188.03]  (ttft dropped: 0 null, 0 unavailable)  order-stat span p37.5-p66.7
  ttft_p95  REFUSED at n=48  refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60
  timing_n = 81  (rows with a usable ttft_ms)
  graded_n = 12  (checkpoint cells graded by grade_v5)
  accuracy = 5/10 (pass 5, fail 5, undecidable 2, missing 0)
  accuracy wilson95 n=10  0.5000 [0.2366, 0.7634]
```

## refusals (numbers withheld on purpose)

- arm transcript-compact p95: refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60
