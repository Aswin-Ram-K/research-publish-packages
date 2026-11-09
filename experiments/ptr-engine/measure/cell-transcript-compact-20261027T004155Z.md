# CELL transcript-compact — 20261027T004155Z

- fixture: `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json`
- arm: `transcript-compact`  turns: 12  reps: 1  mode: live
- harness_sha256: `efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3`
- harness files: `analyze_stats.py`, `client.py`, `fixture`, `grade_v5.py`, `run_longrun.py`, `tools/det_verify.py`
- requests actually used: **14**

## stages

- `1/7 preflight ok checkpoints=12 turns=[6, 8, 12, 14, 18, 20, 24, 26, 32, 36, 42, 46] kinds=['CALL', 'CALL', 'NUM', 'NONE', 'NUM', 'NONE', 'NUM', 'NUM', 'NUM', 'CALL', 'NONE', 'CALL'] fixture=v8-treatments-reachable`
- `2/7 harness ok harness_sha256=efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3 files=6`
- `3/7 budget ok would_send_total=-24 +10%=-26 <= budget=108 (quota_remaining=3106 best-effort)`
- `3a/7 G1 ledger gate ok G1 1,236/4,320 requests · cap 4,320 - reserve 0 - spent 1,176 (counted by request_ledger.py)`
- `3b/7 projection ok turns=12 projected_requests=12 projected_wall~=720s (cap-per-turn 180s -> worst case 2160s) cap=900s projected-turn-wall=60.0s source=artefact-mode thinking=off`
- `3c/7 G3 prereg gate ok G3 n=12 (smoke, non-comparable) · claim none (PARM-1 21cb85511b78dc4046f0f8f1449b68a7de2fd8bd8f659985efd63c9651398ec8) under {"basis": "a cell that declares claim=none makes no PARM-1 claim, so no n threshold applies; claim_mode.resolve_claim is the only resolver of that decision", "min_n": 0}`
- `gates recorded experiments/ptr-engine/measure/cell-transcript-compact-20261027T004155Z-p16-001.gates.json (3 verdicts, 3 artefact digest(s))`
- `4/7 run ok rows=14 path=experiments/ptr-engine/measure/rows-cell-transcript-compact-20261027T004155Z.jsonl`
- `5/7 grade ok verdicts=transcript-compact   acc=1/12 decidable=12(pass 1, fail 11) undecidable=0 missing=9 text=0 verified=False reasons=callee_mismatch,callee_mismatch,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing`
- `6/7 analyse ok checks=2 refusals=2 (a refusal is printed, never replaced by a number)`
- `6b/7 consistency ok grader decidable=12 (grade_v5.py:653) vs analyser graded_n=12 (analyze_stats.py:457)`

## budget

would_send_total=-24  budget=108  required_with_headroom=-26  quota_remaining=3106 (best-effort: project cap 4320 minus rows on disk in experiments/ptr-engine/measure (21 files); the runner reports no quota)

## gate chain (verdicts taken before the runner was invoked)

- `G1 allow` computed=1,236 requests limit=4,320 requests (cap 4,320 - reserve 0 - spent 1,176) artefact=`experiments/ptr-engine/measure/REQUEST-LEDGER.json` sha256=`63e3a15631d63e4ee1fd7e8acc905262f5bb4f1680749f723e1877c3d34f5716`
- `G2 allow` computed=720 s limit=900 s (--max-wall) artefact=`experiments/ptr-engine/measure/PROJECTION.json` sha256=`75d02c735da66156f6d7b13554d9cdd2da8b2d99df5d7032ea2e761feca3925c`
- `G3 allow` computed=claim=none declared (smoke/plumbing) limit=no claim is made, so no PARM-1 n threshold applies artefact=`experiments/ptr-engine/measure/PREREG-ARM-RUN.json` sha256=`696de5100315889172d4424de1c60a9699c17bc5d3a736226cc3171987bf56d6`
- hypothesis: `none` (flag:--hypothesis (smoke)), n=12, rule_sha256=`21cb85511b78dc4046f0f8f1449b68a7de2fd8bd8f659985efd63c9651398ec8`
- manifest: `experiments/ptr-engine/measure/cell-transcript-compact-20261027T004155Z-p16-001.gates.json`

## grade (verbatim)

```
transcript-compact   acc=1/12 decidable=12(pass 1, fail 11) undecidable=0 missing=9 text=0 verified=False reasons=callee_mismatch,callee_mismatch,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing,turn_missing
  cp.0.t06     T6   fail   callee_mismatch          asserted={'callee': 'record_resolution', 'kwargs': {'block_size': 'scope.block()', 'bytes_appended': 'len(presented.encode("utf-8"))', 'entry_text': 'entry.text', 'scope': 'scope.name', 'serialized_ref': 'presented'}, 'kwargs_as_written': ['scope', 'serialized_ref', 'bytes_appended', 'block_size', 'entry_text']} expected={'callee': 'ledger.record_resolution', 'kwargs': {'block_size': 'scope.block()', 'bytes_appended': "len(presented.encode('utf-8'))", 'entry_text': 'entry.text', 'scope': 'scope.name', 'serialized_ref': 'presented'}, 'kwargs_as_written': ['scope', 'serialized_ref', 'bytes_appended', 'block_size', 'entry_text']}  [experiments/ptr-engine/ptr_engine/resolve.py:159 ast.Call inside resolve -> ledger.record_resolution(scope=scope.name, serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), block_size=scope.block(), entry_text=entry.text)]
  cp.1.t08     T8   fail   callee_mismatch          asserted={'callee': 'block', 'kwargs': {}, 'kwargs_as_written': []} expected={'callee': 'scope.block', 'kwargs': {}, 'kwargs_as_written': []}  [experiments/ptr-engine/ptr_engine/resolve.py:163 ast.Call inside resolve -> scope.block()]
  cp.2.t12     T12  pass   num_equal                asserted=64 expected=64  [experiments/ptr-engine/ptr_engine/resolve.py:39 ast.Assign DEFAULT_MAX_REFS = 64]
  cp.3.t14     T14  fail   turn_missing             asserted=None expected='NONE'  [experiments/ptr-engine/ptr_engine/resolve.py ast.Call *.record_refusal inside resolve -> absent]
  cp.4.t18     T18  fail   turn_missing             asserted=None expected=6  [experiments/ptr-engine/ptr_engine/errors.py:176-211 ast.ClassDef count(^PtrLedger\w*$) = 6]
  cp.5.t20     T20  fail   turn_missing             asserted=None expected='NONE'  [experiments/ptr-engine/ptr_engine/resolve.py ast.Call *.resolved_count inside _refuse -> absent]
  cp.6.t24     T24  fail   turn_missing             asserted=None expected=31  [experiments/ptr-engine/ptr_engine/errors.py:15-247 ast.ClassDef count(^Ptr\w*$) = 31]
  cp.7.t26     T26  fail   turn_missing             asserted=None expected=5  [experiments/ptr-engine/ptr_engine/errors.py:217-247 ast.ClassDef count(^PtrLaw\w*$) = 5]
  cp.8.t32     T32  fail   turn_missing             asserted=None expected=2  [experiments/ptr-engine/ptr_engine/errors.py:36-42 ast.ClassDef count(^PtrUnknown\w*$) = 2]
  cp.9.t36     T36  fail   turn_missing             asserted=None expected={'callee': 'ledger.resolved_count', 'kwargs': {}, 'kwargs_as_written': []}  [experiments/ptr-engine/ptr_engine/resolve.py:141 ast.Call (line-pinned) -> ledger.resolved_count()]
  cp.10.t42    T42  fail   turn_missing             asserted=None expected='NONE'  [experiments/ptr-engine/ptr_engine/resolve.py ast.Call *.block inside _refuse -> absent]
  cp.11.t46    T46  fail   turn_missing             asserted=None expected={'callee': 'ledger.record_refusal', 'kwargs': {'code': 'error.code', 'scope': 'scope_name', 'serialized_ref': 'text'}, 'kwargs_as_written': ['scope', 'serialized_ref', 'code']}  [experiments/ptr-engine/ptr_engine/resolve.py:69 ast.Call inside _refuse -> ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)]
```

## analysis (verbatim)

```
analyze_stats  rows=14  files=1
  definition[ttft-definition/1]: per-turn TTFT = the TTFT of the turn's own initial request: kind='turn-initial' when present, else the legacy kind='turn' row with definition_fallback=true; a kind='tool-followup' row is a request inside a turn and is never a turn's latency
  rows-cell-transcript-compact-20261027T004155Z.jsonl  rows=14
  usable_for unstamped  rows-cell-transcript-compact-20261027T004155Z.jsonl  (included: no usability stamp on disk -- not a certification)
  CLAIM REFUSAL  incomparable_claim rows-cell-transcript-compact-20261027T004155Z.jsonl: refusing a comparison that includes 14 cell row(s) which make no claim (claim_free): cell=LR-01 arm=transcript-compact rep=1 turn=1; cell=LR-01 arm=transcript-compact rep=1 turn=1; cell=LR-01 arm=transcript-compact rep=1 turn=1; cell=LR-01 arm=transcript-compact rep=1 turn=2; cell=LR-01 arm=transcript-compact rep=1 turn=3; cell=LR-01 arm=transcript-compact rep=1 turn=4; cell=LR-01 arm=transcript-compact rep=1 turn=5; cell=LR-01 arm=transcript-compact rep=1 turn=6; cell=LR-01 arm=transcript-compact rep=1 turn=7; cell=LR-01 arm=transcript-compact rep=1 turn=8; cell=LR-01 arm=transcript-compact rep=1 turn=9; cell=LR-01 arm=transcript-compact rep=1 turn=10; cell=LR-01 arm=transcript-compact rep=1 turn=11; cell=LR-01 arm=transcript-compact rep=1 turn=12. A smoke/plumbing cell declares claim='none' with comparison_eligible=false, so its rows can never enter a comparison -- they are not filtered out silently, they stop the comparison. Compare only cells that declare H1|H2|H3, or report the smoke cell's numbers on their own with its claim named.

arm transcript-compact  (rows n=14)
  definition: per-turn TTFT = the turn's own initial request (kind=turn-initial, else legacy kind=turn)  version=ttft-definition/1  turns selected=12 of 14 rows  follow-up rows dropped=1  mode=mixed  definition_fallback=true
  provenance transcript-compact: fixture_sha256=0804b51575cc model=occamy-1.0-NVFP4 thinking=off tools_mode=on:read_file
  ttft_p50  REFUSED at n=12  refusing p50 at n=12: the 95% order-statistic span is ranks 4-10 (p33.3-p83.3) and n*(1-q)=6.0 < 3; minimum n for p50 is 20
  ttft_p95  REFUSED at n=12  refusing p95 at n=12: the 95% order-statistic span is ranks 11-12 (p91.7-p100.0) and n*(1-q)=0.6 < 3; minimum n for p95 is 60
  timing_n = 14  (rows with a usable ttft_ms)
  graded_n = 12  (checkpoint cells graded by grade_v5)
  accuracy = 1/12 (pass 1, fail 11, undecidable 0, missing 9)
  accuracy wilson95 n=12  0.0833 [0.0149, 0.3539]
```

## refusals (numbers withheld on purpose)

- arm transcript-compact p50: refusing p50 at n=12: the 95% order-statistic span is ranks 4-10 (p33.3-p83.3) and n*(1-q)=6.0 < 3; minimum n for p50 is 20
- arm transcript-compact p95: refusing p95 at n=12: the 95% order-statistic span is ranks 11-12 (p91.7-p100.0) and n*(1-q)=0.6 < 3; minimum n for p95 is 60
