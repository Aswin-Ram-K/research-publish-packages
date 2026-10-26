# Interface contract — the only bridge between the two halves

Consonance measures **quality and authority** (did the task complete, and was the context authorised and
auditable). The extractor measures **cache economics** (what the serving engine actually charged). Neither
number means anything to the other unless every run emits the same record. This file is that record.

## 1. Comparability rule (read this before designing an arm)

Two arms are comparable **only if all four fingerprints are equal**:

1. `model_fingerprint` — model id + revision/quantization digest;
2. `tokenizer_fingerprint` — tokenizer files or hash, plus the chat template hash;
3. `renderer_fingerprint` — the code that turns modules into the request bytes (content digest);
4. `engine_fingerprint` — container image digest + the exact serving flags.

If any differs, it is a **different experiment**, not a worse arm. Record it as such instead of adjusting a
number.

## 2. Per-call record (NDJSON, one row per model call)

```json
{"schema":"consonance.call/1",
 "call_id":"…","run_id":"…","arm":"B4","task_id":"…","step":7,
 "manifest_id":"sha256:…","branch_id":"sha256:…","parent_branch_id":null,
 "state_epoch":12,
 "model":"occamy-1.0","engine":"sglang",
 "model_fingerprint":"sha256:…","tokenizer_fingerprint":"sha256:…",
 "renderer_fingerprint":"sha256:…","engine_fingerprint":"sha256:…",
 "prompt_tokens":48211,
 "cached_tokens":null,
 "uncached_prefill_tokens":null,
 "ttft_ms":312.4,"total_ms":5901.0,
 "completion_tokens":812,"finish_reason":"stop",
 "verified_success":true,
 "exit_cause":"completed",
 "derived":{"uncached_prefill_tokens_from_prompt_minus_cached":true}}
```

### The three quantities that must never be conflated

| Field | Meaning | Absent means |
|---|---|---|
| `prompt_tokens` | logical tokens the renderer produced | required — never absent |
| `cached_tokens` | **provider-reported** reuse | **not reported** (unknown) — **never 0** |
| `uncached_prefill_tokens` | **measured** prefill work, when the engine exposes it | not measured |

Anything computed from the other two goes under `derived` with the formula named in the key. A derived
number may be reported; it may never be quoted as a measurement. This is the same rule as
`src/model/contract.ts:84` on our side, and it is the rule that keeps a `null` from becoming a `0` three
tables later.

## 3. Run envelope (`run.json`, frozen BEFORE the first call)

```json
{"schema":"consonance.run/1","run_id":"…","arm":"B4",
 "started_utc":"2026-10-26T…Z",
 "git_sha":"…","fixture_sha":"sha256:…",
 "engine_image_digest":"sha256:…","engine_flags":["--enable-prefix-caching","…"],
 "hardware":"gx10 / GB10, 128 GB unified","quantization":"nvfp4",
 "budgets":{"max_calls":400,"max_cost_usd":0},
 "controls":{"identical_repeat_hits":true,"never_sent_misses":true,
             "append_reuses":true,"rewrite_registers":true},
 "notes":""}
```

A run whose `run.json` was written after its first call is not a pre-registered run; mark it
`"retrospective":true` and expect to be disbelieved.

## 4. Task-replay fixture (the shared unit of work)

One JSON per task class; the same file must be usable by both halves.

```json
{"schema":"consonance.fixture/1","task_id":"repo-fix-0007","class":"single-task-coding",
 "objective":"…",
 "sources":[{"id":"src/lease.ts","revision":"…","sha256":"…","pointer":"#L300-L360"}],
 "observations":[{"step":1,"kind":"tool_output","sha256":"…","tokens":812}],
 "acceptance":{"checks":["…"],"negative_constraints":["never widen a grant"]},
 "expected":{"verified_success":true,"forbidden_claims":["…"]}}
```

`acceptance.negative_constraints` is the field our EXP#51 (prohibition survival) keys on. If a fixture has
no negative constraints, it cannot test the property that matters most to us, and it should not be used for
a quality arm.

## 5. What we need back from each arm

1. `run.json` + the NDJSON rows;
2. a one-page verdict: what fired, what did not, and whether the falsifier was reached;
3. the **control results stated separately** from the primary result — a control that can only report
   "as expected" is not a control;
4. the rebuild/eviction costs you paid, itemised, so a net-benefit claim can be charged for them.

## 6. What we owe back

When our manifest and replay fixture land, this directory gains `schema/context-manifest.v0.json` and
`schema/fixture.v0.json`, plus two golden fixtures that reproduce byte-identically offline. Until then the
field names above are the contract, and `prompt_tokens` from your renderer is the joining key.
